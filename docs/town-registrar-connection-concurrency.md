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

## jackie-chan's review — connection lifecycle, transaction semantics, WAL posture (2026-09-22)

**Status: reviewed by reading the design note plus `main.py`, `db.py`, `service.py`,
`attestation.py`, `auth.py`, and `tests/test_registrar.py` directly — not taking any
of ip-man's correctness claims on trust. Sign-off given on risks 2, 4, 5 below. One
implementation requirement added that the note doesn't spell out (see "check_same_thread"
below) — read that before bruce-lee starts, it's a real footgun in FastAPI's threadpool
dispatch model, not a nitpick.**

### Ruling on Risk 2 — dirty reads become snapshot reads: endorsed, ship it

Confirmed mechanically, not just conceptually. `db.py`'s `connect()` uses
`isolation_level=None` (Python-level autocommit — SQLite, not the DBAPI2 module,
owns transaction boundaries) plus `journal_mode=WAL`. In WAL mode, any read that
isn't inside an explicit `BEGIN` runs as its own implicit read transaction and gets
a **consistent snapshot as of the last committed frame at the moment that statement
starts** — this is fundamental to how WAL readers work (they read committed pages
from the WAL/base-file merge, never in-progress writer pages), independent of
`BEGIN IMMEDIATE` on some other connection. A per-request connection issuing a plain
`SELECT` therefore cannot observe another connection's uncommitted `BEGIN IMMEDIATE`
work, full stop — there's no code path in this fix that could partially achieve
this, it's a property of the WAL engine itself once reads move off the shared
connection.

I agree with ip-man's characterization: this is strictly more correct than today's
dirty-read exposure, and I found no consumer in `service.py`, the viewer, or the
test suite that depends on a threadpool read observing an in-flight writer's
uncommitted rows (that would be a very strange thing to depend on, and nothing does).
**Ruling: approved, land it, no mitigation needed.**

### Ruling on Risk 4 — WAL file lifecycle: harmless, but decline the pin

Confirmed the mechanism: SQLite checkpoints (and can tear down `-wal`/`-shm`) when
the last connection to a WAL database closes, and per-request open/close means that
happens repeatedly during idle gaps. Agreed this is harmless at 1,070 rows and
home-LAN request volumes — cheap I/O, no correctness exposure, nothing here that
would show up as a problem in Francis's container metrics at this scale.

