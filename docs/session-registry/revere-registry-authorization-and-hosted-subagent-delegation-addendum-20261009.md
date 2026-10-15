# Revere registry authorization and hosted subagent delegation — design addendum and draft Vertical changes

Status: **DRAFT ADDENDUM / GSP REWORK APPLIED / PENDING GSP RE-REVIEW AND OPERATOR VERTICAL AUTHORIZATION**  
Planning date: 2026-10-09  
Decision owner: Operator  
Document owner: Ip Man  
Required design peer review: GSP  
Review state: **REWORKED FOR GSP FINDINGS RHD-1, RHD-2, RRA-1, AND VH-1; NOT YET RE-REVIEWED**  

This addendum preserves the approved design bytes at
`C:\Workspace\TownSquare-MVP\docs\session-registry\session-registry-mvp-design-and-draft-work-items.md`
(SHA-256 `82e6fbcf4eb7073a26cfced4710369875929a32dc522158f22fc07f14fcc099d`). It proposes additive Vertical work only. It authorizes no live Vertical append or transition, implementation, broker or ACL change, credential operation, service restart, cross-host test, deployment, or external contact.

## Authoritative links and current placement

- Operator authorization bulletin:
  `C:\Workspace\TownSquare-MVP\docs\session-registry\BB-20261009-venom-001.000-POST__to-all__impact-project__from-venom__operator-authorizes-top-priority-revere-session-relay.txt`.
- `VR-20261009-ynm-038` / `YNM-EPIC-022` — **WORKING**, “Routable, auditable, bilateral agent sessions”; accountable owner `eddie-brock`; only the Registry prerequisite is currently admitted. Live head: `\\192.168.2.3\YNM\Projects\Vertical\ledger\VR-20261009-ynm-038.1-WORKING.txt`.
- `VR-20261009-ynm-042` / `REVERE-PHASE2-DURABLE-SESSION-RELAY` — **OPEN**, assigned `cable`, parked until `SESSION-REGISTRY-MVP` is accepted. Live head: `\\192.168.2.3\YNM\Projects\Vertical\ledger\VR-20261009-ynm-042.0-OPEN.txt`.
- `VR-20261009-ynm-043` / `REVERE-DURABLE-SESSION-MAILBOX` — **OPEN**, child of `VR-042`; its current authorization contract binds the session `agent_id` directly to the authenticated `Principal.agent_ids`. Live head: `\\192.168.2.3\YNM\Projects\Vertical\ledger\VR-20261009-ynm-043.0-OPEN.txt`.
- `VR-20261009-ynm-044` / `REVERE-CODEX-CLAUDE-BILATERAL-ADAPTERS` — **OPEN**, child of `VR-042`, dependent on the durable mailbox. Live head: `\\192.168.2.3\YNM\Projects\Vertical\ledger\VR-20261009-ynm-044.0-OPEN.txt`.
- Authoritative live ledger: `\\192.168.2.3\YNM\Projects\Vertical\ledger`.

The operator has clarified that portable agents are session-scoped subagents. They communicate through the hosted/root agent's authenticated Revere connection. They do not receive permanent Revere credentials and do not become ACL owners.

## Decision: two concerns, two dependency lanes

### A. Host-bound Registry-to-Revere authorization coverage

Place this as a new Feature under `YNM-EPIC-022`, with one bounded child Story. It is a sibling of `VR-042`, not its child and not dependent on `SESSION-REGISTRY-MVP`.

This lane reconciles a fresh active Agent Registry snapshot to Revere's existing host-principal ownership model. It covers Wolverine's canonical active identity now and the active host-bound identities whose host principals are not yet enrolled. It does not wait for durable session relay because the existing Revere authentication and ACL path already decides host-bound ownership.

For a principal already onboarded, reconciliation may add or correct an owned active host-bound `agent_id`, but must not rotate, replace, expose, redistribute, or otherwise change its permanent credential. Wolverine's reported `logan`/`wolverine` mismatch is resolved from the fresh Registry's canonical active identity, not from an assumed alias.

