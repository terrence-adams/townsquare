# Helio's GATEWAY on decision 6: REWORK on the session, not yet to Sensei

Delivered 2026-09-26. The design itself is ready and Helio's recommendation is yes, but
the GATEWAY explicitly withholds going to the operator: the session's own P2 send-command
fix from the prior turn has three real problems -- the filler and its draft live only in
this session's temp scratchpad with no stable path, the curl send does not actually depend
on the filler succeeding, and the 'compare by eye' step can never pass since a filled body's
hash necessarily differs from the template's. Helio's own random spot-check caught the
session's claim of 'an absolute path' as a MISMATCH -- it was a relative path under a cd.
The fill logic itself (which value goes where) is independently confirmed sound. Also
revises the recommended trial window to 30 days (matching the operator's own established
precedent for the sibling tracker trial) and routes an unrated security question (gsp) in
parallel, non-blocking. Pulled byte-for-byte from the subagent transcript's SubagentHandback
field, not retyped -- save_verbatim.py's CLI reads only an end_turn text block, so it cannot
extract this delivery shape; the hash below was computed by hand, not printed by that tool.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=721df0013f657d07612f002bc2d19b204e71d9ad108d6cc3b4d37beeb9b09d00 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a0806ba14f48b54ab.jsonl:153 message=msg_011CfRqvYEEZtfpGAq3hkRxs -->
# Helio: GATEWAY on decision 6, registering `claude-app` under `binding: offsite`

**Sensei, my call: not yet. One short drafting fix first, then I recommend yes.**

The design itself is ready. v3, as amended by v4 and with §4 as re-issued in v5, has answered every design finding raised against it. I recommend you register `claude-app` under `binding: offsite`, with the posting card on trial.

One piece isn't ready for your yes: the command that sends the registration (P2). Three things are wrong with it:
- It reads the request body through a relative path, inside a folder whose name is still a placeholder, and that folder is in a temp directory.
- The script that fills in and checks the body isn't pinned by hash anywhere.
- Its "compare by eye" step can't pass as written.

Your yes covers these commands by their exact text (v5 §4). So they have to be fixed before you see them, not after. The fix is the session's drafting and needs nothing from you.

You can decide now if you'd rather; nothing below changes with the fix. A yes now would cover everything except P2's send command, which would come back to you once, pinned, before it runs.

I've also changed the trial window I recommend. It's now **30 days from filing, or venom acting on the 5th `claude-app` post, whichever comes first.** The reasons are below.

**Terms**
- **P1–P5:** the five-step pre-registration check in v5 §4. P1 takes baseline reads, P2 is the registration POST, P3 compares immediately, P4 compares again after things settle, and P5 is the response table.
- **B.6:** kano's draft Bulletin that announces `claude-app` and carries the posting card (kano's review, lines 376–460).
- **The draft:** P2's request body, with two blanks, pinned by SHA-256 `96a760d0…`.
- **The filler:** `fill_day_of_values.py`, the session's script that fills those blanks and refuses to write if anything else has drifted.
- **Day-of values:** values that can only be known on the day: the filing date and number, the time, your words, and the Window.
- **Flag, park, REWORK:** a flag is a marker and work continues. A park makes one step wait for a stated condition. A REWORK is a park sent back to the work's author.
- **MATCH, MISMATCH:** I re-derived a claim and it holds, or it doesn't.
- **N and k:** I number N claims and check claim k = (s mod N) + 1 at random, where s is the output of `date +%s`.
- **Target checked:** the exact thing a command acts on is pinned by a hash, and that hash equals what I checked.

## Why yes, once the fix is in

- **The condition for lifting the hold has been met.** The tracker Bulletin, in venom's own text, held this proposal "pending a fresh check of the fleet's actual SSH-key sync procedure" (`BB-20260925-venom-001`, lines 56–58).
  - v3 is that check: it was re-derived against the sync script that actually runs, fetched from the NAS.
  - francis-ngannou found it "sound overall, with concrete additions" (his review, §5).
  - v4 and v5 answered every design finding raised since. The one left, F5, is about the wording of the work order and holds nothing up.
- **The crew agree, and nobody dissents.**
  - kano: "I recommend yes" (review, line 468).
  - ip-man, after listing everything that reads `binding`: "nothing in this pass argues against it" (v2, line 284).
