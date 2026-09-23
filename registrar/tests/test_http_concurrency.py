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

What this file builds (per the design doc's "New regression test category
needed" section, items 1-5). Items 3, 4a, and the status-code assertions
under lock/busy contention were originally HELD pending open rulings; all
three rulings landed (Addendum B: B1 narrow exception-handler scope, B2
`_migrate_at_boot()` replacing `_boot`, B3 status-code spec; jackie-chan's
review of `60ee5aa` confirmed the delivered code matches), so they are built
here now, on top of `d9eb5a0`:

  1. HTTP-layer concurrency through the real app: `HttpConcurrentPaginationTests`.
  2. Data correctness, not just absence of exceptions: every walk asserts the
     *exact* expected set of post_uids -- no duplicates, no missing rows, no
     premature termination -- not merely "no 5xx". A "no 5xx" assertion alone
     would have passed against the pre-fix code roughly two-thirds of the
     time (ip-man's design note, "Measured impact").
  3. Mixed read/write, plus the B3 status-code spec: `MixedReadWriteConcurrencyTests`
     -- readers walking `GET /v1/posts` while a writer reserves and publishes.
     Per B3's exact guidance (not reinvented here): 200 is normal; a 503 is
     legitimate under genuine contention and must be retryable (a retry after
     the writer's transaction completes must succeed); 500 is never
     acceptable for lock contention -- that is the defect B1 exists to close,
     and it is the assertion that matters most; a 503 is never asserted to
     occur (timing-dependent, would flake) -- only its absence-as-anything-
     other-than-503 and its recovery are asserted. Also covers the plain
     correctness half of item 3: a post observed as `registration_state`
     `published` must never be missing the rest of `publish()`'s single
     transaction (drive fields, and the filename alias `publish()` inserts
     in the same `BEGIN IMMEDIATE`) -- readers must never observe an
     uncommitted row, and a post-completion read must never miss a
     committed one.
  4a. `NoModuleLevelConnectionTripwireTests` -- the design doc's own item-4
      structural tripwire, now a strong assertion rather than one with a
      footnote: `registrar.app.main` has no module attribute that is a
      `sqlite3.Connection`, and the module does not import `connect` at all
      (Addendum B2's `_migrate_at_boot()` made both unconditionally true,
      confirmed structurally in `60ee5aa` and re-verified by jackie-chan).
  4b. `WriteRouteCoroutineTripwireTests` -- every write route stays a
      coroutine function, converting Risk #1 (writers must never land on the
      threadpool) from a remembered invariant into an enforced one.
  4c. `RegistrarCallsWrappedInInvokeTripwireTests` -- Addendum B1's own
      convention, made auditable: "every route that calls a Registrar method
      wraps it in invoke()", true of all eight such routes with no
      exceptions. Static AST analysis of `main.py`'s source, not a live-app
      probe -- flagged as the one remaining item in ronda-rousey's original
      QA report and closed here.
  5. File-scoped rule (unchanged, restated below): no test in this file gives
     a thread its own `sqlite3.Connection`.

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

import ast
import hashlib
import inspect
import sqlite3
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import registrar.app  # package __init__ only -- a docstring, no DB/migration side effects; safe to import at collection time
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


class MixedReadWriteConcurrencyTests(FreshAppCase):
    """Design doc test-category item 3 + the B3 status-code spec, using B3's
    exact guidance rather than an invented one:

    - Reads in flight when a writer takes the write lock: 200 is normal; 503
      is legitimate if genuinely contended, and must be retryable -- a retry
      after the writer's transaction completes must succeed.
    - Reads arriving after a writer's transaction completes must see the
      writer's committed state -- no dirty reads of in-flight, uncommitted
      writer state. This is the whole point of the fix.
    - 500 is never acceptable for lock contention -- this is the actual
      defect B1 exists to close, and it is the assertion that matters most.
    - Do NOT assert that a 503 occurs -- B3 is explicit this is
      timing-dependent and would flake. Assert the negative (no 5xx other
      than 503) and the recovery (any 503 is followed by a successful retry
      that returns 200 with correct data).

    The "no dirty read" check is not taken on WAL's word alone (jackie-chan's
    Risk-2 ruling already established that mechanically): it is exercised
    live, over the real HTTP topology, by cross-checking two independent
    reads against the SAME multi-statement transaction. `Registrar.publish`
    does an `UPDATE posts ... registration_state='published'` and then, in
    the SAME `BEGIN IMMEDIATE`, `INSERT INTO aliases` for the post's
    filename. Because both statements commit together or not at all, the
    instant any reader observes `registration_state=='published'` via
    `GET /v1/posts`, the filename alias it names is *already* durably
    committed too -- so a `GET /v1/aliases/{filename}` that fails to resolve
    it at that point is a genuine torn/dirty read across the transaction
    boundary, not a timing artifact to explain away.

    File-scoped rule (unchanged): no test in this file gives a thread its own
    `sqlite3.Connection`. The writer and every reader drive the real app
    through the shared `TestClient` instance, exactly like
    `HttpConcurrentPaginationTests` above -- dispatched through `main.py`'s
    real `get_db` dependency exactly as a real client's request would be.
    The only direct `db.connect()` call is `_grant_acl`'s, a sequential,
    single-threaded bootstrap step that runs to completion and closes before
    the concurrent section starts (same pattern as
    `HttpConcurrentPaginationTests._grant_acl`)."""

    NUM_WRITES = 12          # well under GET /v1/posts's default page size (100) and hard max (200) -- no pagination/cursor complexity needed to exercise this
    NUM_READERS = 4
    NAMESPACE = "qa"
    BOARD = "mixed"
    MAX_503_RETRY_ATTEMPTS = 20  # B3: any 503 must be followed by a successful retry -- bounded so a genuine regression (503 that never clears) fails loud instead of hanging the suite
    RETRY_DELAY_SECONDS = 0.1

    def setUp(self):
        self.main_module = self._boot()  # no cursor-signing key needed: NUM_WRITES is well under the page limit, so no response in this test ever carries a cursor
        self.client = TestClient(self.main_module.app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self._grant_acl("writer", self.NAMESPACE, self.BOARD)
        self.write_headers = self._bearer(self.main_module, scope="post:write", principal="writer")
        self.reader_headers = [self._bearer(self.main_module, scope="post:read", principal=f"mixed-reader-{i}") for i in range(self.NUM_READERS)]

    def _grant_acl(self, principal, namespace, board):
        from registrar.app.db import connect
        import os
        db = connect(os.environ["REGISTRAR_DB"])
        try:
            db.execute("INSERT INTO acls VALUES (?,?,?,NULL,NULL)", (principal, "namespace", namespace))
            db.execute("INSERT INTO acls VALUES (?,?,?,NULL,NULL)", (principal, "board", board))
        finally:
            db.close()

    def _get_retrying_on_503(self, path, params, headers):
        """One GET, retried on 503 up to MAX_503_RETRY_ATTEMPTS. Fails the
        test immediately on any 500 (B3: never acceptable for lock
        contention) or any status other than 200/503 (not the shape this
        helper exists to characterize). Returns (response, was_retried)."""
        last = None
        for attempt in range(self.MAX_503_RETRY_ATTEMPTS):
            r = self.client.get(path, params=params, headers=headers)
            self.assertNotEqual(500, r.status_code, f"GET {path} attempt {attempt}: 500 under lock contention -- this is exactly the defect B1 exists to close: a locked/busy sqlite3.OperationalError must map to a retryable 503, never surface as an unhandled 500. Body: {r.text}")
            self.assertIn(r.status_code, (200, 503), f"GET {path} attempt {attempt}: unexpected status {r.status_code}: {r.text}")
            if r.status_code != 503:
                return r, attempt > 0
            last = r
            time.sleep(self.RETRY_DELAY_SECONDS)
        self.fail(f"GET {path} kept returning 503 for {self.MAX_503_RETRY_ATTEMPTS} attempts ({self.MAX_503_RETRY_ATTEMPTS * self.RETRY_DELAY_SECONDS:.1f}s of retry delay) -- B3 requires that a retry after the writer's transaction completes succeeds; last body: {last.text if last else None}")

    def _assert_published_row_fully_committed(self, row):
        for field in ("drive_file_id", "drive_url", "filename", "content_sha256"):
            self.assertIsNotNone(row.get(field), f"post {row['post_uid']} has registration_state='published' but {field!r} is null/missing -- partial visibility of publish()'s UPDATE, a dirty/torn read")

    def _assert_alias_resolves(self, post_uid, filename, headers):
        r, _ = self._get_retrying_on_503(f"/v1/aliases/{filename}", {}, headers)
        self.assertEqual(200, r.status_code, r.text)
        matches = {m["resource_uid"] for m in r.json()["matches"]}
        self.assertIn(post_uid, matches, f"post {post_uid} was observed as registration_state='published' via GET /v1/posts, but its filename alias {filename!r} -- inserted in the SAME publish() BEGIN IMMEDIATE transaction, after the UPDATE -- does not resolve via GET /v1/aliases. Either both the state change and the alias must be visible, or neither: this is the 'readers never observe an uncommitted row' invariant the fix exists to guarantee.")

    def _writer_reserve_and_publish(self, write_headers):
        """Sequential, single writer thread: NUM_WRITES independent
        reserve-then-publish pairs, each its own BEGIN IMMEDIATE transaction
        (idem() in service.py). Returns the list of {post_uid, filename} for
        everything that successfully published, in commit order."""
        published = []
        for i in range(self.NUM_WRITES):
            key = f"mixed-write-{i}"
            body = {"namespace": self.NAMESPACE, "board": self.BOARD, "state": "OPEN", "assignments": [{"agent_id": "writer", "role": "responsible"}]}
            r = self.client.post("/v1/roots/reserve", headers={**write_headers, "Idempotency-Key": key}, json=body)
            self.assertEqual(201, r.status_code, r.text)
            reserved = r.json()
            filename = f'{reserved["thread_id"]}.000-OPEN__by-writer__pid-{reserved["pid"]}.txt'
            drive_file_id = f"mixed-write-{i}"
            payload = {"drive_file_id": drive_file_id, "drive_url": f"https://drive.google.com/file/d/{drive_file_id}/view", "filename": filename, "content_sha256": hashlib.sha256(f"mixed-{i}".encode()).hexdigest()}
            r2 = self.client.put(f"/v1/posts/{reserved['post_uid']}/publication", headers={**write_headers, "Idempotency-Key": f"{key}-pub"}, json=payload)
            self.assertEqual(200, r2.status_code, r2.text)
            published.append({"post_uid": reserved["post_uid"], "filename": filename})
        return published

    def _reader_loop(self, headers, stop_event, verified_published, lock):
        """Poll GET /v1/posts until told to stop. Every response is checked
        for the no-500/retryable-503 contract; every 'published' row seen for
        the first time triggers the cross-transaction alias check. Sets
        stop_event on any exit (normal or error) so siblings wind down
        promptly instead of continuing to poll after a sibling has already
        failed the test."""
        try:
            while not stop_event.is_set():
                r, _ = self._get_retrying_on_503("/v1/posts", {"board": self.BOARD, "limit": 200}, headers)
                body = r.json()
                self.assertIsNone(body["next_cursor"], "test fixture writes only NUM_WRITES posts, well under the page limit -- a non-null next_cursor means an assumption behind this test (single-page reads, no cursor complexity) no longer holds")
                for row in body["posts"]:
                    if row["registration_state"] != "published":
                        continue
                    self._assert_published_row_fully_committed(row)
                    with lock:
                        first_time = row["post_uid"] not in verified_published
                        if first_time:
                            verified_published.add(row["post_uid"])
                    if first_time:
                        self._assert_alias_resolves(row["post_uid"], row["filename"], headers)
        finally:
            stop_event.set()

    def test_mixed_read_write_no_500_and_503_is_retryable_and_writer_commits_are_visible(self):
        stop_event = threading.Event()
        verified_published = set()
        lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=self.NUM_READERS + 1) as pool:
            reader_futures = [pool.submit(self._reader_loop, self.reader_headers[i], stop_event, verified_published, lock) for i in range(self.NUM_READERS)]
            writer_future = pool.submit(self._writer_reserve_and_publish, self.write_headers)
            published = writer_future.result()  # propagates any writer-side failure into the main test thread
            stop_event.set()
            for f in reader_futures:
                f.result()  # propagates any reader-side failure (no-500, retryable-503, dirty-read) into the main test thread

        self.assertEqual(self.NUM_WRITES, len(published), "writer must successfully publish every post it reserved -- a short count here means the writer itself failed silently, not a reader-side finding")

        # Correctness check: a read AFTER every writer transaction has
        # committed must see every published post, fully formed, with its
        # alias resolvable -- "never miss a committed row" (B3/item 3).
        final, _ = self._get_retrying_on_503("/v1/posts", {"board": self.BOARD, "limit": 200}, self.reader_headers[0])
        final_body = final.json()
        final_by_uid = {row["post_uid"]: row for row in final_body["posts"]}
        expected_uids = {p["post_uid"] for p in published}
        self.assertEqual(expected_uids, set(final_by_uid), "post-completion read is missing committed post_uid(s), or shows extra ones -- a committed write must never be invisible to a subsequent read")
        for p in published:
            row = final_by_uid[p["post_uid"]]
            self.assertEqual("published", row["registration_state"], f"post {p['post_uid']}: writer's publish() returned 200 but the post-completion read shows registration_state={row['registration_state']!r}")
            self._assert_published_row_fully_committed(row)
            self._assert_alias_resolves(p["post_uid"], p["filename"], self.reader_headers[0])

        # Deliberately NOT asserted, per B3: that verified_published is
        # non-empty (i.e., that some reader actually observed a post
        # mid-race, before the writer finished). It is expected under this
        # test's timing (4 readers polling continuously against a
        # multi-second sequential writer), but asserting it would be exactly
        # the kind of timing-dependent assertion B3 warns against for the
        # 503 case -- a slower or faster environment could legitimately
        # shift every observation to before or after the race window without
        # that being a regression. The in-flight check that matters (no
        # dirty reads) still ran on whatever was observed; the
        # post-completion check above is what makes the "never miss a
        # committed row" guarantee unconditional regardless of timing.


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


class NoModuleLevelConnectionTripwireTests(FreshAppCase):
    """Structural tripwire, design doc item 4 ("assert two concurrent
    requests never share a sqlite3.Connection identity / no module-level
    connection is reachable from handlers"), written now that Addendum B2's
    `_migrate_at_boot()` replaced the old `del _boot` plan -- per B2's own
    consequence, this can be a strong structural assertion rather than one
    carrying an unexplained special case: `main.py` no longer has a
    module-level connection of any kind (open or closed), and it does not
    import `connect` from db.py at all. `session()` is the only door out of
    db.py it uses, and everything opened through it closes in a `finally`.

    Both properties were confirmed by jackie-chan's review of `60ee5aa`
    against the running booted module (not just by reading source); this
    test is the permanent, repeatable regression guard for that same
    property, not a new discovery. Non-timing-dependent -- runs once,
    deterministically, and can never pass flakily."""

    def setUp(self):
        self.main_module = self._boot()

    def test_no_module_attribute_is_a_sqlite3_connection(self):
        offenders = [name for name, value in vars(self.main_module).items() if isinstance(value, sqlite3.Connection)]
        self.assertEqual([], offenders, f"registrar.app.main has a module-level sqlite3.Connection attribute {offenders} -- this is exactly the shared/leaked-connection topology the fix removes; every connection must be opened and closed per-request (get_db) or per-boot (_migrate_at_boot), never bound at module scope where a handler could reach it")

    def test_main_module_does_not_import_connect(self):
        self.assertFalse(hasattr(self.main_module, "connect"), "registrar.app.main has a `connect` attribute -- main.py must only ever open a connection through db.py's `session()`, which always closes in a `finally`; importing `connect` directly reopens the possibility of an unclosed or module-scoped connection (Addendum B2)")

    def test_no_boot_attribute_survives_import(self):
        self.assertFalse(hasattr(self.main_module, "_boot"), "a module-level `_boot` name survived import -- Addendum B2 replaced the closed-but-still-bound `_boot` connection with a function-scoped `_migrate_at_boot()` specifically so no module attribute of this shape exists at all, closed or otherwise")


class RegistrarCallsWrappedInInvokeTripwireTests(unittest.TestCase):
    """Structural tripwire, design doc item 4 / Addendum B1 and B4's own
    "Done when" line: "Every route that calls a Registrar method is wrapped
    in invoke(), enforced by a structural test." B1's narrow ruling made this
    convention exact and auditable -- "true of all eight such routes with no
    exceptions" -- instead of merely remembered; this is the enforcement,
    flagged as the one remaining item in ronda-rousey's original QA report
    and closed here.

    Static AST analysis of registrar/app/main.py's actual source file --
    deliberately not import-based (importing main.py runs migration/startup
    side effects this check has no need to pay for, and AST analysis is
    robust to reformatting in a way that, say, regex-over-source-text would
    not be). Non-timing-dependent, cannot pass flakily: it runs once,
    deterministically, against whatever main.py's source currently says.

    Per ip-man's B1 ruling, the five routes that call `db.execute` directly
    and never construct a `Registrar` -- `ready`, `get_root`, `get_post`,
    `assignments`, `reconciliation` -- are NOT required to wrap anything:
    they call no service method and cannot raise a domain exception
    (Conflict/Forbidden/Invalid/Unavailable), so an unwrapped `db.execute` in
    one of them is not a finding. This class checks the right population --
    routes that call `Registrar(...)`, not all DB-touching routes -- and
    `test_the_expected_eight_routes_are_exactly_the_ones_calling_registrar`
    guards that population assumption itself, so a route quietly starting or
    ceasing to call `Registrar` doesn't silently drop out of coverage."""

    EXPECTED_ROUTES_CALLING_REGISTRAR = {"reserve_root", "reserve_post", "publish", "verify", "import_run", "promote", "posts", "aliases"}

    @classmethod
    def setUpClass(cls):
        main_path = Path(inspect.getsourcefile(registrar.app)).parent / "main.py"
        cls.tree = ast.parse(main_path.read_text(encoding="utf-8"), filename=str(main_path))

    @staticmethod
    def _is_route_function(node):
        """A route handler: a (possibly async) def decorated with
        `@app.<verb>(...)` -- matches every route in main.py, not just the
        eight this test cares about; population-narrowing happens in
        `_registrar_calls_in`, not here."""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        return any(isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app" for dec in node.decorator_list)

    @staticmethod
    def _is_registrar_method_call(node):
        """Matches the AST shape of `Registrar(db).some_method(...)`: a Call
        whose func is attribute-access on the result of calling `Registrar`."""
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Call) and isinstance(node.func.value.func, ast.Name) and node.func.value.func.id == "Registrar"

    @staticmethod
    def _is_invoke_call(node):
        return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "invoke"

    def _registrar_calls_in(self, fn_node):
        """Every Registrar(...).method(...) call anywhere inside fn_node
        (walking through the lambda that normally wraps it), each tagged
        with whether it is nested -- at any depth, matching the actual
        `invoke(lambda:Registrar(db).method(...))` shape -- inside the
        arguments of a call to `invoke(...)`. Parent links are built once
        per function, scoped to that function's own subtree, so climbing
        never escapes into a sibling route."""
        parent = {}
        for node in ast.walk(fn_node):
            for child in ast.iter_child_nodes(node):
                parent[child] = node
        found = []
        for node in ast.walk(fn_node):
            if not self._is_registrar_method_call(node):
                continue
            wrapped = False
            cur = node
            while cur in parent:
                cur = parent[cur]
                if self._is_invoke_call(cur):
                    wrapped = True
                    break
            found.append((node.lineno, node.func.attr, wrapped))
        return found

    def test_every_route_calling_registrar_wraps_the_call_in_invoke(self):
        unwrapped = []
        for node in ast.walk(self.tree):
            if not self._is_route_function(node):
                continue
            for lineno, method, wrapped in self._registrar_calls_in(node):
                if not wrapped:
                    unwrapped.append(f"{node.name} (main.py line {lineno}): Registrar(...).{method}(...) is not wrapped in invoke()")
        self.assertEqual([], unwrapped, "found Registrar method call(s) not wrapped in invoke() -- every route that calls a Registrar method must wrap it (Addendum B1); an unwrapped call means Conflict/Forbidden/Invalid/Unavailable raised from service.py escapes as an unhandled 500 instead of the correct mapped HTTP status:\n" + "\n".join(unwrapped))

    def test_the_expected_eight_routes_are_exactly_the_ones_calling_registrar(self):
        """Guards the population itself, not just the wrapping -- confirms
        this test is checking the right set of routes. B1's own audit found
        exactly eight; ready/get_root/get_post/assignments/reconciliation
        call db.execute directly and are correctly excluded. If this set ever
        changes, the wrapping test above needs re-auditing against the new
        population rather than silently continuing to pass over a
        newly-unwrapped route this test no longer looks at."""
        routes_seen_calling_registrar = {node.name for node in ast.walk(self.tree) if self._is_route_function(node) and self._registrar_calls_in(node)}
        self.assertEqual(self.EXPECTED_ROUTES_CALLING_REGISTRAR, routes_seen_calling_registrar, "the set of routes that call Registrar(...) has changed -- a route was added to or removed from this population without the invoke()-wrapping tripwire's assumptions being re-audited")


if __name__ == "__main__":
    unittest.main()
