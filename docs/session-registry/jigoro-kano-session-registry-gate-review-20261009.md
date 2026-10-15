# Session Registry MVP — governance and logic-gate review

**Review date:** 2026-10-09  
**Disposition:** **REWORK**  
**Scope:** planning artifact and draft Vertical work items only; no review of code, deployment, ledger state, or live registry state.

## Source-access limitation

The command runner failed before process creation with `helper_unknown_error: apply deny-read ACLs`, so I could not directly open the files. This review is based on the coordinating session's evidence packet, which identified the relevant draft sections and supplied the adopted-rule substance. Section references below therefore name the sections/items as represented in that packet rather than line numbers. This review stops being reliable if that packet omitted materially different text.

Sources represented in the packet:

- `docs/session-registry/session-registry-mvp-design-and-draft-work-items.md` — draft status/authority disclaimer; Decision; Architecture; fields and mutations; explicit gates; draft Epic/Feature/Stories S1–S2; Decision requested; work order.
- `docs/governance/townsquare-charter-v1.0-release/RULES-OF-ENGAGEMENT.md` — TSC-ROE-01, TSC-ROE-05, and TSC-ROE-06.
- `docs/governance/townsquare-charter-v1.0-release/LIFECYCLE.md` — registration is claimed identity/role/capability and grants no operator authority; OPEN and CLOSED prerequisites.
- `docs/vertical-poc/README.md` and `docs/vertical-poc/townsquare-vertical-poc-design.md` — OPEN carries goal and definition of done; metadata grants no authority; transitions append and do not edit prior state.

## Result

The draft correctly separates the four concepts under review:

| Concept | Draft treatment | Result |
| --- | --- | --- |
| Session locator | Private provider/session pair used for routing; clear value excluded from Git Vertical and general audit | PASS |
| Agent identity | `agent_id` binding is a claimed registry record, not proof of identity | PASS — consistent with `LIFECYCLE.md` |
| Work authorization | `work_ref` is informative unless the live Vertical item and state authorize the action; retrieve-before-act remains required | PASS — consistent with TSC-ROE-01 and the Vertical rule that metadata grants no authority |
| Operator authority | No session record, locator, or registration grants it; clear-locator access is reserved to a protected operator path | PASS in principle; the access predicate and override behavior require the edits below |

The draft status and **Decision requested** wording also correctly limit the requested authorization to design/boundaries and creation of parent-before-child OPEN records after exact owner IDs are verified. Its express exclusions of WORKING, implementation, deployment, external contact, and any authority inferred from a locator are correct and should remain verbatim in substance.

## Blocking findings

### 1. S1 says “legal transitions only,” but the legal transition relation is not defined

The **Fields**, **Mutation actions**, and **Story S1 — atomic lifecycle** sections name `STARTING | ACTIVE | IDLE | ENDED | LOST` and `register | heartbeat | terminate | mark_lost`, but the supplied draft evidence contains no state-transition table. `IDLE` also has no stated mutation or deterministic derivation. A test cannot decide “legal” without inventing policy, and a state with no producer is not a complete lifecycle.

**Required edit:** In S1, add an exact transition table that identifies (a) the state created by registration, (b) every allowed source/target pair for heartbeat, termination, and lost marking, (c) how `IDLE` is entered or else remove `IDLE` from the MVP, (d) terminal-state behavior, and (e) how an exact idempotent replay differs from a new mutation. Mark every unlisted transition forbidden. Add one positive and one negative acceptance test for each action, including no heartbeat or state change after `ENDED` or `LOST`.

This is a checkability correction within the accepted MVP, not production hardening.

### 2. S2's “protected operator credential” is not yet a decidable authorization predicate

The **protected lookup/history** story reserves clear provider locators to a protected operator credential, but the evidence packet does not define what observable fact makes the caller the operator. A request field such as `agent_id`, `session_uuid`, or an asserted role cannot establish operator authority; `LIFECYCLE.md` expressly says registration grants none. TSC-ROE-06 requires operator stop/question/override/accept/resume/direction to use a protected, attributable path.

**Required edit:** Add this predicate, or equivalent precise language, to S2:

> Clear-locator access is allowed only when the authentication layer supplies a verified principal equal to the configured operator principal. Request-body, query, session-registry, agent-registry, and work-item claims cannot satisfy or override this predicate.

Add tests proving: verified operator principal → allow; authenticated non-operator → deny without revealing the locator; unauthenticated caller → deny; an agent setting an operator-looking field → deny; failure of the Session Registry or GSP-review mechanism does not block or reinterpret an operator stop, question, override, acceptance, resume, or direction.

### 3. The GSP-review precondition can read as a gate on the operator

The **Decision requested / work order** says implementation occurs only after GSP review has no blocking finding. Applied to agent action, that is a checkable precondition. Unqualified, it also reads as preventing the operator from directing otherwise, contrary to TSC-ROE-06's protected operator authority.

**Required edit:** Replace it with:

> A non-operator agent MUST NOT begin implementation until the recorded GSP review has no open blocking finding. The operator retains unconditional authority to direct, stop, override, accept, resume, or otherwise decide through the protected attributable path; this review precondition does not gate the operator.

Add two precondition tests: an agent cannot begin with a missing/open-blocking GSP review; an attributable operator direction is not rejected by this gate. This wording does **not** itself authorize implementation—implementation still requires a later lifecycle action.

## Nonblocking observations

- Before minting the Epic, Feature, or Stories, dereference `eddie-brock` and every other proposed owner/reviewer against the current Agent Registry. Treat the returned registration as a locator/claim, not authority. The draft already identifies this precondition; no additional artifact is needed.
- At eventual closure, TSC-ROE-05 and `LIFECYCLE.md` require an authorized independent acceptor, disposition of every acceptance criterion, and an acceptance Decision before `RESOLVED -> CLOSED`. The named GSP review and operator acceptance do not by themselves document those three closure facts. This is nonblocking for minting OPEN items, but the Story definition of done should point to those existing closure requirements rather than invent a parallel close process.
- The atomic projection/history/audit criterion is checkable if tests establish all-or-nothing commit and exactly one immutable history event for one accepted mutation. Naming those two observations would make S1 easier to verify but is not a separate governance gate.
- The proposal's clear-ID exclusions are appropriately narrow for this MVP. Do not expand this work item into general secret-management, deployment, contact, or production-hardening work without a separate approved item.

## Gate decision

**REWORK before the draft items are filed or offered for final operator approval.** Required rework is limited to the three exact edits above. After those edits, the governance/authority design is suitable to proceed to the independent security review already named in the draft and then to operator decision. This review neither files a tracker event nor authorizes OPEN, WORKING, implementation, deployment, external contact, or live use.

