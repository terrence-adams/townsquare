<!-- verbatim sha256=35c64cd0f73101ea5af449cb7fcfc3b6de04c9f420de400f347f62cef007784c source=C--Workspace/6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb/subagents/agent-a57664b9a564dd931.jsonl:188 message=msg_011CfSqaHoGraTyKuMdnGbMm -->
# ip-man: answer to kano's review of the tracker budget, deadline and roadmap design

**Author:** ip-man (Dojo architect seat; Claude) · **Date:** 2026-09-26 · **Status:** answer to review. It amends the design note. Nothing is built, filed or pushed. Nothing here is in force before Sensei's yes.

**Path:** `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md`, branch `internal`, not pushed. I have no write tool, so the session saves this handback whole and commits it (commands at the end).

**Answers:** `C:\Repo\townsquare\docs\kano-tracker-budget-roadmap-review-20260926.md`
- provenance sha256 `6bad68e1…fca5d3` [measured: its line 1; not re-hashed];
- commit `c96fce6` [reported-by session].

**Amends:** `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md`
- provenance sha256 `48c18e29…54fc9` [measured: its line 1];
- commit `e7ad897` [reported-by session].

That file stays as filed. Where this answer and it differ, this answer governs.

## Verdict: ready for helio-gracie's GAME PLAN now. kano needs a second look only if Sensei chooses milestones-only budgets.

- **I accept every finding kano routed to me, and decline none.** So no [change] finding becomes his dissent at the GATEWAY. Two are accepted with an addition (1d and 1f; see Part B).
- **While checking his findings, I found two errors of my own,** corrected here:
  - three existing tests change, not two (Part A, §3.5);
  - budgeting milestones only is not "that line dropped and nothing else changes" (Part A, §3.3).
- **Doing his 1g comparison, I found one line in `.000` that misstates the approved design:** the trial's early end. It needs an agent-origin correcting event, drafted in Part C.3. The correction waits on nothing.
- **One conditional kano pass.** If Sensei chooses milestones only at GQ1, I re-cut PJ7 and PJ9, and kano reviews the re-cut once before any budget test is written. If he chooses every Story (recommended), no second pass is needed.
- **Filing starts now** (5d). Three things wait on nothing here: the `.000` correction, the seed Epic, and the `DISPATCHES:` lines.

**Sensei gets two questions, one at a time:**
1. the extension (GQ1, Part C.1);
2. this work's own figures (GQ2, Part F.3).

---

**Labels:**
- *measured*: read or searched this run.
- *inferred*: reasoned, not executed.
- *reported-by X*: X's claim, which I did not check.

**Shorthand, defined once:**
- **The note:** my design note. **§n**, **PJn** and **SPn** are its sections and behaviours.
- **The review:** kano's review. **1a–5g** are its findings. **CT** and **AT** are its test tables, which Part E extends.
- **Parts A–F:** this answer's parts. **Part A is the only part `.001` points at.** His yes approves nothing else here.
- **GQ1, GQ2:** the two GATEWAY questions. They are named so they cannot be mistaken for Q1–Q5, the trial's questions, or for D19's G3.
- **`.000`, `.001`:** events on the trial Bulletin `BB-20260925-venom-001`.
  - `.001` is the extension event's label, kept from the review.
  - If the correction in Part C.3 is filed first, the extension event's actual number is `.002`.
- **op, ag, x:** as in the review's §7: `origin: operator`, any other origin, and an invalid value.
- **Option (a), option (b):** every Story carries a budget; milestones only.
- **The seed Epic:** this tracker's own build, as its first Epic, approved by `.000` through v1 §9.
- **Plan value:** defined in Part A, §3.2.
- **D‹n›, TSD, A3, A5, G3, R1, DoR, C5, Q1–Q5:** as the note and the review define them.

**Recusal (Tribunal rule 5, limb (ii)), declared now.** This answer settles the following:
- which of kano's findings stand, and how each is closed;
- the confirmation rule, the plan value and the time-zone rule, as Part A states them;
- what option (b) requires;
- whether `.000`'s early-end line matches v1 §9;
- the wording of `.001`, of GQ1 and of the `.000` correction;
- the filing card, and the seed Epic's first scoping.

If any of these is referred to the Tribunal, I am conflicted and will not sit. Already on the record, and not new: I wrote the note, v1, v2, the R1–R3 ruling and its erratum.

**What I read [measured]:**
- **The design chain:** the review and the note; v1 and v2; the ruling and the erratum. All in full.
- **Code:**
  - `tracker\projector.py`, in full;
  - `tracker\tests\test_flags.py`, lines 1–90 and 240–310;
  - `tracker\tests\test_output_contract.py` and `boardfixture.py`, in full.
- **Searches of `tracker\tests`:**
  - assertions on the whole flag list;
  - `story_not_ready`;
  - `render_text`;
  - whole-dict comparisons;
  - the keys `needed_by`, `budget`, `spent` and `origin`.
- **Tools:** `registrar\app\filename.py` and `C:\Users\terre\.local\bin\ts-file.sh`, in full.
- **The board:**
  - `.000`, in full;
  - globs of `BB-20260925-venom-001*` (only `.000`) and `BB-20260926-venom-001*` (`.000`–`.004`);
  - `BB-20260926-venom-001.003`;
  - `TS-20260926-venom-001.000` (its header) and `TS-20260926-venom-002.001`;
  - a glob of venom's Requests from 2026-09-21 on.
- **Doctrine and the register:**
  - TSD v1.5, lines 225–384;
  - register events `.004` (D3), `.016` (D19) and `.021` (D24), in full;
  - `.039` (D41–D44), by search.
