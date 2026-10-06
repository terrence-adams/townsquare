"""Lifecycle, archive, and stop durability acceptance tests."""
from __future__ import annotations

from registrar.tests.mvp_fixture import NativeLedgerCase, OPENING


class LifecycleTests(NativeLedgerCase):
    def test_mvp_arc_01_archive_is_logical_and_explicitly_readable(self):
        opening = self.post()
        claimed = self.post(
            {**OPENING, "state": "CLAIMED"},
            principal="writer-b", key="archive-claim", revision=opening["event_id"],
        )
        started = self.post(
            {**OPENING, "state": "IN_PROGRESS"},
            principal="writer-b", key="archive-start", revision=claimed["event_id"],
        )
        resolved = self.post(
            {**OPENING, "state": "RESOLVED", "evidence_refs": ["archive-evidence"]},
            principal="writer-b", key="archive-resolve", revision=started["event_id"],
        )
        closed = self.post(
            {**OPENING, "state": "CLOSED", "accepted_by": "reviewer", "criterion_dispositions": {"criterion-1": "accepted"}},
            principal="reviewer", key="archive-accept", revision=resolved["event_id"],
        )
        archive_receipt = self.receipt(
            principal="operator", action="archive", thread_id="thread-alpha", revision=closed["event_id"],
        )
        archive = self.ledger.archive_thread(
            "operator", "thread-alpha", "completed",
            context_receipt=archive_receipt, expected_revision=closed["event_id"],
        )
        self.assertTrue(archive["event_id"])
        self.assertNotIn("thread-alpha", [r["thread_id"] for r in self.ledger.open_work()])
        self.assertEqual("thread-alpha", self.ledger.get_thread("thread-alpha", include_archived=True)["thread_id"])

    def test_mvp_sec_03_stop_is_durable_and_only_distinct_resume_reopens_writes(self):
        self.ledger.set_operator_stop("operator", True, "hold")
        self.assert_code("forbidden", self.ledger.set_operator_stop, "operator", False, "wrong capability")
        self.ledger.set_operator_resume("operator-resume", "resume")
        self.post()

    def test_mvp_sec_02_payload_actor_spoofing_and_invalid_delegation_fail_closed(self):
        spoof = {**OPENING, "represented_actor": "operator"}
        self.assert_code("forbidden", self.post, spoof)
        self.assert_code("forbidden", self.ledger.post_event, "delegate", "bad-delegation", self.receipt("delegate"), "new", OPENING)
