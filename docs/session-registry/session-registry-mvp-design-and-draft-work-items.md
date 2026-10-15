# Session Registry MVP — design decision and draft Vertical work items

Status: **DRAFT / PENDING_OPERATOR_APPROVAL**  
Planning date: 2026-10-09  
Decision owner: Operator  
Document owner: Ip Man  
Required design peer review: GSP  
Review state: **APPROVAL-READY — independent GSP design review has no unresolved blocking finding**  

No tracker event, state transition, implementation, deployment, or external contact is authorized by this document.

## Problem and decision

The Agent Registry records stable agent identity, but it does not record the temporary provider sessions through which an agent can be located. Operators therefore cannot reliably answer which session currently represents an agent, which work authorized that session, or how a handoff changed over time.

Extend the existing Registry service with a private Session Registry. A session is a provider-specific locator attached to a registered agent; it is never identity, authentication, operator authority, or work authorization. The existing Agent Registry remains the identity source, and the referenced Vertical work item remains the authority source.

The MVP is limited to registration, lookup, heartbeat, termination, and append-only session history.

## Fit with the current architecture

- Preserve the Registry-owned SQLite boundary. `registry-migrate` remains the sole DDL writer.
- Reuse the existing authenticated, idempotent request pattern.
- Mutations atomically update a current-state projection, append immutable history, and enqueue a sanitized audit event in the Registry database. No cross-service transaction is introduced.
- Keep provider session IDs out of the Git-tracked Vertical ledger and the general TownSquare audit payload. Those systems receive only the Registry session UUID and non-sensitive lifecycle facts.
- Preserve current Agent Registry semantics: registration is a claimed identity/role/capability and grants no operator authority.
- Preserve Vertical semantics: metadata records ownership and relationships but grants no authority; work begins only after an approved item is opened through the normal lifecycle.

## Interfaces and data

### Current projection

Add a Registry-owned `sessions` projection with:

- `session_uuid`: Registry-generated canonical UUID and public reference.
- `agent_id`: registered Agent Registry identity.
- `provider` and `provider_session_id`: provider namespace and private locator; unique as a pair.
- `seat_or_host`, `runtime`, and `model`: optional routing context.
- `status`: `STARTING`, `ACTIVE`, `IDLE`, `ENDED`, or `LOST`.
- `started_utc`, `last_seen_utc`, and nullable `ended_utc`.
- nullable `work_ref`: a non-authoritative context link to a Vertical or TownSquare item; the Registry does not decide whether it authorizes action.
- `revision` and `updated_utc` for projection concurrency and freshness.

The exact DDL and constraints require peer review before implementation. A registration must reference an existing active agent. A session can be located without a `work_ref`, but that does not permit consequential work. `provider` is normalized to lowercase ASCII matching `[a-z0-9._-]{1,64}`. `provider_session_id` is an opaque, case-sensitive printable-ASCII value of 1–512 characters. The `(provider, provider_session_id)` pair is permanently unique, including after termination; an ended locator is not re-registered. Parent/handoff graph fields are deferred from the MVP.

### Immutable history

Add a `session_journal` using the Registry journal pattern: sequence, unique event ID, session UUID, agent ID, action, event body, and committed UTC. Guards reject update and delete. Actions are `register`, `heartbeat`, `terminate`, and `mark_lost`. Each mutation updates `sessions`, appends `session_journal`, and inserts a sanitized `audit_outbox` record in one transaction.

For every mutation, the existing idempotency store is authoritative. An exact replay with the same idempotency key returns the stored original status and response and performs **zero** additional projection revisions, journal inserts, or outbox inserts. Reusing the key with a different request is rejected. Registering an existing `(provider, provider_session_id)` with a different idempotency key returns a sanitized conflict and performs no writes.

Full provider session IDs remain in the private Registry projection and private session journal. Outbox and Vertical payloads contain the canonical `session_uuid`, provider name, status, agent ID, work reference, and timestamps, but never the clear provider session ID.

### HTTP surface

- `POST /v1/sessions` — register, idempotently.
- `GET /v1/sessions/{session_uuid}` — authenticated redacted lookup.
- `POST /v1/sessions/{session_uuid}/heartbeat` — update freshness/status and append history, idempotently.
- `POST /v1/sessions/{session_uuid}/terminate` — end or mark lost and append history, idempotently.
- `GET /v1/sessions/{session_uuid}/history` — authenticated redacted history.
- `GET /v1/sessions/{session_uuid}/provider-locator` — return the clear provider session ID only to the protected operator credential.

