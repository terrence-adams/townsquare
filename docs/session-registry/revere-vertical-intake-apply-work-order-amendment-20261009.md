# Revere Vertical intake apply — work-order amendment

Status: **DRAFT HANDOFF / QA AND AUTHORIZATION REQUIRED / NO APPLY AUTHORIZED**  
Planning date: 2026-10-09  
Artifact owner and prospective ledger operator: **Eddie Brock on Venom**  
Script review and QA owner: **Ronda Rousey**  
Dojo checkpoint owner: **Helio Gracie**  
Final command approval owner: **Sensei / Operator**  

This amendment narrows the intake-apply handoff. It does not append or transition a live Vertical event and does not authorize execution of the apply command.

## Hash-bound inputs

| Artifact | Path or identity | Required SHA-256 |
|---|---|---|
| Final approved addendum | `C:\Workspace\TownSquare-MVP\docs\session-registry\revere-registry-authorization-and-hosted-subagent-delegation-addendum-20261009.md` | `29feff5e1abe53569083ad89eecd64e884c3d477417987f2245eea47907753ac` |
| Final focused GSP re-review | `C:\Workspace\TownSquare-MVP\docs\session-registry\gsp-revere-registry-authorization-hosted-subagent-delegation-final-rereview-20261009.md` | `23e380b8b71e9de5560f0a4e3896718f19924477ea0eaf90fbcc13eb4205f451` |
| Intake script | `C:\Workspace\vertical_revere_registry_authorization_and_hosted_subagent_intake.py` | `fffcfb8a727ad46f3a3c3096f079874667254f2069ca70625fe3c870b11d0ded` |
| Canonical intake plan | Script `PLAN_SPEC` canonical SHA-256 | `204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc` |

Any mismatch makes QA and release `FAIL`. A new script or plan hash requires a new source review, dry run, Helio checkpoint, and exact-command approval.

## Authorized shape of the proposed intake

The future apply may produce exactly five events in this order and no others:

1. Append a `WORKING` supersession event to `VR-20261009-ynm-038`.
2. Open `REVERE-REGISTRY-AUTHORIZATION-COVERAGE` as one `OPEN` Feature under the resulting `VR-038` head.
3. Open `REVERE-HOST-BOUND-AUTHORIZATION-RECONCILIATION` as one `OPEN` Story under the resulting Feature opening.
4. Append an `OPEN` supersession event to `VR-20261009-ynm-042`.
5. Open `REVERE-HOSTED-SUBAGENT-DELEGATION` as one `OPEN` Story under the resulting `VR-042` head.

This intake creates no `WORKING` child Story and grants no implementation authority beyond the append contents approved in the final addendum. The delegation Story remains parked on its recorded dependencies.

## Reported dry-run repairs requiring regression checks

1. **VR-reference parsing:** live parents must be found by their unique `work_item_key`/`epic_key` thread match, while displayed `vr_ref` comes from the event routing ID. The script must not parse a `VR-...` reference from a work-item key. Regression fixtures must prove that `YNM-EPIC-022`, `REVERE-PHASE2-DURABLE-SESSION-RELAY`, and `REVERE-DURABLE-SESSION-MAILBOX` resolve uniquely to `VR-038`, `VR-042`, and `VR-043`; zero or multiple matching threads must fail before mutation.
2. **OPEN append role:** the supersession appended to the `OPEN` `VR-042` thread must retain state `OPEN`, use `role_acted_under: project-owner`, and pass `Gate.authorize("OPEN", ...)`. It must not use the `WORKING` append role/path. The `VR-038` supersession remains `WORKING` under its operations-orchestrator path. Regression fixtures must cover both state/role combinations and reject the swapped combinations before mutation.

## Ronda QA work order

Ronda reviews the source and executes only isolated dry-run or throwaway-ledger tests. Every criterion is reported as `PASS` or `FAIL` using only its listed evidence fields. Evidence contains no credential, verifier, token, provider locator, receipt, live message body, or secret-bearing command output.

