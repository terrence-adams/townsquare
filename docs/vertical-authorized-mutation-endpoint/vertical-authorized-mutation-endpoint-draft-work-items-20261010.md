# Vertical Authorized Mutation Endpoint MVP — Draft Work Items

Status: **DRAFT — NOT IN THE LIVE VERTICAL LEDGER**  
Date: 2026-10-10  
Design authority: `vertical-authorized-mutation-endpoint-mvp-design-20261010.md`  
Governance: bounded MVP; acceptance is PASS/FAIL only against the criteria below.

## 1. Intake rule

These are proposed keys, not assigned `VR-*` references. Live opening and transitions require an append-only Vertical action by a current, authorized project owner after GSP and Tony Jaa review and a Helio checkpoint.

Venom/Eddie Brock is the primary operator-engagement and coordination vehicle and may relay operator decisions and receipts. Eddie is not assigned endpoint implementation, deployment, administration, credential custody, or sustained Story execution. Wolverine/Logan is the Feature and Story facilitator for dependency coordination, work-item state/evidence handoffs, consumer-acceptance facilitation, and cross-agent scheduling. Logan may not self-approve or act as the sole independent reviewer, and facilitation alone conveys no endpoint authority, credentials, or project-owner seat. If no current project-owner independently resolves through Gate, intake stops for an explicit owner-seat decision.

## 2. Proposed Feature

### `VERTICAL-AUTHORIZED-MUTATION-ENDPOINT-MVP`

| Field | Draft value |
| --- | --- |
| Level | Feature |
| Parent | `YNM-EPIC-011` |
| Dependencies | `VERTICAL-TYPED-UOW-AUTHORING-001` (VR-048) |
| Accountable owner | A current authorized project owner, independently resolved at intake; relay/facilitator roles do not confer this authority |
| Design owner | Ip Man |
| Operator decision/receipt relay | Eddie Brock on Venom |
| Feature facilitator | Wolverine / Logan |
| Security review | GSP |
| Coordination | Root session only; not endpoint ownership or administration |
| Scope | Deliver and adopt the smallest authorized network mutation boundary for Vertical work-item open/append operations |

Definition of done: both child Stories below are accepted; the operator has accepted the cutover evidence; direct client SMB writes are prohibited only after that acceptance; all exclusions remain true.

Feature PASS requires every Story criterion to PASS. Any child FAIL makes the Feature FAIL.

## 3. Proposed Story 1

### `VERTICAL-AUTHORIZED-MUTATION-SERVICE-001`

| Field | Draft value |
| --- | --- |
| Level | User Story |
| Parent | `VERTICAL-AUTHORIZED-MUTATION-ENDPOINT-MVP` |
| Dependencies | `VERTICAL-TYPED-UOW-AUTHORING-001` (VR-048) |
| Primary implementer | Bruce Lee |
| Story facilitator | Wolverine / Logan — dependencies, state/evidence handoffs, consumer acceptance, cross-agent scheduling |
| API/client integration peer review | Tony Jaa |
| Security review | GSP |
| QA | Ronda Rousey |
| Persistence/schema review | Jackie Chan only if implementation evidence shows a new persistence or schema decision is necessary |
| Deployment | None under this Story |
| Reference, not dependency | `IRON-CURTAIN-PERMIT-POC-CONTRACT` (VR-047); TownSquare implementation is not treated as reusable Vertical code |

### Story intent

Implement the three-route Vertical mutation service described by the design note, reusing the accepted VR-048 typed in-process authoring behavior behind an authenticated network boundary. The server, not each client, serializes authoritative writes and retries harmless unrelated global-domain-head churn. Semantic changes still stop for approval.

### Acceptance criteria

Evidence reports only `PASS` or `FAIL` plus the fields named by the criterion. Secrets, bearer values, raw provider locators, and credential material are forbidden evidence.

