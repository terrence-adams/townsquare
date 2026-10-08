"""Bounded LAN read gateway for the non-authoritative TownSquare canary.

The public surface is deliberately smaller than the authenticated Ledger API:
two health reads, sanitized discovery, and exact non-RESTRICTED thread reads.
There is no write method, generic proxy, client credential, or configurable
upstream origin.
"""
from __future__ import annotations

import json
import re
import socket
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


LEDGER_ORIGIN = "http://ledger:8790"
TOKEN_FILE = "/run/secrets/viewer-native-credential"
STATUS_PATH = "/v1/native/status/ready"
DISCOVERY_PATH = "/v1/native/discovery"
THREAD_PREFIX = "/v1/native/threads/"
MAX_TOKEN_BYTES = 4096
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_DISCOVERY_THREADS = 256
TIMEOUT_SECONDS = 5.0
THREAD_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}\Z")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


_OPENER = build_opener(ProxyHandler({}), _NoRedirect())


@dataclass(frozen=True)
class PublicError(Exception):
    status: int
    code: str
    message: str


NOT_FOUND = PublicError(404, "not_found", "record not found")
BAD_REQUEST = PublicError(400, "bad_request", "request is outside the read gateway contract")
UNAVAILABLE = PublicError(503, "unavailable", "read gateway dependency unavailable")


def _token() -> str:
    try:
        with open(TOKEN_FILE, "rb") as handle:
            raw = handle.read(MAX_TOKEN_BYTES + 1)
    except OSError:
        raise UNAVAILABLE from None
    if not raw or len(raw) > MAX_TOKEN_BYTES:
        raise UNAVAILABLE
    try:
        value = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise UNAVAILABLE from None
    if not value or any(character in value for character in "\r\n"):
        raise UNAVAILABLE
    return value


def _allowed_upstream_path(path: str) -> bool:
    if path in {STATUS_PATH, DISCOVERY_PATH}:
        return True
    if not path.startswith(THREAD_PREFIX):
        return False
    suffix = path[len(THREAD_PREFIX):]
    thread_id, separator, query = suffix.partition("?")
    return bool(THREAD_ID.fullmatch(thread_id)) and separator == "?" and query == "include_archived=true"


def _read_json(path: str, *, thread_lookup: bool = False) -> dict[str, Any]:
    if not _allowed_upstream_path(path):
        raise UNAVAILABLE
    request = Request(
        LEDGER_ORIGIN + path,
        method="GET",
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + _token(),
            "User-Agent": "townsquare-read-gateway/1",
        },
    )
    try:
        response = _OPENER.open(request, timeout=TIMEOUT_SECONDS)
        status = int(getattr(response, "status", response.getcode()))
        if status < 200 or status >= 300:
            raise HTTPError(request.full_url, status, "upstream status", {}, response)
        body = bytearray()
        while True:
            chunk = response.read(min(65536, MAX_RESPONSE_BYTES + 1 - len(body)))
            if not chunk:
                break
            body.extend(chunk)
            if len(body) > MAX_RESPONSE_BYTES:
                raise UNAVAILABLE
    except HTTPError as exc:
        if thread_lookup and exc.code in {403, 404}:
            raise NOT_FOUND from None
        raise UNAVAILABLE from None
    except (URLError, OSError, socket.timeout, TimeoutError):
        raise UNAVAILABLE from None
    try:
        payload = json.loads(bytes(body))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise UNAVAILABLE from None
    if not isinstance(payload, dict):
        raise UNAVAILABLE
    return payload


def _thread(thread_id: str) -> dict[str, Any]:
    if not THREAD_ID.fullmatch(thread_id):
        raise NOT_FOUND
    payload = _read_json(THREAD_PREFIX + thread_id + "?include_archived=true", thread_lookup=True)
    events = payload.get("events")
    if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
        raise UNAVAILABLE
    if any(str(event.get("sensitivity", "")).upper() == "RESTRICTED" for event in events):
        raise NOT_FOUND
    return payload


