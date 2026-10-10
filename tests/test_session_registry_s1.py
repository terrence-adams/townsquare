"""Focused acceptance checks for SESSION-REGISTRY-PERSIST-LIFECYCLE (S1)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import secrets
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_app():
    """Load the mutation boundary without requiring a real canary authority."""
    shared = types.ModuleType("shared")
    authority = types.ModuleType("shared.canary_authority")
    authority.CanaryAuthorityError = RuntimeError
    authority.CanaryProofVerifier = object
    authority.FileNonceStore = object
    authority.canonical_bytes = lambda value: json.dumps(value, sort_keys=True).encode()
    authority.decode_proof = authority.decode_signature = lambda value: value
    authority.load_r7_context = lambda *_: "test-context"
    identity = types.ModuleType("shared.canary_identity")
    identity.compatible_identity = lambda *_: True
    identity.require_canary_identity = lambda: types.SimpleNamespace(as_dict=lambda: {})
    outbox = types.ModuleType("shared.registry_outbox")
    outbox.acknowledge_delivery = lambda *_: True
    old = {name: sys.modules.get(name) for name in ("shared", "shared.canary_authority", "shared.canary_identity", "shared.registry_outbox")}
    sys.modules.update({"shared": shared, "shared.canary_authority": authority, "shared.canary_identity": identity, "shared.registry_outbox": outbox})
    try:
        spec = importlib.util.spec_from_file_location("session_registry_s1_app", ROOT / "registry" / "app.py")
        module = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(module)
        return module
    finally:
        for name, value in old.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value


class SessionRegistryS1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = load_app()

    def setUp(self):
        self.locator = secrets.token_urlsafe(48)
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript((ROOT / "registry" / "schema.sql").read_text(encoding="utf-8"))
        self.db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", ("active-agent", "{}", 1, 1, "2026-01-01T00:00:00Z"))
        self.db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", ("retired-agent", "{}", 1, 0, "2026-01-01T00:00:00Z"))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def register(self, key="register-1", **extra):
        body = {"agent_id": "active-agent", "provider": "vendor", "provider_session_id": self.locator, "initial_status": "STARTING", "work_ref": "VR-test"}
        body.update(extra)
        return self.app.mutate_session(self.db, "caller", key, body, "register")

    def counts(self):
        return tuple(self.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("sessions", "session_journal", "audit_outbox"))

    def register_in_state(self, state, key):
        initial = "ACTIVE" if state == "ACTIVE" else "STARTING"
        _, registered = self.register(key, provider_session_id=secrets.token_urlsafe(48), initial_status=initial)
        if state == "IDLE":
            status, registered = self.app.mutate_session(self.db, "caller", f"{key}-to-active", {"session_uuid": registered["session_uuid"], "status": "ACTIVE"}, "heartbeat")
            self.assertEqual(200, status)
            status, registered = self.app.mutate_session(self.db, "caller", f"{key}-to-idle", {"session_uuid": registered["session_uuid"], "status": "IDLE"}, "heartbeat")
            self.assertEqual(200, status)
        return registered

    def test_registration_requires_active_agent_and_hides_locator_from_response_and_outbox(self):
        status, response = self.register(agent_id="unknown-agent")
        self.assertEqual(409, status)
        self.assertEqual((0, 0, 0), self.counts())
        status, response = self.register(agent_id="retired-agent")
        self.assertEqual(409, status)
        self.assertEqual((0, 0, 0), self.counts())
        status, response = self.register()
        self.assertEqual(201, status)
        self.assertNotIn("provider_session_id", response)
        self.assertEqual((1, 1, 1), self.counts())
        audit_body = self.db.execute("SELECT body_json FROM journal WHERE action='session_register'").fetchone()[0]
        self.assertFalse(self.locator in audit_body, "generated locator leaked into the audit journal")

    def test_registration_rejects_non_printable_or_oversized_private_locator_without_writes(self):
        for locator in (secrets.token_urlsafe(24) + "\n", secrets.token_urlsafe(385)):
            status, _ = self.register(provider_session_id=locator)
            self.assertEqual(400, status)
            self.assertEqual((0, 0, 0), self.counts())

    def test_exact_replay_is_zero_write_and_changed_replay_is_rejected(self):
        status, original = self.register()
        self.assertEqual(201, status)
        before = self.counts() + (original["revision"],)
        status, replay = self.register()
        self.assertEqual(201, status)
        self.assertEqual(original, replay)
        self.assertEqual(before, self.counts() + (self.db.execute("SELECT revision FROM sessions").fetchone()[0],))
        status, _ = self.register(work_ref="different")
        self.assertEqual(409, status)
        self.assertEqual(before, self.counts() + (self.db.execute("SELECT revision FROM sessions").fetchone()[0],))

    def test_duplicate_locator_has_no_writes_and_history_is_immutable(self):
        self.register()
        before = self.counts()
        status, _ = self.register("register-2")
        self.assertEqual(409, status)
        self.assertEqual(before, self.counts())
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE session_journal SET action='heartbeat'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM session_journal")

    def test_every_approved_lifecycle_transition_is_atomic_and_timestamped(self):
        cases = (
            ("STARTING", "heartbeat", "ACTIVE", "ACTIVE"),
            ("ACTIVE", "heartbeat", "ACTIVE", "ACTIVE"),
            ("ACTIVE", "heartbeat", "IDLE", "IDLE"),
            ("IDLE", "heartbeat", "IDLE", "IDLE"),
            ("IDLE", "heartbeat", "ACTIVE", "ACTIVE"),
        )
        for index, (initial, action, requested, expected) in enumerate(cases):
            registered = self.register_in_state(initial, f"register-{index}")
            body = {"session_uuid": registered["session_uuid"], "status": requested}
            status, response = self.app.mutate_session(self.db, "caller", f"transition-{index}", body, action)
            self.assertEqual(200, status)
            self.assertEqual(expected, response["status"])
            self.assertGreaterEqual(response["last_seen_utc"], registered["last_seen_utc"])
            self.assertEqual(2 if initial != "IDLE" else 4, self.db.execute("SELECT count(*) FROM session_journal WHERE session_uuid=?", (registered["session_uuid"],)).fetchone()[0])

    def test_every_live_state_can_end_or_be_marked_lost_and_terminal_writes_are_zero_write(self):
        for index, initial in enumerate(("STARTING", "ACTIVE", "IDLE")):
            for terminal in ("ENDED", "LOST"):
                key = f"{initial}-{terminal}"
                registered = self.register_in_state(initial, f"register-{key}")
                status, terminal_response = self.app.mutate_session(self.db, "caller", f"terminate-{key}", {"session_uuid": registered["session_uuid"], "terminal_status": terminal}, "terminate")
                self.assertEqual(200, status)
                self.assertEqual(terminal, terminal_response["status"])
                self.assertEqual(terminal_response["ended_utc"], terminal_response["last_seen_utc"])
                before = self.counts() + (terminal_response["revision"],)
                for action, body in (("heartbeat", {"session_uuid": registered["session_uuid"], "status": "ACTIVE"}), ("terminate", {"session_uuid": registered["session_uuid"], "terminal_status": "ENDED"})):
                    status, _ = self.app.mutate_session(self.db, "caller", f"after-{key}-{action}", body, action)
                    self.assertEqual(409, status)
                    self.assertEqual(before, self.counts() + (self.db.execute("SELECT revision FROM sessions WHERE session_uuid=?", (registered["session_uuid"],)).fetchone()[0],))

    def test_unlisted_live_transition_is_conflict_with_no_writes(self):
        _, registered = self.register(initial_status="STARTING")
        before = self.counts() + (registered["revision"],)
        status, _ = self.app.mutate_session(self.db, "caller", "starting-to-idle", {"session_uuid": registered["session_uuid"], "status": "IDLE"}, "heartbeat")
        self.assertEqual(409, status)
        self.assertEqual(before, self.counts() + (self.db.execute("SELECT revision FROM sessions WHERE session_uuid=?", (registered["session_uuid"],)).fetchone()[0],))

    def test_migration_from_v2_creates_s1_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry.db"
            db = sqlite3.connect(path)
            try:
                statements = (ROOT / "registry" / "schema.sql").read_text(encoding="utf-8").splitlines(True)
                current = ""
                executed = 0
                for line in statements:
                    current += line
                    if sqlite3.complete_statement(current):
                        executed += 1
                        if executed <= 15:
                            db.execute(current)
                        current = ""
                db.execute("PRAGMA application_id=1414746695")
                db.execute("PRAGMA user_version=2")
                db.execute("INSERT INTO requests VALUES(?,?,?,?)", ("legacy", "legacy-key", "legacy-hash", "{}"))
                db.commit()
                old = __import__("os").environ.get("REGISTRY_DB")
                __import__("os").environ["REGISTRY_DB"] = str(path)
                try:
                    import registry.migrate as migrate
                    migrate = __import__("importlib").reload(migrate)
                    migrate.migrate(db)
                finally:
                    if old is None: __import__("os").environ.pop("REGISTRY_DB", None)
                    else: __import__("os").environ["REGISTRY_DB"] = old
                self.assertEqual([(1,), (2,), (3,), (4,)], list(db.execute("SELECT version FROM registry_migrations ORDER BY version")))
                self.assertEqual({"sessions", "session_journal"}, {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('sessions','session_journal')")})
                self.assertIn("response_status", {row[1] for row in db.execute("PRAGMA table_info(requests)")})
                self.assertEqual(200, db.execute("SELECT response_status FROM requests WHERE principal='legacy'").fetchone()[0])
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