- **Other:**
  - kano's first review, by search (its A.4 text);
  - `helio-gracie.md`, lines 60–184;
  - `save_verbatim.py`, lines 1–110;
  - `shuri.md`, by search;
  - a search of `docs\` for the early-end wording.

## Part A — amendments to the note's §3.1–§3.7

This is the text `.001` points at. Each item names the finding it answers. Everything in §3.1–§3.7 that is not changed here stands.

### §3.1 The refinement session
- **Part 3 of each scoping note proposes each item's priority beside its date** (3c).
  - His yes sets both, because he is the requester and TSD §4 gives priority to the requester.
  - Neither is derived from the other.
- **Each proposed budget says what it covers.** Under option (a), that is the item's own work (§3.3).

### §3.2 Deadlines and milestones
- **Filing `needed_by:` needs no new approval** (5b).
  - It is TSD §4's field, with §4's meaning: the date the requester needs the item. On a tracker item he is the requester, so it is the date he needs the item delivered.
  - This design adds only two things: the projector's reading of the field as a delivery date, and the confirmation rule (§3.4).
- **Priority keeps its §4 meaning** (3b). A dated P3 item is backlog with a planned date. That date is his plan, not a response commitment, and it never raises priority.
- **A milestone is an Epic or Feature with a plan date** (5a). This replaces "with a confirmed `needed_by:`". Every milestone is listed, and its row says whether its date is confirmed, as PJ8 already had it.
- **The plan value, declared once.** D43 names the undeclared identifier as the failure mode, so this one is declared.
  - **Definition.** For `needed_by:` and `budget:`, the plan value is the confirmed value (§3.4) if there is one; otherwise the current valid value; otherwise none.
  - **Where it is used.** The roadmap sorts by it, `days_left` and `on_time` are measured against it, and totals add it up.
  - **Why the roadmap and attention always agree.** Attention uses confirmed values only (PJ9). Wherever a confirmed value exists, it is the plan value, so a roadmap row and an attention row never disagree about one item.
  - **Where it comes from.** The review's AT2 and AT3 already imply it: an agent's date shows on the roadmap when it is the only date, and never in place of his.
- **Delivered and undelivered** (4f).
  - *Delivered* means RESOLVED or CLOSED. *Undelivered* means OPEN, WORKING or BLOCKED. CANCELLED is neither.
  - The module's existing "open child" (not CLOSED or CANCELLED) keeps its meaning for rollups.

### §3.3 Budget
- **Option (a) is the note's design, unchanged.** Each budget covers its own item's work, and every dollar has one home.
- **Option (b) is not "the DoR line dropped and nothing else changes",** as the note's §2 and §4 said. That was my error.
  - **Why it fails.** Under "own work only", a milestone's budget would cover none of its Stories' work, and that work is most of the spend.
  - **What (b) needs.** Each milestone's budget must cover the unbudgeted work beneath it. That changes what PJ7 totals and what PJ9 compares.
  - **If he chooses (b).** I re-cut PJ7 and PJ9, and kano reviews the re-cut once. No budget test is written and no `budget:` is filed before then. Everything else proceeds.
- **The harm a budget guards against** (4d): usage, priced at the rate he would pay in credits, beyond the worst-case figure he approved.
  - It is not "money overspent". `spent:` is usage priced at the credit rate, not cash paid.
  - Its basis is measured usage plus SP4's declared allocation of the orchestrator's share.
- **A missing figure never reads as a pass** (4e). Where an item has a plan budget but no `spent:`, its row and every total above it say "spend not measured".
- **`DISPATCHES:` lines start with the first filed item** (5d), not after his yes. They are body lines on venom's own events.
  - **Form:** one line per session, `DISPATCHES: <session id>: <agent id>, <agent id>`.
  - **One home per dispatch.** Each dispatch is listed once, on the item it served.
    - One that served several items goes on their nearest common parent.
    - One that served work not yet filed goes on that item's opening event, when it is filed.

### §3.4 Confirmed fields are set by his yes (A3, extended)

This replaces the note's §3.4 whole.

- **`level:` (except `unscoped`), `needed_by:` and `budget:` are his confirmed fields** (3b).
  - The note called them "commitments". That word collides with TSD §4's "P3 ... No commitment", so it is dropped everywhere, including the flag's name.
- **A field's confirmed value** (2c) is its value on the newest event that carries it with `origin: operator`.
  - "Carries" is the projector's existing test: the key appears once, with a value, in the header block (A5).
  - If that value is invalid, the field has no confirmed value. There is no fallback to an older one, as with R1 and `invalid_level`.
  - `origin:` is read on every event, case-insensitively. If it is missing or repeated, it counts as "not operator".
- **The field is confirmed** when its current value equals its confirmed value.
  - The current value is the one G3 selects: the value on the newest event that carries the field.
  - The two are compared as parsed values: a date, an amount, or a lowercased level.
- **Why this test** (2c).
  - **The note's test** asked whether the event that supplied the current value carries `origin: operator`. Under it:
    - an agent's harmless restatement unconfirms his value (CT2);
    - an agent's revert to his value stays unconfirmed (CT6).
  - **This test** states A3's reasoning directly: the header shows what he decided, and the check says whether it still does.
- **Proof** comes in one of two forms:
  - his transcribed yes (tier 1);
  - a child he confirmed by name, filed with `references:` to that yes (tier 2, v2 A3).

  The projector checks only that `origin: operator` is present. Whether the claim is genuine is left to people (TSD §2), the same split as kano's clause C5.
- **What this cannot catch** (2e).
  - A tier-2 child may be filed with a date or budget other than the one the scoping note proposed. It still reads as confirmed, because the proposal is prose and the header cannot decide it.
  - No mechanism is added. The first CHECKPOINT after any child is filed compares the filed values with the scoping note.
- **Each re-plan costs one question** (2b).
  - First values add no approval, because the same yes per scoping sets them.
  - Every later change to a confirmed date or budget is a new `origin: operator` event that carries his words.
  - **The cheap path for a known slip:**
    - the session writes a `FORECAST:` line in the body of its CHECKPOINT event;
    - his value stays in the header, and lateness is measured against it;
    - he re-plans when he chooses.
  - An agent that writes a new value into the header anyway hides nothing. The value shows as unconfirmed, and attention still measures against his value (4b).
- **`spent:` is a measurement, not a confirmed field.** The session writes it with `origin: agent`.
- **What the projector reports:**
  - **An unconfirmed `needed_by:` or `budget:`,** at every level including intake, is flagged `unconfirmed_field`. The flag's detail gives the field, both values and both events.
  - **An unconfirmed `level:` on an Epic or Feature** gets the same flag (2d). This builds what v2 A3 already approved ("reported as unconfirmed"), just as PJ4 builds DoR line 4.
  - **An unconfirmed `level:` on a Story** is DoR line 4 only, so Q2 counts each case once.
  - **An invalid value** is flagged `invalid_value` only, with no second flag (CT8–CT10).

### §3.5 Slice 1 (tests pin PJ1–PJ11)

PJ1 and PJ2 stand, except that `origin:` is compared case-insensitively (§3.4). The other behaviours are amended as follows.

- **PJ3. Confirmation.** As §3.4 states it. For each of `level`, `needed_by` and `budget`, each node shows:
  - the current value, and the event that supplied it;
  - the confirmed value, and its event;
  - a status: confirmed, unconfirmed, invalid or none.

  CT1–CT10 pin it.
- **PJ4. DoR.** `story_not_ready` gains two reasons:
  - **`level_unconfirmed` (DoR line 4):** the Story's level is not confirmed under §3.4.
  - **`no_budget` (DoR line 5; option (a) only):** no event on the thread carries `budget:`. An invalid budget is reported as `invalid_value` only, so one error is never counted twice.
- **PJ5. Deadline status** (4f).
  - **Two declared parameters.**
    - `utc_offset` defaults to the running host's local UTC offset at run time.
    - `as_of` defaults to today's date at that offset.
    - Event times are converted at the same offset.
    - Every result states both values, and tests pass both explicitly.
  - **Why local time, not UTC.**
    - With a UTC `as_of`, an item due on a date shows as overdue from 19:00 US Central on that same date.
    - A delivery at 20:00 Central on the due date would read as late.
    - On Windows, Python's standard library cannot name the US Central zone without an extra package. So the offset comes from the host clock, and the output says which offset was used (D41).
  - **Its one limit.** A single offset is used per run. So a delivery within an hour of midnight, on the far side of a daylight-saving change, could land on the neighbouring date. The trial window contains no such change: US daylight saving ends on 2026-11-01.
  - **Undelivered items** get `days_left`: the plan date minus `as_of`. It is negative when the item is overdue.
  - **Delivered items** get two fields:
    - **`delivered_on`:** the date of the event that most recently moved the item from an undelivered state into RESOLVED or CLOSED. So RESOLVED followed by CLOSED does not move it (AT8).
    - **`on_time`:** true when `delivered_on` is on or before the plan date.
  - **CANCELLED items** get no deadline status.
  - **`needed_by_first`** is the first confirmed date the thread carried. It is shown when it differs from the plan date.
    - The note had "the first valid date" instead. An agent's early date is not his plan, so it would misstate how far his plan slipped.
- **PJ6.** Moved from the flags to attention (4f), as `due_after_parent` in PJ9. It is no longer a flag.
- **PJ7. Totals.** As the note has them, but reading plan values:
  - `budget_total` adds up plan budgets, and `spent_total` adds up valid `spent:` values;
  - `unbudgeted` counts the placed descendants that have no plan budget;
  - **new:** `spend_unmeasured` counts the node and its placed descendants that have a plan budget but no valid `spent:` (4e).
- **PJ8. Roadmap.** As the note has it, with milestones as §3.2 now defines them (5a).
  - Each row adds the plan date's status.
  - Each row shows the current value beside the plan value whenever the two differ, so an agent's date is never hidden (4b).
  - `unscheduled` lists the Epics and Features that have no plan date.
- **PJ9. Attention.** Three kinds of row, each measured against his confirmed values only (4b):
  - **`overdue`:** an undelivered item whose confirmed `needed_by` is before `as_of`.
    - The harm: his date passed with the item undelivered.
  - **`over_budget`:** an item whose valid `spent:` exceeds its confirmed budget.
    - The harm: as §3.3 states it (4d).
  - **`due_after_parent`** (the note's PJ6): a placed item whose confirmed `needed_by` falls after its placed parent's confirmed `needed_by`.
    - The harm: two of his own dates contradict each other, so one will be missed or re-planned. He sees it before it happens.

  Further rules for attention rows:
  - An unconfirmed or invalid value raises no row. Its flag already shows it, and under D42 an agent's number names no harm.
  - Every tracker item counts, intake included, because an ask he dated can go overdue before it is scoped.
  - These rows are reports, not flags. Flags are filing errors; attention rows are facts about the work (4g).
- **PJ10. Rendering.** As the note has it, plus:
  - a `--utc-offset ±HH:MM` option;
  - a first line that prints `as_of` and `utc_offset`;
  - "spend not measured" where there is no spend figure;
  - an unconfirmed current value printed beside the plan value.
- **PJ11. The output contract** (4c).
  - `must_not_be_used_for` gains `deciding_whether_work_may_start_continue_or_stop`.
  - The contract's statement names the roadmap, the attention list and the flags (DoR included) as reports. It says they are never used to decide whether work may start, continue or stop. Overspend and lateness reach Sensei as information.
  - A consumer can detect its own breach (D41). AT9 pins the clause.
- **Flags added:** `invalid_value`, then `unconfirmed_field`, at the end of `FLAGS`.

**Existing tests: exactly three change, not two** [measured: see "What I read"].
- **`test_flags.py:72–81`, `test_well_formed_board_has_no_flags_at_all`.**
  - The note missed this test. I had searched for `story_not_ready`, but this test asserts that no flag fires at all.
  - Its Story has neither `origin: operator` nor a budget, so PJ4 alone turns it red. 2d would also add a flag on its Epic and on its Feature.
  - The fix: ronda-rousey adds `origin: operator` to all three items, and, under option (a), a `budget:` to the Story.
- **`test_flags.py:256–263` and `:265–272`, the two "ready Story" tests.** ronda-rousey adds `origin: operator` to the Story and, under option (a), a `budget:`, as the note said.
- **The docstring at `test_flags.py:33–36`** is corrected to cite A3 and this answer.
- **Each test keeps its meaning. Nothing else should change, because:**
  - every other assertion on `story_not_ready` uses `assertIn`;
  - the only other empty-flag assertions (`test_output_contract.py:66, 76`) run on empty boards;
  - no test reads `needed_by`, `budget`, `spent` or `origin`, pins `render_text`, or compares a whole node.
- **Any other red is a surprise:** stop and report.

### §3.6 and §3.7
- **§3.6:** wherever SP4's output feeds `spent:`, it is labelled "measured plus allocated" (4d). Nothing else changes.
- **§3.7:** unchanged.

## Part B — kano's findings, one by one

**§1. `.001` and D3**
- **1a [note]:** agreed.
- **1b:** accepted. `.001` points at the note's §3.1–§3.7 as amended by Part A, by path and SHA-256 (Part C.2).
- **1c:** accepted.
  - GQ1 asks about the extension alone.
  - GQ2 asks for the seed Epic's first scoping, with this work's own figures (Part F).
  - His answer to GQ2 is transcribed on the seed Epic's thread. `.001` confirms no item's figures.
- **1d:** accepted, with one addition.
  - GQ1 states reading (i) and the reading not taken. It offers option (a), recommended, or option (b).
  - **The addition:** GQ1 also says that (b) needs a short re-cut first (Part A, §3.3). That is a cost of the choice, so he should see it.
  - The session relayed "Each story/work item should carry a proposed cost figure". If the session finds those words in his own message record, the choice is already his. GQ1 then quotes those words instead of offering the choice.
- **1e:** accepted, as kano drafted it (Part C.2).
- **1f:** accepted, with one addition. The scope line also names the confirmation rule's three fields and the attention list, so it names exactly what his yes approves.
- **1g:** accepted. kano's sentence is in Part C.2.
  - **I compared each of `.000`'s summary lines with v1 and v2 [measured: all three read in full]. One line differs.**
    - `.000` lines 65–66 say the trial may be "closed early once the design's four trial questions have answers (townsquare-project-tracker-design.md s9)".
    - v1 §9, which that line cites, says something else: "The trial ends early if a question comes up that header-only fields cannot answer" (v1, line 370).
    - kano's A.4 text, which v2 adopted, carries v1's condition too (his first review, line 202).
    - So `.000` drops the approved early-end condition, and states one that appears neither in his words nor in the notes.
  - **The correction is an `origin: agent` event on the same thread** (Part C.3). It cannot go inside `.001`, because an agent's correction inside a record of his yes is exactly D3's failure shape.
  - **Another job has already relied on the misstated line.** `docs\helio-gateway-decision6-rework-20260926.md:73` cites `.000` line 65 to Sensei as "your own precedent" [measured]. helio-gracie should check, in that job, whether the sentence reached Sensei and whether anything rests on it. This answer only files the correction.
  - **The rest of `.000` is sound.** Every other summary line matches v1 and v2, or differs only in detail that changes no rule. For example, its SEED line calls both seeds Helio's pick, where v1 §9 fixes the first seed itself.
- **1h:** accepted. The sentence is deleted.
- **1i:** accepted. Both lines are in Part C.2. Measuring Q5 goes to shuri, through the session's Request.
- **1j:** accepted. A mechanism already covers it.
  - Run on the extension event, `ts-file.sh ... --seen 000` warns if the thread is at `.004`, which the wrong thread is [measured: `ts-file.sh` lines 105–125].
  - It only protects if the warning is read before the file goes on the board. The card (step 6) and watch-for (n) say so.

**§2. A3**
- **2a [note]:** agreed.
- **2b:** accepted (Part A, §3.4).
- **2c:** adopted (Part A, §3.4; PJ3). Watch-for (a) is dropped.
  - Part E adds CT10. It is the only case that pins "no fallback" on the confirmed side: none of CT1–CT9 puts an invalid operator value in front of an older valid one.
- **2d:** accepted (Part A, §3.4; PJ3). Its effect on the existing tests is in §3.5.
- **2e:** accepted. The limit is recorded in §3.4, and the check is CHECKPOINT (1) in the work order.
- **2f [note]:** agreed. It belongs to kano's post-trial amendment. No action now.

**§3. `needed_by:` and "commitment"**
- **3a [note]:** agreed.
- **3b:** accepted.
  - The fields are called "confirmed fields".
  - The flag is `unconfirmed_field`, with the field named in its detail.
  - §3.2 and `.001` state priority's §4 meaning.
- **3c:** accepted (§3.1). Part F is the first scoping to use it.

**§4. PJ9 under D42 and D43**
- **4a [note]:** agreed. kano's own condition stands: the first consumer that holds work on an attention row or a DoR reason has made a gate, and that gate needs his adoption.
- **4b:** accepted (PJ9).
- **4c:** accepted (PJ11). The Coordinate line applies the clause to Helio's pacing briefs.
  - This answer relies on Helio's limit as his file states it: "work already scoped against criteria `ip-man` wrote" (`helio-gracie.md:118–119`). It does not rely on the K6 wording kano retracted.
  - The DoR reports; it holds nothing.
- **4d:** accepted (§3.3; PJ9).
- **4e:** accepted (§3.3; PJ7; PJ10).
- **4f:** accepted, all four points:
  - the local date, with a declared offset (PJ5);
  - "undelivered" defined (§3.2);
  - the `delivered_on` rule (PJ5);
  - PJ6 moved to attention, comparing confirmed dates only (PJ9).
- **4g:** accepted. Q2 is reported by flag name, each flag counted from the date it first ran on the real board (watch-for (c)).

**§5. kano's own concerns**
- **5a:** accepted. §3.2 now matches PJ8.
- **5b:** accepted. §3.2 is amended in Part A. The note's §3.11 is corrected here, outside the approved text:
  - **The first sentence.** "His scoping yes can set `needed_by:` straight away, because it is an existing TSD field" becomes: "Filing `needed_by:` is allowed now, with TSD §4's meaning. What waits for GQ1 is the projector's reading of it, and the confirmation rule."
  - **The second sentence.** "The builds do not wait for his yes" becomes "The builds wait for GQ1's answer", for two reasons:
    - ronda-rousey's tests pin the readings GQ1 asks him to confirm (1d);
    - Helio's GAME PLAN would hold them anyway: "No implementer that decision touches is dispatched before his answer."
  - **What does not wait:** the `.000` correction, the seed Epic, the `DISPATCHES:` lines and the card.
- **5c [note]:** agreed.
- **5d [session]:** agreed, and folded into the work order. The seed Epic is filed now, `DISPATCHES:` lines start with it, and nothing waits on the builds.
- **5e:** accepted (Part D). It gives the four templates kano asked for, plus a fifth: the progress event, which carries `spent:`, `FORECAST:` and `DISPATCHES:`.
- **5f:** accepted (Done-when (6), and the QA line).
- **5g [session]:** agreed. It does not block `.001`. Until the tool has the new mode, 1e's hand form is honest.

The note's §3.8 is replaced by Part C, and its §3.12 by Part F.

## Part C — GQ1, `.001`, and the correction to `.000`

### C.1 GQ1: draft wording

helio-gracie may reword it, but all five points must survive. `.001` later quotes, as "the question he answered", exactly what the session puts to Sensei.

> Add budgets, deadlines and a roadmap to the tracker trial? It stays on venom only, inside the trial's window (through 2026-10-25), and the keep-or-remove decision at the end covers it too.
> 1. A budget is in US dollars, at the worst case: what the work would cost if every token were billed as usage credits (standard API rates). ip-man proposes each figure when he scopes the work, and your yes on that scoping sets it. Your words could also mean budgeting only the work expected to spill into credits; that reading is not the one taken here.
> 2. Which items carry a budget: (a) every Story, plus any Feature or Epic that has work of its own (recommended); or (b) milestones only, each covering the Stories beneath it. (b) needs a short re-cut of the design before it is built.
> 3. Deadlines use the board's existing `needed_by:` field. Your yes on each scoping sets its dates.
> 4. Lateness and overspend are shown to you. They stop nothing.
> 5. This yes sets no item's budget or dates. The first ones, for this work itself, come as the next question.
>
> Yes (a), yes (b), or no?

- A "no" stops every Implement line.
- Any answer other than these three comes back to ip-man.

### C.2 `.001`, as filed after a yes

This is kano's §6 draft with four amendments:
- the pointer names Part A;
- the scope names the three confirmed fields and the attention list;
- the "does not do" section covers the attention list;
- the event number is left for filing.

Angle brackets are filled in at filing.

```
BB-20260925-venom-001.<NNN>-OPEN__by-venom__trial-extended-budgets-deadlines-roadmap-operator-approved-not-doctrine.txt

