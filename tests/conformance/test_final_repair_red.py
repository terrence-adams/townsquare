"""Final release-repair contracts.  These intentionally name missing release gates."""
from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FinalRepairContracts(unittest.TestCase):
    def text(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_authority_proof_requires_detached_minisign_and_public_key_only(self):
        source = self.text("registrar/app/native_ledger.py")
        self.assertIn("minisign", source.lower(), "authority proof must invoke detached Minisign verification")
        self.assertNotIn("hmac.compare_digest(signature", source, "HMAC-like authority proofs are not external adoption")
        self.assertNotIn("AUTHORITY_RESOLVER_KEY_FILE", source, "Ledger must not hold an authority signing key")
        self.assertIn("AUTHORITY_PUBLIC_KEY", source, "Ledger verifies only a pinned public key")

    def test_nas_overlay_refers_only_to_ledger_migrate(self):
        overlay = self.text("compose.nas.yml")
        self.assertIn("  ledger-migrate:\n", overlay)
        self.assertNotIn("  migrate:\n", overlay)
        merged = self.text("compose.yml") + overlay
        self.assertEqual(1, merged.count("  ledger-migrate:\n"))
        self.assertEqual(1, merged.count("  registry-migrate:\n"))

    def test_readiness_is_active_peer_tuple_exchange_not_environment_self_attestation(self):
        ledger = self.text("registrar/app/main.py")
        registry = self.text("registry/app.py")
        self.assertIn("REGISTRY_READINESS_URL", ledger)
        self.assertIn("urllib.request.urlopen", ledger)
        self.assertIn("LEDGER_READINESS_URL", registry)
        self.assertIn("urllib.request.urlopen", registry)

    def test_registry_recovers_stranded_outbox_with_claim_lease_and_periodic_worker(self):
        source = self.text("registry/app.py")
        self.assertIn("lease_until", source)
        self.assertIn("claim", source.lower())
        self.assertIn("periodic", source.lower())
        self.assertIn("threading.Thread", source)

    def test_registry_journal_and_outbox_are_append_only_with_recoverable_lease_state(self):
        schema = self.text("registry/schema.sql")
        self.assertIn("journal_no_update", schema)
        self.assertIn("journal_no_delete", schema)
        self.assertIn("audit_outbox_no_delete", schema)
        self.assertIn("lease_owner", schema)
        self.assertIn("lease_until", schema)

    def test_backup_image_is_offline_staged_and_dockerignore_protects_release_secrets(self):
        dockerfile = self.text("backup/Dockerfile").lower()
        ignore = self.text(".dockerignore")
        self.assertNotIn("apt-get", dockerfile)
        self.assertNotIn("apt ", dockerfile)
        self.assertIn("wheelhouse", dockerfile)
        self.assertIn(".env", ignore)
        self.assertIn(".env.*", ignore)
        self.assertIn("release.env*", ignore)
        self.assertIn("secrets/", ignore)
        self.assertIn("*.key", ignore)

    def test_backup_and_restore_record_domain_watermarks_parity_and_reconciliation(self):
        create = self.text("backup/create-backup.py")
        restore = self.text("backup/restore-drill.py")
        for value in ("closed_fsynced_copy", "plaintext_sha256", "ciphertext_sha256", "schema_head", "ledger_watermark", "registry_journal_watermark", "lease_state", "non_atomic_domains"):
            with self.subTest(value=value):
                self.assertIn(value, create)
        self.assertIn("reconciliation", restore)
        self.assertIn("pending", restore)

    def test_restore_reconciles_pending_registry_event_exactly_once(self):
        restore = self.text("backup/restore-drill.py")
        registry = self.text("registry/app.py")
        self.assertIn("reconcile", restore.lower())
        self.assertIn("event_uuid", restore)
        self.assertIn("lease_until", registry)


if __name__ == "__main__":
    unittest.main()