The MVP adds one narrowly scoped operator credential check for the clear locator endpoint; it does not add general RBAC. The operator issues an opaque bearer secret through the existing protected service-configuration path as `REGISTRY_OPERATOR_TOKEN`. For this endpoint, and only this endpoint, the decidable operator-principal predicate is: **ordinary Registry authentication succeeds AND `X-Registry-Operator-Token` is constant-time equal to the currently configured non-empty `REGISTRY_OPERATOR_TOKEN`**. No body field, agent record, work reference, query parameter, forwarded identity header, or self-asserted role contributes to that predicate. Validation occurs before any locator retrieval. The operator rotates or revokes the capability by replacing or removing the configured secret and restarting through the existing service configuration procedure; only the currently configured value is valid. Missing, invalid, rotated, revoked, self-asserted, or ordinary-auth-only requests receive the same `404` response as an unknown session, with `Cache-Control: no-store`, so the endpoint discloses neither locator nor record existence. Credential material is never logged, journaled, returned, or placed in idempotency/audit records. Default responses and errors must not echo full provider session IDs.

### Lifecycle contract

The service assigns all timestamps from its UTC clock; clients cannot supply them. Registration requires request field `initial_status` equal to `STARTING` or `ACTIVE`. Heartbeat requires request field `status` equal to `ACTIVE` or `IDLE`; the authenticated heartbeat caller is the sole MVP producer of `IDLE`. Termination requires `terminal_status` equal to `ENDED` or `LOST`.

| Operation | Allowed current state | Requested/new state | Timestamp effect |
| --- | --- | --- | --- |
| Register | no record | `STARTING` or `ACTIVE` | Set `started_utc = last_seen_utc`; `ended_utc = null`. |
| Heartbeat | `STARTING` | `ACTIVE` | Advance `last_seen_utc`; keep `started_utc`; `ended_utc = null`. |
| Heartbeat | `ACTIVE` | `ACTIVE` or `IDLE` | Advance `last_seen_utc`; keep `started_utc`; `ended_utc = null`. |
| Heartbeat | `IDLE` | `IDLE` or `ACTIVE` | Advance `last_seen_utc`; keep `started_utc`; `ended_utc = null`. |
| Terminate | `STARTING`, `ACTIVE`, or `IDLE` | request body `terminal_status = ENDED` or `LOST` | Set `ended_utc = last_seen_utc = committed UTC`; keep `started_utc`. |
| Any mutation | `ENDED` or `LOST` | any | Reject with sanitized `409`; perform no projection, journal, outbox, or idempotency-success write. |

Every service timestamp must be greater than or equal to the prior stored timestamp. A request outside this table is rejected atomically with no state/history/outbox change.

## Authority and privacy gates

1. A provider session ID is routing data only. Possessing it proves neither agent identity nor authorization.
2. A registered `agent_id` binds the session to a claimed agent record, not to operator authority.
3. `work_ref` is informative unless the referenced Vertical item is in a state that authorizes the requested action.
4. Consequential action still requires retrieve-before-act and the normal Vertical/operator gates.
5. Only the operator-only endpoint returns the clear provider locator. Request-body logs, application logs, exception traces, metrics/traces, idempotency records, audit delivery, errors, test fixtures/failure reports, and Git-tracked artifacts use the canonical session UUID and never a locator suffix. The sensitive response uses `Cache-Control: no-store`.
6. Corrections are new journal events; history is never edited.

## Trade-off and rejected alternative

This design adds a small private projection because current lookup must be fast while history remains immutable. The cost is maintaining projection/history consistency, controlled by the existing single-transaction Registry pattern.

Rejected: putting provider session IDs directly in the Vertical JSONL ledger. That would expose private locators in Git, confuse a locator with work authority, and force mutable presence data into a compatibility ledger that does not enforce native state.

## Draft Vertical hierarchy

These are proposal identifiers, not live tracker references. On approval, the intake owner must mint valid references and append `OPEN` events in parent-before-child order. Until then all items remain **DRAFT / PENDING_OPERATOR_APPROVAL**.

