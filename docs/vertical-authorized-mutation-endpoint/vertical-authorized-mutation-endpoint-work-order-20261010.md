# Vertical Authorized Mutation Endpoint MVP — Dojo Work Order

Status: **DRAFT — PLANNING ONLY**  
Date: 2026-10-10  
Design owner: Ip Man  
Coordinator: root session (coordination only)  
Source design: `vertical-authorized-mutation-endpoint-mvp-design-20261010.md`  
Draft items: `vertical-authorized-mutation-endpoint-draft-work-items-20261010.md`

This work order does not authorize code, ledger writes, credentials, deployment, access-control changes, service operations, or live transactions.

## 1. Outcome

Deliver the smallest accepted Vertical mutation endpoint that keeps semantic operator approval meaningful while removing client exposure to harmless global-domain-head churn and direct SMB ledger mutation. The endpoint uses per-thread compare-and-append, server-side Gate/owner revalidation, server-managed authoritative serialization, exact idempotency, and an atomic receipt.

## 2. Separation of duties

| Responsibility | Assigned role |
| --- | --- |
| Design and work-item package | Ip Man |
| Operator engagement, decision and receipt relay | Eddie Brock on Venom |
| Feature/Story facilitation and cross-agent scheduling | Wolverine / Logan |
| Security design and permit-boundary review | GSP |
| Primary service implementation | Bruce Lee |
| API/client integration peer review | Tony Jaa |
| Persistence/schema consultation | Jackie Chan only if a new persistence/schema need is reproduced |
| QA and acceptance evidence | Ronda Rousey |
| Packaging and deployment workflow | Francis Ngannou on a non-Venom target |
| Dojo checkpoints/gateway | Helio Gracie |
| Coordination | root session only |

Venom/Eddie Brock is the primary operator-engagement and coordination vehicle and may relay operator decisions and receipts, but is not assigned endpoint implementation, deployment, administration, credential custody, or sustained Story execution. Wolverine/Logan facilitates dependency coordination, work-item state/evidence handoffs, consumer acceptance, and cross-agent scheduling for the Feature and both Stories. Logan may not self-approve or serve as sole independent reviewer; facilitation does not silently confer endpoint authority, credentials, administration, or a project-owner seat. Either may later be a bounded consumer under separate enrollment and acceptance authority.

## 3. Ordered delivery

### Gate 0 — Document review

1. GSP reviews the design, single-source project/authority rules, pinned hash fields, permit lifecycle, committed-replay ordering, authority revalidation, safe observability, secret exclusions, and cutover access boundary.
2. Tony Jaa reviews the pinned request/payload/result schemas, HTTP/error/retry matrix, issuance and mutation retry behavior, immutable receipt contract, non-Venom deployment assumptions, and the distinction between the reusable Iron Curtain permit concept and non-reusable TownSquare implementation.
3. Any blocking finding returns only the affected design/draft item to Ip Man for bounded amendment.

Release: GSP PASS and Tony PASS against the documented MVP scope.

### Gate 1 — Dojo game plan

Helio verifies the reviewed hashes, proposed hierarchy, dependencies, role separation, costs, exclusions, and explicit future Actions. No implementer begins before this checkpoint.

### Gate 2 — Future live Vertical intake

An independently validated current project owner prepares append-only intake for exactly the following items. Eddie may relay the operator decision and Logan may coordinate the handoff, but neither role substitutes for Gate-resolved authority or independent approval:

1. Feature `VERTICAL-AUTHORIZED-MUTATION-ENDPOINT-MVP` under `YNM-EPIC-011`, dependent on `VERTICAL-TYPED-UOW-AUTHORING-001` (VR-048).
2. Story `VERTICAL-AUTHORIZED-MUTATION-SERVICE-001` under that Feature, dependent on `VERTICAL-TYPED-UOW-AUTHORING-001` (VR-048).
3. Story `VERTICAL-AUTHORIZED-MUTATION-CUTOVER-001` under that Feature, dependent on Story 1.

The Iron Curtain permit contract is a cited concept, not a dependency. VR-072 is a motivating future consumer, not a dependency.

Release: exact reviewed document hashes, fresh ledger/item heads, hierarchy/key collision checks, Helio checkpoint, and Sensei approval of the exact append command. If no eligible current project owner exists, stop for an owner-seat decision.

### Gate 3 — Story 1 implementation

Bruce Lee implements only the accepted three-route service and mandatory tests. He reuses the accepted VR-048 typed authoring path and does not create a parallel ledger writer. No deployment or client ACL change is in scope.

Release: Story 1 is live and WORKING with implementation explicitly authorized; no open review rework.

### Gate 4 — Story 1 peer/security review

Tony Jaa independently reviews the one-source project/authority contract, exact schema/hash field sets, issuance/execution equality, machine-readable errors and retry classes, issuance recovery/expiry/exhaustion, Option A receipt-lookup ordering, and stable receipt ID/hash. GSP confirms only that credential revocation and static tuple checks remain before lookup and that mutable-check bypass is limited to immutable safe receipt recovery; a full security rereview is unnecessary unless GSP identifies a regression. Jackie Chan is engaged only if S10 reproduces a persistence/schema requirement.