def _candidate_ids(discovery: dict[str, Any]) -> list[str]:
    candidates: set[str] = set()
    for key in ("history", "open_work"):
        rows = discovery.get(key, [])
        if not isinstance(rows, list):
            raise UNAVAILABLE
        for row in rows:
            if not isinstance(row, dict):
                raise UNAVAILABLE
            value = row.get("thread_id")
            if isinstance(value, str) and THREAD_ID.fullmatch(value):
                candidates.add(value)
    boards = discovery.get("boards", {})
    if not isinstance(boards, dict):
        raise UNAVAILABLE
    for values in boards.values():
        if not isinstance(values, list):
            raise UNAVAILABLE
        for value in values:
            if isinstance(value, str) and THREAD_ID.fullmatch(value):
                candidates.add(value)
    projects = discovery.get("projects", {})
    if not isinstance(projects, dict):
        raise UNAVAILABLE
    for records in projects.values():
        if not isinstance(records, list):
            raise UNAVAILABLE
        for record in records:
            if not isinstance(record, dict):
                raise UNAVAILABLE
            parent = record.get("parent")
            if isinstance(parent, str) and THREAD_ID.fullmatch(parent):
                candidates.add(parent)
    if len(candidates) > MAX_DISCOVERY_THREADS:
        raise UNAVAILABLE
    return sorted(candidates)


def _scrub_blocked(value: Any, blocked: set[str]) -> Any:
    if isinstance(value, list):
        return [_scrub_blocked(item, blocked) for item in value if not (isinstance(item, str) and item in blocked)]
    if isinstance(value, dict):
        return {
            key: _scrub_blocked(item, blocked)
            for key, item in value.items()
            if not (isinstance(item, str) and item in blocked)
        }
    return value


def _discovery() -> dict[str, Any]:
    raw = _read_json(DISCOVERY_PATH)
    allowed: set[str] = set()
    blocked: set[str] = set()
    for thread_id in _candidate_ids(raw):
        try:
            _thread(thread_id)
        except PublicError as exc:
            if exc.status == 404:
                blocked.add(thread_id)
                continue
            raise
        allowed.add(thread_id)

    result = _scrub_blocked(raw, blocked)
    for key in ("history", "open_work"):
        result[key] = [
            row for row in result.get(key, [])
            if isinstance(row, dict) and row.get("thread_id") in allowed
        ]
    result["boards"] = {
        name: [thread_id for thread_id in values if thread_id in allowed]
        for name, values in result.get("boards", {}).items()
    }
    return result


def _json_response(status: int, payload: dict[str, Any]) -> tuple[int, list[tuple[bytes, bytes]], bytes]:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("ascii")),
        (b"cache-control", b"no-store"),
    ]
    return status, headers, body


async def app(scope, receive, send):
    if scope.get("type") != "http":
        return
    try:
        if scope.get("method") != "GET":
            raise PublicError(405, "method_not_allowed", "only GET is available")
        if scope.get("query_string", b""):
            raise BAD_REQUEST
        if b"%" in scope.get("raw_path", b""):
            raise NOT_FOUND
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        if b"authorization" in headers:
            raise BAD_REQUEST
        path = scope.get("path", "")
        if path == "/health/live":
            payload = {"ok": True}
        elif path == "/health/ready":
            _read_json(STATUS_PATH)
            payload = {"ok": True}
        elif path == DISCOVERY_PATH:
            payload = _discovery()
        elif path.startswith(THREAD_PREFIX):
            payload = _thread(path[len(THREAD_PREFIX):])
        else:
            raise NOT_FOUND
        status, response_headers, body = _json_response(200, payload)
    except PublicError as exc:
        status, response_headers, body = _json_response(exc.status, {"detail": {"code": exc.code, "message": exc.message}})
        if exc.status == 405:
            response_headers.append((b"allow", b"GET"))
    await send({"type": "http.response.start", "status": status, "headers": response_headers})
    await send({"type": "http.response.body", "body": body})
