"""New regression-test category for the shared-connection concurrency defect
(docs/town-registrar-connection-concurrency.md), built on the real HTTP
topology -- TestClient/httpx + a thread pool, real bearer tokens -- reusing
the `FreshAppCase` harness bruce-lee extracted to
`registrar/tests/app_harness.py` (Addendum A3).

Separate file from `test_http.py` deliberately (Addendum A3): different
runtime profile (thread pools, repeated trials -- slow), and the file most
likely to ever be quarantined if it goes flaky. Keeping it apart means a
quarantine of this file never takes gsp's fast F1/F2/F4 security regression
coverage in `test_http.py` down with it.

**File-scoped rule (design doc, item 5 of the test-category list): no test in
this file may give a thread its own `sqlite3.Connection`.** That is exactly
the blind spot that let the original defect through undetected --
`test_registrar.py`'s `test_concurrent_root_allocation`/
`test_concurrent_children_and_publication` already cover the
own-connection-per-thread topology and remain valuable for file-level
contention, but they could never see a defect that only exists in
`main.py`'s per-*request* wiring. Every concurrent operation below goes
through the real ASGI app via `TestClient`/httpx, dispatched to `main.py`'s
real `get_db` dependency exactly as a real client's request would be. The
only direct `db.connect()` calls in this file are sequential, single-threaded
bootstrap steps (ACL grant, token minting) that run to completion and close
before any concurrent section starts -- the same pattern `FreshAppCase._bearer`
already uses, not a workaround of the rule above.

What this file builds now (per the design doc's "New regression test
category needed" section, items 1-2 and 4b) -- items 3, 4a, and any
status-code assertion under lock/busy contention are explicitly HELD, not
built here, pending open rulings (mixed read/write correctness depends on
the still-open narrow-vs-generalized exception-handler scope question with
ip-man; the `del _boot` tripwire depends on her Issue 3 ruling landing):

  1. HTTP-layer concurrency through the real app: `HttpConcurrentPaginationTests`.
  2. Data correctness, not just absence of exceptions: every walk asserts the
     *exact* expected set of post_uids -- no duplicates, no missing rows, no
     premature termination -- not merely "no 5xx". A "no 5xx" assertion alone
     would have passed against the pre-fix code roughly two-thirds of the
     time (ip-man's design note, "Measured impact").
  4b. `WriteRouteCoroutineTripwireTests` -- every write route stays a
      coroutine function, converting Risk #1 (writers must never land on the
      threadpool) from a remembered invariant into an enforced one.

Run pytest from the parent of registrar/ (the repo root), matching every
other file in this suite -- see the note in app_harness.py.

**Known environment quirk, documented rather than hidden (same convention
app_harness.py already uses for the Windows open-file-lock note) --
ronda-rousey, 2026-09-22:** on this dev box (Windows, CPython 3.14.6),
individual `GET /v1/posts` requests under genuine multi-thread concurrency
occasionally (observed roughly 1-in-3 trials at 4-6 concurrent readers, not
tied to a specific reader count) take approximately 122 seconds to complete
instead of the usual <0.1s, before returning a normal 200 with fully correct
data. Reproduced two independent ways: via bare and `with`-block `TestClient`,
and via a real `uvicorn.Server` hit with `httpx.Client` over a real loopback
socket (which instead raises `httpx.ReadTimeout` at whatever client timeout
is configured, since there is no TestClient-style indefinite wait on a real
transport) -- so this is not an artifact of TestClient's in-process ASGI
portal specifically. It does NOT reproduce in isolated stress tests of either
SQLite write contention alone or argon2 verification alone (both stay
sub-second under the same 6-way thread concurrency), so it is not simply
"SQLite is slow" or "argon2 is slow" -- something in the full FastAPI +
Starlette + anyio + per-request-`get_db` + argon2 stack, under genuine
OS-thread concurrency, occasionally stalls for a strikingly consistent
~122.0-122.1s (reproduced to within tens of milliseconds across unrelated
runs, which reads as a fixed timeout-and-recover somewhere in the stack, not
random scheduling jitter) and then always recovers and returns correct data.
Never once, across dozens of trials at 4/5/6 concurrent readers, did this
produce wrong data, a dropped request, or a permanent hang -- only latency.
Reported as a distinct, NOT-yet-root-caused finding (see ronda-rousey's QA
report, 2026-09-22) rather than silently engineered around: it is explicitly
out of scope for this file to fix or fully diagnose, since it does not bear
on the connection-concurrency defect/fix this test category exists to
regression-test, and per ip-man's own Risk #7 (design doc), a local dev-box
timing anomaly is not evidence about NAS (Python 3.12, Linux container)
behavior either way. Parameters below are sized modestly so a typical run
stays fast, while accepting -- per Addendum A3's own framing, "concurrency
tests run thread pools over repeated trials: slow" -- that an occasional run
may take several minutes rather than seconds. No assertion below is weakened
or skipped on account of this; a trial that stalls and then returns correct
data still passes, exactly as it should.
"""
from __future__ import annotations

