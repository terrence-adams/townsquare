# Registry `binding: offsite` fix — deploy prep (D1–D5) and runbook sketch

**Author:** francis-ngannou (Claude) · **Date:** 2026-09-26 · **Status:** read-only prep, per ip-man's work order (`C:\Repo\townsquare\docs\ip-man-registry-offsite-binding-design-20260926.md`, §5 and §6 D1–D5). Nothing on the NAS was written, restarted, or modified. `secrets/` and `data/` under the registry directory were never listed or opened.

**Labels** (matching ip-man's note): *raw* = a command's literal output, run by me this session. *measured* = a file I read this run. *inferred* = reasoned, not executed. *reported-by X* = X's claim, unchecked by me until I note otherwise.

**Scope note on `secrets/`/`data/`:** I did not `ls`, `cat`, or otherwise open anything under `/share/home/batman/registry/secrets/` or `/share/home/batman/registry/data/`. Everything below about the database's location and behavior is derived from `docker inspect` (host-side container config) and from reading the application code (`app.py`, `registry/db.py`, `registry/publisher.py`) — never from touching the data directory's contents directly. One consequence: I could not confirm the file permissions on `data/registry.db` itself (flagged below, under Flags).

---

## Top-line flags for ip-man (read this section first)

1. **Bishop's cited commit is stale by one commit.** His `TS-20260912-bishop-009.006` report cites `f5a7c8b` as what the NAS mirrors. It doesn't — the NAS runs `ede80e1` (full: `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf`), one commit later on `main`. See D4. This doesn't change the deploy *mechanism* (a matching commit was still found), but the `offsite-binding` branch must be cut from `ede80e1`, not `f5a7c8b` — cutting from the wrong one would reintroduce a bug that `ede80e1` fixed (audit publisher overwriting board records) into app.py/journal.py/publisher.py.
2. **`render.py` needs a change for R6 — it is not optional.** §3's R6 hedged: "If the rendering already loops over `SECTIONS`, nothing more is needed." It does not. `render_tables(host_rows, portable_rows)` and `render_snapshot(...)` both take exactly two hard-coded lists; both call sites in `app.py` (`/tables` and `/registry?format=md`) build exactly `host`/`port` lists by list-comprehension on `section=="host_bound"` / `"portable"`. An offsite row matches neither comprehension, so under R1–R5 alone it would be **silently dropped** from both endpoints — not shown "under its own heading," just absent. This resolves jackie-chan's U7 outright: rendering does not already generalize. `render.py` and both `app.py` call sites need a third list/section. This also affects R7 of the work order ("smallest diff, leaving R8 untouched") — the diff is one file larger than schema.py+app.py.
3. **R7 (version 1.2 → 1.3) has no live write path on the populated production DB.** The version string is not a constant — it's a row in SQLite's `meta` table, written only in two places: `RegistryDB.__init__` sets it to `"1.1"` *only if it has never been set* (`db.py:73-74`), and `app.py`'s `_seed_if_empty()` sets it from the seed filename's `-v(\d+\.\d+)` *only if `db.count() == 0`* (`app.py:110-122`). Confirmed live right now (`GET /health` → `"version":"1.2"`, `"agents":25`) — the DB is populated, so neither path fires on a restart. Bumping to `1.3` needs an explicit one-time write added somewhere (e.g. a startup migration check, or a manual `db.set_meta` call) or step 6 of the runbook ("`/health` ... reports 1.3") will fail even on an otherwise-correct deploy. This is squarely U9's question ("where the version string lives, and whether anything depends on '1.2'") — I found the mechanism while reading for D2/D3, handing it over rather than ruling on it.
4. **U4 appears resolved clear (bonus finding, not formally mine to rule on).** `registry/db.py`'s `CREATE TABLE agents (...)` declares `section TEXT NOT NULL DEFAULT 'host_bound'` and `binding TEXT DEFAULT 'unknown'` — plain `TEXT` columns, **no `CHECK` constraint, no enum**, nothing that would reject `'offsite'` at the SQL layer or require a migration. Full schema text is under D5/evidence below. I'm surfacing this for jackie-chan's formal U4 sign-off, not substituting for it.
5. **Open question I could not close (see Flags detail below):** whether `batman` (the SSH account used for backups) can read `data/registry.db` without `sudo` — the `data/` directory itself is root-owned (`drwxr-xr-x 3 root root`), consistent with the container running as root, but I did not look inside it, so I don't know the DB file's own permission bits.

None of D1 or D2 came back as the kind of surprise that changes the deploy's shape (§6 watch item (g)): the code is *not* baked into the image, and the DB *is* on the same host mount as the code. Both came back on the safe branch of ip-man's contingency.

---

## D1 — bind-mounted or baked into the image?

**Bind-mounted. Nothing is baked in — there is not even application code in the image to be shadowed.**

From `docker inspect agent-registry` [raw]:
```
"HostConfig": { "Binds": ["/home/batman/registry:/app:rw"] }
"Mounts": [{"Type":"bind","Source":"/home/batman/registry","Destination":"/app","Mode":"rw","RW":true,"Propagation":"rprivate"}]
```
Exactly one mount, covering the entire `/app` working directory. `/home/batman/registry`, `/share/home/batman/registry`, and the real path all resolve to the same inode [raw, `readlink -f`]:
```
/home/batman/registry        -> /volume1/home/batman/registry
/share/home/batman/registry  -> /volume1/home/batman/registry
```
So every file I read via `/share/home/batman/registry/...` is byte-identical to what the container sees at `/app/...`.

The `Dockerfile` [measured] confirms the other half: it installs the rclone static binary and `pip install Flask`, sets `WORKDIR /app`, and `CMD ["python","app.py"]` — **it contains no `COPY` of any application code whatsoever.** The image has no `app.py`, no `schema.py`, nothing; all code is supplied entirely by the bind mount at container start. This is a stronger guarantee than "the mount shadows a stale baked-in copy" — there's no baked-in copy to shadow.

**Conclusion:** editing the host files under `/share/home/batman/registry/` and restarting the container is fully sufficient. A rebuild (`docker compose up -d --build`) is only needed if the *Dockerfile itself* changes (new OS package, new pip dependency). This fix (schema.py/app.py/render.py, pure Python, no new imports beyond what's already used) needs no rebuild.

---

## D2 — where the DB lives, and a safe backup

**Location:** `REG_DB=/app/data/registry.db` [raw, docker inspect `Config.Env`], read by `registry/db.py`'s `DB_PATH = os.environ.get("REG_DB", "data/registry.db")` [measured]. Since `/app` is the bind-mount destination for `/home/batman/registry` (= `/share/home/batman/registry` = `/volume1/home/batman/registry`), the DB's real host path is:

```
/volume1/home/batman/registry/data/registry.db
```

**It is on the same single host bind mount as the code — not a separate Docker volume, and not inside the container's own writable (overlay2) layer.** There is only one mount defined for this container (see D1), and `data/` is a subdirectory of that same mounted tree. Restarting or even recreating the container does not touch this file (though per ip-man's note, recreation should still never happen "blind" — that guidance stands for other reasons, e.g. anonymous volumes elsewhere in a compose file, which don't apply here since there's only the one bind mount).

Two independent, weaker signals corroborate this without opening `data/` directly: (a) the docker-compose.yml comment — "The `/home/batman/registry` bind mount below carries code + `data/` (SQLite + journal + audit outbox) + `seed/` + `secrets/`" [measured]; (b) the earlier top-level `ls -la` (not descending into `data/`) showed a `data` directory owned `root:root`, last modified `Sep 26 20:26` — today, consistent with a live process (running as root, per the container's `Config.User` being unset) actively writing there.

**What else lives in `data/`, derived from code, not from opening the directory:** `registry/db.py`'s `_DATA_DIR` is `os.path.dirname(DB_PATH)` = `/app/data`; `app.py` defaults `JOURNAL_PATH` to `<data_dir>/journal.log` and `OUTBOX_DIR` to `<data_dir>/outbox` [measured, `app.py:41-49`]. `publisher.py`'s docstring independently confirms "the outbox (`data/outbox/`)" and that on success an artifact moves to `data/outbox/published/` [measured]. So `data/` holds: `registry.db` (SQLite), `journal.log` (append-only audit log), and `outbox/` (+ `outbox/published/`) — all on the one bind mount.

**Journal mode:** `registry/db.py` opens the connection with `sqlite3.connect(self.path, check_same_thread=False)` and never issues `PRAGMA journal_mode=WAL` or sets `isolation_level` [measured, full file read] — so SQLite's default rollback-journal mode applies (a transient `-journal` file during a write, not a persistent `-wal`/`-shm` pair). Every write path (`upsert`, `retire`, `set_meta`) calls `self.conn.commit()` immediately, so transactions are short.

**Recommended safe backup (for the runbook, not run today):**
```
sqlite3 /volume1/home/batman/registry/data/registry.db ".backup '<dest>/registry.db'"
```
This is SQLite's own online-backup API — safe for a live, open database regardless of journal mode, requires no downtime, and needs no assumption about whether a write happens to be mid-flight. (Given the default rollback-journal mode above, a plain `cp` taken at a quiet instant would likely also be consistent, but `.backup` removes the need to guess "quiet.") For `journal.log` and `outbox/`, which are plain files/artifacts rather than a live SQLite handle, a straightforward recursive copy of the whole `data/` directory (`cp -a` or `tar`) taken right after the `.backup` command is sufficient — worst case a mid-append line is truncated in the copy, which is a much smaller risk than a raw DB copy would carry.

---

## D3 — what a container restart actually does

**Live environment, in full** [raw, `docker inspect` `Config.Env`]:
```
REG_POLL=1
REG_PUBLISH=1
REG_PUBLISH_FOLDER_ID=1MWBVJyTKFap55LkJkAcgjWS9acqU8iIO
REG_POLL_SECONDS=60
REG_CRIER_URL=http://192.168.2.3:8787
RCLONE_CONFIG=/app/secrets/rclone.conf
REG_PUBLISH_REMOTE=gdrive_rw
REG_PORT=8788
REG_RCLONE=rclone
REG_SEED_MD=/app/seed/AGENT-REGISTRY-v1.2.md
REG_DB=/app/data/registry.db
```
**Both `REG_POLL` and `REG_PUBLISH` are ON in production.** A restart is not an inert code reload — it resumes live behavior almost immediately. Point by point, from reading `app.py` in full [measured]:

- **The process is fully re-executed.** `docker restart` kills the `python app.py` process and starts a brand-new one; there is no persistent Python state across a restart. Every module-level statement in `app.py` runs again from scratch.
- **DB open/init is idempotent — no data loss, no reseed.** `db = RegistryDB(DB_PATH)` (line 52) runs `CREATE TABLE IF NOT EXISTS` and a per-column `ALTER TABLE ... ADD COLUMN` wrapped in `try/except sqlite3.OperationalError: pass` (`db.py:64-71`) — both safe to re-run against an existing, populated table.
- **`_seed_if_empty()` (line 125, called unconditionally at import) will NOT re-seed.** It only acts `if db.count() == 0`. Confirmed live right now: `GET /health` → `"agents":25` [raw, see Live snapshot below]. A restart does not touch existing rows via this path.
- **The Crier poll thread starts unconditionally, gated only by `REG_POLL`:**
  ```python
  if os.environ.get("REG_POLL", "1") == "1":
      threading.Thread(target=_poll_loop, daemon=True).start()
  ```
  (`app.py:322-323`, default is "1" if unset). Live `REG_POLL=1` → **this thread starts immediately on every restart.** `_poll_loop` calls `_consumer.poll_once()` *before* its first `time.sleep(POLL_SECONDS)` (`app.py:313-319`), so the very first poll against `REG_CRIER_URL=http://192.168.2.3:8787` fires essentially at startup, then every 60 seconds (`REG_POLL_SECONDS=60`). By default this poll only advances liveness (`db.touch`) and the watermark for events it sees — it does **not** upsert full agent records; that legacy path (`ingest_registrations`) is off by default (`crier.py:250-260`, confirms ip-man's Q2 table row exactly).
  - Minor unresolved curiosity, not load-bearing: live `/health` reports `"crier":{"poll_seconds":300,...}` — a different number from the `REG_POLL_SECONDS=60` that governs the outer thread's sleep. I did not dig into `CrierConsumer.__init__` to see whether `300` is a separate staleness-threshold default rather than the actual poll cadence; leaving this for jackie-chan's broader crier.py read (U-items) rather than guessing.
- **The publish loop also starts unconditionally, gated on `_publisher.enabled` and `REG_PUBLISH_LOOP`:**
  ```python
  if _publisher.enabled and os.environ.get("REG_PUBLISH_LOOP", "1") == "1":
      threading.Thread(target=_publish_loop, daemon=True).start()
      threading.Thread(target=_safe_drain, daemon=True).start()   # <- runs once, immediately
  ```
  (`app.py:334-337`). `Publisher.enabled` defaults on unless `REG_PUBLISH` is `"0"/"false"/"no"`, or the rclone binary/config is missing (`publisher.py:28`, docstring + `__init__`). Live: `REG_PUBLISH=1`, rclone is installed by the Dockerfile, and `RCLONE_CONFIG=/app/secrets/rclone.conf` points at a real, working OAuth token (per ip-man's note; I did not open that file myself). So `_publisher.enabled` is true in production, meaning **a restart fires an immediate outbox-drain attempt to the real `gdrive_rw` Google Drive remote**, and then retries every `REG_PUBLISH_LOOP_SECONDS` (120s default, not overridden here) regardless of whether any new write happened. This is a genuinely live integration, not a no-op — worth calling out plainly in the runbook's verify step.
- **`_BUILD` (used by `/health`) is resolved once, at import, in this order** (`app.py:64-90`): `REG_BUILD` env (unset in production) → a `BUILD` file dropped beside `app.py` (found: contains exactly `ede80e1`, no trailing content) → `git rev-parse --short HEAD` run against the app's own directory (moot — no `.git` directory exists under `/share/home/batman/registry/`, confirmed by the earlier `ls -la`/no `.gitignore` check) → `"unknown"`. **Live-confirmed:** `GET /health` → `"build":"ede80e1"`. This means **the deploy must update the `BUILD` file to the new commit hash**, or `/health`'s `build` field will keep reporting the pre-fix commit even after the code changes — a concrete addition for runbook step 4/6 that wasn't in ip-man's original 7-step sketch.

**Bottom line for D3:** a restart is safe with respect to data (idempotent seeding/schema init), but it is *not* a quiet reload — it resumes live Crier polling (near-instantly) and live Google Drive publishing (near-instantly) against real external systems. The runbook's verify step should expect this, not be surprised by it.

---

## D4 — Wonderland comparison: bishop's citation vs. the NAS

**Bishop's citation does not match. The NAS runs a later commit than reported.**

ip-man's note: "It was last reported at `f5a7c8b` with 41/41 tests, and the NAS's `~/registry/` mirrors it [reported-by bishop, `TS-20260912-bishop-009.006`]." I did not trust this — I cloned `terrence-adams/Wonderland` (found via `gh repo list`; there is no local checkout under `C:\Repo`) and hashed both candidate commits' `services/registry` files against the NAS's own hashes.

**NAS file hashes** [raw, `sha256sum` over SSH]:
```
d9717f3b6fddbd19b04934fff014e7440a3bf32549fc8e461b618c40b24de3b8  app.py
688fcaad1b0a4afb54f4efa9b5eda5ef5855bbf4edbc0d0d85ec8e26778cc8fc  registry/crier.py
7f16d6967828b6c44d19dcf9d3acb34ccbfe3a92aaaab83120d0d923678f0877  registry/db.py
2f3acf5d6bc7518fcb31cf046d4f4897d0ace1db2ad529bef2e8fa7a2d450abc  registry/journal.py
e6fa206a8977659d88d5be522be19ea5910eed121c22bfff233586237024bf3b  registry/parse_md.py
c4e839be8c0084c695ea7a78465a028f3be0d6bea2104e261065a78b9a607208  registry/publisher.py
3173a3f6a04627c2599af007318308908208f5484def491dc5148a9075c449f4  registry/render.py
8ac1fa806d4811fcc96fa3ffe24ba407b86608472b4ab8f01cd4e84a8b80377c  registry/schema.py
```

**`git show f5a7c8b:services/registry/<file>` hashes** — 3 of 8 differ from the NAS (`app.py`, `journal.py`, `publisher.py`); `crier.py`, `db.py`, `parse_md.py`, `render.py`, `schema.py` match.

**`git show ede80e1:services/registry/<file>` hashes — all 8 of 8 match the NAS byte-for-byte.**

`ede80e1`'s commit message: *"registry: stop the audit publisher overwriting board records (TS-20260913-bishop-006)"* — exactly explains the 3-file delta (app.py/journal.py/publisher.py are the audit-publish pipeline; schema/db/crier/parse_md/render are untouched by that fix, hence identical between the two commits). `git log --oneline -- services/registry` [raw] shows `ede80e1` sits directly after `f5a7c8b` (with one unrelated commit — Town Watcher — between them in the full history):
```
ede80e1 registry: stop the audit publisher overwriting board records (TS-20260913-bishop-006)
4924058 Add Town Watcher app under services/townwatcher/
f5a7c8b registry: publish audit outbox to the board (Condition 1, TS-20260913-bishop-001)
```
Confirmed `ede80e1` is the current tip, not just an ancestor: `git rev-parse main` and `git rev-parse origin/main` both return `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf` [raw].

**Timestamps corroborate this independently.** The NAS's `ls -la registry/` [raw] shows `schema.py`/`db.py`/`crier.py` last modified `Sep 13 07:14-07:15`, while `app.py`/`journal.py`/`publisher.py` — precisely the 3 files that differ from `f5a7c8b` — are `Sep 13 21:18`, i.e. edited later the same day, consistent with the `ede80e1` fix landing after an earlier deploy at `f5a7c8b`. The container itself was `Created` `2026-09-14T06:08:28Z` [raw], after all these file timestamps, consistent with a `docker compose up -d --build` picking up the final (`ede80e1`) file versions.

**Conclusion: the baseline branch point is `ede80e1` (full `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf`), on `main`, not `f5a7c8b`.** A matching commit was found, so per ip-man's rule, no fallback is needed — I did **not** create `C:\Repo\townsquare\registry-offsite\` or commit anything there, since that path is only for the no-match case. `offsite-binding` should be cut from `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf` in `terrence-adams/Wonderland` when Implement begins. I did not check the "41/41 tests" half of bishop's claim (out of scope for D4 as framed — that's a test-suite question, ronda-rousey/jackie-chan territory), only the file-identity half.

---

## D5 — exact file list and pre-deploy hashes

**Files that need to change for this fix (confirmed in-scope):**

| File | NAS path | SHA-256 (= `ede80e1` blob) | Why |
|---|---|---|---|
| `schema.py` | `/share/home/batman/registry/registry/schema.py` | `8ac1fa806d4811fcc96fa3ffe24ba407b86608472b4ab8f01cd4e84a8b80377c` | R1 (`SECTIONS`, `BINDING_RE`), R2 (`derive_section`), R3 (new `offsite_violations`) |
| `app.py` | `/share/home/batman/registry/app.py` | `d9717f3b6fddbd19b04934fff014e7440a3bf32549fc8e461b618c40b24de3b8` | R3 (`/register` calls the new check), R4 (`/authorized_keys`), R5 (`/mesh`), R6 (`/tables`, `/registry?format=md` need a third list), R7 (version-bump call site, mechanism TBD — see Flag 3) |
| `registry/render.py` | `/share/home/batman/registry/registry/render.py` | `3173a3f6a04627c2599af007318308908208f5484def491dc5148a9075c449f4` | R6 — **newly identified, see Flag 2.** `render_tables`/`render_snapshot` are hard-coded to exactly 2 lists |

**Files checked, expected to remain byte-identical after the fix (baseline for regression verification):**

| File | NAS path | SHA-256 (= `ede80e1` blob) | Why unchanged |
|---|---|---|---|
| `registry/db.py` | `/share/home/batman/registry/registry/db.py` | `7f16d6967828b6c44d19dcf9d3acb34ccbfe3a92aaaab83120d0d923678f0877` | No CHECK/enum on `section`/`binding` (U4, see Flag 4); R8 doesn't touch it |
| `registry/crier.py` | `/share/home/batman/registry/registry/crier.py` | `688fcaad1b0a4afb54f4efa9b5eda5ef5855bbf4edbc0d0d85ec8e26778cc8fc` | R8 explicit: "crier.py and the legacy flag" do not change |
| `registry/journal.py` | `/share/home/batman/registry/registry/journal.py` | `2f3acf5d6bc7518fcb31cf046d4f4897d0ace1db2ad529bef2e8fa7a2d450abc` | Unrelated to binding/section |
| `registry/publisher.py` | `/share/home/batman/registry/registry/publisher.py` | `c4e839be8c0084c695ea7a78465a028f3be0d6bea2104e261065a78b9a607208` | Unrelated to binding/section |
| `registry/parse_md.py` | `/share/home/batman/registry/registry/parse_md.py` | `e6fa206a8977659d88d5be522be19ea5910eed121c22bfff233586237024bf3b` | Legacy seed/board parser, untouched by R1–R7 |

All 8 hashes above were computed twice independently — once via `sha256sum` over SSH on the live NAS files, once via `git show ede80e1:services/registry/<path> | sha256sum` on the cloned Wonderland repo — and agree exactly. This is the "clean pre-deploy baseline to diff against later" ip-man asked for: post-deploy, the 3 "will change" files should hash *differently* from this table (confirming the fix landed) and the 5 "expected unchanged" files should hash *identically* (confirming nothing unintended moved).

`db.py`'s full schema, for the record (U4 evidence) [measured, `registry/db.py:15-39`]:
```sql
CREATE TABLE IF NOT EXISTS agents (
    agent        TEXT PRIMARY KEY,
    section      TEXT NOT NULL DEFAULT 'host_bound',
    ...
    binding      TEXT DEFAULT 'unknown',
    ...
);
```
No `CHECK (section IN (...))`, no `CHECK (binding IN (...))`, no foreign key, no enum type (SQLite has none natively, but nothing simulates one here either). Plain `TEXT` columns validated only in application code (`schema.py`).

---

## Runbook sketch — concrete form of ip-man's 7 steps

**Nothing below was run.** Every command is labeled with where/how it runs. This is prep for later, gated on Sensei's go per ip-man's note (§5): "The writes and the restart are run by Sensei himself, one command at a time... or by someone he names. A subagent never runs them on a relayed yes."

**Step 1 — confirm live hashes still match the baseline (stop if not).**
*Where:* any machine with SSH access to the NAS (e.g. Sensei's terminal). *How:* non-interactive SSH as `batman`.
```
ssh nas "sha256sum /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py \
  /share/home/batman/registry/registry/db.py \
  /share/home/batman/registry/registry/crier.py \
  /share/home/batman/registry/registry/journal.py \
  /share/home/batman/registry/registry/publisher.py \
  /share/home/batman/registry/registry/parse_md.py"
```
Diff line-by-line against the D5 table above. Any mismatch → stop (per work-order watch item (f): bishop may have redeployed independently).

**Step 2 — pre-deploy reads, taken twice (e.g. a minute apart).**
*Where:* any LAN machine (plain HTTP, no SSH needed) for the four `curl`s; a machine with Python for the projection script.
```
curl -s http://192.168.2.3:8789/authorized_keys
curl -s "http://192.168.2.3:8789/authorized_keys?exclude=claude-app"
curl -s http://192.168.2.3:8789/mesh
curl -s "http://192.168.2.3:8789/journal?limit=5"
curl -s http://192.168.2.3:8789/health
python C:\Repo\townsquare\docs\decision-6-projection.py <out_path_1>
```
(`decision-6-projection.py` [measured] itself does a `GET /registry` and writes a sorted, hashed, claude-app-excluded projection — this is "the projection" ip-man's step 2 refers to. It prints its own SHA-256, so no separate hashing step is needed.)

**Step 3 — back up code files and the DB.**
*Where:* SSH session on the NAS as `batman`. Recommend backups live **outside** the bind-mounted tree (e.g. a sibling `registry-backups/` directory), so a backup never ends up inside the container's own `/app` view.
```
ssh nas "mkdir -p /share/home/batman/registry-backups/preoffsite-$(date -u +%Y%m%dT%H%M%SZ)"
# code (plain, static files — cp is fine):
ssh nas "cp /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py \
  /share/home/batman/registry-backups/preoffsite-<ts>/"
# DB (live, SQLite-safe backup — see D2):
ssh nas "sqlite3 /share/home/batman/registry/data/registry.db \
  \".backup '/share/home/batman/registry-backups/preoffsite-<ts>/registry.db'\""
# journal + outbox (plain copy of the rest of data/):
ssh nas "cp -a /share/home/batman/registry/data/journal.log \
  /share/home/batman/registry/data/outbox \
  /share/home/batman/registry-backups/preoffsite-<ts>/ 2>/dev/null || true"
```
*Caveat (Flag 5): confirm `batman` can actually read `data/registry.db` before relying on this — I did not check its permission bits. If it's root-owned and non-world-readable, these commands need `sudo` on the NAS.*

**Step 4 — copy the reviewed files, then verify in place.**
*Where:* from wherever the reviewed fix lives after peer review (e.g. Venom), to the NAS, as `batman`. Also update the `BUILD` file (Flag/D3 finding) so `/health` reports the new commit.
```
scp <reviewed>/schema.py  batman@192.168.2.3:/share/home/batman/registry/registry/schema.py
scp <reviewed>/app.py     batman@192.168.2.3:/share/home/batman/registry/app.py
scp <reviewed>/render.py  batman@192.168.2.3:/share/home/batman/registry/registry/render.py
ssh nas "echo -n '<new-short-sha>' > /share/home/batman/registry/BUILD"
ssh nas "sha256sum /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py"
```
Compare against the reviewed files' own local `sha256sum`, computed before the copy.

**Step 5 — restart the container.**
*Where:* SSH session on the NAS, as `batman` (same account already used for `docker inspect`/reads this session, so it already has the needed Docker permission).
```
ssh nas "docker restart agent-registry"
```
Per D3: this immediately restarts Crier polling (first poll near-instant, then every 60s) and immediately attempts an outbox drain to the live `gdrive_rw` Google Drive remote, then every 120s thereafter. Expect this — it is not a quiet reload.

**Step 6 — verify, read-only.**
```
curl -s http://192.168.2.3:8789/health
curl -s http://192.168.2.3:8789/authorized_keys
curl -s "http://192.168.2.3:8789/authorized_keys?exclude=claude-app"
curl -s http://192.168.2.3:8789/mesh
curl -s "http://192.168.2.3:8789/journal?limit=5"
python C:\Repo\townsquare\docs\decision-6-projection.py <out_path_2>
ssh nas "docker logs agent-registry --since 5m"
```
Expect: `/health` `"ok":true`, `"build":"<new-short-sha>"`; version `"1.3"` **only if** Flag 3's version-bump mechanism was actually implemented — if not, expect `"1.2"` and treat that as a known, already-flagged gap, not a deploy failure. Everything else from step 2 should be byte-identical (feed, `/mesh`, the projection's own printed SHA-256, `/journal?limit=5`'s newest entry). Logs show no traceback.

**Step 7 — rollback, if anything fails.**
```
scp <backup>/schema.py  batman@192.168.2.3:/share/home/batman/registry/registry/schema.py
scp <backup>/app.py     batman@192.168.2.3:/share/home/batman/registry/app.py
scp <backup>/render.py  batman@192.168.2.3:/share/home/batman/registry/registry/render.py
ssh nas "echo -n '<old-build-id>' > /share/home/batman/registry/BUILD"
ssh nas "docker restart agent-registry"
```
Re-run step 6 afterward. The DB backup should not be needed for this fix (it makes no schema/data migration), but is in place per D2 as defense-in-depth in case a copy step goes to the wrong path.

---

## Live snapshot at time of this report (informational only, not a deploy pre-check reading)

`GET /health` [raw, curl, 2026-09-26 ~20:37 UTC]:
```json
{"agents":25,"build":"ede80e1","crier":{"events_known":1098,"last_poll_error":null,"last_poll_ok":"2026-09-26T20:35:08Z","ok":true,"poll_seconds":300,"stale":false,"watermark":463},"crier_watermark":"463","last_poll_ok":"2026-09-26T20:37:17Z","ok":true,"possibly_stale":false,"service":"agent-registry","staleness":{"age_seconds":33.483285,"interval_seconds":60,"last_poll_ok":"2026-09-26T20:37:17Z","possibly_stale":false,"reasons":[]},"version":"1.2"}
```
This single GET is the only live-service call made this session; it directly corroborates the `_build_id()`/`_seed_if_empty()` analysis in D3 (build=`ede80e1` matches the `BUILD` file; version=`1.2` and agents=25 confirm the DB is populated and neither version-bump path has fired).

---

## Commands run this session (all read-only)

- `ssh nas "docker inspect agent-registry"` — mounts, env, image, labels.
- `ssh nas "ls -la /share/home/batman/registry/"` — top-level listing only.
- `ssh nas "readlink -f /home/batman/registry; readlink -f /share/home/batman/registry"`.
- `ssh nas "ls -la /share/home/batman/registry/registry/"` — the nested package dir (not `data/`, not `secrets/`).
- `ssh nas "cat /share/home/batman/registry/Dockerfile"`.
- `ssh nas "cat /share/home/batman/registry/docker-compose.yml"`.
- `ssh nas "cat /share/home/batman/registry/BUILD"`, `.../requirements.txt`, `.../config.env`.
- `ssh nas "ls -la /share/home/batman/registry/tests/"`.
- `ssh nas "cat /share/home/batman/registry/.gitignore"` (none found).
- `ssh nas "sha256sum /share/home/batman/registry/app.py /share/home/batman/registry/registry/*.py"`.
- `gh repo list terrence-adams` — located `terrence-adams/Wonderland` (private).
- `gh repo clone terrence-adams/Wonderland -- --no-checkout` into the scratchpad (a full checkout hit Windows path-length limits on an unrelated `services/townwatcher` test fixture; `--no-checkout` avoided writing any files).
- `git log --oneline -- services/registry`, `git ls-tree -r ede80e1 -- services/registry`, `git rev-parse main / origin/main / ede80e1`, `git show <rev>:<path> | sha256sum` for both `ede80e1` and `f5a7c8b` — all local, against the cloned Wonderland repo.
- `curl -s http://192.168.2.3:8789/health` — one live, read-only GET (see Live snapshot above).

**Not run:** anything under `secrets/` or `data/`; any `docker restart`/`docker exec`/write to the NAS; any push of the Wonderland clone or this repo.

I wrote nothing to the NAS and restarted nothing.
