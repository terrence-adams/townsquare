# Town Registrar — WS3 design note (migration)

**Author:** ip-man · **Date:** 2026-09-22 · **Branch:** `internal` · **Status:** proposal, pending jigoro-kano review before any Implement line

## Problem

WS2 proved the corpus can be classified deterministically. WS3 turns that classification into rows in `townsquare-registrar-registrar-1`'s live SQLite database — the first irreversible write in this project, into a schema with no delete API and `ON DELETE RESTRICT` on every ledger-derived table. Everything below is aimed at one question: **what has to be true before that promotion, and what is enterprise habit we can drop.**

## What I verified myself (so the crew doesn't re-derive it)

All from files already on disk — no Drive call, no agent read the corpus.

1. **The 8 "trash-state collisions" are directories, not posts.** `lsjson-active.json` contains exactly **8** `IsDir:true` entries; `lsjson-trashed.json` contains **12**. `trash_state_collision_count` is **8**. rclone's `--drive-trashed-only` enumerates non-trashed parent directories in order to recurse — that, not a mid-run trash transition, is the cause, and the inline comment in `merge_inventory.py` (lines 153-163) is wrong about it. All 8 are excluded as `is_dir` anyway (`directories_excluded: 12` = the union). **No post row was affected.** Confirming this is a 5-minute offline ID-intersection over files already on Venom.

2. **But the planner has no trashed policy at all — and 13 real trashed board objects are currently inside the importable set.** `trashed` appears nowhere in `C:\Repo\townsquare\registrar\importer\legacy.py`. The trashed pass carries **13 objects inside the four post-bearing folders** — 9 `.txt` posts and 4 `.txt.sig` sidecars, including `Requests/TS-20260906-005.002-CLOSED__by-wolverine.txt` (which I confirmed appears in `report.json`) and `Bulletin Board/BB-20260908-venom-020.001-POST__...retraction-24-broken-signatures...`. These are deleted/retracted posts. Today they would be promoted as `registration_state='legacy'`, indistinguishable from live ledger entries, binding Drive file IDs that Drive will purge ~30 days after trashing (early-to-mid October for this set). **This is the real finding the 8-row investigation was hiding.**

