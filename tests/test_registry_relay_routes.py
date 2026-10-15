"""Focused Registry control-plane checks for coordinator relay routes (migration 11)."""
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
NOW = "2026-10-10T12:00:00Z"
ALPHA_SESSION = "11111111-1111-4111-8111-111111111111"
OTHER_SESSION = "22222222-2222-4222-8222-222222222222"


def add_session(db, session_uuid, agent_id, seat, status="ACTIVE", locator=None):
    db.execute(
        "INSERT INTO sessions(session_uuid,agent_id,provider,provider_session_id,seat_or_host,runtime,model,status,started_utc,last_seen_utc,ended_utc,work_ref,revision,updated_utc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (session_uuid, agent_id, "codex", locator or secrets.token_urlsafe(48), seat, "runtime", "model", status, NOW, NOW, None, "VR008", 1, NOW),
    )


class RegistryRelayRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = load_app()

    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript((ROOT / "registry" / "schema.sql").read_text(encoding="utf-8"))
        for agent_id in ("eddie-brock", "nimrod"):
            self.db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", (agent_id, "{}", 1, 1, NOW))
        self.private_locator = secrets.token_urlsafe(48)
        add_session(self.db, ALPHA_SESSION, "eddie-brock", "alpha-host", locator=self.private_locator)
        add_session(self.db, OTHER_SESSION, "nimrod", "nimrod-host")
        self.db.commit()
        self.public_key = base64.b64encode(os.urandom(32)).decode()

    def tearDown(self):
        self.db.close()

    def bind(self, *, key="bind-1", session_uuid=None, expected=0, **extra):
        body = {
            "session_uuid": session_uuid or ALPHA_SESSION,
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
        self.assertEqual((200, route), self.app.resolve_relay_route(self.db, "eddie-brock"))
        serialized = repr(route) + self.db.execute("SELECT body_json FROM relay_route_journal").fetchone()[0]
        self.assertNotIn(self.private_locator, serialized)
        self.assertNotIn("provider_session_id", serialized)
        self.assertNotIn("authority", serialized)

    def test_unknown_route_is_not_found(self):
        self.assertEqual((404, {"disposition": "ROUTE_NOT_FOUND"}), self.app.resolve_relay_route(self.db, "eddie-brock"))
        status, missing = self.app.mutate_relay_route(self.db, "operator", "d", "eddie-brock", {"expected_route_revision": 1}, "disable")
        self.assertEqual((404, {"disposition": "ROUTE_NOT_FOUND"}), (status, missing))
        self.assertEqual((0, 0, 0), self.counts())

    def test_stale_revision_and_session_mismatch_reject_before_any_route_effect(self):
        status, mismatch = self.bind(session_uuid=OTHER_SESSION)
        self.assertEqual(409, status)
        self.assertEqual("ROUTE_MISMATCH", mismatch["disposition"])
        self.assertEqual((0, 0, 0), self.counts())

        self.assertEqual(200, self.bind()[0])
        before = self.counts()
        status, stale = self.bind(key="stale", expected=0, dispatcher_key_id="replacement")
        self.assertEqual(409, status)
        self.assertEqual({"disposition": "STALE_ROUTE", "route_revision": 1}, stale)
        self.assertEqual(before, self.counts())
        self.assertEqual(ALPHA_SESSION, self.db.execute("SELECT session_uuid FROM relay_routes").fetchone()[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE relay_routes SET route_revision=route_revision WHERE agent_id='eddie-brock'")

    def test_session_cannot_be_shared_between_agents(self):
        self.assertEqual(200, self.bind()[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO relay_routes(agent_id,session_uuid,transport,relay_capability,capability_version,dispatcher_key_id,dispatcher_public_key,state,route_revision,last_verified_utc,updated_utc) VALUES('nimrod',?,'revere.v1','coordinator-contact','1','k',?,'ACTIVE',1,?,?)",
                (ALPHA_SESSION, self.public_key, NOW, NOW),
            )

    def test_disable_increments_revision_and_has_no_session_or_authority_side_effect(self):
        self.assertEqual(200, self.bind()[0])
        session_before = tuple(self.db.execute("SELECT status,revision,updated_utc FROM sessions WHERE session_uuid=?", (ALPHA_SESSION,)).fetchone())
        agent_before = tuple(self.db.execute("SELECT active,revision,updated_utc FROM agents WHERE agent_id='eddie-brock'").fetchone())
        journal_before = self.db.execute("SELECT count(*) FROM journal").fetchone()[0]
        status, disabled = self.app.mutate_relay_route(
            self.db, "operator", "disable-1", "eddie-brock", {"expected_route_revision": 1}, "disable"
        )
        self.assertEqual(200, status)
        self.assertEqual("DISABLED", disabled["route_state"])
        self.assertEqual(2, disabled["route_revision"])
        self.assertEqual((409, {"disposition": "ROUTE_INELIGIBLE"}), self.app.resolve_relay_route(self.db, "eddie-brock"))
        self.assertEqual(session_before, tuple(self.db.execute("SELECT status,revision,updated_utc FROM sessions WHERE session_uuid=?", (ALPHA_SESSION,)).fetchone()))
        self.assertEqual(agent_before, tuple(self.db.execute("SELECT active,revision,updated_utc FROM agents WHERE agent_id='eddie-brock'").fetchone()))
        self.assertEqual(journal_before, self.db.execute("SELECT count(*) FROM journal").fetchone()[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("DELETE FROM relay_route_journal")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE relay_route_journal SET action='bind'")

    def test_ineligible_session_and_invalid_requests_fail_closed(self):
        for extra in (
            {"dispatcher_public_key": "not-an-ed25519-public-key"},
            {"dispatcher_public_key": base64.b64encode(b"short").decode()},
            {"session_uuid": "not-a-uuid"},
            {"expected_route_revision": True},
            {"expected_route_revision": -1},
            {"unexpected": "field"},
        ):
            with self.subTest(extra=extra):
                status, invalid = self.bind(**extra)
                self.assertEqual((400, {"detail": "invalid relay route request"}), (status, invalid))
        self.assertEqual(400, self.app.mutate_relay_route(self.db, "operator", "k", "Eddie", {"expected_route_revision": 1}, "disable")[0])
        self.db.execute("UPDATE sessions SET status='ENDED',ended_utc=updated_utc WHERE session_uuid=?", (ALPHA_SESSION,))
        self.db.commit()
        status, ineligible = self.bind()
        self.assertEqual(409, status)
        self.assertEqual("ROUTE_INELIGIBLE", ineligible["disposition"])
        self.assertEqual((0, 0, 0), self.counts())

    def test_resolution_fails_closed_when_session_ends_or_agent_retires_after_bind(self):
        self.assertEqual(200, self.bind()[0])
        self.db.execute("UPDATE sessions SET status='LOST',ended_utc=updated_utc WHERE session_uuid=?", (ALPHA_SESSION,))
        self.assertEqual((409, {"disposition": "ROUTE_INELIGIBLE"}), self.app.resolve_relay_route(self.db, "eddie-brock"))
        self.db.execute("UPDATE sessions SET status='ACTIVE',ended_utc=NULL WHERE session_uuid=?", (ALPHA_SESSION,))
        self.assertEqual(200, self.app.resolve_relay_route(self.db, "eddie-brock")[0])
        self.db.execute("UPDATE agents SET active=0 WHERE agent_id='eddie-brock'")
        self.assertEqual((409, {"disposition": "ROUTE_INELIGIBLE"}), self.app.resolve_relay_route(self.db, "eddie-brock"))

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

    def test_migration_from_head_ten_reaches_head_eleven_and_matches_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry-head-ten.db"
            old = os.environ.get("REGISTRY_DB")
            os.environ["REGISTRY_DB"] = str(path)
            db = sqlite3.connect(path, isolation_level=None)
            try:
                import registry.migrate as migrate
                migrate = importlib.reload(migrate)
                for statement in migrate._statements(migrate.SCHEMA):
                    db.execute(statement)
                    if statement.lstrip().upper().startswith("INSERT INTO REGISTRY_MIGRATIONS VALUES(10,"):
                        break
                db.execute(f"PRAGMA application_id={migrate.APPLICATION_ID}")
                db.execute("PRAGMA user_version=10")
                self.assertEqual(set(), {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE name LIKE 'relay_route%'")})
                self.assertEqual(11, migrate.migrate(db))
                self.assertEqual(list(range(1, 12)), [row[0] for row in db.execute("SELECT version FROM registry_migrations ORDER BY version")])
                self.assertEqual({"relay_routes", "relay_route_journal"}, {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'relay_route%'")})
                self.assertEqual(11, db.execute("PRAGMA user_version").fetchone()[0])
                self.assertEqual(11, migrate.migrate(db))
            finally:
                db.close()
                if old is None:
                    os.environ.pop("REGISTRY_DB", None)
                else:
                    os.environ["REGISTRY_DB"] = old


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
        db.execute("INSERT INTO agents VALUES(?,?,?,?,?)", ("eddie-brock", "{}", 1, 1, NOW))
        add_session(db, ALPHA_SESSION, "eddie-brock", "alpha-host")
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

    def request(self, method, path, *, body=None, operator=True, bearer=True, key="route-http-1"):
        headers = {}
        if bearer:
            headers["Authorization"] = "Bearer " + self.api_token
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
            "session_uuid": ALPHA_SESSION,
            "capability_version": "1",
            "dispatcher_key_id": "alpha-dispatcher-1",
            "dispatcher_public_key": base64.b64encode(os.urandom(32)).decode(),
            "expected_route_revision": 0,
        }
        status, headers, _ = self.request("POST", "/v1/relay-routes/eddie-brock", body=body, operator=False)
        self.assertEqual(404, status)
        self.assertEqual("no-store", headers.get("cache-control"))
        status, _, _ = self.request("POST", "/v1/relay-routes/eddie-brock", body=body, bearer=False)
        self.assertEqual(401, status)
        status, headers, bound = self.request("POST", "/v1/relay-routes/eddie-brock", body=body)
        self.assertEqual(200, status)
        self.assertEqual("no-store", headers.get("cache-control"))
        status, _, resolved = self.request("GET", "/v1/relay-routes/eddie-brock", operator=False)
        self.assertEqual(200, status)
        self.assertEqual(bound, resolved)
        self.assertNotIn("provider_session_id", resolved)
        self.assertNotIn("authority_granted", resolved)
        status, _, _ = self.request("GET", "/v1/relay-routes/eddie-brock", bearer=False)
        self.assertEqual(401, status)
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
