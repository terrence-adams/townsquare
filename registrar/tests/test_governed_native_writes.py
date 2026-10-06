"""Release-blocking contracts for governed native Request writes (GOV-RB-01..10).

These checks describe observable facts at the public ledger boundary.  They
do not prescribe tables, event encodings, or a particular policy-engine
implementation.  An adopted authority fixture is intentionally represented
as data so a mounted candidate file can never become its own authorization.
"""
from __future__ import annotations

from registrar.tests.mvp_fixture import MANIFEST, NativeLedgerCase, OPENING


ADOPTED_AUTHORITY = {
    "authority_ref": "governance-record-1",
    "digest": "d" * 64,
    "status": "ADOPTED",
    "effective": True,
    "verified": True,
    "capabilities": {
        "writer-a": {"work:open", "work:start", "work:resolve"},
        "writer-b": {"work:claim", "work:block", "work:accept"},
        "operator": {"work:cancel", "work:archive"},
    },
}


def governed_manifest(**changes):
    """Return a shape-valid manifest with an external adopted authority."""
    return {**MANIFEST, "governance_authority": {**ADOPTED_AUTHORITY, **changes}}


class GovernedNativeWriteTests(NativeLedgerCase):
    def governed_post(self, label, *args, **kwargs):
        """Turn an unsupported prerequisite into a readable contract failure."""
        try:
            return self.post(*args, **kwargs)
        except Exception as exc:
            self.fail(f"{label} must be an authorized governed lifecycle action; got {getattr(exc, 'code', type(exc).__name__)}: {exc}")

    def test_gov_rb_01_bundle_binds_current_thread_notes_scope_and_criteria(self):
        initial = self.bundle(thread_id="thread-alpha", revision="new")
        first = self.post()
        current = self.bundle(thread_id="thread-alpha", revision=first["event_id"])

        # A later bundle must be assembled from current authoritative reads,
        # rather than returning the same static manifest items.
        self.assertNotEqual(initial["required_items"], current["required_items"])
        sources = {item.get("source") for item in current["required_items"]}
        self.assertTrue({"thread", "operator_note", "scope", "acceptance_criterion"} <= sources)

    def test_gov_rb_02_selection_retrieval_and_receipt_are_separate_audited_facts(self):
        bundle = self.bundle()
        audit_kinds = {row["kind"] for row in self.ledger.context_audit() if row["bundle_id"] == bundle["bundle_id"]}
        self.assertIn("required_item_selected", audit_kinds)
        self.assertNotIn("item_retrieved", audit_kinds)

        # Seeing a bundle is not evidence of retrieving its selected bytes.
        self.assert_code(
            "context_required",
            self.ledger.acknowledge_context,
            bundle["bundle_id"],
            "writer-a",
            [item["sha256"] for item in bundle["required_items"]],
        )

    def test_gov_rb_03_only_resolved_adopted_effective_verified_authority_enables_writes(self):
        rejected = (
            {"status": "CANDIDATE"},
            {"status": "ADOPTED", "effective": False},
            {"status": "WITHDRAWN"},
            {"status": "SUPERSEDED"},
            {"status": "ADOPTED", "verified": False},
        )
        for index, change in enumerate(rejected):
            with self.subTest(change=change):
                self.ledger.set_context_manifest(governed_manifest(**change))
                payload = {**OPENING, "thread_id": f"authority-{index}"}
                receipt = self.receipt(thread_id=payload["thread_id"])
                self.assert_code("context_required", self.ledger.post_event, "writer-a", f"authority-{index}", receipt, "new", payload)

    def test_gov_rb_04_request_lifecycle_has_six_states_and_correction_is_not_a_state(self):
        first = self.post()
        # Correction is an append-only purpose/reference, not a seventh state.
        self.assert_code(
            "invalid_transition",
            self.post,
            {**OPENING, "state": "CORRECTED", "corrects_event": first["event_id"]},
            key="correction-is-purpose",
            revision=first["event_id"],
        )

    def test_gov_rb_05_ownership_addressee_and_criteria_are_required_and_carried_from_history(self):
        missing_owner = {key: value for key, value in OPENING.items() if key != "owner"}
        missing_owner["thread_id"] = "missing-owner-thread"
        with self.subTest("opening requires ownership facts"):
            self.assert_code("invalid", self.post, missing_owner, key="missing-owner")

        first = self.post()
        claimed = self.governed_post(
            "CLAIMED",
            {**OPENING, "state": "CLAIMED"},
            principal="writer-b", key="claim-by-addressee", revision=first["event_id"],
        )
        with self.subTest("later metadata cannot replace opening owner"):
            self.assert_code(
                "forbidden",
                self.post,
                {**OPENING, "state": "IN_PROGRESS", "owner": "writer-b"},
                principal="writer-b",
                key="replace-owner",
                revision=claimed["event_id"],
            )

    def test_gov_rb_06_closure_independence_uses_complete_history_not_client_metadata(self):
        opening = self.post()
        claimed = self.governed_post("CLAIMED",
            {**OPENING, "state": "CLAIMED"},
            principal="writer-b", key="work-by-b", revision=opening["event_id"],
        )
        working = self.governed_post("IN_PROGRESS",
            {**OPENING, "state": "IN_PROGRESS"},
            principal="writer-b", key="started-by-b", revision=claimed["event_id"],
        )
        resolved = self.governed_post("RESOLVED",
            {**OPENING, "state": "RESOLVED", "evidence_refs": ["evidence-1"]},
            principal="writer-b", key="resolved-by-b", revision=working["event_id"],
        )
        # writer-a authored the opening.  A mutable close payload cannot make
        # that actor independent of the work being accepted.
        self.assert_code(
            "forbidden",
            self.post,
            {**OPENING, "state": "CLOSED", "accepted_by": "writer-a", "criterion_dispositions": {"criterion-1": "accepted"}},
            principal="writer-a", key="history-not-metadata", revision=resolved["event_id"],
        )

    def test_gov_rb_07_only_request_kind_has_an_adopted_governed_lifecycle(self):
        self.assert_code(
            "invalid",
            self.post,
            {**OPENING, "thread_id": "statement-thread", "kind": "STATEMENT"},
            key="statement-with-request-lifecycle",
        )

    def test_gov_rb_08_archive_requires_current_context_and_eligible_terminal_thread(self):
        self.post()
        self.assert_code("context_required", self.ledger.archive_thread, "operator", "thread-alpha", "premature archive")

    def test_gov_rb_09_continues_must_target_an_eligible_archived_terminal_predecessor(self):
        self.post()
        self.assert_code(
            "invalid",
            self.post,
            {
                **OPENING,
                "thread_id": "thread-beta",
                "continues": {"thread_id": "thread-alpha", "relation": "continues"},
            },
            key="continues-open-predecessor",
        )

    def test_gov_rb_10_action_capabilities_are_distinct_not_coarse_post_write(self):
        self.ledger.set_context_manifest(governed_manifest())
        payload = {**OPENING, "thread_id": "capability-thread"}
        receipt = self.receipt(principal="writer-b", thread_id=payload["thread_id"])
        # writer-b is allowed to claim/accept in the adopted authority, but
        # has no `work:open`; an old blanket post:write must not bypass this.
        self.assert_code("forbidden", self.ledger.post_event, "writer-b", "coarse-bypass", receipt, "new", payload)

    def test_governed_notice_reads_are_authorized_stable_and_do_not_infer_delivery(self):
        commit = self.post()
        # These read APIs are deliberately principal-bound.  A write-only
        # caller cannot discover operational routing or attempt history.
        self.assert_code("forbidden", self.ledger.notice_intents, principal="writer-a")

        intents = self.ledger.notice_intents(principal="viewer", event_id=commit["event_id"])
        self.assertEqual(1, len(intents))
        self.assertNotIn("delivery_status", intents[0])
        attempts = self.ledger.notice_attempts(intents[0]["notice_id"], principal="viewer")
        self.assertEqual([], attempts)