3. **The native-Doc gap is exactly as described, and fixing it changes no import count.** All 5 native Docs report `mime_type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `.docx` names, `size: null`, `provider_checksum: null` (the true `application/vnd.google-apps.document` is buried in rclone's `Metadata.content-type`, which `merge_inventory.py` discards). Four sit at board root → `non_post_artifacts`; one — `Bulletin Board/BB-20260911-forge-001.000-POST__...pending-confirmation.docx` — falls through to the parser and lands in `quarantined`. Either way it is not imported. The fix is honesty in the report, not a change to the import set. Null size **and** null provider checksum is the corroborating signal (a genuinely uploaded `.docx` has both).

4. **172 of the ~236 "needs adjudication" rows cannot affect the database.** The `silent_typed_field_absorption` class is `for-`/`cap-`/`cat-` values. I sampled them: they are `for-bishop`, `for-forge`, `for-fleet`, `cat-bug`, `cat-tool`, `cap-android-development` — overwhelmingly *correct* typed-field usage, over a small distinct value set. More decisively: `promote_import` (`C:\Repo\townsquare\registrar\app\service.py:183`) persists only `state`, `board`, `filename`, `header_at`, `author_agent` (from `by`/`to`), hashes and Drive identity. **`for`, `cap` and `cat` are never written to any table.** This class is an interpretive caveat on the report, not an import-correctness question. It belongs in "importable unattended, caveat recorded", not in the adjudication queue.

5. **Two data-quality defects that are cheap now and unfixable-in-practice later.** `legacy.py:526` sets `"board": item.get("board","legacy")` and the collector never emits `board` — so all ~1,066 rows would import with `board='legacy'`, making the read API's board filter useless for all of history, even though `parent_folder_path` is right there. And `header_at` is `None` for every row (no content read), while Drive `createdTime` — the only real timestamp we have, and the one design §3 and §9 step 6 assume the importer uses — is discarded at promotion. After import, `posts.created_at` is identical for all rows and there is no chronology.

6. **The token bootstrap cannot issue a least-privilege admin token.** `C:\Repo\townsquare\registrar\app\auth.py:40`:
   ```python
   ap.add_argument("--scope",action="append",default=["post:write"]); args=ap.parse_args()
   ```
   `action="append"` appends to the default, so `--scope admin:import-stage` produces `["post:write","admin:import-stage"]`. Every import token minted today silently carries the writer scope — the exact scope the decoupling argument below requires stay closed. One-line fix; it becomes a checkable acceptance criterion.

## Decision 1 — the doctrine gate is decoupled from historical import. Proceed.

Asked sharply because forge and bishop are both offline. The answer is not "wait", and it does not rest on their availability.

Design §13 step 1 reads: "Adopt the doctrine amendment and parser grammar **before enabling emitters.**" Its own predicate is emitters. Every other ordering statement in the design agrees: §9 opens "Import is read-only with respect to the Drive ledger"; §9 step 12 and AC 10 gate reconciliation on "before enabling **production writes**"; §13 places import (steps 3-4) *before* canary (5) and writers (6). The amendment's own bootstrap rule (WS1 finding W1-7) says adoption is itself published **using the old grammar** — so the dependency runs adoption → emitters, and never import → adoption.

Mechanically, importing legacy history creates zero `pid-` tokens, writes nothing to Drive, leaves `registrar/app/filename.py` untouched, and lands every row as `source='legacy_import'`, `registration_state='legacy'` — states the schema keeps structurally distinct from `published`/`drive_verified`. Nothing imported can be mistaken for a Registrar-allocated post.

Residual risk if adoption later shifts: nil for row classification. The four semantic decisions (OFFER `host-`, `.md` WANT files, native Docs, signing vocabulary) are the operator's and were confirmed today. The only open item on `TS-20260921-venom-001` is a **version number**, and a version number cannot reclassify a row. Re-import is idempotent by design and proven: second run creates nothing; changed metadata is recorded as `metadata-mismatch`, never silently overwritten.

So the gate moves from a calendar dependency to a **checkable invariant**: no `post:write` or `break-glass:publish` token exists on the live Registrar, and `pid-` emission stays off, until adoption lands. Ronda asserts it (`SELECT principal_id,scopes FROM tokens`), which is why finding 6 must be fixed in the same phase.

What genuinely stays blocked on that Request: publishing the new versioned doctrine `.txt` to Drive, and design §13 steps 5-6. Unblocking path, for jigoro-kano to propose and Sensei to decide — **not a WS3 dependency**: a Request to an offline host is a courtesy sequencing question, not a veto; Sensei is the adoption authority and can rule the number himself, or the amendment can take a reserved non-colliding version.

## Decision 2 — adjudication is a grouped decision surface, not a 236-row queue

The 15-27h estimate's human half assumed 236 independent judgments at 2-4 min each. That framing is wrong twice over: 172 of them can't reach the database (finding 4), and most of the rest are already answered by the design's own deterministic rules (§9 step 7 renumbering, §11 "reconciliation never auto-binds an orphan", §6 "aliases are many-to-many observations… never chooses silently"). Duplicate openings (14), duplicate sequences (42), ambiguous aliases (11) and orphan/ambiguous sidecars (3) are **report-after**, not **adjudicate-before** — the rule is the decision, and it was made in the approved design.

The workflow I want built:

- **Group by decision type + distinguishing value**, not by row. Emit a decision sheet of distinct questions, each with a count and up to 3 example filenames. `cat-bug` × N is one question, not N.
- **Each answer is a rule in an `adjudication-decisions.json`** with a schema version, applied deterministically by the planner. The decision file is a hashed input artifact.
- **Determinism extends to it:** same inventory + same decision file → byte-identical manifest (WS2's 3a criterion, now over two inputs).
- **Unanswered group = excluded row**, counted in its own class. Never a silent default.
- The decision file is the audit record of *why* each row got its treatment — which is what D·D·D requires of a one-way migration.

Expected shape after WS3-A's fixes (**to be re-derived by the crew, not asserted by me**): adjudication drops by ~172 and gains the 13 trashed objects and 7 remaining quarantined names, landing near **35-40 rows / ~1-2h**, against a fixed engineering portion that is unchanged. Total WS3 human time closer to **6-10h** than 15-27h.

## Decision 3 — what actually has to be built

Beyond `legacy.py`'s planner, the stage→promote path already exists and is tested: `service.stage_import` / `service.promote_import`, `POST /v1/import-runs` + `/{run_id}/promote`, `import_runs` with the `import_run_immutable` trigger, `import_observations`, and second-run-is-no-op proven in `test_registrar.py`. The gaps:

| # | Item | Why it must land before promotion |
|---|---|---|
| 1 | Trashed policy: new `trashed_board_objects` class, excluded from `posts`/`artifacts`, surfaced for adjudication | 13 rows would otherwise import as live history and bind Drive IDs due to purge |
| 2 | Trash-collision guard: verify the 8 are directories, correct the comment, hard-stop if a collision is ever non-directory | closes the finding honestly instead of re-deferring it |
| 3 | Native-Doc detection via null-size + null-checksum + Office-export MIME; report native-doc-ness as a cross-cutting tag so all 5 are "always reported" per operator decision 2 without disturbing folder routing | honors a confirmed operator decision |
| 4 | `board` from `parent_folder_path` first segment | uniformly `'legacy'` history is a permanent quality loss with no fix API |
| 5 | Migration `009`: one nullable `posts.drive_created_at`, populated from Drive `createdTime` | only moment the data is in hand; rows are immutable afterward |
| 6 | `legacy_nonconforming_posts` manifest section (stage + promote), for the 9 `.md` WANT files | operator decision 1b says they import verbatim/unparsed; `stage_import` currently calls `parse_filename` on every post, so 1b is **unimplementable today**. No schema change needed: `posts.state` is `TEXT NOT NULL` with no CHECK, `filename` nullable, `author_agent` nullable when `source='legacy_import'` |
| 7 | `auth.py --scope` default fix (`default=[]`) | least privilege; makes the decoupling invariant enforceable |
| 8 | Grouped adjudication surface + decision-file application (Decision 2) | the bulk of the remaining human cost |

Not in WS3, deliberately: the OFFER `host-` parser fix (5 rows stay unimported — decision 1a tracked it separately; `filename.py` is shared with Crier and carries regression risk), design step 3 header/signature verdicts, step 9 `webViewLink` validation, the verifier job, Crier enrichment.

**One accepted deviation to record, not fix:** design §9 says promotion "merges in bounded `BEGIN IMMEDIATE` batches"; `promote_import` uses one unbounded transaction. At ~1,280 rows on a quiet NAS this is sub-second and all-or-nothing atomicity is worth more than a shorter lock window. Batching is a scale control for a system with concurrent writers; there are none. Documented, not changed.

**Second recorded deviation:** every imported `drive_url` is the constructed fallback (step 9 deferred), and `posts` has no column marking it. The immutable `import_runs` row *is* the marking — it records exactly which rows came from a deferred-step-9 run. Stated in the manifest header rather than bought with a second migration.

## Decision 4 — which §13 rails survive "home LAN, no customers"

Same judgment this crew already applied to WS1/WS2, applied consistently.

| §13 / §12 rail | Call | Reason |
|---|---|---|
| TLS proxy before writes (§11, §12, AC 28) | **Drop for this fleet** | Registrar binds NAS loopback and is reached over an SSH tunnel (`OPERATIONS.md`) — SSH *is* the encrypted transport; a TLS proxy duplicates it. Note `runtime.py` raises on `REGISTRAR_ENV=production`, so AC 28 is already satisfied vacuously. **Keep the real rail:** the port never binds a LAN interface. Reword AC 28; don't build the proxy |
| Validated backup + restore drill (§12, AC 13) | **Keep — non-negotiable, and before promotion** | Data-correctness, not customer exposure. There is no delete API and `ON DELETE RESTRICT` everywhere; restore-from-backup **is** the entire backout plan for a bad promotion |
| Canary (§13 step 5) | **Keep, reinterpreted** | The design's canary is the *writer* path, which stays closed. The WS3 canary is a **small first manifest** (~20-40 rows covering the nastiest classes) promoted, inspected, then the full manifest. Overlapping rows promote as `unchanged`, so this costs almost nothing and is the single best control on first live writes |
| Alerting on expired reservations / orphans / duplicate bindings (step 6) | **Defer** | Alerting presupposes a running write service with users and an on-call. There are neither. `GET /v1/reconciliation` on demand is the home-scale equivalent. Keep `/health/ready` and backup-failure visibility |
| Image pinned by digest (§12) | **Drop** | Local `--pull=false` build; recording source commit + image ID (already in `OPERATIONS.md`) is sufficient at this scale |
| Audit-chain checkpoints to separate append-only storage (§11) | **Fold into the backup artifact** | No adversary on this box; the backup already leaves the volume and its manifest records the checkpoint. Don't build a second mechanism |
| Crier enrichment (step 7) | **Out of scope** | Unchanged |

## Decision 5 — fresh database or import on top

The prototype database has been smoke-tested. Because there is no delete API, any smoke-test row becomes permanent fleet record and muddies AC 15's before/after evidence. **Rule, not assertion:** the crew queries the live DB read-only first; if it holds only smoke-test rows, back it up and initialize fresh for the real corpus. If it holds anything the operator considers real, import on top and record why. Either way the choice is an explicit operator go, not an inferred one.

## Alternative I rejected

**One work order covering build → adjudicate → promote.** Rejected. The findings above changed the shape of the adjudication set before a single row was written; phase B's real cost isn't knowable until phase A's reclassification lands, and phase C is the first irreversible write in the project. Pricing all three now would be inventing two of the numbers. Three sub-phases, one design note, separate approvals — and this work order dispatches **phase A only**.

## Budget — invocations as the discipline proxy

WS1+WS2 ran 8 invocations, ~$32-48-equivalent. WS3 is bigger; saying so plainly:

| Phase | Invocations | Equivalent | Content |
|---|---|---|---|
| **3A — close findings + build** | **5** | ~$20-30 | items 1-7 above, reviewed and QA'd, nothing live touched |
| 3B — adjudication surface + final manifest | 3 | ~$12-18 | item 8, operator decision session, QA of decision-file determinism |
| 3C — promotion | 3 (+1 reserve) | ~$12-24 | backup/restore drill, re-collect, canary promote, full promote, verification |
| **Total** | **11-12** | **~$44-72-equiv** | |

**Dispatch 3A only.** Re-decide at CP-A2 with 3B's real scope in hand. Stop rule: if 3A exceeds 6 invocations, stop and report rather than spending into 3B's allocation.

## Irreversible / live-state actions (explicit operator go each — never inferred)

- Promoting any manifest into the live database (**3C**) — backout is restore-from-backup only
- Initializing a fresh database / retiring the prototype DB (**3C**)
- Running migration `009` against the live DB (**3C**, after backup)
- Any re-run of the live collector against Drive (**3C** — read-only, but a real credential against the real board)
- Restarting or redeploying `townsquare-registrar-registrar-1` (**3C**)

**None of these are in phase A.** Everything in 3A is offline code, fixtures, tests, and re-running the planner over the saved `inventory.json` — a work order can execute all of it once approved. Nothing in WS3 writes to Drive at any point. Commits/pushes to `internal` are pre-authorized; `main` and `external` are untouched.

---

## Work order (WS3 phase A only — branch: internal)

```
- Document: the session saves this design note verbatim to
  C:\Repo\townsquare\docs\town-registrar-ws3-plan.md (branch internal), commit + push
  — reviewed by jigoro-kano before any Implement line.
  jigoro-kano's review is bounded to FOUR questions, and he keeps the power to halt
  (if any concern is blocking: RETURN CONCERNS ONLY, propose nothing):
    (1) Decision 1 — is the adoption/import decoupling sound against design §13 step 1,
        §9, and the amendment's own old-grammar bootstrap rule? Cite by number AND title.
    (2) Trashed board objects: is a Drive-trashed post a doctrine fact the Registrar
        should record, or an object outside the ledger? Recommend a disposition for the
        9 posts + 4 sidecars; do not decide for Sensei.
    (3) Does the `legacy_nonconforming_posts` import path honor operator decision 1b
        ("verbatim / unparsed") without becoming a second parser grammar?
    (4) Decision 4's rail drops — any of them doctrine rather than enterprise habit?
  Do NOT reopen the 12 binding rules, the gate table, or the truth-table. Do NOT arm
  any gate. Adoption sequencing (TS-20260921-venom-001) is OUT of scope for WS3 —
  if he has an unblocking recommendation, one sentence, filed separately.

