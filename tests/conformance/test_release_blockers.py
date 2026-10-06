"""Release evidence contracts deliberately stronger than file-existence checks."""
from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ReleaseBlockerInspection(unittest.TestCase):
    def test_rb_mig_07_schema_009_fixture_exercises_1070_row_upgrade_and_rollback(self):
        fixture = ROOT / "registrar" / "tests" / "fixtures" / "schema_009_1070.py"
        metadata = ROOT / "registrar" / "tests" / "fixtures" / "schema_009_1070_metadata.json"
        self.assertTrue(
            fixture.is_file(),
            "RB-MIG-07 requires a deterministic schema-009 fixture generator containing 1,070 "
            "representative legacy rows for 010-014 count/content/hash/FK/re-run/rollback tests.",
        )
        evidence = json.loads(metadata.read_text())
        self.assertEqual(1070, evidence["counts"]["posts"])
        self.assertRegex(evidence["logical_sha256"], r"^[0-9a-f]{64}$")

    def test_rb_backup_08_verified_restore_evidence_covers_both_independent_domains(self):
        evidence = json.loads((ROOT / "evidence" / "permissions-and-backup.json").read_text())
        self.assertEqual(
            "VERIFIED", evidence.get("status"),
            "RB-BACKUP-08 requires executed restore evidence, not a template status.",
        )
        required = {
            "closed_fsynced_copy", "plaintext_sha256", "ciphertext_sha256",
            "manifest_signature", "external_signed_checkpoint", "ledger_restore",
            "registry_restore", "reconciliation", "integrity_check", "foreign_key_check",
        }
        self.assertTrue(required <= set(evidence.get("checks", {})))

    def test_rb_pkg_09_release_inputs_are_current_pinned_and_nonempty(self):
        manifest = json.loads((ROOT / "release-manifest.json").read_text())
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        self.assertEqual(head, manifest.get("commit"), "RB-PKG-09 manifest must pin this exact source SHA")
        for image in manifest.get("images", {}).values():
            self.assertRegex(image, r"@sha256:[0-9a-f]{64}$")
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")) for row in manifest.get("dependencies", [])))
        wheelhouse = json.loads((ROOT / "wheelhouse.lock.json").read_text())
        self.assertTrue(wheelhouse.get("wheels"), "RB-PKG-09 requires a nonempty hash-locked offline wheelhouse")
        sbom = json.loads((ROOT / "sbom.cdx.json").read_text())
        self.assertTrue(sbom.get("components"), "RB-PKG-09 requires a nonempty verified SBOM")

    def test_rb_view_10_notice_rendering_has_a_native_scope_boundary(self):
        source = (ROOT / "viewer" / "registrar_client.py").read_text()
        self.assertIn(
            "native_notice", source,
            "RB-VIEW-10 requires an explicit native-only notice read model/scope when "
            "legacy credential unification is deferred; generic principal names are insufficient.",
        )
        self.assertNotIn("delivery_status", source.lower())

    def test_rb_compose_11_declares_one_isolated_migrator_per_domain_and_no_wake_or_registry_port(self):
        raw_compose = (ROOT / "compose.yml").read_text()
        compose = raw_compose.lower()
        self.assertRegex(compose, r"(?m)^  registry:\s*$", "RB-COMPOSE-11 requires a separate Registry service")
        self.assertEqual(1, len(re.findall(r"(?m)^  ledger-migrate:\s*$", compose)))
        self.assertEqual(1, len(re.findall(r"(?m)^  registry-migrate:\s*$", compose)))
        for value in ("townsquare-ledger-v0", "townsquare-registry-v0", "registry-ledger-audit-v1"):
            self.assertIn(value, raw_compose)
        self.assertNotIn("wake", compose)
        registry_block = compose.split("  registry:", 1)[1].split("\n  ", 1)[0]
        self.assertNotIn("ports:", registry_block, "Registry must not publish a host port")
