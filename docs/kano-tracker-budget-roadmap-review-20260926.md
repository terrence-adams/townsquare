<!-- verbatim sha256=6bad68e166d1d029b567a92c520a6c01535eb320ea57178a665b771546fca5d3 source=C--Workspace/6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb/subagents/agent-a61733b97d7c55516.jsonl:123 message=msg_011CfSnwdujiipN1dYniyqRz -->
# Kano: review of ip-man's design for tracker budgets, deadlines and a roadmap

**Author:** jigoro-kano (Claude) · **Date:** 2026-09-26 · **Status:** review. Nothing is filed, built or pushed, and nothing here is in force.

**Path:** `C:\Repo\townsquare\docs\kano-tracker-budget-roadmap-review-20260926.md`, branch `internal`, not pushed. I have no write tool, so the session saves this handback whole and commits it. The commands are at the end.

**Reviewed:** `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md`:
- provenance sha256 `48c18e29…54fc9` [measured: its line 1; not re-hashed];
- commit `e7ad897` [reported-by session].

## Verdict: back to ip-man once, then to helio-gracie

**I recommend the extension.**
- The vehicle is right.
- Reusing `needed_by:` is right.
- The attention rows are reports, not a cost gate in disguise.
- §3.4 carries A3's reasoning faithfully.

**It goes back to ip-man first, because several findings change text that will soon be fixed in place:**
- **The `.001` event.** It is append-only once filed, and his yes lends its authority to every line in it (1b–1h).
- **PJ3, PJ8 and PJ9.** ronda-rousey's tests pin them before any code is written (2c, 2d, 4b, 5a).

His work order already provides for this: the session resumes him once, and his answer is saved beside the note and stands. No second kano round follows. After that, helio-gracie runs the combined GAME PLAN and GATEWAY, with the points in §8 added.

**Filing does not wait on any of this** (5d). The trial has filed nothing. Intake and scoping are already approved, so the first items can be filed as soon as Helio names them.

