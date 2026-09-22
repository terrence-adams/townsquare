# Town Registrar — shared-connection concurrency defect (design note)

**Status: DESIGN ONLY, not authorized for implementation. Held pending Sensei prioritization.**
**Author: ip-man (design read, 2026-09-22). No code changed as part of this note.**

## How this was found

During independent QA review of the cursor-pagination change (`466c55d`), ronda-rousey adversarially tested concurrent callers against `GET /v1/posts` and found the pagination walk returns silently wrong data under concurrent load. This is a **pre-existing defect**, not introduced by the pagination work and not fixed by it — confirmed present on `internal` before that commit too. ip-man then did a design-only read (no code changes) to characterize the defect and recommend a fix approach.

## Problem in one sentence

`registrar/app/main.py` wires one `sqlite3.Connection` and one `Registrar` as process-lifetime module globals (`db=connect(DB_PATH); migrate(db); service=Registrar(db)`), and FastAPI dispatches the app's synchronous read routes to a worker threadpool — so concurrent reads drive one connection from many OS threads at once, producing crashes and, worse, silently wrong result sets.

## Confirmed mechanics

- `db.py` passes `check_same_thread=False`, deliberately disabling Python's guardrail against exactly this pattern.
- `Registrar.__init__` stores that one connection as `self.db`; every one of its ~12 methods uses it.
- **The read/write split is asymmetric, and that asymmetry is load-bearing.** Every *write* route (`reserve_root`, `reserve_post`, `publish`, `verify`, `import_run`, `promote`) is `async def` — needs `await request.json()` — so it runs synchronously on the event-loop thread and writers have never contended with each other. Every *read* route (`ready`, `get_root`, `get_post`, `posts`, `aliases`, `assignments`, `reconciliation`) is plain `def`, so it goes to the threadpool.
- Consequences: read↔read on the shared connection is the corruption ronda-rousey measured. Read↔write is a second, previously unreported risk — a threadpool read issued while a writer holds `BEGIN IMMEDIATE` executes inside that writer's uncommitted transaction, a dirty read that can return rows subsequently rolled back. Write↔write has never been exercised under contention in the live topology — **any fix that moves writes off the event loop introduces real SQLite lock contention where none exists today.**
- **The test suite cannot see `main.py` at all.** `tests/test_registrar.py` builds `Registrar(self.db)` directly and gives each concurrency-test thread its own connection — so the suite has zero coverage of the wiring where the defect actually lives, and would not catch a regression here even after a fix.
- **Likely mechanism:** `Connection.execute()` draws prepared statements from the connection's shared LRU statement cache. Two threads running the same SQL text can get the same `sqlite3_stmt`; the second resets/re-binds it while the first is mid-fetch. This produces exactly the symptom set seen: duplicate rows from the start, premature exhaustion, `InterfaceError`.
- **Severity amplifier:** `service.py`'s `next_cursor` is derived from the last row of a (possibly corrupted) result set. A corrupted final row produces a *correctly signed* cursor pointing at the wrong position — corruption persists across requests, poisoning every subsequent page of a multi-page walk with a validly-signed cursor.

Measured impact (ronda-rousey, 20 trials × 5 concurrent independent readers): 34/100 walks crashed outright; of the 66 that completed with no exception, 44 returned silently wrong data (duplicates or premature truncation).

## Recommendation: (a) per-request connection, dependency-injected

One connection per request, opened and closed by a FastAPI dependency. Keep every write route `async def` (do not change this).

- A `get_db` dependency yields `connect(DB_PATH)` and closes it in `finally`.
- Migration moves to app startup (lifespan), on its own connection, run once before serving.
- Routes take the connection as a parameter and build `Registrar(conn)` per request — `Registrar` is a stateless wrapper, per-request construction is free.
- `identity()` takes the connection as an argument instead of closing over the module global; same for `verify_attestation(db, ...)`.
- **Zero changes to `service.py`, `auth.py`, `attestation.py`.**

### Why this is right-sized

SQLite in WAL mode is designed for many connections to one file, not one connection across many threads. The app already has WAL, `busy_timeout=5000`, and `BEGIN IMMEDIATE` on every write — a complete, correct multi-connection posture the deployment currently undermines by handing out a single connection.

