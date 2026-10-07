"""MVP-CMP/GOV tests: documented context is a server-enforced precondition."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from registrar.app.db import connect
from registrar.app.native_ledger import NativeLedger
from registrar.tests.mvp_fixture import MANIFEST, NativeLedgerCase, OPENING


class ContextGateTests(NativeLedgerCase):
    def test_mvp_cmp_01_missing_or_unpinned_manifest_blocks_writes(self):
        self.ledger.set_context_manifest(None)
        self.assert_code("context_required", self.ledger.post_event, "writer-a", "none", "receipt", "new", OPENING)
        self.ledger.set_context_manifest({"id": "mutable", "pinned": False})
        self.assert_code("context_required", self.ledger.post_event, "writer-a", "unpinned", "receipt", "new", OPENING)

    def test_mvp_cmp_02_stale_revision_returns_machine_readable_requirements(self):
        first = self.post()
        receipt = self.receipt(revision="new")
        self.assert_code("conflict", self.ledger.post_event, "writer-a", "stale", receipt, "new", {**OPENING, "state": "WORKING"})

    def test_mvp_cmp_03_receipt_binds_every_context_item_principal_and_expiry(self):
        bundle = self.bundle()
        self.assert_code("context_required", self.ledger.acknowledge_context, bundle["bundle_id"], "writer-a", [])
        receipt = self.receipt()
        self.assertEqual("writer-a", self.ledger.receipt_record(receipt)["principal"])
        self.assertIn("expires_at", self.ledger.receipt_record(receipt))

    def test_mvp_cmp_04_resolution_and_closure_require_evidence_and_dispositions(self):
        first = self.post()
        working = self.post(
            {**OPENING, "state": "WORKING"},
            principal="writer-b", key="evidence-work", revision=first["event_id"],
        )
        self.assert_code("context_required", self.post, {**OPENING, "state": "RESOLVED", "evidence_refs": [], "criteria_refs": []}, principal="writer-b", key="no-evidence", revision=working["event_id"])
        resolved = self.post({**OPENING, "state": "RESOLVED", "evidence_refs": ["evidence-1"]}, principal="writer-b", key="resolved-with-evidence", revision=working["event_id"])
        # This independent acceptor is not self-accepting; closure is invalid
        # solely because it omits the required criterion disposition.
        self.assert_code("invalid_transition", self.post, {
            **OPENING,
            "state": "CLOSED",
            "accepted_by": "reviewer",
        }, principal="reviewer", key="close-without-disposition", revision=resolved["event_id"])

    def test_mvp_cmp_05_context_audit_is_reconstructable(self):
        receipt = self.receipt(); self.post(receipt=receipt)
        kinds = {row["kind"] for row in self.ledger.context_audit()}
        self.assertTrue({"bundle_issued", "item_retrieved", "receipt_issued", "receipt_consumed"} <= kinds)

    def test_mvp_cmp_06_operator_stop_is_immediate_and_agents_cannot_set_it(self):
        self.assert_code("forbidden", self.ledger.set_operator_stop, "writer-a", True, "no")
        stopped = self.ledger.set_operator_stop("operator", True, "hold")
        self.assertTrue(stopped["active"])
        self.assert_code("stopped", self.post)

    def test_mvp_cmp_07_api_surfaces_attestation_limit(self):
        bundle = self.bundle()
        self.assertIn("does_not_prove_comprehension", bundle["limitations"])

    def test_mvp_cmp_08_receipt_consumption_is_one_time_and_rolls_back_with_write(self):
        receipt = self.receipt()
        self.ledger.inject_failure("before_commit")
        self.assert_code("unavailable", self.post, receipt=receipt)
        self.assertIsNone(self.ledger.receipt_consumption(receipt))
        self.ledger.clear_failure(); self.post(receipt=receipt)
        self.assertIsNotNone(self.ledger.receipt_consumption(receipt))

    def test_mvp_cmp_09_two_writers_cannot_claim_the_same_revision(self):
        opening = self.post()
        revision = opening["event_id"]
        payload = {**OPENING, "state": "WORKING", "body": "one current revision, one successor"}
        receipts = [self.receipt("writer-b", "request:work", "thread-alpha", revision) for _ in range(2)]
        barrier = Barrier(2)

        def attempt(index):
            db = connect(self.db_path)
            ledger = NativeLedger(
                db,
                context_manifest=MANIFEST,
                governance_authority=self.authority_proof(MANIFEST),
                authority_verifier=self.authority_verifier,
                authority_public_key=self.authority_public_key,
                authority_signature=self.authority_signature(self.authority_proof(MANIFEST)),
            )
            try:
                barrier.wait(timeout=5)
                result = ledger.post_event("writer-b", f"collision-{index}", receipts[index], revision, payload)
                return "committed", result["event_id"]
            except Exception as exc:
                return "rejected", getattr(exc, "code", None)
            finally:
                db.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))

        self.assertEqual(1, sum(status == "committed" for status, _ in results), results)
        self.assertEqual(["conflict"], [detail for status, detail in results if status == "rejected"], results)
        events = [event for event in self.ledger.events_since(0) if event["thread_id"] == "thread-alpha"]
        self.assertEqual([0, 1], [event["thread_ordinal"] for event in events])

    def test_mvp_gov_01_manifest_references_governance_without_defining_statement(self):
        bundle = self.bundle()
        self.assertIn("governance", bundle)
        self.assertNotIn("Statement", self.ledger.required_kinds())
