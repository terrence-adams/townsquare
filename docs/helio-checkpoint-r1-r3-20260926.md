# Helio-gracie's checkpoint on the tracker Track 2 fix pass (R1-R3)

Delivered 2026-09-26. Verdict PROCEED on all three lines (jackie-chan's review,
ronda-rousey's fixtures, bruce-lee's implementation): right order, no gaps, no other
commit touched tracker/ in between. Confirms bruce-lee's code matches the ruling as
written, including all three of his judgment calls. Flags four problems in the ruling's
own text for ip-man to fix in a short erratum saved beside it, never editing the pinned
file in place: the 'always true' wording error bruce-lee found; one confirming line
needed for R3's edge-flag reading; Done-when (4) overclaims what R2/R3 actually deliver;
and two missing backlog items for section 6. Delegates the actual test re-run to
ronda-rousey, since the tree is shared and Helio ran no crew code himself. Pulled
byte-for-byte from the subagent transcript's SubagentHandback field, not retyped --
save_verbatim.py's CLI reads only an end_turn text block, so it cannot extract this
delivery shape; the hash below was computed by hand, not printed by that tool.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=67c73b00564981eb774a23dacbdf3534da36a0104ff6f7a73fb944f19b64244d source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a5230cbc10cc3e0c6.jsonl:117 message=msg_011CfRkU3CvimvtrCW281137 -->
**Helio: CHECKPOINT on the TownSquare tracker Track 2 fix pass (R1–R3)**

**Bottom line.** The steps ran in the right order with no gaps: jackie-chan's review was filed, then ronda-rousey started and committed her failing tests, then bruce-lee started and committed his fix. No other commit touched `tracker/`. All three lines get **PROCEED**. bruce-lee's code matches §3 of the ruling as written.

Four problems remain in the ruling's own text, and ip-man should write the fixes himself:
- the "always true" sentence is wrong;
- R3 needs one line on which flags an unscoped item keeps (his judgment call 2);
- Done-when (4) is worded more broadly than R2 and R3 actually rule;
- §6 is missing some backlog items.

The one check I could not do myself is re-running the tests, so I've handed that to ronda-rousey. Nothing here needs Sensei.

Shorthand used below:
- **R1–R3:** ip-man's three rulings (§3 of the ruling). **F1–F3:** the jackie-chan findings they answer.
- **G3:** the newest event that carries a field wins.
- **Done-when (n):** the work order's numbered done criteria.
- **Edge:** the child-to-parent link the projector places an item along.

## 1. Sequence: right order, no gaps (measured with git log/show and the first timestamp in each agent's transcript)

| Step | Evidence | Time (-0500) |
|---|---|---|
| Ruling filed | 871dec9, only that file | 02:40:03 |
| jackie-chan starts | transcript 07:40:16Z | 02:40:16 |
| His review filed | 1b62f72, only that file | 02:52:48 |
| ronda-rousey starts (16 s later) | transcript 07:53:04Z | 02:53:04 |
| Tests committed | e40c928, parent 1b62f72, 1 file, 265 insertions | 03:05:25 |
| Her report filed | 737328f, docs only | 03:08:16 |
| bruce-lee starts | transcript 08:08:33Z | 03:08:33 |
| Fix committed | d1fd2b7, parent 737328f, tracker/projector.py only, 62 lines added / 18 removed | 03:15:37 |

- Since the projector was built (334eb26), only e40c928 and d1fd2b7 touch `tracker/`. The commits from other work in between (4d091c3, 9c1e73d, 1f11080) each add one unrelated docs file.
- The work order's "resume ip-man once" step never fired, because jackie-chan raised no concern about R1–R3 ("Nothing here should hold the pass"). His two backlog observations never reached ip-man, though. They go with bruce-lee's (item 4).
- Nothing has been pushed from this tree: `## internal...origin/internal [ahead 17]`, and origin/internal is at eae2b0c.

Done-when status:
- **(1) holds:** the ruling is saved with a SHA-256 on record, and the review was filed before ronda-rousey started and before her commit.
- **(2) and (3) hold for scope.** Both test runs were measured by the crew and shown raw. My own re-runs are delegated (Next 1).
- **(4) holds as R1–R3 are ruled, but not as it is worded.** See item 4.
- **(5)** is this checkpoint. **(6) holds.**

## 2. bruce-lee's three judgment calls, checked against §3

