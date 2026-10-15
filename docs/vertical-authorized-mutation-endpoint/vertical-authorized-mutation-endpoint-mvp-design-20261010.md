# Vertical authorized mutation endpoint MVP — design

Status: **DRAFT FOR DOJO REVIEW — NO LEDGER, CODE, CREDENTIAL, DEPLOYMENT, OR ACL CHANGE AUTHORIZED**  
Date: 2026-10-10  
Design owner: **Ip Man**  
Decision owner: **Sensei / Operator**  
Security review: **GSP**  
API and client integration review: **Tony Jaa**  
Independent QA: **Ronda Rousey**  
Packaging and deployment workflow: **Francis Ngannou, non-Venom target only**  
Implementation: **Bruce Lee**  
Feature and Story facilitation: **Wolverine / Logan**  
Dojo gates: **Helio Gracie**  
Coordination: **root session only; root is not endpoint owner, implementer, reviewer, deployer, administrator, or credential custodian**

## 1. Decision and bounded outcome

Build a small Vertical-owned mutation service so authorized agents submit typed work-item openings and transitions through an approved endpoint instead of writing the authoritative SMB ledger directly.

The service preserves meaningful approval but removes operator re-engagement caused only by unrelated global-domain-head churn. A client approval binds the intended semantic mutation and target Story head. The server, not the client, owns global serialization, current projection refresh, Gate execution, append, exact-retry recovery, and the receipt.

The bounded structure is one Feature with two Stories:

1. Feature `VERTICAL-AUTHORIZED-MUTATION-ENDPOINT-MVP` under `YNM-EPIC-011`, dependent on VR-048;
2. Story `VERTICAL-AUTHORIZED-MUTATION-SERVICE-001` under that Feature, dependent on VR-048, to implement and prove the service contract on an isolated ledger and then the authoritative ledger with direct client writes still available; and
3. Story `VERTICAL-AUTHORIZED-MUTATION-CUTOVER-001` under that Feature, dependent on the service Story, to deploy on the non-Venom authoritative-ledger host, accept the endpoint, then prohibit direct client SMB writes and prepare the first separately approved transaction through it.

One Story was rejected because endpoint correctness and write-path cutover have different owners, risks, and reversible boundaries. More than two Stories was rejected because this MVP does not include generalized identity, policy, UI, high availability, or production hardening.

## 2. Authoritative context and placement

### Hard dependency

`VR-20261009-ynm-048`, `VERTICAL-TYPED-UOW-AUTHORING-001`, is OPEN under `YNM-EPIC-011`. It defines the in-process typed `open_unit_of_work()` and `append_unit_of_work(..., expected_head=...)` façade, server-side project-owner resolution, immutable prepared input, and immediate pre-append Gate reauthorization.

- Thread: `01a12008-b94e-7555-b512-eb5aa66ad534`
- Opening event: `01a12008-b950-7618-be9a-7535f16b9dce`
- Opening content SHA-256: `306e95445b33b3472193c5b53b591482436e99848788b94552da36fd9a2e2ac9`
- Opening file: `\\192.168.2.3\YNM\Projects\Vertical\ledger\VR-20261009-ynm-048.0-OPEN.txt`
- Reconciled design: `C:\Workspace\artifacts\design-vertical-typed-uow-authoring-20261009-reconciled.md`
- Reconciled-design SHA-256 observed before this draft: `a9f59e034a8e4978625afbdc79b60696990facb5b8bca2cd50f0e22a135fa8ab`

The endpoint Feature and service Story depend on accepted completion of VR-048. They do not duplicate or bypass it.

### Reference, not dependency or reusable implementation

`VR-20261008-ynm-047`, `IRON-CURTAIN-PERMIT-POC-CONTRACT`, defines useful exact-action permit properties: actor/action/target binding, canonical payload hash, target version, idempotency, expiry, single use, exact retry, denial, and no bearer disclosure. Its implementation Story, `VR-20261008-ynm-049` / `IRON-CURTAIN-PERMIT-POC-IMPLEMENT`, protects TownSquare `POST /v1/events` and is not Vertical code.

