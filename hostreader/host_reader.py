#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""
TownSquare host reader — read-only canary inbox client for a single host.

READ-ONLY BY DESIGN. Every request this module issues is a GET against one of
two bounded read-gateway paths. There is no write method, no credential, no
posting, no claiming, no wake, and no authenticated identity. The gateway is
intentionally unauthenticated, so no Authorization header is ever constructed;
"this client cannot write" is a property of the surface it speaks, not a promise.

Runs for a fraction of a second and exits. Nothing resident, no daemon, no open
connection, no privilege — the same posture as poller/townsquare-poll.py.

Two invariants carry most of the weight, and both are explained at length in
hostreader/README.md:

  * State is authoritative and the inbox is rendered FROM it, so repeated polls
    cannot duplicate items even if a write fails halfway.
  * Unreachable is UNKNOWN, never "no work". A notification surface that fails
    silently is worse than none, because it gets trusted.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote

# ---------------------------------------------------------------- contract

STATE_SCHEMA = "townsquare-host-reader-state-v1"
EVIDENCE_SCHEMA = "townsquare-host-reader-live-read-v1"
DISCOVERY_PATH = "/v1/native/discovery"
THREAD_PREFIX = "/v1/native/threads/"
USER_AGENT = "townsquare-host-reader/1 (read-only)"

# Mirrors the read gateway's own thread-id grammar (viewer/read_gateway.py).
# Validated before a request is built so a malformed id never becomes a URL.
THREAD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}\Z")

# A discovery row is only usable as work if it carries all of these. A row
# missing one is incomplete, not merely uninteresting: without event_id there
# is no deduplication key, and without addressee there is no way to know whose
# work it is. Such rows are counted and dropped, never guessed at.
REQUIRED_ROW_FIELDS = ("thread_id", "event_id", "addressee", "state", "kind")
ROW_SOURCES = ("open_work", "history")

DEFAULT_BASE_URL = "http://192.168.2.3:18503"
DEFAULT_HOST_IDENTITY = "cable"
DEFAULT_AGENT_IDENTITY = "sentinel-one"
# Deliberately NOT ~/.townsquare: that directory belongs to the installed
# legacy poller, and this client must not be able to collide with its drop
# file or its last_seq cursor even by accident.
DEFAULT_DIR = "~/.townsquare-reader"
DEFAULT_TIMEOUT = 10.0
DEFAULT_CONTENT_CHARS = 240

EXIT_OK = 0
EXIT_POLL_FAILED = 1
EXIT_LOCAL_ERROR = 2