Decisive point: the multi-connection topology is the one the test suite *already* proves. `test_concurrent_root_allocation`/`test_concurrent_children_and_publication` run 100 threads with independent connections and pass. This fix moves production *into* the configuration already battle-tested since WS3, not out of it — inverting the usual risk calculus.

Cost at this scale (1,070 rows, home LAN, a handful of viewer sessions): a `sqlite3.connect` plus four PRAGMAs per request. Sub-millisecond. No new dependency, no async rewrite.

### Rejected alternatives

- **(b) Serializing lock in `Registrar`** — rejected. Five route handlers in `main.py` call `db.execute` directly outside `Registrar` (plus `auth.authenticate_identity`, `attestation.verify`), so a lock scoped to `Registrar` leaves the bug alive on the auth path — exactly where the spurious 403-on-valid-token was observed. Widening the lock to the whole connection would need to be re-entrant (`idem()` wraps `create()`), span lazy cursor iteration, and would serialize all reads, throwing away WAL's free reader concurrency for no reason — connections are free here, locks are not the right tool.
- **(c) `async def` + `aiosqlite`** — rejected firmly. Requires making every `service.py` method async, including `idem()` and `promote_import()` — the two most correctness-critical, least-worth-touching functions in the repo. Adds a dependency. `aiosqlite` funnels one connection through one worker thread regardless, so it buys non-blocking I/O, not concurrency — highest regression risk of the three options for the lowest payoff at this scale.
- **Near-miss considered and set aside:** a module-level proxy forwarding to a thread-local connection (smallest possible diff). Rejected because this defect was caused by implicit sharing, and the fix should remove implicitness rather than add a cleverer layer of it.

## Scope and regression risk

**Files changed:** `registrar/app/main.py` (the bulk — remove the module-level globals, add lifespan migration and the dependency, thread the connection through ~14 routes and `identity()`), `registrar/app/db.py` (small — a context-manager/dependency helper). `service.py`, `auth.py`, `attestation.py`: no changes. `viewer/registrar_client.py` is a pure HTTP consumer, unaffected.

Roughly 50 lines, mechanical, no logic changes. Estimated half a day done carefully.

**Risks to rule on explicitly before implementation:**

1. **Write-path serialization is the invariant the whole risk profile rests on.** If any write route is converted from `async def` to `def` "for consistency," writers land in the threadpool and can contend for the SQLite write lock, raising `sqlite3.OperationalError: database is locked` — which `invoke()` does not currently catch, so it would surface as an unhandled 500. Do not do this. Recommended belt-and-braces: map `OperationalError` (locked/busy) to 503 in `invoke()`, matching the existing `Unavailable`→503 pattern.
2. **Behavior change: dirty reads become snapshot reads.** Today a read concurrent with an open write transaction can see uncommitted rows; after the fix, WAL gives readers a committed snapshot. Strictly more correct, no known consumer depends on the old behavior, but jackie-chan should rule on it explicitly rather than have it land unremarked.
3. **`/health/ready` semantics shift** from asserting PRAGMA posture on *the* connection to asserting it on *a* connection from the same factory — arguably more meaningful, but a semantic change to a liveness contract francis-ngannou may be alerting on.
4. **WAL file lifecycle:** when the last connection to a WAL database closes, SQLite checkpoints and tears down `-wal`/`-shm`. Per-request connections mean this happens repeatedly during idle moments. Harmless at this scale; mitigation if desired is to keep the startup/migration connection open for the process lifetime as a WAL pin — jackie-chan's call.
5. **Verifier nonce ordering must be preserved.** `attestation.verify` inserts into `verifier_nonces` in autocommit, before `verify_publication` opens its own transaction — two separate transactions today. Per-request injection keeps both on the same connection, preserving byte-identical replay semantics. Worth an explicit line here so a future change doesn't "tidy" this apart across connections.
6. **Out of scope, not a regression if left alone:** `promote_import` holds `BEGIN IMMEDIATE` across all imported rows on the event-loop thread, stalling every request (including health checks) for the duration. Pre-existing, unchanged by this fix, a separate conversation.
7. **Python version skew:** the Dockerfile pins `python:3.12-slim`; local dev has been observed on `cpython-314`. CPython's sqlite3 cursor/statement guarding has changed across versions, so concurrency behavior can differ between a local dev run and the NAS deployment. A green local concurrency run is not proof for the NAS — francis-ngannou/ronda-rousey should confirm on-container if this is ever load-tested.