For a genuinely missing host principal, a future authorized issuance action generates the token on that host, retains it there, and provides only the required verifier/digest to the broker configuration path. The provisionally reported candidates are `banshee` (`banshee`), `cable` (`cable`, `nathan-summers`), `forge` (`forge`), and `jeangrey` (`jeangrey`, `phoenix`); a fresh Registry/ACL comparison must confirm each before action. Neither the token nor its verifier value belongs in design, Vertical, logs, evidence, or command output.

Portable identities and retired identities are excluded from ACL ownership. The provisional
`C:\Workspace\revere_reconcile_registry_acl.py` is input for independent review only. This addendum neither approves nor modifies it.

Reconciliation compares the full effective ownership relation, not only totals or proposed additions. The desired relation contains exactly one `(active host-bound identity, owning host principal)` pair per active host-bound Registry identity, zero active portable pairs, and zero retired/inactive pairs. The report calculates missing desired pairs, unexpected pairs, zero-owner host-bound identities, multi-owner host-bound identities, portable-owned identities, and retired/inactive-owned identities independently, so offsetting errors cannot cancel. Any retired or inactive identity retaining ACL ownership makes A1 `FAIL` without exception.

By default, apply is permitted only when A1 is `PASS` and both reviewed hash preconditions match. An exception artifact may document the exact retired/inactive stale-ownership count and reviewed plan hash and support a separate explicit operator override to proceed with that plan despite A1 `FAIL`; the artifact and override never change A1 to `PASS`, reduce its failure count, conceal the stale ownership, or permit acceptance of A1. Without that explicit override, apply does not run and the exact cleanup is parked for operator decision. Portable ownership has no override path. A pre-existing defect cannot be relabeled as outside the change to obtain `PASS`.

**Why this hierarchy:** a separate Feature keeps operational authorization coverage distinct from the durable mailbox data path, while one child Story avoids ceremony beyond the accepted work. Most importantly, Wolverine's safe host-bound correction is not incorrectly blocked behind Session Registry Phase 2.

Opening the Feature is insufficient while the authoritative `VR-038.1` head says `implementation_admission: REGISTRY-PREREQUISITE` and `implementation_authorized: registry-prerequisite-only`. After review and operator authorization, a new immutable `VR-038` event must explicitly supersede those fields with:

- `implementation_admission: REGISTRY-PREREQUISITE-AND-HOST-BOUND-AUTHORIZATION`
- `implementation_authorized: registry-prerequisite-and-host-bound-authorization-reconciliation`
- definition of done: “all admitted child Features are independently accepted.”

The event body must name only `SESSION-REGISTRY-MVP` and `REVERE-REGISTRY-AUTHORIZATION-COVERAGE` as admitted implementation lanes and must state that `REVERE-PHASE2-DURABLE-SESSION-RELAY` remains parked until `SESSION-REGISTRY-MVP` acceptance. That parent append does not itself open or start the proposed Feature/Story; their `OPEN` and later `WORKING` events remain separate authorized actions.

### B. Hosted portable-subagent delegation

Place this as one new child Story under `VR-20261009-ynm-042`, dependent on `REVERE-DURABLE-SESSION-MAILBOX` (`VR-043`). Do not create a second Feature. `VR-042` is already the approved home for durable session-addressed transport, and the mailbox supplies the durable send, receive, ack, ordering, replay, and Registry-session checks this Story extends.

The proposed Story is independent of the Codex/Claude proof in `VR-044`. Neither Story blocks the other unless the operator later changes the adapter proof to require portable-subagent coverage. The `VR-042` definition of done must be additively superseded from “both Revere child Stories” to “all admitted Revere child Stories” if this Story is opened.

## Minimal hosted-delegation contract

The existing direct path remains unchanged:

1. Revere authenticates the bearer token to immutable `Principal(name, agent_ids)`.
2. `_require_owned` proves the direct root `agent_id` is owned.
3. Revere freshly verifies the canonical root `session_uuid`, agent binding, eligible state, and revision through the redacted Session Registry record.

The delegated path adds a Revere-owned delegation record; it does not make the portable agent a principal or a Session Registry locator:

- `delegation_id`: Revere-generated opaque identifier.
- `root_session_uuid`: the canonical Session Registry UUID for the hosted/root agent.
- `portable_agent_id`: an active Registry identity classified as portable.
- `runtime_generation_id`: non-reused high-entropy identifier allocated by the trusted runtime for one adapter/runtime generation.
- `subagent_instance_id`: non-reused high-entropy identifier allocated by the trusted host runtime for one live child instance.
- `expires_at`: Revere-clock deadline for the live child binding.
- `state`: `ACTIVE` or `ENDED`.
- creation and end timestamps plus a sanitized terminal reason.

The authenticated host adapter is the trust boundary. It holds the Revere credential; the subagent and its prompt do not. On actual child creation, the trusted runtime creates exactly one immutable local mapping from that child's execution/IPC context to its returned opaque `delegation_id`. The adapter selects the delegation only by looking up the calling IPC context in this map. It never accepts `portable_agent_id`, `subagent_instance_id`, or `delegation_id` from a child prompt, payload, metadata field, or caller-controlled header. A missing or non-unique local mapping is rejected before a broker write.

On creation, Revere authenticates the root principal, proves ownership of the root session agent, freshly verifies the root session is eligible, verifies the logical agent is active and portable, and permanently enforces uniqueness of `(root_session_uuid, subagent_instance_id)` even after end. Revere receives the adapter-selected opaque `delegation_id`, validates that its stored record is `ACTIVE` and belongs to the authenticated `source_session_uuid` and current runtime generation, and derives every logical actor field from that record. The selector is adapter-selected from the trusted child-context binding; the logical identity is server-resolved and cannot be selected or overridden by the child.

A delegated message continues to use the root `source_session_uuid` and root `destination_session_uuid` for mailbox ownership. The trusted adapter supplies the opaque `source_delegation_id` selected from the caller's immutable IPC-context mapping; Revere validates that selector and resolves the logical `portable_agent_id`, root session, generation, and subagent instance from its stored record. An optional destination delegation is either taken from stored reply correlation or selected by the trusted destination-routing context and validated against the destination root. Reply correlation reverses the recorded source root/delegation pair. The destination host adapter receives under its authenticated root session and demultiplexes only to the matching live local instance.

For same-root siblings, each child has a distinct IPC context, immutable local mapping, high-entropy instance ID, and stored delegation. Source selection is therefore deterministic even when two live children use the same portable template: one calling context resolves to one active delegation or the call fails. A reply targets the stored source root/delegation pair, and the destination adapter resolves that delegation to exactly one live local IPC context. It never chooses a sibling by template name or “latest instance.”

### Delegation lifecycle and root-mailbox progress

Delegation create, renew, and end/revoke use the existing idempotency pattern: an exact replay returns the stored original result with zero additional writes; reuse of the idempotency key with changed input is rejected. Creation and each successful trusted-runtime renewal set `expires_at` to 120 seconds after Revere's current UTC. The adapter renews only while its bound child context is live and at intervals no greater than 60 seconds; the child cannot supply or extend its own deadline. Revere evaluates expiry on every delegation operation and before selecting the next root-mailbox message, so no background sweeper is required. Expiry, explicit end, and authenticated revoke all move the record to tombstoned `ENDED`; it cannot reactivate, and an ended `(root_session_uuid, subagent_instance_id)` is never reused.

Before a restarted adapter receives messages or creates children for a root session, it establishes a new `runtime_generation_id` and performs authenticated startup reconciliation. Revere atomically ends every still-active delegation for that root from an earlier generation. A child's explicit end or revoke, lease expiry, replacement of its runtime generation, or a terminal root-session transition ends the delegation. There is no permanent portable credential or portable ACL owner.

When a delegation ends, Revere atomically gives every queued or leased message addressed to that delegation the durable terminal state `UNDELIVERABLE_DELEGATE_ENDED`, records only sanitized reason metadata, and invalidates any active lease receipt. The message remains in the durable mailbox history and is never delivered to a replacement child, root handler, or sibling. This terminal state counts for contiguous-watermark progress in sequence order, so the next direct-root or sibling message can become the lowest nonterminal message without skipping or silently deleting the ended message. A later send/reply to the ended delegation, stale selector use, or late ack is rejected with no write or watermark change.