**My call on the mitigation: don't add the WAL pin.** Reasoning, since ip-man
explicitly left this to my judgment: a dedicated process-lifetime connection kept
open purely to pin the WAL file is the exact same *shape* of object that caused
this whole defect — a long-lived global connection sitting in `main.py` — just
inert instead of wired into request handling. That's an attractive nuisance: the
next time someone needs "a connection real quick" in a hot path or a script, that
pinned global is sitting right there, unused, looking reusable. ip-man's own
rejected-alternatives section makes this exact point about the thread-local-proxy
near-miss ("the fix should remove implicitness rather than add a cleverer layer of
it") — the same logic applies here. If NAS-side checkpoint I/O ever actually shows
up as a measured problem (it won't at this scale, but if it does), add the pin then,
as a targeted fix with a metric behind it, not preemptively. **Ruling: no pin,
close it out with a code comment in `get_db` noting the tradeoff was considered and
declined, so a future reader doesn't reinvent this debate.**

### Ruling on Risk 5 — verifier nonce transaction ordering: claim verified, holds — with one implementation condition

Read `attestation.py` and the `verify` route in `main.py` line by line rather than
taking the claim on faith, since this is exactly the kind of thing I'm here to catch.

- `verifier_nonces` has `PRIMARY KEY(key_id, nonce)` (migration `007_verifier_nonces.sql`)
  — replay protection is a SQLite-engine-enforced uniqueness constraint on a single
  `INSERT`, not something that depends on transaction wrapping at all.
- `attestation.verify()`'s `db.execute("INSERT INTO verifier_nonces ...")` runs with
  no open `BEGIN` on the connection at that point — under `isolation_level=None`
  that's an implicit, immediately-committed autocommit transaction. This is
  transaction #1, and it is durable the instant that call returns.
- The `verify` route (`main.py`) calls `verify_attestation(db, ...)` and *then*,
  strictly sequentially in the same Python call, `service.verify_publication(...)`,
  whose `idem()` opens `BEGIN IMMEDIATE` — transaction #2 — and commits at the end.
- **Today**, both calls already run on the one module-global `db` — `service` is
  constructed once at import time from the same object `verify_attestation` closes
  over. So the "two transactions on one connection, in this order" property ip-man
  describes as the target state is, mechanically, *already true today* — the shared-
  connection defect that motivates this whole fix is a read-path/thread problem, not
  a write-ordering problem. The nonce-then-verify ordering was never at risk from
  concurrency in the first place, because writes have always been serialized on the
  event loop.
- **After the fix**, the same two calls need to run against the same per-request
  connection instance for the "one connection, sequential transactions" framing to
  hold literally, not just functionally. This is where I'll add a condition: this
  is only automatically true if `bruce-lee`'s route signature resolves the injected
  connection **once** (a single `Depends(get_db)` parameter) and threads that same
  object into both `verify_attestation(conn, ...)` and `Registrar(conn)`. I checked
  FastAPI's dependency resolution behavior: `Depends()` caches by default per request
  (`use_cache=True`), so even if the route ends up with the dependency referenced in
  two places, it resolves to the identical connection object within one request —
  this is *not* fragile by accident, but it does mean nobody should add
  `use_cache=False` anywhere near `get_db`. Flagging this explicitly rather than
  leaving it implicit, per the same philosophy as the rest of this note.
- Independent of connection identity, I also checked whether the ordering guarantee
  would survive even if a future change *did* split these onto two different
  connections: it would, because the nonce insert is autocommitted and durable
  before `verify_publication` is ever called (strictly sequential Python code, not
  concurrent), so a second connection would still only ever see it as already
  committed. That's a weaker, incidental guarantee though — the design's "one
  connection" approach is the right one to keep, not something to relax later.

**Ruling: claim confirmed correct, both as stated and mechanically verified against
the actual code. Approved, with the single-`Depends`/no-`use_cache=False` condition
above stated explicitly for bruce-lee's implementation, not left to be inferred.**

### Endorsement: per-request connection is the right fix — confirmed, not just deferred to

This is squarely my lane, so I read the rejected alternatives with real skepticism
before agreeing.

- **Lock-based fix, rejected — I checked the count and it's actually worse than
  stated.** I independently counted direct `db.execute`/`db` usage in `main.py`
  outside `Registrar`: `ready()`, `get_root()`, `get_post()`, `assignments()`,
  `reconciliation()` — five route handlers, matching ip-man's count — plus
  `identity()` → `auth.authenticate_identity(db, ...)` and the `verify` route →
  `attestation.verify(db, ...)`. That's seven call sites total touching the
  connection outside `Registrar`, not five. A `Registrar`-scoped lock leaves the bug
  live on the auth path specifically (`authenticate_identity`), which is precisely
  where ronda-rousey's earlier testing saw a spurious 403 on a valid token. A
  connection-scoped lock fixes that but serializes every read behind a mutex,
  discarding WAL's reader concurrency for a workload (home-LAN, ~1,070 rows) where
  that concurrency is free. Rejection stands, and is better-supported than the note
  states.
- **`aiosqlite` rewrite, rejected — accurate characterization, I confirm it.**
  `aiosqlite` is implemented as one dedicated background thread per connection
  processing a request queue; wrapping calls in `await` buys non-blocking
  scheduling, not actual parallelism, since everything still funnels through that
  one thread per connection. Forcing `idem()` and `promote_import()` — the two
  functions with the most invariant-carrying transaction logic in the repo — to
  become `async def` for that payoff is a bad trade. Confirmed, rejection stands.
- **Topology is already proven, not just architecturally plausible.** I read
  `test_concurrent_root_allocation` and `test_concurrent_children_and_publication`
  directly: 100 threads, each opening its own `connect(self.path)` and its own
  `Registrar`, hammering `reserve_root`/`reserve_post` concurrently, closing in
  `finally`. That is *exactly* the per-request connection topology this fix moves
  production into — same `connect()` factory, same PRAGMAs (`foreign_keys=ON`,
  `journal_mode=WAL`, `synchronous=FULL`, `busy_timeout=5000` — all four are
  re-applied by `connect()` on every call, so per-request connections don't need any
  extra PRAGMA setup beyond what `db.py` already does), same `BEGIN IMMEDIATE` write
  pattern. Zero flakiness reported in this suite. Ip-man's framing that this "inverts
  the usual risk calculus" is correct and I'd put it more strongly: production today
  runs a *worse-tested* configuration (single shared connection) than the one this
  fix adopts (already exercised at 100-way concurrency in the test suite).

**Ruling: endorsed, no changes to the approach. Confirm `BEGIN IMMEDIATE` +
`busy_timeout=5000` invariants are unchanged — verified directly, `idem()` and
`promote_import()` are untouched by this fix (ip-man's note is correct that
`service.py` needs zero changes), so those invariants carry over exactly.**

### Additional finding not in the original note: `check_same_thread=False` must be kept, and the reason is specific to FastAPI, not general caution

This is the one place I'd push back on treating the note as complete — it doesn't
mention `check_same_thread` at all, and I think it needs to be explicit before
bruce-lee writes code, because the wrong instinct here is easy to reach for and
looks like a safety improvement when it's actually a regression.

A per-request connection, used by exactly one request at a time, looks like it
should be safe to open with the *default* `check_same_thread=True` — tightening
Python's own guard as defense in depth, since "one connection, one request" sounds
like "one connection, one thread." **It isn't, under FastAPI's dispatch model.** A
sync (`def`, not `async def`) `yield`-based dependency like the proposed `get_db`
has its setup (up to `yield`), and its teardown (after `yield`, running `close()` in
`finally`), each individually wrapped in their own `run_in_threadpool` call by
FastAPI/Starlette — and the sync route body itself is a *third* separate
`run_in_threadpool` call. AnyIO's threadpool does not guarantee thread affinity
across separate `run_in_threadpool` invocations; each can land on a different
worker thread from the pool. So a per-request connection can legitimately be
*opened* on thread A, *queried* on thread B, and *closed* on thread C, within the
lifetime of one HTTP request — never concurrently, always sequentially handed off,
but never guaranteed same-thread either. This is almost certainly why `db.py`
already sets `check_same_thread=False` unconditionally today, since the exact same
cross-thread handoff already happens to the shared module-global connection on
every sync route today.

This is not a re-opening of the concurrency question: `check_same_thread=False`
only disables Python's *thread-identity* guard, it does not make a connection safe
for simultaneous multi-thread use — and per-request connections are never used
simultaneously by more than one thread, so there's nothing unsafe here. It's purely
that the guard would produce false-positive `ProgrammingError`s on legitimate
sequential handoff if left at the default. **Ruling: `connect()` in `db.py` keeps
`check_same_thread=False` exactly as-is — no code change needed there, but this
needs to be a documented, intentional invariant (one line in `get_db`'s docstring
pointing at this section) rather than something that survives by accident and gets
"corrected" by a future reader who doesn't know why it's there.**

### What must be true before bruce-lee starts (in addition to ip-man's work order)

1. Risks 2, 4, 5 ruled on above — all clear, no design changes required.
2. Per-request connection endorsed as the fix approach — no alternative recommended.
3. The `verify` route must resolve the connection dependency once and pass that
   same object to both `verify_attestation()` and `Registrar()` — true by default
   under FastAPI's dependency caching, but nobody should add `use_cache=False`
   anywhere near `get_db`.
4. `get_db`'s `connect()` call keeps `check_same_thread=False` — document why (cross-
   thread handoff across FastAPI's setup/body/teardown phases for sync dependencies),
   don't tighten it.
5. No WAL pin. If checkpoint I/O is ever observed as an actual problem on the NAS,
   revisit with a metric, not preemptively.
6. Confirmed no route returns a lazily-iterated `sqlite3.Cursor`/generator past the
   response boundary — I checked `posts()`, `aliases()`, `assignments()`, and
   `reconciliation()`; all materialize rows into lists/dicts synchronously before
   returning. This must stay true after the fix — a lazily-streamed row generator
   handed to FastAPI's response serializer would run after `get_db`'s `finally:
   conn.close()` has already fired, and would fail or return truncated data. Not a
   change ip-man's plan makes, just a property worth protecting explicitly since
   it's exactly the kind of thing a "small, mechanical, ~50 line" diff can
   accidentally disturb.

No further concerns. Design sign-off given — helio-gracie can proceed to a GAME PLAN.
