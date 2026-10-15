# Revere host-bound authorization — VR-072 OPEN-to-WORKING transition work order

Status: **DRAFT TRANSITION PLAN / NO LEDGER MUTATION AUTHORIZED**  
Planning date: 2026-10-09  
Planning model: **GPT-5.6 Sol / Ip Man / high reasoning**  
Assignee, actor, and accountable owner: **Eddie Brock (`eddie-brock`) on Venom**  
Transition script review: **Ronda Rousey**  
Exact-command checkpoint: **Helio Gracie**  
Owner-validation design re-review: **GSP**  
Implementation review: **GSP — future gate**  
Acceptance QA: **Ronda Rousey — future A1–A7 gate**  
Final acceptance: **Operator — future gate**  

This work order defines one eligible append-only state transition. It does not create a transition script, append the ledger, approve the provisional reconciler, or authorize any Revere system action.

## Authoritative inputs

| Input | Required value |
|---|---|
| Story | `VR-20261009-ynm-072` / `REVERE-HOST-BOUND-AUTHORIZATION-RECONCILIATION` |
| Current file | `VR-20261009-ynm-072.0-OPEN.txt` |
| Thread UID | `01a1218f-f962-7473-8d7f-fa4f841cec57` |
| Current event UID | `01a1218f-f9b9-7383-8373-68570e5044cc` |
| Current content SHA-256 | `c04c6c1e9fd341e4dfed6a0a0cab141999de3caebfc96dc4cfcbe6408d4c0d97` |
| Current state | `OPEN` |
| Dependencies | `[]` |
| Parent key | `REVERE-REGISTRY-AUTHORIZATION-COVERAGE` |
| Parent thread UID | `01a1218f-f881-70b7-bc9a-9d650f342882` |
| Parent opening event UID | `01a1218f-f8e3-76bc-91fa-acc4338220d2` |
| Parent opening content SHA-256 | `0993d88cb0d1971535b24f1bce2a06b312cd994a380c64f31b490e6dda4b9861` |
| Final design addendum SHA-256 | `29feff5e1abe53569083ad89eecd64e884c3d477417987f2245eea47907753ac` |
| Admitting Epic supersession | `VR-20261009-ynm-038.2-WORKING.txt` |
| Epic supersession event UID | `01a1218f-f7d2-75f1-8a00-08af2f832d71` |
| Epic supersession content SHA-256 | `78aaa9ed0a30bb417879271385e40bb5684c2804b4bb3eaee8beb0f209276c3e` |

The expected SHA-256 of this work order cannot be self-embedded. Ronda and Helio must use the externally reported hash for this exact file as the command pin. Any edit requires a new hash and renewed review/checkpoint.

## Owner acceptance and Registry validation contract

The prior observation at `2026-10-09T16:51:45.0786595Z` established HTTP `200`, Registry v1.2, `possibly_stale=false`, one active `eddie-brock` at `host:Venom`, local host `VENOM`, and raw response SHA-256 `e6f0ab2803ba5d18fbb51074bd70e808554bc6c8994917fccebf79841b5f0ac6`. That raw response hash is audit history only. It is not an authorization pin because fresh observations legitimately change time-varying response fields.

The assignee acceptance remains: **explicitly accepted as Eddie Brock on Venom**. Its stable evidence reference is:

`C:\Workspace\TownSquare-MVP\docs\session-registry\revere-host-bound-authorization-working-transition-work-order-20261009.md#owner-acceptance-and-registry-validation-contract`

### Canonical stable owner facts

The corrected dry run constructs this exact logical object before hashing:

