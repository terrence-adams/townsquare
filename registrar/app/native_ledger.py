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
READ_PRINCIPALS = {"writer-a", "writer-b", "reviewer", "viewer", "crier", "projector", "operator", "operator-resume"}
NOTICE_READ_PRINCIPALS = {"viewer", "crier", "projector", "operator"}
INTERNAL_KINDS = {"CONTROL", "ARCHIVE", "REGISTRY_AUDIT"}
TERMINAL_STATES = {"CLOSED", "CANCELLED"}
REQUEST_STATES = {"OPEN", "WORKING", "BLOCKED", "RESOLVED", "CLOSED", "CANCELLED"}
ACTION_CAPABILITIES = {
    "OPEN": "request:open", "WORKING": "request:work", "BLOCKED": "request:block",
    "RESOLVED": "request:resolve", "CLOSED": "request:accept", "CANCELLED": "request:cancel",
}


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


def _manifest_content_sha(manifest) -> str:
    return _canonical_sha({name: value for name, value in manifest.items() if name != "sha256"})


def _jsonable(value):
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, (set, tuple)):
        return sorted(_jsonable(item) for item in value)
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _utc_after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _not_expired(value: str) -> bool:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) > datetime.now(timezone.utc)
    except (TypeError, ValueError):
        return False


def _load_key_file(path_name, key_id_name, label, *, require_explicit_id=True):
    path = os.environ.get(path_name)
    key_id = os.environ.get(key_id_name)
    if not path or not os.path.isfile(path):
        raise RuntimeError(f"{label} key file is required")
    try:
        with open(path, "rb") as handle:
            key = handle.read()
    except OSError as exc:
        raise RuntimeError(f"{label} key file is unreadable") from exc
    if len(key) < 32:
        raise RuntimeError(f"{label} key must contain at least 32 bytes")
    if not key_id:
        if require_explicit_id:
            raise RuntimeError(f"{label} key id is required")
        key_id = "sha256:" + _sha(key)
    return key_id, key


def _authority_proof_mac(proof, key):
    material = {name: value for name, value in proof.items() if name != "signature"}
    return hmac.new(key, canonical(_jsonable(material)).encode("utf-8"), hashlib.sha256).hexdigest()


