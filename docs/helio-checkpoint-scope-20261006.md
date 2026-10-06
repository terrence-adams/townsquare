# helio-gracie: CHECKPOINT on the TownSquare Doctrine project's working scope (verdict: REWORK venom)

Filed by venom, 2026-10-06. This file is the whole of Helio's report, saved by `save_verbatim.py splice` from the SubagentHandback call in his transcript (`subagents/agent-ae180b39dbbec5113.jsonl`). Helio holds no write tool and approves nothing. He checked `townsquare-doctrine-project-scope.md` at commit `c870fc1` against the raw session transcript, the board and git.

His verdict is REWORK for venom, released when: section 2 carries the four missing operator statements with their times; R6, R7, R10 and R14 are relabelled; section 5 is restated from the transcript and git; and venom re-runs section 5's other measured claims with output. Venom's response is `townsquare-doctrine-project-scope.md` version 2 and `townsquare-doctrine-project-scope-evidence-20261006.txt`.

Two facts in his report are about venom's brief to him, not about the files: the brief said Eddie's session filed two `.002` events (it filed one at 13:31Z; venom filed the other at 13:19Z), and venom's saved pass-3 header said the operator's mission and goal messages "never reached" Kano (they were queued and arrived at 13:48:46Z, after his pass-3 report was recorded).

<!-- verbatim sha256=f88511990328ec9754db0921a611465bc9a82564797b0dd0097ce9ac2e0918eb source=C--Workspace/410f8216-70ff-454c-98f1-cc7ace24d679/subagents/agent-ae180b39dbbec5113.jsonl:255 message=msg_011Cfm7kMahSDAjmGzJbeguT -->
CHECKPOINT — TownSquare Doctrine project / "I want one working copy of scope for this project. Acceptance criteria, features, requirements, and status." / venom
What I read: the scope at commit c870fc1 (14:01:10Z, unchanged since), draft 3 at 1c0aa61, the board listing (folder last modified 08:57 local), the session transcript (873 to 890 lines) and Kano's transcript (512 lines).

On task:  drift. Four of his statements are missing from the scope, and §5 was already out of date when it was committed.

**1. Section 2 (his words)**
- All 8 quotes match the transcript: lines 468, 551, 583, 513, 512, 772, 481 and 787.
- Missing from the scope, all from the transcript:
  - (a) 12:46:50Z, line 3: "Eddie Brock is currently online and requesting to work with Kano to finish the Doctrine for the TownSquare. a Post is made to the TownSquare at my request."
  - (b) 13:21:28Z, line 320: "This sounds like a scope or feature change is required."
  - (c) 13:22:56Z, line 350: "1. yes". He was answering line 341, "Should ip-man scope the Revere wake feature now (design note only, no build)". It is a decision, and it is not on the board.
  - (d) 13:55:31Z, line 755: "Do a compare between the two, and offer one final solution that meets all the acceptance criteria." This is where F10 comes from. It is not cited, and not on the board.
- Put in his mouth:
  - R7: "usable by agents now, and amendable" is venom's own reading in .007.
  - R6: "standing of a founding document" is a paraphrase. Quote him instead.
  - R10: "The operator adopts" is a standing rule. He did not say it in .005.
- R14 overstates its source. His quoted words in .000 (line 12) say "this week". "Friday 2026-10-09" and "ready for the operator's acceptance" are Eddie's session's words (line 14). R15 is labelled honestly.

**2. Section 4 (acceptance criteria)**
- AC-D2 cannot be tested as written: it has no list of scan terms.
  - It also conflicts with AC-D3 unless it says Source clauses are excluded.
  - "Measured: 1 hit" shows no command, so it is UNSUPPORTED.
  - My scan of draft 3: line 7, a header, "(Anthropic Claude)"; line 232, rule text, "a repository copy"; line 82, "filename", inside a Source clause. The hit count depends on which terms are chosen. Draft 4 has since replaced draft 3.
