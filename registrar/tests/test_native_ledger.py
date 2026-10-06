"""MVP-LDG acceptance tests: native authority is event+content, never a file."""
from __future__ import annotations

import copy
import hashlib

from registrar.tests.mvp_fixture import NativeLedgerCase, OPENING


class NativeLedgerTests(NativeLedgerCase):
    def test_mvp_ldg_01_native_opening_is_durable_and_receipted(self):
        commit = self.post()
        self.db.close()
        self.db = __import__("registrar.app.db", fromlist=["connect"]).connect(self.db_path)
        self.ledger = type(self.ledger)(self.db, context_manifest=__import__("registrar.tests.mvp_fixture", fromlist=["MANIFEST"]).MANIFEST)
        event = self.ledger.get_thread("thread-alpha")["events"][0]
        self.assertEqual(commit["event_id"], event["event_id"])
        self.assertEqual(OPENING["body"].encode(), event["content"].encode())
        self.assertTrue(all(event[k] for k in ("ledger_seq", "content_sha256", "metadata_sha256", "commit_sha256")))

    def test_mvp_ldg_02_committed_content_is_immutable_and_corrections_append(self):
        first = self.post()
        self.assert_code("forbidden", self.ledger.update_content, first["event_id"], "changed")
        self.assert_code("forbidden", self.ledger.delete_event, first["event_id"])
        correction = self.post({**OPENING, "state": "CORRECTED", "body": "correction"}, key="key-correct", revision=first["event_id"])
        self.assertGreater(correction["ledger_seq"], first["ledger_seq"])

    def test_mvp_ldg_03_projections_are_deterministic(self):
        self.post()
        self.assertEqual(self.ledger.current_projection(), self.ledger.current_projection())

    def test_mvp_ldg_04_lifecycle_rejects_wrong_actor_self_close_and_reopen(self):
        first = self.post()
        self.assert_code("forbidden", self.post, {**OPENING, "state": "CLOSED"}, principal="writer-a", key="self-close", revision=first["event_id"])
        self.assert_code("invalid_transition", self.post, {**OPENING, "state": "OPEN"}, key="reopen", revision="terminal")

    def test_mvp_ldg_05_commit_provenance_is_server_derived_and_anonymous_fails(self):
        commit = self.post()
        event = self.ledger.events_since(0)[0]
        self.assertEqual("writer-a", event["principal"])
        self.assertIn("represented_actor", event)
        self.assertIn("authority_scope", event)
        self.assertIn("committed_at", event)
        self.assert_code("forbidden", self.ledger.post_event, None, "anon", "x", "new", OPENING)

    def test_mvp_ldg_06_idempotency_is_atomic_and_payload_change_conflicts(self):
        receipt = self.receipt()
        first = self.post(receipt=receipt)
        again = self.ledger.post_event("writer-a", "key-1", receipt, "new", OPENING)
        self.assertEqual(first, again)
        self.assertEqual(1, len(self.ledger.notice_intents(event_id=first["event_id"])))
        changed = {**OPENING, "body": "not the original request"}
        self.assert_code("conflict", self.ledger.post_event, "writer-a", "key-1", receipt, "new", changed)

    def test_mvp_ldg_07_hash_chain_and_bidirectional_content_binding_verify(self):
        commit = self.post()
        event = self.ledger.events_since(0)[0]
        self.assertEqual(hashlib.sha256(OPENING["body"].encode()).hexdigest(), event["content_sha256"])
        self.assertTrue(self.ledger.verify_event(commit["event_id"]))
        self.assert_code("invalid", self.ledger.inject_envelope_only, copy.deepcopy(event))
        self.assert_code("invalid", self.ledger.inject_content_only, commit["event_id"], b"orphan")

    def test_mvp_ldg_08_union_reads_label_legacy_and_never_synthesize_body(self):
        self.post()
        rows = self.ledger.union_reads(include_legacy=True)
        self.assertEqual("native", next(r for r in rows if r["thread_id"] == "thread-alpha")["source"])
        legacy = next(r for r in rows if r["source"] == "legacy_import")
        self.assertIn("content_availability", legacy)
        self.assertNotIn("synthetic_body", legacy)

    def test_mvp_ldg_09_failures_at_atomic_boundaries_leave_no_partial_commit(self):
        for boundary in self.ledger.native_write_boundaries():
            with self.subTest(boundary=boundary):
                self.ledger.inject_failure(boundary)
                self.assert_code("unavailable", self.post, key="fail-" + boundary)
                self.assertEqual([], self.ledger.events_since(0))
                self.ledger.clear_failure()

    def test_mvp_ldg_10_native_request_records_are_immutable(self):
        commit = self.post()
        self.assert_code("forbidden", self.ledger.update_native_request, "writer-a", "post", "key-1")
        self.assert_code("forbidden", self.ledger.delete_native_request, "writer-a", "post", "key-1")
        self.assertEqual(commit, self.ledger.idempotency_receipt("writer-a", "post", "key-1"))
