# Ronda-rousey's R1-R3 fixtures for the projector ruling

Delivered 2026-09-26, commit e40c928. One new file, tracker/tests/test_ruling_r1_r3.py,
six tests (one per section-5 fixture row). Red run in a fresh clone, cross-checked in
the working copy: 5 failed, 62 passed, matching the ruling's exact prediction --
R1c (the boundary guard) passes as expected; R1a, R1b, R2a, R2b and R3 fail for the
exact reasons the ruling predicted, with full diagnostic output. Nothing in
tracker/projector.py touched -- that is bruce-lee's pass next. Extracted verbatim from
the subagent transcript, not retyped; save_verbatim.py's CLI reads only an end_turn text
block, and this agent's report was instead delivered as a SubagentHandback tool_use
input field, so this was pulled by hand from that same field.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=e06be36da10c9503a23bc33364a66b0f0d76e19c72ed074fbc83e2a83cb14e2b source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a9f14bd2efd3014de.jsonl:119 message=msg_011CfRhv5p4oZWcWTptjdeKd -->
Read both docs directly (not summaries): `C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md` (R1-R3 rulings + §5 fixture table) and `C:\Repo\townsquare\docs\jackie-chan-review-of-ruling-20260926.md` (no blockers, proceed to fixtures). Built the fixtures from §5's table cells directly, not from Section 3's prose.

WHAT I ADDED

One new file, no existing test file touched:
`C:\Repo\townsquare\tracker\tests\test_ruling_r1_r3.py` — one `unittest.TestCase` (`RulingR1R3Tests`), six tests, one per §5 row, using ids I chose (900s-950s, isolated per-test via `TemporaryDirectory`, so no collision risk with anything else landing in the shared tree):

- `test_r1a_annotated_parent_is_flagged_malformed_and_placed_nowhere` — F=TS-...-900 (feature/townsquare), S=TS-...-901 with `parent: TS-...-900 (its Feature)`. Asserts: one `parent_malformed` on S (`parent`=raw value, `ids_found`=[F]), zero `parent_not_found`, S not among F's children, S in `no_project`, S's `story_not_ready` includes `parent_not_feature`.
- `test_r1b_event_id_parent_is_flagged_malformed_not_parent_not_found` — S=TS-...-910 (story/townsquare), K=SEEK-...-911 with `parent: TS-...-910.001`. Asserts: one `parent_malformed` on K (`ids_found`=[S]), zero `parent_not_found`, K not in S's attachments.
- `test_r1c_guard_bare_parent_naming_a_non_tracker_thread_stays_parent_not_found` — B=BB-...-920 (no tracker fields), S=TS-...-921 with bare `parent: <B>`. Asserts: one `parent_not_found` on S with `thread_exists: true`, zero `parent_malformed`. This is the only row expected to pass both before and after the fix.
- `test_r2a_collided_thread_is_excluded_from_placement_entirely` — TS-...-930 with two `.000-OPEN` opens (by-venom epic/townsquare, by-forge feature/kollective), jackie's F2 shape. Asserts: one `thread_collided` naming both openings, and `projects`/`no_project`/`intake` all completely empty (the whole board here is just this one id, so "appears nowhere at any depth" reduces to all three buckets being empty — chosen deliberately for a maximally diagnostic failure diff over `assertNotIn`).
- `test_r2b_collided_seek_attachment_is_excluded_not_silently_attached` — S=TS-...-940 (story/townsquare), SEEK-...-941 with two `.000-OPEN` opens each carrying `parent: <S>`. Asserts: one `thread_collided` on the SEEK id, S's attachments empty.
- `test_r3_unscoped_item_with_a_resolving_parent_still_goes_to_intake_never_nested` — E=TS-...-950 (epic/townsquare), U1=TS-...-951 (`level: unscoped`, `parent: <E>`), U2=TS-...-952 (`level: unscoped`, no parent), jackie's F3 shape is U1. Asserts: intake holds exactly {U1, U2}, U1 not among E's children, one `nesting_violation` on U1 (`parent`=E, `expected_level`=None, `actual_level`="epic").

Every test prints the projector's full `flags` list plus the specific placement structure it's about to check (F's/E's children, no_project/intake ids, attachments, `projects` dict), unconditionally, before any assertion — pytest's default capture only surfaces that stdout for a test that fails, so it's silent on R1c and the existing 61, and is the raw measurement the ruling delegates for two of jackie-chan's earlier run-claims.