class ReaderError(RuntimeError):
    """A poll could not be completed. Items and cursor are left alone."""

    def __init__(self, message: str, *, code: str = "error", status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class LocalStateError(RuntimeError):
    """Local configuration or state is unusable. Nothing is written."""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- transport


@dataclass(frozen=True)
class HttpResult:
    """What a GET returned, kept so evidence can report the real HTTP result."""

    url: str
    method: str
    status: int
    payload: dict[str, Any] | None
    error: str | None = None


def _get_json(url: str, timeout: float, *, opener: Callable[..., Any] | None = None) -> HttpResult:
    """Issue exactly one GET and parse a JSON object, or raise ReaderError.

    Every failure mode collapses to ReaderError on purpose: unreachable,
    timeout, non-2xx, non-JSON, and JSON-that-is-not-an-object are all "this
    poll told us nothing", and the caller must treat them identically.
    """
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    open_url = opener or urllib.request.urlopen
    try:
        with open_url(request, timeout=timeout) as response:
            status = int(getattr(response, "status", None) or response.getcode())
            raw = response.read()
    except urllib.error.HTTPError as exc:
        # Read a bounded amount only to report the gateway's own error code.
        detail = ""
        try:
            body = exc.read(2048)
            parsed = json.loads(body)
            if isinstance(parsed, dict) and isinstance(parsed.get("detail"), dict):
                detail = str(parsed["detail"].get("code", ""))
        except Exception:  # noqa: BLE001 - diagnostics must never mask the HTTPError
            detail = ""
        finally:
            exc.close()
        raise ReaderError(
            f"gateway returned HTTP {exc.code}" + (f" ({detail})" if detail else ""),
            code=detail or "http_error",
            status=int(exc.code),
        ) from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ReaderError(f"gateway unreachable: {type(exc).__name__}: {exc}", code="unreachable") from None

    if status < 200 or status >= 300:
        raise ReaderError(f"gateway returned HTTP {status}", code="http_error", status=status)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReaderError(f"gateway response was not JSON: {exc}", code="malformed_json", status=status) from None
    if not isinstance(payload, dict):
        raise ReaderError("gateway response was not a JSON object", code="unexpected_schema", status=status)
    return HttpResult(url=url, method="GET", status=status, payload=payload)


def discovery_url(base_url: str) -> str:
    return base_url.rstrip("/") + DISCOVERY_PATH


def thread_url(base_url: str, thread_id: str) -> str:
    """Build the EXACT thread URL, refusing an id outside the gateway grammar."""
    if not isinstance(thread_id, str) or not THREAD_ID.fullmatch(thread_id):
        raise ReaderError(f"thread id is outside the read contract: {thread_id!r}", code="bad_thread_id")
    return base_url.rstrip("/") + THREAD_PREFIX + quote(thread_id, safe="")


def fetch_discovery(base_url: str, timeout: float = DEFAULT_TIMEOUT, *, opener=None) -> HttpResult:
    return _get_json(discovery_url(base_url), timeout, opener=opener)


def fetch_thread(base_url: str, thread_id: str, timeout: float = DEFAULT_TIMEOUT, *, opener=None) -> HttpResult:
    return _get_json(thread_url(base_url, thread_id), timeout, opener=opener)


# ---------------------------------------------------------------- parsing


@dataclass(frozen=True)
class WorkItem:
    thread_id: str
    event_id: str
    addressee: str
    state: str
    kind: str
    owner: str | None = None
    ledger_seq: int | None = None
    thread_ordinal: int | None = None
    sensitivity: str | None = None
    committed_at: str | None = None
    sources: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "event_id": self.event_id,
            "addressee": self.addressee,
            "state": self.state,
            "kind": self.kind,
            "owner": self.owner,
            "ledger_seq": self.ledger_seq,
            "thread_ordinal": self.thread_ordinal,
            "sensitivity": self.sensitivity,
            "committed_at": self.committed_at,
            "sources": list(self.sources),
        }


@dataclass(frozen=True)
class Discovery:
    items: tuple[WorkItem, ...]
    skipped_incomplete: int
    board_thread_ids: tuple[str, ...]


def _row_to_item(row: dict[str, Any], source: str) -> WorkItem | None:
    """Return a WorkItem, or None when the row is incomplete and must be dropped."""
    values: dict[str, str] = {}
    for key in REQUIRED_ROW_FIELDS:
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            return None
        values[key] = value.strip()
    if not THREAD_ID.fullmatch(values["thread_id"]):
        return None
    owner = row.get("owner")
    seq = row.get("ledger_seq")
    ordinal = row.get("thread_ordinal")
    sensitivity = row.get("sensitivity")
    committed_at = row.get("committed_at")
    return WorkItem(
        thread_id=values["thread_id"],
        event_id=values["event_id"],
        addressee=values["addressee"],
        state=values["state"],
        kind=values["kind"],
        owner=owner.strip() if isinstance(owner, str) else None,
        # bool is an int subclass; a boolean sequence number is a schema error.
        ledger_seq=seq if isinstance(seq, int) and not isinstance(seq, bool) else None,
        thread_ordinal=ordinal if isinstance(ordinal, int) and not isinstance(ordinal, bool) else None,
        sensitivity=sensitivity.strip() if isinstance(sensitivity, str) else None,
        committed_at=committed_at.strip() if isinstance(committed_at, str) else None,
        sources=(source,),
    )


