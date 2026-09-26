# Ronda-rousey's 4-case QA on the final P2 send command (Addendum 5)

Delivered 2026-09-26. Zero discrepancies. Cases (a) pass, (b) hash mismatch, and (d)
unfilled placeholders all reproduce exactly as ip-man's ruling specifies, against the
literal Addendum 5 text with curl replaced by a hashing stand-in, no network call made.
Case (c) legitimately stands in on the prior dispatch's result, reinforced by re-hashing
both source files unchanged. Confirms Git Bash's sha256sum correctly opens the C:/ path,
closing ip-man's own open question. Notes case (d) actually fails harder than the minimum
bar -- angle brackets are shell redirection metacharacters, so a literal placeholder paste
is a hard syntax error before anything runs, not merely refused input. Pulled byte-for-byte
from the subagent transcript's SubagentHandback field, not retyped -- save_verbatim.py's
CLI reads only an end_turn text block, so it cannot extract this delivery shape; the hash
below was computed by hand, not printed by that tool.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=e30c658eca1903d6dc3fc5b6b5e63461904279c318c6c23e1c737e07fb50f505 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a961bf7568c373611.jsonl:80 message=msg_011CfRuNS5UVFmxeJc1UJdou -->
Verification only, no code change, branch `internal` untouched throughout, nothing pushed. Ran ip-man's QA work order from `C:\Repo\townsquare\docs\ip-man-ruling-decision6-p2-filler-hash-20260926.md` (the "QA: ronda-rousey" block) against the exact Run 2 (P2 send) command text in `C:\Repo\townsquare\docs\session-v4-prep-20260926.md`, "Addendum 5" (lines 390-400).

## Prior-dispatch reconciliation (done first, per your instruction)

