#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""Focused tests for the read-only host reader. The gateway is never contacted."""
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path

from hostreader.host_reader import (
    DISCOVERY_PATH, LocalStateError, ReaderError, evidence_record, load_state, parse_rows, poll, thread_url,
)

BASE = "http://gw.test:1"
IDS = ("cable", "sentinel-one")


def row(thread, event, to, seq=1):
    return {"thread_id": thread, "event_id": event, "addressee": to, "state": "OPEN", "kind": "REQUEST",
            "ledger_seq": seq}


class Gateway:
    """Fake opener: routes by path, records every request."""

    def __init__(self, discovery, threads=None, fail=None):
        self.discovery, self.threads, self.fail = discovery, threads or {}, fail
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append(request)
        url = request.full_url
        if self.fail:
            raise self.fail
        if url.endswith(DISCOVERY_PATH):
            body = self.discovery
        else:
            body = self.threads.get(url.rsplit("/", 1)[1])
            if body is None:
                raise urllib.error.HTTPError(url, 404, "nf", {}, io.BytesIO(b"{}"))
        return Response(body)


class Response:
    status = 200

    def __init__(self, body):
        self.raw = body if isinstance(body, bytes) else json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.raw


class HostReaderTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.state, self.inbox = Path(tmp.name) / "state.json", Path(tmp.name) / "INBOX.txt"

    def run_poll(self, gateway):
        return poll(BASE, IDS, self.state, self.inbox, opener=gateway)

    def test_filters_to_configured_identities_and_reads_exact_thread(self):
        gw = Gateway({"open_work": [row("T-1", "e1", "Cable"), row("T-2", "e2", "wolverine")]},
                     {"T-1": {"thread_id": "T-1", "events": [{}, {}]}})
        result = self.run_poll(gw)
        self.assertEqual([r["event_id"] for r in result["matched"]], ["e1"])
        self.assertEqual([r.full_url for r in gw.requests], [BASE + DISCOVERY_PATH, BASE + "/v1/native/threads/T-1"])
        self.assertIn("T-1", self.inbox.read_text())
        self.assertNotIn("T-2", self.inbox.read_text())

    def test_only_get_requests_and_no_auth(self):
        gw = Gateway({"open_work": [row("T-1", "e1", "cable")]}, {"T-1": {"events": []}})
        self.run_poll(gw)
        for request in gw.requests:
            self.assertEqual(request.get_method(), "GET")
            self.assertIsNone(request.data)
            self.assertFalse(request.has_header("Authorization"))

    def test_dedup_across_runs_and_overlapping_sources(self):
        discovery = {"open_work": [row("T-1", "e1", "cable")], "history": [row("T-1", "e1", "cable")]}
        gw = Gateway(discovery, {"T-1": {"events": []}})
        self.assertEqual(self.run_poll(gw)["added"], ["e1"])
        self.assertEqual(self.run_poll(gw)["added"], [])
        self.assertEqual(len(load_state(self.state)["items"]), 1)
        self.assertEqual(sum("T-1" in r.full_url and "threads" in r.full_url for r in gw.requests), 1)

    def test_unreachable_is_unknown_and_keeps_last_good_items(self):
        self.run_poll(Gateway({"open_work": [row("T-1", "e1", "cable")]}, {"T-1": {"events": []}}))
        result = self.run_poll(Gateway({}, fail=urllib.error.URLError("down")))
        self.assertFalse(result["ok"])
        self.assertIn("UNKNOWN", self.inbox.read_text())
        self.assertIn("T-1", self.inbox.read_text())
        self.assertEqual(len(load_state(self.state)["items"]), 1)

    def test_malformed_responses_fail_the_poll(self):
        for body in (b"not json", b"[]", {"unrelated": 1}, {"open_work": "x"}):
            result = self.run_poll(Gateway(body))
            self.assertFalse(result["ok"], body)
            self.assertIn("UNKNOWN", self.inbox.read_text())

    def test_http_error_status_fails_the_poll(self):
        err = urllib.error.HTTPError(BASE, 503, "down", {}, io.BytesIO(b"{}"))
        result = self.run_poll(Gateway({}, fail=err))
        self.assertFalse(result["ok"])
        self.assertEqual(result["requests"][0]["http_status"], 503)

    def test_incomplete_rows_are_dropped_and_counted(self):
        rows, skipped = parse_rows({"open_work": [row("T-1", "e1", "cable"), {"thread_id": "T-2"}, "junk",
                                                  row("../x", "e3", "cable")]})
        self.assertEqual(list(rows), ["e1"])
        self.assertEqual(skipped, 3)

    def test_thread_404_is_terminal(self):
        gw = Gateway({"open_work": [row("T-1", "e1", "cable")]})
        self.run_poll(gw)
        self.assertEqual(load_state(self.state)["items"][0]["detail"], "not_found")

    def test_transient_thread_failure_retries_without_second_entry(self):
        discovery = {"open_work": [row("T-1", "e1", "cable")]}
        result = self.run_poll(Gateway(discovery, {"T-1": b"not json"}))
        self.assertFalse(result["ok"])
        self.assertIn("UNKNOWN", self.inbox.read_text())
        self.assertIsNone(load_state(self.state)["items"][0]["detail"])
        result = self.run_poll(Gateway(discovery, {"T-1": {"events": [{}]}}))
        self.assertTrue(result["ok"])
        self.assertEqual(result["added"], [])
        items = load_state(self.state)["items"]
        self.assertEqual((len(items), items[0]["detail"]), (1, "ok (1 events)"))

    def test_bad_thread_id_never_becomes_a_url(self):
        with self.assertRaises(ReaderError):
            thread_url(BASE, "../etc/passwd")

    def test_corrupt_state_is_an_error_not_a_reset(self):
        self.state.write_text("{broken")
        with self.assertRaises(LocalStateError):
            self.run_poll(Gateway({"open_work": []}))
        self.assertEqual(self.state.read_text(), "{broken")

    def test_state_and_inbox_written_atomically_with_private_mode(self):
        self.run_poll(Gateway({"open_work": []}))
        if os.name == "posix":
            self.assertEqual(oct(self.state.stat().st_mode & 0o777), "0o600")
        self.assertFalse(list(self.state.parent.glob("*.tmp")))

    def test_evidence_is_sanitized_and_get_only(self):
        gw = Gateway({"open_work": [row("T-1", "e1", "cable")]}, {"T-1": {"events": [{"content": "SECRET"}]}})
        record = evidence_record(self.run_poll(gw), BASE, IDS, "abc")
        text = json.dumps(record)
        self.assertNotIn("SECRET", text)
        self.assertNotIn(str(self.state), text)
        self.assertEqual(record["story_ref"], "VR-20261008-townsquare-181")
        self.assertEqual(record["mutating_requests"], 0)
        self.assertEqual({r["method"] for r in record["requests"]}, {"GET"})


if __name__ == "__main__":
    unittest.main()