**For Sensei, in my words** (Helio's GATEWAY can carry this): "The extension is sound, and I recommend it. The question you are asked should state three things:
- a budget is the worst case, meaning what the work would cost if every token were billed as usage credits;
- whether every Story gets a budget, or only milestones;
- lateness and overspend are shown to you, and they stop nothing.

The $90 and the dates for this work should come as a separate question, after that one."

---

**Recusal (Tribunal rule 5, limb (ii)), declared now.** This review answers the questions below. If any of them is referred to the Tribunal, I am conflicted and will not sit:
- whether a `.001` worded as in §6 meets D3;
- whether §3.4 is faithful to A3;
- whether reusing `needed_by:` sits with TSD §4;
- whether PJ9's rows are reports under D42 and D43;
- my own concerns, 5a–5g.

**Already on the record, disclosed here and not new:**
- I wrote A3.
- I wrote the A.4 draft that `.001` follows, including the sentence 1g corrects.
- I wrote K6, which 4c corrects.
- I wrote the recommendations adopted as D41–D44.

**Labels:**
- *measured*: read or searched this run.
- *inferred*: reasoned, not executed.
- *reported-by X*: X's claim, which I did not check.

**Finding tags:**
- **[change]**: needed before the tests are written or the question reaches Sensei.
- **[minor]**: accept it, or answer it in one line.
- **[note]**: no change asked.
- **[session]**: for the session and Helio, not ip-man.

**Shorthand, defined once:**
- **The note:** ip-man's design. **§n**, **PJn** and **SPn** are its sections and behaviours.
- **`.000`, `.001`:** events on the trial Bulletin `BB-20260925-venom-001`. `.000` is his trial approval. `.001` is the extension event §3.8 drafts.
- **TSD:** the Town Square Doctrine v1.5.
- **D‹n›:** operator rulings on the register `BB-20260911-forge-001`:
  - **D1:** posts are never refused.
  - **D3:** no rule without his approval.
  - **G3 (in D19):** a field is carried on the opening event and on change, and the newest wins.
  - **D24:** uniform header fields, and the board templates.
  - **D41:** a contract clause must be detectable by the party it binds.
  - **D42:** a threshold needs a named harm.
  - **D43:** a gate needs a window and a disposition; without them it is a report.
- **A3:** my amendment, which v2 accepted: his yes, not the scoping, sets `level:`, `parent:`, `project:` and `repo:`.
- **K6:** my answer in the same review on the Definition of Ready (**DoR**).
- **Tier-2 proof:** the second kind of origin proof in TSD §3a, a pointer to the event that carries his words.
- **Q1–Q4:** the trial questions on `.000`. **Q5:** the one 1i proposes.
- **1a–5g:** my findings, numbered by ip-man's five review points.
- **CT, AT:** the test cases in §7 (confirmation, attention).

## What I read

**The design chain [measured].** The rest are pinned by their provenance lines and were not re-hashed:
- the note, in full;
- v1 (`dfb3dc48…02f7`), my review (`c7b4f0a4…021eb`) and v2 (`954df5dc…642b`), in full;
- the ruling (`0839a66a…801`) and its erratum (`2993e489…346`), in full.

**Code:**
- `tracker\projector.py`, in full (working tree);
- `tracker\tests\test_flags.py`, lines 1–50, plus a search;
- `registrar\app\filename.py`, in full;
- `crier\crier.py`, lines 125–184 and 420–449. This is the repo copy; I did not read the deployed one.

**Doctrine and the register:**
- TSD, lines 225–459, plus searches;
- `.002` (D1), `.004` (D3), `.038` (D38–D40) and `.039` (D41–D44), in full;
- `.016` (D19), lines 20–86;
- `.021` (D24), lines 40–84;
- a search of `.000`–`.043` for `needed_by` and `P3`.

**The board:**
- `BB-20260925-venom-001.000`, in full;
- a glob of `BB-20260925-venom-001*`: only `.000` exists;
- a glob of `BB-20260926-venom-00*`: `.000`–`.004` exist.

**Other:**
- `helio-gracie.md`, lines 100–179, plus a search;
- `save_verbatim.py`, lines 1–110;
- `tako-budget-proposal.md` and `ts-file.sh`, by search. `ts-file.sh` reads neither `needed_by` nor `origin`.
- Memory notes on cost gates and on this tracker. I used these as pointers only, never as a source of rules.

**Not reached:** a content search of `Requests\` for tracker headers timed out after 20 s. So "no tracker item exists" stays reported-by ip-man.

## 1. §3.8: the vehicle and the wording (D3)

**1a [note] The vehicle is right.** A `.001` on `BB-20260925-venom-001` keeps one trial on one thread. Its owner, window and keep-or-remove decision then cover the extension, and there is no second record to reconcile.
- **Appending is how the board changes a bulletin** (TSD §7a: "append a superseding event; never trash it").
- **It stays visible to every host.** The Crier carries `to` forward from the newest event that has one, and it shows every Bulletin Board thread to every host [measured: `crier.py:137–138, 435`].
- **The filename parses.** I read the canonical grammar (`filename.py:8`) but did not execute it [inferred]. The name matches the board's own continuation events [measured: `BB-20260926-venom-001.001`–`.004`].
- **`.001` is the next number** [measured: glob].

**Rejected alternatives:**
- **A new Bulletin thread.** It would put its own subject in listings. But one trial would then have two records, with one keep-or-remove decision split between them.
- **A numbered ruling on the register.** It would be findable by D-number, but it waits on the register's keeper, who is on another host. My K1 chose a Bulletin plus a cross-reference request, which makes the approval findable without waiting.

**1b [change] The pointer approves all of section 3, which includes routing, rejected alternatives, and this work's own $90 and dates.**
- **What the pointer covers today.** Section 3 includes §3.10 (among its rows, how a future overspend gate would be adopted), §3.11 (routing) and §3.12 (this work's figures).
- **Why that matters.** D3 records forge's reading: "The same rule written inside a RECORD OF AN OPERATOR DECISION borrows that decision's authority" [measured: D3 §4].
- **Close.** Point at §3.1–§3.7, which is the mechanism. Add "as amended by" ip-man's answer to this review, by path and SHA-256, the way `.000` named v1 "as amended by v2". Without that second pointer, his yes approves text this review is about to change.

**1c [change] Put §3.12's figures to him as a separate question.**
- **The problem.** The work order puts the extension and §3.12's figures to him "as one yes or no". Those are two decisions:
  - whether the fields exist, which is a rule under D3;
  - what one item's budget and dates are, which is a scoping yes under that rule.
- **What bundling does.**
  - A single answer couples them, so a "no" to $90 would read as a "no" to budgets.
  - The Bulletin becomes the confirmation that the Feature's `budget:` cites as tier-2 proof [inferred from §3.12 and Implement (4)].
  - His stated preference is also one decision at a time [reported-by session memory].
- **Close.**
  - The GATEWAY asks about the extension first.
  - The seed Epic's scoping follows as its own yes, carrying §3.12's figures, transcribed on that Epic's thread.
  - `.001` says it confirms no item's budget or dates.

**1d [change] The question must state the readings his yes is meant to cover.** Two readings are ip-man's, not his:
- **(i)** his budget words mean US dollars, priced at the credit rate, worst case, and proposed at scoping (§2);
- **(ii)** every Story carries a budget (DoR line 5). "Every Story" comes from the session's relay [reported-by session, per the note §2].

**Why this is D3's failure shape.** D3 names it: "the operator answers a SCOPING question, and the recording agent writes a CONSTRAINT into its record of that answer" [measured: D3 §1]. He answered a scoping question: what a budget is measured in.

**Close.**
- The question states reading (i).
- It offers DoR line 5 as an explicit option: every Story (recommended), or milestones only.
- It names, in one clause, the reading not taken: "if we have to use credits" also admits budgeting only work expected to spill into credits.
- `.001` quotes the question as he read it, and names the option he chose.

**1e [change] "Copied exactly from his messages" names no mechanism.**
- **The problem.** save_verbatim.py reads only assistant records: with `--line N`, "that record must have "type": "assistant"" [measured: docstring lines 55–58]. So nothing checks the claim.
- **Close.**
  - Each quote carries its source (transcript path and line) and the SHA-256 of the string as extracted.
  - The session reads each quote from his message record and never retypes it. This is the same honest form the session used for the ruling and the erratum.
  - The quote drops the word that the standing rule reserves for a hash the tool printed.
  - `.001` quotes the question too. A transcribed "yes" points at nothing without it.
  - 5g files the tooling Request.

**1f [change] The `scope:` line and §3.8's own list disagree.**
- **What differs.** §3.8 lists four additions: `budget:`/`spent:`, the confirmation rule, DoR line 5 and the roadmap. The scope line leaves out the confirmation rule and DoR line 5, which are the two that change how venom files.
- **Close.** A D3 record's scope names exactly what it approves (§6).

**1g [change] "Every line below that is not his is that note's text" is not true of this draft.**
- **The problem.** The other lines summarize the note. The sentence leaves open which text governs when a summary and the note differ. It is my sentence from A.4, and `.000` carries it too.
- **Close.** "Every other line in this event is venom's summary of those notes; where a summary and the notes differ, the notes govern."
- **On `.000`.** I did not compare `.000`'s summaries with v1 and v2 line by line. This review records the defect; a correcting event is needed only if a difference is found.

**1h [change] Delete "Any cash limit is the one on his own Claude account, not here."**
- It is an agent's statement about his account settings, placed inside a record of his decision.
- The note itself hedges it ("if he has set one", §2).
- It is not something the extension does or leaves undone.

**1i [minor] Add two lines.**
- **REGISTER:** the cross-reference `.000` asked for covers `.001` too, and nothing waits for it.
- **A keep-or-remove question for what the extension adds.** Q1–Q4 test nothing about budgets or the roadmap.
  - **Q5:** "did the roadmap or the costs change a decision (a priority, a pace or a scope), and how many re-plans did they ask him to confirm?"
  - The first half tests his stated purpose, "help guide work and priorities". The second half counts the supervision it costs him (2b).
  - Measuring it is shuri's lane.

**1j [minor] A filing hazard.**
- **The hazard.** `BB-20260925-venom-001` (this trial, `.000` only) and `BB-20260926-venom-001` (claude-app, `.000`–`.004`) differ by one digit [measured: glob]. Filed on the wrong thread, the extension would become `.005` of the claude-app trial.
- **Close.** At filing, re-check the thread id as well as the number.

## 2. §3.4 as an extension of A3

**2a [note] It is faithful to A3's reasoning.**
- **A3's reasoning.** The header carries only what he has decided, and proposals live in event bodies. "Confirmed" is then decidable from the origin of the event that set the value.
- **What §3.4 does with it.**
  - It applies that reasoning, field by field, to `needed_by:` and `budget:`. Field by field is a faithful generalization, because G3 gives each field its own setting event.
  - It keeps C5's split: the presence of proof is checked, and its genuineness is left to people.
  - It adds no approval when a value is first set.

**2b [change] A3's cost premise does not carry over: every slip or raise needs his words.**
- **The gap.** A3 was "Cost: none; that event already exists", because a level is set once. Dates and budgets change by nature, so "It adds no approvals" is true only of first values.
- **Close.** Say so, and define the cheap path for a known slip:
  - the session records the forecast in the CHECKPOINT body, where A3 puts proposals;
  - his date stays in the header, and lateness is measured against it;
  - he re-plans when he chooses.
- **Why this is safe.** An agent's re-date written into the header is still harmless under 2c: it is flagged, and it never hides the slip.

**2c [change] PJ3 lets a harmless restatement unconfirm his value. Compare the current value with his newest value instead.**
- **Two wordings.** A3 says "the event that set" the value. PJ3 says the event that "supplied" it, meaning the newest event carrying the field.
- **Where they part.** On well-formed threads they agree, because G3 carries a field only on change. They part when an event restates an unchanged value. D19 §2 names the risk: "an `owner:` repeated on every append can go stale on one event and silently contradict the others". Under PJ3, a restatement flips a confirmed date to unconfirmed, and that is the only reason watch-for (a) exists.
- **Recommended close.**
  - A field's **confirmed value** is its value on the newest event that carries the field with `origin: operator`. If that value is invalid, there is none, with no fallback (as in R1 and `invalid_level`).
  - The field is **confirmed** when its current value equals its confirmed value, compared as parsed values (a date, an amount), not as strings.
  - This is A3's reasoning stated as a check: the header shows what he decided. It tolerates an innocent G3 slip, and it gives PJ9 its threshold (4b) with no second concept.
  - CT1–CT9 pin it.
- **Alternatives.**
  - **PJ3 as written, plus watch-for (a).** It saves one pass over the events. But a restatement costs a false flag and a Q2 count, and only discipline prevents it.
  - **A3's literal wording, "the event that last changed the value".** It agrees with my rule on every row except CT6.

**2d [change] PJ3 flags an unconfirmed `needed_by` or `budget`, but not an unconfirmed `level:` on an Epic or Feature, although §3.4 names level as one of the three.**
- **Where the gap is.** A Story gets the check through DoR line 4. An Epic or Feature gets only a marker.
- **Why it matters.** The case A3 was written for goes unflagged: a scoping event that sets `level: epic` itself, as the stale v1 template does (5e).
- **Close.** Flag an unconfirmed level on Epics and Features under the same flag. Stories keep DoR line 4, so Q2 counts each case once.

**2e [minor] Record a case this cannot catch.**
- **The case.** A tier-2 child is filed as `origin: operator` by pointing at his yes. If its filed `budget:` or `needed_by:` differs from what the scoping note proposed, it still reads as confirmed.
- **Why it is unchecked.** This is TSD §3a's "authority inherited from an ADJACENT instruction" [measured: TSD 338–339]. The header cannot decide it, because the proposal is prose.
- **Close.** Add no mechanism now. Helio's CHECKPOINT on the filing compares the filed values with the scoping note, and a real mismatch decides whether anything more is needed.

**2f [note] A3 has a gap of its own, and it is mine, not ip-man's.**
- **The gap.** A3's yes also sets `parent:`, `project:` and `repo:`, but its test reads `level:` only, so a re-parent by an agent is never flagged.
- **Where it goes.** The post-trial amendment. No action now.

## 3. Reusing `needed_by:`, and P3's "No commitment"

**3a [note] There is no rule conflict, and the field keeps one meaning.**
- **TSD §4.** It requires `needed_by` on P0 and P1 and forbids it nowhere [measured: TSD 362–372].
- **The register already treats the date and priority as separate things:**
  - D24 gives the Seeking template an optional `needed_by:`, and that template carries no priority at all, because "s4 ties priority to expected response and nobody is expected to respond" [measured: D24 §4];
  - D24 §3 notes that "A P3 backlog item can carry `impact: security`" [measured].
- **One meaning in both uses:** the date by which the requester needs the item. For a tracker item, that is its delivery date.
- **So reuse is sound,** and ip-man was right to reject a new `due:` field.

**3b [change] The note's word "commitment" collides with TSD §4's "P3 ... No commitment". Rename it.**
- **Where the words meet.**
  - §3.4 calls `needed_by` and `budget` "commitments", and PJ3's flag is `unconfirmed_commitment`.
  - v1 files asks at P3, and the ask's thread becomes the Epic [measured: v1 lines 181, 191, 322].
  - So the typical milestone is a thread whose header says "Backlog. No commitment" and that carries a confirmed "commitment".
- **Two misreadings follow.**
  - "It is P3, so the date does not bind."
  - "The date binds, so raise the priority." v1 §4 rules out exactly that inflation.
- **Two different commitments.** In §4 a commitment is the assignee's promise to respond. In the note it is the operator's plan.
- **Close.**
  - Call these his confirmed fields.
  - Rename the flag, for example to `unconfirmed_field`, with the field in its detail. Do it while nothing has fired it: once anything counts a flag name, that name becomes a dependency.
  - §3.2 and `.001` say that priority keeps its §4 meaning, and that a dated P3 item is backlog with a planned date.
- **Rejected: keep the word and add a gloss.** The flag name prints beside P3 on every dashboard, but the gloss would sit in a document nobody has open.

**3c [minor, recommended] Have the scoping note propose each item's priority beside its date.**
- **The gap.** Nothing sets a child's priority today except v1's P3 template.
- **Close.** His yes sets both the date and the priority, because he is the requester and §4 gives priority to the requester. Neither is derived from the other.
- **An example.** By §4's own words, an item he needs this week is P2 ("Needed this week"). That is his call at his yes, not a rule.

## 4. PJ9's attention rows, under D42 and D43

**4a [note] They are reports, by D43's own definition.**
- **The definition.** D43: "A GATE decides whether an agent may act... A REPORT produces a number and leaves the deciding to a person" [measured].
- **How the rows fit it.** No agent's action triggers them, and they hold nothing. The projector computes them when it runs, and people read them.
- **Why this is not an inferred cost gate.** He stated a budget, not a stop, and §3.10 keeps any gate as a named path he would have to adopt himself.

**4b [change] D42 holds only if attention compares against his confirmed numbers, and PJ9's spec does not.**
- **The gap.** PJ9 argues "the threshold is his own confirmed number". Its spec, though, compares against the current valid value, confirmed or not.
- **Why that fails D42.** The harm D42 needs named here is categorical: the work went beyond what he approved. So crossing an agent's number names no harm (AT3). Comparing against the current value also lets an agent's re-date hide a slip past his date (AT2, AT5).
- **Close.**
  - Attention compares against the confirmed value (2c).
  - An unconfirmed value keeps its own flag, and its roadmap row shows both dates, so nothing goes quiet.

**4c [change] Name the one route by which a report becomes a gate: a consumer holding work on it.**
- **The route.** The session hands Helio "the roadmap and cost facts in each pacing brief" (§4). If a brief treats "over budget" as a reason to hold or cut a Story, that is an inferred cost gate, enforced only by discipline, with no window and no adoption.
- **Close.**
  - PJ11's contract adds, in D43's terms: never used to decide whether work may start, continue or stop.
  - Overspend and lateness reach Sensei as information.
  - A consumer can detect its own breach of that clause (D41).
- **A correction to my own K6.** I wrote that Helio "picking only 'ready' Stories is his existing limit".
  - His file's limit is "work already scoped against criteria `ip-man` wrote" [measured: `helio-gracie.md:118–119`], and it never mentions the DoR.
  - Once the DoR has a cost line, my loose phrase would turn a missing budget into a hold through Helio.
  - The DoR reports; it holds nothing.

**4d [minor] The harm wording needs correcting.**
- **What `spent:` is.** It is usage priced at the credit rate, not cash paid, and it includes SP4's allocated share of the orchestrator's cost.
- **So the harm is** "usage, priced at the rate he would pay in credits, beyond the worst-case figure he approved", not "money overspent".
- **And the basis of `spent:`** is measured plus allocated, under SP4's declared rule.

**4e [minor] A missing figure must not read as a clean pass.**
- **The gap.** Until Slice 2 lands, `spent:` is absent, so no item can show as over budget.
- **Close.** Where an item has a budget but no `spent:`, roadmap rows and totals say "spend not measured". The same rule applies to a check that lets work through when it fails: it must show the gap, so the gap never reads as a pass.

**4f [minor] Four spec points to settle before the tests pin them.**
- **Time zone** (D43: "THE UNDECLARED IDENTIFIER IS THE FAILURE MODE"). `as_of` defaults to the UTC date, so an item due on a date shows as overdue from 19:00 US Central on that same date. Either say so, or default `as_of` to his local date.
- **The meaning of "open" in PJ9.** It should mean "not yet delivered": not RESOLVED, CLOSED or CANCELLED. The module's existing "open child" means only "not CLOSED or CANCELLED" (AT7).
- **RESOLVED→CLOSED must not move `delivered_on`.** §3.2 says so, but PJ5's "last entered RESOLVED or CLOSED from another state" reads either way (AT8).
- **PJ6 (`deadline_after_parent`) describes his plan, not a filing error.** By the note's own category test it belongs with the attention rows; as a flag, Q2 would count his own choices as filing errors.

**4g [note] A sturdier reason for keeping attention rows out of the flags.**
- **The note's reason is moot today.** Its Q2-comparability argument needs counts, and nothing has been counted yet.
- **It becomes real only if filing starts before Slice 1** (5d). Then the new flags in PJ2–PJ6 would shift Q2's counts too.
- **The sturdier reason is category.** Flags are filing errors; attention rows are facts about the work.
- **Close.** Report Q2 by flag name, counted from the date each flag first ran.

## 5. My own concerns

**5a [change] §3.2 and PJ8 disagree about what a milestone is.**
- **The two definitions.** §3.2 says a milestone needs a *confirmed* `needed_by`. PJ8 lists the items with a *valid* one, each marked with whether it is confirmed.
- **Why it matters now.** ronda-rousey will pin one or the other.
- **Recommend PJ8's version** (show every milestone and mark it), and fix §3.2.

**5b [change] §3.11 and `.001` disagree about `needed_by`.**
- **The two statements.** §3.11 says "His scoping yes can set `needed_by:` straight away". `.001`'s scope lists "a delivery-date use of needed_by" among the additions.
- **Close.** Say in both places that:
  - filing `needed_by` is allowed now, with its §4 meaning;
  - the extension adds the projector's reading and the confirmation rule.

**5c [note] Counting RESOLVED as delivered fits TSD §3a here.**
- **Why it fits.** v1 §8 defines a tracker item's RESOLVED as QA passed plus Helio's final CHECKPOINT, which is more than bare self-certification [measured: v1 line 339].
- **Why not CLOSED.** Measuring at CLOSED would count his own closing delay against the crew.

**5d [session] The trial has no data. Start filing now.**
- **Nothing is filed yet.** ip-man found no tracker item on the board [reported-by ip-man; my own search timed out], and neither seed was filed.
- **Nothing here gates filing.** Intake and scoping are already approved (`.000`), and §3.11 agrees.
- **Why not wait for the builds:**
  - Q1–Q4 have no data.
  - The extension's data can start only once Slice 1 lands, on 2026-10-02 at the earliest. That leaves about 23 days of the window [inferred].
  - Slice 1's live check needs a real item. Venom's claim gate passed its suite, then assessed zero sentences on its first live turn (`BB-20260912-venom-001.003`).
  - The first filing tests the templates (5e).
- **The seeds as named are partly stale.** Revere's Step-1.1 has shipped [reported-by session memory]. So Helio's GAME PLAN names them as they stand now:
  - the tracker's own build, as the first Epic. It can cite `.000` as its tier-2 pointer, since his "yes, proceed" approved v1 §9's seed [measured: `.000` lines 22–23, 36];
  - Tako and Wonderland asks, at his pace.
- **Start `DISPATCHES:` lines with the first filed item, not after his yes.**
  - It is a body line on venom's own events, the same class of practice as §3.11's cost proposals.
  - Every dispatch recorded now can be priced later.

**5e [change] Replace the stale templates with a filing card, in ip-man's answer.**
- **v1 cannot be edited.** `.000` pins it by SHA-256.
- **Its templates carry two hazards:**
  - the scoping event sets `level: epic`, which A3 superseded;
  - the trailing `# new` notes, copied into a header, produce `invalid_level` and `parent_malformed` (the ruling's watch-for (e)).
- **Close.**
  - ip-man's answer gives the four current templates: intake ask, scoping event, confirmation event and child Story.
  - They follow A3 and the ruling, carry this note's fields, and have no inline notes.
  - The session saves them in the repo as one filing card. The card is the short, binding core for filers; the notes remain the reasoning record.
  - 2d makes the projector flag an Epic filed from the stale template.

**5f [minor] Add a live check.**
- **The gap.** Done-when (2) uses fixture boards only.
- **Close.** Add a Slice 1 run on the real board once a real item exists, with its command and output saved. tony-jaa's SP5 run already does the same for Slice 2.

**5g [session] save_verbatim.py cannot extract the operator's own words.**
- **Why it matters.** His words are the fleet's tier-1 proof, so every operator-origin event depends on extracting them by hand.
- **Close.** A user-record extract mode, filed as a Request.
- **It does not block `.001`.** Until the mode exists, 1e's hand form is honest.

## 6. `.001`, redrafted

This applies 1b–1j, 3b and 4c. ip-man accepts it, amends it, or answers it. Angle brackets are filled in at filing.

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
basis:       reported-by operator - his words below, each with its source and SHA-256; the notes read at the SHA-256s below
scope:       extends the tracker trial on venom's own Requests: budget: and spent:, needed_by: read as a delivery date, confirmation by his words<, a budget line in the Definition of Ready>, and a roadmap view. Adopts no doctrine. Asks nothing of any other host.
at:          <UTC from date -u>
subject:     ON TRIAL - venom's tracker items may also carry a budget, a spend and a delivery date. Operator-approved for trial. Not doctrine.
---
HIS WORDS (TSD s3a, tier 1), each read from his message record, never retyped;
source and SHA-256 beside each:
  The ask [<transcript>:<line>; sha256 <hex>]
    "<...>"
  The unit [<transcript>:<line>; sha256 <hex>]
    "<...>"
  The question he answered, as he read it [<path or transcript:line>; sha256 <hex>]
    <the question>
  His answer [<transcript>:<line>; sha256 <hex>]
    "<...>"

WHAT THOSE WORDS APPROVE, by pointer:
  C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md, branch internal,
    sha256 48c18e290d4cb62a1befb8f876a03ef1b516c9da13822f7dfdd2016727c54fc9, sections 3.1-3.7,
  as amended by <ip-man's answer to kano's review: path, sha256>,
  with Definition of Ready line 5 <kept | dropped>, as he chose,
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
    lateness are reported, never enforced (D1, D43). <The new Definition of Ready line and> the
    new flags are reports, as .000 says of every tracker flag.
  - confirm any item's budget or dates. Those are set by his yes on that item's own scoping.
  - change the Crier, the Registrar, the filename grammar or Vertical.

TRIAL: unchanged - owner venom, window through 2026-10-25. The keep-or-remove decision at its
  end covers these fields too, adding question 5: did the roadmap or the costs change a
  decision (a priority, a pace or a scope), and how many re-plans did they ask him to confirm?
REGISTER: the D-number cross-reference .000 asked for covers this event too. Nothing waits for
  it.
```

## 7. Test cases

**Confirmation (CT), for `level`, `needed_by` and `budget`.** The events that carry the field are listed oldest first:
- `op` means `origin: operator`;
- `ag` means any other origin;
- `x` is an invalid value.

| Case | Events carrying the field | PJ3 as written | Recommended (2c) | Confirmed value, i.e. the attention threshold (4b) |
|---|---|---|---|---|
| CT1 | A op | confirmed | confirmed | A |
| CT2 | A op, A ag (restated) | unconfirmed | confirmed | A |
| CT3 | A op, B ag (agent re-dates) | unconfirmed | unconfirmed | A |
| CT4 | A op, B op (his re-plan) | confirmed | confirmed | B |
| CT5 | A ag only | unconfirmed | unconfirmed | none, so no attention row |
| CT6 | A op, B ag, A ag | unconfirmed | confirmed | A |
| CT7 | A op, B op, A ag | unconfirmed | unconfirmed | B |
| CT8 | A op, x ag | `invalid_value`; no value | `invalid_value` only (no second flag) | A |
| CT9 | x op | `invalid_value`; no value | `invalid_value`; no fallback | none |

"Unconfirmed" means different things by level:
- On an Epic or Feature, it raises the renamed flag (2d, 3b).
- On a Story, it is DoR line 4.

**Attention (AT).** `as_of` is 2026-10-05. Budget and spend are each item's own figures, and items are open unless stated.

| Case | Input | PJ9 as written | Recommended |
|---|---|---|---|
| AT1 | Feature, `needed_by` 2026-10-02 op | overdue row | overdue row, 3 days past his date |
| AT2 | Feature, 2026-10-02 op, then 2026-10-09 ag | no row; flag on 10-09 | overdue row against 10-02; flag on 10-09 |
| AT3 | Feature, 2026-10-02 ag only | overdue row; flag | no row; flag; roadmap row shows `days_left` −3 |
| AT4 | Story, `budget` 10 usd op, `spent` 12 | over-budget row | row against his 10 |
| AT5 | `budget` 10 op, then 15 ag; `spent` 12 | no row; flag on 15 | row against his 10; flag on 15 |
| AT6 | `budget` 10 op, no `spent` | no row | no row; "spend not measured" shown (4e) |
| AT7 | RESOLVED 2026-10-04, `needed_by` 2026-10-02 op | depends on which "open" | not listed; `on_time` false (4f) |
| AT8 | RESOLVED 2026-10-04, CLOSED 2026-10-06 | `delivered_on` ambiguous | `delivered_on` 2026-10-04 (4f) |
| AT9 | any board | contract names both lists | contract also forbids deciding whether work may start, continue or stop (4c) |

**Operator override.** Nothing is held, so there is nothing to override. AT9 pins that the contract says so.

**What enforces each rule:**
- **By code, once built:** every row above.
- **By prose only:**
  - 2e's value match, which is left to Helio's CHECKPOINT;
  - 4c's clause, which is the consumer's own discipline, written so the consumer can detect a breach (D41).

## 8. Who does what next

**ip-man, in one answer:**
- 1b–1j, through §6;
- 2b–2e;
- 3b and 3c;
- 4b–4g;
- 5a, 5b, 5e and 5f;
- revised work-order lines for the GATEWAY (1c, 1d) and for Done-when (5f);
- dropping watch-for (a) if he adopts 2c.

If he declines a [change] finding, its first sentence is my dissent, in my words, for Helio's GATEWAY.

**helio-gracie, after that answer:**
- **GAME PLAN.** Its first Next lines name what to file now (5d).
- **GATEWAY.** It puts two questions to Sensei, one at a time:
  - first, the extension, stating the budget reading and the DoR line 5 option (1c, 1d);
  - then the seed Epic's scoping, with §3.12's figures.
- **Pacing briefs** treat attention rows as information for Sensei, never as holds (4c).

**ronda-rousey:** tests after ip-man's answer, with CT1–CT9 and AT1–AT9 as fixtures as his answer settles them.

**The session:**
- saves and commits this review (commands below);
- resumes ip-man with it, extracted with save_verbatim.py;
- extracts his words for `.001` from his message records (1e);
- re-checks the thread id at filing (1j);
- starts the `DISPATCHES:` lines (5d);
- files two Requests:
  - a user-record mode for save_verbatim.py (5g): ronda-rousey writes the tests first, then bruce-lee builds it;
  - shuri, to measure Q5 (1i).

**No reviewer from another vendor now.** This is trial text, not doctrine. The post-trial amendment gets one (eddie-brock), as already planned.

## 9. When this review stops being right

- **4a** holds only while no consumer holds work on an attention row or a DoR reason. The first time one does, it is a gate and needs his adoption.
- **2c** trusts that an operator-origin event carries only values he spoke to (2e). Evidence to the contrary reopens it.
- **3a** holds while TSD §4 reads as it does now. Beyond the search listed above, I did not re-read the register for amendments to §4, and ip-man cites none.

## Summary

- **The extension is sound, and I recommend it.**
- **It goes back to ip-man once, then to Helio.** Two things need fixing first:
  - the `.001` wording (D3);
  - four spec points that tests will pin: confirmation, milestones, attention and the level flag.
- **Filing under the trial should start now.** It waits on none of this.

**Next steps:**
1. The session saves and commits this review.
2. The session resumes ip-man, and his answer is saved beside the note.
3. Helio runs the GAME PLAN and GATEWAY.
4. Sensei gets two questions, one at a time.
5. Filing starts on Helio's first Next lines.

**Requirements:**
- His words are extracted with their source and SHA-256 (1e).
- ip-man's answer is pinned by SHA-256 in `.001`'s pointer (1b).

**Commands.** Run these on Venom, in Git Bash, from the orchestrating session, with no elevation. Nothing is pushed.

```
python C:/Repo/Agentic/tools/save_verbatim/save_verbatim.py splice "<this subagent's transcript .jsonl>" C:/Repo/townsquare/docs/kano-tracker-budget-roadmap-review-20260926.md
git -C C:/Repo/townsquare branch --show-current
git -C C:/Repo/townsquare status --short -- docs/
git -C C:/Repo/townsquare add docs/kano-tracker-budget-roadmap-review-20260926.md
git -C C:/Repo/townsquare commit --author="<name> <18243588+terrence-adams@users.noreply.github.com>" -m "docs: kano review of the tracker budget/roadmap design"
git -C C:/Repo/townsquare show --stat HEAD
```

**Expected results:**
- The branch is `internal`.
- `status` shows the review as `??`.
- `show --stat` lists one file.

`internal` carries other sessions' commits, so whoever pushes later runs the pre-push range check first.