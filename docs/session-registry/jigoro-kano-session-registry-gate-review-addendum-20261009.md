# Session Registry MVP — governance gate review addendum

**Review date:** 2026-10-09  
**Disposition:** **PASS**  
**Scope:** closure of the three blockers in `jigoro-kano-session-registry-gate-review-20261009.md`, plus the newly directed Revere Phase-2 Feature. This addendum does not review code, live credentials, deployment, ledger state, or implementation evidence.

## Source-access limitation and claim basis

The host command runner remains unavailable (`helper_unknown_error: apply deny-read ACLs`), so I could not directly read or diff the changed files. The changes assessed here are **reported-by the coordinating session** in its follow-up evidence packet. The PASS stops being reliable if the saved draft differs materially from that packet.

Rules applied remain those identified in the original review: TSC-ROE-01 (retrieve before consequential action), TSC-ROE-05 (independent close), TSC-ROE-06 (protected, attributable operator authority), `LIFECYCLE.md` (registration does not grant operator authority; OPEN/CLOSED prerequisites), and the Vertical POC rule that metadata grants no authority and transitions are appended rather than edited.

## Original blocker closure

| Original blocker | Corrective evidence | Result |
| --- | --- | --- |
| 1. “Legal transitions” was not decidable and `IDLE` had no producer | The lifecycle now enumerates registration states, heartbeat transitions including the sole route into `IDLE`, terminal actions, forbidden terminal/unlisted mutations, server timestamps, and zero-write exact idempotent replay. Forbidden attempts return sanitized `409` with no writes. | **CLOSED**. The legal relation and its failure disposition are now testable from observable inputs and stored rows. |
| 2. The clear-locator authorization predicate was not decidable | Access now requires ordinary Registry authentication **and** constant-time equality between `X-Registry-Operator-Token` and a configured nonempty `REGISTRY_OPERATOR_TOKEN`; asserted body/query/agent/work/role values cannot satisfy the predicate. Negative outcomes are indistinguishable `404` responses with `no-store`, and credentials are excluded from logs. | **CLOSED for this MVP**. The dedicated bearer credential acts as the protected operator principal, provided it is held only by the operator and ordinary Registry authentication remains attributable. A request assertion or registry row cannot manufacture authority. |
| 3. The GSP precondition could gate the operator | The gate now applies to agents: they may implement after a clear GSP review, or after an explicit operator Decision overriding named findings. It expressly does not constrain operator authority. | **CLOSED**. Both branches are observable board facts, and the override belongs only to the operator. |

No further edits are required to close the three findings.

## Revere Phase-2 Feature

The new operator direction introduces no governance or logic-gate blocker on the evidence supplied.

- The direction itself is operator authority to add and prioritize the draft Feature; it is not authority inferred from a session, agent registration, priority label, or parent link.
- Making Revere depend on Registry addressing preserves the separation already passed: a session address tells the relay where to route, not who has authority, what work is authorized, or whether contact is permitted.
- Session-bound send/receive/ack, at-least-once delivery with deduplication, and reconnect/replay identify observable behaviors suitable for acceptance tests. Preserving v1 gives the compatibility boundary a testable reference.
- The Codex↔Claude adapters are transport integrations. They do not merge vendor identity with agent identity or operator authority.
- The reported explicit protected-operator rule carries TSC-ROE-06 into the relay: transported text, sender metadata, agent identity, and session ownership cannot create operator authority; an operator command remains valid only through the protected attributable path.

The existing document-wide disclaimer remains controlling: approval or creation of an OPEN Feature does not authorize WORKING, implementation, deployment, live relay traffic, external contact, or a provider action. At action time, agents must dereference the current dependency and authorization records under TSC-ROE-01. “Top priority” orders queued work; it grants no authority by itself.

## Nonblocking boundary notes

- The operator token design is adequate only while the token is a dedicated operator secret and ordinary Registry authentication yields an attributable caller. If the token is shared with an agent/service or ordinary authentication is anonymous/shared, the TSC-ROE-06 conclusion must be reviewed again.
- Revere's deduplication-key scope, acknowledgement semantics, retention, and replay window are implementation-contract choices. They need tests during implementation, but they are not governance blockers to filing the bounded Feature.
- The Registry dependency should be dereferenced before Revere moves into dependent implementation or live traffic. Its Feature may be created OPEN without pretending the dependency is already satisfied.
- Eventual closure still requires the existing TSC-ROE-05 / `LIFECYCLE.md` independent-acceptance record and criterion-by-criterion disposition; this is not an extra review layer.

## Gate decision

**PASS for submission to the operator.** The three original blockers are closed, and the Revere Phase-2 addition introduces no new governance/gate blocker within the stated MVP/Phase-2 scope. **Exact remaining blocking edits: none.**

This PASS authorizes no filing, state transition, WORKING, implementation, deployment, credential creation, relay traffic, external contact, or provider action. Those remain separate lifecycle actions under operator authority.