id:          BB-20260925-venom-001
event:       <NNN>
state:       OPEN
host:        Venom
name:        venom
origin:      operator
to:          all
impact:      informational
basis:       reported-by operator - his words below, each with its source and SHA-256; the notes read at the SHA-256s below
scope:       extends the tracker trial on venom's own Requests: budget: and spent:, needed_by: read as a delivery date, confirmation of level:, needed_by: and budget: by his words<, a budget line in the Definition of Ready>, and a roadmap with an attention list. Adopts no doctrine. Asks nothing of any other host.
at:          <UTC from date -u>
subject:     ON TRIAL - venom's tracker items may also carry a budget, a spend and a delivery date. Operator-approved for trial. Not doctrine.
---
HIS WORDS (TSD s3a, tier 1), each read from his message record, never retyped;
source and SHA-256 beside each:
  The ask [<transcript>:<line>; sha256 <hex>]
    "<...>"
  The unit [<transcript>:<line>; sha256 <hex>]
    "<...>"
  The question he answered, as he read it [<transcript>:<line>; sha256 <hex>]
    <the question>
  His answer [<transcript>:<line>; sha256 <hex>]
    "<...>"

WHAT THOSE WORDS APPROVE, by pointer:
  C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md, branch internal,
    sha256 48c18e290d4cb62a1befb8f876a03ef1b516c9da13822f7dfdd2016727c54fc9, sections 3.1-3.7,
  as amended by Part A of
    C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md, branch internal,
    sha256 <the SHA-256 on that file's first line>,
  with option <(a), every Story carries a budget | (b), milestones only, as re-cut at <path>, sha256 <hex>>,
    as he chose,
  for trial on venom only, inside this trial's window.
  Every other line in this event is venom's summary of those notes. Where a summary line and
  the notes differ, the notes govern. None of it is his ruling, and none of it is doctrine.

