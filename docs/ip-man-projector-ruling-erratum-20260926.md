# Ip-man's erratum to the R1-R3 projector ruling

Delivered 2026-09-26. Corrects four problems Helio's checkpoint found in the ruling's own
text, not its code: (a) thread_exists is 'always accurate', not 'always true' -- a bare id
still correctly reports false when no such thread exists; (b) confirms Helio's reading of
R3 -- an unscoped item keeps only value-derived flags, never edge-derived ones (no cycle,
no rollup counting), and confirms bruce-lee's U-X edge case matches the ruling as written,
no code change needed; (c) narrows Done-when (4) to what R1-R3 actually deliver rather
than extending the code to match an overclaim; (d) adds four items to the backlog
(section 6). No code, test, or docstring changes; the ruling file itself stays as filed,
pinned to its own hash. Pulled byte-for-byte from the subagent transcript's SubagentHandback
field, not retyped -- save_verbatim.py's CLI reads only an end_turn text block, so it
cannot extract this delivery shape; the hash below was computed by hand, not printed by
that tool.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=2993e48910f6bf24cdc4781d429d4ef564f4f87f3fa8d51ab268ae66b5286346 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a72779f174031c00a.jsonl:53 message=msg_011CfRmPKf7M7tgjef4unTbN -->
# TownSquare tracker: erratum to my ruling on jackie-chan's projector findings 1–3 (R1–R3)

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** erratum. It corrects the text of my ruling, and changes no rule in R1–R3 and no code. It stands for this pass (helio-gracie's checkpoint, Next 2). Nothing is pushed, and nothing touches the board.

**Proposed path:** `C:\Repo\townsquare\docs\ip-man-projector-ruling-erratum-20260926.md`, next to the ruling, on branch `internal`, not pushed. The session saves it, because I have no write tool.

**What it amends:** `docs\ip-man-projector-ruling-20260926.md`.
- It was filed at 871dec9 [reported-by helio-gracie]. Its header (line 15) records sha256=0839a66ad3300b6fd478da25cf418a45836b89a8fc4e3a64ae99c32175872801. I did not recompute that hash.
- The ruling file stays as filed. Editing it would make that hash, and the header that pins it, false.
- Where the two disagree, this erratum governs.
- Line numbers with no file named are the ruling file's. `:NNN` is a line of `tracker\projector.py` in the working tree.

**Why it exists:** helio-gracie's checkpoint on this pass (`docs\helio-checkpoint-r1-r3-20260926.md`, §5) found four problems in my text, not in the code. bruce-lee's d1fd2b7 matches §3 as written. I rule on each problem below.

**Labels** (as in the ruling):
- *measured*: I read or searched it this run.
- *inferred*: reasoned from what I read, not executed.
- *reported-by X*: X's claim, which I did not check.

**Shorthand:**
- **(a)–(d):** the four items in helio-gracie's checkpoint §5, in his order.
- **R1–R3, F1, G3, D1, Q2, Q3:** as the ruling defines them. Q2 and Q3 are trial questions 2 and 3.
- **Edge:** the child-to-parent link along which the projector places an item.
- **The U–X case:** bruce-lee's judgment call 2. U has `level: unscoped` and `parent: X`; X has `level: feature` and `parent: U`.

**Recusal (Tribunal rule 5, limb (ii)), declared now.** This erratum answers further questions on my own ruling:
- what `thread_exists` guarantees;
- which flags an unscoped item keeps, and whether it may act as a parent;
- what Done-when (4) claims;
- what goes to the backlog;
- bruce-lee's judgment calls 1–3.

If any of them is referred to the Tribunal, I am conflicted and will not sit.

## 1. What I checked

- **Read** [measured]:
  - bruce-lee's report, helio-gracie's checkpoint, and jackie-chan's review of the ruling;
  - `tracker\projector.py` in the working tree. It carries d1fd2b7's changes as bruce-lee and helio-gracie describe them. I have no git, so I did not compare it to the commit;
  - `tracker\tests\test_flags.py`, `tracker\tests\test_ruling_r1_r3.py`, `tracker\tests\test_nesting.py` lines 76–93, and v2 §3 K4.
- **Test coverage** [measured: grep of `tracker\tests` for `thread_exists`, `cycle` and `unscoped`]:
  - Only R1c asserts `thread_exists`, and it asserts `true`. test_flags test_2 asserts the flag, its thread and `parent`, but not `thread_exists`. So helio-gracie's correction to bruce-lee's report holds.
  - No test puts an unscoped item in a cycle or under a closed parent.
- **I ran nothing.** Every statement below about behaviour comes from reading the lines cited.

## 2. Rulings

### (a) `thread_exists`: corrected. R1 makes it always accurate, not always true.

**Correction.** In R1's "Unchanged" list (line 92), keep the bullet's first sentence. Replace "After R1 they only ever describe a well-formed id, so `thread_exists` is always true." with:

> After R1 they only ever describe a bare thread id, so `thread_exists` is always accurate. It is true when that thread is on the board but the projector did not build it as a tracker item (R1c's Bulletin). It is false when no thread with that id is on the board (test_flags test_2's shape). What R1 removes is F1's error: a thread that exists was reported as missing, because the annotated value was looked up whole.

**Why.**
- bruce-lee is right, and so is the code. `thread_exists=parent in threads` (:349) is unchanged by d1fd2b7 [measured]. A bare id need not name a thread that exists, so "always true" never followed.
- The guarantee I meant is the one in the replacement. After R1, only a bare id reaches that lookup, so its answer is exact either way. bruce-lee read my intent correctly.

**Should a test pin the `false` case? Yes, but not in this pass.**
- `thread_exists` is the detail F1 was about, and only its `true` half is pinned (R1c).
- The behaviour is correct and unchanged. helio-gracie has paced this pass to take no more code, and one assertion does not justify reopening it.
- It goes into §6 as a rider on the next commit that edits tracker tests (see (d)).

### (b) R3's flags: helio-gracie's reading confirmed

**Ruling.** R3 keeps every flag computed from the `parent:` value itself, and drops every flag computed from the edge it no longer draws. bruce-lee's code does exactly this [measured: read :361–364]. An unscoped item still goes through `resolve()`, but it is never entered in `resolved`. So:
- **It keeps these, with their usual detail:** `nesting_violation` (:366–367), and `parent_malformed`, `parent_collided` or `parent_not_found` where they apply (:344–349).
- **It never:**
  - joins a `cycle`, because the cycle walk runs over `resolved` only (:370–386);
  - raises `open_child_under_closed_parent` or `project_restated_conflict`, which fire only on placed children (:405–406, :424–426);
  - counts toward the `closed_parent_with_open_children` of the item its `parent:` names (:427–429).

**Correction.** In R3's ruling (line 138), replace "Its flags are exactly today's:" with "From its `parent:`, it gets only the flags about the value itself, with their usual detail:". Keep the two sub-bullets under it, and add after them:

> - It gets no flag that depends on an edge, because R3 draws none for it: no `cycle`, `open_child_under_closed_parent` or `project_restated_conflict`. It is not counted in the `closed_parent_with_open_children` of the item its `parent:` names.
> - R3 governs the unscoped item as a child only. As a parent it is unchanged (see "The unscoped item as a parent" in this erratum).

**Why.**
- **"Exactly today's" was loose.** I meant that the listed flags keep today's detail, as U1's `nesting_violation` does in the R3 fixture. I did not mean that every flag the old code raised survives. Read literally, it would keep the edge flags, and R3's operative words rule those out: the parent is "never followed for placement", and the item is "not nested" and "not counted in any rollup".
- **An edge flag would contradict the view.** A flag about an edge that is not drawn describes a placement the view does not show. In the U–X case, a `cycle` flag would report a loop that the view does not contain: the view shows X under U, and U in intake.
- **Nothing goes silent.** Any unscoped item with a `parent:` carries `nesting_violation`, whether or not the parent resolves. In the U–X case both items carry one, and each names the other [measured: read :366–367].
- **Rejected: keeping a second, unplaced set of edges only to detect cycles.** helio-gracie's checkpoint §2, item 2, rejects it too. It is more code, for no known case, and it reports one filing mistake twice.

**The U–X case as ruled** [measured: read]:
- no `cycle` flag;
- U in intake, with X nested under it;
- a `nesting_violation` on each item.

So d1fd2b7 does not depart from the ruling. helio-gracie's checkpoint set aside a new work-order line in case I had ruled the other way. It is not needed.

**The unscoped item as a parent: a deliberate non-gap** (jackie-chan's observation).
- **What happens.** A well-formed item that names an unscoped ask in `parent:` is placed under it, inside intake. It is flagged `nesting_violation`: for a Feature, expected `epic`, actual `unscoped`.
- **Why it is deliberate.** Every wrong-level parent gets this treatment under option (b) and D1: the item is placed as filed, reported, and never refused. `test_nesting.py` lines 76–93 pin the Feature-under-a-Story case.
- **Why it fits R3.** R3 exists to keep intake complete. The unscoped ask stays a root either way, so it stays in intake, and Q3 still sees it.
- **Why not refuse it.** Refusing to nest under an unscoped item would need a new placement rule and a new home for the child. The shape is already flagged as a filing mistake.
- *What would change my mind:* a real filing puts confirmed work under an unscoped ask, and a reader of the view is misled by it. Then the post-trial amendment decides, with that case as evidence.

### (c) Done-when (4): narrowed, not extended

**Correction.** Replace Done-when (4) (lines 258–260) with:

> (4) For Q2:
> - a `parent:` value that is not a bare thread id is reported as `parent_malformed` and places nothing, so `parent_not_found` can no longer report an existing thread as missing (R1);
> - a collided thread is never placed, as a tracker item or as an attachment, and its merged `parent:` is never followed or flagged (R2).
>
> For Q3: an unscoped item's `parent:` can no longer take it out of intake (R3).
>
> Two things are outside this criterion:
> - a collided unscoped ask, which R2 governs and which shows only as `thread_collided`;
> - the level flags on a collided thread (§6).

**Why narrow.**
- **The overclaim was mine, in the wording.** This narrows the criterion to the decision that was reviewed and tested. It does not lower what was built.
- **The R1 clause narrows too.** R1 fixes one false claim, F1's. "No false claim about a thread" promised more than one ruling can show.
- **The Q3 clause cannot be kept true inside R2.** Whether a collided thread is an unscoped ask at all is read from its merged `level:`, the very value R2 refuses to trust. Listing it in intake in any form would act on that guess. Trusting the value only when both openings agree would be a new rule, for a case with no known instance.
  - R2 should win. A node whose state, level and project may each come from either post does more harm than an ask shown only as a flag, and the flag keeps the ask visible.
  - So this clause has to narrow whatever I decide about Q2.
- **The Q2 clause could be kept true by extending R2 to the node loop's level checks.** But that is a code change and a new test for a shape with no known instance. At my ruling's §2 read, no `level:` line was on any live board, and the one known collision is a Bulletin.
  - The gap is small. The level those flags report is still the value on the id's newest event that carries `level:`.
  - What it costs is the collision itself, which goes unreported when no other site would place the thread. Q2 then counts one error where there are two.
- **A done criterion should state what its rulings rule.** jackie-chan reviewed R1–R3 as written, and ronda-rousey pinned them as written. Extending R2 now would be a new ruling without either step.
- *What would change my mind:* a collided thread carrying `level:` turns up on the real board during the trial. Then the §6 item below is pulled forward as its own work-order line, tests first.

**Effect on the checkpoint.** helio-gracie found that (4) holds as R1–R3 are ruled, and the narrowed text says only that. So it asks for no new check of the code. He confirms the match at his GATEWAY (see the work order).

### (d) §6: four additions

Add these to the ruling's §6 (lines 197–205). Each names an owner.
- **Into my post-trial amendment (owner ip-man): `claimed_by` is not checked against the board** (jackie-chan's observation).
  - A SEEK's `claimed_by` is the first TS id, other than its parent, in its CLOSED event's `references:`. It is taken as written [measured: read :294–298].
  - So it can name a collided Request with no flag anywhere, which is his case. By the same reading, it can also name a Request that is not on the board at all.
  - It is only a display label: stored on the attachment and shown in the output (:459, :502–503). It feeds no placement, no rollup, and no Q2 or Q3 count.
  - Let a real case drive it.
- **Into my post-trial amendment (owner ip-man): a collided thread's level flags** (bruce-lee's observation, with helio-gracie's extension). The node loop's level checks (:324–330) run before its collision check (:331). So:
  - `invalid_level` and `level_on_non_request` on a collided thread report a level that G3 picked from across both posts' events (bruce-lee);
  - when no other site would place the thread, it never gets `thread_collided` at all. helio-gracie found this for a TS thread with an invalid `level:`, because the attachment site skips every TS thread that carries `level:` (:452). By the same reading, it also holds for a non-Request that carries `level:` and no `parent:`.
  - This is outside R2, which rules placement only, so d1fd2b7 conforms to R2. Any fix must still raise `thread_collided` only once per id across the node and attachment sites.
- **Two test pins, riding on the next commit that edits tracker tests (owner ronda-rousey).** Each pins behaviour this erratum rules; neither is a fix:
  - a bare `parent:` that names no thread gives `parent_not_found` with `thread_exists: false` (see (a));
  - the U–X case gives no `cycle`, puts U in intake with X as its child, and puts a `nesting_violation` on each, naming the other (see (b)).

  Pulling these forward is helio-gracie's call on pace.
- **A docstring pointer, riding on the next commit that edits `tracker\projector.py` (owner bruce-lee).** The module docstring cites only the ruling file (:31). That commit cites this erratum beside it, so a reader sent to the ruling from the code also finds the correction.

### Also: bruce-lee's judgment calls 1 and 3 — agreed, no text change

- **1.** Checking for a collision before resolving at the attachment site is what R2 means. Whether a collided post is somewhere the projector "would otherwise have placed it" depends on its merged `parent:`, which is the very value R2 refuses to trust. So the only coherent reading is "at the site that does the placing".
- **3.** Raising `parent_malformed` only where a parent is read for placement is what R1 means. It matches `parent_not_found`, and an item that is never placed has no parent read.

## 3. What this erratum does not do

- It changes no code, no test and no docstring. d1fd2b7's docstring already states R2 and R3 the way this erratum reads them (:42–50) [measured].
- It reopens nothing in the pass. helio-gracie's PROCEED stands, and his Next 1 (ronda-rousey's re-run) is unaffected.
- It edits nothing in the ruling file.

```
WORK ORDER — erratum to the R1–R3 ruling (text only; no code; nothing pushed)
- Document: the session saves this erratum with its SHA-256 to
  C:\Repo\townsquare\docs\ip-man-projector-ruling-erratum-20260926.md (branch internal, not
  pushed), extracting it from this handback the same way it saved the ruling. The ruling file is
  not touched.
  Review: none as a separate step, because:
    - it authorizes no code;
    - it brings my text into line with what helio-gracie's checkpoint already found;
    - his Next 2 made it standing for this pass.
  Any §6 item that later drives code, the test pins included, comes in under that commit's own
  work order.
- Coordinate: helio-gracie.
    - GAME PLAN: none; there is no Implement line.
    - CHECKPOINT: none on the erratum by itself, for the reasons above.
    - GATEWAY: the one his checkpoint already requires before this pass is shown to Sensei or
      pushed. There he confirms that the erratum covers (a)–(d) and that its commit adds one file.
- Implement: none.
- Peer review: none (see Document).
- QA: none, because no code changes. Next 1 (ronda-rousey's delegated re-run at e40c928 and
  d1fd2b7) is unaffected and still open.
- Done when:
  (1) the erratum is saved beside the ruling, with its SHA-256;
  (2) its commit adds that one file and changes nothing else, so the ruling file is not in it;
  (3) nothing is pushed.
- Watch for:
  (a) The tree is shared. Stage only the erratum's path, check git status first, and never use
      -A or -a.
  (b) The §6 additions stay backlog. The test pins and the docstring pointer ride on later
      commits. They are not dispatched now unless helio-gracie pulls them forward.
  (c) Anyone reading the ruling needs this erratum beside it, since the erratum governs wherever
      the two disagree.
```

**Commands.** The session runs these on Venom, in Git Bash, with no elevation.
- Before committing: `git -C C:/Repo/townsquare status --short -- docs/`
  - Expected: the erratum shows as untracked (`??`), and the ruling does not show as modified.
- After committing: `git -C C:/Repo/townsquare show --stat <sha>`
  - Expected: one file, the erratum.

**Files**
- C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md (lines 92, 138, 197–205, 258–260)
- C:\Repo\townsquare\docs\helio-checkpoint-r1-r3-20260926.md (§2 item 2, §3, §4, §5)
- C:\Repo\townsquare\docs\bruce-lee-r1-r3-implementation-20260926.md
- C:\Repo\townsquare\docs\jackie-chan-review-of-ruling-20260926.md (§3)
- C:\Repo\townsquare\tracker\projector.py (working tree, carrying d1fd2b7)
- C:\Repo\townsquare\tracker\tests\test_flags.py (test_2, lines 93–100)
- C:\Repo\townsquare\tracker\tests\test_ruling_r1_r3.py (R1c, line 166)
- C:\Repo\townsquare\tracker\tests\test_nesting.py (lines 76–93)
- C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md (§3 K4)
- To be created: C:\Repo\townsquare\docs\ip-man-projector-ruling-erratum-20260926.md