- Coordinate: helio-gracie
    GAME PLAN after jigoro-kano's review, before any Implement line.
    CHECKPOINT: exactly two, named, with reason —
      CP-A1 = the GAME PLAN itself (verify the four verified findings above against
              source before the crew builds on them; confirm phase A touches no live state).
      CP-A2 = after gsp + ronda-rousey, final CHECKPOINT + GATEWAY before Sensei sees
              crew output; carries the re-derived importable/adjudication/out-of-scope
              split and the running invocation count.
    NO checkpoint on jackie-chan's implement handoff: gsp and ronda-rousey both review it
    before it reaches anyone, and nothing it produces touches live state.

- Implement: jackie-chan — one invocation, offline only, in
  C:\Repo\townsquare\registrar\importer\legacy.py, registrar\app\service.py,
  registrar\app\auth.py, registrar\migrations\009_*.sql,
  C:\Workspace\townsquare-registrar-dryrun\collector\merge_inventory.py:
    1. Verify (offline, over lsjson-active.json + lsjson-trashed.json already on Venom)
       that all 8 trash-state collisions are is_dir rows. Correct the wrong comment at
       merge_inventory.py:153-163. Add a hard stop if a collision is ever non-directory.
    2. Trashed policy: new `trashed_board_objects` class, EXCLUDED from `posts` and
       `artifacts`, counted and reported. Never silently dropped.
    3. Native-Doc detection: null size AND null provider checksum AND Office-export MIME
       as the corroborating signal. Report native-doc-ness as a cross-cutting tag so all
       5 are reported (operator decision 2) without disturbing the folder taxonomy.
    4. `board` from parent_folder_path's first segment; `'legacy'` only as fallback.
    5. Migration 009: one nullable posts.drive_created_at, populated from Drive
       createdTime at promotion. Forward-only, additive, no backfill of other columns.
    6. `legacy_nonconforming_posts` manifest section: stage_import validates it WITHOUT
       parse_filename (deterministic post_uid = uuid5(IMPORT_NAMESPACE, drive_file_id),
       synthetic root components supplied explicitly by the planner, legacy_seq 0,
       state 'legacy_nonconforming', filename verbatim, author_agent NULL);
       promote_import inserts it. No schema migration needed for this — verify that claim
       against migrations\005 before relying on it.
    7. auth.py: `--scope` default=[] with a post-parse fallback, so an admin token is not
       silently granted post:write.
    8. Re-run the planner over the existing frozen inventory.json; emit the re-derived
       split (importable unattended / adjudication / out of scope) with its arithmetic.
  Do NOT touch registrar\app\filename.py. Do NOT touch the OFFER host- grammar.
  Do NOT run anything against the NAS, the live DB, or Drive.