This design reuses only reviewed concepts. It does not import TownSquare code, claim TownSquare acceptance for Vertical, or make either Iron Curtain Story a hard dependency.

### Motivating consumer, not dependency

`VR-20261009-ynm-072`, `REVERE-HOST-BOUND-AUTHORIZATION-RECONCILIATION`, demonstrated the gap: its reviewed direct-append command became unusable because an unrelated global-domain-head change invalidated a client pin even though the target Story head and approved semantic payload had not changed.

VR-072 remains parked. It is the first planned post-MVP transaction only after endpoint acceptance or after a separately approved old-path command. Nothing in this design authorizes its transition or any Revere action.

## 3. Ownership and separation of duties

Venom/Eddie Brock is the primary vehicle for operator engagement and coordination: Eddie may relay operator decisions and receipts, but is not assigned endpoint implementation, deployment, administration, credential custody, or sustained Story execution. Wolverine/Logan is an assignable resource and serves as Feature/Story facilitator for dependency coordination, work-item state and evidence handoffs, consumer-acceptance facilitation, and cross-agent scheduling. Facilitation never grants endpoint authority or credentials and cannot substitute for independent approval.

| Responsibility | Owner |
|---|---|
| Design | Ip Man |
| Operator engagement, decision and receipt relay | Eddie Brock on Venom |
| Feature/Story facilitation, dependency and evidence handoffs, consumer-acceptance scheduling | Wolverine / Logan |
| Security and permit review | GSP |
| Primary implementation | Bruce Lee |
| API/client integration peer review | Tony Jaa |
| Independent QA | Ronda Rousey |
| Package, deploy, service administration, endpoint certificate and secret custody | Francis Ngannou on the approved non-Venom target |
| Persistence/schema review | Jackie Chan only if implementation proves that the event-carried idempotency model is insufficient and a persistence/schema change is proposed |
| Delivery checkpoints and gateway | Helio Gracie |
| Final semantic decisions and cutover acceptance | Sensei / Operator |
| Coordination | root session only |

Venom and Wolverine may later be bounded endpoint consumers for acceptance evidence. Eddie's relay role does not make him an endpoint owner, administrator, signing-key custodian, implementer, deployer, or sustained Story executor. Logan may not self-approve or serve as the sole independent reviewer; his facilitator role does not silently create endpoint authority, credential custody, or a project-owner seat. Any later consumer enrollment is separately authorized.

The live Vertical opening must be authored by a currently authorized Vertical project-owner resolved independently through the existing Gate. Eddie may relay the operator's decision and Logan may facilitate the handoff, but neither function is authority. If no current project-owner resolves, intake stops for a separate seat decision.

## 4. MVP topology and trust boundary

The service runs on the internal authoritative-ledger NAS at `192.168.2.3`, or another operator-approved non-Venom host with an exclusive write mount to that ledger. The NAS-local deployment is preferred because only one service identity then needs write access. The exact listener port is selected during Francis's read-only deployment preflight to avoid collision.

Live bearer use requires TLS with a pinned endpoint certificate. This is endpoint-specific transport protection, not a generalized PKI program. The service is LAN-only and receives no public route.

The MVP uses two authorization layers:

1. **Caller authentication.** An opaque Vertical client credential maps server-side to one fixed `principal_id`, `host_id`, and allowed exact `agent_id` set. Only credential digests are stored. The endpoint verifies a fresh, non-stale Registry record for the supplied safe host and agent identity. The internal session ID is evidence, not an authentication factor.
2. **Semantic authority.** A short-lived opaque action permit binds one approved semantic mutation. The permit is signed by an endpoint-only secret, is single-use except for exact retry, and carries no authority beyond its bound claims.

