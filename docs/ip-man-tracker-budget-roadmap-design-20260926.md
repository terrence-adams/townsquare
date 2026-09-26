<!-- verbatim sha256=48c18e290d4cb62a1befb8f876a03ef1b516c9da13822f7dfdd2016727c54fc9 source=C--Workspace/6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb/subagents/agent-a804a4b2ed579f8a7.jsonl:257 message=msg_011CfSmKh6bwyzZWhbVneo4s -->
# TownSquare tracker: budgets, deadlines and a roadmap, added to the trial

**Author:** ip-man (Dojo architect seat; Claude) · **Date:** 2026-09-26 · **Status:** design note for jigoro-kano's review. Nothing is built, filed or pushed. The new fields are not used on the board until Sensei's yes is recorded (§3.8).

**Path:** `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md`, on branch `internal`, not pushed. The checkout is on `internal` [measured: `.git\HEAD`]. I have no write tool, so the session saves this handback whole (see the work order's Document line).

## Summary

**Question 1: is the acceptance-criteria and scoping-as-refinement design still the operative one? Yes. The decision-6 work did not change it.** Five qualifications (§1.3):
1. **"Required" means reported, not enforced.** A Story without acceptance criteria is flagged as not ready. Nothing is refused.
2. **The mapping to Vertical's `definition_of_done` is not in force.** It is written, but decision 5 was deferred to Vertical Stage 2.
3. **DoR line 4 (Sensei's confirmation) was never built.** v2 approved it. A test docstring misstates it.
4. **v1's template for the scoping event is out of date.** A3 replaced it, and anyone who copies it will file the event wrong.
5. **The trial has not been used.** No tracker item exists anywhere on the board, and neither seed was ever filed.

**Budget, as Sensei defined it** (the session relayed his answer while I worked): US dollars, priced at the rate usage credits are billed. Anthropic bills credits at standard API rates. The budget is a worst-case figure, proposed before the work starts and approved along with the scoping.

**The design, in its smallest form:**
- **The refinement session is the scoping note the trial already runs.** It is extended to propose a cost for every item and a date for every milestone.
- **His one yes per scoping sets those values,** exactly as it already sets level and parent.
- **A deadline is `needed_by:`,** the Town Square Doctrine's own field. **A milestone is an Epic or Feature that carries one.**
- **What gets added:** two header fields, `budget:` and `spent:`, and a roadmap view in the existing read-only projector.

**One piece goes beyond header fields and the projector, and it is needed.** It is a small read-only tool that prices the local transcripts. The board holds no usage data, so neither an honest estimate nor an actual cost can come from the board alone.

**Routing:**
- **No question needs to reach Sensei before review.** He answered the only one himself.
- **The extension goes through Helio's GATEWAY after kano's review,** because it adopts trial text.
- **Scoping and the builds do not wait for his yes** (§3.11).

---

**Labels:**
- *measured*: I read or searched it this run.
- *inferred*: my own derivation, not executed.
- *reported-by X*: X's claim, which I did not re-check.

**Shorthand, defined once:**
- **v1, v2:** `townsquare-project-tracker-design.md` (sha256 `dfb3dc48…02f7`) and `townsquare-project-tracker-design-v2.md` (`954df5dc…642b`). **kano's review:** `townsquare-project-tracker-kano-review.md` (`c7b4f0a4…021eb`). All three hashes are as the trial Bulletin pins them [measured: read on the Bulletin; not re-hashed].
- **The trial Bulletin:** `BB-20260925-venom-001.000`, Sensei's approval of the tracker trial.
- **The ruling, the erratum:** `ip-man-projector-ruling-20260926.md` (rulings R1–R3 on the projector) and `ip-man-projector-ruling-erratum-20260926.md`.
- **A2–A5:** kano's amendments as v2 accepted them. **A3** is the one used most here: Sensei's yes, not the scoping, sets `level:`, `parent:`, `project:` and `repo:`.
- **DoR:** Definition of Ready (v1 §8 as amended by v2). It is a report, never a gate.
- **D‹n›:** operator rulings on the decisions register `BB-20260911-forge-001`. The ones used here:
  - **D1:** posts are never refused.
  - **D3:** no rule without his approval.
  - **D17 A4:** acceptance criteria.
  - **D42:** a threshold needs a named harm.
  - **D43:** a gate needs a window and a disposition; without them it is a report.
- **G3:** a field is carried on the opening event and on any event that changes it, and the newest event carrying it wins.
- **TSD:** the Town Square Doctrine v1.5.
- **Q1–Q4:** the trial Bulletin's four trial questions. Q2 is "do filed items carry the fields correctly, per the projector's own report-only flags".
- **Credit rate:** the price of usage credits. Anthropic's help center says "Usage credits are billed at standard API rates" and that they "apply to both Claude conversations and Claude Code terminal usage" [measured: fetched this run; see Sources].
- **Slice 1, Slice 2:** the projector change (§3.5) and the spend tool (§3.6).
- **PJ1–PJ11, SP1–SP6:** the behaviours in §3.5 and §3.6 that ronda-rousey's tests pin.

**Recusal (Tribunal rule 5, limb (ii)), declared now.** This note answers four questions:
- whether the tracker's acceptance-criteria and scoping design is still operative (the design is my own v1, v2 and ruling);
- how budgets, deadlines and a roadmap are carried;
- who sets them;
- how this work reaches Sensei.

If any of these is referred to the Tribunal, I am conflicted and will not sit.

**Read this run [measured]:**
- **The design chain:**
  - v1, kano's review, and v2 through v5;
  - the ruling and the erratum;
  - jackie-chan's projector review and his review of the ruling;
  - both of helio-gracie's tracker checkpoints;
  - a term search across every other file in `docs\`.
- **The code:**
  - `tracker\projector.py`, in full;
  - `tracker\tests\test_flags.py`, lines 20–49 and 245–309, plus searches of the other test files.
- **The board and doctrine:**
  - the trial Bulletin;
  - TSD §4;
  - searches of the live board.
- **Projects:**
  - `C:\Repo\tako\docs\tako-budget-proposal.md`;
  - the memory files for Tako, Wonderland, cost and pacing.
- **Configuration and tools:**
  - `helio-gracie.md`, for its return blocks;
  - `C:\Users\terre\.claude\settings.json`, by search;
  - the docstring of `save_verbatim.py`.
- **Other code, by search:**
  - the Codex-built Wonderland candidate;
  - Vertical's docs.

## 1. WHAT I UNDERSTOOD

### 1.1 The ask

Sensei's words, as the session relayed them, close to word for word [reported-by session]:

> "deliver stories that trigger a refinement session, drafts acceptance criteria, establishes a budget, creates a roadmap with milestones and deadlines. This should help guide work and priorities."

**Stated back:**
- Every ask he delivers should pass through a refinement step. That step produces acceptance criteria, a cost and dates.
- One view should show each project's milestones in date order, with progress and cost measured against the plan.
- Helio's pacing and Sensei's priorities can then be read from that view.
- Of the five parts in his sentence, two already exist and three are new. He wants this in real use this week, for Tako and Wonderland.

### 1.2 What already stands

**The design is operative, and the decision-6 work did not change it:**
- **v3, v4 and v5** deal entirely with the claude-app pre-registration check. Each says that everything else in v1, v2 and kano's review stands [measured: v3 line 26; v4 line 26; v5 line 23].
- **The rest of the decision-6 chain never touches** Epic, Feature or Story fields, the DoR, or intake. That chain is the registry offsite-binding design and its addendum, the gateways and rechecks, and gsp's and kano's notes on the card.
- **I searched every file in `docs\`** for these terms: "Definition of Ready", "DoR", "scoping note", "story_not_ready", "WHAT I UNDERSTOOD", "no_acceptance", "acceptance: yes" and "refinement". The hits fall only in:
  - v1, v2 and kano's review;
  - the ruling;
  - jackie-chan's projector review;
  - ronda-rousey's fixture note;
  - jackie-chan's registry review, which uses the word "refinements" in its ordinary sense [measured].

| Element | Operative text | Approved by |
|---|---|---|
| Every item carries `acceptance:` from creation (D17 A4) | v1 §4 | the trial Bulletin: "Sections 4-6, 8 and 9 of v1, as amended by v2" |
| The DoR (below the table) | v1 §8; v2 A2 and A3 | the trial Bulletin, with nesting option (b) |
| The DoR is a report | v1 §8; kano's K6 | the trial Bulletin: "Every tracker flag, the Definition of Ready included, is a report only" |
| The scoping note's four parts (below the table) | v2 A4 | the trial Bulletin's INTAKE paragraph |
| One yes per scoping before any child is filed. His yes sets `level:`, `parent:`, `project:` and `repo:` | v2 decision 4; A3; the ruling's reading of the design text | the trial Bulletin: "yes, this solutions works." [sic] |
| Projector behaviour | v1 §6; v2 A5; R1–R3 as the erratum corrects them | shipped at `d1fd2b7`; 67 tests green [reported-by helio-gracie's CHECKPOINT, citing bruce-lee's raw green run] |

**The DoR's four lines.** A Story is ready when:
1. if it has a parent, the parent is a Feature;
2. it carries `acceptance: yes`, with criteria;
3. it has a lane in `for:`;
4. it is confirmed: the event that set its current `level:` carries `origin: operator`.

**The scoping note's four parts:**
1. WHAT I UNDERSTOOD.
2. QUESTIONS. The note stops here if an answer would materially change the breakdown.
3. PROPOSED LEVEL AND BREAKDOWN, with acceptance criteria and a lane for each child.
4. WHAT STAYS OPEN.

### 1.3 Drift and ambiguity found

1. **"Required" means reported, not enforced.**
   - A Story with no acceptance criteria is flagged `story_not_ready`, and nothing is refused (D1, D43).
   - The projector checks only the header marker `acceptance: yes`. It does not look for the criteria in the body [measured: `projector.py:440`].
   - Whether the criteria exist and can be checked is a human check, and it is Helio's.
2. **The `definition_of_done` mapping is written but not in force.**
   - v1 §7's second join maps a Story's acceptance criteria to Vertical's `definition_of_done`.
   - Decision 5 was deferred to Vertical Stage 2. The trial Bulletin also says the trial does not "make the Definition of Ready an entry requirement for Vertical" [measured].
   - Treat the mapping as intent only.
3. **DoR line 4 was approved but never built.**
   - v2 A3 says: "All four DoR lines can now be checked by the projector."
   - The projector checks three. Its own comment says line 4 "is not checked here", because no test pins it [measured: `projector.py:431–433`].
   - `test_flags.py` goes further. It says line 4 is "explicitly named in both design docs as NOT projector-checkable" [measured: lines 33–36]. That is v1's wording, and A3 replaced it.
   - Slice 1 closes this gap (PJ4).
4. **v1's template for the scoping event is out of date, and it is a live filing hazard.**
   - v1 §4 shows the scoping event, `.001-WORKING`, setting `level: epic`, `repo:`, `acceptance:` and `next:`.
   - Under A3, as the ruling reads it, the scoping event keeps `level: unscoped` and sets no structural field. The proposals live in its body.
   - Anyone who copies v1's template files the event wrong.
5. **The trial has not been used.**
   - No file in any board folder, Archive included, has a `level:` or `parent:` header line [measured: a case-insensitive search of `G:\My Drive\N3rd0m\TownSquare`]. The same kind of search does read header content on that mount, because it found `needed_by:` lines.
   - The trial Bulletin names two seeds: "this tracker's own build, as its first Epic; and Revere's next deliverable". Neither was filed.
   - Q1–Q4 have no data. The window runs through 2026-10-25.
   - Nothing blocks filing today.

### 1.4 What is genuinely new

- **A budget.** No file in `docs\` defines one [reported-by session; consistent with my reads]. The one precedent is Tako's budget proposal, which Sensei approved. It sets dollar tranches, estimated by analogy with comparable builds, and calls itself "information to plan against, not a pass/fail gate" [measured].
- **Deadlines: the field is not new, the use is.** TSD §4 already says "P0 and P1 require a needed_by". The board already writes `needed_by: YYYY-MM-DD` on P1, P2 and P3 Requests [measured: TSD line 372; board search]. What is new is reading it as a tracker item's delivery date.
- **Milestones and a roadmap view.** Both are new.

## 2. QUESTIONS

**The stop-here question was what a budget is measured in, and Sensei answered it himself.** His words, as relayed close to word for word [reported-by session]:

> "worst case scenario is paying for tokens because the session has been exceeded. So I like to scope budget to actual proposed costs if we have to use credits."

My reading, which §3 builds on:
- **The unit is US dollars,** not tokens and not time.
- **The price is the credit rate.** Credits are billed at standard API rates [measured], so an item's budget is what its work would cost if every token were paid for as credits.
  - This is the worst case. In practice the subscription covers most of it.
- **The figure is proposed before the work,** and he approves it.
- **It fits Tako's precedent.** Tako's approved budget is already in dollars: $10 for Tranche 1, and a $35–40 starting cap for Tranche 2 [measured].

**Why the note stopped here.** The unit decided two things:
- whether actual cost could be read from the board at all (for any unit except time, it cannot);
- whether a new tool was needed (§3.6).

It no longer blocks anything.

**No other question stops the design.** One reading is confirmed at his yes instead of being asked now:
- **Budgets on every Story.** His words say to scope budgets to proposed costs, but not at which level. The session relays them as "Each story/work item should carry a proposed cost figure" [reported-by session].
- §3 makes that the default through a fifth DoR line (PJ4).
- If he wants budgets only on milestones, that line is dropped and nothing else changes.

**Two questions are not asked, because standing rulings already answer them:**
- **What happens on overspend or a missed date?** It is reported, never enforced.
  - His standing correction of 2026-09-13 is that cost is information unless he states a cost requirement [reported-by memory]. D1 and D43 apply.
  - Claude lets an account set a monthly limit on usage credits [measured: the same help-center article]. That limit, if he has set one, is the only hard stop on cash. The tracker does not duplicate it.
- **Does a deadline change priority?** No. Priority in TSD §4 states expected response, and v1 §4 already keeps pacing out of it.

## 3. PROPOSED DESIGN

In one paragraph:
- **The refinement session is the scoping note the trial already runs.** It is extended to propose a cost for every item and dates for its milestones.
- **Sensei's one yes per scoping sets those values,** as it already sets level and parent.
- **A milestone is an Epic or Feature** that carries a confirmed `needed_by:`.
- **The projector gains a roadmap view and cost totals.**
- **One small read-only tool measures actual cost** from the local transcripts.

### 3.1 The refinement session: the scoping note, extended

- **No new trigger is needed.** Filing an ask with `level: unscoped`, `to: venom` and `for: ip-man` already starts one (v1 §8).
- **Sensei can also file from his phone** through the claude-app card. venom marks that ask `level: unscoped` on receipt (v2 §5, item 11).

The four parts keep their order (A4). What changes:
- **Part 2, QUESTIONS:** the stop rule also covers any answer that would materially change a date or a cost.
- **Part 3, PROPOSED LEVEL AND BREAKDOWN:** each proposed item carries:
  - its level, its parent, and checkable acceptance criteria;
  - its lane (`for:`);
  - a **proposed cost** in US dollars at the credit rate, with its basis (§3.7);
  - a **`needed_by`** date, for each proposed milestone and for any Story that has a real date of its own.
- **Part 3 adds a ROADMAP.** It lists the milestones in date order, says what each delivers, and says why they come in that order. It ends with the total cost of the ask.
- **Part 4, WHAT STAYS OPEN:** unchanged.

**The scoping event itself still carries `level: unscoped` and sets nothing structural** (§1.3, item 4). Proposed costs and dates live in its body, beside the proposed level.

**Owner: ip-man.** This is my own practice, so it takes effect from my next scoping, with no code. Helio's GATEWAY checks the stated basis of each cost, as it checks any other claim.

### 3.2 Deadlines and milestones

**A deadline is TSD §4's own field, `needed_by:`.** On a tracker item it means the date that item is due to be delivered.
- **Value:** `YYYY-MM-DD`, the form the board already uses. A `THH:MMZ` suffix is tolerated, and only the date is used.
- **It follows G3.** It is carried on the event that sets or changes it, and the newest value wins.
- **It changes nothing in TSD §4.** P0 and P1 still require one, and it does not change priority.

**A milestone is an Epic or a Feature with a confirmed `needed_by:`.** There is no new level and no new field.
- Tako and Wonderland are already organised in phases:
  - **Tako:** Phase 1, which contains Stage A (closed) and Stage B, whose wave 4D was frozen on 2026-09-25. Phase 2 is designed but not started [reported-by memory; measured: `tako-phase1-wave4d-freeze-qa.md`].
  - **Wonderland:** Phase 0 onward.
- Their Epics and Features therefore already form the timeline.

**"Delivered" means RESOLVED.** That is, QA has passed and Helio's final CHECKPOINT has run (v1 §8). CLOSED is Sensei's closing ceremony and does not move the delivery date.

### 3.3 Budget

**`budget:` is the proposed cost of the item's own work, not its children's.**
- For example, an Epic's own budget covers scoping and coordination. A Story's covers its dispatches.
- **Value:** `<amount> usd`, with at most two decimals, priced at the credit rate.

**`spent:` is the measured cost of the item's own work to date.** It is cumulative, and the newest value wins (G3).
- **The session writes it** on the CHECKPOINT event it already appends, the one that updates `next:`.
- **It comes only from the spend tool's output** (§3.6). It is never estimated by hand, because a guessed actual would look measured.
- **Until the tool exists, `spent:` is absent.**

**Totals are derived, never typed.** An item's planned total is its own figure plus its children's totals, and the same goes for spent.
- **Why "own work only":** every dollar has exactly one home.
- No parent restates a child's figure, so nothing can be counted twice. And there is no "the children add up to more than the parent" inconsistency to police.
- It is the same reason children point up to their parents in v1 §4.

**Where the refinement's own cost lands.** The scoping dispatch works on the ask's thread, and that thread becomes the Epic (v1 §8). So the cost of scoping is the Epic's own spend.

**Recording starts on day one.** Every CHECKPOINT event on a tracker item lists, in its body, the dispatch ids that served the item since the previous event. The line reads `DISPATCHES:` followed by the agent ids.
- **Measurement can then be backfilled without losing anything.** Venom keeps transcripts for 365 days (`cleanupPeriodDays: 365`) [measured: `C:\Users\terre\.claude\settings.json`].

### 3.4 Commitments are set by his yes (A3, extended)

**`level:` (except `unscoped`), `needed_by:` and `budget:` are commitments.**
- **A commitment is confirmed** when the event that supplied its current value carries `origin: operator`. That event is either:
  - his transcribed yes; or
  - a child he confirmed by name, filed with `references:` pointing to that yes (v2 A3's tier-2 rule).
- **Re-planning** (a slipped date, a raised budget) is a new event carrying `origin: operator` and his words.
- **`spent:` is a measurement, not a commitment.** The session writes it with `origin: agent`.

**Why:**
- **In the design this tracker feeds,** deadlines and acceptance are the project owner's call. Vertical's build spec marks `deadline` and `acceptance` decisions "Project-owner only" [measured: `poc-build-spec.md:1407`].
- **It adds no approvals.** The same one yes per scoping sets these values.

**What the projector checks:** only that the `origin: operator` marker is present. Whether a yes is genuine is left to people, as TSD §2 has it. That is the same split as kano's clause C5, where the presence of proof is checkable but its genuineness is not.

### 3.5 Slice 1: the projector's roadmap (tests pin PJ1–PJ11)

All of this is read-only and lives in `tracker\projector.py`.

- **PJ1. Reading.**
  - `needed_by`, `budget` and `spent` are read on tracker items only, under v2 A5's header rules.
  - A key repeated within one header is flagged `duplicate_header_key` and ignored, so an earlier clean value stands. This is the rule the five existing fields follow.
  - `origin` is read on every event. If it is missing or repeated, it counts as "not operator".
- **PJ2. Validity.**
  - A newest value that breaks the grammar in §3.2 or §3.3 is flagged `invalid_value`, with the field, the value and the event.
  - The invalid value has no effect, and the projector does not fall back to an earlier value. The precedents are R1 and `invalid_level`.
- **PJ3. Confirmation.**
  - For each of `level`, `needed_by` and `budget`, each node shows the event that supplied the value and whether that event is confirmed.
  - An unconfirmed `needed_by` or `budget` is flagged `unconfirmed_commitment`.
- **PJ4. DoR.** `story_not_ready` gains two reasons:
  - `level_unconfirmed`: DoR line 4, from A3. It is already approved, and it is built here.
  - `no_budget`: a new line 5, "the Story carries a valid `budget:`".

  Whether a budget is confirmed stays PJ3's flag, not a DoR reason, so Q2 never counts one error twice.
- **PJ5. Deadline status.** This is a status, not a flag.
  - **The reference date** is a parameter, `as_of`, which defaults to today's UTC date.
  - **Open items get `days_left`.** It is negative when the item is overdue.
  - **RESOLVED or CLOSED items get `delivered_on` and `on_time`.** `delivered_on` is the date the item last entered RESOLVED or CLOSED from another state, using the projector's existing event time.
  - **CANCELLED items get no deadline status.**
  - **`needed_by_first`** is the first valid date the thread ever carried. It is shown whenever it differs from the current date, so slips stay visible.
- **PJ6. `deadline_after_parent`.** A flag on a placed child whose `needed_by` falls after its parent's.
- **PJ7. Totals.**
  - `budget_total` and `spent_total` are each node's own figure plus the totals of its placed children.
  - `unbudgeted` counts placed descendants with no valid budget.
  - Every state counts, cancelled included. Money spent on cancelled work is real, and its budget was part of the approved plan.
  - Intake items and unplaced items count toward nothing.
- **PJ8. `result["roadmap"]`.** It is grouped per project, plus a `(no project)` bucket.
  - **`milestones`** lists the Epics and Features with a valid `needed_by`, sorted by date and then by id.
  - Each row carries:
    - the id, level, subject and state;
    - `needed_by`, plus `needed_by_first` if it differs;
    - the confirmation;
    - the PJ5 status;
    - the direct children's state counts;
    - `budget_total`, `spent_total` and `unbudgeted`;
    - `next`.
  - **`unscheduled`** lists the ids of each project's undated Epics and Features. A roadmap that silently dropped undated work would mislead.
  - Intake items are excluded.
- **PJ9. `result["attention"]`.** It lists overdue open items, and items whose own `spent` exceeds their own `budget`.
  - **These are not flags.** Q2 counts flags as filing errors, and these are status. Keeping them apart keeps Q2's counts comparable before and after this change, which is the reason the ruling's §4 gave for landing its fixes before any flag fired.
  - **D42 is met.** The threshold is his own confirmed number, and the harm is a date missed or money overspent against a plan he approved, without his seeing it.
- **PJ10. Rendering.**
  - The text output starts with ROADMAP, one line per milestone, then ATTENTION, then the existing sections.
  - Tree lines gain `due …` and `cost $planned / $spent` where those exist.
  - The command line gains `--as-of YYYY-MM-DD`, for deterministic tests.
  - The session renders the JSON as Sensei's graphical dashboard, as v1 §6 already has it do. There is no new UI.
- **PJ11. Contract.** The roadmap and attention lists come under the existing output contract: a current-state view that is not monotone and is never used for routing, notification or receipt. The contract's statement names both lists.

**Existing tests: exactly two change.** They are the two "ready Story" tests at `test_flags.py:256–272`.
- Under PJ4, their Stories would be flagged, because the fixtures have no `origin: operator` and no budget.
- **ronda-rousey adds both to those two fixtures.** Each test keeps its meaning: a Story that meets every DoR line is ready.
- **She also corrects the docstring at lines 33–36** to cite A3 and this note.
- **Any other existing test that goes red is a surprise:** stop and report it; never edit it. This rests on reading the file and searching `tracker\tests` for `story_not_ready` [inferred]. Her red run confirms it.

### 3.6 Slice 2: measuring cost (tests pin SP1–SP6)

**This is the one piece beyond header fields and the projector, and it is needed:**
- **The board holds no usage data,** so neither an honest proposed cost nor an actual cost can be derived from the ledger.
- **The only per-dispatch record of cost is the transcripts on Venom.** Subagent transcripts carry per-message token usage. One session alone has 3,221 lines with usage fields, across 45 subagent files [measured, by search].
- **It is not infrastructure.** It is one standard-library, read-only command-line tool over local files, in the same class as the projector. There is no service, and nothing changes in the Registrar or the Crier.

**`tracker\spend.py` must meet six behaviours:**
- **SP1. Input.** Either transcript paths, or `--session <id>`, which expands to that session's main transcript plus its `subagents\` folder.
- **SP2. Count each API response once,** by message id, across every file given.
  - One response can be written as several lines [inferred from how Claude Code writes transcripts]. ronda-rousey pins this with a real sample that has several blocks.
  - Counting a response twice would silently inflate every budget.
- **SP3. Price each message** by its model and token class: input, output, 5-minute cache write, 1-hour cache write and cache read.
  - The prices come from a price table checked into the repo. The table records its source URL and the date it was retrieved.
  - If the pricing page publishes a long-context tier, the table carries it.
  - A model missing from the table is reported as unpriced, and the total is marked incomplete. Its price is never guessed.
- **SP4. `--group <item-id>=<agent-id>,…`.**
  - Each group gets its own subagent cost, plus a share of the orchestrator's cost (the main transcript's cost). The share is in proportion to subagent cost within that session.
  - Subagents not named in any group form an `unassigned` group, so the shares add up to the session total.
  - The allocation is labelled as an allocation, not a measurement.
  - It matters because Revere's retrospective put orchestrator overhead at about 39% of total spend [reported-by `tako-budget-proposal.md`].
- **SP5. `--by-agent`, for calibration.** It reports per-dispatch cost (the count, the median and the maximum) keyed by the name of the agent dispatched. The name is read from the main transcript's Agent calls, or the agent id is used where the name cannot be read.
- **SP6. Numbers and ids only.** The tool never prints transcript text, because transcripts can hold secrets. A fixture with a planted fake secret pins this.

**Why measured cost matters:**
- **It calibrates the estimates.** Running SP5 over existing sessions turns §3.7's analogies into measured per-dispatch costs.
- **It answers a live Tako question.** The same run can report what Tako's Stage B has actually cost against its approved $35–40 cap for Tranche 2. Nobody knows that figure today [inferred: no spend is recorded anywhere].

### 3.7 How a proposed cost is estimated

- **Worst case:** every token priced at the credit rate.
- **Per item:** the planned dispatches, times each agent's per-dispatch cost, plus the orchestrator's share.
  - **Until SP5 runs,** per-dispatch costs come from analogy with reported builds of similar size, which is how Tako's budget was made. They are labelled *inferred*.
  - **Until SP4 measures it,** the orchestrator's share is taken as about 39%.
- **The assumptions each estimate states.** They rest on the fleet's own measurements, not on a new model:
  - **Model:** Opus, unless the work order names a cheaper one. The model tier is the largest lever. The same cached context cost about 6 times as much on the Opus 1M-context tier as on Haiku [reported-by memory: measured on Forge, 2026-09-05].
  - **Cache:** one cold start per dispatch. Cache writes carry the cost; a warm run was 12.7 times cheaper than a cold one [same source].
  - **Session length:** one bounded session per Story. Cost grows faster than session length does, because every turn re-reads the whole context (the 2026-09-24 lesson in memory). A Story that needs several sessions says so and is priced per session.
- **A worked basis** [inferred]:
  - **The anchor:** the Forge measurement priced 53,817 cache-write tokens on `claude-opus-5[1m]` at $0.539. That is $10 per million tokens.
  - **The other rates:** the usual ratios then give $5 per million for input, $0.50 for cache reads and $25 for output.
  - **A large review dispatch** (about 40 turns over an average context of about 120,000 tokens) comes to about $4–6.
  - **A focused build or test dispatch** comes to about $3.
  - tony-jaa confirms the table against the pricing page (SP3).

### 3.8 Recording the extension (D3)

**His yes is needed before the new fields are used on the board.** The trial Bulletin approved five fields and the text of v1 and v2. These are additions:
- the `budget:` and `spent:` fields;
- the confirmation rule;
- DoR line 5;
- the roadmap view.

**The session appends one event to the trial Bulletin, in the shape of kano's A.4 draft.** kano reviews this draft together with the note. His words must be copied exactly from his own message record. The session's relay to me was close to word for word, which is not exact. save_verbatim.py extracts assistant messages only [measured: its docstring, lines 55–58].

```
BB-20260925-venom-001.001-OPEN__by-venom__trial-extended-budgets-deadlines-roadmap-operator-approved-not-doctrine.txt

id:          BB-20260925-venom-001
event:       001
state:       OPEN
host:        Venom
name:        venom
origin:      operator
to:          all
impact:      informational
basis:       reported-by operator - his words below; the design note read at the SHA-256 below
scope:       extends the tracker trial on venom's own Requests with budget:, spent:, a delivery-date use of needed_by:, and a roadmap view. Adopts no doctrine. Asks nothing of any other host.
at:          <UTC from date -u>
subject:     ON TRIAL - tracker items may also carry needed_by (as a delivery date), budget and spent. Operator-approved for trial. Not doctrine.
---
HIS WORDS (TSD s3a, tier 1), copied exactly from his messages:
  the ask:       <"deliver stories that trigger a refinement session...">
  the unit:      <"worst case scenario is paying for tokens...">
  the approval:  <his yes to this extension>

WHAT THOSE WORDS APPROVE, by pointer:
  C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md, branch internal,
  sha256 <...>, section 3, for trial on venom only, inside this trial's window.
  Every line below that is not his is that note's text, approved for trial. None of it is his
  ruling, and none of it is doctrine.

WHAT YOU WILL SEE: venom's tracker items may carry needed_by: (TSD s4's field, used here also as
  a delivery date), budget: and spent: (US dollars at the rate usage credits are billed). They
  route nothing; the Crier ignores them (TSD s9).
WHAT YOU MUST DO: nothing. No other host is asked to carry them.

WHAT THIS DOES NOT DO:
  - amend the Town Square Doctrine, or change s4: P0 and P1 still require a needed_by, and a
    needed_by does not change priority
  - stop, park or refuse any work that is over budget or past its date. Both are reported, never
    enforced (D1, D43). Any cash limit is the one on his own Claude account, not here.
  - change the Crier, the Registrar, the filename grammar or Vertical

TRIAL: unchanged - owner venom, window through 2026-10-25. The keep-or-remove decision at its end
  covers these fields too.
```

The Bulletin holds only `.000` today [measured: glob], so `.001` is the next number. Re-check that at filing time.

### 3.9 Consumers

These are listed because the standing ruling on shape changes requires it.

**`needed_by:` keeps its shape.** Its current consumers:
- **TSD §4's P0/P1 rule:** unchanged.
- **kano's claude-app card:** unchanged.
- **The Codex-built Wonderland Charter candidate.** Its rule R2 checks only that P0 and P1 Requests carry the field; "P2/P3 or non-requests are not_applicable" [measured: `C:\Users\terre\Documents\Codex\2026-09-09\ww\outputs\wonderland\audit_pilot.py:18` and `engine\full_evaluate.py:82–85`].
  - It is not deployed.
  - A future check of whether dates were honoured would also audit roadmap dates, which is the intent.
- **No code under `C:\Repo` reads it** [measured: search].
- **The projector is the one new consumer.**

**`budget:` and `spent:` are new.**
- No header on the board uses either key.
- No TownSquare or Vertical code reads them [measured: board search; search of `C:\Repo`].
- The projector is their only consumer.

**Priority** is untouched.

### 3.10 Alternatives rejected

| Option | Why not | What would change my mind |
|---|---|---|
| A `milestone:` label: releases that cut across Epics | It adds a second axis. A Story would be placed in two ways, and each milestone's date would need a third home. Projects organised in phases do not need it. | A real Tako or Wonderland milestone that needs Stories from two Features |
| `level: milestone` | It breaks the three-level nesting he approved, and changes the set of levels the projector validates | None foreseen |
| A new `due:` field | It duplicates TSD §4's `needed_by:`, which is already doctrine, already in use, and already what the Wonderland candidate reads | None |
| A roadmap document (ROADMAP.md or a Drive doc) | It is a second source of truth for dates, and invites the stale-status failure Vertical's README warns about | None |
| Parent budgets that include their children | Double counting, and a consistency rule to police | He wants a parent's cap shown apart from the sum of its children |
| `spent:` estimated by hand until the tool exists | A guessed actual reads as measured. A blank is honest, and backfilling loses nothing because transcripts are kept 365 days | None |
| Overspend or lateness as a gate | It would be an inferred cost gate: he stated a budget, not a stop | He says overspend should stop work. That becomes a gate with a window and a disposition (D43), which he adopts under D3 |

### 3.11 Routing: Helio before Sensei, or straight to him?

- **No open question needs to reach him now.** He answered the only stop-here question himself.
- **The extension yes (§3.8) goes through Helio's GATEWAY after kano's review.** It adopts trial text under D3, and a D3 wording error is exactly the risk the GATEWAY exists to catch. One Helio dispatch can run both the GAME PLAN and that GATEWAY.

**So the week is not run step by step in sequence:**
- **Scoping can start now, under the mechanism already approved.**
  - Asks go to intake.
  - My scoping notes carry proposed costs and dates in their bodies. That is a change of practice and needs no approval.
  - His scoping yes can set `needed_by:` straight away, because it is an existing TSD field.
  - When to scope Tako and Wonderland is Helio's call on pace.
- **The builds do not wait for his yes.** They touch only the repo and nothing live. They start after kano's review and Helio's GAME PLAN.
- **Only the board use of `budget:` and `spent:`, and the confirmation rule, wait for his yes.**

**Expect Wonderland's first scoping to stop at QUESTIONS.** That is the refinement step working as designed. The reasons [reported-by memory]:
- Phase 0 has been stalled since 2026-09-10, waiting on a non-Claude review assigned to venom's Codex seat.
- Three baselines have not been reconciled: Cable's accepted v0.6, Bishop's local-build review, and the Codex-built V1 candidate.

**Wonderland's work involves other hosts,** so venom stays the only host that files tracker items. If another host needed to file tracker items, the trial would end early (v1 §9).

### 3.12 This work's own proposed cost and dates

These figures are the dogfood run. After his yes, this work is filed as a Feature under the seed Epic that was never filed, and the GATEWAY puts these figures to him with the extension.

- **Cost:** $90 worst case [inferred; not calibrated]. The basis:
  - eight dispatches at $4–6 each, at Opus credit rates;
  - a share of about 40% for the orchestrator;
  - headroom for one round of rework;
  - on the assumption that the build runs in a fresh session started from this note.
- **Dates:**
  - Slice 1: `needed_by: 2026-10-02`, so it is usable this week.
  - Slice 2: `needed_by: 2026-10-09`, or sooner if Helio's pace allows.
- **These are the first estimates SP4 will check.**

## 4. WHAT STAYS OPEN

Every item below is owned by ip-man unless it names another owner.

- **How finely to budget.** The default is every Story (DoR line 5). He confirms it at his yes; if he wants budgets on milestones only, the line is dropped.
- **Epic rows on the roadmap count only their direct children,** which are Features. Counting the Stories beneath them waits for a real case.
- **Out of scope: how likely the work is to actually spill into credits,** given how much of his weekly window is left. The budget is the worst case.
- **Out of scope: running-cost budgets,** such as Wonderland v0.6's $45 a month. Those belong in a deployed service's own configuration.
- **No Spend or roadmap line in helio-gracie's blocks during the trial.** Following the 2026-09-24 lesson, the session hands him the roadmap and cost facts in each pacing brief. The post-trial amendment decides whether to add a line, and changing his agent file needs its own review.
- **Deferred:**
  - **The post-trial doctrine amendment** (kano drafts it) now covers these fields too.
  - **Carrying `needed_by`/`budget` in Vertical's entry contract** waits for Stage 2, along with decision 5.
- **Carried over unchanged:**
  - the backlog in the ruling's §6, plus the erratum's additions;
  - my own `project:` slug item;
  - the F7 caveat that event time is the file's modification time, which PJ5's `delivered_on` inherits.

```
WORK ORDER — tracker budgets, deadlines and roadmap (extends the live trial; repo only until Sensei's yes; nothing pushed)
- Document: the session saves this handback whole with
  python C:\Repo\Agentic\tools\save_verbatim\save_verbatim.py splice <this subagent's transcript>
  C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md
  (the tool now reads a SubagentHandback call's message [measured: its docstring, lines 47–70], so
  the SHA-256 is its own). Commit on internal, staging only that path; noreply author; not pushed.
  — reviewed by jigoro-kano before any Implement line, in one pass, together with §3.8's draft:
    (1) §3.8's D3 vehicle and wording;
    (2) §3.4 as an extension of A3;
    (3) reusing needed_by against TSD s4, including whether a confirmed delivery date sits with P3's
        "No commitment";
    (4) PJ9's attention rows as reports under D42/D43, with no inferred cost gate;
    (5) his own concerns.
    If he raises any, the session resumes ip-man once; that answer is saved beside this note and
    stands.
- Coordinate: helio-gracie.
  - One dispatch after kano's review: GAME PLAN (both slices; pace; whether Slice 2 runs this week)
    plus the GATEWAY that puts §3.8's extension and §3.12's figures to Sensei as one yes or no.
  - CHECKPOINT at named handoffs only, to hold cost down:
    (1) one after both slices are green and jackie-chan's review is filed. It covers ronda-rousey's
        commit, both builds and the review, and confirms they ran in that order;
    (2) the final CHECKPOINT + GATEWAY before Sensei sees the new dashboard.
    Why only these: ronda-rousey's tests pin every behaviour before any code is written.
- Implement:
  (0) ip-man — §3.1's scoping template, from my next scoping on (practice; no code).
  (1) ronda-rousey, first, on internal:
      - tracker\tests\test_budget_roadmap.py (PJ1–PJ11);
      - tracker\tests\test_spend.py (SP1–SP6, with a real multi-block transcript sample and a
        planted fake secret);
      - the two fixture edits and the docstring fix in test_flags.py (§3.5), and nothing else;
      - a red run at her commit, in a fresh clone, with raw output.
  (2) bruce-lee, after (1): Slice 1, in tracker\projector.py only; a green run in a fresh clone,
      exit 0.
  (3) tony-jaa, after (1), in parallel with (2): Slice 2.
      - tracker\spend.py plus the price table (source URL and retrieval date; the long-context tier
        if one is published);
      - a green run;
      - then one SP5 calibration run over session 3db5d20b-df7f-42a6-b490-ed1667c0117d (the R1–R3
        pass) and one Tako Stage B session the session names, with the output and its command saved
        under docs\.
  (4) the session (venom), only after Sensei's yes:
      - file §3.8's event, with his words copied exactly;
      - file the seed Epic, and this work as its Feature, with §3.12's figures;
      - from then on, write DISPATCHES on every CHECKPOINT event, and spent: once SP4 exists.
- Peer review: jackie-chan — one pass over both diffs: the derivation in PJ5, PJ7 and PJ8; SP2's
  dedupe; SP4's allocation arithmetic. Show each run's command and raw output, or label the point
  "by reading".
- QA: ronda-rousey — tests first for both slices (Implement (1)). helio-gracie delegates any green
  re-run to her, in a fresh clone.
- Done when:
  (1) the note is saved with its SHA-256; kano's review is filed; each concern is answered, or
      reaches Sensei as dissent in kano's words;
  (2) "deliver stories that trigger a refinement session, drafts acceptance criteria, establishes a
      budget, creates a roadmap with milestones and deadlines": on a fixture board holding one
      scoped ask, the projector's JSON and text show each item's readiness, a confirmed budget,
      confirmed needed_by dates on its milestones, a roadmap in date order with days left and
      planned-against-spent cost, and an attention list;
  (3) "scope budget to actual proposed costs if we have to use credits": budget: and spent: are in
      US dollars at the credit rate; every proposed cost in a scoping note states its basis; spent:
      comes only from SP output;
  (4) each slice's tests were committed before its code and failed as predicted; each builder's
      commit touches only its named files; the whole suite passes in a fresh clone with exit 0;
  (5) Helio's CHECKPOINT has run; Sensei's yes or no on §3.8 is recorded; nothing is pushed.
- Watch for:
  (a) never restate needed_by: or budget: on an event that does not change it. An agent event that
      restates one flips it to unconfirmed (G3: carried on change);
  (b) never estimate spent: by hand; record DISPATCHES from day one instead;
  (c) overdue and over-budget are attention rows, never flags, or Q2's counts stop being comparable;
  (d) only the two named tests in test_flags.py change; any other red is a stop-and-report;
  (e) SP2's dedupe, SP3's unknown-model rule and SP6's no-text rule are where a wrong number or a
      leak would come from;
  (f) session length: start the build in a fresh session from this note. §3.12's cost assumes it,
      and session length is the overage mechanism he named;
  (g) the tree is shared: stage only your own paths, never -A or -a; red and green runs happen in a
      fresh clone; internal carries other sessions' commits, so anyone pushing runs the pre-push
      range check;
  (h) v1 §4's template for the scoping event is out of date (§1.3, item 4): the scoping event keeps
      level: unscoped and sets no commitment field;
  (i) Wonderland: venom stays the only host filing tracker items; other hosts' input arrives as
      references;
  (j) the in-flight registry offsite-binding fix (Wonderland repo, serving decision 6) is not
      touched here; which project it is filed under is for the backlog step;
  (k) the trial ends 2026-10-25: roadmap dates past it survive only if the keep-or-remove decision
      keeps the fields;
  (l) his words in §3.8 are copied from his own message record, not from a relay;
      save_verbatim.py extracts assistant messages only.
- Proposed cost: $90 worst case at credit rates, inferred and not calibrated (§3.12). Slice 1
  needed_by 2026-10-02; Slice 2 needed_by 2026-10-09. Both are for Sensei's confirmation and are
  not in force.
```

## Files

- **To be saved (this note):** `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md`
- **The design chain:**
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-design.md`
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md`
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md`
  - `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v3.md` (and `-v4.md`, `-v5.md`, confirmed not to touch this)
  - `C:\Repo\townsquare\docs\ip-man-projector-ruling-20260926.md`
  - `C:\Repo\townsquare\docs\ip-man-projector-ruling-erratum-20260926.md`
- **Code and tests:**
  - `C:\Repo\townsquare\tracker\projector.py` (lines 431–433 and 440)
  - `C:\Repo\townsquare\tracker\tests\test_flags.py` (lines 33–36 and 256–272)
- **The trial Bulletin:** `G:\My Drive\N3rd0m\TownSquare\Bulletin Board\BB-20260925-venom-001.000-OPEN__to-all__impact-informational__from-venom__project-tracker-on-trial-venom-only-not-doctrine.txt`
- **Doctrine:** `G:\My Drive\N3rd0m\TownSquare\TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt` (§4, line 372)
- **Tako:** `C:\Repo\tako\docs\tako-budget-proposal.md`
- **Vertical:** `C:\Repo\vertical\docs\poc-build-spec.md` (line 1407)
- **Wonderland candidate:** `C:\Users\terre\Documents\Codex\2026-09-09\ww\outputs\wonderland\audit_pilot.py` (line 18)
- **Tooling and settings:**
  - `C:\Repo\Agentic\tools\save_verbatim\save_verbatim.py` (docstring, lines 47–70)
  - `C:\Users\terre\.claude\settings.json` (`cleanupPeriodDays: 365`)

## Sources

- [Manage usage credits for paid Claude plans, Claude Help Center](https://support.claude.com/en/articles/12429409-manage-extra-usage-for-paid-claude-plans). This is the primary source, fetched this run: credits are billed at standard API rates, apply to Claude Code, and can be capped monthly.
- Search results consulted, which agree with it:
  - [Claude Extra Usage in 2026 (agentshortlist)](https://agentshortlist.com/articles/claude-extra-usage)
  - [Claude Pricing 2026 (mem0)](https://mem0.ai/blog/anthropic-claude-pricing)
  - [Claude Code Rate Limits & Usage Quotas Explained (truefoundry)](https://www.truefoundry.com/blog/claude-code-limits-explained)