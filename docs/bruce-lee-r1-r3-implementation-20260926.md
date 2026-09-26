# Bruce-lee's R1-R3 implementation report

Delivered 2026-09-26, commit d1fd2b7. All 67 tests pass in a fresh clone, exit 0.
Implements R1 (a new _is_bare_thread_id check feeding one validated value to all three
read sites), R2 (collided threads excluded at both the node and attachment sites), R3
(unscoped items bucketed by level, never entered into resolved placement). Flags a
genuine wording error in the ruling itself (R1's claim that thread_exists 'is always
true' after the fix is not accurate -- a bare id naming no thread at all still correctly
reports false; the code is right, the ruling's prose should say 'always truthful').
Surfaces three judgment calls for Helio to check against the ruling's own reasoning, and
one backlog observation in the same class as jackie-chan's _claimed_by finding. Extracted
verbatim from the subagent transcript, not retyped; save_verbatim.py's CLI reads only an
end_turn text block, and this agent's report was instead delivered as a SubagentHandback
tool_use input field, so this was pulled by hand from that same field.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=4cf29e3136d87310a63aacd6add90069c873114a659abde3e8de2f328cc090ab source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-ac9048be59dedf81e.jsonl:148 message=msg_011CfRihQ8emP4boFTBKTFft -->
bruce-lee report: tracker R1-R3 fix pass. All 67 tests pass in a fresh clone at my commit, exit code 0.

"R1-R3" are ip-man's rulings in docs/ip-man-projector-ruling-20260926.md. "F1-F3" are jackie-chan's projector findings 1-3, which those rulings answer.

COMMIT
- d1fd2b7f956881272c097dc679397ab2e5068cfa on `internal`. Its parent is 737328f.
- It changes only tracker/projector.py (62 lines added, 18 removed). No test file was edited.
- Before committing I ran `git status`: only my file was modified, and HEAD was unchanged since dispatch.
- I staged with `git add tracker/projector.py` only. No `-A` and no `-a`.
- Author is 18243588+terrence-adams@users.noreply.github.com.
- Not pushed. `internal` is now ahead of origin/internal by 15.

GREEN RUN (fresh clone, Git Bash, my scratch directory, no elevation, raw output)
```
git clone -q C:/Repo/townsquare ts-d1fd2b7f956881272c097dc679397ab2e5068cfa
git -C ts-d1fd2b7f... checkout -q d1fd2b7f956881272c097dc679397ab2e5068cfa
clone HEAD: d1fd2b7f956881272c097dc679397ab2e5068cfa
parent:     737328f1f78de88684f7561290b595fa2be56460
status:     []
python -m pytest tracker/tests -q; echo "exit=$?"
...................................................................      [100%]
67 passed in 1.35s
exit=0
```
- In the same clone, a verbose run shows all six tests in test_ruling_r1_r3.py PASSED, plus test_flags.py test_3 (the test that guards R2's collided-before-not-found order). Result: 7 passed, exit 0.
- Before my change, the working copy reproduced ronda's red run exactly: 5 failed, 62 passed, exit 1.
- After my change, the working copy gave 67 passed, exit 0.

WHAT I CHANGED (tracker/projector.py)
- **R1:** new `_is_bare_thread_id(value)`. It returns True only when `parse_filename(value + ".000-OPEN.txt")["thread"] == value`, and False on FilenameError. This check is the first thing `resolve()` now does:
  - If it fails, the thread is flagged `parent_malformed` with detail `{parent: <raw value>, ids_found: [ids from _thread_ids]}`, and nothing is placed.
  - The order inside `resolve()` is now: malformed, then collided, then not found.
  - Both placing read sites (placement and attachments) already pass the value that G3 (D19's newest-event-carrying-the-field-wins rule) selects through `resolve()`.
  - `_claimed_by(t, parent)` now receives the value `resolve()` accepted instead of reading `t["parent"]` itself. So all three read sites use one validated value by construction.
  - `parse_tracker_header` is untouched.
- **R2, node site:** a `continue` after the `thread_collided` flag, so a collided item is never built as a node.
- **R2, attachment site:** the collision check comes before `resolve()`. It flags `thread_collided` and skips.
- **R3:** an unscoped item still goes through `resolve()`, so its flags and `actual_level` are exactly today's. It is never entered in `resolved`, so it is always a root and is bucketed into intake by its level.
- **FLAGS:** `parent_malformed` is appended at the end, so v1's ten flags stay together and in order. `thread_collided`'s comment now covers attachments.
- **Module docstring:** it states R1-R3 as rulings and cites the ruling file. The "choices the design does not pin" list now keeps only rollup scope, what counts as an "open" child, readiness while not terminal, `no_project`, and Archive depth. I removed the collided-parent item (R2 settles it) and the intake half of the old bucket item (R3 settles it). I also dropped the old "Nothing is dropped silently" line. After R2, a collided thread appears only in the flags, so the line would over-claim again, which is the point jackie-chan made about F3.

JUDGMENT CALLS FOR HELIO TO READ AGAINST RULING §3 (each checked by running a scratch script, not in the repo)
1. **Collided before resolve at the attachment site.** A collided SEEK whose merged `parent:` names nothing gets only `thread_collided`, not `parent_not_found`. I chose this because of Done-when (4) ("never describe a merge of two posts"), and because the node site behaves the same way: a collided item's parent is never resolved there either.
   - The other reading of "wherever the projector would otherwise have placed it" would flag only after the parent resolves. That would raise a `parent_*` flag on a value merged from two posts.
2. **R3 edge: an unscoped item can no longer be part of a cycle.** Take U (unscoped, parent X) and X (feature, parent U).
   - Before: both were flagged `cycle` and cut loose.
   - Now: there is no `cycle` flag, X is nested under U in intake, and both keep `nesting_violation`.
   - Why: R3 says U's parent is "never followed for placement", and R3's own list of U's flags does not include `cycle`.
   - No test pins this. It changes behaviour only in this edge case, so it is ip-man's call if he reads it differently.
3. **`parent_malformed` fires only at the two placing read sites**, the same places `parent_not_found` fires today. So a TS item with an invalid `level:`, or a collided thread, that also has a malformed `parent:` gets no `parent_malformed`. Neither gets `parent_not_found` today either.

A WORDING ERROR IN THE RULING (code left as the ruling directs)
- R1's "Unchanged" list says that after R1, `thread_exists` "is always true". That is not what happens, and it should not be.
- A bare id that names no thread at all still gets `thread_exists: false` (test_flags test_2's shape, TS-20260101-venom-999), and that value is accurate.
- I kept the detail unchanged, as the same list directs. The sentence probably means "always truthful". It is worth correcting in the ruling so the checkpoint doesn't read it as a deviation.

BACKLOG OBSERVATION (not fixed: outside R2's text, and not my call)
- `invalid_level` and `level_on_non_request` on a collided thread still report the level taken from the merge of two posts. This is the same class as jackie-chan's `_claimed_by` observation. It belongs in ip-man's §6 list if he wants Done-when (4) to hold beyond placement.

OTHER CHECKS
- `_is_bare_thread_id` accepts bare ids with each prefix (TS, BB, SEEK, OFFER, WANT).
- It rejects each shape named in the ruling or in jackie's review: an annotation, an event id, jackie's `.0-OPEN__foo` shape, a second id, a POSIX path, a Windows path, a lowercase prefix, a trailing dot, and a copied `# new` template note.
- These all behave as ruled: an epic with a malformed parent, an unscoped item with a malformed parent, a malformed newest value with a clean older one (it does not fall back), and a collided TS sub-request.
- The CLI renders `parent_malformed` and returns rc 0.
- The LF/CRLF warning git printed changes nothing: HEAD's blob and the committed blob both have 0 CR bytes, and the diff shows only my lines.
- No other code imports `_claimed_by`, `resolve` or `FLAGS`. The signature change is private.

NEXT STEPS
1. helio-gracie's CHECKPOINT. It covers, in order: jackie-chan's review (1b62f72), ronda-rousey's commit (e40c928), and this pass (d1fd2b7). He should also rule on judgment calls 1-3 above.
2. Optionally, ip-man corrects the "thread_exists is always true" wording and adds the backlog observation to §6.
Nothing is permission-gated. Nothing gets pushed without Sensei's go-ahead. If anyone pushes, run the pre-push range check first: `git log --oneline origin/internal..<sha>`. It will list 15 commits from several sessions.

Commands for helio-gracie (Git Bash on Venom, no elevation):
- Scope: `git -C C:/Repo/townsquare show --stat d1fd2b7`
- Diff to read against §3: `git -C C:/Repo/townsquare show d1fd2b7 -- tracker/projector.py`
- Re-run (or delegate it to ronda-rousey): `git clone C:/Repo/townsquare ts-d1fd2b7 && git -C ts-d1fd2b7 checkout d1fd2b7 && cd ts-d1fd2b7 && python -m pytest tracker/tests -q; echo "exit=$?"`

FILES
- C:\Repo\townsquare\tracker\projector.py (the only file changed, commit d1fd2b7)
- C:\Repo\townsquare\tracker\tests\test_ruling_r1_r3.py (unchanged, now green)
- C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md
- C:\Repo\townsquare\docs\jackie-chan-review-of-ruling-20260926.md
- C:\Repo\townsquare\docs\ronda-r1-r3-fixtures-20260926.md
- Fresh clone (disposable): C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\ts-d1fd2b7f956881272c097dc679397ab2e5068cfa
- Edge-case script (disposable): C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\bruce_r1r3_edges.py