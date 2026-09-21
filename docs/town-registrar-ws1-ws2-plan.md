# Town Registrar — Workstreams 1–2 Design Note and Work Order

**Author:** ip-man (YNM Dojo lead architect)
**Date:** 2026-09-21 (revision 2, supersedes revision 1)
**Status:** Revised after Helio-gracie's GAME PLAN checkpoint — pending jigoro-kano review before any Implement line proceeds
**Scope:** Doctrine amendment readiness (workstream 1) and dry-run legacy-import inventory design (workstream 2) only. Everything past these two depends on what the dry run finds.

**W1-2 answered by Sensei, 2026-09-21: the board `.txt` is normative** (`G:\My Drive\N3rd0m\TownSquare\TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt`); the repo's `DOCTRINE.md` (v1.2) is a publication regenerated at each version. jigoro-kano's WS1 rebase proceeds as written below — no repricing needed.

---

## Problem

Two workstreams stand between the Registrar prototype and a defensible migration plan: ratify the doctrine amendment that authorizes the new post format, and run a read-only dry-run inventory over the real Drive corpus so that a migration estimate rests on evidence instead of assumption. Everything past those two depends on what the dry run finds, so this note stops there.

I read the two repo docs, the shared parser, the importer, and a sample of the live board. Findings below are from those artifacts, not from the prototype's smoke-test database.

---

## Workstream 1 — doctrine ratification: readiness review

The twelve binding rules themselves are sound. The gate table, the truth-table tests, and the explicit separation between "specifying a gate" and "arming a gate" are consistent with the governance-logic posture already on the board, and rule 7 (Crier read-only) matches the in-force standing rule "THE CRIER NOTIFIES; IT DOES NOT INTERPRET." Those parts should not be reopened — reopening them is how a governance pass turns into a week.

What blocks adoption is not the rules. It is that **the draft is written against the wrong doctrine artifact.**

**W1-1 (blocker). The draft targets a document that is not the one in force.**
`C:\Repo\townsquare\docs\town-registrar-doctrine-amendment-draft.md` says "Proposed target: TownSquare Doctrine after **Specification version 1.2**." That is `C:\Repo\townsquare\DOCTRINE.md` (markdown, source-available). The doctrine actually in force on the board is `G:\My Drive\N3rd0m\TownSquare\TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt` — signed, plain text, **different section numbering**:

| Draft's citation | v1.2 (repo) | v1.5 (board, in force) |
|---|---|---|
| "the §9 statement that sequence collisions cannot be prevented without a lock" | §9 Known limitations ✔ | §11 KNOWN LIMITATIONS (§9 is FINDING WORK) ✘ |
| "the absolute sentence in §1 … 'structurally impossible'" | §1 ✔ | §1 ✔ (wording differs: "Collision becomes structurally impossible rather than merely avoided") |
| Traceability table: §§8.3, 10 | present ✔ | no §8.3; §10 is STANDING RULES ✘ |

Every replacement-text instruction and most of the traceability table must be rebased before adoption means anything. Adopting as-written would amend a document nobody reads.

**W1-2 (blocker, operator decision). Which artifact is normative?** There are two live doctrine lineages — the signed board `.txt` at v1.5 and the published repo markdown at v1.2. Amending one leaves the fleet with two doctrines. This needs a one-sentence rule ("the board `.txt` is normative; the repo markdown is a publication, regenerated at each version") before an amendment lands anywhere. That is the operator's call, not the crew's.

**W1-3. Retention versus permanent identity is unaddressed.** v1.5 §8 is RETENTION — 60 DAYS. The amendment makes Registrar records permanent and defines `drive_verified`, but never says what a `drive_verified` post's state means once its Drive object ages out or is archived. Rule 4 gets halfway ("a Registrar record alone is not proof that a post exists on Drive"). One sentence is needed: retention-driven disappearance is an expected reconciliation class, never a verification failure and never an integrity alarm. Crew can draft the wording.