Whether code fits a design is my agreement, from the same vendor as the crew (Anthropic, Claude Opus 5.5), not independent proof. ip-man owns the design.

1. **He checks for a collided thread before resolving its parent at the attachment site. This matches §3; ip-man needs to do nothing.**
   - R2's reason is that a collided thread's fields are a newest-wins merge of two unrelated posts. Its merged `parent:` is exactly the guess R2 refuses to act on.
   - Resolving it first would raise `parent_not_found` or `parent_malformed` about a merged value, which Done-when (4) says the flags never do.
   - The node site already works this way, and R2 rejects treating nodes and attachments differently. So "wherever the projector would otherwise have placed it" means the site that does the placing, not "only if its parent resolves".

2. **An unscoped item can no longer be part of a `cycle`. This follows R3's operative words, but ip-man should confirm it in one line.**
   - R3 says the parent is "never followed for placement", and its list of the flags an unscoped item keeps leaves out `cycle`. But it also says the flags are "exactly today's", and today this case does raise `cycle`. The text supports both readings.
   - The reading that holds together: R3 keeps the flags computed from the `parent:` value itself (`nesting_violation`, `parent_*`) and drops the flags computed from the edge it removes.
   - That group is wider than bruce-lee's example (from my reading of projector.py :363–364 and :426). An unscoped item under a CLOSED parent no longer raises `open_child_under_closed_parent`, is no longer counted by `closed_parent_with_open_children`, and can't raise `project_restated_conflict`.
   - Nothing disappears silently. In bruce-lee's example both items keep `nesting_violation`, and each flag names the other item.
   - The Feature that now sits inside intake under the unscoped ask is the same pattern jackie-chan already reviewed and accepted as deliberate.
   - The alternative I'd reject is keeping a second, unplaced set of edges just to detect cycles. It is more code, it reports the same filing error twice, and R3 never asks for it. No test covers any of these cases.

3. **`parent_malformed` fires only at the two sites that place items. This matches §3; ip-man needs to do nothing.**
   - R1 ties the check to the value read where items are placed ("one value at all three read sites").
   - A collided thread's parent is never read (R2), and flagging it would describe a merge. An item with an invalid level is never placed, so its parent is never read either. `parent_not_found` behaves the same way today.
   - The cost: an item with both a bad `level:` and a bad `parent:` shows one flag until the level is fixed, and then the second appears. It stays visible.

## 3. The wording error: I agree with bruce-lee

- The code is `thread_exists=parent in threads` (:349), left unchanged as R1's "Unchanged" list tells it to be. A bare id that names no thread gets `false`, which is accurate.
- Ruling line 92 says two things that can't both be true: that the field is "unchanged" (the instruction bruce-lee followed) and that it is "always true". The second doesn't follow, because a well-formed id doesn't have to name a thread that exists.
- What R1 really guarantees is F1's fix: `thread_exists` can no longer be false for a thread that does exist.
- One correction to bruce-lee's report: test_flags test_2 (lines 93–100) checks only the flag and `parent`, not `thread_exists`. So no test covers the `false` case; only R1c covers `true`.

## 4. The backlog observation: I agree, and it goes further

- From reading :325 and :329: `invalid_level` and `level_on_non_request` report `t["level"]`, which G3 merges across both posts' events.
- My addition, also from reading: a collided TS thread with an invalid `level:` never gets `thread_collided` at all. The node site stops at `invalid_level` (:329) before its collision check (:332), and the attachment site skips any TS thread that carries `level:`.
- This also shows Done-when (4) claims more than R2 and R3 deliver:
  - "never describe a merge of two posts" is not true for those two flags;
  - "an ask can no longer fall out of intake" is not true for a collided unscoped ask, which R2 shows only as `thread_collided`.
- The code matches §3; the wording of the criterion is ip-man's to fix. I recommend he narrows the wording now and puts the extension into §6. Extending R2 now would mean a new code change and test for a case with no known instance: his §2 search found no `level:` line on the board.

## 5. Who corrects the ruling: ip-man, in a short erratum saved beside it. Nobody should edit the ruling file itself

Why:
- **It's his design text.** I can propose changes but never make them. If the session wrote the fix, it would be putting words in his mouth. bruce-lee's "always truthful" is a guess at what ip-man meant; it's very likely right, but only ip-man can confirm it.
- **The file is pinned to a hash.** Line 15 records sha256=0839a66a…. Editing the file in place would make that hash and its "extracted verbatim" header false.
- **The work order already sets this pattern:** "the session resumes ip-man once. That answer is saved beside this ruling."

