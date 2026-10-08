#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
"""
Focused tests for the read-only canary host reader (VR-20261008-townsquare-181).

The gateway is never contacted: every test drives the client through a fake
opener, so the suite is hermetic and the live check stays a separate, explicit
act. Fixtures are shaped from the real sanitized discovery payload observed on
http://192.168.2.3:18503 (addressees deliberately include hosts that are NOT
this one, because "visible work is not my work" is the property under test).
"""
from __future__ import annotations

import io
import json
import os
import socket
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from hostreader.host_reader import (
    DISCOVERY_PATH,
    STATE_SCHEMA,
    THREAD_PREFIX,
    Config,
    LocalStateError,
    ReaderError,
    atomic_write,
    empty_state,
    evidence_record,
    filter_for_identities,
    load_state,
    normalize_identities,
    parse_discovery,
    poll_once,
    persist,
    render_inbox,
    summarize_thread,
    thread_url,
)


def row(thread_id, event_id, addressee, *, seq=1, state="OPEN", kind="REQUEST", owner="venom", **extra):
    record = {
        "thread_id": thread_id,
        "event_id": event_id,
        "addressee": addressee,
        "state": state,
        "kind": kind,
        "owner": owner,
        "ledger_seq": seq,
        "thread_ordinal": 0,
        "sensitivity": "INTERNAL",
        "committed_at": "2026-10-08T00:11:24Z",
    }
    record.update(extra)
    return record


CABLE_ROW = row("POC-CABLE-READER-20261008-A", "11111111-1111-4111-8111-111111111111", "cable", seq=7)
WOLVERINE_ROW = row("POC-WOLVERINE-CANARY-ONBOARD-20261007-A", "5302f7e3-aab0-441b-aeda-76bed7ae5a22", "wolverine", seq=4)
BISHOP_ROW = row("POC-BISHOP-CANARY-ONBOARD-20261007-A", "03438c87-8ca6-411f-bb97-e12c19c9c36d", "bishop", seq=5)


def discovery_payload(rows=None, *, history=None, boards=None):
    rows = [CABLE_ROW, WOLVERINE_ROW, BISHOP_ROW] if rows is None else rows
    thread_ids = [r["thread_id"] for r in rows if isinstance(r, dict)]
    return {
        # The real gateway repeats thread ids across boards; mirror that.
        "boards": {"REQUEST": boards if boards is not None else thread_ids + thread_ids[:1]},
        "findings": [],
        "history": rows if history is None else history,
        "open_work": rows,
        "projects": {},
        "registry": {"agents": None, "findings": [], "status": "EXTERNAL"},
    }


def thread_payload(thread_id, *, events=1, content="OPERATOR-MANDATED CANARY ONBOARDING.   Multi   space."):
    return {
        "archived": False,
        "thread_id": thread_id,
        "events": [
            {
                "event_id": f"{thread_id}-event-{index}",
                "state": "OPEN",
                "sensitivity": "INTERNAL",
                "content": content,
                "thread_id": thread_id,
            }
            for index in range(events)
        ],
    }