| ID | PASS condition | Required evidence fields |
| --- | --- | --- |
| S1 | The built artifact identifies the accepted design and VR-048 dependency, and exposes only the three approved routes. | artifact hash; design hash; VR-048 ref; route inventory |
| S2 | The pinned request and payload schemas and exact hash field sets produce byte-equal canonical requests at issuance/execution. Fixtures for top-level/nested caller `project`, alternate/duplicate `authority_ref`, top-level lifecycle, missing/hash-only payload, unknown field, changed payload, and mismatched canonical bytes each return the specified `409`/`422` code with zero writes; equivalent canonical inputs match. | fixture ID; HTTP status; machine code; semantic-payload hash; canonical-request hash; permit-binding hash; write count |
| S3 | Credential authentication, including revocation, occurs before receipt lookup. Missing, invalid, or revoked credential returns its named `401` with zero writes and no receipt disclosure. For first execution only, an authenticated caller resolves to current Registry ownership/assignment; authenticated but unauthorized/authority-denied/Gate-denied returns `403`. | fixture ID; principal ID or `NONE`; credential state; safe context or `NONE`; path `REPLAY|FIRST_EXECUTION|NONE`; HTTP status; machine code; write count; receipt disclosed `YES|NO` |
| S4 | Issuance validates exact authority coverage and permit/hash binding; an uncovered, changed, or alternate authority fixture returns its named error with zero writes. Lost issuance response with the same key/request returns the same unexpired cached permit; changed same-key request conflicts; cache loss/expiry requires a new key and full revalidation; pre-commit failure/retry exhaustion leaves the permit uncommitted; commit and consumption are one event. | fixture ID; permit ID; authority-coverage result; binding hash; idempotency-key hash; permit state; HTTP status; machine code; write count |
| S5 | On first execution only, the service validates fresh Registry ownership/assignment, resolves owner/actor, revalidates authority-reference coverage, dependencies and policy, and reruns Gate immediately before append; any change fails with zero writes. These mutable checks are not run before an exact committed replay. | path; Registry/assignment result; resolved actor/owner IDs; authority-reference result; dependency/policy hashes; Gate result; write count |
| S6 | The complete HTTP/error/retry matrix is machine-readable. Stale Story, parent, dependency, owner, policy, idempotency, permit-binding, expired-permit, and already-committed mismatch fixtures return their named `409` subcodes with zero writes; each `503` identifies whether the same request may retry without operator reapproval. | fixture ID; HTTP status; machine code; retry class; requested/current head where applicable; write count |
| S7 | Unrelated global-domain-head movement is handled by at most three internal retries without new approval; exhaustion is retryable `503` and leaves the permit uncommitted. Two authorized different-thread mutations each commit once. Safe observability contains only request/idempotency hashes, permit/receipt IDs, retry count/outcome, HTTP status, and machine code, with no secret, locator, raw key, or payload/content leakage. | fixture ID; request hash; idempotency-key hash; permit ID; receipt ID or `NONE`; retry count; retry outcome; HTTP status; machine code; leakage count; write count |
| S8 | Two concurrent authorized mutations against the same Story head cannot both append: exactly one commits and the other returns `STORY_HEAD_MISMATCH` or `EXACT_REPLAY` as applicable, with no additional write. | request IDs; initial head; winning receipt ID; losing machine code; final head; total write count |
| S9 | First commit returns the immutable receipt core, stable `receipt_id`, and `receipt_sha256`. Replay first authenticates the credential including revocation and validates only the static canonical/permit tuple. A revoked credential discloses nothing. For the same authenticated principal and exact tuple, assignment/Registry/Gate/dependency/owner/policy changes do not block the byte-identical receipt; if no receipt exists, those changes block first execution. A differing tuple returns the named conflict. | fixture ID; credential state; static-tuple result; lookup-order trace; mutable-state fixture; selected path; receipt ID or `NONE`; receipt-core hash or `NONE`; receipt hash or `NONE`; HTTP status; machine code; write count |
| S10 | The endpoint preserves the existing ledger projection/integrity contract and introduces no new persistence/schema. If a new durable structure is required, this criterion FAILS and work stops for Jackie Chan design review and an amended work item. | projection/integrity result; schema diff count; persistence diff count |

### Story 1 exclusions

- No deployment, production hardening, UI, generalized PKI, generalized RBAC, or unrelated Revere change.
- No client SMB cutover or access-control change.
- No provider locator, secret, bearer, or credential value in logs, receipts, evidence, or ledger payloads.
- No Venom/Eddie endpoint implementation, deployment, administration, credential custody, or sustained Story execution. No Wolverine/Logan self-approval, sole independent review, or endpoint authority/credential acquisition by virtue of facilitation.

### Story 1 estimate

- Implementation and mandatory tests: **18–28 engineering hours**.
- Governance, design/security/API review, and evidence review: **6–10 hours**.
- Unknown: whether the existing Vertical host exposes a suitable service runtime without packaging changes. That belongs to Story 2 preflight, not this implementation scope.

## 4. Proposed Story 2

### `VERTICAL-AUTHORIZED-MUTATION-CUTOVER-001`

| Field | Draft value |
| --- | --- |
| Level | User Story |
| Parent | `VERTICAL-AUTHORIZED-MUTATION-ENDPOINT-MVP` |
| Dependencies | `VERTICAL-AUTHORIZED-MUTATION-SERVICE-001` |
| Packaging/deployment owner | Francis Ngannou on a non-Venom target |
| Story facilitator | Wolverine / Logan — dependencies, state/evidence handoffs, consumer acceptance, cross-agent scheduling |
| Implementation support | Bruce Lee |
| API/client integration review | Tony Jaa |
| Security review | GSP |
| QA | Ronda Rousey |
| Governance gates | Helio Gracie checkpoints and final gateway |

### Story intent

Package, deploy, prove, and deliberately cut over the accepted service on a non-Venom authoritative target. Direct client SMB mutation remains permitted until the endpoint acceptance evidence is complete and the operator explicitly accepts the cutover; after that decision, clients must use the endpoint and must not fall back silently to direct writes.

### Acceptance criteria