| ID | PASS condition | FAIL condition | Required evidence fields |
|---|---|---|---|
| Q1 — source review | Source inspection confirms artifact constants, one canonical `PLAN_SPEC`, exactly five planned writes, one dry-run/apply code path, all preflight checks before the first append, and no Revere/broker/credential/service operation. | Any alternate plan/write path, extra mutation, preflight after mutation begins, or prohibited external operation exists. | `script_sha256`, `plan_sha256`, `planned_write_count`, `alternate_write_path_count`, `prohibited_operation_count`, `result` |
| Q2 — artifact pins | Script SHA, addendum SHA, final-review SHA, and computed canonical plan SHA exactly match the four required pins. | Any pin differs or is not verified. | `script_sha256`, `addendum_sha256`, `final_review_sha256`, `plan_sha256`, `mismatch_count`, `result` |
| Q3 — repair regressions | VR-reference fixtures resolve the three required keys to the three correct routing IDs and reject zero/multiple threads; OPEN/WORKING append fixtures accept only their correct state and role combinations. | A key is treated as a VR reference, ambiguity passes, or an append passes with the wrong state/role. | `vr_ref_case_count`, `vr_ref_pass_count`, `ambiguous_thread_rejection_count`, `append_role_case_count`, `append_role_pass_count`, `wrong_role_rejection_count`, `result` |
| Q4 — dry-run/apply equivalence | Dry-run and apply derive identical event content, parent relationships, state, dependency, and mutation order from the same hash-pinned `PLAN_SPEC`; dry-run writes zero ledger events. | Apply can derive different content/order, or dry-run writes. | `dry_run_plan_sha256`, `apply_plan_sha256`, `event_equivalence_count`, `event_difference_count`, `dry_run_write_count`, `result` |
| Q5 — exact stale-state guards | Apply requires exact event UID and content SHA-256 pins for the domain head and `VR-038`, `VR-042`, and `VR-043`, plus the exact plan SHA; changing any one pin refuses before mutation. | A missing or mismatched pin reaches mutation. | `guard_case_count`, `guard_rejection_count`, `pre_guard_write_count`, `domain_head_guard_result`, `vr038_guard_result`, `vr042_guard_result`, `vr043_guard_result`, `plan_guard_result`, `result` |
| Q6 — collision, hierarchy, state, and gate | Preflight rejects collisions for all three new keys; requires `VR-038=WORKING`, `VR-042=OPEN`, `VR-043=OPEN`; requires `VR-042` under the Epic and `VR-043` under `VR-042`; and Gate authorizes each of the five exact target states/headers. | Any collision, wrong state, wrong parent, or unauthorized event reaches mutation. | `collision_key_count`, `collision_rejection_count`, `required_state_check_count`, `parent_check_count`, `gate_check_count`, `preflight_failure_write_count`, `result` |
| Q7 — mutation order | A throwaway successful apply records exactly the five ordered events above with correct parent-event references and no additional event. | Order, count, state, key, or parent reference differs. | `observed_write_count`, `ordered_match_count`, `unexpected_write_count`, `parent_reference_match_count`, `result` |
| Q8 — no partial write and recovery | Every guard/preflight failure produces zero events. At each induced post-start failure boundary in a throwaway ledger, the script stops without later writes; completed append-only events remain intact; stale rerun is refused; recovery requires integrity inspection and a newly reviewed, current-head/hash-pinned plan. No delete, rename, rollback, or blind retry occurs. | A preflight failure writes, execution continues after failure, an existing event is mutated/removed, or the stale command can be rerun as recovery. | `preflight_failure_case_count`, `preflight_failure_write_count`, `induced_boundary_count`, `continued_after_failure_count`, `completed_event_integrity_count`, `stale_rerun_rejection_count`, `automatic_rollback_count`, `recovery_requires_new_plan`, `result` |
| Q9 — post-write integrity/readback | Throwaway apply rebuilds projection cleanly, ledger integrity is clean, event-count delta is exactly five, all new threads are single-event `OPEN` threads, artifact hashes/parents match, and both supersession heads match expected state/content. | Integrity, projection, event count, parent, hash, state, or head readback differs. | `projection_finding_count`, `ledger_integrity_clean`, `event_count_delta`, `new_open_thread_count`, `artifact_readback_match_count`, `parent_readback_match_count`, `supersession_readback_match_count`, `result` |
| Q10 — scope boundary | Review and tests confirm zero broker, ACL, credential, service, deployment, or live cross-host action. | Any excluded action occurs. | `ledger_apply_count`, `broker_change_count`, `acl_change_count`, `credential_action_count`, `service_action_count`, `deployment_count`, `live_cross_host_test_count`, `result` |

