#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Read-only canary inbox client for one host. GET only; one poll, then exit.

Fetches /v1/native/discovery, keeps rows addressed to the configured identities,
GETs each matched thread once, dedups by event_id across runs, and writes state
then a derived inbox atomically. A gateway or response that is unusable is
UNKNOWN: last-good items are kept and the inbox says so.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

DISCOVERY_PATH = "/v1/native/discovery"
THREAD_PREFIX = "/v1/native/threads/"
STATE_SCHEMA = "townsquare-host-reader-state-v1"
EVIDENCE_SCHEMA = "townsquare-host-reader-live-read-v2"
# Mirrors the read gateway's thread-id grammar; checked before building a URL.
THREAD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}\Z")
ROW_FIELDS = ("thread_id", "event_id", "addressee", "state", "kind")
DEFAULT_BASE_URL = "http://192.168.2.3:18503"
DEFAULT_IDENTITIES = ("cable", "sentinel-one")
# Deliberately not ~/.townsquare, which belongs to the legacy poller.
DEFAULT_DIR = Path("~/.townsquare-reader")


class ReaderError(RuntimeError):
    """The gateway or its response was unusable; the poll tells us nothing."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class LocalStateError(RuntimeError):
    """Local state is unusable; nothing is written."""


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_json(url, timeout, opener=urllib.request.urlopen):
    """One GET returning (status, JSON object); every failure is ReaderError."""
    request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with opener(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read()
    except Exception as exc:  # HTTPError, URLError, timeout, reset
        raise ReaderError(f"gateway unreachable or refused: {type(exc).__name__}: {exc}",
                          getattr(exc, "code", None)) from None
    if not 200 <= status < 300:
        raise ReaderError(f"gateway returned HTTP {status}", status)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except ValueError:
        raise ReaderError("gateway response was not JSON", status) from None
    if not isinstance(payload, dict):
        raise ReaderError("gateway response was not a JSON object", status)
    return status, payload


def thread_url(base_url, thread_id):
    if not THREAD_ID.fullmatch(thread_id):
        raise ReaderError(f"thread id outside the read contract: {thread_id!r}")
    return base_url.rstrip("/") + THREAD_PREFIX + quote(thread_id, safe="")


def parse_rows(payload):
    """Return (rows by event_id, skipped count); raise if not discovery-shaped."""
    sources = [payload.get(key) for key in ("open_work", "history") if key in payload]
    if not sources or not all(isinstance(s, list) for s in sources):
        raise ReaderError("discovery payload lacks open_work/history lists")
    rows, skipped = {}, 0
    for row in (r for source in sources for r in source):
        values = {k: row.get(k).strip() for k in ROW_FIELDS
                  if isinstance(row, dict) and isinstance(row.get(k), str) and row.get(k).strip()}
        if len(values) < len(ROW_FIELDS) or not THREAD_ID.fullmatch(values["thread_id"]):
            skipped += 1
            continue
        seq = row.get("ledger_seq")
        values["ledger_seq"] = seq if isinstance(seq, int) and not isinstance(seq, bool) else None
        rows.setdefault(values["event_id"], values)
    return rows, skipped


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def load_state(path):
    """Missing file is a first run; unreadable or off-schema is an error, never a silent reset."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"schema": STATE_SCHEMA, "last_poll": None, "seen_event_ids": [], "items": []}
    except OSError as exc:
        raise LocalStateError(f"state file unreadable: {exc}") from None
    try:
        state = json.loads(text)
    except ValueError:
        raise LocalStateError(f"state file {path} is corrupt; inspect or remove it deliberately") from None
    if (not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA
            or not isinstance(state.get("seen_event_ids"), list) or not isinstance(state.get("items"), list)):
        raise LocalStateError(f"state file {path} is not {STATE_SCHEMA}; inspect or remove it deliberately")
    return state


def render_inbox(state, base_url, identities):
    last = state["last_poll"]
    lines = ["TOWNSQUARE canary read inbox (READ-ONLY, NON-AUTHORITATIVE)",
             f"identities: {', '.join(identities)}", f"gateway:    {base_url}"]
    if last is None:
        lines.append("poll:       never")
    elif last["ok"]:
        lines.append(f"poll:       OK at {last['at']}")
    else:
        lines += [f"poll:       FAILED at {last['at']} ({last['error']})",
                  "UNKNOWN, not 'no work'. Items below are the last good read; newer work may exist."]
    lines.append("")
    if not state["items"]:
        lines.append("Nothing addressed to these identities in the last good read.")
    for item in state["items"]:
        detail = item.get("detail") or "pending"
        lines.append(f"[{item['kind']}] {item['state']} seq {item['ledger_seq']} {item['thread_id']} "
                     f"to {item['addressee']} event {item['event_id']} thread:{detail}")
    return "\n".join(lines) + "\n"


