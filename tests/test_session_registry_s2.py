"""Focused acceptance checks for SESSION-REGISTRY-PROTECTED-LOOKUP (S2)."""
from __future__ import annotations

import contextlib
import http.client
import io
import json
import os
import secrets
import sqlite3
import subprocess
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

from tests.test_session_registry_s1 import load_app


ROOT = Path(__file__).resolve().parents[1]


class SessionRegistryS2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = load_app()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "registry.db"
        self.api_token_path = Path(self.tmp.name) / "registry-token"
        self.api_token = secrets.token_urlsafe(32)
        self.operator_token = secrets.token_urlsafe(32)
        self.locator = secrets.token_urlsafe(48)
        self.api_token_path.write_text(self.api_token, encoding="utf-8")
        db = sqlite3.connect(self.db_path)
        db.executescript((ROOT / "registry" / "schema.sql").read_text(encoding="utf-8"))
        db.execute(
            "INSERT INTO agents VALUES(?,?,?,?,?)",
            ("operator-shaped-agent", '{"role":"operator"}', 1, 1, "2026-01-01T00:00:00Z"),
        )
        db.commit()
        db.close()
        self.app.DB = self.db_path
        self.app.TOKEN_FILE = str(self.api_token_path)
        self.old_operator_token = os.environ.get("REGISTRY_OPERATOR_TOKEN")
        os.environ["REGISTRY_OPERATOR_TOKEN"] = self.operator_token
        db = self.app.connect()
        try:
            status, self.registered = self.app.mutate_session(
                db,
                "test-principal",
                "register-sentinel",
                {
                    "agent_id": "operator-shaped-agent",
                    "provider": "vendor",
                    "provider_session_id": self.locator,
                    "initial_status": "ACTIVE",
                    "seat_or_host": "seat-a",
                    "runtime": "runtime-a",
                    "model": "model-a",
                    "work_ref": "operator-approved-looking-work",
                },
                "register",
            )
            self.assertEqual(201, status)
            status, _ = self.app.mutate_session(
                db,
                "test-principal",
                "heartbeat-sentinel",
                {"session_uuid": self.registered["session_uuid"], "status": "IDLE"},
                "heartbeat",
            )
            self.assertEqual(200, status)
        finally:
            db.close()
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

    def request(self, path, *, headers=None, body=None):
        request_headers = {"Authorization": "Bearer " + self.api_token}
        request_headers.update(headers or {})
        encoded = None if body is None else json.dumps(body).encode()
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request("GET", path, body=encoded, headers=request_headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, {name.lower(): value for name, value in response.getheaders()}, raw, json.loads(raw)
        finally:
            connection.close()

    def assert_secret_absent(self, secret, surfaces):
        encoded = secret.encode()
        for surface in surfaces:
            value = surface if isinstance(surface, bytes) else str(surface).encode()
            self.assertFalse(encoded in value, "generated sensitive value escaped a prohibited surface")

    def test_authenticated_current_and_ordered_history_are_redacted_facts_only(self):
        session_uuid = self.registered["session_uuid"]
        status, _, current_raw, current = self.request(f"/v1/sessions/{session_uuid}")
        self.assertEqual(200, status)
        self.assertEqual(
            {
                "session_uuid", "agent_id", "provider", "seat_or_host", "runtime", "model", "status",
                "started_utc", "last_seen_utc", "ended_utc", "work_ref", "revision", "updated_utc",
            },
            set(current),
        )
        self.assertEqual("IDLE", current["status"])
        status, _, history_raw, history = self.request(f"/v1/sessions/{session_uuid}/history")
        self.assertEqual(200, status)
        self.assertEqual(["register", "heartbeat"], [event["action"] for event in history["events"]])
        self.assertEqual(sorted(event["seq"] for event in history["events"]), [event["seq"] for event in history["events"]])
        for event in history["events"]:
            self.assertEqual(
                {"seq", "event_id", "session_uuid", "agent_id", "action", "body", "committed_utc"},
                set(event),
            )
        self.assert_secret_absent(self.locator, (current_raw, history_raw))
        claims = ("identity_verified", "authorized", "reachable", "contacted")
        for claim in claims:
            self.assertNotIn(claim, current)
            self.assertTrue(all(claim not in event["body"] for event in history["events"]))

    def test_locator_requires_current_token_and_all_self_assertions_are_not_found(self):
        session_uuid = self.registered["session_uuid"]
        path = f"/v1/sessions/{session_uuid}/provider-locator"
        good = {"X-Registry-Operator-Token": self.operator_token}
        status, headers, raw, value = self.request(path, headers=good)
        self.assertEqual(200, status)
        self.assertEqual("no-store", headers.get("cache-control"))
        self.assertTrue(secrets.compare_digest(self.locator, value.get("provider_session_id", "")), "protected locator mismatch")
        self.assert_secret_absent(self.operator_token, (raw,))

        unknown = str(uuid.uuid4())
        unknown_status, unknown_headers, unknown_raw, _ = self.request(
            f"/v1/sessions/{unknown}/provider-locator", headers=good
        )
        self.assertEqual(404, unknown_status)
        self.assertEqual("no-store", unknown_headers.get("cache-control"))

        original_connect = self.app.connect
        try:
            def forbidden_lookup():
                raise RuntimeError("operator validation must precede locator retrieval")

            self.app.connect = forbidden_lookup
            status, response_headers, response_raw, _ = self.request(path)
            self.assertEqual(404, status)
            self.assertEqual(unknown_raw, response_raw)
            self.assertEqual("no-store", response_headers.get("cache-control"))
        finally:
            self.app.connect = original_connect

        negative_requests = (
            ({"X-Registry-Operator-Token": secrets.token_urlsafe(32)}, None, path),
            ({"X-Registry-Role": "operator"}, None, path),
            ({"X-Forwarded-User": "operator", "X-Forwarded-Role": "operator"}, None, path),
            ({"X-Registry-Agent": "operator-shaped-agent"}, None, path),
            ({"X-Work-Ref": "operator-approved-looking-work"}, None, path),
            ({}, {"operator": True, "operator_token": self.operator_token}, path),
            ({}, None, path + "?operator=true&operator_token=" + self.operator_token),
        )
        for headers_in, body, request_path in negative_requests:
            status, response_headers, response_raw, _ = self.request(request_path, headers=headers_in, body=body)
            self.assertEqual(404, status)
            self.assertEqual(unknown_raw, response_raw)
            self.assertEqual("no-store", response_headers.get("cache-control"))
            self.assert_secret_absent(self.locator, (response_raw,))

        rotated = secrets.token_urlsafe(32)
        os.environ["REGISTRY_OPERATOR_TOKEN"] = rotated
        status, _, rotated_raw, _ = self.request(path, headers=good)
        self.assertEqual(404, status)
        self.assertEqual(unknown_raw, rotated_raw)
        status, _, _, _ = self.request(path, headers={"X-Registry-Operator-Token": rotated})
        self.assertEqual(200, status)
        os.environ.pop("REGISTRY_OPERATOR_TOKEN")
        status, revoked_headers, revoked_raw, _ = self.request(path, headers={"X-Registry-Operator-Token": rotated})
        self.assertEqual(404, status)
        self.assertEqual(unknown_raw, revoked_raw)
        self.assertEqual("no-store", revoked_headers.get("cache-control"))

    def test_generated_secrets_do_not_escape_errors_logs_audit_idempotency_or_git(self):
        session_uuid = self.registered["session_uuid"]
        captured_stderr = io.StringIO()
        original_connect = self.app.connect
        try:
            def fail_connect():
                raise RuntimeError(self.locator)

            self.app.connect = fail_connect
            with contextlib.redirect_stderr(captured_stderr):
                status, headers, error_raw, _ = self.request(
                    f"/v1/sessions/{session_uuid}/provider-locator",
                    headers={"X-Registry-Operator-Token": self.operator_token},
                )
            self.assertEqual(503, status)
            self.assertEqual("no-store", headers.get("cache-control"))
        finally:
            self.app.connect = original_connect

        db = self.app.connect()
        try:
            prohibited_db_surfaces = []
            for table in ("requests", "journal", "audit_outbox"):
                prohibited_db_surfaces.extend(repr(tuple(row)) for row in db.execute(f"SELECT * FROM {table}"))
        finally:
            db.close()
        status, _, current_raw, _ = self.request(f"/v1/sessions/{session_uuid}")
        self.assertEqual(200, status)
        status, _, history_raw, _ = self.request(f"/v1/sessions/{session_uuid}/history")
        self.assertEqual(200, status)
        surfaces = [error_raw, captured_stderr.getvalue(), current_raw, history_raw, *prohibited_db_surfaces]
        self.assert_secret_absent(self.locator, surfaces)
        self.assert_secret_absent(self.operator_token, surfaces)

        tracked = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout.split(b"\0")
        for relative in tracked:
            if not relative:
                continue
            content = (ROOT / os.fsdecode(relative)).read_bytes()
            self.assertFalse(self.locator.encode() in content, "generated locator entered a Git-tracked artifact")
            self.assertFalse(self.operator_token.encode() in content, "generated credential entered a Git-tracked artifact")


def _successor(case, name):
    """Preserve inherited labels while evaluating the corrected ownership boundary."""
    def test(self):
        case.setUpClass()
        result = unittest.TestResult()
        case(name).run(result)
        self.assertEqual([], result.errors)
        self.assertEqual([], result.failures)
        self.assertEqual([], result.skipped)
    return test


from tests import test_session_registry_ed25519 as successor
SessionRegistryS2Tests.test_authenticated_current_and_ordered_history_are_redacted_facts_only = _successor(successor.OwnershipRouteTests, "test_lookup_current_and_signature_only_owned_routes")
SessionRegistryS2Tests.test_locator_requires_current_token_and_all_self_assertions_are_not_found = _successor(successor.OwnershipRouteTests, "test_legacy_lookup_and_operator_route_negatives_are_zero_write_and_redacted")
SessionRegistryS2Tests.test_generated_secrets_do_not_escape_errors_logs_audit_idempotency_or_git = _successor(successor.OwnershipRouteTests, "test_legacy_lookup_and_operator_route_negatives_are_zero_write_and_redacted")


if __name__ == "__main__":
    unittest.main()