def parse_discovery(payload: Any) -> Discovery:
    """Validate a discovery payload against the gateway contract.

    Raises ReaderError when the payload is not shaped like discovery at all:
    that means this client does not understand the gateway, and the honest
    response is to change nothing. Individual unusable rows are counted in
    skipped_incomplete instead, so one bad row cannot hide a good board.
    """
    if not isinstance(payload, dict):
        raise ReaderError("discovery payload was not a JSON object", code="unexpected_schema")
    for key in ROW_SOURCES:
        if key in payload and not isinstance(payload[key], list):
            raise ReaderError(f"discovery field {key!r} was not a list", code="unexpected_schema")
    if not any(key in payload for key in ROW_SOURCES):
        raise ReaderError("discovery payload carried neither open_work nor history", code="unexpected_schema")
    boards = payload.get("boards", {})
    if not isinstance(boards, dict):
        raise ReaderError("discovery field 'boards' was not an object", code="unexpected_schema")

    merged: dict[str, WorkItem] = {}
    skipped = 0
    for source in ROW_SOURCES:
        for row in payload.get(source, []) or []:
            if not isinstance(row, dict):
                skipped += 1
                continue
            item = _row_to_item(row, source)
            if item is None:
                skipped += 1
                continue
            existing = merged.get(item.event_id)
            if existing is None:
                merged[item.event_id] = item
            elif source not in existing.sources:
                # open_work and history overlap by design; record both origins
                # on one item rather than emitting the same event twice.
                merged[item.event_id] = WorkItem(**{
                    **existing.as_dict(),
                    "sources": existing.sources + (source,),
                })

    board_ids: list[str] = []
    for values in boards.values():
        if not isinstance(values, list):
            raise ReaderError("discovery board was not a list", code="unexpected_schema")
        for value in values:
            if isinstance(value, str) and value not in board_ids:
                board_ids.append(value)

    items = tuple(sorted(merged.values(), key=lambda i: (i.ledger_seq if i.ledger_seq is not None else 1 << 62, i.event_id)))
    return Discovery(items=items, skipped_incomplete=skipped, board_thread_ids=tuple(board_ids))


def normalize_identities(*values: Iterable[str] | str | None) -> tuple[str, ...]:
    """Flatten, lowercase, de-blank and de-duplicate configured identities."""
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        parts = [value] if isinstance(value, str) else list(value)
        for part in parts:
            if not isinstance(part, str):
                continue
            for piece in part.split(","):
                token = piece.strip().lower()
                if token and token not in out:
                    out.append(token)
    return tuple(out)


def filter_for_identities(items: Iterable[WorkItem], identities: Iterable[str]) -> tuple[WorkItem, ...]:
    """Keep only work ADDRESSED to a configured identity.

    Visible work is not this host's work. The gateway publishes the whole
    non-RESTRICTED board; ownership is irrelevant here on purpose — being the
    owner of a thread addressed to someone else does not make it an inbox item.
    """
    wanted = {token for token in normalize_identities(identities)}
    if not wanted:
        raise LocalStateError("no host or agent identity is configured; refusing to claim the whole board")
    return tuple(item for item in items if item.addressee.strip().lower() in wanted)


def summarize_thread(payload: Any, *, content_chars: int = DEFAULT_CONTENT_CHARS) -> dict[str, Any]:
    """Reduce an exact thread read to the few fields the inbox needs."""
    if not isinstance(payload, dict):
        raise ReaderError("thread payload was not a JSON object", code="unexpected_schema")
    thread_id = payload.get("thread_id")
    events = payload.get("events")
    if not isinstance(thread_id, str) or not thread_id:
        raise ReaderError("thread payload had no thread_id", code="unexpected_schema")
    if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
        raise ReaderError("thread payload had no usable events list", code="unexpected_schema")
    latest = events[-1] if events else {}
    content = latest.get("content")
    excerpt = None
    if isinstance(content, str):
        collapsed = " ".join(content.split())
        excerpt = collapsed[:content_chars] + ("…" if len(collapsed) > content_chars else "")
    return {
        "status": "ok",
        "thread_id": thread_id,
        "archived": bool(payload.get("archived")),
        "event_count": len(events),
        "latest_event_id": latest.get("event_id") if isinstance(latest.get("event_id"), str) else None,
        "latest_state": latest.get("state") if isinstance(latest.get("state"), str) else None,
        "latest_sensitivity": latest.get("sensitivity") if isinstance(latest.get("sensitivity"), str) else None,
        "excerpt": excerpt,
        "retrieved_at": now_iso(),
    }


# ---------------------------------------------------------------- persistence


