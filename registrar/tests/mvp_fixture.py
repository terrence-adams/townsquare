"""Test-only contract adapter for the TownSquare native-ledger MVP.

The tests deliberately use only the standard library and the existing SQLite
connection helper: the bundled Python does not include FastAPI or pytest.
`NativeLedger` is the public service contract implemented by the MVP.  Keeping
this adapter here makes missing implementation a clear assertion failure,
rather than an import/dependency failure.
"""
from __future__ import annotations

import gc
import hashlib
import hmac
import os
import secrets
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from registrar.app.db import connect, migrate
from registrar.app.service import canonical


MANIFEST = {
    "id": "mvp-test-manifest-v1",
    "sha256": "a" * 64,
    "governance": [{"ref": "DOCTRINE.md", "sha256": "b" * 64}],
    "required_items": [{"ref": "work-order", "sha256": "c" * 64}],
    "pinned": True,
}

OPENING = {
    "thread_id": "thread-alpha",
    "kind": "REQUEST",
    "state": "OPEN",
    "owner": "writer-a",
    "addressee": "writer-b",
    "body": "Native content: \u03b1",
    "media_type": "text/plain; charset=utf-8",
    "sensitivity": "INTERNAL",
    "criteria_refs": ["criterion-1"],
    "evidence_refs": [],
    "governed_refs": ["DOCTRINE.md"],
}

GOVERNED_MANIFEST = dict(MANIFEST)

REQUEST_ACTIONS = {
    "OPEN": "request:open", "WORKING": "request:work", "BLOCKED": "request:block",
    "RESOLVED": "request:resolve", "CLOSED": "request:accept", "CANCELLED": "request:cancel",
}

TEST_AUTHORITY_CAPABILITIES = {
    "writer-a": ["request:open", "request:work", "request:resolve", "request:accept"],
    "writer-b": ["request:work", "request:block", "request:resolve", "request:cancel"],
    "reviewer": ["request:accept"],
    "operator": ["request:cancel", "request:archive"],
}


def authority_proof(manifest, key, key_id, **changes):
    """Create resolver evidence external to the mounted context manifest."""
    proof = {
        "schema": "townsquare-authority-proof-v1",
        "resolver_key_id": key_id,
        "adoption_event_id": "test-adoption-event-1",
        "manifest_id": manifest["id"],
        "manifest_sha256": manifest["sha256"],
        "manifest_content_sha256": hashlib.sha256(canonical(
            {name: value for name, value in manifest.items() if name != "sha256"}
        ).encode("utf-8")).hexdigest(),
        "decision": "ADOPT",
        "revoked": False,
        "status_history_complete": True,
        "authority_sequence": 1,
        "authority_watermark": 1,
        "revocation_checked_through": 1,
        "effective_from": "2020-01-01T00:00:00Z",
        "effective_until": None,
        "scope": {
            "capabilities": deepcopy(TEST_AUTHORITY_CAPABILITIES),
            "actions": sorted({action for actions in TEST_AUTHORITY_CAPABILITIES.values() for action in actions}),
            "targets": ["*"],
        },
    }
    proof.update(changes)
    material = {name: value for name, value in proof.items() if name != "signature"}
    proof["signature"] = hmac.new(key, canonical(material).encode("utf-8"), hashlib.sha256).hexdigest()
    return proof