```json
{
  "acceptance_evidence_ref": "C:\\Workspace\\TownSquare-MVP\\docs\\session-registry\\revere-host-bound-authorization-working-transition-work-order-20261009.md#owner-acceptance-and-registry-validation-contract",
  "acceptance_statement": "explicitly accepted as Eddie Brock on Venom",
  "agent_id": "eddie-brock",
  "binding": "host:VENOM",
  "classification": "host_bound",
  "head_content_sha256": "c04c6c1e9fd341e4dfed6a0a0cab141999de3caebfc96dc4cfcbe6408d4c0d97",
  "head_event_uid": "01a1218f-f9b9-7383-8373-68570e5044cc",
  "local_host": "VENOM",
  "provider": null,
  "registry_contract": "ynm-agent-registry",
  "registry_schema": "agent-registry-response-v1.2",
  "registry_version": "1.2",
  "status": "active",
  "thread_uid": "01a1218f-f962-7473-8d7f-fa4f841cec57",
  "vendor": "OpenAI",
  "work_item_key": "REVERE-HOST-BOUND-AUTHORIZATION-RECONCILIATION"
}
```

Registry v1.2 supplies `section`, not a separate `classification`; raw `section` must equal `host_bound`, and canonical `classification` is `host_bound`. If a future response includes a non-null classification field, it must also equal `host_bound`. Registry v1.2 supplies `vendor: OpenAI` and no separate provider field; canonical `provider` is therefore JSON `null`. Compatible schema means a top-level object with `version`, `possibly_stale`, `staleness`, and an `agents` array, plus the required owner-record fields used above; the canonical schema label is `agent-registry-response-v1.2`. A present provider field, changed vendor, missing required structure, or schema change requires a new review rather than silent normalization.

Normalization and digest rules:

- `agent_id`, `status`, `section`/classification, `vendor`, work-item key, thread UID, event UID, acceptance statement, and evidence reference are case-sensitive and must exactly match the literals above.
- Binding must parse as `host:<hostname>`; `host` is lower-case and the hostname is compared case-insensitively, then canonicalized to upper-case `host:VENOM`.
- Local host is trimmed and upper-cased with invariant rules, then must equal `VENOM`.
- Registry version may carry one leading `v`; remove it and require normalized semantic contract version exactly `1.2`. Any other version is incompatible for this transition.
- SHA-256 values are lower-case hexadecimal. Unknown, missing, blank, malformed, or duplicate values fail; they are not defaulted.
- Serialize the object as UTF-8 JSON with keys sorted lexicographically, `,` and `:` separators, no insignificant whitespace, `ensure_ascii=false`, and no trailing newline; compute SHA-256 over those exact bytes and render lower-case hexadecimal. This is `owner_stable_digest_sha256`.

The Ronda-reviewed dry run reports the resulting stable digest. The exact apply command pins that digest; this work order does not pre-approve a digest emitted by the current provisional script.

### Volatile audit-only observation

The following are recorded in the transition command's JSON evidence output under `owner_observation_audit`, not in the Vertical event header/body and not in the event-plan hash:

- `observed_at`;
- Registry record `last_seen`;
- `staleness.last_poll_ok`, `staleness.age_seconds`, and `staleness.interval_seconds`;
- raw Registry response SHA-256;
- transport start/end/duration and HTTP timing.

The event stores only `owner_validation_contract: vr072-owner-v1`, `owner_stable_digest_sha256`, and the acceptance-evidence reference. The rendered event-plan hash is computed over the stable event content before apply. Apply performs a new Registry read, recomputes the same stable digest, and requires both the digest pin and rendered event-plan pin to match. Its newly observed volatile values may differ without changing either pin; they remain in separate command evidence. No volatile field may be copied into the rendered event or used to recompute its plan hash.

### Apply-time freshness

Immediately before all ledger mutation guards, apply performs a new Registry GET and requires:

- HTTP `200`, `possibly_stale=false`, and Registry version compatible exactly as normalized above;
- compute `agent_id_record_count` over all Registry records whose case-sensitive `agent` value is exactly `eddie-brock`, before any status, binding, section, vendor, provider, classification, or freshness filtering, and require `agent_id_record_count == 1`;
- validate that sole record with `status=active`; a binding that parses as `host:<hostname>` with lower-case scheme `host`, a case-insensitive hostname equal to `VENOM`, and canonical value `host:VENOM`; raw `section=host_bound`; `vendor=OpenAI`; and no separate non-null provider/classification conflict. Any second exact-agent record fails even when it is inactive, wrong-host, or otherwise invalid;
- local host normalized to `VENOM`;
- valid RFC 3339 UTC `staleness.last_poll_ok` and record `last_seen`, each neither in the future beyond five seconds of clock-skew tolerance nor older than **120 seconds** at the apply observation;
- reported `staleness.age_seconds` between `0` and `120`, with absolute difference from the locally derived non-negative `last_poll_ok` age no greater than five seconds, and `staleness.interval_seconds` no greater than `60`.

The 120-second ceiling is twice the Registry's declared 60-second polling interval: it tolerates one delayed poll plus command processing without allowing an indefinitely stale binding to authorize a write. Unknown/missing/duplicate/inactive/wrong-host/incompatible/stale/unavailable data fails before any ledger write.

## Provisional script status

`C:\Workspace\vertical_revere_host_bound_authorization_working.py` at SHA-256 `e1dae1fd1d386e8966bc6b2675b04b589870efbb87092359cdc4d2879ed0bb3c` pins the volatile raw response and embeds volatile receipt data in the rendered plan. It is **not approved**. Eddie Brock on Venom may make only the script correction required by this contract after GSP re-review; the corrected script receives a new SHA and must pass Ronda review before any Helio checkpoint.

## Exactly one proposed event

The future command may append exactly one file:

`VR-20261009-ynm-072.1-WORKING.txt`

The event must:

- append to thread `01a1218f-f962-7473-8d7f-fa4f841cec57` with `expected_head: 01a1218f-f9b9-7383-8373-68570e5044cc`;
- set `event: 1` and `state: WORKING`;
- name `eddie-brock` as `assigned_to`, `actor`, and `accountable_owner`, with `actor_host: Venom` and a provenance basis of explicit assignee acceptance plus current Registry binding;
- use the gate-valid WORKING-transition role and record Eddie as the action owner; assignment text alone is not acceptance evidence;
- preserve `work_item_key`, `work_item_level`, `project`, title, parent key/thread/event/content, dependency keys, scope, A1–A7 definition of done, full acceptance-criteria objects, explicit exclusions, cost metadata, addendum/review hashes, and acceptance owners exactly from `VR-072.0`;
- set `implementation_start_authorized: true` and `implementation_authorized: bounded-a1-a7-host-bound-reconciliation-lane-only`;
- set `dispatch_target: eddie-brock` and record only `owner_validation_contract: vr072-owner-v1`, the pinned `owner_stable_digest_sha256`, and the acceptance-evidence reference; volatile observation fields remain outside the event;
- keep `self_acceptance_authorized: false` and mark GSP implementation review, Ronda A1–A7 QA, and operator acceptance as pending;
- keep `broker_change_authorized: false`, `acl_change_authorized: false`, `credential_operation_authorized: false`, `service_operation_authorized: false`, `reconciler_execution_authorized: false`, `deployment_authorized: false`, and `live_cross_host_test_authorized: false`.

The bounded WORKING state admits only source inspection, read-only Registry/ACL evidence gathering, plan preparation, provisional-reconciler review, and preparation of later permission-gated handoffs. It does not authorize running the reconciler, applying an ACL, creating/enrolling a credential, restarting a service, or sending a live cross-host Revere message.

## Preserved lane contract

The transition preserves this exact scope from `VR-072.0`:

> review the provisional reconciler; report and reconcile the complete effective ownership relation; generate a hash-bound dry-run; correct host-bound ownership including Wolverine; locally issue credentials only for confirmed missing host principals; validate authenticated host-bound send/receive and rejection of every non-owning principal.

