# TownSquare Doctrine project: working scope (version 2)

**One working copy.** Requirements, features, acceptance criteria and status for the TownSquare Doctrine project. When this file and another document disagree about scope, correct this file.

- **Last updated:** 2026-10-06 ~14:25Z, by venom, at the operator's request to end the session.
- **Version 2 answers helio-gracie's CHECKPOINT** (`docs/helio-checkpoint-scope-20261006.md`, verdict REWORK of version 1). Done here: the four missing statements added with their times; R6, R7, R10 and R14 relabelled; section 5 restated from the transcript and git, with raw output in `docs/townsquare-doctrine-project-scope-evidence-20261006.txt`; AC-D2 given a scan command and its measured result. Still to do: ip-man ratifies the AC-D set; Helio re-checkpoints this version.
- **What "the project" covers (venom's reading; correct it if wrong):** Track 1, the official TownSquare Doctrine and its replaceable bindings. Track 2, the Revere nudge, which after `.009` is an implementation and trial plan under a binding, not doctrine. Track 2 does not gate Track 1.
- **Quotes** are hand-copied from the session by venom (not tool-hashed), with the UTC time and the transcript line (`C:\Users\terre\.claude\projects\C--Workspace\410f8216-70ff-454c-98f1-cc7ace24d679.jsonl`). Board copies: `TS-20261006-venom-001` `.004` to `.009` and `TS-20260911-forge-001` `.002`. Basis tokens: measured, inferred, assumed, reported-by.

---

## RESUME HERE (next session)

1. **Read this file, then `docs/helio-checkpoint-scope-20261006.md`.** Nothing of venom's is running. Kano, ip-man and Helio are all finished (ListAgents, 14:2xZ). Nothing is adopted. Nothing has been reviewed by Eddie.
2. **Do not push** the `internal` branch of townsquare (12 commits ahead of origin at 14:14Z) or the `lan-phase-1` branch of revere. The work is pending review.
3. **Another session** ("New TownSquare") is running the NAS ledger and Crier tracks. Its handoff is `docs/session-handoff-20261006-nas-ledger-crier-drive-auth.md`. The Crier's Google token expires about 2026-10-13; re-auth is due by about 2026-10-12 (`python C:\Repo\townsquare\tools\crier-reauth.py --check`).
4. **Follow Helio's `Next:` order** (section 10). Rule learned today: record the operator's statements, but send a running subagent nothing more. Send ONE consolidated message after it finishes, and confirm arrival in its transcript. See memory note `feedback-queued-subagent-messages-get-lost`.
5. **Ask the operator only for what is in section 6.**

---

## 1. Mission and scope

**Mission (his words, 13:38:51Z, line 551):** "Kano's mission is to take all the provincial drafts, current documents that have been created to assist in governance and formalize them into an actual working TownSquare Doctrine. Scoped documents that provide value and governance but aren't tied to infrastructure like google drive, azure dev ops, or AWS." ("Provincial" is read as "provisional".)

**Goal (his words, 13:42:11Z, line 583):** "Kano should know that goal is an official version. To be treated like the Declaration of Independence or Magna Charta. I want to have a working version of our Doctrine as an official part of the Wonderland project to govern agents for the town square."

**Package shape after `.009`** (reported by Eddie's Codex session, item 5; his reading of the operator's correction): (1) an infrastructure-neutral Doctrine 2.0; (2) a replaceable durable-record binding (today: Google Drive); (3) a replaceable wake-mechanism binding; (4) a Revere-specific implementation and trial plan under that binding.

**In scope:** the doctrine; its bindings; an inventory of every governance document with a proposed fate; the amendments, finished in the same text; a neutral recognition rule and an adoption record; a recommendation for where the doctrine lives and is issued inside Wonderland; the review (Eddie's outside review, Kano's reply, Helio's checkpoint, gsp where a clause needs it); Revere's implementation and trial plan, design only.

**Out of scope:** adopting anything (only the operator adopts); building, installing or deploying anything, or changing any host's settings, credentials or services (each needs his separate word); rewriting the Agentic Operating Charter, Bedrock or Charter 2.0 (mapped only); the Dojo process findings DJ-1 to DJ-4.

**Related tracks, not this project:** the NAS-hosted ledger that replaces Drive (`docs/ip-man-nas-ledger-design-v1-20261006.md`, delta 1 `5952ea9`, delta 1.1 `f3e27f9`) and the single reconciled Crier (`docs/ip-man-crier-one-version-ruling-20261006.md`). They need their own bindings. The NAS ledger is the test for AC-D13.

---

## 2. Requirements

"When" is the UTC time of his message and the transcript line.

| ID | Requirement | Source (his words) | When | Basis |
|---|---|---|---|---|
| R1 | A TownSquare doctrine, created and finalized, for agent behavior | "I want the TownSQuare doctrine created and finalized for agent behavior." | 13:33:22Z, 468 | reported-by the operator |
| R2 | Not tightly coupled to Google Drive, Azure DevOps, AWS or any infrastructure | "I do not want it tightly coupled to google drive." and the mission (R5) | 13:33:22Z, 468; 13:38:51Z, 551 | reported-by the operator |
| R3 | Centered on concepts such as the Bulletin Board and the Requests board | "I want it centered around concepts like the Bulletin Board, and Requests board." | 13:33:22Z, 468 | reported-by the operator |
| R4 | The rules that govern do not change when the infrastructure changes | "The infrastructure will change, but the rules that govern should not." | 13:33:22Z, 468 | reported-by the operator |
| R5 | Built from all provisional drafts and current governance documents, as scoped documents | the mission, quoted in section 1 | 13:38:51Z, 551 | reported-by the operator |
| R6 | An official version | "...goal is an official version. To be treated like the Declaration of Independence or Magna Charta." | 13:42:11Z, 583 | reported-by the operator |
| R7 | A working version | "I want to have a working version of our Doctrine..." | 13:42:11Z, 583 | reported-by the operator |
| R8 | An official part of the Wonderland project, to govern agents for the town square | "...as an official part of the Wonderland project to govern agents for the town square." | 13:42:11Z, 583 | reported-by the operator |
| R9 | Finish the doctrine and the amendments (the 2026-09-11 tabling is lifted) | "correct, I wish to finish the doctrine and amendments." | 13:34:31Z, 481 | reported-by the operator |
| R10 | Kano creates and defines the doctrine. Eddie is the outside reviewer, giving an alternative perspective and checking Kano's work | "Kano is the expert, he creates and defines the doctrine. Eddie is the outside reviewer to provide alternative perspective and check Kano's work." | 13:36:40Z, 513 | reported-by the operator |
| R11 | Revere is a cross-vendor nudge that starts an agent which is not running (see 4.3 for R11a to R11c) | "Revere is designed to solve a gap in our ability to reach agents from different vendors and let them know a post or request has been made. It is a "nudge" for engagement." (13:36:08Z, 512). Asked whether "nudge" means starting an agent that isn't running: "yes, that's exactly what it means." (13:56:18Z, 772) | 13:36:08Z; 13:56:18Z | reported-by the operator |
| R12 | Know what is outstanding and what needs review to be accepted | "I want to know what it is outstanding and needs review to be accepted." | 13:34:31Z, 481 | reported-by the operator |
| R13 | One working copy of scope, acceptance criteria, features, requirements and status | "I want one working copy of scope for this project. Acceptance criteria, features, requirements, and status." | 13:57:40Z, 787 | reported-by the operator |
| R14 | Finish this week. Friday 2026-10-09 and "ready for the operator's acceptance" are Eddie's session's words | his words quoted in Request `.000` (as reported by Eddie's session): "...finish the Doctrine this week?" | 12:46Z (filed) | reported-by Eddie's session; "this week" is quoted as his |
| R15 | Try the implemented version for 2 to 4 weeks | Eddie's `.002`: "Coordinate with Kano to draft a version to implement, and we will try it for 2 to 4 weeks." | 13:31Z (filed) | reported-by Eddie's session; **unconfirmed by venom** |
| R16 | Standing rules hold: a defect needs reproducing proof before a fix; trial before formalizing; signing stays retired; the operator is never gated; nothing is deleted; gated actions need his word; only the operator adopts | his standing rules and rulings (D3, D30, D32, D45) | standing | reported-by the operator |
| R17 | Revere is a tool and infrastructure. It does not belong in the doctrine as a literal. A different tool can serve the same function. Test: replacing Revere with another compliant wake mechanism needs no doctrine amendment | `.009`: "Revere is just a tool, it is infrastructure. It does not belong in the Doctrine as a literal. A different tool can serve the same function..." (truncated in the event) | 14:06:37Z (filed) | reported-by Eddie's Codex session; **quote and truncation unverified by venom** |
| R18 | Eddie Brock is online and asks to work with Kano to finish the doctrine; a post is made to the TownSquare at the operator's request | "Eddie Brock is currently online and requesting to work with Kano to finish the Doctrine for the TownSquare. a Post is made to the TownSquare at my request." | 12:46:50Z, 3 | reported-by the operator |
| R19 | Revere's wake gap calls for a scope or feature change | "This sounds like a scope or feature change is required." | 13:21:28Z, 320 | reported-by the operator |
| R20 | **Decision:** scope the Revere wake feature now, as a design note only | Asked "Should ip-man scope the Revere wake feature now (design note only, no build), or leave it as "proposed"...", he answered: "1. yes" | 13:22:56Z, 350 | reported-by the operator |
| R21 | Compare the two Revere notes and offer one final solution that meets all the acceptance criteria | "Do a compare between the two, and offer one final solution that meets all the acceptance criteria." | 13:55:31Z, 755 | reported-by the operator |

**Other instructions he gave this session** (not requirements): "LIst the concerns, and acknowledge that operator may override." (13:28:30Z, 429; done, section 7); "Have Kano state the mission and request, so that I know that he understands the goal." (13:29:34Z, 442; done); on the Crier token, "this has happened already in another session" (13:40:02Z, 570; confirmed, Crier healthy); and "I wish to end the session, save all relevant information for the next session." (~14:15Z).

---

## 3. Features (deliverables)

| ID | Feature | Meets | Owner | Status |
|---|---|---|---|---|
| F1 | **Town Square Doctrine 2.0**, the founding text, no infrastructure in its rules | R1 to R8, R17 | Kano | Draft 4 saved (`docs/town-square-doctrine-v2.0-draft-4-20261006.md`, with a commentary). Not reviewed |
| F2 | **Durable-record binding**: Google Drive binding 1.0 | R2, R4 | Kano | Draft 1 saved. Pass 4 gives five edits, not yet merged into one file |
| F2b | **Wake-mechanism binding**, replaceable (new after `.009`) | R17, R11 | Kano | Not started |
| F3 | Scoped companion documents, only if the content needs them | R5 | Kano decides | Pass 4 proposes a commentary and maps the rest; no companion written |
| F4 | Governance inventory: every governance document, its status, its proposed fate | R5 | Kano | Done in pass 4 (about 35 documents, statuses from headers). Herding Cats not read in full; Night Shift conformance and the RoE export are left for pass 5 |
| F5 | Amendments folded in: (a) the tabled 2026-09-11 set, (b) the Registrar's behavior rules, (c) the board templates | R9 | Kano | Carried in draft 4. The provenance field (P8) awaits the operator's ruling |
| F6 | A neutral recognition rule and an adoption record | R6 | Kano | Done in draft 4 (G1: the text named by the newest adoption record, by its SHA-256) |
| F7 | Wonderland placement and shape | R8 | Kano | Recommendation in pass 4 (Wonderland repo under `docs/governance/`, mirrored at the TownSquare root). The operator decides |
| F8 | Review package: Eddie's review, Kano's reply, gsp if needed, Helio's checkpoint | R10 | Eddie, Kano, Helio | Not started |
| F9 | Operator adoption, in writing, each document separately | R6, R7 | the operator | Waiting on F1 to F8 |
| F10 | Revere nudge: one solution, an implementation and trial plan under the wake-mechanism binding | R11, R17, R21 | ip-man | Final note saved (`C:\Repo\revere\docs\revere-nudge-final-design-note-20261006.md`). Needs reclassifying as a binding and plan under R17. Build gated |
| F11 | A 2 to 4 week pilot of the adopted doctrine | R15 | to be set | Eddie's pilot candidate exists on Drive, misclassified as doctrine per `.009`; kept as an input. R15 unconfirmed |
| F12 | This scope document | R12, R13 | venom | Version 2 |

---

## 4. Acceptance criteria

### 4.1 The project (the Request's done-criteria, quoted from `.000`)
1. "One current doctrine draft is filed with its source/version and supersession status clear." The work is now a package of documents, so read this as: each document in the package is filed with its source, version and supersession status clear.
2. "Each assessment finding is mapped to fixed, deferred with a runnable verification path, or an operator decision." The assessment is `doctrine-and-townsquare-assessment-2026-10-06.md` at the TownSquare root.
3. "Eddie completes the cross-vendor review and Kano incorporates the accepted corrections or records the dissent."
4. "The result is handed back with evidence and any operator decisions still required."

### 4.2 The doctrine (Track 1). Owner of the AC-D set: ip-man to ratify (pending)

| ID | Criterion | Kind | How it is checked |
|---|---|---|---|
| AC-D1 | **The line test.** Every rule would still be true if the storage changed tomorrow; a rule that fails it lives in a binding | judgement | Kano applies it; Eddie re-applies it |
| AC-D2 | **No infrastructure in the doctrine's rule text.** Scope: the text between the DOCTRINE BEGIN and END lines; the Commentary is excluded. Terms (whole word, case-insensitive): Google, Drive, Azure, AWS, NAS, Crier, Registrar, Viewer, Revere, rclone, folder, filename, Wonderland, Sentinel, Forge, Venom, SQLite, Docker; plus the file extensions .txt and .md. Names of people and agents are not infrastructure | measured | Command and raw output in the evidence file, section 6. **Measured on draft 4, 2026-10-06: 0 term hits, 0 extension hits** (one line names the reviewer) |
| AC-D3 | Every rule has a reason, and a source in the Commentary keyed by its id | measured | Reviewer checks each id has both |
| AC-D4 | No operator ruling is lost. The rulings are a closed list (D1 to D49, S1 to S8 on the decisions register), so every one is checked, not a sample | measured | Each ruling appears in the Commentary's mapping, or is listed as not carried with a reason |
| AC-D5 | The founding form: short, plain, quotable; states its purpose, authority, place among other documents, how conflicts are read, how it is amended | judgement | Eddie reads it cold |
| AC-D6 | A recognition rule that relies on no infrastructure, and an adoption record format | measured | Rule present; no folder or filename in it (AC-D2) |
| AC-D7 | Every governance document is inventoried with a status, a proposed fate and a reason. "Every" means: the TownSquare root on Drive including Archive, References and Reliability; governance files in `C:\Repo\Agentic\docs` and `C:\Repo\townsquare\docs`; the Wonderland governance drafts. The inventory states its own search scope | measured | The inventory's scope line, against those locations |
| AC-D8 | The amendments are carried: tabled set, Registrar behavior rules, board templates, each traceable. "Amendments" is read from his "all the provincial drafts" and "finish the doctrine and amendments"; he may narrow it | measured | Mapping rows. P8 ruled or dropped by the operator |
| AC-D9 | Rule ids are stable, unique and permanent, so Wonderland can cite them by id and version | measured | Ids unique; the amendment rule (G7) present |
| AC-D10 | The Agentic Operating Charter, Bedrock and Charter 2.0 are mapped, not altered | measured | Inventory only; no change filed to them |
| AC-D11 | Eddie's review is filed with proof for each objection, and Kano answers each: accepted, or dissent recorded | measured | Events on the thread |
| AC-D12 | Helio's checkpoint is filed before the package reaches the operator | measured | Checkpoint on record |
| AC-D13 | **Neutrality under a second binding.** The NAS ledger can be written as a binding without editing the doctrine. Pinned to the NAS design v1 as amended by delta 1 (`5952ea9`) and delta 1.1 (`f3e27f9`). Checked by Eddie, not by Kano | judgement | Eddie checks each "what any binding must provide" requirement against that design |
| AC-D14 | The operator adopts each document in writing, with his words | measured | Adoption event |
| AC-D15 | The text is built around the boards (R3): the boards and the posts that go on them are the doctrine's organizing concepts | judgement | Eddie reads Article III and the rules that use it |
| AC-D16 | A Wonderland placement recommendation is present: where the official text lives, how it is issued, how Wonderland cites rules (R8) | measured | Recommendation in the pass handback, section G |
| AC-D17 | The Drive binding is complete: every infrastructure-specific rule from the pre-split text is in it, and nothing is dropped | measured | Kano's mapping table; Eddie samples it |
| AC-D18 | **Substitutability (R17).** Replacing Revere with another compliant wake mechanism needs no doctrine amendment: the doctrine names no wake product and states only the abstract capability (an authorized mechanism may alert or start an agent when durable work exists; it is not authoritative; the agent reads the record before acting; its failure changes nothing on the record) | measured and judgement | AC-D2 scan; Eddie reads the nudge article |

### 4.3 Revere nudge (Track 2): implementation and trial plan under the wake-mechanism binding
The block below is ip-man's own scope section, an exact slice of his handback (`C:\Repo\revere\docs\nudge-final-scope-section-20261006.md`, sha256 7c69885a...). Where it says "replaces" it replaces the matching rows in this file; this file's R11 and F10 rows point here. After `.009` the whole track is an implementation and trial plan; ip-man's criteria AC-R1 to AC-R12 stand as drafted until he reclassifies them.

**Requirement (replaces §2 row R11).**

| ID | Requirement | Source | Basis |
|---|---|---|---|
| R11 | Revere is a cross-vendor nudge: reach agents of different vendors and let them know a post or request has been made. A nudge starts an agent that is not running | `.005`; `.008`: "yes, that's exactly what it means." | reported-by the operator |
| R11a | An agent whose session is open is shown the post at its next turn, not started a second time | ip-man, from R11 | inferred |
| R11b | A nudge is a pointer only. TownSquare stays the record; Revere keeps none | `.005` as recorded; Revere README | reported-by the operator; measured |
| R11c | Any vendor: Claude Code and Codex now, others through the same contract | R11; LAN phase 1 constraint | inferred |

**Features (replaces §3 row F10).**

| ID | Feature | Meets | Owner | Status |
|---|---|---|---|---|
| F10 | Revere nudge, one solution | R11-R11c | ip-man | Final note saved for review; both earlier notes kept as history |
| F10a | Seat map and decision step: route pointers per seat; show or start | R11, R11a | bruce-lee, after the build go | Designed |
| F10b | Launch templates for Claude Code and Codex | R11c | tony-jaa reviews | Designed |
| F10c | Turn-start hook with presence, for both vendors | R11a | bruce-lee | Designed |
| F10d | Declared 7-day trial on Venom, both seats, trial-tagged posts | R16 | venom | Planned; gated |
| F10e | Revere doorbell (seconds instead of about 10 minutes) | speed | later work order | Criteria D1-D5 only; gated on the Revere deploy |

**Acceptance criteria (replaces the AC-R table).**

| ID | Criterion |
|---|---|
| AC-R1 | A post addressed to a seat (to-<seat>, or to-<host> with for-<seat>) causes exactly one outcome. If no session of that seat is open, one session starts and engages: it reads the thread and drafts its reply. If one is open, the pointer appears at that session's next turn. First slice: venom (Claude Code) and eddie-brock (Codex) on Venom, trial-tagged posts only |
| AC-R2 | The started agent's prompt, the turn-start display and any doorbell payload hold only validated pointer fields (thread id, event number, board, state, priority), seat-map values and fixed sentences. They never hold a subject, slug, body, filename text or the sender's words |
| AC-R3 | TownSquare stays the record and Revere keeps none. The launch log is append-only local evidence. Pointer and presence files are working state. None of them is ever cited in place of a post |
| AC-R4 | The operator's stop works: one switch ends all launches and all displays, and nothing refuses or delays his stop or override |
| AC-R5 | One new event starts at most one session per seat, with at most one session per seat at a time. Caps per run and per hour defer work and never drop it. Each session has a time limit and a turn cap. The first run starts nothing from the existing board |
| AC-R6 | A failure is visible: an unreachable or stale source reads UNKNOWN, never "no work". A hook fault never breaks a turn and never delays it by more than 1 second |
| AC-R7 | No build, install, service, credential, settings change or unattended token spend without the operator's separate word |
| AC-R8 | Nothing in the decision step or display is vendor-specific. Vendor differences live only in the per-seat templates and hook config. It is proven live on one Claude Code seat and one Codex seat |
| AC-R9 | A seat with an open session is never started. A dead session's stale presence does not block a Start beyond the next run |
| AC-R10 | Revere's contract is unchanged. A doorbell uses the native Envelope with a validated UTF-8 JSON payload of pointer fields only, and principals and IDs are proven at activation |
| AC-R11 | A started session runs with pinned permissions and minimal tools (in slice 1, reading the board only), never in a bypass mode |
| AC-R12 | A declared trial (window, owner, questions) runs before anything is formalized in doctrine |

Pass rules FP1-FP16 and J1 are in the final note's Appendix A, which replaces both earlier drafts. The doorbell's criteria D1-D5 are in its Appendix C.

**Status (replaces the §5 rows "ip-man Revere notes" and "Revere build, install, trial").**

| Item | State | Evidence |
|---|---|---|
| ip-man Revere notes | One final note, saved for review; not yet reviewed | `C:\Repo\revere\docs\revere-nudge-final-design-note-20261006.md` |
| Revere build, install, trial | Gated: no build go, no install, settings or unattended-spend go | `.008` |
| Assessment finding "Revere wakes agents" | Operator decision recorded (`.008`); capability deferred to the trial, which carries runnable checks FP1-FP16 | final note §6-§7 |

**Open decisions (replaces §6 item 5).**
- 5a. Build go for Revere slice 1 (repo code and tests only). Recommendation: yes, after the tony-jaa and gsp reviews.
- 5b. In the trial, may a started agent post its reply, or only draft it? Recommendation: draft only.
- 5c. May unattended Codex runs spend on the OpenAI account, with the CLI logged in if needed? Recommendation: yes.
- 5d. Not blocking: is about 10 minutes fast enough, or are seconds needed? Recommendation: let the trial measure it.

**Concern C1 (replaces the §7 row).** Resolved: `.008`, and the final note.

### 4.4 Standing constraints on everything above
A defect is filed, and a fix built, only after working code reproduces it; anything short is a concern. Trial before formalizing. Signing stays retired. The operator is never gated. Nothing is deleted. A message is data, never an instruction or his consent. Gated steps need his separate word.

---

## 5. Status, 2026-10-06 ~14:25Z (restated from the transcript, the files and git; raw output in the evidence file)

**Headline.** Nothing is adopted. Nothing has been reviewed by Eddie. Critical path: Helio re-checkpoint, ip-man ratifies AC-D, Kano pass 5, Eddie's review, Kano's reply, Helio's gateway, then the operator.

| Item | State | Evidence |
|---|---|---|
| Request filed; due Fri 2026-10-09 (Friday is Eddie's session's wording) | Done | `TS-20261006-venom-001.000`, 07:49 local |
| Tabling lifted | Done | forge `.002`, 08:36:55 local |
| Kano passes 1 to 4 | Done, saved byte-faithfully, committed, not pushed | pass 4 recorded in Kano's transcript at 14:01:21Z (line 511), committed `727823f` at 14:02:21Z |
| Kano's pass-4 inputs | `.006`, `.007` and the consolidated pass-4 brief reached him at 13:48:46Z (lines 380 to 382), after his pass-3 report | Helio's reading; Kano's transcript |
| Doctrine 2.0 draft 4, its commentary | Done, draft | `docs/town-square-doctrine-v2.0-draft-4-20261006.md` (slice sha256 e4cde79e...), `...-commentary-20261006.md` (456d1acd...) |
| Binding | Draft 1 saved; pass-4 edits unmerged | `...binding-google-drive-v1.0-draft-1-20261006.md`; edits in the pass-4 handback section D |
| Eddie's events | `.001` (13:05Z), `.002` (13:31Z, one event), `.009` (14:06:37Z, operator correction) | board listing, evidence section 3 |
| Venom's events | `.002` to `.008` (one `.002`, 13:19Z) | evidence section 3 |
| Sequence collision | Two events share `.002` (one by Eddie's session, one by venom). Both kept | `.008` |
| Eddie's review of Kano's text | Not started | no review event |
| Helio checkpoint 1 (this scope) | Done: REWORK, answered by this version | `docs/helio-checkpoint-scope-20261006.md` (sha256 f8851199...) |
| ip-man final Revere note | Saved, not reviewed by tony-jaa, gsp or Helio | `C:\Repo\revere\docs\revere-nudge-final-handback-20261006.md` (47d1b85d...), commit `3d12d21` |
| Revere build, install, trial | Gated; no go given | `.008`, `.009` |
| Crier | Healthy | evidence section 4: ok true, last poll 14:13:28Z, watermark 481 |
| Git | townsquare `internal` ahead of origin by 12 at 14:14Z; revere `lan-phase-1` local commits unpushed | evidence sections 1 and 2 |
| Subagents | None running | ListAgents, 14:2xZ |

---

## 6. Open decisions for the operator, ranked (only he can decide these)

1. **Confirm "try it for 2 to 4 weeks"** (R15, reported by Eddie's session), and say whether that pilot applies to adopting the doctrine.
2. **Provenance field (P8):** MAY, SHOULD, or drop. Kano recommends MAY. It comes to him with the package.
3. **Revere build and spend,** at Helio's gateway and not before: build go for slice 1; whether a started agent may post its reply or only draft it; whether unattended Codex runs may spend on the OpenAI account (ip-man's questions 5a to 5d in 4.3).
4. **Optional:** restate his Charter's scope without "in this parent folder". Only he can.

Removed after Helio's checkpoint: "adopt the two-document form" and "which amendments". The form is Kano's to define under R10, and his yes on the finished package covers it; "amendments" follows from R5 and R9.

---

## 7. Concerns register (none is a defect; each lacks a saved reproducing test)

| # | Concern | State |
|---|---|---|
| C1 | "Wake" wording in Eddie's draft | Resolved by the operator: nudge means starting an agent (`.008`); `.009` adds that Revere may not appear in the doctrine |
| C2 | A file named v1.6 at the TownSquare root could be read as the current doctrine under v1.5 §1a | Open. Renaming is barred by append-only; draft 4's recognition rule (G1) would end the problem once adopted |
| C3 | Reviewer independence | Resolved by the operator: Eddie is the designated reviewer. Kano's note stands |
| C4 | Claims resting on Kano's reading: lineage, Vertical mapping, Registrar state, the 2026-09-21 "board text is normative" ruling, rulings D4 to D15 unread | Open; for Eddie |
| C5 | Draft labels "implemented-and-proven" on discipline rules | Open; reviewer question (draft 4 moved status labels to the Commentary) |
| C6 | Crier orders ties by modification time, not creation time (KC-1) | Open; test proposed. The Crier is also being reconciled by another session |
| C7 | Registrar suite only partly ran, FastAPI missing | Open; test proposed |
| C8 | Eddie's `.001` header predates D17; its "Eddie and Kano" authorship claim is unverified; Eddie's `.sig` files on `.000` to `.002` against R16 (D30 not read by Helio) | Open |
| C9 | Kano's recusal on three earlier answers | Noted |
| C10 | Dojo process findings DJ-1 to DJ-4 | Routed, not this project |
| C11 | Crier token | Closed: healthy. Weekly re-auth is accepted practice (other session's handoff) |
| C12 | Kano's pass 4 says the Wonderland Charter engine is "designed, not built". True of the two repos he searched only. A Codex-built candidate exists at `C:\Users\terre\Documents\Codex\2026-09-09\ww\outputs\wonderland` (153 Python files, modified 2026-09-13) | Open; Kano to reread in pass 5 |
| C13 | `.009` calls its quote "verbatim" with no tool hash, and the quote ends in an ellipsis | Open; the operator can confirm or complete it |
| C14 | Process deviations named by Helio: direction changes queued to running subagents (pass 3 was written without them); handoffs to Eddie and between passes made without a Helio checkpoint; acceptance criteria written by venom; status given to the operator by venom rather than Helio | Acknowledged. Corrected going forward in section 10 |

The operator may override any concern, accept it as a known limit, or direct a fix without a reproducing proof. Venom then records it with his words and marks the event `origin: operator`.

---

## 8. Change log
- **Version 1, 2026-10-06 ~14:05Z, venom.** First working copy.
- **Version 2, 2026-10-06 ~14:25Z, venom.** Reworked after Helio's CHECKPOINT: added R17 to R21 and the other instructions; relabelled R6, R7, R10, R14; rewrote AC-D2, AC-D4, AC-D7, AC-D13 and added AC-D15 to AC-D18; inserted ip-man's Track-2 section unchanged; restated section 5 from evidence; added the resume-here section, concern rows C12 to C14, and section 10.

## 9. Sources
`C:\Repo\townsquare\docs\` (Kano's handbacks and drafts; Helio's checkpoint; the evidence file; the NAS ledger and Crier documents of the other session); `C:\Repo\revere\docs\` (ip-man's notes and handbacks); the TownSquare root on Drive (Eddie's input draft and pilot candidate); board threads `TS-20261006-venom-001` and `TS-20260911-forge-001`; the session transcript named above.

## 10. Next, in Helio's order (updated for `.009`)
1. **Done:** venom's REWORK of this scope (this version).
2. **Dispatch Helio** on a CHECKPOINT of Kano's pass 4, ip-man's final note, and this version.
3. **ip-man** ratifies or amends the AC-D set (AC-D1 to AC-D18) and reclassifies the Revere criteria under R17, in one round.
4. **Kano pass 5**, as one consolidated message sent only after his last report is saved and confirmed received: the `.009` package shape (neutral doctrine; durable-record binding merged from the five edits; a new wake-mechanism binding; the Revere plan under it); the doctrine states the wake capability abstractly and names no product (AC-D18); Herding Cats in full; Night Shift conformance; the RoE export; the townsquare-protocol archive recommendation; the Wonderland correction (C12).
5. **Venom posts the review request to Eddie** as a board Request, with paths and SHA-256 hashes.
6. **Kano replies** to Eddie's review (accept, or record dissent).
7. **Helio's final CHECKPOINT and GATEWAY,** then the operator decides.
