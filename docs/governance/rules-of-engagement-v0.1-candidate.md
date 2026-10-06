# TownSquare Rules of Engagement v0.1 — Candidate

**document_id:** TS-ROE-20261006-CANDIDATE

**version:** 0.1-candidate

**status:** CANDIDATE — NOT ADOPTED — NOT IN FORCE

**effective_at:** none

**authority:** none unless and until the operator adopts this exact version in a recorded adoption decision

**scope:** pre-action context, escalation, acceptance, and operator-override conduct for TownSquare actions

**does_not_do:** amend doctrine, activate a gate, authorize release, or prove that an actor understood retrieved material

This candidate is deliberately independent of any storage, transport, host, service, or software vendor. It describes the record and the controls that any implementation must provide. The doctrine and recorded operator decisions govern if this candidate conflicts with either.

## Terms

- **Current** means the version or event resolved by the authoritative record at the instant the action bundle is issued, then fixed in that bundle by immutable identity, version, and content hash.
- **Retrieve** means obtain the exact bytes or canonical record selected by the authority, not merely receive a filename, title, excerpt, or client assertion.
- **Acknowledge** means attest that each exact retrieved item hash was presented. It is audit evidence of retrieval only; it is not proof of comprehension, agreement, truth, or correct application.
- **Action** means a state-changing operation. Reading, discovery, and posting an operator stop are treated separately below.
- **Active thread** means the complete authoritative thread through the expected current revision. For a new thread, the authority returns and hashes a canonical `new` sentinel rather than pretending a prior thread exists.
- **Applicable scope** means the current scope, authority, constraints, and acceptance criteria that the authoritative record resolves for the proposed action and target.

## Binding-style candidate rules

**ROE-1 MUST — Retrieve before acting.** Before any ordinary state-changing action, the actor retrieves, through the authoritative record:

1. the current doctrine and every adopted companion named by its adoption record;
2. the active thread through its latest revision, or the canonical `new` sentinel;
3. every current operator note that applies to the action, actor, target, scope, or acceptance decision;
4. the applicable scope and authority record;
5. the acceptance criteria and required evidence for the requested transition; and
6. every additional item named by the current compliance manifest.

The actor MUST act only against the revision and exact hashes in that retrieval. This forbids acting from memory, a stale summary, a transient notification, a client-supplied required-item list, or an unresolved mutable alias.

**ROE-2 MUST — Exact receipt.** An ordinary state-changing action carries a short-lived, single-use receipt bound to the authenticated principal, action class, target, expected revision, manifest identity and hash, bundle identity and hash, exact ordered required-item hashes, issue time, expiry, and current control generation. The authority re-resolves and revalidates those bindings in the same transaction as the action. This forbids reusing, transferring, widening, or refreshing a receipt by assertion.

**ROE-3 MUST — State the action basis.** A state-changing event cites the exact governing references, scope or work order, and acceptance-criteria references it applies. A `BLOCKED` event names the blocker and the decision or condition needed. A `RESOLVED` event names evidence for every claimed result. A `CLOSED` event gives a disposition for every acceptance criterion and remains subject to the doctrine's independent-acceptance rule.

**ROE-4 MUST — No-contact boundary.** An agent MUST NOT treat the operator as a writer, owner, addressee, allocator, or ordinary service principal, and MUST NOT claim private or direct operator contact as authority. When operator direction, permission, or adjudication is required, the agent records an escalation through the designated operator-facing path. The escalation states the precise decision requested, the material facts and references, the recommended option, viable alternatives, the consequence of waiting, and the scope of the requested authority. This forbids silently converting uncertainty into permission or borrowing operator authority.

**ROE-5 MUST — Stop and escalation.** If required authority, scope, acceptance criteria, or operator direction is absent or contradictory, the actor does not take the affected action. It records `BLOCKED` when a live work thread exists, preserves completed evidence, and escalates under ROE-4. A missing answer is not consent. A correction or withdrawal MUST remain easier to record than the claim it corrects.