def poll(base_url, identities, state_file, inbox_file, timeout=10.0, opener=urllib.request.urlopen):
    """One poll. Returns a result dict; raises LocalStateError/OSError for local faults."""
    state = load_state(state_file)
    base = base_url.rstrip("/")
    requests, result = [], {"ok": False, "error": None, "visible": 0, "matched": [], "added": [], "skipped": 0}

    def get(url):
        entry = {"method": "GET", "url": url, "http_status": None}
        requests.append(entry)
        try:
            status, payload = get_json(url, timeout, opener)
        except ReaderError as exc:
            entry["http_status"], entry["error"] = exc.status, str(exc)
            raise
        entry["http_status"] = status
        return payload

    try:
        rows, result["skipped"] = parse_rows(get(base + DISCOVERY_PATH))
        wanted = {i.lower() for i in identities}
        matched = sorted((r for r in rows.values() if r["addressee"].lower() in wanted),
                         key=lambda r: (r["ledger_seq"] is None, r["ledger_seq"] or 0, r["event_id"]))
        result.update(visible=len(rows), matched=matched)
        seen = set(state["seen_event_ids"])
        for row in matched:
            if row["event_id"] not in seen:
                seen.add(row["event_id"])
                state["seen_event_ids"].append(row["event_id"])
                state["items"].append({**row, "first_seen_at": now_iso(), "detail": None})
                result["added"].append(row["event_id"])
        for item in state["items"]:  # exact-thread GET; a transient failure retries next poll
            if item["detail"] is None:
                try:
                    events = get(thread_url(base, item["thread_id"])).get("events")
                    item["detail"] = f"ok ({len(events)} events)" if isinstance(events, list) else None
                except ReaderError as exc:
                    if exc.status == 404:
                        item["detail"] = "not_found"
        result["ok"] = True
        state["last_poll"] = {"at": now_iso(), "ok": True, "error": None}
    except ReaderError as exc:
        result["error"] = str(exc)
        state["last_poll"] = {"at": now_iso(), "ok": False, "error": str(exc)}

    atomic_write(state_file, json.dumps(state, indent=2, sort_keys=True) + "\n")
    atomic_write(inbox_file, render_inbox(state, base_url, identities))  # derived from state
    result["requests"], result["total_items"] = requests, len(state["items"])
    return result


def evidence_record(result, base_url, identities, client_commit):
    """Identifiers, endpoints and HTTP results only: no content, headers or paths."""
    return {
        "schema": EVIDENCE_SCHEMA,
        "boundary": "CANARY / NON-AUTHORITATIVE; read-only; GET only",
        "generated_at": now_iso(),
        "client_commit": client_commit,
        "gateway_base_url": base_url,
        "configured_identities": list(identities),
        "poll_ok": result["ok"],
        "error": result["error"],
        "visible_rows": result["visible"],
        "matched_rows": len(result["matched"]),
        "rows_skipped_incomplete": result["skipped"],
        "matched_work": [{k: r[k] for k in ("thread_id", "event_id", "ledger_seq", "addressee")}
                         for r in result["matched"]],
        "requests": [{k: e[k] for k in ("method", "url", "http_status")} for e in result["requests"]],
        "mutating_requests": sum(e["method"] != "GET" for e in result["requests"]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m hostreader", description="Read-only canary inbox client.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--identity", action="append", help="repeatable; default: cable, sentinel-one")
    parser.add_argument("--state-file", default=str(DEFAULT_DIR / "state.json"))
    parser.add_argument("--inbox-file", default=str(DEFAULT_DIR / "INBOX.txt"))
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--evidence", help="write a sanitized evidence JSON file here")
    args = parser.parse_args(argv)
    identities = tuple(dict.fromkeys(i.strip().lower() for i in (args.identity or DEFAULT_IDENTITIES) if i.strip()))
    if not identities:
        print("host reader: no identity configured", file=sys.stderr)
        return 2
    try:
        result = poll(args.base_url, identities, Path(args.state_file).expanduser(),
                      Path(args.inbox_file).expanduser(), args.timeout)
        if args.evidence:
            commit = subprocess.run(["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "HEAD"],
                                    capture_output=True, text=True, check=False).stdout.strip()
            atomic_write(Path(args.evidence).expanduser(), json.dumps(
                evidence_record(result, args.base_url, identities, commit or "unknown"), indent=2) + "\n")
    except (LocalStateError, OSError) as exc:
        print(f"host reader: {exc}", file=sys.stderr)
        return 2
    if not result["ok"]:
        print(f"poll FAILED: {result['error']} -- UNKNOWN, not 'no work'", file=sys.stderr)
        return 1
    print(f"poll ok: {result['visible']} visible, {len(result['matched'])} matched, {len(result['added'])} new")
    return 0