def empty_state() -> dict[str, Any]:
    return {
        "schema": STATE_SCHEMA,
        "created_at": now_iso(),
        "last_poll": None,
        "seen_event_ids": [],
        "items": [],
        "counters": {
            "polls_ok": 0,
            "polls_failed": 0,
            "items_added": 0,
            "rows_skipped_incomplete": 0,
            "thread_reads_ok": 0,
            "thread_reads_failed": 0,
        },
    }


def load_state(path: Path) -> dict[str, Any]:
    """Load state, or raise LocalStateError.

    A missing file is a first run. An unreadable or off-schema file is NOT
    silently reset: re-deriving an empty state would re-add every item and
    duplicate the inbox, so the operator chooses that with --reset-state.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return empty_state()
    except OSError as exc:
        raise LocalStateError(f"state file is unreadable: {exc}") from None
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LocalStateError(
            f"state file is corrupt ({exc}); inspect it, then re-run with --reset-state to start a new cursor"
        ) from None
    if not isinstance(state, dict) or state.get("schema") != STATE_SCHEMA:
        raise LocalStateError(
            f"state file is not {STATE_SCHEMA}; inspect it, then re-run with --reset-state to start a new cursor"
        )
    for key in ("seen_event_ids", "items"):
        if not isinstance(state.get(key), list):
            raise LocalStateError(f"state file field {key!r} is not a list; re-run with --reset-state")
    counters = state.get("counters")
    if not isinstance(counters, dict):
        state["counters"] = empty_state()["counters"]
    else:
        for key, value in empty_state()["counters"].items():
            counters.setdefault(key, value)
    return state


def atomic_write(path: Path, text: str) -> None:
    """Write via a same-directory temp file, fsync, then rename.

    os.replace is atomic within a filesystem, so a reader never observes a
    half-written cursor and a crash leaves the previous good file in place.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    handle = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    os.replace(str(tmp), str(path))


def save_state(path: Path, state: dict[str, Any]) -> None:
    atomic_write(path, json.dumps(state, indent=2, sort_keys=True) + "\n")


# ---------------------------------------------------------------- rendering


