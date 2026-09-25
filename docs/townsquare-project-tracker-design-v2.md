<!-- verbatim sha256=954df5dc957aea2de168b41837ee8d4687e2fc3cef5fca98828d32f0fc0e642b source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a8619247e640a0585.jsonl:347 message=msg_011CfQCAYLeJriJ9SYtHRfMp -->
# TownSquare project tracker, v2: rulings on jigoro-kano's review, and the `binding: offsite` consumers

**Author:** ip-man (Claude) · **Date:** 2026-09-25 · **Status:** recommendation only. No build has been commissioned.

**Proposed path:** `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md` on branch `internal`, next to v1.

**Read this together with:**
- v1, `C:\Repo\townsquare\docs\townsquare-project-tracker-design.md`. Its first line records sha256 `dfb3dc4859b3093225bf0cca8214b9bf8f7fb3e740f1ff0ef8673840cd0202f7` (I read the comment; I did not re-hash the file).
- kano's review, `C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md`, sha256 `c7b4f0a412307724682a4a5ae151f4445735e60c42a9a31b86ecc0b491f021eb`.

**v1 still stands except where §0 below says otherwise.**

**Labels and shorthand** are the same as v1. New in this note:
- **A1–A5** are kano's amendments.
- **K1–K7** are my questions to kano, with his answers.
- **RH** is the Request Handling Process Doctrine v1.0.
- **C3, C6** are clauses of kano's receipt check (his B.3).
- **P0–P5** are the steps of the pre-registration check in §5.

**Recusal, extended.** This note answers A1–A5 and lists the consumers of `binding: offsite`. §5 also cites the receipt design (`TS-20260913-forge-014`), and its host-keying was my own earlier answer. If any of these questions is referred to the Tribunal, I am conflicted and will not sit on it.

## 0. What v2 changes in v1

| v1 | Change | Why |
|---|---|---|
| §4: nesting is strict | This becomes **Sensei's decision 2**. The spec for both answers is in §1. | A2 |
| §4/§8: the scoping event sets `level:` | Scoping keeps `level: unscoped`, and Sensei's yes sets the level. Children he confirmed carry a pointer to that yes (tier 2). | A3 |
| §8: the scoping note leads with the breakdown | The note leads with a reflect-back and questions. | A4 (RH §1) |
| §6: projector rules | Adds header-reading rules and an output contract. | A5 |
| §5: the claim link is `parent:` on the claimer's Request | The claim link is `references:` on the SEEK's CLOSED event. | K4 |
| §7: "front door" was the whole relationship; the `.010` rejection | The relationship has two parts. The in-flight part is **Sensei's decision 5b**. The `.010` argument is withdrawn. | A1, and kano's A.1 |
| §7: join 1 | Also pins the newest event id read on the parent chain. | K3 |
| §9: the trial Bulletin was a label only | Uses kano's A.4 text, amended. Adds a trial window and a fourth trial question. | K1, K6 |
| §10: decisions | Replaced by §4 below. | all |
| Work order | Replaced below. | none |

## 1. The two open decisions that belong to Sensei (A1, A2)

Sensei's "proceed as planned" (reported-by session) is not a ruling on either decision. Treating it as one would be the D3 pattern: an agent writing a rule into its record of an operator's words.

### A1: BB8.005 also says "VERTICAL IS THE TRACKER"

**The finding is accepted.** My §7 quoted only half of the event. The same event says "V1 ....... Vertical REPLACES Jira and ADO. It is the system of record." It also records the net effect on scope: "In, and larger than before: being the system of record for the work itself" `[measured: BB8.005, re-read]`. So the tracker's in-flight states (WORKING → RESOLVED → CLOSED) cover the span BB8.005 assigns to Vertical.

**Where I sharpen kano's framing.** There are only two lifecycle authorities if YNM's own fleet work runs through Vertical once Vertical exists. BB8.005 defines Vertical as a product. It does not say the fleet's own board has to move into it. That turns A1 into a question Sensei can answer directly:

**"When Vertical runs, does the fleet's own work run through it?"**
- **If yes:** the tracker's in-flight states are interim. At Stage 2, Vertical's design adds the hand-off: a Story records that it crossed into Vertical, and it closes when Vertical reports it deployed or dropped.
- **If no:** the tracker remains the fleet's record from start to finish, and Vertical is the system of record wherever an organisation deploys it.

**The permanent half holds either way.**
- Intake, vetting, scoping and the Definition of Ready (DoR) stay outside Vertical, per BB8.005's first clause.
- The entry contract stays the same (§3, K3): the Story's thread id, its content hash, and the newest event id read on its parent chain.

**Recommendation.** Answer this at Stage 2. Until then, the trial uses kano's "interim" label, which commits Sensei to nothing. My v1 Vertical note (§10 B) built the Vertical integration around a Dojo work order as its reference case, which leans toward "yes". Still, this is his scope decision, and nothing is lost by making it at Stage 2.

**Withdrawn from v1 §7:**
- The `.010` argument against "a precursor Vertical absorbs". kano's A.1 is right: `.010` says Vertical must not be limited to YNM; it does not keep YNM's own work out of Vertical.
- "The tracker never reads Vertical." That only holds until the hand-off is designed.

### A2: nesting as required lineage, or as ordered levels

**The cost finding is accepted.** Under v1, the smallest tracked ask in a new project takes three threads: an Epic, a Feature and a Story. TSD 0.4 and §11 name ceremony as the failure most likely to make the board a net negative.

**Both readings fit Sensei's words**, "a traditional agile nesting approach". Both also keep the brief's gloss: "an Epic contains multiple Features; a Feature contains multiple Stories". So the choice is his.

| | (a) Strict lineage (v1) | (b) Ordered levels, parent optional (kano) |
|---|---|---|
| `parent:` | required on Features and Stories | optional at every level; when present, it points exactly one level up |
| `project:` | on Epics | on every item that has no parent |
| DoR line 1 | "its parent is a Feature" | "if it has a parent, the parent is a Feature" |
| Smallest ask | three threads | one thread |
| Rollup | every Story reaches an Epic | parentless items show directly under their project, and the projector lists them |

**Recommendation: (b).** Common agile trackers behave this way, and (b) removes the ceremony cost without hiding anything.

**What would change my mind:** if Sensei wants every Story to roll up to an Epic for portfolio views, then (a) is right and the extra filings are worth it.

Nothing is filed before he answers, because the trial itself waits on his go.

## 2. A3–A5

### A3: accepted, with one refinement

- The scoping event keeps `level: unscoped` and puts the proposed level in its body.
- The event that transcribes Sensei's yes carries `origin: operator` and sets `level:`, `parent:`, `project:` and `repo:`.

**Refinement for children.** The session files children after his yes, so each child's own level-setting event would otherwise show `origin: agent`.
- A child he confirmed by name is filed with `origin: operator` and `references: <his confirmation event> (evidence)`. TSD §3a accepts that pointer to his words as tier-2 proof. It is not borrowed authority, because he approved exactly those items.
- Anything added later without his yes stays `origin: agent` and is reported as unconfirmed.

**The result: "confirmed" can be decided per item.** An item is confirmed if the event that set its current `level:` carries `origin: operator`.
- The projector can check that the field is present. Whether the claim is genuine is left to people (TSD §2), exactly as in kano's C5.
- All four DoR lines can now be checked by the projector.

### A4: accepted, after checking RH myself

RH §1 says an agent's "FIRST response is to reflect back what it understood and ask clarifying questions… NOT to propose structure". RH §3 adds that this is "not a license to stall on obvious or already-settled requests" `[measured]`.

The scoping note therefore has four parts, in this order:
1. WHAT I UNDERSTOOD
2. QUESTIONS. **Stop here if any answer would materially change the breakdown.**
3. PROPOSED LEVEL AND BREAKDOWN, with acceptance criteria and a lane for each child
4. WHAT STAYS OPEN

### A5: accepted, and tightened