Francis holds endpoint signing and service credentials on the non-Venom target. Client credentials stay on their enrolled non-Venom test hosts during MVP. GSP reviews handling. No token, token hash, signing key, certificate private key, raw provider locator, or provider session identifier enters Vertical, logs, receipts, or this repository.

## 5. Approved API contract

The service exposes exactly three MVP routes under `/v1/vertical`:

### `POST /v1/vertical/action-permits`

Headers:

- `Authorization: Bearer <opaque-client-credential>`
- `Idempotency-Key: <caller-generated-opaque-key>`

The request body is schema `vertical.action-permit-request.v1` and has exactly these top-level fields:

```json
{
  "api_version": "vertical.action-permit-request.v1",
  "authority_ref": {
    "authority_type": "VERTICAL_EVENT|OPERATOR_DECISION",
    "authority_id": "one stable event or approval-receipt identifier",
    "authority_sha256": "sha256 of the immutable authority content"
  },
  "operation": "OPEN|APPEND",
  "work_item_key": "exact-key",
  "thread_uid": "required for APPEND; absent for OPEN",
  "expected_story_head": {
    "event_uid": "required for APPEND",
    "content_sha256": "required for APPEND"
  },
  "parent_anchor": {
    "key": "required when an OPEN has a parent",
    "event_uid": "current approved parent head",
    "content_sha256": "current approved parent head"
  },
  "dependency_snapshot": [
    {"key": "dependency-key", "event_uid": "head", "content_sha256": "head", "state": "state"}
  ],
  "policy_sha256": "Gate and endpoint policy bundle hash",
  "typed_payload": {
    "schema": "vertical.vr048-uow-input.v1",
    "state": "OPEN|WORKING|BLOCKED|RESOLVED|CLOSED|CANCELLED",
    "authoring_mode": "current-project-owner|ordinary-non-seat",
    "actor": "ordinary represented author or null",
    "role_acted_under": "ordinary role or null",
    "header": {"string-key": "string-value"},
    "body": "exact event body string",
    "routing": {"string-key": "string-value"}
  },
  "client_context": {
    "host_id": "safe host name",
    "agent_id": "exact Registry identity",
    "internal_session_id": "safe internal assignment/session identifier"
  }
}
```

There is one source for each formerly ambiguous field:

- `project` is never caller input. The endpoint resolves one `resolved_project` from its configured Vertical scope and current Gate state. Any `project` key at the top level or inside `typed_payload.header` or `typed_payload.routing` is rejected with `422 CALLER_PROJECT_FORBIDDEN`, even if its value matches.
- `authority_ref` exists only as the exact three-field object above. It is forbidden inside the typed payload, header, routing, or any alternate header. Duplicate or alternate representations fail with `422 AUTHORITY_REF_DUPLICATE`.
- lifecycle exists only as `typed_payload.state`. The former top-level `lifecycle` field is forbidden.
- authenticated execution provenance and the VR-048 `project` argument are server-constructed; they are not part of caller `typed_payload`.

All eight `typed_payload` fields shown above are present in canonical JSON, using explicit `null` for inapplicable `actor` and `role_acted_under` and `{}` for empty maps. No unknown field is accepted. `OPEN` requires `state=OPEN` and owner mode; `APPEND` forbids `OPEN`. VR-048 protected fields (`project`, `event_type`, `actor_provenance`, `schema_version`) are forbidden in both maps; `actor` and `role_acted_under` are allowed only in their two named typed fields under VR-048 mode rules.

The permit request carries that exact payload, not a caller-supplied payload hash alone. Before issuance, the server resolves project/owner/policy, validates that the canonical `authority_ref` covers the exact operation, target, Story head, parent/dependencies, owner, policy, and payload, and computes all hashes itself. A first successful issuance returns `201 PERMIT_ISSUED` with the bearer, non-secret permit ID, expiry, and the four pinned hashes. The bounded in-memory issuance cache retains that exact response only through expiry so a lost response can return `200 PERMIT_ISSUANCE_REPLAY`.

