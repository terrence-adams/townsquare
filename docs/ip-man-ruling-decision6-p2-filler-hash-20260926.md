# Ip-man's ruling: yes, P2's send command must check the filler's hash

Delivered 2026-09-26, settling Helio's ESCALATE. Requires a sha256sum -c clause before the
filler runs, in both the first run of the day (whose output is filed as B.6) and inside
P2's send -- one path string for the check and the run, output left visible, no design
text changed. Rejects running the filler from its own commit (swaps a matched pin for an
unrecorded one). Precisely specifies the clause's form, placement, and mismatch behavior,
and gives ronda-rousey four exact QA cases to run against the final text. Also notes gsp's
rating is on file (MEDIUM/LOW, non-blocking) and defers his fleet-side F2 question as a
separate matter, not ruled here. Pulled byte-for-byte from the subagent transcript's
SubagentHandback field, not retyped -- save_verbatim.py's CLI reads only an end_turn text
block, so it cannot extract this delivery shape; the hash below was computed by hand, not
printed by that tool.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=7af57350e710504484c7b1e03955c313a94e7d2bde8a261056eef79d78d0d1f9 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a8c90bd398607b278.jsonl:80 message=msg_011CfRtEWo9VsUtaVaY28ZpG -->
# ip-man: ruling on Helio's ESCALATE, decision 6. Must P2's send command check the filler's hash?

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** ruling only. Nothing registers, runs or is pushed. Decision 6 stays held for Sensei.

**Question** (Helio, `helio-recheck-2-decision6-20260926.md`, line 192): "must P2's send command check the filler's recorded SHA-256 (75e17655…) before running it?" His recommendation (line 202): "require it."

**Ruling: yes, required.**
- P2's send command checks the filler's SHA-256 inside the command itself, immediately before the filler runs. The chain stops on a mismatch.
- The filler's first run on the day, whose output is filed as B.6, gets the same check.
- This applies v5 §4 as written. No design text changes, and the filler and the draft keep their hashes.

**Terms**
- **P2:** the registration POST in v5 §4.
- **B.6:** kano's registration Bulletin, filed between P1 and P2.
- **The filler:** `C:\Repo\townsquare\docs\decision-6-fill-day-of-values.py`, sha256 `75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda`. The session reported this hash (prep doc, line 289), and Helio's `sha256sum` matched it. I did not re-hash it, because I have no shell.
- **The clause:** the hash check this ruling requires.
- **D, N:** the day-of values. D is `<YYYYMMDD>`, the UTC date at filing. N is `<NNN>`, the next free `BB-<D>-venom-` number.
- **Target checked:** Helio's term. A command's target is pinned by a hash written into the command. A line without one is not covered by Sensei's yes.
- **1ee6601:** the session's commit on `internal` that added the filler and the draft.
- **#8, #11, #14:** claims as numbered in Helio's re-check 2.
- **His Next 2, 3, 4:** the numbered next steps in the same re-check (lines 214–229).

## Why

1. **The filler is P2's check, so it has to be pinned.**
   - v5 §4 P2 says to check the body "against the draft the GATEWAY carried, pinned by its SHA-256" (line 195), and not to send it if it differs anywhere else (line 204). The filler does both.
   - It holds the draft's pin (`96a760d0…`) and B.6's pin (`f0dac81e…`) as constants (its lines 34–35). A constant protects nothing if the file that holds it can change.
   - Pinning the filler pins every check it runs. Without the clause, every other pin in the chain rests on one file that nothing checks.
2. **His yes covers exact text** (v5 §4 Writes, line 145). **But `python "<path>"` names a location, not code.**
   - The tree is shared: the brief says so, and Helio re-ran nothing because of it.
   - So what runs on the day is whatever sits at that path by then, after any checkout, stray edit or line-ending conversion.
   - This is not hypothetical here. The operator's standing rule on pushing from a shared working tree comes from exactly this kind of event (2026-09-25).
   - With the clause, the text he approves decides what runs. Without it, the text only decides where to look.
