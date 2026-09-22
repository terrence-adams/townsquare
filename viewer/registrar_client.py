#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""
Read-only HTTP client for the Town Registrar API.

READ-ONLY BY DESIGN. Every function here issues a GET against one of the
Registrar's read endpoints. The write surface (`/v1/roots/reserve`,
`/v1/posts/{uid}/publication`, `/v1/verifications/...`, `/v1/import-runs`)
is deliberately absent from this module, and the viewer's credential carries
only `post:read` — so "the viewer cannot write" is enforced by the Registrar's
own scope check, not by a promise this code has to keep. Same posture the
Crier takes toward the ledger.

Configuration is entirely environment-driven — see env.example and README.md.
"""
from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st

# ---------------------------------------------------------------- configuration
# The Registrar's Compose service name on the shared `registrar-internal`
# network. Never 127.0.0.1: the viewer is a sibling container, not a host
# process, and the Registrar's own published port is loopback-only by design.
BASE_URL = os.environ.get("REGISTRAR_BASE_URL", "http://registrar:8790").rstrip("/")

# (connect, read). The Registrar is one Uvicorn worker over local SQLite; a
# read that has not answered in 15s means something is wrong, not slow.
TIMEOUT = (3.05, 15.0)

# ---------------------------------------------------------------- API constants
# Mirrors of values the Registrar enforces. Kept here so the UI can offer exact
# filter values without a schema endpoint to discover them from. If a migration
# widens one of these CHECK constraints, this list is what goes stale.
REGISTRATION_STATES = (
    "reserved",
    "published",
    "drive_verified",
    "abandoned",
    "legacy",
    "conflict",
)
ASSIGNMENT_ROLES = ("responsible", "requester", "assignee", "reviewer", "observer")
RECONCILIATION_STATUSES = (
    "missing-publication",
    "legacy-collision",
    "unresolved-responsibility",
    "artifacts",
)

# `GET /v1/posts` is `limit: int = Query(100, ge=1, le=200)` with no cursor
# parameter implemented (design §7 specifies one; main.py does not have it yet).
# 200 rows is therefore a hard ceiling per call, and the live corpus is ~1,070
# posts — see sweep_posts() for how this module gets past that.
API_MAX_LIMIT = 200

POST_COLUMNS = (
    "thread_id",
    "post_no",
    "board",
    "state",
    "registration_state",
    "author_agent",
    "created_at",
    "filename",
    "drive_url",
    "source",
    "legacy_seq",
    "post_uid",
    "root_uid",
    "drive_file_id",
    "content_sha256",
    "header_at",
    "reserved_until",
    "drive_created_at",
)


class RegistrarError(RuntimeError):
    """A read call did not produce a usable answer. Never carries the credential."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- transport
def _read_token() -> str:
    """Resolve the bearer credential. File first, matching the Registrar's own
    Docker-secret pattern; env second for local development; never a literal."""
    path = os.environ.get("REGISTRAR_API_TOKEN_FILE")
    if path:
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read().strip()
        except OSError as exc:
            raise RegistrarError(
                f"Cannot read REGISTRAR_API_TOKEN_FILE ({exc.strerror})."
            ) from None
    token = os.environ.get("REGISTRAR_API_TOKEN", "").strip()
    if token:
        return token
    try:  # st.secrets raises when no secrets.toml exists at all.
        return str(st.secrets.get("registrar_api_token", "")).strip()
    except Exception:
        return ""


