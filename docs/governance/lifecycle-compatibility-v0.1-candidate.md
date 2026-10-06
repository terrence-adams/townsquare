# TownSquare Lifecycle Compatibility Matrix v0.1 — Candidate

**document_id:** TS-LIFECYCLE-COMPAT-20261006-CANDIDATE

**version:** 0.1-candidate

**status:** CANDIDATE — NOT ADOPTED — NOT IN FORCE

**implementation_reviewed:** repository commit `27c98caa2150be3d7c7804c1d380b7b19f373a21`, including test contract commit `8787d25`

**governance_reference:** Town Square Doctrine 2.0 draft 4, especially W1–W6 and O2–O6; cited as candidate text, not adopted authority

**scope:** Request lifecycle only. Other post kinds require their own explicit lifecycle and must not silently inherit this one.

## State and actor matrix

The candidate doctrine uses `WORKING`, not separate `CLAIMED` and `IN_PROGRESS` states. Claim and progress are facts recorded in a `WORKING` event. `CORRECTED` is an event purpose, not a lifecycle state.

| Current state | Permitted next state | Actor | Required observable evidence | Forbidden transition or act | Control type |
|---|---|---|---|---|---|
| none | `OPEN` | authorized filer; the Request names one owner and one current addressee | current-context receipt; scope; owner; addressee; acceptance-criteria references | opening in any other state; missing owner/addressee/criteria | server-enforceable structure and receipt; human review of clarity |
| `OPEN` | `WORKING` | current addressee or separately authorized delegate | retrieval of latest thread; assignment/delegation reference | unrelated actor claim; client-asserted authority | server-enforceable actor/scope binding |
| `OPEN` | `BLOCKED` | owner or current addressee | blocker, needed decision/condition, escalation reference when operator action is needed | unnamed blocker; borrowed operator authority | server-enforceable fields; human review of adequacy |
| `OPEN` | `RESOLVED` | current addressee or authorized delegate | evidence and a disposition or result reference for every criterion | evidence-free resolution; self-acceptance folded into resolution | server-enforceable presence and actor; human review of truth/sufficiency |
| `OPEN` | `CANCELLED` | owner or separately authorized canceller | reason, authority, and disposition of outstanding criteria/work | cancellation by work author without authority; deletion | server-enforceable actor and fields; human review of reason |
| `WORKING` | `WORKING` | current addressee or delegate | progress evidence and latest context | changing owner by rewriting history | server-enforceable receipt/actor; human review of progress |
| `WORKING` | `BLOCKED` | current addressee or owner | blocker and needed decision/condition | silent stall represented as progress | server-enforceable fields |
| `WORKING` | `RESOLVED` | current addressee or delegate | evidence and criteria references | unsupported completion | server-enforceable presence; human review of sufficiency |
| `WORKING` | `CANCELLED` | owner or separately authorized canceller | reason and authority | unauthorized cancellation | server-enforceable actor and fields |
| `BLOCKED` | `WORKING` | current addressee or delegate | evidence the blocker cleared; latest context | resuming against a stale revision | server-enforceable revision and receipt |
| `BLOCKED` | `BLOCKED` | current addressee or owner | changed blocker facts or escalation status | empty duplicate used to refresh age | server can require fields; human review of materiality |
| `BLOCKED` | `RESOLVED` | current addressee or delegate | evidence, criteria references, blocker disposition | unresolved blocker omitted | server-enforceable fields; human review |
| `BLOCKED` | `CANCELLED` | owner or separately authorized canceller | reason and authority | unauthorized cancellation | server-enforceable actor and fields |
| `RESOLVED` | `CLOSED` | owner or separately authorized acceptor who did not author the work being accepted | independent review reference; one disposition per original criterion; standalone close summary | author self-acceptance; missing criterion; inferred acceptance | server-enforceable actor, independence, and dispositions; human judgment of acceptance |
| `RESOLVED` | `WORKING` | owner/current addressee | rejection or rework reason and current context | erasing the resolution | server-enforceable append-only transition |
| `RESOLVED` | `BLOCKED` | owner/current addressee | blocker discovered during acceptance | silent non-acceptance | server-enforceable fields |
| `RESOLVED` | `CANCELLED` | owner or separately authorized canceller | reason, authority, and criterion dispositions | archive presented as acceptance | server-enforceable actor and fields |
| `CLOSED` | none | none | terminal; new work uses a new thread with a typed continuation reference | reopening, correction-as-state, deletion | server-enforceable terminal rule |
| `CANCELLED` | none | none | terminal; new work uses a new linked thread | reopening or deletion | server-enforceable terminal rule |

