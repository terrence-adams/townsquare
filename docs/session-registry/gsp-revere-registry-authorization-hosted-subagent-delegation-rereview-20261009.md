# Revere Registry authorization and hosted-subagent delegation — focused GSP re-review

**Review date:** 2026-10-09  
**Reviewer:** GSP  
**Disposition:** **REWORK — one blocking correction remains**  
**Approval state:** **NOT APPROVAL-READY**  
**Scope:** Closure review of only `RHD-1`, `RHD-2`, `RRA-1`, and `VH-1` from the prior GSP review. No code, provisional reconciler, broker/ACL/credential/service state, or live Vertical ledger was inspected or changed in this re-review.

## Reviewed evidence

| Source | SHA-256 |
| --- | --- |
| Revised `revere-registry-authorization-and-hosted-subagent-delegation-addendum-20261009.md` | `2a1a2d26f8ddeee690577a3be7f1e4608ace1e68f17c9876b210175027d1a408` |
| Prior `gsp-revere-registry-authorization-hosted-subagent-delegation-review-20261009.md` | `501a59b04aac2b841f74a3b0f293947dd6a6fe6490d15d1b20f6f9907e6a2bcc` |

The revised addendum hash matches the value reported for re-review.

## Closure matrix

| Finding | Result | Re-review basis |
| --- | --- | --- |
| `RHD-1` — same-root sibling selection and authorization | **CLOSED** | Lines 80–86 bind a real child IPC context to exactly one immutable adapter-held delegation mapping, prohibit child-controlled identity/selectors, require Revere to validate the adapter-selected opaque ID against the authenticated root/current generation, and server-resolve logical actor fields. B2–B4 directly test missing/non-unique mappings, caller override, same-root sibling override, same-root concurrent instances, cross-instance delivery, and reply isolation using bounded aggregate evidence. |
| `RHD-2` — end/restart/expiry/revocation and ordered progress | **CLOSED** | Lines 74–78 and 90–96 add non-reused generation/instance IDs, broker-clock expiry, trusted renewal, idempotent tombstoned end/revoke, restart reconciliation, lease invalidation, and durable `UNDELIVERABLE_DELEGATE_ENDED`. Terminal messages remain in history, are neither rerouted nor deleted, and count for sequence-ordered watermark progress. B1, B3, B6, and B8 directly test replay, expiry, revoke/end, restart, stale-operation rejection, wrong-instance non-delivery, and post-terminal mailbox progress. |
| `RRA-1` — complete ownership relation | **OPEN — one residual blocker** | Lines 41–43 and A1/A5/A6 now independently count missing, unexpected, zero-owner, multi-owner, portable-owner, and retired/inactive-owner relations and test every non-owner, so offsetting errors close. However, A1 permits a retired/inactive ACL owner when backed by an exception artifact. That does not close the prior required zero-owner invariant. See `RRA-1R` below. |
| `VH-1` — append-only `VR-038` supersession | **CLOSED** | Lines 47–53 specify an immutable parent supersession of both implementation-admission fields, admit only `SESSION-REGISTRY-MVP` and the bounded host-authorization lane, keep `VR-042` parked, and retain separate child `OPEN`/`WORKING` authority. A7 makes each fact independently observable. Wolverine is no longer structurally blocked by the Session Registry/Revere Phase-2 dependency lane. |

## Remaining blocking finding

### RRA-1R — A1 can still pass with a retired/inactive identity authorized in the effective ACL

**Severity:** **HIGH / BLOCKING**  
**Likelihood:** Plausible because this work reconciles an existing ACL with known identity drift.  
**Affected design/criteria:** Revised addendum lines 38, 41–43, 164, and 168; A1 and A5. Prior review lines 110–117.

**Reproducible scenario:**

1. The effective ACL contains an agent ID that the fresh Registry classifies as retired or inactive.
2. A separate artifact approves retaining that entry and its hash is placed in the plan evidence.
3. Revised A1 treats that ownership as an approved exception and can report `PASS`; A5 then sees no unresolved A1 exception and may permit apply.
4. The retired/inactive agent ID remains an authenticated Revere-owned sender identity. In particular, preserving Revere v1 means the ACL ownership remains meaningful even where the new v2 Session Registry eligibility check is not involved.
5. This contradicts revised line 38's statement that retired identities are excluded from ACL ownership and the prior review's exact correction: post-state retired ownership must be zero; if cleanup is not authorized, A1 must report `FAIL` and park the decision.

**Minimal correction:**

- Remove the retired/inactive PASS exception from lines 41–43 and A1. Require `post_retired_inactive_acl_owner_count = 0`, just as `post_portable_acl_owner_count = 0` is required.
- Remove `approved_retired_inactive_exception_count` and `approved_exception_artifact_sha256` from A1 evidence. Rename `post_unapproved_retired_inactive_acl_owner_count` to `post_retired_inactive_acl_owner_count` so the field cannot hide an approved-but-still-effective owner.
- In A5, treat any nonzero retired/inactive ownership count as an unresolved A1 exception: report `FAIL`, do not apply, and park the exact cleanup for operator decision.
- If the operator expressly chooses to retain a retired/inactive ACL owner, record that as an explicit override of this named finding. Do not represent the invariant itself as passing.

This correction adds no identity list, token, verifier, locator, receipt, or payload to evidence. It is the exact prior acceptance invariant, not new hardening.

## Acceptance traceability and MVP proportionality

- The `GSP rework traceability` table maps every prior finding to concrete design language and criteria. RHD-1, RHD-2, and VH-1 have sufficient positive and negative acceptance coverage with minimal aggregate fields.
- A1/A5/A6 now prevent offsetting ownership totals and prove the full principal/identity relation, except for the residual retired/inactive exception above.
- The new generation, expiry, terminal disposition, and restart tests are bounded responses to the reproduced stale-delivery and head-of-line failures. They do not add per-delegation mailboxes, PKI, signed child capabilities, general RBAC, cross-host attestation, discovery, autonomous spawning, or production-hardening work.
- Evidence remains limited to identifiers, counts, hashes, and PASS/FAIL results; prohibited secrets and message content remain excluded.
- The revised cost comparison keeps governance/review below implementation/test effort and separately identifies the cost of required defect closure. Actual costs remain unknown.

## Gate decision

The revised addendum is **not approval-ready** while `RRA-1R` remains. `RHD-1`, `RHD-2`, and `VH-1` require no further design correction. One surgical A1/A5 edit and one focused confirmation are sufficient; no broader review or production-hardening work is requested.

This re-review authorizes no live Vertical append or transition, implementation, provisional-script approval, ACL or credential action, broker/service change, restart, live test, deployment, or external contact.

## Validation and model

- Validation performed: SHA-256 verification and full-text comparison of the revised addendum against the prior GSP findings; criterion-level traceability review for A1/A5/A6/A7 and B1–B8.
- Validation not performed: source-code or provisional-script inspection, executable tests, live Registry/ACL comparison, broker/service inspection, credential checks, or ledger mutation.
- File created by this re-review: this artifact only.
- Model used: GPT-6.1 Sol, GSP security-specialist role.
