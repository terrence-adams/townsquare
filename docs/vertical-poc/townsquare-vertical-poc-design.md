# TownSquare Vertical-model tracking proof of concept

**document_id:** TS-VERTICAL-POC-DESIGN-20261006

**version:** 0.5-design

**status:** DESIGN DECISION FOR INTERNAL POC — NOT NATIVE VERTICAL ENFORCEMENT

**owner:** ip-man

**project:** TownSquare

**repository_baseline:** `6239f12da3dbedd24e9d4ef971c8995936d1db40`

**implementation_baseline:** `8dc6c11840e2bcfb3f1a307a40c110b1354c22e7`

**scope:** Internal, Git-tracked representation of current TownSquare work in the new Vertical model until native Vertical tracking is available.

**exclusions:** This note does not deploy TownSquare, create Vertical events, adopt governance, accept the MVP, enforce hierarchy or blockers, or authorize Stage 2.

## Decision

Track TownSquare through an append-only JSONL event ledger and generate a Markdown roadmap from it. The POC will model one Epic as a project-level goal-or-priority decision and every Feature and Story as a Vertical `unit-of-work`.

`VR-*` is only a stable, human-readable `poc_ref`. It is never an `event_uid`, `thread_uid`, concurrency token, or authoritative native link. Each POC record carries separate `poc_event_uid` and `poc_thread_uid` identities. Migration allocates native UUIDv7 `event_uid` and `thread_uid` values and preserves an explicit mapping from both POC identities to both native identities.

Vertical currently has no enforced Epic → Feature → Story hierarchy. Therefore `vertical_level`, `parent_ref`, and `depends_on_refs` are transparent POC body metadata only. `poc_event_uid` is the link inside the POC; native `event_uid` becomes authoritative only after successful native append and recorded migration mapping. No roadmap view, rollup, dependency marker, or owner field grants authority or changes native lifecycle state.

The POC artifacts will be added only after this design is independently reviewed. This note creates none of them. Their implementation and operation remain off the NAS deployment critical path: a tracker defect may fail this POC but must not block, approve, or alter TownSquare deployment.

## Product boundary and authority

TownSquare is the vendor-neutral, centralized coordination and record layer for transparent, traceable, auditable agentic interactions. It records what actors said, requested, decided, produced, and acknowledged, with stable evidence links. It does not encode a particular cloud, scheduler, wake tool, storage vendor, or model provider as doctrine.

The TownSquare Doctrine is the governing body of rules and guidance. TownSquare records its adoption and application but does not silently create governance authority.

Vertical is the work model and projection layer. It represents work, decisions, workflow state, and evidence using its own event identities and transition contracts. This POC is a temporary compatibility ledger for that model, not a second authority and not proof that native Vertical accepted an event.

Wonderland is a read-only downstream behavior observation and modeling layer. It may consume TownSquare and Vertical records to derive behavioral features, patterns, and analysis, but it cannot mutate their source records, authorize actions, satisfy gates, block transitions, close work, or become a hidden decision authority. Derived Wonderland outputs must retain source identity, time, content hash, and model/version provenance so an observation can be reproduced without being mistaken for source truth.

## Current deployment status

Deployment of the new MVP package is actively underway. The initial ledger must seed the following evidence-bounded status. Each active unit first receives its `OPEN` event and then a separate `WORKING` event; the table's operational wording is `delivery_status`, not a substitute lifecycle state.

The initial progress snapshot uses fixed `claimed_at: 2026-10-07T03:19:52Z` on its appended `WORKING` events. That value is the time this design recorded the snapshot, not the time the underlying work occurred and not store-assigned order. Subsequent status events receive their own checked, caller-supplied time.

| Work units | Status to seed | Evidence basis | Vertical treatment |
|---|---|---|---|
| Governance package `VR-060/061/062` | Candidate commit `6239f12da3dbedd24e9d4ef971c8995936d1db40`; Doctrine byte SHA-256 `2eb46ce715d4439e9410a2cedc64e9bac798024d22ad4a987f24bb4004ff047f`; Eddie Brock review returned `REWORK` and remains pending TownSquare ingestion and Kano disposition | `basis_kind: measured`; `basis_ref: artifact:docs/governance/reviews/eddie-brock-governance-review-6239f12-20261006.md#sha256=9a503268fd1c6180d25d4da822db8174ba2378ee7ed32f5795fd85005fead104`; review recorded `2026-10-07T03:10:26Z` | `WORKING`, `delivery_status: rework-required`; never adoption |
| Governance adoption `VR-063` | No protected operator adoption decision has been reported | `basis_kind: reported-by`; `basis_ref: codex-task:01a11131-3fdb-7e72-9084-c73e493a81cb` | `OPEN`; no adoption may be inferred |
| Portable release `VR-040/043` | Complete offline v4 archive exists with SHA-256 `33a793d73447ab16be90197ff78e997d1cf2a326ac1265fea52293626dd23328`; clean Compose parsing and runtime validation remain pending | `basis_kind: measured`; `basis_ref: artifact:../townsquare-v4-offline-6239f12da3db-r2-20261006.tar#sha256=33a793d73447ab16be90197ff78e997d1cf2a326ac1265fea52293626dd23328` | `WORKING`, `delivery_status: offline-artifact-assembled-validation-pending`; never runtime or acceptance proof |
| Recovery proof `VR-050/051` | Restore-drill reconciliation is in `REWORK`; no accepted restore/replay evidence exists | `basis_kind: reported-by`; `basis_ref: codex-task:01a11131-3fdb-7e72-9084-c73e493a81cb` | `WORKING`, `delivery_status: rework-required`; not `BLOCKED` without a valid gate-authored blocked-attempt |
| Backup exercise `VR-052` | Backup image payload is present in the offline archive, but no accepted executed backup, signature, restore, or replay evidence exists | `basis_kind: measured`; `basis_ref: artifact:../townsquare-v4-offline-6239f12da3db-r2-20261006.tar#sha256=33a793d73447ab16be90197ff78e997d1cf2a326ac1265fea52293626dd23328`; absence of runtime proof remains explicit | `WORKING`, `delivery_status: runtime-evidence-pending` |
| Deployment umbrella and dark-stack assembly `VR-070/072` | Compose parsing, dark start, migration, health, security, restore, replay, and degradation evidence are pending | `basis_kind: reported-by`; `basis_ref: codex-task:01a11131-3fdb-7e72-9084-c73e493a81cb` | `WORKING`, `delivery_status: runtime-evidence-pending` |
| Runtime conformance and fault testing `VR-073` | Waiting for a validated dark stack; no accepted execution evidence has been reported | `basis_kind: reported-by`; `basis_ref: codex-task:01a11131-3fdb-7e72-9084-c73e493a81cb` | `OPEN`, `delivery_status: not-started` |
| Cutover, native-writer activation, and bounded pilot `VR-074/075/076` | No operator cutover decision, activation, pilot start, or MVP acceptance has been reported | `basis_kind: reported-by`; `basis_ref: codex-task:01a11131-3fdb-7e72-9084-c73e493a81cb` | `OPEN`; no `RESOLVED` or `CLOSED` event |

An archive hash proves the bytes of that archive only. It is never clean Compose proof, container-runtime proof, cutover, recovery readiness, pilot readiness, or MVP acceptance. Manifest and backup evidence files remain templates or candidates until a row cites concrete executed evidence. No initial item is `RESOLVED` or `CLOSED`.

The last documented pre-cutover NAS footprint remains useful only as a dated baseline to revalidate during the active deployment: the frozen Registrar snapshot contained 1,070 posts, 197 artifacts, and 313 roots; Viewer was on port 8502; the Drive-backed Crier was on port 8787; and the existing Registry was on port 8789 with 25 agents. This note does not assert that each legacy fact remains live now.

## Proposed artifacts

The exact repository paths are:

- `docs/vertical-poc/townsquare-work-events.jsonl` — append-only machine-readable source of truth.
- `docs/vertical-poc/townsquare-work-event.schema.json` — POC validation schema.
- `docs/vertical-poc/README.md` — operating rules, field dictionary, transition rules, and migration procedure.
- `docs/townsquare-vertical-poc-roadmap.md` — generated human-readable projection.
- `tools/render-vertical-poc-roadmap.py` — deterministic projector; it must not mutate the event ledger.
- `tests/test_vertical_poc_roadmap.py` — schema, reference, transition-chain, and deterministic-render checks.
- `requirements/vertical-poc-win-amd64-cp312.lock.txt` — tracker-only, hash-locked Windows validation dependencies.
- `tools/bootstrap-vertical-poc.ps1` — offline, fail-atomic creation and preflight of the approved tracker environment.

The JSONL ledger is authoritative for this POC. The Markdown roadmap is disposable and must reproduce byte-for-byte from the ledger and pinned projector. Its primary work table must contain, in this fixed order: `Milestone`, `POC ref`, `Level`, `Title`, `Lifecycle`, `Delivery status`, `Evidence/basis`, `Review/gate`, `Next action`, `Reported at`, and `Owners (non-authoritative)`. The renderer may add summaries derived from those rows, but it may not omit these columns, query the current clock, or turn an owner, milestone, dependency, review, or next-action value into authority or lifecycle state.

Rendering is fail-atomic. Before producing any Markdown bytes, the renderer must read the complete ledger and complete schema, validate the schema against its declared meta-schema, reject duplicate keys, validate every event against the schema and canonicalization profile, recompute every hash, and validate all identities, global/per-thread ordering, workflow shape, permitted transitions, roles, required fields, evidence classifications, reference targets, chain heads, and seed invariants. It accumulates diagnostics but treats any single error as fatal: exit non-zero, create no roadmap when none existed, and leave an existing roadmap byte-for-byte unchanged. Only after the full validation pass succeeds may it render to a temporary file in the roadmap's directory, flush and close it, then atomically replace `docs/townsquare-vertical-poc-roadmap.md`. It may never stream a partial roadmap into the target.

### Pinned Windows validation runtime and offline bootstrap

The renderer is not permitted to depend on an ambient `python`, an inherited `PYTHONPATH`, or a package that merely happens to be installed. The sole supported Windows POC execution profile is `townsquare-vertical-poc-win-amd64-cp312/1`:

- CPython is exactly `3.12.14`, `sys.platform == "win32"`, pointer width is 64 bits, and `platform.machine()` is `AMD64`.
- The initially approved bootstrap interpreter is `C:\Users\terre\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`, whose measured byte SHA-256 is `b7a12c3af0b4db44191eec14ea095eba731b7328917f570806183093d19ddca2`. Bootstrap accepts a different `-PythonExe` only when all profile predicates and that exact executable hash match; it never searches `PATH`.
- Bootstrap creates the disposable, untracked repository-relative environment `.vertical-poc-venv`, and the only approved renderer locator after bootstrap is `.vertical-poc-venv\Scripts\python.exe`. The README command is that interpreter followed by `tools/render-vertical-poc-roadmap.py`; bare `python`, `py`, and direct script execution are unsupported.
- `requirements/vertical-poc-win-amd64-cp312.lock.txt` is the tracker-only hash lock, and `tools/bootstrap-vertical-poc.ps1` is the tracker-only offline bootstrap entry point. Neither file is a governance artifact, deployment input, or NAS runtime dependency.

The lock contains exactly these six wheels and hashes; no version range or alternate distribution is accepted:

| Wheel | SHA-256 |
|---|---|
| `attrs-26.1.0-py3-none-any.whl` | `c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309` |
| `jsonschema-4.26.0-py3-none-any.whl` | `d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce` |
| `jsonschema_specifications-2025.9.1-py3-none-any.whl` | `98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe` |
| `referencing-0.37.0-py3-none-any.whl` | `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231` |
| `rpds_py-2026.9.1-cp312-cp312-win_amd64.whl` | `5ce8943f79c2210f7abcc28e86367b03b28d95027fd01c46d2472373ae70c86f` |
| `typing_extensions-4.16.0-py3-none-any.whl` | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` |

The first five pure-Python wheel hashes and versions above are measured from the approved repository wheelhouse; the Windows `rpds_py` filename and hash are pinned from the PyPI release metadata at `https://pypi.org/pypi/rpds-py/2026.9.1/json`. The current Linux `rpds_py-2026.9.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` is not a Windows substitute. Until the exact Windows wheel is present, bootstrap must fail closed.

Bootstrap is offline and fail-atomic. It verifies the bootstrap interpreter and every listed wheel before invoking pip with `--no-index`, `--find-links wheelhouse`, `--require-hashes`, and `--only-binary=:all:`. Network fallback, source builds, compatible-version substitution, use of the general application requirements lock, and installation into the bootstrap interpreter are forbidden. It builds and self-tests a temporary sibling environment, verifies the six installed distribution versions plus a Draft 2020-12 meta-schema check, then renames that environment into `.vertical-poc-venv`. Any error leaves an existing approved environment unchanged and removes the temporary environment. The generated environment and downloaded wheel bytes are never committed as ledger or roadmap evidence.

The renderer performs dependency preflight before reading the schema, ledger, or target. It catches import and version errors and emits stable diagnostics rather than an import traceback. Exit `0` means validation and atomic render succeeded; exit `65` means the schema, ledger, workflow, seed, or projection contract is invalid and each stderr line begins `VERTICAL_POC_INVALID <code>:`; exit `78` means the execution profile or dependency preflight failed and each stderr line begins `VERTICAL_POC_CONFIG <code>:`; exit `70` means an unexpected internal failure and stderr begins `VERTICAL_POC_INTERNAL:`. Every non-zero exit preserves an existing roadmap byte-for-byte and creates no roadmap when it was absent. A renderer never bootstraps, installs, downloads, or modifies its environment.

## Vertical mapping and field dictionary

### Identity domains

The POC deliberately uses three identity domains and never overloads one for another:

| Identity | Shape | Purpose |
|---|---|---|
| `poc_ref` | `VR-<date>-<namespace>-<NNN>` | Stable human label, for example `VR-20261006-townsquare-010`; display/search only. |
| `poc_thread_uid` | `urn:townsquare:vertical-poc:thread:<uuidv7>` | Immutable POC thread identity. The prefix makes it syntactically distinct from a native bare UUIDv7. |
| `poc_event_uid` | `urn:townsquare:vertical-poc:event:<uuidv7>` | Immutable POC event identity and the target of references inside the POC ledger. The prefix makes it syntactically distinct from a native bare UUIDv7. |
| native `thread_uid` | bare UUIDv7 allocated by Vertical | Authoritative native Vertical thread identity after migration. It is never predeclared by this POC. |
| native `event_uid` | bare UUIDv7 allocated by Vertical | Authoritative native Vertical event identity after migration. It is never predeclared by this POC. |

Every POC event has one `poc_event_uid`; all events in its chain share one `poc_thread_uid`; only the opening event carries the chain's `poc_ref`. Later events resolve to that opening by thread identity. POC cross-references use `poc_event_uid`. During migration, the adapter translates each POC reference to the mapped native `event_uid` before append.

The ledger begins with a POC representation of the exact workflow-definition decision that governs this tracker. It has `poc_ref: VR-20261006-townsquare-000`, `event_type: decision`, `decision_type: workflow-definition`, routing `state: RECORDED`, `target: workflow`, and the pinned workflow object below. Its `basis_kind` is `measured`; its `basis_ref` is the content-addressed reviewed design in the form `artifact:docs/vertical-poc/townsquare-vertical-poc-design.md#sha256=<reviewed-design-byte-sha256>`, with the reviewed Git commit/path also recorded in `evidence_refs`. The implementation must obtain that digest from the completed independent design-review handoff and verify it against the file before generating the ledger. The generated README or roadmap may not be the workflow decision's basis. Every `OPEN` work item has a `workflow_ref` resolving to that record's `poc_event_uid`. Validation fails if the workflow record is absent, duplicated, superseded without an explicit migration event, or unresolvable. The workflow record is a native-shaped decision, so it does not misuse the `unit-of-work`-only `artifact_ref` field.

### Pinned workflow definition

The workflow decision carries these fields with these exact types and values:

```json
{
  "workflow_profile": "townsquare-vertical-poc-workflow/1",
  "workflow_states": ["OPEN", "WORKING", "BLOCKED", "RESOLVED", "CLOSED", "CANCELLED"],
  "workflow_initial_state": "OPEN",
  "workflow_terminal_states": ["CLOSED", "CANCELLED"],
  "workflow_transitions": [
    {"transition_id":"OPEN->WORKING","from_state":"OPEN","to_state":"WORKING","allowed_roles":["implementer"],"required_fields":["reason_category","reason_text"],"requirements":[],"validators":["system-forward-reason"]},
    {"transition_id":"OPEN->BLOCKED","from_state":"OPEN","to_state":"BLOCKED","allowed_roles":["implementer"],"required_fields":["blocked_attempt_ref","reason_category","reason_text","reason_trigger_ref"],"requirements":[],"validators":["blocked-attempt-valid","explicit-reason"]},
    {"transition_id":"OPEN->CANCELLED","from_state":"OPEN","to_state":"CANCELLED","allowed_roles":["implementer","project-owner"],"required_fields":["reason_category","reason_text"],"requirements":[],"validators":["explicit-reason"]},
    {"transition_id":"WORKING->BLOCKED","from_state":"WORKING","to_state":"BLOCKED","allowed_roles":["implementer"],"required_fields":["blocked_attempt_ref","reason_category","reason_text","reason_trigger_ref"],"requirements":[],"validators":["blocked-attempt-valid","explicit-reason"]},
    {"transition_id":"WORKING->RESOLVED","from_state":"WORKING","to_state":"RESOLVED","allowed_roles":["implementer"],"required_fields":["artifact_ref","cites_decision","evidence_refs","reason_category","reason_text"],"requirements":[{"role":"architect","artifact_type":"design-of-record"}],"validators":["artifact-and-design-decision-current","system-forward-reason"]},
    {"transition_id":"WORKING->CANCELLED","from_state":"WORKING","to_state":"CANCELLED","allowed_roles":["implementer","project-owner"],"required_fields":["reason_category","reason_text"],"requirements":[],"validators":["explicit-reason"]},
    {"transition_id":"BLOCKED->WORKING","from_state":"BLOCKED","to_state":"WORKING","allowed_roles":["implementer"],"required_fields":["clears_blocked_attempt_ref","evidence_refs","reason_category","reason_text"],"requirements":[],"validators":["all-blocked-conditions-cleared","system-forward-reason"]},
    {"transition_id":"BLOCKED->CANCELLED","from_state":"BLOCKED","to_state":"CANCELLED","allowed_roles":["implementer","project-owner"],"required_fields":["reason_category","reason_text"],"requirements":[],"validators":["explicit-reason"]},
    {"transition_id":"RESOLVED->WORKING","from_state":"RESOLVED","to_state":"WORKING","allowed_roles":["project-owner"],"required_fields":["reason_category","reason_text","reason_trigger_ref"],"requirements":[],"validators":["review-trigger-valid","explicit-reason"]},
    {"transition_id":"RESOLVED->CLOSED","from_state":"RESOLVED","to_state":"CLOSED","allowed_roles":["project-owner"],"required_fields":["cites_decision","evidence_refs","reason_category","reason_text"],"requirements":[{"role":"architect","artifact_type":"design-of-record"},{"role":"architect","artifact_type":"conformance-ruling"}],"validators":["acceptance-decision-current","independent-acceptance","system-forward-reason"]},
    {"transition_id":"RESOLVED->CANCELLED","from_state":"RESOLVED","to_state":"CANCELLED","allowed_roles":["project-owner"],"required_fields":["reason_category","reason_text"],"requirements":[],"validators":["explicit-reason"]}
  ]
}
```

`workflow_transitions` is populated by the complete matrix below. Each entry is an object with exactly these keys: `transition_id` (the literal `<from_state>-><to_state>`), `from_state`, `to_state`, `allowed_roles` (non-empty unique list drawn from `implementer` and `project-owner`), `required_fields` (unique field-name list), `requirements` (unique list of native-shaped `{"role":"<role>","artifact_type":"<decision_type>"}` objects), and `validators` (unique list of the closed validator tokens defined in the matrix). Lists retain the order shown. No unlisted ordinary transition is valid, and terminal states have no outgoing ordinary edge.

All transitions also require `role_acted_under`, `claimed_at`, `basis_kind`, `basis_ref`, `base_event_id`, and `expected_head`; those common fields are not repeated in each row. `system-forward-reason` requires gate-generated `reason_category` and `reason_text`. `explicit-reason` requires actor-supplied `reason_category` and `reason_text`; `reason_trigger_ref` is additionally mandatory for `downstream-constraint` and `dependency-change`.