import inspect
import unittest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from registrar.tests.app_harness import FreshAppCase


class HttpConcurrentPaginationTests(FreshAppCase):
    """Reproduces, over the real per-request-connection HTTP topology, the
    exact scenario ronda-rousey's original adversarial QA pass found broken:
    independent concurrent callers paginating GET /v1/posts. Pre-fix, this
    corrupted ~44% of completed walks and crashed outright ~34% of the time
    (20 trials x 5 concurrent readers, ip-man's design note). Post-fix, every
    trial must be exactly correct -- this is not a flaky-tolerance test, a
    single bad trial is a real regression back to shared-connection
    corruption, not noise to average away. (Latency is a different matter --
    see the environment-quirk note in the module docstring; a slow-but-
    correct trial is not a regression.)"""

    NUM_POSTS = 24           # multiple pages per walk at PAGE_LIMIT below
    PAGE_LIMIT = 6            # ceil(24/6) = 4 pages/walk -- forces real cursor traffic, not a single-page happy path
    CONCURRENT_READERS = 5    # matches ip-man's original defect-reproduction scale (design doc, "Measured impact")
    TRIALS = 8
    MAX_PAGES_PER_WALK = NUM_POSTS + 5  # safety valve: a corrupted cursor must not be allowed to hang the suite

    def setUp(self):
        self.main_module = self._boot(cursor_key_file=self._key_file())
        # `with`-entered explicitly via addCleanup rather than a `with` block
        # (setUp has no natural block scope): reuses one portal for every
        # request in this test instead of spinning up a fresh one per call,
        # Starlette's own recommended TestClient usage. Does not depend on
        # lifespan firing -- main.py registers no lifespan handler at all
        # (Addendum A1) -- so this is not a reopening of that decision, just
        # the ordinary efficient way to drive many requests at one client.
        self.client = TestClient(self.main_module.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self._grant_acl("writer", "qa", "concurrency")
        write_headers = self._bearer(self.main_module, scope="post:write", principal="writer")
        self.expected_uids = self._seed_posts(write_headers)
        self.assertEqual(self.NUM_POSTS, len(self.expected_uids), "seed step itself must produce exactly NUM_POSTS distinct posts")
        # One bearer token per reader -- real per-caller credentials, not one
        # token shared and hammered by every thread (that would introduce
        # its own, separate write-contention hazard on tokens.last_used_at,
        # which is a distinct, currently-open finding -- jackie-chan's Issue
        # 1 -- not what this test is characterizing).
        self.reader_headers = [self._bearer(self.main_module, scope="post:read", principal=f"reader-{i}") for i in range(self.CONCURRENT_READERS)]

    def _grant_acl(self, principal, namespace, board):
        from registrar.app.db import connect
        import os
        db = connect(os.environ["REGISTRAR_DB"])
        try:
            db.execute("INSERT INTO acls VALUES (?,?,?,NULL,NULL)", (principal, "namespace", namespace))
            db.execute("INSERT INTO acls VALUES (?,?,?,NULL,NULL)", (principal, "board", board))
        finally:
            db.close()

    def _seed_posts(self, write_headers):
        """Sequential, single-threaded, via the real HTTP layer -- seeding is
        not the thing under test here (writer concurrency is explicitly HELD,
        see module docstring), so there is no reason to introduce write
        contention while building the fixture."""
        uids = set()
        for i in range(self.NUM_POSTS):
            body = {"namespace": "qa", "board": "concurrency", "state": "OPEN", "assignments": [{"agent_id": "writer", "role": "responsible"}]}
            r = self.client.post("/v1/roots/reserve", headers={**write_headers, "Idempotency-Key": f"seed-{i}"}, json=body)
            self.assertEqual(201, r.status_code, r.text)
            uids.add(r.json()["post_uid"])
        return uids

    def _walk_all(self, headers):
        """One full paginated walk of GET /v1/posts, following next_cursor
        until it is None. Raises AssertionError (with full diagnostics) on
        any non-200 response or on exceeding the page-count safety valve --
        both are real findings, not conditions to swallow and keep looping."""
        uids = []
        cursor = None
        pages = 0
        while True:
            pages += 1
            if pages > self.MAX_PAGES_PER_WALK:
                raise AssertionError(f"walk did not terminate within {self.MAX_PAGES_PER_WALK} pages -- likely a corrupted cursor looping (post-fix regression)")
            params = {"board": "concurrency", "limit": self.PAGE_LIMIT}
            if cursor is not None:
                params["cursor"] = cursor
            r = self.client.get("/v1/posts", params=params, headers=headers)
            if r.status_code != 200:
                raise AssertionError(f"GET /v1/posts page {pages} returned {r.status_code}: {r.text}")
            body = r.json()
            uids.extend(row["post_uid"] for row in body["posts"])
            cursor = body["next_cursor"]
            if cursor is None:
                break
        return uids

    def test_concurrent_paginated_walks_return_exactly_the_expected_post_uid_set(self):
        for trial in range(self.TRIALS):
            with ThreadPoolExecutor(max_workers=self.CONCURRENT_READERS) as pool:
                futures = [pool.submit(self._walk_all, self.reader_headers[i]) for i in range(self.CONCURRENT_READERS)]
                results = [f.result() for f in futures]  # re-raises any per-thread AssertionError in the main test thread, with its original diagnostic text
            for reader_index, uids in enumerate(results):
                with self.subTest(trial=trial, reader=reader_index):
                    seen = set(uids)
                    duplicates = [u for u in seen if uids.count(u) > 1]
                    missing = self.expected_uids - seen
                    extra = seen - self.expected_uids
                    self.assertEqual(len(uids), len(seen), f"trial {trial} reader {reader_index}: duplicate post_uid(s) in one walk: {duplicates}")
                    self.assertEqual(set(), missing, f"trial {trial} reader {reader_index}: walk missing post_uid(s) (premature termination or lost rows): {missing}")
                    self.assertEqual(set(), extra, f"trial {trial} reader {reader_index}: walk returned unexpected post_uid(s) not in the seeded set: {extra}")
                    self.assertEqual(self.expected_uids, seen, f"trial {trial} reader {reader_index}: final set mismatch")

    def test_single_reader_walk_is_a_sanity_baseline(self):
        # Not itself a concurrency assertion -- confirms the harness/fixture
        # (seed data, pagination params, walk helper) is correct in isolation
        # before trusting the concurrent trials above to mean anything.
        uids = self._walk_all(self.reader_headers[0])
        self.assertEqual(self.NUM_POSTS, len(uids))
        self.assertEqual(self.expected_uids, set(uids))


class WriteRouteCoroutineTripwireTests(FreshAppCase):
    """Structural tripwire (design doc item 4, second half), non-timing-
    dependent so it can never pass flakily: every write route must remain a
    coroutine function. This is Risk #1 of the design note made an enforced
    invariant instead of a remembered one -- if any write route were ever
    converted from `async def` to `def` "for consistency", it would land on
    FastAPI's worker threadpool and introduce real SQLite write-lock
    contention where none exists today (writers are event-loop-serialized by
    design). This test fails the moment that invariant is violated, rather
    than waiting for someone to notice contention in production."""

    WRITE_ROUTES = ("reserve_root", "reserve_post", "publish", "verify", "import_run", "promote")

    def setUp(self):
        self.main_module = self._boot()

    def test_every_write_route_is_a_coroutine_function(self):
        for name in self.WRITE_ROUTES:
            with self.subTest(route=name):
                fn = getattr(self.main_module, name)
                self.assertTrue(inspect.iscoroutinefunction(fn), f"{name} must stay `async def` -- a sync `def` write route would land on the threadpool and introduce write-lock contention (Risk #1)")


if __name__ == "__main__":
    unittest.main()