That scope describes the Story's eventual accepted outcome; the operational portions remain held by the false authorization fields above until separately reviewed and approved.

The transition preserves A1–A7 without changing pass/fail language or required evidence fields:

1. A1 — complete post-plan ownership relation and strict failure for portable or retired/inactive ownership.
2. A2 — canonical Wolverine ownership and authenticated synthetic send/receive.
3. A3 — no change or exposure of already-onboarded credentials/verifiers.
4. A4 — local-only issuance and successful authentication for confirmed missing host principals.
5. A5 — Registry/ACL/plan hash binding and explicit operator override boundary.
6. A6 — owner send/receive plus every non-owner rejection.
7. A7 — admitted parent lane, parked Revere Phase 2, and valid child WORKING authority.

The transition also preserves every explicit exclusion in `VR-072.0`, including no portable credential/ACL ownership, no change to already-onboarded credentials, no Session Registry parent graph or portable locator, no generalized auth/delegation framework, no Revere-v1 guarantee change, no exactly-once claim, no deployment/external contact/live content/optional hardening/self-acceptance, and no cleanup or reversion of the reported out-of-scope Agentic fast-forward or Venom scratch file.

## Transition-script release conditions

The transition script or command remains dry-run by default. Apply is unavailable unless every condition below passes:

1. Verify the externally approved SHA-256 of this exact work-order file and the addendum SHA above before loading Vertical code.
2. Independently read and pin the current Vertical domain-head event UID and content SHA-256 immediately before command approval.
3. Re-read `VR-072` and require the exact thread, event UID, content SHA, filename, event sequence, and `OPEN` state above.
4. Require one and only one live thread/opening for `REVERE-HOST-BOUND-AUTHORIZATION-RECONCILIATION` and no existing event above sequence `0`.
5. Require `dependency_keys: []` and the exact parent key/thread/event/content relation above.
6. Require the admitting `VR-038.2` event UID/content hash in the Epic lineage and no later Epic event that revokes the host-bound lane or admits parked `VR-073`.
7. Perform a new Registry read; compute and require `agent_id_record_count == 1` before any status, binding, section, vendor, provider, classification, or freshness filtering; enforce the canonical field, sole-record validation, compatibility, local-host, and 120-second freshness rules above; recompute `owner_stable_digest_sha256`; and require it to equal the reviewed command pin. The raw response hash is audit-only and may differ.
8. Rebuild the projection and require zero findings; require a clean ledger integrity result and successful gate authorization for the exact proposed WORKING header.
9. Dry-run must render one stable event only, make zero ledger writes, exclude all volatile observation fields from the event/event-plan hash, and emit the current domain/head pins, stable owner digest, rendered event-plan hash, and exact future apply command.
10. Apply must require literal expected values for corrected script hash, work-order hash, addendum hash, domain head event/content, `VR-072` head event/content, `owner_stable_digest_sha256`, and the rendered event-plan hash. Missing or mismatched pins refuse before mutation.
11. Apply appends one event only with `expected_head` bound to the opening event. There is no second transition, child dispatch, or Revere action.
12. Post-write readback must prove the exact filename, sequence `1`, new event UID/content hash, `WORKING` state, thread/key/parent preservation, Eddie owner/actor/assignee fields, stable owner-validation fields with no volatile metadata, bounded authorization/hold fields, one-event domain delta, clean projection/integrity, and `VR-073` still `OPEN`/parked.

Any mismatch stops without retry. Do not rerun a stale command, delete or rename an event, or attempt corrective mutation. Re-read current state and prepare a new dry-run, work-order review, Helio checkpoint, and Sensei-approved exact command.

## PASS/FAIL transition criteria

Evidence reports only `PASS` or `FAIL` plus the named minimal fields. It contains no secret material or full Registry payload.