### DRAFT-SR-E1 — Epic: Routable, auditable, bilateral agent sessions

- `vertical_level`: `EPIC`
- `parent_ref`: none
- `depends_on_refs`: none
- `creation_owner`: `eddie-brock` (proposed; verify the exact registered `agent_id` before opening)
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: make provider sessions locatable, auditable, and able to exchange durable bilateral messages while preserving Agent Registry identity and Vertical authority boundaries.
- Definition of done: both approved Features are independently accepted; a registered agent has a private provider locator and durable lifecycle history; Revere relays acknowledged messages between addressed sessions without routine operator relay; no clear locator appears in Git-tracked Vertical records or general audit payloads.
- Evidence required: accepted child Feature references; privacy test showing no clear locator in redacted API, audit outbox, application logs, or Vertical evidence; bilateral Codex/Claude relay evidence; operator acceptance Decision.
- Current evidence: `NOT RUN — DRAFT`.

### DRAFT-SR-F1 — Feature: Session Registry MVP

- `vertical_level`: `FEATURE`
- `parent_ref`: `DRAFT-SR-E1`
- `depends_on_refs`: none
- `creation_owner`: `eddie-brock` (proposed; verify before opening)
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: add registration, lookup, heartbeat, termination, and append-only history to the Registry service.
- Scope: only the two Stories below. No discovery daemon, automated provider contact, deployment, production monitoring, generalized RBAC, retention automation, or cross-service transaction.
- Definition of done: both Stories pass their criteria; schema migration and service tests pass; independent review confirms locator/identity/authority separation; operator records acceptance.
- Evidence required: accepted child Story references; migration/test command and raw result; peer-review result; operator acceptance Decision.
- Current evidence: `NOT RUN — DRAFT`.

### DRAFT-SR-S1 — Story: Persist session lifecycle atomically

- `vertical_level`: `STORY`
- `parent_ref`: `DRAFT-SR-F1`
- `depends_on_refs`: none
- `creation_owner`: `eddie-brock` (proposed; verify before opening)
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: register, heartbeat, terminate, and mark lost sessions with an atomic current projection and immutable history.
- Scope: versioned Registry migration, `sessions`, `session_journal`, guards, existing idempotency integration, sanitized outbox events, and mutation endpoints.
- Acceptance criteria:
  1. Registration rejects an unknown or inactive `agent_id` and creates a Registry UUID for a valid active agent.
  2. An exact replay with the same idempotency key returns the original status/body and leaves projection revision plus journal/outbox row counts unchanged; a changed request with that key is rejected with no writes.
  3. A duplicate provider/session pair under a different idempotency key returns sanitized `409` and leaves projection revision plus journal/outbox row counts unchanged.
  4. An original register, heartbeat, or terminate mutation atomically updates the projection, appends exactly one immutable history event, and enqueues exactly one sanitized audit event.
  5. Update/delete attempts against session history fail.
  6. Every lifecycle transition and timestamp rule in the approved table passes; every unlisted transition and mutation after terminal status returns sanitized `409` with no projection, history, outbox, or idempotency-success change.
  7. Registry endpoints persist `work_ref` as non-authoritative metadata and expose no consequential-action interface or claim that the reference is open/authorizing. Retrieve-before-act authorization belongs to the action-owning service and requires its own approved work item.
- Evidence required: migration result; focused service tests for each criterion; database assertions for atomicity and no-update/no-delete guards; sanitized audit payload sample.
- Current evidence: `NOT RUN — DRAFT`.

### DRAFT-SR-S2 — Story: Provide protected lookup and history