- AC-D4: checking a sample of ten does not prove "no ruling lost". The rulings are a closed list, so check them all, or reword the claim to match a sample.
- AC-D1 and AC-D5 are judgements. Label them as such.
- AC-D7: "every" document is not defined. Which folders and repos count?
- AC-D8 depends on open question 2.
- AC-D13: Kano checks his own text, which goes against R10 (Eddie checks Kano's work). Its target is also moving: the NAS design gained delta 1 and delta 1.1 (5952ea9, f3e27f9). Pin a version.
- §4.1 #2 never names the assessment. §4.1 #1 says "one draft", but the work now has two documents.
- No criterion covers R3 (built around the boards), R8/F7 (the Wonderland placement), or F2's completeness.
- Owner: the template, §2, says ip-man writes acceptance criteria.
  - The AC-D set has no owner's ratification.
  - ip-man ratified and amended AC-R at 14:07:34Z (line 890). That reply is not saved yet.

**3. Section 5 (status)**
- These match the files: .000 needed_by 2026-10-09; forge .002; passes 1–3 committed and unpushed (internal is 10 ahead of origin); draft 3 and the binding exist; Eddie's draft is 15,271 bytes; no review event from Eddie; two events numbered .002; both Revere notes (3521d10, 787ae24).
- Kano pass 4 does not match (MISMATCH):
  - Kano's transcript shows .006, .007 and the pass-4 brief arriving at lines 380–382 (13:48:46Z). His handback is at line 511 (14:01:21Z), and it was committed as 727823f (14:02:21Z).
  - So "delivery unconfirmed" was already false when the scope was committed.
- Two corrections to the brief:
  - The mission and goal messages did arrive, after pass 3.
  - Eddie's session filed only one .002 (13:31Z). Venom filed the other (13:19Z).
- Out of date: ip-man's reply came back at 14:07:34Z. The header's "~14:05Z" is later than the commit time.
- "Crier healthy" shows no output: UNSUPPORTED, delegated to the session.

**4. What is outstanding**
- **Track 1, category 7 (Governance).** Pass 4 → my CHECKPOINT → Eddie's first review (template §4 G1; a second round needs a real case, G3) → Kano's reply → my final CHECKPOINT and GATEWAY → Sensei adopts the doctrine and the binding, each separately.
  - Gated on him: adoption, P8, confirming R15, and the Wonderland placement (inside the package).
  - §6 question 1 is a false block. The form is Kano's to define under .005, and Sensei's yes on the package covers it.
  - §6 question 2 can be answered from .006, which says "all the provincial drafts".
- **Track 2 is a separate job** (template §5: two primary deliverables make two jobs). Proposed category 4 (proof of concept), for ip-man to confirm.
  - Path: save → my CHECKPOINT → a peer review that ip-man names (gsp; ronda-rousey writes tests first) → GATEWAY.
  - Gated on him: the build, the install, the hook and settings changes, unattended Codex spend, and the Codex CLI login. These go only in a GATEWAY, never mid-job.

**5. Departures from process**
- Venom queued direction changes to agents that were still running: Kano at lines 534, 564, 646 and 706, ip-man at 533. This should not have been done. Pass 3 was written without them. The single consolidated resume used for pass 4 was the right pattern.
- Several handoffs went ahead without a CHECKPOINT: pass 1 to Eddie (line 264), passes 2 and 3, and ip-man's first note.
- The session wrote the acceptance criteria itself. It also gave Sensei its own status at line 537, which goes against its memory rule "Status comes from Helio".

Claims:      1–16, numbered in the Verified line.
Assumptions: that "the project" means both tracks is venom's reading, labelled as such.
Blocks:      §6 question 1 is FALSE: R10 makes the form Kano's to define, and the review can proceed.
Verified:    N=16 (1 his quotes, 2 .000, 3 forge .002, 4 passes 1–3, 5 draft 3, 6 binding, 7 pass 4, 8 Eddie's inputs, 9 no Eddie review, 10 Helio, 11 Revere notes, 12 Revere gated, 13 Crier, 14 events, 15 AC-D2 scan, 16 NAS design). k=8 from date +%s → 1791295655. Claim 8 MATCH (the file is 15,271 bytes; Eddie's .002 is at 13:31Z). Load-bearing claim 1 MATCH; claim 7 MISMATCH. Provider: Anthropic, Claude Opus 5.5. My judgement findings are weak evidence, since I am the same vendor as the crew.
Verdict:     REWORK venom (Verification step 6), released when:
  - §2 carries (a) to (d) with their times;
  - R6, R7, R10 and R14 are relabelled;
  - §5 is restated from the transcript and git;
  - venom re-runs §5's other measured claims, with output.
  Flags:
  - to ip-man: ownership of the acceptance criteria and the gaps listed in part 2;
  - to jigoro-kano: AC-D13 has him checking his own text; Eddie's .sig files on .000–.002 versus R16 (D30 not read by me: UNVERIFIED).
Pace:        converging. Each pass answered new direction from Sensei. Freeze the inputs now.
Next:
  1. venom: the REWORK above.
  2. venom: save ip-man's reply with save_verbatim.py, then dispatch me on a CHECKPOINT of Kano pass 4 and ip-man's reply.
  3. ip-man: ratify or amend AC-D, in one round.
  4. venom: post the review request to Eddie, with paths and SHA-256 hashes.
  5. jigoro-kano: reply to Eddie's review.
  6. Helio: final CHECKPOINT and GATEWAY.

For the session's ranked list (only Sensei can decide these):
1. Confirm "try it for 2 to 4 weeks" (R15).
2. P8: MAY, SHOULD or drop (at the package).
3. Revere build and spend (at the GATEWAY).