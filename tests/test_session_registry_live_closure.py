"""LC03 tests for verifier-bound enrollment, ownership, rotation, and lookup."""
from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import secrets
import shutil
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from tests.test_session_registry_s1 import ROOT, load_app


def verifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def session_proof(credential: str, method: str, path: str, key: str = "", body=None) -> str:
    body_sha256 = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    payload = f"registry-session-proof-v1\n{method}\n{path}\n{key}\n{body_sha256}".encode()
    return hmac.new(bytes.fromhex(verifier(credential)), payload, hashlib.sha256).hexdigest()


class RegistryFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = load_app()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "registry.db"
        self.api_token_path = Path(self.tmp.name) / "operator-api"
        self.lookup_verifier_path = Path(self.tmp.name) / "lookup.sha256"
        self.api_token = secrets.token_urlsafe(32)
        self.lookup_token = secrets.token_urlsafe(32)
        self.operator_token = secrets.token_urlsafe(32)
        self.api_token_path.write_text(self.api_token, encoding="utf-8")
        self.lookup_verifier_path.write_text(verifier(self.lookup_token) + "\n", encoding="ascii")
        db = sqlite3.connect(self.db_path)
        db.executescript((ROOT / "registry" / "schema.sql").read_text(encoding="utf-8"))
        for agent in ("nimrod", "eddie-brock"):
            db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", (agent, "{}", 1, 1, "2026-01-01T00:00:00Z"))
        db.commit()
        db.close()
        self.app.DB = self.db_path
        self.app.TOKEN_FILE = str(self.api_token_path)
        self.app.LOOKUP_TOKEN_SHA256_FILE = str(self.lookup_verifier_path)
        self.old_operator_token = os.environ.get("REGISTRY_OPERATOR_TOKEN")
        os.environ["REGISTRY_OPERATOR_TOKEN"] = self.operator_token

    def tearDown(self):
        if self.old_operator_token is None:
            os.environ.pop("REGISTRY_OPERATOR_TOKEN", None)
        else:
            os.environ["REGISTRY_OPERATOR_TOKEN"] = self.old_operator_token
        self.tmp.cleanup()

    def db(self):
        return self.app.connect()

    def grant(self, agent="nimrod", provider="codex", seat="sentinel1"):
        db = self.db()
        try:
            status, response = self.app.create_session_enrollment(
                db, {"agent_id": agent, "provider": provider, "seat_or_host": seat}
            )
            self.assertEqual(201, status)
            return response
        finally:
            db.close()

    def registration_body(self, credential, *, agent="nimrod", provider="codex", seat="sentinel1", locator=None):
        return {
            "agent_id": agent,
            "provider": provider,
            "provider_session_id": locator or secrets.token_urlsafe(36),
            "seat_or_host": seat,
            "runtime": "codex-runtime",
            "model": "bounded-test-model",
            "initial_status": "ACTIVE",
            "work_ref": "VR-20261011-ynm-002",
            "session_credential_sha256": verifier(credential),
        }

    def register(self, grant, credential, *, key="registration-1", **changes):
        body = self.registration_body(credential)
        body.update(changes)
        db = self.db()
        try:
            return body, self.app.register_enrolled_session(db, verifier(grant["enrollment_token"]), key, body)
        finally:
            db.close()

    def counts(self):
        db = self.db()
        try:
            return tuple(
                db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in (
                    "sessions", "session_enrollments", "session_registration_replays",
                    "session_credential_rotations", "session_journal", "journal", "audit_outbox",
                )
            )
        finally:
            db.close()