- `vertical_level`: `STORY`
- `parent_ref`: `DRAFT-SR-F1`
- `depends_on_refs`: `DRAFT-SR-S1`
- `creation_owner`: `eddie-brock` (proposed; verify before opening)
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: find current session state and lifecycle history without leaking the provider locator.
- Scope: redacted current/history endpoints, operator-only provider-locator endpoint, response/error/log redaction, and focused tests.
- Acceptance criteria:
  1. Authenticated current lookup returns canonical session UUID, agent, provider, state, routing context, work reference, and timestamps without the clear provider session ID.
  2. Authenticated history returns ordered immutable lifecycle events without the clear provider session ID.
  3. The clear provider locator is returned only after ordinary Registry authentication plus the current operator token. Ordinary auth alone and missing, invalid, rotated, revoked, or self-asserted operator claims receive the same `404` body as an unknown session and no locator; negative tests cover body, query, agent metadata, work reference, and forwarded-header assertions.
  4. Request-body logs, application logs, exception traces, metrics/traces, idempotency records, API errors, audit outbox records, test fixtures/failure output, and Git-tracked evidence do not contain the clear provider session ID or credential. Tests use a generated sentinel locator, suppress it from command output, and assert its absence from every captured surface.
  5. The clear-locator response carries `Cache-Control: no-store`; default/current/history responses carry no clear locator or suffix.
  6. Lookup does not claim identity, authority, reachability, or successful contact.
- Evidence required: endpoint test matrix; negative authorization tests; automated leak scan over captured responses, logs, outbox rows, and evidence fixtures.
- Current evidence: `NOT RUN — DRAFT`.

### DRAFT-SR-F2 — Feature: Revere Phase 2 durable session relay (TOP PRIORITY)

- `vertical_level`: `FEATURE`
- `parent_ref`: `DRAFT-SR-E1`
- `depends_on_refs`: `DRAFT-SR-F1`
- `creation_owner`: `eddie-brock` (proposed; verify before opening)
- `fulfillment_owner`: `cable / sentinel-one` (proposed; verify the exact registered `agent_id` before `OPEN` or `WORKING`)
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Priority: **TOP PRIORITY**, immediately after the minimum Session Registry addressing dependency. The priority removes manual session-ID lookup, prompt/file relaying, and routine delivery monitoring; it does not bypass protected operator approval, override, scope, or acceptance.
- Goal: expand Revere, the existing vendor-neutral transport, with durable bilateral delivery addressed by canonical Registry session UUID.
- Scope: preserve Revere v1 authenticated directed Publish and long-lived Subscribe exactly as best-effort, in-memory, at-most-once interfaces. Add a backward-compatible Phase-2 durable API and Revere-owned store; do not silently change v1 guarantees. TownSquare/Vertical supplies `work_ref` authority context but is not the queue.
- Definition of done: both Stories below pass; Codex and Anthropic Claude adapters exchange and acknowledge messages in both directions, and reconnect/replay succeeds, without manual operator relay.
- Evidence required: accepted child Story references; v1 regression result; durable store/API test result; bilateral adapter transcript using synthetic content and canonical session UUIDs; reconnect/replay and dedup evidence; operator acceptance Decision.
- Current evidence: `NOT RUN — DRAFT`.

#### Revere Phase-2 contract

Revere owns a durable per-destination-session mailbox and sender outbox. Each message has:

- Registry `source_session_uuid` and `destination_session_uuid`.
- Revere-generated `message_id` and per-destination-session monotonic `delivery_sequence`.
- caller-supplied or generated `conversation_id`, with nullable `reply_to_message_id`.
- nullable `work_ref`, treated as non-authoritative metadata.
- content type and bounded payload.
- `created_utc`, delivery lease fields, attempt count, and state `QUEUED`, `LEASED`, or `ACKED`.

Phase-2 API:

- `POST /v2/session-messages` — authenticated, idempotent send.
- `GET /v2/sessions/{session_uuid}/messages` — authenticated resumable receive; leases the single lowest unacknowledged message and returns a one-time opaque lease receipt with `Cache-Control: no-store`.
- `POST /v2/sessions/{session_uuid}/messages/{message_id}/ack` — authenticated, idempotent acknowledgement requiring the lease receipt.

Delivery is **at least once**, never claimed exactly once. A send replay with the same idempotency key returns the original result without a second message.

Revere owns the contiguous acknowledged watermark; clients cannot choose or advance a cursor. The receive endpoint rejects caller-supplied `after_sequence`/cursor parameters and always selects the lowest unacknowledged destination sequence. Exactly one message may hold an active lease for a destination session. A lease lasts 60 seconds by Revere's UTC clock, cannot be renewed, and has no automatic maximum attempt count in the MVP; each redelivery increments `attempt_count`. Later messages remain withheld until the earlier message is acknowledged. After expiry, the same `message_id` becomes eligible for a new lease and receipt. Reconnect simply calls receive again and therefore resumes from the server-owned watermark without skipping.