| ID | PASS condition | FAIL condition | Required evidence fields |
|---|---|---|---|
| T1 — artifact pins | Work-order and addendum hashes match the approved pins. | Either hash differs or is unverified. | `work_order_sha256`, `addendum_sha256`, `mismatch_count`, `result` |
| T2 — eligible current state | Domain/head pins match; `VR-072` is the unique sequence-0 `OPEN` thread for the key; dependencies are empty; parent and admitting Epic lineage match; projection/integrity are clean. | Any state, uniqueness, sequence, dependency, parent, admission, projection, integrity, or head check fails. | `domain_head_event_uid`, `domain_head_content_sha256`, `vr072_head_event_uid`, `vr072_head_content_sha256`, `matching_thread_count`, `dependency_count`, `parent_match`, `epic_admission_match`, `projection_finding_count`, `ledger_integrity_clean`, `result` |
| T3 — owner validation | A fresh read computes `agent_id_record_count` across all exact case-sensitive `eddie-brock` records before other filtering and requires it to equal one; the sole record then satisfies every stable owner fact, version/local-host/freshness rule, and explicit acceptance reference; recomputed stable digest equals the reviewed pin. Changed volatile metadata alone does not change the digest. | Data is unavailable, unknown, missing, duplicated by any second exact-agent record, inactive, wrong-host, incompatible, stale, or the stable digest differs. | `owner_validation_contract`, `owner_stable_digest_sha256`, `expected_owner_stable_digest_sha256`, `stable_digest_match`, `agent_id_record_count`, `matching_record_count`, `freshness_threshold_seconds`, `last_poll_age_seconds`, `last_seen_age_seconds`, `possibly_stale`, `acceptance_evidence_ref`, `result` |
| T4 — preservation and boundary | Rendered event preserves the key, parent, dependency, scope, A1–A7 criteria, exclusions, owners, and design hashes; it authorizes only bounded A1–A7 work and retains every operational hold. | A preserved field changes, scope expands, or any held operation becomes authorized. | `preserved_field_count`, `preserved_field_mismatch_count`, `criteria_count`, `exclusion_count`, `bounded_lane_authorized`, `operational_hold_false_count`, `result` |
| T5 — dry-run and gate | Dry-run is default, writes zero events, renders exactly one gate-authorized stable WORKING event, excludes volatile observation metadata from the event and plan hash, and emits all required pins. | Dry-run writes, renders another action, includes volatile metadata in the event/plan, omits a pin, or gate rejects. | `dry_run_write_count`, `rendered_event_count`, `gate_result`, `volatile_event_field_count`, `required_pin_count`, `missing_pin_count`, `result` |
| T6 — apply guard and mutation | Apply accepts only the corrected script plus exact artifact/head/stable-digest/rendered-plan pins and appends exactly one event with expected-head concurrency control. Every mismatch refuses before mutation. | Apply uses the provisional script, accepts a missing/stale pin, writes before validation, or appends other than one event. | `corrected_script_sha256`, `guard_case_count`, `guard_rejection_count`, `pre_guard_write_count`, `stable_digest_match`, `rendered_plan_match`, `applied_event_count`, `expected_head_match`, `result` |
| T7 — readback | Readback proves the exact filename, sequence, state, event/content hashes, key/thread/parent, Eddie fields, stable owner-validation fields, absence of volatile observation fields, bounded authorization/holds, one-event delta, clean projection/integrity, and parked `VR-073`. | Any readback differs, volatile metadata enters the event, or another event/state changes. | `filename_match`, `sequence`, `state`, `new_event_uid`, `new_content_sha256`, `owner_stable_digest_match`, `volatile_event_field_count`, `preserved_field_match`, `operational_hold_match`, `domain_event_delta`, `projection_finding_count`, `ledger_integrity_clean`, `vr073_state`, `result` |
| T8 — scope exclusion | Transition produces no `VR-073`/`VR-042` transition and no reconciler, broker, ACL, credential, service, deployment, or live-test action. | Any excluded action occurs. | `vr073_transition_count`, `vr042_transition_count`, `reconciler_execution_count`, `broker_change_count`, `acl_change_count`, `credential_action_count`, `service_action_count`, `deployment_count`, `live_cross_host_test_count`, `result` |
| T9 — owner-validation regressions | Identical stable owner facts with changed volatile audit metadata produce the same digest and rendered event-plan hash. Wrong host, inactive, stale flag, poll/last-seen age over 120 seconds, duplicate, missing, changed story head, stable-digest mismatch, and rendered-plan mismatch each fail before write. A collision fixture containing one valid Eddie record plus a second exact-agent wrong-host or inactive Eddie record reports `agent_id_record_count == 2` and fails before write. | The valid volatility case changes a stable pin, any invalid case reaches mutation, or either duplicate-collision fixture is accepted. | `volatile_change_pass_count`, `wrong_host_rejection_count`, `inactive_rejection_count`, `stale_rejection_count`, `freshness_rejection_count`, `duplicate_rejection_count`, `duplicate_collision_rejection_count`, `missing_rejection_count`, `changed_head_rejection_count`, `stable_digest_mismatch_rejection_count`, `rendered_plan_mismatch_rejection_count`, `invalid_case_write_count`, `result` |