class _FakeResponse(io.BytesIO):
    def __init__(self, payload, status=200):
        super().__init__(payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8"))
        self.status = status

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class FakeGateway:
    """Records every request and replays scripted responses."""

    def __init__(self, *, discovery=None, threads=None, thread_errors=None, discovery_error=None):
        self.discovery = discovery if discovery is not None else discovery_payload()
        self.threads = threads or {}
        self.thread_errors = thread_errors or {}
        self.discovery_error = discovery_error
        self.calls: list[tuple[str, str]] = []

    def __call__(self, request, timeout=None):
        self.calls.append((request.get_method(), request.full_url))
        if DISCOVERY_PATH in request.full_url:
            if self.discovery_error is not None:
                raise self.discovery_error
            return _FakeResponse(self.discovery)
        thread_id = request.full_url.split(THREAD_PREFIX, 1)[1]
        if thread_id in self.thread_errors:
            raise self.thread_errors[thread_id]
        if thread_id in self.threads:
            return _FakeResponse(self.threads[thread_id])
        raise urllib.error.HTTPError(
            request.full_url, 404, "not found", {},
            io.BytesIO(json.dumps({"detail": {"code": "not_found", "message": "record not found"}}).encode()),
        )

    @property
    def methods(self):
        return {method for method, _ in self.calls}


def http_error(status, code="unavailable"):
    return urllib.error.HTTPError(
        "http://gateway" + DISCOVERY_PATH, status, "error", {},
        io.BytesIO(json.dumps({"detail": {"code": code, "message": "x"}}).encode()),
    )


class TempConfigCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="townsquare-host-reader-test-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.config = Config(
            base_url="http://gateway",
            identities=("cable", "sentinel-one"),
            state_file=self.root / "state.json",
            inbox_file=self.root / "INBOX.txt",
            timeout=1.0,
        )

    def all_threads(self):
        return {
            CABLE_ROW["thread_id"]: thread_payload(CABLE_ROW["thread_id"]),
            WOLVERINE_ROW["thread_id"]: thread_payload(WOLVERINE_ROW["thread_id"]),
            BISHOP_ROW["thread_id"]: thread_payload(BISHOP_ROW["thread_id"]),
        }


# ------------------------------------------------------------------ parsing


class ParsingTests(unittest.TestCase):
    def test_parses_real_shaped_discovery(self):
        result = parse_discovery(discovery_payload())
        self.assertEqual(len(result.items), 3)
        self.assertEqual(result.skipped_incomplete, 0)
        first = result.items[0]
        self.assertEqual(first.ledger_seq, 4)
        self.assertEqual(first.addressee, "wolverine")
        self.assertEqual(first.kind, "REQUEST")

    def test_open_work_and_history_overlap_yields_one_item_per_event(self):
        result = parse_discovery(discovery_payload([CABLE_ROW]))
        self.assertEqual(len(result.items), 1)
        self.assertEqual(set(result.items[0].sources), {"open_work", "history"})

    def test_repeated_board_entries_do_not_create_items(self):
        payload = discovery_payload([CABLE_ROW], boards=[CABLE_ROW["thread_id"]] * 4)
        result = parse_discovery(payload)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.board_thread_ids, (CABLE_ROW["thread_id"],))

    def test_incomplete_rows_are_skipped_not_fatal(self):
        bad_missing_event = {k: v for k, v in CABLE_ROW.items() if k != "event_id"}
        bad_missing_addressee = dict(row("T-2", "e2", "cable"))
        bad_missing_addressee["addressee"] = "   "
        payload = discovery_payload([CABLE_ROW, bad_missing_event, bad_missing_addressee, "not-a-dict"], history=[])
        result = parse_discovery(payload)
        self.assertEqual([item.event_id for item in result.items], [CABLE_ROW["event_id"]])
        self.assertEqual(result.skipped_incomplete, 3)

    def test_non_integer_ledger_seq_is_dropped_not_guessed(self):
        payload = discovery_payload([row("T-3", "e3", "cable", seq="seven"), row("T-4", "e4", "cable", seq=True)],
                                    history=[])
        result = parse_discovery(payload)
        self.assertEqual({item.ledger_seq for item in result.items}, {None})

    def test_rejects_thread_id_outside_gateway_grammar(self):
        payload = discovery_payload([row("../escape", "e5", "cable")], history=[])
        result = parse_discovery(payload)
        self.assertEqual(result.items, ())
        self.assertEqual(result.skipped_incomplete, 1)

    def test_unexpected_schema_raises(self):
        for payload in (
            [],
            "string",
            {"boards": {}},
            {"open_work": {"not": "a list"}},
            {"open_work": [], "boards": []},
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ReaderError) as caught:
                    parse_discovery(payload)
                self.assertEqual(caught.exception.code, "unexpected_schema")


# ------------------------------------------------------------------ identity