@st.cache_resource
def _session() -> requests.Session:
    """One connection pool for the whole server process."""
    session = requests.Session()
    session.headers.update(
        {"Accept": "application/json", "User-Agent": "townsquare-viewer/1"}
    )
    return session


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    token = _read_token()
    if not token:
        raise RegistrarError(
            "No Registrar credential configured. Set REGISTRAR_API_TOKEN_FILE "
            "(preferred) or REGISTRAR_API_TOKEN."
        )
    clean = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    try:
        # The credential goes in a header, per request — never in the URL, where
        # it would land in access logs, referrers, and exception strings.
        response = _session().get(
            BASE_URL + path,
            params=clean,
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        # `from None` so the chained traceback (which holds the prepared
        # request, and therefore the Authorization header) never reaches the
        # browser via Streamlit's error display.
        raise RegistrarError(f"Cannot reach the Registrar at {BASE_URL}: {exc}") from None
    if response.status_code in (401, 403):
        raise RegistrarError(
            "The Registrar rejected the viewer credential (HTTP "
            f"{response.status_code}). It must be a live token with the "
            "post:read scope.",
            response.status_code,
        )
    if response.status_code == 404:
        raise RegistrarError("No such record.", 404)
    if response.status_code >= 400:
        raise RegistrarError(
            f"Registrar returned HTTP {response.status_code}: {response.text[:200]}",
            response.status_code,
        )
    try:
        return response.json()
    except ValueError:
        raise RegistrarError("Registrar returned a non-JSON body.") from None


# ---------------------------------------------------------------- read calls
# Caching note: the Registrar is the source of truth and the corpus is static
# between imports, so a short TTL is plenty and keeps the sidebar health check
# from hammering one Uvicorn worker on every widget interaction. Bounded
# max_entries so a user cycling filters cannot grow the cache without limit.
@st.cache_data(ttl="30s", max_entries=4, show_spinner=False)
def health() -> dict[str, Any]:
    """`/health/ready` — schema version plus the SQLite pragma assertions.

    Returns a UI-shaped dict rather than raising, because the health panel has
    to be able to render the bad news too.
    """
    try:
        payload = _get("/health/ready")
        return {"ok": True, "detail": payload}
    except RegistrarError as exc:
        return {"ok": False, "detail": str(exc), "status": exc.status}


@st.cache_data(ttl="30s", max_entries=4, show_spinner=False)
def live() -> bool:
    try:
        return bool(_get("/health/live").get("ok"))
    except RegistrarError:
        return False


@st.cache_data(ttl="60s", max_entries=64, show_spinner=False)
def list_posts(
    *,
    assigned_to: str | None = None,
    role: str | None = None,
    state: str | None = None,
    board: str | None = None,
    registration_state: str | None = None,
    root: str | None = None,
    limit: int = API_MAX_LIMIT,
) -> list[dict[str, Any]]:
    """`GET /v1/posts`. Ordered (created_at, post_uid); capped at API_MAX_LIMIT."""
    params = {
        "assigned_to": assigned_to,
        "role": role,
        "state": state,
        "board": board,
        "registration_state": registration_state,
        "root": root,
        "limit": min(int(limit), API_MAX_LIMIT),
    }
    return list(_get("/v1/posts", params).get("posts", []))


@st.cache_data(ttl="60s", max_entries=32, show_spinner=False)
def get_root(thread_id: str) -> dict[str, Any]:
    """`GET /v1/roots/{thread_id}`. Keys on thread_id, not root_uid."""
    return _get("/v1/roots/" + quote(thread_id, safe=""))


@st.cache_data(ttl="60s", max_entries=32, show_spinner=False)
def get_post(post_uid: str) -> dict[str, Any]:
    """`GET /v1/posts/{post_uid}`."""
    return _get("/v1/posts/" + quote(post_uid, safe=""))


@st.cache_data(ttl="60s", max_entries=32, show_spinner=False)
def get_aliases(alias: str) -> dict[str, Any]:
    """`GET /v1/aliases/{alias}` — `{alias, ambiguous, matches[]}`.

    The route is declared `{alias:path}` precisely because aliases are legacy
    filenames: they carry spaces, em dashes, and `#`. Everything but `/` is
    percent-encoded here so a `#` is sent as data rather than read as a
    fragment and dropped before it ever reaches the server.
    """
    return _get("/v1/aliases/" + quote(alias, safe="/"))


@st.cache_data(ttl="60s", max_entries=32, show_spinner=False)
def get_assignments(agent_id: str, active: bool = True) -> list[dict[str, Any]]:
    """`GET /v1/assignments/{agent_id}`."""
    payload = _get(
        "/v1/assignments/" + quote(agent_id, safe=""),
        {"active": str(bool(active)).lower()},
    )
    return list(payload.get("assignments", []))


@st.cache_data(ttl="60s", max_entries=8, show_spinner=False)
def reconciliation(status: str) -> dict[str, Any]:
    """`GET /v1/reconciliation?status=...`.

    Three of the four statuses answer with `posts`; `unresolved-responsibility`
    answers with `observations` and `artifacts` with `artifacts`. The caller
    gets the raw payload and picks the key it expects.
    """
    return _get("/v1/reconciliation", {"status": status})


def reconciliation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Unwrap a reconciliation payload, whichever key this status answers under."""
    for key in ("posts", "observations", "artifacts"):
        if key in payload:
            return list(payload[key] or [])
    return []


# ---------------------------------------------------------------- corpus sweep
@st.cache_data(ttl="60s", max_entries=16, show_spinner="Reading the Registrar…")
def sweep_posts(
    *,
    assigned_to: str | None = None,
    role: str | None = None,
    state: str | None = None,
    board: str | None = None,
    registration_state: str | None = None,
    root: str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Union `GET /v1/posts` across partitions to see past the 200-row cap.

    WHY this exists: the read API implements `limit` (max 200) but not the
    cursor pagination design §7 specifies, so no single call can enumerate a
    1,070-post corpus. Partitioning on a closed enum the Registrar itself
    enforces — `registration_state` — turns one saturated call into six
    independent 200-row windows, and any window that still comes back full is
    re-queried per board. Partitions that saturate even then are reported
    rather than silently truncated, because a dashboard that quietly drops rows
    is worse than one that admits it cannot see them all.

    Returns `(rows, saturated)` where `saturated` names every partition that
    returned exactly API_MAX_LIMIT rows and so may be incomplete.
    """
    base = {"assigned_to": assigned_to, "role": role, "state": state, "root": root}
    reg_values = [registration_state] if registration_state else list(REGISTRATION_STATES)

    rows: dict[str, dict[str, Any]] = {}
    seen: set[tuple[str, str | None]] = set()
    full: set[tuple[str, str | None]] = set()
    subdivided: set[str] = set()

    def run(reg: str, brd: str | None) -> None:
        if (reg, brd) in seen:
            return
        seen.add((reg, brd))
        batch = list_posts(**base, registration_state=reg, board=brd, limit=API_MAX_LIMIT)
        rows.update({r["post_uid"]: r for r in batch})
        if len(batch) == API_MAX_LIMIT:
            full.add((reg, brd))

    for value in reg_values:
        run(value, board)

    # Subdivide saturated windows by the boards observed so far, repeating
    # while newly observed boards keep appearing. Bounded at three rounds: this
    # is a dashboard, not a crawler, and each round costs real API calls.
    if board is None:
        for _round in range(3):
            boards = sorted({r["board"] for r in rows.values() if r.get("board")})
            targets = [reg for reg, brd in full if brd is None]
            pending = [
                (reg, name)
                for reg in targets
                for name in boards
                if (reg, name) not in seen
            ]
            if not pending:
                break
            for reg, name in pending:
                run(reg, name)
                subdivided.add(reg)

    saturated = sorted(
        f"registration_state={reg}" + (f", board={brd}" if brd else "")
        for reg, brd in full
        # A window that was successfully broken up by board is no longer the
        # thing that truncated; only its still-full children are.
        if brd is not None or reg not in subdivided
    )
    ordered = sorted(
        rows.values(), key=lambda r: (r.get("created_at") or "", r.get("post_uid") or "")
    )
    return ordered, saturated