### `POST /v1/vertical/work-items`

Creates one typed `OPEN` event. It requires the client credential, permit, idempotency key, and the byte-equivalent canonical `vertical.action-permit-request.v1` envelope used at issuance. The server rejects a hash-only execution request and all caller-supplied protected fields. The VR-048 façade resolves the project-owner and constructs protected event fields.

### `POST /v1/vertical/threads/{thread_uid}/events`

Appends one typed non-opening event. It requires the exact expected Story head event UID and content SHA-256 and the byte-equivalent canonical `vertical.action-permit-request.v1` envelope used at issuance. The server derives the execution identity from the authenticated principal, applies VR-048 authoring-mode rules, and calls the façade with `expected_head` immediately before append.

At both mutation routes, the server canonicalizes the execution payload again, recomputes its semantic-payload and complete-request hashes, and requires byte-equivalent canonical JSON and equal hashes to the permit-bound issuance envelope. A missing or changed payload, a caller-supplied hash without the payload, or any issuance/execution mismatch fails before a write.

### Machine-readable result and retry matrix

Every response body contains `api_version=vertical.mutation-result.v1`, `status`, `code`, `request_sha256` when canonicalization succeeded, and `retry_class=NEVER|SAME_REQUEST|NEW_PERMIT_AFTER_REVALIDATION`. Error text is non-authoritative.

| HTTP | Machine code | Meaning and retry rule | Write guarantee / operator effect |
|---|---|---|---|
| `201` | `PERMIT_ISSUED` | First successful, fully revalidated permit issuance | Zero ledger writes; no new operator approval beyond the bound authority |
| `201` | `EVENT_CREATED` | First committed mutation | Exactly one write; no new approval |
| `200` | `EXACT_REPLAY` | After current credential authentication/revocation check and static tuple validation, committed-receipt lookup matched principal, permit, idempotency, and canonical request | Zero new writes; return immutable original receipt; no new approval |
| `200` | `PERMIT_ISSUANCE_REPLAY` | Same issuance key and request recovered the same unexpired cached permit response | Zero writes; no new approval |
| `401` | `AUTHENTICATION_REQUIRED`, `CLIENT_CREDENTIAL_INVALID`, or `CLIENT_CREDENTIAL_REVOKED` | Caller credential is missing, invalid, or currently revoked | Zero writes and no receipt disclosure; `NEVER` until authenticated with a valid non-revoked credential |
| `403` | `CALLER_NOT_AUTHORIZED`, `AUTHORITY_REF_NOT_COVERING`, or `GATE_DENIED` | Authenticated principal lacks current semantic authority | Zero writes; operator/project-owner action only if authority must change |
| `409` | `IDEMPOTENCY_CONFLICT` | Same idempotency key with different canonical request, principal, or permit | Zero writes; `NEVER` for that key |
| `409` | `CANONICAL_REQUEST_MISMATCH` or `PERMIT_BINDING_MISMATCH` | Issuance/execution envelope, canonical bytes, or permit claims differ | Zero writes; semantic change requires new approval; transport defect does not |
| `409` | `STORY_HEAD_MISMATCH`, `PARENT_HEAD_MISMATCH`, `DEPENDENCY_SNAPSHOT_MISMATCH`, `OWNER_CHANGED`, or `POLICY_CHANGED` | A bound semantic snapshot changed | Zero writes; fresh semantic authority/approval required |
| `409` | `PERMIT_EXPIRED` | Uncommitted permit expired | Zero writes; `NEW_PERMIT_AFTER_REVALIDATION`; no operator reapproval if every semantic binding and authority remain valid |
| `409` | `PERMIT_ALREADY_COMMITTED` | Permit has a committed event but the replay tuple is not exact | Zero writes; `NEVER`; investigate mismatch |
| `422` | `MALFORMED_REQUEST`, `UNKNOWN_FIELD`, `CALLER_PROJECT_FORBIDDEN`, `AUTHORITY_REF_DUPLICATE`, or `HASH_ONLY_PAYLOAD_FORBIDDEN` | Request violates the pinned schema | Zero writes; correct client request; no operator reapproval for a non-semantic encoding repair |
| `503` | `REGISTRY_UNAVAILABLE`, `PROJECTION_UNAVAILABLE`, `STORE_UNAVAILABLE`, or `GLOBAL_SERIALIZATION_RETRY_EXHAUSTED` | Required state is unavailable or three internal unrelated-global-head retries were exhausted | Zero new writes; if a prior commit exists, step 3 returns `200 EXACT_REPLAY` instead. The exact same request/permit may retry while unexpired, with no operator reapproval |