class IdentityFilterTests(unittest.TestCase):
    def test_only_addressed_work_is_taken(self):
        items = parse_discovery(discovery_payload()).items
        matched = filter_for_identities(items, ("cable", "sentinel-one"))
        self.assertEqual([item.addressee for item in matched], ["cable"])

    def test_visible_work_for_other_hosts_is_not_claimed(self):
        payload = discovery_payload([WOLVERINE_ROW, BISHOP_ROW], history=[])
        matched = filter_for_identities(parse_discovery(payload).items, ("cable",))
        self.assertEqual(matched, ())

    def test_being_owner_does_not_make_it_my_work(self):
        payload = discovery_payload([row("T-OWN", "e-own", "bishop", owner="cable")], history=[])
        matched = filter_for_identities(parse_discovery(payload).items, ("cable",))
        self.assertEqual(matched, ())

    def test_agent_identity_is_matched_too(self):
        payload = discovery_payload([row("T-AGENT", "e-agent", "Sentinel-One")], history=[])
        matched = filter_for_identities(parse_discovery(payload).items, ("cable", "sentinel-one"))
        self.assertEqual(len(matched), 1)

    def test_identity_matching_is_case_and_space_insensitive(self):
        payload = discovery_payload([row("T-CASE", "e-case", "  CABLE ")], history=[])
        self.assertEqual(len(filter_for_identities(parse_discovery(payload).items, ("cable",))), 1)

    def test_empty_identity_set_refuses_to_claim_the_board(self):
        items = parse_discovery(discovery_payload()).items
        with self.assertRaises(LocalStateError):
            filter_for_identities(items, ())

    def test_normalize_identities(self):
        self.assertEqual(normalize_identities("Cable", " sentinel-one ,cable", ["", None, "x"]), ("cable", "sentinel-one", "x"))


# ------------------------------------------------------------------ threads


class ExactThreadTests(TempConfigCase):
    def test_thread_url_is_exact_and_quoted(self):
        self.assertEqual(
            thread_url("http://gateway/", "POC-A.b_1"),
            "http://gateway" + THREAD_PREFIX + "POC-A.b_1",
        )

    def test_thread_url_refuses_traversal_and_wildcards(self):
        for bad in ("../../etc/passwd", "a/b", "*", "", "POC A"):
            with self.subTest(bad=bad):
                with self.assertRaises(ReaderError) as caught:
                    thread_url("http://gateway", bad)
                self.assertEqual(caught.exception.code, "bad_thread_id")

    def test_only_addressed_threads_are_retrieved(self):
        gateway = FakeGateway(threads=self.all_threads())
        state = empty_state()
        poll_once(self.config, state, opener=gateway)
        fetched = [url for method, url in gateway.calls if THREAD_PREFIX in url]
        self.assertEqual(fetched, ["http://gateway" + THREAD_PREFIX + CABLE_ROW["thread_id"]])
        self.assertEqual(gateway.methods, {"GET"})

    def test_summarize_thread_collapses_whitespace_and_truncates(self):
        summary = summarize_thread(thread_payload("T", events=2, content="a" * 500), content_chars=10)
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(summary["event_count"], 2)
        self.assertEqual(summary["excerpt"], "a" * 10 + "…")
        self.assertEqual(summary["latest_event_id"], "T-event-1")

    def test_summarize_thread_rejects_bad_shape(self):
        for payload in ({"thread_id": "T"}, {"events": []}, {"thread_id": "T", "events": [1]}, "nope"):
            with self.subTest(payload=payload):
                with self.assertRaises(ReaderError):
                    summarize_thread(payload)

    def test_transient_thread_failure_is_retried_without_duplicating(self):
        threads = self.all_threads()
        gateway = FakeGateway(threads=threads, thread_errors={CABLE_ROW["thread_id"]: http_error(503)})
        state = empty_state()
        poll_once(self.config, state, opener=gateway)
        self.assertEqual(len(state["items"]), 1)
        self.assertIsNone(state["items"][0]["detail"])
        self.assertEqual(state["counters"]["thread_reads_failed"], 1)

        healthy = FakeGateway(threads=threads)
        result = poll_once(self.config, state, opener=healthy)
        self.assertEqual(result.added, ())
        self.assertEqual(len(state["items"]), 1)
        self.assertEqual(state["items"][0]["detail"]["status"], "ok")

    def test_missing_thread_is_terminal_and_stops_retrying(self):
        gateway = FakeGateway(threads={})
        state = empty_state()
        poll_once(self.config, state, opener=gateway)
        self.assertEqual(state["items"][0]["detail"]["status"], "not_found")
        second = FakeGateway(threads={})
        poll_once(self.config, state, opener=second)
        self.assertEqual([url for _, url in second.calls if THREAD_PREFIX in url], [])

    def test_work_is_surfaced_even_when_detail_is_unavailable(self):
        gateway = FakeGateway(threads={}, thread_errors={CABLE_ROW["thread_id"]: http_error(503)})
        state = empty_state()
        poll_once(self.config, state, opener=gateway)
        inbox = render_inbox(state, base_url=self.config.base_url, identities=self.config.identities)
        self.assertIn(CABLE_ROW["thread_id"], inbox)
        self.assertIn("detail PENDING", inbox)

    def test_no_threads_mode_issues_discovery_only(self):
        gateway = FakeGateway(threads=self.all_threads())
        config = Config(**{**self.config.__dict__, "fetch_threads": False})
        poll_once(config, empty_state(), opener=gateway)
        self.assertEqual([url for _, url in gateway.calls], ["http://gateway" + DISCOVERY_PATH])