def render_inbox(state: dict[str, Any], *, base_url: str, identities: Iterable[str]) -> str:
    """Render the human-readable inbox entirely FROM state."""
    who = ", ".join(normalize_identities(identities)) or "(none)"
    last = state.get("last_poll") if isinstance(state.get("last_poll"), dict) else None
    lines = [
        "TOWNSQUARE - canary read inbox (READ-ONLY, CANARY / NON-AUTHORITATIVE)",
        f"identities:  {who}",
        f"gateway:     {base_url}",
    ]
    if last is None:
        lines += ["poll:        never", ""]
    elif last.get("ok"):
        lines += [
            f"poll:        OK at {last.get('at')}  (HTTP {last.get('http_status')} {last.get('endpoint')})",
            "",
        ]
    else:
        lines += [
            f"poll:        FAILED at {last.get('at')}  ({last.get('error')})",
            f"endpoint:    {last.get('endpoint')}",
            "",
            "This is UNKNOWN, not 'no work'. Do not read the list below as current.",
            "Items shown are the last good read; newer work may exist unseen.",
            "",
        ]

    items = [item for item in state.get("items", []) if isinstance(item, dict)]
    if not items:
        lines.append("  Nothing addressed to these identities in the last good read.")
    else:
        lines.append(f"  {len(items)} item(s) addressed to these identities:")
        for item in items:
            detail = item.get("detail") if isinstance(item.get("detail"), dict) else None
            if detail is None:
                mark = "detail PENDING"
            elif detail.get("status") == "ok":
                mark = f"detail ok ({detail.get('event_count')} event(s))"
            else:
                mark = f"detail {str(detail.get('status', 'unknown')).upper()}"
            seq = item.get("ledger_seq")
            lines.append(
                f"  [{str(item.get('kind', '?')):<8}] {str(item.get('state', '?')):<9} "
                f"seq {str(seq if seq is not None else '--'):>4}  {item.get('thread_id')}"
            )
            lines.append(
                f"            to {item.get('addressee')}  owner {item.get('owner')}  "
                f"event {item.get('event_id')}  {mark}"
            )
            lines.append(f"            first seen {item.get('first_seen_at')}  committed {item.get('committed_at')}")
            if detail and detail.get("excerpt"):
                lines.append(f"            {detail['excerpt']}")
            lines.append("")
        lines += [
            f"  Detail:  curl -s {base_url.rstrip('/')}{THREAD_PREFIX}<thread_id>",
            "  This client only reads. It cannot post, claim, or acknowledge.",
        ]

    counters = state.get("counters", {}) if isinstance(state.get("counters"), dict) else {}
    lines += [
        "",
        "  counters: " + "  ".join(f"{key}={value}" for key, value in sorted(counters.items())),
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- poll


@dataclass
class Config:
    base_url: str = DEFAULT_BASE_URL
    identities: tuple[str, ...] = ()
    state_file: Path = field(default_factory=lambda: Path(DEFAULT_DIR).expanduser() / "state.json")
    inbox_file: Path = field(default_factory=lambda: Path(DEFAULT_DIR).expanduser() / "INBOX.txt")
    timeout: float = DEFAULT_TIMEOUT
    content_chars: int = DEFAULT_CONTENT_CHARS
    fetch_threads: bool = True


@dataclass
class PollResult:
    ok: bool
    added: tuple[str, ...] = ()
    error: str | None = None
    error_code: str | None = None
    http_status: int | None = None
    requests: tuple[dict[str, Any], ...] = ()
    matched: tuple[WorkItem, ...] = ()
    visible: int = 0
    skipped_incomplete: int = 0


def poll_once(config: Config, state: dict[str, Any], *, opener=None) -> PollResult:
    """Run one bounded poll and mutate `state` in place.

    On failure only the last_poll/counter fields change: known items, their
    detail, and the dedup cursor are preserved exactly.
    """
    requests: list[dict[str, Any]] = []
    endpoint = discovery_url(config.base_url)
    try:
        result = fetch_discovery(config.base_url, config.timeout, opener=opener)
        requests.append({"method": "GET", "url": result.url, "http_status": result.status})
        discovery = parse_discovery(result.payload)
    except ReaderError as exc:
        requests.append({"method": "GET", "url": endpoint, "http_status": exc.status, "error": exc.code})
        state["last_poll"] = {
            "at": now_iso(),
            "ok": False,
            "endpoint": endpoint,
            "http_status": exc.status,
            "error": f"{exc.code}: {exc}",
        }
        state["counters"]["polls_failed"] = int(state["counters"].get("polls_failed", 0)) + 1
        return PollResult(
            ok=False, error=str(exc), error_code=exc.code, http_status=exc.status, requests=tuple(requests)
        )

    matched = filter_for_identities(discovery.items, config.identities)
    seen = list(state.get("seen_event_ids", []))
    seen_set = set(seen)
    items = [item for item in state.get("items", []) if isinstance(item, dict)]
    by_event = {item.get("event_id"): item for item in items}
    added: list[str] = []

    for item in matched:
        if item.event_id in seen_set:
            continue
        record = item.as_dict()
        record["first_seen_at"] = now_iso()
        record["detail"] = None
        items.append(record)
        by_event[item.event_id] = record
        seen.append(item.event_id)
        seen_set.add(item.event_id)
        added.append(item.event_id)

    # Exact-thread retrieval, only for items whose detail is still missing.
    # A transient failure leaves detail null so the NEXT poll retries it
    # without producing a second inbox entry; a gateway 404 is terminal.
    if config.fetch_threads:
        for record in items:
            if record.get("detail") is not None:
                continue
            thread_id = record.get("thread_id")
            try:
                thread = fetch_thread(config.base_url, str(thread_id), config.timeout, opener=opener)
                requests.append({"method": "GET", "url": thread.url, "http_status": thread.status})
                record["detail"] = summarize_thread(thread.payload, content_chars=config.content_chars)
                state["counters"]["thread_reads_ok"] = int(state["counters"].get("thread_reads_ok", 0)) + 1
            except ReaderError as exc:
                requests.append({
                    "method": "GET",
                    "url": thread_url(config.base_url, str(thread_id)) if THREAD_ID.fullmatch(str(thread_id)) else None,
                    "http_status": exc.status,
                    "error": exc.code,
                })
                state["counters"]["thread_reads_failed"] = int(state["counters"].get("thread_reads_failed", 0)) + 1
                if exc.status == 404 or exc.code in {"not_found", "bad_thread_id"}:
                    record["detail"] = {"status": "not_found", "error": exc.code, "retrieved_at": now_iso()}

    state["items"] = items
    state["seen_event_ids"] = seen
    state["last_poll"] = {
        "at": now_iso(),
        "ok": True,
        "endpoint": endpoint,
        "http_status": requests[0].get("http_status"),
        "error": None,
        "visible_rows": len(discovery.items),
        "matched_rows": len(matched),
    }
    counters = state["counters"]
    counters["polls_ok"] = int(counters.get("polls_ok", 0)) + 1
    counters["items_added"] = int(counters.get("items_added", 0)) + len(added)
    counters["rows_skipped_incomplete"] = int(counters.get("rows_skipped_incomplete", 0)) + discovery.skipped_incomplete
    return PollResult(
        ok=True,
        added=tuple(added),
        http_status=requests[0].get("http_status"),
        requests=tuple(requests),
        matched=matched,
        visible=len(discovery.items),
        skipped_incomplete=discovery.skipped_incomplete,
    )


def persist(config: Config, state: dict[str, Any]) -> None:
    """Write state first, then render the inbox FROM it. Order matters."""
    save_state(config.state_file, state)
    atomic_write(config.inbox_file, render_inbox(state, base_url=config.base_url, identities=config.identities))


def run_poll(config: Config, *, reset_state: bool = False, opener=None) -> PollResult:
    state = empty_state() if reset_state else load_state(config.state_file)
    result = poll_once(config, state, opener=opener)
    persist(config, state)
    return result


# ---------------------------------------------------------------- evidence


def client_commit(repo: Path | None = None) -> str:
    """Best-effort source commit of this client, for evidence only."""
    override = os.environ.get("TS_READER_COMMIT")
    if override:
        return override.strip()
    root = repo or Path(__file__).resolve().parent.parent
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=10, check=False, shell=False, text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else "unknown"


def evidence_record(config: Config, result: PollResult, state: dict[str, Any]) -> dict[str, Any]:
    """Build a SANITIZED live-read record.

    Identifiers, endpoints, HTTP results and counts only. No credentials (there
    are none), no headers, no thread content, no excerpts.
    """
    observed = [
        {
            "thread_id": item.thread_id,
            "event_id": item.event_id,
            "ledger_seq": item.ledger_seq,
            "state": item.state,
            "kind": item.kind,
            "addressee": item.addressee,
        }
        for item in result.matched
    ]
    threads = sorted({entry.get("url") or "" for entry in result.requests if THREAD_PREFIX in (entry.get("url") or "")})
    return {
        "schema": EVIDENCE_SCHEMA,
        "runtime_boundary": "CANARY / NON-AUTHORITATIVE; read-only host client; no write, claim, wake, or authenticated identity",
        "generated_at": now_iso(),
        "host": os.uname().nodename,
        "client_commit": client_commit(),
        "gateway_base_url": config.base_url,
        "configured_identities": list(normalize_identities(config.identities)),
        "http_methods_used": ["GET"],
        "mutating_requests": 0,
        "requests": [
            {"method": entry.get("method"), "url": entry.get("url"),
             "http_status": entry.get("http_status"), "error": entry.get("error")}
            for entry in result.requests
        ],
        "discovery": {
            "endpoint": discovery_url(config.base_url),
            "http_status": result.http_status,
            "ok": result.ok,
            "error": result.error_code,
            "visible_rows": result.visible,
            "matched_rows": len(result.matched),
            "rows_skipped_incomplete": result.skipped_incomplete,
        },
        "exact_thread_reads": threads,
        "observed_addressed_work": observed,
        "items_added_this_poll": list(result.added),
        "inbox_item_total": len(state.get("items", [])),
        "counters": state.get("counters", {}),
        "state_file": str(config.state_file),
        "inbox_file": str(config.inbox_file),
    }


# ---------------------------------------------------------------- CLI


def _env_flag(name: str) -> bool | None:
    value = os.environ.get(name)
    if value is None:
        return None
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_parser() -> argparse.ArgumentParser:
    default_dir = Path(os.environ.get("TS_READER_DIR", DEFAULT_DIR)).expanduser()
    parser = argparse.ArgumentParser(
        prog="python -m hostreader",
        description="Read-only TownSquare canary inbox client for one host. Issues GET only.",
    )
    parser.add_argument("--base-url", default=os.environ.get("TS_READER_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--host-identity", default=os.environ.get("TS_READER_HOST_IDENTITY", DEFAULT_HOST_IDENTITY))
    parser.add_argument("--agent-identity", default=os.environ.get("TS_READER_AGENT_IDENTITY", DEFAULT_AGENT_IDENTITY))
    parser.add_argument("--identity", action="append", default=[],
                        help="additional identity to accept work for; repeatable")
    parser.add_argument("--state-file", default=os.environ.get("TS_READER_STATE_FILE", str(default_dir / "state.json")))
    parser.add_argument("--inbox-file", default=os.environ.get("TS_READER_INBOX_FILE", str(default_dir / "INBOX.txt")))
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("TS_READER_TIMEOUT", DEFAULT_TIMEOUT)))
    parser.add_argument("--content-chars", type=int,
                        default=int(os.environ.get("TS_READER_CONTENT_CHARS", DEFAULT_CONTENT_CHARS)))
    parser.add_argument("--no-threads", action="store_true", default=bool(_env_flag("TS_READER_NO_THREADS")),
                        help="skip exact-thread retrieval; discovery rows only")
    parser.add_argument("--once", action="store_true", default=True,
                        help="poll exactly once and exit (the default; recurrence is scheduled externally)")
    parser.add_argument("--repeat-seconds", type=float, default=None,
                        help="instead of one shot, poll every N seconds for --max-cycles cycles")
    parser.add_argument("--max-cycles", type=int, default=int(os.environ.get("TS_READER_MAX_CYCLES", "2")))
    parser.add_argument("--reset-state", action="store_true",
                        help="discard the local cursor and inbox and start a new one")
    parser.add_argument("--evidence", default=os.environ.get("TS_READER_EVIDENCE"),
                        help="write a sanitized live-read evidence JSON file to this path")
    parser.add_argument("--quiet", action="store_true")
    return parser