Send, receive, and ack retain the existing fresh root-session verification and principal binding. Delegation registration, renewal, delegated send, delivery, reply routing, end, and revoke fail closed for an unknown, expired, ended, mismatched, non-portable, cross-root, prior-generation, or terminal-root binding. Existing lease-receipt ownership remains bound to the authenticated principal and root destination session.

This is the minimum MVP trust contract. It deliberately does not add per-delegation mailboxes, PKI, signed portable-agent capabilities, general RBAC, cross-host spawn attestation, or permanent portable credentials. A compromised trusted host runtime is outside this Story's boundary, just as compromise of an existing host principal credential is outside the current mailbox contract. The required controls are deterministic child-context selection, server-resolved logical identity, tombstoned lifecycle, and terminal queue progress; they close reproduced MVP defects rather than add unrelated production hardening.

## Draft Vertical changes

These keys are proposals, not live ledger IDs. The intake owner must allocate live `VR-...` references and append immutable events through the normal parent-before-child lifecycle after review and operator authorization.

### DRAFT-RRA-F1 — Feature: Revere Registry authorization coverage

- `work_item_key`: `REVERE-REGISTRY-AUTHORIZATION-COVERAGE`
- `parent_work_item_key`: `YNM-EPIC-022` (`VR-20261009-ynm-038`)
- `accountable_owner`: `eddie-brock`
- `assigned_to`: `eddie-brock`
- `review_owner`: `gsp`
- `qa_owner`: `ronda-rousey`
- `operator_acceptance_owner`: `operator`
- `dependency_keys`: `[]`
- Goal: every active host-bound Registry identity can use Revere through exactly one authorized host principal, without placing portable identities in the ACL or changing credentials already onboarded.
- Definition of done: child Story passes every criterion; GSP records independent authorization/secret-handling review; Ronda records criterion-level PASS/FAIL; the operator accepts.
- Current evidence: `NOT RUN — DRAFT`.

### DRAFT-RRA-S1 — Story: Reconcile active host-bound Revere ownership

- `work_item_key`: `REVERE-HOST-BOUND-AUTHORIZATION-RECONCILIATION`
- `parent_work_item_key`: `REVERE-REGISTRY-AUTHORIZATION-COVERAGE`
- `accountable_owner`: `eddie-brock`
- `assigned_to`: `eddie-brock`, assisted by the relevant host operator; Wolverine retains exclusive control of Wolverine's local credential.
- `review_owner`: `gsp`
- `qa_owner`: `ronda-rousey`
- `operator_acceptance_owner`: `operator`
- `dependency_keys`: `[]`; a fresh reachable Agent Registry and reviewed current ACL are execution preconditions, not a Session Registry dependency.
- Scope: review the provisional reconciler; report and reconcile the complete effective ownership relation; generate a hash-bound dry-run; correct host-bound ownership including Wolverine; locally issue credentials only for confirmed missing host principals; validate authenticated host-bound send/receive and rejection of every non-owning principal.
- Current evidence: `NOT RUN — DRAFT`.

### DRAFT-RHD-S1 — Story: Relay hosted portable subagents through authenticated root sessions

- `work_item_key`: `REVERE-HOSTED-SUBAGENT-DELEGATION`
- `parent_work_item_key`: `REVERE-PHASE2-DURABLE-SESSION-RELAY` (`VR-20261009-ynm-042`)
- `accountable_owner`: `eddie-brock`
- `assigned_to`: `cable`
- `review_owner`: `gsp`
- `qa_owner`: `ronda-rousey`
- `operator_acceptance_owner`: `operator`
- `dependency_keys`: `[REVERE-DURABLE-SESSION-MAILBOX]`; `SESSION-REGISTRY-MVP` is inherited transitively through `VR-043`.
- Scope: Revere-owned root/session/portable/generation/instance delegation bindings; deterministic child-context selection; delegated envelope attribution; tombstoned create/end and startup reconciliation; terminal disposition for ended-delegate messages; reply routing; host-adapter demultiplexing; direct-path regression tests; synthetic bounded end-to-end proof.
- Current evidence: `NOT RUN — DRAFT`.