# ------------------------------------------------------------------ dedup


class DeduplicationTests(TempConfigCase):
    def test_repeated_polls_add_nothing_new(self):
        gateway = FakeGateway(threads=self.all_threads())
        state = empty_state()
        first = poll_once(self.config, state, opener=gateway)
        self.assertEqual(len(first.added), 1)
        for _ in range(4):
            again = poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
            self.assertEqual(again.added, ())
        self.assertEqual(len(state["items"]), 1)
        self.assertEqual(len(state["seen_event_ids"]), 1)
        self.assertEqual(state["counters"]["items_added"], 1)

    def test_repeated_polls_through_the_file_do_not_duplicate(self):
        for _ in range(3):
            state = load_state(self.config.state_file)
            poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
            persist(self.config, state)
        saved = json.loads(self.config.state_file.read_text())
        self.assertEqual(len(saved["items"]), 1)
        inbox = self.config.inbox_file.read_text()
        self.assertEqual(inbox.count(CABLE_ROW["event_id"]), 1)
        self.assertEqual(saved["counters"]["polls_ok"], 3)

    def test_new_event_on_a_known_thread_is_a_new_item(self):
        state = empty_state()
        poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
        follow_up = row(CABLE_ROW["thread_id"], "22222222-2222-4222-8222-222222222222", "cable",
                        seq=9, state="WORKING")
        gateway = FakeGateway(discovery=discovery_payload([CABLE_ROW, follow_up], history=[]),
                              threads=self.all_threads())
        result = poll_once(self.config, state, opener=gateway)
        self.assertEqual(result.added, (follow_up["event_id"],))
        self.assertEqual(len(state["items"]), 2)

    def test_dedup_survives_reordered_discovery(self):
        state = empty_state()
        poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
        reversed_rows = [BISHOP_ROW, CABLE_ROW, WOLVERINE_ROW]
        result = poll_once(self.config, state,
                           opener=FakeGateway(discovery=discovery_payload(reversed_rows), threads=self.all_threads()))
        self.assertEqual(result.added, ())


# ------------------------------------------------------------------ persistence


