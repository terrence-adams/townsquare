# TownSquare Working Default — governance and logic-gate review

**Review date:** 2026-10-09  
**Verdict:** **REWORK**  
**Reviewer:** Jigoro Kano governance/logic-gate role  
**Model actually used:** GPT-5 Codex family; the exact deployment SKU is not exposed to this subagent  
**Elapsed time:** unknown; no reliable start timestamp was captured and the host command runner was unavailable

## Scope and validation limitation

This is a governance and logic review only. It authorizes no implementation, deployment, authoritative-ledger append, probe deletion, publication, external contact, or live state transition.

The host command runner failed before process creation with `helper_unknown_error: apply deny-read ACLs`. I therefore could not independently read or diff the workspace files. The coordinating session supplied the full amended draft as a four-part, line-numbered packet and supplied source packets for the adopted Charter, canonical Iron Curtain POC, and approved Session Registry/Revere design and live states. Findings below are **reported-source review**, not filesystem readback. The verdict stops being reliable if the saved files differ materially from those packets.

Reviewed sources:

- `docs/townsquare-default/townsquare-working-default-architecture-and-draft-vertical.md`, supplied lines 1–end.
- `docs/iron-curtain-single-use-permit-poc.md`, canonical contract/source packet including live `VR-20261008-ynm-047.5-WORKING` through `VR-051` states.
- `docs/session-registry/session-registry-mvp-design-and-draft-work-items.md`, approved boundary and canonical live Registry/Revere keys/statuses.
- Adopted TownSquare Charter source packet: TSC-REC-01/02/03, TSC-CTL-01, TSC-CHG-01, TSC-WRK-01/02, TSC-NOT-01, TSC-GATE-01, TSC-BND-01, Authority Resolver, lifecycle, protected-control, receipt-profile, and ROE rules.

Validation performed:

1. Manual predicate-to-authority mapping for TownSquare, Registry, Vertical, Revere, Iron Curtain, operator control, environment/promotion, and acceptance.
2. Dependency walk from S7 and S1 through S2/S3/S5/S6, S4/S8/S9, and S10, including inherited parent dependencies.
3. Comparison of proposed Registry/Revere scope with canonical live keys and statuses.
4. Negative-path review for false authority from content, receipt, identity, session, lineage, `work_ref`, delivery, Crier, environment name, and permit trace.
5. S7 replay against the reproduced `.cable-write-probe` incident, including the no-delete and no-second-probe paths.
6. Check of override, stop, correction, acceptance, deployment, cutover, rollback, and failure dispositions against the adopted Charter.
7. Cost-proportionality check against the stated 104–168 implementation hours and 20–33 governance hours.

## Findings by severity

### BLOCKING 1 — F2 inherits a dependency that defeats the intended non-circular bootstrap

Draft §9 makes **F2 Native intake/receipts depend on all of F1**, while S3 is meant to start after only S1 and S7. F1 cannot complete until S2 completes; S2 waits on S7 and the canonical `VR-047.5 -> VR-051` chain. If a parent Feature dependency applies to its children, S3 is blocked by S2 despite its narrower explicit dependency. The graph is acyclic, but it unintentionally overblocks the non-authorizing receipt lane the draft says may precede full permit integration.

This conflicts with the stated two-lane bootstrap in §6.2 and the desired sequencing in §9.

**Exact required edit:**

- Change F2 from `depends F1` to `depends S1 and S7` (or declare no Feature-level dependency and make child dependencies authoritative).
- Keep S3 depending only on S1 and S7.
- Keep S4 depending on S2 and S3.
- Add one explicit rule: “Child Story dependencies are authoritative for dispatch; a parent Feature dependency MUST NOT silently add dependencies to a child.” If the Vertical engine always inherits Feature dependencies, then remove the F2→F1 edge rather than relying on this sentence.
- Add dependency tests: S1+S7 satisfied/S2 pending permits S3 but not S4; S2+S3 satisfied permits S4; no state permits material `/v1/events` action before the canonical permit chain is accepted.

