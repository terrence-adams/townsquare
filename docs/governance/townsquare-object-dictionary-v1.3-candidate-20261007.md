# TownSquare Object Dictionary v1.3 — candidate

**document_id:** `TS-OBJECT-DICTIONARY-1.3-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT IN FORCE

This semantics-level dictionary leaves wire fields and encodings to accepted bindings. Every object has durable identity, actor, represented authority if any, created/evaluation time, scope, typed references, basis, and append linkage where applicable.

| Object | Required semantic attributes | Citation/linkage and authority meaning |
|---|---|---|
| Bulletin | audience, impact, statement of change | cites related objects; information alone cannot assign/accept work |
| Statement | claim, basis, scope, subject | cites evidence and counterstatements; no decision effect by name |
| Request | accountable agent, addressee, criteria, lifecycle state | links criteria/evidence/parent; creates accountable work only under adopted profile |
| Decision | decider, decision kind, scope, rationale, effective window, revocation/supersession relation | cites authority basis and affected identity/version; only protected operator Decision may adopt/control/accept where required |
| Notice | delivery target and durable target reference | points to record only; never proves receipt, assignment, or authority |
| Receipt | action/evaluation context, dependencies, results, correlation | links audit evidence; never authorizes itself |
| Registration | claimed identity, role/capability, validity | cites verification/role source; does not grant operator authority |
| Evidence Pointer | locator, digest, classification, retrieval basis | points to evidence; does not make its target true or current |
| Archive Marker | retention/discoverability action, target, reason | links preserved target; never deletes, accepts, or authorizes |
| Correction | target identity/revision, correction/dispute/withdrawal statement, reason | appends to target; never mutates prior history or grants authority |

An object with missing required semantic attributes is preserved labelled evidence; an accepted binding determines validation and effect disposition.
