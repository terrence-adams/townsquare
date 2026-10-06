"""Read-model acceptance tests; a derived view must tell the truth about gaps."""
from __future__ import annotations

from registrar.tests.mvp_fixture import NativeLedgerCase


class CrierProjectionTests(NativeLedgerCase):
    def test_mvp_read_01_discovery_exposes_work_history_boards_hierarchy_registry_and_findings(self):
        self.post()
        view = self.ledger.discovery_projection()
        self.assertTrue({"open_work", "history", "boards", "projects", "registry", "findings"} <= set(view))

    def test_mvp_read_02_read_credentials_cannot_write_or_mutate(self):
        for principal in ("viewer", "crier", "projector"):
            with self.subTest(principal=principal):
                self.assert_code("forbidden", self.post, principal=principal, key="read-" + principal)

    def test_mvp_read_03_dependency_failure_is_unknown_or_degraded_not_empty_success(self):
        self.ledger.set_projection_dependency("registry", available=False)
        view = self.ledger.discovery_projection()
        self.assertEqual("DEGRADED", view["registry"]["status"])
        self.assertNotEqual([], view["registry"].get("findings", []))
