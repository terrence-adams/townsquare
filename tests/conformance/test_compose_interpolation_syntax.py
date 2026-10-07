"""Compose interpolation must remain valid YAML before Docker evaluates it."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILES = (
    ROOT / "compose.yml",
    ROOT / "compose.nas.yml",
    ROOT / "registrar" / "compose.example.yml",
    ROOT / "viewer" / "compose.yml",
)


class ComposeInterpolationSyntaxContract(unittest.TestCase):
    def test_required_interpolations_are_quoted_yaml_scalars(self):
        """`:?` messages contain `:` and must not be YAML plain scalars."""
        required = re.compile(r"\$\{[^}\n]*:\?[^}\n]*\}")

        for path in COMPOSE_FILES:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                for line_number, line in enumerate(text.splitlines(), start=1):
                    for expression in required.finditer(line):
                        before = line[:expression.start()]
                        after = line[expression.end():]
                        self.assertEqual(
                            1,
                            before.count('"') % 2,
                            f"{path.relative_to(ROOT)}:{line_number} has an unquoted required interpolation",
                        )
                        self.assertIn('"', after, f"{path.relative_to(ROOT)}:{line_number} lacks a closing quote")

    @unittest.skipUnless(shutil.which("docker"), "Docker Compose is not installed in this test environment")
    def test_docker_compose_parses_the_release_and_nas_overlay(self):
        """Exercise the actual Compose/YAML parser when Docker is available."""
        values = {
            "TOWNSQUARE_LEDGER_IMAGE": "example.invalid/townsquare-ledger@sha256:" + "0" * 64,
            "TOWNSQUARE_VIEWER_IMAGE": "example.invalid/townsquare-viewer@sha256:" + "1" * 64,
            "TOWNSQUARE_REGISTRY_IMAGE": "example.invalid/townsquare-registry@sha256:" + "2" * 64,
            "TOWNSQUARE_BACKUP_IMAGE": "example.invalid/townsquare-backup@sha256:" + "3" * 64,
            "TOWNSQUARE_PYTHON_IMAGE": "python@sha256:" + "4" * 64,
            "TOWNSQUARE_AGE_VERSION": "1.2.0-1",
            "TOWNSQUARE_MINISIGN_VERSION": "0.11-1",
            "TOWNSQUARE_LEDGER_PORT": "8786",
            "TOWNSQUARE_VIEWER_PORT": "8791",
        }
        path_values = (
            "TOWNSQUARE_LEDGER_DATA_DIR",
            "TOWNSQUARE_REGISTRY_DATA_DIR",
            "TOWNSQUARE_BACKUP_DIR",
            "TOWNSQUARE_TOKEN_PEPPER_FILE",
            "TOWNSQUARE_CURSOR_SIGNING_KEY_FILE",
            "TOWNSQUARE_RECEIPT_HASH_KEY_FILE",
            "TOWNSQUARE_VIEWER_API_TOKEN_FILE",
            "TOWNSQUARE_REGISTRY_API_TOKEN_FILE",
            "TOWNSQUARE_REGISTRY_LEDGER_AUDIT_TOKEN_FILE",
            "TOWNSQUARE_REGISTRY_LEDGER_READINESS_TOKEN_FILE",
            "TOWNSQUARE_LEDGER_REGISTRY_READINESS_TOKEN_FILE",
            "TOWNSQUARE_BACKUP_RECIPIENT_FILE",
            "TOWNSQUARE_CONTEXT_MANIFEST",
            "TOWNSQUARE_AUTHORITY_PUBLIC_KEY_FILE",
            "TOWNSQUARE_AUTHORITY_PROOF_FILE",
            "TOWNSQUARE_AUTHORITY_SIGNATURE_FILE",
        )
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            for name in path_values:
                target = temp / name.lower()
                target.write_text("test", encoding="utf-8")
                values[name] = str(target)
            values["TOWNSQUARE_LEDGER_DATA_DIR"] = str(temp / "ledger")
            values["TOWNSQUARE_REGISTRY_DATA_DIR"] = str(temp / "registry")
            values["TOWNSQUARE_BACKUP_DIR"] = str(temp / "backup")
            for name in ("TOWNSQUARE_LEDGER_DATA_DIR", "TOWNSQUARE_REGISTRY_DATA_DIR", "TOWNSQUARE_BACKUP_DIR"):
                Path(values[name]).mkdir()
            env_file = temp / "release.env"
            env_file.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")
            release = subprocess.run(
                ["docker", "compose", "--env-file", str(env_file), "-f", "compose.yml", "-f", "compose.nas.yml", "config", "--quiet"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )

            registrar_data = temp / "registrar-data"
            registrar_backup = temp / "registrar-backup"
            registrar_data.mkdir()
            registrar_backup.mkdir()
            registrar_env = temp / "registrar.env"
            registrar_env.write_text(
                "\n".join((
                    "REGISTRAR_UID=10001", "REGISTRAR_GID=10001",
                    f"REGISTRAR_DATA_DIR={registrar_data}", f"REGISTRAR_BACKUP_DIR={registrar_backup}",
                    f"REGISTRAR_TOKEN_PEPPER_FILE={temp / 'registrar-pepper'}",
                    f"REGISTRAR_CURSOR_KEY_FILE={temp / 'registrar-cursor'}",
                )) + "\n", encoding="utf-8",
            )
            (temp / "registrar-pepper").write_text("test", encoding="utf-8")
            (temp / "registrar-cursor").write_text("test", encoding="utf-8")
            registrar = subprocess.run(
                ["docker", "compose", "--env-file", str(registrar_env), "-f", "compose.example.yml", "config", "--quiet"],
                cwd=ROOT / "registrar", text=True, capture_output=True, check=False,
            )

            viewer_token = temp / "viewer-token"
            viewer_token.write_text("test", encoding="utf-8")
            viewer_env = temp / "viewer.env"
            viewer_env.write_text(f"VIEWER_TOKEN_FILE={viewer_token}\n", encoding="utf-8")
            viewer = subprocess.run(
                ["docker", "compose", "--env-file", str(viewer_env), "-f", "compose.yml", "config", "--quiet"],
                cwd=ROOT / "viewer", text=True, capture_output=True, check=False,
            )
        for name, result in (("release", release), ("registrar example", registrar), ("viewer", viewer)):
            with self.subTest(compose_file=name):
                self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
