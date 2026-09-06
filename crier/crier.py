#!/usr/bin/env python3
#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""
Town Crier — read-only index and notification service for a TownSquare ledger.

Watches an append-only ledger of plain-text event files (see DOCTRINE.md),
computes each thread's current state, and serves it over HTTP so every agent in
a domain gets the same answer without each reimplementing the rules.

READ-ONLY BY DESIGN. It never writes to the ledger. Point it at a credential
whose scope is read-only and that becomes structurally enforced rather than a
promise this code has to keep.

Configuration is entirely environment-driven — see config.example.env.
"""
import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------- configuration
RCLONE = os.environ.get("TS_RCLONE", "rclone")
REMOTE = os.environ.get("TS_REMOTE", "remote:TownSquare")
STATE_FILE = Path(os.environ.get("TS_STATE", "~/.townsquare-crier/state.json")).expanduser()
POLL_SECONDS = int(os.environ.get("TS_POLL_SECONDS", "300"))
RCLONE_TIMEOUT = int(os.environ.get("TS_RCLONE_TIMEOUT", "180"))
BIND_HOST = os.environ.get("TS_BIND_HOST", "0.0.0.0")
BIND_PORT = int(os.environ.get("TS_BIND_PORT", "8787"))

# Signature verification. Optional: unset TS_ALLOWED_SIGNERS and the Crier
# reports signature PRESENCE only, which is cheap (it comes free from the file
# listing) but proves nothing. With it set, each new event is fetched and
# cryptographically verified once, and the verdict cached.
ALLOWED_SIGNERS = os.environ.get("TS_ALLOWED_SIGNERS", "")
SIG_NAMESPACE = os.environ.get("TS_SIG_NAMESPACE", "townsquare")

# Lifecycle. RESOLVED is the assignee claiming completion with evidence; CLOSED
# is the REQUESTER accepting it. Separating them prevents self-certification.
NEEDS_ASSIGNEE = ("OPEN", "WORKING", "BLOCKED")
NEEDS_REQUESTER = ("RESOLVED", "DONE")   # DONE accepted as a legacy alias
TERMINAL = ("CLOSED", "CANCELLED")
IN_FLIGHT = ("WORKING", "BLOCKED")
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

# <THREAD-ID>.<NNN>-<STATE>__<fields>.txt
#
# THREAD IDS ARE NAMESPACED BY THE ALLOCATING AGENT:
#     TS-20260101-agent-a-001
# Two agents can then never collide on an id no matter how simultaneously they
# write, because the namespace segment differs. This replaces coordination with
# construction - the same reasoning that made the ledger append-only. It also
# extends to federation: <org>-<agent> namespaces across organisations.
#
# The un-namespaced form (TS-20260101-001) is still parsed, because ledgers
# created before this change contain it. A namespace must start with a letter,
# so the two forms are unambiguous.
NAME_RE = re.compile(
    r"^(?P<thread>(?:TS|BB|SEEK|OFFER|WANT)-\d{8}"
    r"(?:-(?P<ns>[a-z][a-z0-9-]*))?-\d{3,})"
    r"\.(?P<seq>\d+)-(?P<state>[A-Z]+)"
    r"(?P<rest>__.*)?\.txt$"
)

_lock = threading.Lock()
_state: dict[str, Any] = {
    "seq": 0, "seen": {}, "events": {}, "newest_at": None,
    "last_poll_ok": None, "last_poll_error": None, "seeded": False,
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_name(path: str, name: str) -> dict[str, Any] | None:
    """The filename IS the interface: routing, priority and state live here."""
    m = NAME_RE.match(name)
    if not m:
        return None
    ev: dict[str, Any] = {
        "thread": m.group("thread"), "seq": int(m.group("seq")),
        "state": m.group("state"), "ns": m.group("ns"),
        "board": path.split("/")[0] if "/" in path else "",
        "filename": name, "path": path,
        "priority": None, "to": None, "from": None, "by": None, "slug": None,
    }
    for f in (f for f in (m.group("rest") or "").split("__") if f):
        if re.fullmatch(r"P[0-3]", f):
            ev["priority"] = f
        elif f.startswith("to-"):
            ev["to"] = f[3:]
        elif f.startswith("from-"):
            ev["from"] = f[5:]
        elif f.startswith("by-"):
            ev["by"] = f[3:]
        elif f.startswith(("impact-", "cap-", "cat-", "host-")):
            k, v = f.split("-", 1)
            ev[k] = v
        else:
            ev["slug"] = f
    return ev


def list_remote() -> list[dict[str, Any]]:
    out = subprocess.run(
        [RCLONE, "lsjson", "--recursive", "--files-only", REMOTE],
        capture_output=True, text=True, timeout=RCLONE_TIMEOUT,
    )
    if out.returncode != 0:
        raise RuntimeError((out.stderr or "rclone failed").strip().splitlines()[-1])
    return json.loads(out.stdout or "[]")


def threads_view() -> dict[str, dict[str, Any]]:
    """Collapse events into threads. THE NEWEST EVENT WINS — the core rule."""
    threads: dict[str, dict[str, Any]] = {}
    for ev in _state["events"].values():
        threads.setdefault(ev["thread"], {"thread": ev["thread"], "events": []})["events"].append(ev)
    for t in threads.values():
        # Duplicate sequence numbers are possible - the store permits duplicate
        # names and there is no locking. Break ties by timestamp, which is what
        # the doctrine specifies. Sorting by seq alone is STABLE, so the winner
        # would otherwise depend on listing order and a claim could be silently
        # lost - observed in practice 2026-09-06.
        evs = sorted(t["events"], key=lambda e: (e["seq"], e.get("mod_time") or ""))
        newest, opening = evs[-1], evs[0]
        t["state"] = newest["state"]
        t["board"] = opening.get("board")
        t["seq_latest"] = newest["seq"]
        t["event_count"] = len(evs)
        for key in ("priority", "to"):
            t[key] = next((e[key] for e in reversed(evs) if e.get(key)), None) or opening.get(key)
        t["from"] = opening.get("from")
        t["subject"] = opening.get("slug")
        t["claimed_by"] = next((e.get("by") for e in reversed(evs) if e.get("by")), None)
        # COLLISION DETECTION. Neither collision observed in practice triggered
        # any alarm - both were found by a human noticing a subject looked wrong.
        # Namespaced ids prevent new thread-id collisions; this surfaces the ones
        # already on the ledger, and any duplicate sequence.
        seqs = [e["seq"] for e in evs]
        dup_seqs = sorted({q for q in seqs if seqs.count(q) > 1})
        openings = sum(1 for e in evs if e["seq"] == 0)
        t["collision"] = None
        if openings > 1 or dup_seqs:
            # A collision on an APPEND-ONLY ledger can never be un-made: both
            # events are real and neither may be deleted. So a flag that simply
            # stays on forever would decay into noise - the exact failure this
            # detection exists to prevent.
            #
            # Split it by whether current truth is still ambiguous:
            #   duplicate openings  - two distinct requests wearing one id. The
            #                         second is invisible while looking filed.
            #                         NEVER benign, however old.
            #   duplicate seq @ head - the newest event is ambiguous RIGHT NOW.
            #   duplicate seq below  - both events happened, order settled by
            #                         timestamp, the thread has moved past it.
            #                         Historical: worth recording, not shouting.
            head = max(seqs)
            t["collision"] = {
                "duplicate_openings": openings if openings > 1 else 0,
                "duplicate_sequences": dup_seqs,
                "unresolved": bool(openings > 1 or head in dup_seqs),
            }
        t["namespace"] = opening.get("ns")
        t["signed"] = all(e.get("signed") for e in evs)
        t["verified"] = (None if any(e.get("verified") is None for e in evs)
                         else all(e.get("verified") for e in evs))
        t["events"] = [{k: e.get(k) for k in
                        ("seq", "state", "filename", "by", "priority", "to",
                         "signed", "verified")} for e in evs]
    return threads


def _fetch(path: str) -> bytes:
    out = subprocess.run([RCLONE, "cat", f"{REMOTE}/{path}"],
                         capture_output=True, timeout=RCLONE_TIMEOUT)
    if out.returncode != 0:
        raise RuntimeError("rclone cat failed")
    return out.stdout


def verify_event(ev: dict[str, Any]) -> bool | None:
    """Cryptographically verify one event. None if verification is disabled.

    Enforces BOTH checks: the signature must validate, AND the header must match
    the filename. Signing only the body would leave priority, assignee and state
    - everything routing depends on - forgeable by rename.
    """
    if not ALLOWED_SIGNERS or not Path(ALLOWED_SIGNERS).expanduser().exists():
        return None
    identity = ev.get("by") or ev.get("from")
    if not identity:
        return False
    try:
        body = _fetch(ev["path"])
        sig = _fetch(ev["path"] + ".sig")
    except Exception:  # noqa: BLE001
        # TRANSPORT FAILURE IS NOT FORGERY. rclone being down or timing out must
        # not be reported as a bad signature - that is the same "unknown read as
        # a definite answer" error this project warns about everywhere else.
        return None
    hdr = {}
    for line in body.decode(errors="replace").splitlines():
        if line.startswith("---"):
            break
        if ":" in line:
            k, v = line.split(":", 1)
            hdr[k.strip()] = v.strip()
    expected = f"{hdr.get('id')}.{hdr.get('event')}-{hdr.get('state')}"
    if not ev["filename"].startswith(expected):
        return False
    # EVERY ROUTING FIELD THE FILENAME CARRIES MUST BE BOUND BY THE SIGNED BODY.
    # id/event/state alone leaves priority and assignee forgeable by rename - a
    # signed P3 for one host becomes a "verified" P0 for another with a copy.
    if ev.get("priority") and hdr.get("priority") != ev["priority"]:
        return False
    if ev.get("to") and hdr.get("to") != ev["to"]:
        return False
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        sp = Path(td) / "s.sig"
        sp.write_bytes(sig)
        r = subprocess.run(
            ["ssh-keygen", "-Y", "verify", "-f", str(Path(ALLOWED_SIGNERS).expanduser()),
             "-I", identity, "-n", SIG_NAMESPACE, "-s", str(sp)],
            input=body, capture_output=True, timeout=30,
        )
    return r.returncode == 0


def poll() -> None:
    try:
        files = list_remote()
    except Exception as e:  # noqa: BLE001
        with _lock:
            _state["last_poll_error"] = f"{_now()}: {e}"
        return
    sigs = {f.get("Path") for f in files if (f.get("Path") or "").endswith(".sig")}
    new_ids: list[str] = []
    pending: list[dict[str, Any]] = []

    with _lock:
        seen = set(_state["seen"])
    for f in files:
        fid = f.get("ID") or f.get("Path")
        if fid in seen:
            continue
        ev = parse_name(f.get("Path", ""), f.get("Name", ""))
        if not ev:
            continue
        ev["mod_time"], ev["id"] = f.get("ModTime"), fid
        ev["signed"] = (ev["path"] + ".sig") in sigs
        pending.append(ev)

    # Verify OUTSIDE the lock. Each verification is two rclone subprocesses plus
    # an ssh-keygen; holding the lock across them would block /health and every
    # other endpoint for the whole of a first seed.
    #
    # UNSIGNED IS NOT THE SAME AS FAILED. No signature is unknown (None); only a
    # signature that exists and does not validate is a failure. Conflating them
    # would report every legacy event as an attack the day verification is
    # switched on, and an alarm that cries wolf immediately is never read again.
    for ev in pending:
        ev["verified"] = verify_event(ev) if ev["signed"] else None

    # The index must be able to FORGET. poll() previously only ever added, so an
    # event archived under §7, or withdrawn as a collision artifact, stayed in
    # the index forever and the index diverged permanently from the ledger. That
    # also makes the collision flag below stick on after a thread is reconciled,
    # turning the one alarm that matters into background noise.
    #
    # Guarded on a NON-EMPTY listing: a successful-but-empty response is far more
    # likely to be a broken remote than a genuinely emptied board, and pruning on
    # it would erase the whole index in one poll.
    present = {f.get("ID") or f.get("Path") for f in files}
    gone: list[str] = []
    with _lock:
        for ev in pending:
            _state["seen"][ev["id"]] = ev["filename"]
            _state["events"][ev["id"]] = ev
            new_ids.append(ev["id"])
        if files:
            gone = [i for i in list(_state["events"]) if i not in present]
            for i in gone:
                _state["events"].pop(i, None)
                _state["seen"].pop(i, None)
        _state["last_removed"] = len(gone)
        if new_ids or gone:
            if new_ids:
                newest = max((_state["events"][i].get("mod_time") or "") for i in new_ids)
                if not _state["newest_at"] or newest > _state["newest_at"]:
                    _state["newest_at"] = newest
            # First run seeds silently; never announce the entire history.
            if _state["seeded"]:
                _state["seq"] += 1
            else:
                _state["seeded"] = True
        _state["last_poll_ok"], _state["last_poll_error"] = _now(), None
        save_state()


def save_state() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(_state))
    tmp.replace(STATE_FILE)


def load_state() -> None:
    if STATE_FILE.exists():
        try:
            _state.update(json.loads(STATE_FILE.read_text()))
        except Exception:  # noqa: BLE001
            pass


def poller() -> None:
    while True:
        poll()
        time.sleep(POLL_SECONDS)


app = FastAPI(title="Town Crier", version="1.0")


@app.get("/health")
def health():
    with _lock:
        stale = True
        if _state["last_poll_ok"]:
            age = (datetime.now(timezone.utc) - datetime.strptime(
                _state["last_poll_ok"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds()
            stale = age > POLL_SECONDS * 2
        body = {"ok": not stale and _state["last_poll_error"] is None,
                "last_poll_ok": _state["last_poll_ok"],
                "last_poll_error": _state["last_poll_error"], "stale": stale,
                "events_known": len(_state["events"]), "watermark": _state["seq"],
                "poll_seconds": POLL_SECONDS}
    return JSONResponse(body, status_code=200 if body["ok"] else 503)


@app.get("/watermark")
def watermark():
    with _lock:
        return {"seq": _state["seq"], "newest_at": _state["newest_at"],
                "last_poll_ok": _state["last_poll_ok"]}


@app.get("/open")
def open_work(host: str = Query(..., description="agent or host name")):
    """Everything needing THIS host to act: work assigned, and closures owed."""
    rows = []
    for t in threads_view().values():
        if t["state"] in NEEDS_ASSIGNEE and t.get("to") == host:
            rows.append({**t, "action": "work"})
        elif t["state"] in NEEDS_REQUESTER and t.get("from") == host:
            rows.append({**t, "action": "close"})
    rows.sort(key=lambda t: (PRIORITY_ORDER.get(t.get("priority"), 4), t["thread"]))
    return {"host": host, "count": len(rows),
            "work": sum(1 for r in rows if r["action"] == "work"),
            "awaiting_closure": sum(1 for r in rows if r["action"] == "close"),
            "threads": rows}


@app.get("/active")
def active():
    """In-flight work fleet-wide. CHECK THIS BEFORE STARTING ANYTHING.

    Duplicate work happens when two agents both see a thread as OPEN and both
    begin. Propagation is not instant, so that window is real.
    """
    rows = [t for t in threads_view().values() if t["state"] in IN_FLIGHT]
    rows.sort(key=lambda t: t["thread"])
    return {"count": len(rows), "threads": rows}


@app.get("/fleet")
def fleet():
    """One call for 'what is everyone doing' — the anti-duplicate-work view."""
    ts = threads_view()
    by_state: dict[str, int] = {}
    per_host: dict[str, dict[str, int]] = {}
    in_flight, blocked, awaiting_closure = [], [], []
    for t in ts.values():
        st = t["state"]
        by_state[st] = by_state.get(st, 0) + 1
        h = per_host.setdefault(t.get("to") or "unassigned", {"work": 0, "in_flight": 0})
        if st == "OPEN":
            h["work"] += 1
        elif st in IN_FLIGHT:
            h["in_flight"] += 1
            entry = {"thread": t["thread"], "to": t.get("to"), "state": st,
                     "priority": t.get("priority"), "subject": t.get("subject"),
                     "claimed_by": t.get("claimed_by")}
            (blocked if st == "BLOCKED" else in_flight).append(entry)
        elif st in NEEDS_REQUESTER:
            awaiting_closure.append({"thread": t["thread"], "requester": t.get("from"),
                                     "subject": t.get("subject")})
    with _lock:
        seq, poll_ok = _state["seq"], _state["last_poll_ok"]
    events = list(_state["events"].values())
    integrity = {
        "verification_enabled": bool(ALLOWED_SIGNERS),
        "events_total": len(events),
        "signed": sum(1 for e in events if e.get("signed")),
        "unsigned": sum(1 for e in events if not e.get("signed")),
        "verified": sum(1 for e in events if e.get("verified") is True),
        # the only alarm condition: a signature that exists and does not validate
        "FAILED_VERIFICATION": sum(1 for e in events if e.get("verified") is False),
        "unverifiable_no_signature": sum(
            1 for e in events if not e.get("signed") and ALLOWED_SIGNERS),
    }
    collisions = [
        {"thread": t["thread"], **t["collision"]}
        for t in ts.values() if t.get("collision")
    ]
    # COLLISIONS is the number still ambiguous, so a clean board reads zero and
    # an operator who reconciles one sees it fall. The historical ones stay in
    # the list and are counted separately - recorded, not shouted.
    integrity["COLLISIONS"] = sum(1 for c in collisions if c.get("unresolved"))
    integrity["collisions_historical"] = len(collisions) - integrity["COLLISIONS"]
    return {"watermark": seq, "last_poll_ok": poll_ok, "threads_total": len(ts),
            "by_state": by_state, "per_host": per_host, "in_flight": in_flight,
            "blocked": blocked, "awaiting_closure": awaiting_closure,
            "collisions": collisions, "integrity": integrity}


@app.get("/events")
def events(since: int = 0, host: str | None = None):
    with _lock:
        seq = _state["seq"]
    rows = list(threads_view().values())
    if host:
        rows = [t for t in rows
                if t.get("to") in (host, "all", None) or t.get("board") == "Bulletin Board"]
    return {"seq": seq, "since": since, "changed": seq > since,
            "count": len(rows), "threads": rows}


@app.get("/thread/{thread_id}")
def thread(thread_id: str):
    t = threads_view().get(thread_id)
    if not t:
        return JSONResponse({"error": "unknown thread", "thread": thread_id}, 404)
    return t


def main() -> None:
    load_state()
    threading.Thread(target=poller, daemon=True).start()
    import uvicorn
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT, log_level="info")


if __name__ == "__main__":
    main()
