# Revere Registry authorization and hosted-subagent delegation — independent security/design review

**Review date:** 2026-10-09  
**Reviewer:** GSP  
**Disposition:** **REWORK — four blocking corrections**  
**Checkpoint readiness:** **Ready for a Dojo REWORK checkpoint; not approval-ready and not ready for live Vertical append preparation.**  
**Scope:** Design and proposed Vertical changes only. No application code, provisional reconciler, live ledger, broker state, ACL, credential, service, deployment, or external system was changed or tested.

## Reviewed evidence

| Source | SHA-256 |
| --- | --- |
| `revere-registry-authorization-and-hosted-subagent-delegation-addendum-20261009.md` | `38d5035eb1d15c71bd5c94819d3e3963de3394489abc02634c0ecf7574b60653` |
| `session-registry-mvp-design-and-draft-work-items.md` | `82e6fbcf4eb7073a26cfced4710369875929a32dc522158f22fc07f14fcc099d` |
| `BB-20261009-venom-001.000-POST__to-all__impact-project__from-venom__operator-authorizes-top-priority-revere-session-relay.txt` | `27b8377e97827622276d5bd624a14477d26bf3477dbd95c4c7861f839e269183` |
| `VR-20261009-ynm-038.1-WORKING.txt` | `e7d9525367c0fd1e374ad0018627f26cd7792d99315db01c4726a04330d1da23` |
| `VR-20261009-ynm-042.0-OPEN.txt` | `2054ac288b66758ebeaa8e29f447d3eca0793f085c95f33ffb9da37682d8f96c` |
| `VR-20261009-ynm-043.0-OPEN.txt` | `d76201903fa4f00674c1906b26a9439d78ca777c9c567e85f41a3457aa35fefc` |
| `VR-20261009-ynm-044.0-OPEN.txt` | `a3eff85dd387c003a15c323a7051f2d8396797cb5a70ff7e283f64109406804a` |

The operator's binding clarification was applied as an authoritative review condition: a portable agent is a session-scoped subagent using its hosted/root agent's authenticated Revere connection; it receives neither a permanent Revere credential nor ACL ownership. Every active registered identity must have either host-bound authenticated access or delegated portable access through its host.

## Threat model

**Protected assets:** permanent Revere credentials and verifier material; the integrity of `Principal.agent_ids`; canonical root-session ownership; logical portable-agent and live-instance attribution; message/reply destination integrity; lease and watermark integrity; and availability of a root mailbox to its active root and sibling subagents.

**Adversaries and failure sources:** an untrusted portable prompt or payload attempting to claim another identity; one sibling subagent attempting to act as another; a non-owning authenticated principal; replayed create/end/send requests; stale delegation state after a runtime crash or restart; Registry/ACL drift between review and apply; and an operator or script accidentally creating duplicate ACL ownership. A compromised trusted host runtime or stolen host credential remains outside the bounded Story, as the addendum states.

**Trust boundaries:** Revere authenticates the host-bound transport principal. The trusted host runtime binds a real child execution context to one Revere delegation. Revere, not the portable caller, resolves the logical actor from that stored binding. The Agent Registry classifies stable identity; the Session Registry proves the canonical root session and eligible lifecycle state; Vertical remains the action-authority source.

## Review result by requested focus