### BLOCKING 2 — S7's incident receipt currently has no identified non-circular bootstrap path

Draft §§7 and 9 require the probe incident to be receipted before **all** Sentinel implementation, while S3 implements the new receipt lane and itself depends on S7. The draft does not identify an already-operational, authoritative, non-authorizing append path that can create the S7 incident Receipt without implementing S3 or inferring permission to write the NAS ledger. Charter adoption explicitly authorized no governed writes. Planning approval also explicitly authorizes no ledger append.

TSC-GATE-01 and the ROE preserve informational append, but they do not manufacture a write mechanism or actor authorization. A Receipt is evidence, never its own authority.

**Exact required edit:**

- Add an S7 bootstrap precondition naming the **existing authoritative system and exact operation** that will record the incident Receipt before Sentinel implementation.
- State that this append requires a separate attributable operator Decision naming the exact incident Receipt payload/digest and destination; approval of this package is not that Decision.
- State that the append is non-authorizing intake and therefore needs no per-message Iron Curtain permit, but still requires ordinary authentication and append authorization for that existing system.
- If no such existing safe append operation exists, mark S7 blocked and return to the operator; do not implement a temporary endpoint, write the NAS ledger directly, or treat S3 as satisfying its own prerequisite.
- Add a negative test: missing incident Receipt leaves every Sentinel implementation Story nondispatchable while preserving operator control and informational reporting.

### BLOCKING 3 — S7's “probe” evidence wording can authorize the exact failure it is meant to prevent

S7 asks for “independent mount/ACL/probe/adjacent metadata.” In the context of a reproduced hidden write probe, “probe” is ambiguous enough to be read as permission to create another file on the production NAS. The controlling incident boundary forbids that. TSC-GATE-01 requires an exact trigger and disposition; TSC-BND-01 requires missing/unknown authority to block the effect.

**Exact required edit:** Replace that criterion with all of the following:

> Inspect the existing `/…/.cable-write-probe` and adjacent directory/mount metadata read-only. No actor may create, write, touch, rename, move, chmod, chown, truncate, or delete any NAS object during S7 verification. Write-denial tests run only on an explicitly named non-production synthetic target after mount isolation. The existing probe remains untouched until a separate attributable operator Decision and exact one-file cleanup authority name that path and action.

Add tests that fail S7 if a NAS write syscall is attempted or if the existing probe's bytes, metadata, name, or parent entries change without the separate cleanup authority. Record incident Receipt and cleanup Decision as distinct references. Package approval satisfies neither.

### BLOCKING 4 — Proposed S6 duplicates the canonical live Revere work

Draft §§1 and 8 say the package amends/integrates and does not duplicate YNM-EPIC-022. Yet proposed S6 repeats durable per-session mailbox, lease, ACK, replay, at-least-once/dedup, bilateral Codex↔Claude adapters, and v1 compatibility. Those are already the approved canonical Revere Feature and two live OPEN Stories. A new Story with the same deliverable creates competing ownership, acceptance, and state.

The source packet confirms the canonical Revere Feature and both Stories are OPEN. TSC-CHG-01 forbids silent replacement or identifier reassignment, and TSC-REC-03 requires the current authoritative objects rather than a stale projection.

**Exact required edit:** Choose one of these, with the first recommended:

1. **Recommended:** Remove S6 as a new implementation Story. Append operator-approved amendments to the existing canonical Revere items for only the new lineage, receipt-link, and authority-matrix requirements. Make F3 and S9 depend on the existing Revere Story keys at their accepted state.
2. If a separate S6 is operationally necessary, retitle and narrow it to **TownSquare–Revere integration only**. It MUST NOT own or reimplement mailbox, lease, ACK, replay, dedup, v1 compatibility, or bilateral adapters. Its dependencies must name the accepted canonical Revere Stories, and its criteria may cover only integration not already present there.

Add a duplicate scan keyed by canonical work identity before filing. “No duplicate code” is insufficient; there must be no duplicate live work item.

