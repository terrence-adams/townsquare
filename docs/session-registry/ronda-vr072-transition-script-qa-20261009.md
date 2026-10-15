# VR-072 Transition Script QA Record

Date: 2026-10-09
QA owner: Ronda Rousey
Overall result: PASS

## Scope

This record covers C:\Workspace\vertical_revere_host_bound_authorization_working.py for the bounded VR-072 transition. QA used retained exact outputs, fake Registry responses, synthetic inputs, a copied throwaway ledger, and read-only live dry-runs. No live --apply was executed. No Revere event, reconciler, broker, ACL, credential, service, deployment, provider contact, or live messaging action was performed.

## Authoritative artifacts

| Artifact | SHA-256 |
| --- | --- |
| C:\Workspace\vertical_revere_host_bound_authorization_working.py | a29264709dab12d6cf96adb68b6234a4e686af7d3d8d994afda61f3c47764132 |
| C:\Workspace\TownSquare-MVP\docs\session-registry\revere-host-bound-authorization-working-transition-work-order-20261009.md | d21a4c51a07293cb078252dcb1f811a6044fb82a5a2d9cb8257a2da09a2183f5 |
| C:\Workspace\TownSquare-MVP\docs\session-registry\revere-registry-authorization-and-hosted-subagent-delegation-addendum-20261009.md | 29feff5e1abe53569083ad89eecd64e884c3d477417987f2245eea47907753ac |

Independent verification reported AST_PARSE=PASS and inspected the complete current source.

## T1-T9

| Test | Result | Evidence |
| --- | --- | --- |
| T1 artifact pins | PASS | Independent final hashes matched; AST parse passed. |
| T2 eligible current state | PASS | Corrected-script live dry-run found one VR-072 thread, no dependencies, matching parent/admission, clean ledger, zero projection findings, and unchanged heads. |
| T3 owner validation | PASS | Valid current owner and full fake-Registry matrix passed; exact case-sensitive eddie-brock count occurred before filtering. |
| T4 preservation/boundary | PASS | 7 criteria, 7 exclusions, 7 false operational holds, 36 preserved fields, zero mismatches. |
| T5 dry-run/gate | PASS | Exit 0, empty stderr, gate PASS, 10 required pins, zero missing, one rendered event, zero live writes, no volatile event/plan fields. |
| T6 apply guards | PASS | All omitted pins and artifact/digest/plan/head mismatches rejected before write; no live apply. |
| T7 readback | PASS | Exactly one event appended only to a copied ledger; delta 1, sequence 1, WORKING, clean readback/integrity/projection. |
| T8 exclusions | PASS | Zero prohibited actions; VR-073 and VR-042 unchanged. |
| T9 regressions | PASS | Required invalid, collision, freshness, schema, head, digest, and plan cases exercised with zero invalid writes. |

## Behavioral matrix

PASS: valid current/dry-run; hostname case normalization; negative signed-age normalization; valid present v1.2 schema; absent optional schema; volatile-only changes with identical stable digest and rendered plan; exactly one proposed append and one copied-ledger event.

REJECT before write with write_count=0: valid plus wrong-host duplicate; valid plus inactive duplicate; missing exact agent; two valid duplicates; inactive; wrong host, section, vendor, provider, classification, version, schema, or local host; possibly_stale; last_poll or last_seen over 120 seconds; more than five seconds future; reported/derived age difference over five seconds; interval over 60; changed domain/story UID or content; work-order, addendum, script, stable-digest, or rendered-plan mismatch; and omission of each of 10 required pins.

The exact case-sensitive count rejected duplicates before filtering. Volatile variants retained digest 184e47fe2f4b7e34b3c6266e15a5ec062a249a08ec7f4d588f699289e14473b9. Scans reported volatile_event_field_count=0, volatile_plan_field_count=0, volatile_plan_fields=[].

## Schema defect and fix

The isolated schema test found that pre-fix SHA ad6a3daab47f1d7c36f22b3191ddeb7cb0f89784155f9153f0c3024a461fa529 accepted present schema agent-registry-response-v1.3. Corrected SHA a29264709dab12d6cf96adb68b6234a4e686af7d3d8d994afda61f3c47764132 rejects v1.3 and unknown-schema with zero writes, accepts v1.2 or an absent optional label, and preserves stable digest/rendered-plan equality under volatile changes. Independent source review confirmed the narrow optional-label/exact-value clause and current protected holds, binding, counting, age, rendering, gate, re-gate, and append logic.

## Independent live recapture

Exact invocation, once and without --apply:

    python "C:\Workspace\vertical_revere_host_bound_authorization_working.py" --vertical-src "C:\Repo\vertical\src" --ledger "\\192.168.2.3\YNM\Projects\Vertical\ledger" --projection "C:\Workspace\.tmp\vr072-independent-recapture-20261009-843d72f3fa7c4d27b04940218b27f117\projection.sqlite3"

Result: PROCESS_COMPLETED=True, EXIT_CODE=0, empty stderr, full dry-run JSON.

- plan SHA: dff2b7a05fd76dfcfe09a8719824253975983fb4ba7a1ac960ab4db25f04fea0
- rendered event-plan SHA: dbd686d9feb51cf2c606f6df7fb66782b8f4190251878ba759bff64ced77fbf6
- stable owner digest: 184e47fe2f4b7e34b3c6266e15a5ec062a249a08ec7f4d588f699289e14473b9
- domain head: event 01a1218f-fb1b-71f2-bdf2-6e3375596ec7; content 45b356dbd893980f5c183789ebba37ced5686e5830535f830e7d9ad8e16d6692
- story head: event 01a1218f-f9b9-7383-8373-68570e5044cc; content c04c6c1e9fd341e4dfed6a0a0cab141999de3caebfc96dc4cfcbe6408d4c0d97
- proposed append count: 1
- VR-073 and VR-042: unchanged