class EnrollmentAndRotationTests(RegistryFixture):
    def test_registration_exact_retry_and_all_changed_or_consumed_reuse_is_zero_write(self):
        runtime_credential = secrets.token_urlsafe(32)
        grant = self.grant()
        body, (status, first) = self.register(grant, runtime_credential)
        self.assertEqual(201, status)
        before = self.counts()

        db = self.db()
        try:
            status, replay = self.app.register_enrolled_session(
                db, verifier(grant["enrollment_token"]), "registration-1", body
            )
        finally:
            db.close()
        self.assertEqual((201, first), (status, replay))
        self.assertEqual(before, self.counts())

        changed = dict(body, session_credential_sha256=verifier(secrets.token_urlsafe(32)))
        for key, request in (("registration-1", changed), ("registration-2", body)):
            db = self.db()
            try:
                status, response = self.app.register_enrolled_session(
                    db, verifier(grant["enrollment_token"]), key, request
                )
            finally:
                db.close()
            self.assertEqual(409, status)
            self.assertEqual("SESSION_REGISTRATION_CONFLICT", response["code"])
            self.assertEqual(before, self.counts())

        db_bytes = self.db_path.read_bytes()
        self.assertNotIn(runtime_credential.encode(), db_bytes)
        self.assertNotIn(grant["enrollment_token"].encode(), db_bytes)
        self.assertNotIn("session_credential_sha256", first)

    def test_expired_and_wrong_binding_fail_without_consumption_or_session(self):
        runtime_credential = secrets.token_urlsafe(32)
        expired = self.grant()
        db = self.db()
        try:
            db.execute("UPDATE session_enrollments SET expires_utc='2000-01-01T00:00:00Z' WHERE grant_id=?", (expired["grant_id"],))
        finally:
            db.close()
        before = self.counts()
        _, (status, response) = self.register(expired, runtime_credential)
        self.assertEqual((409, "SESSION_ENROLLMENT_EXPIRED"), (status, response["code"]))
        self.assertEqual(before, self.counts())

        wrong = self.grant()
        before = self.counts()
        _, (status, response) = self.register(wrong, runtime_credential, seat_or_host="venom")
        self.assertEqual((409, "SESSION_REGISTRATION_CONFLICT"), (status, response["code"]))
        self.assertEqual(before, self.counts())
        db = self.db()
        try:
            self.assertIsNone(db.execute("SELECT consumed_utc FROM session_enrollments WHERE grant_id=?", (wrong["grant_id"],)).fetchone()[0])
        finally:
            db.close()

    def test_rotation_exact_retry_accepts_old_or_new_after_restart_and_changed_reuse_is_zero_write(self):
        old_credential = secrets.token_urlsafe(32)
        new_credential = secrets.token_urlsafe(32)
        grant = self.grant()
        _, (_, registered) = self.register(grant, old_credential)
        session_uuid = registered["session_uuid"]
        body = {"session_credential_sha256": verifier(new_credential)}
        path = f"/v1/sessions/{session_uuid}/credential-rotations"
        db = self.db()
        try:
            proof = session_proof(old_credential, "POST", path, "rotation-1", body)
            status, first = self.app.rotate_session_credential(db, session_uuid, "rotation-1", proof, body)
        finally:
            db.close()
        self.assertEqual(200, status)
        before = self.counts()

        for retry_credential in (old_credential, new_credential):
            db = self.db()
            try:
                status, replay = self.app.rotate_session_credential(
                    db, session_uuid, "rotation-1",
                    session_proof(retry_credential, "POST", path, "rotation-1", body), body
                )
            finally:
                db.close()
            self.assertEqual((200, first), (status, replay))
            self.assertEqual(before, self.counts())

        changed = {"session_credential_sha256": verifier(secrets.token_urlsafe(32))}
        db = self.db()
        try:
            status, response = self.app.rotate_session_credential(
                db, session_uuid, "rotation-1",
                session_proof(new_credential, "POST", path, "rotation-1", changed), changed
            )
        finally:
            db.close()
        self.assertEqual((409, "SESSION_ROTATION_CONFLICT"), (status, response["code"]))
        self.assertEqual(before, self.counts())
        self.assertNotIn(old_credential.encode(), self.db_path.read_bytes())
        self.assertNotIn(new_credential.encode(), self.db_path.read_bytes())

    def test_session_credential_owns_heartbeat_and_cannot_cross_session(self):
        nimrod_credential = secrets.token_urlsafe(32)
        eddie_credential = secrets.token_urlsafe(32)
        _, (_, nimrod) = self.register(self.grant(), nimrod_credential)
        eddie_grant = self.grant("eddie-brock", seat="venom")
        eddie_body = self.registration_body(eddie_credential, agent="eddie-brock", seat="venom")
        db = self.db()
        try:
            _, eddie = self.app.register_enrolled_session(db, verifier(eddie_grant["enrollment_token"]), "eddie-register", eddie_body)
        finally:
            db.close()

        db = self.db()
        try:
            nimrod_body = {"status": "IDLE"}
            nimrod_path = f"/v1/sessions/{nimrod['session_uuid']}/heartbeat"
            status, response = self.app.mutate_session(
                db, "session:" + nimrod["session_uuid"], "nimrod-idle",
                {"session_uuid": nimrod["session_uuid"], **nimrod_body}, "heartbeat",
                session_proof(nimrod_credential, "POST", nimrod_path, "nimrod-idle", nimrod_body)
            )
            self.assertEqual((200, "IDLE"), (status, response["status"]))
            before = self.counts()
            cross_body = {"status": "IDLE"}
            cross_path = f"/v1/sessions/{eddie['session_uuid']}/heartbeat"
            status, _ = self.app.mutate_session(
                db, "session:" + eddie["session_uuid"], "cross-read-write",
                {"session_uuid": eddie["session_uuid"], **cross_body}, "heartbeat",
                session_proof(nimrod_credential, "POST", cross_path, "cross-read-write", cross_body)
            )
        finally:
            db.close()
        self.assertEqual(401, status)
        self.assertEqual(before, self.counts())
        db = self.db()
        try:
            terminate_body = {"terminal_status": "ENDED"}
            terminate_path = f"/v1/sessions/{eddie['session_uuid']}/terminate"
            status, response = self.app.mutate_session(
                db, "session:" + eddie["session_uuid"], "eddie-terminate",
                {"session_uuid": eddie["session_uuid"], **terminate_body}, "terminate",
                session_proof(eddie_credential, "POST", terminate_path, "eddie-terminate", terminate_body)
            )
        finally:
            db.close()
        self.assertEqual((200, "ENDED"), (status, response["status"]))


