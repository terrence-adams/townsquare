from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from registrar.app.auth import create_native_credential, revoke_native_credential
from registrar.app.db import connect
from registrar.tests.app_harness import FreshAppCase


FIXTURE = Path(__file__).resolve().parents[2] / "tests/conformance/fixtures/viewer-peer-readiness-prefixed-401.json"


class CanaryStatusTests(FreshAppCase):
    def setUp(self):
        inbound = self._key_file(b"registry-to-ledger-readiness-token")
        outbound = self._key_file(b"ledger-to-registry-readiness-token")
        os.environ["REGISTRY_PEER_READINESS_TOKEN_FILE"] = inbound
        os.environ["REGISTRY_READINESS_TOKEN_FILE"] = outbound
        self.main = self._boot()
        self.client = TestClient(self.main.app)

    def credential(self, principal="viewer", policy="townsquare-mvp-v1", ttl=3600):
        db = connect(os.environ["REGISTRAR_DB"])
        try:
            value = create_native_credential(db, principal, policy_version=policy, ttl_seconds=ttl)
        finally:
            db.close()
        return value

    def test_captured_prefixed_failure_and_corrected_viewer_status(self):
        viewer = self.credential()
        old = self.client.get("/health/ready", headers={"Authorization": "Bearer " + viewer})
        self.assertEqual(401, old.status_code)
        captured = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(old.status_code, captured["actual"]["status"])
        self.assertEqual(old.json(), captured["actual"]["body"])

        corrected = self.client.get("/v1/native/status/ready", headers={"Authorization": "Bearer " + viewer})
        self.assertEqual(200, corrected.status_code, corrected.text)
        payload = corrected.json()
        for name, expected in self.main.CANARY_IDENTITY.as_dict().items():
            self.assertEqual(expected, payload[name])
        self.assertEqual("townsquare-ledger-v0", payload["service_id"])

    def test_missing_revoked_expired_wrong_principal_and_wrong_capability_fail(self):
        self.assertEqual(401, self.client.get("/v1/native/status/ready").status_code)

        revoked = self.credential()
        db = connect(os.environ["REGISTRAR_DB"])
        try: revoke_native_credential(db, revoked.split(".", 1)[0], "test", "test-harness")
        finally: db.close()
        self.assertEqual(403, self.client.get("/v1/native/status/ready", headers={"Authorization": "Bearer " + revoked}).status_code)

        expired = self.credential()
        db = connect(os.environ["REGISTRAR_DB"])
        try: db.execute("UPDATE auth_credentials SET expires_at='2000-01-01T00:00:00Z' WHERE credential_id=?", (expired.split('.', 1)[0],))
        finally: db.close()
        self.assertEqual(403, self.client.get("/v1/native/status/ready", headers={"Authorization": "Bearer " + expired}).status_code)

        for principal in ("crier", "registry-audit"):
            credential = self.credential(principal)
            self.assertEqual(403, self.client.get("/v1/native/status/ready", headers={"Authorization": "Bearer " + credential}).status_code)

    def test_viewer_token_never_authenticates_peer_route_and_tokens_are_directional(self):
        viewer = self.credential()
        self.assertEqual(401, self.client.get("/health/ready", headers={"Authorization": "Bearer " + viewer}).status_code)
        inbound = Path(os.environ["REGISTRY_PEER_READINESS_TOKEN_FILE"]).read_text(encoding="utf-8")
        outbound = Path(os.environ["REGISTRY_READINESS_TOKEN_FILE"]).read_text(encoding="utf-8")
        self.assertNotEqual(inbound, outbound)
        self.assertEqual(200, self.client.get("/health/ready", headers={"Authorization": "Bearer " + inbound}).status_code)
        self.assertEqual(401, self.client.get("/health/ready", headers={"Authorization": "Bearer " + outbound}).status_code)


if __name__ == "__main__":
    import unittest
    unittest.main()
