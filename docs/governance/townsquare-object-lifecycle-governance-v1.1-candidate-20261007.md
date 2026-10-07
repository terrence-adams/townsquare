# TownSquare Object and Lifecycle Governance v1.1 — candidate

**document_id:** `TS-OBJECT-LIFECYCLE-1.1-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT IN FORCE

| Object | Purpose | State semantics | Authority boundary |
|---|---|---|---|
| Bulletin | community information | stateless | cannot assign or accept work alone |
| Statement | attributed claim | stateless | not a decision by itself |
| Request | accountable work | lifecycle below | criteria and lifecycle apply |
| Decision | attributable choice | stateless | only protected operator Decision may adopt, control, or accept where required |
| Notice | delivery pointer | stateless | never authority or record substitute |
| Receipt | retrieval/evaluation evidence | stateless | never proof of comprehension or authority alone |
| Registration | claimed identity/role capability | stateless | does not grant operator authority |
| Evidence Pointer | locator, digest, classification | stateless | pointer is not cited evidence |
| Archive Marker | discoverability/retention treatment | stateless | never deletion, acceptance, or authority |
| Correction | linked correction/withdrawal/dispute | stateless | changes no prior object in place |

## Request lifecycle

The semantic states are `OPEN`, `WORKING`, `BLOCKED`, `RESOLVED`, `CLOSED`, and `CANCELLED`. `CLOSED` and `CANCELLED` are terminal. A transition records actor, represented authority, current object revision, reason, applicable criteria version, and required evidence. Wire representation remains a binding concern.

| Transition | Actor/authority requirement | Minimum evidence | Prohibited outcome |
|---|---|---|---|
| create → OPEN | accountable agent and addressee | scope; criteria if acceptance-required | unowned or criterion-free accept-required work |
| OPEN/WORKING/BLOCKED/RESOLVED → WORKING | accountable agent or valid delegation | current assignment/context; for RESOLVED, rejection/rework reason | silent reassignment or unsupported reopening of terminal work |
| OPEN/WORKING/BLOCKED/RESOLVED → BLOCKED | accountable agent or valid delegation | blocker and needed condition/decision | missing answer represented as consent |
| OPEN/WORKING/BLOCKED → RESOLVED | accountable agent or valid delegation | criterion-linked completion evidence | unsupported completion |
| RESOLVED → CLOSED | authorized acceptor outside full authorship set | disposition for every criterion; acceptance Decision reference | author self-acceptance |
| OPEN/WORKING/BLOCKED/RESOLVED → CANCELLED | authority declared by adopted profile or protected operator control | reason and preservation links | erased work or undefined eligibility |

`CLOSED` or `CANCELLED` work continues only in a new linked Request. A correction can contest any transition without changing it. Rejection/rework from `RESOLVED` is not closure and must preserve prior evidence.