Each lease produces a cryptographically random 256-bit opaque receipt. Revere stores only its hash together with message ID, exact destination session UUID, immutable authenticated `Principal`, lease time, and expiry. Ack must present the matching unexpired receipt while authenticated as the same immutable `Principal` and destination session; verification and the transition to `ACKED` are atomic. Missing, wrong, cross-session, cross-principal, or expired receipts are rejected with no state change. A successful ack replay with the same idempotency key returns the stored success with no additional write; other double-ack attempts return the existing `ACKED` state without changing it or reviving the lease. Every response containing a lease receipt sets `Cache-Control: no-store`; lease receipts are prohibited from request/application logs, errors, exception traces, metrics/traces, test fixtures/output, and all evidence artifacts.

Receivers deduplicate by `message_id`. The reference adapters keep a durable inbound record keyed by `(destination_session_uuid, message_id)`. In one adapter-local transaction they insert that key and the synthetic handler/transcript effect, then commit before ack. If the adapter crashes after the local commit but before ack, redelivery with a new lease receipt finds the durable key, skips the effect, and acknowledges. This makes the bounded synthetic adapter proof restart-safe; it does not turn Revere or arbitrary external side effects into exactly-once delivery.

Revere v2 reuses the existing authentication and ownership path exactly: `src/revere/auth.py` `Authenticator.authenticate(metadata) -> Principal` validates the single bearer token and returns immutable `Principal(name, agent_ids)` from the TOML ACL loaded by `load_acl()`; `BrokerServicer._authenticate(context)` invokes it; and `Broker._require_owned(...)` proves the exact sender/receiver `agent_id` is in `Principal.agent_ids`. `Principal.name` is audit identity, while the owned agent ID is the Registry binding key. No request body/header assertion other than the existing bearer credential, session UUID, `work_ref`, or payload field may create or extend ownership.

Revere then verifies the owned agent/session relationship and state through the Registry's redacted session record. Send requires source and destination sessions in `ACTIVE` or `IDLE`; `STARTING`, `ENDED`, and `LOST` are ineligible. Source must map to an agent ID owned by the authenticated sender. Receive and ack require the destination session in `ACTIVE` or `IDLE` and mapped to an agent ID owned by the authenticated receiver. This check does not reveal or use the clear provider locator.

There is no cross-service transaction. Every send, receive, and ack requires a fresh successful redacted Registry lookup with the expected session UUID, agent binding, eligible state, and revision; Revere records the observed revision for the decision. Unavailable, malformed, stale/unverifiable, mismatched, or incomplete Registry results fail closed. The failed operation creates or changes no message, lease, receipt hash, acknowledgement, watermark, or attempt count. A terminal transition after a successful check can race a send/lease, but every later receive and ack performs a fresh verification and rejects a terminal session without advancing delivery state. An adapter also retrieves current action authority before any consequential effect. A locator, agent registration, successful send, `work_ref`, or delivered message grants no authority to act.

Revere and adapter observability records only message/session/conversation IDs, state, byte size, and content type. Arbitrary payload bodies are excluded from application/request logs, errors, exception traces, metrics/traces, and test artifacts because a payload could itself contain a locator or credential. Approval evidence uses synthetic-safe bodies and their hashes.

### DRAFT-SR-S3 — Story: Add Revere durable session mailbox

