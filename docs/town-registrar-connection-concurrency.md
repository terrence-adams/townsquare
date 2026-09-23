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
- **No test exercises `main.py` under concurrency.** *[Corrected 2026-09-22 — the original text read "The test suite cannot see `main.py` at all." That was true of `test_registrar.py` only, the one test file I had read. See Addendum A0.]* `tests/test_registrar.py` builds `Registrar(self.db)` directly and gives each concurrency-test thread its own connection, so it has zero coverage of the wiring where the defect actually lives. `tests/test_http.py` *does* import `registrar.app.main` and drive `TestClient(main_module.app)`, but only for single-threaded cursor/key regression cases — so it would not catch a regression here either. It is also a direct consumer of the module globals this fix deletes; see Addendum A.
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

Decisive point: the multi-connection topology is the one the test suite *already* proves. `test_concurrent_root_allocation`/`test_concurrent_children_and_publication` run 100 threads with independent connections and pass. This fix moves production *into* the configuration already battle-tested since WS3, not out of it — inverting the usual risk calculus. *[Corrected 2026-09-22 — these two tests do not reliably pass; see jackie-chan's correction near the end of this note. The multi-connection *read* topology this fix actually adopts for production is not what these tests exercise regardless — see the same correction for why the core recommendation is unaffected.]*

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

The existing suite would not catch a regression here even after a correct fix — `test_registrar.py` gives every thread its own connection, and `test_http.py`, which *does* load `main.py`, is entirely single-threaded. *[Corrected 2026-09-22 — the original text read "it never loads `main.py`." See Addendum A0.]* Keep those tests (they remain valuable for file-level contention); add a new category built on the real topology, reusing `test_http.py`'s boot harness — see Addendum A3:

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
  pattern. Zero flakiness reported in this suite. *[Corrected 2026-09-22 — wrong; these
  tests fail at high, reproducible rates on this machine. See jackie-chan's correction
  near the end of this note — this claim should not have been made as worded, and the
  session had direct disconfirming evidence in hand before ronda-rousey surfaced it.]*
  Ip-man's framing that this "inverts
  the usual risk calculus" is correct and I'd put it more strongly: production today
  runs a *worse-tested* configuration (single shared connection) than the one this
  fix adopts (already exercised at 100-way concurrency in the test suite). *[Same
  correction applies — see below.]*

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

## Addendum A — `test_http.py` ownership and the startup-work split (ip-man, 2026-09-22)

helio-gracie's GAME PLAN routed three items back to me as scope calls under D·D·D rather than
deciding them himself. Ruling below. This does not reopen jackie-chan's review; two of the three
items *reduce* scope.

### A0. Correction to this note: the "suite cannot see `main.py`" claim was wrong

I asserted twice that the test suite never loads `main.py`, citing `tests/test_registrar.py`.
That file does build `Registrar(self.db)` directly and never imports `main.py` — but it is not
the whole suite. `tests/test_http.py`, added in the same cursor-pagination review pass that
surfaced this concurrency bug, imports `registrar.app.main` and builds
`TestClient(main_module.app)`. Both sites are corrected in place above; this addendum is the
authority.

Two consequences I got wrong as a result:

1. **The blindness is narrower than I described, and the starting position is better.** The suite
   is not blind to `main.py`; it is blind to `main.py` *under concurrency*. The new test category
   below is still needed for exactly the reason given, and the structural tripwires in item 4 are
   still the right idea — but it now has a working HTTP-layer harness to build on rather than
   starting from nothing.
2. **`test_http.py` is a consumer of the globals this fix deletes**, at two sites in
   `_FreshAppCase`: `self.addCleanup(main_module.db.close)` in `_boot`, and
   `auth.create_token(main_module.db, ...)` in `_bearer`. Both break the moment `main.py`'s
   module-level `db`/`service` are removed. My "Files changed" line was therefore incomplete;
   corrected in A4.

Lesson worth keeping: I asserted a *negative* about a test suite ("it cannot see X") from a
single file read. A negative claim about a suite needs a directory listing, not one file.
helio-gracie's catch.

### A1. Decision: migration stays at import time. Do NOT introduce `lifespan` in this change.

This item decides the other two, so it comes first.

The recommendation above ("Migration moves to app startup (lifespan)") is **withdrawn**. Replace
it with a dedicated boot connection at module level, closed immediately:

    DB_PATH=os.environ.get("REGISTRAR_DB","/data/registrar.db")
    _boot=connect(DB_PATH); migrate(_boot); _boot.close()

Reasoning — why this is right, not merely convenient:

1. **A split startup is worse than either pure option.** `main.py` already performs two startup
   gates as import-time side effects: `ensure_runtime_mode()` (line 9) and
   `ensure_cursor_signing_key_at_startup()` (line 92). Moving *only* migration into `lifespan`
   leaves the app with two startup mechanisms and no rule governing which work goes where. The
   next person adding a startup check has to guess.

2. **`lifespan` would churn gsp's security regression tests, by mechanism, for no correctness
   gain.** Starlette runs the lifespan protocol only inside `TestClient.__enter__`; a bare
   `TestClient(app)` invokes the ASGI app with an `http` scope and never fires startup.
   helio-gracie flagged this as inferred-not-measured — it is correct, and I am ruling on it
   rather than leaving it to be measured, because the ruling is to not go there. Under
   full-lifespan, `CursorSigningKeyStartupProbeTests` stops working as written: two of its four
   tests assert `RuntimeError` escapes `self._boot(...)`, i.e. escapes the *import*. Under
   lifespan that error surfaces only at `with TestClient(app)`, so all four need restructuring.
   Rewriting the security regression tests that exist *because a bug got past a first review
   round* as collateral of an unrelated concurrency fix is exactly the blast-radius creep this
   note is supposed to prevent.

3. **It does not weaken the fix.** The defect is the *shared, long-lived, request-serving*
   connection. A migration connection opened before any request can arrive, used single-threaded,
   and closed on the same line is not that object. `migrate()` is already idempotent (it checks
   `schema_migrations`), and it takes `BEGIN EXCLUSIVE` — both fine at import, neither safe to
   leave racing under a lifespan started per worker. Consistent with jackie-chan's Risk 4 ruling:
   the boot connection closes, it does not linger as a WAL pin.

4. **It shrinks the diff** in `main.py`, and reduces the `test_http.py` delta from a harness
   rewrite to roughly five lines.

**Accepted trade-off, stated so nobody rediscovers it as a finding:** DDL still runs as an import
side effect, so `import registrar.app.main` still writes to disk. That is pre-existing, it is this
module's established convention, and it is worth fixing — as its own change, moving *all three*
startup gates into `lifespan` together with the matching harness rewrite, designed and reviewed on
its own merits. All-or-nothing, never a split. Not smuggled in here. Raise it after this ships.

**Routing:** this amends a line in a note jackie-chan reviewed. It touches none of her rulings
(Risks 2, 4, 5) and none of her four implementation conditions (single `Depends`, no
`use_cache=False` near `get_db`, keep `check_same_thread=False`, no lazily-iterated cursor past
the response boundary), and it strictly reduces scope. **Notify, do not re-gate:** helio-gracie
sends her this addendum, bruce-lee proceeds now, and if she objects it comes back to me — not to
bruce-lee mid-change.

### A2. Ownership of `test_http.py`: bruce-lee, inside the implementation change

Three reasons:

- **Removing a symbol and leaving its consumer broken is not "done."** The `main_module.db`
  references in `_boot` and `_bearer` are not test *design* — they are wiring to a global
  bruce-lee is deleting. Repairing a consumer of a deleted global belongs to the commit that
  deletes it. Any other split leaves `internal` red across a handoff, where nobody can tell a real
  failure from known-broken scaffolding.
- **It is small.** Under A1 the delta is: drop `addCleanup(main_module.db.close)` (there is no
  module-global to close; `main.py` closes its own boot connection before import returns), and
  give `_bearer` its own short-lived connection — `auth.create_token(db, principal, scopes)`
  accepts any connection, so it opens `connect(os.environ["REGISTRAR_DB"])`, mints the token, and
  closes in a `finally` (the Windows lock applies to this connection too). That is not a QA
  workstream.
- **QA independence.** ronda-rousey must not be the person who makes the implementer's change go
  green. Her job is to find what he missed; owning the repair of his breakage compromises that —
  the same reason implementers do not write their own peer review.

**Hard constraint, and this is the part that matters: bruce-lee adapts the harness only. He may
not change, weaken, skip, `expectedFailure`, or delete a single assertion in `test_http.py`.**
Every existing test must still assert exactly what it asserts today. The four
`CursorSigningKeyStartupProbeTests` and the three `MalformedCursorRejectionTests` are gsp's and
ronda-rousey's regression coverage for F1/F2/F4; they are not his to trim. If he concludes an
assertion *must* change, that is a deviation — stop, route through helio-gracie to me. Not a
judgment call at the keyboard.

Two riders:

- **Comments and docstrings that describe deleted mechanics must be updated** — `_FreshAppCase`'s
  docstring ("main.py's module-level `db=connect(...)` is otherwise process-global"), and the
  `_boot` NOTE block about an orphaned connection kept alive by a traceback. Those describe
  behavior that will no longer exist. Updating prose is required; it is not an assertion change.
- **Do not delete the `gc.collect()` calls or the Windows file-lock commentary**, even if A1
  makes them unnecessary. They are harmless, and removing them discards hard-won platform
  knowledge for no gain. Separate cleanup, if ever.

ronda-rousey reviews the harness diff as part of her QA pass and holds a **veto on any
assertion-semantics change**. jackie-chan's peer review stays scoped to connection lifecycle and
transaction semantics; the test harness is not her lane.

### A3. New concurrency tests: separate file, shared harness — extract it

**Separate file: `registrar/tests/test_http_concurrency.py`. Do not grow `test_http.py`.**

- Different purpose, different runtime profile. `test_http.py` is fast, deterministic regression
  coverage for named security findings. Concurrency tests run thread pools over repeated trials:
  slow, and — however carefully written — the file most likely to be quarantined if it ever goes
  flaky. Same file means nobody can run gsp's F1/F2/F4 guards without paying for the concurrency
  run, and a quarantine of one takes out the other.
- Concrete collision risk right now: bruce-lee is editing `_FreshAppCase` in the same window
  ronda-rousey is writing tests. Separate files means no conflict and no serialization between
  them.
- Item 5 of the test-category list above ("no test in this category may give a thread its own
  connection") is a **file-scoped rule**. It needs a file to scope to. It is false for
  `test_registrar.py` by design, and irrelevant to `test_http.py`'s existing single-threaded
  tests.

**Extract the harness rather than importing a private class across test modules.** Move
`_FreshAppCase` from `test_http.py` to a new `registrar/tests/app_harness.py` as `FreshAppCase`
(`registrar/tests/__init__.py` exists, so `from registrar.tests.app_harness import FreshAppCase`
resolves), and have `test_http.py` import it.

- **bruce-lee does the move**, in the same pass — he is already rewriting those exact lines, so it
  is one edit instead of two, and ronda-rousey builds on a stable base instead of rebasing onto
  his change mid-flight.
- **Move only.** No behavior change beyond the two `main_module.db` repairs in A2. The env
  save/restore, the per-test temp DB, the `sys.modules.pop` + fresh re-import, and the LIFO
  `addCleanup` ordering that solves the Windows open-file lock are all load-bearing. They move
  byte-for-byte.
- ronda-rousey may add concurrency-only helpers (seeding, thread-pool runner, trial loop) to
  `app_harness.py` or keep them in her own file — her call. She may **not** change `FreshAppCase`'s
  existing behavior without coming back through helio-gracie, since `test_http.py` depends on it.

helio-gracie's read that the harness is "also an asset" is correct and is the deciding factor: it
already solved fresh-boot env isolation and the Windows open-file lock, both of which
ronda-rousey would otherwise rediscover the hard way.

### A4. Corrected scope (supersedes the "Files changed" line above)

bruce-lee's implementation:

- `registrar/app/main.py` — the bulk (remove module-level `db`/`service`, boot-connect/migrate/
  close, `get_db` dependency, thread the connection through ~14 routes and `identity()`,
  `OperationalError`→503 in `invoke()`)
- `registrar/app/db.py` — small context-manager/dependency helper
- `registrar/tests/app_harness.py` — **NEW**; `_FreshAppCase` moved out of `test_http.py`, plus
  the two `main_module.db` repairs
- `registrar/tests/test_http.py` — import line, plus the stale comments named in A2. **No
  assertion changes.**
- Unchanged: `service.py`, `auth.py`, `attestation.py`, `test_registrar.py`,
  `viewer/registrar_client.py`

ronda-rousey's QA: `registrar/tests/test_http_concurrency.py` (new), optionally concurrency-only
additions to `app_harness.py`.

### A5. Added to "Done when"

- `registrar/tests/test_http.py` passes with every assertion it has today, unmodified, against the
  new wiring.
- No file in the repo references `registrar.app.main.db` or `registrar.app.main.service` as
  module attributes.
- No `lifespan=` / `@app.on_event` handler was added to `main.py` (A1).

## jackie-chan's checkpoint review — Issues 1-3, coverage-gap ruling, Addendum A sign-off (2026-09-22)

**Status: reviewed `cfa7ecd` (parent `fe6d953`) directly with `git show`/`git diff`, re-read
`main.py`, `db.py`, `auth.py`, `service.py`, `attestation.py` at their current state (not from
memory of my first pass), and independently verified two technical claims by running code rather
than trusting them (see below). helio-gracie routed three issues to me plus a checkpoint list;
rulings below. Nothing here reopens my original Risk 2/4/5 sign-offs — Issue 1 corrects a premise
in Risk 5's supporting reasoning, not its conclusion (see Issue 1).**

### Work-order line, confirmed directly: BEGIN IMMEDIATE / busy_timeout / cursor-pagination unchanged

- `git diff fe6d953 cfa7ecd -- registrar/app/service.py registrar/app/auth.py
  registrar/app/attestation.py` is empty — byte-identical, exactly as the commit message claims.
  `idem()` (service.py:98) and `promote_import()` (service.py:230) still open `BEGIN IMMEDIATE` on
  `self.db`; `Registrar.posts()` (the cursor-pagination method) is untouched.
- `db.py`'s `connect()` still applies all four PRAGMAs, `busy_timeout=5000` last, on every call —
  the only change is that `connect()` (via the new `session()` context manager) now runs once per
  request instead of once per process. That is not a change to the invariant, it's the invariant
  being enforced more consistently: previously it was set once on the one long-lived connection;
  now every connection any code path opens gets it, including per-request connections that did not
  exist before.
- All six write routes (`reserve_root`, `reserve_post`, `publish`, `verify`, `import_run`,
  `promote`) are still `async def`; all seven read routes plus `ready` are still plain `def`
  (`grep -n "async def\|^def "` against the current file). Risk #1's invariant — writers stay off
  the threadpool — holds.
- `Registrar(db)` is constructed against the connection resolved by exactly one
  `Depends(get_db)` parameter per route (checked every route signature); the `verify` route threads
  that same object into both `verify_attestation(db,...)` and `Registrar(db)`, preserving the
  nonce-then-verify transaction ordering on one connection, per my condition in the first review.
- **Confirmed: no regression on any of these. Ruling stands as originally given.**

One caveat stated plainly: this is a *static* re-verification — I read the diff and the code, I did
not run a concurrency test myself. I am not treating bruce-lee's 8x15 smoke test (run from an
uncommitted, now-discarded scratchpad — no durable evidence in the repo) as proof the original
corruption is fixed. That proof is explicitly ronda-rousey's work-order line, not mine, and my
sign-off below does not stand in for it.

### Issue 1 — `identity()`'s embedded write, and a correction to my own Risk 5 reasoning

Confirmed at `auth.py:25`: `authenticate()` ends with an autocommit
`UPDATE tokens SET last_used_at=? WHERE token_id=?` on every successful authentication, read or
write route alike — `identity()` (`main.py:65`) is called as a bare statement at the top of 12 of
the 13 DB-touching routes, *separately from and before* any `invoke(...)` call, including in the
six write routes. *[Corrected 2026-09-22 — the original text read "all 13," but `ready` is
DB-touching (it takes `db` via `Depends(get_db)`) and never calls `identity()`, since it has no
`authorization` parameter and is a liveness-adjacent check, not an authenticated route. 12 of the
13 is the accurate count; caught by helio-gracie's independent re-derivation, re-verified directly
against `main.py` rather than taken on trust.]* `identity()`'s own `try/except` catches only
`Forbidden`; nothing catches
`sqlite3.OperationalError` there, and no route wraps its `identity(...)` call in `invoke()`. If that
UPDATE loses the busy-lock race, it is an unhandled 500, confirmed by reading the code, not
inferred.

**Correction to my own Risk 5 ruling, not just a new finding.** My first-pass text says "writes have
always been serialized on the event loop" as a blanket premise. That statement is accurate for the
six enumerated write *routes* (their own internal transactions genuinely never contended, because
those routes are `async def`) but I stated it more broadly than the evidence supported — I did not
separately audit every `db.execute` call in the codebase for which thread class runs it, only the
route-level `async def`/`def` split the design note itself enumerated. `authenticate()`'s UPDATE is
a write that has *never* been event-loop-serialized: it runs inside `identity()`, called from all
seven plain-`def` read routes too, so under the OLD shared-connection design it already ran
concurrently, from multiple threadpool threads, on the ONE shared connection — i.e. it was already
exposed to the exact LRU-statement-cache-aliasing hazard that produced ronda-rousey's corruption
numbers, just never specifically isolated as its own finding (a 1-row UPDATE with no read-back has
no consumer-visible corruption signature the way a paginated SELECT does, so it could have been
misfiring silently and nobody would see it in the response body).

**What changes for THIS write, specifically, from old to new design:** old design — shared-cache
corruption hazard, present but unmeasured; new design — that hazard is fully eliminated (own
connection, own statement cache), but real SQLite single-writer lock contention is introduced in its
place, and it is uncaught on this specific path. My Risk 5 *conclusion* (verifier-nonce ordering
survives the fix) is unaffected — the `verify` route is genuinely `async def`, so that specific pair
of writes stays event-loop-serialized exactly as I described. What's corrected is the *general*
premise text, which I should not have stated without the caveat "for the six named write routes
specifically."

**Is the contention risk hypothetical? No — the design note already documents the exact collision
window.** Risk 6 (endorsed, out of scope) states `promote_import` holds `BEGIN IMMEDIATE` across all
imported rows on the event-loop thread, "stalling every request (including health checks) for the
duration." Any GET request already dispatched to the threadpool *before* that block begins continues
running on its own OS thread in parallel — threadpool dispatch is real OS-thread parallelism, it
does not stop just because the event loop can't schedule anything new. That in-flight GET's
`identity()` UPDATE then contends for SQLite's single writer lock against `promote_import`'s
long-held transaction, for however long the import batch takes — plausibly longer than
`busy_timeout=5000` for anything beyond a handful of rows. This is the accepted, already-documented
Risk 6 scenario colliding with the newly-per-connection auth write, not a new abstract worry.

**Ruling: not acceptable as-is.** I am not persuaded by the 8x15 smoke test (evidence-gap caveat
above applies) and the promote_import collision window is a real, already-accepted condition of this
system, not a hypothetical. Of the three options offered, I rule for the third, generalized: **move
exception-to-HTTP-status mapping out of `invoke()`'s per-call-site convention and into FastAPI
app-level exception handlers** (`@app.exception_handler(Conflict)`, `Forbidden`, `Invalid`,
`Unavailable`, and `sqlite3.OperationalError` with the same locked/busy string discrimination
`invoke()` uses today). I verified this mechanism works for exactly this failure mode before ruling
on it, rather than assuming FastAPI semantics: a probe against this repo's installed versions
(fastapi 0.116.1 / starlette 0.47.3) confirms an app-level exception handler catches an exception
raised *inside a `Depends()` dependency before `yield`* — status 503 came back for both a
dependency-raised and a route-body-raised instance of the same custom exception type, via a bare
`TestClient(app)` with no `with` block (so this does not depend on, or reopen, Addendum A1's
lifespan-vs-import-time decision — exception handlers are unrelated to the lifespan protocol A1
declined). Scratch probe kept at
`C:\Users\terre\AppData\Local\Temp\claude\...\scratchpad\exc_handler_probe.py` for reproducibility,
not committed (throwaway, not part of the suite).

This closes Issue 1 (identity()'s UPDATE, at all 12 call sites, uniformly) and Issue 2 (below) with
the same mechanism, which is why I'm ruling for the general form rather than patching
`sqlite3.OperationalError` alone: patching only the one exception type asked about in Issue 1 while
leaving `Conflict`/`Forbidden`/`Invalid`/`Unavailable` on the old per-call-site convention would
create exactly the kind of split invariant ip-man's own A1 reasoning warns against ("a split startup
is worse than either pure option") — here, a split *error-mapping* posture, structural for one
exception type and convention-remembered for four others, is worse than either "all convention" or
"all structural." Once the app-level mechanism exists for one exception type, extending it to all
five costs nothing extra and removes the remembered-per-call-site burden entirely.

**Implementation note, not mine to make (routes to bruce-lee via helio-gracie, not made here):**
`invoke()`'s lambda-wrapping becomes redundant once handlers are structural; I'd expect `invoke()`
to shrink to nothing or be deleted with call sites simplified to direct calls, but that shape
decision belongs to whoever implements it. `identity()`'s own `HTTPException(401,...)` for a
missing/malformed bearer header stays exactly as-is — that's an input-validation guard clause with
no underlying service exception to map, not something the new handlers touch.

### Issue 2 — coverage-gap count and the busy_timeout/PRAGMA-ordering claim

**My own audit, independent of both bruce-lee's and helio-gracie's counts:** grepping every route
and reading each body, I count exactly **six** route/handler-level surfaces where a `db.execute` or
service call runs outside `invoke()`: `get_root`, `get_post`, `assignments`, `reconciliation`
(bruce-lee's original four, confirmed) plus `aliases` (`Registrar(db).aliases(alias)` called bare)
and `ready` (three direct PRAGMA/schema_migrations calls). That matches helio-gracie's "six, not
four" exactly once `get_db` is read as a *separate*, more severe finding rather than a seventh item
in the same list — which is how I read it too: `get_db`'s `connect()` call happens during dependency
resolution, before any route body runs, for all 13 DB-touching routes at once. It's not route-level
at all, it's upstream of every route, so folding it into a route-count would understate it, not
overstate it. Between the six route-level surfaces, `get_db`, and `identity()`'s embedded write
(Issue 1, a distinct angle — not a `db.execute` in a route body, a write buried in an auth
helper), there are eight things I can point to, and none of them overlap. I'm stating my own count
explicitly rather than restating "six" uncritically, per this doc's own established norm (Addendum
A0: a negative/count claim needs a directory listing, not a restatement).

One precision on `aliases` specifically: `Registrar.aliases()` does not currently raise `Invalid`
or `Conflict` — I read it, it's a bare `SELECT` with no validation branch. So the specific "service-
layer Invalid/Conflict escapes as 500" scenario named for `aliases` isn't reachable *today*. It's
still correctly flagged: (a) `OperationalError` could still hit that `db.execute` and escape as 500
regardless, and (b) it's a live trap for the next person who adds a validation branch to `aliases()`
with nothing forcing them to remember the `invoke()` convention.

**Technical claim, independently verified rather than accepted:** confirmed by direct test against
this repo's Python/sqlite3, not read from documentation —
`sqlite3.connect(path, timeout=5)` sets the C-level busy handler to 5000ms *at connection-open time*,
before any Python-level statement executes:

    >>> sqlite3.connect(':memory:', timeout=5).execute('PRAGMA busy_timeout').fetchone()
    (5000,)

confirmed immediately after `connect()`, with no PRAGMA statement issued yet. So `db.py`'s first
three PRAGMAs (`foreign_keys`, `journal_mode=WAL`, `synchronous`) all run under an already-active
5-second busy handler; the explicit fourth `PRAGMA busy_timeout=5000` is redundant in effect (same
value) but not harmful, and it's useful self-documentation plus a safety net if someone changes the
`timeout=5` kwarg without noticing it's paired with the literal `5000` in the PRAGMA string, or vice
versa — those two now encode the same 5-second value in two places with nothing enforcing they stay
in sync. **Minor finding, not blocking:** worth a one-line comment in `db.py`'s `connect()` noting
the pairing (`timeout=5` seconds == `PRAGMA busy_timeout=5000` ms, keep them equal), so a future
change to one doesn't silently orphan the other. Small, non-blocking, bruce-lee's call whether to
fold it into the same pass as the exception-handler change.

**Ruling on scope: not acceptable as originally scoped, widen it.** The work order asked for the
mapping "in `invoke()`," and what's built matches that literally — but "in `invoke()`" was always
shorthand for "every exception a DB-touching code path can raise gets mapped correctly," and the
actual surface (eight distinct gaps, not the four originally scoped) is bigger than that shorthand
covered. Same ruling and same mechanism as Issue 1: app-level exception handlers close this
uniformly, covering `ready`/`get_root`/`get_post`/`aliases`/`assignments`/`reconciliation` and
`get_db` itself in one change, rather than hand-patching six-plus call sites and hoping the next
addition remembers the convention.

### Issue 3 — module-level `_boot`: ruling for `del _boot`, routed to ip-man per A1's own precedent

Confirmed at `main.py:28`: `_boot=connect(DB_PATH); migrate(_boot); _boot.close()`. `_boot` remains
bound at module scope after import — a closed, inert `sqlite3.Connection` object, and grepped: not
referenced anywhere else in `main.py` (the `_boot` hits in `app_harness.py`/`test_http.py` are an
unrelated test-harness *method* name on a different class, not this module global — no collision).

**Ruling: (b) — `main.py` should `del _boot` immediately after `.close()`.** Reasoning, mirroring
the logic I already used for my own WAL-pin ruling and A1's "attractive nuisance" framing for the
same reason: a closed connection sitting at module scope is the same *shape* of object that caused
this entire defect, just currently inert. "Closed, so it's harmless" is exactly the kind of
invariant that survives by accident today and breaks tomorrow — a future edit that adds a line before
`.close()`, or reopens `_boot` for "a quick fix," or drops the `.close()` call in a refactor while
leaving the name, would silently reintroduce the leaked-global topology this whole fix removes, and
nothing would flag it as a regression because the name was already sitting there looking normal.
`del _boot` costs one line and makes the test-category item 4 spec ("no module-level connection is
reachable from handlers") literally, unconditionally true instead of true-with-a-footnote that a
future reader has to independently know and keep in sync with the code. It lets ronda-rousey write
the structural tripwire as a plain assertion instead of one carrying an unexplained special case.

**Routing, not deciding unilaterally:** this changes one line of ip-man's literal Addendum A1
snippet. Per A1's own rule ("this amends a line in a note jackie-chan reviewed... Notify, do not
re-gate"), I'm applying the same precedent in the direction it wasn't originally written for: this
is a one-line, purely additive change on top of A1's snippet, touches none of A1's actual reasoning
(the boot-connection-instead-of-lifespan decision, the split-startup argument, the
`TestClient.__enter__` point are all untouched), and strictly tightens an invariant rather than
loosening one. **Notify, do not re-gate: helio-gracie sends ip-man this ruling, bruce-lee proceeds
with `del _boot` now, and if ip-man objects it comes back to her, not to bruce-lee mid-change** —
same shape as A1 itself, applied symmetrically.

### Also flagged by helio-gracie — my confirmation

- **13 of 14 routes thread the connection, not all 14 — confirmed correct behavior, not an
  oversight.** Grepped every route: `/health/live` has no `Depends(get_db)` parameter and touches
  nothing DB-related. A liveness probe that touches the DB collapses the live/ready distinction this
  app already deliberately maintains (my own Risk 3 in the first review flagged `/health/ready`'s
  semantics as a liveness-adjacent contract worth being careful with — this is the same care applied
  correctly on the live side). Agreed, not a defect.
- **Evidence gap — agreed, and my sign-off above does not treat the concurrency claim as proven
  in-repo.** Stated explicitly in the BEGIN IMMEDIATE/busy_timeout confirmation section above: this
  was a static re-verification, not a dynamic one. That proof is ronda-rousey's work-order line.

### Addendum A — no objection, written down

I gave this verbally when notified; recording it here as the doc of record. I have no objection to
Addendum A0-A5 (ip-man, 2026-09-22): the correction to the "test suite can't see `main.py`" claim,
the decision to keep migration at import time on a closed boot connection rather than introduce
`lifespan` (A1), the `test_http.py` ownership assignment to bruce-lee with the hard
no-assertion-changes constraint (A2), the harness extraction to `app_harness.py` (A3), and the
corrected file-scope list (A4/A5). None of it touches my Risk 2/4/5 rulings or my four
implementation conditions from the first review, and A1/A2's reasoning is sound on its own terms
independent of my lane. Read `cfa7ecd`'s actual diff against these commitments (not just the design
note) before signing off here: `test_http.py`'s diff shows harness extraction and the two
`main_module.db` repairs only, no assertion text changed — matches A2's hard constraint exactly.

### Net ruling

`cfa7ecd`'s connection-lifecycle and transaction-semantics work is sound and matches what was
designed and reviewed — **BEGIN IMMEDIATE, busy_timeout, and cursor-pagination invariants are
confirmed unchanged.** It is not yet "Done" per the work order's own checklist: Issues 1 and 2 need
a follow-up commit widening exception mapping to app-level handlers (routes to bruce-lee via
helio-gracie), and Issue 3 needs one line (`del _boot`) routed through ip-man per A1's own
notify-not-re-gate precedent. None of these block ronda-rousey's QA work order, which is orthogonal
(new test file, existing harness) — she can and should proceed against `cfa7ecd` now. Pushing
`cfa7ecd` to `internal` alongside this review so it's available for that work; the exception-handler
widening and the `_boot` cleanup land as separate follow-up commits, reviewed on their own merits
when bruce-lee delivers them.

## Addendum B — ruling on jackie-chan's checkpoint review: exception-mapping scope, `del _boot`, import-window availability (ip-man, 2026-09-22)

One round, three rulings. B1 is the scope call, B2 is a governance-precedent call, B3 is
ronda-rousey's status-code spec.

### B1. Narrow, not generalized. One app-level handler for `sqlite3.OperationalError`; `invoke()` stays.

**Ruling:** add exactly one FastAPI app-level exception handler, for `sqlite3.OperationalError`,
with the same locked/busy discrimination `invoke()` uses today. **Move** that clause out of
`invoke()` rather than duplicating it. `Conflict`/`Forbidden`/`Invalid`/`Unavailable` stay in
`invoke()`, untouched. No route body changes except one line in `aliases` (below).

The rule this creates is one sentence and needs no memory to apply: **driver exceptions map
structurally at the app boundary, because they can originate anywhere — including inside `get_db`
before a route body exists; domain exceptions raised deliberately by `service.py` map at the call
site that raised them.** That is a partition by origin, not a split posture.

Why jackie-chan's split-invariant argument does not carry here — three reasons, in order of weight:

1. **The A1 analogy inverts.** A1's split-startup problem was *ambiguity with no rule*: two
   mechanisms doing the same job, nothing telling the next person which to use. Here the rule is
   mechanical. `get_db`'s `connect()` cannot be wrapped in `invoke()` by construction — that is
   jackie-chan's own finding and it is what makes the app-level handler necessary — so
   infrastructure exceptions *must* be structural. Domain exceptions can only arise where
   `service.py` is called, which is exactly where `invoke()` already is. There is no guess to make.

2. **Her end state is not a single posture either.** After full retirement, `main.py` still maps
   conditions to statuses inline in at least five places: `identity()`'s 401 (she excludes it
   explicitly) and its `Forbidden`→403, `get_root`/`get_post`'s 404s, `verify`'s two 503
   configuration guards, and `ready()`'s 503. The uniformity being bought does not exist at the end
   of the purchase. The argument pays for a seven-route diff and does not deliver the invariant it
   is justified by.

3. **Zero additional reachable defects.** Her own audit establishes this: `aliases()` is a bare
   `SELECT` with no validation branch, and the other five uncovered surfaces (`ready`, `get_root`,
   `get_post`, `assignments`, `reconciliation`) call no service method at all — `OperationalError`
   is the only exception class they can raise. The generalized form's four extra handlers cover
   nothing that can happen today. This is round three on one commit, with ronda-rousey already
   building against `cfa7ecd`; smallest change that solves it applies with full force.

**Her real point — the `aliases` future trap — is valid and the narrow form closes it, cheaply.**
Wrap the call: `return invoke(lambda:Registrar(db).aliases(alias))`. That makes the convention exact
and *auditable* instead of remembered: **every route that calls a `Registrar` method wraps it in
`invoke()`** — after this one line that is true of all eight such routes with no exceptions, and
ronda-rousey can assert it structurally (item-4 tripwire class). The next person who adds a
validation branch to `aliases()` is caught by a failing test, not by memory — which is the outcome
jackie-chan wanted, at one line instead of seven routes. The five raw-`db.execute` routes never call
a service method; the tripwire must not require `invoke()` of them.

**Implementation conditions for bruce-lee, not optional:**

1. Register on `sqlite3.OperationalError` only — **not** `sqlite3.Error`. `IntegrityError` and
   friends must keep surfacing as 500; they are bugs, not contention.
2. Non-locked/busy `OperationalError` must **re-raise from inside the handler**, not be converted to
   a tidy 500 response. "no such table"/"no such column" must keep producing a logged traceback and
   must keep behaving as a server exception under `TestClient`. Swallowing it would hide schema skew
   behind a clean error body — the exact silent-wrongness this whole change exists to remove.
   **Verify this empirically** (extend jackie-chan's probe); do not assume Starlette's re-raise
   semantics.
3. The 503 response body must be byte-identical in shape to what `HTTPException(503,str(exc))`
   produces today (`{"detail": ...}`). An app-level handler that invents its own JSON is a silent
   contract change for `viewer/registrar_client.py` and every other consumer.
4. `invoke()`'s `OperationalError` clause is deleted in the same commit. One rule, one place — this
   is what keeps the narrow form from being a duplication hazard.

**Retiring `invoke()` is deferred, not rejected on the merits.** If it is wanted, it is its own
design note and its own review, judged on whether one uniform mechanism beats two with the inline
`HTTPException` raises counted honestly. Not smuggled into a contention fix. Same call A1 made on
`lifespan`, for the same reason.

### B2. `del _boot`: instance approved, generalized rule rejected as phrased — and the line is amended.

**The instance:** approved. `del _boot` is right in substance and notify was acceptable here.

**The rule she stated: rejected, replaced.** A1's notify rule never rested on direction — a reviewer
amending the author's snippet is fine, direction was never the load-bearing part. It rested on three
conditions: touches no standing ruling or implementation condition; strictly reduces scope; an
objection routes back to the amendment's author, never to the implementer mid-change.

The load-bearing one is the second, and **"strictly tightens an invariant" is not a safe substitute
for "strictly reduces scope."** Reducing scope is self-limiting — a smaller diff cannot introduce new
behavior. Tightening an invariant is not self-limiting — tightening can break a consumer. The
counterexample is in her own first review: tightening `check_same_thread` to `True` strictly tightens
an invariant and is a regression. A rule that would license that as notify-only is too broad, and it
is the rule, not this instance, that gets quoted next time.

**Replacement boundary, binding from here.** Notify-don't-re-gate applies when (a) the change touches
no standing ruling or implementation condition, (b) it introduces **no new behavior on any reachable
path — verified, not asserted**, and (c) an objection routes back to the amendment's author, never to
the implementer mid-change. Direction is irrelevant; (b) is the test. `del _boot` passes (b) because
helio-gracie *verified* the name is unreferenced. That verification is what earned the notify, not
the tightening.

**Amendment to the line.** This does not qualify as notify under the rule I just wrote, so it is
gated here rather than notified. Replace the whole boot line instead of appending `del`:

```python
def _migrate_at_boot(path):
    with session(path) as db: migrate(db)
_migrate_at_boot(DB_PATH)
```

- Achieves jackie-chan's invariant **structurally, by scope**, rather than by a cleanup statement a
  future refactor can drop while keeping the connection. Strictly stronger than `del`.
- **Fixes a leak `del _boot` leaves in place.** The current line closes only on the success path: if
  `migrate()` raises — partial migration, DDL error, `BEGIN EXCLUSIVE` busy — `_boot` is never
  closed, and the traceback holds the frame and the connection alive. That is precisely the hazard
  `db.py`'s `session()` exists for ("Windows holds an exclusive lock on an open DB file, so a leak is
  not merely untidy") and the one `_FreshAppCase`'s Windows-lock NOTE documents from the test side.
  The boot path should use the helper the rest of the app already uses.
- **Consequence:** `connect` becomes unused in `main.py` — drop it from the import line
  (`from .db import migrate,session`). After this, `main.py` cannot open a raw connection at all;
  `session()` is the only door and everything it opens closes in a `finally`. Ronda-rousey's item-4
  tripwire gets simpler and stronger: assert no module attribute of `registrar.app.main` is a
  `sqlite3.Connection`, and assert `main.py` does not import `connect`.

This is connection lifecycle, so jackie-chan holds the objection route on the form. bruce-lee
proceeds now; an objection comes back to me, not to him mid-change.

### B3. Import-window 503: (a) accept and document. Risk 6 stays out of scope.

**First, a correction to the finding's blast radius, because it changes the test design.**
`promote_import` blocks the event loop, so requests that *arrive* during the import cannot advance at
all — they are served normally once it returns. Only a read whose **body was already executing on a
worker thread** when the import took the write lock can contend. The window is not instantaneous,
though: `authenticate()` runs an argon2 verify — deliberately expensive, tens of milliseconds —
between the body's start and its `last_used_at` UPDATE. So there is a real several-tens-of-ms window
per in-flight read. Reachable, rare, bounded. Not "all reads 503 during imports."

**Why accept:**

1. **The 503 is correct, and it is what we paid for.** What it replaces is a write that silently
   joined a stranger's transaction, subject to that transaction's rollback, on a connection being
   driven from two threads. Trading a silent correctness violation for a loud, retryable,
   correctly-signalled unavailability *is the change*. Engineering the 503 away here would be
   re-buying the thing we just removed.
2. **The degradation is reshaped, not new.** Risk 6 always said an import stalls every request
   including health checks. A caller during an import already could not get a response — they got a
   stall, which past any client timeout is indistinguishable from unavailability. A fast, retryable,
   observable 503 is the *better* failure mode: it appears in metrics instead of as mysterious
   latency. The new finding weakens the case for urgency rather than strengthening it.
3. **Bounding `promote_import` is a different change in a different lane.** It means chunking one
   atomic transaction, which changes what an import promotion *guarantees* — partial visibility,
   resumability, what `import_runs.status` means after a mid-way failure. That is a `service.py`
   transaction-semantics redesign, jackie-chan's lane, its own note and its own review, against this
   note's standing zero-changes-to-`service.py` constraint. It would be the largest scope expansion
   proposed on this job, on round three, for a rare and already-accepted condition.

**Cheaper lever, named so a future conversation does not start in the wrong place:**
`authenticate()`'s `last_used_at` UPDATE is the only write on the read path, and it is *telemetry* —
nothing reads it to make a decision. Making that write contention-tolerant, or moving it off the
synchronous path, removes read-path write contention entirely at a fraction of the cost of
restructuring imports. **Not ordered now:** it is `auth.py`, which this change has deliberately held
at zero diff, and gsp has a stake in token-liveness observability. Raise it after this ships, if it
is ever worth raising.

**Do not raise `busy_timeout` to mask this.** That trades a fast retryable failure for a longer stall
and hides the condition. Any change there needs a measurement first.

**Expected status codes — ronda-rousey's answer, explicit:**

- Reads in flight when an import takes the write lock: **200 normally; 503 is legitimate** and must
  be retryable — a retry after the import completes succeeds.
- Reads arriving *during* an import: **200**, after a delay. They do not 503.
- **500 is never acceptable for lock contention.** That is the defect B1 closes and it is the
  assertion that matters.
- **Do not assert that a 503 occurs.** That is timing-dependent and will flake, against this note's
  own rule that tripwires must not pass flakily. Assert the negative and the recovery: no 5xx other
  than 503 under import-window load, and any 503 is followed by a successful retry.

### B4. Added to "Done when"

- No `sqlite3.OperationalError` with a locked/busy message — from `get_db`'s `connect()`,
  `identity()`'s `last_used_at` UPDATE, or any of the six bare route surfaces — surfaces as a 500.
- A non-locked/busy `OperationalError` still surfaces as a server exception with its traceback,
  verified empirically, not assumed.
- Every route that calls a `Registrar` method is wrapped in `invoke()`, enforced by a structural test.
- `registrar.app.main` has no module attribute that is a `sqlite3.Connection`, and `main.py` does not
  import `connect`.
- 503 response bodies are unchanged in shape from `cfa7ecd`.

### B5. Routing

helio-gracie sends this to jackie-chan and bruce-lee together. jackie-chan holds the objection route
on B2's boot-connection form and on B1's four implementation conditions — both her lane. bruce-lee
proceeds now on B1 and B2; an objection comes back to me, not to him mid-change. B3 needs no further
review: it is a documented accepted consequence and it is ronda-rousey's status-code spec.

## jackie-chan's sign-off on Addendum B — no objection, verified not accepted-on-read (2026-09-22)

Both items routed to me. Verified directly rather than taken on ip-man's word, same standard I held
everyone else to in the checkpoint review above.

### On B1's scope ruling (narrow, not generalized) — I'm persuaded, not just overruled

Re-audited the claim my own proposal was measured against: across `ready`, `get_root`, `get_post`,
`assignments`, `reconciliation`, and `aliases`, none call a `Registrar` method that can raise
`Conflict`/`Forbidden`/`Invalid`/`Unavailable` — `aliases()` is a bare `SELECT`, the other five never
touch `service.py` at all. `sqlite3.OperationalError` is the only exception class reachable on any of
them today. That's my own finding, re-confirmed, and it means the generalized form's other four
handlers would cover zero currently-reachable defects while costing six extra routes of diff. Point 2
(my end state still has five other places where `main.py` maps a condition to a status inline —
`identity()`'s 401, the two `verify` 503 guards, `get_root`/`get_post`'s 404s, `ready()`'s 503) is
also correct on a re-read of the actual routes; I stated "uniformity" as the payoff without pricing
those in. I was over-broad. No objection to the narrow ruling — this is a better-scoped fix than what
I proposed, not a compromise of it.

### On B1's four implementation conditions — verified empirically, no objection

1. **Scope to `OperationalError`, not `sqlite3.Error`:** confirmed via `issubclass` that
   `sqlite3.IntegrityError` is a *sibling* of `OperationalError` under `DatabaseError`, not a
   subclass — `issubclass(sqlite3.IntegrityError, sqlite3.OperationalError)` is `False`. A handler
   registered on `OperationalError` specifically cannot accidentally intercept `IntegrityError`
   (`publish()`'s `Drive file already bound` conflict path stays exactly as-is, unaffected).
2. **Non-locked/busy re-raise from inside the handler:** probed directly against this repo's
   installed fastapi 0.116.1/starlette 0.47.3, not assumed. A handler that re-raises `exc` for a
   "no such table" `OperationalError` propagates as the real exception under
   `TestClient(raise_server_exceptions=True)` (pytest sees the actual `OperationalError`, not a
   tidy response) and correctly becomes a 500 under `raise_server_exceptions=False`
   (Starlette's `ServerErrorMiddleware` path — what a real deployed ASGI server without debug mode
   does). Not swallowed in either mode.
3. **503 body shape:** probed side by side — the handler's `{"detail": str(exc)}` for the
   locked/busy case is byte-for-byte what `HTTPException(503, str(exc))` produces via FastAPI's own
   default handler. No contract change for `viewer/registrar_client.py`.
4. **`invoke()`'s remaining clauses can't re-catch it:** `Conflict`, `Forbidden`, `Invalid`,
   `Unavailable` share no ancestry with `sqlite3.OperationalError` (custom classes, unrelated
   hierarchy) — removing `invoke()`'s `OperationalError` clause lets it propagate cleanly out to the
   app-level handler with no risk of an intermediate `except` swallowing it first.

Scratch probe: `...\scratchpad\exc_handler_probe2.py` (conditions 1-3), not committed.

### On B2's boot-connection form — verified, and it's a real fix for a bug I missed

Reproduced the leak directly rather than trusting the claim: built the exact `cfa7ecd` pattern
(`connect(); fn_that_raises(); close()`) with a synthetic failure standing in for a partial-migration
error, and confirmed the connection is left open and queryable after the exception — `.close()`
genuinely never runs, because the line after the raising call is skipped. My own `del _boot` proposal
would not have caught this; `del` only runs after `.close()`, which itself never executes on this
path. Then built `_migrate_at_boot()`'s actual replacement (`with session(path) as db: migrate(db)`)
against the same failure and confirmed the connection is genuinely closed afterward
(`ProgrammingError: Cannot operate on a closed database` on a post-exception probe query) while the
original exception still propagates uncaught, exactly as required. This is a strictly stronger fix
than what I ruled for, on a defect I didn't find. No objection — accepted as-is, including the
`connect` import removal and the resulting stronger tripwire (no module attribute is a
`sqlite3.Connection`, and `main.py` doesn't import `connect` at all).

Scratch probe: `...\scratchpad\session_leak_probe.py`.

### On the rejected "tighten under notify" precedent

Agreed, and the `check_same_thread` counterexample is exactly right — I generalized a single routing
decision into a durable rule without stress-testing it against my own adjacent finding in the same
document, which is the one thing that rule should have been checked against first. The replacement
boundary (no standing ruling/condition touched; **no new behavior on any reachable path, verified not
asserted**; objection routes to the amendment's author, never the implementer mid-change) is the
correct fix, not just a safer-sounding one — "reduces scope" is self-limiting in a way "tightens an
invariant" isn't, and that's the actual load-bearing distinction. No objection. Not re-raising the
rejected form.

**No further concerns on B1 or B2. Both proceed as ruled.** bruce-lee's resulting commit is the next
thing I review — connection lifecycle, transaction semantics, and the four conditions above are what
I'll check it against.

## jackie-chan's review of `60ee5aa` — B1/B2 implementation, both flagged items resolved (2026-09-22)

**No objection. Approved.** `git diff 8b2d2a4 60ee5aa` touches only `registrar/app/main.py` (75
insertions, 27 deletions); confirmed `registrar/tests/test_http.py`'s diff against the same range is
empty (`0` lines) — zero assertion changes, exactly as claimed.

### B1's four conditions — re-verified against the actual delivered code, not the description of it

1. **`OperationalError` only:** `app.exception_handlers` dumped directly from the booted module shows
   exactly one custom entry (`OperationalError`) alongside FastAPI's own three defaults
   (`HTTPException`, `RequestValidationError`, `WebSocketRequestValidationError`) — nothing broader
   registered. Matches.
2. **Non-locked/busy re-raise:** confirmed by reading `operational_error()` — `raise exc` on the
   non-matching branch, no conversion. Matches my own independent probe from the prior round.
3. **503 body shape:** `JSONResponse({"detail":str(exc)},status_code=503)` — byte-identical to
   `HTTPException(503,str(exc))`'s own output, previously verified.
4. **`invoke()`'s clause deleted, not duplicated:** confirmed by reading `invoke()` — the
   `except sqlite3.OperationalError` clause is gone, the other four (`Conflict`/`Forbidden`/
   `Invalid`/`Unavailable`) are untouched, with a comment against re-adding it or promoting them.

### B2 boot form — confirmed structurally, not just by diff inspection

Ran this myself against the real booted module (`import registrar.app.main`, then inspected `vars()`):
`[k for k,v in vars(m).items() if isinstance(v,sqlite3.Connection)]` returns `[]` — no module
attribute is a connection. `hasattr(m,'_boot')` is `False`. `hasattr(m,'connect')` is `False` — the
import line correctly dropped it. All three of B2's structural claims hold against the running app,
not just the source text.

### Flagged item 1 — teardown-phase reachability — resolved: it IS reachable, not a gap

bruce-lee's uncertainty was reasonable to raise (dependency-cleanup exception handling has been a
genuinely version-dependent FastAPI/Starlette footgun historically), but on this repo's pinned
versions it does not hold. Built a faithful reproduction of the actual shape — a fake connection whose
`.close()` itself raises `sqlite3.OperationalError("database is locked")` inside `session()`'s
`finally`, wired through the real `get_db()`/`session()` contextmanager nesting, against
`fastapi==0.116.1`/`starlette==0.47.3` — and confirmed the app-level handler catches it and returns
`503 {"detail":"database is locked"}` correctly under both `TestClient(raise_server_exceptions=True)`
(pytest's view) and `False` (production-equivalent ASGI error path). The "driver exceptions map
structurally at the app boundary" framing from Addendum B holds through dependency teardown on this
stack, not just through route bodies and dependency setup. **Ruling: no doc note needed as a caveat or
limitation — but recording the verification here so it isn't re-litigated, and flagging the one real
caveat:** this specific guarantee (yield-dependency cleanup exceptions routed through app-level
handlers) is a property of the current fastapi/starlette pin, not a language-level guarantee — if
either is ever upgraded, this should be re-checked, not assumed to still hold. Low cost, worth one
line in a future dependency-bump changelog, not a standing risk today. Scratch probe:
`...\scratchpad\teardown_probe2.py`.

### Flagged item 2 — `exc.sqlite_errorcode` — verified sound, ruled to defer, not implement now

Reproduced a genuine lock-contention `OperationalError` (two real connections, one holding
`BEGIN IMMEDIATE` uncommitted, the other timing out) rather than trusting a synthetic string, on the
pinned Python (3.14.6): `exc.sqlite_errorcode` is `5` (`SQLITE_BUSY`), `exc.sqlite_errorname` is
`"SQLITE_BUSY"`. Compared against the schema-skew case ("no such table"): `sqlite_errorcode` is `1`
(`SQLITE_ERROR`), cleanly distinct. Both attributes are populated, present, and correctly discriminate
the exact two conditions this handler needs to tell apart. One correction to bruce-lee's framing
worth recording: SQLite's error strings are not locale-sensitive (`sqlite3_errmsg()` is fixed English
text in the C library regardless of OS locale), so "locale-independent" overstates the real risk —
the genuine risk is *wording drift across SQLite/Python versions*, which errorcode is immune to and
substring matching is not. That risk is real but low-probability today.

**Ruling: defer, don't implement in this commit.** Ip-man's B1 text specified "the same locked/busy
discrimination `invoke()` uses today" as a deliberate scope limit on an already-third-round change
("smallest change that solves it applies with full force"). Swapping the discrimination mechanism is
not a bug fix within that scope, it's a second, independent improvement riding on the same commit —
exactly the kind of addition the B1/A1 pattern in this doc has consistently pushed to its own,
separate, reviewed change rather than folding in opportunistically. I'm applying that same discipline
to my own finding here, not just other people's. The verification above stands so a future change
doesn't have to re-derive it — this is a named, ready-to-implement follow-up
(`exc.sqlite_errorcode in (5,6)` for `SQLITE_BUSY`/`SQLITE_LOCKED`, replacing the `"locked" in
message or "busy" in message` check), not a vague someday-item. Raise it as its own line if it's ever
worth raising, same framing B3 used for the `last_used_at` UPDATE lever. Scratch probe:
`...\scratchpad\errorcode_probe.py`.

### Test suite — reproduced independently, not accepted from the commit message

Ran the full suite myself: `2 failed, 104 passed` on one pass, `1 failed, 104 passed` (same single
test, `test_concurrent_children_and_publication`) on two more targeted re-runs of `test_registrar.py`
alone — consistent with the pre-existing Windows SQLite flake this doc has tracked since `cfa7ecd`'s
own commit message (which reported the same two tests, same failure mode, against `HEAD` in a clean
worktree before any of this round's changes existed). Both failing tests build their own connections
directly in `test_registrar.py` and never import `main.py` — structurally incapable of being affected
by this change. `test_http.py` + `test_legacy_taxonomy.py` together: `71 passed, 0 failed`, confirming
bruce-lee's 9+62 claim.

**No further concerns. `60ee5aa` is approved as delivered.** Pushing it now along with this review,
per the coordinator's routing — my sign-off, my access, no further gate needed.

## jackie-chan's correction — "zero flakiness" was wrong; reconciled against ronda-rousey's finding (2026-09-22)

ronda-rousey ran `test_concurrent_root_allocation`/`test_concurrent_children_and_publication`
standalone, 5 times each, on an idle machine (checked via `tasklist` for other python processes):
**4 of 5 failed, each time, with `sqlite3.OperationalError: database is locked`.** This directly
contradicts my first-pass review's "Zero flakiness reported in this suite" and the "already
battle-tested"/"inverts the usual risk calculus" framing built on it (line 40, ip-man's original
text; line 256, my endorsement of it). Investigated rather than accepted or defended, per this doc's
own standard applied to everyone else all session.

### Was the original claim ever actually run? Honest answer: I don't know, and the evidence available points the wrong way

I have no record from that first-pass session of these two tests being executed with output captured
— nothing resembling the pass/fail counts I've shown my work with everywhere else in this file. The
phrasing itself ("I *read* `test_concurrent_root_allocation`... directly... Zero flakiness *reported*")
uses a code-reading verb and an absence-of-complaints framing, not an execution-and-observation one.
I cannot rule out that it was run once, quietly, and passed — but I can rule out that it was run
enough times to support the word "zero," because five is enough to falsify that word and one or two
would not have been. **Worse: this session had direct disconfirming evidence already in hand and
didn't connect it.** My own checkpoint-review commit (`8b1ae27`) and my `60ee5aa` review commit
(`95990ac`) both separately ran the full suite, both saw these exact two tests fail, and both
described it — accurately, in isolation — as "the pre-existing Windows SQLite flake this doc has
tracked since `cfa7ecd`." I used the word "flake" about these tests twice this session without ever
going back to reconcile it against my own earlier "zero flakiness" claim about the *same two tests*
in the *same document*. That is exactly the kind of contradiction-across-sections this doc's own
culture (Addendum A0, B1's audits) exists to catch, and I should have caught it myself without
needing ronda-rousey to surface it. Recording that plainly rather than only fixing the text.

### Reproduced directly, with the confound explicitly checked

Ronda-rousey checked for other *python* processes only. The coordinator's confound — this session
running many parallel background agents on this machine for hours, which could look like "the design
is flaky" when it's really "the machine was busy" — is a real thing to rule out before accepting
either the original claim or the contradiction of it at face value. Checked properly:

- `Win32_Processor.LoadPercentage` immediately before/after each of 5 runs:
  `0, 5, 4, 3` before; `14, 6, 6, 4, 3` after. **Never above 14%.** Multiple `claude` processes are
  indeed running (confirmed via `Get-Process`, matching the coordinator's premise about this
  session's background load), but CPU load at the moments these tests actually ran was low, not
  saturated.
- Ran the two tests 5 times (`pytest -k "test_concurrent_root_allocation or
  test_concurrent_children_and_publication"`), matching ronda-rousey's methodology:
  `test_concurrent_root_allocation` failed **5 of 5**; `test_concurrent_children_and_publication`
  failed **3 of 5**. Same failure mode both times: `sqlite3.OperationalError: database is locked`,
  from `self.db.execute("BEGIN IMMEDIATE")` inside `Registrar.idem()` — a genuine SQLite write-lock
  timeout, not an application bug or a test-harness artifact.
- **Conclusion: "the machine was busy" is not a sufficient explanation.** These failures reproduce
  reliably at measured CPU load under 15%, which is not what a saturated machine looks like. I can't
  produce a true zero-other-process baseline on this shared, long-running session host, so I can't
  rule out background load as a *partial* contributor — but the load readings make it clearly
  insufficient as the *primary* cause, at the magnitude observed (worse than or matching
  ronda-rousey's own rate).

### The actual mechanism, best-supported by the evidence: thread-count oversubscription, not a design flaw

This machine (`AMD Ryzen 5 5600G`) has **6 cores / 12 logical processors**. Both tests spin up
**100 threads**, each opening its own connection and immediately racing for `BEGIN IMMEDIATE`'s
single SQLite write lock — roughly 8x thread oversubscription before any other process on the system
is counted at all. `busy_timeout=5000` is a *wall-clock* timeout, not a CPU-time budget: a thread
holding the write lock that gets preempted by the OS scheduler under 8x oversubscription can stay
descheduled long enough, in real elapsed time, for every other waiting thread's 5-second clock to run
out — with zero unrelated processes required to make that happen, just this test's own thread count
against this machine's core count. This is the best-supported explanation for reproducing at 0-14%
measured load: the contention is mostly self-inflicted by the test's own concurrency level, not
externally imposed.

**One more scoping point, independent of the flakiness finding, that further limits what these tests
ever proved:** they are pure **write-write** contention stress tests — 100 threads all doing
`BEGIN IMMEDIATE` writes concurrently. They say nothing about **read** concurrency, which is what
`cfa7ecd` actually changes for production (`main.py`'s read routes moving off a shared connection).
Citing them as proof the *production read topology* was "already battle-tested" was importing
evidence from the wrong axis, flakiness aside.

### What this does and does not change

**Does not change:** `BEGIN IMMEDIATE`/`busy_timeout` invariants are still confirmed unchanged
mechanically (verified by diff, independent of this finding). Production's write routes are still
all `async def`, still fully serialized on the event loop — so production itself never subjects
`BEGIN IMMEDIATE` to 100-way simultaneous contention the way this stress test artificially does; the
mechanism that makes these two tests flaky is not a mechanism production traffic exercises. B1/B2
stand as reviewed and approved.

**Does change, and strengthens rather than weakens the case for it:** this is now direct, reproduced
evidence that `busy_timeout=5000` *can* be legitimately exceeded under real concurrent-writer
contention on this exact hardware — not a hypothetical. That's the precise condition Issue 1 and B1's
503 mapping exist to handle gracefully instead of surfacing as an unhandled 500. Bruce-lee's own
8x15 smoke test read as clean partly because it never approached this thread count; this data doesn't
contradict that result, it explains why "the smoke test was clean" was never strong enough evidence
that contention was "practically negligible" — which is exactly why I didn't accept it as sufficient
when ruling on Issue 1.

**Correction to the record, stated plainly:** "Zero flakiness reported in this suite" (line 256) was
wrong and should not have been asserted as worded. The "already battle-tested" / "inverts the usual
risk calculus" framing (line 40, ip-man's original; line 256-259, my endorsement) is not supported
by these two tests as evidence of reliability — it is, at best, evidence that the *pattern*
(connect-per-caller, correct PRAGMAs, `BEGIN IMMEDIATE`) is *architecturally* the right one, which
these tests still demonstrate by having a real, mechanical, wall-clock-bound failure mode
(`busy_timeout` expiring) rather than the silent-corruption failure mode the whole fix targets. Real
distinction, but "architecturally sound, mechanically clean-if-flaky under stress" is a materially
weaker claim than "zero flakiness," and the doc should have said the weaker, true thing.

### Recommendation, not actioned here — routes to ronda-rousey's QA lane

`test_concurrent_root_allocation` asserts `self.assertFalse(errors)` — zero tolerance, no retry, for
100 raw threads against a single write lock. Given the confirmed oversubscription mechanism, I'd
recommend one of: (a) reduce these two tests' thread count to something closer to this class of
machine's logical-processor count so they stay meaningful without guaranteeing timeout-driven
flakiness by construction, (b) add a bounded retry-on-`OperationalError`-locked/busy inside the
test's own writer function, mirroring what a real client would do against a 503, or (c) explicitly
mark them as known-flaky-under-thread-oversubscription in a comment so a future CI run doesn't waste
time treating a single red run as a regression signal. Not implementing any of these myself — test
logic changes in `test_registrar.py` are ronda-rousey's QA lane, and this needs its own small,
reviewed decision rather than being folded into this correction. Flagging once, per this doc's own
norm on scope discipline.

**This does not block the final gateway or reopen B1/B2.** Recorded per the coordinator's
instruction so a wrong "already battle-tested" premise does not sit unreconciled in the design doc.

## Addendum C — closeout rulings on helio-gracie's final ESCALATE bundle (ip-man, 2026-09-22)

Five items, one round. C1, C2, C3 and C4 gate closeout; C5 is deferred with a named shape.
C1 and C3 gate because each is a Done-when criterion with no honest proof behind it — the
one failure mode this doc has corrected repeatedly and must not commit on its own last page.

### C1. Done-when bullet 2 is false as written. Amend the criterion now; fix the tests after closeout.

**The finding is not in question** — `test_concurrent_root_allocation` and
`test_concurrent_children_and_publication` fail intermittently on this hardware (jackie-chan
5/5 and 3/5, ronda-rousey 4/5), root-caused in the correction section above. What was missing
is a ruling on the criterion. Ruling: **amend it, and fix the tests separately.**

**Amendment.** In the work order's "Done when", replace:

> - Full existing suite green, including both WS3 concurrency tests.

with:

> - Full existing suite green, with exactly two documented exceptions:
>   `test_concurrent_root_allocation` and `test_concurrent_children_and_publication`,
>   which fail intermittently on this hardware for a cause this job did not create and
>   cannot reach. **The required evidence is structural, not statistical:**
>   `git diff fe6d953..HEAD -- registrar/tests/test_registrar.py` is empty, and neither
>   test imports `registrar.app.main` — so no line changed by this job is reachable from
>   either one. Both must be re-run and shown at closeout, not remembered. Root cause:
>   100 threads against 12 logical processors, `busy_timeout` being wall-clock rather
>   than CPU-time (see the correction section above).

**Why structural proof rather than a green run, and why this is stronger rather than a
concession.** A green run of a flaky test proves nothing about causation — it is a coin
landing the right way, and re-running until it lands is the dishonest version of this
criterion, not the rigorous one. An empty diff on the test file plus the absence of a
`main.py` import is a *deductive* argument that this job could not have affected these
tests, and it is deterministic, cheap, and re-checkable by anyone. jackie-chan already made
exactly this argument in her `60ee5aa` review ("structurally incapable of being affected by
this change"); the criterion should say what she actually proved. Note that this only works
*because* `test_registrar.py` was held at zero diff — which is why the test fix below must
land after closeout, not inside it.

**Test fix: jackie-chan's option (b), bounded retry-on-locked. Ordered as a separate
follow-up commit after this job closes.**

Of her three options, (b) is the only one that preserves what these tests are *for*. The
invariant under test is allocation uniqueness under concurrent writers
(`assertEqual(100, len(set(results)))`); the thread count is a proxy for contention, not the
invariant. Option (a) — reduce the thread count — weakens the contention that makes the
uniqueness assertion meaningful, trading a real signal for a quiet suite. Option (c) — a
known-flaky comment alone — leaves a permanently red suite, and a suite that is *expected* to
be partly red trains every future reader to discount red, which costs more than these two
tests are worth. Option (b) keeps 100-way contention at full strength and removes only the
failure mode this system now explicitly defines as recoverable: B1 established that a lost
busy-lock race is a retryable 503 and that the correct client response is to retry. A test
writer that does not retry is asserting a contract stricter than the one the API offers.
After the change, `assertFalse(errors)` means "no error survived bounded retry" — which is a
genuine defect signal, where today it is a hardware-scheduling coin flip.

Conditions on the fix, so a retry loop does not become a way to hide a real regression:
1. Retry **only** on `sqlite3.OperationalError` whose message matches the same locked/busy
   discrimination `main.py`'s handler uses. Every other exception fails the test immediately.
2. Bounded — a small fixed attempt cap with brief backoff. Exhaustion is a test failure, not
   a skip, not a warning.
3. A comment naming the oversubscription mechanism and pointing at the correction section
   above, so the next reader does not mistake the retry for tolerance of a real defect.
4. No assertion is weakened. The uniqueness assertions stay exactly as they are today.

This does not gate closeout. `test_registrar.py` staying byte-unchanged through this job is
itself the evidence C1's amended criterion rests on.

### C2. Pin `starlette==0.47.3` in `registrar/requirements.txt`. Authorized.

`registrar/tests/test_dependency_exception_handling.py` asserts `starlette.__version__ ==
"0.47.3"` and calls it "fastapi 0.116.1's resolved transitive pin". It is not a pin.
`requirements.txt` declares `fastapi`, `uvicorn` and `argon2-cffi` only, and fastapi's
dependency range admits other `0.47.x` releases — so a clean `docker build` can resolve a
version that fails a test whose failure message explains nothing about why.

Either the assertion is wrong or the manifest is incomplete. **The manifest is incomplete**,
and the reason is not merely that a test would go red: jackie-chan's B2-round verification of
teardown-phase exception reachability was conducted against this exact version and she flagged
its scope herself — "a property of the current fastapi/starlette pin, not a language-level
guarantee — if either is ever upgraded, this should be re-checked". An unpinned transitive
makes that re-check something that can be skipped silently. Pinning converts an upgrade into
a deliberate act that trips a visible, explainable test.

Loosening the assertion instead was considered and rejected: it would make the test assert an
accident rather than a declared contract, and it would remove the only tripwire protecting a
version-scoped verification.

Conditions:
1. Add `starlette==0.47.3` with a one-line comment: transitive dependency of fastapi 0.116.1,
   pinned explicitly because `test_dependency_exception_handling.py` and the teardown-phase
   reachability verification in this doc are scoped to this exact version — bump it together
   with fastapi and re-run that verification.
2. **Verify, do not assert**, that the pin resolves cleanly alongside `fastapi==0.116.1` in a
   clean environment — a fresh venv is sufficient; the pip resolver is what is under test, not
   the container.
3. Re-run `test_dependency_exception_handling.py` and the full suite after.

**Named and explicitly not ordered:** the rest of `requirements.txt` is equally unlocked
(uvicorn's and argon2-cffi's transitives are unconstrained). Whether this project wants a full
lockfile is a real question and a reproducibility posture decision for francis-ngannou's lane
— it is not this job. Smallest change that solves it: pin the one transitive a test asserts on.

### C3. Build the handler regression test. Confirmed gap, and wider than reported.

Confirmed by grep: `main.py`'s `@app.exception_handler(sqlite3.OperationalError)` is the only
registration outside the synthetic app in `test_dependency_exception_handling.py`, and no test
in `test_http_concurrency.py` asserts its existence or behavior — the tripwires there cover
async write routes, module-level connections, the `connect` import, `_boot`, and the
`invoke()`-wrapping AST check. Deleting the decorator passes the entire suite today.

**It is worse than "the handler could be deleted unnoticed."** B4's first two Done-when bullets
both lack a durable test:
- "No `sqlite3.OperationalError` with a locked/busy message ... surfaces as a 500" — provable
  today only by inducing real contention, which B3 forbids asserting on.
- "A non-locked/busy `OperationalError` still surfaces as a server exception with its
  traceback, **verified empirically, not assumed**" — the only evidence is jackie-chan's
  scratch probes, uncommitted and discarded. That is precisely the gap
  `test_dependency_exception_handling.py` was created to close one round ago, recurring on a
  different claim.

**Ruling: build it — `registrar/tests/test_operational_error_handler.py`, new file, built on
`FreshAppCase` from `app_harness.py`.** Deterministic, no threads, no timing. Four cases,
against the **real** `main.app`, not a synthetic one:

1. **Registration:** `sqlite3.OperationalError` is a key in `main.app.exception_handlers`.
   The literal tripwire for someone deleting the decorator.
2. **Dependency-setup origin:** `app.dependency_overrides[main.get_db]` replaced with a
   generator raising `sqlite3.OperationalError("database is locked")` before its `yield`.
   Assert 503 and a body of exactly `{"detail": "database is locked"}` — B1 condition 3's
   contract with `viewer/registrar_client.py`, currently untested against the real app.
3. **Auth-path origin:** monkeypatch `main.authenticate_identity` to raise the same. This is
   Issue 1's actual finding — `identity()`'s `last_used_at` UPDATE, which no route wraps in
   `invoke()` — and it is the origin most likely to regress if someone "tidies" `identity()`.
4. **Negative control:** `sqlite3.OperationalError("no such table: posts")` re-raises under
   `TestClient(raise_server_exceptions=True)` and yields a genuine 500 under
   `raise_server_exceptions=False`. This is the assertion that stops a future "improvement"
   from turning schema skew into a tidy retryable 503 — the silent-wrongness this whole
   change exists to remove.

Constraints: `FreshAppCase` is not modified (Addendum A3). Every override and monkeypatch is
undone in `addCleanup`. No new assertion in any existing file.

Why the four cases and not just case 1: case 1 alone tests that a decorator exists, which is
a weaker claim than the doc actually makes. Cases 2-4 cost little more and convert B4's first
two bullets from probe-and-discard into standing coverage — the same move
`test_dependency_exception_handling.py` made, applied to the real app instead of a stand-in.

### C4. ronda-rousey appends her own QA section to this doc. She writes it, not a summarizer.

Verified rather than assumed: grepping this file for `ronda` returns only second-hand
references written by others, and `122` appears nowhere in it. Every other contributor's work
lives here in their own voice with their own evidence; hers exists in commit messages and in
`test_http_concurrency.py`'s module docstring (lines 78-112, which is a good home for it and
should stay) — and that docstring cross-references "ronda-rousey's QA report, 2026-09-22",
which this doc does not contain.

This is not cosmetic consistency. The 122s stall is an **open, not-root-caused finding**, and a
doc of record that omits an open finding is not a doc of record. A job cannot be declared closed
against an artifact that does not contain what is still open.

**It must be written by her.** A summary composed by anyone else is the restate-someone-else's-
finding-uncritically failure mode this file has already corrected twice (A0's negative claim from
a single file read; Issue 2's insistence on an independent count). Bounded scope — one section,
no re-litigation of anything already ruled:

- What she tested and how, with her actual numbers (the original 20x5 repro, the WS3 flake rate,
  the concurrency-suite trials).
- The 122s stall as a **still-open finding**: the observed rate, the two independent
  reproductions, what she ruled out (SQLite contention alone, argon2 alone), why it is out of
  scope here, and why it is not evidence about the NAS (Risk 7 — Windows/CPython 3.14.6 local vs
  Python 3.12 Linux container).
- What she did **not** cover, stated as plainly as what she did.

**Routing if the stall is ever picked up:** jet-li (latency/performance analysis), with
ronda-rousey holding the repro. A strikingly fixed ~122.0-122.1s that always recovers with
correct data reads as a timeout-and-retry somewhere in the anyio/Starlette/argon2 stack, not as
a concurrency defect. Named so a future conversation starts in the right lane. **Not ordered.**

### C5. `viewer/registrar_client.py` has no retry — deferred, with the shape named.

Confirmed at `viewer/registrar_client.py:157`: any status >= 400 raises `RegistrarError`, and
`_session()` mounts no retry adapter. B3's "any 503 must be retryable" is true of the API and
unexercised by the one consumer.

**Ruling: do not action now. Named follow-up, same treatment as B3's `last_used_at` lever and
jackie-chan's `sqlite_errorcode` swap.** Four reasons, in order of weight:

1. **This job did not create the gap.** The Registrar already returned 503 before any of this
   work — `invoke()`'s `Unavailable`, `ready()`'s pragma failure, and `verify`'s two
   configuration guards — and the viewer has never retried any of them. B1 adds one more, rare
   source of a status the client was already unable to handle. Fixing a pre-existing client-side
   robustness gap because this job made it marginally more reachable is scope drift with a
   plausible cover story.
2. **The right fix is a policy decision, not a patch.** A `urllib3.Retry` mounted on
   `_session()` changes behavior for every call and every status, adds latency on genuine
   outages, and interacts with `TIMEOUT = (3.05, 15.0)` and Streamlit's `@st.cache_data`. That
   is a small design decision deserving its own note, not a reflex `for attempt in range(3)`.
3. **Exposure is bounded and low.** Tens of milliseconds per in-flight read, during
   operator-initiated imports, on a home LAN, and only for a read whose body was already
   executing when the import took the write lock (B3's corrected blast radius).
4. `viewer/registrar_client.py` has been at zero diff as a standing constraint of this job since
   the original scope line. Round four is the wrong time to breach that for a low-severity
   pre-existing condition.

**Shape, so the follow-up does not start from zero:** a `urllib3.util.Retry` with
`status_forcelist=[503]`, `allowed_methods=["GET"]` (safe — this module is read-only by design),
a small `total` and short `backoff_factor`, mounted on the `@st.cache_resource` session. The
non-obvious part is what the user sees when retries are exhausted mid-`sweep_posts()` walk, and
whether a partial walk is allowed to render — that is the actual design question, not the retry
itself.

**Lane when raised: tony-jaa** — consuming an external API is his, not bruce-lee's.

### C6. Closeout gate

This job is closed when C1's amendment is applied with its two pieces of structural evidence
re-run and shown, C2 is pinned and clean-resolve verified, C3's test file is green and
peer-reviewed, and C4's section is in this doc. C1's test fix and C5 are separate, smaller
jobs raised after closeout. Nothing in Addendum C reopens A, B, or any ruling already signed off.

## Ronda-rousey's QA report — testing summary and the 122s stall (2026-09-22)

**Why this section exists:** ip-man's C4 ruling checked and found that my work on this job lived
only in commit messages and in `test_http_concurrency.py`'s module docstring, never in this doc of
record the way every other contributor's work does — and that docstring cross-references "ronda-
rousey's QA report, 2026-09-22" for the 122s stall, a section this doc did not actually contain
until now. Writing my own record, in my own voice, of my own work — not a restatement of what
others have already said about it (Issue 2 and A0's own standard, applied to myself this time).
Not re-litigating B1, B2, B3, or the WS3-flakiness reconciliation — those are ruled, and this is my
testing record, not a re-review of anyone else's ruling.

### What I tested, and how

**1. The original defect repro — what started this whole job.** Against the pre-fix `main.py`
(the single module-level `db`/`service` shared across every threadpool-dispatched read route),
20 trials of 5 concurrent, independent readers each running a full paginated walk of
`GET /v1/posts` (100 walks total). Result: **34/100 walks crashed outright** (raised an exception
before completing); of the 66 that completed with no exception, **44 returned silently wrong data**
— duplicate `post_uid`s or premature truncation from a corrupted, validly-signed cursor. Only
22/100 walks were both exception-free and correct. This is the number cited at the top of this doc
("How this was found" and "Measured impact") and the reason a "no 5xx" assertion was never going to
be sufficient regression coverage — it would have passed on roughly two-thirds of these runs.

**2. `test_registrar.py`'s WS3 concurrency tests — flake-rate check.** Ran
`test_concurrent_root_allocation` and `test_concurrent_children_and_publication` standalone, 5
times each, on an otherwise idle machine (checked via `tasklist` immediately before running, for
other `python.exe` processes). **Both failed 4 of 5 runs**, every failure
`sqlite3.OperationalError: database is locked` from `Registrar.idem()`'s `BEGIN IMMEDIATE`. This is
the finding that triggered jackie-chan's correction elsewhere in this doc — her own independent
re-run got `test_concurrent_root_allocation` failing 5/5 and `test_concurrent_children_and_publication`
failing 3/5, with CPU load ruled out (`Win32_Processor.LoadPercentage` never above 14% across her
runs) and the root cause pinned to 100 threads racing SQLite's single write lock on a 12-logical-
processor machine — real wall-clock `busy_timeout` expiry under OS-scheduler preemption at 8x
thread oversubscription, not a defect in the tests or in the fix. I independently confirm that
read: my numbers (4/5, 4/5) and hers (5/5, 3/5) are two different samples of the same
timeout-under-oversubscription race, not two different phenomena — the exact pass/fail count
varying run to run is itself consistent with a wall-clock race, not a deterministic defect
signature. Neither test imports `main.py` or touches this job's actual changes (confirmed via
`git diff fe6d953..HEAD -- registrar/tests/test_registrar.py` being empty), which is the structural
argument C1's amended Done-when criterion now rests on instead of a green run.

**3. The post-fix concurrency suite (`test_http_concurrency.py`), built by me against the real
per-request-connection topology through the real HTTP layer — not direct connections, per the
file-scoped rule I wrote into it.**

- `HttpConcurrentPaginationTests`: `NUM_POSTS=24`, `PAGE_LIMIT=6` (4 pages/walk, so every walk
  exercises real cursor traffic, not a single-page happy path), `CONCURRENT_READERS=5` (matching
  the original repro's scale), `TRIALS=8` — 8 trials × 5 readers = **40 concurrent paginated walks
  per run**, each asserted against the *exact* expected `post_uid` set (no duplicates, no missing
  rows, no extras), not merely absence of a 5xx. Every walk in every run I've executed against the
  fixed code passes exactly.
- `MixedReadWriteConcurrencyTests`: `NUM_WRITES=12` sequential reserve-then-publish pairs racing
  against `NUM_READERS=4` continuously-polling readers, cross-checking the reserve→publish
  transaction boundary live via `GET /v1/aliases` (the filename alias `publish()` inserts in the
  same `BEGIN IMMEDIATE` as the state-change `UPDATE`) rather than relying on WAL's snapshot-read
  guarantee by assertion alone. `MAX_503_RETRY_ATTEMPTS=20` at `RETRY_DELAY_SECONDS=0.1` backoff,
  per B3's exact status-code spec (200 normal, 503 legitimate-and-retryable, 500 never acceptable).
  No 500 observed in any run I've executed; any 503 observed always cleared inside the retry
  budget.
- Four structural-tripwire classes (non-timing-dependent, can't pass flakily): no module-level
  `sqlite3.Connection` reachable from `main.py`, `main.py` doesn't import `connect`, every write
  route stays `async def`, and every route calling a `Registrar` method wraps it in `invoke()`
  (static AST check against `main.py`'s actual source). All green, every run.

**4. This pass, C3: `test_operational_error_handler.py`** — four deterministic cases against the
real `main.app` (registration in `app.exception_handlers`, a `get_db`-origin locked/busy 503 with
exact body, an `identity()`-origin locked/busy 503 with exact body, and the non-locked/busy
negative control under both `raise_server_exceptions=True` and `=False`). No threads, no timing —
every case is a scripted `dependency_overrides` entry or monkeypatch, so the result is identical on
every run. 5/5 tests pass (the negative control is split across two test methods). Sanity-checked
by temporarily deleting `@app.exception_handler(sqlite3.OperationalError)` from `main.py`: 3 of the
5 tests fail as expected (registration, and both locked/busy 503 cases — the errors now propagate
raw instead of mapping to 503), while the two negative-control tests still pass unchanged, because a
non-locked error re-raising is the correct outcome whether or not the handler exists at all.
Reverted cleanly; `git diff` on `main.py` after revert is empty.

**5. Final full-suite verification for this pass, run once more at closeout as the task requires.**
`python -m pytest registrar/tests/` (all six test files, 127 tests total): **126 passed, 1 failed**,
511.68s (8m31s) wall time. The one failure was `test_concurrent_children_and_publication` — one of
the two documented, pre-existing WS3 exceptions under C1's amended Done-when criterion;
`test_concurrent_root_allocation` passed on this particular run, which is itself consistent with
the probabilistic nature of the oversubscription race jackie-chan root-caused (the criterion
requires these two stay the *only* tests permitted to fail, not that both fail on every run). No
other test failed, including all 5 of the new `test_operational_error_handler.py` cases above. The
8m31s wall time, well above what 127 mostly-sub-second tests would otherwise take, is consistent
with the 122s stall (below) occurring at least once somewhere in `test_http_concurrency.py` during
this run — expected, and not itself a failure, per the module docstring's own framing.

### The 122s stall — still open, stated plainly

This is a real, reproduced, **not-root-caused** finding, and it stays open at the close of this job.
I am recording it here rather than letting it live only in a test-file docstring, per C4's own
reasoning: a doc of record that omits an open finding is not a doc of record.

**What I observed:** on this dev box (Windows, CPython 3.14.6), individual `GET /v1/posts` requests
under genuine multi-thread concurrency — 4 to 6 concurrent readers, not tied to one specific reader
count — occasionally take approximately **122 seconds** to complete instead of the usual <0.1s,
before returning a normal 200 with fully correct data. Observed rate: **roughly 1-in-3 trials** at
that concurrency range.

**Reproduced two independent ways**, so this is not an artifact of one harness:

1. Via `TestClient` — both a bare instance and one entered with a `with` block (ruling out
   lifespan-related state as a factor, independent of Addendum A1's decision not to use `lifespan`
   in the app itself).
2. Via a real `uvicorn.Server` hit with `httpx.Client` over a real loopback socket. This path
   instead raises `httpx.ReadTimeout` at whatever client timeout is configured, since a real
   transport has no `TestClient`-style indefinite wait — different failure surface, same underlying
   stall, which is what rules out "an artifact of `TestClient`'s in-process ASGI portal specifically"
   as the explanation.

**What I ruled out:** isolated stress tests of SQLite write contention alone, and of argon2
verification alone, both stay sub-second under the same 6-way thread concurrency. So this is not
simply "SQLite is slow" or "argon2 is slow" in isolation — something in the combination (FastAPI +
Starlette + anyio + per-request `get_db` + argon2, under genuine OS-thread concurrency) occasionally
stalls. The duration itself is suspiciously precise: reproduced to within tens of milliseconds
across unrelated runs (~122.0–122.1s), which reads as a fixed timeout-and-recover somewhere in the
stack rather than random scheduling jitter — but I have not identified where.

**Blast radius is wider than "isolated latency" alone — confirmed by a third, independent
reproduction, folded in here since I hold the repro and this is the section of record for it.**
francis-ngannou, working C2 in parallel on this same round, ran the *full* suite (not this file in
isolation) after his `requirements.txt` pin and got one FAILED + one ERROR entry — a
`sqlite3.OperationalError: disk I/O error` surfacing inside `get_db` on
`MixedReadWriteConcurrencyTests::test_mixed_read_write_no_500_and_503_is_retryable_and_writer_commits_are_visible`.
Re-running that single test in isolation, it passed, taking **125.23s** — close enough to my
documented ~122.0–122.1s window that this is almost certainly the same underlying stall, not a
separate defect. He ruled out his own change as the cause (`git stash`/`pop` confirmed his diff was
`requirements.txt`-only). **What this adds to my own finding:** under full-suite thread contention
specifically (as opposed to running this one concurrency file by itself), the stall can present as
an apparent test *failure* (a raised `OperationalError`, not caught and retried the way an
in-request 503 would be, or a raw stall long enough to look like a hang from outside), not only as
added latency on an otherwise-passing trial. I had not personally observed the failure/ERROR
presentation before this — only the always-passes-eventually latency presentation documented above
— so this widens what I can honestly claim about the finding's behavior, not just its cause. It
does not change the "data is always correct when a trial does complete" observation, and it does
not change that root-causing it is out of scope for me (below) — it does mean a future full-suite
run, especially under added contention from other concurrently-running processes on the same
machine, should not be surprised by an occasional single failed/errored test here rather than only
slow ones, and that this is the same open finding, not a new regression to chase.

**Why it's out of scope for me to root-cause further:** it does not bear on the connection-
concurrency defect this test category exists to regression-test. Across dozens of trials at 4/5/6
concurrent readers run in isolation, it never produced wrong data or a permanent hang — only
latency, with the data returned always correct; the one full-suite-contention presentation above is
the first time it has surfaced as an apparent failure rather than only as latency, and even there no
wrong data was involved (the isolated re-run passed cleanly). Diagnosing a latency/failure anomaly
this specific is a performance-analysis job, not a QA regression-coverage job; per ip-man's routing
note in C4, if it's ever picked up, the lane is jet-li's (latency/performance analysis), with me
holding the repro.

**Why it is not evidence one way or the other about the NAS:** this is Risk #7 from the original
design note, and it applies exactly here — this box runs Windows with CPython 3.14.6; the NAS
deployment target runs Linux in a `python:3.12-slim` container. A local dev-box timing anomaly on a
different OS and a different CPython minor version, with its own sqlite3 module and its own
thread-scheduling behavior, is not proof the stall exists on the NAS, and is equally not proof it
doesn't. I have not tested this on the NAS or on any Linux/3.12 environment. It stays exactly what
it is: a local, dev-box-only, reproduced-but-unexplained finding.

### What I did NOT cover

Stated as plainly as what I did, not just as a footnote:

- **No testing on the NAS, or on Linux, or on Python 3.12 at all.** Every number in this report —
  the original repro, the WS3 flake rates, the concurrency-suite trials, the 122s stall — comes
  from this one Windows/CPython-3.14.6 dev box. Nothing here is evidence about the actual deployment
  target's behavior under concurrency, in either direction.
- **I did not root-cause the 122s stall**, beyond the two ruled-out isolated-stress-test hypotheses
  above. I don't know which layer of the stack it comes from.
- **I did not build or verify jackie-chan's recommended `test_registrar.py` fix** (bounded
  retry-on-locked, her option (b), the one C1 ordered as a separate follow-up commit after
  closeout). That test file remains at zero diff, by design, for the structural argument C1's
  amended criterion rests on — but the actual fix is not built, and is not mine to have built inside
  this job.
- **No concurrency scale beyond this job's own numbers.** `CONCURRENT_READERS=5` /
  `NUM_READERS=4` is what I tested through the real HTTP layer. I have not tested 10, 50, or 100
  concurrent HTTP callers against the per-request topology — the only place this app has ever seen
  100-way concurrency is `test_registrar.py`'s direct-connection stress tests, which test
  write-write contention on raw connections, not the HTTP-layer read topology this job's fix
  actually changes.
- **No true multi-process concurrency.** Every test here runs one Python process — in-process
  `TestClient` or a single `uvicorn.Server` instance. Multiple worker processes (e.g., a real
  `uvicorn --workers N` deployment) were not exercised.
- **No concurrent writer-vs-writer contention through the real HTTP layer.** `MixedReadWriteConcurrencyTests`
  has one sequential writer; write routes are event-loop-serialized by design (Risk #1, still true),
  so this is expected to be a non-issue — but I have no empirical HTTP-layer data on what happens if
  that invariant were ever violated, only the direct-connection WS3 tests' data on raw write-write
  contention.
- **No fuzzing or adversarial-input concurrency.** The concurrency suite exercises well-formed
  pagination and well-formed mixed CRUD traffic only — no malformed cursors, no malformed request
  bodies, arriving mid-race.
- **The C3 handler tests are deliberately deterministic, single-request probes, not a concurrency
  test.** They prove the handler exists and behaves correctly on a scripted exception; they do not
  exercise it under actual lock contention (B3 already ruled that a timing-dependent "503 occurred"
  assertion would flake, and I'm not reopening that here) — the contention-triggered path is only
  ever exercised indirectly, by the absence of 500s in `MixedReadWriteConcurrencyTests` and by the
  WS3 tests' own failures being `OperationalError`, not observed 500s downstream of the handler.
- **No production-like network load.** Aside from the one `uvicorn.Server` + `httpx.Client` check
  used specifically to rule out a `TestClient`-portal artifact for the 122s stall, everything else
  runs over `TestClient`'s in-process ASGI transport, not real sockets under real client load.

## jackie-chan's review of C3 — `test_operational_error_handler.py`, verified not assumed (2026-09-22)

**Status: read `3d997b7` directly (`git show --stat` confirms exactly two files touched — this
doc and the new test file, zero lines changed anywhere else, including `app_harness.py` and
`test_http.py`), read `main.py`'s current state end to end rather than from memory of the B1/B2
rounds, ran the delivered file myself (`5 passed` in `0.39s`), and reproduced ronda-rousey's
sanity check independently — commented out `@app.exception_handler(sqlite3.OperationalError)` in
`main.py`, re-ran, got the same `3 failed, 2 passed` split she reported (registration and both
locked-path cases fail; both negative-control tests still pass, correctly, since re-raise is
right with or without the handler), then reverted with `git checkout --` and confirmed
`git status`/`git diff --stat` empty before moving on. Addendum C, my own B1/B2 rulings, and Issue
1/B4 are the standing reference; this section doesn't restate their reasoning, only checks the
delivered file against it.**

### 1. Tests the real `main.app`, not a synthetic stand-in — confirmed

Every one of the four test classes calls `FreshAppCase._boot()`, which does
`import registrar.app.main as main_module` under a controlled temp-DB environment (`app_harness.py`,
unchanged — see item 5) and hands back the actual booted module. `TestClient(self.main_module.app)`
wraps the real `FastAPI` instance from `main.py:51`, with the real `@app.exception_handler` from
`main.py:53` on it. This is the deliberate contrast the file's own docstring draws against my
`test_dependency_exception_handling.py`, and I re-read that file to confirm the contrast is accurate
rather than asserted: its own docstring says outright "This file does NOT test registrar's actual
`main.py`/`get_db`" and builds throwaway `FastAPI()` apps inline. The new file has no synthetic app
anywhere in it. Confirmed by construction, not by docstring claim alone — my own decorator-removal
sanity check only works at all because the test is exercising the literal production decorator.

### 2. Case 4 (negative control) — genuinely proves non-reclassification, both `TestClient` modes

Read `operational_error()` (`main.py:53-84`) directly: the non-matching branch is a bare `raise exc`,
no conversion. The two tests exercise that exact branch (message `"no such table: posts"`, containing
neither `"locked"` nor `"busy"`) through both portals:

- `raise_server_exceptions=True` (TestClient's default): `assertRaises(sqlite3.OperationalError)`
  around the request — this is the stronger of the two assertions, because it checks the real
  exception *type* reaches the caller, not merely a non-200 status. A future regression that swapped
  `raise exc` for some other unhandled-but-different exception, or for a caught-and-rethrown
  `HTTPException`, would fail this specific assertion even though both would still 500 under the
  other mode.
- `raise_server_exceptions=False` (production-equivalent — Starlette's `ServerErrorMiddleware` path):
  `assertEqual(500, r.status_code)`. Since both modes exercise the identical `raise exc` line in the
  handler (the divergence is downstream, in how the ASGI portal treats an escaping exception, not in
  the handler itself), the strict-mode test's type-level proof and the loose-mode test's status-level
  proof are two views of one confirmed code path, not two independent risks of the same gap.

My own decorator-removal run adds first-hand confirmation on top of the code read: with the handler
gone, these two negative-control tests are the *only* two of five that still pass — because
`raise exc`'s effective behavior for a non-matching message is identical to there being no handler at
all. That is exactly the property the case is supposed to prove.

### 3. No case is timing-dependent — confirmed, and confirmed fast

Grepped the file: no `threading`, no `time.sleep`, no thread pool, no retry loop. Every case drives
its exception through `app.dependency_overrides` (a scripted generator raising before `yield`, same
shape as `get_db`) or a direct `setattr` monkeypatch of `main_module.authenticate_identity`, both
undone in `addCleanup`. My own run: `5 passed in 0.39s` — that runtime alone is corroborating evidence
against any hidden timing dependency; a file with a real contention or sleep-based mechanism could not
plausibly complete in under half a second. B3's rule (no timing-dependent assertion — Addendum C3
explicitly scoped this file to stay clear of it) holds.

### 4. Matches B1's four implementation conditions and closes B4's first two bullets

- **Condition 1 (register on `OperationalError` only, not `sqlite3.Error`):** confirmed by reading
  `main.py:53` — one `@app.exception_handler`, scoped to `sqlite3.OperationalError`. Case 1
  (`test_operational_error_is_a_registered_exception_handler`) checks presence in
  `app.exception_handlers` keyed by that exact type. `sqlite3.IntegrityError` is a sibling of
  `OperationalError` under `DatabaseError`, not a subclass (my own `issubclass` check from the B2
  round, re-confirmed here by re-reading that this file makes no change to the registration), so
  nothing in this delivery reopens that guarantee. Not independently re-tested against a live
  `IntegrityError` in this file, and it doesn't need to be — that's a registration-scope fact already
  closed by code review, not a new behavior this delivery introduces.
- **Condition 2 (non-matching re-raise):** Case 4, both modes — see item 2 above.
- **Condition 3 (503 body byte-identical to `{"detail": str(exc)}`):** Cases 2 and 3 both assert
  `self.assertEqual({"detail": "database is locked"}, r.json())` against the real handler's real
  `JSONResponse` (`main.py:83`), not a probe against a stand-in. Matches.
- **Condition 4 (`invoke()`'s clause deleted, not duplicated):** confirmed directly by reading
  `invoke()` (`main.py:124-135`) — no `except sqlite3.OperationalError` clause, with a comment against
  re-adding one. This is a static fact about the source, correctly not something the new test file
  tries to prove via HTTP behavior (there's no route path that would distinguish "deleted" from
  "present but unreachable" at the HTTP layer); it's confirmed by direct code read, same standard I
  applied to every other file this session.
- **B4 bullet 1** ("no `OperationalError` with a locked/busy message ... surfaces as a 500 — from
  `get_db`'s `connect()`, `identity()`'s `last_used_at` UPDATE, or any of the six bare route
  surfaces"): Cases 2 and 3 cover the two *origins* (dependency-setup, auth-path) through one
  representative route each (`/health/ready`, `/v1/posts`). That's the right level of abstraction, not
  a shortcut: the mapping is a single app-level handler with no route-specific branching, so every
  route that resolves `get_db` or calls `identity()` shares the exact same code path already proven
  here — a per-route repeat of the same two cases across all six surfaces would add test count without
  adding coverage. My own decorator-removal run confirms this mapping is real and reachable, not just
  present in source.
- **B4 bullet 2** ("non-locked/busy `OperationalError` still surfaces as a server exception with its
  traceback, verified empirically, not assumed"): Case 4, confirmed empirically by me independently
  (item 2), converting what was previously only jackie-chan's discarded scratch-probe evidence into
  committed, durable, re-runnable coverage — which is exactly the gap Addendum C3 named.

### 5. `FreshAppCase` genuinely unmodified — checked the diff, not the description

`git log --oneline -- registrar/tests/app_harness.py` shows exactly one commit, `cfa7ecd` (the file's
creation, per Addendum A3) — no commit since, including `3d997b7`, touches it.
`git diff fe6d953..HEAD -- registrar/tests/app_harness.py` is empty. `git show 3d997b7 --stat`
independently confirms the same at the single-commit level: two files changed
(`docs/town-registrar-connection-concurrency.md`, `registrar/tests/test_operational_error_handler.py`),
388 insertions, 0 deletions, 0 files besides those two touched. `test_http.py` is likewise untouched
by this commit. Confirmed structurally, not from the commit message's own claim.

### ronda-rousey's QA report section — no contradiction with any of my prior rulings

Read it in full per ip-man's C4 ruling. It restates the WS3-flakiness correction accurately (matches
my own numbers and root-cause, doesn't reopen it), and the 122s-stall material doesn't touch
connection-lifecycle, transaction-semantics, or isolation-posture claims I ruled on — it's routed to
jet-li, correctly, not something in my lane either way. Nothing there contradicts Risk 2/4/5, the B1/B2
implementation conditions, or the Issue 1/2 rulings. No objection.

### One concrete, non-blocking observation — named, not ordered

Case 4's two negative-control tests both drive the schema-skew error through the `get_db` origin only
(`_raise_before_yield`), not through the `identity()`/auth-path origin `AuthPathOriginTests` uses for
the locked-path case. Since `operational_error()` is one handler with no origin-specific branching,
this is not a coverage gap today — but it's the one place in this file where "one representative
origin proves the general case" (my own reasoning in the B4-bullet-1 item above) is carrying weight for
the *negative* control specifically, and the negative control is the one B1 called "the most important
of the four" cases. A fifth test — `AuthPathOriginTests` raising a non-locked message and asserting the
same 500/re-raise pair — would remove that last inference step entirely, at low cost (the class already
exists and already proves the origin is reachable for the locked case). Not blocking: the current
coverage is sound by the same reasoning that makes bullet-1's route-level abstraction sound, and I'm
not going to ask for a sixth round on this job to add one symmetrical test. Naming it so it's cheap to
pick up later, same treatment this doc gives the `last_used_at` lever and the `sqlite_errorcode` swap.

### Net ruling

**Approved, no issues.** All five review points confirmed directly, not assumed: real `main.app`
(item 1), Case 4 proves non-reclassification in both `TestClient` modes (item 2), fully deterministic
and non-timing-dependent (item 3, plus my own 0.39s run), matches B1's four conditions and closes B4's
first two Done-when bullets (item 4), `FreshAppCase` confirmed unmodified by diff (item 5). My own
independent decorator-removal sanity check reproduced ronda-rousey's exact `3 failed, 2 passed` split
before I reverted cleanly (`git status`/`git diff --stat` empty). Nothing in ronda-rousey's QA report
section contradicts any ruling I've made earlier in this job. C3 is closed. This does not reopen C1,
C2, C4, or C5 — those stand as ruled in Addendum C. Per C6, this was the last open review item on my
lane; pending only helio-gracie's closing gateway pass.
