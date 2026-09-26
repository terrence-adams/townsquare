<!-- extracted (not a plain splice: this SubagentHandback delivered the document inside a larger report, delimited by BEGIN FILE/END FILE markers, because ip-man has no write tool and asked the session to slice it out; the surrounding preamble/summary text is not part of this file) sha256=f9cdded7cb0527394de3ddf3f98eb1d14ead7f833d66d89337a2b0f7301305fa source=C--Workspace/6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb/subagents/agent-a7f01575feaa11a9b.jsonl:87 message=msg_011CfSp2qWVQuhQcgcWYJcrs -->
# Registry `binding: offsite`: ruling on gsp's security review (G1–G5, default-deny, runbook s1–s7)

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** design ruling only. I only read; I wrote, ran, built and deployed nothing.
**Rules on:** `C:\Repo\townsquare\docs\gsp-registry-offsite-security-review-20260926.md` ("the review"; commit `6510fb4` on `internal`, reported-by the session).
**Amends:** two documents in `C:\Repo\townsquare\docs\`:
- `ip-man-registry-offsite-binding-design-20260926.md` ("the note", SHA-256 `3f86d159…`);
- `ip-man-registry-offsite-addendum-1-20260926.md` ("Addendum 1", SHA-256 `64f14c4d…`).

Neither is edited. Where this ruling conflicts with either, this ruling governs.
**Proposed path:** `C:\Repo\townsquare\docs\ip-man-registry-offsite-security-ruling-20260926.md`, on branch `internal`, not pushed.

**Recusal.** The note's recusal carries over and widens. This ruling answers:
- G1–G5;
- the definition of an offsite row;
- default-deny's place in R4;
- s1–s7.

If any of these is referred to the Tribunal, I am conflicted under rule 5 limb (ii) and will not sit.

**Labels**, as in the chain:
- *measured*: a file I read this run;
- *inferred*: reasoned, not executed;
- *reported-by X*: X's claim, which I did not check.

**Shorthand**
- **From the review:**
  - **G1–G5**: its findings on the fix;
  - **s1–s7**: its refinements to the runbook;
  - **R3c**: the write-time check it proposes under G1;
  - **T4e–T13**: its proposed tests;
  - **run NN**: one of its proof-of-concept runs.
- **From the note and Addendum 1:**
  - **R1–R8**: the requirements;
  - **T1–T12**: the tests;
  - **S1–S5**: the security claims;
  - **P1**: the live captures;
  - **the P2 draft**: the pinned registration body;
  - **the feed**: `GET /authorized_keys`, in both of its forms (with and without `?exclude=`).
- **U10–U12**: jackie-chan's findings on the note's read-requests of those numbers.
- **D34**: the standing LAN-trust write model.
- **D28**: "the key belongs to the host".
- **Charter 2.0 Part C:**
  - **C1** labels a question at its second round of disagreement;
  - **C4** keeps a settled question settled unless one of its stated grounds is met.
- **Explicit binding**: a binding whose stripped value matches `BINDING_RE` after R1, which means `host:<Name>`, `portable` or `offsite`.
- **Offsite row**: defined in §2.1.

## 0. Verdict

- **G1 and G2 are confirmed with gsp's fixes. G3, G4 and G5 are adopted.** I dispute none of the five. Under C1 this reply is therefore not a second round, and it carries no label.
- **gsp's default-deny call stands as R4's rule** (§2.3). The call was his to make, and it matches the lean I gave in the note.
- **I add one placement detail:** the G4 lock also covers the journal write (§2.6). It changes neither which writes are accepted nor what is stored. gsp checks it with the rest of the lock's span when he reviews the hunks.
- **This is ready for Helio's GAME PLAN** as soon as the session has saved and committed this ruling. No further design round is needed, and nothing goes back to jackie-chan or francis-ngannou before Implement.
- **ronda-rousey's test additions are in §4.** She writes them against the interface names fixed in §3.

## 1. What I checked myself

I read the baseline at `ede80e1`, in jackie-chan's clone: `C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb\scratchpad\jackie-wonderland\services\registry\`. The checkout's CRLF line endings do not change line numbers. Everything below is measured.

- **`registry/schema.py`, lines 80–118: G1's mechanism is exactly as the review states it.**
  - Once `offsite` is in `SECTIONS`, `section: offsite` passes the membership check.
  - With no binding, or with `unknown`, `derive_section` returns `""`, so the contradiction check is skipped.
  - `normalize_record` then fills the binding with `unknown` and keeps the body's section, through `setdefault`.
- **`app.py`, lines 178–204:** `at` is computed at line 193, outside any lock, and before both `before` (line 195) and `upsert` (line 196).
- **`registry/db.py`:**
  - lines 101–111: a write whose `at` is older than the stored `applied_at` has all of its fields dropped;
  - line 64: every thread shares one `sqlite3` connection;
  - lines 153–162: `touch` and `retire` write none of `binding`, `section`, `pubkey` or `host_address`.
- **`registry/journal.py`, lines 59–97:** `Journal.record` takes its own lock around sequence allocation and both of its writes.
- **`registry/crier.py`, lines 291–300:** the legacy path rejects and skips any record that fails `validate_record`.
- **The review's `runs\results.json` and run 02's `authorized_keys`:** runs 02–05, 13–15 and 18–20 match the review's §3 table.

I re-ran nothing.

## 2. Rulings

### 2.1 What an offsite row is

G1 raises a definitional question, and I settle it here before anyone disputes it. I adopt the review's rule text for the note, Addendum 1 and this ruling:
- **An offsite row is a row whose stripped binding is `offsite`, or whose section is `offsite`.**
- **S1 applies to both kinds:** an offsite row holds no key and no address.
- **The two fields agree on every accepted write.** R3c (§2.2) enforces this on every `/register` write and every legacy-path write, since both run `validate_record`.
- **Both kinds stay out of the feed,** through default-deny (§2.3).
- **Only a direct DB edit can make a row whose two fields disagree.** That case joins S3's other direct-edit residuals.
  - A later partial `/register` could re-bind such a row to `unknown`/`host_bound`. Default-deny would then publish any key the row holds.
  - I do not widen R3b to catch this. Widening it would change which writes are accepted, a change no reviewer has seen, and the starting state it guards against is one only root can create.

**Why this fault is mine.**
- The note chose `binding` as the security field, because a stored section drifts.
- R1 then created a section value that `/register` could set without the binding.
- Addendum 1's R6 renders rows into tables by `section`.
- So the registry could present a row as offsite while the security gate read it as a host.

This is the class of fault I corrected in Addendum 1: a check reads one field while a related field moves on its own.

### 2.2 G1: confirmed. R3c goes in `validate_record`

- **The rule:** if the body's section passes `is_offsite` and its binding does not, return 400 with "section 'offsite' requires binding 'offsite'".
- **Where it goes:** in `validate_record`, beside the contradiction check, because it is that check's missing offsite case.
  - It needs only the body.
  - Every path that validates inherits it, including the legacy path, which rejects on a validation failure (§1).
  - No line of `crier.py` changes, so R8 holds.
- **Its effect:** the three G1 bodies get 400, and the host row stays unchanged (runs 08–10, measured by gsp). The P2 draft sends no section, so T1 does not move (hardened T1, measured by gsp).
- **Rejected: default-deny alone.** It keeps the key out of the feed, but three problems remain:
  - the row still displays under "Offsite agents" while it holds a key;
  - a later partial write flips the row to `unknown`/`host_bound`, and the feed then publishes the key;
  - R3b cannot see that flip, because the row's binding was never offsite.

### 2.3 Default-deny is gsp's call, and it becomes R4's rule

The feed publishes a row's key only if `key_publishable(row)` holds. That requires all four of these:
- the row is active (the feed's loop already selects only active rows);
- its stripped `pubkey` is non-empty;
- `row["section"] == "host_bound"`, matched exactly;
- `not is_offsite(row["binding"])`.

`key_publishable` is a pure function in `schema.py`, and both forms of the feed call it.
- On P1's data it changes no byte (measured by gsp).
- It can remove lines from the feed. It can never add one.

**I confirm gsp's rejection of a rule based on binding alone.**
- It would drop bishop's key, because his row is `unknown`/`host_bound`. That would break Done-when (5).
- That rule belongs on bishop's thread, once the bindings have been repaired.

Watch-for (b) is amended to match (§8).

### 2.4 G2: confirmed. Strip before testing, and use one predicate

- **The predicate:** `is_offsite(v) -> bool`, a pure function in `schema.py`, defined as `str(v or "").strip().lower() == "offsite"`.
- **Where it is used:** R3a, R3b, R3c and `key_publishable` all call it. None of those checks writes its own offsite comparison inline.
- **R3b tests the stripped binding.** So `""`, `"  "` and `"\t"` all count as no binding (runs 12 and 13, measured by gsp).
- **Two deliberate exceptions stay exact.**
  - `derive_section`'s new branch compares the stripped value exactly. This keeps it consistent with `BINDING_RE`, which rejects `Offsite` at validation.
  - R6 selects `section == "offsite"` exactly, like its two sibling lists.
  - Neither is a security gate: `derive_section` only sees bindings that validation has already accepted, and R6 only chooses which table a row is shown in.

### 2.5 G3: adopted. `unknown` is not an explicit binding

- **The rule.** For an existing offsite row, R3b passes only when the body carries an explicit binding.
  - An absent, empty, whitespace-only or `unknown` binding gets 400.
  - The error reads: "agent '<name>' is bound offsite: send binding explicitly (host:<Name>, portable or offsite)".
  - This is measured by gsp in run 15.
- **This supersedes one sentence of Addendum 1's R3b:** the one that listed `unknown` among the deliberate re-binds. That sentence was my error.
  - `unknown` is the service's own marker for "not stated"; `normalize_record` writes it.
  - So a body carrying `unknown` most likely came from a template, not from a decision to re-bind.
- **Deliberate re-binds still work, as D34 requires.** A body can state `host:<Name>` or `portable`, with or without a key. After that the row is no longer offsite, and its key is handled like any other host or portable row's key.
- **Rows that are not offsite are unaffected.** T10 holds for them, unchanged.

### 2.6 G4: adopted, and it closes more than the review claims

**The rule.**
- Add one module-level `threading.Lock` in `app.py`, named `_REGISTER_LOCK` and used as a context manager (`with _REGISTER_LOCK:`). The name is fixed here so that T13 can refer to it.
- `/register` holds the lock through this whole sequence:
  1. R3's `db.get`;
  2. R3 itself;
  3. `normalize_record`;
  4. computing `at`;
  5. `before`;
  6. `db.upsert`;
  7. `after`;
  8. `_journal.record`.
- Validation, including R3c, runs before the lock is taken. `_publish_async()` runs after it is released.
- `/retire` and `/poll` do not change.

**The lock closes both orders of the race.** This is inferred from the code in §1.

The review measured one order (run 19):
- the offsite write lands second;
- the row then sits offsite, holding the key;
- `/agent` serves the key, and the journal records it.

The order Addendum 1 traced is worse:
- the offsite write lands first, and the write carrying a key but no binding lands second;
- `normalize_record` re-binds the row to `unknown`/`host_bound`;
- the feed then **publishes** the key.

That is a silent re-bind, exactly what R3b exists to stop. Under the lock, whichever write takes the lock second is refused:
- by R3b, when the offsite write went first;
- by R3a's merge rule, when the keyed write went first.

So S5's race residual is withdrawn for every `/register` writer. Run 20 (measured by gsp) shows the lock working in run 19's order.

**It also closes a fault that predates this fix** (inferred, by gsp and by me).
- `at` has one-second resolution and is computed outside any lock.
- So a write that computes its `at` first but lands second is dropped as stale, and its caller still gets `ok: true`.
- Inside the lock, `at` never decreases in the order writes are applied, unless the clock steps backwards.

**Why the journal write is inside the lock.**
- For any one agent, each journal entry's `before` should equal the previous entry's `after`.
- With the journal write outside the lock, two `/register` writes can be journaled in the opposite order to the one they were applied in.
- Inside it, the audit chain follows the order of application, at the cost of one level of indentation.
- It cannot cause colliding sequence numbers or a deadlock. The journal's own lock is always taken second, and `/retire` takes only that inner lock (§1).

**An assumption, recorded:** the service runs as one `python app.py` process. This is reported-by francis (the Dockerfile's `CMD`) and by jackie (the threaded server). An in-process lock serializes that one process only (Watch-for (m)).

**What the lock covers:**
- It serializes `/register` writers.
- The poll thread's `touch` and `/retire` stay outside it. Neither writes any of the four fields S1 is about (§1).
- The legacy path, if it were ever switched on, would write outside the lock. It cannot write a key (jackie, U10).

**Rejected: a database transaction instead of the lock.**
- All threads share one connection, and so one transaction. A transaction therefore would not isolate one request from another.
- Real isolation would need a connection per request. That changes `db.py`, which R8 keeps unchanged.

**Rejected: keeping the race as an accepted residual,** as Addendum 1 did. It was a residual only because I had not seen a cheap way to close it. A few lines close both orders.

### 2.7 G5: adopted

G5 is built into `key_publishable` (§2.3):
- the deny side normalizes the stored binding through `is_offsite`;
- the allow side matches `section == "host_bound"` exactly, so a malformed stored section fails closed.

This is measured by gsp in runs 17 and 18.

### 2.8 S1–S5 as they now stand

- **S1** holds for both kinds of offsite row:
  - through `/register`, by R3a, R3b, R3c, G2 and G3;
  - at rest, by G4.
- **S2** holds as restated in Addendum 1, with G2's wording.
- **S3:** the feed drops the key of any row whose section is not exactly `host_bound`, or whose binding is offsite, whoever wrote the row. Direct DB edits stay outside the model, including rows whose two fields disagree (§2.1).
- **S4** is unchanged.
- **S5** splits three ways:
  - the race residual is withdrawn (G4);
  - D34's deliberate re-bind remains an accepted residual;
  - a partial write that adds a key to a *host* row remains bishop's to fix. A *portable* row's key no longer reaches the feed.

### 2.9 What I leave as it is

- **F6 stays out of this diff.**
  - It is rated Low.
  - It is orthogonal to decision 6, because R3a already forbids any key on an offsite row.
  - Changing it would change validation on the path that carries host keys, and that needs its own regression check.
  - The review claims no C4 ground to reopen Addendum 1's scope ruling, and I see none.

  F6 stays on bishop's thread.
- **R5 and R7 stay withdrawn.** `/mesh` already lists only rows whose section is exactly `host_bound`, which leaves out every offsite row that `/register` can now produce.
- **The review's other ratings stand as rated,** with their routing unchanged:
  - a stale write gives no signal (Low);
  - the agent name is stored unstripped (Low);
  - partial writes fill in defaults.

## 3. The requirements as they now stand (bruce-lee builds exactly this)

Three files change: `registry/schema.py`, `app.py` and `registry/render.py`.

| Item | Where | What |
|---|---|---|
| R1 | `schema.py` | As in the note. |
| R2 | `schema.py` | As in the note: `derive_section("offsite")` returns `"offsite"`, matching the stripped value exactly. |
| `is_offsite(v) -> bool` | `schema.py` | §2.4. |
| R3c | `schema.py`, in `validate_record` | §2.2. |
| R3a | `schema.py`, in `offsite_violations(existing, incoming) -> list[str]` | As in Addendum 1, with its trigger tested through `is_offsite`. |
| R3b | the same function | As in Addendum 1, amended by §2.4 and §2.5. |
| R4 | `schema.py`, as `key_publishable(row) -> bool`, called by both forms of the feed in `app.py` | §2.3 and §2.7. |
| The lock | `app.py`, `_REGISTER_LOCK` | §2.6. |
| R6 | `render.py`, plus the two call sites in `app.py` | As in Addendum 1. |
| R5, R7 | none | Withdrawn. |
| R8 | none | Stands. `crier.py` inherits R3c through `validate_record`; its file does not change. |

**The interface names are fixed, so that ronda can write her tests first:**
- `is_offsite`, `key_publishable` and `offsite_violations` live in `registry/schema.py`;
- `_REGISTER_LOCK` lives in `app.py`;
- `/register` calls `schema_mod.offsite_violations(...)` through the module attribute, as Addendum 1's snippet shows, so a test can wrap it.

**Error messages.** Tests match substrings, which is the existing suite's pattern (jackie, U12). So each message only has to name the right terms:
- R3a's message names `offsite` and the offending field;
- R3b's and R3c's messages name `offsite` and `binding`.

## 4. Tests: what ronda-rousey must cover before she writes anything

**How every test is built** (jackie, U12 and §3(b); the review, §10):
- It creates its own rows, and depends on no other test having run.
- Every behaviour test goes through `POST /register`, then checks the stored row (via `/agent/<name>`), the journal, and both forms of the feed.
- Unit tests of the three pure functions may be added. They do not replace the round trip.
- Any row "written straight to the DB" goes into the isolated test DB only.

**The full set** is T1–T12 as amended in Addendum 1 §3, plus the adversarial cases, plus the following.

1. **T4e (G2).** With an offsite row in place, send a binding of `""`, then `"  "`, then `"\t"`, each with a valid key.
   - Each returns 400.
   - The row, the journal and the feed are all unchanged.
2. **T4f (G3).** With an offsite row in place:
   - `{binding: "unknown", pubkey: K}` returns 400;
   - `{binding: "unknown"}` on its own returns 400, and the row stays `offsite`/`offsite`;
   - then a deliberate re-bind, `{binding: "host:x", pubkey: K}`, returns 200 (D34). This last case keeps R3b from blocking too much. After it, the row is no longer offsite.
3. **T6b (default-deny).** In both forms of the feed:
   - a `portable` row with a key is absent;
   - an `unknown`/`host_bound` row with a key (bishop's shape) is present.
4. **T6c.** An `unknown`/`offsite` row with a key, written straight to the DB, is absent from both forms of the feed.
5. **T6d (G5).** A row with a key, binding `" Offsite\n"` and section `host_bound`, written straight to the DB, is absent from both forms of the feed.
6. **T9b (R3c).** Each of these returns 400:
   - `{section: offsite, pubkey: K}` on a new name;
   - `{binding: unknown, section: offsite}` on a new name;
   - `{section: offsite}` on a host row that has a key. That row also stays unchanged: it is still on `/mesh`, and its key is still in the feed.
7. **T13 (G4).** On a new name, send two writes: `{binding: offsite}`, and `{pubkey: K}` with no binding. Force them to race at R3, once for each order in which they can land.
   - **With the lock,** each order gives exactly one 200 and one 400. At no point may `/agent/<name>`, the feed or any journal `after` show the row as offsite while it holds K.
   - **The test proves its own forcing.** Run the same interleaving with `_REGISTER_LOCK` replaced by a no-op context manager, and assert that the race does happen (both writes return 200). Without that control, a pass could just mean the race was never forced.
   - **Force it deterministically.** Wrap `offsite_violations` so that it waits on a barrier or an event, and give that wait a timeout. Under the real lock the second thread cannot enter R3 until the first has left, so a two-party wait with no timeout would deadlock.
8. **T10, with its scope made explicit.** `binding: unknown` behaves as it does on the baseline, for rows that are not offsite.
9. **Regression.** The existing suite still passes. It has 43 tests at `ede80e1` (jackie and gsp each measured 43/43), and everything above is added to it.
10. **Optional:** the review's end-to-end check. Serve the feed's bytes to the real sync script over `file://` with a temporary `HOME`, then run `ssh-keygen -lf` on the result.