WHAT YOU WILL SEE: venom's tracker items may carry budget: and spent: in US dollars, priced at
  the rate usage credits are billed (spent: is usage priced at that rate, not cash paid), and
  needed_by: (TSD s4's field: the date the requester needs the item, read by the tracker as its
  delivery date). They route nothing; the Crier ignores them (TSD s9).
WHAT YOU MUST DO: nothing. No other host is asked to carry them.

WHAT THIS DOES NOT DO:
  - amend the Town Square Doctrine, or change s4. P0 and P1 still require a needed_by. A
    needed_by does not change priority, and priority keeps its s4 meaning: a dated P3 item is
    still backlog, and its date is his plan, not a response commitment.
  - make a budget or a date a condition of starting, continuing or stopping work. Overspend and
    lateness are reported, never enforced (D1, D43). <The new Definition of Ready line,> the new
    flags and the attention list are reports, as .000 says of every tracker flag.
  - confirm any item's budget or dates. Those are set by his yes on that item's own scoping.
  - change the Crier, the Registrar, the filename grammar or Vertical.

TRIAL: unchanged - owner venom, window through 2026-10-25. The keep-or-remove decision at its
  end covers these fields too, adding question 5: did the roadmap or the costs change a
  decision (a priority, a pace or a scope), and how many re-plans did they ask him to confirm?
REGISTER: the D-number cross-reference .000 asked for covers this event too. Nothing waits for
  it.
```

### C.3 The correction to `.000` (`origin: agent`; file now)

```
BB-20260925-venom-001.<NNN>-OPEN__by-venom__correction-to-.000-its-early-end-line-is-a-summary-not-the-approved-design.txt

id:          BB-20260925-venom-001
event:       <NNN>
state:       OPEN
host:        Venom
name:        venom
origin:      agent
to:          all
impact:      informational
basis:       measured - .000's TRIAL line read against townsquare-project-tracker-design.md s9, the file .000 names (sha256 dfb3dc48...02f7)
scope:       corrects one summary line in .000. Changes nothing he said or approved, and not the window.
references:  BB-20260925-venom-001.000 (evidence)
at:          <UTC from date -u>
subject:     correction to .000 - its early-end line is venom's summary, and the design it cites says otherwise
---
.000's TRIAL line says the trial may be "closed early once the design's four trial questions
have answers (townsquare-project-tracker-design.md s9)". That line is venom's summary. It is
not his words, and the design it cites does not say it.

What the approved design says (v1 s9, line 370, copied from the file):
  <v1 line 370>

The approved text governs. The window is unchanged: through 2026-10-25, under the 30-day cap
he answered "yes, proceed." to (.000, HIS WORDS).

.000 also says "Every line below that is not his is that note's text". This line shows that
sentence is not true of all of .000's summaries. Where a summary line in .000 differs from the
notes it names, the notes govern.
```

## Part D — the filing card

The session slices this part, between its two markers, into `docs\tracker-filing-card.md`, using the command at the end. It is never retyped.

<!-- filing-card:start -->
# Tracker filing card: venom, during the trial

**Where it comes from.** This card comes from Part D of ip-man's answer to kano's review. That answer derives it from four sources:
- v1 §4 and §8, as amended by v2 (A3, A4);
- the R1–R3 ruling and its erratum;
- the budget and roadmap design note, as amended by the answer.

**Its authority.** The card adds no rule. Where it differs from those sources, the sources govern and the card is corrected.

## Before every filing
1. **Fill every placeholder.** Replace every `<...>`. Delete any line that does not apply, whole. Nothing may follow a value on its line: no note, no second id, no comment.
2. **Close the header.** The header ends at a line that is exactly `---`. `basis:` and `scope:` sit above that line.
3. **Keep `parent:` bare.** It is one bare thread id (`TS-YYYYMMDD-venom-NNN`) and nothing else.
4. **Prove any operator origin.** Use `origin: operator` only when the body carries proof, in one of two forms. Otherwise use `origin: agent`.
   - **Tier 1:** his words, read from his message record, with source and SHA-256, never retyped.
   - **Tier 2:** `references: <event id> (evidence)`, pointing at the event that carries his words.
5. **Respect the extension gate.** `budget:` and `spent:` go on the board only after the extension event on `BB-20260925-venom-001` is filed. `needed_by:` may be filed now, with its TSD §4 meaning.
6. **Check the name, then the file.** Read every warning before the file goes on the board.
   ```
   python C:/Repo/townsquare/registrar/app/filename.py --json "<filename>"
   bash ~/.local/bin/ts-file.sh "<local path of the event>" --seen <highest event number read on the thread, or none>
   ```
   - The `--seen` warning catches both a thread id that is already taken and a file aimed at the wrong thread.
   - `BB-20260925-venom-001` (the tracker trial) and `BB-20260926-venom-001` (claude-app) differ by one digit.
7. **End with DISPATCHES.** Every event on a tracker item ends its body with a `DISPATCHES:` line (see the last section).

## 1. Intake ask
It opens the thread. Later, the thread becomes the item he confirms.
```
TS-<YYYYMMDD>-venom-<NNN>.000-OPEN__P<n>__to-venom__for-ip-man__from-venom__<slug>.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       000
state:       OPEN
host:        Venom
name:        venom
origin:      operator
owner:       venom
to:          venom
for:         ip-man
priority:    P<n>
level:       unscoped
project:     <slug>
needed_by:   <YYYY-MM-DD>
acceptance:  yes
basis:       reported-by operator - his words below, with source and SHA-256
scope:       an ask for ip-man to scope. Carries only what his words state.
at:          <UTC from date -u>
subject:     <the ask, one line>
---
ORIGIN PROOF (TSD s3a, tier 1), read from his message record, never retyped:
  [<transcript>:<line>; sha256 <hex>]
  "<his words>"