class PersistenceTests(TempConfigCase):
    def test_atomic_write_leaves_no_temp_and_replaces_content(self):
        target = self.root / "nested" / "file.txt"
        atomic_write(target, "first\n")
        atomic_write(target, "second\n")
        self.assertEqual(target.read_text(), "second\n")
        self.assertEqual([p.name for p in target.parent.iterdir()], ["file.txt"])

    def test_atomic_write_is_mode_600(self):
        target = self.root / "secretless.json"
        atomic_write(target, "{}\n")
        self.assertEqual(oct(target.stat().st_mode & 0o777), "0o600")

    def test_failed_write_leaves_previous_file_intact(self):
        target = self.root / "state.json"
        atomic_write(target, "good\n")
        with patch("hostreader.host_reader.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                atomic_write(target, "bad\n")
        self.assertEqual(target.read_text(), "good\n")
        self.assertFalse((self.root / "state.json.tmp").exists())

    def test_first_run_state_is_empty_not_an_error(self):
        state = load_state(self.root / "absent.json")
        self.assertEqual(state["schema"], STATE_SCHEMA)
        self.assertEqual(state["items"], [])

    def test_corrupt_state_is_a_hard_error_not_a_silent_reset(self):
        self.config.state_file.write_text("{not json", encoding="utf-8")
        with self.assertRaises(LocalStateError) as caught:
            load_state(self.config.state_file)
        self.assertIn("--reset-state", str(caught.exception))

    def test_foreign_schema_state_is_refused(self):
        self.config.state_file.write_text(json.dumps({"schema": "something-else"}), encoding="utf-8")
        with self.assertRaises(LocalStateError):
            load_state(self.config.state_file)

    def test_state_is_written_before_the_inbox_is_rendered(self):
        order: list[str] = []
        real = atomic_write

        def tracking(path, text):
            order.append(Path(path).name)
            return real(path, text)

        state = empty_state()
        poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
        with patch("hostreader.host_reader.atomic_write", side_effect=tracking):
            persist(self.config, state)
        self.assertEqual(order, ["state.json", "INBOX.txt"])

    def test_inbox_is_derived_only_from_state(self):
        state = empty_state()
        poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
        persist(self.config, state)
        from_disk = render_inbox(json.loads(self.config.state_file.read_text()),
                                 base_url=self.config.base_url, identities=self.config.identities)
        self.assertEqual(
            [line for line in from_disk.splitlines() if CABLE_ROW["thread_id"] in line],
            [line for line in self.config.inbox_file.read_text().splitlines() if CABLE_ROW["thread_id"] in line],
        )

    def test_legacy_poller_paths_are_never_written(self):
        """The default state/inbox directory must not be the legacy drop dir."""
        from hostreader.host_reader import DEFAULT_DIR

        self.assertNotIn(DEFAULT_DIR.rstrip("/"), ("~/.townsquare",))
        default = Config()
        self.assertNotIn(".townsquare/", str(default.state_file) + str(default.inbox_file))
        for name in ("NEW-EVENTS.txt", "last_seq"):
            self.assertNotIn(name, str(default.state_file) + str(default.inbox_file))


# ------------------------------------------------------------------ failure


class FailureTests(TempConfigCase):
    def seeded_state(self):
        state = empty_state()
        poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
        return state

    def test_unreachable_gateway_preserves_last_good_items(self):
        state = self.seeded_state()
        before = json.loads(json.dumps(state["items"]))
        result = poll_once(self.config, state,
                           opener=FakeGateway(discovery_error=urllib.error.URLError("Connection refused")))
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "unreachable")
        self.assertEqual(state["items"], before)
        self.assertEqual(state["seen_event_ids"], [CABLE_ROW["event_id"]])
        self.assertEqual(state["counters"]["polls_failed"], 1)

    def test_timeout_is_a_failed_poll_not_an_empty_board(self):
        state = self.seeded_state()
        result = poll_once(self.config, state, opener=FakeGateway(discovery_error=socket.timeout("timed out")))
        self.assertFalse(result.ok)
        self.assertEqual(len(state["items"]), 1)

    def test_gateway_503_is_reported_with_its_code(self):
        state = empty_state()
        result = poll_once(self.config, state, opener=FakeGateway(discovery_error=http_error(503, "unavailable")))
        self.assertFalse(result.ok)
        self.assertEqual(result.http_status, 503)
        self.assertEqual(result.error_code, "unavailable")

    def test_malformed_json_is_a_failed_poll(self):
        state = self.seeded_state()

        def broken(request, timeout=None):
            return _FakeResponse(b"{ not json at all")

        result = poll_once(self.config, state, opener=broken)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "malformed_json")
        self.assertEqual(len(state["items"]), 1)

    def test_unexpected_schema_is_a_failed_poll(self):
        state = self.seeded_state()
        result = poll_once(self.config, state, opener=FakeGateway(discovery={"unrelated": True}))
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "unexpected_schema")
        self.assertEqual(len(state["items"]), 1)

    def test_failed_poll_inbox_says_unknown_not_quiet(self):
        state = self.seeded_state()
        poll_once(self.config, state, opener=FakeGateway(discovery_error=urllib.error.URLError("refused")))
        persist(self.config, state)
        inbox = self.config.inbox_file.read_text()
        self.assertIn("poll:        FAILED", inbox)
        self.assertIn("UNKNOWN, not 'no work'", inbox)
        self.assertIn(CABLE_ROW["thread_id"], inbox)

    def test_empty_board_reads_as_nothing_addressed_not_as_failure(self):
        state = empty_state()
        result = poll_once(self.config, state,
                           opener=FakeGateway(discovery=discovery_payload([WOLVERINE_ROW], history=[])))
        self.assertTrue(result.ok)
        self.assertEqual(result.matched, ())
        persist(self.config, state)
        self.assertIn("Nothing addressed to these identities", self.config.inbox_file.read_text())

    def test_failed_poll_after_success_does_not_resurface_items_as_new(self):
        state = self.seeded_state()
        poll_once(self.config, state, opener=FakeGateway(discovery_error=urllib.error.URLError("refused")))
        result = poll_once(self.config, state, opener=FakeGateway(threads=self.all_threads()))
        self.assertTrue(result.ok)
        self.assertEqual(result.added, ())


