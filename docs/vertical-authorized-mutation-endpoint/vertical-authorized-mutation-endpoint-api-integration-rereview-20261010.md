# Vertical Authorized Mutation Endpoint MVP — Focused API/Integration Rereview

Status: **REWORK — ONE REMAINING CONTRACT CORRECTION**  
Date: 2026-10-10  
Reviewer: **Tony Jaa — API/client integration**  
Boundary: focused rereview of prior R1–R6 and adjacent regressions only; no code, ledger, credential, deployment, service, or ACL action performed

## Reviewed artifacts

| Artifact | Verified SHA-256 |
| --- | --- |
| `vertical-authorized-mutation-endpoint-mvp-design-20261010.md` | `f95fbbf39306cf334f7dd53b40ce821d8366540c2035980c6d178e29cff077f8` |
| `vertical-authorized-mutation-endpoint-draft-work-items-20261010.md` | `41f8e279e2513c55453a12a0decab4f652da35f1a6e5bccca454a243098efe36` |
| `vertical-authorized-mutation-endpoint-work-order-20261010.md` | `ce3359108f532b9803ca6bdc1915f90747c29ffb9bb2cb9c4556280f8078bf7d` |

All hashes matched before rereview. This verdict applies only to these hashes.

## R1–R6 disposition

| Finding | Result | Evidence in corrected package |
| --- | --- | --- |
| R1 — execution-envelope consistency | **PASS** | Project is server-resolved and forbidden in caller input; authority has one three-field representation; lifecycle has one source; the eight-field typed payload, request schema, unknown-field behavior, four hash inputs, canonical ordering, and issuance/execution equality are pinned. |
| R2 — committed receipt lookup before mutable checks | **REWORK** | Design §7 step 3 and S9 correctly require lookup before Story head, permit expiry/consumption, policy, owner, dependencies, and authorization. However, step 1 still validates fresh Registry host/agent ownership before that lookup. |
| R3 — idempotency and permit lifecycle | **PASS** | One operation key spans issuance/execution; cache replay, changed-key collision, cache loss, expiry, new-key reissue, precommit failures, retry exhaustion, atomic commit/consumption, and ambiguous mutation response are defined. |
| R4 — HTTP/error/retry semantics | **PASS** | The result envelope, `401`/`403` split, named `409` and `422` codes, retry classes, and retryable `503 GLOBAL_SERIALIZATION_RETRY_EXHAUSTED` behavior are specified and testable. |
| R5 — immutable receipt | **PASS** | Exact receipt-core fields, canonical receipt-core hash, stable receipt ID, receipt hash, replay-invariant recorded time, and delivery metadata outside the immutable core are defined. |
| R6 — bounded safe observability | **PASS** | S7 fields are limited to hashes, non-secret permit/receipt IDs, retry count/outcome, status, and machine code; raw key, payload/content, provider locator/session, credentials, digests, and bearer are forbidden. |

## Remaining correction

### RR1 — Split authentication from current Registry authorization before exact replay

The design algorithm currently says:

- step 1: authenticate the caller **and validate fresh Registry host/agent ownership**;
- step 3: perform committed-receipt lookup **before current authorization**.

Fresh Registry host/agent ownership is a mutable current-authorization check. If Registry is unavailable, stale, changed, or revoked after a mutation committed, step 1 can return `503` or denial before the service reaches the immutable receipt. That contradicts step 3, design §8's lost-response rule, Feature criterion 3, work-order invariant 117, and S9's explicit lookup-order fixture.

Correct only the ordering:

1. Before exact committed replay lookup, authenticate the presented client credential and recompute/validate the static canonical replay tuple and permit structure/binding required to identify the committed event.
2. If the tuple exactly matches a committed event for that authenticated principal, return the immutable receipt with zero writes.
3. Only when no committed exact match exists, validate fresh Registry host/agent ownership and continue the first-execution mutable-state path.

The replay must still fail for a different authenticated principal, changed canonical request, changed idempotency key, changed permit tuple, or invalid credential. This correction grants no new mutation authority; it only permits an authenticated caller to recover the immutable result of its already committed operation.

Update design §7 step 1/step 3 and, if necessary, the matching wording in S3/S9 and the work-order invariant so they state the same order. No schema, persistence, deployment, credential, or acceptance-scope change is needed.

## Regression checks

- **Canonical project/authority/payload/hash contract:** PASS.
- **Per-thread expected-head CAS:** PASS.
- **Server-only unrelated global-head serialization/retry:** PASS. No global head appears in the request, permit binding, receipt core, retry decision, or client approval pin. Audit-only post-commit metadata is non-authoritative and outside the immutable receipt.
- **No operator approval for harmless retry:** PASS for issuance recovery, permit reissue after identical-state revalidation, internal retry exhaustion, and exact mutation replay, subject only to RR1 ordering.
- **VR-048 compatibility:** PASS; one existing typed façade/canonical profile remains the implementation path.
- **Non-Venom deployment/client boundary and assignments:** PASS; Francis retains deployment/administration, Eddie remains relay-only, and Logan remains facilitator without self-approval or endpoint authority.
- **Bounded MVP acceptance/dependencies:** PASS; no production-hardening or new persistence requirement was added.

## Verdict and rereview boundary

The package is one wording/ordering correction from **APPROVAL-READY**. Ip Man should amend only RR1 consistently across the design, directly affected acceptance text, and work-order invariant, then provide new hashes for a final focused verification.

## Model and cost

- Model used: GPT-5, Tony Jaa specialist role; billable token/currency figures and explicit reasoning-tier telemetry were unavailable.
- Actions: three hash validations, focused R1–R6/regression rereview, and this one rereview artifact.
- Implementation work performed: **0 engineering hours**.
- Elapsed engineering time, tokens, and currency cost: **unknown**.