## GSP rework traceability

Review source:
`C:\Workspace\TownSquare-MVP\docs\session-registry\gsp-revere-registry-authorization-hosted-subagent-delegation-review-20261009.md`.

| Finding | Concern | Design resolution | Acceptance coverage |
|---|---|---|---|
| `RHD-1` | B | Immutable child IPC-context mapping selects one opaque delegation; Revere validates it against the authenticated root and resolves logical identity from the stored live record; same-root sibling selection never uses caller metadata or template name. | B1–B4 |
| `RHD-2` | B | High-entropy non-reused instance and runtime-generation IDs; bounded trusted-runtime-renewed delegation lease; idempotent tombstoned create/renew/end/revoke; startup reconciliation; durable `UNDELIVERABLE_DELEGATE_ENDED` disposition; lease invalidation; contiguous-watermark progress without rerouting or deletion. | B1, B3, B4, B6, B8 |
| `RRA-1` | A | Full desired-versus-effective ownership relation with independent missing, unexpected, zero-owner, multi-owner, portable-owner, and retired/inactive-owner counts; any retired/inactive ownership makes A1 fail, while a separately authorized override may permit apply without changing that result; non-owner matrix covers every other principal. | A1, A5, A6 |
| `VH-1` | A | Proposed immutable `VR-038` event explicitly supersedes both current implementation-admission fields while keeping `VR-042` parked and retaining separate child lifecycle actions. | A7 |

## Exact MVP acceptance criteria

Every criterion is reported only as `PASS` or `FAIL`. Evidence must contain only the fields named below. Secrets, verifier/digest values, clear provider locators, lease receipts, arbitrary message bodies, and real payload content are prohibited.

### A — host-bound authorization reconciliation

| ID | Trace | PASS | FAIL | Required evidence fields |
|---|---|---|---|---|
| A1 | Concern A / `RRA-1` | A fresh Registry snapshot and the complete post-plan ACL relation show one owner for every active host-bound identity, no missing or unexpected owner pair, zero active portable owners, and zero retired/inactive owners. | Any desired pair is missing; any unexpected, zero-owner, or multi-owner relation exists; any active portable remains owned; or any retired/inactive ownership is introduced or retained. A documented or operator-overridden stale entry still makes A1 `FAIL`. | `registry_snapshot_revision`, `registry_snapshot_sha256`, `active_host_bound_count`, `desired_owner_pair_count`, `effective_owner_pair_count`, `missing_owner_pair_count`, `unexpected_owner_pair_count`, `zero_owner_host_bound_count`, `multi_owner_host_bound_count`, `post_portable_acl_owner_count`, `post_retired_inactive_acl_owner_count`, `operator_override_present`, `operator_override_artifact_sha256`, `result` |
| A2 | Concern A / original Wolverine requirement | The fresh canonical Wolverine identity is owned by the Wolverine principal and its authenticated synthetic send and receive succeed. | The canonical identity is assumed from an alias, is owned elsewhere/more than once, or either operation fails. | `canonical_agent_id`, `principal_name`, `owner_count`, `send_result`, `receive_result`, `result` |
| A3 | Concern A / confirmed GSP boundary | Every already-onboarded principal retains its existing credential/verifier bytes; only ownership entries required by the reviewed plan change. | Any already-onboarded token or verifier is rotated, replaced, exposed, redistributed, or changed. | `already_onboarded_principal_count`, `credential_change_count`, `credential_exposure_count`, `result` |
| A4 | Concern A / confirmed GSP boundary | Every confirmed missing active host principal generates its credential on that host, retains the token there, enrolls only the verifier through the approved path, and authenticates successfully. | A token leaves its host, secret/verifier material appears in evidence, or authentication fails. | `missing_principal_count`, `locally_generated_count`, `verifier_enrolled_count`, `authentication_pass_count`, `secret_leak_count`, `result` |
| A5 | Concern A / `RRA-1` confirmed hash gate | The reviewed plan is bound to the Registry snapshot hash and current ACL hash; apply refuses either drift; apply with A1 `FAIL` occurs only under an explicit operator override artifact bound to that plan; post-change ownership equals the reviewed full relation. | An unreviewed snapshot/ACL is applied, apply proceeds while A1 is `FAIL` without a matching explicit operator override, or post-state differs. An override cannot change the recorded A1 result. | `registry_snapshot_sha256`, `pre_acl_sha256`, `reviewed_plan_sha256`, `a1_result`, `operator_override_present`, `operator_override_artifact_sha256`, `drift_refusal_result`, `post_plan_match`, `result` |
| A6 | Concern A / `RRA-1` | Each active host-bound identity completes one authenticated synthetic send and receive as its single A1 owner; every tested principal other than that owner is rejected for that identity. | Any owner flow fails, any non-owner case is omitted, or any non-owner succeeds. | `tested_identity_count`, `tested_principal_count`, `owner_send_pass_count`, `owner_receive_pass_count`, `expected_non_owner_case_count`, `non_owner_rejection_count`, `unexpected_authorized_principal_count`, `failure_count`, `result` |
| A7 | Concern A / `VH-1` | The latest authorized `VR-038` event explicitly admits `SESSION-REGISTRY-MVP` and `REVERE-REGISTRY-AUTHORIZATION-COVERAGE`, authorizes the bounded host-bound lane, and keeps `REVERE-PHASE2-DURABLE-SESSION-RELAY` parked; the child Story starts only under its own valid `WORKING` event. | The parent still says Registry-prerequisite-only, implicitly admits `VR-042`, or child work begins without a separate valid lifecycle event. | `parent_thread_id`, `parent_head_event`, `registry_lane_admitted`, `host_bound_lane_admitted`, `revere_phase2_parked`, `child_working_event_valid`, `result` |