The projector reads tracker fields only under these rules:
- **Only from a header block that ends at a line that is exactly `---`.** A file with no such line contributes no tracker fields, so a body line like `NEXT:` in an old header-less file can never be read as a key.
- **Keys start at column 0 and match case-insensitively**, as `ts-file.sh` does (reported-by kano). An indented line is a continuation, never a key.
- **A tracker key that appears twice in one header** is flagged for that event and ignored, never guessed.
- **Last activity comes from Drive `createdTime`**, the time D20 arbitrates on. `at:` is for display only, so a date-only `at:` (as on kano's claude-app card) is harmless.
- **Output contract:** groupings are a non-monotone view of current state. Nothing may use them for routing, notification, receipt or a Vertical entry without pinning the event ids it read. Stating this lets a consumer detect a violation (D41).
- **`next:` is a copy.** It authorizes nothing (K2).

ronda-rousey's fixtures add one case per rule.

## 3. K1–K7: what I add to kano's readings

- **K1: accepted.**
  - The vehicle is Sensei's trial approval in his own words. D40, the precedent I cited, was itself a numbered ruling on the register.
  - The trial Bulletin uses kano's A.4 text with three amendments:
    1. "WHAT THOSE WORDS APPROVE" names v1 and v2 by path and SHA-256.
    2. It states the nesting rule he chose.
    3. It states the window he sets, or the window Helio proposes in his Pace line and Sensei accepts.
  - kano names the window's harm: "an unbounded trial becomes doctrine without adoption".
  - The D-number cross-reference does not gate the trial.
- **K2: accepted in full.**
  - The header `next:` is the session's one-line summary.
  - The event body carries Helio's `Next:` block, extracted with save_verbatim.py, together with its SHA-256.
  - If the summary and the block differ, the block wins.
  - On Epics and Features, `next:` is the session's own statement.
- **K3: accepted.** The caveat becomes part of the entry contract in §1. A Vertical entry pins three things: the Story thread id, the content hash, and the newest event id read on the parent chain. This follows the same write-time-snapshot principle as Vertical's `workflow_ref`.
- **K4: accepted.** Carrying the claim link is an addition to §7b, not a reinterpretation.
  - I take kano's cheaper link. The claimer's CLOSED event on the SEEK names the claimer's new Request in `references:` (D19; any type), and the projector follows SEEK → Request. Other hosts learn no new field.
  - `parent:` on a TS post remains the way venom attaches its own sub-requests.
  - Expecting other hosts to carry the link belongs in the post-trial TSD amendment, for Sensei to adopt.
- **K5: accepted.**
  - `name:` is the agent that wrote the file.
  - The party whose ask it is goes in `basis:` as `reported-by <party>` (D46).
  - The projector reads the first `reported-by <party>` in `basis:`. If there is none, it shows none.
- **K6: accepted, both halves.**
  - Decision 5a states that it does not adopt the DoR as Vertical's entry requirement.
  - For Shuri's asks, Sensei's yes rests on "I will always initiate and sign off on any real work making it to production or the main branch" (`BB-20260906-008.002`) `[measured]`.
  - The trial gains a fourth question: in how many scopings did his yes change anything?
- **K7: accepted.** kano's case-insensitive search replaces my possibly incomplete one.
  - Vertical's `authority-designation` `scope` field could collide with D16's `scope:`. The collision is latent: it only becomes real once Vertical publishes to TownSquare.
  - It is routed to the Vertical design line (owner: ip-man) for when Stage 2 resumes. This job does not touch Stage 2.
- **kano's handoff note: an eddie-brock review of the post-trial amendment.** That review would come after the trial. Nothing in this job depends on it.

## 4. Decisions for Sensei (replaces v1 §10; Helio queues them one at a time)

1. **Architecture: option C.** kano agrees.
2. **Nesting (A2):** (a) strict lineage, or (b) ordered levels with optional parents. Recommended: (b).
3. **Trial go or no-go**, on v1 §9 as amended here, using kano's Bulletin text and a trial window.
4. **Intake:**
   - ip-man scopes each ask, reflect-back first.
   - Sensei gives one yes per scoping before any children are filed.
   - For Shuri's asks, that yes is his initiation (`BB-20260906-008.002`).
5. **Vertical:**
   - **5a.** The tracker is Vertical's external gateway, using the entry contract. This does **not** adopt the DoR as Vertical's entry requirement.
   - **5b (A1).** When Vertical runs, does the fleet's own work run through it? Recommended: answer at Stage 2. Until then, the "interim" label commits him to nothing.

Decisions 1–3 gate the trial. Decision 4 shapes it. Decision 5 does not gate the trial, but it is in front of him when he decides, as kano asked.

**Dissent.** kano's dissent line stands as he wrote it. v2 departs from his amendments in three places, and Sensei should see all three:
- A1 is framed as a question about the fleet's own work, not as a settled "interim".
- A3 adds the tier-2 rule for children.
- §5 corrects two items in his list.

If Helio judges that kano should answer these before Sensei decides, that is one ESCALATE, and it is Helio's call.

## 5. Deliverable B (a separate problem): consumers of `binding: offsite`

### The contract today

- **Registry v1.6 §2:** "`binding` is the operator's flag: an agent either belongs to a host, or is a portable subagent." That gives two values: `host:<Name>` and `portable`.
- **§2.3:** agent rows "join to [the hosts table] through their `binding` column". `portable` "points at no row" `[measured]`.
- **D29:** with D28, "the keys are held per HOST, joined to agent rows through the `binding` column". The `binding` column is also one of the fleet's three copies of the host list `[measured: BB-20260911-forge-001.027]`.
- **The service is primary (D34).** It derives "section… from binding" `[reported-by bishop: BB-20260912-bishop-002.000]`.
- **Its code** is in the private Wonderland repo, under `services/registry/` `[same source]`. It is **not cloned on Venom** `[measured: glob]`.

A third value changes the shape of this contract. So, following the standing ruling, each consumer below gets either a migration or a deferral with a named owner.

### Consumers

1. **Registry `POST /register`.**
   - **Today:** it accepted `portable` with an empty pubkey and host_address `[reported-by session memory, measured 2026-09-13]`. The validation code has not been read.
   - **With `offsite`:** it may reject the value, or accept it without checking.
   - **Migration:** P0–P5 below. Session reads the code; bishop owns any fix.
   - **Before the POST?** Yes.
2. **Registry `section` derivation.**
   - **Risk:** a two-way rule could file `offsite` as host-bound (and then look up a host named "offsite") or as portable.
   - **Migration:** P0 and P3 confirm which section it gets. A third section, if needed, is bishop's.
   - **Before the POST?** Yes.
3. **Registry `GET /authorized_keys` and `GET /mesh`, plus any "which hosts exist" derivation from `binding` values.** This is the load-bearing item.
   - **Risk:** if the host join throws on an unfamiliar value, the keyring endpoint returns an error.
   - **Why that matters:** the fleet's published sync one-liner is `curl -s` with no `-f`, and it appends every line it receives to `~/.ssh/authorized_keys` `[measured: BB-20260912-bishop-002.000]`. Hosts sync "on startup" or on their next poll, so an error body would be written into `authorized_keys` on every syncing host `[inferred: curl without -f passes error bodies through]`. sshd skips malformed lines, so this is pollution, not a lockout.
   - **Separately:** the `/mesh` inventory and forge's pending host-list reconciliation read `binding` values as host names. `offsite` is not a host.
   - **Migration:** P0, then P1/P3 require the keyring and mesh to be byte-identical before and after the POST. If they are not, run P5. bishop owns any fix.
   - **Before the POST?** Yes.
4. **Registry Crier-feed ingest** (upserts with `last_source: crier:<agent>`; open defects bishop-007 and bishop-009).
   - **The precedent may not apply.** The on-behalf jigoro-kano and helio-gracie registrations left rows untouched, but those bulletins carried no `cat-registration` token `[reported-by session memory]`. That precedent may not cover a bulletin that carries the token. bishop-009's substring detection could also match on the slug.
   - **Migration:** P4 re-reads both the new row and venom's own row, because venom's `from-` is on the bulletin. bishop owns any fix.
   - **Before the POST?** Yes.
5. **Revere broker** `[measured: C:\Repo\revere\src\revere\registry.py:62-63; broker.py:90, 120; docs\design-note.md §9]`.
   - **Today:** it authorizes subscribe (receive) and publish (send) on `status == "active"` alone and ignores `binding`.
   - **With `offsite`:** an active `claude-app` becomes a valid Revere subscriber. That is venom-015's "address that cannot receive", reproduced inside Revere.
   - **Harm today is nil:** Revere is loopback-only, its wire protocol has no credential field, and claude-app is off the LAN.
   - **Deferred.** If Revere ever goes off-host or starts reading `binding`, subscribe should require a binding that can receive. Owner: ip-man, through a Revere work order.
   - **Before the POST?** No.
6. **The registry document.**
   - **What changes:** v1.6 §2 (two-way wording), §2.2 (its open "third category" question, which `offsite` must not absorb), §2.3 (the join rule), and §5–§6 ("registers ITSELF and its host SSH key").
   - **The repo mirror** `agents/REGISTRY.md` "must not diverge", and D48 measured the board against it. It is not in Venom's Agentic checkout `[measured: glob]`.
   - **Migration:** reissue as v1.7 under TSD §1a right after the POST. venom can do this as the registering host; forge issued v1.2–v1.6.
   - **Before the POST?** No; the reissue follows it.
7. **Onboarding texts:** D34b ("register themselves and their keys") and `C:\Repo\Agentic\host-agents\templates\host-agent.template.md:172-176` `[measured]`.
   - **Situation:** claude-app can post its own bulletin, because it writes to Drive. It cannot reach the LAN service, and it has no key.
   - **Migration:** none. The on-behalf precedent covers it: "the installing session files the bulletin and `POST /register` on its behalf and says so" (`C:\Repo\Agentic\memory\dojo-agent-crew.md:19`). The template covers host agents only.
   - **Before the POST?** No.
8. **D48 addressing allowed-list check** (a gate spec routed to jigoro-kano; not built).
   - **Requirement:** it must pass `offsite` as a sender and fail it as an addressee. That is kano's reason for a distinct value.
   - **Migration:** put it in the spec. Owner: jigoro-kano.
   - **Before the POST?** No.
9. **D18 R2 `to`/`for` mismatch finding, and kano's C3/C6** (all prose-only today).
   - **Situation:** these map agent to host, and `offsite` has no host.
   - **Migration:** each should report a finding, never throw an error. Owners: jigoro-kano's spec; francis-ngannou and ronda-rousey if it is ever built.
   - **Before the POST?** No.
10. **D49, "fleet = all registered agents".**
    - **Situation:** every doctrine marked "BINDING ON EVERY FLEET AGENT" (TSD 0.2 cadence, RH §4), and every `to: fleet` post, then nominally covers a writer that cannot poll.
    - **Migration:** the registration bulletin states the exemption, as kano's B.6 already does. The tabled TSD amendment scopes those obligations by binding (jigoro-kano drafts, Sensei adopts).
    - **Before the POST?** No.
11. **This tracker.**
    - **Situation:** claude-app becomes a third filing path for Sensei's own asks.
    - **Migration:** none. On receipt, venom appends `level: unscoped` when the ask is project work, and the source is read from `basis:`. Owner: ip-man.
    - **Before the POST?** No.

### Two corrections to kano's starting list

- **"The Registrar's future principal access lists" is not a consumer.** Its design "does not change, query, or couple to the Agent Registry" (design §2; acceptance criterion 14) `[measured]`. The effect lands on posts instead. claude-app can never reach the LAN-bound Registrar, so every post it makes is a direct Drive write that the Registrar's reconciliation reports as a bypass. That is deferred to Registrar phase B, where kano's `post:delegate` route belongs. Owner: ip-man.
- **"Any receipt view keyed on agents": the receipt design is keyed on hosts.** The design says "THE UNIT IS THE HOST, NOT THE AGENT" `[measured: TS-20260913-forge-014.001]`. An offsite agent has no host and no poller, so it never gets a row. That holds only if the view's host set does not come from `binding` values (D29 names `binding` as a host-list copy). If it does come from `binding`, `offsite` shows up as a phantom host stuck at NOT ENROLLED. tony-jaa's Gate-0 decision doc should name where the host set comes from.

### Checked and found not to be consumers

- The Crier. The repo copy reads no registry; I did not read the deployed copy.
- The pollers and `ts-file.sh` (kano reports no lookup).
- Vertical `src\` (grep).
- Cerebra and Cerebro (no reference under `C:\Repo`).
- The Ansible inventory, which holds hosts only.
- The Agentic agent files (grep).
- Charter 2.0's cross-vendor dereference. It reads `vendor` and `model`, not `binding` (F-41).
- Signing. Verification is off, and a keyless agent's events are "unknown", never "failed" (`crier.py` lines 255–264).

### Pre-registration check

Every step is a read except P2, which is Sensei's to approve.

- **P0 (mandatory before P2).** Read `services/registry/` in the Wonderland repo for three things:
  - the binding validation;
  - the section derivation;
  - whether the keyring join iterates rows it cannot map, retired rows included.

  **This step is mandatory because P5's only undo is `status: retired`, and there are no deletes. If the join still iterates retired rows, retiring the row will not repair it.** If the code cannot be read, hold P2 and send a Request to bishop.
- **P1.** Capture `GET /registry`, `GET /authorized_keys` and `GET /mesh`.
- **P2.** `POST /register` for claude-app.
- **P3.** Capture them again and compare:
  - the registry has exactly one new row, and its `section` is not host-bound;
  - the keyring and mesh are byte-identical to P1.
- **P4.** After the doctrine's worst-case latency of 10 minutes (TSD §9), re-read the claude-app row and venom's row. Both should be unchanged.
- **P5.** If any check fails: retire the row, and file a Request to bishop.

**Separately, whatever Sensei decides:** the published sync one-liner should use `curl -fsS`, so that an HTTP error never reaches `authorized_keys`. The session files this as a Request to bishop.

### Limits of this pass

I could not reach:
- the service code;
- how each host actually runs its sync;
- anything built privately on other hosts.

bishop's own list is the complement to this one.

**My view on adopting the value:** nothing in this pass argues against it. One consumer, the keyring, has to be checked before the POST, because its failure reaches every host.

```
WORK ORDER — tracker v2 + binding consumers (recommendation only; no build commissioned)
- Document: the session saves this with save_verbatim.py, printing its SHA-256, to
  C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md (branch `internal`), beside v1 and
  kano's review — reviewed by jigoro-kano already (A1–A5, K1–K7); no second kano round
- Coordinate: helio-gracie — CHECKPOINT on the set (v1, kano's review, v2); final CHECKPOINT + GATEWAY
  before Sensei sees any of it. §4's decisions go one at a time, A1 and A2 marked as his. kano's
  dissent line travels as he wrote it, beside v2's three departures. kano's Deliverable B decision
  (his B.7) travels with §5 as the consumer list the standing ruling requires
- Implement: none yet — pending Sensei's decision
- Peer review: none further — v2 is the answer to kano's review; any follow-up is Helio's ESCALATE
- QA: none — no code changes in this job
- Done when: (1) v2 is saved with its SHA-256; (2) Helio's GATEWAY has put §4's five decisions and
  kano's Deliverable B decision to Sensei, one at a time; (3) no trial artifact is filed before
  decisions 1–3; (4) no POST /register for claude-app happens before P0 and P1, and P3–P5 follow it
  at once
- Watch for:
  (a) A1 or A2 defaulted silently — the trial Bulletin states only what he chose;
  (b) the keyring hazard (§5 item 3) — the one consumer whose failure reaches every host;
  (c) Revere's binding-blind authorization (§5 item 5) — deferred, not forgotten;
  (d) Vertical Stage 2 untouched — the A1 hand-off, the entry contract and the `scope` collision wait;
  (e) bishop follow-ups (P5, the curl -fsS fix) go as TownSquare Requests, never as a dependency of
      the tracker trial
```