| Focus | Result | Basis |
| --- | --- | --- |
| Authenticated transport principal versus portable logical actor | **PASS in design intent** | The portable actor is not a `Principal`, credential holder, ACL owner, or Session Registry locator. Root ownership remains the transport authorization. Finding RHD-1 is required to make source selection implementable without sibling impersonation. |
| Trusted create/end binding, server resolution, replay/expiry, reply demultiplexing, concurrent isolation | **FAIL** | Create-time validation is present, but the source-selector trust path and end/restart/queued-message semantics are incomplete. See RHD-1 and RHD-2. |
| Eddie/Wolverine and sibling anti-impersonation | **FAIL** | Wolverine's canonical host-bound check is sound in principle. Same-root sibling source impersonation has no decidable adapter-to-Revere binding or exact negative test. See RHD-1. |
| ACL reconciliation, secret protection, duplicate ownership, hash drift, restart/rollback boundary | **FAIL narrowly** | Credential preservation, local issuance, hash-bound drift refusal, and separate restart authorization are correctly bounded. The post-state portable/retired ownership invariant and duplicate/unowned evidence are not exact. See RRA-1. No additional rollback ceremony is required for this MVP; A5/A6 already prevent acceptance of a bad activation. |
| Vertical hierarchy and dependencies | **FAIL narrowly** | Delegation correctly belongs under `VR-042`, depends on `VR-043`, and remains independent of `VR-044`. The host-bound lane is structurally independent, but the authoritative `VR-038` head still admits only the Registry prerequisite. See VH-1. |
| MVP proportionality | **PASS** | The four corrections close reproducible identity, lifecycle/availability, ACL-invariant, and live-authority defects. PKI, general RBAC, cross-host attestation, permanent portable credentials, and production hardening remain out of scope. |
| Acceptance testability and evidence minimization | **FAIL narrowly** | Most criteria are observable and use aggregate, non-secret evidence. RHD-1, RHD-2, and RRA-1 need the exact additions below; no raw IDs, tokens, verifiers, locators, receipts, or bodies need be added. |

## Blocking findings

### RHD-1 — The design cannot presently distinguish a same-root sibling's source selection from an authorized one

**Severity:** **HIGH / BLOCKING**  
**Likelihood:** Plausible and deterministic if a portable request can carry a delegation selector.  
**Affected sections/criteria:** Addendum lines 66–72; B1–B4, especially B3 `caller-overridden` and B4 concurrent isolation.

**Reproducible scenario:**

1. Root session `R` hosts live child instances `I1` and `I2`, with delegations `D1` and `D2`.
2. Both children ultimately send through the same authenticated root principal and root session.
3. Revere cannot infer `D1` versus `D2` from that shared principal/session alone. Some trusted input must select a delegation.
4. If `I1` can place `D2` or `I2`'s logical identity in a payload/header that the adapter forwards, Revere can validate that `D2` belongs to `R` and attribute `I1`'s message to `I2`.
5. The current prose says `source_delegation_id` is server-resolved and rejects caller override, but it does not define the trusted selector or a same-root sibling negative test. B4 tests only the same portable identity across different root sessions.

**Minimal correction:**

- State that the trusted runtime binds each child execution/IPC context to exactly one immutable local delegation handle at successful child creation. The adapter chooses the opaque `delegation_id` from that binding; it never accepts `portable_agent_id`, `subagent_instance_id`, or `delegation_id` from the child's prompt, message body, metadata, or caller-controlled header.
- State that Revere receives the adapter-selected opaque ID, validates that its stored record is `ACTIVE` and belongs to the authenticated `source_session_uuid`, and resolves all logical actor fields from the stored record. Calling the logical identity “server-resolved” is correct; calling the selector server-resolved is not unless a separate authenticated child channel is specified.
- Add one exact same-root sibling override case to B3 and require zero durable change. Extend B4 to cover two simultaneous instances under the same root as well as two roots. Aggregate evidence is sufficient: add only `same_root_instance_count`, `sibling_override_rejection_count`, and `cross_instance_delivery_count` (expected zero); do not record delegation IDs or payloads.

**Concrete alternative:** If the runtime already provides unforgeable per-child channels, Revere need not add portable capabilities. The adapter can maintain an in-memory/durable channel-to-delegation map and pass only the mapped opaque ID. This is smaller than PKI or signed child tokens and stays inside the accepted trust boundary.

### RHD-2 — Delegation end/restart semantics can either misdeliver to a replacement child or permanently block the root mailbox

**Severity:** **HIGH / BLOCKING**  
**Likelihood:** Plausible on an ordinary child exit, adapter crash, or restart; the head-of-line outcome follows deterministically from the two written contracts.  
**Affected sections/criteria:** Addendum lines 59–70 and 176/196; B2–B4 and B6. Base design lines 206, 208, 210, 214–216; live `VR-043` definition of done for lowest-unacknowledged ordering and fail-closed lifecycle verification.

**Reproducible scenario A — stale instance reuse:**