def config_from_args(args: argparse.Namespace) -> Config:
    identities = normalize_identities(args.host_identity, args.agent_identity, args.identity)
    if not identities:
        raise LocalStateError("no host or agent identity is configured; refusing to claim the whole board")
    return Config(
        base_url=args.base_url,
        identities=identities,
        state_file=Path(args.state_file).expanduser(),
        inbox_file=Path(args.inbox_file).expanduser(),
        timeout=args.timeout,
        content_chars=args.content_chars,
        fetch_threads=not args.no_threads,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = config_from_args(args)
    except LocalStateError as exc:
        print(f"host reader: {exc}", file=sys.stderr)
        return EXIT_LOCAL_ERROR

    cycles = 1 if args.repeat_seconds is None else max(1, args.max_cycles)
    result: PollResult | None = None
    state: dict[str, Any] = {}
    for cycle in range(cycles):
        if cycle and args.repeat_seconds:
            time.sleep(args.repeat_seconds)
        try:
            state = empty_state() if (args.reset_state and cycle == 0) else load_state(config.state_file)
            result = poll_once(config, state)
            persist(config, state)
        except LocalStateError as exc:
            print(f"host reader: {exc}", file=sys.stderr)
            return EXIT_LOCAL_ERROR
        except OSError as exc:
            print(f"host reader: could not persist state or inbox: {exc}", file=sys.stderr)
            return EXIT_LOCAL_ERROR
        if not args.quiet:
            if result.ok:
                print(
                    f"poll ok: {result.visible} visible row(s), {len(result.matched)} addressed to "
                    f"{','.join(config.identities)}, {len(result.added)} new, "
                    f"{result.skipped_incomplete} incomplete row(s) skipped"
                )
            else:
                print(f"poll FAILED ({result.error_code}): {result.error} -- UNKNOWN, not 'no work'", file=sys.stderr)

    assert result is not None
    if args.evidence:
        try:
            atomic_write(Path(args.evidence).expanduser(),
                         json.dumps(evidence_record(config, result, state), indent=2, sort_keys=True) + "\n")
        except OSError as exc:
            print(f"host reader: could not write evidence: {exc}", file=sys.stderr)
            return EXIT_LOCAL_ERROR
        if not args.quiet:
            print(f"evidence written: {args.evidence}")
    return EXIT_OK if result.ok else EXIT_POLL_FAILED