What the erratum should cover (I describe it; he writes it):
- **(a)** Replace line 92's "always true" with what R1 actually guarantees, and say whether a test should cover the `false` case (backlog).
- **(b)** Confirm or overrule the edge-flag reading in item 2, and record jackie-chan's "unscoped item as parent" as a deliberate non-gap.
- **(c)** Either narrow Done-when (4)'s wording to what R2 and R3 rule, or extend R2 (item 4). I recommend narrowing.
- **(d)** Add to §6: jackie-chan's `_claimed_by` observation, and bruce-lee's merged-level observation with my addition from item 4.

The cheaper option is to leave all four for ip-man's post-trial amendment. Nothing is waiting on them, but "always true" would then stay in force for the whole 30-day trial and invite the false alarm bruce-lee predicted. I recommend the erratum now.

## Not verified

- **Both test runs.** The tree is shared, so I ran no crew code; the runs are delegated (Next 1). Until ronda-rousey re-runs it, the passing run is bruce-lee's own.
- **The SHA-256 lines on the four filed documents.** I didn't recompute them. They were extracted by hand because save_verbatim.py can't read a SubagentHandback field, and each header says so.
- **jackie-chan's and bruce-lee's scratch-script results.** Neither showed any output.
- **The GitHub remote.** I have no network access, so I read only the local origin/internal ref.
- **Sensei's words.** No `SENSEI (verbatim):` section was passed. Nothing here depends on his words. The approval the work order cites (BB-20260925-venom-001) is reported by ip-man, not seen by me.
- **My earlier ESCALATE.** It wasn't passed to me. I checked against the ruling's own restatement of the sequence and assumed it is accurate.

```
CHECKPOINT — tracker Track 2 fix pass (R1–R3) / "jackie-chan reviews it in one pass before ronda-rousey starts" / jackie-chan
On task:     yes — answers all four questions; drift: the Document line says "He shows the command and its output for any run, or labels the point 'by reading'"; he labelled runs "(by execution)" and showed no output
Design:      conforms (a review of the design; no deviation)
Doctrine:    conforms — Document · Discuss · Decide: ruling filed (871dec9) before his review; review filed (1b62f72) before ronda-rousey started
Claims:      N=21, report order: 1 suite 61 passed at start and end; 2 tree clean, zero commits, ahead 9→10; 3 F1 reproduced; 4 R1's test rejects annotated and event-id values, accepts bare ids of any prefix; 5 a malformed value never reaches thread_exists; 6 F2 reproduced; 7 collided SEEK today: no flag, silent attachment, thread_collided only in the node loop; 8 F3 reproduced; 9 U1's nesting_violation detail survives R3; 10 §5 rows red/pass as predicted; 11 _thread_ids collapses three shapes to one id; 12 a bare non-TS parent stays parent_not_found; 13 nothing he meant is lost; 14 the equality check is load-bearing; 15 second-id and path shapes rejected; 16 no integrity gap; 17 _claimed_by surfaces a collided id unflagged; 18 a Feature naming an unscoped ask nests inside intake, flagged; 19 projector.py never checks project:'s slug rule; 20 a copied "# new" note gives invalid_level / parent_malformed; 21 v2 §0's row names only level:, A3 sets four fields
             — 1–4, 6–12, 14, 15, 17, 18, 20 reported-by jackie-chan (no command or output shown); 19, 21 reported-by jackie-chan (by reading); 5, 13, 16 judgement. The observed results his verdict rests on (3, 6, 7, 8, 10) were measured afterwards by ronda-rousey's red run (raw output) — supported; the rest are flags, none load-bearing. 2 fits the log (871dec9 is the 9th commit ahead; 4d091c3, the 10th, landed 02:48:24 during his review)
Assumptions: the "resume ip-man once" branch was not triggered — the session's inference — checked (his §4: "Nothing here should hold the pass"; both items framed as backlog). His two observations never reached ip-man → ip-man (erratum d)
Blocks:      none
Verified:    one clock read for all three blocks, applied to each report's own N. N=21; k=13 from date +%s → 1790411376 (mod 21 = 12). 13 is a judgement; 14, 15, 17 are runs I cannot repeat on a shared tree, 16 a judgement, 18 mostly a run; next checkable is 19 — MATCH by reading: projector.py's only "slug"/"a-z" hits are the filename slug (:206, :275) and the PROJECT label (:507); roots bucket by the raw value, projects.setdefault(node["project"], []). d1fd2b7's diff touches no project: handling, so this holds at the commit he read. Load-bearing 10 — measured since by ronda-rousey's fresh-clone red run; my own re-run DELEGATED → ronda-rousey (Next 1)
Verdict:     PROCEED (flags: evidence-form drift → jackie-chan, for his next brief: paste each run's command and raw output, which would have made 3, 6, 7, 8, 10 measured on arrival; two unrouted backlog observations → ip-man)
Pace:        converging
Next:        none for jackie-chan on this pass
```

