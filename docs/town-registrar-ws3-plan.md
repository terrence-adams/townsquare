# Town Registrar — WS3 design note (migration)

**Author:** ip-man · **Date:** 2026-09-22 · **Branch:** `internal` · **Status:** proposal, pending jigoro-kano review before any Implement line

**Path note (2026-09-22):** all row-level JSON artifacts (`inventory.json`, every `report*.json`, the raw `lsjson-*.json` collector passes, the flag-count-delta and adjudication-decision-sheet files) were moved from `C:\Workspace\townsquare-registrar-dryrun\` directly into `C:\Workspace\townsquare-registrar-dryrun\reference\` to declutter the working directory. Every path to one of these files quoted earlier in this document (before this note) is now stale by that one path segment — read `reference\<same filename>` instead. Synthetic test fixtures (`wsb2-fixtures\`) and the collector scripts (`collector\`) were left in place, unmoved.

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

## CP-A1 (helio-gracie) and operator decisions — 2026-09-22

Helio cleared CP-A1: **build may start**, phase A confirmed to touch no live state. He re-verified all six of ip-man's findings and jigoro-kano's spot-checked claims against source directly (not by trusting the reports) — conclusions all held, but three findings had loose stated evidence that jackie-chan must not build on: the "8 collisions are directories" conclusion is right but the stated proof method doesn't match (real mechanism: `--drive-trashed-only` lists intermediate folders to recurse, not "trash state changed mid-run"); the "172 adjudication rows collapse" figure conflates an instance count with a row count — the real reducible number is unique posts whose *only* flag is silent absorption, not yet computed; and `legacy.py:526`'s `'legacy'` board value is a default for a field nothing populates, not a "hardcode" — same conclusion, different fix site (the five row-construction call sites, not just line 526). Full detail and six additional refinements (A1-A7) are in Helio's block; jackie-chan's implement dispatch carries them.

Two decisions Helio surfaced for the operator, **both confirmed 2026-09-22, both per recommendation**:
- **Doctrine rollout prerequisites 6 and 8** reworded to match home-LAN scope rather than adopted as enterprise-pattern text the system doesn't implement — applied directly to `docs/town-registrar-doctrine-amendment-draft.md`.
- **Trashed-object disposition**: **record, don't register** — confirms jigoro-kano's recommendation. Excluded from `posts`/`artifacts`, full Drive metadata preserved in the hashed manifest so the evidence survives Drive's ~30-day trash purge, nothing imported that can't be cleanly unwound later.

(Report/inventory storage location — Helio's queue item 3 — was already resolved earlier: `/home/batman/town-registrar/dry-run-reports/` on the NAS, `drwx------`/`600`.)

## CP-A2 (helio-gracie) — phase A complete, GATEWAY to Sensei (2026-09-22)

**Verdict: PROCEED.** No real block. Phase A touched no live state (verified: no `.db`/`.sqlite` file exists anywhere in either tree). Item 6 is correctly blocked — a taxonomy decision, not a failed work item. Code committed at `3a33d21`, pushed to `internal`.

**Corrected corpus split, replacing the CP2 figures of 1,066 / 236 / 93 and the 15-27h estimate:**

| Bucket | Count | Composition |
|---|---|---|
| A — importable unattended | **1,258** | 1,061 posts + 197 signature sidecars |
| B — needs adjudication | **16** | 7 unparseable names + 9 flagged posts (this 9 is producer-verified only — not yet independently reproduced; deferred to phase B QA at no extra cost, not asked of Sensei prematurely) |
| C — out of scope this pass | **28** | 13 trashed + 1 native Doc + 5 OFFER grammar-B + 9 misfiled `.md` (see correction below — really 1 real WANT file + 8 unrelated documents) |
| Never posts | **93** | 81 documents + 12 folders |

The adjudication queue fell from 236 to 16 (93% reduction) because most of the original flags were on typed routing fields (`for-`/`cap-`/`cat-`) that the database schema has nowhere to store — those rows were never going to need a human.

**Two self-corrections Helio made against his own earlier blocks, both worth recording plainly:** his CP-A1 claim that a native Doc intersects `trashed_board_objects` was wrong (it's at board root, outside all four post-bearing folders — jackie-chan and ronda both caught this independently). More consequentially, his CP2 instruction to Sensei — "rule on 9, not 1" for decision 1b's `.md` WANT count — was **also wrong**. jackie-chan's homogeneity check (required at CP-A1) found only 1 of those 9 objects actually matches the WANT shape; the other 8 are unrelated documents (audits, protocol drafts, an operating memo) that only landed in that bucket via folder+extension coincidence. **Decision 1b, as confirmed by Sensei, governs exactly 1 object — jigoro-kano's original "one-off" reading was correct.** The other 8 need a separate taxonomy ruling, not an import-path fix.

**For Sensei — real decisions, not yet asked:**
1. **The rewrite-and-trash candidate** — `BB-20260908-forge-001.000-POST__...key-attestation-forge-and-forge-now-verifies.txt` exists both live and trashed under the identical filename. Found independently by gsp and ronda-rousey. A candidate doctrine section-1 violation (rewriting and trashing is not how doctrine allows a post's state to change), not an ordinary trashed post.
2. **The 8 misfiled documents** — need a taxonomy ruling on what they actually are (ordinary standing documents that don't belong in the import scope at all, most likely), separate from decision 1b, which they were never really part of.

**Security:** the `auth.py` least-privilege defect is real, fixed, and rated **Low** by gsp with explicit reasoning (over-granted scope doesn't reach the admin import gates; a second ACL gate still holds; reachable only from the local console) — kept off "trivial" because it was silent, would have collapsed verifier/author separation of duties, and falsified a documented invariant. Nothing High or Critical. Minting now prints granted scopes so the failure mode can't recur silently.

**Not verified, deferred to phase B/C at zero extra invocation cost:** the STRICT(5)/EXTENDED(9) adjudication ID lists (ronda couldn't reproduce them; jackie-chan's recompute is unconfirmed); an unreported corpus change since CP2 (duplicate_openings 14→4, duplicate_sequences 42→38 — likely because excluding trashed posts collapsed duplicate pairs, meaning some "collisions" were really trash-and-repost events, not true collisions); whether any existing live-DB token already carries `post:write` (needs the 3C live-DB audit).

**Invocation budget:** 7 total for phase A (jigoro-kano, CP-A1, jackie-chan implement, gsp, ronda, jackie-chan follow-up, this CP-A2) — 5 discretionary as planned, the 6th reviewer-triggered (the ceiling working as designed), the 7th being this mandated checkpoint. Helio confirmed the session's call not to dispatch an 8th invocation for a ronda re-check was correct, on the grounds that nothing depends on the B=16-vs-12 number until phase B, where ronda is already invoked.

### Operator decisions, CP-A2 queue — both confirmed 2026-09-22

1. **Rewrite-and-trash candidate (`BB-20260908-forge-001.000`): hold for now, revisit at phase B.** No immediate investigation. Already excluded from import either way under the "record, don't register" trashed-object policy — this defers the doctrine question, not the import handling.
2. **8 misfiled documents: excluded from import as ordinary documents.** Routed the same as the other `non_post_artifacts` — never posts, never imported. Bucket C shrinks from 28 to **20** (13 trashed + 1 native Doc + 5 OFFER grammar-B + 1 genuine WANT nonconforming file). Decision 1b's actual scope (1 object) is unaffected.

**Corrected bucket C, reflecting decision 2:** 20, not 28. Never-posts grows from 93 to **101** (93 + 8). Total unchanged: 1,258 + 16 + 20 + 101 = 1,395.

---

## Phase B — jackie-chan (2026-09-22)

Scope: regenerate the report with the 8-misfiled-document exclusion applied, settle the STRICT/EXTENDED
adjudication-candidate dispute flagged open at CP-A2, explain the WS2→WS3-A flag-count delta, build the
grouped adjudication decision sheet, and design (not build) `adjudication-decisions.json`. Offline only;
touched `registrar/importer/legacy.py` only (not `filename.py`, not service.py/auth.py/migrations); nothing
live touched. Existing test suite re-run clean (`pytest registrar/tests/` — 76 passed, no regressions).
Row-level detail (per-row lists, all example filenames beyond what's below) stays in
`C:\Workspace\townsquare-registrar-dryrun\` per the standing disclosure-boundary rule (gsp, phase A).

**1. Report regenerated with the 8-doc exclusion applied.** `legacy.py` gained a homogeneity check
(`_is_want_shaped_md`, a plain regex over the filename only — `filename.py` untouched) that separates
decision 1b's true scope (`WANT-<date>-<local_number>[__...].md`) from folder+extension coincidence. Of the
prior 9 `.md`-in-board-folder rows, exactly 1 matches; the other 8 now route to `non_post_artifacts` with
`reason: "misfiled_standing_document"`, same disposition as every other standing document. New file:
`report-ws3-phaseB-final.json` (report-ws3-phaseA-final.json kept as-is for the prior audit trail).
Corrected counts: `legacy_nonconforming` 9→1, `non_post_artifacts` 81→89, everything else unchanged.
Arithmetic reconciles exactly against the frozen corpus: `directories_excluded(12) + non_post_artifacts(89)
+ trashed_board_objects(13) + native_doc_objects(1) + grammar_b_offer_host_field(5) + legacy_nonconforming(1)
+ quarantined_invalid_name(7) + posts(1070) + artifacts_signature/sidecars(197) = 1395`, matching the
operator-confirmed total. Determinism re-proved: two runs over the same frozen `inventory.json` produce a
byte-identical SHA-256 (`2baa612...`), same guarantee WS2's 3a criterion established.

**2. STRICT(5)/EXTENDED(9) — retired as unreproducible, replaced with a defined, embedded method.**
Several natural-join attempts against the manifest's own data were tried before concluding this (raw union of
`duplicate_sequences`+`ambiguous_unnamespaced_aliases` member ids = 49; distinct collision groups = 19+3=22;
intersection with `unresolved_responsibility` = 4; per-group tie-break signal strength = 0 "no signal"
groups found) — none reproduces 5 or 9. This **confirms ronda-rousey's CP-A2 finding independently**: the
figures cannot be recovered from the manifest, and this session (a fresh dispatch, no transcript memory)
cannot recall the original method either. They are retired, not pattern-matched to.

In their place, `legacy.py`'s `plan()` now computes and embeds `adjudication_candidates: {method_note,
strict, extended}` directly in the report — re-derivable by anyone who re-runs the planner, closing Helio's
"a number Sensei may be asked to choose on lives in a transcript" flag for good. The definition, with
evidence: `duplicate_openings`/`duplicate_sequences` are **excluded** from both lists — Decision 2 already
treats them as report-after (the renumbering rule is the decision), and this run confirms every one of the
corpus's 19 collision groups has a real, distinct Drive `created_time` on every member (zero "no signal"
ties) — so the deterministic rule has real signal in 100% of cases, not just nominally. **STRICT (11)** =
`ambiguous_unnamespaced_aliases` membership only (design §11's "never auto-binds" class — genuinely
undecidable by rule). **EXTENDED (15)** = STRICT + the 4 posts whose only warning is
`unresolved_responsibility` and aren't already in STRICT. Neither list removes anything from `posts` — under
Decision 2's own rule these rows already import; the list is a review flag layered on top (like the
`native_doc` cross-cutting tag elsewhere in this report), not a second import gate. This also means the true
**blocking** adjudication bucket (rows that cannot import without a ruling) is **7** (`quarantined_invalid_name`
only), not 16 — see the decision sheet for why duplicate/alias/responsibility flags don't gate import.

**3. Flag-count delta (`duplicate_openings` 14→4, `duplicate_sequences` 42→38): CONFIRMED, with one
precision correction.** Diffed `report.json` (WS2 baseline) against this run by `drive_file_id`: all 10
`duplicate_openings` losses and all 4 `duplicate_sequences` losses are fully accounted for by exactly **7**
two-member collision pairs (5 + 2) where one member moved into the new `trashed_board_objects` class — 7
removed + 7 un-flagged survivors = 14 lost entries, zero residual. Helio's mechanism is right. The correction:
in **6 of the 7 pairs** the trashed and surviving filenames are *different* (different slug/subject) — these
were two independent posts that happened to collide on the same thread+`legacy_seq` slot; trashing one
removed the report's evidence of that coincidence, it does not mean the collision was fake. Only **1 of 7**
(`BB-20260908-forge-001.000`, "key-attestation-forge-and-forge-now-verifies") has an identical filename on
both sides — a true same-identity trash-and-repost, and it is the *same* row already named in
`trashed_rewrite_and_trash_candidates` and held by the operator at CP-A2. So: most of what vanished were
ordinary numeric coincidences, not repost events — say that plainly rather than the broader "duplicate
openings were trash-and-repost" reading. Full pair-by-pair evidence:
`C:\Workspace\townsquare-registrar-dryrun\flag-count-delta-ws2-to-ws3b.json` (a one-time forensic diff
against the WS2 baseline report, not reproducible from `plan()`'s single-input output alone — kept as a
standalone artifact rather than folded into the planner).

**4. Grouped decision sheet** — `C:\Workspace\townsquare-registrar-dryrun\adjudication-decision-sheet-phaseB.json`.
Eight groups, by decision type + distinguishing value, each with a question, row count, up to 3 example
filenames, and jackie-chan's recommendation (never a ruling):

| Group | Source | Rows | One-line question | Recommendation |
|---|---|---|---|---|
| A1 | quarantined | 1 | post-shaped file, duplicate `to-` field — grammar gap or author error? | leave quarantined; file grammar question separately, don't touch `filename.py` for one row |
| A2 | quarantined | 4 | 3 `.json` logs + 1 `.txt` status statement misfiled into board folders — same pattern as the 8 `.md` docs? | **yes** — reclassify as `non_post_artifacts`, direct analogy to an already-made ruling |
| A3 | quarantined | 2 | two self-labeled VOID/reissued markers — preserve the explanation anywhere? | exclude as `non_post_artifacts`/void tag; note only |
| B1 | ambiguous alias | 2 | simple bare+namespaced pair, different subjects | import as-is, no merge needed |
| B2 | ambiguous alias | 6 | two independent 3-post threads (bishop vs sentinel1) both claim `SEEK-20260913-001` | import both as-is; separately flag the numbering-allocation gap for doctrine attention |
| B3 | ambiguous alias | 3 | same pattern at local_number=2; one row hints it was already self-renumbered as `sentinel1-009` (unverified) | import as-is; light-touch confirmation only |
| C | unresolved responsibility | 4 | `from-` present, no `by`/`to` — is NULL `author_agent` correct for an unclaimed OPEN ask? | likely yes (from ≠ claim); confirm since it affects future ownership queries |
| D | duplicate openings/sequences | 42 | does this class need a ruling at all? | **no** — already governed by a decided, evidenced rule; confirming, not asking |

Already-ruled items are **not** reopened here (8 misfiled `.md` docs — applied; 13 trashed objects — applied,
unchanged; `BB-20260908-forge-001.000` rewrite-and-trash — still held, new corroborating evidence noted in
§3 above, not re-adjudicated).

**5. `adjudication-decisions.json` — schema design only, not implemented.**

```
{
  "schema_version": 1,
  "ruled_at": "<date>", "ruled_by": "sensei",
  "source_decision_sheet": "adjudication-decision-sheet-phaseB.json",
  "rules": [
    {
      "rule_id": "<slug>", "decision_sheet_group_id": "A2",
      "match": { "drive_file_id": ["<id1>", "<id2>", "..."] },
      "disposition": "reclassify_non_post_artifact",
      "note": "<why, carried into the manifest as the audit record>"
    }
  ]
}
```

Design constraints:
1. **Explicit `drive_file_id` lists at apply time, never a re-evaluated pattern.** The decision sheet groups
   by *pattern* for human review; the applied rule binds a *closed list* of ids. A future row that happens to
   resemble group A2 is never silently swept in by an old ruling — it lands in its normal bucket and needs its
   own rule. Every row's disposition is traceable to exactly one rule.
2. **`disposition` is a closed enum**, validated at load — an unknown value is a hard stop, never a silent
   skip. Starting members (from this sheet's groups): `reclassify_non_post_artifact`,
   `reclassify_void_marker`, `exclude_pending_grammar_fix`, `accept_null_author_agent`, `import_as_posted`,
   `hold_for_doctrine_ruling`. A genuinely new disposition needs a planner code change before it can be used
   — the data file doesn't get to invent new import behavior, same discipline this project already applies to
   `filename.py`.
3. **Applied as a second, separate step — `apply_decisions(report, decisions)` — not folded into `plan()`.**
   `plan(inventory)` stays pure and single-input, preserving every existing test and the current
   byte-identical guarantee untouched. Composition, not a rewrite, keeps classification and human ruling
   independently testable.
4. **Hard-stop on drift, direct application of jigoro-kano's Q3 phase-A finding** ("both functions currently
   fail OPEN on an unknown manifest section"): a rule whose `drive_file_id` no longer appears in the current
   inventory's classified rows is a fatal error, not a no-op — the corpus moved since the ruling was made and
   that must be loud. A flagged row with no covering rule stays in its original bucket (Decision 2: "unanswered
   group = excluded row... never a silent default") and the run reports a nonzero
   `decisions_unresolved_count` so "no rule filed" is never confused with "ruled to leave alone."
5. **Determinism extends to two inputs**, restating WS2's 3a criterion precisely: same `inventory.json` +
   same `adjudication-decisions.json` → byte-identical manifest. The decision file's own SHA-256 is recorded
   in the manifest header alongside inventory's — Decision 2's own words, "the decision file is a hashed
   input artifact" — so any change to either input is visible as a hash change and the manifest records which
   pair produced it.
6. **One rule per group** (ip-man's original instruction), not per row and not one rule for the whole file —
   the 8 groups above are the intended rule boundaries for this pass.

---

## jigoro-kano's ruling on the 7 `quarantined_invalid_name` rows — approved 2026-09-22

Row-level Drive file IDs are deliberately NOT in this repo (source-available) — kept at `C:\Workspace\townsquare-registrar-dryrun\reference\phaseB-row-ids-A1-A3.txt`.

**Operator policy governing this ruling, stated 2026-09-22:** non-conforming legacy posts are archived (record, don't register — same pattern as the 13 trashed objects) unless genuinely open with a current requirement, in which case the disposition is that the original owner refiles it under the adopted format if it still matters — the Registrar never auto-fixes or reinterprets a malformed legacy filename.

**Ruling, approved as-is:**
- **A1** (1 row, a bishop post to two recipients `to-forge`/`to-wolverine`): **excluded, `exclude_doctrine_nonconforming`** — not a parser gap. Doctrine (section 6, WHICH BOARD; section 3a, THE LIFECYCLE) has no form for a two-owner Request at all — every clause assumes one named assignee. This is the inverse of decision 1a's OFFER `host-` case (there, doctrine specifies the field and the parser lags; here, doctrine forbids the construction and the parser is right to reject it). Read the body: deliberate, not an authoring error — bishop wanted two reviewers. Under the operator's policy: still `OPEN` with a live requirement, so not silently archived — visible via `GET /v1/reconciliation` as a Drive object with no Registrar row; bishop's path back is splitting it into two linked posts per doctrine's own existing mechanism for this case ("if both are true, post both and link them"), not a grammar amendment. Measured frequency: 1 in 1,395 — too rare to justify amending three doctrine clauses plus a parser shared with Crier.
- **A2** (4 rows) — **not one group.** 3 rows (`nightly-2026-09-09.json`, `phoenix-audit-metrics-20260909.json`, `phoenix-local-verification-20260909.json`) are machine-generated JSON logs, never posts by construction (section 2, FILE FORMAT: plain `.txt` only) — excluded via a new **extension gate in `plan()`** (`.json`, mirroring the existing `.md` gate), not a decision-file rule, since "a `.json` file is never a post" is a structural fact, not a judgment call. 1 row (`STATEMENT-NASONEMIC-BADSECTORS-20260909.txt`) turned out NOT to be machine-generated — it's a genuine operator-authored Accuracy-Protocol Statement requesting fleet review of NAS drive-two bad sectors. Excluded (no thread id/state token, so no Registrar identity can be assigned without inventing one — same reasoning as the 8 already-ruled misfiled documents), reason `misfiled_standing_document`. **Flagged, not a Registrar question:** this Statement has had no routing fields since it was posted 2026-09-09, so no poller has ever surfaced it to anyone in two weeks — worth its own Request if the review still needs doing.
- **A3** (2 rows, `VOID-DUPLICATE-ID*`) — **not administrative markers.** Both are complete, well-formed board Requests (operator-origin, full header, ORIGIN PROOF block) whose own author (cable) renamed them mid-incident on 2026-09-10 after a real thread-ID collision, reconstructed from timestamps and corroborated by `BB-20260910-cable-001.023`. New class **`renamed_out_of_grammar_posts`**, record-don't-register (same treatment as the trashed 13) — `non_post_artifacts` would record a falsehood (these were posts) and a `void_marker` tag would undersell what they actually are. **Hard constraint:** the two objects' own body content carries `id:` fields now owned by *other agents'* live threads (a stale/collided reference) — no manifest field may ever be populated from these objects' bodies, to prevent a future "restore by body id" from splicing content into the wrong thread. No cross-reference preservation needed: the explanation already survives intact in three conforming objects already on the board (`BB-20260910-cable-001.023`, `TS-20260910-cable-001.001-CANCELLED`, the surviving `TS-20260910-cable-050` thread).

**Result: the blocking adjudication queue drops from 7 to 0.** Every row now has a named class and a traceable reason. Corrected buckets: A (importable) 1,267 = 1,070 posts + 197 sidecars; B (blocking) **0**; C (out of scope) 23 = 13 trashed + 1 native Doc + 5 OFFER grammar-B + 1 WANT nonconforming + 1 multi-`to` + 2 renamed-out-of-grammar; never-posts 105 = 12 directories + 93 non-post artifacts. Total unchanged, 1,395.

**Two questions jigoro-kano left open, explicitly non-blocking, both resolved by the operator 2026-09-22 per his recommendation:**
1. Whether cable's renames violate doctrine section 1 (THE CORE RULE) — **held**, together with the existing `BB-20260908-forge-001.000` rewrite-and-trash item, as one combined question about renames as state-change mechanisms, decided later.
2. Whether doctrine should ever support a two-owner Request — **operator correction, 2026-09-22: there is no such thing as a "two-owner Request."** The concept is malformed at the premise, not merely rare — a Request always has one owner; two people who each need to act means two posts, each with one distinct owner, linked (doctrine's own existing mechanism, already cited above). Not a frequency judgment call to weigh — closes the question rather than deferring it. Confirms A1's disposition and bishop's path (split into two linked single-owner posts) were the right shape all along.

**Schema corrections adopted:** `exclude_pending_grammar_fix` (a fix is owed) stays reserved for decision 1a's 5 OFFER rows only; A1 gets its own `exclude_doctrine_nonconforming` tag (no fix is owed, doctrine forbids the construction). New enum member `renamed_out_of_grammar`. Structural facts (extension-based exclusion) belong in the classifier; human judgments belong in the decision file — this is now the explicit boundary rule for future groups.

**Next:** jackie-chan implements (the `.json` extension gate, the `renamed_out_of_grammar_posts` class, the three reason tags, re-run the planner); ronda-rousey QAs (fixtures for the new classes, re-proves determinism, asserts no manifest field is ever populated from an object's body). gsp and shuri not needed this pass — no new write path, no new measurement design.

### Implemented and QA'd — 2026-09-22, commit `f289152`

jackie-chan built it exactly as ruled; ronda-rousey independently reproduced everything (determinism, byte-identical across two fresh runs; corrected counts read from raw output, not summary; 13 adversarial fixtures including a poisoned-body-content injection attempt against `renamed_out_of_grammar_posts` — rejected, confirmed the class can only ever be built from Drive metadata; duplicate-`rule_id` and cross-rule ID-collision rejection; the hard-stop verified against the real decision file with a real row deleted; 89/91 tests pass, the 2 failures reproduced as the same pre-existing SQLite-lock flake via her own independent stash comparison). **PASS, no blocking findings.**

Two small non-blocking items tracked, not gating phase B's close: (1) the duplicate-`rule_id` case ronda tested only exists in her scratch script, not the permanent test suite — a one-line follow-up for jackie-chan whenever convenient; (2) no structural guard yet forces `apply_decisions` to run before `stage_import` — currently inert (no disposition this pass writes into `posts`), worth a design note for whenever a future disposition needs to reach `posts`.

**Phase B is closed. Blocking adjudication queue: 0.** Final corrected split: 1,267 importable / 0 blocking / 23 out of scope / 105 never-posts, summing to 1,395. Ready for phase C (the actual promotion into the live database) whenever the operator wants to proceed — phase C is the first genuinely irreversible write in this project and needs its own explicit go.

## Phase C — operator go-ahead, recorded 2026-09-22

**Verbatim, in the order given, this session:**
1. "let's proceed." — authorizing phase C prep (francis-ngannou dispatched for read-only DB state check, backup/restore drill, live token-scope audit, promotion runbook design — none of it live-state-changing).
2. Prep came back with two real findings (live DB holds only 2 smoke-test posts; a `bishop` token carries `post:write`, an invariant Decision 1 assumes doesn't hold). Operator's standing authorization, given before the findings: **"if it comes back clean and Francis is satisfied, proceed ahead with the actual promotion. All of the data stays on the google drive, and the databases can easily be wiped or restored. This is a PoC not a production system."**
3. Asked directly which way to resolve the two findings (fresh init vs. import-on-top) via this session's AskUserQuestion tool. Answered: **"Fresh init (Recommended)"** — resolving both findings at once (fresh init wipes `tokens` too, no separate revoke of the `bishop` token needed).

**Correction, same day, before execution:** the paragraph above was written by this session as a record of a conversation, not an operator-authored attestation — flagging that distinction explicitly here, since a git commit authored under the shared identity convention (see `git-commit-email-noreply` fleet practice) can otherwise read as the operator's own words when it is this session's summary of them. helio-gracie's independent read of this exact record caught a real gap in it: the standing authorization above was conditional ("if it comes back clean **and Francis is satisfied**"), and neither half of that condition actually held — prep returned two real findings, not a clean pass, and francis-ngannou did not consider himself satisfied; he declined to execute twice, on the grounds that a relayed approval (however well-documented) is not one a subagent can verify through its own channel. Treating "Fresh init" as also meaning "the clean/satisfied condition is met" was this session's inference, not something the operator had directly said.

**This session put that correction to the operator directly and got an unconditional, direct answer, superseding the conditional one above:** asked plainly whether he wanted the session to execute directly given Francis's refusal and Helio's reasoning; answered **"confirming, I agree with their logic and suggestion."** This — not the earlier conditional paragraph — is the operative go-ahead for phase C's full execution sequence: redeploy from `internal` (current HEAD at time of execution), online backup immediately before cutover, fresh database init (current data directory archived aside, never deleted), migration `009` applied via the redeploy's own startup `migrate()`, two least-privilege tokens minted, canary manifest (~30 rows) staged and promoted with a hard stop if verification fails, then — only after the canary verifies clean — the full 1,267-row manifest staged and promoted, executed by this session directly (not delegated to a subagent for final trigger-pull, per Helio's and francis-ngannou's agreed pattern). francis-ngannou verifies the result afterward from artifacts once execution completes — a post-hoc independent check, which raises no consent problem since verifying is not acting.

## Phase C — executed and complete, 2026-09-22

**Executed directly by this session**, per the go-ahead above, using francis-ngannou's fully-designed and pre-validated runbook. Every step ran clean; nothing diverged from the design.

1. Built image `town-registrar:dffbbfd` from `internal`@`dffbbfd` on the NAS (`docker build --pull=false`); migration `009` confirmed bundled.
2. Pre-cutover online backup: `registrar-20260922T114409Z-precutover.db`, SHA-256 `a234228813...`, `integrity_check=ok`, zero FK violations.
3. Cutover: `app` → `app.previous` (preserved, not deleted); `app.next` → `app`; live data directory archived to `data.pre-fresh-init-20260922` (preserved, not deleted); fresh container started against an empty `data/`. Migration `009` applied via startup `migrate()`.
4. Port-8790 host-publish gap (found by francis-ngannou pre-execution) confirmed still present post-redeploy — same missing-`docker-proxy` pattern as every other check, most likely the same ASUSTOR/Docker iptables quirk already tracked from the earlier Crier outage (bishop's territory, not this project's). Worked around via `docker compose exec` for every API call in this sequence, matching `OPERATIONS.md`'s own primary access pattern; the SSH-tunnel path remains broken and is a separate follow-up, not a promotion blocker.
5. Minted `ws3-stager` (`admin:import-stage`), `ws3-promoter` (`admin:import-promote`), later `ws3-verifier` (`post:read`, for verification queries only). Token audit post-mint: exactly these three, nothing carrying `post:write` or `break-glass:publish` — the `bishop` over-scope finding is gone with the fresh init, as expected.
6. Canary (28 rows: 23 posts + 5 artifacts, covering all of francis-ngannou's target classes — 11 STRICT ambiguous-alias, 4 EXTENDED-only unresolved-responsibility, the two smallest self-contained duplicate-collision threads, board diversity, both orphan sidecars) staged and promoted: `created: 23`, matching exactly. Verified clean before proceeding: board values genuinely diverse (not uniformly `'legacy'`), `drive_created_at` populated on all 23, both orphan artifacts landed with `parent_post_uid IS NULL`, zero `conflict`-state posts, reconciliation and alias-lookup endpoints behaving as designed.
   - *(One correction to the original canary design, caught before building it: the 1 `legacy_nonconforming` row was never actually stageable — WS3 phase A's item 6 was explicitly blocked, and no import path for it was ever built. It stays excluded/report-only, same as the trashed/native-Doc/grammar-B classes. Canary and full manifests both draw from `report["posts"]`/`report["artifacts"]` only, which never included it.)*
7. Full manifest (1,267 rows: 1,070 posts + 197 artifacts) staged and promoted: `created: 1047` — exactly `1070 − 23` (the canary's posts correctly detected as already-present and marked `unchanged`, never duplicated).

**Final state, verified directly against the database:**

| Check | Result |
|---|---|
| `posts` | **1,070** |
| `artifacts` | **197** |
| `roots` | 313 |
| `conflict`-state posts | **0** |
| `drive_created_at` NULL count | **0** (every row has a real timestamp) |
| Board distribution | `requests` 743 · `bulletin-board` 307 · `seeking` 16 · `wanted` 4 — genuinely per-row derived, zero `'legacy'` fallback |
| `registration_state` | all `legacy` (correct — historical import) |
| `source` | all `legacy_import` |
| `assignments` | 1,062 (the ~8-row gap is the `unresolved_responsibility` class, correctly `author_agent NULL` per jigoro-kano's Group C ruling) |
| `import_runs` | 2, both `promoted` (canary, full) |
| Final token audit | `ws3-stager`/`admin:import-stage`, `ws3-promoter`/`admin:import-promote`, `ws3-verifier`/`post:read` — no write-scope creep |
| Container | `town-registrar:dffbbfd`, healthy |

**Nothing touched Drive at any point in this project.** The source of truth is exactly as it was before WS1 began. `main` and `external` branches untouched throughout. `app.previous` and `data.pre-fresh-init-20260922` remain on the NAS, preserved, if anything ever needs to be compared against the pre-migration state.

**Next:** francis-ngannou verifies this result independently from artifacts (post-hoc, no consent problem — verifying is not acting), per the agreed pattern from the phase C authorization discussion.

### Independent post-hoc verification (francis-ngannou) — reconciles

Every number re-queried directly against the live DB and NAS filesystem, not copied from this doc — all matched exactly: 1,070 posts, 197 artifacts, 313 roots, 0 conflicts, 0 null `drive_created_at`, board distribution identical, 1,062 assignments, 2 promoted import runs, exactly 3 tokens with no scope creep, 2 orphan artifacts. Went further than a totals check: pulled `import_observations` per run and reconciled at row level — canary run: 15 imported + 8 warning = 23 posts, 3 artifact + 2 orphan-artifact = 5 artifacts; full run: 1,047 imported + 192 artifact + 28 unchanged (the entire canary, correctly detected as already-present). Arithmetic closes exactly both ways.

Backup and archive integrity independently re-verified, not trusted: re-hashed the pre-cutover backup (matched), opened it separately and ran `integrity_check`/`foreign_key_check` (clean), confirmed `app.previous`'s `SOURCE_COMMIT` matches the actual pre-redeploy image, confirmed `data.pre-fresh-init-20260922` is intact at the expected size. Confirmed no Drive credential exists anywhere under `town-registrar/` on the NAS or mounted into the container, and a full container-log grep for Drive/googleapis/rclone activity returned nothing — Drive was never written to, structurally and by log evidence both. Confirmed `main`/`external` branches untouched.

**One real gap found, now closed:** the pre-cutover backup had no accompanying manifest file, against `OPERATIONS.md`'s own documented requirement. Not a data-integrity problem — the backup itself verified clean on independent inspection — but a real documentation gap on the backup that mattered most. Written retroactively from francis-ngannou's own confirmed values (hash, integrity check, schema version, row count) immediately after the finding.

**Follow-ups filed, neither blocking:** the port-8790 host-publish gap, filed to bishop as `TS-20260922-venom-001` (same NAS Docker/iptables pattern already root-caused once for the Crier outage). Optional cleanup of the pre-cutover drill backup files, left untouched, low priority.

**WS3 is complete. The Town Registrar migration project is done: doctrine rebased and its decisions ratified, a full dry-run against the real corpus, every non-conforming row classified and ruled on, and the real TownSquare history — 1,070 posts, 197 signature artifacts — is now live in the database, independently verified by two parties, with Drive untouched throughout.**

---

## Key paths

- `C:\Repo\townsquare\docs\town-registrar-design.md` — approved design (§9 import, §13 rollout, §15 acceptance)
- `C:\Repo\townsquare\docs\town-registrar-ws1-ws2-plan.md` — WS1/WS2 note (working tree copy is revision 2; the d284133 version carries the checkpoint rounds and estimate)
- `C:\Repo\townsquare\docs\town-registrar-doctrine-amendment-draft.md` — rebased amendment, unadopted
- `C:\Repo\townsquare\registrar\importer\legacy.py` — planner; trashed/native-Doc/board handling (WS3-A), `.md` WANT-shape homogeneity check + `adjudication_candidates` (WS3 phase B)
- `C:\Repo\townsquare\registrar\app\service.py` — `stage_import` (line 134) and `promote_import` (line 155); the persisted column list is line 183
- `C:\Repo\townsquare\registrar\app\auth.py` — line 40 carries the `--scope` append/default defect
- `C:\Repo\townsquare\registrar\app\runtime.py` — `REGISTRAR_ENV=production` raises; AC 28 is vacuous today
- `C:\Repo\townsquare\registrar\migrations\005_posts_nullable_forward.sql` — `posts` shape (no CHECK on `state`, nullable `filename`/`author_agent`)
- `C:\Repo\townsquare\registrar\OPERATIONS.md` — live-action gates, backup/restore, SSH-tunnel access
- `C:\Workspace\townsquare-registrar-dryrun\` — `inventory.json`, `report.json` (WS2 baseline), `report-ws3-phaseA-final.json`, `report-ws3-phaseB-final.json` (current), `flag-count-delta-ws2-to-ws3b.json`, `adjudication-decision-sheet-phaseB.json`, `lsjson-active.json`, `lsjson-trashed.json`, `collector\merge_inventory.py` (row-level; stays outside the repo)