| Transition | Allowed roles | Additional required fields | Citation/evidence rule | Native decision requirements | Validators |
|---|---|---|---|---|---|
| `OPEN->WORKING` | `implementer` | `reason_category`, `reason_text` | No cross-thread citation; basis still required | `[]` | `system-forward-reason` |
| `OPEN->BLOCKED` | `implementer` | `blocked_attempt_ref`, `reason_category`, `reason_text`, `reason_trigger_ref` | Both references name the same earlier gate-authored blocked-attempt | `[]` | `blocked-attempt-valid`, `explicit-reason` |
| `OPEN->CANCELLED` | `implementer`, `project-owner` | `reason_category`, `reason_text` | No citation unless the selected reason category requires `reason_trigger_ref` | `[]` | `explicit-reason` |
| `WORKING->BLOCKED` | `implementer` | `blocked_attempt_ref`, `reason_category`, `reason_text`, `reason_trigger_ref` | Both references name the same earlier gate-authored blocked-attempt | `[]` | `blocked-attempt-valid`, `explicit-reason` |
| `WORKING->RESOLVED` | `implementer` | `artifact_ref`, `cites_decision`, `evidence_refs`, `reason_category`, `reason_text` | Artifact is content-addressed; `cites_decision` names the current design-of-record; evidence lists supporting events | `[{"role":"architect","artifact_type":"design-of-record"}]` | `artifact-and-design-decision-current`, `system-forward-reason` |
| `WORKING->CANCELLED` | `implementer`, `project-owner` | `reason_category`, `reason_text` | No citation unless the selected reason category requires `reason_trigger_ref` | `[]` | `explicit-reason` |
| `BLOCKED->WORKING` | `implementer` | `clears_blocked_attempt_ref`, `evidence_refs`, `reason_category`, `reason_text` | Clearance names the current blocked-attempt; evidence names every satisfying decision | `[]` | `all-blocked-conditions-cleared`, `system-forward-reason` |
| `BLOCKED->CANCELLED` | `implementer`, `project-owner` | `reason_category`, `reason_text` | No citation unless the selected reason category requires `reason_trigger_ref` | `[]` | `explicit-reason` |
| `RESOLVED->WORKING` | `project-owner` | `reason_category`, `reason_text`, `reason_trigger_ref` | Trigger names the earlier review finding, rejected acceptance, or conformance decision requiring rework | `[]` | `review-trigger-valid`, `explicit-reason` |
| `RESOLVED->CLOSED` | `project-owner` | `cites_decision`, `evidence_refs`, `reason_category`, `reason_text` | Citation names the current authorized acceptance; evidence names current design-of-record and conformance-ruling | `[{"role":"architect","artifact_type":"design-of-record"},{"role":"architect","artifact_type":"conformance-ruling"}]` | `acceptance-decision-current`, `independent-acceptance`, `system-forward-reason` |
| `RESOLVED->CANCELLED` | `project-owner` | `reason_category`, `reason_text` | No citation unless the selected reason category requires `reason_trigger_ref` | `[]` | `explicit-reason` |

Validator meanings are closed, not implementation-defined: `blocked-attempt-valid` requires `blocked_attempt_ref == reason_trigger_ref` and a referenced, earlier, gate-authored `blocked-attempt` covering this work item and attempted edge; `all-blocked-conditions-cleared` requires `clears_blocked_attempt_ref` to name the current block and every listed `condition_id` to have an earlier satisfying decision in `evidence_refs`; `artifact-and-design-decision-current` requires a resolvable artifact and current architect `design-of-record` for this work opening; `review-trigger-valid` requires an earlier review finding, rejected acceptance, or conformance decision concerning this work opening; `acceptance-decision-current` requires `cites_decision` to name a current authorized acceptance decision for this work opening; `independent-acceptance` rejects the implementation author as sole acceptance actor; and the two reason validators enforce the reason rules above. Requirements and validators are cumulative.

### Required event headers

| Field | Rule |
|---|---|
| `schema_version` | Required literal string `"1"`, matching the target Vertical POC schema. |
| `poc_ref` | Required on an opening event; stable `VR-*` display/reference label only. Never presented as a Vertical identity. |
| `poc_event_uid` | Required unique POC event identity in the prefixed form above. POC cross-references resolve against this field. |
| `poc_thread_uid` | Required POC thread identity in the prefixed form above. Opening and transition events in one chain share it. |
| `poc_seq` | Required zero-based, dense order within `poc_thread_uid`; opening is `0`. |
| `poc_global_order` | Required zero-based, dense order matching the JSONL line order. It preserves deterministic replay order without pretending to be Vertical's store-allocated `global_seq`. |
| `poc_content_sha256` | Required lowercase SHA-256 over the canonical POC event defined below. Migration preserves this source hash in the map and separately records Vertical's native `content_sha256`; identity translation means the two hashes need not match. |
| `canonicalization_profile` | Required literal `rfc8785+townsquare-vertical-poc-safeint/1`. Any other or absent profile is invalid. |
| `event_type` | Feature and Story openings use the exact native token `unit-of-work`. The Epic and POC workflow record use the exact native token `decision`. |
| `project` | `townsquare`. |
| `state` | Required routing state. Fact threads use `RECORDED`; work threads use one of the workflow's declared lifecycle states. |
| `actor` | Actor creating the event. |
| `actor_provenance` | Required JSON **string**, not an object: a serialized snapshot containing `provider`, `model_id`, `model_family`, `runtime`, `runtime_version`, `host`, `agent_name`, and `basis`. |
| `role_acted_under` | Required on every `unit-of-work` event. An opening declares `project-owner`; `WORKING` and `RESOLVED` declare the actor's implementer role; `CLOSED` declares `project-owner`. It is a claim checked during migration, not self-certifying authority. |
| `claimed_at` | Required fixed RFC3339 timestamp with an explicit offset on every POC event. It is the actor's reported time, not a store clock or ordering authority. The seed process must receive it as checked input; neither schema validation nor rendering may substitute the current time. |
| `basis_kind` | Required epistemic classification: `measured`, `inferred`, `assumed`, or `reported-by`. Status used for a gate or acceptance view must be `measured` or visibly remain unverified. |
| `basis_ref` | Required resolvable evidence locator for `measured` and `reported-by`; optional only for `inferred` or `assumed`. A `measured` reference must be immutable and content-addressed with a lowercase 64-hex SHA-256 or a full Git commit plus path; a mutable path, branch, tag, latest alias, owner, or agent name alone is invalid. Task/session reports use `reported-by`, not `measured`. |
| `base_event_id` | Required on every POC transition; names the immediately preceding `poc_event_uid`. Omitted on an opening event. Migration translates it to the immediately preceding native `event_uid`. |
| `expected_head` | Required alongside `base_event_id` on every POC transition and equal to it. Omitted on an opening event. Migration supplies the translated native value to Vertical's compare-and-append operation; it is not merely descriptive metadata. |

### Canonical JSONL and native serialization

1. The pinned profile is `rfc8785+townsquare-vertical-poc-safeint/1`: RFC 8785 JSON Canonicalization Scheme is normative, with the additional input restrictions in this section. A later profile is a new reviewed workflow version, never an implicit library upgrade.
2. The ledger is strict UTF-8 without a BOM, contains exactly one top-level JSON object per physical line, uses LF (`0x0A`) line endings, and ends with one LF. Literal CR bytes, invalid UTF-8, lone Unicode surrogates, and duplicate object keys at any nesting depth are rejected before schema or hash validation. Parsers must use a duplicate-detecting object-pairs hook or equivalent; last-key-wins parsing is forbidden.
3. JSON numeric values are integers only: floating-point, decimal, exponent, `NaN`, and infinity forms are invalid. Booleans are not integers. Every integer is in the interoperable exact JSON range `-9007199254740991..9007199254740991`; `poc_seq` and `poc_global_order` are specifically JSON integers in `0..9007199254740991`. Both sequences are dense, start at zero in their declared domain, and may not be encoded as strings.
4. To calculate `poc_content_sha256`, remove only `poc_content_sha256` from the already duplicate-checked, schema-valid event object, canonicalize the remaining complete object under the pinned profile, and hash those exact UTF-8 bytes with no trailing newline. The stored lowercase hexadecimal digest must match. Array order is significant. No path, platform newline, locale, parser insertion order, or wall-clock value participates implicitly.
5. The POC keeps naturally structured fields such as `definition_of_done`, `workflow_states`, `workflow_transitions`, and other declared variable-length shapes as JSON arrays or objects so the schema can validate them. On native Vertical migration, the adapter canonicalizes each such value under the same pinned profile and writes those bytes as the native header's required JSON **string**. `actor_provenance` is already a JSON string and must be parsed with duplicate detection for its embedded object, validated, then re-emitted once; it must not be double encoded.
6. Native migration then allows Vertical to compute its own `content_sha256` over the translated native envelope. The POC and native hashes are separate evidence and are never asserted equal.

### Reference order and one-pass migration invariant

Every field containing a POC `poc_event_uid` is validated as a reference, including `workflow_ref`, `parent_ref`, `depends_on_refs`, `base_event_id`, `expected_head`, `cites_decision`, POC-valued `evidence_refs`, `blocked_attempt_ref`, `clears_blocked_attempt_ref`, `reason_trigger_ref`, and any TownSquare source link expressed in the POC identity domain. The target event must exist and have a strictly smaller `poc_global_order` than the referring event; therefore its thread opening also has an earlier order. Forward references and cycles are invalid. Same-thread `base_event_id` and `expected_head` retain the stronger rule that both equal the immediately preceding event. External content-addressed or task references are not POC event references and do not participate in this ordering rule.

This earlier-target invariant is the chosen migration design; no two-phase fix-up is permitted. A native migration processes valid POC events once in ascending `poc_global_order`, opens or appends the corresponding native thread, and records each native mapping before the next event. Every translated reference must already exist in the map; otherwise migration aborts before the next write.

### Native lifecycle body fields