## 6. Canonical request and permit binding

The implementation uses Vertical's existing canonical serializer. It does not introduce a second canonicalization profile.

The exact hash inputs are pinned:

1. `semantic_payload_sha256 = SHA256(canonical_json({schema,state,authoring_mode,actor,role_acted_under,header,body,routing}))`, with exactly those `typed_payload` fields.
2. `canonical_request_sha256 = SHA256(canonical_json({api_version,authority_ref,operation,work_item_key,thread_uid,expected_story_head,parent_anchor,dependency_snapshot,policy_sha256,typed_payload,client_context}))`, with exactly those request fields and the full payload, not its hash.
3. `idempotency_key_sha256 = SHA256(UTF8(Idempotency-Key))`.
4. `permit_binding_sha256 = SHA256(canonical_json({canonical_request_sha256,semantic_payload_sha256,idempotency_key_sha256,principal_id,resolved_project,resolved_owner,permit_id,issued_at,expires_at,audience}))`.

Map keys use Vertical canonical ordering; strings are UTF-8 without trimming or case folding unless VR-048 already specifies normalization. Arrays retain order except `dependency_snapshot`, which is rejected unless already sorted by case-sensitive `key`. Issuance and execution are equal only when their canonical request bytes and all four hashes match.

The action permit binds:

- authenticated principal, safe host ID, exact agent ID, and operation;
- server-resolved project, key, thread, `typed_payload.state`, parent anchor, and exact Story head;
- semantic payload hash and dependency snapshot hash;
- current resolved owner/seat identity where applicable;
- Gate/endpoint policy hash;
- idempotency-key hash;
- permit ID, issued time, expiry, and audience.

The bearer value is never persisted. Permit issuance keeps only a bounded in-memory response cache through permit expiry, keyed by authenticated principal plus idempotency-key hash. An exact same-key/request retry returns the same cached bearer and metadata; a changed request returns `IDEMPOTENCY_CONFLICT`. A lost response is recovered by that exact retry. Cache loss or permit expiry cannot reconstruct the bearer: the client requests a new permit with a new idempotency key, and the server performs full current revalidation. No operator reapproval is needed when authority and every semantic binding are unchanged.

A permit has only two durable outcomes in this MVP: **issued/uncommitted** or **committed/consumed**. Failure before event commit leaves it uncommitted and retryable while unexpired. The append atomically stores the non-secret permit ID, authority reference, canonical request hash, semantic-payload hash, idempotency-key hash, authenticated principal ID, resolved project, safe client-context fields, and policy hash in the event; that event is both the consumption record and receipt source. There is no durable consumed-without-commit state. If an event exists for the permit but the replay tuple differs, return `PERMIT_ALREADY_COMMITTED`. If implementation cannot prove this from the event record without a new database or schema, work stops for Jackie Chan review; no sidecar persistence is added ad hoc.

## 7. Server-side mutation algorithm