Release: Tony PASS, GSP PASS, and S10 PASS; otherwise return bounded rework.

### Gate 5 — Story 1 QA

Ronda runs S1–S10, including caller-project and duplicate-authority zero-write fixtures; exact schema/hash equality; lost issuance response, changed-key request, cache loss, expiry, and retry exhaustion; credential-revoked no-disclosure behavior; `401` versus `403`; every named `409` and retryable `503`; static tuple checks before lookup; mutable assignment/Registry/Gate/dependency/owner/policy changes after lookup only when no exact receipt exists; byte-identical receipt replay; safe S7 correlation and leakage checks; concurrency; integrity; and zero direct client SMB mutation.

Release: all S1–S10 PASS with only the specified evidence fields.

### Gate 6 — Implementation handoff checkpoint

Helio reviews the implementation, review, and QA outputs. Story 2 must not begin while Story 1 has an open FAIL, mismatch, exposed credential, or unreviewed schema change.

### Gate 7 — Story 2 package and shadow deployment

Francis performs read-only target/runtime/port/certificate/direct-write-surface preflight, then prepares packaging and a deployment workflow for an approved non-Venom target. Deployment remains a future permission-gated Action. Shadow mode does not change direct-write permissions.

Release: Story 2 is live and WORKING; exact package/config hashes have review; target is non-Venom; Helio checkpoint and exact deployment approval are present.

### Gate 8 — Live canary and cutover evidence

After separate approval, Francis deploys; Ronda runs C1–C4. GSP and Tony review only evidence relevant to their lanes. No direct-write prohibition occurs yet.

Release: C1–C4 PASS and no credential exposure.

### Gate 9 — Operator cutover decision

Helio presents the exact evidence and access-control change as a gateway Action. Sensei decides whether to accept the endpoint and prohibit direct client SMB mutation.

Release: explicit approval of the exact pinned access-control action.

### Gate 10 — Controlled cutover and closure evidence

Francis applies only the approved direct-write prohibition. Ronda runs C5, C6, and C8. Clients must not silently fall back to SMB writes. Service unavailability becomes a clean mutation failure unless Sensei separately approves a temporary rollback.

Release: C1–C8 PASS. For C7, `NOT_RUN` is the required transaction result: PASS means VR-072 is unchanged and parked and the separately gated first-consumer plan is pinned; it does not mean the transition ran.

### Gate 11 — First post-MVP consumer

VR-072 is eligible as the first post-MVP endpoint transaction only after Feature acceptance and a separate, exact semantic transaction approval. That transaction is not part of implementation or cutover authorization. Its purpose is to show that unrelated global-head churn no longer requires operator reapproval while story-head, payload, owner, dependency, policy, or authorization changes still stop.

## 4. Release invariants

- The client supplies one pinned request envelope and expected Story head; it does not supply project, alternate authority references, protected provenance, or ledger files. `authority_ref` exists only as the canonical three-field object; project is server-resolved.
- The server resolves actor/owner, rechecks current policy and Gate, and compares the per-thread head immediately before append.
- Server retries are bounded to unrelated global-domain-head churn. A change to story head, semantic payload, dependencies, owner, authorization, policy, action, target, or permit validity stops without a write.
- Permit issuance and execution both carry the same exact eight-field typed payload. The server computes the four pinned hashes at each boundary, requires byte-equal canonical requests, validates authority-reference coverage at issuance, and revalidates it immediately before append.
- Lost issuance response recovers the same cached unexpired permit; expiry/cache loss uses a new key after full revalidation. A permit is durably consumed only by its committed event; retry exhaustion leaves it uncommitted.
- Credential authentication, including current credential revocation, and static canonical/permit tuple validation occur before every receipt lookup. Revocation blocks all operations and all receipt disclosure.
- For the same authenticated principal and exact tuple, committed-receipt lookup occurs before stale-head, expiry/consumption, current assignment/Registry/Gate/policy/authorization, owner, and dependency checks. Non-exact reuse fails; exact replay returns only the immutable safe receipt. Those mutable changes block first execution when no receipt exists.
- HTTP status, machine code, and retry class decide client behavior. A retryable `503` or non-semantic encoding repair never silently demands operator reapproval; semantic snapshot changes do.
- Safe observability is limited to request/idempotency hashes, non-secret permit/receipt IDs, retry count/outcome, HTTP status, and machine code.
- Client identity context contains only `host_id`, `agent_id`, and internal `session_id`; evidence may add only the criterion's safe hashes, IDs, status, code, and retry fields and never contains raw provider locators or secrets.
- After accepted cutover, endpoint clients perform zero direct SMB ledger writes.

## 5. Permission-gated future Actions

None of these Actions is authorized by this work order:

