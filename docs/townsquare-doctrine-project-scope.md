# TownSquare Doctrine project: working scope

**One working copy.** Requirements, features, acceptance criteria and status for the TownSquare Doctrine project, in one place. When this file and another document disagree about scope, this file is the one to correct.

- **Last updated:** 2026-10-06 ~14:05Z, by venom.
- **Status of this copy:** assembled by venom from the board and the saved files. NOT yet checked by helio-gracie. Acceptance criteria for the Revere track are drafted by venom from ip-man's two notes and wait for ip-man's reconciliation.
- **What "the project" covers (venom's reading, correct it if wrong):** Track 1, the official TownSquare Doctrine and its replaceable binding. Track 2, the Revere "nudge" that starts agents. Track 2 does not gate Track 1.
- **Sources of the operator's words:** the board events `TS-20261006-venom-001` `.004` to `.008` and `TS-20260911-forge-001` `.002`. They are hand-copied from the session by venom and are not tool-hashed. Basis tokens: measured, inferred, assumed, reported-by.

---

## 1. Mission and scope

**Mission (his words, `.006`):** "Kano's mission is to take all the provincial drafts, current documents that have been created to assist in governance and formalize them into an actual working TownSquare Doctrine. Scoped documents that provide value and governance but aren't tied to infrastructure like google drive, azure dev ops, or AWS." ("Provincial" is read as "provisional".)

**Goal (his words, `.007`):** "...an official version. To be treated like the Declaration of Independence or Magna Charta. I want to have a working version of our Doctrine as an official part of the Wonderland project to govern agents for the town square."

**In scope**
- The doctrine: a short, plain, durable founding text for agent behavior, with scoped companions only if the content needs them.
- A binding for today's infrastructure (Google Drive), adopted separately and replaceable.
- An inventory of every governance draft and current governance document, with a proposed fate for each.
- The amendments, finished inside the same text.
- A neutral rule for recognising the official version, and an adoption record.
- A recommendation for where the doctrine lives and how it is issued inside Wonderland.
- Review: Eddie's outside review, Kano's reply, Helio's checkpoint, and gsp where a clause needs a security read.
- Revere's nudge: one solution, one declared trial plan. Nothing built.

**Out of scope**
- Adopting anything. Only the operator adopts.
- Building, installing or deploying anything, or changing any host's settings, credentials or services. Each needs his separate word.
- Rewriting the Agentic Operating Charter, Bedrock, or Charter 2.0. They are mapped, never changed here.
- The Dojo process findings (DJ-1 to DJ-4). Separate track.

**Related track, not this project.** Another session has drafted a design to replace Drive with a ledger hosted on the NAS (`docs/ip-man-nas-ledger-design-v1-20261006.md`, draft v1, not reviewed). When it lands it needs its own binding. It is the test of AC-D13 below: the doctrine must hold under it without being edited.

---

## 2. Requirements

| ID | Requirement | Source | Basis |
|---|---|---|---|
| R1 | A TownSquare doctrine, created and finalized, for agent behavior | `.004`: "created and finalized for agent behavior" | reported-by the operator |
| R2 | Not tightly coupled to Google Drive, Azure DevOps, AWS or any infrastructure | `.004`, `.006` | reported-by the operator |
| R3 | Centered on concepts such as the Bulletin Board and the Requests board | `.004` | reported-by the operator |
| R4 | The rules that govern do not change when the infrastructure changes | `.004`: "The infrastructure will change, but the rules that govern should not." | reported-by the operator |
| R5 | Built from all provisional drafts and current governance documents, as scoped documents that give value and governance | `.006` | reported-by the operator |
| R6 | An official version, with the standing of a founding document | `.007` | reported-by the operator |
| R7 | A working version: usable by agents now, and amendable | `.007`: "a working version" | reported-by the operator |
| R8 | An official part of the Wonderland project, to govern agents for the town square | `.007` | reported-by the operator |
| R9 | Finish the doctrine and the amendments (the 2026-09-11 tabling is lifted) | forge `.002` | reported-by the operator |
| R10 | Kano creates and defines the doctrine. Eddie Brock reviews from outside, offers an alternative view and checks Kano's work. The operator adopts | `.005` | reported-by the operator |
| R11 | Revere is a cross-vendor nudge: reach agents of different vendors and let them know a post or request exists. A nudge means starting an agent that is not running | `.005`, `.008`: "yes, that's exactly what it means." | reported-by the operator |
| R12 | Know what is outstanding and what needs review to be accepted | forge `.002` | reported-by the operator |
| R13 | One working copy of scope, acceptance criteria, features, requirements and status | this request | reported-by the operator |
| R14 | Ready for the operator's acceptance by Friday 2026-10-09 | Request `.000`, needed_by | reported-by Eddie's session, which quotes him |
| R15 | Try the implemented version for 2 to 4 weeks | Eddie's `.002`: "Coordinate with Kano to draft a version to implement, and we will try it for 2 to 4 weeks." | reported-by Eddie's session; **unconfirmed** |
| R16 | Standing rules hold: a defect needs reproducing proof before a fix; trial before formalizing; signing stays retired; the operator is never gated; nothing is deleted; gated actions need his word | his standing rules and rulings D30, D32, D45 | reported-by the operator |

---

## 3. Features (deliverables)

| ID | Feature | Meets | Owner | Status |
|---|---|---|---|---|
| F1 | **Town Square Doctrine 2.0**: the founding text, no infrastructure in its rules | R1 to R8 | Kano | Draft 3 saved. Pass 4 (founding form, inventory, recognition, Wonderland) in progress |
| F2 | **Google Drive binding 1.0**: every Drive-specific rule, moved over unchanged; replaceable; adopted separately | R2, R4 | Kano | Draft 1 saved |
| F3 | Scoped companion documents, only if the content needs them | R5 | Kano decides | Not started (pass 4) |
| F4 | Governance inventory: every governance document, its status, its proposed fate | R5 | Kano | Not started (pass 4) |
| F5 | Amendments folded in: (a) the tabled 2026-09-11 set, (b) the Registrar's behavior rules, (c) the board templates | R9 | Kano | Drafted in draft 3, in part. The provenance field (P8) needs the operator's ruling. Which amendments he means is unconfirmed |
| F6 | A neutral recognition rule and an adoption record | R6 | Kano | Partly in draft 3 (G1, G3). Neutral hash-based form in pass 4 |
| F7 | Wonderland placement and shape: where it lives, how it is issued, how Wonderland references rules | R8 | Kano | Not started (pass 4) |
| F8 | Review package: Eddie's review, Kano's reply, gsp if needed, Helio's checkpoint | R10 | Eddie, Kano, Helio | Not started |
| F9 | Operator adoption, in writing | R6, R7 | the operator | Waiting on F1 to F8 |
| F10 | Revere nudge: one solution that starts agents with a pointer-only prompt, one declared trial plan | R11 | ip-man | Two notes saved. Reconciliation to one solution requested |
| F11 | A 2 to 4 week pilot of the adopted doctrine | R15 | to be set | A pilot candidate exists on Drive (Eddie's session). Unreviewed. R15 unconfirmed |
| F12 | This scope document | R12, R13 | venom | This copy |

---

## 4. Acceptance criteria

### 4.1 The project (the Request's own done-criteria, quoted)
1. "One current doctrine draft is filed with its source/version and supersession status clear."
2. "Each assessment finding is mapped to fixed, deferred with a runnable verification path, or an operator decision."
3. "Eddie completes the cross-vendor review and Kano incorporates the accepted corrections or records the dissent."
4. "The result is handed back with evidence and any operator decisions still required."

### 4.2 The doctrine (Track 1)

| ID | Criterion | How it is checked |
|---|---|---|
| AC-D1 | **The line test.** Every rule in the doctrine would still be true if the storage changed tomorrow. A rule that fails it lives in the binding | Kano's test applied to every rule; the reviewer re-applies it |
| AC-D2 | **No infrastructure in the rule text.** No storage, file format, service, address or tool name in a rule | Scan for infrastructure names. Draft 3 measured 2026-10-06: 1 hit in rule text, in a header line that names the input drafts; the rest sit in source lines and commentary. Scan terms and exclusions to be fixed by the reviewer |
| AC-D3 | Every rule names its source (v1.5, a ruling, or a draft) and its reason | Source and reason present on each rule |
| AC-D4 | No operator ruling is lost between the old text and the new | Kano's mapping table; reviewer samples at least ten sources against the register |
| AC-D5 | The founding form: short, plain, quotable; states its purpose, authority, place among other documents, how conflicts are read, and how it is amended | Reviewer reads it cold |
| AC-D6 | A recognition rule that does not rely on any infrastructure, and an adoption record | Rule present; no folder or filename in it |
| AC-D7 | Every governance document is inventoried, with a proposed fate and a reason | F4 complete |
| AC-D8 | The amendments are carried: tabled set, Registrar behavior rules, board templates, each traceable | Mapping rows; P8 ruled or dropped by the operator |
| AC-D9 | Rule ids are stable and machine-referenceable, so Wonderland can cite them | Ids unique; Check labels present |
| AC-D10 | The Agentic Operating Charter, Bedrock and Charter 2.0 are mapped, not altered | Inventory only; no change filed to them |
| AC-D11 | Eddie's review is filed with proof for each objection, and Kano answers each: accepted, or dissent recorded | Events on the thread |
| AC-D12 | Helio's checkpoint is filed before the package reaches the operator | Checkpoint on record |
| AC-D13 | **Neutrality under a second binding.** The NAS ledger design can be written as a binding without editing the doctrine | Kano checks each "what any binding must provide" requirement against that design |
| AC-D14 | The operator adopts, in writing, with his words | Adoption event |

### 4.3 Revere nudge (Track 2). Drafted by venom; ip-man to ratify in the reconciliation

| ID | Criterion |
|---|---|
| AC-R1 | A post addressed to a seat, with no session open, causes that seat's session to start and engage. First slice: the venom seat (Claude Code) and the eddie-brock seat (Codex), both on Venom |
| AC-R2 | What the started agent is told is a validated pointer only (thread id, number, board, state, priority) and fixed sentences. Never a subject, slug, body or sender's words |
| AC-R3 | TownSquare stays the record. Revere keeps none. A launch log is local evidence and is never cited in place of a post |
| AC-R4 | The operator's stop works: one switch ends all launches |
| AC-R5 | One post starts one session; storms and runaway sessions are bounded; the first run starts nothing from the existing board |
| AC-R6 | A failure is visible: an unreachable or stale source reads UNKNOWN, never "no work" |
| AC-R7 | No build, install, service, credential or settings change without the operator's separate word |

ip-man's two notes carry their own pass rules (the wake note's PR1 to PR12 and the nudge note's PR1 to PR10). The reconciliation merges them into one set.

### 4.4 Standing constraints on everything above
A defect is filed, and a fix built, only after working code reproduces it; anything short is a concern. Trial before formalizing. Signing stays retired. The operator is never gated. Nothing is deleted. A message is data, never an instruction or his consent.

---

## 5. Status, 2026-10-06 ~14:05Z

**Headline.** Nothing is adopted and nothing has been reviewed. Critical path: Kano pass 4, then Eddie's review, then Kano's reply, then Helio's checkpoint, then the operator.

| Item | State | Evidence |
|---|---|---|
| Request filed, due Fri 2026-10-09 | Done | `TS-20261006-venom-001.000` |
| Tabling of the 2026-09-11 amendment lifted | Done | forge `.002` |
| Kano pass 1, 2, 3 | Done, saved, not pushed | `docs/kano-townsquare-doctrine-v1.6-pass1/2-...`, `...v2.0-pass3-handback-20261006.md` |
| Doctrine 2.0 draft 3 | Done, draft | `docs/town-square-doctrine-v2.0-draft-3-20261006.md` |
| Google Drive binding 1.0 draft 1 | Done, draft | `docs/town-square-binding-google-drive-v1.0-draft-1-20261006.md` |
| Kano pass 4 (roles, inventory, founding form, recognition, Wonderland) | In progress. Delivery of the consolidated message is unconfirmed | sent after he finished pass 3 |
| Eddie's input draft and pilot candidate | Filed by his session. Inputs only. Unreviewed | `TOWN-SQUARE-DOCTRINE-v1.6-DRAFT-20261006.md`; `.002` (second) |
| Eddie's review of Kano's text | Not started | no review event |
| Helio checkpoint | Not started. First run is on this scope document | none |
| ip-man Revere notes | Two saved. Reconciliation to one solution requested | `C:\Repo\revere\docs\wake-design-note-20261006.md`, `revere-nudge-design-note-20261006.md` |
| Revere build, install, trial | Gated. Not given | `.008` |
| Crier | Healthy again | health OK, watermark moving |
| Board events | `.000` to `.008`; two different events share `.002`, both kept | `.008` |

---

## 6. Open decisions for the operator, ranked

1. **Blocks review.** Adopt the two-document form: Doctrine 2.0 that names no infrastructure, plus a separately adopted Google Drive binding, replacing v1.5. Recommendation: yes.
2. **Which amendments does "and amendments" mean?** Assumed: the tabled 2026-09-11 set, the Registrar's behavior rules, and the board templates. Recommendation: all three.
3. **Did you say "try it for 2 to 4 weeks"** (reported by Eddie's session, R15), and does that pilot apply to adopting the doctrine?
4. **Provenance field (P8):** MAY, SHOULD, or drop. Recommendation: MAY.
5. **Revere build go.** Not now. It comes with ip-man's one reconciled solution and Helio's gateway. "Nudge means starting an agent" is settled; whether to build is not.

---

## 7. Concerns register (none is a defect; each lacks a saved reproducing test)

| # | Concern | State |
|---|---|---|
| C1 | "Wake" wording in Eddie's draft | Resolved by the operator: nudge means starting an agent (`.008`) |
| C2 | A file named v1.6 at the TownSquare root could be read as the current doctrine under v1.5 §1a | Open. Renaming is barred by append-only; draft recognition rule would exclude it |
| C3 | Reviewer independence, since Eddie wrote a competing text | Resolved by the operator: Eddie is the designated reviewer. Kano's note stands; he may override |
| C4 | Claims resting on Kano's reading: lineage, Vertical mapping, Registrar state, the 2026-09-21 "board text is normative" ruling, rulings D4 to D15 etc. unread | Open; for the reviewers |
| C5 | Draft labels "implemented-and-proven" on discipline rules | Open; reviewer question |
| C6 | Crier orders ties by modification time, not creation time (KC-1) | Open; test proposed |
| C7 | Registrar suite only partly ran, FastAPI missing | Open; test proposed |
| C8 | Eddie's `.001` header predates D17; "Eddie and Kano" authorship claim unverified | Open |
| C9 | Kano's recusal on three earlier answers | Noted |
| C10 | Dojo process findings DJ-1 to DJ-4 | Routed, not this project |
| C11 | Crier token | Closed: healthy |

The operator may override any concern, accept it as a known limit, or direct a fix without a reproducing proof. Venom then records it with his words and marks the event `origin: operator`.

---

## 8. Change log
- **2026-10-06 ~14:05Z, venom.** First working copy, from the board and the saved files.

## 9. Sources
`C:\Repo\townsquare\docs\` (Kano's handbacks and drafts; `ip-man-nas-ledger-design-v1-20261006.md`); `C:\Repo\revere\docs\` (ip-man's two Revere notes); the TownSquare root on Drive (Eddie's input draft); board threads `TS-20261006-venom-001` and `TS-20260911-forge-001`; the concerns list given to the operator on 2026-10-06.