### BLOCKING 5 — Revere authority is checked too late for external contact

S6 says delivery must not become consequential before current Vertical+permit resolution. That protects downstream effects but not the **send itself**. A Revere send is external contact and a state-changing operation. Under the controlling decision, it requires exact valid authority before the send/delivery commit; a recipient's later refusal cannot cure an unauthorized contact. Session binding, a `work_ref`, delivery state, or a safe receipt is not that authority.

**Exact required edit:**

- In the S1 machine matrix, enumerate Revere `send`, lease-producing `receive`, `ack`, redelivery/replay, and adapter delivery separately. For each, name the authoritative classifier, authenticated actor, exact work/decision dependency, whether the canonical permit contract applies or needs a reviewed amendment, enforcement owner, commit point, failure disposition, operator override path, and audit Receipt.
- Require external send/adapter delivery authorization **before** enqueue or delivery commits. Denial/unknown must produce a safe failure Receipt and zero delivery-state mutation.
- Require lease/ack/replay authorization before their state mutation; do not treat session authentication as work authority.
- Make any reviewed endpoint extension depend on the accepted canonical Iron Curtain chain. Do not silently stretch `townsquare-action-permit-poc-v1` beyond its current `/v1/events` contract.
- Keep synthetic/local adapter tests possible without contacting an external session. Live bilateral proof requires a separate exact operator authorization.

### BLOCKING 6 — Lineage records are not yet separated from delegation authority at every use

Draft §§1, 5, and S5 place parent/delegator/subagent lineage in Registry, and S1 says identity/session/`work_ref` are not authority. It does not explicitly include parent/delegator/subagent lineage in that denial. The approved Registry design originally deferred the parent/handoff graph, and the new direction authorizes drafting an amendment—not pretending the graph is already accepted. A field named `delegator` is especially likely to be interpreted as delegated authority.

**Exact required edit:**

- Add `parent_session`, `delegator`, `subagent`, and all lineage fields to S1's explicit non-authority list.
- In S5, label lineage as attributable routing/audit context only. Registry owns the lineage fact; Vertical owns accountable work/addressee; Iron Curtain owns exact action authorization.
- Require every effect to bind the authenticated executing actor/session plus the current accountable work and exact action authority. A parent or delegator link cannot substitute for any of them.
- State that derived subagent permits/delegated capabilities remain rejected in this package, matching §6.3. Do not add a `delegation_decision_ref` that is treated as executable authority unless a later operator-approved contract defines and tests it.
- Amend the canonical Registry items under their existing keys and acceptance path; do not claim the previously deferred graph was already accepted.

### BLOCKING 7 — Rollback is named but its authority gate is not defined

Draft §§7, S8, S10, Hard Gate 9, and the operator choices define deployment and cutover authority, but “rollback bounded” and “rollback prior release” do not say who authorizes rollback or what exact action is bound. Rollback is a material production action and cannot be self-certified by a failing deployment, a test result, or a manifest.

**Exact required edit:** Add one explicit rollback predicate and tests:

> A production rollback may execute only when either (a) the operator's protected deployment Decision and corresponding exact-action permit pre-authorize a named rollback artifact, NAS target, trigger conditions, action, idempotency key, and bounded window, or (b) a later protected operator Decision and fresh exact-action permit authorize that rollback. A failed check may stop/isolate safely but cannot manufacture rollback authority.

Test no permit, expired/mismatched/replayed permit, wrong artifact/target/window, and operator stop. All deny mutation, retain the failure Receipt, and never ordinary-gate the operator's control message.

## Nonblocking observations