1. Append or transition any live Vertical Feature or Story.
2. Generate, install, rotate, revoke, or distribute endpoint certificates or client credentials.
3. Reserve/open a listener, package/install software, deploy, start/restart a service, or change host configuration.
4. Run an authoritative mutation canary or any other live ledger transaction.
5. Change SMB/share/file permissions or prohibit direct client writes.
6. Execute the VR-072 transition or any Revere action.

Each later Action requires the immediately preceding peer/QA/checkpoint gates, exact artifact and current-state pins, and Sensei approval where specified.

## 6. Explicit exclusions

- Generalized PKI, enterprise RBAC, UI, multi-project mutation APIs, high-availability architecture, unrelated observability, and production hardening not required by a criterion.
- Any Revere broker, relay, mailbox, adapter, ACL, credential, service, or hosted-subagent implementation.
- Reuse claims for the TownSquare Iron Curtain service code; only its reviewed permit concept may inform the Vertical-specific boundary.
- Any change to VR-072 during endpoint implementation/cutover.
- Assigning Venom/Eddie endpoint implementation, deployment, administration, credential custody, or sustained Story execution; or treating Wolverine/Logan facilitation as self-approval, sole independent review, endpoint authority, administration, credentials, or a project-owner seat.

### Parked future follow-up

`VERTICAL-RECEIPT-RECOVERY-CAPABILITY-001` — **Vertical Receipt Recovery Capability and Token Lifecycle** — is a future parked Feature candidate under `YNM-EPIC-011`. It is not part of this MVP, not admitted for implementation, not a dependency of the endpoint Feature/Stories, and defines no recovery credential or token design here. Creating its live Vertical item or designing its token lifecycle requires a separate future work order and Dojo gate.

## 7. Validation and failure behavior

- Ronda reports every accepted criterion as `PASS` or `FAIL`, with only its named evidence fields.
- Any required criterion FAIL stops the dependent gate. It does not authorize expanded hardening.
- A receipt mismatch, duplicate write, story-head violation, authorization bypass, credential exposure, integrity failure, or direct-write fallback after cutover is blocking.
- Endpoint unavailability before cutover leaves existing policy unchanged. After cutover it causes a clean endpoint failure; direct-write restoration is a separate operator decision.
- Optional findings without a reproduced criterion failure are parked for their own work item.

## 8. Cost control

- Implementation and mandatory delivery/testing: **26–40 engineering hours**.
- Governance, security/API review, evidence review, and checkpoints: **9–16 hours**.
- Jackie Chan participation is conditional and excluded from the current estimate; a reproduced S10 failure triggers a separately estimated bounded design amendment.
- Optional review or follow-up must be deferred before governance exceeds implementation cost unless a criterion fails or Sensei explicitly expands scope.
- The parked Option C Feature candidate has no current implementation or governance estimate and is excluded from this MVP's cost totals.

## 9. Planning-package acceptance

This planning package is ready for review when:

1. Exactly three new documentation artifacts exist in the package directory.
2. The Feature and two Story keys, levels, parents, and dependencies agree across the design and draft items.
3. The role roster contains the required separation of duties and no prohibited owner/administrator/custodian assignment.
4. Every endpoint criterion has a binary PASS/FAIL rule and bounded evidence fields.
5. No application code, live ledger, credential, broker/service, ACL, or deployment state changed.

## WORK ORDER

- Document: Ip Man — maintain the design, draft Vertical hierarchy, interfaces, acceptance criteria, and explicit Actions.
- Discuss/review: GSP — security and permit boundary; Tony Jaa — API/client integration and non-Venom service assumptions.
- Facilitate: Wolverine / Logan — dependency coordination, Story state/evidence handoffs, consumer acceptance, and cross-agent scheduling without self-approval or endpoint authority.
- Relay: Eddie Brock on Venom — operator decisions and receipts without sustained Story execution or endpoint administration.
- Decide/gate: Helio Gracie — reviewed-design checkpoint, each delivery checkpoint, and final gateway to Sensei.
- Implement: Bruce Lee — Story 1 service only after reviewed design and live work-item admission.
- Package/deploy: Francis Ngannou — Story 2 workflow on a non-Venom target, only after permission gates.
- Peer review: Tony Jaa — pinned schemas/hashes, API/error/retry contract, issuance lifecycle, replay ordering, receipt stability, and integration behavior.
- Security review: GSP — authentication/authorization, canonical project/authority sources, permit binding and consumption, replay bypass limits, safe observability, credential hygiene, and server-side resolution.
- QA: Ronda Rousey — S1–S10 and C1–C8, including every named mismatch/retry/replay fixture, reporting PASS/FAIL only.
- Conditional specialist: Jackie Chan — only if S10 proves persistence/schema work is required.
- Watch for: duplicate project/authority sources; assignment/Registry/Gate/dependency/owner/policy checks before exact committed replay; omission of credential-revocation or static tuple checks before lookup; ambiguous permit consumption; operator reapproval on transport-only retry; payload leakage; prohibited role assignment; global-head pins leaking back to clients; semantic changes hidden as retries; direct-write fallback after cutover; or governance exceeding implementation cost.