```
CHECKPOINT — tracker Track 2 fix pass (R1–R3) / "(1) ronda-rousey, first, on internal, before any code" / ronda-rousey
On task:     yes — one new test file, six tests, one per §5 row, no existing test edited; red run shows the summary line, FAILED lines and exit code, as the line asks
Design:      conforms — read at e40c928, each test asserts its §5 row (R1a: parent_malformed with raw parent and ids_found [F], no parent_not_found, not F's child, in no_project, parent_not_feature; R1b; R1c guard with thread_exists true; R2a: all three buckets empty; R2b; R3: intake {U1, U2}, nesting_violation None/"epic")
Doctrine:    conforms — tests first: committed 03:05:25, before bruce-lee started 03:08:33; staged her own path only
Claims:      N=21, report order: 1 read both docs directly; 2 one new file, six tests, no existing test touched; 3–8 what R1a, R1b, R1c, R2a, R2b and R3 each assert; 9 each test prints flags and placement before asserting; 10 asserts only what each row states; 11 traced all six, every red an AssertionError; 12 status showed only her file, staged only it; 13 the commit touched one file, 265 insertions; 14 ahead 13, not pushed; 15 commit e40c928ef64f…; 16 fresh-clone red run: 5 failed, 62 passed, exit=1; 17 the five FAILED lines, no collection error; 18 per-test diagnostics; 19 R1c passed, 67 in all; 20 the working-copy re-run matched; 21 projector.py untouched
             — 16, 17, 19 measured (command and raw output shown); 13, 15, 21 measured by me (git); 2–10 reported-by ronda-rousey, agree with the file by my reading; 1, 11, 12, 14, 18, 20 reported-by ronda-rousey. All supported; 14 fits the log (e40c928 is the 13th commit ahead)
Assumptions: each of the five fails for its ruled reason, not by accident — reported-by ronda-rousey (18) — checked by reading the pre-fix code: parent_malformed did not exist before d1fd2b7 (R1a, R1b), the merged node was placed (R2a), the attachment loop had no collision check (R2b), an unscoped item with a resolving parent was nested (R3). Agreement, not measurement
Blocks:      none
Verified:    N=21; k=13 (same s; mod 21 = 12). Claim 13 — MATCH: git show --stat e40c928 → "tracker/tests/test_ruling_r1_r3.py | 265 +++…" / "1 file changed, 265 insertions(+)". Load-bearing 16 — DELEGATED → ronda-rousey (Next 1): shared tree, and I may not clone
Verdict:     PROCEED
Pace:        converging
Next:        Next 1 (the delegated re-run)
```