1. **Boundary ownership is otherwise sound.** TownSquare owns receipts/evidence/trace; Registry owns identity/session/private locator; Vertical owns work state and acceptance; Revere owns delivery state; Iron Curtain owns policy and canonical exact-action permits. §5.3 correctly denies distributed atomicity and uses local transactions plus causal reconciliation.
2. **The two-lane design preserves the canonical POC in substance.** §6 retains the 120-second single-use opaque bearer, exact binding, HMAC-only persistence, transactional consume, safe `permit_id`, retry semantics, and exclusions. It adds a distinct non-authorizing route instead of weakening `/v1/events`. Blocking Findings 1 and 2 concern sequencing, not the two-lane principle.
3. **False-authority controls are mostly explicit.** Content, identity, session, `work_ref`, delivery, Crier, receipt, digest, and permit trace are correctly non-authorizing. Apply Blocking Findings 5 and 6 so environment/lineage/transport metadata cannot become implicit authority.
4. **Protected locators remain protected.** The public/protected split, digest treatment, and Registry boundary are consistent with the approved Session Registry design. No distributed atomicity claim is made.
5. **Stops, corrections, overrides, and acceptance are correctly pointed to the adopted Charter.** The S1 matrix must preserve TSC-CTL-01: operator control is never delayed or rejected by an ordinary action gate. A receipt for the control is evidence, not a precondition on the operator's authority.
6. **S7 is correctly global in intent.** It gates every Sentinel implementation and separates incident recording from cleanup. Blocking Findings 2 and 3 make that intent decidable and prevent the criterion itself from causing another production write.
7. **Cost remains proportional.** Stated governance effort (20–33 hours) is below stated implementation effort (104–168 hours), optional hardening is zero, and reusable leases, generalized capabilities, derived permits, break glass, HA, retention, and extra vendors are deferred. The required edits do not add production hardening.
8. **Open operator choices remain decisions, not defects.** The operator must choose the Drive shadow criterion (`7 days` or `100 engagements`), rollback window, exact owners after live ID verification, and any separate probe cleanup/incident-append action. None may be inferred from approval of the architecture unless the approval text names it.
9. **S5 is not automatically a duplicate** if it remains reconciliation plus an explicit amendment to the canonical Registry items. It must not create a second Session Registry lifecycle implementation or redefine the live F1/S1/S2 statuses.

## Question-by-question disposition

| # | Review question | Result |
| --- | --- | --- |
| 1 | Every predicate decidable and assigned once | **REWORK** — incident-receipt bootstrap, Revere operation authorization, lineage authority, and rollback predicates need the edits above. |
| 2 | Two-lane bootstrap non-circular and canonical | **REWORK** — design is compatible, but F2 inheritance and S7 receipt bootstrap create operational circularity. |
| 3 | Dependency deadlock/overblocking | **REWORK** — no graph cycle, but F2→F1 overblocks S3. |
| 4 | No artifact mistaken for authority | **PASS after edits** — add explicit lineage denial and pre-send authority. |
| 5 | Lineage/attribution without locator leak or false ACID | **REWORK** — locator and ACID boundaries pass; lineage/delegation separation needs one explicit rule set. |
| 6 | S7 global and no new live probe; cleanup separate | **REWORK** — global intent passes; receipt path and “probe” wording do not. |
| 7 | Override/accept/deploy/cutover/rollback explicit | **REWORK** — all except rollback are sufficiently explicit. |
| 8 | Bounded and cost-proportional | **PASS**. |
| 9 | Duplicate/conflicting live items | **REWORK** — proposed S6 duplicates the canonical Revere Feature/Stories. |
| 10 | Amendments before final checkpoint | The seven blocking edits in this review. |

## Final gate decision

**REWORK before Helio's final checkpoint and before the package is submitted as approval-ready.** The architecture has a viable core, preserves the adopted Charter and canonical permit boundary in principle, and stays cost-proportional. The seven defects above are checkable gate failures rather than preferences: one inherited-dependency overblock, one receipt bootstrap circularity, one unsafe probe ambiguity, one duplicate live-work scope, one too-late external-contact check, one lineage/authority conflation, and one missing rollback authority predicate.

After the exact edits, validation should repeat only these bounded checks: dependency walk, canonical-key duplicate scan, S7 no-write negative test review, Revere pre-send authority table, lineage non-authority tests, and rollback truth table. No implementation, deployment, ledger append, cleanup, publication, or external contact is needed to close this document review.

