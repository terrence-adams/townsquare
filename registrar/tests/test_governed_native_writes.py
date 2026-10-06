"""Release-blocking contracts for governed native Request writes (GOV-RB-01..10).

These checks describe observable facts at the public ledger boundary.  They
do not prescribe tables, event encodings, or a particular policy-engine
implementation.  An adopted authority fixture is intentionally represented
as data so a mounted candidate file can never become its own authorization.
"""
from __future__ import annotations

from registrar.tests.mvp_fixture import MANIFEST, NativeLedgerCase, OPENING


def governed_manifest(**changes):
    """Mounted context stays non-authoritative even when it carries flags."""
    return {**MANIFEST, "governance_authority": {"status": "CANDIDATE", **changes}}


class GovernedNativeWriteTests(NativeLedgerCase):
    REQUEST_ACTIONS = {
        "OPEN": "request:open", "WORKING": "request:work", "BLOCKED": "request:block",
        "RESOLVED": "request:resolve", "CLOSED": "request:accept", "CANCELLED": "request:cancel",
    }

    def install_controlled_lifecycle(self):
        self.ledger.set_context_manifest(governed_manifest())
        self.install_authority_proof(self.authority_proof(governed_manifest()))

    def governed_receipt(self, principal, payload, revision):
        return self.receipt(
            principal,
            self.request_action(payload),
            payload["thread_id"],
            revision,
        )

    def governed_post(self, label, payload, *, principal="writer-a", key="governed", revision="new", receipt=None):
        """Turn an unsupported prerequisite into a readable contract failure."""
        try:
            receipt = receipt or self.governed_receipt(principal, payload, revision)
            return self.ledger.post_event(principal, key, receipt, revision, payload)
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

        # Once each exact selected item is actually retrieved, issuance is
        # permitted and the audit gains retrieval evidence (not a synthetic
        # claim emitted during bundle selection).
        for item in bundle["required_items"]:
            self.ledger.retrieve_context_item(bundle["bundle_id"], item["sha256"], principal="writer-a")
        audit_kinds = {row["kind"] for row in self.ledger.context_audit() if row["bundle_id"] == bundle["bundle_id"]}
        self.assertIn("item_retrieved", audit_kinds)
        receipt = self.ledger.acknowledge_context(
            bundle["bundle_id"], "writer-a", [item["sha256"] for item in bundle["required_items"]]
        )
        self.assertTrue(receipt)

    def test_gov_rb_03_only_resolved_adopted_effective_verified_authority_enables_writes(self):
        rejected = (
            {"decision": "CANDIDATE"},
            {"revoked": True},
            {"status_history_complete": False},
            {"authority_watermark": 0},
            {"effective_from": "2999-01-01T00:00:00Z"},
        )
        for index, change in enumerate(rejected):
            with self.subTest(change=change):
                self.ledger.set_context_manifest(governed_manifest(**change))
                self.install_authority_proof(self.authority_proof(governed_manifest(**change), **change))
                payload = {**OPENING, "thread_id": f"authority-{index}"}
                receipt = self.receipt(thread_id=payload["thread_id"])
                self.assert_code("context_required", self.ledger.post_event, "writer-a", f"authority-{index}", receipt, "new", payload)

    def test_gov_rb_04_request_lifecycle_has_exactly_six_states_and_working_is_progress(self):
        self.install_controlled_lifecycle()
        first = self.governed_post("OPEN", dict(OPENING), key="working-open")
        # CLAIMED/IN_PROGRESS/CORRECTED are not lifecycle states.  CORRECTION
        # remains a purpose/reference on an event carrying its actual state.
        for state in ("CLAIMED", "IN_PROGRESS", "CORRECTED"):
            with self.subTest(state=state):
                payload = {**OPENING, "state": state}
                receipt = self.governed_receipt("writer-b", payload, first["event_id"])
                self.assert_code("invalid_transition", self.ledger.post_event, "writer-b", "not-a-state-" + state, receipt, first["event_id"], payload)
        work_payload = {**OPENING, "state": "WORKING"}
        work_receipt = self.receipt("writer-b", "request:work", "thread-alpha", first["event_id"])
        self.assertEqual("request:work", self.ledger.receipt_record(work_receipt)["permitted_action"])
        working = self.governed_post("WORKING claim/start", work_payload, principal="writer-b", key="working-claim", revision=first["event_id"], receipt=work_receipt)
        self.assertEqual("WORKING", self.ledger.current_projection()["threads"][0]["state"])
        progress = self.governed_post("WORKING progress", {**OPENING, "state": "WORKING", "body": "progress note"}, principal="writer-b", key="working-progress", revision=working["event_id"])
        blocked = self.governed_post("BLOCKED", {**OPENING, "state": "BLOCKED", "body": "blocker named"}, principal="writer-b", key="working-block", revision=progress["event_id"])
        resumed = self.governed_post("BLOCKED to WORKING", {**OPENING, "state": "WORKING"}, principal="writer-b", key="working-resume", revision=blocked["event_id"])
        self.governed_post("WORKING to RESOLVED", {**OPENING, "state": "RESOLVED", "evidence_refs": ["evidence-1"]}, principal="writer-b", key="working-resolve", revision=resumed["event_id"])

    def test_gov_rb_05_ownership_addressee_and_criteria_are_required_and_carried_from_history(self):
        self.install_controlled_lifecycle()
        missing_owner = {key: value for key, value in OPENING.items() if key != "owner"}
        missing_owner["thread_id"] = "missing-owner-thread"
        with self.subTest("opening requires ownership facts"):
            receipt = self.governed_receipt("writer-a", missing_owner, "new")
            self.assert_code("invalid", self.ledger.post_event, "writer-a", "missing-owner", receipt, "new", missing_owner)

        first = self.governed_post("OPEN", dict(OPENING), key="owner-open")
        working = self.governed_post(
            "WORKING",
            {**OPENING, "state": "WORKING"},
            principal="writer-b", key="work-by-addressee", revision=first["event_id"],
        )
        with self.subTest("later metadata cannot replace opening owner"):
            self.assert_code(
                "forbidden",
                self.post,
                {**OPENING, "state": "WORKING", "owner": "writer-b"},
                principal="writer-b",
                key="replace-owner",
                revision=working["event_id"],
            )

    def test_gov_rb_06_closure_independence_uses_complete_history_not_client_metadata(self):
        self.install_controlled_lifecycle()
        opening = self.governed_post("OPEN", dict(OPENING), key="history-open")
        working = self.governed_post("WORKING",
            {**OPENING, "state": "WORKING"},
            principal="writer-b", key="work-by-b", revision=opening["event_id"],
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
        self.install_controlled_lifecycle()
        payload = {**OPENING, "thread_id": "statement-thread", "kind": "STATEMENT"}
        receipt = self.governed_receipt("writer-a", payload, "new")
        self.assert_code(
            "invalid",
            self.ledger.post_event, "writer-a", "statement-with-request-lifecycle", receipt, "new", payload,
        )

    def test_gov_rb_08_archive_requires_current_context_and_eligible_terminal_thread(self):
        self.install_controlled_lifecycle()
        self.governed_post("OPEN", dict(OPENING), key="archive-open")
        self.assert_code("context_required", self.ledger.archive_thread, "operator", "thread-alpha", "premature archive")

    def test_gov_rb_09_continues_must_target_an_eligible_archived_terminal_predecessor(self):
        self.install_controlled_lifecycle()
        self.governed_post("OPEN", dict(OPENING), key="continues-open")
        payload = {
            **OPENING,
            "thread_id": "thread-beta",
            "continues": {"thread_id": "thread-alpha", "relation": "continues"},
        }
        receipt = self.governed_receipt("writer-a", payload, "new")
        self.assert_code(
            "invalid",
            self.ledger.post_event, "writer-a", "continues-open-predecessor", receipt, "new", payload,
        )

    def test_terminal_work_continues_only_in_a_linked_new_thread(self):
        self.install_controlled_lifecycle()
        opening = self.governed_post("OPEN", dict(OPENING), key="terminal-open")
        cancelled = self.governed_post(
            "CANCELLED", {**OPENING, "state": "CANCELLED"},
            principal="writer-b", key="terminal-cancel", revision=opening["event_id"],
        )
        archive_receipt = self.receipt("operator", "request:archive", "thread-alpha", cancelled["event_id"])
        self.ledger.archive_thread(
            "operator", "thread-alpha", "superseded",
            context_receipt=archive_receipt, expected_revision=cancelled["event_id"],
        )
        continued = self.governed_post(
            "linked continuation",
            {**OPENING, "thread_id": "thread-beta", "continues": {"thread_id": "thread-alpha", "relation": "continues"}},
            principal="writer-a", key="terminal-continuation", revision="new",
        )
        event = self.ledger.get_thread(continued["thread_id"])["events"][0]
        self.assertEqual({"thread_id": "thread-alpha", "relation": "continues"}, event["continues"])

    def test_gov_rb_10_action_capabilities_are_distinct_not_coarse_post_write(self):
        self.install_controlled_lifecycle()
        payload = {**OPENING, "thread_id": "capability-thread"}
        receipt = self.governed_receipt("writer-b", payload, "new")
        # writer-b is allowed to work/accept in the adopted authority, but
        # has no `request:open`; an old blanket post:write must not bypass it.
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