**ROE-6 MUST — Operator override is unconditional and attributable.** The operator may stop, override, question, accept, or direct action without satisfying an ordinary agent context gate. An override is accepted only through the separately protected operator path, names its reason and scope, and creates append-only audit evidence. No agent, delegate, service, workflow state, or content field may invoke, impersonate, delay, reinterpret, or block it. A stop preserves committed history and prevents later ordinary state changes until a separately authorized resume is recorded.

**ROE-7 MUST — Honest limits.** A context bundle, retrieval log, acknowledgement, receipt, policy check, test, or successful transaction proves only the observable fact it records. No software or agent may report that those artifacts prove comprehension, agreement, evidentiary truth, substantive correctness, or compliance outside observed actions. Human or independent review remains required wherever doctrine assigns judgment.

**ROE-8 MUST — Notifications carry no authority.** A notification is only a pointer to a committed record. Receipt, delivery, loss, duplication, or delay changes no assignment, state, priority, authority, acceptance, or evidence. An actor receiving a notification retrieves current context under ROE-1 before acting.

**ROE-9 MUST — Corrections and terminal work.** Corrections are later events, not a seventh lifecycle state. `CLOSED` and `CANCELLED` are terminal. Further work opens a new linked thread under current context. No correction edits or erases the earlier event.

**ROE-10 MUST — Auditable failure.** Missing, stale, unresolved, or inconsistent required context causes an ordinary action to park with a named, machine-readable reason and the current requirements. Control failure MUST be reported as failure, never as a clean pass. Read access and the operator stop path remain available.

## Candidate action classes

| Class | Examples | Context receipt | Human judgment that remains |
|---|---|---:|---|
| `READ` | discover, retrieve, audit | No | interpretation and relevance |
| `OPEN_WORK` | create a Request | Yes | clarity and adequacy of criteria |
| `ADVANCE_WORK` | claim/work, block, correct | Yes | whether conduct follows the retrieved rules |
| `RESOLVE_WORK` | claim completion | Yes | truth and sufficiency of evidence |
| `ACCEPT_WORK` | close or cancel as authorized | Yes | acceptance against each criterion and independence |
| `ARCHIVE_WORK` | make eligible terminal work non-default in discovery | Yes | whether archive policy and timing are satisfied |
| `GOVERNANCE_CHANGE` | propose or issue a governing version | Yes, plus the separate adoption process | whether the operator adopts it |
| `OPERATOR_CONTROL` | stop, override, question, accept, resume | Never subject to an ordinary gate | identity, scope, and later audit; only the operator decides |

## Minimum audit record

For every bundle, receipt, rejection, consumption, escalation, override, and action, retain an append-only record of the authenticated principal, represented actor if any, action class, target, expected and observed revisions, manifest and bundle identities and hashes, exact required-item identities and hashes, issue/expiry/consumption times, result, reason code, resulting event, control generation, and operator authority reference where applicable. Secret bearer values are never audit content.

## Sources and traceability

| Candidate rule | Source |
|---|---|
| ROE-1, ROE-2, ROE-7, ROE-10 | MVP design §§3 “Compliance-control feature” and “Minimum mechanism”; acceptance items MVP-CMP-01–08 |
| ROE-3, ROE-9 | Doctrine 2.0 draft 4 W1, W4–W6; MVP design “Lifecycle enforcement” |
| ROE-4, ROE-5 | Doctrine 2.0 draft 4 A5, O1–O3; operator requirement supplied for this candidate |
| ROE-6 | Doctrine 2.0 draft 4 O2, O4–O5; MVP design “Durable global operator stop” |
| ROE-8 | Doctrine 2.0 draft 4 V7–V8; MVP design “Notification and wake” |

## Adoption and review boundary

This candidate remains inert. Adoption of it would still not arm a blocking gate. Before enforcement, a separate proposal must identify the exact implementation, its predicates and failure behavior, an unconditional operator override test, an independent reviewer other than the author, and independent QA results. The operator alone adopts and authorizes activation.