| Field | Rule |
|---|---|
| `goal` | Required on `OPEN`. |
| `definition_of_done` | Required JSON **list** of short checklist-item strings on `OPEN`; never a free-text paragraph or object. |
| `workflow_ref` | Required on every `OPEN`; resolves to the `poc_event_uid` of the current POC workflow-definition decision. Migration translates it to that decision's native `event_uid`. |
| `artifact_ref` | Required for `RESOLVED`; points to implementation or other outcome evidence. It may also carry the TownSquare source opening hash. |
| `cites_decision` | Required for `RESOLVED` and `CLOSED`. On `CLOSED`, it must cite the authorized acceptance decision. |
| `blocked_attempt_ref` | Required on `BLOCKED`; cites the earlier gate-authored blocked-attempt event for this work item and attempted transition. |
| `clears_blocked_attempt_ref` | Required on `BLOCKED->WORKING`; cites the current blocked-attempt being cleared. |
| `reason_category`, `reason_text`, `reason_trigger_ref` | Required according to the pinned transition matrix. `reason_text` is single-line; the trigger is a POC event reference when present. |

### POC metadata: visible but non-enforced

| Field | Meaning |
|---|---|
| `vertical_level` | `Feature` or `Story`; display grouping only. |
| `parent_ref` | Opening `poc_event_uid` of the display parent; not an enforced hierarchy. |
| `depends_on_refs` | Opening `poc_event_uid` values for transparent sequencing; not a cross-story blocker mechanism. |
| `phase` | `MVP` or `VERTICAL_STAGE_2`. |
| `owner` | Accountable owner; assignment metadata, not authorization. |
| `creation_owner` | Who drafts or opens the deliverable. Informational assignment only; it grants no authorship permission or governance authority. |
| `fulfillment_owner` | Who produces the evidence or implementation. Informational assignment only. |
| `review_owner` | Who performs the named independent review. A name does not waive the applicable workflow or evidence requirement. |
| `operator_acceptance_owner` | Always the operator for program-deliverable acceptance. This identifies the required human decision-maker; the field itself does not create or simulate an acceptance decision. |
| `delivery_status` | Operational nuance such as `not-started`, `source-implemented`, `independent-review-in-progress`, `rework-required`, `offline-artifact-assembled-validation-pending`, or `runtime-evidence-pending`; not a Vertical lifecycle state. `REWORK` is represented here unless a valid lifecycle transition says otherwise. |
| `acceptance_refs` | Stable criteria IDs from `docs/townsquare-mvp-v0-design-20261006.md`. |
| `evidence_refs` | Commits, paths, hashes, tests, and runtime evidence. |
| `current_gate` | Short visible description of the review or decision presently owed. Informational only; it cannot block or authorize a transition. |
| `next_action` | Short visible description of the next intended action. Informational only; it cannot assign authority or satisfy a workflow condition. |
| `townsquare_thread_ref` | Existing TownSquare thread reference when one exists. |
| `townsquare_opening_sha256` | Hash of the corresponding TownSquare opening/source record. It supplements, never replaces, either POC or native identity. |

## Lifecycle and status rules

1. A Feature or Story chain begins with an `OPEN` `unit-of-work` event containing `role_acted_under: project-owner`, `goal`, a JSON-list `definition_of_done`, and a `workflow_ref` that resolves to the POC workflow-definition record.
2. Work already underway appends a distinct `WORKING` event. It has a new `poc_event_uid`, the same `poc_thread_uid`, the next dense `poc_seq`, the implementer's `role_acted_under`, fixed `claimed_at`, evidence basis, and `base_event_id == expected_head ==` the immediately preceding event. It may update `delivery_status`, `evidence_refs`, `current_gate`, and `next_action`; it may not rewrite the opening event.
3. The projection takes lifecycle state from the last event in each dense, valid thread. For operational columns it takes the latest explicitly supplied value in that same thread, falling back toward the opening event; absence renders `UNKNOWN`, never a guessed value. `Reported at` is that projected event's fixed `claimed_at`. Renderer execution time is never displayed as work time.
4. An outcome with sufficient evidence appends a `RESOLVED` transition. It receives its own `poc_event_uid`, names the immediately preceding POC event in both `base_event_id` and `expected_head`, supplies a concrete `artifact_ref`, and cites a concrete resolution decision through `cites_decision`.
5. Acceptance appends `CLOSED` only after an authorized acceptance decision. It must cite that decision, supply both concurrency fields naming the immediately preceding POC event, and later migrate with compare-and-append.
6. `source-implemented`, `independent-review-in-progress`, `rework-required`, `offline-artifact-assembled-validation-pending`, and `runtime-evidence-pending` are `delivery_status` values, not Vertical lifecycle states. `REWORK` does not become `BLOCKED`; a `BLOCKED` lifecycle event is valid only with the gate-authored blocker evidence required by the workflow.
7. Source or package existence may support `WORKING` and a delivery status, but never invents a `RESOLVED` or `CLOSED` decision. The initial ledger contains no `RESOLVED` or `CLOSED` item.
8. Feature rollups are projections only. A child transition does not mechanically transition its Feature. `parent_ref` and `depends_on_refs` can never authorize or prevent a transition, supply workflow requirements, block work, roll up state, or close any item.

## Work inventory

The `VR-*` references below are `poc_ref` labels, not opening-event IDs. The implementation allocates separate prefixed POC thread/event identities. Later transition events receive new `poc_event_uid` values and chain through both `base_event_id` and `expected_head`.

Every Feature and Story listed below first receives an `OPEN` `unit-of-work` event and must carry a `workflow_ref` resolving to `VR-20261006-townsquare-000`'s `poc_event_uid`. A unit identified as active by the measured seed table then receives a separate `WORKING` event under the rules above. Narrative shorthand in this inventory states the chain's opening state unless it explicitly names a later transition; it never waives either event or field.

### Epic

**`VR-20261006-townsquare-001` — Deliver and accept the NAS-first TownSquare MVP, then enter Vertical Stage 2**

