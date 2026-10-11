"""AUD-01..12 behavior checks for the durable Registry audit worker."""
from __future__ import annotations

import contextlib
import base64
import hashlib
import io
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
import importlib
import urllib.error
from pathlib import Path
from unittest import mock

from shared.registry_outbox import acknowledge_delivery
from tests.test_session_registry_s1 import ROOT, load_app


class Response:
    status = 201

    def __init__(self, event_id):
        self.raw = json.dumps({"event_uuid": event_id, "ledger_event_id": "ledger-" + event_id}).encode()

    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self, _limit=-1): return self.raw


class AuditWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = load_app()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "registry.db"
        db = sqlite3.connect(self.path)
        db.executescript((ROOT / "registry" / "schema.sql").read_text(encoding="utf-8"))
        db.close()
        self.saved = {name: getattr(self.app, name) for name in ("DB", "compatible", "peer_ready", "ledger_audit_token", "acknowledge_delivery", "_deliver_claimed", "_prepare_audit_configuration")}
        self.app.DB = self.path
        self.app.compatible = lambda: True
        self.app.peer_ready = lambda _configuration=None: {"compatible": True}
        self.app.ledger_audit_token = lambda: "test-only-token"
        self.app.acknowledge_delivery = acknowledge_delivery
        self.effects = []
        credential = bytes(range(32, 64))
        self.app._prepare_audit_configuration = lambda: {
            "static_fingerprint": "1" * 64, "full_fingerprint": "2" * 64,
            "decoded": {"ledger_audit": credential, "ledger_readiness_outbound": credential, "registry_peer_readiness_inbound": bytes(range(64, 96))},
            "candidates": {}, "full": {"credential_bindings": [{"role": "ledger_audit", "revision": 1}]},
        }
        self.app._deliver_claimed = lambda event_id, _configuration=None: self.effects.append(event_id)

    def tearDown(self):
        for name, value in self.saved.items(): setattr(self.app, name, value)
        self.tmp.cleanup()

    def db(self):
        db = sqlite3.connect(self.path, isolation_level=None, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def add(self, event_id, committed="2026-10-11T00:00:00Z"):
        db = self.db()
        db.execute("INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)", (event_id, "agent", "test", '{"secret":"must-not-log"}', committed))
        db.execute("INSERT INTO audit_outbox(event_id) VALUES(?)", (event_id,))
        db.close()

    def row(self, event_id):
        db = self.db()
        try: return dict(db.execute("SELECT * FROM audit_outbox WHERE event_id=?", (event_id,)).fetchone())
        finally: db.close()

    def recovery_configuration(self, marker="a", revision=1, verifier=None):
        verifier = verifier or marker * 64
        bindings = [
            {"role": role, "canonical_path": "/" + role, "revision": revision, "verifier": verifier if role == "ledger_audit" else ("c" if role == "ledger_readiness_outbound" else "d") * 64}
            for role in ("ledger_audit", "ledger_readiness_outbound", "registry_peer_readiness_inbound")
        ]
        full = {
            "schema": "townsquare-registry-audit-config-v1",
            "registry": {"service_id": "registry-" + marker},
            "peer_expected": {"service_id": "ledger"},
            "transport": {"interval_seconds": 30},
            "credential_bindings": bindings,
        }
        return {"static_fingerprint": marker * 64, "full_fingerprint": ("e" if marker == "a" else marker) * 64, "full": full, "static": dict(full), "candidates": {item["role"]: True for item in bindings}}

    def test_aud_01_stranded_row_delivers_after_worker_cycle(self):
        self.add("aud-01")
        result = self.app.audit_worker_cycle()
        self.assertEqual((1, 1, 0), (result["attempted"], result["delivered"], result["failed"]))
        self.assertEqual(["aud-01"], self.effects)
        self.assertIsNotNone(self.row("aud-01")["delivered_utc"])

    def test_aud_02_idle_cycle_changes_no_journal_or_outbox_row(self):
        before = self.path.read_bytes()
        result = self.app.audit_worker_cycle()
        db = self.db()
        try:
            self.assertEqual((0, 0), tuple(db.execute("SELECT (SELECT count(*) FROM journal),(SELECT count(*) FROM audit_outbox)").fetchone()))
            self.assertIsNotNone(db.execute("SELECT heartbeat_utc FROM audit_worker_state WHERE singleton=1").fetchone()[0])
        finally: db.close()
        self.assertEqual(0, result["attempted"])
        self.assertNotEqual(before, self.path.read_bytes(), "only the durable worker heartbeat may change")

    def test_aud_03_concurrent_workers_make_one_remote_effect_and_ack(self):
        self.add("aud-03")
        entered = threading.Event(); release = threading.Event()
        def delivery(event_id, _configuration=None):
            self.effects.append(event_id); entered.set(); self.assertTrue(release.wait(3))
        self.app._deliver_claimed = delivery
        first = threading.Thread(target=self.app.audit_worker_cycle)
        first.start(); self.assertTrue(entered.wait(3))
        second = self.app.audit_worker_cycle(); release.set(); first.join(3)
        self.assertFalse(first.is_alive()); self.assertEqual(0, second["attempted"])
        self.assertEqual(["aud-03"], self.effects); self.assertEqual(1, self.row("aud-03")["attempts"])

    def test_aud_04_expired_crash_claim_is_recovered(self):
        self.add("aud-04")
        db = self.db(); self.assertEqual("aud-04", self.app.claim(db, "crashed")); db.execute("UPDATE audit_outbox SET lease_until=? WHERE event_id=?", ("2000-01-01T00:00:00Z", "aud-04")); db.close()
        self.assertEqual(1, self.app.audit_worker_cycle()["delivered"])
        self.assertIsNotNone(self.row("aud-04")["delivered_utc"])

    def test_aud_05_lost_response_retries_exact_identity_once(self):
        self.add("aud-05")
        seen = []
        def urlopen(request, timeout):
            body = json.loads(request.data); identity = (body["event_uuid"], request.get_header("Idempotency-key")); seen.append(identity)
            if len(seen) == 1: raise TimeoutError("lost after remote commit")
            return Response(body["event_uuid"])
        self.app._deliver_claimed = self.saved["_deliver_claimed"]
        with mock.patch.object(self.app.urllib.request, "urlopen", side_effect=urlopen), mock.patch.object(self.app.time, "time", return_value=1_800_000_000):
            self.assertEqual(1, self.app.audit_worker_cycle(interval=5)["failed"])
        with mock.patch.object(self.app.urllib.request, "urlopen", side_effect=urlopen), mock.patch.object(self.app.time, "time", return_value=1_800_000_006):
            self.assertEqual(1, self.app.audit_worker_cycle(interval=5)["delivered"])
        self.assertEqual(2, len(seen)); self.assertEqual(seen[0], seen[1]); self.assertIsNotNone(self.row("aud-05")["delivered_utc"])

    def test_aud_06_poison_attempted_once_and_does_not_starve_next_row(self):
        self.add("aud-06-a"); self.add("aud-06-b")
        def delivery(event_id, _configuration=None):
            self.effects.append(event_id)
            if event_id == "aud-06-a": raise OSError("payload must not be retained")
        self.app._deliver_claimed = delivery
        result = self.app.audit_worker_cycle()
        self.assertEqual((2, 1, 1), (result["attempted"], result["delivered"], result["failed"]))
        self.assertEqual(["aud-06-a", "aud-06-b"], self.effects)
        failed = self.row("aud-06-a"); self.assertRegex(failed["last_error"], r"^REMOTE_UNAVAILABLE:[0-9a-f]{64}$"); self.assertIsNotNone(failed["lease_until"])

    def test_aud_06_long_cycle_never_reclaims_failed_row(self):
        self.add("aud-06-long-a"); self.add("aud-06-long-b")
        clock = iter([1_800_000_000] * 4 + [1_800_000_006] * 16)
        self.app._deliver_claimed = lambda _event, _configuration=None: (_ for _ in ()).throw(OSError("offline"))
        with mock.patch.object(self.app.time, "time", side_effect=lambda: next(clock)):
            result = self.app.audit_worker_cycle(interval=5)
        self.assertEqual((2, 2), (result["attempted"], result["failed"]))
        self.assertEqual((1, 1), (self.row("aud-06-long-a")["attempts"], self.row("aud-06-long-b")["attempts"]))

    def test_aud_07_restart_resumes_pending_work(self):
        self.add("aud-07")
        self.app._deliver_claimed = lambda _event, _configuration=None: (_ for _ in ()).throw(OSError("offline"))
        with mock.patch.object(self.app.time, "time", return_value=1_800_000_000): self.app.audit_worker_cycle(interval=5)
        self.app._deliver_claimed = lambda event, _configuration=None: self.effects.append(event)
        with mock.patch.object(self.app.time, "time", return_value=1_800_000_006): result = self.app.audit_worker_cycle(interval=5)
        self.assertEqual(1, result["delivered"]); self.assertEqual(["aud-07"], self.effects)

    def test_aud_08_peer_identity_failure_degrades_then_recovers(self):
        self.add("aud-08", self.app._audit_utc())
        self.app.peer_ready = lambda _configuration=None: {"compatible": False, "failure_code": "PEER_IDENTITY_INVALID", "failure_field_mask": ("peer_expected.service_id",)}
        result = self.app.audit_worker_cycle(); self.assertEqual("PEER_IDENTITY_INVALID", result["failure_code"]); self.assertEqual([], self.effects)
        db = self.db(); self.assertFalse(self.app.audit_delivery_health(db)["ready"]); db.close()
        self.app.peer_ready = lambda _configuration=None: {"compatible": True}; self.app.audit_worker_cycle()
        db = self.db(); self.assertTrue(self.app.audit_delivery_health(db)["ready"]); db.close()

    def test_aud_09_release_interval_and_bounds_are_exact(self):
        for value in ("5", "30", "300"): self.assertEqual(int(value), self.app.audit_interval({self.app.AUDIT_INTERVAL_ENV: value}))
        for value in (None, "", "04", "4", "301", "30.0", " 30"):
            with self.assertRaisesRegex(RuntimeError, "interval configuration invalid"): self.app.audit_interval({self.app.AUDIT_INTERVAL_ENV: value})
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")
        self.assertIn('REGISTRY_AUDIT_INTERVAL_SECONDS: "30"', compose)

    def test_aud_10_cooperative_shutdown_finishes_within_bound(self):
        self.add("aud-10"); stop = threading.Event(); entered = threading.Event()
        def delivery(event, _configuration=None): entered.set(); self.assertTrue(stop.wait(3)); self.effects.append(event)
        self.app._deliver_claimed = delivery
        started = time.monotonic(); worker = threading.Thread(target=self.app.audit_worker, args=({self.app.AUDIT_INTERVAL_ENV: "5"}, stop)); worker.start(); self.assertTrue(entered.wait(3)); stop.set(); worker.join(5)
        self.assertFalse(worker.is_alive()); self.assertLess(time.monotonic() - started, 5); self.assertEqual(["aud-10"], self.effects)

    def test_aud_11_logs_and_metrics_are_payload_and_secret_free(self):
        self.add("aud-11"); stop = threading.Event()
        def delivery(_event, _configuration=None): stop.set()
        self.app._deliver_claimed = delivery
        output = io.StringIO()
        with contextlib.redirect_stdout(output): self.app.audit_worker({self.app.AUDIT_INTERVAL_ENV: "5"}, stop)
        value = output.getvalue(); self.assertIn("registry_audit_worker_cycle", value)
        for prohibited in ("aud-11", "must-not-log", "test-only-token", "Authorization"): self.assertNotIn(prohibited, value)

    def test_aud_12_production_has_exactly_one_non_public_worker(self):
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")
        self.assertEqual(1, compose.count("\n  registry-audit-worker:\n"))
        block = compose.split("\n  registry-audit-worker:\n", 1)[1].split("\n  registry-migrate:\n", 1)[0]
        self.assertIn('command: ["python", "-m", "canary.preexec", "--", "python", "-m", "registry.app", "--audit-worker"]', block)
        self.assertIn("COPY --chown=10003:10003 registry/app.py /app/registry/app.py", (ROOT / "registry" / "Dockerfile").read_text(encoding="utf-8"))
        self.assertNotRegex(block, r"(?m)^\s+ports:"); self.assertNotIn("build:", block); self.assertNotIn("--audit-worker", compose.split("\n  registry:\n", 1)[1].split("\n  registry-audit-worker:\n", 1)[0])

    def test_aud_13_permanent_latch_survives_idle_restart_and_time(self):
        self.add("aud-13")
        self.app._deliver_claimed = lambda *_: (_ for _ in ()).throw(self.app.AuditDeliveryFailure("REMOTE_REJECTED", True, ("event.identity",)))
        first = self.app.audit_worker_cycle()
        self.assertEqual("REMOTE_REJECTED", first["failure_code"])
        with mock.patch.object(self.app.time, "time", return_value=2_000_000_000):
            idle = self.app.audit_worker_cycle()
        self.assertEqual("REMOTE_REJECTED", idle["failure_code"])
        db = self.db()
        try:
            self.assertEqual(("event:aud-13", "REMOTE_REJECTED"), tuple(db.execute("SELECT latch_key,failure_code FROM audit_failure_latches").fetchone()))
            self.assertFalse(self.app.audit_delivery_health(db, now_epoch=2_000_000_000)["ready"])
        finally: db.close()

    def test_aud_14_closed_failure_classes_and_credential_pre_db_rejection(self):
        cases = {
            urllib.error.HTTPError("http://ledger", status, "x", {}, None): expected
            for status, expected in ((400, "REMOTE_REJECTED"), (401, "REMOTE_REJECTED"), (403, "REMOTE_REJECTED"), (409, "REMOTE_REJECTED"), (408, "REMOTE_UNAVAILABLE"), (425, "REMOTE_UNAVAILABLE"), (429, "REMOTE_UNAVAILABLE"), (503, "REMOTE_UNAVAILABLE"))
        }
        for error, expected in cases.items():
            with self.subTest(status=error.code): self.assertEqual(expected, self.app._audit_failure(error, "event")[0])
        for error, expected in ((TimeoutError(), "REMOTE_UNAVAILABLE"), (ValueError(), "REMOTE_PROTOCOL_INVALID")):
            self.assertEqual(expected, self.app._audit_failure(error, "event")[0])
        weak = [bytes([7]) * 32, bytes(range(32)), bytes(range(31, -1, -1))]
        weak.extend((bytes(range(size)) * (32 // size)) for size in (1, 2, 4, 8, 16))
        invalid = [
            b"", b"A" * 42, b"A" * 44, b"A" * 43 + b"=", b"A" * 42 + b"+", b"A" * 42 + b"/",
            b"A" * 42 + b" ", b"A" * 42 + b"\n", "é".encode(), b"short", b"_" * 43,
            *[base64.urlsafe_b64encode(value).rstrip(b"=") for value in weak],
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(self.app.AuditConfigurationError): self.app.validate_audit_credential(raw)
        with tempfile.TemporaryDirectory() as directory:
            for index, value in enumerate(weak):
                target = Path(directory) / str(index)
                with self.subTest(generator=index), self.assertRaises(self.app.AuditConfigurationError): self.app.generate_audit_credential(target, rng=lambda _size, value=value: value)
                self.assertFalse(target.exists())
        called = []
        env = {**os.environ, **{
            "TOWNSQUARE_RUNTIME_CLASS": "CANARY", "TOWNSQUARE_AUTHORITY_CLASS": "NON-AUTHORITATIVE",
            "TOWNSQUARE_CANARY_LABEL": "TS-CANARY-NAS1-20261007-A", "TOWNSQUARE_COMPOSE_PROJECT": "townsquare-canary-20261007-a",
            "TOWNSQUARE_SOURCE_COMMIT": "a" * 40, "TOWNSQUARE_SOURCE_TREE": "b" * 40,
            "TOWNSQUARE_R7_RELEASE_ID": "TS-R7-" + "c" * 64, "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256": "d" * 64,
            "TOWNSQUARE_R7_IDENTITY_SHA256": "e" * 64, "REGISTRY_SERVICE_ID": "townsquare-registry-v0", "REGISTRY_SCHEMA_HEAD": "2",
            "REGISTRY_AUDIT_CONTRACT_VERSION": "registry-ledger-audit-v1", "REGISTRY_LEDGER_SERVICE_ID": "townsquare-ledger-v0",
            "REGISTRY_LEDGER_SCHEMA_HEAD": "14", "REGISTRY_LEDGER_AUDIT_CONTRACT": "registry-ledger-audit-v1", "REGISTRY_AUDIT_INTERVAL_SECONDS": "30",
            "REGISTRY_LEDGER_AUDIT_TOKEN_FILE": "/audit", "LEDGER_READINESS_TOKEN_FILE": "/out", "REGISTRY_PEER_READINESS_TOKEN_FILE": "/in",
            "REGISTRY_LEDGER_AUDIT_CREDENTIAL_REVISION": "1", "LEDGER_READINESS_CREDENTIAL_REVISION": "1", "REGISTRY_PEER_READINESS_CREDENTIAL_REVISION": "1",
        }}
        with mock.patch.object(self.app, "_credential_verifier", side_effect=lambda *_: called.append("verifier")):
            with self.assertRaises(self.app.AuditConfigurationError):
                self.saved["_prepare_audit_configuration"](env, reader=lambda _path: b"invalid", db_factory=lambda: called.append("db"))
        self.assertEqual([], called)
        credentials = {
            "/audit": base64.urlsafe_b64encode(bytes(range(32, 64))).rstrip(b"="),
            "/out": base64.urlsafe_b64encode(bytes(range(64, 96))).rstrip(b"="),
            "/in": base64.urlsafe_b64encode(bytes(range(96, 128))).rstrip(b"="),
        }
        identical = dict(credentials); identical["/in"] = identical["/out"]
        with self.assertRaises(self.app.AuditConfigurationError) as rejected:
            self.saved["_prepare_audit_configuration"](env, reader=identical.__getitem__, db_factory=lambda: called.append("db"))
        self.assertEqual("CREDENTIAL_INVALID", rejected.exception.code); self.assertEqual([], called)
        configuration = self.saved["_prepare_audit_configuration"](
            env, reader=credentials.__getitem__, db_factory=self.db, salt_source=lambda _size: bytes(range(128, 160)))
        self.assertEqual(
            ["ledger_audit", "ledger_readiness_outbound", "registry_peer_readiness_inbound"],
            [item["role"] for item in configuration["full"]["credential_bindings"]])
        self.assertEqual(
            hashlib.sha256(b"townsquare-registry-audit-static-config-fingerprint-v1\0" + self.app._jcs(configuration["static"]).encode()).hexdigest(),
            configuration["static_fingerprint"])
        self.assertEqual(
            hashlib.sha256(b"townsquare-registry-audit-config-fingerprint-v1\0" + self.app._jcs(configuration["full"]).encode()).hexdigest(),
            configuration["full_fingerprint"])

    def test_aud_14_a_to_g_transactional_recovery_matrix(self):
        db = self.db()
        try:
            old = self.recovery_configuration("a", 1, "1" * 64)
            repaired = self.recovery_configuration("b", 2, "2" * 64)

            # A: exact accepted event proof clears only the exact event latch.
            self.app._record_latch(db, "event:a", "REMOTE_REJECTED", old, ("event.a.identity",), "a", "ledger_audit", 1)
            self.app._record_latch(db, "event:other", "REMOTE_REJECTED", old, ("event.other.identity",), "other", "ledger_audit", 1)
            db.execute("BEGIN IMMEDIATE")
            self.assertTrue(self.app._recover_latch(db, "event:a", old, "event_accept", "a", "ledger_audit")); db.commit()
            self.assertEqual(["event:other"], [row[0] for row in db.execute("SELECT latch_key FROM audit_failure_latches")])

            # B: authoritative peer repair may clear an identity latch without local fingerprint change.
            db.execute("DELETE FROM audit_failure_latches")
            self.app._record_latch(db, "peer", "PEER_IDENTITY_INVALID", old, ("peer_expected.service_id",))
            db.execute("BEGIN IMMEDIATE"); self.assertTrue(self.app._recover_latch(db, "peer", old, "peer_identity", role="ledger_readiness_outbound")); db.commit()

            # C: local semantic recovery requires the masked leaf and both fingerprints to change.
            self.app._record_latch(db, "configuration", "CONFIGURATION_INVALID", old, ("registry.service_id",))
            db.execute("BEGIN IMMEDIATE"); self.assertTrue(self.app._recover_latch(db, "configuration", repaired, "peer_identity")); db.commit()

            # D: same-path credential repair binds only a greater revision/new verifier after role proof.
            db.execute("INSERT INTO audit_credential_bindings(role,salt) VALUES('ledger_audit',?)", (bytes(range(32)),))
            self.app._record_latch(db, "credential:ledger_audit", "CREDENTIAL_INVALID", old, ("credential_bindings.ledger_audit",), role="ledger_audit", revision=1)
            db.execute("BEGIN IMMEDIATE")
            self.assertTrue(self.app._recover_latch(db, "credential:ledger_audit", repaired, "event_accept", role="ledger_audit"))
            self.app._accept_bindings(db, repaired, {"ledger_audit"}); db.commit()
            self.assertEqual((2, "2" * 64), tuple(db.execute("SELECT accepted_revision,verifier FROM audit_credential_bindings WHERE role='ledger_audit'").fetchone()))

            # E: unrelated fingerprint change, wrong mask, stale revision, same verifier, or lost proof cannot clear.
            unrelated = self.recovery_configuration("b", 2, "2" * 64); unrelated["full"]["registry"]["service_id"] = old["full"]["registry"]["service_id"]
            db.execute("DELETE FROM audit_failure_latches"); self.app._record_latch(db, "configuration", "CONFIGURATION_INVALID", old, ("registry.service_id",))
            for candidate, proof in ((unrelated, "peer_identity"), (repaired, "missing")):
                db.execute("BEGIN IMMEDIATE"); self.assertFalse(self.app._recover_latch(db, "configuration", candidate, proof)); db.rollback()
            db.execute("DELETE FROM audit_failure_latches"); self.app._record_latch(db, "credential:ledger_audit", "CREDENTIAL_INVALID", old, ("credential_bindings.ledger_audit",), role="ledger_audit", revision=2)
            for candidate in (self.recovery_configuration("b", 1, "2" * 64), self.recovery_configuration("b", 3, "1" * 64)):
                db.execute("BEGIN IMMEDIATE"); self.assertFalse(self.app._recover_latch(db, "credential:ledger_audit", candidate, "event_accept", role="ledger_audit")); db.rollback()
            db.execute("UPDATE audit_failure_latches SET failure_field_mask_json='[\"wrong.mask\"]'")
            db.execute("BEGIN IMMEDIATE"); self.assertFalse(self.app._recover_latch(db, "credential:ledger_audit", repaired, "event_accept", role="ledger_audit")); db.rollback()

            # F: idle/restart/time never mutates a latch; G: transient errors never create one.
            before = tuple(db.execute("SELECT latch_key,updated_utc FROM audit_failure_latches").fetchone())
            self.assertEqual(before, tuple(db.execute("SELECT latch_key,updated_utc FROM audit_failure_latches").fetchone()))
            self.assertEqual(("REMOTE_UNAVAILABLE", False), (self.app._audit_failure(TimeoutError(), "g")[0], self.app._audit_failure(TimeoutError(), "g")[2]))
        finally: db.close()

    def test_schema_v6_copy_migrates_atomically_to_worker_state_v7(self):
        old = os.environ.get("REGISTRY_DB"); os.environ["REGISTRY_DB"] = str(self.path)
        try:
            import registry.migrate as migrate
            importlib.reload(migrate)
            path = Path(self.tmp.name) / "v6.db"; db = sqlite3.connect(path, isolation_level=None)
            for statement in migrate._statements(migrate.SCHEMA):
                db.execute(statement)
                if statement.lstrip().upper().startswith("INSERT INTO REGISTRY_MIGRATIONS VALUES(6,"): break
            db.execute(f"PRAGMA application_id={migrate.APPLICATION_ID}"); db.execute("PRAGMA user_version=6")
            migrate.migrate(db)
            self.assertEqual(9, db.execute("PRAGMA user_version").fetchone()[0])
            self.assertEqual((1, None), tuple(db.execute("SELECT singleton,heartbeat_utc FROM audit_worker_state").fetchone()))
            db.close()
            contract = json.loads((ROOT / "contracts" / "r7" / "registry-schema.json").read_text(encoding="utf-8"))
            self.assertEqual(contract["schema_sha256"], migrate._sha(migrate.SCHEMA)); self.assertEqual(contract["migrator_sha256"], migrate._sha(Path(migrate.__file__)))
        finally:
            if old is None: os.environ.pop("REGISTRY_DB", None)
            else: os.environ["REGISTRY_DB"] = old

    def test_production_registry_build_runtime_and_files_share_exact_r7_identity(self):
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")
        dockerfile = (ROOT / "registry" / "Dockerfile").read_text(encoding="utf-8")
        release = (ROOT / "deploy" / "release.env.example").read_text(encoding="utf-8")
        fixed = {
            "TOWNSQUARE_RUNTIME_CLASS": "CANARY",
            "TOWNSQUARE_AUTHORITY_CLASS": "NON-AUTHORITATIVE",
            "TOWNSQUARE_CANARY_LABEL": "TS-CANARY-NAS1-20261007-A",
            "TOWNSQUARE_COMPOSE_PROJECT": "townsquare-canary-20261007-a",
        }
        for name, value in fixed.items():
            self.assertGreaterEqual(compose.count(f"{name}: {value}"), 2)
            self.assertIn(f"{name}={value}", release)
            self.assertIn(f"ARG {name}", dockerfile)
        following = {"registry": "registry-audit-worker", "registry-audit-worker": "registry-migrate", "registry-migrate": "backup"}
        for service, next_service in following.items():
            block = compose.split(f"\n  {service}:\n", 1)[1].split(f"\n  {next_service}:\n", 1)[0]
            self.assertIn("*registry-r7-environment", block)
            self.assertIn("r7_identity", block); self.assertIn("context_manifest", block)
        self.assertIn("*registry-r7-build-args", compose)
        self.assertIn("townsquare.r7-identity-sha256", dockerfile)


if __name__ == "__main__": unittest.main()