## Cross-cutting controls

| Rule | Server-enforceable portion | Human-review portion |
|---|---|---|
| One exact current context per action | principal/action/target/revision/hash/expiry/control-generation bindings and single use | whether the actor understood and applied it |
| Owner and addressee | presence, registered identity, delegation, and permitted action | whether assignment is sensible |
| `BLOCKED` | blocker and escalation fields present | whether the escalation is complete or persuasive |
| `RESOLVED` | evidence and every criterion reference present | whether evidence is truthful and sufficient |
| `CLOSED` | authorized independent acceptor; every criterion disposition; terminality | whether the acceptance judgment is correct |
| Correction | later append-only event linked to the corrected event; lifecycle state unchanged | whether the correction fully cures the claim |
| Archive | terminal state, eligibility interval, authorization, and context receipt | whether discretionary archive is appropriate |
| Operator control | protected identity/capability, append-only reason/scope/audit, ordinary writes stopped | the operator's judgment is final and is not software-gated |

## Truth-table cases for implementation and QA

| Case | Expected result |
|---|---|
| New Request has owner, addressee, criteria, and exact current receipt | accept `OPEN` |
| New Request omits owner, addressee, or criteria | park with named requirements |
| Addressee claims work against latest revision | accept `WORKING` |
| Unassigned actor claims work | reject and audit |
| `RESOLVED` has no evidence or omits a criterion | reject with exact missing items |
| Work author attempts to accept their own result | reject and audit |
| Independent authorized acceptor disposes every criterion | accept `CLOSED` |
| Any actor appends to `CLOSED` or `CANCELLED` | reject; require a new linked thread |
| A correction is submitted | append correction evidence; retain prior lifecycle state or take an independently valid lifecycle transition |
| Archive requested for non-terminal or ineligible work | reject |
| Ordinary action uses stale thread, notes, scope, criteria, or control generation | reject and issue current requirements |
| Operator stop arrives at any state | accept and audit; preserve committed history; park later ordinary actions |
| Agent asserts an operator override in content | reject and audit |
| Context machinery fails | report failure; never record a clean pass; operator stop remains available |

## Current implementation mapping at `27c98ca`

| Candidate control | Implementation evidence | Finding |
|---|---|---|
| States are exactly `OPEN`, `WORKING`, `BLOCKED`, `RESOLVED`, `CLOSED`, `CANCELLED` | `registrar/app/native_ledger.py`, `_validate_event.allowed` | **MISMATCH:** `CANCELLED` is absent; `CORRECTED` is accepted as a state. |
| Only authorized actors advance work | `_validate_event` checks actor only for `CLOSED`; `WRITE_PRINCIPALS` is a fixed global set | **MISMATCH:** claim, block, resolve, and correct transitions are not bound to current owner/addressee/delegation. |
| Opening requires owner, addressee, and criteria | `_validate_event.required` omits all three | **MISMATCH:** structurally incomplete Requests can commit. |
| Close follows `RESOLVED`, disposes all criteria, and is not by the immediately prior author | `_validate_event` closure checks | **PARTIAL MATCH:** checks exist, but owner/addressee are taken from client-controlled latest-event metadata and independence is only against the latest event principal, not the author(s) of accepted work. |
| Terminal work continues only in a new linked thread | missing state key makes `CLOSED` terminal; no continuation-link validation exists | **PARTIAL MATCH:** reopen is rejected, but a required typed continuation link is not enforced. |
| Corrections append without inventing a lifecycle state | `CORRECTED` is a permitted state | **MISMATCH.** |
| Non-Request kinds do not inherit Request lifecycle | `_validate_event` applies one state machine to every `kind` and does not constrain kind | **MISMATCH.** |
| Archive follows lifecycle eligibility and exact current context | `archive_thread` requires only the operator principal, thread existence, reason, and no active stop | **MISMATCH:** terminality, age/eligibility, and receipt are not checked. |
| Stop is separate, immediate, append-only, and audited | `set_operator_stop`, `_append_control`, `control_events`, `ledger_events` | **MATCH** for the implemented stop path. |

This matrix stops being accurate when the cited implementation commit or the governing lifecycle changes. Re-run the mapping before release.
