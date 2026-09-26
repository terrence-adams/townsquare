# Ronda-rousey's delegated re-run: R1-R3 verified independently

Delivered 2026-09-26, closing helio-gracie's delegated 'Next 1'. Independent fresh clone,
checked out at e40c928 then d1fd2b7: 5 failed/62 passed/exit=1, then 67 passed/exit=0 --
both an exact match to Helio's stated expectations. Verification only, no new tests, no
code changes. Pulled byte-for-byte from the subagent transcript's SubagentHandback field,
not retyped -- save_verbatim.py's CLI reads only an end_turn text block, so it cannot
extract this delivery shape; the hash below was computed by hand, not printed by that
tool.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=e864f6a661174529858a17780177db2e45c280be8db66bace4f12a8f379045a7 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a9769e20c3d22a5a3.jsonl:65 message=msg_011CfRko9NXspU1njCaEyheU -->
Next 1 (delegated re-run) complete. Both results match the stated expectations exactly.

**Setup.** Read `C:\Repo\townsquare\docs\helio-checkpoint-r1-r3-20260926.md` for the delegation, and `C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md` for the exact clone-and-run commands (bottom of that file, "Commands" section). Made one fresh clone in my scratch directory, then checked it out at each commit in turn, per the brief:

```
cd "C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad"
git clone C:/Repo/townsquare ts-verify-next1
```

**Run 1 — e40c928** (`git checkout e40c928` → HEAD at `e40c928 tests: add R1a, R1b, R1c(guard), R2a, R2b, R3 fixtures for ip-man's projector ruling`)

Command: `python -m pytest tracker/tests -q; echo "exit=$?"`

Raw summary line and exit code:
```
5 failed, 62 passed in 1.54s
exit=1
```
Failed tests (raw): `test_r1a_annotated_parent_is_flagged_malformed_and_placed_nowhere`, `test_r1b_event_id_parent_is_flagged_malformed_not_parent_not_found`, `test_r2a_collided_thread_is_excluded_from_placement_entirely`, `test_r2b_collided_seek_attachment_is_excluded_not_silently_attached`, `test_r3_unscoped_item_with_a_resolving_parent_still_goes_to_intake_never_nested` — all in `tracker/tests/test_ruling_r1_r3.py::RulingR1R3Tests`.

Expected: 5 failed/62 passed/exit=1. **MATCH.**

**Run 2 — d1fd2b7** (`git checkout d1fd2b7` → HEAD at `d1fd2b7 tracker: R1-R3 fix pass per ip-man's projector ruling`)

Command: `python -m pytest tracker/tests -q; echo "exit=$?"`

Raw summary line and exit code:
```
67 passed in 1.42s
exit=0
```
Expected: 67 passed/exit=0. **MATCH.**

**Scope check.** After both runs, `C:\Repo\townsquare` (the shared tree) is unaffected: `git status` there still shows "On branch internal ... nothing to commit, working tree clean", HEAD unchanged at `ce6e9a1` (Helio's checkpoint-filing commit). All clone/checkout/pytest activity happened only inside the isolated fresh clone at `C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\ts-verify-next1`. I ran no `git push` anywhere.

No new tests written, no code changed, nothing fixed — this was verification only, as instructed.

**Files**
- C:\Repo\townsquare\docs\helio-checkpoint-r1-r3-20260926.md (the delegation, "Not verified" section and Next 1)
- C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md (Commands section, bottom of file — source of the exact clone/run commands used)
- C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\ts-verify-next1 (this run's fresh clone, left in place as evidence; not the same directory as the prior `ts-e40c928ef64f05b7f0c24461c4d96205346348ad` / `ts-d1fd2b7f956881272c097dc679397ab2e5068cfa` clones already present in scratch from the implementer's/my own earlier commit-time runs)