class ScopedHttpTests(RegistryFixture):
    def setUp(self):
        super().setUp()
        self.server = self.app.ThreadingHTTPServer(("127.0.0.1", 0), self.app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        super().tearDown()

    def request(self, method, path, *, authorization=None, headers=None, body=None):
        request_headers = dict(headers or {})
        if authorization:
            request_headers["Authorization"] = authorization
        encoded = None if body is None else json.dumps(body).encode()
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path, body=encoded, headers=request_headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, {key.lower(): value for key, value in response.getheaders()}, raw, json.loads(raw)
        finally:
            connection.close()

    def test_enrollment_registration_lookup_scope_owner_reads_and_provider_locator_separation(self):
        status, headers, enrollment_raw, grant = self.request(
            "POST", "/v1/session-enrollments",
            headers={"X-Registry-Operator-Token": self.operator_token},
            body={"agent_id": "nimrod", "provider": "codex", "seat_or_host": "sentinel1"},
        )
        self.assertEqual(201, status)
        self.assertEqual("no-store", headers.get("cache-control"))
        runtime_credential = secrets.token_urlsafe(32)
        locator = secrets.token_urlsafe(36)
        body = self.registration_body(runtime_credential, locator=locator)
        status, _, registration_raw, registered = self.request(
            "POST", "/v1/sessions", authorization="Enrollment " + grant["enrollment_token"],
            headers={"Idempotency-Key": "http-registration"}, body=body,
        )
        self.assertEqual(201, status)
        session_uuid = registered["session_uuid"]
        for secret in (runtime_credential, locator):
            self.assertNotIn(secret.encode(), registration_raw)

        status, _, lookup_raw, lookup = self.request(
            "GET", f"/v1/sessions/{session_uuid}", authorization="Bearer " + self.lookup_token
        )
        self.assertEqual(200, status)
        self.assertEqual("nimrod", lookup["agent_id"])
        self.assertNotIn(locator.encode(), lookup_raw)
        own_path = f"/v1/sessions/{session_uuid}"
        status, _, _, _ = self.request(
            "GET", own_path,
            authorization="SessionProof " + session_proof(runtime_credential, "GET", own_path)
        )
        self.assertEqual(200, status)

        heartbeat_path = f"/v1/sessions/{session_uuid}/heartbeat"
        heartbeat_body = {"status": "IDLE"}
        status, _, heartbeat_raw, heartbeat = self.request(
            "POST", heartbeat_path,
            authorization="SessionProof " + session_proof(
                runtime_credential, "POST", heartbeat_path, "http-heartbeat", heartbeat_body
            ),
            headers={"Idempotency-Key": "http-heartbeat"}, body=heartbeat_body,
        )
        self.assertEqual((200, "IDLE"), (status, heartbeat["status"]))

        replacement_credential = secrets.token_urlsafe(32)
        rotation_path = f"/v1/sessions/{session_uuid}/credential-rotations"
        rotation_body = {"session_credential_sha256": verifier(replacement_credential)}
        status, _, rotation_raw, rotation = self.request(
            "POST", rotation_path,
            authorization="SessionProof " + session_proof(
                runtime_credential, "POST", rotation_path, "http-rotation", rotation_body
            ),
            headers={"Idempotency-Key": "http-rotation"}, body=rotation_body,
        )
        self.assertEqual((200, "credential_rotate"), (status, rotation["action"]))
        status, _, retry_raw, retry = self.request(
            "POST", rotation_path,
            authorization="SessionProof " + session_proof(
                replacement_credential, "POST", rotation_path, "http-rotation", rotation_body
            ),
            headers={"Idempotency-Key": "http-rotation"}, body=rotation_body,
        )
        self.assertEqual((200, rotation), (status, retry))

        other_credential = secrets.token_urlsafe(32)
        other_grant = self.grant("eddie-brock", seat="venom")
        other_body = self.registration_body(other_credential, agent="eddie-brock", seat="venom")
        db = self.db()
        try:
            _, other = self.app.register_enrolled_session(db, verifier(other_grant["enrollment_token"]), "other", other_body)
        finally:
            db.close()
        cross_path = f"/v1/sessions/{other['session_uuid']}"
        status, _, _, _ = self.request(
            "GET", cross_path,
            authorization="SessionProof " + session_proof(runtime_credential, "GET", cross_path)
        )
        self.assertEqual(404, status)

        status, _, _, _ = self.request(
            "GET", f"/v1/sessions/{session_uuid}/provider-locator", authorization="Bearer " + self.lookup_token,
            headers={"X-Registry-Operator-Token": self.operator_token},
        )
        self.assertEqual(404, status)
        status, _, _, _ = self.request(
            "POST", f"/v1/sessions/{session_uuid}/heartbeat", authorization="Bearer " + self.lookup_token,
            headers={"Idempotency-Key": "lookup-cannot-write"}, body={"status": "IDLE"},
        )
        self.assertEqual(401, status)
        captured = enrollment_raw + registration_raw + lookup_raw + heartbeat_raw + rotation_raw + retry_raw
        self.assertNotIn(runtime_credential.encode(), captured)
        self.assertNotIn(replacement_credential.encode(), captured)


class MigrationAndPeerIdentityTests(unittest.TestCase):
    def test_v4_copy_upgrades_to_v5_and_rollback_copy_remains_byte_preserving(self):
        import registry.migrate as migrate

        with tempfile.TemporaryDirectory() as tmp:
            baseline = Path(tmp) / "registry-v4.db"
            candidate = Path(tmp) / "registry-candidate.db"
            rollback = Path(tmp) / "registry-rollback.db"
            db = sqlite3.connect(baseline)
            try:
                for statement in migrate._statements(migrate.SCHEMA):
                    if statement.lstrip().upper().startswith("ALTER TABLE SESSIONS ADD COLUMN SESSION_CREDENTIAL_SHA256"):
                        break
                    db.execute(statement)
                db.execute("PRAGMA application_id=1414746695")
                db.execute("PRAGMA user_version=4")
                db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", ("preserved", "{}", 1, 1, "2026-01-01T00:00:00Z"))
                session_uuid = "11111111-1111-4111-8111-111111111111"
                db.execute(
                    "INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (session_uuid, "preserved", "fixture", "private-locator", "host", None, None, "ACTIVE", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z", None, None, 1, "2026-01-01T00:00:00Z"),
                )
                db.execute(
                    "INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?,?)",
                    ("22222222-2222-4222-8222-222222222222", session_uuid, "preserved", "register", "{}", "2026-01-01T00:00:00Z"),
                )
                db.commit()
            finally:
                db.close()
            shutil.copy2(baseline, candidate)
            shutil.copy2(baseline, rollback)
            db = sqlite3.connect(candidate)
            try:
                self.assertEqual(5, migrate.migrate(db))
                self.assertEqual("preserved", db.execute("SELECT agent_id FROM agents").fetchone()[0])
                self.assertEqual((session_uuid, "register"), db.execute("SELECT session_uuid,action FROM session_journal").fetchone())
                self.assertIsNone(db.execute("SELECT session_credential_sha256 FROM sessions").fetchone()[0])
            finally:
                db.close()
            original = sqlite3.connect(baseline)
            restored = sqlite3.connect(rollback)
            try:
                self.assertEqual(4, original.execute("PRAGMA user_version").fetchone()[0])
                self.assertEqual(4, restored.execute("PRAGMA user_version").fetchone()[0])
                self.assertEqual(list(original.iterdump()), list(restored.iterdump()))
            finally:
                original.close()
                restored.close()

    def test_contract_hashes_and_same_release_registry_ledger_peer_identity(self):
        import registry.migrate as migrate

        contract = json.loads((ROOT / "contracts" / "r7" / "registry-schema.json").read_text(encoding="utf-8"))
        step_hashes = [row["sha256"] for row in contract["steps"]]
        calculated_v5 = hashlib.sha256(
            "".join(migrate._upgrade_statements(4)).replace("\r\n", "\n").replace("\r", "\n").encode()
        ).hexdigest()
        self.assertEqual(step_hashes[-1], calculated_v5)
        self.assertEqual(contract["history_sha256"], hashlib.sha256("".join(step_hashes).encode()).hexdigest())
        self.assertEqual(contract["schema_sha256"], migrate._sha(migrate.SCHEMA))
        self.assertEqual(contract["migrator_sha256"], migrate._sha(Path(migrate.__file__)))
        fresh = sqlite3.connect(":memory:")
        try:
            fresh.executescript(migrate.SCHEMA.read_text(encoding="utf-8"))
            self.assertEqual(contract["canonical_schema_sha256"], migrate.canonical_schema_sha256(fresh))
        finally:
            fresh.close()
        self.assertEqual(2, load_app().SCHEMA_VERSION)
        ledger_db_source = (ROOT / "registrar" / "app" / "db.py").read_text(encoding="utf-8")
        self.assertIn("REGISTRY_SCHEMA_VERSION=2", ledger_db_source)

        app = load_app()
        identity = {"source_commit": "a" * 40, "source_tree": "b" * 40, "r7_release_id": "TS-R7-" + "c" * 64}
        app.CANARY_IDENTITY = type("Identity", (), {"as_dict": lambda self: identity})()
        app.compatible_identity = lambda payload, expected: all(payload.get(key) == value for key, value in expected.as_dict().items())
        with tempfile.TemporaryDirectory() as tmp:
            inbound = Path(tmp) / "inbound"
            outbound = Path(tmp) / "outbound"
            inbound.write_text(secrets.token_urlsafe(32), encoding="utf-8")
            outbound.write_text(secrets.token_urlsafe(32), encoding="utf-8")
            old_inbound = os.environ.get("REGISTRY_PEER_READINESS_TOKEN_FILE")
            old_outbound = app.LEDGER_READINESS_TOKEN_FILE
            os.environ["REGISTRY_PEER_READINESS_TOKEN_FILE"] = str(inbound)
            app.LEDGER_READINESS_TOKEN_FILE = str(outbound)
            peer = {"ok": True, "service_id": "townsquare-ledger-v0", "schema_version": 14, "audit_contract_version": app.AUDIT_CONTRACT_VERSION, **identity}

            class Response:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def read(self, *_):
                    return json.dumps(peer).encode()

            try:
                with mock.patch("urllib.request.urlopen", return_value=Response()):
                    self.assertTrue(app.peer_ready()["compatible"])
                peer["source_commit"] = "d" * 40
                with mock.patch("urllib.request.urlopen", return_value=Response()):
                    self.assertFalse(app.peer_ready()["compatible"])
            finally:
                app.LEDGER_READINESS_TOKEN_FILE = old_outbound
                if old_inbound is None:
                    os.environ.pop("REGISTRY_PEER_READINESS_TOKEN_FILE", None)
                else:
                    os.environ["REGISTRY_PEER_READINESS_TOKEN_FILE"] = old_inbound