- Native-shape representation: `event_type: decision`, `decision_type: goal-or-priority`, native record status `RECORDED` (Vertical's routing `state` field), and **no** `unit_of_work_ref`. It is a fact thread, not `unit-of-work`; the decision header named `status` is omitted because that derived field applies only to rule-set adoption/amendment.
- POC phase status: active.
- Owner: operator; Helio coordinates gates.
- Outcome: authoritative native ledger, governed writes, Registry, read surfaces, recovery, NAS activation, and bounded pilot, followed by separately gated Stage 2.
- Acceptance: an operator acceptance decision after the required core MVP criteria and bounded-pilot evidence pass.
- Evidence: `d7cc247`, `docs/townsquare-mvp-v0-design-20261006.md`.

### MVP Feature 1 — Native ledger and governed lifecycle

**`VR-20261006-townsquare-010` — Native ledger and governed lifecycle — `OPEN`**

- Owner: Bruce Lee. Parent metadata: `VR-20261006-townsquare-001`.
- Delivery status: `source-implemented`; no concrete `cites_decision` is recorded, so this is not `RESOLVED`.
- Outcome/DoD: immutable native content/envelopes, Request lifecycle, archive, exact context retrieval, receipts, authority, idempotency, and crash atomicity; MVP-LDG-01–10, MVP-CMP-01–08, and MVP-ARC-01.
- Evidence: `4983c11`, `27c98ca`, `768fc0b`, `3818dee`, `7eea350`; migrations 010–014; Registrar native-ledger, lifecycle, context, governed-write, security, and conformance tests.

Stories:

- **`VR-20261006-townsquare-011` — Immutable native event/content core — `OPEN`; `delivery_status: source-implemented`.** Owner Bruce. DoD: canonical hashes, monotonic sequence, immutable envelope/content pairing, idempotent requests, and all-or-none transaction behavior. Reported evidence candidates: `4983c11` and native-ledger tests; no resolution decision is yet cited.
- **`VR-20261006-townsquare-012` — Governed Request lifecycle and archive — `OPEN`; `delivery_status: source-implemented`.** Owner Bruce. Depends metadata on `VR-20261006-townsquare-011`. DoD: valid lifecycle succeeds; wrong actor, self-close, terminal reopen, and unauthorized override fail; logical archive preserves history. Reported evidence candidates: `3818dee`, `7eea350`, lifecycle and security tests; no resolution decision is yet cited.
- **`VR-20261006-townsquare-013` — Context, receipt, and authority enforcement — `OPEN`; `delivery_status: source-implemented`.** Owner Bruce. Depends metadata on `VR-20261006-townsquare-011`. DoD: exact selected/retrieved context, action-bound single-use receipts, detached external authority proof, and reconstructable audit. Reported evidence candidates: `768fc0b`, `1b0e315`, context and governed-write tests; no resolution decision is yet cited.

### MVP Feature 2 — Agent Registry integration

**`VR-20261006-townsquare-020` — Registry integration — `OPEN`**

- Owner: Bruce Lee. Parent metadata: Epic.
- Delivery status: `source-implemented`; no concrete `cites_decision` is recorded, so this is not `RESOLVED`.
- Outcome/DoD: schema-2 Registry, durable journal/outbox, exactly-once Ledger audit delivery, and authenticated compatibility; MVP-REG-01–03 and MVP-OPS-11.
- Evidence: `8235a59`, `b308f21`, `4684276`, `91fd48c`, `ca6eaee`; Registry and conformance release suites.

Stories:

- **`VR-20261006-townsquare-021` — Registry roster lifecycle — `OPEN`; `delivery_status: source-implemented`.** DoD: register, update, retire, query; retirement never deletes history.
- **`VR-20261006-townsquare-022` — Atomic audit outbox and delivery acknowledgement — `OPEN`; `delivery_status: source-implemented`.** DoD: mutation/outbox atomicity, retry without duplicates, production-boundary acknowledgement. Reported evidence candidates: `b308f21`, `ca6eaee`; no resolution decision is yet cited.
- **`VR-20261006-townsquare-023` — Directional peer readiness — `OPEN`; `delivery_status: source-implemented`.** DoD: distinct credentials and exact Ledger/Registry/audit-contract tuple fail closed when wrong or missing. Reported evidence candidates: `4684276`, `91fd48c`; no resolution decision is yet cited.

### MVP Feature 3 — Read surfaces and notices

**`VR-20261006-townsquare-030` — Viewer, Crier, and projections — `OPEN`**

- Owner: Chuck Norris for Viewer; Bruce Lee for ledger projections.
- Delivery status: `source-implemented`; no concrete `cites_decision` is recorded, so this is not `RESOLVED`.
- Outcome/DoD: read-only human views, deterministic projections, honest degraded state, and durable pointer notices; MVP-READ-01–03 and MVP-NTF-01–04.
- Evidence: `bcfef94`, `a0c6ef9`; Viewer, tracker, Registrar Crier, and notice tests.

Stories:

- **`VR-20261006-townsquare-031` — Native/historical Viewer boundary — `OPEN`; `delivery_status: source-implemented`.** Owner Chuck. DoD: native authority and historical metadata are distinguishable; Viewer cannot write.
- **`VR-20261006-townsquare-032` — Deterministic project/Crier projections — `OPEN`; `delivery_status: source-implemented`.** Owner Bruce. DoD: repeated projections are byte-identical and dependency loss renders UNKNOWN/DEGRADED.
- **`VR-20261006-townsquare-033` — Durable notice intents and attempts — `OPEN`; `delivery_status: source-implemented`.** Owner Bruce. DoD: pointer-only immutable intent/attempt history without shipping a notifier in the core profile.

### MVP Feature 4 — Secure portable release

**`VR-20261006-townsquare-040` — Secure portable release package — opens `OPEN`, then appends `WORKING`**

- Owner: Francis Ngannou. Depends metadata on `VR-20261006-townsquare-010`, `VR-20261006-townsquare-020`, and `VR-20261006-townsquare-030`.
- Delivery status: `offline-artifact-assembled-validation-pending`. Evidence includes archive SHA-256 `33a793d73447ab16be90197ff78e997d1cf2a326ac1265fea52293626dd23328`; clean Compose parsing, image/config/SBOM reconciliation, and runtime evidence remain pending.
- Outcome/DoD: exact digest-pinned release, offline reproducible build evidence, hardened Compose, and complete runtime security proof; MVP-PKG-01, MVP-PORT-01, MVP-OPS-01/02/09–11, and MVP-SEC-01–13.

Stories:

- **`VR-20261006-townsquare-041` — Compose, migrator, and container hardening contract — `OPEN`; `delivery_status: source-implemented`.** Reported evidence candidates: `7756488`, `8235a59`, `cac8007`, release-blocker tests; no resolution decision is yet cited.
- **`VR-20261006-townsquare-042` — Offline build inputs and supply-chain tooling — `OPEN`; `delivery_status: source-implemented`.** Reported evidence candidates: `24ee012`, `22a97f7`, offline-build tests; no resolution decision is yet cited.
- **`VR-20261006-townsquare-043` — Build and pin the exact release images — opens `OPEN`, then appends `WORKING`.** Delivery status: `offline-artifact-assembled-validation-pending`; the archive hash proves the package bytes but not clean Compose, manifest reconciliation, or runtime behavior. DoD: all images built, manifest image/config/SBOM digests resolved, clean Compose config recorded, no mutable tags. Candidate manifest files are not proof until their values and evidence locator are captured from the executed build.
- **`VR-20261006-townsquare-044` — Runtime security evidence — `OPEN`.** Owner GSP. Depends metadata on `VR-20261006-townsquare-043`. DoD: permissions, secrets, capability matrix, network confinement, inert rendering, CSP, limits, and external probes pass against the assembled release.

### MVP Feature 5 — Backup, restore, and rollback

**`VR-20261006-townsquare-050` — Recovery proof — opens `OPEN`, then appends `WORKING`**

- Owner: Francis Ngannou.
- Delivery status: `rework-required`; restore-drill reconciliation has not passed review and no executed recovery evidence is accepted.
- Outcome/DoD: encrypted, signed, externally anchored backups; separate domain restores; production-boundary replay; safe rollback; MVP-OPS-03–08 and MVP-SEC-09.

Stories:

- **`VR-20261006-townsquare-051` — Isolated restore and separate replay tooling — opens `OPEN`, then appends `WORKING`; `delivery_status: rework-required`.** Reported evidence candidates: `67e89eb`, `e3903df`, `ca6eaee`, recovery suites; reconciliation is still owed and no resolution decision is cited.
- **`VR-20261006-townsquare-052` — Build and exercise the Backup image — opens `OPEN`, then appends `WORKING`.** Delivery status: `runtime-evidence-pending`. The offline archive contains the Backup payload; that does not prove an executed backup, signature, external checkpoint, empty-directory restore, or exactly-once replay. Depends metadata on `VR-20261006-townsquare-043`.
- **`VR-20261006-townsquare-053` — Pre-write and post-write rollback rehearsal — `OPEN`.** Depends metadata on `VR-20261006-townsquare-052`. DoD: pre-write rollback preserves data; post-write rollback stops writes and preserves the new ledger for forward repair.

### MVP Feature 6 — Governance activation

**`VR-20261006-townsquare-060` — Complete and adopt Doctrine, Rules of Engagement, and TownSquare governance — opens `OPEN`, then appends `WORKING`**

- Creation and fulfillment owner: Jigoro Kano. Review owners: GSP and Ip Man. Operator remains the only acceptance owner. These assignments do not grant authority or constitute adoption.
- Delivery status: `rework-required`. Eddie Brock's review of commit `6239f12da3dbedd24e9d4ef971c8995936d1db40` returned REWORK; it is a review result pending ingestion and Kano disposition, not an adoption decision.
- Outcome/DoD: vendor-neutral Doctrine, Rules of Engagement, TownSquare governance, binding, workflow, scope/work order, notes, and acceptance documents are internally consistent and externally adopted with protected, current scope/authority evidence.

Stories:

- **`VR-20261006-townsquare-061` — Pin exact governing sources and hashes — opens `OPEN`, then appends `WORKING`.** The candidate commit and Doctrine byte hash are pinned above; the review found additional traceability and readiness work. Candidate status is not adoption.
- **`VR-20261006-townsquare-062` — Review authority, expiry, revocation, and scope — opens `OPEN`, then appends `WORKING`; `delivery_status: rework-required`.** Depends metadata on `VR-20261006-townsquare-061`; Eddie's recorded objections require Kano disposition.
- **`VR-20261006-townsquare-063` — Record protected operator adoption — `OPEN`.** Depends metadata on `VR-20261006-townsquare-062`; only the operator can complete it.

### MVP Feature 7 — NAS deployment, cutover, and acceptance

**`VR-20261006-townsquare-070` — Deploy and accept the MVP — opens `OPEN`, then appends `WORKING`**

- Owner: Francis Ngannou for deployment; Ronda Rousey for QA; operator for activation and acceptance.
- Delivery status: `runtime-evidence-pending`; the offline artifact exists, but Compose/runtime validation, recovery proof, and cutover evidence do not.
- Depends metadata on `VR-20261006-townsquare-040`, `VR-20261006-townsquare-050`, and `VR-20261006-townsquare-060`.
- Outcome/DoD: pinned dark deployment, live conformance/recovery evidence, operator-approved activation, and bounded pilot. Every core MVP acceptance row except the explicitly excluded wake rows must pass.

Stories:

- **`VR-20261006-townsquare-071` — Revalidate the NAS and legacy baseline — `OPEN`.** DoD: capture current host, storage, containers, sockets, firewall/NAT, selected ports, and existing-service state. Historical facts are not silently carried forward.
- **`VR-20261006-townsquare-072` — Assemble and start the dark stack — opens `OPEN`, then appends `WORKING`.** Delivery status: `runtime-evidence-pending`. The exact offline archive is assembled; Compose parsing, dark start, domain migration, runtime schemas, and directional compatibility still require concrete evidence locators.
- **`VR-20261006-townsquare-073` — Execute runtime conformance and fault testing — `OPEN`; `delivery_status: not-started`.** Owner Ronda. DoD: source, container, restart, migration, security, stop, backup, restore, replay, and degradation suites produce pinned evidence.
- **`VR-20261006-townsquare-074` — Approve exact cutover — `OPEN`.** Owner operator. DoD: decision cites exact SHA, image digests, commands, ports, transport mode, trust material, rollback boundary, and cutover moment.
- **`VR-20261006-townsquare-075` — Activate constrained native writers — `OPEN`.** Depends metadata on `VR-20261006-townsquare-074`. DoD: loopback/SSH-tunnel profile enabled, Drive removed from normal runtime authority, legacy source preserved as historical fallback.
- **`VR-20261006-townsquare-076` — Complete the 2–4 week bounded pilot and accept MVP — `OPEN`.** DoD: pilot start and cohort are pinned; day-0, day-7, and day-14 evidence are recorded; the operator either accepts at two weeks or explicitly extends to day 28; any selected day-28 evidence is recorded; known gaps become visible roadmap items; an operator acceptance decision is required for `CLOSED`.

## Program Milestones 0–5

Milestones are reporting projections over native-shaped work records, not lifecycle states or an enforced hierarchy. A milestone label, `parent_ref`, dependency marker, or named owner cannot open, block, transition, roll up, resolve, or close work. Only the pinned workflow and an explicit event/decision can do that. The tracker records every workstream below, but tracker completion is not a precondition for NAS deployment unless the applicable deployment work item's own reviewed DoD says so.

| Milestone | Outcome | Native-shaped units tracked | Exit evidence |
|---|---|---|---|
| 0 — Program contract | Fix product boundaries, POC workflow, identity, evidence classes, owners, and acceptance rules | Epic `VR-20261006-townsquare-001`; workflow decision `VR-20261006-townsquare-000`; this reviewed design | Reviewed design decision and resolvable workflow record; no implied deployment approval |
| 1 — Deployable MVP | Produce and verify the MVP deployment, recovery proof, and portable stack | `VR-20261006-townsquare-040`, `-050`, `-070` | Pinned images/config/SBOMs, live health/security evidence, backup/restore/replay evidence, and exact operator cutover decision |
| 2 — Shared contracts | Define the TownSquare dictionary plus Vertical, Wonderland, and governance-evidence integration profiles | `VR-20261006-townsquare-120`, `-130`, `-140`, `-150` | Reviewed versioned documents with schemas, examples, compatibility rules, provenance, and acceptance evidence |
| 3 — Governing package | Finish Doctrine, Rules of Engagement, and TownSquare governance without infrastructure literals | `VR-20261006-townsquare-060` | Kano-owned governing package, independent review, cross-document authority map, and operator adoption decision |
| 4 — Convergence and integration | Prove infrastructure workflows and governing rules cover one another, then implement the approved integrations | `VR-20261006-townsquare-170`, `-180`, plus portability rehearsal `-100` | Convergence matrix has no unexplained workflow/rule gap; integration conformance and second-environment portability evidence pass |
| 5 — Bounded pilot and acceptance | Run the unified solution for 2–4 weeks, record gaps, and decide acceptance | `VR-20261006-townsquare-076` | Day-0/7/14 evidence and, when extended, day-28 evidence; final operator acceptance or explicit non-acceptance decision |

The milestone sequence communicates intent but does not invent Vertical dependency enforcement. Design work for later milestones may proceed in parallel when it does not destabilize the deployment contract; runtime activation remains subject to the relevant workflow, evidence, review, and operator decision.

### Program deliverable registry

Each row below is or maps to one native-shaped `unit-of-work` opening with lifecycle `OPEN`, `schema_version: "1"`, and `workflow_ref` equal to the `poc_event_uid` of `VR-20261006-townsquare-000`. The table pins the minimum JSON-list DoD and the four ownership roles that the implementation must copy into event metadata/body. Ownership fields are coordination facts, never authorization.

| Deliverable / POC ref | Milestone | Minimum `definition_of_done` JSON list | Creation owner | Fulfillment owner | Review owner | Operator acceptance owner |
|---|---|---|---|---|---|---|
| MVP deployment / `VR-20261006-townsquare-070` | 1 | `["exact release and ports pinned", "migrations and health verified", "security and fault tests evidenced", "cutover and rollback decision recorded"]` | Ip Man | Francis Ngannou | Ronda Rousey and GSP | Operator |
| Portable stack / `VR-20261006-townsquare-040` | 1 | `["single Docker Compose package", "vendor-neutral storage and secret contracts", "offline reproducible build", "image/config/SBOM digests evidenced"]` | Ip Man | Francis Ngannou | Tony Jaa | Operator |
| TownSquare object/event/state dictionary / `VR-20261006-townsquare-120` | 2 | `["objects and field types defined", "required and optional fields defined", "state transitions and invalid transitions defined", "authority provenance retention and compatibility rules defined"]` | Jackie Chan | Bruce Lee | Ip Man | Operator |
| Vertical Integration Profile / `VR-20261006-townsquare-130` | 2 | `["identity and reference mapping defined", "workflow and transition mapping defined", "compare-and-append migration defined", "conformance fixtures and failure behavior defined"]` | Ip Man | Bruce Lee | Jackie Chan | Operator |
| Wonderland Observation/Behavioral Data Requirements / `VR-20261006-townsquare-140` | 2 | `["read-only source feeds defined", "behavioral feature and provenance requirements defined", "privacy retention and redaction boundaries defined", "model version and reproducibility requirements defined", "non-authority contract tested"]` | Shuri | Shuri | GSP | Operator |
| Governance Evidence and Policy Receipt Profile / `VR-20261006-townsquare-150` | 2 | `["governing source identity and hash defined", "policy receipt and context proof defined", "expiry revocation and supersession defined", "fail-closed validation and audit reconstruction defined"]` | Jigoro Kano | Bruce Lee | GSP | Operator |
| Doctrine, Rules of Engagement, and TownSquare governance / `VR-20261006-townsquare-060` | 3 | `["vendor-neutral doctrine defined", "rules of engagement defined", "TownSquare governance and adjudication defined", "authority and amendment boundaries defined", "operator adoption decision recorded"]` | Jigoro Kano | Jigoro Kano | GSP and Ip Man | Operator |
| Convergence matrix / `VR-20261006-townsquare-170` | 4 | `["every infrastructure workflow mapped to governing rule", "every governing rule mapped to enforceable workflow or declared human gate", "uncovered and non-viable mappings recorded", "owners and remediation units assigned"]` | Ip Man | Jackie Chan | Jigoro Kano and Bruce Lee | Operator |
| Integration implementation / `VR-20261006-townsquare-180` | 4 | `["approved profiles implemented", "TownSquare Vertical and Wonderland boundaries integrated", "policy receipt enforcement verified", "end-to-end conformance and degradation tests pass"]` | Ip Man | Bruce Lee | Jackie Chan, GSP, and Ronda Rousey | Operator |
| 2–4 week pilot / `VR-20261006-townsquare-076` | 5 | `["pilot scope cohort and start recorded", "day-0 day-7 and day-14 evidence recorded", "extension to day-28 explicitly decided when used", "known gaps entered as OPEN roadmap work", "operator acceptance or non-acceptance decision recorded"]` | Helio Gracie | Helio Gracie | Ronda Rousey | Operator |

### Added shared-contract and convergence work units

The following units supplement the detailed MVP and Stage 2 inventory. All are initially `OPEN`; none is `RESOLVED` or `CLOSED`. Their detailed acceptance criteria are the JSON lists in the deliverable registry above, and each opening carries the concrete workflow reference specified there.

- **`VR-20261006-townsquare-120` — Publish the TownSquare object/event/state dictionary — `OPEN`.** `vertical_level: Feature`; includes Bulletin, Statement, Request, notice, receipt, actor/registration, policy/governance evidence, artifact/evidence pointer, lifecycle event, and archive/tombstone definitions; field cardinality, identity, authority, provenance, versioning, valid/invalid transitions, and compatibility rules are mandatory.
- **`VR-20261006-townsquare-130` — Publish the Vertical Integration Profile — `OPEN`.** `vertical_level: Feature`; defines TownSquare-to-Vertical identity, event, workflow, evidence, transition, migration, retry, concurrency, error, and conformance behavior without claiming native hierarchy support.
- **`VR-20261006-townsquare-140` — Publish Wonderland Observation/Behavioral Data Requirements — `OPEN`.** `vertical_level: Feature`; defines read-only feeds, event-time/source-time handling, provenance, behavior features/labels, model and dataset versioning, privacy/retention/redaction, reproducibility, drift, and prohibition on Wonderland becoming a gate or authority.
- **`VR-20261006-townsquare-150` — Publish the Governance Evidence and Policy Receipt Profile — `OPEN`.** `vertical_level: Feature`; defines exact governing source identity, content hashes, context selection/retrieval proof, actor/role/authority, acknowledgement, expiry, revocation, supersession, decision linkage, and fail-closed reconstruction.
- **`VR-20261006-townsquare-170` — Produce the workflow/governance convergence matrix — `OPEN`.** `vertical_level: Feature`; maps both directions and records every gap as a distinct OPEN unit rather than hiding it in narrative.
- **`VR-20261006-townsquare-180` — Implement and verify the approved cross-project integrations — `OPEN`.** `vertical_level: Feature`; implementation begins only from reviewed profiles and matrix rows, preserves TownSquare as record, Vertical as work model/projection, and Wonderland as read-only observer.

## Vertical Stage 2 boundary and roadmap

Stage 2 runtime expansion is not required for MVP acceptance unless a later operator decision explicitly changes scope. Milestone-2 contract drafting may proceed in parallel when it cannot affect deployment; those documents are not ratified against the runtime until deployed contracts freeze. Stage 2 and Milestone-4 implementation begins only after its profiles and convergence matrix are reviewed, and ordinarily after MVP acceptance unless the operator knowingly authorizes parallel risk. No calendar estimate is asserted while clean Compose, runtime, security, restore, replay, and recovery evidence remain pending.

### Stage 2 Feature 1 — Full Drive migration and retirement

**`VR-20261006-townsquare-080` — Full Drive migration and disposition — `OPEN`**

- Owner: Jackie Chan for inventory/reconciliation; Bruce Lee for importer; operator for disposition.
- DoD: AC-M01–M11 evidence or an explicitly revised accepted boundary.

Stories:

- **`VR-20261006-townsquare-081` — Immutable Drive inventory and content extraction — `OPEN`.**
- **`VR-20261006-townsquare-082` — Idempotent import and reconciliation — `OPEN`.** Depends metadata on `VR-20261006-townsquare-081`.
- **`VR-20261006-townsquare-083` — Record Drive archive/retirement disposition — `OPEN`.** Owner operator.

### Stage 2 Feature 2 — Delivery and optional dormant wake

**`VR-20261006-townsquare-090` — Replaceable notification and wake release — `OPEN`**

- Owner: Tony Jaa; GSP security review; operator activation.
- DoD: separate release with fixed identifiers, trusted-origin revalidation, stop, dedupe, caps, and unattended-spend control.

Stories:

- **`VR-20261006-townsquare-091` — Pointer-only delivery adapter — `OPEN`.**
- **`VR-20261006-townsquare-092` — Disabled dry-run host runner — `OPEN`.** DoD: MVP-WAKE-01.
- **`VR-20261006-townsquare-093` — Real dormant-agent activation — `OPEN`.** DoD: MVP-WAKE-02 plus explicit operator approval.

### Stage 2 Feature 3 — Network and portability maturity

**`VR-20261006-townsquare-100` — Broader transport and portability proof — `OPEN`**

- Owner: Tony Jaa for transport/cloud; Francis Ngannou for release operations.

Stories:

- **`VR-20261006-townsquare-101` — Reviewed broad-LAN TLS/mTLS profile — `OPEN`.** DoD: exact certificates, binds, firewall allowlist, no-DNAT/no-UPnP evidence, and rejected-host probe.
- **`VR-20261006-townsquare-102` — Second-host or cloud rehearsal — `OPEN`.** DoD: storage-neutral conformance on a second environment; no horizontal or multi-region claim.
- **`VR-20261006-townsquare-103` — Native-compatible upgrade rollback — `OPEN`.** DoD: previous release demonstrably serves the current native schema/contract before seamless rollback is claimed.

### Stage 2 Feature 4 — Deferred product and Vertical semantics

**`VR-20261006-townsquare-110` — Resolve deferred semantics and migrate the POC — `OPEN`**

- Owner: Ip Man for architecture; Jigoro Kano for doctrine/logic; Jackie Chan for data migration; Bruce Lee for implementation.

Stories:

- **`VR-20261006-townsquare-111` — Decide Statement semantics — `OPEN`.** DoD: explicit adoption or rejection of its domain meaning, schema, workflow, and migration impact.
- **`VR-20261006-townsquare-112` — Design attachments and binary content — `OPEN`.** DoD: limits, scanning, storage, rendering, authorization, and recovery proof.
- **`VR-20261006-townsquare-113` — Migrate the POC into native Vertical — `OPEN`.** DoD: replay valid events, preserve authoritative links/evidence, compare counts/states/hashes, and freeze the POC ledger.
- **`VR-20261006-townsquare-114` — Decide hierarchy and blocker enforcement — `OPEN`.** DoD: add enforcement only if Vertical later defines it; otherwise preserve the metadata with its non-enforced label.

## Normative implementation corrections from peer review

The following are clarifications of the existing contract, not new product scope:

1. **Closed, complete schema.** `townsquare-work-event.schema.json` declares every field in this design's header, lifecycle-body, metadata, decision, workflow, and reference dictionaries, including `acceptance_refs`, `townsquare_thread_ref`, `townsquare_opening_sha256`, `artifact_ref`, `cites_decision`, `blocked_attempt_ref`, `clears_blocked_attempt_ref`, and `reason_trigger_ref`. The event object, workflow object, workflow-transition objects, and native decision-requirement objects are all closed with `additionalProperties: false`. Conditional branches distinguish the workflow decision, Epic decision, work opening, and each transition body. They constrain exact tokens, non-empty strings, array item types, integer ranges, required and forbidden fields, and the declared lifecycle states. The renderer validates this schema with `Draft202012Validator.check_schema` before constructing an event validator.
2. **Exact workflow decision.** Validation compares the complete workflow object byte-for-byte after canonicalization against the pinned profile, all six states in order, initial and terminal declarations, and all eleven ordered transition objects. It also verifies that the workflow record's measured `basis_ref` hash equals the current reviewed design bytes and that its Git evidence names the reviewed full commit and this design path. Checking only transition names or roles is insufficient.
3. **Complete transition semantics.** Validation selects the exact matrix row for each edge, checks `role_acted_under` against that row's `allowed_roles`, requires every common and edge-specific field, rejects forbidden or empty values, and enforces the row's citation, evidence, decision-requirement, and validator rules. There is no global hardcoded `implementer` shortcut: the declared `project-owner` cancellation, reopen, and close edges must work, while an undeclared role must fail.
4. **Evidence verification.** A measured locator is not accepted merely because its text ends in a hash. The workflow design is always read and hashed, and its Git locator resolves the full commit and path. Current-status seeds must equal the exact immutable basis values in the seed table; seed creation verifies available source bytes before append, while later projection preserves that historical content address without making continued availability of the external archive or governance-review file a renderer prerequisite. Any measured evidence used to satisfy a transition requirement, resolution, closure, or acceptance must be supplied to the validation fixture/resolver and rehashed; missing bytes, a hash mismatch, a mutable ref, or an unverifiable required locator fails with exit `65`. `reported-by` task references remain claims and are never promoted to measured evidence.
5. **Canonical physical JSONL.** After duplicate-detecting parse and schema validation, each physical line without its LF must equal the pinned canonical serialization of the complete stored event, including `poc_content_sha256`. The content hash is then independently recomputed over the same validated event with only `poc_content_sha256` removed. Reordered keys, alternate legal JSON escapes, extra whitespace, or another noncanonical spelling therefore fails even if it decodes to the same object and carries a matching semantic hash.
6. **Exact current-status seeds.** The seed table under `Current deployment status` is normative for the latest event and projection, not only for the opening. In particular, `VR-052` remains `basis_kind: measured` with the pinned offline archive as `basis_ref`; a later task-report transition may not replace that latest measured basis. Governance gates state that Eddie Brock returned `REWORK` and Kano disposition plus TownSquare ingestion are owed. Portable-release gates state that clean Compose parsing and runtime validation are owed. Recovery gates state that restore-drill reconciliation is in `REWORK`. Backup gates state that executed backup, signature, restore, and replay proof are absent. Deployment gates state that clean Compose, dark start, migration, health, security, restore, replay, and degradation evidence are pending. Their next actions name those concrete owed checks. No generic “record evidence” text may replace the known gate or action, and no row implies adoption, cutover, pilot start, resolution, closure, or acceptance.
7. **Exact program registry.** Tests compare an exact ten-key map, not a subset. The required keys are `VR-20261006-townsquare-070`, `-040`, `-120`, `-130`, `-140`, `-150`, `-060`, `-170`, `-180`, and `-076`. Each opening copies its full `definition_of_done` list and all four ownership values from the Program deliverable registry exactly. `VR-076` and `VR-180` are both mandatory. Ownership remains reporting metadata and grants no authority.
8. **Complete operator README.** `docs/vertical-poc/README.md` contains the pinned runtime/bootstrap command, wheel-lock boundary, exit-code table, complete field dictionary, complete transition matrix with roles/fields/evidence requirements, append procedure, canonicalization rules, failure behavior, projection rules, and one-pass migration/map procedure. Token mentions alone do not satisfy this requirement.
9. **Readable deterministic roadmap.** The roadmap adds a deterministic status summary and immediate-gates section derived only from validated ledger values, then presents the required eleven-column primary table sorted by numeric milestone and `poc_ref`. It shows Milestones 0–5, all ten program deliverables, concrete evidence/gates/actions, and populated registry ownership. `UNKNOWN` is rendered only when the source chain genuinely omits the field; it is never used in place of registry data. The roadmap preserves full evidence locators and the non-authority boundary, and it never infers hierarchy, deployment, adoption, acceptance, or lifecycle from display metadata.
10. **Tests prove the intended layer.** Every renderer test first completes one baseline render successfully with the approved interpreter. A malformed-input test then asserts exit `65`, the specific `VERTICAL_POC_INVALID <code>:` diagnostic for the mutation, and unchanged/absent target behavior; `returncode != 0` alone is forbidden. Separate preflight tests invoke an unapproved or dependency-incomplete interpreter and assert exit `78` with `VERTICAL_POC_CONFIG`, proving that an import failure cannot satisfy a schema, transition, hash, reference, or fail-atomic test.

## Milestones and timeline policy

The earlier pre-deployment calendar estimate is superseded by active deployment facts and is not the current forecast.

The next reliable estimate must be made after these observable milestones:

1. the corrected service-account source is rebuilt and the Backup image evidence is captured;
2. the exact release manifest and all image/config/SBOM digests are captured;
3. dark runtime health, migrations, backup, restore, and replay pass;
4. the operator records governance, transport, trust-material, and cutover decisions; and
5. the bounded pilot starts, establishing its actual day-7/day-14/day-28 dates.

Stage 2 design begins after runtime contracts freeze. Stage 2 implementation begins after the MVP acceptance decision unless separately authorized. This milestone-based forecast is more honest than converting remaining gates into an unsupported calendar date.

## Migration into native Vertical

1. Freeze and SHA-256 hash `townsquare-work-events.jsonl` at the migration boundary.
2. Before any native write, run the same complete strict parse, duplicate-key, schema, pinned-canonicalizer, hash, identity, workflow, transition, role, evidence, earlier-reference, and chain validation required before rendering. Reject any unresolved or forward reference, including `workflow_ref`.
3. Replay once in ascending `poc_global_order`. When an opening is encountered, open its native thread and record the store-allocated native `thread_uid` and opening `event_uid`; when a transition is encountered, its thread and every cross-thread target must already be present in the migration map. No fix-up or second pass may repair a forward reference.
4. Create the workflow-definition decision and Epic with their pinned native decision shapes. Create each Feature and Story opening as `unit-of-work`, translating `workflow_ref`, `parent_ref`, `depends_on_refs`, evidence links, and TownSquare source links through the already-populated migration map where the target is a POC event.
5. For each transition, translate both `base_event_id` and `expected_head` to the same immediately preceding native `event_uid`. Call Vertical `append_event(..., expected_head=<translated-head>)`; a `HeadConflict` aborts migration. Never use unconditional append for a transition.
6. Preserve `vertical_level`, `parent_ref`, and `depends_on_refs` as visibly non-enforced metadata unless the target Vertical release has adopted explicit corresponding contracts. Translation does not strengthen their semantics.
7. Write `docs/vertical-poc/migration-map.json`. For every event, record `poc_ref` when present, `poc_thread_uid`, `poc_event_uid`, `poc_seq`, `poc_global_order`, `poc_content_sha256`, mapped native `thread_uid`, native `event_uid`, native `seq`, native `global_seq`, and native `content_sha256`. This map preserves both identity domains, both hashes, and both source/native orders; it never claims the translated event hashes are equal.
8. Compare source/native event and thread counts, event order within every thread, translated reference targets, latest lifecycle state per opening, evidence/artifact hashes, citations, and generated roadmap. Independently recompute POC and native content hashes from their respective canonical forms.
9. Mark the POC ledger read-only. Never delete it, renumber it, rewrite its history to imitate native IDs, or discard the migration map.

## Alternative rejected

An external tracker such as Notion, a spreadsheet, or GitHub Issues was rejected for the POC. It would introduce a second mutable authority, weaker transition provenance, and a separate migration problem. A hand-maintained Markdown-only roadmap was also rejected because it cannot reliably validate transition chains or regenerate state. Git-tracked JSONL plus a generated Markdown projection is the smallest solution that preserves auditability and later migration. A two-phase native migration with unresolved-reference fix-ups was rejected because it admits forward references and partial semantic repair; the earlier-target ordering rule permits a simpler, auditable one-pass replay. A bespoke standard-library replacement for JSON Schema validation was rejected because reimplementing Draft 2020-12 meta-schema behavior would enlarge the security and correctness surface while weakening interoperability. The smaller controlled solution is the pinned, offline, hash-verified `jsonschema` runtime above.

## Implementation acceptance checks

The POC implementation is acceptable only when automated tests prove all of the following:

1. `schema_version` is exactly `"1"`; `canonicalization_profile` is exactly `rfc8785+townsquare-vertical-poc-safeint/1`; `actor_provenance` is a duplicate-free valid JSON string with all required provenance keys; every work event has valid `role_acted_under`, fixed RFC3339 `claimed_at`, `basis_kind`, and required `basis_ref`; and every `OPEN` `definition_of_done` is a JSON list of strings.
2. `poc_ref`, `poc_thread_uid`, and `poc_event_uid` are distinct concepts and valid in their pinned formats. No `VR-*` value is accepted as an event/thread identity, and no prefixed POC identity is accepted as a native bare UUIDv7.
3. The POC workflow-definition record exists exactly once, is anchored to the independently reviewed design's verified byte hash and Git identity rather than generated output, and contains exactly the pinned profile, six states, initial/terminal declarations, eleven transition entries, roles, fields, requirements, and validators above. Every `OPEN` unit's `workflow_ref` resolves to its `poc_event_uid`; an absent, stale, changed, or dangling workflow reference fails validation.
4. The Epic is exactly `event_type: decision`, `decision_type: goal-or-priority`, native record status `RECORDED` (routing `state: RECORDED`), with no `unit_of_work_ref`.
5. Every transition is one of the eleven permitted edges, uses an allowed role, provides every common and edge-specific field, satisfies all requirements and validators, and has `base_event_id == expected_head ==` the immediately preceding `poc_event_uid`; openings omit both; chains are dense and unbranched. Tests cover valid and invalid `BLOCKED` entry/clearance plus terminal-state rejection. Active seeded units project `WORKING` from an appended event rather than mutating their opening.
6. A `RESOLVED` unit is rejected without both a concrete `artifact_ref` and a resolvable `cites_decision`. A `CLOSED` unit is rejected without a resolvable acceptance decision. The initial ledger contains no `CLOSED` items and no unsupported `RESOLVED` items.
7. Every `measured` basis is content-addressed or pinned to a full Git commit/path and is verified before use. Task/session claims are `reported-by`. Mutable measured paths, branches, tags, latest aliases, owner names, candidate manifest/backup templates, and reported or assumed evidence cannot satisfy build, runtime, deployment, recovery, pilot, or acceptance criteria. `rework-required` cannot be projected as `BLOCKED` without the workflow's gate-authored blocker evidence.
8. Changing, adding, removing, or making `parent_ref`/`depends_on_refs` dangling may create a display/reference finding but produces **no** lifecycle transition, block, authorization, feature rollup, or closure. In particular: a dependency marked open cannot block an otherwise workflow-valid transition; a dependency marked complete cannot authorize one; a child closure cannot close or resolve its parent; and a parent state cannot close or resolve its children.
9. The generated Markdown is byte-identical on repeated renders and is derived only from the JSONL ledger; it never becomes a writable authority. Its primary table contains the eleven required columns in their fixed order, uses the last valid event per thread, and obtains `Reported at` only from `claimed_at`, never the renderer clock. Any malformed line, duplicate key, schema/profile/hash/identity/reference/workflow/transition/chain/seed error aborts before rendering; tests prove a missing target is not created and an existing target remains byte-identical.
10. Every POC event reference targets an event with smaller `poc_global_order`; forward references and cycles fail validation. A migration dry run replays once by global order, translates both POC identities without fix-ups, uses compare-and-append `expected_head` for every transition, aborts on an unmapped target or simulated `HeadConflict`, and produces a map preserving POC/native identities, hashes, and order.
11. TownSquare, Vertical, and Wonderland boundary tests or fixtures show that Wonderland consumes read-only projections and cannot write source events, satisfy workflow conditions, block work, or change lifecycle state.
12. Tracker test failure has no code path into NAS deployment, runtime health, cutover, or rollback decisions.
13. The generated ledger and roadmap contain Milestones 0–5 and all ten program deliverables in the registry. Every chain opens `OPEN` with a resolvable workflow reference, pinned JSON-list DoD, and creation/fulfillment/review/operator-acceptance ownership metadata; the exact active units in the seed table then append valid `WORKING` events. The governance review, offline artifact, recovery REWORK, pending runtime validation, and absence of adoption/cutover/pilot are projected exactly as specified above, with no initial `RESOLVED` or `CLOSED` unit.
14. Changing an owner or milestone label changes only assignment/reporting output. It cannot change authorship permissions, satisfy a workflow requirement, create an acceptance decision, or alter lifecycle state.
15. JSONL validation rejects BOMs, CR bytes, invalid UTF-8, lone surrogates, missing final LF, more than one object on a line, duplicate keys at any nesting depth, any non-integer numeric value, boolean-as-integer, integers outside the safe range, non-dense/out-of-range sequences, an absent or changed canonicalization profile, noncanonical or mismatched `poc_content_sha256`, renderer-introduced timestamps, and native migration that fails to canonicalize POC arrays/objects or double-encodes `actor_provenance`.
16. From a clean checkout with no ambient `jsonschema`, the pinned offline bootstrap verifies the exact CPython profile and six wheel hashes, creates the approved environment without network access, and completes a positive baseline render. Missing, altered, Linux-only, or version-substituted wheels fail before installation and preserve any existing environment. Renderer dependency failure returns exactly `78` with `VERTICAL_POC_CONFIG`; invalid tracker data returns exactly `65` with the intended `VERTICAL_POC_INVALID` code; tests never treat an import failure as successful invalid-data validation.
17. The schema is meta-schema-valid, closed at every declared object level, declares every field named in this design, and conditionally validates workflow decisions, Epic decisions, openings, and every transition body. Tests mutate the initial state, terminal states, every transition role, every edge-specific required field, decision requirements, evidence citations, and reviewed-design basis independently; each mutation fails for its own diagnostic.
18. The exact ten-entry program registry is asserted by equality, including full DoD arrays and owner metadata for both `VR-076` and `VR-180`. Latest-event assertions prove the exact current seed basis, gate, next action, and lifecycle. The generated roadmap is grouped in numeric milestone order, includes a deterministic status/gate summary, contains no placeholder where registry data exists, and remains explicit that hierarchy, ownership, deployment, adoption, pilot, and acceptance are not inferred.

## WORK ORDER

- **Document:** Ip Man/main session — retain this design note as the single decision record for the POC; update it only through reviewed design changes.
- **Decision review:** Jackie Chan — independently examine the amended event identity, complete closed schema, transition ordering, JSON field shapes, evidence/reference integrity, exact seed/registry contract, pinned dependency profile, native migration mapping, and all prior REWORK findings; raise her own concerns before implementation. The previous review does not approve this `0.5-design` delta.
- **QA preparation and test ownership:** Ronda Rousey — after the decision review passes and before implementation resumes, update and own `tests/test_vertical_poc_roadmap.py` from the implementation acceptance checks above, including positive dependency preflight, diagnostic-specific negative tests, exact ten-entry registry, exact seed-state, full workflow matrix, canonical physical JSONL, earlier-reference, readable projection, and fail-atomic assertions. This test-preparation handoff is an implementation gate.
- **Package tracker runtime:** Francis Ngannou — only after decision review and QA preparation pass, own `requirements/vertical-poc-win-amd64-cp312.lock.txt`, `tools/bootstrap-vertical-poc.ps1`, and acquisition/verification of the exact Windows `rpds_py` wheel in the approved wheelhouse. Do not change TownSquare service/runtime requirements or make the tracker a deployment prerequisite.
- **Implement tracker:** Bruce Lee — only after the decision-review, Ronda test-preparation, and pinned-runtime handoffs pass, own the five tracker artifacts: `docs/vertical-poc/townsquare-work-events.jsonl`, `docs/vertical-poc/townsquare-work-event.schema.json`, `docs/vertical-poc/README.md`, `tools/render-vertical-poc-roadmap.py`, and generated `docs/townsquare-vertical-poc-roadmap.md`. Include Milestones 0–5 and every program deliverable, satisfy Ronda's prepared tests, do not edit her test file or Francis's runtime artifacts, and do not modify TownSquare runtime code.
- **Define shared contracts:** Jackie Chan — TownSquare object/event/state dictionary; Ip Man — Vertical Integration Profile; Shuri — Wonderland Observation/Behavioral Data Requirements; Jigoro Kano — Governance Evidence and Policy Receipt Profile plus Doctrine/Rules of Engagement/TownSquare governance. Each owner documents interfaces, data shapes, examples, failure behavior, workflow, and acceptance evidence before any dependent code is written.
- **Review shared contracts:** Ip Man reviews the TownSquare dictionary; Jackie Chan reviews the Vertical profile; GSP reviews the Wonderland, governance-evidence, and governing-package security/authority boundaries. Reviewers must raise their own concerns and record a decision before dependent implementation.
- **Converge:** Ip Man and Jackie Chan — produce the bidirectional workflow/governance convergence matrix after the infrastructure and governance drafts exist; Jigoro Kano and Bruce Lee review rule coverage and technical viability. Every uncovered row becomes an explicit OPEN unit.
- **Implement integrations:** Bruce Lee — only after the relevant profile and convergence decisions are reviewed, implement the approved TownSquare/Vertical/Wonderland/policy-receipt integration boundaries. Wonderland remains read-only.
- **Package and deploy:** Francis Ngannou — complete the portable stack and MVP deployment; Tony Jaa reviews portability and service-boundary contracts. This remains the delivery priority and is not blocked by the tracker itself.
- **Peer review tracker:** Ip Man — verify the artifacts match the reviewed design and do not imply enforced hierarchy, blockers, acceptance, or deployment results.
- **QA:** Ronda Rousey — run and independently validate the tracker acceptance checks above and the eventual integration/portable-stack conformance, including separate POC/native identities, exact JSON shapes and canonical hashes, `OPEN → WORKING` plus later `base_event_id`/`expected_head` chains, workflow resolution, exact current-status seeds, no unsupported terminal state, evidence classification, required roadmap columns, deterministic no-clock rendering, migration serialization/mapping, required metadata-no-effect negative tests, read-only Wonderland behavior, and recovery/degradation paths.
- **Pilot:** Helio Gracie — coordinate the bounded 2–4 week pilot, delivery checkpoints, evidence cadence, and gap conversion into OPEN roadmap units; never substitute coordination metadata for the operator's acceptance decision.
- **Accept:** operator — issue the explicit acceptance, extension, variance, or non-acceptance decisions for deliverables and the final pilot. No assignment metadata or agent statement closes a unit.
- **Coordinate:** Helio Gracie — checkpoint the decision review, implementation, and QA handoffs; gateway the exact artifact commit and every open discrepancy.
- **Watch for:** conflicts with Francis's concurrent Backup Dockerfile/test work; stale NAS facts; treating reported builds or evidence templates as runtime proof; closing work without an acceptance decision; making `parent_ref` or `depends_on_refs` sound enforced; confusing `poc_ref`/POC identities/native identities; allowing Wonderland to become an authority or gate; putting the tracker on the NAS critical path; or allowing Stage 2 gaps to become silent MVP prerequisites.