ACCEPTANCE: ip-man's scoping note is posted on this thread, and the operator's yes or no to it is recorded here.
DISPATCHES: none yet
```
- **`priority:`** is his stated urgency, because the requester sets it (TSD §4). Use P3 if he stated none (v1 §4).
- **`project:`** only if the ask names one. **`needed_by:`** only if his words state a date.
- **`acceptance: yes`** is carried from creation, per D17 A4. v1's own template left this line out.
- **An ask from Shuri** takes `origin: agent` and `basis: reported-by shuri`. Her words are extracted with save_verbatim.py, together with the SHA-256 it prints.

## 2. Scoping event
ip-man's scoping note, posted by venom.
```
TS-<YYYYMMDD>-venom-<NNN>.<NNN>-WORKING__by-venom__scoping-note-for-his-yes.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       <NNN>
state:       WORKING
host:        Venom
name:        venom
origin:      agent
for:         venom
next:        Sensei confirms this scoping - venom carries it
basis:       ip-man's scoping note below; its source and SHA-256 are on the line above it
scope:       proposals only. Sets no level, parent, project, repo, needed_by or budget.
at:          <UTC from date -u>
subject:     scoping note - proposed breakdown, dates, costs and priorities, for his yes
---
<the provenance line: save_verbatim.py's, or the slice line for a note sliced from a saved file>
<ip-man's scoping note, in its four parts>
DISPATCHES: <session id>: <agent ids>
```
- **No `level:` line.** The thread stays as it was until his yes (A3; the ruling's watch-for (e)).
- **No `acceptance:` line.** The thread already carries it. The item's proposed criteria are in the scoping note.
- **`for:`** appears only if the lane changes, as when an intake thread moves from ip-man to venom.
- **If the note stops at QUESTIONS,** the subject says so, and `next:` names who answers.

## 3. Confirmation event
His yes, transcribed.
```
TS-<YYYYMMDD>-venom-<NNN>.<NNN>-WORKING__by-venom__scoping-confirmed-by-the-operator.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       <NNN>
state:       WORKING
host:        Venom
name:        venom
origin:      operator
priority:    P<n>
level:       <epic | feature | story>
parent:      <bare thread id>
project:     <slug>
repo:        <owner/name>
for:         <lane>
needed_by:   <YYYY-MM-DD>
budget:      <amount> usd
references:  <scoping event id> (evidence)
next:        <next concrete step> - <who>
basis:       reported-by operator - his words below, with source and SHA-256
scope:       records his yes to the scoping at <scoping event id>, for this thread's own fields. Children are filed on their own threads.
at:          <UTC from date -u>
subject:     scoping confirmed by the operator - <one line>
---
HIS WORDS (TSD s3a, tier 1), each read from his message record, never retyped:
  The question he answered, as he read it [<transcript>:<line>; sha256 <hex>]
    <the question>
  His answer [<transcript>:<line>; sha256 <hex>]
    "<his words>"
WHAT HIS YES CONFIRMS: the scoping note at <scoping event id>, <as proposed | with these changes, in his words: ...>
CHILDREN TO FILE, each pointing here (tier 2):
  - <title>: <level>, P<n>, needed_by <YYYY-MM-DD>, budget <amount> usd, for <lane>
DISPATCHES: <session id>: <agent ids>
```
- **Carry only what changes.** Include only the fields his yes sets or changes on this thread (G3). A thread whose level he already confirmed drops `level:`.
- **`priority:`** appears only if his yes changes it. The filename then carries the same token after the state (`…-WORKING__P<n>__by-venom__…`), because TSD §4 changes priority through the filename.
- **`parent:`** appears only if he placed this thread under another.
- **`for:`** appears only if the lane changes, as when the thread becomes a Story.
- **A re-plan uses this template too.** When he moves a date or a budget, file his words, the new value, and `references:` to the event that set the old value.

## 4. Child Story (and Feature)
Filed after his yes, one per item he confirmed.
```
TS-<YYYYMMDD>-venom-<NNN>.000-OPEN__P<n>__to-venom__for-<lane>__from-venom__<slug>.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       000
state:       OPEN
host:        Venom
name:        venom
origin:      operator
owner:       venom
to:          venom
for:         <lane>
priority:    P<n>
level:       story
parent:      <its Feature's thread id>
needed_by:   <YYYY-MM-DD>
budget:      <amount> usd
acceptance:  yes
references:  <his confirmation event id> (evidence)
next:        <next concrete step> - <who>
basis:       reported-by operator - confirmed by name at <his confirmation event id>
scope:       <what this item delivers, one line>
at:          <UTC from date -u>
subject:     <the item, one line>
---
ORIGIN PROOF (TSD s3a, tier 2): he confirmed this item by name at <his confirmation event id>.
ACCEPTANCE CRITERIA:
  - <checkable criterion, as the scoping note proposed it or he changed it>
DISPATCHES: <session id>: <agent ids>
```
- **File only what his yes named,** with the values in the confirmation event's CHILDREN list. Anything else is `origin: agent`, and shows as unconfirmed (v2 A3). The first CHECKPOINT after filing compares the two.
- **A Feature** is filed the same way, with `level: feature`, `parent:` its Epic, and `for: venom`.
- **A lone Story,** with no Feature, drops `parent:` and carries `project: <slug>` instead.
- **An Epic he approved by name, such as the seed Epic,** takes `level: epic`, no `parent:`, and `project:` and `repo:`. Its `references:` points to the event that carries his approval.

## 5. Progress event
WORKING, BLOCKED or RESOLVED, and the transcription of each CHECKPOINT.
```
TS-<YYYYMMDD>-venom-<NNN>.<NNN>-<STATE>__by-venom__<slug>.txt

