# Ip-man's ruling on jackie-chan's projector findings 1-3 (R1-R3)

Delivered 2026-09-26, answering the ESCALATE in helio-gracie's checkpoint. R1: parent:
must be a bare thread id, else flagged parent_malformed and placed nowhere. R2: a
collided thread is never placed, as a node or an attachment. R3: intake is by level,
never nested regardless of whether parent: resolves. Also resolves a drafting gap in
ip-man's own v2 (A3 governs all four fields a scoping event may set, not just level:).
Confirms nothing has been filed on the real board yet, so the fix pass runs now, before
any flag fires on real data. Amends helio-gracie's proposed sequence: jackie-chan reviews
this ruling before ronda-rousey starts; R2 covers attachments too; red/green runs happen
in a fresh clone with raw output. Extracted verbatim from the subagent transcript, not
retyped; save_verbatim.py's CLI reads only an end_turn text block, and this agent's report
was instead delivered as a SubagentHandback tool_use input field, so this was pulled by
hand from that same field.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=0839a66ad3300b6fd478da25cf418a45836b89a8fc4e3a64ae99c32175872801 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-ae5fe517479186bf5.jsonl:123 message=msg_011CfRfkCfooetPuZopqjzw3 -->
# TownSquare tracker: rulings on jackie-chan's projector findings 1–3, and the Track 2 fix pass

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** design ruling. jackie-chan reviews it before any test or code is written. Nothing is pushed, and nothing touches the board.

**Proposed path:** `C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md`, branch `internal`, not pushed.

**This answers** the ESCALATE in helio-gracie's checkpoint (the TownSquare half of `docs\helio-checkpoint-tracker-and-revere-20260926.md`). That checkpoint is on `docs\jackie-chan-projector-review-20260926.md`.

**Labels:**
- *measured*: I read or searched it this run.
- *inferred*: reasoned from what I read, not executed.
- *reported-by X*: X's claim, which I did not check.

**Shorthand, defined once:**
- **F1, F2, F3:** jackie-chan's findings 1–3, as Helio labels them.
- **R1, R2, R3:** my rulings on those findings.
- **R1a–R3:** the test fixtures in §5.
- **Q1–Q3:** trial questions 1–3 as the trial Bulletin states them.
  - Q2: "do filed items carry the fields correctly, per the projector's own report-only flags".
  - Q3: "did one real ask from each of the operator and Shuri become a confirmed, scoped Story".
- **G3:** D19's rule that the newest event carrying a field wins.
- **D1:** posts are never refused.
- **D23:** thread ids are namespaced. A *collided* id has two different `.000` opens.
- **A3:** kano's amendment 3, as accepted in v2 §2: Sensei's yes, not the scoping, sets the level.
- **Bare thread id:** one thread id and nothing else, in the canonical grammar, with any prefix (TS, SEEK, OFFER, WANT, BB).
- **DoR:** Definition of Ready.

**Recusal (Tribunal rule 5, limb (ii)), declared now.** This note answers F1–F3 and resolves a drafting gap in my own v2 (see "The design-text question" below). If any of these questions is referred to the Tribunal, I am conflicted and will not sit.

## 1. The problem, stated back

F1–F3 are edges the design never decided:
- what `parent:` means when its value is not a bare thread id;
- whether a collided thread may still be drawn as one item;
- whether intake means "unscoped items" or "unscoped items at top level".

The projector made its own choice in each case. Two of those choices skew exactly what Q2 and Q3 read.

## 2. What I checked

- **Read** [measured]:
  - jackie-chan's review, and Helio's checkpoint (the TownSquare half).
  - v1, kano's review, and v2. v3 turned out to be unrelated: it is the claude-app registration check.
  - `tracker\projector.py`, all 7 test files and `boardfixture.py`.
  - `registrar\app\filename.py`.
  - The trial Bulletin `BB-20260925-venom-001.000` on the Drive mount.