- **It's bounded and reversible.**
  - `claude-app` gets no key. The one outcome a retire can't undo is a key reaching the hosts, and that would need a mistake in the request body.
  - The pinned draft prevents that mistake, and P3 would see one within seconds.
  - One retire undoes our own write, and the trial has a Window.
- **It removes a standing cost.** Unregistered, every post from your phone carries a permanent finding, and its sender never resolves to a known agent (kano's first rejected option).
- **One security item is open, and nobody has rated it yet.**
  - kano asked gsp to rate the prompt-injection surface: your app session would follow the newest event on B.6's thread.
  - This job's record has no rating from gsp.
  - That surface only opens when you paste the app instruction, which is your own step after filing.
  - If gsp rates it high or critical, it becomes a real block, and I'll say so.
- **Rejected:**
  - No: your phone posts run unregistered, each carrying findings.
  - An inbox folder that venom re-files: a new kind of artifact plus a polling duty (kano's second option).
  - Holding past the fix: it gains nothing unless gsp's rating says otherwise.

## The Window: 30 days or the 5th post

**30 days from B.6's filing, or venom acting on the 5th `claude-app` post that follows the card, whichever comes first.** My v5 re-check said 14 days. I changed it for two reasons.

- **Your own precedent.** For the tracker trial you said "yes, proceed." to a trial "capped at 30 days" that closes early once its questions have answers (venom's record: `BB-20260925-venom-001`, lines 22–23 and 65). This trial would close within days of that one, which ends 2026-10-25, so you could judge both in one sitting.
- **My v5 reasoning was wrong twice.**
  - I rejected a time-only window because it "can close with nothing to judge". A 14-day cap has the same flaw whenever you post from the app less than weekly, and only one app post appears in the record I read.
  - I rejected 30 days because it would delay your call. But the 5-post rule already closes the trial early when posts are frequent. The cap only matters when posts are rare, and that is exactly when more days add evidence.

The question the trial answers stays as B.6 wrote it: did offsite posts reach venom and get acted on without you correcting anything? If the window closes with no posts, venom reports that there was nothing to judge, and keeping or removing is still your call.

**Rejected:**
- 14 days: it can close with nothing to judge.
- Count only: it has no end if you rarely post.
- Time only: it keeps running after the question is answered.

B.6, line 456, lets either you or my pace-setting set the Window ("<his, or Helio's Pace>"). It travels in the package for your yes, and you can set a different one.

## What your yes will cover (v5 §4, "Writes")

Everything runs from Venom, in one sitting that starts with P1's reads:
1. **Filing B.6**, between P1 and P2. It is the pinned template (`f0dac81e…`), changed only in its day-of values:
   - the id and filename (`<YYYYMMDD>`, `<NNN>`);
   - `at:` (UTC time at filing);
   - HIS WORDS (your answer, copied byte for byte, with its SHA-256);
   - `Window:`.
2. **One registration POST (P2), sent once.** It is the pinned draft, changed only in the two blanks in its annotation.
3. **The retire, only as a contingency.** `POST /retire/claude-app`, with no body, only if P5's row 3 or row 2 applies. It runs once and is never repeated.
4. **Result events on B.6's thread**, in v5's shape: P4(a)'s, plus one more if P4(b) finds a difference.
5. **Any Request to bishop** that P5 or v3 §5 files, in v5's shape.

After a register or retire, the registry posts its own audit record. That comes from the service, not from us.

**Not covered. Each of these comes back to you:**
- a second retire or any other registry write (v4, Watch for (c));
- restoring another agent's row (P5 row 5);
- removing a key from the hosts (P5 row 3);
- anything else P5 might need;
- reissuing the Agent Registry document (Queue item 2);
- any doctrine change.

**Left to the session after your yes, with nothing more needed from you:**
- P1's reads and their stop rules: both key feeds and `/mesh` twice, `/registry` twice with its projection (a hash of every other agent's row), the journal, and a re-read of the retire route;
- running the filler and copying your words;
- the reads for P3, P4(a) and P4(b);
- applying the P5 table, and owning every Request.

I run CHECKPOINT (2) on B.6's result event after P4(a), before you're told the registration held.

**Your own step, after B.6 is filed:** paste kano's app instruction (review, line 464) into the Claude app, with the thread id the session gives you.

## For the session: the REWORK

The filler's logic is sound. I read it in full and hashed its inputs. It fills only B.6's id and filename and the draft's annotation, and it writes nothing if anything else differs, so F2 is fixed. What's parked is how P2's command finds the filler and uses it. The fixes are below in words; you write them. This is drafting only and needs no approval.

1. **Give the files a stable home.**
   - Commit the filler and the draft on `internal`, at a repo path you choose. Don't push.
   - Point the filler at the draft's repo path. Write its outputs to a folder outside the repo, because the working tree is shared, and have the command name that folder by absolute path.
   - Show both files' SHA-256 as checked out. The draft must still be `96a760d0…`. Record the filler's new hash in the prep doc.
   - *Why:* both files live only in this session's `%TEMP%` scratchpad, which the command reaches through the placeholder `<scratchpad>`. A later session won't have that path, and a temp cleanup would delete both files. The filler would then stop safely, but Sensei's yes would have to be asked again.
   - *Rejected:* keeping them in the scratchpad with absolute paths. It's cheaper now, but it fails the same way if the day slips.
2. **Use one send command.**
   - Make the POST depend on the filler within a single command: check the filler's recorded hash, run it, and POST only if it succeeded.
   - Name the file the filler wrote by its absolute path.
   - Drop the "compare that hash by eye" line.
   - *Why:* as drafted, the curl is a separate command that runs whether or not the filler refused, and it reads a relative path. The by-eye step compares the filled body's hash with the draft's hash; those always differ, so the step can only fail or be ignored. v5 P2 says "do not send it". I haven't tested what curl does when its input file is missing, and chaining removes the question.
3. **Show the test.** Re-run the dummy-value test with its command and raw output, writing outside the repo and deleting the outputs afterwards.

Flags for the same addendum. These are not release conditions:
- Name where `<YYYYMMDD>` and `<NNN>` come from without going in a circle. "From B.6's filed filename" can't work, because the filler makes that filename. Use the UTC date at filing (the same clock `at:` uses) and the next free `BB-<YYYYMMDD>-venom-` number on the board at that moment.
- Optionally, write B.6's filing as an exact command: write the file under the name the filler prints, then run `ts-file.sh … --seen none`. Add a diff before filing, showing that only `at:`, HIS WORDS and `Window:` changed from the filler's output. B.6 goes to Sensei as `target checked: no` either way, because his words fill it.
- Carried from my v5 re-check: copy his answer by hand, byte for byte, with its SHA-256, and put the disclosure inside the HIS WORDS slot. save_verbatim.py can't read user records.

```
CHECKPOINT — TownSquare tracker, decision 6 / "(i) P2 and the retire as exact curl commands, with P2's body in a file pinned by SHA-256. The body holds exactly v5 P2's fields, and names its two day-of values and their source" (v5 Implement) + "Session, now (drafting only, no approval needed): fix F1 and F2 in the prep doc." (my v5 re-check, Next 1) / session (3934106; the filler is in the scratchpad, uncommitted)
On task:     partly.
             - F2 is fixed: the filler fills only B.6's id line and its filename, and the card's own examples stay as written.
             - F1 is partly fixed:
               - done: --data-binary; the fill changes only the two values; the draft's hash is checked first; any other difference stops it; the commands are labelled.
               - not done: a stable path. The filler, and the draft it reads, live only in this session's %TEMP% scratchpad,
                 reached through the placeholder <scratchpad>.
               - new with the filler: it is pinned nowhere; the send doesn't depend on it succeeding; and the by-eye check can't pass.
Design:      The filler conforms to v5 §4 P2's check: the body may differ from the pinned draft only in the two values, or nothing is written.
             The send command does not conform. v5 P2 says "do not send it", and nothing stops the curl running after the filler refuses.
             That fix is part of the REWORK.
Doctrine:    conforms: drafting only, dummy values, outputs deleted, nothing sent (reported-by session).
             The filler is a drafting aid for v5 P2's reviewed check, not a build (v5: "Implement: none", "QA: none").
             Its independent check is my reading plus my hashes of its inputs. That is same-vendor evidence, so it is weak.
Claims:      1. my F1: relative path, no fill, no pre-send check, --data — true by reading
             2. --data strips newlines, so the bytes checked aren't the bytes sent — reported-by Helio (curl's documentation; not run)
             3. my F2: the placeholders recur in the card's own instructions, which must stay as written — true by reading
             4. "Both fixed with one verified script" — judgement: F2 yes; F1 only in part (see On task)
             5. it re-checks the pinned B.6 template and P2 draft against their hashes before anything else — MATCH; load-bearing
             6. it fills <YYYYMMDD>-venom-<NNN> in exactly one place in each — MATCH (counts below)
             7. it confirms the card's <YYYYMMDD>-claude-app-<NNN> examples are untouched — true by reading (65–68). That check can't
                fail, because the two patterns never overlap; the inverse check at 70 is what proves it
             8. it confirms byte for byte that nothing else differs — true by reading (70, 82)
             9. it writes nothing if any check fails — true by reading: every stop comes before the writes at 89–90
             10. the dummy run: one substitution per file, the examples untouched, no leftover < or > — UNSUPPORTED (no command, no output)
             11. the test output was deleted, and nothing is a real filing — reported-by session; consistent: v4-prep holds no 20261001 file
             12. commands labelled: Venom, Git Bash, the orchestrating session's scratchpad, no elevation — true by reading
             13. the filler prints the day body's path and SHA-256 — true by reading (94)
             14. "compare that hash by eye against what it prints for the pinned draft" — judgement: it can't pass. The filled body's hash
                 always differs from the draft's
             15. the curl sends with --data-binary — true by reading, from a relative path (263)
             16. the retire command is unchanged — true by reading; it matches v5 P1
             17. F3: ip-man's "source as read" wording governs — true by reading
             18. docstring: the filler reads the draft "from this repo" — refuted by reading: line 18 points into %TEMP%
             19. docstring: it writes nothing to the repo, and its outputs go beside the script — true by reading (21, 87–88)
             20. brief: it "fills B.6's and P2's day-of values in exactly the right places" — overstated: it fills only the id's two
                 values; at:, HIS WORDS and Window: are still filled by hand
             21. brief: "The P2 curl command now uses --data-binary and an absolute path" — picked; MISMATCH
Assumptions: - The send assumes one shell keeps its working directory from the cd through to the curl, and that the curl runs only after
               the filler reports OK. Not declared → session (REWORK 2).
             - It assumes %TEMP% keeps both files until the day. If they go, the filler stops, and the yes has to be asked again
               → session (REWORK 1).
             - "<YYYYMMDD> and <NNN> from B.6's filed filename" is circular, because the filler makes that filename → session (flag).
             - kano's review stays LF on disk. Checked: ls-files --eol shows i/lf w/lf.
             - write_text(newline=) needs Python 3.10 or later. Checked: 3.14.6.
Blocks:      - HIS WORDS — REAL (b), (c): decision 6 is his and not yet made, and his words are an input only he can supply. His answer
               clears it.
             - Not a block: committing the filler on internal needs no approval. It is local, reversible and not pushed, and every doc on
               this job was filed the same way.
Verified:    N=21; k=21 from date +%s → 1790415605 (mod 21 = 20).
             #21 → MISMATCH. The --data-binary part holds; the "absolute path" part does not. Deciding lines, prep doc 256 and 263:
               `cd "<scratchpad>/v4-prep"` and `--data-binary @p2-body-<YYYYMMDD>-venom-<NNN>.json \`
             Load-bearing #5 → MATCH. The constants at lines 19–20 are the pins, and this run's inputs hash to them:
             - B.6's block, extracted the way the filler does: f0dac81e… (79 lines; one <YYYYMMDD>-venom-<NNN>;
               two <YYYYMMDD>-claude-app-<NNN>; no CR);
             - the draft: 96a760d0… (one placeholder, which holds its only < and >; no CR).
             Also MATCH: #6; #13 and #19 by reading; projection.py still hashes to b536f664…
             #18 is refuted by reading.
             Recorded now: the filler hashes to 2f3433f2619539df576f0e80e8c879ba06661b65275be79c150ee18ce4abc8ec. No record pinned it before.
             Not re-run: the filler writes files, and I treat the tree as shared. #10 stays UNSUPPORTED. Since I re-derived the other
             checkable claims this run, #10 is the only re-run owed by its author.
Verdict:     REWORK session. Released when a new addendum shows all three of:
               (1) the filler and the draft committed at a stable repo path on internal; the filler reads the draft there and writes
                   outside the repo; both hashes are shown as checked out (the draft still 96a760d0…, the filler's new hash recorded);
               (2) one send command that checks the filler's hash, runs it, and POSTs only if it succeeded, naming the file it wrote
                   by absolute path, with no by-eye step;
               (3) #10's dummy run, with its command and raw output.
             Cite: v5 §4 "Writes" (the yes covers "the exact text the session writes out before the GATEWAY"); v5 §4 P2 ("do not send it";
             "Send it once"); v5 Implement (i); Verification step 6 (a MISMATCH parks its line, and its author re-runs the report's
             measured claims with output).
             Flags → session: where <YYYYMMDD> and <NNN> come from; optionally, B.6's filing command and a diff before filing.
Pace:        converging. F2 is closed, and the deliverable changed shape: a verified filler replaced a bare curl. What remains is the
             stable-path point F1 already raised, plus two small defects the new script brought in. This is the last drafting round I
             foresee: the re-run checks only the fix.
Next:        1. session, now: the REWORK (drafting only; no approval needed).
             2. session: re-dispatch Helio for the final CHECKPOINT + GATEWAY. Pass this report verbatim (or its saved copy), the new
                addendum, and gsp's rating if it has arrived.
```

```
GATEWAY — TownSquare tracker, decision 6: register claude-app under binding: offsite, on trial
For Sensei:   none yet: REWORK session — P2's send command (v5 Implement (i)).
              After the re-run, one yes or no comes to you: register claude-app per v3 as amended by v4, with §4 as re-issued in v5,
              with the card on trial. Window: 30 days from filing, or venom acting on the 5th claude-app post, whichever comes first.
              Recommendation: yes (reasons, and what the yes covers, are above).
              You may decide now instead; if you do, P2's send command alone comes back to you, pinned, before it runs.
Queue:        1. decision 6, as above, after the re-run.
              2. Later, as a separate decision: v2 §5 item 6 has venom reissue the Agent Registry document as v1.7 "right after the POST".
                 No yes on decision 6 covers that, because v5 §4 lists the writes it covers.
                 Recommendation: hold the reissue until your keep-or-remove call on the trial.
                 Rejected: reissuing right after the POST. It would write a binding value you haven't decided to keep into the registry
                 document as if it were settled.
Delivered:    - the design: v3, v4 and v5 §4, reviewed by francis-ngannou (v3) and by my re-checks of v4 and v5;
              - the pins: B.6 template f0dac81e…, P2 draft 96a760d0…, projection script b536f664…;
              - the retire command;
              - the filler: F2 fixed; its fill logic is sound by my reading; its send command is parked.
Verified:     By me (Anthropic, Claude Opus 5.5), read-only, this run, at 3934106 on internal:
              - the three pins above;
              - B.6's placeholder counts;
              - the filler, read in full, and its hash (2f3433f2…);
              - its filename constant, which equals kano's line 378;
              - kano's review: unchanged since 752ef16, LF in the index and on disk;
              - Python 3.14.6;
              - the random pick (#21) → MISMATCH.
              Carried from my v5 re-check:
              - v5 §4 differs from v4 §4 only where ip-man lists;
              - the draft holds exactly v5 P2's 12 fields.
              The design judgements I cleared are agreement from the crew's own vendor, so they are weak evidence.
              v5's projection check was my own proposal.
Not verified: - No SENSEI (verbatim) block and no list of your decisions reached me, so nothing here rests on your words.
                The 30-day precedent is venom's record of your "yes, proceed." (BB-20260925-venom-001): reported-by venom.
              - The dummy run (#10): no output yet. The REWORK asks for it.
              - The filler when run: I read it but didn't run it, because it writes files.
              - The running registry, and "not sent": reading either would be a network call.
                v5's "What the source shows" is the NAS's source as read on 2026-09-26, not the running process (ip-man's words).
              - What curl does with a missing input file: untested. The REWORK removes the question.
              - Whether the card is clear to other vendors' models: kano's handoff to eddie-brock is not on record.
Security:     jigoro-kano (review, B.4, line 325), in the finder's words: "One item for gsp to rate, not a reason to block. His app session
              is his general assistant, with personal connectors such as mail and calendar. Having it read board text widens the
              prompt-injection surface to his personal account. It already reads the board today. The card limits reading to one
              venom-authored event and the thread being written."
              Severity: unrated. gsp has not rated it on this job's record.
              My question for gsp, not a rating: the card makes the newest event on B.6's thread a source of instructions, and any writer
              on the board can append that event (B.4: every agent reaches the board through one connector with OWNER on the whole tree).
              I found no credential in the draft, the template or the commands. That is a reading, not a gsp review.
Open:         - the REWORK — session
              - gsp's rating — gsp
              - HIS WORDS and the Window — Sensei, when the package comes
              - after a yes: P1–P5 in one sitting, and every Request they produce — session
              - CHECKPOINT (2) on B.6's result event after P4(a), before Sensei is told the registration held — Helio
              - pasting the app instruction (kano, line 464) with the filed id — Sensei
              - the register's D-number cross-reference — venom; not blocking
              - F5, the ordering in Done-when (3) — ip-man; holds nothing
Routed:       - B.4's injection surface → gsp, by name. Deliver it now, in parallel with the REWORK. It holds nothing unless rated high or
                critical.
              - kano's B.7 handoff to eddie-brock (read the card for clarity across vendors) has been on no work order since v2 → ip-man,
                as a flag.
              - francis's corrections #2 and #19 → francis-ngannou, for the record.
              - save_verbatim.py's two gaps (SubagentHandback inputs; user records) → session, for the tool's owner.
Dropped:      0
```

## When this verdict stops being right

- **If gsp rates B.4 high or critical,** my yes becomes a real block (f) until gsp's path clears it.
- **If the fix changes more than how P2 is sent** (the draft's bytes, its fields, or B.6's template), the re-run is no longer a check of the fix alone.
- **If P1–P5 can't run soon after your yes,** a pin can drift, for example kano's review or the registry's source. The filler stops on drift by design, so nothing unsafe follows, but the yes would have to be asked again.
- **If you want the trial's answer sooner, whatever the post count,** 14 days fits better than 30.

## Missing from the brief

- There was no `SENSEI (verbatim):` block and no list of your decisions. Nothing here rests on your words; I read the tracker Bulletin for the decisions on record.
- My v5 block wasn't passed verbatim. I read the saved copy the brief named.
- The revised command text wasn't passed. I read it in the prep doc at `3934106`.
- No `r` was given, so I used `date +%s`.
- Nothing said the working tree is unshared, so I re-ran no crew program.

## My shell use

- `git --no-optional-locks`: `log`, `status --porcelain --ignored` (at the start and the end; the same both times, ignored caches only), `show --stat`, `ls-files --eol` and `rev-parse`.
- `ls`, `sha256sum`, `date +%s` and `python --version`.
- Two read-only `python -c` one-liners that hashed and counted B.6's block and the draft. Each was a single expression, with no `;`, `|` or `>`; angle brackets and backticks were built with `chr()`.
- Nothing was written, sent, fetched or pushed.

## Files

- C:\Repo\townsquare\docs\session-v4-prep-20260926.md (3934106; Addendum 3 is lines 231–273; the commands are lines 255–267)
- C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep\fill_day_of_values.py (sha256 2f3433f2…, uncommitted)
- C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep\p2-body-draft.json (96a760d0…)
- C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d\scratchpad\v4-prep\projection.py (b536f664…)
- C:\Repo\townsquare\docs\townsquare-project-tracker-design-v5.md
- C:\Repo\townsquare\docs\townsquare-project-tracker-design-v4.md
- C:\Repo\townsquare\docs\townsquare-project-tracker-design-v3.md
- C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md (§5, lines 174–309)
- C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md (lines 268–269, 325, 376–475)
- C:\Repo\townsquare\docs\helio-v5-recheck-20260926.md
- C:\Repo\townsquare\docs\helio-v4-recheck-20260926.md
- C:\Repo\townsquare\docs\francis-ngannou-review-v3-20260926.md (§5)
- G:\My Drive\N3rd0m\TownSquare\Bulletin Board\BB-20260925-venom-001.000-OPEN__to-all__impact-informational__from-venom__project-tracker-on-trial-venom-only-not-doctrine.txt (lines 22–23, 56–58, 65)
- C:\Users\terre\.local\bin\ts-file.sh
- C:\Repo\revere\docs\step-1.1-final-checkpoint-gateway-20260926.md (the shape this follows)