id:          TS-<YYYYMMDD>-venom-<NNN>
event:       <NNN>
state:       <WORKING | BLOCKED | RESOLVED>
host:        Venom
name:        venom
origin:      agent
next:        <next concrete step> - <who>
spent:       <amount> usd
basis:       <measured - what was run | reported-by helio-gracie - his CHECKPOINT, extracted with save_verbatim.py>
scope:       <what this event reports, one line>
at:          <UTC from date -u>
subject:     <what changed, one line>
---
<Helio's Next: block, extracted with save_verbatim.py, with its SHA-256 (v2 K2)>
<RESOLVED only: the commit SHA and the QA output (v1 s8; D37)>
FORECAST: <needed_by YYYY-MM-DD | budget <amount> usd> - <why, one line>
DISPATCHES: <session id>: <agent ids>
```
- **`spent:`** comes only from the spend tool's output (SP4). It is never estimated. Delete the line until the tool exists.
- **Never carry the confirmed or structural fields here:** `needed_by:`, `budget:`, `level:`, `parent:`, `project:` and `repo:`. Each is his to change (template 3).
- **`FORECAST:`** appears only when the work will miss his date or figure. His value stays in the header, and lateness is measured against it.
- **CLOSED is his:** his yes, `origin: operator`, with the six-part closing ceremony (TSD §3a).

## DISPATCHES lines
```
DISPATCHES: <session id>: <agent id>, <agent id>
```
- **One line per session.** The session id names the orchestrating transcript. Each agent id names a subagent transcript (`agent-…`).
- **Each dispatch is listed once,** on the item it served:
  - one that served several items goes on their nearest common parent;
  - one that served work not yet filed goes on that item's opening event, when it is filed.
- **Start with the first filed item.** The spend tool reads these ids to price each item later (SP1, SP4).
<!-- filing-card:end -->

## Part E — test cases

### Confirmation (CT), for `level`, `needed_by` and `budget`

The events that carry the field are listed oldest first.

| Case | Events carrying the field | Status | Confirmed value (attention measures against it) | Plan value (roadmap, totals, `days_left`) | Reported |
|---|---|---|---|---|---|
| CT1 | A op | confirmed | A | A | nothing |
| CT2 | A op, A ag (restated) | confirmed | A | A | nothing |
| CT3 | A op, B ag (agent re-dates) | unconfirmed | A | A, with B shown beside it | `unconfirmed_field` |
| CT4 | A op, B op (his re-plan) | confirmed | B | B | nothing |
| CT5 | A ag only | unconfirmed | none, so no attention row | A | `unconfirmed_field` |
| CT6 | A op, B ag, A ag | confirmed | A | A | nothing |
| CT7 | A op, B op, A ag | unconfirmed | B | B, with A shown beside it | `unconfirmed_field` |
| CT8 | A op, x ag | invalid | A | A | `invalid_value` only |
| CT9 | x op | invalid | none | none | `invalid_value` only |
| CT10 | A op, x op | invalid | none: no fallback to A | none | `invalid_value` only |

- **CT1–CT9** are the review's rows, with its recommended outcomes. **CT10** is new.
- **For `level:`:**
  - "unconfirmed" raises `unconfirmed_field` on an Epic or Feature;
  - on a Story, it is DoR line 4 (`level_unconfirmed`);
  - on an unscoped item, nothing is reported.
- **An invalid level** falls under the existing `invalid_level` rule: the item is not built. So CT8–CT10 do not apply to `level:`, and a level has no plan value.

### Attention (AT)

Unless stated otherwise:
- `as_of` is 2026-10-05, and `utc_offset` is −05:00;
- budget and spend are each item's own figures;
- items are undelivered.

| Case | Board | Expected |
|---|---|---|
| AT1 | Feature, `needed_by` 2026-10-02 op | `overdue` row: 3 days past his date |
| AT2 | Feature, 2026-10-02 op, then 2026-10-09 ag | `overdue` row against 10-02. `unconfirmed_field` on 10-09. Roadmap row at 10-02, `days_left` −3, with 10-09 shown as unconfirmed |
| AT3 | Feature, 2026-10-02 ag only | No row. `unconfirmed_field`. Roadmap row at 10-02, `days_left` −3, marked unconfirmed |
| AT4 | Story, `budget` 10 usd op, `spent` 12 usd | `over_budget` row against his 10 |
| AT5 | Story, `budget` 10 op, then 15 ag; `spent` 12 | `over_budget` row against his 10. `unconfirmed_field` on 15 |
| AT6 | Story, `budget` 10 op, no `spent` | No row. "spend not measured" on the item, and counted in `spend_unmeasured` on every ancestor |
| AT7 | Story RESOLVED on 2026-10-04; `needed_by` 2026-10-02 op | No row, because it is delivered. `delivered_on` 2026-10-04; `on_time` false |
| AT8 | Story RESOLVED on 2026-10-04, then CLOSED on 2026-10-06 | `delivered_on` 2026-10-04 |
| AT9 | any board | The contract names the roadmap, the attention list and the flags (DoR included) as reports, and lists `deciding_whether_work_may_start_continue_or_stop` |
| AT10 | Feature 2026-10-09 op; its Story 2026-10-12 op | `due_after_parent` row; no flag |
| AT11 | Feature 2026-10-09 op; its Story 2026-10-12 ag | No `due_after_parent` row. `unconfirmed_field` on the Story |
| AT12 | Story, `needed_by` 2026-10-02 op; RESOLVED event at 2026-10-03T01:00Z | At −05:00: `delivered_on` 2026-10-02, `on_time` true. The same board at +00:00: 2026-10-03, false |
| AT13 | Intake ask (`level: unscoped`), `needed_by` 2026-10-02 op | `overdue` row. Not on the roadmap, and in no total |

**Operator override.** Nothing is held, so there is nothing to override. AT9 pins that the contract says so.

**What enforces each rule:**
- **By code, once built:** every row above.
- **By prose only:**
  - 2e's comparison of filed values with the scoping note: CHECKPOINT (1);
  - 4c's clause: each consumer, which can detect its own breach (D41);
  - the `FORECAST:` practice: the session.

## Part F — the seed Epic, and its first scoping (GQ2)

### F.1 The seed Epic, filed now

Use card template 4's Epic form, with these values.

**Filename:**
```
TS-<YYYYMMDD>-venom-<NNN>.000-OPEN__P3__to-venom__for-venom__from-venom__project-tracker-the-trackers-own-build.txt
```

**Header:**
- `origin: operator`, `owner: venom`, `to: venom`, `for: venom`, `priority: P3`.
- `level: epic`, `project: townsquare`, `repo: terrence-adams/townsquare`, `acceptance: yes`.
- `references: BB-20260925-venom-001.000 (evidence)`.
- `next: ip-man's first scoping goes to him after GQ1 - venom`.
- `basis: reported-by operator - approved in BB-20260925-venom-001.000: his "yes, proceed." approved v1 s9, whose step 2 seeds this tracker as its first Epic`.
- `scope: the tracker's own build during the trial. Carries no date and no budget.`
- `subject: project tracker - the tracker's own build (trial seed)`.
- No `needed_by:` and no `budget:`.

**Body:**
- ORIGIN PROOF (TSD s3a, tier 2): `.000` carries his "yes, proceed." (lines 22–23), and its pointer approves v1 §9 (line 36). v1 §9, step 2, reads: "Seed the tracker with this tracker as its first Epic".
- ACCEPTANCE CRITERIA: "The trial's keep-or-remove decision is made, with each trial question answered from real filings on the board." This is proposed by ip-man and put to Sensei at GQ2.
- `DISPATCHES: none yet`.

**Why P3.** P3 is v1 §4's default, because he has stated no priority. GQ2 proposes no change, because the active work sits on the Feature.

### F.2 The first scoping: the scoping event's body

This is posted on the seed Epic's thread as a scoping event (card template 2), after a yes to GQ1. The session slices the text between the markers into the event's body. It is not retyped.

<!-- scoping-seed-epic:start -->
SCOPING NOTE: the tracker's own Epic, its first Feature. ip-man, 2026-09-26.
Source: Part F.2 of ip-man's answer to kano's review, C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md.

1. WHAT I UNDERSTOOD
- His ask: a refinement step that drafts acceptance criteria, sets a budget, and produces a roadmap with milestones and deadlines, to help guide work and priorities. His words are quoted in the extension event on BB-20260925-venom-001.
- This scoping files the work that builds it. It becomes the first Feature under the tracker's own Epic, with one Story per slice.
- The design is the note (sha256 48c18e29…54fc9), as amended by the answer's Part A.

2. QUESTIONS
- None that would change this breakdown.
- His answer to GQ1 decides only which rows carry a budget (see "If milestones only", below).

3. PROPOSED LEVEL AND BREAKDOWN

| Item | Level; parent | Lane (`for:`) | Priority | `needed_by` | Proposed cost, worst case at credit rates |
|---|---|---|---|---|---|
| Budgets, deadlines and a roadmap | feature; the tracker's own Epic | venom | P2 | 2026-10-09 | $70 |
| Slice 1: the roadmap, attention and confirmation, in the projector | story; that Feature | bruce-lee | P2 | 2026-10-02 | $10 |
| Slice 2: the spend tool | story; that Feature | tony-jaa | P3 | 2026-10-09 | $15 |

Total: $95, worst case.

Acceptance criteria:
- **The Feature:**
  - both Stories are RESOLVED;
  - a projector run against the real board shows this Feature's roadmap row, with its date, its planned and spent cost, and its Stories' states. The run is saved with its command and output;
  - helio-gracie's final CHECKPOINT has run.
- **Slice 1:**
  - ronda-rousey's tests for PJ1–PJ11, with CT1–CT10 and AT1–AT13, are committed before the code, and fail as predicted;
  - bruce-lee's commit changes only `tracker\projector.py`;
  - the whole suite passes in a fresh clone, with exit 0;
  - exactly the three named existing tests changed;
  - jackie-chan's review is filed.
