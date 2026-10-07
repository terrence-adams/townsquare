from __future__ import annotations

import copy
import ast
import io
import json
import os
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path

from canary.safe_archive import CanaryPathError, extract_validated, validated_members
from canary.validate_compose import ComposeValidationError, read_identity_env, validate
from shared.canary_authority import (
    CanaryAuthorityError,
    CanaryProofVerifier,
    SQLiteNonceStore,
    reject_canary_test_in_normal_domain,
)
from shared.canary_identity import (
    EMBEDDED_FIELDS,
    RUNTIME_FIELDS,
    CanaryIdentityError,
    verify_canary_identity,
)
from registrar.app import auth as registrar_auth
from registrar.app.service import Forbidden
from registrar.app.db import connect as ledger_connect, migrate as ledger_migrate
from canary.bootstrap import BootstrapError, SECRET_FILES, bootstrap


ROOT = Path(__file__).resolve().parents[2]
IDENTITY = {
    "TOWNSQUARE_RUNTIME_CLASS": "CANARY",
    "TOWNSQUARE_AUTHORITY_CLASS": "NON-AUTHORITATIVE",
    "TOWNSQUARE_CANARY_LABEL": "TS-CANARY-NAS1-20261007-A",
    "TOWNSQUARE_COMPOSE_PROJECT": "townsquare-canary-20261007-a",
    "TOWNSQUARE_SOURCE_COMMIT": "a" * 40,
    "TOWNSQUARE_SOURCE_TREE": "b" * 40,
    "TOWNSQUARE_R7_RELEASE_ID": "TS-R7-" + "c" * 64,
    "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256": "d" * 64,
}


def identity_environment():
    values = dict(IDENTITY)
    for name, value in IDENTITY.items():
        values["TOWNSQUARE_EMBEDDED_" + name.removeprefix("TOWNSQUARE_")] = value
    return values


