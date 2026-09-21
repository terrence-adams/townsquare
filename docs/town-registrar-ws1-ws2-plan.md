# Town Registrar — Workstreams 1–2 Design Note and Work Order

**Author:** ip-man (YNM Dojo lead architect)
**Date:** 2026-09-21
**Status:** Draft — pending jigoro-kano review before any Implement line proceeds
**Scope:** Doctrine amendment readiness (workstream 1) and dry-run legacy-import inventory design (workstream 2) only. Everything past these two depends on what the dry run finds.

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

## Work order

```
- Document: the session saves this design note verbatim — C:\Repo\townsquare\docs\town-registrar-ws1-ws2-plan.md
  (no corpus content, no credential material) — reviewed by jigoro-kano before any Implement line
- Coordinate: helio-gracie — GAME PLAN after that review, before any Implement line;
  CHECKPOINT at every delivery handoff (implement, review, test);
  final CHECKPOINT + GATEWAY before Sensei sees crew output.
  Standing instruction to enforce at every checkpoint: no agent has read corpus files into context.

- Implement (WS1): jigoro-kano — readiness review + rebase of
  C:\Repo\townsquare\docs\town-registrar-doctrine-amendment-draft.md onto the in-force
  G:\My Drive\N3rd0m\TownSquare\TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt.
  Scope is exactly: (1) rebase every section citation and both replacement-text instructions [W1-1];
  (2) draft the retention-reconciliation sentence [W1-3]; (3) draft path-is-not-identity [W1-4];
  (4) draft the adoption-ceremony paragraph incl. the old-grammar bootstrap [W1-7];
  (5) consolidate W1-2, W1-5, W1-6 into ONE "Open operator decisions" list with a recommendation each.
  Do NOT reopen the 12 binding rules, the gate table, or the truth-table. Do NOT arm any gate.
  Read-only: produce the revised text as a proposal; adopting, signing and publishing are the operator's.

- Implement (WS2a): tony-jaa — read-only Drive inventory collector emitting inventory.json
  (file ID, exact name, parent path, MIME, created/modified, size, trashed, provider checksum).
  Recommend Option A (rclone lsjson via the existing read-only Crier remote); document the
  Option A/B trade and which was chosen. `rclone link` is forbidden — lsjson only.
  Plan the run; the live execution is operator-gated per registrar/OPERATIONS.md.

- Implement (WS2b): jackie-chan — extend C:\Repo\townsquare\registrar\importer\legacy.py to the
  full exception/reconciliation taxonomy above; separate collector defects from corpus exceptions;
  emit per-root next_post_no; classify-and-count grammar B WITHOUT extending
  registrar\app\filename.py; keep content_sha256 null with not_computed_dry_run.
  Record (do not fix) the check_header zero-padding/priority defect as a finding for WS7.

- Peer review: jackie-chan — tony-jaa's collector: paging completeness, trashed/shortcut handling,
  name fidelity on the 4 native-Doc objects, and that file ID is present on every row.
- Peer review: gsp — credential scope and least privilege across both artifacts; proof that no
  code path can write to Drive or to the live Registrar DB; the rclone command allowlist; and the
  disclosure boundary (report + inventory.json stay OUT of the source-available repo;
  row-level output to C:\Workspace\townsquare-registrar-dryrun\ only).
- QA: ronda-rousey — fixture corpus carrying the known-nasty real cases: TS-20260906-016.002 and
  .003 (same thread, same sequence, two authors), the OFFER host- token, the WANT .md shape,
  the .gdoc/.txt same-name pair, an unsigned post, an orphan sidecar, a doctrine reference .txt.
  Prove: second run byte-identical to the first; zero Drive writes; zero rows in the live
  Registrar DB; collector-defect rows never appear as corpus exceptions.

- Done when:
  1. The amendment is rebased onto the doctrine actually in force, reviewed, and carries one
     consolidated open-operator-decisions list — awaiting Sensei, not adopted by anyone else.
  2. A dry-run exception/reconciliation report exists with a count for every class and a firm
     migration estimate derived from it — the estimate the design says cannot exist before this.
  3. It ran twice with identical output, wrote nothing to Drive, and promoted nothing into the
     live Registrar database.
  4. Steps 3 and 9 of design §9 are recorded as explicitly deferred in the report header.
  5. Total spend for workstreams 1-2 is within Sensei's "$60 cap".

- Watch for:
  * Cap risk. If WS1 review says the amendment needs more than a rebase, STOP and report —
    do not re-cut it inside the cap. If Sensei wants steps 3 and 9 in this pass, that is ~$90,
    and he should be told before the work starts.
  * Corpus-in-context. Any agent that starts reading board posts individually burns the cap.
  * Shared parser. filename.py is shared with Crier by design. Any edit to it is out of scope
    this phase and would need Crier regression cover.
  * NAS. Nothing from this phase is deployed to townsquare-registrar-registrar-1 (commit 4726278).
    The collector run, credential use, and any Drive touch are operator-gated live actions.
  * Grammar B is a governance answer, not an implementation convenience — if an implementer
    "just extends the parser," send it back.
  * Agent Registry stays untouched (design AC 14, amendment rollout prerequisite 8).
```

**Key paths:** `C:\Repo\townsquare\docs\town-registrar-doctrine-amendment-draft.md`, `C:\Repo\townsquare\docs\town-registrar-design.md`, `C:\Repo\townsquare\DOCTRINE.md`, `C:\Repo\townsquare\registrar\importer\legacy.py`, `C:\Repo\townsquare\registrar\app\filename.py`, `C:\Repo\townsquare\registrar\OPERATIONS.md`, `G:\My Drive\N3rd0m\TownSquare\TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt`.
