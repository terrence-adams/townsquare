"""Ledger-side Registry boundary contracts.

Roster mutation, Registry history, and Registry delivery outbox belong to the
separate Registry service.  These tests deliberately reject the removed
same-database convenience API; separate-service integration owns the positive
audit-ingest/retry/reconciliation behavior.
"""
from __future__ import annotations

from registrar.tests.mvp_fixture import NativeLedgerCase


class RegistryAuditTests(NativeLedgerCase):
    def test_mvp_reg_01_embedded_registry_mutation_is_inert(self):
        self.assert_code(
            "forbidden", self.ledger.registry_mutate,
            "registry-admin", "register", {"agent_id": "a"},
        )

    def test_mvp_reg_02_embedded_registry_queries_and_reconciliation_are_inert(self):
        for method, arguments in (
            (self.ledger.registry_query, ("a",)),
            (self.ledger.registry_history, ("a",)),
            (self.ledger.registry_outbox, ("event",)),
        ):
            with self.subTest(method=method.__name__):
                self.assert_code("forbidden", method, *arguments)
        self.assert_code("forbidden", self.ledger.reconcile_registry_outbox)