Recursive live-ledger inventory:
- before: count 347; SHA-256 6b2542cbc4093048bed7a26717e3ff2353c95220e3334aabdd4fd601751d0f8a
- after: count 347; SHA-256 6b2542cbc4093048bed7a26717e3ff2353c95220e3334aabdd4fd601751d0f8a
- count equal=True; SHA equal=True; zero writes
- projection existed only in the bounded directory; cleanup removed it

## Safe identity

Evidence contains host_id=VENOM, agent_id=eddie-brock, safe session_id=codex-task:/root/eddie_vr072_transition_fix, and provider=null. No raw provider locator or credential was recorded.

## Fixtures and cleanup

The broad harness copied the ledger to C:\Workspace\.tmp\vr072-qa-a188jumu and appended one event only there, moving count 348 to 349. Its projection and directory were removed. Schema regression used fake Registry and synthetic in-memory opening data with no ledger/projection. Temporary harnesses were deleted. One initial cleanup method failed; a guarded non-repeating cleanup succeeded. No substantive harness retry occurred.

Synthetic plan SHA f5e21af905fa01e360956abbad71fdef62cad6026aced3bbc246d0ddda7e9111 is test-only and prohibited as a live pin.

## Reviewed future command - NOT EXECUTED

Separate approval is required. Exact reviewed command:

    $scriptPath = 'C:\Workspace\vertical_revere_host_bound_authorization_working.py'; $expectedScriptSha256 = 'a29264709dab12d6cf96adb68b6234a4e686af7d3d8d994afda61f3c47764132'; $actualScriptSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $scriptPath).Hash.ToLowerInvariant(); if ($actualScriptSha256 -ne $expectedScriptSha256) { throw 'transition script SHA-256 mismatch' }; & python $scriptPath '--vertical-src' 'C:\Repo\vertical\src' '--ledger' '\\192.168.2.3\YNM\Projects\Vertical\ledger' '--projection' 'C:\Workspace\.tmp\vertical_revere_host_bound_authorization_working-apply.sqlite' '--expected-script-sha256' 'a29264709dab12d6cf96adb68b6234a4e686af7d3d8d994afda61f3c47764132' '--expected-work-order-sha256' 'd21a4c51a07293cb078252dcb1f811a6044fb82a5a2d9cb8257a2da09a2183f5' '--expected-addendum-sha256' '29feff5e1abe53569083ad89eecd64e884c3d477417987f2245eea47907753ac' '--expected-plan-sha256' 'dff2b7a05fd76dfcfe09a8719824253975983fb4ba7a1ac960ab4db25f04fea0' '--expected-rendered-event-plan-sha256' 'dbd686d9feb51cf2c606f6df7fb66782b8f4190251878ba759bff64ced77fbf6' '--expected-domain-head-event-uid' '01a1218f-fb1b-71f2-bdf2-6e3375596ec7' '--expected-domain-head-content-sha256' '45b356dbd893980f5c183789ebba37ced5686e5830535f830e7d9ad8e16d6692' '--expected-story-head-event-uid' '01a1218f-f9b9-7383-8373-68570e5044cc' '--expected-story-head-content-sha256' 'c04c6c1e9fd341e4dfed6a0a0cab141999de3caebfc96dc4cfcbe6408d4c0d97' '--expected-owner-stable-digest-sha256' '184e47fe2f4b7e34b3c6266e15a5ec062a249a08ec7f4d588f699289e14473b9' '--apply'

Command usability: C:\Workspace\.tmp exists; target projection absent; old/new commands parse; 66 tokens each; exactly token 43, the projection StringLiteral, changed; round-trip equality passed. Reviewed command SHA-256: 86ae35203bbb1736e28e0143602e0a71d43be93c160036d061a43e0481ba3d8d. It was NOT EXECUTED.

## Superseded/prohibited

Do not use the pre-fix ad6a3d... command, the command whose projection parent was deleted, synthetic f5e21a... as a live pin, or any unreviewed command variation. The live dbd686d9... rendered-plan pin was independently recaptured under final SHA a292647....

## Commands and provenance

Retained commands:

    powershell -NoProfile -Command 'python "C:\Workspace\.tmp\vr072_retained_qa_harness.py"'
    powershell -NoProfile -Command 'python "C:\Workspace\.tmp\vr072_schema_regression_harness.py"'

QA direct reads were blocked twice by managed ACL before PowerShell started, and the retry limit was honored. Eddie supplied retained exact commands/raw JSON. Ip Man independently verified disk hashes, AST, current source conformance, recursive ledger equality, and the corrected live recapture.

Temporary harness sources were deleted. No retained pre-fix source supported a binary diff, so review established current behavioral narrowness/conformance rather than byte-exclusive patch provenance.

## Cost and effort

QA model: GPT-5 family; exact variant and token/currency cost were not exposed. Other agent models/costs were not supplied. Implementation elapsed cost: unknown. Mandatory QA/governance elapsed cost: unknown. Their comparison is therefore unknown; no estimate is invented. Observable effort included implementation, fake/throwaway tests, one schema fix/regression, one incomplete live capture, one final recapture, and command-only path correction. No optional production-hardening scope was added.

## Final disposition

T1 PASS; T2 PASS; T3 PASS; T4 PASS; T5 PASS; T6 PASS; T7 PASS; T8 PASS; T9 PASS.

Overall PASS for the approved scope. This PASS does not authorize execution. Any later apply requires separate approval and must use the exact reviewed command only after all artifact, head, owner, freshness, and plan pins still pass.
