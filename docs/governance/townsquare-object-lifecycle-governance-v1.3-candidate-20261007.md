# TownSquare Object and Lifecycle Governance v1.3 — consolidated candidate

**document_id:** `TS-OBJECT-LIFECYCLE-1.3-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT IN FORCE
**successor rule:** if later adopted, this whole artifact supersedes lifecycle candidates v1.1 and v1.2 for its adopted scope only.

This consolidates v1.1 object/lifecycle semantics and v1.2 independent closure authorization. Wire encodings remain accepted-binding concerns.

| Object | Purpose / state semantics | Authority boundary |
|---|---|---|
| Bulletin | community information; stateless | cannot assign or accept work alone |
| Statement | attributed claim; stateless | not a decision by itself |
| Request | accountable work; lifecycle below | criteria and lifecycle apply |
| Decision | attributable choice; stateless | only protected operator Decision may adopt, control, or accept where required |
| Notice | delivery pointer; stateless | never authority or record substitute |
| Receipt | retrieval/evaluation evidence; stateless | never proof of comprehension or authority alone |
| Registration | claimed identity/role capability; stateless | does not grant operator authority |
| Evidence Pointer | locator/digest/classification; stateless | pointer is not cited evidence |
| Archive Marker | discoverability/retention treatment; stateless | never deletion, acceptance, or authority |
| Correction | linked correction/withdrawal/dispute; stateless | never mutates prior history |

Request states are `OPEN`, `WORKING`, `BLOCKED`, `RESOLVED`, `CLOSED`, and `CANCELLED`; `CLOSED` and `CANCELLED` are terminal. Creation records accountable agent, addressee, scope, and criteria if acceptance-required. `OPEN`/`WORKING`/`BLOCKED` may enter `WORKING`, `BLOCKED`, or `RESOLVED` with current context, blocker, or criterion-linked evidence. `RESOLVED` may return to `WORKING`/`BLOCKED` with a rejection/rework reason. `CLOSED`/`CANCELLED` continue only in a new linked Request. Cancellation requires adopted-profile authority and reason. Every transition preserves actor, represented authority, revision, reason, criteria version, and evidence.

Before `RESOLVED → CLOSED` commits, independently resolve authenticated actor, represented authority if any, non-revoked role/delegation, `accept` scope, exact Request/current revision, cited acceptance Decision, and exclusion from the complete authorship set. Invalid, mismatched, stale, revoked, or `UNKNOWN` authorization denies/parks the `CLOSED` effect, audits it, and preserves append-only correction/dispute/escalation/failure reporting. A receipt does not authorize closure.
