"""Final Stage-B identity/preexec and backup containment regressions."""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from canary import preexec
from shared.canary_identity import CanaryIdentityError, verify_canary_identity
from tests.conformance.test_canary_containment import ROOT, identity_environment


class ReleaseIdentityAllRolesTests(unittest.TestCase):
    def test_every_image_embeds_exact_identity_tuple_and_digest(self):
        for role in ("registrar", "registry", "viewer", "backup"):
            text = (ROOT / role / "Dockerfile").read_text(encoding="utf-8")
            with self.subTest(role=role):
                for field in (
                    "RUNTIME_CLASS", "AUTHORITY_CLASS", "CANARY_LABEL", "COMPOSE_PROJECT",
                    "SOURCE_COMMIT", "SOURCE_TREE", "R7_RELEASE_ID", "R7_INPUT_MANIFEST_SHA256",
                    "R7_IDENTITY_SHA256",
                ):
                    self.assertIn("TOWNSQUARE_EMBEDDED_" + field, text)
                self.assertIn("townsquare.r7-input-manifest-sha256", text)
                self.assertIn("canary.preexec", text)

    def test_each_identity_field_and_combined_override_fail_closed(self):
        valid = identity_environment()
        verify_canary_identity(valid)
        fields = tuple(name for name in valid if name.startswith("TOWNSQUARE_") and "EMBEDDED" not in name)
        for field in fields:
            changed = dict(valid); changed[field] = "altered"
            with self.subTest(field=field), self.assertRaises(CanaryIdentityError): verify_canary_identity(changed)
        changed = dict(valid)
        changed["TOWNSQUARE_SOURCE_COMMIT"] = changed["TOWNSQUARE_EMBEDDED_SOURCE_COMMIT"] = "f" * 40
        changed["TOWNSQUARE_R7_IDENTITY_SHA256"] = changed["TOWNSQUARE_EMBEDDED_R7_IDENTITY_SHA256"] = "9" * 64
        identity = verify_canary_identity(changed)
        self.assertEqual("f" * 40, identity.source_commit)

    def test_all_commands_and_healthchecks_cross_preexec(self):
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")
        following = {"ledger-migrate": "ledger", "registry-audit-worker": "registry-migrate", "registry-migrate": "backup"}
        for role, next_role in following.items():
            block = compose.split(f"\n  {role}:\n", 1)[1].split(f"\n  {next_role}:\n", 1)[0]
            self.assertIn("canary.preexec", block, role)
        self.assertEqual(3, compose.count("test: [CMD, python, -m, canary.preexec"))
        backup = (ROOT / "backup" / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn('ENTRYPOINT ["python","-m","canary.preexec","--"]', backup)

    def test_backup_identity_failure_has_zero_db_recipient_output_or_network_effect(self):
        touched = []
        with mock.patch.object(preexec, "require_canary_identity", side_effect=CanaryIdentityError("rejected")), \
             mock.patch.object(preexec.os, "execvp", side_effect=lambda *_: touched.append("exec")):
            with self.assertRaises(SystemExit): preexec.main(["--", "python", "/opt/townsquare/backup/create-backup.py"])
        self.assertEqual([], touched)
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")
        block = compose.split("\n  backup:\n", 1)[1].split("\nnetworks:\n", 1)[0]
        for required in ('<<: *hardened', 'user: "10004:10004"', "network_mode: none"):
            self.assertIn(required, block)
        hardened = compose.split("x-hardened: &hardened", 1)[1].split("x-registry-r7-build-args", 1)[0]
        for required in ("read_only: true", "cap_drop: [ALL]", "no-new-privileges:true"):
            self.assertIn(required, hardened)
        self.assertNotRegex(block, r"(?m)^\s+ports:")
        self.assertEqual(2, block.count("read_only: true"))
        self.assertIn("target: /var/backups/townsquare", block)


if __name__ == "__main__": unittest.main()