Overall transition evidence is `PASS` only when T1–T9 are all `PASS`.

## Explicit exclusions

This work order authorizes none of the following:

- transition of `VR-073`, `VR-042`, or any item other than `VR-072`;
- a second ledger write or a `WORKING` transition for the parent Feature;
- execution or approval of `C:\Workspace\revere_reconcile_registry_acl.py`;
- broker or Revere application/configuration change;
- ACL read-write apply or credential generation/enrollment/distribution;
- service reload/restart, deployment, external contact, or live cross-host Revere test;
- GSP implementation approval, Ronda A1–A7 acceptance, operator acceptance, or self-acceptance.

## Cost for this transition only

- Corrected guarded transition script/command and isolated owner-validation regressions: **4–7 engineering hours**.
- Planning, focused GSP design re-review, Ronda script review, Helio command checkpoint, and operator command review: **2–3 engineering hours**.
- Revere implementation, system operation, or production hardening admitted here: **0 hours**.
- Actual elapsed time and token/cost data: **unknown until recorded**.

Cost delta from the prior work order: **+2–3 implementation/test hours** for canonical digest, freshness, and volatility regression coverage; **+1 governance hour** for the required GSP re-review and renewed gates. No optional hardening was added.

## Handoff

- Design re-review: GSP — verify the canonical field set, normalization/digest algorithm, 120-second freshness rule, and separation of volatile evidence from the stable event plan.
- Script-only correction: Eddie Brock on Venom — replace raw-response pinning and volatile event-plan content; preserve every existing hold/exclusion; emit a new script SHA; one-event dry-run by default.
- Review corrected transition script and T1–T9: Ronda Rousey — source review plus isolated/throwaway validation only; the provisional SHA `e1dae1fd1d386e8966bc6b2675b04b589870efbb87092359cdc4d2879ed0bb3c` cannot pass.
- Checkpoint exact command: Helio Gracie — verify hashes, heads, stable owner digest, freshness/audit evidence, one-write plan, holds, and exclusions.
- Decide exact command: Sensei / Operator — separate approval is required after the checkpoint.
- Future implementation review: GSP; future A1–A7 acceptance testing: Ronda Rousey; final acceptance: Operator.
- Watch for: assignment mistaken for acceptance, raw-response hash used as an authorization pin, volatile observation data entering the rendered event plan, unacceptable Registry freshness, provider/vendor or host normalization drift, newer domain/story head, parent/admission drift, criteria/exclusion loss, a hold field set true, additional ledger writes, accidental `VR-073`/`VR-042` transition, or any Revere operation smuggled into the state change.