| ID | PASS condition | Required evidence fields |
| --- | --- | --- |
| C1 | The deployed package and configuration are pinned to accepted Story 1 artifacts on a named non-Venom target and expose the approved routes only. | target host ID; artifact/config hashes; route inventory |
| C2 | TLS and per-host client authentication succeed for approved clients; wrong, missing, revoked, or expired credentials fail before mutation. No credential material appears in evidence. | certificate fingerprint; principal IDs; auth results; write counts |
| C3 | Shadow deployment passes health, read-only contract, and mutation dry-run checks while existing direct-write policy remains unchanged. | deployment ID; check results; mutation write count `0` |
| C4 | An authorized canary creates exactly one approved Vertical mutation through the endpoint and returns a valid atomic receipt; the authoritative ledger and projection validate. | request ID; receipt/event/thread/content hashes; before/after write count; integrity result |
| C5 | Direct client SMB mutation is prohibited only after C1–C4 PASS and explicit operator cutover acceptance. A direct-write attempt then fails with zero writes while endpoint append still succeeds. | acceptance reference; policy/ACL hash; direct-write result; endpoint receipt; write counts |
| C6 | At least two approved non-Venom clients use endpoint-only mutation successfully, and authoritative evidence identifies the endpoint service as the sole writer for their test window. | client principal IDs; receipt IDs; test window; writer inventory; write counts |
| C7 | VR-072 remains unchanged and parked during this MVP. A hash-pinned first-consumer plan names it for a separate post-Feature transaction, requires its then-current Story head and exact semantic approval, and does not require an operator decision for unrelated global-head churn. No VR-072 transaction is executed by this criterion. | VR-072 observed head; unchanged result; first-consumer plan hash; transaction result `NOT_RUN` |
| C8 | No prohibited ownership/custody and no excluded Revere, UI, generalized PKI/RBAC, or production-hardening work occurred. | role roster; changed-systems inventory; exclusion result |

### Story 2 exclusions and holds

- No VR-072 transition or other semantic ledger mutation is authorized by this Story's creation alone.
- No Revere broker, relay, mailbox, ACL, credential, service, adapter, or hosted-subagent work.
- Eddie/Venom is limited to operator-decision and receipt relay, not endpoint implementation, deployment, administration, credential custody, or sustained Story execution. Wolverine/Logan facilitation does not grant self-approval, sole-review status, endpoint authority, administration, or credentials.
- No client direct-write prohibition before operator acceptance of C1–C4.
- No automatic fallback to direct SMB mutation after cutover. Endpoint unavailability makes mutation unavailable until service restoration or an explicitly approved temporary rollback.
- No generalized multi-project API, UI, production-scale availability system, or unrelated hardening.

### Story 2 estimate

- Packaging, deployment workflow, mandatory canary tests, and controlled cutover: **8–12 engineering hours**.
- Governance, security/API review, checkpoints, acceptance, and evidence review: **3–6 hours**.
- Unknowns: eligible non-Venom target runtime, listener port, certificate issuer/pinning mechanism, and the existing client direct-write permission surface. Francis resolves these through read-only preflight before any deployment action.

## 5. Parked future Feature candidate — Option C

### `VERTICAL-RECEIPT-RECOVERY-CAPABILITY-001`

| Field | Draft value |
| --- | --- |
| Level | Feature candidate |
| Title | Vertical Receipt Recovery Capability and Token Lifecycle |
| Parent | `YNM-EPIC-011` |
| Relationship | Related future follow-up only; not a dependency of the endpoint Feature or either Story |
| State | `FUTURE / PARKED / NOT ADMITTED FOR IMPLEMENTATION` |
| Scope now | None; no credential, token, endpoint, grant, rotation, revocation, custody, acceptance, or implementation design |

This candidate records Sensei's Option C direction without expanding the MVP. It has no live `VR-*` reference, creates no live event, contributes no current acceptance criterion or cost, and cannot block intake, implementation, acceptance, or cutover of the endpoint Feature/Stories.

## 6. Combined bounded cost

- MVP implementation and mandatory delivery/testing: **26–40 engineering hours**.
- Governance, review, and acceptance: **9–16 hours**.

The governance estimate remains below the implementation estimate. Optional architecture debate, production-hardening analysis, and unrelated follow-up proposals are deferred unless a criterion reproduces a failure or Sensei expands scope.

The parked Option C candidate is excluded from both estimates until separately admitted and designed.

## 7. Draft item release rule

These items may be proposed to the live ledger only after:

1. GSP reports security design PASS or enumerates required rework.
2. Tony Jaa reports API/client integration design PASS or enumerates required rework.
3. Helio issues the Dojo checkpoint for exact, hash-pinned intake artifacts.
4. A current project owner is independently resolved and validated; neither Eddie's relay nor Logan's facilitation is treated as authority or self-approval.
5. Sensei approves the exact append-only intake action.

No live `VR-*` number, implementation authorization, deployment authorization, credential action, or ledger mutation is implied by this draft.