1. Authenticate the client credential, including its current revocation status. Missing, invalid, or revoked credentials return `401` before any receipt lookup or disclosure. Do not query current assignment, Registry ownership, Gate, dependency, owner, or policy state in this step.
2. Perform only static validation: parse/canonicalize the complete envelope, recompute the pinned hashes, require issuance/execution canonical equality, and validate permit structure, signature, audience, authenticated principal, permit ID, idempotency-key hash, and canonical-request hash. Defer permit expiry/consumption and every mutable assignment/Registry/Gate/dependency/owner/policy check until after step 3.
3. **Before checking current Story head, permit expiry/consumption, current policy, owner, dependencies, or authorization**, look up a committed event by authenticated principal, permit ID, idempotency-key hash, and canonical-request hash. An exact tuple returns `200 EXACT_REPLAY`; the server rebuilds the immutable receipt and performs zero new writes. The same idempotency key or permit with a different tuple returns the applicable `409`.
4. Only when no exact committed receipt exists, enter the first-execution path: validate fresh Registry host/agent ownership and current assignment, require an unexpired permit with no committed event, then acquire the single-writer service lock. The MVP runs one active writer; high availability is excluded.
5. Refresh the authoritative store and projection.
6. Resolve current owner/actor and dependency/policy snapshots server-side, and revalidate immediately before append that the authority reference remains valid and covers this exact operation, target, Story head, canonical typed payload, dependencies, owner, and policy.
7. Compare the exact target Story head. A changed target head returns `409 STORY_HEAD_MISMATCH`; it is never retried as harmless churn.
8. Run the existing Gate through the accepted VR-048 typed façade immediately before append.
9. Append with per-thread `expected_head`, atomically storing the non-secret permit-consumption/idempotency markers in the event.
10. If only the unrelated global domain head changed, refresh and retry internally up to three times while the Story head, owner, dependencies, policy, principal, authority, and canonical request remain identical. Exhaustion returns `503 GLOBAL_SERIALIZATION_RETRY_EXHAUSTED`; the permit remains uncommitted and the exact same request may retry while it is unexpired.
11. Return one atomic receipt derived from the stored event. A lost mutation response followed by an exact retry takes step 3 and creates no event.

Option A policy is explicit: credential revocation blocks every operation, including exact receipt recovery. For the same still-authenticated principal and exact static tuple, later assignment, Registry ownership, Gate, dependency, owner, or policy changes block a new mutation but do not block recovery of the already committed immutable safe receipt. Receipt recovery discloses no payload or secret and grants no mutation authority.

The immutable `receipt_core` has exactly these fields: `receipt_version`, `canonical_request_sha256`, `semantic_payload_sha256`, `idempotency_key_sha256`, `permit_id`, canonical `authority_ref`, `principal_id`, safe `host_id`, `agent_id`, and internal `session_id`, `resolved_project`, `thread_uid`, `event_uid`, `sequence`, `state`, `content_sha256`, `story_head_before`, `story_head_after`, `policy_sha256`, and ledger `recorded_at`. Define `receipt_core_sha256=SHA256(canonical_json(receipt_core))`, `receipt_id="vertical-receipt:" + receipt_core_sha256`, and `receipt_sha256=SHA256(canonical_json({receipt_id,receipt_core}))`. These values never change. `EVENT_CREATED` or `EXACT_REPLAY`, retry count, response time, and audit-only domain head are response metadata outside the immutable receipt. Exact replay returns byte-identical receipt core, ID, and hash.

Minimal S7 observability emits only `canonical_request_sha256`, `idempotency_key_sha256`, non-secret `permit_id`, `receipt_id` when committed, `retry_count`, `retry_outcome=COMMITTED|EXACT_REPLAY|RETRYABLE_503|REJECTED`, HTTP status, and machine code. Logs/metrics must not contain credentials or credential digests, permit bearer, raw idempotency key, raw provider locator, provider session ID, `typed_payload`, header/body/routing content, or authority content.

## 8. Approval reuse and mandatory stop rules