3. **Helio's rule for scripts decides coverage, and it names this exact form.**
   - A script in an Actions line needs "its hash written into the command (`echo "<sha256>  <file>" | sha256sum -c - && <script>`) … or the line is `target checked: no`".
   - A `no` line "is not covered; it is its own question" (`C:\Repo\Agentic\agents\helio-gracie.md`, lines 246–250 and 255–256).
   - So declining sends P2 back to Sensei as a second question, and it comes back to him pinned anyway (re-check 2, line 82). Declining costs him a question and saves nobody anything but a line.
4. **It is not new scope.**
   - Helio's release condition (2) already named it: "one send command that checks the filler's hash, runs it, and POSTs only if it succeeded" (`helio-gateway-decision6-rework-20260926.md`, line 207).
   - Addendum 4 dropped it without comment. I checked this myself: prep doc lines 296–302 have nothing before the filler.
   - This ruling just holds the condition to its own words.
5. **Cost: one line.** The hash is already recorded and re-derived. The filler and the draft stay byte-identical.

## The clause, precisely

- **Form.** Use Helio's own form, with the full 64-character hex hash and two spaces before the path:
  ```bash
  echo "75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda  C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py" | sha256sum -c -
  ```
- **Place.** It comes first in the chain, joined to the filler by `&&` with nothing in between: check `&&` filler `&&` curl. Without `pipefail`, a pipe's exit status is `sha256sum`'s, which is what `&&` tests. (That is my reading of bash, not a test.)
- **One path string.** The file checked and the file run are named by the same string, typed once. A variable set at the head of the command does this. Otherwise a reviewer has to prove that two spellings name the same file.
- **Output left visible.** Don't use `--status` or `--quiet`. The day's raw output then shows `<path>: OK`, as a record that the check ran.
- **Both runs of the filler on the day get the clause:**
  - the first run, whose output is filed as B.6;
  - the run inside P2's send.
- **Why the first run too:**
  - If only the send is guarded, a changed filler is caught only after B.6 is on the board.
  - B.6 would then announce a registration that never happened, and no write on v5 §4's list could correct it (lines 135–140, 148).
  - The card itself would also have been filed from an unchecked filler.
  - Guarding the first run moves the stop to before the sitting's first write.
- **Deliberately not covered:**
  - The milliseconds between `sha256sum` reading the file and `python` opening it. The risk is a file changing over the days between his yes and the send, not a race within the same second.
  - `python`, `curl` and `sha256sum` themselves. The threat is a reviewed file changing in a shared tree, not a compromised toolchain.

## On a mismatch

- **What happens.** This is inferred from how GNU coreutils behaves; ronda's run will show the real text.
  - `sha256sum` prints the path with `FAILED` (or `FAILED open or read` if the file is missing) and exits 1.
  - The filler doesn't run, so nothing is written.
  - curl doesn't run, so nothing is sent.
- **What the session does.** It ends the sitting and reports through Helio, with the output of:
  - `git --no-optional-locks status`;
  - `git --no-optional-locks diff 1ee6601 -- docs/decision-6-fill-day-of-values.py`.
- **What it does not do:**
  - edit the hash;
  - restore the file;
  - run the filler any other way.

  In a shared tree, the change may be someone else's work.