**On the baseline,** every new-behaviour case above fails and the regression cases pass (the note's Implement (1)). Keep the raw output.

**gsp's proof-of-concept harness** sits in the scratchpad and will not last.
- It must not be committed to the townsquare repo, because it embeds private Wonderland code (the review, §2).
- If ronda wants it for T13, its home is the private `offsite-binding` branch.

## 5. Runbook refinements: all seven confirmed (francis-ngannou)

These fold into the runbook together with two earlier sets of changes:
- Addendum 1 §4's changes;
- jackie's U11 exemption, which leaves `outbox_pending` and `publisher.pending`/`publisher.published` out of the byte-identical check, for the same reason as the per-entry `publishing` field.

The seven:
- **s1 (confirmed).** Name every file. Never `tar`, `cp -r` or `rsync` the registry root, which holds `secrets/`.
- **s2 (adopted).** In step 3, remove `2>/dev/null || true` from the copy of the journal and outbox. A failed backup must show up before the restart.
- **s3 (required, if the `docker exec` fallback is used).** Pin it to one exact command, which francis writes:
  - Python's `sqlite3` backup API copies `/app/data/registry.db` to a file inside the container, outside `/app`;
  - `docker cp` then moves that file into the NAS backup directory;
  - no step ever runs `env`, `printenv`, `ls` or `cat` against `/app/secrets`.
- **s4 (adopted).** No raw `docker inspect` or `docker logs` output goes into a repo document.
  - Filter it down to what is needed.
  - Before committing, scan for `token`, `refresh_token`, `client_secret` and `password`.
  - The one existing instance is the environment block in francis's prep document. That is the F1 item the session is already taking to Sensei.
- **s5 (confirmed).** The DB copy stays on the NAS.
- **s6 (required).** Deploy from the reviewed commit's blobs, never from a working tree, because `core.autocrlf=true` on this machine (jackie, §0).
  1. Export the three files with `git show <fix-sha>:services/registry/<path>`.
  2. Check that they contain no CR byte.
  3. Check that their SHA-256 equals the blob hashes.
  4. `scp` the exported files, not working-tree copies.
  5. Check that the NAS copies' SHA-256 equals the same hashes.

  **Run the export in Git Bash, not PowerShell.** PowerShell's `>` can re-encode a native command's output; Windows PowerShell 5.1, for example, writes UTF-16. This is inferred from PowerShell's documented behaviour, not measured here. The CR-byte check in step 2 is the backstop.
- **s7 (required).** Add a pre-check to step 2, before the deploy.
  - List every active row that has a non-empty stripped key and for which the reviewed `key_publishable` returns false. **The list must be empty.** If it is not, stop and bring it to Sensei.
  - **Run the reviewed function itself.** Import it from the `schema.py` exported in s6, in a local Python, and apply it to a saved copy of the live `/registry?retired=0` JSON.
  - Do not rewrite the rule in the runbook. A copy of the rule is one more place for the two to drift apart.

gsp confirms that the runbook's s3, s6 and s7 steps match this section (Peer review, §8).

## 6. F1, F6, F7: noted, no ruling needed

- **F1.** The townsquare repo is public. Checking the Drive folder's sharing before any push of `internal` is with Sensei, through the session.
  - A related point for the same pre-push look, which is not a blocker and not mine to rule on: this chain's documents, this ruling included, quote short excerpts of the private Wonderland registry code.
  - gsp kept his proof-of-concept out of this repo for exactly that reason.
  - Whether short excerpts may go public with `internal` is Sensei's call; gsp can advise.
  - This ruling carries no folder ID and no credential.
- **F6** is Low, and it goes to bishop's thread (§2.9).
- **F7.** Nothing in this order waits on the fleet survey.
  - With G4 in place, no `/register` writer can leave an offsite row holding a key.
  - So `/registry`, `/agent` and the journal have no offsite key to leak.
  - The review's standing constraint becomes Watch-for (l).

## 7. Follow-ons, and a fault that predates this fix, outside this order

- **ip-man: the amendment to v5 §4, after the deploy is verified.** The second send's post-send check (P3) compares the `agent` object in the response with the body it sent, field by field (the review, §9). That way a dropped write is caught at the send itself.
- **For bishop's thread (the session adds it):** `/retire` stays outside the lock. So a retire and a register on the same row can still be journaled in the opposite order to the one they were applied in. [inferred]

**Files read this run**
- In `C:\Repo\townsquare\docs\`: the review, the note, Addendum 1, jackie-chan's review and francis-ngannou's deploy prep.
- At `ede80e1`, in jackie's clone: `app.py`, `registry/schema.py`, `registry/db.py` and `registry/journal.py` in full, plus `registry/crier.py` lines 240–317.
- In the review's scratch folder: part of `runs\results.json`, and `runs\02-patched-newpath_section_only\srv\authorized_keys`.
- `C:\Repo\Agentic\docs\charter-2.0-part-c.md`: C1 and C2, and the heading of C4.

I wrote nothing and ran nothing.

## 8. Work order: amended lines (every other line of the note and Addendum 1 stands)

```
WORK ORDER — registry `binding: offsite`: after gsp's security review
- Document: the session saves this ruling byte for byte from this SubagentHandback, with its SHA-256 and the
  same extraction disclosure as the note and Addendum 1, at
  C:\Repo\townsquare\docs\ip-man-registry-offsite-security-ruling-20260926.md (internal, not pushed).
  Reviewed: its decisions are gsp's own measured proposals, adopted unchanged; jackie-chan's review of the
  base design stands. The one detail it adds (§2.6: the journal write inside the lock) changes no outcome.
  gsp checks it at hunk review, and Helio's GAME PLAN confirms that nothing else here is new.
- Coordinate: helio-gracie — GAME PLAN next, covering this ruling, before any Implement line. CHECKPOINT at
  every delivery handoff (default). Final CHECKPOINT + GATEWAY before Sensei sees the deploy question. His
  Next sets the pace.
- Implement:
    (1) ronda-rousey: §4, committed on offsite-binding before any fix code exists. On the baseline the
        new-behaviour cases fail and the regression cases pass. Raw output.
    (2) bruce-lee: §3 to green, with the smallest diff, in three files.
    (3) francis-ngannou, in parallel with (1) and (2): the runbook, with Addendum 1 §4, jackie's U11
        exemption, and s1–s7 as set out in §5.
- Peer review:
    1. jackie-chan: the diff against §3, and every consumer, as before;
    2. then gsp:
       - the R3a–R3c and R4 hunks match his review;
       - every offsite comparison goes through is_offsite;
       - the lock covers exactly the span in §2.6;
       - the runbook's s3, s6 and s7 steps match §5.
       The hunks he reviews are hashed from git show blobs.
- QA: ronda-rousey — the full run in isolation (T12), raw, including both orders of T13 and its no-op-lock
  control.
- Done when:
    (3) amended: the full suite and §4's set pass in isolation, raw. jackie's review and gsp's confirmation
        leave no open blocker. gsp's confirmation covers the R3a–R3c and R4 hunks, the lock's span, and the
        runbook's s3, s6 and s7 steps.
    (4) amended: "as designed" holds for both kinds of offsite row (§2.1):
          - no test sequence puts an offsite row's key in the feed (T2–T6d, T9b, T13 and the adversarial
            cases);
          - no /register sequence leaves an offsite row holding a key at rest (T13).
    (5) adds two conditions:
          - s7's list was empty on the day;
          - the deployed files' SHA-256 equal the reviewed commit's blob hashes (s6).
- Watch for:
    (b) amended: R4 keys on both fields, as §2.3 says. Keying on section alone trusts a field that drifts.
        Keying on binding alone drops bishop's key and breaks Done-when (5).
    (l) crier.py's _KNOWN must never gain pubkey or host_address, and board ingestion stays off, for as long
        as the board has writers outside the LAN (the review, F7).
    (m) the lock assumes a single process. A server with several worker processes voids it. The fix would
        then be a connection per request plus a DB transaction, which comes back to ip-man first.
    (n) T13 traps: a wait with no timeout deadlocks the locked build, and without its no-op-lock control T13
        can pass without ever forcing the race.
    (o) running s6's export through PowerShell redirection can re-encode the files: use Git Bash. The
        CR-byte check is the backstop.
    (p) s7 runs the reviewed key_publishable itself, never a copy of its rule.
```