- `vertical_level`: `STORY`
- `parent_ref`: `DRAFT-SR-F2`
- `depends_on_refs`: `DRAFT-SR-F1`
- `creation_owner`: `eddie-brock` (proposed; verify before opening)
- `fulfillment_owner`: `cable / sentinel-one` (proposed; verify before `OPEN` or `WORKING`)
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: provide durable, session-addressed send, receive, acknowledgement, redelivery, ordering, correlation, and replay without changing v1 behavior.
- Scope: Revere-owned durable schema/migration, Phase-2 API above, Registry binding lookup, idempotent send/ack, delivery leases, per-session ordering, conversation/reply fields, bounded payload validation, and v1 regression tests.
- Acceptance criteria:
  1. Revere v1 Publish/Subscribe behavior and compatibility tests remain unchanged and best-effort/at-most-once.
  2. Revere v2 uses existing `Authenticator.authenticate` → immutable `Principal.agent_ids` → `Broker._require_owned` checks before Registry binding. Every send, receive, and ack performs a fresh Registry verification of UUID, agent, state, and revision; unavailable, malformed, stale/unverifiable, mismatched, or incomplete results fail closed with no message, lease, ack, watermark, or attempt-count change. A valid owned source sends only when both sessions are `ACTIVE` or `IDLE`; receive and ack also require an `ACTIVE` or `IDLE` destination. Self-asserted ownership, source/receive-session mismatch, `STARTING`/unknown/terminal sessions, and terminal-state races are rejected without revealing a provider locator.
  3. Original send persists one message; exact idempotent replay returns the original result and writes no second message; changed replay is rejected.
  4. Receive always leases the lowest unacknowledged destination sequence for 60 seconds, allows one active lease per destination, rejects any client cursor, and withholds later messages. Expiry redelivers the same `message_id` with a new receipt; reconnect resumes from the server-owned contiguous acknowledged watermark.
  5. Receive returns a 256-bit opaque lease receipt whose hash is bound to message, destination session, immutable authenticated `Principal`, and expiry. Ack succeeds atomically only with a matching unexpired receipt from the same `Principal` and session; wrong/missing/stale/cross-session/cross-principal receipts make no change; an exact idempotent ack replay makes no second write. Receipt-bearing responses set `Cache-Control: no-store`, and leak tests cover headers plus every prohibited observability/evidence surface.
  6. Duplicate delivery is possible and documented. The reference adapter durably records `(destination_session_uuid, message_id)` and its synthetic effect in one local transaction before ack, then skips the effect on redelivery. No evidence or API claims transport or arbitrary effects are exactly once.
  7. `message_id`, `conversation_id`, `reply_to_message_id`, and `work_ref` persist and round-trip; `work_ref` is explicitly non-authoritative and TownSquare/Vertical is not used as queue storage.
  8. Clear provider locators, Registry operator credentials, and arbitrary message bodies never enter Revere logs, errors, exception traces, metrics/traces, or test artifacts; evidence uses synthetic-safe bodies/hashes.
- Evidence required: schema/migration result; focused API/store test matrix; DB counts for idempotent send/ack; lease-expiry/reconnect trace using synthetic messages; v1 regression output; generated-sentinel leak scan.
- Current evidence: `NOT RUN — DRAFT`.

### DRAFT-SR-S4 — Story: Prove Codex ↔ Anthropic Claude bilateral adapters

- `vertical_level`: `STORY`
- `parent_ref`: `DRAFT-SR-F2`
- `depends_on_refs`: `DRAFT-SR-S3`
- `creation_owner`: `eddie-brock` (proposed; verify before opening)
- `fulfillment_owner`: `cable / sentinel-one` (proposed; verify before `OPEN` or `WORKING`)
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: remove file-drop/manual-prompt relay by connecting one Codex session and one Anthropic Claude session through Revere Phase 2.
- Scope: two bounded vendor adapters or turn-safe inbox helpers using existing authenticated Revere identities, canonical session UUID addressing, receive/dedup/ack checkpoints, conversation/reply correlation, and a synthetic local end-to-end proof. No autonomous consequential action and no contact outside the approved test environment.
- Acceptance criteria:
  1. The Codex session sends a synthetic message to the Claude session; Claude receives it once at the adapter boundary, replies with matching conversation/reply correlation, and both deliveries are acknowledged.
  2. The Claude session initiates the reverse exchange under a new conversation; Codex receives, replies, and both deliveries are acknowledged.
  3. After either adapter restarts after durably recording the synthetic effect but before ack, replay presents the same `message_id` with a new lease receipt; the durable adapter ledger suppresses the duplicate effect, acknowledges, and continues in per-session order.
  4. All three flows complete without manual operator lookup, prompt relay, file drop, or delivery monitoring.
  5. Adapter receipt does not execute consequential work until the receiving action owner independently retrieves an authorizing Vertical state; operator approval, override, scope, and acceptance remain protected.
  6. The proof records canonical session UUIDs and synthetic message IDs only; it does not expose provider locators, credentials, or real message content.
- Evidence required: synthetic bidirectional transcript, ack/state rows, forced-disconnect reconnect/replay trace, dedup assertion, manual-intervention count of zero, and leak scan.
- Current evidence: `NOT RUN — DRAFT`.