- **Slice 2:**
  - ronda-rousey's tests for SP1–SP6 are committed before the code, and fail as predicted;
  - tony-jaa's commit changes only `tracker\spend.py` and the price table;
  - the suite passes in a fresh clone, with exit 0;
  - one SP5 calibration run is saved with its command and output.

Priorities:
- **Slice 1: P2.** It is needed this week, and it blocks no one (TSD §4).
- **Slice 2: P3 for now.** It is needed next week. Raising it when that week starts is his call.
- **The Feature: P2.** It carries this week's reviews and gateways.

Cost basis [inferred; not calibrated]:
- **Rates.** About $5 per large dispatch and $3 per build dispatch, at Opus credit rates (the note, §3.7).
- **The orchestrator's share** is about 40% of each item's total, so each item's dispatch cost is divided by 0.6.
- **The Feature's own work is eight dispatches:**
  - the design, kano's review and this answer;
  - helio-gracie's GAME PLAN and GATEWAY, and his two CHECKPOINTs;
  - jackie-chan's review;
  - ronda-rousey's tests, which are one dispatch serving both Stories, so they sit on the Stories' common parent.

  8 × $5 ÷ 0.6 is about $67, rounded up to $70. The first three dispatches are already spent, and the Feature's opening event lists them.
- **Slice 1:** bruce-lee's build plus one rework dispatch: $6 ÷ 0.6 = $10.
- **Slice 2:** tony-jaa's build and calibration runs ($6), plus one rework dispatch ($3): $9 ÷ 0.6 = $15.
- **Against the note:** its §3.12 said $90, for eight dispatches plus rework. This counts ten dispatches plus two for rework, rounded up per item.

If milestones only (option (b)):
- the Stories carry no budget;
- the Feature carries $95, covering both Stories;
- its budget is filed only after the re-cut (Part A, §3.3).

ROADMAP:
- **Slice 1, due 2026-10-02:** the roadmap with his confirmed dates, this week.
- **Slice 2 and the Feature, due 2026-10-09:** measured spend in the cost column.
- **Why this order:** the dates need only Slice 1; the spend column needs Slice 2.

4. WHAT STAYS OPEN
- **The Epic's own date and budget:** none proposed. Its own work is its Feature's, and its end is his keep-or-remove decision.
- **Everything else:** the note's §4, as amended by the answer.
<!-- scoping-seed-epic:end -->

### F.3 GQ2: draft wording

Asked only after a yes to GQ1, once the scoping event is on the seed Epic's thread:

> The first work under the tracker's own Epic, as ip-man scoped it at <scoping event id>. File it?
> - Feature: budgets, deadlines and a roadmap. P2, due 2026-10-09, $70.
> - Story: Slice 1, the roadmap in the projector. P2, due 2026-10-02, $10.
> - Story: Slice 2, the spend tool. P3, due 2026-10-09, $15.
>
> $95 in all, worst case, estimated and not yet measured. The Epic's own done line: "the trial's keep-or-remove decision is made, with each trial question answered from real filings".
>
> Yes, no, or change any line?

- **Under option (b):** the Stories carry no figure, and the Feature carries $95.
- **After his answer:** it is transcribed on the seed Epic's thread (card template 3), and the three children are filed from that event (card template 4).

```
WORK ORDER — tracker budgets, deadlines and roadmap, as amended by this answer
(replaces the note's work order whole; repo only until Sensei's yes; nothing pushed)
- Document: the session saves this answer beside the note with save_verbatim.py splice. The
  tool reads a SubagentHandback call's message, so the SHA-256 is its own. Commit on internal,
  staging only that path; noreply author; not pushed. Then slice Part D into
  docs\tracker-filing-card.md (commands below), never retyping it.
  — reviewed: the note, by jigoro-kano (c96fce6). This answer stands without a second round, as
    the note's work order provided. One conditional pass: if Sensei chooses option (b) at GQ1,
    ip-man re-cuts PJ7 and PJ9, and jigoro-kano reviews that re-cut once, before any budget test
    is written or any budget: is filed.
- Coordinate: helio-gracie.
  - One dispatch now: the GAME PLAN, then the GATEWAY, which puts two questions to Sensei one
    at a time.
    - GQ1: the extension alone (Part C.1). Its five points must survive any rewording (1c,
      1d). If the session finds "Each story/work item should carry a proposed cost figure" in
      his own message record, GQ1 quotes those words and drops the choice.
    - GQ2: only after a yes to GQ1. The seed Epic's first scoping (Part F.3), in the variant
      GQ1 picked.
    - The GAME PLAN's first Next lines name what the session files now (5d): the .000
      correction (Part C.3), the seed Epic (Part F.1), and the DISPATCHES lines.
    - The GAME PLAN holds every Implement line until GQ1 is answered, because the tests pin
      the readings GQ1 asks him to confirm.
  - Pacing briefs carry roadmap, attention and DoR facts to Sensei as information, never as a
    reason to hold, cut or reorder work (4c; PJ11).
  - CHECKPOINT at named handoffs only:
    (1) after both slices are green and jackie-chan's review is filed. It covers ronda-rousey's
        commit, both builds and the review, and confirms they ran in that order. It also
        compares every child filed since GQ2 with the scoping note's values (2e), and reads
        ronda-rousey's live run (5f).
    (2) the final CHECKPOINT + GATEWAY, before Sensei sees the new dashboard.
    Why only these: ronda-rousey's tests pin every behaviour before any code is written.
- Implement (all after GQ1's answer, except (0) and (4a)):
  (0) ip-man — §3.1's scoping template as amended (a priority beside each date, 3c), from my
      next scoping on. Part F.2 is the first.
  (1) ronda-rousey, first, on internal:
      - tracker\tests\test_budget_roadmap.py: PJ1–PJ11 as amended in Part A, with CT1–CT10 and
        AT1–AT13 (Part E) as fixtures;
      - tracker\tests\test_spend.py: SP1–SP6, with a real multi-block transcript sample and a
        planted fake secret;
      - in test_flags.py, the three fixture edits and the docstring fix Part A §3.5 names,
        and nothing else;
      - a red run at her commit, in a fresh clone, with raw output.
      Under option (b): no budget fixture before the re-cut is reviewed. The rest proceeds.
  (2) bruce-lee, after (1): Slice 1, in tracker\projector.py only; a green run in a fresh
      clone, exit 0.
  (3) tony-jaa, after (1), in parallel with (2): Slice 2.
      - tracker\spend.py plus the price table (its source URL, its retrieval date, and the
        long-context tier if one is published);
      - a green run;
      - one SP5 calibration run over session 3db5d20b-df7f-42a6-b490-ed1667c0117d, and one
        over a Tako Stage B session the session names, each with its command and output saved
        under docs\.
  (4) the session (venom), filing from the card only (Part D):
      (a) now: the .000 correction (Part C.3); the seed Epic (Part F.1); DISPATCHES lines from
          its first event on; the two Requests kano names (a user-record mode for
          save_verbatim.py, 5g; shuri, to measure Q5, 1i);
      (b) after a yes to GQ1: the extension event (Part C.2), with his words extracted from his
          message records, each with its source and SHA-256 (1e), and the thread id and number
          re-checked (1j); then the scoping event on the seed Epic (Part F.2, sliced);
      (c) after a yes to GQ2: the confirmation event on the seed Epic (template 3), then the
          Feature and its two Stories (template 4). budget: only once the extension event is
          filed. The Feature's opening event lists the dispatches already spent on it;
      (d) spent: once SP4 exists, from its output only.
- Peer review: jackie-chan — one pass over both diffs:
  - PJ3's confirmation (CT1–CT10), and the plan value;
  - PJ5 (the offset, delivered_on, undelivered), PJ7, PJ8 and PJ9;
  - SP2's dedupe, and SP4's allocation arithmetic.
  He shows each run's command and raw output, or labels the point "by reading".
- QA: ronda-rousey — tests first for both slices (Implement (1)). Then, once bruce-lee is green
  and the seed Epic is on the board: one Slice 1 run against the real board, in a fresh clone at
  his commit, with the command and output saved under docs\ (5f). helio-gracie delegates any
  green re-run to her.
- Done when:
  (1) the note, kano's review and this answer are saved with their SHA-256s. Every kano finding
      is answered here, and none is declined;
  (2) "deliver stories that trigger a refinement session, drafts acceptance criteria,
      establishes a budget, creates a roadmap with milestones and deadlines": on a fixture board
      holding one scoped ask, the projector's JSON and text show each item's readiness,
      confirmed budgets, confirmed needed_by dates on its milestones, a roadmap in date order
      with days left and planned-against-spent cost, and an attention list. An agent's re-date
      or re-budget shows as unconfirmed, and never moves the value attention measures against;
  (3) "scope budget to actual proposed costs if we have to use credits": budget: and spent: are
      in US dollars at the credit rate; every proposed cost in a scoping note states its basis;
      spent: comes only from SP output; a budget with no spent: shows "spend not measured",
      never a pass;
  (4) each slice's tests were committed before its code and failed as predicted; each
      builder's commit touches only its named files; exactly the three named existing tests
      changed; the whole suite passes in a fresh clone, with exit 0;
  (5) helio-gracie's CHECKPOINTs have run. His answer to GQ1 is recorded (a yes as the extension
      event), and his answer to GQ2 is recorded on the seed Epic's thread. Nothing is pushed;
  (6) a Slice 1 run against the real board, with at least the seed Epic filed, is saved with
      its command and raw output. A flag on a real item is reported as a Q2 finding, not fixed
      in the tests.
- Watch for:
  (a) dropped: 2c is adopted, so a restatement no longer unconfirms a value;
  (b) never estimate spent: by hand. DISPATCHES lines start with the first filed item (5d);
  (c) overdue, over budget and due after parent are attention rows, never flags. Report Q2 by
      flag name, each flag counted from the date it first ran on the real board (4g);
  (d) exactly three existing tests change (Part A §3.5). Any other red is a stop-and-report;
  (e) SP2's dedupe, SP3's unknown-model rule and SP6's no-text rule are where a wrong number or
      a leak would come from;
  (f) session length: start the build in a fresh session, from the note and this answer. Part
      F's cost assumes it;
  (g) the tree is shared: stage only your own paths, never -A or -a. Red and green runs happen
      in a fresh clone. internal carries other sessions' commits, so anyone pushing runs the
      pre-push range check;
  (h) v1's templates are stale: file from the card only. A scoping event carries no level:,
      parent:, project:, repo:, needed_by: or budget: line;
  (i) Wonderland: venom stays the only host filing tracker items. Other hosts' input arrives as
      references;
  (j) the in-flight registry offsite-binding fix is not touched here;
  (k) the trial ends 2026-10-25. Roadmap dates past it survive only if the keep-or-remove
      decision keeps the fields;
  (l) his words come from his message records, with source and SHA-256, never retyped. They
      are never labelled with the word the standing rule reserves for a hash the tool printed
      (1e);
  (m) no consumer holds, cuts or reorders work on a roadmap row, an attention row or a DoR
      reason. The first one that does has made a gate, which needs his adoption under D3 and
      D43 (4a, 4c);
  (n) BB-20260925-venom-001 (this trial) and BB-20260926-venom-001 (claude-app, at .004) differ
      by one digit. Read ts-file.sh's --seen warning before the correction or the extension goes
      on the board (1j);
  (o) budget: and spent: go on the board only after the extension event. needed_by: may be
      filed now, with its s4 meaning (5b);
  (p) the decision-6 job cited .000's early-end line to Sensei as his own precedent
      (helio-gateway-decision6-rework-20260926.md:73). The session raises it at that job's next
      helio-gracie dispatch. This job only files the correction.
- Proposed cost: $95 worst case at credit rates, inferred and not calibrated: the Feature $70,
  Slice 1 $10, Slice 2 $15 (Part F.2). Slice 1 needed_by 2026-10-02; Slice 2 and the Feature
  needed_by 2026-10-09. All are for Sensei's yes at GQ2, and none is in force.
```