Scoping discipline: where a §5 row states fewer facts than the general R1/R2 ruling text implies (e.g. R1b's row doesn't repeat the `detail["parent"]` raw-value check R1a's row states explicitly), I asserted only what that row literally states, not the fuller blanket rule — staying inside "exactly as §5 specifies" rather than inventing additional coverage.

VERIFIED BEFORE WRITING ASSERTIONS

Manually traced all six fixtures against `tracker/projector.py`'s actual current logic (line-by-line, cited in my working notes) before committing, to be sure every expected red failure is a clean `AssertionError` and not an exception — then confirmed it by running. This also cross-checks two of jackie-chan's own by-execution claims (annotated-parent → `parent_not_found`/`thread_exists: false`; the SEEK-collision shape → zero flags + silent attachment).

COMMIT

`git status --short --branch` before staging showed only my new file untracked; staged only it (`git add tracker/tests/test_ruling_r1_r3.py`, never `-A`/`-a`); committed on `internal`. `git show --stat HEAD` confirms the commit touched exactly one file (265 insertions). Not pushed — `internal` is ahead of `origin/internal` by 13 (12 pre-existing + this one).

Commit: `e40c928ef64f05b7f0c24461c4d96205346348ad`

RED RUN — FRESH CLONE, RAW OUTPUT

Commands (Git Bash, this agent's own scratch dir, no elevation):
```
cd /c/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad
git clone C:/Repo/townsquare ts-e40c928ef64f05b7f0c24461c4d96205346348ad
git -C ts-e40c928ef64f05b7f0c24461c4d96205346348ad checkout e40c928ef64f05b7f0c24461c4d96205346348ad
cd ts-e40c928ef64f05b7f0c24461c4d96205346348ad
python -m pytest tracker/tests -q; echo "exit=$?"
```

Raw result:
```
...........................................................FF.FFF..      [100%]
5 failed, 62 passed in 1.49s
exit=1
```

FAILED (all `AssertionError`, no exceptions, no collection error):
```
FAILED tracker/tests/test_ruling_r1_r3.py::RulingR1R3Tests::test_r1a_annotated_parent_is_flagged_malformed_and_placed_nowhere
FAILED tracker/tests/test_ruling_r1_r3.py::RulingR1R3Tests::test_r1b_event_id_parent_is_flagged_malformed_not_parent_not_found
FAILED tracker/tests/test_ruling_r1_r3.py::RulingR1R3Tests::test_r2a_collided_thread_is_excluded_from_placement_entirely
FAILED tracker/tests/test_ruling_r1_r3.py::RulingR1R3Tests::test_r2b_collided_seek_attachment_is_excluded_not_silently_attached
FAILED tracker/tests/test_ruling_r1_r3.py::RulingR1R3Tests::test_r3_unscoped_item_with_a_resolving_parent_still_goes_to_intake_never_nested
```

Which/why, from the captured diagnostics:
- **R1a**: `parent_malformed` count is 0 (expected 1) — today's projector still emits `parent_not_found` (`thread_exists: false`) for the annotated value instead.
- **R1b**: same — `parent_malformed` count is 0 (expected 1); today's flag is `parent_not_found` on the SEEK.
- **R2a**: `thread_collided` itself already fires correctly today (that assertion passed) — the test fails on `result["projects"] != {}`: the collided id is still built as a merged node (`level: "epic"`, arbitrary sort-winner) and placed under `projects["townsquare"]`.
- **R2b**: `thread_collided` count is 0 (expected 1) — this shape raises no flag at all today; `S.attachments` also still silently contains `SEEK-20260101-venom-941`.
- **R3**: `intake` today holds only U2 (`['TS-20260101-venom-952']`); U1 is missing (nested under E instead, `E.children == ['TS-20260101-venom-951']`), reproducing F3 exactly.

R1c passed. Not in the FAILED list. Total 67 tests (61 pre-existing + 6 new): 62 passed, 5 failed, matching the ruling's exact prediction.

Also re-ran the full suite in the plain working copy immediately before committing (not the fresh clone) as a second, independent check: `5 failed, 62 passed in 1.43s` — same tests, same reasons, consistent with the fresh-clone run above.

NOT DONE (by design, per the work order)

`tracker/projector.py` was not touched. That is bruce-lee's pass next (R1-R3 implementation, FLAGS gains `parent_malformed`, `thread_collided`'s comment covers attachments, module docstring cites this ruling) — my commit only adds the failing fixtures that pass will need to turn green.

FILES

- `C:\Repo\townsquare\tracker\tests\test_ruling_r1_r3.py` (new, this commit)
- `C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md`
- `C:\Repo\townsquare\docs\jackie-chan-review-of-ruling-20260926.md`
- `C:\Repo\townsquare\tracker\projector.py` (read only)
- `C:\Repo\townsquare\tracker\tests\boardfixture.py`, `test_flags.py`, `test_nesting.py`, `test_header_parsing.py`, `test_seeking_claim_link.py`, `test_filename_token_reproduction.py`, `test_output_contract.py` (read for convention; unmodified)
- Fresh clone (scratch, disposable): `C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\ts-e40c928ef64f05b7f0c24461c4d96205346348ad`