def _parse_utc(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def ensure_receipt_key_at_startup():
    _load_key_file(
        "TOWNSQUARE_RECEIPT_HASH_KEY_FILE", "TOWNSQUARE_RECEIPT_HASH_KEY_ID", "receipt hash",
        require_explicit_id=False,
    )


class NativeLedger:
    """Single-connection facade; callers provide a migrated SQLite handle."""

    def __init__(self, db: sqlite3.Connection, *, context_manifest=None, governance_authority=None):
        self.db = db
        self._context_manifest = context_manifest
        self._failure_boundary = None
        self._receipt_key_id, self._receipt_key = _load_key_file(
            "TOWNSQUARE_RECEIPT_HASH_KEY_FILE", "TOWNSQUARE_RECEIPT_HASH_KEY_ID", "receipt hash",
            require_explicit_id=False,
        )
        self._governance_authority = None
        if governance_authority is not None:
            self.set_authority_proof(governance_authority)

    # ---- context -----------------------------------------------------

    def set_context_manifest(self, manifest):
        self._context_manifest = manifest

    def set_authority_proof(self, proof):
        """Verify one resolver-produced adoption proof against a pinned key."""
        if not isinstance(proof, dict):
            _fail("context_required", "authenticated authority proof is required")
        key_id, key = _load_key_file(
            "TOWNSQUARE_AUTHORITY_RESOLVER_KEY_FILE", "TOWNSQUARE_AUTHORITY_RESOLVER_KEY_ID", "authority resolver"
        )
        signature = proof.get("signature")
        if proof.get("schema") != "townsquare-authority-proof-v1" or proof.get("resolver_key_id") != key_id:
            _fail("context_required", "authority proof trust binding is invalid")
        if not isinstance(signature, str) or not hmac.compare_digest(signature, _authority_proof_mac(proof, key)):
            _fail("context_required", "authority proof signature is invalid")
        self._governance_authority = _jsonable(proof)

    def clear_authority_proof(self):
        """Drop resolver evidence for fail-closed diagnostics and rotation."""
        self._governance_authority = None

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
        required, contents = self._context_items(bound_principal, action, thread_id, revision, manifest)
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
        for ordinal, item in enumerate(required):
            self.db.execute(
                "INSERT INTO context_bundle_items VALUES (?,?,?,?,?,?,?)",
                (bundle_id, item["item_id"], ordinal, item["ref"], item["source"], contents[item["item_id"]], item["sha256"]),
            )
            self._context_audit("required_item_selected", bound_principal, bundle_id, None, thread_id, {"item_id": item["item_id"], "ref": item["ref"], "source": item["source"], "sha256": item["sha256"]})
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

    def _context_items(self, principal, action, thread_id, revision, manifest=None):
        manifest = manifest or self._manifest()
        entries = []
        for item in manifest["governance"]:
            entries.append(("governance", str(item.get("ref", "governance")), _jsonable(item)))
        for item in manifest["required_items"]:
            entries.append(("operator_note", str(item.get("ref", "operator-note")), _jsonable(item)))
        authority = _jsonable(self._governance_authority)
        scope = {
            "action": action, "principal": principal, "target_thread": thread_id,
            "expected_revision": revision, "governance_authority": authority,
            "control_generation": self.db.execute("SELECT COALESCE(MAX(generation),0) FROM control_events").fetchone()[0],
        }
        entries.append(("scope", f"scope:{action}:{thread_id}", scope))
        latest = self._latest_event(thread_id)
        if latest:
            metadata = json.loads(latest["metadata_json"])
            snapshot = {
                "event_id": latest["event_id"], "commit_sha256": latest["commit_sha256"],
                "state": latest["state"], "kind": latest["kind"], "owner": latest["owner"],
                "addressee": latest["addressee"], "criteria_refs": metadata.get("criteria_refs", []),
            }
            entries.append(("thread", f"thread:{thread_id}:{latest['event_id']}", snapshot))
            for criterion in metadata.get("criteria_refs", []):
                entries.append(("acceptance_criterion", f"criterion:{criterion}", {"criterion_ref": criterion, "thread_id": thread_id, "opening_event_id": self._opening_event(thread_id)["event_id"]}))
        selected = []
        contents = {}
        for ordinal, (source, ref, content) in enumerate(entries):
            content_json = canonical(content)
            digest = _sha(content_json.encode("utf-8"))
            item_id = _sha(f"{source}\0{ref}\0{ordinal}\0{digest}".encode("utf-8"))
            selected.append({"item_id": item_id, "ref": ref, "source": source, "sha256": digest})
            contents[item_id] = content_json
        return selected, contents

    def retrieve_context_item(self, bundle_id, item_reference, *, principal):
        bound_principal = principal if isinstance(principal, str) and principal else "__anonymous__"
        bundle = self.db.execute("SELECT * FROM context_bundles WHERE bundle_id=?", (bundle_id,)).fetchone()
        if not bundle or bundle["principal"] != bound_principal:
            _fail("context_required", "unknown or mismatched context bundle")
        row = self.db.execute(
            "SELECT * FROM context_bundle_items WHERE bundle_id=? AND (item_id=? OR content_sha256=? OR ref=?)",
            (bundle_id, item_reference, item_reference, item_reference),
        ).fetchone()
        if not row:
            _fail("context_required", "unknown context item")
        self._context_audit("item_retrieved", bound_principal, bundle_id, None, bundle["target_thread"], {"item_id": row["item_id"], "ref": row["ref"], "source": row["source"], "sha256": row["content_sha256"]})
        return {"item_id": row["item_id"], "ref": row["ref"], "source": row["source"], "sha256": row["content_sha256"], "content": json.loads(row["content_json"])}

    def retrieve_context_items(self, bundle_id, principal):
        refs = [row[0] for row in self.db.execute("SELECT item_id FROM context_bundle_items WHERE bundle_id=? ORDER BY ordinal", (bundle_id,))]
        return [self.retrieve_context_item(bundle_id, ref, principal=principal) for ref in refs]

    def acknowledge_context(self, bundle_id, principal, acknowledged_hashes):
        bundle = self.db.execute("SELECT * FROM context_bundles WHERE bundle_id=?", (bundle_id,)).fetchone()
        bound_principal = principal if isinstance(principal, str) and principal else "__anonymous__"
        if not bundle or bundle["principal"] != bound_principal:
            _fail("context_required", "unknown or mismatched context bundle")
        expected = self._validated_bundle_hashes(bundle)
        if not isinstance(acknowledged_hashes, list) or sorted(acknowledged_hashes) != expected or len(set(acknowledged_hashes)) != len(expected):
            _fail("context_required", "every exact context item hash must be acknowledged")
        retrieved = set()
        for row in self.db.execute("SELECT detail_json FROM context_audit WHERE bundle_id=? AND kind='item_retrieved'", (bundle_id,)):
            detail = json.loads(row[0])
            if detail.get("sha256"):
                retrieved.add(detail["sha256"])
        if retrieved != set(expected):
            _fail("context_required", "every selected context item must be retrieved before receipt issuance")
        token = secrets.token_urlsafe(32)
        token_hash = self._receipt_hash(token)
        receipt_id = str(uuid.uuid4())
        issued = now()
        expires = _utc_after(RECEIPT_TTL_SECONDS)
        aggregate = _canonical_sha(expected)
        self.db.execute(
            """INSERT INTO context_receipt_issues(
                 receipt_id,token_hash,principal,permitted_action,target_thread,expected_revision,
                 manifest_id,manifest_sha256,bundle_id,bundle_sha256,required_item_hashes_json,
                 required_items_sha256,issued_at,expires_at,ttl_seconds,receipt_hash_key_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                receipt_id, token_hash, bound_principal, bundle["permitted_action"], bundle["target_thread"],
                bundle["expected_revision"], bundle["manifest_id"], bundle["manifest_sha256"], bundle_id,
                bundle["bundle_sha256"], bundle["required_item_hashes_json"], aggregate, issued, expires,
                RECEIPT_TTL_SECONDS, self._receipt_key_id,
            ),
        )
        self._context_audit("receipt_issued", bound_principal, bundle_id, receipt_id, bundle["target_thread"], {"expires_at": expires})
        return token

    def _receipt_hash(self, token):
        if not isinstance(token, str):
            return ""
        return hmac.new(self._receipt_key, b"townsquare-context-receipt-v1\0" + token.encode("utf-8"), hashlib.sha256).hexdigest()

    def _validated_bundle_hashes(self, bundle):
        if not bundle:
            _fail("context_required", "context bundle is missing")
        rows = list(self.db.execute(
            "SELECT * FROM context_bundle_items WHERE bundle_id=? ORDER BY ordinal,item_id",
            (bundle["bundle_id"],),
        ))
        hashes = []
        for expected_ordinal, item in enumerate(rows):
            digest = _sha(item["content_json"].encode("utf-8"))
            item_id = _sha(f"{item['source']}\0{item['ref']}\0{item['ordinal']}\0{digest}".encode("utf-8"))
            if item["ordinal"] != expected_ordinal or item["content_sha256"] != digest or item["item_id"] != item_id:
                _fail("context_required", "persisted context item binding is invalid")
            hashes.append(digest)
        hashes.sort()
        try:
            persisted_hashes = json.loads(bundle["required_item_hashes_json"])
        except (TypeError, ValueError):
            _fail("context_required", "persisted context item hash set is invalid")
        if hashes != persisted_hashes or len(hashes) != len(set(hashes)):
            _fail("context_required", "persisted context item hash set changed")
        material = {
            "principal": bundle["principal"], "action": bundle["permitted_action"],
            "thread_id": bundle["target_thread"], "expected_revision": bundle["expected_revision"],
            "manifest_id": bundle["manifest_id"], "manifest_sha256": bundle["manifest_sha256"],
            "required_item_hashes": hashes,
        }
        if bundle["bundle_sha256"] != _canonical_sha(material):
            _fail("context_required", "persisted context bundle binding is invalid")
        return hashes

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
        if not principal or principal in {"expired-writer", "revoked-writer"}:
            _fail("forbidden", "authenticated governed principal required")
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
            manifest = self._manifest()
            self._assert_not_stopped()
            latest = self._latest_event(payload.get("thread_id")) if isinstance(payload.get("thread_id"), str) else None
            if latest is not None and revision != latest["event_id"]:
                issued = self.db.execute(
                    "SELECT * FROM context_receipt_issues WHERE token_hash=?", (self._receipt_hash(context_receipt),)
                ).fetchone()
                consumed = issued and self.db.execute(
                    "SELECT 1 FROM context_receipt_consumptions WHERE receipt_id=?", (issued["receipt_id"],)
                ).fetchone()
                if consumed or principal != latest["principal"]:
                    _fail("context_required", "fresh current context is required", requirements={"expected_revision": latest["event_id"]})
                if str(payload.get("state", "")).upper() == "OPEN" and str(payload.get("purpose", "")).upper() != "CORRECTION":
                    _fail("invalid_transition", "a terminal or existing thread cannot be reopened")
                _fail("conflict", "stale revision", requirements={"expected_revision": latest["event_id"]})
            action_capability = self.required_action_capability(payload)
            authority = self._resolve_authority(manifest, principal, action_capability, payload.get("thread_id"), idempotency_key)
            event = self._validate_event(principal, revision, payload)
            receipt = self._validate_receipt(context_receipt, principal, action_capability, event["thread_id"], revision)
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
                "authority_scope": action_capability,
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
                    "native-api", action_capability, committed_at, commit_hash,
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
                (event_id, principal, "post", canonical({"idempotency_key_sha256": _sha(idempotency_key.encode()), "action_capability": action_capability, "authority_ref": authority["authority_ref"]}), committed_at),
            )
            self._maybe_fail("after_audit")
            pointer = {"notice_id": notice_id, "event_id": event_id}
            self.db.execute(
                "INSERT INTO notice_intents VALUES (?,?,?,?,?,?,?,?)",
                (notice_id, event_id, ledger_seq, 1, event.get("addressee"), "poll", canonical(pointer), committed_at),
            )
            continues = event.get("continues")
            if continues:
                self.db.execute(
                    "INSERT INTO thread_continuations VALUES (?,?,?,?,?)",
                    (event["thread_id"], continues["thread_id"], "continues", event_id, committed_at),
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

    @staticmethod
    def required_action_capability(payload):
        if not isinstance(payload, dict):
            _fail("invalid", "event payload must be an object")
        if str(payload.get("purpose", "")).upper() == "CORRECTION":
            return "request:correct"
        state = str(payload.get("state", "")).upper()
        capability = ACTION_CAPABILITIES.get(state)
        if not capability:
            _fail("invalid_transition", "state is outside the controlled Request lifecycle")
        return capability

    def _resolve_authority(self, manifest, principal, capability, thread_id, request_key, *, operation="post"):
        authority = self._governance_authority
        reason = "effective"
        disposition = "EFFECTIVE"
        if not isinstance(authority, dict):
            disposition, reason = "UNKNOWN", "authority_source_absent"
        elif authority.get("decision") != "ADOPT":
            disposition, reason = "NOT_EFFECTIVE", "authority_not_adopted"
        elif (
            authority.get("manifest_id") != manifest.get("id")
            or authority.get("manifest_sha256") != manifest.get("sha256")
            or authority.get("manifest_content_sha256") != _manifest_content_sha(manifest)
        ):
            disposition, reason = "NOT_EFFECTIVE", "authority_manifest_mismatch"
        elif authority.get("revoked") is not False:
            disposition, reason = "NOT_EFFECTIVE", "authority_revoked_or_unknown"
        elif authority.get("status_history_complete") is not True:
            disposition, reason = "UNKNOWN", "authority_status_history_incomplete"
        elif not isinstance(authority.get("authority_sequence"), int) or authority["authority_sequence"] < 1:
            disposition, reason = "UNKNOWN", "authority_sequence_invalid"
        elif not isinstance(authority.get("authority_watermark"), int) or authority["authority_watermark"] < authority["authority_sequence"]:
            disposition, reason = "UNKNOWN", "authority_watermark_stale"
        elif not isinstance(authority.get("revocation_checked_through"), int) or authority["revocation_checked_through"] < authority["authority_watermark"]:
            disposition, reason = "UNKNOWN", "authority_revocation_watermark_stale"
        elif _parse_utc(authority.get("effective_from")) is None or _parse_utc(authority["effective_from"]) > datetime.now(timezone.utc):
            disposition, reason = "NOT_EFFECTIVE", "authority_not_yet_effective"
        elif authority.get("effective_until") is not None and (
            _parse_utc(authority.get("effective_until")) is None
            or _parse_utc(authority["effective_until"]) <= datetime.now(timezone.utc)
        ):
            disposition, reason = "NOT_EFFECTIVE", "authority_expired"
        prior_watermark = None
        if isinstance(authority, dict) and isinstance(authority.get("resolver_key_id"), str):
            prior_watermark = self.db.execute(
                "SELECT MAX(authority_watermark) FROM governance_resolution_audit WHERE resolver_key_id=?",
                (authority["resolver_key_id"],),
            ).fetchone()[0]
        if disposition == "EFFECTIVE" and prior_watermark is not None and authority["authority_watermark"] < prior_watermark:
            disposition, reason = "UNKNOWN", "authority_watermark_rollback"
        scope = authority.get("scope", {}) if isinstance(authority, dict) else {}
        capabilities = scope.get("capabilities", {}) if isinstance(scope, dict) else {}
        actions = set(scope.get("actions", [])) if isinstance(scope, dict) and isinstance(scope.get("actions"), list) else set()
        targets = set(scope.get("targets", [])) if isinstance(scope, dict) and isinstance(scope.get("targets"), list) else set()
        if disposition == "EFFECTIVE" and (capability not in actions or ("*" not in targets and thread_id not in targets)):
            disposition, reason = "NOT_EFFECTIVE", "authority_scope_mismatch"
        granted = capabilities.get(principal, set()) if isinstance(capabilities, dict) else set()
        authority_ref = authority.get("adoption_event_id") if isinstance(authority, dict) else None
        authority_digest = _canonical_sha({name: value for name, value in authority.items() if name != "signature"}) if isinstance(authority, dict) else None
        evidence = {
            "resolver_version": "governed-native-v1", "principal": principal, "capability": capability,
            "target_thread": thread_id, "manifest_id": manifest.get("id"), "manifest_sha256": manifest.get("sha256"),
            "authority_ref": authority_ref, "authority_digest": authority_digest,
            "resolver_key_id": authority.get("resolver_key_id") if isinstance(authority, dict) else None,
            "authority_sequence": authority.get("authority_sequence") if isinstance(authority, dict) else None,
            "authority_watermark": authority.get("authority_watermark") if isinstance(authority, dict) else None,
            "signature_valid": isinstance(authority, dict), "disposition": disposition, "reason_code": reason,
        }
        self.db.execute(
            """INSERT INTO governance_resolution_audit(
                 resolution_id,native_request_principal,native_request_operation,native_request_key,
                 action_capability,target_thread,manifest_id,manifest_sha256,authority_ref,authority_digest,
                 disposition,reason_code,evidence_json,resolved_at,resolver_key_id,authority_sequence,authority_watermark)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()), principal, operation, request_key, capability, str(thread_id), manifest.get("id"),
                manifest.get("sha256"), authority_ref, authority_digest, disposition, reason,
                canonical(evidence), now(),
                authority.get("resolver_key_id") if isinstance(authority, dict) else None,
                authority.get("authority_sequence") if isinstance(authority, dict) else None,
                authority.get("authority_watermark") if isinstance(authority, dict) else None,
            ),
        )
        if disposition != "EFFECTIVE":
            self.db.commit()
            _fail("context_required", f"governance authority resolution failed: {reason}")
        if capability not in set(granted):
            # Resolution evidence is independently durable even when the
            # resolved authority does not grant this actor the requested
            # action.  No ordinary ledger mutation has happened yet.
            self.db.commit()
            _fail("forbidden", f"principal lacks {capability}")
        return {**authority, "authority_ref": authority_ref, "digest": authority_digest, "capabilities": capabilities}

    def _validate_event(self, principal, revision, payload):
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
        purpose = str(event.get("purpose", "EVENT")).upper()
        if event["kind"] != "REQUEST":
            _fail("invalid", "only Request has a controlled governed lifecycle")
        if state == "CORRECTED":
            _fail("invalid_transition", "correction is a purpose, not a lifecycle state")
        if latest is None:
            if revision != "new" or state != "OPEN":
                _fail("conflict", "new thread requires revision=new and state=OPEN")
            if not isinstance(event.get("owner"), str) or not event["owner"]:
                _fail("invalid", "opening owner is required")
            if not isinstance(event.get("addressee"), str) or not event["addressee"]:
                _fail("invalid", "opening addressee is required")
            if event["owner"] != principal:
                _fail("forbidden", "opening owner must be the authenticated principal")
            criteria = event.get("criteria_refs")
            if not isinstance(criteria, list) or not criteria or any(not isinstance(item, str) or not item for item in criteria) or len(set(criteria)) != len(criteria):
                _fail("invalid", "opening acceptance criteria are required")
            self._validate_continuation(event)
        else:
            if revision != latest["event_id"]:
                if principal != latest["principal"]:
                    _fail("context_required", "recipient must retrieve current context", requirements={"expected_revision": latest["event_id"]})
                _fail("conflict", "stale revision", requirements={"expected_revision": latest["event_id"]})
            opening = self._opening_event(event["thread_id"])
            opening_metadata = json.loads(opening["metadata_json"])
            if state == "RESOLVED" and (not event.get("evidence_refs") or not event.get("criteria_refs")):
                _fail("context_required", "resolution requires evidence and criteria dispositions")
            for field in ("owner", "addressee"):
                authoritative = opening[field]
                if field in event and event[field] != authoritative:
                    _fail("forbidden", f"{field} is authoritative from the opening event")
                event[field] = authoritative
            authoritative_criteria = opening_metadata.get("criteria_refs", [])
            if "criteria_refs" in event and event["criteria_refs"] != authoritative_criteria:
                _fail("forbidden", "acceptance criteria are authoritative from the opening event")
            event["criteria_refs"] = authoritative_criteria
            if purpose == "CORRECTION":
                corrected = event.get("corrects_event")
                target = self.db.execute("SELECT * FROM ledger_events WHERE event_id=? AND thread_id=?", (corrected, event["thread_id"])).fetchone()
                if not target:
                    _fail("invalid_transition", "correction must reference an event in the same thread")
                if target["principal"] != principal:
                    _fail("forbidden", "only the target event author may correct that event")
                if state != latest["state"]:
                    _fail("invalid_transition", "correction purpose carries the current lifecycle state")
                if state == "OPEN" and principal != opening["owner"]:
                    _fail("forbidden", "only the authoritative owner may correct an open Request")
                if state in {"WORKING", "BLOCKED", "RESOLVED"} and principal not in {opening["owner"], opening["addressee"]}:
                    _fail("forbidden", "principal is not an authoritative work actor")
                return event
            if state == "OPEN":
                _fail("invalid_transition", "a terminal or existing thread cannot be reopened")
            if state == "WORKING" and latest["state"] == "OPEN" and principal != opening["addressee"]:
                _fail("forbidden", "only the authoritative addressee may begin work")
            if state in {"WORKING", "BLOCKED", "RESOLVED"} and principal not in {opening["owner"], opening["addressee"]}:
                _fail("forbidden", "principal is not an authoritative work actor")
            if state == "CANCELLED" and principal not in {opening["owner"], opening["addressee"], "operator"}:
                _fail("forbidden", "only the owner, addressee, or operator may cancel a Request")
            if state == "RESOLVED" and (not event.get("evidence_refs") or not authoritative_criteria):
                _fail("context_required", "resolution requires evidence and criteria dispositions")
            if state == "CLOSED":
                accepted_by = event.get("accepted_by")
                if accepted_by != principal:
                    _fail("forbidden", "accepted_by must be the authenticated acceptor")
                history_authors = {row[0] for row in self.db.execute("SELECT principal FROM ledger_events WHERE thread_id=? AND kind='REQUEST'", (event["thread_id"],))}
                if principal in history_authors:
                    _fail("forbidden", "a thread author cannot accept work from that thread")
                if latest["state"] != "RESOLVED":
                    _fail("invalid_transition", "closure requires a resolved event")
                required_criteria = authoritative_criteria
                dispositions = event.get("criterion_dispositions")
                if not isinstance(required_criteria, list) or not required_criteria:
                    _fail("invalid_transition", "resolved event has no acceptance criteria")
                if not isinstance(dispositions, dict) or set(dispositions) != set(required_criteria):
                    _fail("invalid_transition", "closure requires one disposition for every criterion")
                if any(value not in {"accepted", "rejected"} for value in dispositions.values()):
                    _fail("invalid_transition", "invalid criterion disposition")
            allowed = {
                "OPEN": {"WORKING", "CANCELLED"},
                "WORKING": {"WORKING", "BLOCKED", "RESOLVED", "CANCELLED"},
                "BLOCKED": {"WORKING", "RESOLVED", "CANCELLED"},
                "RESOLVED": {"CLOSED", "CANCELLED"},
            }
            if state not in allowed.get(latest["state"], set()):
                _fail("invalid_transition", f"{latest['state']} cannot transition to {state}")
        return event

    def _opening_event(self, thread_id):
        return self.db.execute(
            "SELECT * FROM ledger_events WHERE thread_id=? AND kind='REQUEST' ORDER BY thread_ordinal LIMIT 1",
            (thread_id,),
        ).fetchone()

    def _validate_continuation(self, event):
        link = event.get("continues")
        if link is None:
            return
        if not isinstance(link, dict) or set(link) != {"thread_id", "relation"} or link.get("relation") != "continues" or not isinstance(link.get("thread_id"), str) or link["thread_id"] == event["thread_id"]:
            _fail("invalid", "continues must be one typed predecessor reference")
        predecessor = self._latest_event(link["thread_id"])
        archived = self.db.execute("SELECT 1 FROM logical_archives WHERE thread_id=?", (link["thread_id"],)).fetchone()
        if not predecessor or predecessor["state"] not in TERMINAL_STATES or not archived:
            _fail("invalid", "continues predecessor must be terminal and archived")

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
        if receipt["receipt_hash_key_id"] != self._receipt_key_id:
            _fail("context_required", "context receipt key binding is unavailable")
        bundle = self.db.execute("SELECT * FROM context_bundles WHERE bundle_id=?", (receipt["bundle_id"],)).fetchone()
        persisted_hashes = self._validated_bundle_hashes(bundle)
        if (
            receipt["bundle_sha256"] != bundle["bundle_sha256"]
            or receipt["required_item_hashes_json"] != bundle["required_item_hashes_json"]
            or receipt["required_items_sha256"] != _canonical_sha(persisted_hashes)
        ):
            _fail("context_required", "persisted receipt binding is invalid")
        manifest = self._manifest()
        if receipt["manifest_id"] != manifest["id"] or receipt["manifest_sha256"] != manifest["sha256"]:
            _fail("context_required", "context manifest changed")
        selected, _ = self._context_items(principal, action, thread_id, revision, manifest)
        current_hashes = sorted(item["sha256"] for item in selected)
        if current_hashes != persisted_hashes:
            _fail("context_required", "authoritative context changed after receipt issuance")
        retrieved = set()
        for row in self.db.execute("SELECT detail_json FROM context_audit WHERE bundle_id=? AND kind='item_retrieved'", (receipt["bundle_id"],)):
            detail = json.loads(row[0])
            if detail.get("sha256"):
                retrieved.add(detail["sha256"])
        if retrieved != set(current_hashes):
            _fail("context_required", "receipt lacks complete retrieval evidence")
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
        if row["predecessor_event_id"] is None:
            if row["predecessor_commit_sha256"] is not None or row["thread_ordinal"] != 0:
                return False
        else:
            predecessor = self.db.execute(
                "SELECT thread_id,thread_ordinal,commit_sha256 FROM ledger_events WHERE event_id=?",
                (row["predecessor_event_id"],),
            ).fetchone()
            if (
                not predecessor
                or predecessor["thread_id"] != row["thread_id"]
                or predecessor["thread_ordinal"] != row["thread_ordinal"] - 1
                or predecessor["commit_sha256"] != row["predecessor_commit_sha256"]
            ):
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

    def get_thread(self, thread_id, *, principal="operator", capabilities=None, include_archived=False):
        if capabilities is None:
            from .auth import NATIVE_CAPABILITY_POLICIES
            capabilities = NATIVE_CAPABILITY_POLICIES["townsquare-mvp-v1"].get(principal, set())
        capabilities = set(capabilities)
        if principal not in READ_PRINCIPALS or "post:read" not in capabilities:
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
        if any(row["sensitivity"] == "RESTRICTED" for row in rows) and "content:restricted:read" not in capabilities:
            _fail("forbidden", "restricted content capability required")
        events = []
        for row in rows:
            event = dict(row)
            metadata = json.loads(event["metadata_json"])
            if "continues" in metadata:
                event["continues"] = metadata["continues"]
            events.append(event)
        return {"thread_id": thread_id, "archived": bool(archived), "events": events}

    def current_projection(self):
        rows = list(self.db.execute(
            """SELECT e.thread_id,e.event_id,e.ledger_seq,e.thread_ordinal,e.kind,e.state,e.owner,e.addressee,e.sensitivity,e.committed_at
               FROM ledger_events e JOIN (
                 SELECT thread_id,MAX(thread_ordinal) AS ordinal FROM ledger_events
                 WHERE kind NOT IN ('CONTROL','ARCHIVE','REGISTRY_AUDIT') GROUP BY thread_id
               ) latest ON latest.thread_id=e.thread_id AND latest.ordinal=e.thread_ordinal
               ORDER BY e.thread_id"""
        ))
        obsolete = [row["thread_id"] for row in rows if row["kind"] == "REQUEST" and row["state"] not in REQUEST_STATES]
        if obsolete:
            _fail(
                "context_required",
                "obsolete native Request lifecycle state requires operator disposition",
                requirements={"threads": obsolete, "supported_states": sorted(REQUEST_STATES)},
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
        return rows

    def open_work(self):
        archived = {row[0] for row in self.db.execute("SELECT thread_id FROM logical_archives")}
        return [row for row in self.current_projection()["threads"] if row["thread_id"] not in archived and row["state"] not in TERMINAL_STATES]

    def discovery_projection(self):
        threads = self.current_projection()["threads"]
        dependencies = {row["dependency"]: dict(row) for row in self.db.execute("SELECT * FROM projection_dependencies")}
        registry_dep = dependencies.get("registry")
        if registry_dep and not registry_dep["available"]:
            registry = {"status": "DEGRADED", "agents": None, "findings": [{"code": "registry_unavailable", "detail": registry_dep["detail"]}]}
        else:
            registry = {"status": "EXTERNAL", "agents": None, "findings": []}
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

    def notice_intents(self, *, principal="viewer", event_id=None):
        if principal not in NOTICE_READ_PRINCIPALS:
            _fail("forbidden", "principal lacks notice:read")
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

    def notice_attempts(self, notice_id, *, principal="viewer"):
        if principal not in NOTICE_READ_PRINCIPALS:
            _fail("forbidden", "principal lacks notice:read")
        return [dict(row) for row in self.db.execute("SELECT * FROM notice_attempts WHERE notice_id=? ORDER BY attempt_number", (notice_id,))]

    def notice_status(self, notice_id):
        attempts = self.notice_attempts(notice_id, principal="viewer")
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

    def archive_thread(self, principal, thread_id, reason, *, context_receipt=None, expected_revision=None):
        if principal != "operator":
            _fail("forbidden", "operator archive capability required")
        if not isinstance(reason, str) or not reason.strip():
            _fail("invalid", "archive reason is required")
        if context_receipt is None or expected_revision is None:
            _fail("context_required", "archive requires current context")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self._assert_not_stopped()
            latest = self._latest_event(thread_id)
            if not latest:
                _fail("invalid", "unknown thread")
            if latest["event_id"] != expected_revision:
                _fail("conflict", "archive revision is stale", requirements={"expected_revision": latest["event_id"]})
            if latest["state"] not in TERMINAL_STATES:
                _fail("context_required", "only a terminal thread is archive eligible")
            manifest = self._manifest()
            receipt = self._validate_receipt(context_receipt, principal, "request:archive", thread_id, expected_revision)
            authority = self._resolve_authority(manifest, principal, "request:archive", thread_id, receipt["receipt_id"], operation="archive")
            event_id = str(uuid.uuid4())
            committed = now()
            ledger_seq = self._append_internal_event(thread_id, "ARCHIVE", "ARCHIVED", reason, principal, event_id=event_id)
            self.db.execute("INSERT INTO logical_archives VALUES (?,?,?,?,?)", (thread_id, event_id, reason, principal, committed))
            response = {"thread_id": thread_id, "event_id": event_id, "ledger_seq": ledger_seq, "archived": True}
            request_hash = _canonical_sha({"thread_id": thread_id, "reason": reason, "expected_revision": expected_revision})
            self.db.execute(
                "INSERT INTO native_requests VALUES (?,?,?,?,?,?,?,?,?)",
                (principal, "archive", receipt["receipt_id"], request_hash, event_id, ledger_seq, 201, canonical(response), committed),
            )
            self.db.execute(
                "INSERT INTO context_receipt_consumptions VALUES (?,?,?,?,?,?)",
                (receipt["receipt_id"], principal, "archive", receipt["receipt_id"], event_id, committed),
            )
            self._context_audit("receipt_consumed", principal, receipt["bundle_id"], receipt["receipt_id"], thread_id, {"event_id": event_id, "operation": "archive"})
            self.db.execute("INSERT INTO archive_requests VALUES (?,?,?,?,?)", (thread_id, receipt["receipt_id"], principal, request_hash, committed))
            self.db.execute(
                "INSERT INTO ledger_audit(event_id,principal,operation,detail_json,created_at) VALUES (?,?,?,?,?)",
                (event_id, principal, "archive", canonical({"authority_ref": authority["authority_ref"], "expected_revision": expected_revision}), committed),
            )
            self.db.commit()
            return response
        except NativeLedgerError:
            self.db.rollback()
            raise
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
        _fail("forbidden", "Registry authority is external; submit only authenticated audit events")

    def registry_query(self, agent_id):
        _fail("forbidden", "Registry reads belong to the external Registry service")

    def registry_history(self, agent_id):
        _fail("forbidden", "Registry history belongs to the external Registry service")

    def registry_outbox(self, event_uuid):
        _fail("forbidden", "Registry outbox belongs to the external Registry service")

    def append_registry_audit(self, principal, payload):
        if principal != "registry-audit" or not isinstance(payload, dict) or set(payload) != {"board", "actor", "event_uuid"} or payload.get("board") != "BOARD-AUDIT-RECORD" or payload.get("actor") != "registry" or not isinstance(payload.get("event_uuid"), str):
            _fail("forbidden", "fixed registry audit capability/schema required")
        payload_json = canonical(payload)
        existing = self.db.execute("SELECT canonical_payload FROM registry_audit_events WHERE event_uuid=?", (payload["event_uuid"],)).fetchone()
        if existing:
            if existing["canonical_payload"] != payload_json:
                _fail("conflict", "registry audit event UUID payload mismatch")
            return {"event_uuid": payload["event_uuid"]}
        self.db.execute("BEGIN IMMEDIATE")
        try:
            ledger_event_id = str(uuid.uuid4())
            self._append_internal_event("__registry_audit__", "REGISTRY_AUDIT", "RECORDED", payload_json, "registry", event_id=ledger_event_id)
            self.db.execute("INSERT INTO registry_audit_events(event_uuid,actor,board,canonical_payload,payload_sha256,created_at,authenticated_principal) VALUES (?,?,?,?,?,?,?)", (payload["event_uuid"], "registry", "BOARD-AUDIT-RECORD", payload_json, _sha(payload_json.encode()), now(), principal))
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
        _fail("forbidden", "Registry reconciliation belongs to the external Registry service")

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