class NativeLedgerCase(unittest.TestCase):
    """An isolated database and a direct handle to the required MVP facade."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "ledger.db")
        self.receipt_key_path = Path(self.tmp.name) / "receipt-hash.key"
        self.authority_key_path = Path(self.tmp.name) / "authority-resolver.key"
        # Leave margin for production's whitespace trimming when a random
        # byte happens to be a leading/trailing ASCII whitespace character.
        self.receipt_key = secrets.token_bytes(64)
        self.authority_key = secrets.token_bytes(64)
        self.receipt_key_path.write_bytes(self.receipt_key)
        self.authority_key_path.write_bytes(self.authority_key)
        for path in (self.receipt_key_path, self.authority_key_path):
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        self._environment = patch.dict(os.environ, {
            "TOWNSQUARE_RECEIPT_HASH_KEY_FILE": str(self.receipt_key_path),
            "TOWNSQUARE_RECEIPT_HASH_KEY_ID": "test-receipt-key-v1",
            "TOWNSQUARE_AUTHORITY_RESOLVER_KEY_FILE": str(self.authority_key_path),
            "TOWNSQUARE_AUTHORITY_RESOLVER_KEY_ID": "test-authority-key-v1",
        })
        self._environment.start()
        self.db = connect(self.db_path)
        migrate(self.db)
        try:
            from registrar.app.native_ledger import NativeLedger
        except ModuleNotFoundError as exc:
            # unittest does not call tearDown when setUp fails.  Close the
            # Windows SQLite handle here so the expected red failure is clean.
            self.db.close()
            gc.collect()
            self.tmp.cleanup()
            self.fail("MVP service missing: implement registrar.app.native_ledger.NativeLedger")
        self.ledger = NativeLedger(
            self.db,
            context_manifest=MANIFEST,
            governance_authority=self.authority_proof(MANIFEST),
        )

    def tearDown(self):
        self.db.close()
        self._environment.stop()
        # Windows will retain SQLite WAL handles until cyclic frames are
        # collected after a failed setUp; release them before deleting temp DB.
        gc.collect()
        self.tmp.cleanup()

    def authority_proof(self, manifest=MANIFEST, **changes):
        return authority_proof(manifest, self.authority_key, "test-authority-key-v1", **changes)

    def bundle(self, principal="writer-a", action="request:open", thread_id="thread-alpha", revision="new"):
        return self.ledger.create_context_bundle(principal, action, thread_id, revision)

    def receipt(self, principal="writer-a", action="request:open", thread_id="thread-alpha", revision="new"):
        bundle = self.bundle(principal, action, thread_id, revision)
        # Retrieval is a separate, observable operation.  The SHA-256 is the
        # stable identity of an exact selected item; a caller cannot attest to
        # items whose content it did not ask the ledger to return.
        for item in bundle["required_items"]:
            self.ledger.retrieve_context_item(bundle["bundle_id"], item["sha256"], principal=principal)
        return self.ledger.acknowledge_context(bundle["bundle_id"], principal, [i["sha256"] for i in bundle["required_items"]])

    @staticmethod
    def request_action(payload):
        """Return the receipt action for the Request transition being made.

        A correction is append-only purpose/reference metadata on a valid
        lifecycle event.  It therefore uses the capability for that carried
        state; it is not a seventh state or a coarse post permission.
        """
        if str(payload.get("purpose", "")).upper() == "CORRECTION":
            return "request:correct"
        return REQUEST_ACTIONS.get(str(payload.get("state", "")).upper(), "request:invalid")

    def post(self, payload=None, *, principal="writer-a", key="key-1", revision="new", receipt=None):
        event = payload or dict(OPENING)
        receipt = receipt or self.receipt(
            principal, self.request_action(event), event["thread_id"], revision,
        )
        return self.ledger.post_event(principal, key, receipt, revision, event)

    def governed_receipt(self, principal, payload, revision):
        return self.receipt(principal, self.request_action(payload), payload["thread_id"], revision)

    def governed_post(self, payload, *, principal="writer-a", key="governed", revision="new", receipt=None):
        return self.ledger.post_event(principal, key, receipt or self.governed_receipt(principal, payload, revision), revision, payload)

    def seed_legacy_import(self):
        """Create an actual historical projection via its supported importer.

        A sentinel pretending to be a historical post would make the union
        projection dishonest.  This fixture uses the same staged/promotion
        path as the legacy-import regression tests.
        """
        from registrar.app.service import Registrar
        from registrar.importer.legacy import plan

        manifest = plan([{
            "name": "TS-20260917-legacy-009.001-WORKING__by-legacy.txt",
            "drive_file_id": "mvp-legacy-drive-a",
        }])
        registrar = Registrar(self.db)
        staged = registrar.stage_import("importer", manifest)
        registrar.promote_import("promoter", staged["run_id"], staged["manifest_digest"])

    def assert_code(self, code, fn, *args, **kwargs):
        with self.assertRaises(Exception) as caught:
            fn(*args, **kwargs)
        self.assertEqual(code, getattr(caught.exception, "code", None), str(caught.exception))
        return caught.exception