- **After that:**
  - If the file returns to `75e17655…`, the same command runs under the same yes, starting again from P1. The artifact the command names is unchanged (Helio's rule, lines 250–253).
  - If the filler has to change, that is a code change. It gets reviewed and re-pinned, and goes back to Sensei.
- **A harmless byte change also fails the check,** for example a line-ending conversion on a later checkout. That is intended. Deciding that a change is harmless is a review, not a call to make at run time.

## Rejected

- **Declining, and sending P2 as `target checked: no`.** It saves one line. It costs Sensei a second question, and his answer to that question pins the filler anyway.
- **Running the filler from its commit** (`git -C … show <sha>:docs/… | python - …`). Helio left this choice to the session. I am making it, so that his final re-check has nothing to interpret.
  - It would close the millisecond gap.
  - But it swaps a pin Helio has already matched for one nobody has recorded (the commit SHA).
  - It is not the form his rule names for a script, so whether it counts as `target checked: yes` becomes a matter of interpretation. That is exactly the kind of loop this ESCALATE ends.
  - The filler still reads its inputs from the working tree, under its own pins.

## Helio's flags: seen

I have seen all four. They are for the session's same edit, and I am not ruling on them. I note only where they touch the clause.
1. **Type each day-of value once.**
   - Whatever form the session uses, pasting the command with D and N unfilled must still fail closed, as the current form does (re-check 2, line 44).
   - Across the sitting, the send uses the D and N from the name the first run printed, which is the name B.6 was filed under.
2. **Label where the command runs.**
   - This matters for the clause: `sha256sum`, the `C:/` paths and the `\` line continuations are all Git Bash forms.
   - Both lines are labelled "Venom, Git Bash, the orchestrating session, no elevation", as the retire line is.
3. **The send's re-run overwrites a hand-edited local copy of B.6.** This ruling makes two runs deliberate, so hand-fill B.6 in a copy under another name.
4. **Show #8 and #14 raw, or label them as reported** (also in his flags). ronda's run below covers both.

## Read this run, not ruled on

- **gsp's rating is on disk:** `C:\Repo\townsquare\docs\gsp-b4-security-rating-20260926.md`.
  - He rates it MEDIUM as drafted, and LOW with his R1 and R2 (his two text-only mitigations). That is below Helio's block line, so it holds nothing.
  - Helio's re-check says the rating hadn't reached him, so it goes to his final CHECKPOINT.
  - gsp routes one item to me: the fleet-side half of F2 (his second finding). B.6's result events land in the card's "newest event" slot, which collides with my v5 §4 list of writes.
  - That item is not in this brief, and I am not ruling on it here. Send it as its own question when Helio paces it.
- **The projection script** (`b536f664…`, whose output P5's gate hashes) exists as a file only in this session's temp scratchpad.
  - I checked with Glob: `v4-prep` holds `projection.py` and its two captures, and `docs\` has no `.py` file besides the filler. The script's full text is in the prep doc.
  - My v5 work order accepted it as "pinned in the prep doc". By this ruling's logic, a pin written in prose is not a check at run time.
  - It is a read step, not an Actions line, so it is not a GATEWAY condition and holds nothing.
  - The cheapest fix is to commit it beside the filler (moving it doesn't change its hash) and run it on the day under the same form of check.

**Pace.** I agree with Helio: converging, not cycling. What remains is a clause his own release condition named, not a new finding.

**Tribunal and recusal.** No Tribunal convenes. This is an ESCALATE to the design owner under Helio's second-REWORK rule (his definition, lines 211–213). My v5 recusal stands. This ruling now also answers this question, so if it is ever referred to the Tribunal, I am conflicted under rule 5 limb (ii) and will not sit.

**I only read.** I ran nothing and wrote nothing. Read this run:
- in full:
  - `C:\Repo\townsquare\docs\helio-recheck-2-decision6-20260926.md`
  - `C:\Repo\townsquare\docs\decision-6-fill-day-of-values.py`
  - `C:\Repo\townsquare\docs\decision-6-p2-body-draft.json`
  - `C:\Repo\townsquare\docs\session-v4-prep-20260926.md`
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v5.md`
  - `C:\Repo\townsquare\docs\helio-gateway-decision6-rework-20260926.md`
  - `C:\Repo\townsquare\docs\gsp-b4-security-rating-20260926.md`
- in part: `C:\Repo\Agentic\agents\helio-gracie.md`, lines 200–319 and 340–384;
- by Glob: `C:\Repo\townsquare\docs\*.py`, and `C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep\`.

```
WORK ORDER: decision 6, ruling on Helio's ESCALATE (P2's filler hash). Drafting only; decision 6 stays held for Sensei
- Document: the session saves this ruling byte for byte, with its SHA-256.
  - It extracts it by hand from this SubagentHandback input, with the same header disclosure as v5,
    because save_verbatim.py cannot read that shape.
  - Path: C:\Repo\townsquare\docs\ip-man-ruling-decision6-p2-filler-hash-20260926.md, on internal, not pushed.
  - Reviewed by helio-gracie at his final CHECKPOINT, together with the edit.
  - No review before the edit: it is drafting, runs nothing and changes no code. The filler and the draft
    keep 75e17655... and 96a760d0....
  - No francis or gsp round: Helio's own rule fixes the clause's form, and ronda tests how it behaves.
