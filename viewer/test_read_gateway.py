from __future__ import annotations

import asyncio
import json
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from viewer import read_gateway as gateway


class FakeResponse(BytesIO):
    def __init__(self, payload=b"{}", status=200):
        super().__init__(payload)
        self.status = status

    def getcode(self):
        return self.status


class FakeOpener:
    def __init__(self, routes=None):
        self.routes = routes or {}
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        result = self.routes.get(request.full_url)
        if isinstance(result, Exception):
            raise result
        if result is None:
            raise AssertionError("unexpected upstream URL: " + request.full_url)
        if callable(result):
            result = result()
        return result


def response(payload, status=200):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    return FakeResponse(body, status)


async def asgi_request(path, *, method="GET", query=b"", raw_path=None, headers=None):
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "raw_path": raw_path if raw_path is not None else path.encode("ascii"),
        "query_string": query,
        "headers": headers or [],
    }
    await gateway.app(scope, receive, send)
    start, body = sent
    return start["status"], dict(start["headers"]), json.loads(body["body"])


def call(path, **kwargs):
    return asyncio.run(asgi_request(path, **kwargs))


class ReadGatewayTests(unittest.TestCase):
    def setUp(self):
        self.token = patch.object(gateway, "_token", return_value="mounted-secret")
        self.token.start()
        self.addCleanup(self.token.stop)

    def install(self, routes):
        opener = FakeOpener(routes)
        replacement = patch.object(gateway, "_OPENER", opener)
        replacement.start()
        self.addCleanup(replacement.stop)
        return opener

    def test_only_four_get_routes_and_no_client_authorization(self):
        opener = self.install({})
        status, headers, body = call("/health/live")
        self.assertEqual((200, {"ok": True}), (status, body))
        self.assertEqual(b"no-store", headers[b"cache-control"])
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            with self.subTest(method=method):
                self.assertEqual(405, call("/health/live", method=method)[0])
        for path in ("/docs", "/redoc", "/openapi.json", "/v1/native/notices", "/v1/native/threads"):
            with self.subTest(path=path):
                self.assertEqual(404, call(path)[0])
        self.assertEqual(400, call("/health/live", query=b"x=1")[0])
        self.assertEqual(400, call("/health/live", headers=[(b"authorization", b"Bearer client")])[0])
        self.assertEqual([], opener.calls)

    def test_ready_uses_fixed_origin_get_internal_token_and_no_redirect_handler(self):
        opener = self.install({gateway.LEDGER_ORIGIN + gateway.STATUS_PATH: response({"ok": True})})
        self.assertEqual(200, call("/health/ready")[0])
        request, timeout = opener.calls[0]
        self.assertEqual("GET", request.get_method())
        self.assertEqual(gateway.LEDGER_ORIGIN + gateway.STATUS_PATH, request.full_url)
        self.assertEqual("Bearer mounted-secret", request.get_header("Authorization"))
        self.assertEqual(gateway.TIMEOUT_SECONDS, timeout)
        self.assertIsNone(gateway._NoRedirect().redirect_request(None, None, 302, "", {}, "http://attacker"))

    def test_discovery_exact_reads_every_candidate_and_scrubs_blocked_references(self):
        discovery = {
            "history": [
                {"thread_id": "public", "sensitivity": "INTERNAL"},
                {"thread_id": "secret", "sensitivity": "INTERNAL"},
            ],
            "open_work": [{"thread_id": "public"}, {"thread_id": "secret"}],
            "boards": {"ops": ["public", "secret", "public"]},
            "projects": {"alpha": [{"parent": "secret", "level": 1}, {"parent": "public", "level": 2}]},
            "registry": {"status": "EXTERNAL"},
            "findings": [],
        }
        secret_url = gateway.LEDGER_ORIGIN + gateway.THREAD_PREFIX + "secret?include_archived=true"
        opener = self.install({
            gateway.LEDGER_ORIGIN + gateway.DISCOVERY_PATH: response(discovery),
            gateway.LEDGER_ORIGIN + gateway.THREAD_PREFIX + "public?include_archived=true": response({
                "thread_id": "public", "events": [{"thread_id": "public", "sensitivity": "INTERNAL"}]
            }),
            secret_url: HTTPError(secret_url, 403, "forbidden", {}, None),
        })
        status, _, body = call(gateway.DISCOVERY_PATH)
        self.assertEqual(200, status)
        self.assertEqual(["public"], [row["thread_id"] for row in body["history"]])
        self.assertEqual(["public"], [row["thread_id"] for row in body["open_work"]])
        self.assertEqual(["public", "public"], body["boards"]["ops"])
        self.assertNotIn("parent", body["projects"]["alpha"][0])
        rendered = json.dumps(body, sort_keys=True)
        self.assertNotIn("secret", rendered)
        self.assertEqual(3, len(opener.calls))

    def test_exact_thread_hides_forbidden_and_restricted_as_the_same_404(self):
        restricted_url = gateway.LEDGER_ORIGIN + gateway.THREAD_PREFIX + "restricted?include_archived=true"
        forbidden_url = gateway.LEDGER_ORIGIN + gateway.THREAD_PREFIX + "forbidden?include_archived=true"
        opener = self.install({
            gateway.LEDGER_ORIGIN + gateway.THREAD_PREFIX + "public?include_archived=true": response({
                "thread_id": "public", "events": [{"sensitivity": "INTERNAL", "content": "ok"}]
            }),
            restricted_url: response({"thread_id": "restricted", "events": [{"sensitivity": "RESTRICTED", "content": "never"}]}),
            forbidden_url: HTTPError(forbidden_url, 403, "forbidden", {}, None),
        })
        self.assertEqual(200, call(gateway.THREAD_PREFIX + "public")[0])
        restricted = call(gateway.THREAD_PREFIX + "restricted")
        forbidden = call(gateway.THREAD_PREFIX + "forbidden")
        self.assertEqual(404, restricted[0])
        self.assertEqual(restricted[2], forbidden[2])
        self.assertNotIn("never", json.dumps(restricted[2]))
        self.assertEqual(3, len(opener.calls))

    def test_invalid_thread_identifiers_are_rejected_before_upstream(self):
        opener = self.install({})
        cases = (
            (gateway.THREAD_PREFIX + "../secret", None, b""),
            (gateway.THREAD_PREFIX + "bad!id", None, b""),
            (gateway.THREAD_PREFIX + "a" * 201, None, b""),
            (gateway.THREAD_PREFIX + "bad/child", None, b""),
            (gateway.THREAD_PREFIX + "bad/child", (gateway.THREAD_PREFIX + "bad%2Fchild").encode(), b""),
            (gateway.THREAD_PREFIX + "public", None, b"fragment=not-allowed"),
        )
        for path, raw_path, query in cases:
            with self.subTest(path=path, raw_path=raw_path):
                self.assertIn(call(path, raw_path=raw_path, query=query)[0], {400, 404})
        self.assertEqual([], opener.calls)

    def test_upstream_failures_are_bounded_and_sanitized(self):
        secret = "upstream-secret-body"
        cases = {
            "auth": HTTPError("x", 401, secret, {}, None),
            "server": HTTPError("x", 500, secret, {}, None),
            "redirect": HTTPError("x", 302, secret, {}, None),
            "network": URLError(secret),
            "malformed": response(b"not-json"),
            "oversize": response(b"{" + b"x" * gateway.MAX_RESPONSE_BYTES),
        }
        for name, result in cases.items():
            with self.subTest(name=name):
                opener = FakeOpener({gateway.LEDGER_ORIGIN + gateway.STATUS_PATH: result})
                with patch.object(gateway, "_OPENER", opener):
                    status, _, body = call("/health/ready")
                self.assertEqual(503, status)
                rendered = json.dumps(body)
                self.assertNotIn(secret, rendered)
                self.assertNotIn("mounted-secret", rendered)


if __name__ == "__main__":
    unittest.main()