1. A child is registered as `ACTIVE`; the host runtime crashes before sending `end` while the root Session Registry record remains `ACTIVE` or `IDLE`.
2. The delegation has no runtime generation, expiry, startup reconciliation rule, or permanent non-reuse rule for the local instance ID.
3. On restart, a new child can reuse the same local instance identifier or the adapter can encounter the still-active record.
4. A queued message or reply for the old instance can be demultiplexed to the replacement, or registration can remain blocked by the stale uniqueness record.

**Reproducible scenario B — permanent head-of-line block:**

1. A sender queues delegated message `M` while destination delegation `D` is active.
2. `D` ends before `M` is received.
3. The addendum requires delivery through an ended binding to fail closed without message, lease, ack, watermark, or attempt-count change (B3).
4. The approved base mailbox always selects the lowest unacknowledged destination sequence and withholds all later messages.
5. `M` therefore remains the lowest unacknowledged item forever and blocks direct-root and sibling traffic in the same root mailbox.

**Minimal correction:**

- Make delegation creation and end idempotent and tombstoned: an exact replay adds no write; a changed replay is rejected; an ended `(root_session_uuid, subagent_instance_id)` can never reactivate.
- Require a non-reused, high-entropy child instance ID and a host-runtime generation ID, or an equivalent trusted-runtime epoch. Before a restarted adapter receives or creates children for the root, it must end stale delegations from the prior generation. State explicitly that validity ends on child end, runtime-generation replacement, or root terminal state; no permanent portable credential is introduced.
- Define one terminal disposition for messages already queued or leased to a delegation that ends. The smallest compatible option is a Revere-owned terminal `CANCELLED`/`UNDELIVERABLE` state that is applied by the authorized end/root-terminal transition, invalidates any lease, never dispatches the payload to another child, and counts as terminal for contiguous-watermark progress. Rejected later use of the ended binding still makes no state change.
- Add an acceptance case covering: queue to live child → child ends (and separately adapter restart) before receive → no child receives the payload → stale reply/selector fails → the next direct-root or sibling message is receivable in order. Evidence can remain aggregate: `terminal_delegated_message_count`, `wrong_instance_delivery_count`, `post_terminal_progress_result`, `stale_replay_rejection_count`, and `result`.

**Concrete alternative:** A per-delegation mailbox would also remove cross-sibling head-of-line blocking, but it is a larger change to the approved per-root-session mailbox. A terminal message disposition plus runtime generation is the proportional MVP correction.

### RRA-1 — A1 can pass while pre-existing portable/retired ACL ownership or offsetting owner-count errors remain

**Severity:** **HIGH / BLOCKING**  
**Likelihood:** Plausible because this lane is explicitly reconciling an existing ACL with reported identity drift.  
**Affected sections/criteria:** Addendum lines 32–41 and 88–102; A1, A5, A6; B5.

**Reproducible scenario:**

1. The current ACL already owns an identity that the fresh Registry classifies as portable, or retains a retired identity.
2. A reviewed plan adds nothing for that identity and leaves the existing entry unchanged.
3. A1 currently forbids portable/retired identities only when they are “ACL-owned by this change,” and its FAIL text only catches one being added. The plan can therefore claim PASS while an active portable identity remains an ACL-owned sender, contrary to the binding operator clarification.
4. Separately, `active_host_bound_count` and the ambiguous `unique_owner_count` do not independently expose zero-owner and multi-owner defects. Offsetting errors can be hidden by an aggregate total, and A6 can choose one unrelated non-owner without proving that every other principal is rejected.

**Minimal correction:**

- Make A1 a post-state invariant: every active host-bound identity has exactly one owner, and **zero** active portable or retired identities are ACL-owned after the plan; FAIL if any remain, are added, or are duplicated.
- Replace or define the ambiguous ownership count with aggregate exception counts: `zero_owner_host_bound_count`, `multi_owner_host_bound_count`, `post_portable_acl_owner_count`, and `post_retired_acl_owner_count`, all required to be zero. Keep the existing snapshot/hash and total counts. No identity list or secret material is needed.
- Define A6's non-owner assertion as rejection of every tested principal other than the single A1 owner for that identity, or provide an aggregate `unexpected_authorized_principal_count` required to be zero.
- Keep A5's two hash preconditions, post-plan equality, and no-secret evidence rules unchanged; they are appropriately narrow.