- **Helio's line numbers still match.** The three `parent:` read sites are placement (:316–327), attachments (:409–415) and `_claimed_by` (:258–265). Intake is at :420–423 [measured].
- **No existing test pins today's behaviour for these shapes.** No test mentions intake, `no_project`, `unscoped` or `thread_collided`. Every `parent:` value in the 61 tests is a bare id. The only collided fixture is `test_flags.py` test_3 [measured: grep]. So every ruling below adds behaviour.
- **Nothing is filed yet.** No line in any file on Requests, Seeking, Wanted or Bulletin Board starts with `level:` or `parent:` [measured: case-insensitive grep on the Venom mount as synced at this read. I confirmed grep reads content there by matching the Bulletin's `subject:` line].
  - So the trial has filed no tracker item, and no flag has fired on real data.
  - This supports Helio's assumption that the flags have not yet fed a view for Sensei.
- **The Bulletin's terms** [measured]:
  - It records Sensei's choice of nesting option (b).
  - The window runs through 2026-10-25.
  - It approves "Sections 4-6, 8 and 9 of v1, as amended by v2", with each file named by SHA-256.

## 3. The rulings

### R1 — `parent:` must be a bare thread id. Any other value is reported and places nothing.

**Ruling.**
- **The validity test.** A `parent:` value is valid only if it is a bare thread id. The test uses the one canonical grammar:
  - complete the value as `<value>.000-OPEN.txt`;
  - it must parse with `parse_filename`;
  - the thread id that comes back must equal the value itself.

  There is no new regex. The equality check is what rejects annotations, event suffixes, second ids and paths.
- **What happens to an invalid value.**
  - It is flagged **`parent_malformed`** on that thread, with detail `{"parent": <raw value>, "ids_found": [<each thread id _thread_ids finds in it, in order>]}`. `parent_not_found` is not raised as well.
  - It places nothing. A tracker item shows at top level, as if it had no parent. A SEEK, WANT, BB, OFFER or TS sub-request is not attached.
- **Which value is checked.** The check applies at projection time to the value G3 selects: the newest event carrying a non-empty, non-duplicated `parent:`. It is not applied in `parse_tracker_header`.
  - A malformed newest value does not fall back to an earlier clean one. `level:` already behaves this way (`invalid_level`).
- **One value at all three read sites.** Placement, attachments and `_claimed_by` all read the same validated value (v1 §5: "one meaning everywhere").
  - `_claimed_by` shows no observable change. A post with a malformed `parent:` is never attached, so no claim is computed for it.
  - It reads the same value anyway, so the three sites cannot drift apart.
- **Unchanged:**
  - `parent_not_found` and its `thread_exists` detail. After R1 they only ever describe a well-formed id, so `thread_exists` is always true.
  - A bare id that names a thread which is not a tracker item (a Bulletin, say) stays `parent_not_found` with `thread_exists: true`.
  - `nesting_violation` still fires on an epic or unscoped item that carries `parent:` at all, whatever the value.
  - DoR line 1 still fails a Story whose `parent:` does not resolve to a Feature.
  - A node's `parent` still reports the header's raw value.

**Why.**
- **The design defines the field.** v1 §4 defines `parent:` as "exactly one thread id", and gives the reason: "The parent is the item, not one of its events."
  - Placing an annotated value would mean reading `parent:` with the free-text grammar of `references:`.
  - That widens the field through behaviour, not through a decision.
- **There is a precedent.** The one existing rule for a malformed tracker-field value is `invalid_level`: the value is reported and takes no effect. R1 gives `parent:` the same rule.
- **It keeps Q2 honest.** Q2 counts filing errors through the flags. A malformed value that still places correctly tends to stay uncorrected. The post-trial amendment should codify the grammar the trial actually used.
- **The fix is cheap.** Appending one event with the bare id repairs it, and the flag names that id.

**Rejected alternatives.**
- **jackie-chan's fix:** accept a value that collapses to exactly one TS id, and flag only otherwise. Helio's three objections hold:
  - it accepts the annotated value with no flag, which hides from Q2 the very error Q2 counts;
  - it accepts an event id as its thread;
  - it would report a real non-TS parent as malformed.
- **Place the item and flag it.** This is inside the range Helio accepts. It gives a better tree the moment the error happens, but it makes the malformed form work for the whole trial.
  - *What would change my mind:* real filings hit this more than once, and the misplaced item costs Sensei a correction. Then place-and-flag is the better trade. That would be decided in the post-trial amendment, with the flag counts as evidence.

### R2 — A collided id is never placed, either as a tracker item or as an attachment

**Ruling.**
- A thread whose id has two different `.000` opens is not built as a tracker node, and it is not attached to one.
- Wherever the projector would otherwise have placed it, it is reported once as `thread_collided`, with both openings in the detail.
- Anything naming it in `parent:` is reported as `parent_collided` and shown at top level, as today.
- `resolve()` must keep checking "collided" before "not found". `test_flags.py` test_3 already guards this.

**Why.**
- **Today's merged node mixes two posts.** It is built from two unrelated posts by newest-wins, so its state, level and project can come from either one.
  - That is exactly the guess the collided-parent rule already refuses (v1 §6 flag 3, and v1's watch-for (d)).
- **Attachments are included, because the merge and the harm are the same** [inferred from the newest-wins merge at :229–248].
  - A collided SEEK can show CLOSED (need met) while the other post's need is still open.
  - That skews the list of open needs that Q1's "next steps" reads.
  - Leaving attachments out would mean documenting a new asymmetry, which is the kind of blind spot F2 found.
- **It is cheap.** The change is one condition at two sites. Collisions should also be rare during the trial: ids are namespaced (D23), and the one known collision is a Bulletin (`BB-20260909-venom-005`, v1 §6).

**Rejected alternative: document the asymmetry** (Helio's cheaper fallback). It saves two lines, but it leaves an item whose state may be wrong inside the rollups.

### R3 — Intake is by level. An unscoped item is never nested.

**Ruling.**
- Every tracker item whose current `level:` is `unscoped` is listed in `intake`, and nowhere else.
- Its `parent:`, if it has one, is never followed for placement. The item is not nested under another item and is not counted in any rollup.
- Its flags are exactly today's:
  - `nesting_violation`, with expected level none, and actual level equal to the named item's level when that id resolves;
  - `parent_not_found`, `parent_collided` or (under R1) `parent_malformed`, where they apply.

**Why.**
- **Intake is about waiting, not position.** Under A3, "unscoped" means "awaiting Sensei's yes", and intake is where that wait is seen. Where the item sits in the tree has no bearing on it.
- **Nesting would show unconfirmed structure.** A3 exists so that the header shows only structure Sensei has confirmed. Nesting an unscoped ask under confirmed work, and counting it in that work's rollup, does the opposite.
- **It protects Q3.** Q3 follows asks through intake to confirmed Stories, so an ask that drops out of intake by mistake skews Q3.

**Rejected alternatives.**
- **Keep "unscoped items at top level", and document it.** Then "Nothing is dropped silently" is true only for a reader who already checks the flags.
- **List the item in intake and also nest it.** The same node would appear twice in the output, and unconfirmed work would count in a confirmed rollup.

### The design-text question: may a scoping event set `parent:`? No.

**Where the text disagrees:**
- v2 A3 reads: "The scoping event keeps `level: unscoped` and puts the proposed level in its body. The event that transcribes Sensei's yes carries `origin: operator` and sets `level:`, `parent:`, `project:` and `repo:`."
- v2 also says v1 stands "except where §0 below says otherwise". §0's A3 row names only `level:`.

**The ruling: A3 governs.** That row's own "Why" column points to A3, and A3's text changes all four fields. The row is an incomplete summary of the change it cites, and A3's text is what the Bulletin approved.

**What follows:**
- For all four fields, A3 supersedes v1 §8 step 2 ("That event sets `level:`, plus `parent:`, `project:` and `repo:` where they apply").
- The scoping note carries its proposals in its body.
- An ask may still carry `project:` (and `repo:`) from its filing, when the ask names one (v1 §4).
- This adds no rule. It reads the approved text, and it corrects a summary gap in my own v2.
- It also means F3's shape is a filing mistake, not the normal path. With R3, the projector shows it correctly even when that mistake is made.

## 4. Now or wait: now, before any flag fires on real data

**Run the pass now.** It should land before the first projection is shown to Sensei or read for Q2 or Q3.
- **The timing is ideal.** Nothing has been filed yet [measured, §2]. If a flag's meaning changed after the trial had already counted some flags, Q2's counts from before and after the change could not be compared [inferred].
- **It needs no permission.** Once jackie-chan has looked, the pass is fully ruled. It touches only the repo, never the board.
- **Filings do not wait on it.** The rules filers already follow avoid all three shapes (Helio): a bare `parent:`, no `parent:` on an unscoped ask, and a fresh id for each thread.

Whether the pass runs this session or opens the next one is Helio's call on pace. His "what would change this" already covers it, and I agree.

**Where I amend Helio's sequence, and why:**
1. **jackie-chan looks at this ruling before ronda-rousey starts.** This is Helio's own condition ("unless he picks an option outside jackie-chan's"). R1 departs from jackie's fix, and R2 and R3 add detail he did not propose. House law also requires a reviewed decision before tests encode it. He gets one pass.
2. **R2 covers attachments too.** That adds one fixture.
3. **The red and green runs are recorded at their own commit, in a fresh clone, with raw output.** The tree is shared, and this is the standard of evidence that Helio's Revere checkpoint had to ask for after the fact.

Everything else is as Helio proposed. There is no second review round.

## 5. Fixtures (ronda-rousey; one per ruled behaviour)

- They go in one new test file under `tracker\tests\`. No existing test is edited.
- Ids and test names are hers.
- Each red failure should print what the projector actually produced: the flags, and the placement the assertion checked. That way the red run also serves as the measurement Helio delegated for jackie-chan's run claims (his claims 9, 12 and 15).

| # | Board | Expected after the fix | At her commit |
|---|---|---|---|
| R1a | Feature F (`project: townsquare`). Story S with `parent: <F> (its Feature)`. | One `parent_malformed` on S: `parent` is the raw value, `ids_found` is `[F]`. No `parent_not_found`. S is not among F's children. S is in `no_project` (the first direct test of it: jackie's finding 6b). S's `story_not_ready` reasons still include `parent_not_feature`. | fails |
| R1b | Story S (`project: townsquare`). SEEK K with `parent: <S>.001`, which is an event id. | One `parent_malformed` on K, with `ids_found` `[S]`. No `parent_not_found`. K is not in S's attachments. | fails |
| R1c (guard) | BB post B with no tracker fields. Story S with a bare `parent: <B>`. | One `parent_not_found` on S, with `thread_exists: true`. No `parent_malformed`. | passes; it pins R1's boundary |
| R2a | One TS id with two `.000-OPEN` files: by-venom (`epic`, `townsquare`) and by-forge (`feature`, `kollective`). This is jackie's shape. | One `thread_collided` on that id, naming both openings. The id appears nowhere in `projects` (at any depth), `no_project` or `intake`. | fails |
| R2b | Story S (`project: townsquare`). One SEEK id with two `.000-OPEN` files, each with `parent: <S>`. | One `thread_collided` on the SEEK id. The SEEK is not in S's attachments. | fails |
| R3 | Epic E (`project: townsquare`). U1: `level: unscoped`, `parent: <E>`. U2: `level: unscoped`, no parent. | `intake` holds U1 and U2. U1 is not among E's children. One `nesting_violation` on U1: `parent` is E, `expected_level` is None, `actual_level` is "epic". | fails (U1 is missing from intake) |

## 6. What stays open (backlog, not this pass)

- **Into my post-trial amendment:** F4, F5, F6a, and F8's reason code.
- **Into the post-trial Viewer design note** (owner ip-man; the jet-li and francis-ngannou lanes sit there): the deployment points in F7 and F8, meaning the mtime check and cache-by-path.
- **Closed by this pass:** F6b, through R1a and R3.
- **One item of my own, in the same class as R1.** v1 §4 gives `project:` a slug rule, `[a-z][a-z0-9-]*`, that the projector never checks.
  - So a malformed value creates a project bucket named after the raw text, instead of raising a flag.
  - It is visible, not silent. Let a real case drive it.
- **Helio's delegated claim 17** (F4's run) stays with F4. Nothing in this pass depends on it.

```
WORK ORDER — tracker Track 2 fix pass, R1–R3 (amends v1 §9 Track 2; repo only; nothing pushed)
- Document: the session saves this ruling with its SHA-256 to
  C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md (branch internal, not pushed).
  It extracts the text from this handback the same way it saved the review and the checkpoint.
  jackie-chan reviews it in one pass before ronda-rousey starts:
    - does each ruling close his finding;
    - does R1's departure from his fix lose anything he meant;
    - does R2's attachment clause, or R3's "never nested", open an integrity gap;
    - his own concerns.
  He shows the command and its output for any run, or labels the point "by reading".
  If he raises a concern, the session resumes ip-man once. That answer is saved beside this
  ruling and stands for this pass. Any disagreement that remains goes to helio-gracie as an
  ESCALATE.
- Coordinate: helio-gracie.
    - GAME PLAN: none as a separate step. His 2026-09-26 ESCALATE already set this pass's order
      and its gate (his Next items 1–4). The session starts ronda-rousey only after jackie-chan's
      review is filed, plus my answer if he raised a concern.
    - CHECKPOINT: one, after bruce-lee's green run. It covers jackie-chan's review, ronda-rousey's
      commit and bruce-lee's pass together, and confirms they happened in that order.
    - GATEWAY: none. Nothing here needs Sensei's decision, and the projector's use is already
      approved (BB-20260925-venom-001).
- Implement:
  (1) ronda-rousey, first, on internal, before any code:
      - one new test file under tracker\tests\, holding R1a, R1b, R1c (guard), R2a, R2b and R3
        as §5 specifies;
      - no edits to existing tests;
      - a red run at her commit, in a fresh clone, with raw output: the summary line, the FAILED
        lines and the exit code. R1a, R1b, R2a, R2b and R3 fail by assertion; R1c and the
        existing 61 pass; there is no collection error.
  (2) bruce-lee, after (1): one pass to green, in tracker\projector.py only.
      - Implement R1–R3 as ruled.
      - FLAGS gains parent_malformed, and thread_collided's comment covers attachments.
      - The module docstring states R1–R3 as rulings and cites the ruling file.
      - Its "choices the design does not pin" list keeps only what is still the module's own
        choice: rollup scope, what counts as an "open" child, readiness while not terminal,
        no_project, and Archive depth.
      - No test edits.
      - A green run at his commit, in a fresh clone: the summary line and exit code 0.
- Peer review: jackie-chan, on the ruling (see the Document line). There is no separate code
  review. The diff is small, ronda-rousey's fixtures pin every behaviour before the code is
  written, and helio-gracie reads the diff against §3.
- QA: ronda-rousey. The tests-first step is the QA. helio-gracie delegates any run he wants
  re-checked to her, in a fresh clone at bruce-lee's commit.
- Done when:
  (1) the ruling is saved with its SHA-256, and jackie-chan's review was filed before
      ronda-rousey's commit;
  (2) ronda-rousey's commit adds one test file, changes nothing else, and fails at its own commit
      as §5 predicts;
  (3) bruce-lee's commit changes only tracker\projector.py, and the whole suite passes at it with
      exit code 0;
  (4) for Q2, "do filed items carry the fields correctly, per the projector's own report-only
      flags", the flags now make no false claim about a thread (R1) and never describe a merge
      of two posts (R2). For Q3, an ask can no longer fall out of intake (R3);
  (5) helio-gracie's CHECKPOINT has run;
  (6) nothing is pushed.
- Watch for:
  (a) The tree is shared. Other sessions and dispatches may be working in C:\Repo\townsquare.
      - Stage only your own paths: never git add -A, never commit -a.
      - Check git status before committing.
      - Run the red and green runs in a fresh clone at your own commit.
      - internal already carries commits from other work (Helio's flag (b)), so the pre-push
        range check applies whenever anyone pushes.
  (b) Where R1's check lives: on the value G3 selects, at projection time. Placed inside
      parse_tracker_header, it would change what the header-parser tests mean, and a malformed
      newest value would fall back to an earlier one.
  (c) One grammar only. Bareness is decided by parse_filename, with the equality check.
      ids_found comes from _thread_ids.
  (d) R2 must keep resolve()'s order: collided before not-found. test_3 guards this.
  (e) Filing side (the session, venom): scoping events carry level: unscoped and no header
      parent: (§3). The design templates' trailing "# new" notes are for readers. Copied into a
      header, they produce exactly invalid_level and parent_malformed.
  (f) The backlog stays backlog (§6).
```

**Commands.** Run these on Venom, in Git Bash, from the dispatched agent's own scratch directory, with no elevation. Each agent runs them at its own commit.
- Make a fresh clone at a commit:
  `git clone C:/Repo/townsquare ts-<sha> && git -C ts-<sha> checkout <sha>`
- Run the suite and show the exit code (for either the red or the green run):
  `cd ts-<sha> && python -m pytest tracker/tests -q; echo "exit=$?"`
- Check a commit's scope (helio-gracie):
  `git -C C:/Repo/townsquare show --stat <sha>`

**Files**
- C:\Repo\townsquare\docs\jackie-chan-projector-review-20260926.md
- C:\Repo\townsquare\docs\helio-checkpoint-tracker-and-revere-20260926.md
- C:\Repo\townsquare\docs\townsquare-project-tracker-design.md (v1: §4, §5, §6, §8, §9)
- C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md
- C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md (§0, §2 A3)
- C:\Repo\townsquare\tracker\projector.py
- C:\Repo\townsquare\tracker\tests\test_flags.py (test_3 guards R2's resolve order)
- C:\Repo\townsquare\tracker\tests\boardfixture.py
- C:\Repo\townsquare\registrar\app\filename.py
- G:\My Drive\N3rd0m\TownSquare\Bulletin Board\BB-20260925-venom-001.000-OPEN__to-all__impact-informational__from-venom__project-tracker-on-trial-venom-only-not-doctrine.txt
- To be created: C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md