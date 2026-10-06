"""Security behavior that the MVP itself, not a deployment worksheet, must enforce."""
from __future__ import annotations

from registrar.tests.mvp_fixture import NativeLedgerCase, OPENING


class SecurityMvpTests(NativeLedgerCase):
    def test_mvp_sec_01_capability_matrix_rejects_anonymous_expired_revoked_and_operator_escalation(self):
        for principal in (None, "expired-writer", "revoked-writer", "viewer"):
            with self.subTest(principal=principal): self.assert_code("forbidden", self.post, principal=principal, key="sec-" + str(principal))
        self.assert_code("forbidden", self.ledger.issue_operator_credential, "writer-a")

    def test_mvp_sec_06_receipts_are_hashed_one_time_redacted_and_short_lived(self):
        receipt = self.receipt(); record = self.ledger.receipt_record(receipt)
        self.assertNotIn(receipt, repr(record))
        self.assertIn("token_hash", record)
        self.assertLessEqual(record["ttl_seconds"], 900)
        self.post(receipt=receipt)
        self.assert_code("context_required", self.post, key="replay", receipt=receipt)

    def test_mvp_sec_07_core_has_no_runner_and_notices_reject_injection(self):
        self.assertFalse(self.ledger.runner_enabled())
        self.assert_code("invalid", self.ledger.validate_notice_pointer, {"notice_id": "n", "event_id": "e", "url": "http://bad"})

    def test_mvp_sec_08_content_validation_and_restricted_read_are_safe(self):
        for change in ({"media_type": "application/x-shellscript"}, {"sensitivity": None}, {"body": "x" * (2 ** 20 + 1)}):
            with self.subTest(change=change): self.assert_code("invalid", self.post, {**OPENING, **change}, key="bad-" + str(change))
        restricted = self.post({**OPENING, "thread_id": "restricted", "sensitivity": "RESTRICTED"}, key="restricted")
        self.assert_code("forbidden", self.ledger.get_thread, "restricted", principal="viewer")

    def test_mvp_sec_10_registry_audit_credential_is_fixed_schema_and_actor_only(self):
        good = {"board": "BOARD-AUDIT-RECORD", "actor": "registry", "event_uuid": "u"}
        self.ledger.append_registry_audit("registry-audit", good)
        self.assert_code("forbidden", self.ledger.append_registry_audit, "registry-audit", {**good, "actor": "operator"})

    def test_mvp_sec_13_hostile_content_is_rendered_inertly(self):
        payload = {**OPENING, "body": "<script>x</script> javascript:alert(1) {{template}}; rm -rf"}
        self.post(payload, key="hostile")
        rendered = self.ledger.render_event("thread-alpha")
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("javascript:", rendered.lower())
