"""Registry-to-ledger audit adapter contracts."""
from __future__ import annotations

import hashlib

from registrar.tests.mvp_fixture import NativeLedgerCase


class RegistryAuditTests(NativeLedgerCase):
    def test_mvp_reg_01_registry_retirement_preserves_history(self):
        self.ledger.registry_mutate("registry-admin", "register", {"agent_id": "a"})
        self.ledger.registry_mutate("registry-admin", "retire", {"agent_id": "a"})
        self.assertEqual("retired", self.ledger.registry_query("a")["status"])
        self.assertTrue(self.ledger.registry_history("a"))

    def test_mvp_reg_02_mutation_and_hashed_uuid_outbox_are_atomic_and_idempotent(self):
        result = self.ledger.registry_mutate("registry-admin", "register", {"agent_id": "a"})
        outbox = self.ledger.registry_outbox(result["event_uuid"])
        self.assertEqual(result["event_uuid"], outbox["event_uuid"])
        self.assertEqual(hashlib.sha256(outbox["canonical_payload"].encode()).hexdigest(), outbox["payload_sha256"])
        self.assertEqual(result, self.ledger.registry_mutate("registry-admin", "register", {"agent_id": "a"}, event_uuid=result["event_uuid"]))

    def test_mvp_reg_03_crash_after_registry_commit_reconciles_one_ledger_audit_without_cross_rollback(self):
        result = self.ledger.registry_mutate("registry-admin", "register", {"agent_id": "a"}, deliver=False)
        self.assertEqual([], self.ledger.registry_audit_events(result["event_uuid"]))
        self.ledger.reconcile_registry_outbox()
        self.assertEqual(1, len(self.ledger.registry_audit_events(result["event_uuid"])))