Approval is reusable without operator engagement only when the semantic decision is unchanged.

| Change observed after approval | Result |
|---|---|
| Unrelated global domain head changes; target Story head unchanged | Server refreshes and retries; no new approval |
| Lost permit-issuance response; same principal, issuance key, and canonical request while cache entry is unexpired | Return the same cached permit response; no approval |
| Issuance cache is lost or permit expires before commit while authority, target head, payload, owner, dependencies, policy, and principal remain identical | Full revalidation and a new permit/new idempotency key; no semantic operator reapproval |
| Lost mutation response or exact committed replay tuple | After current credential authentication/revocation and static tuple validation, receipt lookup occurs before assignment/Registry/Gate/dependency/owner/policy checks and returns the immutable stored receipt; no append or approval |
| Three unrelated-global-head retries are exhausted | Return retryable `503`; permit remains uncommitted and exact retry needs no operator reapproval while unexpired |
| Server-generated event ID, recorded time, receipt time, or audit-only domain head changes | No new approval |
| Target Story head or parent anchor changes | Stop; fresh semantic review/approval required |
| Semantic payload, action, lifecycle, target key/thread, criteria, scope, exclusion, or requested ordinary role changes | Stop; fresh approval required |
| Current owner/seat, authenticated principal, host/agent binding, dependency head/state, or policy hash changes | Stop; fresh authority resolution and approval required |
| Permit is replayed by another principal, idempotency key, payload, action, or target | Reject with zero writes |
| Authority reference is missing, ambiguous, revoked, or does not cover the exact action | Reject; operator/project-owner decision required |

This moves operator attention from transport/global-head churn to actual semantic changes. It does not create standing authority to invent work, change scope, accept delivery, or bypass Gate.

## 9. Transition from direct SMB writes

1. **Design gate.** GSP and Tony review this package; Helio issues the implementation game plan.
2. **Build and isolated proof.** Bruce implements against an isolated directory ledger and existing SQLite tests. No authoritative write occurs.
3. **Shadow deployment.** Francis packages and deploys the service on the approved non-Venom target. Direct client SMB writes remain available. Ronda proves authentication, permits, Gate behavior, idempotency, concurrency, receipts, and zero unintended writes.
4. **Authoritative canary.** After a Helio checkpoint and exact operator approval, one synthetic, preapproved canary transition is submitted through the endpoint while direct writes remain available. The ledger event and receipt must match exactly.
5. **Cutover decision.** After Story-level PASS evidence, Sensei accepts or rejects endpoint use and the direct-write prohibition.
6. **Direct-write prohibition.** Only after acceptance, Francis removes client write capability or remounts client access read-only. The endpoint service identity remains the only ledger writer. Read-only consumers remain unchanged.
7. **First consumer.** VR-072 may be submitted through the accepted endpoint using a newly validated permit bound to its still-current Story head and approved semantic plan. Any Story-head or semantic change stops for approval. This action is separately gated and is not authorized by this design.

Before cutover, existing direct-write actions continue to require their current exact permissions. After cutover, a client-side SMB write attempt must fail and endpoint mutations must continue to pass.

## 10. Feature-level acceptance boundary

The Feature passes only when both child Stories pass and the operator accepts cutover.

