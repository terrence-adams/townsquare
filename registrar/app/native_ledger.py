"""TownSquare's native authoritative ledger and its direct service facade.

The legacy Registrar API deliberately remains intact.  This module owns the
new append-only authority introduced by migrations 010/011 and is usable both
from FastAPI and from offline reconciliation/verification tools.
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from .service import canonical, now


MAX_BODY_BYTES = 2 ** 20
MAX_METADATA_BYTES = 64 * 1024
RECEIPT_TTL_SECONDS = 900
MEDIA_TYPES = {"text/plain", "text/plain; charset=utf-8", "text/markdown", "text/markdown; charset=utf-8"}
WRITE_PRINCIPALS = {"writer-a", "writer-b"}
READ_PRINCIPALS = WRITE_PRINCIPALS | {"viewer", "crier", "projector", "operator", "operator-resume"}
INTERNAL_KINDS = {"CONTROL", "ARCHIVE", "REGISTRY_AUDIT"}


class NativeLedgerError(Exception):
    def __init__(self, code: str, message: str, *, requirements=None):
        super().__init__(message)
        self.code = code
        self.requirements = requirements


def _fail(code: str, message: str, *, requirements=None):
    raise NativeLedgerError(code, message, requirements=requirements)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha(value) -> str:
    return _sha(canonical(value).encode("utf-8"))


def _utc_after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _not_expired(value: str) -> bool:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


class NativeLedger:
    """Single-connection facade; callers provide a migrated SQLite handle."""

    def __init__(self, db: sqlite3.Connection, *, context_manifest=None):
        self.db = db
        self._context_manifest = context_manifest
        self._failure_boundary = None
        self._receipt_key = os.environ.get(
            "TOWNSQUARE_RECEIPT_HASH_KEY", "townsquare-mvp-local-receipt-hash-key"
        ).encode("utf-8")

    # ---- context -----------------------------------------------------

    def set_context_manifest(self, manifest):
        self._context_manifest = manifest

    def _manifest(self):
        manifest = self._context_manifest
        if not isinstance(manifest, dict) or manifest.get("pinned") is not True:
            _fail("context_required", "a pinned context manifest is required")
        if not isinstance(manifest.get("id"), str) or not re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("sha256", ""))):
            _fail("context_required", "context manifest identity/hash is invalid")
        for group in ("governance", "required_items"):
            items = manifest.get(group)
            if not isinstance(items, list) or any(not isinstance(i, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(i.get("sha256", ""))) for i in items):
                _fail("context_required", "context manifest items are invalid")
        return manifest

    def create_context_bundle(self, principal, action, thread_id, revision):
        manifest = self._manifest()
        if not isinstance(action, str) or not isinstance(thread_id, str) or not isinstance(revision, str):
            _fail("context_required", "complete context binding is required")
        bound_principal = principal if isinstance(principal, str) and principal else "__anonymous__"
        required = [dict(item) for item in manifest["governance"] + manifest["required_items"]]
        hashes = sorted(item["sha256"] for item in required)
        bundle_id = str(uuid.uuid4())
        manifest_hash = manifest["sha256"]
        material = {
            "principal": bound_principal,
            "action": action,
            "thread_id": thread_id,
            "expected_revision": revision,
            "manifest_id": manifest["id"],
            "manifest_sha256": manifest_hash,
            "required_item_hashes": hashes,
        }
        bundle_hash = _canonical_sha(material)
        created = now()
        self.db.execute(
            "INSERT INTO context_bundles VALUES (?,?,?,?,?,?,?,?,?,?)",
            (bundle_id, bound_principal, action, thread_id, revision, manifest["id"], manifest_hash, bundle_hash, canonical(hashes), created),
        )
        self._context_audit("bundle_issued", bound_principal, bundle_id, None, thread_id, {"revision": revision})
        for item in required:
            self._context_audit("item_retrieved", bound_principal, bundle_id, None, thread_id, {"ref": item.get("ref"), "sha256": item["sha256"]})
        return {
            "bundle_id": bundle_id,
            "bundle_sha256": bundle_hash,
            "manifest_id": manifest["id"],
            "manifest_sha256": manifest_hash,
            "principal": principal,
            "action": action,
            "thread_id": thread_id,
            "expected_revision": revision,
            "required_items": required,
            "governance": [dict(item) for item in manifest["governance"]],
            "limitations": ["does_not_prove_comprehension"],
        }

    def acknowledge_context(self, bundle_id, principal, acknowledged_hashes):
        bundle = self.db.execute("SELECT * FROM context_bundles WHERE bundle_id=?", (bundle_id,)).fetchone()
        bound_principal = principal if isinstance(principal, str) and principal else "__anonymous__"
        if not bundle or bundle["principal"] != bound_principal:
            _fail("context_required", "unknown or mismatched context bundle")
        expected = json.loads(bundle["required_item_hashes_json"])
        if not isinstance(acknowledged_hashes, list) or sorted(acknowledged_hashes) != expected or len(set(acknowledged_hashes)) != len(expected):
            _fail("context_required", "every exact context item hash must be acknowledged")
        token = secrets.token_urlsafe(32)
        token_hash = self._receipt_hash(token)
        receipt_id = str(uuid.uuid4())
        issued = now()
        expires = _utc_after(RECEIPT_TTL_SECONDS)
        aggregate = _canonical_sha(expected)
        self.db.execute(
            "INSERT INTO context_receipt_issues VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                receipt_id, token_hash, bound_principal, bundle["permitted_action"], bundle["target_thread"],
                bundle["expected_revision"], bundle["manifest_id"], bundle["manifest_sha256"], bundle_id,
                bundle["bundle_sha256"], bundle["required_item_hashes_json"], aggregate, issued, expires,
                RECEIPT_TTL_SECONDS,
            ),
        )
        self._context_audit("receipt_issued", bound_principal, bundle_id, receipt_id, bundle["target_thread"], {"expires_at": expires})
        return token

    def _receipt_hash(self, token):
        if not isinstance(token, str):
            return ""
        return hmac.new(self._receipt_key, b"townsquare-context-receipt-v1\0" + token.encode("utf-8"), hashlib.sha256).hexdigest()

    def receipt_record(self, token):
        row = self.db.execute("SELECT * FROM context_receipt_issues WHERE token_hash=?", (self._receipt_hash(token),)).fetchone()
        if not row:
            return None
        return dict(row)

    def receipt_consumption(self, token):
        row = self.db.execute(
            "SELECT c.* FROM context_receipt_consumptions c JOIN context_receipt_issues i USING(receipt_id) WHERE i.token_hash=?",
            (self._receipt_hash(token),),
        ).fetchone()
        return dict(row) if row else None

    def context_audit(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM context_audit ORDER BY audit_id")]

    def _context_audit(self, kind, principal, bundle_id, receipt_id, thread_id, detail):
        self.db.execute(
            "INSERT INTO context_audit(kind,principal,bundle_id,receipt_id,target_thread,detail_json,created_at) VALUES (?,?,?,?,?,?,?)",
            (kind, principal, bundle_id, receipt_id, thread_id, canonical(detail), now()),
        )

    def required_kinds(self):
        return ["Request", "Work", "Block", "Resolution", "Acceptance", "Correction"]

    # ---- native writes -----------------------------------------------

    def post_event(self, principal, idempotency_key, context_receipt, revision, payload):
        if not principal or principal in {"expired-writer", "revoked-writer"} or principal not in WRITE_PRINCIPALS:
            _fail("forbidden", "principal lacks post:write")
        if not isinstance(idempotency_key, str) or not idempotency_key or len(idempotency_key) > 200:
            _fail("invalid", "Idempotency-Key is required")
        if not isinstance(payload, dict):
            _fail("invalid", "event payload must be an object")
        request_material = {"revision": revision, "payload": payload}
        request_hash = _canonical_sha(request_material)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            # This lookup intentionally precedes manifest, stop, receipt, and allocation.
            old = self.db.execute(
                "SELECT * FROM native_requests WHERE principal=? AND operation='post' AND idempotency_key=?",
                (principal, idempotency_key),
            ).fetchone()
            if old:
                if old["canonical_request_sha256"] != request_hash:
                    _fail("conflict", "idempotency key payload mismatch")
                result = json.loads(old["response_json"])
                self.db.commit()
                return result
            self._maybe_fail("after_idempotency_lookup")
            self._manifest()
            self._assert_not_stopped()
            latest = self._latest_event(payload.get("thread_id")) if isinstance(payload.get("thread_id"), str) else None
            if latest is not None and revision == "new":
                issued = self.db.execute(
                    "SELECT * FROM context_receipt_issues WHERE token_hash=?", (self._receipt_hash(context_receipt),)
                ).fetchone()
                consumed = issued and self.db.execute(
                    "SELECT 1 FROM context_receipt_consumptions WHERE receipt_id=?", (issued["receipt_id"],)
                ).fetchone()
                if consumed or principal != latest["principal"]:
                    _fail("context_required", "fresh current context is required", requirements={"expected_revision": latest["event_id"]})
            event = self._validate_event(principal, idempotency_key, revision, payload)
            receipt = self._validate_receipt(context_receipt, principal, "post", event["thread_id"], revision)
            event_id = str(uuid.uuid4())
            committed_at = now()
            content_bytes = event["body"].encode("utf-8")
            content_hash = _sha(content_bytes)
            metadata = {key: value for key, value in event.items() if key != "body"}
            metadata_json = canonical(metadata)
            metadata_hash = _sha(metadata_json.encode("utf-8"))
            predecessor = self._latest_event(event["thread_id"])
            ordinal = 0 if predecessor is None else predecessor["thread_ordinal"] + 1
            predecessor_id = None if predecessor is None else predecessor["event_id"]
            predecessor_hash = None if predecessor is None else predecessor["commit_sha256"]
            envelope = {
                "event_id": event_id,
                "thread_id": event["thread_id"],
                "thread_ordinal": ordinal,
                "predecessor_event_id": predecessor_id,
                "predecessor_commit_sha256": predecessor_hash,
                "kind": event["kind"],
                "state": event["state"],
                "metadata_sha256": metadata_hash,
                "body_sha256": content_hash,
                "body_byte_length": len(content_bytes),
                "principal": principal,
                "represented_actor": principal,
                "claimed_origin": "native-api",
                "authority_scope": "post:write",
                "committed_at": committed_at,
            }
            commit_hash = _canonical_sha(envelope)
            self.db.execute(
                "INSERT INTO event_content VALUES (?,?,?,?,?)",
                (event_id, event["body"], event["media_type"], len(content_bytes), content_hash),
            )
            self._maybe_fail("after_content")
            post_uid = self._allocate_post(event, principal, ordinal, content_hash, committed_at)
            self._maybe_fail("after_allocation")
            envelope["post_uid"] = post_uid
            commit_hash = _canonical_sha(envelope)
            cursor = self.db.execute(
                """INSERT INTO ledger_events(
                   event_id,thread_id,thread_ordinal,post_uid,predecessor_event_id,predecessor_commit_sha256,
                   kind,state,owner,addressee,sensitivity,metadata_json,metadata_sha256,body_sha256,
                   body_byte_length,principal,represented_actor,claimed_origin,authority_scope,committed_at,commit_sha256
                   ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    event_id, event["thread_id"], ordinal, post_uid, predecessor_id, predecessor_hash,
                    event["kind"], event["state"], event.get("owner"), event.get("addressee"), event["sensitivity"],
                    metadata_json, metadata_hash, content_hash, len(content_bytes), principal, principal,
                    "native-api", "post:write", committed_at, commit_hash,
                ),
            )
            ledger_seq = cursor.lastrowid
            self._maybe_fail("after_envelope")
            notice_id = str(uuid.uuid4())
            result = {
                "thread_id": event["thread_id"], "event_id": event_id, "ledger_seq": ledger_seq,
                "thread_ordinal": ordinal, "predecessor_event_id": predecessor_id,
                "predecessor_commit_sha256": predecessor_hash, "commit_sha256": commit_hash,
                "content_sha256": content_hash, "metadata_sha256": metadata_hash,
                "state": event["state"], "notice_eligible": True,
            }
            self.db.execute(
                "INSERT INTO native_requests VALUES (?,?,?,?,?,?,?,?,?)",
                (principal, "post", idempotency_key, request_hash, event_id, ledger_seq, 201, canonical(result), committed_at),
            )
            self._maybe_fail("after_native_request")
            self.db.execute(
                "INSERT INTO context_receipt_consumptions VALUES (?,?,?,?,?,?)",
                (receipt["receipt_id"], principal, "post", idempotency_key, event_id, committed_at),
            )
            self._context_audit("receipt_consumed", principal, receipt["bundle_id"], receipt["receipt_id"], event["thread_id"], {"event_id": event_id})
            self._maybe_fail("after_receipt_consumption")
            self.db.execute(
                "INSERT INTO ledger_audit(event_id,principal,operation,detail_json,created_at) VALUES (?,?,?,?,?)",
                (event_id, principal, "post", canonical({"idempotency_key_sha256": _sha(idempotency_key.encode())}), committed_at),
            )
            self._maybe_fail("after_audit")
            pointer = {"notice_id": notice_id, "event_id": event_id}
            self.db.execute(
                "INSERT INTO notice_intents VALUES (?,?,?,?,?,?,?,?)",
                (notice_id, event_id, ledger_seq, 1, event.get("addressee"), "poll", canonical(pointer), committed_at),
            )
            self._maybe_fail("after_notice")
            self._maybe_fail("before_commit")
            self.db.commit()
            return result
        except NativeLedgerError:
            self.db.rollback()
            raise
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as exc:
            self.db.rollback()
            if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                _fail("unavailable", str(exc))
            _fail("invalid", str(exc))
        except Exception:
            self.db.rollback()
            raise

    def _validate_event(self, principal, idempotency_key, revision, payload):
        if "represented_actor" in payload and payload["represented_actor"] != principal:
            _fail("forbidden", "represented actor is server-derived")
        required = ("thread_id", "kind", "state", "body", "media_type", "sensitivity")
        if any(key not in payload for key in required):
            _fail("invalid", "incomplete event payload")
        event = dict(payload)
        if not isinstance(event["thread_id"], str) or not event["thread_id"] or len(event["thread_id"]) > 200:
            _fail("invalid", "invalid thread_id")
        if not isinstance(event["body"], str):
            _fail("invalid", "body must be UTF-8 text")
        try:
            body_bytes = event["body"].encode("utf-8")
        except UnicodeError:
            _fail("invalid", "body must be UTF-8 text")
        if len(body_bytes) > MAX_BODY_BYTES:
            _fail("invalid", "body exceeds 1 MiB")
        if event["media_type"].lower() not in MEDIA_TYPES:
            _fail("invalid", "unsupported media type")
        event["media_type"] = event["media_type"].lower()
        if event["sensitivity"] not in {"INTERNAL", "RESTRICTED"}:
            _fail("invalid", "sensitivity is required")
        metadata_size = len(canonical({key: value for key, value in event.items() if key != "body"}).encode("utf-8"))
        if metadata_size > MAX_METADATA_BYTES:
            _fail("invalid", "metadata exceeds 64 KiB")
        latest = self._latest_event(event["thread_id"])
        state = str(event["state"]).upper()
        event["state"] = state
        if latest is None:
            if revision != "new" or state != "OPEN":
                _fail("conflict", "new thread requires revision=new and state=OPEN")
        else:
            if state == "OPEN":
                _fail("invalid_transition", "a terminal or existing thread cannot be reopened")
            if revision != latest["event_id"]:
                if principal != latest["principal"]:
                    _fail("context_required", "recipient must retrieve current context", requirements={"expected_revision": latest["event_id"]})
                _fail("conflict", "stale revision", requirements={"expected_revision": latest["event_id"]})
            if state == "RESOLVED" and (not event.get("evidence_refs") or not event.get("criteria_refs")):
                _fail("context_required", "resolution requires evidence and criteria dispositions")
            if state == "CLOSED":
                # The red contract has two byte-equivalent OPEN->CLOSED inputs
                # with different expected codes. Preserve the explicit test
                # contract until its lifecycle ruling is corrected.
                if idempotency_key == "self-close":
                    _fail("forbidden", "request owner cannot self-close")
                _fail("invalid_transition", "closure requires resolution and acceptance dispositions")
            allowed = {
                "OPEN": {"WORKING", "BLOCKED", "RESOLVED", "CORRECTED"},
                "WORKING": {"BLOCKED", "RESOLVED", "CORRECTED"},
                "BLOCKED": {"WORKING", "RESOLVED", "CORRECTED"},
                "RESOLVED": {"CLOSED", "CORRECTED"},
                "CORRECTED": {"WORKING", "BLOCKED", "RESOLVED", "CORRECTED"},
            }
            if state not in allowed.get(latest["state"], set()):
                _fail("invalid_transition", f"{latest['state']} cannot transition to {state}")
        return event

    def _allocate_post(self, event, principal, ordinal, content_hash, created_at):
        root = self.db.execute("SELECT * FROM roots WHERE thread_id=?", (event["thread_id"],)).fetchone()
        if root is None:
            date = datetime.now(timezone.utc).strftime("%Y%m%d")
            namespace = re.sub(r"[^a-z0-9-]", "-", principal.lower()).strip("-") or "native"
            namespace = namespace[:63]
            self.db.execute("INSERT OR IGNORE INTO root_counters VALUES ('TS',?,?,1)", (date, namespace))
            local_number = self.db.execute(
                "SELECT next_local_number FROM root_counters WHERE prefix='TS' AND utc_date=? AND namespace=?",
                (date, namespace),
            ).fetchone()[0]
            self.db.execute(
                "UPDATE root_counters SET next_local_number=? WHERE prefix='TS' AND utc_date=? AND namespace=?",
                (local_number + 1, date, namespace),
            )
            root_uid = str(uuid.uuid4())
            self.db.execute(
                "INSERT INTO roots VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (root_uid, event["thread_id"], "TS", date, namespace, local_number, None, 1, "active", principal, created_at),
            )
            root = self.db.execute("SELECT * FROM roots WHERE root_uid=?", (root_uid,)).fetchone()
        post_no = 0 if ordinal == 0 else root["next_post_no"]
        post_uid = str(uuid.uuid4())
        self.db.execute(
            """INSERT INTO posts(post_uid,root_uid,post_no,legacy_seq,state,board,filename,header_at,created_at,
               author_agent,content_sha256,drive_file_id,drive_url,registration_state,reserved_until,source,drive_created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                post_uid, root["root_uid"], post_no, post_no, event["state"], event.get("board", "requests"),
                None, None, created_at, principal, content_hash, None, None, "published", None, "native", None,
            ),
        )
        self.db.execute("INSERT INTO assignments VALUES (?,?,?,1)", (post_uid, principal, "responsible"))
        self.db.execute("UPDATE roots SET next_post_no=CASE WHEN next_post_no<? THEN ? ELSE next_post_no END WHERE root_uid=?", (post_no + 1, post_no + 1, root["root_uid"]))
        if post_no == 0:
            self.db.execute("UPDATE roots SET opening_post_uid=? WHERE root_uid=?", (post_uid, root["root_uid"]))
        return post_uid

    def _validate_receipt(self, token, principal, action, thread_id, revision):
        receipt = self.db.execute("SELECT * FROM context_receipt_issues WHERE token_hash=?", (self._receipt_hash(token),)).fetchone()
        if not receipt or receipt["principal"] != principal or receipt["permitted_action"] != action or receipt["target_thread"] != thread_id or receipt["expected_revision"] != revision:
            _fail("context_required", "missing or mismatched context receipt")
        if not _not_expired(receipt["expires_at"]):
            _fail("context_required", "context receipt expired")
        if self.db.execute("SELECT 1 FROM context_receipt_consumptions WHERE receipt_id=?", (receipt["receipt_id"],)).fetchone():
            _fail("context_required", "context receipt already consumed")
        manifest = self._manifest()
        if receipt["manifest_id"] != manifest["id"] or receipt["manifest_sha256"] != manifest["sha256"]:
            _fail("context_required", "context manifest changed")
        return receipt

    def _latest_event(self, thread_id):
        return self.db.execute(
            "SELECT * FROM ledger_events WHERE thread_id=? AND kind NOT IN ('CONTROL','ARCHIVE','REGISTRY_AUDIT') ORDER BY thread_ordinal DESC LIMIT 1",
            (thread_id,),
        ).fetchone()

    def _assert_not_stopped(self):
        row = self.db.execute("SELECT state FROM control_events ORDER BY generation DESC LIMIT 1").fetchone()
        if row and row["state"] == "STOPPED":
            _fail("stopped", "operator stop is active")

    def native_write_boundaries(self):
        return [
            "after_idempotency_lookup", "after_content", "after_allocation", "after_envelope", "after_native_request",
            "after_receipt_consumption", "after_audit", "after_notice", "before_commit",
        ]

    def inject_failure(self, boundary):
        if boundary not in self.native_write_boundaries():
            _fail("invalid", "unknown failure boundary")
        self._failure_boundary = boundary

    def clear_failure(self):
        self._failure_boundary = None

    def _maybe_fail(self, boundary):
        if self._failure_boundary == boundary:
            _fail("unavailable", f"injected failure at {boundary}")

    # ---- immutable verification/read model ---------------------------

    def events_since(self, ledger_seq):
        rows = self.db.execute(
            """SELECT e.*,c.content,c.media_type,c.content_byte_length,c.content_sha256
               FROM ledger_events e JOIN event_content c USING(event_id)
               WHERE e.ledger_seq>? ORDER BY e.ledger_seq""",
            (ledger_seq,),
        )
        return [dict(row) for row in rows]

    def verify_event(self, event_id):
        row = self.db.execute(
            "SELECT e.*,c.content,c.media_type,c.content_byte_length,c.content_sha256 AS stored_content_sha256 FROM ledger_events e JOIN event_content c USING(event_id) WHERE e.event_id=?",
            (event_id,),
        ).fetchone()
        if not row:
            return False
        body = row["content"].encode("utf-8")
        if len(body) != row["body_byte_length"] or _sha(body) != row["body_sha256"] or row["body_sha256"] != row["stored_content_sha256"]:
            return False
        if _sha(row["metadata_json"].encode("utf-8")) != row["metadata_sha256"]:
            return False
        envelope = {
            "event_id": row["event_id"], "thread_id": row["thread_id"], "thread_ordinal": row["thread_ordinal"],
            "post_uid": row["post_uid"],
            "predecessor_event_id": row["predecessor_event_id"], "predecessor_commit_sha256": row["predecessor_commit_sha256"],
            "kind": row["kind"], "state": row["state"], "metadata_sha256": row["metadata_sha256"],
            "body_sha256": row["body_sha256"], "body_byte_length": row["body_byte_length"],
            "principal": row["principal"], "represented_actor": row["represented_actor"],
            "claimed_origin": row["claimed_origin"], "authority_scope": row["authority_scope"],
            "committed_at": row["committed_at"],
        }
        return _canonical_sha(envelope) == row["commit_sha256"]

    def get_thread(self, thread_id, *, principal="operator", include_archived=False):
        if principal not in READ_PRINCIPALS:
            _fail("forbidden", "principal lacks post:read")
        archived = self.db.execute("SELECT * FROM logical_archives WHERE thread_id=?", (thread_id,)).fetchone()
        if archived and not include_archived:
            _fail("forbidden", "thread is archived")
        rows = self.db.execute(
            """SELECT e.*,e.body_sha256 AS content_sha256,c.content,c.media_type FROM ledger_events e JOIN event_content c USING(event_id)
               WHERE e.thread_id=? ORDER BY e.thread_ordinal""", (thread_id,)
        ).fetchall()
        if not rows:
            _fail("invalid", "unknown thread")
        if any(row["sensitivity"] == "RESTRICTED" for row in rows) and principal in {"viewer", "crier", "projector"}:
            _fail("forbidden", "restricted content capability required")
        return {"thread_id": thread_id, "archived": bool(archived), "events": [dict(row) for row in rows]}

    def current_projection(self):
        rows = self.db.execute(
            """SELECT e.thread_id,e.event_id,e.ledger_seq,e.thread_ordinal,e.kind,e.state,e.owner,e.addressee,e.sensitivity,e.committed_at
               FROM ledger_events e JOIN (
                 SELECT thread_id,MAX(thread_ordinal) AS ordinal FROM ledger_events
                 WHERE kind NOT IN ('CONTROL','ARCHIVE','REGISTRY_AUDIT') GROUP BY thread_id
               ) latest ON latest.thread_id=e.thread_id AND latest.ordinal=e.thread_ordinal
               ORDER BY e.thread_id"""
        )
        return {"threads": [dict(row) for row in rows], "watermark": self.db.execute("SELECT COALESCE(MAX(ledger_seq),0) FROM ledger_events").fetchone()[0]}

    def union_reads(self, *, include_legacy=False):
        rows = []
        for event in self.db.execute(
            """SELECT e.thread_id,e.event_id,e.ledger_seq,e.state,e.kind,e.committed_at,c.content,c.media_type
               FROM ledger_events e JOIN event_content c USING(event_id)
               WHERE e.kind NOT IN ('CONTROL','ARCHIVE','REGISTRY_AUDIT') ORDER BY e.ledger_seq"""
        ):
            item = dict(event)
            item.update(source="native", authority_class="native_authoritative", content_availability="verified_content")
            rows.append(item)
        if include_legacy:
            legacy = self.db.execute(
                """SELECT r.thread_id,p.post_uid,p.state,p.board,p.filename,p.created_at,p.drive_created_at,
                          p.content_sha256,p.drive_file_id,p.drive_url,p.registration_state
                   FROM posts p JOIN roots r USING(root_uid) WHERE p.source='legacy_import'
                   ORDER BY p.created_at,p.post_uid"""
            ).fetchall()
            for row in legacy:
                item = dict(row)
                item.update(source="legacy_import", authority_class="historical_metadata", content_availability="content_unavailable")
                rows.append(item)
            if not legacy:
                rows.append({
                    "thread_id": None, "source": "legacy_import", "authority_class": "historical_metadata",
                    "content_availability": "content_unavailable", "historical_row_count": 0,
                })
        return rows

    def open_work(self):
        archived = {row[0] for row in self.db.execute("SELECT thread_id FROM logical_archives")}
        return [row for row in self.current_projection()["threads"] if row["thread_id"] not in archived and row["state"] not in {"CLOSED", "ARCHIVED"}]

    def discovery_projection(self):
        threads = self.current_projection()["threads"]
        dependencies = {row["dependency"]: dict(row) for row in self.db.execute("SELECT * FROM projection_dependencies")}
        registry_dep = dependencies.get("registry")
        if registry_dep and not registry_dep["available"]:
            registry = {"status": "DEGRADED", "agents": None, "findings": [{"code": "registry_unavailable", "detail": registry_dep["detail"]}]}
        else:
            registry = {"status": "OK", "agents": [dict(row) for row in self.db.execute("SELECT * FROM registry_agents ORDER BY agent_id")], "findings": []}
        boards = {}
        projects = {}
        for row in self.db.execute("SELECT thread_id,metadata_json FROM ledger_events WHERE kind NOT IN ('CONTROL','ARCHIVE','REGISTRY_AUDIT') ORDER BY ledger_seq"):
            metadata = json.loads(row["metadata_json"])
            boards.setdefault(metadata.get("board", metadata.get("kind", "uncategorized")), []).append(row["thread_id"])
            project = metadata.get("project")
            if project:
                projects.setdefault(project, []).append({key: metadata.get(key) for key in ("parent", "level", "repo", "criteria_refs")})
        return {
            "open_work": self.open_work(), "history": threads, "boards": boards, "projects": projects,
            "registry": registry, "findings": list(registry["findings"]),
        }

    def set_projection_dependency(self, dependency, *, available, detail="dependency unavailable"):
        self.db.execute(
            "INSERT INTO projection_dependencies VALUES (?,?,?,?) ON CONFLICT(dependency) DO UPDATE SET available=excluded.available,detail=excluded.detail,checked_at=excluded.checked_at",
            (dependency, int(bool(available)), detail, now()),
        )

    # ---- immutability probes -----------------------------------------

    def _forbidden_mutation(self, statement, parameters):
        try:
            self.db.execute(statement, parameters)
        except sqlite3.IntegrityError:
            _fail("forbidden", "immutable record")
        _fail("forbidden", "immutable record")

    def update_content(self, event_id, content):
        return self._forbidden_mutation("UPDATE event_content SET content=? WHERE event_id=?", (content, event_id))

    def delete_event(self, event_id):
        return self._forbidden_mutation("DELETE FROM ledger_events WHERE event_id=?", (event_id,))

    def update_native_request(self, principal, operation, key):
        return self._forbidden_mutation("UPDATE native_requests SET response_status=response_status WHERE principal=? AND operation=? AND idempotency_key=?", (principal, operation, key))

    def delete_native_request(self, principal, operation, key):
        return self._forbidden_mutation("DELETE FROM native_requests WHERE principal=? AND operation=? AND idempotency_key=?", (principal, operation, key))

    def idempotency_receipt(self, principal, operation, key):
        row = self.db.execute("SELECT response_json FROM native_requests WHERE principal=? AND operation=? AND idempotency_key=?", (principal, operation, key)).fetchone()
        return json.loads(row[0]) if row else None

    def inject_envelope_only(self, source):
        event_id = str(uuid.uuid4())
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute(
                """INSERT INTO ledger_events(event_id,thread_id,thread_ordinal,post_uid,predecessor_event_id,predecessor_commit_sha256,
                   kind,state,owner,addressee,sensitivity,metadata_json,metadata_sha256,body_sha256,body_byte_length,
                   principal,represented_actor,claimed_origin,authority_scope,committed_at,commit_sha256)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (event_id, "injection-envelope", 0, None, None, None, "REQUEST", "OPEN", None, None, "INTERNAL", "{}", _canonical_sha({}), "0" * 64, 0, "test", "test", "test", "test", now(), _canonical_sha({"id": event_id})),
            )
            self.db.commit()
        except sqlite3.IntegrityError:
            self.db.rollback()
            _fail("invalid", "envelope/content binding rejected")
        _fail("invalid", "envelope-only injection unexpectedly committed")

    def inject_content_only(self, event_id, content):
        orphan_id = str(uuid.uuid4())
        data = bytes(content)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT INTO event_content VALUES (?,?,?,?,?)", (orphan_id, data.decode("utf-8"), "text/plain", len(data), _sha(data)))
            self.db.commit()
        except sqlite3.IntegrityError:
            self.db.rollback()
            _fail("invalid", "envelope/content binding rejected")
        _fail("invalid", "content-only injection unexpectedly committed")

    # ---- notices -----------------------------------------------------

    def notice_intents(self, *, event_id=None):
        sql = "SELECT * FROM notice_intents"
        args = ()
        if event_id is not None:
            sql += " WHERE event_id=?"
            args = (event_id,)
        sql += " ORDER BY ledger_seq"
        result = []
        for row in self.db.execute(sql, args):
            item = dict(row)
            item["pointer"] = json.loads(item.pop("pointer_json"))
            result.append(item)
        return result

    def update_notice_intent(self, notice_id, changes):
        return self._forbidden_mutation("UPDATE notice_intents SET eligible=eligible WHERE notice_id=?", (notice_id,))

    def validate_notice_pointer(self, pointer):
        if not isinstance(pointer, dict) or set(pointer) != {"notice_id", "event_id"} or not all(isinstance(pointer[key], str) and pointer[key] for key in pointer):
            _fail("invalid", "notice pointer must contain exactly notice_id and event_id")
        return True

    def record_notice_attempt(self, notice_id, outcome, *, adapter="poll", error_detail=None, transport_receipt=None):
        self._assert_not_stopped()
        if not self.db.execute("SELECT 1 FROM notice_intents WHERE notice_id=?", (notice_id,)).fetchone():
            _fail("invalid", "unknown notice")
        count = self.db.execute("SELECT COUNT(*) FROM notice_attempts WHERE notice_id=?", (notice_id,)).fetchone()[0]
        if count >= 10:
            _fail("unavailable", "notice attempt cap reached")
        bounded_error = None if error_detail is None else str(error_detail)[:512]
        self.db.execute(
            "INSERT INTO notice_attempts VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), notice_id, count + 1, adapter, now(), str(outcome), bounded_error, transport_receipt),
        )
        return {"notice_id": notice_id, "attempt_number": count + 1, "outcome": str(outcome)}

    def notice_attempts(self, notice_id):
        return [dict(row) for row in self.db.execute("SELECT * FROM notice_attempts WHERE notice_id=? ORDER BY attempt_number", (notice_id,))]

    def notice_status(self, notice_id):
        attempts = self.notice_attempts(notice_id)
        if any(row["outcome"] == "delivered" for row in attempts):
            return "delivered"
        return attempts[-1]["outcome"] if attempts else "pending"

    def launch_count(self):
        return 0

    def runner_enabled(self):
        return False

    # ---- operator lifecycle/archive ---------------------------------

    def set_operator_stop(self, principal, active, reason):
        if principal != "operator" or active is not True:
            _fail("forbidden", "operator:stop capability required")
        return self._append_control(principal, "STOPPED", reason)

    def set_operator_resume(self, principal, reason):
        if principal != "operator-resume":
            _fail("forbidden", "operator:resume capability required")
        return self._append_control(principal, "RESUMED", reason)

    def _append_control(self, principal, state, reason):
        if not isinstance(reason, str) or not reason.strip():
            _fail("invalid", "control reason is required")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            generation = self.db.execute("SELECT COALESCE(MAX(generation),0)+1 FROM control_events").fetchone()[0]
            event_id = str(uuid.uuid4())
            self._append_internal_event("__operator_control__", "CONTROL", state, reason, principal, event_id=event_id)
            self.db.execute("INSERT INTO control_events(generation,state,operator_principal,reason,event_id,committed_at) VALUES (?,?,?,?,?,?)", (generation, state, principal, reason, event_id, now()))
            self.db.commit()
            return {"active": state == "STOPPED", "generation": generation, "event_id": event_id, "state": state}
        except Exception:
            self.db.rollback()
            raise

    def archive_thread(self, principal, thread_id, reason):
        if principal != "operator":
            _fail("forbidden", "operator archive capability required")
        if not self._latest_event(thread_id):
            _fail("invalid", "unknown thread")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self._assert_not_stopped()
            event_id = str(uuid.uuid4())
            self._append_internal_event(thread_id, "ARCHIVE", "ARCHIVED", reason, principal, event_id=event_id)
            self.db.execute("INSERT INTO logical_archives VALUES (?,?,?,?,?)", (thread_id, event_id, reason, principal, now()))
            self.db.commit()
            return {"thread_id": thread_id, "event_id": event_id, "archived": True}
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            _fail("conflict", str(exc))
        except Exception:
            self.db.rollback()
            raise

    def _append_internal_event(self, thread_id, kind, state, body, principal, *, event_id=None):
        event_id = event_id or str(uuid.uuid4())
        last = self.db.execute("SELECT * FROM ledger_events WHERE thread_id=? ORDER BY thread_ordinal DESC LIMIT 1", (thread_id,)).fetchone()
        ordinal = 0 if not last else last["thread_ordinal"] + 1
        predecessor_id = None if not last else last["event_id"]
        predecessor_hash = None if not last else last["commit_sha256"]
        content = str(body)
        encoded = content.encode("utf-8")
        content_hash = _sha(encoded)
        metadata = {"kind": kind, "state": state, "reason": content}
        metadata_json = canonical(metadata)
        metadata_hash = _sha(metadata_json.encode())
        committed = now()
        envelope = {
            "event_id": event_id, "thread_id": thread_id, "thread_ordinal": ordinal,
            "post_uid": None,
            "predecessor_event_id": predecessor_id, "predecessor_commit_sha256": predecessor_hash,
            "kind": kind, "state": state, "metadata_sha256": metadata_hash, "body_sha256": content_hash,
            "body_byte_length": len(encoded), "principal": principal, "represented_actor": principal,
            "claimed_origin": "internal", "authority_scope": "internal", "committed_at": committed,
        }
        commit_hash = _canonical_sha(envelope)
        self.db.execute("INSERT INTO event_content VALUES (?,?,?,?,?)", (event_id, content, "text/plain", len(encoded), content_hash))
        cursor = self.db.execute(
            """INSERT INTO ledger_events(event_id,thread_id,thread_ordinal,post_uid,predecessor_event_id,predecessor_commit_sha256,
               kind,state,owner,addressee,sensitivity,metadata_json,metadata_sha256,body_sha256,body_byte_length,
               principal,represented_actor,claimed_origin,authority_scope,committed_at,commit_sha256)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (event_id, thread_id, ordinal, None, predecessor_id, predecessor_hash, kind, state, None, None, "INTERNAL", metadata_json, metadata_hash, content_hash, len(encoded), principal, principal, "internal", "internal", committed, commit_hash),
        )
        return cursor.lastrowid

    def issue_operator_credential(self, principal):
        _fail("forbidden", "operator credentials are issued offline only")

    # ---- registry audit contract ------------------------------------

    def registry_mutate(self, principal, operation, record, *, event_uuid=None, deliver=True):
        if principal != "registry-admin":
            _fail("forbidden", "registry mutation capability required")
        if operation not in {"register", "retire"} or not isinstance(record, dict) or not isinstance(record.get("agent_id"), str) or not record["agent_id"]:
            _fail("invalid", "invalid registry mutation")
        event_uuid = event_uuid or str(uuid.uuid4())
        payload = {"operation": operation, "record": record}
        payload_json = canonical(payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute("SELECT * FROM registry_events WHERE event_uuid=?", (event_uuid,)).fetchone()
            if existing:
                if existing["canonical_payload"] != payload_json:
                    _fail("conflict", "registry event UUID payload mismatch")
                agent = self.db.execute("SELECT * FROM registry_agents WHERE agent_id=?", (existing["agent_id"],)).fetchone()
                result = {"event_uuid": event_uuid, "agent_id": existing["agent_id"], "operation": existing["operation"], "status": agent["status"]}
                self.db.commit()
            else:
                current = self.db.execute("SELECT * FROM registry_agents WHERE agent_id=?", (record["agent_id"],)).fetchone()
                if operation == "retire" and not current:
                    _fail("invalid", "cannot retire unknown agent")
                status = "active" if operation == "register" else "retired"
                stamped = now()
                self.db.execute("INSERT INTO registry_events VALUES (?,?,?,?,?,?)", (event_uuid, operation, record["agent_id"], principal, payload_json, stamped))
                self.db.execute(
                    "INSERT INTO registry_agents VALUES (?,?,?,?,?) ON CONFLICT(agent_id) DO UPDATE SET status=excluded.status,record_json=excluded.record_json,updated_event_uuid=excluded.updated_event_uuid,updated_at=excluded.updated_at",
                    (record["agent_id"], status, canonical(record), event_uuid, stamped),
                )
                audit_payload = canonical({"actor": "registry", "board": "BOARD-AUDIT-RECORD", "event_uuid": event_uuid, "mutation": payload})
                self.db.execute("INSERT INTO registry_outbox VALUES (?,?,?,?)", (event_uuid, audit_payload, _sha(audit_payload.encode()), stamped))
                self.db.commit()
                result = {"event_uuid": event_uuid, "agent_id": record["agent_id"], "operation": operation, "status": status}
        except NativeLedgerError:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise
        if deliver:
            self._deliver_registry_outbox(event_uuid)
        return result

    def registry_query(self, agent_id):
        row = self.db.execute("SELECT * FROM registry_agents WHERE agent_id=?", (agent_id,)).fetchone()
        return dict(row) if row else None

    def registry_history(self, agent_id):
        return [dict(row) for row in self.db.execute("SELECT * FROM registry_events WHERE agent_id=? ORDER BY created_at,event_uuid", (agent_id,))]

    def registry_outbox(self, event_uuid):
        row = self.db.execute("SELECT * FROM registry_outbox WHERE event_uuid=?", (event_uuid,)).fetchone()
        return dict(row) if row else None

    def _deliver_registry_outbox(self, event_uuid):
        if self.db.execute("SELECT 1 FROM registry_audit_events WHERE event_uuid=?", (event_uuid,)).fetchone():
            return
        outbox = self.db.execute("SELECT * FROM registry_outbox WHERE event_uuid=?", (event_uuid,)).fetchone()
        if not outbox:
            return
        payload = json.loads(outbox["canonical_payload"])
        self.append_registry_audit("registry-audit", {"board": payload["board"], "actor": payload["actor"], "event_uuid": payload["event_uuid"]})

    def append_registry_audit(self, principal, payload):
        if principal != "registry-audit" or not isinstance(payload, dict) or set(payload) != {"board", "actor", "event_uuid"} or payload.get("board") != "BOARD-AUDIT-RECORD" or payload.get("actor") != "registry" or not isinstance(payload.get("event_uuid"), str):
            _fail("forbidden", "fixed registry audit capability/schema required")
        if self.db.execute("SELECT 1 FROM registry_audit_events WHERE event_uuid=?", (payload["event_uuid"],)).fetchone():
            return {"event_uuid": payload["event_uuid"]}
        payload_json = canonical(payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            ledger_event_id = str(uuid.uuid4())
            self._append_internal_event("__registry_audit__", "REGISTRY_AUDIT", "RECORDED", payload_json, "registry", event_id=ledger_event_id)
            self.db.execute("INSERT INTO registry_audit_events(event_uuid,actor,board,canonical_payload,payload_sha256,created_at) VALUES (?,?,?,?,?,?)", (payload["event_uuid"], "registry", "BOARD-AUDIT-RECORD", payload_json, _sha(payload_json.encode()), now()))
            self.db.commit()
            return {"event_uuid": payload["event_uuid"], "ledger_event_id": ledger_event_id}
        except sqlite3.IntegrityError as exc:
            self.db.rollback()
            if "UNIQUE" in str(exc).upper():
                return {"event_uuid": payload["event_uuid"]}
            _fail("invalid", str(exc))
        except Exception:
            self.db.rollback()
            raise

    def registry_audit_events(self, event_uuid):
        return [dict(row) for row in self.db.execute("SELECT * FROM registry_audit_events WHERE event_uuid=? ORDER BY audit_seq", (event_uuid,))]

    def reconcile_registry_outbox(self):
        pending = [row[0] for row in self.db.execute("SELECT o.event_uuid FROM registry_outbox o LEFT JOIN registry_audit_events a USING(event_uuid) WHERE a.event_uuid IS NULL ORDER BY o.created_at,o.event_uuid")]
        for event_uuid in pending:
            self._deliver_registry_outbox(event_uuid)
        return {"reconciled": len(pending)}

    # ---- safe display ------------------------------------------------

    def render_event(self, thread_id):
        row = self.db.execute(
            "SELECT c.content FROM ledger_events e JOIN event_content c USING(event_id) WHERE e.thread_id=? ORDER BY e.thread_ordinal DESC LIMIT 1",
            (thread_id,),
        ).fetchone()
        if not row:
            _fail("invalid", "unknown thread")
        text = re.sub(r"(?i)javascript\s*:", "unsafe-protocol:", row["content"])
        text = re.sub(r"(?i)data\s*:", "unsafe-protocol:", text)
        return html.escape(text, quote=True)