Found the prior dispatch: `C:\Repo\townsquare\docs\ronda-raw-reverify-filler-20260926.md`, filed as commit `a8d5edb`. It is exactly "Helio's Next 2" (`helio-recheck-2-decision6-20260926.md` lines 214-221: "dispatch ronda-rousey for #11 at 1ee6601 ... show the NNN=1 case and the chain with a harmless stand-in for curl, both raw"). That prior run:
- Confirmed the valid dummy run's 3 `OK:` lines and correct file writes (#11).
- Confirmed `NNN=1` prints `STOP: NNN must be 3 digits, got '1'`, exits 1, writes nothing, before/after directory listings byte-identical (#14).
- Confirmed the stand-in chain reaches the stand-in only on success and never on failure, both directions shown raw (#8).
- Explicitly noted at the time: "there is no hash-check clause preceding `python ...`" — i.e. it could not and did not test the clause this ruling adds, because the clause didn't exist yet.

I re-hashed both source files at current HEAD before relying on that prior run:
```
$ sha256sum "C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py" "C:/Repo/townsquare/docs/decision-6-p2-body-draft.json"
75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda *C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
96a760d088b49305668e25ff4cca9be9282cba29bd9616b9e89f0c907033c9c7 *C:/Repo/townsquare/docs/decision-6-p2-body-draft.json
EXIT=0
```
Both byte-identical to what the prior run tested. **Per ip-man's own note, that stands in for #8, #11 and #14 — I did not re-run case (c) (`NNN=1`) fresh.** This run covers (a), (b), (d) only, which is everything new (the hash-check clause didn't exist at the time of the prior run).

## Setup: current HEAD, branch, baseline

- Branch: `internal`. `git status`: clean (only ignored `__pycache__`/`.venv` dirs), 35 commits ahead of `origin/internal`, nothing pushed.
- HEAD `799f5c1` (after `f03c336`, "implement ip-man's filler-hash-check ruling (Addendum 5)") — Addendum 5's text is present in the working tree copy I read.
- Baseline listing, scratchpad `v4-prep`, before any test:
```
total 32
-rw-r--r-- 1 terre 197609 3659 Sep 26 03:19 projection-capture1.txt
-rw-r--r-- 1 terre 197609 3659 Sep 26 03:24 projection.py
-rw-r--r-- 1 terre 197609  953 Sep 26 03:19 projection.py
-rw-r--r-- 1 terre 197609 3659 Sep 26 03:24 projection-capture2.txt
```
(3 pre-existing files only — matches the prior dispatch's own restored baseline.)

Curl stand-in used for all three cases (a shell function defined immediately before each test, in the same invocation — the P2 send command's own text is otherwise pasted **unmodified** from Addendum 5):
```bash
curl() {
  local file=""
  for arg in "$@"; do
    case "$arg" in
      @*) file="${arg#@}" ;;
    esac
  done
  echo "STANDIN-CURL: invoked, $# args, NO NETWORK CALL MADE"
  if [ -n "$file" ]; then
    echo "STANDIN-CURL: hashing file curl would have read: $file"
    sha256sum "$file"
  else
    echo "STANDIN-CURL: no @file argument found among args"
  fi
}
```
No real `curl` binary ran in any case below; no network call was made to `192.168.2.3:8789` at any point.

## Case (a) — pass

Command (Addendum 5's Run 2, D/N filled with fresh dummy values `20261015`/`015`, curl shadowed as above):
```bash
D=20261015; N=015
FILLER=C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
echo "75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda  $FILLER" | sha256sum -c - \
  && python "$FILLER" "$D" "$N" \
  && curl -sS -X POST http://192.168.2.3:8789/register \
       -H 'Content-Type: application/json' \
       --data-binary "@C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/p2-body-${D}-venom-${N}.json" \
       -w '\nhttp_code=%{http_code}\n'
echo "CHAIN_EXIT=$?"
```
Raw output (complete, unedited):
```
C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py: OK
OK: filename            = BB-20261015-venom-015.000-OPEN__to-all__impact-informational__from-venom__claude-app-registered-on-its-behalf-offsite-writer-and-posting-card-on-trial.txt
OK: B.6 body written to = C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep\B6-20261015-venom-015-body.txt
OK: P2 body written to  = C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep\p2-body-20261015-venom-015.json
STANDIN-CURL: invoked, 10 args, NO NETWORK CALL MADE
STANDIN-CURL: hashing file curl would have read: C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/p2-body-20261015-venom-015.json
1d6e25aec771c23553baa5a534fb6f75bd1c2c8846e384cf5076999b232174ae *C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/p2-body-20261015-venom-015.json
CHAIN_EXIT=0
```
**MATCH**: `<path>: OK` ✓, filler's three `OK:` lines ✓, stand-in's hash ✓, exit 0 ✓. The 10-arg count matches the real curl invocation exactly (`-sS -X POST <url> -H '<ct>' --data-binary @<path> -w '<fmt>'`), confirming the command text reached the stand-in completely unmodified. Also answers the ruling's open question: **Git Bash's `sha256sum` does open the `C:/` path correctly** — no path-string change needed, (a) does not need a second run.

Directory listing after (a):
```
total 41
-rw-r--r-- 1 terre 197609 4673 Sep 26 05:35 B6-20261015-venom-015-body.txt
-rw-r--r-- 1 terre 197609  542 Sep 26 05:35 p2-body-20261015-venom-015.json
(plus the 3 baseline files, unchanged)
```

## Case (b) — mismatch (one hex digit flipped in the command's copy only, never in the file)

Command (hash's first character changed `7`→`8`; fresh D/N `20261016`/`016`):
```bash
D=20261016; N=016
FILLER=C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
echo "85e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda  $FILLER" | sha256sum -c - \
  && python "$FILLER" "$D" "$N" \
  && curl -sS -X POST http://192.168.2.3:8789/register \
       -H 'Content-Type: application/json' \
       --data-binary "@C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/p2-body-${D}-venom-${N}.json" \
       -w '\nhttp_code=%{http_code}\n'
echo "CHAIN_EXIT=$?"
```
Raw output (complete, unedited — this is everything that printed):
```
C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
CHAIN_EXIT=1
```
Follow-up checks:
```
$ ls -la ".../v4-prep"          # unchanged from post-(a) state, no 20261016-* files
$ ls ".../v4-prep" | grep -c '20261016'
0
$ sha256sum "C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py"
75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda *C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
```
**MATCH**: `FAILED` ✓, exit 1 ✓, no new file in `v4-prep` ✓, no `STANDIN-CURL` line anywhere (curl stand-in never ran) ✓, and the real on-disk file is confirmed untouched (still `75e17655...`) — the mismatch was entirely in the command's own copy of the hash, never in the file, as specified.

## Case (d) — command pasted with D and N left unfilled

Command (Addendum 5's Run 2 pasted with the literal placeholders `<YYYYMMDD>`/`<NNN>` untouched — the correct hash, curl shadowed as before):
```bash
D=<YYYYMMDD>; N=<NNN>
FILLER=C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
echo "75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda  $FILLER" | sha256sum -c - \
  && python "$FILLER" "$D" "$N" \
  && curl -sS -X POST http://192.168.2.3:8789/register \
       -H 'Content-Type: application/json' \
       --data-binary "@C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/p2-body-${D}-venom-${N}.json" \
       -w '\nhttp_code=%{http_code}\n'
echo "CHAIN_EXIT=$?"
```
Raw output (complete, unedited — this is everything that printed, tool reported exit code 2):
```
/usr/bin/bash: eval: line 17: syntax error near unexpected token `;'
/usr/bin/bash: eval: line 17: `D=<YYYYMMDD>; N=<NNN>'
```
**MATCH, and fails even harder-closed than the minimum bar**: `<`/`>` are Git Bash redirection metacharacters, so the pasted placeholder line is a **hard shell syntax error** — the whole invocation aborts at parse time, before the hash check, the filler, or the curl stand-in ever run. "No file written, nothing sent" holds, confirmed:
```
$ ls -la ".../v4-prep"                          # identical to post-(a)/(b) state, no 20261016-* or placeholder-named files
$ find "<session-dir>" -iname "*YYYYMMDD*" -o -iname "*NNN*"   # zero matches
$ ls -la "YYYYMMDD"                             # No such file or directory
```
No stray file was created anywhere, including no redirection-target file — the parser rejected the line before attempting to open anything.

**One observation, not a fourth case, not run**: this specific failure mode (hard syntax error) is a property of the angle brackets themselves. If someone instead stripped the brackets but forgot to substitute real values (e.g. pasted bare `YYYYMMDD`/`NNN` as literal strings), the hash check would still pass and the failure would happen one step later, inside the filler's own argument validation, similar in shape to case (c). I did not test this variant — it's outside the four named cases — flagging it only as an adjacent seam worth awareness, not a defect or a blocking finding.

## Cleanup and final state

```
$ rm -v ".../v4-prep/B6-20261015-venom-015-body.txt" ".../v4-prep/p2-body-20261015-venom-015.json"
removed 'C:/Users/terre/.../v4-prep/B6-20261015-venom-015-body.txt'
removed 'C:/Users/terre/.../v4-prep/p2-body-20261015-venom-015.json'
RM_EXIT=0
```
Final directory listing (identical to the pre-test baseline — same 3 files, same sizes, same timestamps):
```
total 32
-rw-r--r-- 1 terre 197609 3659 Sep 26 03:19 projection-capture1.txt
-rw-r--r-- 1 terre 197609 3659 Sep 26 03:24 projection-capture2.txt
-rw-r--r-- 1 terre 197609  953 Sep 26 03:19 projection.py
```
`git status --porcelain --ignored` after all testing: identical to before (only ignored cache dirs) — no repo file touched, nothing staged, nothing pushed, branch still `internal`.

## Bottom line

Zero discrepancies. (a), (b), (d) all reproduce exactly as ip-man's ruling specifies, against the literal final Run 2 text in Addendum 5, with curl fully replaced by a hashing stand-in and no network call made at any point. (c) is legitimately stood in for by the prior dispatch (`a8d5edb`, per Helio's own "Next 2" instruction), reinforced today by re-hashing the filler and P2 draft and finding both unchanged. No bug found here to route to Bruce Lee/Jackie Chan/etc. — this is confirming evidence, not a new defect.

Files referenced:
- `C:\Repo\townsquare\docs\ip-man-ruling-decision6-p2-filler-hash-20260926.md` (QA work order, cases a-d)
- `C:\Repo\townsquare\docs\session-v4-prep-20260926.md` (Addendum 5, the exact command text tested)
- `C:\Repo\townsquare\docs\ronda-raw-reverify-filler-20260926.md` (prior dispatch, commit `a8d5edb`, stands in for #8/#11/#14)
- `C:\Repo\townsquare\docs\helio-recheck-2-decision6-20260926.md` (lines 214-221, "Next 2" instruction the prior dispatch fulfilled)
- `C:\Repo\townsquare\docs\decision-6-fill-day-of-values.py` (sha256 `75e17655...`, re-confirmed unchanged)
- `C:\Repo\townsquare\docs\decision-6-p2-body-draft.json` (sha256 `96a760d0...`, re-confirmed unchanged)
- Scratchpad: `C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep\` (test outputs written and deleted here; restored to baseline)
