# Ronda QA — Revere Vertical intake apply

Overall result: **PASS**

Scope: exact script SHA `fffcfb8a727ad46f3a3c3096f079874667254f2069ca70625fe3c870b11d0ded`, canonical plan SHA `204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc`, non-mutating live-ledger dry run, and apply/failure testing only on fresh throwaway copies under `C:\Workspace\.tmp\vertical-intake-qa-20261009-7c1b4e90`.

## Q1 — source review

- `script_sha256`: `fffcfb8a727ad46f3a3c3096f079874667254f2069ca70625fe3c870b11d0ded`
- `plan_sha256`: `204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc`
- `planned_write_count`: `5`
- `alternate_write_path_count`: `0`
- `prohibited_operation_count`: `0`
- `result`: `PASS`

## Q2 — artifact pins

- `script_sha256`: `fffcfb8a727ad46f3a3c3096f079874667254f2069ca70625fe3c870b11d0ded`
- `addendum_sha256`: `29feff5e1abe53569083ad89eecd64e884c3d477417987f2245eea47907753ac`
- `final_review_sha256`: `23e380b8b71e9de5560f0a4e3896718f19924477ea0eaf90fbcc13eb4205f451`
- `plan_sha256`: `204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc`
- `mismatch_count`: `0`
- `result`: `PASS`

## Q3 — repair regressions

- `vr_ref_case_count`: `5`
- `vr_ref_pass_count`: `5`
- `ambiguous_thread_rejection_count`: `2`
- `append_role_case_count`: `4`
- `append_role_pass_count`: `4`
- `wrong_role_rejection_count`: `2`
- `result`: `PASS`

## Q4 — dry-run/apply equivalence

- `dry_run_plan_sha256`: `204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc`
- `apply_plan_sha256`: `204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc`
- `event_equivalence_count`: `5`
- `event_difference_count`: `0`
- `dry_run_write_count`: `0`
- `result`: `PASS`

## Q5 — exact stale-state guards

- `guard_case_count`: `9`
- `guard_rejection_count`: `9`
- `pre_guard_write_count`: `0`
- `domain_head_guard_result`: `PASS`
- `vr038_guard_result`: `PASS`
- `vr042_guard_result`: `PASS`
- `vr043_guard_result`: `PASS`
- `plan_guard_result`: `PASS`
- `result`: `PASS`

## Q6 — collision, hierarchy, state, and gate

- `collision_key_count`: `3`
- `collision_rejection_count`: `3`
- `required_state_check_count`: `3`
- `parent_check_count`: `2`
- `gate_check_count`: `5`
- `preflight_failure_write_count`: `0`
- `result`: `PASS`

## Q7 — mutation order

- `observed_write_count`: `5`
- `ordered_match_count`: `5`
- `unexpected_write_count`: `0`
- `parent_reference_match_count`: `5`
- `result`: `PASS`

## Q8 — no partial write and recovery

- `preflight_failure_case_count`: `12`
- `preflight_failure_write_count`: `0`
- `induced_boundary_count`: `4`
- `continued_after_failure_count`: `0`
- `completed_event_integrity_count`: `10`
- `stale_rerun_rejection_count`: `4`
- `automatic_rollback_count`: `0`
- `recovery_requires_new_plan`: `true`
- `result`: `PASS`

## Q9 — post-write integrity/readback

- `projection_finding_count`: `0`
- `ledger_integrity_clean`: `true`
- `event_count_delta`: `5`
- `new_open_thread_count`: `3`
- `artifact_readback_match_count`: `3`
- `parent_readback_match_count`: `3`
- `supersession_readback_match_count`: `2`
- `result`: `PASS`

## Q10 — scope boundary

- `ledger_apply_count`: `1`
- `broker_change_count`: `0`
- `acl_change_count`: `0`
- `credential_action_count`: `0`
- `service_action_count`: `0`
- `deployment_count`: `0`
- `live_cross_host_test_count`: `0`
- `result`: `PASS`

The one ledger apply was against a fresh throwaway copy. The authoritative ledger received no apply from QA; its recursive file count was `340` at initial copy and at the post-test checkpoint. After that checkpoint, a concurrent `VR-20261009-ynm-070.0-OPEN.txt` appeared at `2026-10-09 11:41:58 -05:00`, increasing the count to `341`. The reviewed domain-head pin is therefore stale and the work order's fresh dry-run/current-head checkpoint is required before any release command is prepared.

## Concise execution record

Hash and syntax checks:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath <work-order>,<addendum>,<final-review>,<script>
python -m py_compile C:\Workspace\vertical_revere_registry_authorization_and_hosted_subagent_intake.py
```

Raw concise result: all four required hashes matched; `py_compile` exited `0`.

Non-mutating live dry run:

```powershell
python C:\Workspace\vertical_revere_registry_authorization_and_hosted_subagent_intake.py --vertical-src C:\Repo\vertical\src --ledger \\192.168.2.3\YNM\Projects\Vertical\ledger --projection C:\Workspace\.tmp\vertical-intake-qa-20261009-7c1b4e90\live-dryrun-projection.sqlite3 --expected-plan-sha256 204bcf8c8ec928cd7d4e02346e65c7ba8616920295ee47a17a3231168c0db6fc
```

Raw concise result: `action=dry-run`; `write_count=5`; `dry_run_no_ledger_write=true`; `projection_findings=[]`; `ledger_integrity_clean=true`; all three collision lists empty; required states, hierarchy, and all five gates passed.

Throwaway test harness:

```powershell
python C:\Workspace\.tmp\vertical-intake-qa-20261009-7c1b4e90\qa_harness.py
```

Raw concise result: stale addendum and final-review fixtures rejected; `9/9` stale head/plan pins rejected with zero write; correct role/state combinations accepted and `2/2` swapped combinations rejected; successful apply wrote the exact five ordered events; four induced boundaries retained exactly `1`, `2`, `3`, and `4` clean completed events, stopped before later writes, and rejected stale reruns without changing a completed file.

## Delivery record

- Authoritative ledger apply: `not executed`
- Files changed: `C:\Workspace\TownSquare-MVP\docs\session-registry\ronda-revere-vertical-intake-apply-qa-20261009.md` only
- Temporary directory disposition: remove after resolving and verifying the target remains inside `C:\Workspace\.tmp`
- Final temporary directory disposition: removed; verified absent
- Concurrent ledger change after QA checkpoint: `VR-20261009-ynm-070.0-OPEN.txt`; no live apply was run by QA; fresh dry run/current-head review required
- Material retries: sandbox command helper failed before launch and commands were rerun through the approved elevated PowerShell path; initial `Copy-Item -LiteralPath` wildcard copied zero files and was corrected with bounded `robocopy` (`340/340`); two long dry-run invocations did not return captured output through the command wrapper and were replaced by one hidden subprocess with output redirected inside the bounded QA directory.
- Actual model: exact inherited specialist model identifier unavailable to the agent
- QA elapsed engineering time: approximately `14 minutes`
- Implementation/build cost in this QA work item: `0 engineering time`
- Optional hardening/review admitted: `0`