### B — hosted portable-subagent delegation

| ID | Trace | PASS | FAIL | Required evidence fields |
|---|---|---|---|---|
| B1 | Concern B / `RHD-1`, `RHD-2` | A root-owned eligible session can idempotently register one live instance of an active portable identity with non-reused generation/instance IDs and the 120-second broker-time lease; exact replay adds no write, changed replay is rejected, trusted-runtime renewal succeeds, and logical fields resolve from the stored binding. | Ownership/lifecycle/classification fails, an ID is reused, replay changes state, a child controls lease duration, renewal succeeds without the bound live runtime context, or caller assertions determine logical identity. | `root_session_uuid`, `portable_agent_id`, `runtime_generation_id`, `subagent_instance_id`, `lease_expiry_seconds`, `original_write_count`, `exact_replay_write_count`, `changed_replay_rejection_count`, `trusted_renewal_result`, `untrusted_renewal_rejection_count`, `delegation_registration_result`, `result` |
| B2 | Concern B / `RHD-1` | A child-specific IPC context deterministically maps to one active delegation; delegated synthetic send, receive, reply, and ack preserve server-resolved logical identity/session/instance and reach only that instance. | Mapping is missing/non-unique, caller metadata selects identity, any operation fails, attribution changes, or delivery/reply reaches a different instance. | `source_root_session_uuid`, `source_portable_agent_id`, `source_subagent_instance_id`, `destination_root_session_uuid`, `destination_portable_agent_id`, `destination_subagent_instance_id`, `context_mapping_count`, `send_result`, `receive_result`, `reply_result`, `ack_result`, `wrong_instance_delivery_count`, `result` |
| B3 | Concern B / `RHD-1`, `RHD-2` | Unknown, expired, revoked/ended, mismatched, non-portable, cross-root, prior-generation, terminal-root, caller-overridden, and same-root sibling-override cases all fail closed; invalid rejected use changes no durable state. | Any invalid case succeeds, a sibling can select another sibling's delegation/logical identity, or rejected use changes durable state. | `case_count`, `rejection_count`, `same_root_instance_count`, `sibling_override_rejection_count`, `durable_state_change_count`, `result` |
| B4 | Concern B / `RHD-1`, `RHD-2` | Two same-template instances under one root and two instances under different roots exchange independently; each context selects exactly its own live binding and replies reach only the recorded source instance. | Attribution/delivery/reply crosses an instance or root boundary, or selector ambiguity exists. | `portable_agent_id`, `root_session_count`, `instance_count`, `same_root_instance_count`, `correct_delivery_count`, `cross_instance_delivery_count`, `cross_session_delivery_count`, `result` |
| B5 | Concern B / operator portable-agent clarification | Every active portable Registry identity completes a synthetic delegated send and receive through a hosted/root session without an ACL ownership entry or permanent credential. | Any active portable identity is untested, cannot communicate, gains ACL ownership, or receives a permanent credential. | `registry_snapshot_revision`, `active_portable_count`, `tested_portable_count`, `send_receive_pass_count`, `portable_acl_owner_count`, `portable_permanent_credential_count`, `result` |
| B6 | Concern B / `RHD-2` and confirmed compatibility boundary | Revere v1 and direct v2 mailbox compatibility tests pass; terminal delegated messages advance the existing root mailbox only in sequence and do not alter direct-message ordering. | Existing compatibility fails, a later message bypasses a nonterminal earlier message, or terminal handling changes direct ordering. | `v1_test_result`, `direct_v2_test_result`, `terminal_sequence_progress_result`, `direct_order_result`, `result` |
| B7 | Concern B / confirmed GSP redaction boundary | Captured logs, errors, traces, metrics, fixtures, and evidence contain no credential, verifier/digest, locator, lease receipt, or arbitrary message body. | Any prohibited value appears. | `captured_surface_count`, `prohibited_value_match_count`, `result` |
| B8 | Concern B / `RHD-2` | Queue to a live child, then separately test explicit end, authenticated revoke, lease expiry, and adapter restart before receive: each targeted message becomes durable `UNDELIVERABLE_DELEGATE_ENDED`, no old/replacement/sibling child receives it, stale selector/reply/ack attempts fail, and the next direct-root or sibling message becomes receivable in order. Exact terminal-action replay adds no write; changed replay is rejected. | Any stale payload is delivered or rerouted, an ended instance reactivates/reuses its ID, a stale operation succeeds, the terminal record is deleted, expiry fails to unblock on the next mailbox operation, or the root mailbox remains head-of-line blocked. | `scenario_count`, `terminal_delegated_message_count`, `wrong_instance_delivery_count`, `post_terminal_progress_result`, `stale_replay_rejection_count`, `exact_terminal_replay_write_count`, `changed_terminal_replay_rejection_count`, `result` |