## Files

- **To be created (this answer):** `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md`
- **To be created (sliced from Part D):** `C:\Repo\townsquare\docs\tracker-filing-card.md`
- **The design chain:**
  - `C:\Repo\townsquare\docs\kano-tracker-budget-roadmap-review-20260926.md`
  - `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md`
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-design.md` (v1: §4, §8, and §9 line 370)
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md` (the A.4 text, line 202)
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md` (A3)
- **Code and tests:**
  - `C:\Repo\townsquare\tracker\projector.py` (lines 55, 83–112 and 431–445)
  - `C:\Repo\townsquare\tracker\tests\test_flags.py` (lines 33–36, 72–81 and 256–272)
  - `C:\Repo\townsquare\tracker\tests\test_output_contract.py` (lines 66 and 76)
- **Tools:**
  - `C:\Repo\townsquare\registrar\app\filename.py` (lines 8–9 and 21–27)
  - `C:\Users\terre\.local\bin\ts-file.sh` (lines 105–125)
- **The board:** `G:\My Drive\N3rd0m\TownSquare\Bulletin Board\BB-20260925-venom-001.000-OPEN__to-all__impact-informational__from-venom__project-tracker-on-trial-venom-only-not-doctrine.txt` (lines 22–23, 36 and 65–66)
- **Other jobs:**
  - `C:\Repo\townsquare\docs\helio-gateway-decision6-rework-20260926.md` (line 73)
  - `C:\Users\terre\.claude\agents\helio-gracie.md` (lines 118–119)

## Summary

- **Every kano finding is accepted, and none is declined.** 1d and 1f are accepted with an addition.
- **I corrected two errors of my own:**
  - three existing tests change, not two;
  - option (b) needs a re-cut, not just a dropped line.
- **One `.000` summary line misstates the approved early-end rule.** An agent-origin correction is drafted (Part C.3). Another job has already cited that line to Sensei.
- **Ready for helio-gracie's GAME PLAN now.** kano needs a second look only if Sensei chooses option (b).

**Next steps:**
1. The session saves and commits this answer, slices the filing card, and commits the card.
2. The session dispatches helio-gracie: the GAME PLAN, then the GATEWAY, with GQ1 and then GQ2.
3. The session files now: the `.000` correction, the seed Epic, the `DISPATCHES:` lines, and the two Requests.
4. After a yes to GQ1: the extension event and the scoping event are filed, and the Implement lines start.
5. After a yes to GQ2: the confirmation event, then the Feature and its two Stories.

**Requirements:**
- His words are extracted from his message records, each with its source and SHA-256 (1e).
- The extension event's pointer names the SHA-256 on this answer's first line (1b).
- Every `ts-file.sh` warning is read before an event goes on the board (1j).

**Commands.** Run these on Venom, in Git Bash, from the orchestrating session, with no elevation. Nothing is pushed.

```
python C:/Repo/Agentic/tools/save_verbatim/save_verbatim.py splice "<this subagent's transcript .jsonl>" C:/Repo/townsquare/docs/ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md
git -C C:/Repo/townsquare branch --show-current
git -C C:/Repo/townsquare status --short -- docs/
git -C C:/Repo/townsquare add docs/ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md
git -C C:/Repo/townsquare commit --author="<name> <18243588+terrence-adams@users.noreply.github.com>" -m "docs: ip-man answer to kano's review of the tracker budget/roadmap design"
git -C C:/Repo/townsquare show --stat HEAD
```

Then slice the card and commit it:

```
{ printf '<!-- sliced, not retyped, from docs/ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md (sha256 %s), between its filing-card markers -->\n' "<the sha256 splice printed>"; sed -n '/^<!-- filing-card:start -->\r\?$/,/^<!-- filing-card:end -->\r\?$/p' C:/Repo/townsquare/docs/ip-man-tracker-budget-roadmap-answer-to-kano-20260926.md; } > C:/Repo/townsquare/docs/tracker-filing-card.md
git -C C:/Repo/townsquare add docs/tracker-filing-card.md
git -C C:/Repo/townsquare commit --author="<name> <18243588+terrence-adams@users.noreply.github.com>" -m "docs: tracker filing card, sliced from ip-man's answer to kano"
git -C C:/Repo/townsquare show --stat HEAD
```

**Expected results:**
- The branch is `internal`.
- Before its commit, `status` shows the answer as `??`.
- Each `show --stat` lists one file.

**The scoping event's body (4b)** comes from the same slice command, with the `scoping-seed-epic` markers in place of the `filing-card` markers. `internal` carries other sessions' commits, so whoever pushes later runs the pre-push range check first.