def rendered_compose_fixture():
    """Independent representative rendered config, not validator-derived input."""
    environment = {
        "ledger-migrate": {"REGISTRAR_DB": "/var/lib/townsquare/ledger.db", "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json"},
        "ledger": {
            "REGISTRAR_ENV": "canary", "REGISTRAR_DB": "/var/lib/townsquare/ledger.db",
            "REGISTRAR_CURSOR_KEY_FILE": "/run/secrets/ledger-cursor-signing-key",
            "TOWNSQUARE_RECEIPT_HASH_KEY_FILE": "/run/secrets/ledger-receipt-hash-key",
            "TOWNSQUARE_CANARY_TEST_PUBLIC_KEY_FILE": "/run/config/canary-test-authority.pub",
            "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json",
            "TOWNSQUARE_LEDGER_CONTEXT_MANIFEST": "/run/config/ledger-context-manifest.json",
            "TOWNSQUARE_LEDGER_CONTEXT_MANIFEST_SHA256": "f" * 64,
            "REGISTRY_READINESS_TOKEN_FILE": "/run/secrets/ledger-to-registry-readiness",
            "REGISTRY_PEER_READINESS_TOKEN_FILE": "/run/secrets/registry-to-ledger-readiness",
            "TOWNSQUARE_SERVICE_ID": "townsquare-ledger-v0", "TOWNSQUARE_LEDGER_SCHEMA_HEAD": "14",
            "TOWNSQUARE_REGISTRY_AUDIT_CONTRACT": "registry-ledger-audit-v1",
            "REGISTRY_INTEGRATION_ENABLED": "true", "REGISTRY_SERVICE_ID": "townsquare-registry-v0",
            "REGISTRY_SCHEMA_HEAD": "2", "REGISTRY_AUDIT_CONTRACT_VERSION": "registry-ledger-audit-v1",
            "REGISTRY_READINESS_URL": "http://registry:8789/health/ready",
        },
        "registry-migrate": {"REGISTRY_DB": "/var/lib/registry/registry.db", "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json"},
        "registry": {
            "REGISTRY_DB": "/var/lib/registry/registry.db",
            "REGISTRY_TOKEN_FILE": "/run/secrets/registry-api-credential",
            "REGISTRY_LEDGER_AUDIT_TOKEN_FILE": "/run/secrets/registry-audit-credential",
            "LEDGER_READINESS_TOKEN_FILE": "/run/secrets/registry-to-ledger-readiness",
            "REGISTRY_PEER_READINESS_TOKEN_FILE": "/run/secrets/ledger-to-registry-readiness",
            "REGISTRY_CANARY_NONCE_DIRECTORY": "/var/lib/registry/canary-nonces",
            "REGISTRY_AUDIT_DELIVERY_MODE": "manual",
            "REGISTRY_AUDIT_CONTRACT_VERSION": "registry-ledger-audit-v1",
            "REGISTRY_SERVICE_ID": "townsquare-registry-v0", "REGISTRY_SCHEMA_HEAD": "2",
            "REGISTRY_LEDGER_SERVICE_ID": "townsquare-ledger-v0", "REGISTRY_LEDGER_SCHEMA_HEAD": "14",
            "REGISTRY_LEDGER_AUDIT_CONTRACT": "registry-ledger-audit-v1",
            "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json",
        },
        "viewer": {"TOWNSQUARE_VIEWER_PROFILE": "native-ledger-mvp", "REGISTRAR_BASE_URL": "http://ledger:8790", "HOME": "/tmp", "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json"},
    }
    def mount(source, target, readonly=False):
        return {"type": "bind", "source": "/volume1/Docker/townsquare-canary-20261007-a/" + source, "target": target, "read_only": readonly}
    ledger_data = mount("data/ledger", "/var/lib/townsquare")
    registry_data = mount("data/registry", "/var/lib/registry")
    mounts = {
        "ledger-migrate": [ledger_data, mount("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
        "ledger": [ledger_data,
            mount("secrets/ledger-token-pepper", "/run/secrets/ledger-token-pepper", True),
            mount("secrets/ledger-cursor-signing-key", "/run/secrets/ledger-cursor-signing-key", True),
            mount("secrets/ledger-receipt-hash-key", "/run/secrets/ledger-receipt-hash-key", True),
            mount("secrets/ledger-to-registry-readiness.ledger", "/run/secrets/ledger-to-registry-readiness", True),
            mount("secrets/registry-to-ledger-readiness.ledger", "/run/secrets/registry-to-ledger-readiness", True),
            mount("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True),
            mount("config/ledger-context-manifest.json", "/run/config/ledger-context-manifest.json", True),
            mount("config/canary-test-authority.pub", "/run/config/canary-test-authority.pub", True)],
        "registry-migrate": [registry_data, mount("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
        "registry": [registry_data,
            mount("secrets/registry-api-credential", "/run/secrets/registry-api-credential", True),
            mount("secrets/registry-audit-credential", "/run/secrets/registry-audit-credential", True),
            mount("secrets/ledger-to-registry-readiness.registry", "/run/secrets/ledger-to-registry-readiness", True),
            mount("secrets/registry-to-ledger-readiness.registry", "/run/secrets/registry-to-ledger-readiness", True),
            mount("config/canary-test-authority.pub", "/run/config/canary-test-authority.pub", True),
            mount("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
        "viewer": [mount("secrets/viewer-native-credential", "/run/secrets/viewer-native-credential", True), mount("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
    }
    services = {}
    for name, uid, image in (
        ("ledger-migrate", "10001:10001", "townsquare-canary-ledger"),
        ("ledger", "10001:10001", "townsquare-canary-ledger"),
        ("registry-migrate", "10003:10003", "townsquare-canary-registry"),
        ("registry", "10003:10003", "townsquare-canary-registry"),
        ("viewer", "10002:10002", "townsquare-canary-viewer"),
    ):
        services[name] = {
            "environment": {**IDENTITY, **environment[name]}, "user": uid,
            "image": image + ":" + "a" * 40, "volumes": copy.deepcopy(mounts[name]),
            "restart": "no", "read_only": True, "pull_policy": "never",
            "networks": {"canary-internal": None}, "tmpfs": ["/tmp:rw,noexec,nosuid,size=32m,mode=1777"],
            "cap_drop": ["ALL"], "security_opt": ["no-new-privileges:true"],
        }
    services["ledger-migrate"]["command"] = ["python", "-m", "canary.preexec", "--", "python", "-c", "from registrar.app.db import connect,migrate; import os; d=connect(os.environ['REGISTRAR_DB']); migrate(d); d.close()"]
    services["registry-migrate"]["command"] = ["python", "-m", "canary.preexec", "--", "python", "/app/migrate.py"]
    services["ledger"]["networks"] = {"canary-internal": None, "canary-ingress": None}
    services["viewer"]["networks"] = {"canary-internal": None, "canary-ingress": None}
    services["viewer"]["tmpfs"] = ["/tmp:rw,noexec,nosuid,size=64m,mode=1777"]
    services["ledger"]["ports"] = [{"host_ip": "192.168.2.3", "published": "18790", "target": 8790}]
    services["viewer"]["ports"] = [{"host_ip": "192.168.2.3", "published": "18502", "target": 8502}]
    return {
        "name": "townsquare-canary-20261007-a",
        "services": services,
        "networks": {"canary-internal": {"internal": True}, "canary-ingress": {}},
    }


class CanaryIdentityTests(unittest.TestCase):
    def test_every_runtime_and_embedded_field_is_required_and_exact_before_effect(self):
        baseline = identity_environment()
        for name in (*RUNTIME_FIELDS, *EMBEDDED_FIELDS):
            for mode in ("omit", "mutate"):
                candidate = dict(baseline)
                if mode == "omit":
                    candidate.pop(name)
                else:
                    candidate[name] = "wrong"
                effects = []
                with self.assertRaises(CanaryIdentityError, msg=f"{mode} {name}"):
                    verify_canary_identity(candidate)
                    effects.append("socket/db/thread/status/data")
                self.assertEqual([], effects)

    def test_exact_tuple_is_immutable_and_accepted(self):
        identity = verify_canary_identity(identity_environment())
        self.assertEqual(IDENTITY["TOWNSQUARE_SOURCE_TREE"], identity.source_tree)
        with self.assertRaises(Exception):
            identity.source_tree = "c" * 40


class CanaryAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.identity = verify_canary_identity(identity_environment())
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.db.execute("CREATE TABLE verifier_nonces(key_id TEXT,nonce TEXT,used_at TEXT,PRIMARY KEY(key_id,nonce))")
        self.instant = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
        self.proof = {
            "schema": "townsquare-canary-test-proof-v2",
            "authority_class": "CANARY_TEST",
            "canary_label": self.identity.canary_label,
            "compose_project": self.identity.compose_project,
            "source_commit": self.identity.source_commit,
            "source_tree": self.identity.source_tree,
            "r7_release_id": self.identity.r7_release_id,
            "r7_input_manifest_sha256": self.identity.r7_input_manifest_sha256,
            "r7_context_sha256": "e" * 64,
            "audience": "townsquare-canary-ledger-api",
            "service_id": "townsquare-ledger-v0",
            "issuer": "townsquare-canary-test:fixture-issuer",
            "key_id": "townsquare-canary-test:fixture-key",
            "scope": {"action": "request:open", "object_id": "canary-thread-1"},
            "context_sha256": "c" * 64,
            "issued_at": "2026-10-07T11:59:00Z",
            "expires_at": "2026-10-07T12:05:00Z",
            "nonce": "nonce-canary-000000000001",
        }

    def verifier(self):
        return CanaryProofVerifier(
            self.identity, SQLiteNonceStore(self.db), "unused.pub",
            r7_context_sha256="e" * 64,
            signature_verifier=lambda payload, signature, path: signature == b"valid",
        )

    def verify(self, proof=None):
        return self.verifier().verify_and_consume(
            proof or self.proof, b"valid", audience="townsquare-canary-ledger-api",
            service_id="townsquare-ledger-v0", action="request:open",
            object_id="canary-thread-1", context_sha256="c" * 64, now=self.instant,
        )

    def test_valid_proof_consumes_nonce_once(self):
        self.assertEqual("CANARY_TEST", self.verify()["authority_class"])
        with self.assertRaisesRegex(CanaryAuthorityError, "already consumed"):
            self.verify()

    def test_all_bound_fields_and_negative_domains_fail_before_nonce_write(self):
        mutations = {
            "schema": "townsquare-authority-proof-v1",
            "authority_class": "ADOPT",
            "canary_label": "wrong",
            "compose_project": "wrong",
            "source_commit": "d" * 40,
            "source_tree": "e" * 40,
            "r7_release_id": "TS-R7-" + "f" * 64,
            "r7_input_manifest_sha256": "a" * 64,
            "r7_context_sha256": "b" * 64,
            "audience": "wrong",
            "service_id": "wrong",
            "issuer": "operator:issuer",
            "key_id": "operator:key",
            "scope": {"action": "request:open", "object_id": "other"},
            "context_sha256": "f" * 64,
            "issued_at": "2026-10-07T12:01:00Z",
            "expires_at": "2026-10-07T11:59:00Z",
            "nonce": "short",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.proof)
                candidate[field] = value
                with self.assertRaises(CanaryAuthorityError):
                    self.verify(candidate)
        self.assertEqual(0, self.db.execute("SELECT COUNT(*) FROM verifier_nonces").fetchone()[0])

    def test_missing_excess_forged_signature_and_cross_swap_fail(self):
        missing = dict(self.proof); missing.pop("audience")
        excess = {**self.proof, "operator": True}
        for candidate in (missing, excess):
            with self.assertRaises(CanaryAuthorityError): self.verify(candidate)
        with self.assertRaisesRegex(CanaryAuthorityError, "signature"):
            self.verifier().verify_and_consume(
                self.proof, b"forged", audience="townsquare-canary-ledger-api",
                service_id="townsquare-ledger-v0", action="request:open",
                object_id="canary-thread-1", context_sha256="c" * 64, now=self.instant,
            )
        with self.assertRaisesRegex(CanaryAuthorityError, "forbidden"):
            reject_canary_test_in_normal_domain(self.proof)
        adopted = {"schema": "townsquare-authority-proof-v1", "decision": "ADOPT"}
        with self.assertRaises(CanaryAuthorityError): self.verify(adopted)
        self.assertEqual(0, self.db.execute("SELECT COUNT(*) FROM verifier_nonces").fetchone()[0])

    def test_environment_cannot_select_verifier_and_forgery_precedes_nonce_and_effect(self):
        with tempfile.TemporaryDirectory() as temp:
            public_key = Path(temp) / "test.pub"
            public_key.write_text("test public key", encoding="utf-8")
            verifier = CanaryProofVerifier(self.identity, SQLiteNonceStore(self.db), str(public_key), r7_context_sha256="e" * 64)
            effects = []
            with patch.dict(os.environ, {"TOWNSQUARE_MINISIGN_EXECUTABLE": "/bin/true"}), \
                 patch("shared.canary_authority.os.path.isabs", return_value=True), \
                 patch("shared.canary_authority.os.path.isfile", return_value=True), \
                 patch("shared.canary_authority.subprocess.run", return_value=subprocess.CompletedProcess([], 1)) as run:
                with self.assertRaisesRegex(CanaryAuthorityError, "signature"):
                    verifier.verify_and_consume(
                        self.proof, b"forged", audience="townsquare-canary-ledger-api",
                        service_id="townsquare-ledger-v0", action="request:open",
                        object_id="canary-thread-1", context_sha256="c" * 64, now=self.instant,
                    )
                    effects.append("authorized-write")
                self.assertEqual("/usr/local/bin/minisign", run.call_args.args[0][0])
                self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual([], effects)
            self.assertEqual(0, self.db.execute("SELECT COUNT(*) FROM verifier_nonces").fetchone()[0])
            with patch("shared.canary_authority.os.path.isfile", return_value=False), \
                 patch("shared.canary_authority.subprocess.run") as run:
                with self.assertRaisesRegex(CanaryAuthorityError, "signature"):
                    verifier.verify_and_consume(
                        self.proof, b"forged", audience="townsquare-canary-ledger-api",
                        service_id="townsquare-ledger-v0", action="request:open",
                        object_id="canary-thread-1", context_sha256="c" * 64, now=self.instant,
                    )
                run.assert_not_called()
            self.assertEqual(0, self.db.execute("SELECT COUNT(*) FROM verifier_nonces").fetchone()[0])


class StatusCapabilityTests(unittest.TestCase):
    class FakeHasher:
        def verify(self, stored, supplied):
            if stored != "hash:" + supplied: raise ValueError("wrong secret")

    def setUp(self):
        self.original = registrar_auth.PasswordHasher
        registrar_auth.PasswordHasher = self.FakeHasher
        self.addCleanup(setattr, registrar_auth, "PasswordHasher", self.original)
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.execute("CREATE TABLE auth_credentials(credential_id TEXT,principal TEXT,token_hash TEXT,authorization_policy_version TEXT,issued_at TEXT,expires_at TEXT)")
        self.db.execute("CREATE TABLE credential_revocations(revocation_id TEXT,credential_id TEXT,reason TEXT,revoked_by TEXT,revoked_at TEXT)")

    def insert(self, credential_id, principal, *, expires="2099-01-01T00:00:00Z", revoked=False):
        self.db.execute("INSERT INTO auth_credentials VALUES (?,?,?,?,?,?)", (credential_id, principal, "hash:secret", "townsquare-mvp-v1", "2026-10-07T00:00:00Z", expires))
        if revoked: self.db.execute("INSERT INTO credential_revocations VALUES (?,?,?,?,?)", ("r-" + credential_id, credential_id, "test", "test", "2026-10-07T00:01:00Z"))

    def test_status_read_is_viewer_only_and_missing_expired_revoked_wrong_credentials_fail(self):
        self.assertIn("status:read", registrar_auth.NATIVE_CAPABILITY_POLICIES["townsquare-mvp-v1"]["viewer"])
        for principal in ("writer-a", "writer-b", "reviewer", "crier", "projector", "operator", "operator-resume", "registry-audit"):
            self.assertNotIn("status:read", registrar_auth.NATIVE_CAPABILITY_POLICIES["townsquare-mvp-v1"][principal])
        self.insert("viewer", "viewer")
        self.assertEqual("viewer", registrar_auth.authenticate_native_identity(self.db, "viewer.secret", "status:read")[0])
        self.insert("expired", "viewer", expires="2000-01-01T00:00:00Z")
        self.insert("revoked", "viewer", revoked=True)
        self.insert("wrong-principal", "crier")
        for credential in ("missing.secret", "expired.secret", "revoked.secret", "wrong-principal.secret", "viewer.wrong"):
            with self.assertRaises(Forbidden, msg=credential):
                registrar_auth.authenticate_native_identity(self.db, credential, "status:read")


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_is_no_clobber_nonprinting_and_has_no_operator_credential(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            secret_dir = root / "secrets"; secret_dir.mkdir()
            evidence_key = root / "evidence-key"; evidence_key.write_bytes(b"e" * 32)
            db_path = root / "ledger.db"
            db = ledger_connect(db_path)
            try: ledger_migrate(db)
            finally: db.close()

            issued = []
            def fake_create(db, principal, *, policy_version, ttl_seconds):
                issued.append((principal, policy_version, ttl_seconds))
                credential = principal + "-id.secret-value-" + principal
                db.execute("INSERT INTO auth_credentials VALUES (?,?,?,?,?,?)", (principal + "-id", principal, "test-hash-" + principal, policy_version, "2026-10-07T00:00:00Z", "2099-01-01T00:00:00Z"))
                return credential
            with patch("canary.bootstrap.create_native_credential", side_effect=fake_create):
                metadata = bootstrap(str(db_path), str(secret_dir), str(evidence_key), 3600)
            self.assertEqual({"viewer", "registry-audit", "venom", "wolverine", "bishop"}, {row[0] for row in issued})
            self.assertNotIn("operator", json.dumps(metadata))
            rendered = json.dumps(metadata, sort_keys=True)
            for filename in SECRET_FILES.values():
                path = secret_dir / filename
                self.assertTrue(path.is_file())
                self.assertNotIn(path.read_text(encoding="utf-8").strip(), rendered)
            with self.assertRaises(BootstrapError):
                bootstrap(str(db_path), str(secret_dir), str(evidence_key), 3600)


class ArchiveTests(unittest.TestCase):
    def archive(self, members):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for info, data in members:
                archive.addfile(info, io.BytesIO(data) if data is not None else None)
        buffer.seek(0)
        return buffer

    def test_rejects_traversal_links_devices_fifo_duplicates_and_unexpected_top_level(self):
        cases = []
        for name in ("/absolute", "../escape", "unexpected/file"):
            info = tarfile.TarInfo(name); info.size = 1
            cases.append([(info, b"x")])
        for type_code in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.FIFOTYPE):
            info = tarfile.TarInfo("shared/bad"); info.type = type_code; info.linkname = "target"
            cases.append([(info, None)])
        first = tarfile.TarInfo("shared/dup"); first.size = 1
        second = tarfile.TarInfo("shared/dup"); second.size = 1
        cases.append([(first, b"a"), (second, b"b")])
        for members in cases:
            with self.subTest(member=members[0][0].name, type=members[0][0].type):
                with tarfile.open(fileobj=self.archive(members), mode="r:") as archive:
                    with self.assertRaises(CanaryPathError): validated_members(archive)

    def test_accepts_required_contract_tree(self):
        info = tarfile.TarInfo("contracts/r7/ledger-migrations.json"); info.size = 2
        with tarfile.open(fileobj=self.archive([(info, b"{}")]), mode="r:") as archive:
            self.assertEqual(["contracts/r7/ledger-migrations.json"], [member.name for member in validated_members(archive)])

    def test_path_swap_symlink_fails_closed_when_platform_allows_symlinks(self):
        info = tarfile.TarInfo("shared/value.txt"); info.size = 1
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "destination"; root.mkdir()
            archive_path = Path(temp) / "source.tar"
            archive_path.write_bytes(self.archive([(info, b"x")]).getvalue())
            outside = Path(temp) / "outside"; outside.mkdir()
            def swap(_target):
                try: (root / "shared").symlink_to(outside, target_is_directory=True)
                except OSError: self.skipTest("directory symlinks are unavailable")
            with self.assertRaises(CanaryPathError): extract_validated(archive_path, root, before_write=swap)
            self.assertFalse((outside / "value.txt").exists())


class StaticContainmentTests(unittest.TestCase):
    def test_rendered_compose_validator_accepts_allowlist_and_rejects_escape(self):
        model = rendered_compose_fixture()
        validate(model, expected_identity=IDENTITY)
        escaped = copy.deepcopy(model)
        escaped["services"]["ledger"]["volumes"][0]["source"] = "/volume1/Docker/other"
        with self.assertRaises(ComposeValidationError): validate(escaped, expected_identity=IDENTITY)
        privileged = copy.deepcopy(model)
        privileged["services"]["registry"]["privileged"] = True
        with self.assertRaises(ComposeValidationError): validate(privileged, expected_identity=IDENTITY)
        for mutate in (
            lambda m: m["services"]["registry"].update(networks={"canary-internal": None, "canary-ingress": None}),
            lambda m: m["services"]["ledger"].update(networks={"canary-internal": None}),
            lambda m: m["networks"]["canary-internal"].update(internal=False),
            lambda m: m["networks"]["canary-ingress"].update(internal=True),
        ):
            candidate = copy.deepcopy(model)
            mutate(candidate)
            with self.assertRaises(ComposeValidationError):
                validate(candidate, expected_identity=IDENTITY)

    def test_rendered_compose_rejects_uid_and_cross_service_mount_mutations(self):
        baseline = rendered_compose_fixture()
        validate(baseline, expected_identity=IDENTITY)
        for mutate in (
            lambda m: m["services"]["viewer"].update(user="0:0"),
            lambda m: m["services"]["viewer"]["volumes"].append(copy.deepcopy(m["services"]["ledger"]["volumes"][1])),
            lambda m: m["services"]["ledger-migrate"]["volumes"].append(copy.deepcopy(m["services"]["ledger"]["volumes"][1])),
        ):
            candidate=copy.deepcopy(baseline); mutate(candidate)
            with self.assertRaises(ComposeValidationError): validate(candidate, expected_identity=IDENTITY)

    def test_rendered_compose_rejects_split_unbounded_and_wrong_size_tmpfs(self):
        baseline = rendered_compose_fixture()
        validate(baseline, expected_identity=IDENTITY)
        mutations = (
            ("ledger", ["/tmp:rw", "noexec", "nosuid", "size=32m", "mode=1777"]),
            ("registry", ["/tmp:rw,noexec,nosuid,mode=1777"]),
            ("viewer", ["/tmp:rw,noexec,nosuid,size=32m,mode=1777"]),
        )
        for service, tmpfs in mutations:
            with self.subTest(service=service, tmpfs=tmpfs):
                candidate = copy.deepcopy(baseline)
                candidate["services"][service]["tmpfs"] = tmpfs
                with self.assertRaises(ComposeValidationError):
                    validate(candidate, expected_identity=IDENTITY)

    def test_every_environment_field_is_required_exact_and_no_unknown_keys(self):
        baseline = rendered_compose_fixture()
        for service, raw in baseline["services"].items():
            for key in raw["environment"]:
                for mode in ("missing", "changed", "unrendered", "null"):
                    with self.subTest(service=service, key=key, mode=mode):
                        candidate = copy.deepcopy(baseline)
                        env = candidate["services"][service]["environment"]
                        if mode == "missing": env.pop(key)
                        else: env[key] = {"changed": "wrong", "unrendered": "${VALUE:?required}", "null": None}[mode]
                        with self.assertRaises(ComposeValidationError): validate(candidate, expected_identity=IDENTITY)
            for key in (
                "UNKNOWN", "TOWNSQUARE_MINISIGN_EXECUTABLE", "TOWNSQUARE_CANARY_TEST_PUBLIC_KEY_FILE",
                "TOWNSQUARE_CONTEXT_MANIFEST", "REGISTRY_CANARY_NONCE_DIRECTORY", "REGISTRY_READINESS_TOKEN_FILE",
                "REGISTRY_PEER_READINESS_TOKEN_FILE", "LEDGER_READINESS_TOKEN_FILE", "REGISTRAR_DB", "REGISTRY_DB",
                "REGISTRY_TOKEN_FILE", "REGISTRY_LEDGER_AUDIT_TOKEN_FILE", "REGISTRAR_API_TOKEN_FILE",
                "REGISTRAR_TOKEN_PEPPER_FILE", "REGISTRAR_CURSOR_KEY_FILE", "TOWNSQUARE_RECEIPT_HASH_KEY_FILE",
                "TOWNSQUARE_AUTHORITY_PROOF_FILE", "TOWNSQUARE_AUTHORITY_PUBLIC_KEY_FILE", "TOWNSQUARE_AUTHORITY_SIGNATURE_FILE",
                "REGISTRAR_API_TOKEN", "REGISTRY_API_TOKEN", "LD_PRELOAD", "PYTHONPATH", "PATH",
                "TOWNSQUARE_EMBEDDED_SOURCE_COMMIT",
            ):
                with self.subTest(service=service, override=key):
                    candidate = copy.deepcopy(baseline)
                    candidate["services"][service]["environment"][key] = "/bin/true" if key == "TOWNSQUARE_MINISIGN_EXECUTABLE" else "/tmp/attacker"
                    with self.assertRaises(ComposeValidationError): validate(candidate, expected_identity=IDENTITY)

    def test_trusted_identity_rejects_invalid_fields_and_model_self_attestation(self):
        baseline = rendered_compose_fixture()
        for field in IDENTITY:
            for value in (None, "wrong", "${SOURCE:?required}", "A" * 40):
                expected = {**IDENTITY, field: value}
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ComposeValidationError): validate(baseline, expected_identity=expected)
            expected = dict(IDENTITY); expected.pop(field)
            with self.assertRaises(ComposeValidationError): validate(baseline, expected_identity=expected)
        with self.assertRaises(ComposeValidationError): validate(baseline, expected_identity={**IDENTITY, "SECRET": "forbidden"})
        for field in ("TOWNSQUARE_SOURCE_COMMIT", "TOWNSQUARE_SOURCE_TREE"):
            candidate = copy.deepcopy(baseline)
            for raw in candidate["services"].values():
                raw["environment"][field] = "c" * 40
                if field.endswith("COMMIT"): raw["image"] = raw["image"].split(":")[0] + ":" + "c" * 40
            with self.assertRaises(ComposeValidationError): validate(candidate, expected_identity=IDENTITY)
            validate(candidate, expected_identity={**IDENTITY, field: "c" * 40})

    def test_image_build_entrypoint_and_command_contracts_for_every_service(self):
        baseline = rendered_compose_fixture()
        for name, raw in baseline["services"].items():
            wrong_repository = "townsquare-canary-viewer" if name != "viewer" else "townsquare-canary-ledger"
            for key, value in (
                ("image", raw["image"].split(":")[0] + ":" + "c" * 40),
                ("image", wrong_repository + ":" + "a" * 40),
                ("image", raw["image"].split(":")[0] + ":${TOWNSQUARE_SOURCE_COMMIT:?required}"),
                ("build", "."), ("build", None), ("entrypoint", ["sh"]), ("entrypoint", None),
                ("command", ["python", "/app/app.py"]), ("command", None),
            ):
                with self.subTest(service=name, key=key, value=value):
                    candidate = copy.deepcopy(baseline); candidate["services"][name][key] = value
                    with self.assertRaises(ComposeValidationError): validate(candidate, expected_identity=IDENTITY)
        for name, other in (("ledger-migrate", "registry-migrate"), ("registry-migrate", "ledger-migrate")):
            for command in (None, baseline["services"][other]["command"], baseline["services"][name]["command"][4:]):
                candidate = copy.deepcopy(baseline)
                if command is None: candidate["services"][name].pop("command")
                else: candidate["services"][name]["command"] = command
                with self.assertRaises(ComposeValidationError): validate(candidate, expected_identity=IDENTITY)

    def test_cli_requires_independent_identity_file_and_rejects_bad_identity_files(self):
        with tempfile.TemporaryDirectory() as temp:
            identity_path = Path(temp) / "identity.env"
            rendered_path = Path(temp) / "rendered.json"
            valid_text = "\n".join(f"{key}={value}" for key, value in IDENTITY.items()) + "\n"
            identity_path.write_text(valid_text, encoding="utf-8")
            model = rendered_compose_fixture()
            rendered_path.write_text(json.dumps(model), encoding="utf-8")
            command = [sys.executable, "-m", "canary.validate_compose", str(rendered_path)]
            self.assertNotEqual(0, subprocess.run(command, cwd=ROOT, capture_output=True).returncode)
            command += ["--identity-env", str(identity_path)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            for raw in model["services"].values(): raw["environment"]["TOWNSQUARE_SOURCE_TREE"] = "c" * 40
            rendered_path.write_text(json.dumps(model), encoding="utf-8")
            self.assertNotEqual(0, subprocess.run(command, cwd=ROOT, capture_output=True).returncode)
            for text in (valid_text + "SECRET=sentinel\n", valid_text + "TOWNSQUARE_SOURCE_TREE=" + "b" * 40, valid_text.replace("a" * 40, "${SOURCE}"), valid_text.replace("b" * 40, "B" * 40), valid_text + "malformed"):
                identity_path.write_text(text, encoding="utf-8")
                with self.assertRaises(ComposeValidationError): read_identity_env(str(identity_path))

    def test_prefixed_viewer_credential_hits_peer_only_401_before_fix_surface(self):
        """Execute the source peer gate itself; it never calls native auth."""
        source = (ROOT / "registrar/app/main.py").read_text(encoding="utf-8")
        module = ast.parse(source)
        selected = [node for node in module.body if isinstance(node, ast.FunctionDef) and node.name in {"_read_readiness_token", "_authorize_registry_peer"}]
        namespace = {"os": os, "secrets": __import__("secrets")}
        class HTTPException(Exception):
            def __init__(self, status_code, detail):
                self.status_code = status_code; self.detail = detail
        namespace["HTTPException"] = HTTPException
        with tempfile.TemporaryDirectory() as temp:
            inbound = Path(temp) / "inbound"; inbound.write_text("peer-inbound", encoding="utf-8")
            outbound = Path(temp) / "outbound"; outbound.write_text("peer-outbound", encoding="utf-8")
            namespace["REGISTRY_INBOUND_READINESS_FILE"] = str(inbound)
            namespace["REGISTRY_OUTBOUND_READINESS_FILE"] = str(outbound)
            exec(compile(ast.Module(body=selected, type_ignores=[]), "registrar/app/main.py", "exec"), namespace)
            with self.assertRaises(HTTPException) as caught:
                namespace["_authorize_registry_peer"]("Bearer valid-viewer-native-credential")
        fixture = json.loads((ROOT / "tests/conformance/fixtures/viewer-peer-readiness-prefixed-401.json").read_text(encoding="utf-8"))
        self.assertEqual(401, caught.exception.status_code)
        self.assertEqual(fixture["actual"]["body"]["detail"], caught.exception.detail)

    def test_compose_and_registry_are_manual_and_isolated(self):
        compose = (ROOT / "canary/compose.canary.yml").read_text(encoding="utf-8")
        registry = (ROOT / "registry/app.py").read_text(encoding="utf-8")
        self.assertIn("name: townsquare-canary-20261007-a", compose)
        self.assertEqual(1, compose.count("internal: true"))
        self.assertEqual(1, compose.count("internal: false"))
        self.assertIn("networks: [canary-internal, canary-ingress]", compose)
        self.assertIn('ports: ["192.168.2.3:18790:8790"]', compose)
        self.assertIn('ports: ["192.168.2.3:18502:8502"]', compose)
        for forbidden in ("privileged:", "cap_add:", "network_mode:", "extra_hosts:", "devices:", "docker.sock", "restart: unless-stopped"):
            self.assertNotIn(forbidden, compose)
        self.assertIn("REGISTRY_AUDIT_DELIVERY_MODE: manual", compose)
        self.assertNotIn("periodic_worker", registry)
        self.assertNotIn("threading.Thread", registry)
        self.assertIn("--deliver-audit-once", registry)

    def test_consumer_secret_mount_matrix_and_identity_only_env_file(self):
        compose = (ROOT / "canary/compose.canary.yml").read_text(encoding="utf-8")
        boundaries = {}
        names = ["ledger-migrate", "ledger", "registry-migrate", "registry", "viewer"]
        for index, name in enumerate(names):
            start = compose.index(f"  {name}:\n")
            later = [compose.find(f"  {other}:\n", start + 1) for other in names[index + 1:]]
            end = min((value for value in later if value >= 0), default=compose.index("\nnetworks:\n"))
            boundaries[name] = compose[start:end]
        self.assertNotIn("/secrets/", boundaries["ledger-migrate"])
        self.assertNotIn("/secrets/", boundaries["registry-migrate"])
        self.assertEqual(2, boundaries["viewer"].count("/secrets/viewer-native-credential"))
        for forbidden in ("token-pepper", "cursor-signing", "receipt-hash", "registry-api", "registry-audit", "readiness"):
            self.assertNotIn(forbidden, boundaries["viewer"])
        for required in ("ledger-token-pepper", "ledger-cursor-signing-key", "ledger-receipt-hash-key", "ledger-to-registry-readiness.ledger", "registry-to-ledger-readiness.ledger"):
            self.assertIn(required, boundaries["ledger"])
        self.assertNotIn("viewer-native-credential", boundaries["ledger"])
        for required in ("registry-api-credential", "registry-audit-credential", "ledger-to-registry-readiness.registry", "registry-to-ledger-readiness.registry"):
            self.assertIn(required, boundaries["registry"])
        self.assertNotIn("viewer-native-credential", boundaries["registry"])
        self.assertNotIn("operator", compose.lower())
        env_lines = [line for line in (ROOT / "canary/canary.env.example").read_text().splitlines() if line]
        self.assertEqual(8, len(env_lines))
        self.assertEqual(set(RUNTIME_FIELDS), {line.split("=", 1)[0] for line in env_lines})

    def test_status_banner_build_identity_and_coarse_lock_supersession(self):
        viewer_client = (ROOT / "viewer/registrar_client.py").read_text(encoding="utf-8")
        viewer_app = (ROOT / "viewer/streamlit_app.py").read_text(encoding="utf-8")
        registrar = (ROOT / "registrar/app/main.py").read_text(encoding="utf-8")
        self.assertIn('/v1/native/status/ready', viewer_client)
        self.assertNotIn('_get("/health/ready")', viewer_client)
        self.assertIn("CANARY — NON-AUTHORITATIVE — TS-CANARY-NAS1-20261007-A", viewer_app)
        self.assertIn('page_title="[CANARY]', viewer_app)
        self.assertIn('native_identity(db,authorization,"status:read")', registrar)
        for dockerfile in ("registrar/Dockerfile", "registry/Dockerfile", "viewer/Dockerfile"):
            text = (ROOT / dockerfile).read_text(encoding="utf-8")
            self.assertIn("TOWNSQUARE_EMBEDDED_SOURCE_TREE", text)
            self.assertIn("townsquare.canary-label", text)
            self.assertIn("canary.preexec", text)
            self.assertNotIn("requirements/requirements.lock.json", text)
        disposition = json.loads((ROOT / "canary/coarse-lock-supersession.json").read_text())
        self.assertEqual("STALE_SUPERSEDED_NON_BUILD_INPUT", disposition["status"])
        for path in [*ROOT.glob("**/Dockerfile"), *ROOT.glob("canary/*.py")]:
            self.assertNotIn("requirements/requirements.lock.json", path.read_text(encoding="utf-8"), str(path))

    def test_registry_image_layout_can_load_pinned_contract_and_migrate(self):
        """Reproduce /app + /contracts image paths without a Docker daemon."""
        dockerfile = (ROOT / "registry/Dockerfile").read_text(encoding="utf-8")
        self.assertIn(
            "COPY --chown=root:root contracts/r7/registry-schema.json /contracts/r7/registry-schema.json",
            dockerfile,
        )
        self.assertNotIn("/app/contracts/r7/registry-schema.json", dockerfile)
        with tempfile.TemporaryDirectory() as temp:
            image_root = Path(temp)
            app = image_root / "app"
            contract = image_root / "contracts/r7"
            data = image_root / "data"
            app.mkdir()
            contract.mkdir(parents=True)
            data.mkdir()
            for name in ("migrate.py", "schema.sql"):
                (app / name).write_bytes((ROOT / "registry" / name).read_bytes())
            (contract / "registry-schema.json").write_bytes(
                (ROOT / "contracts/r7/registry-schema.json").read_bytes()
            )
            database = data / "registry.db"
            environment = {**os.environ, "REGISTRY_DB": str(database)}
            result = subprocess.run(
                [sys.executable, str(app / "migrate.py")],
                cwd=image_root,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            db = sqlite3.connect(database)
            try:
                self.assertEqual(1414746695, db.execute("PRAGMA application_id").fetchone()[0])
                self.assertEqual(2, db.execute("PRAGMA user_version").fetchone()[0])
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