# ------------------------------------------------------------------ evidence


class EvidenceTests(TempConfigCase):
    def test_evidence_is_sanitized_and_names_identifiers(self):
        state = empty_state()
        gateway = FakeGateway(threads=self.all_threads())
        result = poll_once(self.config, state, opener=gateway)
        with patch.dict(os.environ, {"TS_READER_COMMIT": "0" * 40}):
            record = evidence_record(self.config, result, state)
        serialized = json.dumps(record)
        self.assertEqual(record["http_methods_used"], ["GET"])
        self.assertEqual(record["mutating_requests"], 0)
        self.assertEqual(record["client_commit"], "0" * 40)
        self.assertEqual(record["discovery"]["http_status"], 200)
        self.assertEqual(record["observed_addressed_work"][0]["thread_id"], CABLE_ROW["thread_id"])
        self.assertEqual(record["observed_addressed_work"][0]["event_id"], CABLE_ROW["event_id"])
        self.assertIn(CABLE_ROW["thread_id"], record["exact_thread_reads"][0])
        # No content, no excerpt, no header, no credential may leak into evidence.
        for forbidden in ("excerpt", "Authorization", "Bearer", "OPERATOR-MANDATED", "content"):
            self.assertNotIn(forbidden, serialized)

    def test_evidence_records_a_failed_poll_honestly(self):
        state = empty_state()
        result = poll_once(self.config, state, opener=FakeGateway(discovery_error=http_error(503)))
        record = evidence_record(self.config, result, state)
        self.assertFalse(record["discovery"]["ok"])
        self.assertEqual(record["discovery"]["http_status"], 503)
        self.assertEqual(record["observed_addressed_work"], [])


class ReadOnlyTests(TempConfigCase):
    def test_every_request_is_a_get_with_no_body_and_no_authorization(self):
        captured: list[tuple[str, Any]] = []

        def recording(request, timeout=None):
            captured.append((request.get_method(), request.data, dict(request.header_items())))
            if DISCOVERY_PATH in request.full_url:
                return _FakeResponse(discovery_payload())
            return _FakeResponse(thread_payload(CABLE_ROW["thread_id"]))

        poll_once(self.config, empty_state(), opener=recording)
        self.assertTrue(captured)
        for method, data, headers in captured:
            self.assertEqual(method, "GET")
            self.assertIsNone(data)
            self.assertNotIn("Authorization", headers)

    def test_module_defines_no_write_verb(self):
        source = Path(__file__).resolve().parents[1].joinpath("hostreader", "host_reader.py").read_text()
        for verb in ('"POST"', '"PUT"', '"PATCH"', '"DELETE"', "method=\"POST\""):
            self.assertNotIn(verb, source)


if __name__ == "__main__":
    unittest.main()