**W1-4. Move/archive versus identity.** Doctrine rejects rename and move as state mechanisms, yet the board demonstrably archives (`Archive\TOWN-SQUARE-DOCTRINE-v1.4-…`). Drive file IDs survive a move, so this is safe — but the amendment should say so explicitly: **path and board are observational metadata, never identity**, so archiving never re-registers a post. Crew can draft.

**W1-5 (blocker, operator decision). A second filename grammar exists on the board and no document acknowledges it.** The Seeking/Wanted boards use tokens and shapes outside both the design's typed-field list and the shared parser:

- `Seeking\OFFER-20260907-jeangrey-001.000-OPEN__host-jeangrey__client-work-laptop-full-capability-intermittent.txt` — a `host-` typed field (confirmed: the file's header carries `host: jeangrey`), which is not in the design's typed list (`pid, mode, priority, to, from, by, for, impact, cap, cat`) and not in `PREFIXED` in the parser.
- `Wanted\WANT-20260907-001__skill__kollective-display-timeout-debugging.md` — no `.SEQ-STATE` segment, `.md` extension.

Amendment rule 3 ("the signed bytes and filename MUST also agree on every other applicable typed routing field") and the design's "one versioned parser" claim are both incomplete against the live board. Whether grammar B is doctrine or undocumented drift is a **governance** question, and it must be answered here — not settled implicitly by whoever next edits the parser.

**W1-6 (operator decision). Native Google Docs are posts on this board.** `Bulletin Board\BB-20260911-forge-001.000-POST__…pending-confirmation.gdoc` exists *alongside* a same-named `.txt`, and a Request already on the board records the problem: `TS-20260913-sentinel1-007.000-OPEN__P2__to-forge__from-sentinel1__decisions-register-000-exists-twice-one-is-a-native-google-doc-that-get-media-cannot-read`. Doctrine §2 says posts are plain text; every amendment rule assumes a byte-hashable object. Needs an explicit disposition — preserved, never content-hashed, always reported — or a decision to reissue them as `.txt`.

**W1-7. Adoption ceremony and the bootstrap.** Board precedent for adoption is: new versioned `.txt` + `.sig` at board root, prior version moved to `Archive\`, BB announcement (`BB-20260907-jeangrey-005.000-…doctrine-v1.3-is-live-v1.2-archived`). Say plainly in the amendment that adoption itself is published **using the old grammar** (emitters are not enabled yet, by the amendment's own rule), and that the Drive write is an operator-gated action.

### What stays an open operator decision vs. what the crew can settle

**Operator only:** which doctrine artifact is normative and the sync rule (W1-2); whether this exact amendment becomes binding; whether grammar B is doctrine or drift (W1-5); disposition of native-Doc posts (W1-6); any gate arming (the draft already reserves this correctly — do not let it drift).

**Crew settles:** the rebase of all section citations onto the in-force text (W1-1); wording for retention-reconciliation (W1-3) and path-is-not-identity (W1-4); the ceremony paragraph (W1-7).

Scope discipline: this is a **rebase plus four short insertions and a decision list**. It is not a doctrine rewrite, and given the Charter 2.0 experience it must not become one.

---

## Workstream 2 — dry-run import inventory: design

### What exists and what does not

`C:\Repo\townsquare\registrar\importer\legacy.py` is a **planner over an inventory JSON that something else must produce**. It implements design §9 steps 4–8 and 10 partially. Missing outright: step 1 (the Drive listing itself — Registrar has no Drive credential by design), step 3 (header/signature verdicts), step 9 (webViewLink validation and canonical URL), and the persisted-mapping half of step 7.

Three concrete defects to hand the implementer, all verified against real board files:

1. **`check_header` cannot pass on any legacy post.** In `C:\Repo\townsquare\registrar\app\filename.py`:

   ```python
   values={"id":parsed["thread"],"event":str(parsed["seq"]),"state":parsed["state"]}
   ```

   `parsed["seq"]` is `int`, so `event` compares as `"2"`; real headers are zero-padded (`Requests\TS-20260906-002.002-RESOLVED__by-cable.txt` has `event: 002`). Likewise a filename `P2` token compares against a `priority:` header line that legacy posts do not carry. Running step 3 today would flag ~100% of the corpus. This is the native profile applied to legacy posts; the design says legacy posts keep a legacy verification profile, and that profile does not exist.
2. **Grammar-B files quarantine silently as a parse error.** `host-jeangrey` is consumed as a slug, the real slug then raises `duplicate slug field`, and the object lands in `quarantined` indistinguishable from genuine corruption. Same for the `.md` WANT shape.
3. **Collector defects and corpus exceptions share one bucket.** `except (FilenameError,KeyError)` means a missing `drive_file_id` (a bug in whatever produced the inventory) is reported identically to a malformed legacy name (a fact about history). Those must never be one class.

Also worth the implementer's attention: a slug beginning `for-`, `cat-`, `cap-`, or `mode-` is silently absorbed as a typed field. That class should be counted, not assumed absent.

### Approach

**Two artifacts, run entirely off the NAS, writing nothing anywhere the fleet reads.**

**(a) Collector → `inventory.json`.** A read-only listing producing, per object: Drive file ID, exact name, parent folder path, MIME type, createdTime, modifiedTime, size, trashed flag, and provider checksum. Transport choice, with the trade stated:

- **Option A (recommended for this pass): rclone `lsjson --recursive` against the existing read-only Crier remote.** Zero new credentials, zero new scope, one command. Costs: no `webViewLink`, so design step 9 becomes *explicitly deferred* rather than satisfied, and canonical URLs are the design's "marked fallback" for every row; and rclone's Drive backend can synthesize export extensions on native Google Docs, distorting four observed names. Both are acceptable **because the migration estimate depends on counts and collision classes, not on URLs** — but they must be recorded as deferred, never faked.
- **Option B: Drive `files.list` with a metadata-only read scope.** Satisfies step 9 and gives exact names. Costs operator time to provision a credential and a wider surface to review. Escalate to B only if the dry run shows name fidelity or URL binding actually changes the estimate.

Hard safety rule either way, and this one is not obvious: **`rclone link` is forbidden.** On the Drive backend it can create a sharing permission — a write to the ledger's access state from a tool everyone thinks is read-only. The allowlist is `lsjson` only.

**(b) Planner → exception/reconciliation report.** Extend `legacy.py` to emit the classes acceptance criterion 10 requires, each counted separately and never merged:

duplicate openings · duplicate sequences (already partly there) · ambiguous un-namespaced aliases · orphan sidecars · ambiguous sidecar parents · unsigned posts (~204 `.sig` against ~1,087 `.txt` — a *class*, not an error) · non-post artifacts (doctrine/protocol/register documents that will never parse) · **grammar-B objects, classified and counted but deliberately not parsed** · native-Doc objects · collector defects · per-root `next_post_no`.

**The grammar-B call is the important one.** The parser is shared with Crier by design ("no component independently reimplements token parsing"), and whether grammar B is doctrine at all is question W1-5, unanswered. So the dry run **classifies and counts grammar B without extending the parser** — the operator still gets the number he needs for the estimate, the shared parser is untouched, Crier carries zero regression risk, and the grammar decision stays where it belongs.

**Content is not read.** No header verdicts, no signature verification, no SHA-256 in this pass. `content_sha256` stays `null` with an explicit `not_computed_dry_run` marker; the provider checksum is recorded under its own name. This follows from defect 1 above — header verdicts today are noise — and it keeps the credential at metadata-only, which forecloses content claims structurally rather than by promise.

### Cost control — the single biggest budget risk

**No agent reads the corpus.** 1,087 `.txt` + 204 `.sig` + `.md` + `.gdoc` must never pass through an LLM context. The collector and planner are scripts; crew read the report's aggregates plus at most 20 sampled exception rows. This is the difference between a $40 workstream and a $300 one, and it is the line to hold at every handoff.

### Disclosure boundary

The `townsquare` repo is source-available. A full corpus inventory is a map of the fleet — hostnames, agent names, project structure, the shape of internal decisions. **The report and `inventory.json` do not go in the repo.** Code and aggregate counts may; row-level output goes to `C:\Workspace\townsquare-registrar-dryrun\` on Venom and nowhere else until the operator decides where to file it. The design note itself is fine in `docs/` (that repo already publishes NAS paths in `OPERATIONS.md`).

### Trade-offs and the alternative I rejected

**Rejected: promote the dry run into the live Registrar staging database on the NAS now.** It is tempting since the container is already up and healthy at commit `4726278`. Rejected because the report *is* the decision input — promoting couples an un-adopted doctrine, an unreviewed parser gap, and a corpus nobody has yet characterized to a live database, and it spends the cap on deployment mechanics instead of on evidence. Design §13 orders it the other way for good reason. Corollary for the crew: **nothing built in this phase gets deployed to the NAS container.** The dry run runs off-box.

**Accepted trade:** deferring step 9 (URL binding) and step 3 (header/signature verdicts) costs completeness against the design's step list. It buys a report that is readable rather than one where every one of ~1,087 rows carries a false mismatch. State both deferrals in the report header so the gap is visible.

### Budget — flagging, as instructed

WS1 + WS2 fit US$60 **only** under three conditions: the corpus never enters an agent context; steps 3 and 9 are carved out as above; and there is **one** review round, not an iteration loop. Rough allocation: WS1 ≈ $12, WS2 ≈ $40, $8 reserve.

Honest read: that is at the cap with no slack. If review finds substantial rework — most likely on W1-2 or W1-5, where an operator answer could change the shape of the amendment — **stop and report; do not spend into the cap re-cutting the work.** If Sensei wants steps 3 and 9 done in this pass rather than deferred, the realistic number is closer to US$90 and he should be told that before the work starts rather than after.

---

## Revision 2 — Helio's GAME PLAN checkpoint and ip-man's response (2026-09-21)

Helio-gracie independently re-derived this note's two load-bearing claims directly against source files — the doctrine section-numbering mismatch (W1-1) and the `check_header` zero-padding defect — both **matched**. He also found process/scope gaps, closed below.

**C1 (gsp's scope) — agreed, bounded to two items.** Design §14 defers "security review" out of MVP scope; Sensei confirmed no customer ever touches this. gsp's review is exactly: (1) the rclone command allowlist including the `link` prohibition; (2) proof no code path can write to Drive or the live Registrar DB. Both survive the §14 carve because they protect the fleet's real ledger, not a customer. The disclosure boundary (report/inventory.json outside the repo) moves from "gsp opines" to "QA mechanically asserts" — cheaper and enforced rather than promised.

**C3 (checkpoint cadence) — agreed, exactly two Helio checkpoints, named.** CP1 (before the operator-gated live collector run — the one irreversible step) and CP2 (after the report and estimate, with the final GATEWAY). WS1's handoff gets no separate checkpoint: its output is a document proposal Sensei adopts himself, and Helio already independently re-derived its load-bearing claim.

**R1 (closes A2) — execution context named, not left as "off-box."**

| Step | Host | Shell / session | Elevation | Notes |
|---|---|---|---|---|
| Collector (`rclone lsjson`) | NAS `192.168.2.3` (NASOneMic) | interactive SSH as `batman`, bash on the NAS, initiated from Venom PowerShell | non-elevated | Uses the existing read-only Drive remote; runs on the host, **not** inside `townsquare-registrar-registrar-1` |
| Collector output staging | NAS | same session | non-elevated | NAS-local path under `batman`'s home, **not** inside any rclone/Drive-synced tree |
| Transfer | Venom ← NAS | Venom PowerShell (`scp`) | non-elevated | |
| Planner (`legacy.py`) | Venom | PowerShell, venv in `C:\Repo\townsquare` on branch `internal` | non-elevated | Output to `C:\Workspace\townsquare-registrar-dryrun\` |

Unverified and not asserted: the exact rclone config path/remote name on the NAS. WS2a's first deliverable is locating and confirming it — read-only scope confirmed before any listing command is proposed. If the credential isn't on the NAS or its scope is wider than `drive.readonly`, tony-jaa stops and reports rather than deciding the transport alone.

**R2 (closes A1 / Done-when #3) — the "ran twice, identical" claim was wrong against a live board; split in two.**
- **3a — planner determinism (offline, checkable):** two planner runs over one frozen `inventory.json` produce byte-identical reports (equal SHA-256).
- **3b — collector stability (live, bounded):** two collector runs compared only on a stable projection `{file ID, name, parent path, MIME type, createdTime, size}` over the intersection of file IDs. `modifiedTime`, trashed-state transitions, and single-run-only objects are excluded from comparison and reported as a counted delta, not a failure. A changed *stable* field on an existing file ID **is** a failure.

**R3 (closes Done-when #2) — "firm migration estimate" defined:** one row per exception class with an exact count; a split into (a) importable unattended, (b) requires human adjudication, (c) out of scope; an effort range in hours with its arithmetic basis stated (adjudication rate × count of class (b), plus stated fixed overhead). Dollars are derived and are information for Sensei's next decision, never a pass/fail gate.

**R4 (closes Done-when #5) — spend measurement named:** spend against the cap = the sum of named agent invocations, from the session's own `/cost` accounting, reported at each checkpoint and recorded by Helio. The collector/planner runs themselves cost nothing — scripts under operator approval, not agent invocations. **Stop rule: if running total at CP1 exceeds US$30, stop and report rather than proceeding into WS2b.**

**R5 (closes C2) — citation discipline:** v1.5 numbers 13 standing rules *inside* section 10 and separately has a section 11 — "section 11 (KNOWN LIMITATIONS)" and "standing rule 11 (BE BRIEF)" are different objects. jigoro-kano cites by number **and** title throughout the rebase, never bare "§11".

**R6 — branch:** all work is on `internal` (this note is at `4193c53`, `origin/internal`). `main` is not the working branch for this project. `external` is a separate, not-yet-started future initiative — out of scope, nothing here touches it. `internal` is a branch on a **source-available** repo, not a private one — the disclosure rule is unchanged and now mechanical: row-level inventory/report output lives at `C:\Workspace\townsquare-registrar-dryrun\`, outside the git tree, QA asserts it.

**R7 (non-blocking, folded into WS2b design) — two Helio findings that change counts:**
- `NAME_RE` anchors on `\.txt$`, so every `.md`/`.gdoc` object raises `invalid TownSquare filename` and lands in the same bucket as genuinely corrupt names. The taxonomy must branch on **extension before parsing**, or grammar-B `.md` files and native Google Docs get miscounted as corruption.
- The misparse classes are **two, not one**: `for-`/`cat-`/`cap-` slugs are absorbed *silently* as typed fields (wrong data, no signal); `mode-<x>` and `pid-<non-ULID>` *raise hard errors* and quarantine the object (no data, loud signal). Opposite failure modes, separate counts.

**R8 (closes A4) — repriced via a shorter plan, not a smaller number on the same one.** Two structural changes: WS2b (jackie-chan) reviews the collector *and* implements the planner against fixtures in one invocation, before any live run; gsp reviews *before* the run, not after (proving "no write path" after the write already happened is worthless). Result: 8 invocations, ~$32–48 projected, $12–28 reserve.

| # | Invocation | Purpose |
|---|---|---|
| 1 | jigoro-kano | Note review **and** WS1 rebase in one call — halts if any concern is blocking |
| 2 | tony-jaa | Credential verification + collector + run plan |
| 3 | jackie-chan | Review tony-jaa's collector **and** implement WS2b against fixtures |
| 4 | gsp | Bounded review (2 items) |
| 5 | ronda-rousey | Fixture QA + planner determinism (3a) |
| 6 | helio-gracie | **CP1** — gates the operator-approved live run |
| — | *(session runs collector + planner under operator approval — not an invocation)* | |
| 7 | jackie-chan | Migration estimate from the report aggregates |
| 8 | helio-gracie | **CP2 + GATEWAY** |

Collapsing jigoro-kano's review and rebase into one call is a deliberate, cost-driven narrowing of the D·D·D gate — acceptable only because his instruction is *if blocking, return concerns only, produce no rebase* (he keeps the power to halt), and because WS1's output is a proposal Sensei must still adopt, not shipped code. Not a precedent for the WS2 code path.

**If even this doesn't fit the cap, say so now:** the migration estimate (#7) collapses into CP2 as raw counts with no effort range — a degraded but honest deliverable. Never cut to save money: gsp's two items, QA, or CP1.

---

## Work order (revision 2 — supersedes revision 1; branch: `internal`)

```
- Document: the session applies revisions R1-R8 above to this note
  (branch internal, base 4193c53) — reviewed by jigoro-kano before any Implement line
- Coordinate: helio-gracie — CHECKPOINT at exactly two points, named, with reason:
    CP1 — after gsp + ronda, BEFORE the operator-gated live collector run.
          (Named because this is the only irreversible step: a command against the fleet's
           real ledger using a real credential. Verify tony-jaa's credential findings, gsp's
           no-write proof, and the running spend total against the $30 stop rule.)
    CP2 — after the run, the report, and the migration estimate. Includes final GATEWAY.
  WS1's handoff has NO checkpoint: its output is a document proposal Sensei adopts himself,
  and Helio has already independently re-derived this note's two load-bearing claims.

- Implement (WS1): jigoro-kano — one invocation, two parts.
  Part 1: review this note. If any concern is blocking, RETURN CONCERNS ONLY and produce no rebase.
  Part 2 (only if not blocked): rebase
    C:\Repo\townsquare\docs\town-registrar-doctrine-amendment-draft.md onto the in-force
    G:\My Drive\N3rd0m\TownSquare\TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt (Sensei has ruled: the
    board .txt is normative — see the note under Status above).
  Scope is exactly: (1) rebase every citation and both replacement-text instructions, citing
  BY NUMBER AND TITLE throughout [R5]; (2) draft the retention-reconciliation sentence [W1-3];
  (3) draft path-is-not-identity [W1-4]; (4) draft the adoption-ceremony paragraph incl. the
  old-grammar bootstrap [W1-7]; (5) consolidate W1-5, W1-6 into ONE "Open operator decisions"
  list with a recommendation each (W1-2 is now answered, drop it from the list).
  Also: one round on the C1 bounding of gsp's scope — if a third item is wanted, name which of
  the two it displaces.
  Do NOT reopen the 12 binding rules, the gate table, or the truth-table. Do NOT arm any gate.
  Read-only: produce the revised text as a proposal; adopting, signing and publishing are the operator's.

- Implement (WS2a): tony-jaa — one invocation, in this order.
  (1) VERIFY FIRST: locate the Crier service user's rclone config on NAS 192.168.2.3, confirm
      the remote name and that its Drive scope is read-only. Report both. If the credential is
      not there, or its scope is wider than drive.readonly, STOP AND REPORT.
  (2) Collector emitting inventory.json: file ID, exact name, parent path, MIME, created/
      modified, size, trashed, provider checksum. `rclone link` is FORBIDDEN — lsjson only.
  (3) Run plan with host/shell/elevation per R1's table: collector runs ON the NAS host as
      batman over SSH from Venom PowerShell, NOT inside townsquare-registrar-registrar-1;
      output to a NAS-local path outside any Drive-synced tree; pulled to Venom by scp.
  Plan only — execution is operator-gated per registrar/OPERATIONS.md.

- Implement (WS2b): jackie-chan — one invocation, two parts.
  Part 1: review tony-jaa's collector — paging completeness, trashed/shortcut handling, name
    fidelity on the 4 native-Doc objects, file ID present on every row.
  Part 2: implement the planner in C:\Repo\townsquare\registrar\importer\legacy.py AGAINST
    FIXTURES (pure function over inventory.json — no live data needed). Full exception
    taxonomy; collector defects separated from corpus exceptions; per-root next_post_no;
    grammar B classified and counted WITHOUT extending registrar\app\filename.py;
    content_sha256 null with not_computed_dry_run.
    Fold in R7: branch the taxonomy on EXTENSION BEFORE PARSING; count the two misparse
    classes separately (silent absorption vs. hard error).
    Record, do not fix: the check_header zero-padding/priority defect — a WS7 finding.

- Peer review: gsp — EXACTLY TWO items, before the run, not after:
    (1) the rclone command allowlist including the `link` prohibition;
    (2) proof that no code path can write to Drive or to the live Registrar DB.
  "Least privilege across both artifacts" is out of scope — design §14 defers security review.
- QA: ronda-rousey — fixture corpus carrying the real nasty cases: TS-20260906-016.002 and .003
  (same thread, same sequence, two authors), the OFFER host- token, the WANT .md shape, the
  .gdoc/.txt same-name pair, an unsigned post, an orphan sidecar, a doctrine reference .txt,
  a for-/cap- slug, a mode-<x> hard-error name.
  Prove: 3a planner determinism (two runs, one frozen inventory.json, equal SHA-256);
  zero writes to Drive; zero rows in the live Registrar DB; collector-defect rows never appear
  as corpus exceptions; and ASSERT the output path is outside C:\Repo\townsquare\.

- Done when:
  1. The amendment is rebased onto the doctrine actually in force, cited by number AND title,
     reviewed, carrying one consolidated open-operator-decisions list — awaiting Sensei,
     adopted by nobody else.
  2. The report contains a count per exception class, a split into (a) importable unattended /
     (b) requires adjudication / (c) out of scope, and an effort range whose arithmetic basis
     is written out. Dollars are information for Sensei's next decision, not a gate.
  3a. Planner determinism proven: two runs over one frozen inventory.json, byte-identical.
  3b. Collector stability proven on the declared stable projection over the intersection of
      file IDs; modifiedTime, trashed transitions and single-run objects excluded and reported
      as a counted delta. A changed stable field on an existing file ID is a failure.
  4. Nothing was written to Drive; nothing was promoted into the live Registrar database.
  5. Design §9 steps 3 and 9 are recorded as explicitly deferred in the report header.
  6. Spend within Sensei's "$60 cap", measured as the sum of named agent invocations from the
     session's /cost accounting, recorded by Helio at CP1 and CP2. Stop rule: >$30 at CP1 means
     stop and report.

- Watch for:
  * Cap. 8 invocations, $32-48 projected, thin reserve. If WS1 needs more than a rebase, STOP.
    If the estimate (#7) has to be cut to stay under, cut it — never cut gsp's two items,
    QA, or CP1.
  * `internal` is a branch on a SOURCE-AVAILABLE repo, not a private one. Row-level inventory
    and report output never enter the git tree. Never touch `external`.
  * Corpus-in-context. No agent reads board posts individually. Aggregates + <=20 sampled rows.
  * Shared parser. filename.py is shared with Crier. Editing it is out of scope this phase.
  * NAS. Collector runs on the NAS HOST, never in townsquare-registrar-registrar-1 (4726278).
    The run, the credential use, and any Drive touch are operator-gated live actions.
  * Grammar B is a governance answer, not an implementation convenience. If an implementer
    "just extends the parser," send it back.
  * Agent Registry stays untouched (design AC 14, amendment rollout prerequisite 8).
```

**Key paths:** `C:\Repo\townsquare\docs\town-registrar-doctrine-amendment-draft.md`, `C:\Repo\townsquare\docs\town-registrar-design.md`, `C:\Repo\townsquare\DOCTRINE.md`, `C:\Repo\townsquare\registrar\importer\legacy.py`, `C:\Repo\townsquare\registrar\app\filename.py`, `C:\Repo\townsquare\registrar\OPERATIONS.md`, `G:\My Drive\N3rd0m\TownSquare\TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt`.