1. The service accepts approved typed openings/appends and applies the pinned request/payload schemas, project/authority single-source rules, authority coverage checks, and machine-readable HTTP/error matrix; every mismatched, unauthenticated, unauthorized, malformed, stale-Story, changed-policy, changed-owner, changed-dependency, or non-exact replay fixture produces its specified zero-write result.
2. Two concurrent requests to different Stories succeed without client global-head pins; two requests against one Story head produce exactly one append and one `409` or exact-replay response as applicable.
3. Lost issuance response, expiry/reissue, retry exhaustion, and lost mutation response follow the defined lifecycle. Credential authentication/revocation and static tuple validation precede every lookup; exact committed replay then precedes assignment/Registry/Gate/dependency/owner/policy checks and returns the stable receipt ID and hash with no event.
4. Receipt, safe correlation logs, event metadata, tests, and evidence contain no credential, credential digest, signing key, permit bearer, raw idempotency key, raw provider locator, provider session identifier, or typed payload/content.
5. The authoritative endpoint runs on a non-Venom target under Francis's administration. Eddie/Venom remains the operator-decision/receipt relay without endpoint implementation, deployment, administration, credential custody, or sustained Story execution. Logan/Wolverine facilitates the Stories without self-approval, sole independent review, or authority/credential acquisition from that role.
6. Direct client SMB writes are prohibited only after endpoint acceptance; afterward, at least two enrolled non-Venom client principals can mutate only through the endpoint and direct writes fail.
7. VR-072 remains unchanged until endpoint acceptance or separately approved old-path execution.

Criterion-level PASS/FAIL definitions and evidence fields are in the draft work-item package. No extra production-readiness evidence is implied.

## 11. Explicit exclusions

- generalized PKI, enterprise IAM, generalized RBAC, or a new fleet identity platform;
- UI, dashboard, notification, or human workflow redesign;
- changes to Revere broker, mailbox, relay, adapters, ACLs, credentials, or protocol;
- changes to Vertical lifecycle semantics, Gate authorization matrix, projection schema, ledger schema, or canonical hashing;
- multi-writer high availability, cross-region failover, public exposure, performance scaling, production SLOs, or unrelated hardening;
- arbitrary SQL or filesystem operations through the API;
- acceptance, closure, deployment, or scope changes without their existing semantic authority;
- assigning Venom/Eddie endpoint implementation, deployment, administration, credential custody, or sustained Story execution; allowing Wolverine/Logan to self-approve, serve as sole independent reviewer, or acquire endpoint authority/credentials merely through facilitation;
- executing VR-072 or any other consumer transaction under this design package.

### Parked future Feature candidate — Option C

- Proposed key: `VERTICAL-RECEIPT-RECOVERY-CAPABILITY-001`
- Proposed title: **Vertical Receipt Recovery Capability and Token Lifecycle**
- Proposed level/parent: Feature under `YNM-EPIC-011`
- Relationship: future follow-up related to, but not a dependency of, `VERTICAL-AUTHORIZED-MUTATION-ENDPOINT-MVP` or either MVP Story.
- Status: **FUTURE / PARKED / NOT ADMITTED FOR IMPLEMENTATION**.

Option C may later design a separate receipt-recovery capability and token lifecycle. This MVP defines no recovery credential, token, endpoint, grant, rotation, revocation, or custody model. No live Vertical event is created, no current criterion depends on it, and its absence cannot block the endpoint Feature or Stories.

## 12. Cost proportionality

Best-current implementation estimate:

- service, typed façade integration, permit verification, concurrency/idempotency, and tests: **16–24 engineering hours**;
- reference client and cutover controls: **6–10 engineering hours**;
- non-Venom packaging/deployment and bounded live proof: **4–6 engineering hours**;
- total implementation/delivery: **26–40 engineering hours**.

Best-current governance and review estimate:

- design and work-item package: **3–5 hours**;
- GSP and Tony focused reviews: **2–4 hours**;
- Ronda independent QA planning/reporting: **3–5 hours**;
- Helio checkpoints and operator decisions: **1–2 hours**;
- total governance/review: **9–16 hours**.

Governance remains below implementation. Actual elapsed effort and token/currency cost remain unknown until recorded. Optional hardening is parked.

## 13. Rejected alternative

Extending the VR-072 transition script to ignore global-head drift was rejected. It would fix one consumer while retaining direct SMB writers, per-command shell approval, duplicated authorization logic, and no reusable endpoint receipt. The central service is the smallest change that removes the repeated failure class without weakening Story-head or semantic approval.
