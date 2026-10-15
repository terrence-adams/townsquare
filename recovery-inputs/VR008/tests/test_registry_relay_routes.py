"""Focused Registry control-plane checks for coordinator relay routes."""
from __future__ import annotations

import base64
import http.client
import importlib
import json
import os
import secrets
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from tests.test_session_registry_s1 import load_app


ROOT = Path(__file__).resolve().parents[1]


class RegistryRelayRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = load_app()

    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript((ROOT / "registry" / "schema.sql").read_text(encoding="utf-8"))
        now = "2026-10-10T12:00:00Z"
        for agent_id in ("eddie-brock", "nimrod"):
            self.db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", (agent_id, "{}", 1, 1, now))
        self.alpha_session = "11111111-1111-4111-8111-111111111111"
        self.other_session = "22222222-2222-4222-8222-222222222222"
        self.private_locator = secrets.token_urlsafe(48)
        self.db.execute(
            "INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (self.alpha_session, "eddie-brock", "codex", self.private_locator, "alpha-host", "runtime", "model", "ACTIVE", now, now, None, "VR008", 1, now),
        )
        self.db.execute(
            "INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (self.other_session, "nimrod", "codex", secrets.token_urlsafe(48), "nimrod-host", "runtime", "model", "ACTIVE", now, now, None, "VR008", 1, now),
        )
        self.db.commit()
        self.public_key = base64.b64encode(os.urandom(32)).decode()

    def tearDown(self):
        self.db.close()

    def bind(self, *, key="bind-1", session_uuid=None, expected=0, **extra):
        body = {
            "session_uuid": session_uuid or self.alpha_session,
            "capability_version": "1",
            "dispatcher_key_id": "alpha-dispatcher-1",
            "dispatcher_public_key": self.public_key,
            "expected_route_revision": expected,
        }
        body.update(extra)
        return self.app.mutate_relay_route(self.db, "operator", key, "eddie-brock", body, "bind")

    def counts(self):
        return tuple(self.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in ("relay_routes", "relay_route_journal", "requests"))

    def test_bind_and_resolve_return_only_the_safe_frozen_projection(self):
        status, route = self.bind()
        self.assertEqual(200, status)
        self.assertEqual(
            {
                "agent_id", "seat_or_host", "session_uuid", "transport", "recipient_id",
                "relay_capability", "capability_version", "dispatcher_key_id",
                "dispatcher_public_key", "route_revision", "route_state", "session_state",
                "last_verified_utc",
            },
            set(route),
        )
        self.assertEqual("eddie-brock", route["recipient_id"])
        self.assertEqual("revere.v1", route["transport"])
        self.assertEqual("coordinator-contact", route["relay_capability"])
        self.assertEqual(1, route["route_revision"])
        serialized = repr(route) + self.db.execute("SELECT body_json FROM relay_route_journal").fetchone()[0]
        self.assertNotIn(self.private_locator, serialized)
        self.assertNotIn("provider_session_id", serialized)
        self.assertNotIn("authority", serialized)

    def test_stale_revision_and_session_mismatch_reject_before_any_route_effect(self):
        status, mismatch = self.bind(session_uuid=self.other_session)
        self.assertEqual(409, status)
        self.assertEqual("ROUTE_MISMATCH", mismatch["disposition"])
        self.assertEqual((0, 0, 0), self.counts())

        self.assertEqual(200, self.bind()[0])
        before = self.counts()
        status, stale = self.bind(key="stale", expected=0, dispatcher_key_id="replacement")
        self.assertEqual(409, status)
        self.assertEqual({"disposition": "STALE_ROUTE", "route_revision": 1}, stale)
        self.assertEqual(before, self.counts())
        self.assertEqual(self.alpha_session, self.db.execute("SELECT session_uuid FROM relay_routes").fetchone()[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE relay_routes SET route_revision=route_revision WHERE agent_id='eddie-brock'")

    def test_disable_increments_revision_and_has_no_session_or_authority_side_effect(self):
        self.assertEqual(200, self.bind()[0])
        session_before = tuple(self.db.execute("SELECT status,revision,updated_utc FROM sessions WHERE session_uuid=?", (self.alpha_session,)).fetchone())
        agent_before = tuple(self.db.execute("SELECT active,revision,updated_utc FROM agents WHERE agent_id='eddie-brock'").fetchone())
        status, disabled = self.app.mutate_relay_route(
            self.db, "operator", "disable-1", "eddie-brock", {"expected_route_revision": 1}, "disable"
        )
        self.assertEqual(200, status)
        self.assertEqual("DISABLED", disabled["route_state"])
        self.assertEqual(2, disabled["route_revision"])
        self.assertEqual((409, {"disposition": "ROUTE_INELIGIBLE"}), self.app.resolve_relay_route(self.db, "eddie-brock"))
        self.assertEqual(session_before, tuple(self.db.execute("SELECT status,revision,updated_utc FROM sessions WHERE session_uuid=?", (self.alpha_session,)).fetchone()))
        self.assertEqual(agent_before, tuple(self.db.execute("SELECT active,revision,updated_utc FROM agents WHERE agent_id='eddie-brock'").fetchone()))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM relay_route_journal")

    def test_ineligible_route_and_invalid_dispatcher_key_fail_closed(self):
        status, invalid = self.bind(dispatcher_public_key="not-an-ed25519-public-key")
        self.assertEqual(400, status)
        self.assertEqual({"detail": "invalid relay route request"}, invalid)
        self.db.execute("UPDATE sessions SET status='ENDED',ended_utc=updated_utc WHERE session_uuid=?", (self.alpha_session,))
        self.db.commit()
        status, ineligible = self.bind()
        self.assertEqual(409, status)
        self.assertEqual("ROUTE_INELIGIBLE", ineligible["disposition"])
        self.assertEqual((0, 0, 0), self.counts())

    def test_exact_replay_is_idempotent_and_changed_replay_is_rejected(self):
        status, original = self.bind()
        self.assertEqual(200, status)
        before = self.counts()
        self.assertEqual((status, original), self.bind())
        self.assertEqual(before, self.counts())
        changed_status, changed = self.bind(dispatcher_key_id="different")
        self.assertEqual(409, changed_status)
        self.assertEqual("idempotency key reused with different request", changed["detail"])
        self.assertEqual(before, self.counts())

    def test_migration_from_accepted_head_four_reaches_head_five(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry-head-four.db"
            db = sqlite3.connect(path)
            try:
                current = ""
                for line in (ROOT / "registry" / "schema.sql").read_text(encoding="utf-8").splitlines(True):
                    current += line
                    if sqlite3.complete_statement(current):
                        if current.lstrip().upper().startswith("CREATE TABLE RELAY_ROUTES"):
                            break
                        db.execute(current)
                        current = ""
                db.execute("PRAGMA application_id=1414746695")
                db.execute("PRAGMA user_version=4")
                db.commit()
                old = os.environ.get("REGISTRY_DB")
                os.environ["REGISTRY_DB"] = str(path)
                try:
                    import registry.migrate as migrate
                    migrate = importlib.reload(migrate)
                    self.assertEqual(5, migrate.migrate(db))
                finally:
                    if old is None:
                        os.environ.pop("REGISTRY_DB", None)
                    else:
                        os.environ["REGISTRY_DB"] = old
                self.assertEqual([(1,), (2,), (3,), (4,), (5,)], list(db.execute("SELECT version FROM registry_migrations ORDER BY version")))
                self.assertEqual({"relay_routes", "relay_route_journal"}, {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'relay_route%'")})
            finally:
                db.close()


class RegistryRelayRouteHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = load_app()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "registry.db"
        self.token_path = Path(self.tmp.name) / "registry-token"
        self.api_token = secrets.token_urlsafe(32)
        self.operator_token = secrets.token_urlsafe(32)
        self.token_path.write_text(self.api_token, encoding="utf-8")
        db = sqlite3.connect(self.db_path)
        db.executescript((ROOT / "registry" / "schema.sql").read_text(encoding="utf-8"))
        now = "2026-10-10T12:00:00Z"
        db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", ("eddie-brock", "{}", 1, 1, now))
        db.execute(
            "INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("11111111-1111-4111-8111-111111111111", "eddie-brock", "codex", secrets.token_urlsafe(48), "alpha-host", "runtime", "model", "ACTIVE", now, now, None, "VR008", 1, now),
        )
        db.commit()
        db.close()
        self.app.DB = self.db_path
        self.app.TOKEN_FILE = str(self.token_path)
        self.old_operator_token = os.environ.get("REGISTRY_OPERATOR_TOKEN")
        os.environ["REGISTRY_OPERATOR_TOKEN"] = self.operator_token
        self.server = self.app.ThreadingHTTPServer(("127.0.0.1", 0), self.app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        if self.old_operator_token is None:
            os.environ.pop("REGISTRY_OPERATOR_TOKEN", None)
        else:
            os.environ["REGISTRY_OPERATOR_TOKEN"] = self.old_operator_token
        self.tmp.cleanup()

    def request(self, method, path, *, body=None, operator=True, key="route-http-1"):
        headers = {"Authorization": "Bearer " + self.api_token}
        if operator:
            headers["X-Registry-Operator-Token"] = self.operator_token
        if body is not None:
            headers.update({"Content-Type": "application/json", "Idempotency-Key": key, "X-Registry-Principal": "operator"})
            encoded = json.dumps(body).encode()
        else:
            encoded = None
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path, body=encoded, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, {name.lower(): value for name, value in response.getheaders()}, json.loads(raw)
        finally:
            connection.close()

    def test_admin_bind_safe_get_and_disable_endpoints(self):
        body = {
            "session_uuid": "11111111-1111-4111-8111-111111111111",
            "capability_version": "1",
            "dispatcher_key_id": "alpha-dispatcher-1",
            "dispatcher_public_key": base64.b64encode(os.urandom(32)).decode(),
            "expected_route_revision": 0,
        }
        status, headers, _ = self.request("POST", "/v1/relay-routes/eddie-brock", body=body, operator=False)
        self.assertEqual(404, status)
        self.assertEqual("no-store", headers.get("cache-control"))
        status, headers, bound = self.request("POST", "/v1/relay-routes/eddie-brock", body=body)
        self.assertEqual(200, status)
        self.assertEqual("no-store", headers.get("cache-control"))
        status, _, resolved = self.request("GET", "/v1/relay-routes/eddie-brock")
        self.assertEqual(200, status)
        self.assertEqual(bound, resolved)
        self.assertNotIn("provider_session_id", resolved)
        self.assertNotIn("authority_granted", resolved)
        status, _, disabled = self.request("POST", "/v1/relay-routes/eddie-brock/disable", body={"expected_route_revision": 1}, key="route-http-disable")
        self.assertEqual(200, status)
        self.assertEqual("DISABLED", disabled["route_state"])
        status, _, failure = self.request("GET", "/v1/relay-routes/eddie-brock")
        self.assertEqual((409, {"disposition": "ROUTE_INELIGIBLE"}), (status, failure))

    def test_role_label_is_not_a_resolvable_identity(self):
        status, _, value = self.request("GET", "/v1/relay-routes/Alpha")
        self.assertEqual(404, status)
        self.assertEqual({"detail": "not found"}, value)


if __name__ == "__main__":
    unittest.main()