## Explicit exclusions

- No permanent credentials or ACL ownership for portable agents.
- No change to already-onboarded principal credentials.
- No Session Registry parent/handoff graph or portable provider locator.
- No generalized RBAC, PKI, signed delegation framework, cross-host spawn attestation, portable-instance discovery service, autonomous spawning, or defense against a compromised trusted host runtime.
- No change to Revere v1 guarantees and no exactly-once claim.
- No production deployment, external-provider contact, live-message content, optional framework work, or self-acceptance.
- No cleanup or reversion of the reported out-of-scope `C:\Repo\Agentic` fast-forward or `C:\Workspace\.venom-refresh-20261009\venom.md` scratch file. They are not part of this design.

## Future actions requiring authorization

Each action below requires the appropriate Helio gateway and operator or lifecycle authorization. This addendum performs none of them.

1. Append or transition any live Vertical event, including the proposed new Feature/Stories, the `VR-038` definition-of-done plus implementation-admission/authorization supersession, and the `VR-042` definition-of-done update.
2. Approve, copy, or run the provisional reconciliation script against live Registry or ACL state.
3. Copy files to a broker/host, change `/etc/revere/acl.toml`, generate or enroll credentials/verifiers, distribute configuration, or alter file permissions.
4. Change Revere or adapter code, schema, service configuration, or delegation state.
5. Reload or restart `revere.service` or any host adapter/runtime.
6. Run live cross-host authentication, send/receive, negative-authorization, restart, replay, or delegation tests.
7. Deploy or contact any external provider session.