```
CHECKPOINT — tracker Track 2 fix pass (R1–R3) / "(2) bruce-lee, after (1): one pass to green, in tracker\projector.py only." / bruce-lee
On task:     yes — R1–R3, FLAGS, the thread_collided comment, the docstring and the trimmed "choices" list all as ordered; nothing extra (the _claimed_by signature change is R1's "one value at all three read sites")
Design:      conforms to §3 as written (full diff and file at d1fd2b7 read against §3). Flags → ip-man: (a) ruling line 92 wording; (b) R3's edge-flag group, judgment call 2 — confirm; (c) Done-when (4) claims more than R2/R3 as ruled; (d) §6 additions
Doctrine:    conforms — built only after ronda-rousey's red commit; staged his own path only; noreply author
Claims:      N=32, report order: 1 commit d1fd2b7…, parent 737328f; 2 only tracker/projector.py, 62 added / 18 removed; 3 status showed only his file, HEAD unchanged since dispatch; 4 staged his path only; 5 noreply author; 6 ahead 15, not pushed; 7 fresh-clone green run: 67 passed, exit=0; 8 verbose run: six new tests and test_3 pass; 9 working copy red before his change; 10 working copy green after; 11 _is_bare_thread_id as ruled, first in resolve(); 12 parent_malformed detail, places nothing; 13 resolve order malformed → collided → not found; 14 both placing sites pass the G3 value through resolve(); 15 _claimed_by takes the accepted value; 16 parse_tracker_header untouched; 17 node site: continue after thread_collided; 18 attachment site: collision check before resolve(); 19 R3: unscoped still resolved for flags, never entered in resolved; 20 FLAGS gains parent_malformed at the end, comment covers attachments; 21 docstring states R1–R3, list trimmed to five; 22–24 judgment calls 1–3; 25 a bare id naming no thread still gives thread_exists: false; 26 invalid_level / level_on_non_request on a collided thread report the merged level; 27 accepts bare ids of each prefix; 28 rejects nine malformed shapes; 29 four edge boards behave as ruled; 30 CLI renders parent_malformed, rc 0; 31 CRLF warning harmless; 32 nothing else imports _claimed_by, resolve or FLAGS
             — 7 measured (raw output); 1, 2, 5 measured by me (git); 11–21, 25, 26 reported-by bruce-lee, agree with the diff by my reading; 3, 4, 6, 8–10, 27–32 reported-by bruce-lee (no output shown; none load-bearing); 22–24 judgement (report item 2). All supported
Assumptions: 67 = the 61 + 6, none skipped — checked (the raw summary reads "67 passed", nothing skipped). The erratum changes no code — assumed; if ip-man overrules judgment call 2, that is a new work-order line (tests first), not a REWORK of this one. No commit touches tracker/ before a push → whoever pushes (pre-push range check)
Blocks:      none
Verified:    N=32; k=17 (same s; mod 32 = 16). Claim 17 — MATCH: the node-site hunk shows flag("thread_collided", tid, openings=t["openings"]) then "+            continue" before nodes[tid] = {…} (:332–333). Scope 1, 2, 5 — MATCH: "tracker/projector.py | 80 …" / "1 file changed, 62 insertions(+), 18 deletions(-)", parent 737328f1f7…, author 18243588+terrence-adams@users.noreply.github.com. Load-bearing 7 — DELEGATED → ronda-rousey (Next 1); until then the green run is the implementer's own
Verdict:     PROCEED (flags → ip-man: a–d above)
Pace:        converging — each step brought new, distinct findings; nothing is circling. Nearest shippable deliverable: d1fd2b7 as it stands, ready for Sensei's yes or no once Next 1 matches. Recommend no more code in this pass; the rest is backlog for real cases to drive
Next:        1. ronda-rousey (DELEGATED re-run): one fresh clone in her scratch directory, using the ruling's own clone and run commands, at e40c928 and then at d1fd2b7; paste each summary line and exit code raw. Expected: 5 failed, 62 passed, exit=1; then 67 passed, exit=0. It holds nothing; a MISMATCH comes back as a correction and parks the line it hits.
             2. ip-man (resume once, same agent; runs alongside 1): one erratum covering a–d, saved beside the ruling the way the work order saves his answers. His answer stands for this pass.
```

No GATEWAY was run, because the work order says none. If this pass is shown to Sensei or pushed, a GATEWAY comes first. Any push also needs the pre-push range check, because `internal` carries 17 unpushed commits from several sessions.

**When this verdict stops being right:**
- If Next 1 doesn't match, the line it contradicts is parked as a REWORK.
- If ip-man reads R3 as keeping the edge flags, d1fd2b7 departs from the ruling in those untested edge cases. That becomes a new work-order line, tests first.
- If any commit touches `tracker/` after d1fd2b7 and before a push, the scope checks here no longer describe what gets pushed.

**Files**
- C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md (line 92: the sentence; lines 197–205: §6)
- C:\Repo\townsquare\docs\jackie-chan-review-of-ruling-20260926.md
- C:\Repo\townsquare\docs\ronda-r1-r3-fixtures-20260926.md
- C:\Repo\townsquare\docs\bruce-lee-r1-r3-implementation-20260926.md
- C:\Repo\townsquare\tracker\projector.py (at d1fd2b7; lines cited from the working tree, whose tracked files matched HEAD 37229ba)
- C:\Repo\townsquare\tracker\tests\test_ruling_r1_r3.py (at e40c928)
- C:\Repo\townsquare\tracker\tests\test_flags.py (test_2, lines 93–100)