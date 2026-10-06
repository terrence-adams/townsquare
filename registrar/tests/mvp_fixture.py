"""Test-only contract adapter for the TownSquare native-ledger MVP.

The tests deliberately use only the standard library and the existing SQLite
connection helper: the bundled Python does not include FastAPI or pytest.
`NativeLedger` is the public service contract implemented by the MVP.  Keeping
this adapter here makes missing implementation a clear assertion failure,
rather than an import/dependency failure.
"""
from __future__ import annotations

import gc
import tempfile
import unittest
from pathlib import Path

from registrar.app.db import connect, migrate


MANIFEST = {
    "id": "mvp-test-manifest-v1",
    "sha256": "a" * 64,
    "governance": [{"ref": "DOCTRINE.md", "sha256": "b" * 64}],
    "required_items": [{"ref": "work-order", "sha256": "c" * 64}],
    "pinned": True,
    # This is resolution evidence supplied to the test service, not an
    # authority claim made by the mounted manifest itself.  Individual tests
    # replace status/effective/verification facts to prove fail-closed gates.
    "governance_authority": {
        "authority_ref": "governance-record-1",
        "digest": "d" * 64,
        "status": "ADOPTED",
        "effective": True,
        "verified": True,
        "capabilities": {
            "writer-a": {"work:open", "work:start", "work:resolve", "work:accept", "work:correct"},
            "writer-b": {"work:claim", "work:start", "work:resolve", "work:accept", "work:correct"},
            "reviewer": {"work:accept"},
            "operator": {"work:cancel", "work:archive"},
        },
    },
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


class NativeLedgerCase(unittest.TestCase):
    """An isolated database and a direct handle to the required MVP facade."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "ledger.db")
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
        self.ledger = NativeLedger(self.db, context_manifest=MANIFEST)

    def tearDown(self):
        self.db.close()
        # Windows will retain SQLite WAL handles until cyclic frames are
        # collected after a failed setUp; release them before deleting temp DB.
        gc.collect()
        self.tmp.cleanup()

    def bundle(self, principal="writer-a", action="post", thread_id="thread-alpha", revision="new"):
        return self.ledger.create_context_bundle(principal, action, thread_id, revision)

    def receipt(self, principal="writer-a", action="post", thread_id="thread-alpha", revision="new"):
        bundle = self.bundle(principal, action, thread_id, revision)
        # Retrieval is a separate, observable operation.  The SHA-256 is the
        # stable identity of an exact selected item; a caller cannot attest to
        # items whose content it did not ask the ledger to return.
        for item in bundle["required_items"]:
            self.ledger.retrieve_context_item(bundle["bundle_id"], item["sha256"], principal=principal)
        return self.ledger.acknowledge_context(bundle["bundle_id"], principal, [i["sha256"] for i in bundle["required_items"]])

    def post(self, payload=None, *, principal="writer-a", key="key-1", revision="new", receipt=None):
        return self.ledger.post_event(principal, key, receipt or self.receipt(principal, "post", (payload or OPENING)["thread_id"], revision), revision, payload or dict(OPENING))

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