**Concrete alternative:** If removal of a stale portable/retired ACL entry is not authorized in the same apply, A1 must report `FAIL` and park that exact cleanup for operator decision. It must not pass by labeling the stale entry pre-existing.

### VH-1 — The proposed parent update does not actually unblock the host-bound lane in the authoritative ledger

**Severity:** **MEDIUM / BLOCKING**  
**Likelihood:** Certain if append preparation follows only the addendum's stated `VR-038` definition-of-done supersession.  
**Affected sections/criteria:** Addendum lines 30–41, 76–103, 159, 194; live `VR-038.1-WORKING` fields `implementation_admission: REGISTRY-PREREQUISITE` and `implementation_authorized: registry-prerequisite-only`.

**Reproducible scenario:**

1. Intake opens the proposed sibling Feature and child Story and updates `VR-038` only from “both approved Features” to “all admitted child Features,” as directed by the addendum.
2. The latest authoritative `VR-038` head still authorizes implementation only for the Registry prerequisite.
3. The new Story has no dependency key, but moving or acting on it would conflict with its parent's current implementation-admission boundary. Wolverine remains blocked in practice despite the intended independent lane.

**Minimal correction:**

- Include in the proposed immutable `VR-038` supersession an explicit admission/authorization update that admits the bounded host-bound authorization-reconciliation lane alongside the current Registry prerequisite, while leaving `VR-042` parked until `SESSION-REGISTRY-MVP` acceptance.
- Keep the new Feature/Story parentage and empty dependency list. Do not add a dependency on `VR-042`, `VR-043`, or Session Registry.
- The append and any later `WORKING` transition remain separate authorized actions; this edit only makes the intended parent boundary internally consistent.

**Concrete alternative:** If the operator wants the host-bound correction open but not admitted yet, retain the current parent boundary and state that Wolverine remains parked. That would be consistent, but it would not satisfy the addendum's stated “covers Wolverine now” outcome.

## Confirmed passes and scope boundaries

- The addendum correctly keeps permanent credentials with host principals and excludes portable identities from credentials and `Principal.agent_ids` in design intent.
- Existing onboarded credentials are preserved; confirmed missing principals generate tokens locally and expose neither token nor verifier in evidence or command output.
- A5 correctly binds apply to both Registry snapshot and pre-ACL hashes and requires post-state equality. A separate restart authorization is correctly retained. Failed activation is caught by A6, so a production rollback runbook is not an additional MVP deliverable.
- Delegation placement under `VR-042` with dependency on `VR-043` is correct. The dependency on Session Registry is inherited through `VR-043`. The new Story need not depend on `VR-044`, and `VR-044` need not wait for it.
- B5 correctly expresses the fleet-wide portable coverage requirement without granting portable ACL ownership or credentials. B6 and B7 preserve direct v1/v2 behavior and secret/locator/receipt/body redaction.
- The exclusions of PKI, general RBAC, cross-host spawn attestation, portable discovery, autonomous spawning, exactly-once claims, production deployment, and compromised-runtime defense are proportional and remain approved scope boundaries.

## Gate decision

The addendum is **not approval-ready** and is **not ready for live Vertical append preparation**. It is ready for a Dojo **REWORK** checkpoint carrying only RHD-1, RHD-2, RRA-1, and VH-1.

After those four corrections, one focused re-review should be sufficient. No application implementation, provisional-reconciler approval, credential action, ACL change, service restart, live test, or ledger append is authorized by this review.

## Cost-proportionality record

The addendum estimates accepted implementation and mandatory tests at 12–22 engineering hours and governance/review at 2–4 hours. This review adds no optional hardening work; each blocker is tied to a reproducible accepted-scope defect. Actual elapsed implementation and governance costs were not provided and remain unknown.

## Validation and model

- Validation performed: byte-level SHA-256 of every named input; full-text review of the addendum, approved base design, bulletin, and four live heads; internal consistency analysis against the stated mailbox ordering, authorization, lifecycle, and evidence rules.
- Validation not performed: code inspection, provisional script inspection, executable tests, live Registry/ACL comparison, broker inspection, credential checks, service operations, or ledger mutation.
- Model used: GPT-6.1 Sol, GSP security-specialist role.