## Cost-proportional estimate

- Accepted functionality plus mandatory acceptance tests for A: **4–8 engineering hours**, assuming host access and Registry/ACL formats match the provisional evidence.
- Incremental accepted functionality plus mandatory acceptance tests for B: **12–20 engineering hours** after `VR-043` is accepted.
- Total incremental implementation/test estimate: **16–28 engineering hours**.
- This addendum, initial GSP review, one focused re-review, Vertical append preparation, Dojo checkpoints, and operator evidence review: **3–5 engineering hours**.
- Optional production hardening and generalized delegation architecture: **deferred; zero hours admitted**.
- Remote-access wait, existing adapter-hook availability, and actual elapsed/token costs are unknown. Delivery evidence must replace estimates with actuals when available.

Compared with the pre-review estimate, reproduced lifecycle/queue gaps add **4–6 implementation/test hours**, and the required rework/re-review adds approximately **1 governance hour**. A remains **4–8 hours**; no optional review or hardening was admitted.

Governance/review remains below the implementation estimate. If the trusted host runtime exposes no reliable child-instance hook, B becomes blocked for a narrowly scoped owner decision; permanent portable credentials are not the fallback.

## Required work order after approval

- Document and Vertical append preparation: Ip Man — maintain this additive decision and exact draft hierarchy; do not alter the approved base design bytes.
- Independent design re-review: GSP — verify traceable closure of `RHD-1`, `RHD-2`, `RRA-1`, and `VH-1`, including same-root selection, tombstoned lifecycle/queue progress, full effective ownership, and parent admission.
- Decide: Operator — accept/reject the addendum and authorize or decline the proposed immutable Vertical appends, including the `VR-038` admission/authorization supersession and `VR-042` definition-of-done supersession.
- Dojo gate: Helio Gracie — checkpoint after design review and at every implementation, peer-review, and QA handoff.
- Implement A: Eddie Brock — after valid live items admit work, review the provisional reconciler, prepare the hash-bound plan, assist Wolverine, and coordinate only the confirmed missing-host issuance actions. Wolverine and each host operator retain exclusive control of local credentials.
- Peer review A: GSP — verify exact ownership, no portable ACL entries, no changes to already-onboarded credentials, and no secret exposure.
- QA A: Ronda Rousey — report A1–A7 as PASS/FAIL using only their required fields.
- Implement B: Cable — only after `VR-043` acceptance and valid `WORKING` authority, implement the minimum Revere delegation binding, logical envelope, reply demultiplexing, and focused tests; preserve v1 and direct v2 behavior.
- Peer review B: GSP — verify stored-record-derived attribution, fail-closed invalid cases, session isolation, and absence of portable credentials/ownership.
- QA B: Ronda Rousey — report B1–B8 as PASS/FAIL using only their required fields.
- Watch for: canonical Wolverine alias ambiguity, stale Registry/ACL plans, offsetting ownership errors, verifier leakage, portable IDs entering `Principal.agent_ids`, caller-selected delegation identity, ambiguous same-root child mappings, stale runtime generations, ended-delegate head-of-line blocking, cross-instance/session reply delivery, scope duplication with `VR-043`/`VR-044`, and work beginning before the parent and child live items both admit it.

## Remaining decisions and unknowns

1. The operator must approve the proposed new live items, the `VR-038` definition-of-done and implementation-admission/authorization supersession, and the `VR-042` definition-of-done update; this document does not append them.
2. A fresh Registry snapshot must resolve Wolverine's canonical active identity and confirm the reported missing host principals before any plan is approved.
3. Implementation discovery must confirm that the trusted hosted runtime exposes reliable child-specific IPC context plus create, liveness-renewal, end/revoke, and runtime-generation hooks. If it does not, B is blocked for an operator decision on a narrowly scoped runtime integration; it does not fall back to portable credentials.
4. `VR-044` remains independent. Expanding its cross-vendor proof to require portable subagents would be a later operator scope decision, not an implied requirement here.