Ronda's overall result is `PASS` only when Q1–Q10 are all `PASS`. A failed criterion returns to Eddie and Ip Man for a new reviewed artifact; it is not waived inside QA.

## No-partial-write and recovery boundary

The five filesystem-ledger appends are ordered, not claimed to be one cross-file transaction. The required guarantee is:

- every artifact, integrity, collision, hierarchy, state, gate, domain-head, parent-head, and plan guard completes before the first mutation;
- dry-run and all rejected preflight cases write zero events;
- an unexpected failure after mutation starts stops the sequence immediately and never changes or removes an event already appended;
- the original command becomes stale after any successful append and must not be retried;
- recovery begins with independent integrity/readback, a fresh dry run against the new heads, and a separately reviewed and authorized recovery plan/command.

This is append-only recovery, not rollback ceremony. It is required because a five-file ledger mutation cannot honestly be described as atomic.

## Exact release rule

**No apply may occur until all of the following are true, in order:**

1. Ronda records Q1–Q10 `PASS` for the exact script SHA and plan SHA in this amendment.
2. Helio returns a proceed checkpoint for the reviewed QA handoff.
3. Ronda independently re-reads the current Vertical domain head plus `VR-038`, `VR-042`, and `VR-043` heads and records their event UIDs and content SHA-256 values; any difference from the reviewed dry run requires a fresh dry run and checkpoint.
4. Eddie prepares one exact PowerShell command that first computes the intake script SHA-256, throws unless it equals `fffcfb8a727ad46f3a3c3096f079874667254f2069ca70625fe3c870b11d0ded`, and only then invokes Python with `--apply`, the exact current domain/`VR-038`/`VR-042`/`VR-043` event-UID and content-hash pins, and `--expected-plan-sha256 204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc`.
5. Sensei explicitly approves that exact script-hash/head/plan-pinned command unchanged.

The corrected command must use fail-closed sequential PowerShell statements: assign the literal script path and expected hash, compute `Get-FileHash`, `throw` on mismatch, then invoke Python. A command that invokes Python before or regardless of the hash comparison is invalid. Changing any command byte that affects script path, ledger/domain target, projection, head pins, plan pin, or apply mode requires renewed approval.

This amendment defines the release gate but does not itself satisfy step 5 or authorize execution.

## Explicit exclusions

Under this amendment there is:

- no live Vertical ledger apply or transition;
- no Revere application or broker change;
- no ACL or credential work;
- no service reload or restart;
- no deployment;
- no live cross-host test;
- no implementation `WORKING` transition;
- no modification or approval of `C:\Workspace\revere_reconcile_registry_acl.py`.

## Cost-proportionality

- Implementation/build cost added by this amendment: **0 engineering hours**; it changes no implementation.
- Mandatory script review, isolated QA, head recheck, and approval-package preparation: **4–7 engineering hours**.
- Optional hardening or additional review: **deferred; 0 hours admitted**.

The added effort is mandatory evidence for the five-event mutable handoff and remains below the accepted implementation/test estimate in the bound addendum. Actual elapsed time replaces estimates when available.

## Handoff

- Artifact owner / prospective ledger operator: Eddie Brock on Venom — preserve the four hashes, prepare the dry-run evidence, and prepare but do not execute the corrected exact command.
- Script review / QA: Ronda Rousey — inspect the exact source and execute Q1–Q10 only in dry-run or isolated throwaway-ledger scope.
- Dojo checkpoint: Helio Gracie — evaluate Ronda's result, repairs, mutation/recovery boundary, and current-head handoff.
- Decision: Sensei — approve or decline the exact final hash/head/plan-pinned command.
- Watch for: an unverified script between the hash check and Python invocation, stale domain or parent heads, plan drift, repaired VR-ref/OPEN-role regressions, partial-write misrepresentation, blind retry after a partial sequence, extra events, or any excluded Revere/host action.
