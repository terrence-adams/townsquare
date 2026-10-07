"""TSC-GATE-01/TSC-BND-01/TSC-ROE correction-append regressions."""
from __future__ import annotations

import json

from registrar.tests.mvp_fixture import NativeLedgerCase, OPENING


class CharterCorrectionAppendTests(NativeLedgerCase):
    def correction(self, target_event_id, **changes):
        return {
            **OPENING,
            "purpose": "CORRECTION",
            "corrects_event": target_event_id,
            "body": "informational correction",
            **changes,
        }

    def correction_receipt(self, revision):
        return self.receipt("writer-a", "request:correct", "thread-alpha", revision)

    def test_tsc_gate_01_missing_authority_allows_informational_correction_only(self):
        opening = self.post(key="missing-authority-opening")
        self.ledger.clear_authority_proof()
        correction = self.ledger.post_event(
            "writer-a", "missing-authority-correction", self.correction_receipt(opening["event_id"]),
            opening["event_id"], self.correction(opening["event_id"]),
        )

        self.assertTrue(correction["informational_append"])
        self.assertFalse(correction["effect_applied"])
        self.assertEqual(
            correction,
            self.ledger.post_event(
                "writer-a", "missing-authority-correction", "not-a-valid-receipt",
                opening["event_id"], self.correction(opening["event_id"]),
            ),
        )
        audit = self.db.execute(
            "SELECT disposition,reason_code FROM governance_resolution_audit ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(("UNKNOWN", "authority_source_absent"), tuple(audit))
        self.assertNotIn("missing-authority-correction", audit["reason_code"])

    def test_tsc_gate_01_denied_authority_correction_cannot_create_a_thread_or_effect(self):
        self.ledger.clear_authority_proof()
        attempted = self.correction("not-an-existing-event")
        receipt = self.correction_receipt("new")

        self.assert_code(
            "invalid_transition", self.ledger.post_event,
            "writer-a", "denied-new-correction", receipt, "new", attempted,
        )
        self.assertEqual(0, len(self.ledger.events_since(0)))
        for table in (
            "notice_intents", "native_requests", "control_events", "logical_archives",
            "governance_resolution_audit",
        ):
            with self.subTest(table=table):
                self.assertEqual(0, self.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
        self.assertEqual([], self.ledger.current_projection()["threads"])
        self.assertIsNone(self.ledger._governance_authority)

    def test_tsc_bnd_01_failed_authority_allows_correction_but_not_ordinary_write(self):
        opening = self.post(key="failed-authority-opening")
        self.install_authority_proof(self.authority_proof(decision="REJECT"))
        correction = self.ledger.post_event(
            "writer-a", "failed-authority-correction", self.correction_receipt(opening["event_id"]),
            opening["event_id"], self.correction(opening["event_id"]),
        )

        self.assertTrue(correction["informational_append"])
        self.assert_code(
            "context_required", self.post, {**OPENING, "thread_id": "ordinary-denied"},
            key="failed-authority-ordinary",
        )

    def test_tsc_roe_02_active_ordinary_stop_allows_correction_but_not_effect(self):
        opening = self.post(key="stopped-correction-opening")
        self.ledger.set_operator_stop("operator", True, "ordinary effects paused")
        correction = self.ledger.post_event(
            "writer-a", "stopped-correction", self.correction_receipt(opening["event_id"]),
            opening["event_id"], self.correction(opening["event_id"]),
        )

        self.assertTrue(correction["informational_append"])
        self.assert_code(
            "stopped", self.post, {**OPENING, "thread_id": "stopped-ordinary"}, key="stopped-ordinary",
        )

    def test_tsc_roe_02_forged_protected_operator_claim_is_not_a_correction(self):
        opening = self.post(key="forged-claim-opening")
        forged = self.correction(opening["event_id"], represented_actor="operator")
        self.assert_code(
            "forbidden", self.ledger.post_event,
            "writer-a", "forged-operator-correction", self.correction_receipt(opening["event_id"]),
            opening["event_id"], forged,
        )
        self.assertEqual(1, len(self.ledger.events_since(0)))
        self.assertEqual(0, self.db.execute("SELECT count(*) FROM control_events").fetchone()[0])

    def test_tsc_roe_03_non_correction_behavior_is_unchanged(self):
        self.ledger.clear_authority_proof()
        self.assert_code("context_required", self.post, key="ordinary-missing-authority")

    def test_tsc_roe_03_correction_is_append_only_and_cannot_transition_or_accept(self):
        opening = self.post(key="informational-opening")
        correction = self.ledger.post_event(
            "writer-a", "informational-correction", self.correction_receipt(opening["event_id"]),
            opening["event_id"], self.correction(opening["event_id"]),
        )

        self.assertEqual("OPEN", self.ledger.current_projection()["threads"][0]["state"])
        stored = self.db.execute(
            "SELECT authority_scope,metadata_json FROM ledger_events WHERE event_id=?", (correction["event_id"],)
        ).fetchone()
        self.assertEqual("informational:correction", stored["authority_scope"])
        self.assertEqual("CORRECTION", json.loads(stored["metadata_json"])["purpose"])
        self.assert_code(
            "invalid_transition", self.ledger.post_event,
            "writer-a", "correction-cannot-close", self.correction_receipt(correction["event_id"]),
            correction["event_id"], self.correction(opening["event_id"], state="CLOSED", accepted_by="writer-a"),
        )
        self.assertEqual("OPEN", self.ledger.current_projection()["threads"][0]["state"])
