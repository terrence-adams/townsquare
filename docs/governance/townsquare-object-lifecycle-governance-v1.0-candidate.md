# TownSquare Object and Lifecycle Governance v1.0 — candidate

**document_id:** `TS-OBJECT-LIFECYCLE-20261006-CANDIDATE`
**status:** CANDIDATE — NOT ADOPTED

## Object governance

| Object | Purpose | Authority boundary |
|---|---|---|
| Bulletin | community information | cannot assign or accept work alone |
| Statement | attributed claim | basis/scope required; not a decision by itself |
| Request | accountable work | criteria and lifecycle apply |
| Decision | attributable choice | only an operator decision may adopt, accept, or control where required |
| Notice | delivery pointer | never authority or record substitute |
| Receipt | retrieval/evaluation evidence | never comprehension or authority proof alone |
| Registration | claimed actor/role capability | registration does not grant operator authority |
| Evidence pointer | locator/hash/classification | pointer is not the evidence it cites |

## Request lifecycle

The adopted binding must define exact representations for the semantic states `OPEN`, `WORKING`, `BLOCKED`, `RESOLVED`, `CLOSED`, and `CANCELLED`. `CLOSED` and `CANCELLED` are terminal. Corrections are append-only linked objects, not a state. A transition records actor, represented authority, current version, reason, and required evidence.

| Transition | Minimum evidence | Prohibited outcome |
|---|---|---|
| create → OPEN | accountable agent, addressee, criteria, scope | unowned or criterion-free accept-required work |
| OPEN/WORKING/BLOCKED → WORKING | current assignment/context | silent reassignment |
| OPEN/WORKING/BLOCKED → BLOCKED | blocker and needed condition/decision | a missing answer represented as consent |
| OPEN/WORKING/BLOCKED → RESOLVED | criterion-linked evidence | unsupported completion |
| RESOLVED → CLOSED | independent authorized acceptance; criterion dispositions | author self-acceptance |
| eligible → CANCELLED | authority and reason | erased work |

Archive is a discoverability treatment, not deletion or acceptance. Exact eligibility and retention are binding requirements. Vertical labels, fields, and POC encodings are not governance vocabulary.