- Coordinate: helio-gracie.
  - No GAME PLAN, because nothing is built.
  - CHECKPOINT at one named handoff only: his final CHECKPOINT + GATEWAY (his Next 4), covering this
    ruling, the edit and ronda's result, before Sensei sees any of it.
  - The session relays ronda's result without a Helio dispatch, per his rule for DELEGATED picks.
- Implement: the session, drafting only (his Next 3), as Addendum 5 of session-v4-prep-20260926.md,
  committed on internal, not pushed:
  (1) P2's send with the clause as specified: the full hash, one path string for the check and the run,
      && into the filler, output left visible;
  (2) the filler's first run on the day, whose output is filed as B.6, as an exact line under the same clause;
  (3) Helio's flags: each day-of value typed once; both lines labelled "Venom, Git Bash, the orchestrating
      session, no elevation"; B.6 hand-filled in a copy the send won't overwrite;
  (4) optional, holds nothing: projection.py committed beside the filler at the same hash, and run on the day
      under the same form of check.
  The filler and the draft are not edited.
- Peer review: helio-gracie, at the final CHECKPOINT. He checks that:
  - both lines carry the hash his sha256sum reads for the filler;
  - each line uses one path string;
  - the check comes first, and && joins it to the filler;
  - the filler and the draft still hash to their pins;
  - the flags are addressed;
  - P2's line reads target checked: yes.
- QA: ronda-rousey. One run against the final text, at the commit carrying Addendum 5.
  Setup:
  - Replace curl alone with a stand-in that hashes the file curl would have read.
  - No network call. Delete the outputs afterwards. Show every command and its output raw, unedited.
  Cases:
  (a) pass: "<path>: OK", the filler's three OK lines, the stand-in's hash, exit 0. This is Helio's #11;
  (b) mismatch: change one hex digit in the command's copy of the hash, never in the file. Expect FAILED,
      exit 1, no new file in v4-prep, and no stand-in output;
  (c) NNN=1: the check passes, the filler exits 1, no file is written, and the stand-in doesn't run (#14);
  (d) the command pasted with D and N unfilled: no file written, nothing sent.
  Notes:
  - (a) to (d) together show the chain working both ways (#8).
  - (a) also shows whether Git Bash's sha256sum opens the C:/ path. If it doesn't, the session changes the
    one path string, and (a) runs again.
  - The command names the working tree's filler by absolute path, so a clone isolates nothing here.
    That is intended: the test is of the text as it will actually run.
  - If ronda has already run Helio's Next 2 at 1ee6601, that run stands for #11, #8 and #14, and this run
    is (a), (b) and (d) only.
- Done when:
  (1) this ruling is saved in docs\ with its SHA-256, on internal, not pushed;
  (2) Addendum 5 holds items (1) to (3), and the filler and the draft still hash to 75e17655... and 96a760d0...;
  (3) ronda's cases (a) to (d) are shown raw;
  (4) Helio's final CHECKPOINT reads P2's line as target checked: yes, and his GATEWAY puts decision 6 to
      Sensei, with gsp's rating passed to him.
- Watch for:
  (a) On the day, a FAILED from the clause ends the sitting. Nobody edits the hash, restores the file or
      runs the filler another way; the failure goes through Helio.
  (b) The send's D and N must be the ones B.6 was filed under. A mistyped pair points the row's annotation
      at the wrong post, and P3 will not catch it. Low harm: the annotation is not a stable field.
  (c) gsp's F2 fleet-side half goes to ip-man as its own question, when Helio paces it. It is not ruled here.
  (d) No design text changes. v5 §4 stands, and Helio's re-check reads one hash, in two lines.
```