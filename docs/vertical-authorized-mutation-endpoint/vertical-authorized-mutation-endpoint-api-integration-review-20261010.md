# Vertical Authorized Mutation Endpoint MVP — API and Integration Peer Review

Status: **REWORK**  
Date: 2026-10-10  
Reviewer: **Tony Jaa — API/client integration**  
Review boundary: design/API review only; no code, ledger mutation, credential, deployment, service, or ACL action performed

## Reviewed artifacts

| Artifact | Verified SHA-256 |
| --- | --- |
| `vertical-authorized-mutation-endpoint-mvp-design-20261010.md` | `9def649bd2dd03523222bf121f99eb6d865f290a04ef87188c5c30ef2eebf935` |
| `vertical-authorized-mutation-endpoint-draft-work-items-20261010.md` | `080adbe4a8dd488e3e144d94665211ab604282ab89c3b87584e0a8362ea4f643` |
| `vertical-authorized-mutation-endpoint-work-order-20261010.md` | `888158ab046d5c05e1d575a1e6bf9cbfd5e41a379bdf9c4ea7bb0e37c69a4df1` |

All three hashes matched before review. This verdict applies only to those hashes.

## Outcome

The architecture is directionally sound and remains a bounded MVP: VR-048 is the hard dependency and sole typed authoring path; the client never pins the global domain head; the server owns serialization and harmless global-head retry; the target Story head remains a semantic compare-and-append boundary; direct SMB cutover is a separate accepted action; deployment/administration remains on a non-Venom target under Francis; Eddie is limited to operator-decision/receipt relay; and Logan is correctly assigned Feature/Story facilitation without self-approval, endpoint authority, credential custody, or sole-review power.

The package is not yet approval-ready because the following contract ambiguities would make conforming clients and the S2/S4/S6/S7/S9 tests disagree. These are corrections to the accepted endpoint behavior, not scope expansion.

## Required corrections

### R1 — Make the execution envelope internally consistent

The permit request includes `project`, and both mutation routes require the same complete envelope, but the work-item route also says caller-supplied `project` is rejected. Define one rule:

- preferably remove `project` from caller input because this is a Vertical-only API and bind the server-owned Vertical project identifier; or
- accept it only as a fixed validated selector, clearly distinguish it from an authoritative event field, and reject every value except the configured Vertical project.

For each mutation route, specify the exact headers and body fields, where the opaque permit is carried, required/forbidden fields by `OPEN` versus `APPEND`, unknown-field behavior, and the equality rule between issuance and execution. Define the complete-request hash field set explicitly. Compare canonical bytes and hashes, not original JSON byte layout; semantically equivalent JSON accepted by the VR-048 schema must produce the same canonical representation as S2 requires.

### R2 — Put durable exact-replay lookup before mutable pre-append checks

After a successful append, the original `expected_story_head` is necessarily stale and the permit is consumed. The current algorithm verifies the permit and later compares the current Story head before it describes receipt recovery. A retry after an ambiguous response could therefore return `409` instead of the promised receipt.

After caller authentication and canonical request recomputation, perform a durable lookup by the bound principal, idempotency-key hash, complete-request hash, and permit ID before permit-expiry/consumption, current-head, owner, dependency, policy, authority, and Gate checks. If an exactly matching committed event exists, return its original durable receipt with zero writes. Any partial-key collision or changed binding remains `409`. Only requests with no committed match continue into current-state validation and append.

This replay path does not reuse authority for a new write; it reports an already committed result.

### R3 — Define one idempotency and permit lifecycle

Both permit issuance and mutation use an idempotency key, while the permit binds that key, but route scope and recovery behavior are unspecified. Define:

- whether the same operation key is mandatory across permit issuance and execution (recommended for this MVP);
- uniqueness scope, minimum supported retention, and collision behavior;
- recovery after an ambiguous permit-issuance response when the bearer was returned “once” but not received;
- exact issuance retry while a permit is live;
- replacement of an expired, unused permit without new semantic approval after full identical-state revalidation; and
- behavior for consumed permits, failed pre-write attempts, server retry exhaustion, and an ambiguous post-commit response.

The lifecycle must not force operator reapproval merely because issuance delivery was lost, the bounded internal global-head retries were exhausted, or a permit expired while all bound semantic state remained identical.

### R4 — Specify machine-readable response and error semantics

The status families are too coarse for a safe client. Add a single bounded response/error envelope with at least `request_id`, stable machine `code`, human-safe message, and safe retry guidance. Include the current Story head only for the S6 conflict response.

