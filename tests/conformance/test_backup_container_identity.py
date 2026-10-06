"""Static contract for the backup image's non-root account."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IDENTITY = "10004:10004"


class BackupContainerIdentityContract(unittest.TestCase):
    def test_backup_account_avoids_base_image_name_collision_and_matches_compose(self):
        dockerfile = (ROOT / "backup/Dockerfile").read_text(encoding="utf-8")
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")

        self.assertNotRegex(dockerfile, r"addgroup --system --gid 10004 backup(?:\s|$)")
        self.assertNotRegex(dockerfile, r"adduser --system --uid 10004 --ingroup backup(?:\s|$)")
        self.assertRegex(
            dockerfile,
            rf"addgroup --system --gid 10004 townsquare-backup"
            rf" && adduser --system --uid 10004 --ingroup townsquare-backup"
            rf" --home /nonexistent townsquare-backup",
        )
        self.assertIn(f"COPY --chown={IDENTITY}", dockerfile)
        self.assertIn(f"USER {IDENTITY}", dockerfile)

        backup_block = re.search(r"(?ms)^  backup:\n(.*?)(?=^[^ ]|\Z)", compose)
        self.assertIsNotNone(backup_block)
        self.assertIn(f'user: "{IDENTITY}"', backup_block.group(0))


if __name__ == "__main__":
    unittest.main()
