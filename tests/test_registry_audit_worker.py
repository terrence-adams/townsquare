"""AUD-01..12 behavior checks for the durable Registry audit worker."""
from __future__ import annotations

import contextlib
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
        self.saved = {name: getattr(self.app, name) for name in ("DB", "compatible", "peer_ready", "ledger_audit_token", "acknowledge_delivery", "_deliver_claimed")}
        self.app.DB = self.path
        self.app.compatible = lambda: True
        self.app.peer_ready = lambda: {"compatible": True}
        self.app.ledger_audit_token = lambda: "test-only-token"
        self.app.acknowledge_delivery = acknowledge_delivery
        self.effects = []
        self.app._deliver_claimed = lambda event_id: self.effects.append(event_id)

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
        def delivery(event_id):
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
        def delivery(event_id):
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
        self.app._deliver_claimed = lambda _event: (_ for _ in ()).throw(OSError("offline"))
        with mock.patch.object(self.app.time, "time", side_effect=lambda: next(clock)):
            result = self.app.audit_worker_cycle(interval=5)
        self.assertEqual((2, 2), (result["attempted"], result["failed"]))
        self.assertEqual((1, 1), (self.row("aud-06-long-a")["attempts"], self.row("aud-06-long-b")["attempts"]))

    def test_aud_07_restart_resumes_pending_work(self):
        self.add("aud-07")
        self.app._deliver_claimed = lambda _event: (_ for _ in ()).throw(OSError("offline"))
        with mock.patch.object(self.app.time, "time", return_value=1_800_000_000): self.app.audit_worker_cycle(interval=5)
        self.app._deliver_claimed = lambda event: self.effects.append(event)
        with mock.patch.object(self.app.time, "time", return_value=1_800_000_006): result = self.app.audit_worker_cycle(interval=5)
        self.assertEqual(1, result["delivered"]); self.assertEqual(["aud-07"], self.effects)

    def test_aud_08_peer_identity_failure_degrades_then_recovers(self):
        self.add("aud-08", self.app._audit_utc())
        self.app.peer_ready = lambda: {"compatible": False}
        result = self.app.audit_worker_cycle(); self.assertEqual("PEER_IDENTITY_INVALID", result["failure_code"]); self.assertEqual([], self.effects)
        db = self.db(); self.assertFalse(self.app.audit_delivery_health(db)["ready"]); db.close()
        self.app.peer_ready = lambda: {"compatible": True}; self.app.audit_worker_cycle()
        db = self.db(); self.assertTrue(self.app.audit_delivery_health(db)["ready"]); db.close()

    def test_aud_09_release_interval_and_bounds_are_exact(self):
        for value in ("5", "30", "300"): self.assertEqual(int(value), self.app.audit_interval({self.app.AUDIT_INTERVAL_ENV: value}))
        for value in (None, "", "04", "4", "301", "30.0", " 30"):
            with self.assertRaisesRegex(RuntimeError, "interval configuration invalid"): self.app.audit_interval({self.app.AUDIT_INTERVAL_ENV: value})
        compose = (ROOT / "compose.yml").read_text(encoding="utf-8")
        self.assertIn('REGISTRY_AUDIT_INTERVAL_SECONDS: "30"', compose)

    def test_aud_10_cooperative_shutdown_finishes_within_bound(self):
        self.add("aud-10"); stop = threading.Event(); entered = threading.Event()
        def delivery(event): entered.set(); self.assertTrue(stop.wait(3)); self.effects.append(event)
        self.app._deliver_claimed = delivery
        started = time.monotonic(); worker = threading.Thread(target=self.app.audit_worker, args=({self.app.AUDIT_INTERVAL_ENV: "5"}, stop)); worker.start(); self.assertTrue(entered.wait(3)); stop.set(); worker.join(5)
        self.assertFalse(worker.is_alive()); self.assertLess(time.monotonic() - started, 5); self.assertEqual(["aud-10"], self.effects)

    def test_aud_11_logs_and_metrics_are_payload_and_secret_free(self):
        self.add("aud-11"); stop = threading.Event()
        def delivery(_event): stop.set()
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
            self.assertEqual(7, db.execute("PRAGMA user_version").fetchone()[0])
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