Use `401` for missing/invalid client authentication and `403` for an authenticated principal denied by authority, permit, Registry/Gate, or policy. Keep `409` for state or binding conflicts, but distinguish at least Story-head conflict, idempotency-key collision, permit replay/binding mismatch, dependency change, owner change, and policy change with machine codes. Define `503` for unavailable/stale dependencies and exhausted harmless-global-head retry; state explicitly that the latter permits retry with the same semantic request/key and does not require fresh operator approval while bound state remains unchanged. Define whether syntactic JSON failure is `400` or `422`, then use `422` consistently for typed/canonical validation failures.

### R5 — Make the receipt durable and replay-stable

S4/S7/C6 require a receipt ID and S9 requires a receipt hash, but neither appears in the design receipt. Add a non-secret stable `receipt_id` and define the receipt hash over a canonical durable receipt core reconstructed from the committed event. The durable core must be identical on exact replay.

Do not mutate the stored receipt outcome from `CREATED` to `EXACT_REPLAY` while also promising “the same receipt.” Report replay as response-delivery metadata outside the durable receipt core, or define `original_outcome: CREATED` plus a non-hashed `delivery: EXACT_REPLAY`. Likewise, use the committed event's recorded time on replay, not a newly generated receipt time.

State that a commit followed by process/response loss is recovered from the event and returns the same receipt ID/hash with no second append. If that cannot be proven without new persistence/schema, S10 correctly fails and Jackie Chan's conditional review is triggered.

### R6 — Define bounded safe observability required by the accepted tests

S7 requires retry counts and request IDs, but the approved receipt/log contract does not define them. Permit only the minimum structured service evidence needed by S1–S10: request ID, route, authenticated principal ID, safe host/agent/session IDs, machine result code, retry count, permit ID, request/idempotency hashes, event/thread IDs when committed, receipt ID/hash, and timing/status. Apply the existing secret/provider-locator exclusions. This is test evidence, not production observability or an SLO expansion.

## Acceptance and dependency validation

- **VR-048 compatibility:** PASS at design intent. The endpoint delegates typed construction, owner/actor resolution, immediate Gate reauthorization, and per-thread `expected_head` append to VR-048. Implementation must not create a parallel writer or canonicalizer.
- **No client global-head pin:** PASS. The global domain head is absent from the request and permit claims and appears only as server-observed audit data after commit.
- **Harmless retry approval boundary:** PASS in intent, REWORK in executable contract pending R2–R4. Unrelated global-head churn is correctly server-owned, but retry exhaustion and post-commit recovery need deterministic client rules.
- **Per-thread CAS:** PASS in intent. Changed Story head is non-retryable semantic conflict; different-thread global serialization remains server-owned.
- **Typed-payload binding:** PASS after the amendment. Issuance and execution carry the payload; the server recomputes canonical semantic and complete-request hashes and rejects hash-only/mismatched input before write. R1 is still needed to remove the `project` contradiction and pin the envelope schema.
- **Transaction/receipt recovery:** REWORK pending R2 and R5.
- **Client migration/cutover:** PASS. Shadow/canary precedes explicit cutover acceptance; no silent SMB fallback is allowed afterward.
- **Non-Venom boundary and facilitation:** PASS. Francis owns packaging/deployment/administration on the approved non-Venom target. Eddie relays operator decisions/receipts only. Logan facilitates dependencies, state/evidence handoffs, scheduling, and consumer acceptance without self-approval or endpoint authority.
- **Bounded criteria/dependencies:** PASS. S1–S10 and C1–C8 stay binary and scoped; VR-047 is a concept reference, VR-072 is a parked future consumer, and no new persistence is silently authorized.

## Concrete alternative/improvement

Keep the three routes, but publish one shared `MutationIntentV1` schema used verbatim by permit issuance and execution. Treat the permit as a separate execution credential, not a field that changes the intent. Derive `semantic_payload_sha256`, `bound_request_sha256`, `idempotency_key_sha256`, and the replay-stable receipt core only on the server. This removes duplicate client models and makes S2 fixtures reusable across all three routes without adding another service or persistence layer.

## Re-review boundary

Ip Man should amend only the API/canonicalization/algorithm/receipt passages and the directly affected S2, S4, S6, S7, and S9 wording/evidence fields. No implementation, deployment, credential, ledger, ACL, Revere, UI, HA, or production-hardening work is required for re-review.

Approval-ready when R1–R6 are resolved consistently across the three artifacts and new hashes are supplied.

## Model and cost

- Model used: GPT-5, Tony Jaa specialist role; reasoning tier and billable token/currency figures were not exposed to this reviewer.
- Review actions: three artifact hash validations, focused contract/dependency review, and this one review artifact.
- Implementation cost changed by this review: **0 engineering hours performed**; expected correction effort is part of design maintenance and was not independently timed.
- Governance cost: elapsed engineering time, token count, and currency cost are **unknown**; no retry/escalation caused implementation work.
