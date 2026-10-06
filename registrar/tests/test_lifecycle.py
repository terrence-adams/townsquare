"""Lifecycle, archive, and stop durability acceptance tests."""
from __future__ import annotations

from registrar.tests.mvp_fixture import NativeLedgerCase, OPENING


class LifecycleTests(NativeLedgerCase):
    def test_mvp_arc_01_archive_is_logical_and_explicitly_readable(self):
        self.post()
        archive = self.ledger.archive_thread("operator", "thread-alpha", "completed")
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