## Ownership

- **Implement:** bruce-lee — API/app-wiring in `main.py` is his original lane; the change deliberately does not enter `service.py`.
- **Design sign-off and peer review:** jackie-chan — connection lifecycle, transaction boundaries, isolation semantics, and WAL posture are hers. Must rule explicitly on risks 2, 4, and 5 above, and confirm per-request connections preserve the `BEGIN IMMEDIATE` + `busy_timeout` invariants the WS3 write path depends on.
- **QA:** ronda-rousey — holds the repro; owns the new test category below.

## New regression test category needed

The existing suite would not catch a regression here even after a correct fix — it never loads `main.py` and gives every thread its own connection. Keep those tests (they remain valuable for file-level contention); add a new category built on the real topology:

1. HTTP-layer concurrency through the real app (`TestClient`/httpx + a thread pool, real bearer tokens) — already proven to reproduce the defect.
2. **Assert data correctness, not just absence of exceptions.** A full paginated walk under concurrent load must return exactly the expected set of `post_uid`s — no duplicates, no missing rows, no premature termination. A "no 5xx" assertion alone would have passed against the broken code roughly two-thirds of the time.
3. Mixed read/write: readers walking while a writer reserves and publishes; assert readers never observe an uncommitted row and never miss a committed one.
4. Structural tripwires (non-timing-dependent, so they don't pass flakily): assert two concurrent requests never share a `sqlite3.Connection` identity / no module-level connection is reachable from handlers; assert every write route remains a coroutine function (`inspect.iscoroutinefunction`), converting risk #1 above from a remembered invariant into an enforced one.
5. Explicit rule for the new test file: no test in this category may give a thread its own connection — doing so is what made the existing suite blind to this defect in the first place.

## Work order (held — not authorized to start)

```
- Trigger: Sensei prioritizes this. Nothing below starts before that.
- Document: this note, reviewed by jackie-chan — she must raise her own
  concerns and rule explicitly on risks 2 (dirty-read -> snapshot),
  4 (WAL pin) and 5 (verifier nonce transaction ordering) before any
  Implement line.
- Coordinate: helio-gracie — GAME PLAN after jackie-chan's review, before
  any Implement line; CHECKPOINT at every delivery handoff (implement,
  review, test); final CHECKPOINT + GATEWAY before Sensei sees crew output.
- Implement: bruce-lee — per-request connection dependency + lifespan
  migration in registrar/app/main.py; helper in registrar/app/db.py;
  OperationalError(locked/busy) -> 503 in invoke(). Zero changes to
  service.py, auth.py, attestation.py. Write routes stay `async def`.
- Peer review: jackie-chan — connection lifecycle and transaction
  semantics; confirm BEGIN IMMEDIATE + busy_timeout invariants and
  cursor-pagination correctness are unchanged.
- QA: ronda-rousey — new concurrency test category per above: real
  TestClient topology, data-correctness assertions (not just no-5xx),
  mixed read/write, and the two structural tripwires. Existing
  own-connection-per-thread tests stay, untouched.
- Done when:
  - Concurrent paginated walks return exactly the expected post_uid set
    -- no duplicates, no truncation, no spurious 403 on a valid token,
    no unhandled exceptions, across repeated trials.
  - Full existing suite green, including both WS3 concurrency tests.
  - Structural tripwires fail if the module-level singleton or a sync
    write route is reintroduced.
  - jackie-chan has signed off on the isolation-semantics change.
- Watch for:
  - Do NOT convert write routes to `def` -- introduces real write-lock
    contention where none exists today (risk #1).
  - promote_import blocking the event loop is pre-existing and out of
    scope; do not let it be "fixed" inside this change or reported as
    a regression.
  - Python 3.12 (container) vs local dev skew -- a green local
    concurrency run is not proof for the NAS deployment.
```