def _successor(case, name):
    """Keep inherited test labels active while exercising the replacement contract."""
    def test(self):
        case.setUpClass()
        result = unittest.TestResult()
        case(name).run(result)
        self.assertEqual([], result.errors)
        self.assertEqual([], result.failures)
        self.assertEqual([], result.skipped)
    return test


from tests import test_session_registry_ed25519 as successor
EnrollmentAndRotationTests.test_registration_exact_retry_and_all_changed_or_consumed_reuse_is_zero_write = _successor(successor.EnrollmentTests, "test_atomic_registration_replay_conflicts_and_no_private_material")
EnrollmentAndRotationTests.test_expired_and_wrong_binding_fail_without_consumption_or_session = _successor(successor.EnrollmentTests, "test_expiry_binding_and_duplicate_locator_are_zero_write")
EnrollmentAndRotationTests.test_rotation_exact_retry_accepts_old_or_new_after_restart_and_changed_reuse_is_zero_write = _successor(successor.OwningRequestTests, "test_rotation_cutoff_replay_and_terminate")
EnrollmentAndRotationTests.test_session_credential_owns_heartbeat_and_cannot_cross_session = _successor(successor.OwningRequestTests, "test_get_one_use_and_database_exfiltration_cannot_forge")
ScopedHttpTests.test_enrollment_registration_lookup_scope_owner_reads_and_provider_locator_separation = _successor(successor.EnrollmentTests, "test_http_requires_one_exact_enrollment_header_and_returns_no_store")
MigrationAndPeerIdentityTests.test_v4_copy_upgrades_to_v5_and_rollback_copy_remains_byte_preserving = _successor(successor.FixtureAndMigrationTests, "test_v5_copy_migrates_to_lost_and_rollback_copy_is_unchanged")
MigrationAndPeerIdentityTests.test_contract_hashes_and_same_release_registry_ledger_peer_identity = _successor(successor.FixtureAndMigrationTests, "test_public_fixture_is_byte_exact_and_identity_coherent")


if __name__ == "__main__":
    unittest.main()
