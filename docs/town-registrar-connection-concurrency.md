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
write route alike — `identity()` (`main.py:65`) is called as a bare statement at the top of all 13
DB-touching routes, *separately from and before* any `invoke(...)` call, including in the six write
routes. `identity()`'s own `try/except` catches only `Forbidden`; nothing catches
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

This closes Issue 1 (identity()'s UPDATE, at all 13 call sites, uniformly) and Issue 2 (below) with
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
