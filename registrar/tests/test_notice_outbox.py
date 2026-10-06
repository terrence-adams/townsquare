"""Notification is durable, pointer-only, and cannot alter authority."""
from __future__ import annotations

from registrar.tests.mvp_fixture import NativeLedgerCase


class NoticeOutboxTests(NativeLedgerCase):
    def test_mvp_ntf_01_commit_creates_one_immutable_pointer_intent(self):
        commit = self.post()
        intent = self.ledger.notice_intents(event_id=commit["event_id"])[0]
        self.assertEqual({"notice_id", "event_id"}, set(intent["pointer"]))
        self.assert_code("forbidden", self.ledger.update_notice_intent, intent["notice_id"], {})

    def test_mvp_ntf_02_delivery_faults_are_bounded_and_visible_without_launch(self):
        intent = self.ledger.notice_intents(event_id=self.post()["event_id"])[0]
        for outcome in ("duplicate", "adapter_outage", "malformed_pointer", "backlog", "stopped"):
            self.ledger.record_notice_attempt(intent["notice_id"], outcome)
        self.assertLessEqual(len(self.ledger.notice_attempts(intent["notice_id"])), 5)
        self.assertEqual(0, self.ledger.launch_count())

    def test_mvp_ntf_03_recipient_must_fetch_fresh_context_before_write(self):
        self.post()
        self.assert_code("context_required", self.post, principal="writer-b", key="recipient")

    def test_mvp_ntf_04_attempts_append_and_status_is_derived(self):
        intent = self.ledger.notice_intents(event_id=self.post()["event_id"])[0]
        self.ledger.record_notice_attempt(intent["notice_id"], "failed")
        self.ledger.record_notice_attempt(intent["notice_id"], "delivered")
        attempts = self.ledger.notice_attempts(intent["notice_id"])
        self.assertEqual([1, 2], [a["attempt_number"] for a in attempts])
        self.assertEqual("delivered", self.ledger.notice_status(intent["notice_id"]))