## Cost-proportional MVP estimate

- Session Registry accepted-functionality implementation: **8–12 engineering hours** (migration, service/API work, and mandatory tests).
- Revere Phase-2 relay accepted-functionality implementation: **14–22 engineering hours** (durable store/API, v1 regression protection, two bounded adapters, and mandatory end-to-end tests).
- Total accepted-functionality implementation: **22–34 engineering hours**.
- Governance/review/acceptance evidence: **4–6 engineering hours** (design, one focused security/authority review cycle, and operator evidence review).
- Optional follow-up work: **0 hours authorized**. Automatic discovery, production presence monitoring, retention automation, multi-node queueing, dead-letter operations, additional vendor adapters, deployment, and generalized RBAC are parked.

Governance remains below the current implementation estimate. Actual elapsed time must replace these estimates in delivery evidence; unknown costs remain marked unknown.

## Independent review result

GSP completed the independent security/authority design review. Findings were raised and corrected across four passes: operator-locator authorization, testable authority boundaries, mutation replay/transition rules, relay lease ownership, server-owned ordering, restart-safe adapter deduplication, lifecycle eligibility, receipt cache protection, and fail-closed Registry verification. Final result: **APPROVAL-READY with no unresolved BLOCKING finding**. This clears only the design gate; it does not open work, authorize `WORKING`, approve implementation output, deploy, contact external systems, or replace operator decision authority.

## Decision requested from the operator

Approve or reject the following as one bounded package:

1. Adopt the Session Registry addressing design, the Revere Phase-2 transport placement, and the authority/privacy boundaries above.
2. Confirm DRAFT-SR-F2 as top priority, with DRAFT-SR-F1 limited to its prerequisite addressing capability.
3. Authorize the intake owner to mint live Vertical references and append `OPEN` events for the Epic, both Features, and their Stories in parent-before-child/dependency order.
4. Approve the proposed owners, subject to resolving their exact registered `agent_id` values before opening.
5. Agents may implement only after GSP records a follow-up independent design review with no unresolved blocking finding, unless the operator records an explicit Decision overriding named findings. This review gate constrains agents, never the operator's authority to accept, reject, or override.

Approval does not authorize deployment, external contact, or a transition to `WORKING`; those remain separate lifecycle actions.

## Work order after approval

**DOCUMENT · DISCUSS · DECIDE gate**

- Document: Ip Man — this decision, interfaces, data ownership, lifecycle, privacy boundary, and draft work hierarchy.
- Independent design review: GSP — challenge clear-locator access, redaction, audit payloads, authority separation, and whether the criteria are testable. Record concerns in their own words.
- Decide: Operator — approve/reject the design, item hierarchy, and proposed ownership. No implementation before this gate passes.

**WORK ORDER**

- Implement (Registry): Bruce Lee — after approval and valid assigned `WORKING` Stories exist, deliver only the minimum DRAFT-SR-S1/S2 Registry addressing prerequisite and focused tests; do not deploy or contact provider sessions.
- Implement (Revere): Cable / Sentinel One — after the Registry dependency is accepted and valid assigned `WORKING` Stories exist, deliver top-priority DRAFT-SR-S3/S4 on an isolated branch; preserve v1 behavior; do not deploy, self-review, self-accept, contact unapproved external sessions, or add optional framework features. Verify Cable's exact registered `agent_id` before `OPEN` or `WORKING`; this proposal is not dispatch authorization.
- Peer review: GSP — verify the implementation matches the approved sensitive-data, authenticated-session binding, delivery, and authority boundaries and that no clear locator escapes protected Registry storage/API.
- QA: Ronda Rousey — run Registry migration/idempotency/atomicity/transition/authorization/redaction tests; Revere v1 regressions and Phase-2 send/receive/ack/redelivery/order/dedup tests; and the bounded Codex↔Claude reconnect proof. Report each approved acceptance criterion as `PASS` or `FAIL` with only its required evidence.
- Watch for: Registry schema ownership, accidental full-locator leakage to Revere/audit/JSONL/logs, heartbeat and redelivery volume, invalid principal/session binding, v1 compatibility, false exactly-once claims, and any attempt to treat lookup/message delivery as identity or authority. Escalate schema-specific concerns to Jackie Chan; do not expand scope without a separately approved work item.