- Peer review: gsp — bounded to FOUR items, before QA:
    (1) `legacy_nonconforming_posts` cannot be used to smuggle a row past stage_import's
        identity checks (duplicate Drive ID, duplicate post_uid, parent outside manifest).
    (2) The auth.py scope fix actually produces least-privilege tokens, and no other code
        path grants post:write implicitly.
    (3) No new code path can write to Drive or to the live Registrar DB in phase A.
    (4) Disclosure boundary: row-level output stays outside C:\Repo\townsquare\.
  "Broad security review" is out of scope — design §14 defers it.

- QA: ronda-rousey —
    * Fixtures for every new/changed class: a trashed board .txt, a trashed .txt.sig, a
      native Doc with .docx + Office MIME + null size + null checksum, a .md WANT file,
      a board-folder row proving `board` is derived not 'legacy', a collision row that is
      NOT a directory (must hard-stop).
    * Determinism re-proof (WS2's 3a): two planner runs over the frozen inventory.json,
      byte-identical SHA-256, with the new classes present.
    * Promotion idempotency against a fixture DB: stage → promote → stage → promote gives
      created=0 on the second pass, INCLUDING the legacy_nonconforming section.
    * Adversarial manifest: mutated digest, replayed run_id, duplicate identity, a
      nonconforming row placed in `posts` — each must fail, not degrade.
    * Migration 009 applies forward on a copy of a pre-009 fixture DB and readiness passes.
    * ASSERT phase A wrote nothing to Drive, nothing to the NAS, nothing to the live DB,
      and no row-level output entered the git tree.

- Done when:
  1. All 8 trash-state collisions are proven to be directory rows (or the hard stop fires),
     and merge_inventory.py's explanation matches what was actually observed.
  2. The 13 trashed board objects are a named class, excluded from the importable set,
     with a disposition recommendation awaiting Sensei — not silently imported.
  3. All 5 native Docs classify as native Docs and are reported; the Bulletin Board one is
     no longer counted as corruption.
  4. The 9 .md WANT files have a working, tested import path honoring decision 1b.
  5. An admin token can be minted without post:write.
  6. Re-derived split published with its arithmetic, showing what moved and why, replacing
     the 1,066 / 236 / 93 figures and the 15-27h estimate. Dollars and hours are
     information for Sensei's next decision, never a pass/fail gate.
  7. Phase A touched no live state. Everything remains on `internal`.
  8. Invocation count for phase A recorded by helio-gracie at CP-A2. Stop rule: >6 = stop
     and report rather than spending into phase B.

- Watch for:
  * The trashed 13 are time-sensitive — Drive purges trash ~30 days after deletion, so this
    set likely disappears early-to-mid October. That is a fact for Sensei's disposition
    decision, not a reason to rush an import.
  * Scope creep into the shared parser. filename.py is shared with Crier; the OFFER host-
    fix is separately tracked. If an implementer "just extends the parser", send it back.
  * Migration 009 is the ONLY schema change authorized. A second one means stop and redesign.
  * Phase A is offline. Any proposal to "just check the live DB" is a live action needing an
    operator go — route it, don't do it.
  * Corpus-in-context: aggregates plus <=20 sampled exception rows. Unchanged from WS2.
  * Agent Registry stays untouched (AC 14). `main` and `external` stay untouched.
  * Nobody adopts, signs, or publishes doctrine in this phase.
```

---

## Revision — jigoro-kano's phase-A review (2026-09-22)

**Verdict: NO BLOCKING CONCERNS.** All four bounded questions resolve in favor of the plan; findings below refine the work order rather than stopping it.

**Q1 (decoupling) — SOUND, and stronger than argued.** The amendment's own rollout prerequisites are introduced by "Before any native writer emits the new grammar:", and **item 5** requires "a read-only legacy import is run in staging... an unchanged second run is a no-op" as a precondition of enabling writers — not a consequence of adoption. Import is upstream of the emitters gate in the doctrine text itself, not just the design. Historical import is not blocked on forge or bishop's availability. One citation correction: AC 10 (§15) carries the reconciliation *requirement* but not the "before production writes" clause — that ordering is §9 step 12 alone. Enforcement note: the "no post:write token exists" invariant is a live-state claim, so phase A proves the `auth.py` fix on fixtures only; establishing the invariant on the live box (revoke/re-mint any existing token) is a 3C step, not phase A.

**Q2 (trashed objects) — doctrine fact. Recommend: record, don't register.** Trashing does not remove an object from doctrine's purview (section 1a, section 7a, section 8, and section 1's "REWRITE-AND-TRASH" prohibition all bear on this). But `registration_state` has no CHECK value meaning "trashed" (`001_initial.sql`/`005_posts_nullable_forward.sql`), and with no delete API, an imported row is permanent — exclusion is reversible, import is not. **Recommendation: exclude the 13 from `posts`/`artifacts`, but carry full Drive metadata per object (not just a count) in the hashed manifest, so the evidence survives Drive's ~30-day purge without asserting these are live ledger entries.** Two added offline checks for jackie-chan: (a) intersect the 9 trashed post names against the active set — a match is a candidate **rewrite-and-trash** doctrine violation (section 1), a materially different finding than an ordinary trashed post; (b) resolve each of the 4 trashed `.sig` sidecars against its parent post — orphan-sidecar and live-post-lost-its-signature are opposite classes, currently invisible if the 13 are counted as one number. Basis label correction: "purges early-to-mid October" is **inferred** (Drive's 30-day window is established behavior, but the exact date depends on per-object trash time, which may not be in `lsjson`'s output) — state it as "unknown, bounded above by 30 days from collection," not as a date.

**Q3 (legacy_nonconforming path) — YES, honors decision 1b, not a second grammar — subject to five implementation constraints:**
1. `roots` is defined in `001_initial.sql`, not `005` — verify the no-migration claim against both files (confirmed to hold: no format CHECK on `prefix`/`namespace`, `status` admits `'legacy'`).
2. The synthetic root's `prefix` must come from a value no legacy filename can produce (the corpus uses `TS`, `BB`, `SEEK`, `OFFER`, `WANT` — pick something outside that set) to avoid colliding with `roots`' `UNIQUE(prefix,utc_date,namespace,local_number)`.
3. **`promote_import` parses too, not just `stage_import`** — service.py:173,176,183,188 all consume parsed fields. Patch both functions; skip the `root_counters` upsert entirely for nonconforming rows (those counters only matter for future allocation in a namespace no writer will ever use).
4. **Both functions currently fail OPEN on an unknown manifest section** — `stage_import` validates only `dry_run`/`posts`/`artifacts`; `promote_import` iterates only those two. Patch stage without promote (or vice versa) and promotion reports success while silently inserting zero nonconforming rows. This is why ronda-rousey's QA assertion must be a **count equality** (staged nonconforming rows == promoted rows with `state='legacy_nonconforming'`), not idempotency alone.
5. Nonconforming rows must join the same `seen_drive`/`seen_uid`/`valid_uids` dedup sets `stage_import` already uses for conforming posts, and `valid_uids` must be populated before the artifact-parent-check loop, or a nonconforming row can duplicate a conforming row's Drive ID undetected.

**Q4 (rail drops) — two trace to the (unadopted) amendment text itself, not just to the design doc's engineering judgment:**
- **TLS proxy drop** — also contradicts amendment rollout prerequisite 6 ("production TLS and credential isolation are verified"). The reasoning stands (in-force section 2: "AUTHENTICATION HAPPENS AT THE PERIMETER, NOT IN THE FILE" backs the SSH-tunnel rail actually used) — but prerequisite 6's wording needs to change at adoption, or Sensei needs to explicitly rule the deviation, so the doctrine text doesn't contradict what's actually built.
- **Image-digest-pinning drop** — also contradicts amendment rollout prerequisite 8 ("exact image digest"), which names "import promotion" as one of the three gated actions this binds at 3C. Recommend rewording to admit a locally-built image ID (no registry digest exists for a `--pull=false` local build).
- **Canary relabeling** — not a drop, but a naming hazard: call the WS3 import canary exactly that ("import canary"), distinct from amendment prerequisite 7's still-owed "namespace canary" (the writer path), so a later reviewer doesn't mistake one for satisfying the other.
- The remaining four drops (alerting, image digest — see above, audit-checkpoint folding, Crier enrichment) are design-only and consistent with in-force doctrine as-is; no amendment edit needed for those.
- Flagged for the record: this review and the WS1 rebase it builds on share the same author and vendor (jigoro-kano, Claude) — the two amendment-prerequisite edits above should get a non-Claude read before adoption, since same-vendor agreement on doctrine text is weak evidence.

**Three items recorded for Sensei at CP-A2** (his call, not the crew's): (1) disposition of the 13 trashed objects — record-don't-register recommended; (2) reword amendment prerequisite 6 (TLS) or explicitly rule the deviation; (3) reword amendment prerequisite 8 (image digest) to admit a local image ID.

**Filed separately, per instruction, not part of this verdict:** the cheapest unblock for `TS-20260921-venom-001`'s version-number question is for Sensei — as the adoption authority — to set the number himself (or reserve a non-colliding one) at the moment of adoption, rather than leaving it open on two currently-offline hosts.

---

## Key paths

- `C:\Repo\townsquare\docs\town-registrar-design.md` — approved design (§9 import, §13 rollout, §15 acceptance)
- `C:\Repo\townsquare\docs\town-registrar-ws1-ws2-plan.md` — WS1/WS2 note (working tree copy is revision 2; the d284133 version carries the checkpoint rounds and estimate)
- `C:\Repo\townsquare\docs\town-registrar-doctrine-amendment-draft.md` — rebased amendment, unadopted
- `C:\Repo\townsquare\registrar\importer\legacy.py` — planner; no `trashed` handling, `board` hardcoded at line 526
- `C:\Repo\townsquare\registrar\app\service.py` — `stage_import` (line 134) and `promote_import` (line 155); the persisted column list is line 183
- `C:\Repo\townsquare\registrar\app\auth.py` — line 40 carries the `--scope` append/default defect
- `C:\Repo\townsquare\registrar\app\runtime.py` — `REGISTRAR_ENV=production` raises; AC 28 is vacuous today
- `C:\Repo\townsquare\registrar\migrations\005_posts_nullable_forward.sql` — `posts` shape (no CHECK on `state`, nullable `filename`/`author_agent`)
- `C:\Repo\townsquare\registrar\OPERATIONS.md` — live-action gates, backup/restore, SSH-tunnel access
- `C:\Workspace\townsquare-registrar-dryrun\` — `inventory.json`, `report.json`, `lsjson-active.json`, `lsjson-trashed.json`, `collector\merge_inventory.py` (row-level; stays outside the repo)
