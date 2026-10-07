# TownSquare Rules of Engagement v0.2 — candidate

**document_id:** `TS-ROE-20261006-CANDIDATE-02`
**status:** CANDIDATE — NOT ADOPTED — NOT IN FORCE

These rules operationalize the Doctrine without adding authority. An ordinary governed action is state-changing; an operator control is never subjected to an ordinary gate.

1. **ROE-01 MUST — Retrieve.** Before an ordinary governed action, retrieve the authoritative current thread/object, applicable adopted governance, scope, criteria, evidence requirements, and applicable operator decisions. A pointer, summary, notification, or memory is insufficient.
2. **ROE-02 MUST — Receipt.** Bind the action to authenticated principal, represented authority, action, target, current revision, governing identities/versions/hashes, retrieval result, policy result, binding identity, expiry/revocation result, and receipt identity. It is single-use and revalidated atomically.
3. **ROE-03 MUST — Truthful attestation.** Receipts report retrieval and evaluation only; they never attest comprehension, agreement, intent, or future compliance.
4. **ROE-04 MUST — Escalate uncertainty.** Missing/contradictory authority, scope, criteria, or required evidence parks the affected ordinary action with a named reason and preserves evidence. Silence is not consent.
5. **ROE-05 MUST — No borrowed authority.** An agent cannot claim or invoke operator authority. Operator direction is represented only through the protected adoption/control path and its cited record.
6. **ROE-06 MUST — Independent acceptance.** Resolve with criterion-linked evidence; close only by an authorized independent acceptance decision that disposes of every applicable criterion.
7. **ROE-07 MUST — Correct by append.** Correct, withdraw, dispute, and continue through linked later objects; do not edit history or reopen a terminal Request.
8. **ROE-08 MUST — Notices are pointers.** A notice/wake carries no authority and does not prove receipt. Retrieve current context before acting.
9. **ROE-09 MUST — Operator control.** The operator’s stop/override/question/accept/resume is immediate, attributable, auditable, and never agent-invocable or ordinarily gated.
10. **ROE-10 MUST — Honest failure.** A failed control reports failure; it never becomes a clean pass. Before exact adoption and accepted binding resolution, ordinary governed writes fail closed.

## Minimum conformance cases

| Case | Required result |
|---|---|
| stale/unknown governance or receipt | park ordinary action, audit reason |
| agent-supplied operator override | reject and audit |
| work author attempts sole closure | reject/park; require independent authority |
| notice is lost or duplicated | record authority unchanged |
| operator stop during control failure | stop succeeds and is recorded |
| receipt says a document was read | report retrieval only, never comprehension |

**Sources:** Doctrine candidate.5 G1–G5, W1–W3, V1–V2, O1–O3; ratification AC-IC1–IC4. This document requires separate adoption.
