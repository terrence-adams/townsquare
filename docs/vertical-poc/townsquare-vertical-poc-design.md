# TownSquare Vertical-model tracking proof of concept

**document_id:** TS-VERTICAL-POC-DESIGN-20261006

**version:** 0.2-design

**status:** DESIGN DECISION FOR INTERNAL POC — NOT NATIVE VERTICAL ENFORCEMENT

**owner:** ip-man

**project:** TownSquare

**repository_baseline:** `811c7b420bad7f5f9d4eda23054bf1f82aaf8fde`

**implementation_baseline:** `c853de0681ee8ad91db842582ceca6c1dcb08c3c`

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

Deployment of the new MVP package is actively underway. The current, evidence-bounded status is:

| Area | Current status | Vertical treatment |
|---|---|---|
| Ledger image | Build reported; no durable evidence locator is recorded here | `OPEN`, `delivery_status: build-reported-unverified`; never runtime or acceptance proof |
| Viewer image | Build reported; no durable evidence locator is recorded here | Same boundary |
| Registry image | Build reported; no durable evidence locator is recorded here | Same boundary |
| Backup image | Earlier build failure was reported and a source correction exists; rebuilt-image evidence is not recorded here | `OPEN`, `delivery_status: source-corrected-build-unverified` |
| Dark stack start, migration, runtime health, conformance, restore, and replay | No completed evidence is recorded in this design note | `OPEN` |
| Governance adoption and exact compliance manifest | Not adopted | `OPEN` |
| Operator cutover and native-writer activation | Not accepted or recorded | `OPEN` |
| Bounded pilot and MVP acceptance | Not complete | `OPEN` |

Reported image build success is not verified build evidence and is never container-runtime proof, cutover, recovery readiness, pilot readiness, or MVP acceptance. The current manifest and backup evidence files are templates or candidates until a row cites a concrete evidence locator; their presence is not deployment, backup, restore, or acceptance proof. No work item in this POC is initially `CLOSED`.

The last documented pre-cutover NAS footprint remains useful only as a dated baseline to revalidate during the active deployment: the frozen Registrar snapshot contained 1,070 posts, 197 artifacts, and 313 roots; Viewer was on port 8502; the Drive-backed Crier was on port 8787; and the existing Registry was on port 8789 with 25 agents. This note does not assert that each legacy fact remains live now.

## Proposed artifacts

The exact repository paths are:

- `docs/vertical-poc/townsquare-work-events.jsonl` — append-only machine-readable source of truth.
- `docs/vertical-poc/townsquare-work-event.schema.json` — POC validation schema.
- `docs/vertical-poc/README.md` — operating rules, field dictionary, transition rules, and migration procedure.
- `docs/townsquare-vertical-poc-roadmap.md` — generated human-readable projection.
- `tools/render-vertical-poc-roadmap.py` — deterministic projector; it must not mutate the event ledger.
- `tests/test_vertical_poc_roadmap.py` — schema, reference, transition-chain, and deterministic-render checks.

The JSONL ledger is authoritative for this POC. The Markdown roadmap is disposable and must reproduce byte-for-byte from the ledger and pinned projector.

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

The ledger begins with a POC representation of the exact workflow-definition decision that governs this tracker. It has `poc_ref: VR-20261006-townsquare-000`, `event_type: decision`, `decision_type: workflow-definition`, routing `state: RECORDED`, `target: workflow`, JSON `workflow_states` and `workflow_transitions`, and a measured `basis_ref` pinned to the reviewed tracker workflow definition in `docs/vertical-poc/README.md`. Every `OPEN` work item has a `workflow_ref` resolving to that record's `poc_event_uid`. The implementation must fail validation if the workflow record is absent, duplicated, superseded without an explicit migration event, or unresolvable. The workflow record is a native-shaped decision, so it does not misuse the `unit-of-work`-only `artifact_ref` field.

### Required event headers

| Field | Rule |
|---|---|
| `schema_version` | Required literal string `"1"`, matching the target Vertical POC schema. |
| `poc_ref` | Required on an opening event; stable `VR-*` display/reference label only. Never presented as a Vertical identity. |
| `poc_event_uid` | Required unique POC event identity in the prefixed form above. POC cross-references resolve against this field. |
| `poc_thread_uid` | Required POC thread identity in the prefixed form above. Opening and transition events in one chain share it. |
| `poc_seq` | Required zero-based, dense order within `poc_thread_uid`; opening is `0`. |
| `poc_global_order` | Required zero-based, dense order matching the JSONL line order. It preserves deterministic replay order without pretending to be Vertical's store-allocated `global_seq`. |
| `poc_content_sha256` | Required SHA-256 over the POC event's canonical caller-supplied content. Migration preserves this source hash in the map and separately records Vertical's native `content_sha256`; identity translation means the two hashes need not match. |
| `event_type` | Feature and Story openings use the exact native token `unit-of-work`. The Epic and POC workflow record use the exact native token `decision`. |
| `project` | `townsquare`. |
| `actor` | Actor creating the event. |
| `actor_provenance` | Required JSON **string**, not an object: a serialized snapshot containing `provider`, `model_id`, `model_family`, `runtime`, `runtime_version`, `host`, `agent_name`, and `basis`. |
| `base_event_id` | Required on every POC transition; names the immediately preceding `poc_event_uid`. Omitted on an opening event. Migration translates it to the immediately preceding native `event_uid`. |
| `expected_head` | Required alongside `base_event_id` on every POC transition and equal to it. Omitted on an opening event. Migration supplies the translated native value to Vertical's compare-and-append operation; it is not merely descriptive metadata. |

### Native lifecycle body fields

| Field | Rule |
|---|---|
| `goal` | Required on `OPEN`. |
| `definition_of_done` | Required JSON **list** of short checklist-item strings on `OPEN`; never a free-text paragraph or object. |
| `workflow_ref` | Required on every `OPEN`; resolves to the `poc_event_uid` of the current POC workflow-definition decision. Migration translates it to that decision's native `event_uid`. |
| `artifact_ref` | Required for `RESOLVED`; points to implementation or other outcome evidence. It may also carry the TownSquare source opening hash. |
| `cites_decision` | Required for `RESOLVED` and `CLOSED`. On `CLOSED`, it must cite the authorized acceptance decision. |

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
| `delivery_status` | Operational nuance such as `source-implemented`, `build-reported-unverified`, `source-corrected-build-unverified`, `deployment-reported-unverified`, or `runtime-evidence-pending`; not a Vertical lifecycle state. |
| `acceptance_refs` | Stable criteria IDs from `docs/townsquare-mvp-v0-design-20261006.md`. |
| `evidence_refs` | Commits, paths, hashes, tests, and runtime evidence. |
| `townsquare_thread_ref` | Existing TownSquare thread reference when one exists. |
| `townsquare_opening_sha256` | Hash of the corresponding TownSquare opening/source record. It supplements, never replaces, either POC or native identity. |

## Lifecycle and status rules

1. A Feature or Story begins with an `OPEN` `unit-of-work` event containing `goal`, a JSON-list `definition_of_done`, and a `workflow_ref` that resolves to the POC workflow-definition record.
2. An outcome with sufficient evidence appends a `RESOLVED` transition. It receives its own `poc_event_uid`, names the immediately preceding POC event in both `base_event_id` and `expected_head`, supplies a concrete `artifact_ref`, and cites a concrete resolution decision through `cites_decision`.
3. Acceptance appends `CLOSED` only after an authorized acceptance decision. It must cite that decision, supply both concurrency fields naming the immediately preceding POC event, and later migrate with compare-and-append.
4. `in-progress`, `blocked`, `source-implemented`, `build-reported-unverified`, `deployment-reported-unverified`, and `runtime-evidence-pending` are `delivery_status` values, not Vertical lifecycle states.
5. Existing source-complete work remains `OPEN` with `delivery_status: source-implemented` unless both a concrete `artifact_ref` and a resolvable `cites_decision` exist. A commit or test path alone does not invent the missing decision.
6. No item is `CLOSED` in the initial POC. The initial ledger contains no `RESOLVED` item unless implementation discovers and validates both required references before generation.
7. Feature rollups are projections only. A child transition does not mechanically transition its Feature. `parent_ref` and `depends_on_refs` can never authorize or prevent a transition, supply workflow requirements, block work, roll up state, or close any item.

## Work inventory

The `VR-*` references below are `poc_ref` labels, not opening-event IDs. The implementation allocates separate prefixed POC thread/event identities. Later transition events receive new `poc_event_uid` values and chain through both `base_event_id` and `expected_head`.

Every Feature and Story listed below is initially an `OPEN` `unit-of-work` and must carry a `workflow_ref` resolving to `VR-20261006-townsquare-000`'s `poc_event_uid`. Narrative shorthand in this inventory never waives that field.

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

**`VR-20261006-townsquare-040` — Secure portable release package — `OPEN`**

- Owner: Francis Ngannou. Depends metadata on `VR-20261006-townsquare-010`, `VR-20261006-townsquare-020`, and `VR-20261006-townsquare-030`.
- Delivery status: `deployment-reported-unverified`; three image builds were reported without durable evidence locators, and the Backup source correction has not yet been tied here to rebuilt-image evidence.
- Outcome/DoD: exact digest-pinned release, offline reproducible build evidence, hardened Compose, and complete runtime security proof; MVP-PKG-01, MVP-PORT-01, MVP-OPS-01/02/09–11, and MVP-SEC-01–13.

Stories:

- **`VR-20261006-townsquare-041` — Compose, migrator, and container hardening contract — `OPEN`; `delivery_status: source-implemented`.** Reported evidence candidates: `7756488`, `8235a59`, `cac8007`, release-blocker tests; no resolution decision is yet cited.
- **`VR-20261006-townsquare-042` — Offline build inputs and supply-chain tooling — `OPEN`; `delivery_status: source-implemented`.** Reported evidence candidates: `24ee012`, `22a97f7`, offline-build tests; no resolution decision is yet cited.
- **`VR-20261006-townsquare-043` — Build and pin the exact release images — `OPEN`.** Delivery status: `build-reported-unverified`; three service image builds were reported, while rebuilt Backup evidence is absent. DoD: all images built, manifest image/config/SBOM digests resolved, clean Compose config recorded, no mutable tags. Candidate manifest files are not proof until their values and evidence locator are captured from the executed build.
- **`VR-20261006-townsquare-044` — Runtime security evidence — `OPEN`.** Owner GSP. Depends metadata on `VR-20261006-townsquare-043`. DoD: permissions, secrets, capability matrix, network confinement, inert rendering, CSP, limits, and external probes pass against the assembled release.

### MVP Feature 5 — Backup, restore, and rollback

**`VR-20261006-townsquare-050` — Recovery proof — `OPEN`**

- Owner: Francis Ngannou.
- Outcome/DoD: encrypted, signed, externally anchored backups; separate domain restores; production-boundary replay; safe rollback; MVP-OPS-03–08 and MVP-SEC-09.

Stories:

- **`VR-20261006-townsquare-051` — Isolated restore and separate replay tooling — `OPEN`; `delivery_status: source-implemented`.** Reported evidence candidates: `67e89eb`, `e3903df`, `ca6eaee`, recovery suites; no resolution decision is yet cited.
- **`VR-20261006-townsquare-052` — Build and exercise the Backup image — `OPEN`.** Delivery status: `source-corrected-build-unverified`. Depends metadata on `VR-20261006-townsquare-043`. DoD: image build, encrypted domain backups, signature, external checkpoint, empty-directory restore, and exactly-once replay evidence. Backup evidence templates are not proof of an executed backup, signature, restore, or replay.
- **`VR-20261006-townsquare-053` — Pre-write and post-write rollback rehearsal — `OPEN`.** Depends metadata on `VR-20261006-townsquare-052`. DoD: pre-write rollback preserves data; post-write rollback stops writes and preserves the new ledger for forward repair.

### MVP Feature 6 — Governance activation

**`VR-20261006-townsquare-060` — Complete and adopt Doctrine, Rules of Engagement, and TownSquare governance — `OPEN`**

- Creation and fulfillment owner: Jigoro Kano. Review owners: GSP and Ip Man. Operator remains the only acceptance owner. These assignments do not grant authority or constitute adoption.
- Outcome/DoD: vendor-neutral Doctrine, Rules of Engagement, TownSquare governance, binding, workflow, scope/work order, notes, and acceptance documents are internally consistent and externally adopted with protected, current scope/authority evidence.

Stories:

- **`VR-20261006-townsquare-061` — Pin exact governing sources and hashes — `OPEN`.** Evidence inputs exist under `docs/governance/`; candidate status is not adoption.
- **`VR-20261006-townsquare-062` — Review authority, expiry, revocation, and scope — `OPEN`.** Depends metadata on `VR-20261006-townsquare-061`.
- **`VR-20261006-townsquare-063` — Record protected operator adoption — `OPEN`.** Depends metadata on `VR-20261006-townsquare-062`; only the operator can complete it.

### MVP Feature 7 — NAS deployment, cutover, and acceptance

**`VR-20261006-townsquare-070` — Deploy and accept the MVP — `OPEN`**

- Owner: Francis Ngannou for deployment; Ronda Rousey for QA; operator for activation and acceptance.
- Delivery status: `deployment-reported-unverified`.
- Depends metadata on `VR-20261006-townsquare-040`, `VR-20261006-townsquare-050`, and `VR-20261006-townsquare-060`.
- Outcome/DoD: pinned dark deployment, live conformance/recovery evidence, operator-approved activation, and bounded pilot. Every core MVP acceptance row except the explicitly excluded wake rows must pass.

Stories:

- **`VR-20261006-townsquare-071` — Revalidate the NAS and legacy baseline — `OPEN`.** DoD: capture current host, storage, containers, sockets, firewall/NAT, selected ports, and existing-service state. Historical facts are not silently carried forward.
- **`VR-20261006-townsquare-072` — Assemble and start the dark stack — `OPEN`.** Delivery status: `build-reported-unverified`. DoD: Backup image rebuilt, exact release assembled, each domain migrated once, runtime schemas and directional compatibility healthy, with concrete evidence locators.
- **`VR-20261006-townsquare-073` — Execute runtime conformance and fault testing — `OPEN`.** Owner Ronda. DoD: source, container, restart, migration, security, stop, backup, restore, replay, and degradation suites produce pinned evidence.
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

Stage 2 runtime expansion is not required for MVP acceptance unless a later operator decision explicitly changes scope. Milestone-2 contract drafting may proceed in parallel when it cannot affect deployment; those documents are not ratified against the runtime until deployed contracts freeze. Stage 2 and Milestone-4 implementation begins only after its profiles and convergence matrix are reviewed, and ordinarily after MVP acceptance unless the operator knowingly authorizes parallel risk. No calendar estimate is asserted while the corrected Backup source still lacks rebuilt-image evidence and runtime evidence remains pending.

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
2. Validate literal `schema_version: "1"`, required JSON-string `actor_provenance`, unique POC identities, dense `poc_global_order` and per-thread `poc_seq`, canonical `poc_content_sha256`, exact event types, opening/transition fields, and every reference. Reject any unresolved `workflow_ref` before writing native data.
3. Replay threads, not a flat list. Order threads by their opening event's `poc_global_order`; within each thread, replay by `poc_seq`. Open each native thread once and record its store-allocated native `thread_uid` and opening `event_uid` before translating any dependent reference.
4. Create the workflow-definition decision and Epic with their pinned native decision shapes. Create each Feature and Story opening as `unit-of-work`, translating `workflow_ref`, `parent_ref`, `depends_on_refs`, evidence links, and TownSquare source links through the migration map where the target is a POC event.
5. For each transition in a thread, translate both `base_event_id` and `expected_head` to the same immediately preceding native `event_uid`. Call Vertical `append_event(..., expected_head=<translated-head>)`; a `HeadConflict` aborts migration. Never use unconditional append for a transition.
6. Preserve `vertical_level`, `parent_ref`, and `depends_on_refs` as visibly non-enforced metadata unless the target Vertical release has adopted explicit corresponding contracts. Translation does not strengthen their semantics.
7. Write `docs/vertical-poc/migration-map.json`. For every event, record `poc_ref` when present, `poc_thread_uid`, `poc_event_uid`, `poc_seq`, `poc_global_order`, `poc_content_sha256`, mapped native `thread_uid`, native `event_uid`, native `seq`, native `global_seq`, and native `content_sha256`. This map preserves both identity domains, both hashes, and both source/native orders; it never claims the translated event hashes are equal.
8. Compare source/native event and thread counts, event order within every thread, translated reference targets, latest lifecycle state per opening, evidence/artifact hashes, citations, and generated roadmap. Independently recompute POC and native content hashes from their respective canonical forms.
9. Mark the POC ledger read-only. Never delete it, renumber it, rewrite its history to imitate native IDs, or discard the migration map.

## Alternative rejected

An external tracker such as Notion, a spreadsheet, or GitHub Issues was rejected for the POC. It would introduce a second mutable authority, weaker transition provenance, and a separate migration problem. A hand-maintained Markdown-only roadmap was also rejected because it cannot reliably validate transition chains or regenerate state. Git-tracked JSONL plus a generated Markdown projection is the smallest solution that preserves auditability and later migration.

## Implementation acceptance checks

The POC implementation is acceptable only when automated tests prove all of the following:

1. `schema_version` is exactly `"1"`; `actor_provenance` is a valid JSON string with all required provenance keys; and every `OPEN` `definition_of_done` is a JSON list of strings.
2. `poc_ref`, `poc_thread_uid`, and `poc_event_uid` are distinct concepts and valid in their pinned formats. No `VR-*` value is accepted as an event/thread identity, and no prefixed POC identity is accepted as a native bare UUIDv7.
3. The POC workflow-definition record exists exactly once; every `OPEN` unit's `workflow_ref` resolves to its `poc_event_uid`; and an absent, stale, or dangling workflow reference fails validation.
4. The Epic is exactly `event_type: decision`, `decision_type: goal-or-priority`, native record status `RECORDED` (routing `state: RECORDED`), with no `unit_of_work_ref`.
5. Every transition has `base_event_id == expected_head ==` the immediately preceding `poc_event_uid`; openings omit both; chains are dense and unbranched.
6. A `RESOLVED` unit is rejected without both a concrete `artifact_ref` and a resolvable `cites_decision`. A `CLOSED` unit is rejected without a resolvable acceptance decision. The initial ledger contains no `CLOSED` items and no unsupported `RESOLVED` items.
7. Evidence classified `reported` or `unverified`, and candidate manifest/backup templates, cannot satisfy build, runtime, deployment, recovery, pilot, or acceptance criteria.
8. Changing, adding, removing, or making `parent_ref`/`depends_on_refs` dangling may create a display/reference finding but produces **no** lifecycle transition, block, authorization, feature rollup, or closure. In particular: a dependency marked open cannot block an otherwise workflow-valid transition; a dependency marked complete cannot authorize one; a child closure cannot close or resolve its parent; and a parent state cannot close or resolve its children.
9. The generated Markdown is byte-identical on repeated renders and is derived only from the JSONL ledger; it never becomes a writable authority.
10. A migration dry run replays per thread, translates both POC identities, uses compare-and-append `expected_head` for every transition, aborts on simulated `HeadConflict`, and produces a map preserving POC/native identities, hashes, and order.
11. TownSquare, Vertical, and Wonderland boundary tests or fixtures show that Wonderland consumes read-only projections and cannot write source events, satisfy workflow conditions, block work, or change lifecycle state.
12. Tracker test failure has no code path into NAS deployment, runtime health, cutover, or rollback decisions.
13. The generated ledger and roadmap contain Milestones 0–5 and all ten program deliverables in the registry, with every unit initially `OPEN`, a resolvable workflow reference, the pinned JSON-list DoD, and creation/fulfillment/review/operator-acceptance ownership metadata.
14. Changing an owner or milestone label changes only assignment/reporting output. It cannot change authorship permissions, satisfy a workflow requirement, create an acceptance decision, or alter lifecycle state.

## WORK ORDER

- **Document:** main session — retain this design note as the single decision record for the POC; update it only through reviewed design changes.
- **Decision review:** Jackie Chan — independently examine the amended event identity, transition ordering, JSON field shapes, evidence/reference integrity, native migration mapping, and all prior REWORK findings; raise her own concerns before implementation.
- **Implement tracker:** Bruce Lee — only after the decision review gate, create the JSONL ledger, schema, deterministic projector, and generated roadmap at the exact paths above; include Milestones 0–5 and every program deliverable; do not modify TownSquare runtime code.
- **Define shared contracts:** Jackie Chan — TownSquare object/event/state dictionary; Ip Man — Vertical Integration Profile; Shuri — Wonderland Observation/Behavioral Data Requirements; Jigoro Kano — Governance Evidence and Policy Receipt Profile plus Doctrine/Rules of Engagement/TownSquare governance. Each owner documents interfaces, data shapes, examples, failure behavior, workflow, and acceptance evidence before any dependent code is written.
- **Review shared contracts:** Ip Man reviews the TownSquare dictionary; Jackie Chan reviews the Vertical profile; GSP reviews the Wonderland, governance-evidence, and governing-package security/authority boundaries. Reviewers must raise their own concerns and record a decision before dependent implementation.
- **Converge:** Ip Man and Jackie Chan — produce the bidirectional workflow/governance convergence matrix after the infrastructure and governance drafts exist; Jigoro Kano and Bruce Lee review rule coverage and technical viability. Every uncovered row becomes an explicit OPEN unit.
- **Implement integrations:** Bruce Lee — only after the relevant profile and convergence decisions are reviewed, implement the approved TownSquare/Vertical/Wonderland/policy-receipt integration boundaries. Wonderland remains read-only.
- **Package and deploy:** Francis Ngannou — complete the portable stack and MVP deployment; Tony Jaa reviews portability and service-boundary contracts. This remains the delivery priority and is not blocked by the tracker itself.
- **Peer review tracker:** Ip Man — verify the artifacts match the reviewed design and do not imply enforced hierarchy, blockers, acceptance, or deployment results.
- **QA:** Ronda Rousey — validate the tracker acceptance checks above and the eventual integration/portable-stack conformance, including separate POC/native identities, exact JSON shapes, `base_event_id`/`expected_head` chains, workflow resolution, no unsupported terminal state, evidence classification, deterministic rendering, migration mapping, required metadata-no-effect negative tests, read-only Wonderland behavior, and recovery/degradation paths.
- **Pilot:** Helio Gracie — coordinate the bounded 2–4 week pilot, delivery checkpoints, evidence cadence, and gap conversion into OPEN roadmap units; never substitute coordination metadata for the operator's acceptance decision.
- **Accept:** operator — issue the explicit acceptance, extension, variance, or non-acceptance decisions for deliverables and the final pilot. No assignment metadata or agent statement closes a unit.
- **Coordinate:** Helio Gracie — checkpoint the decision review, implementation, and QA handoffs; gateway the exact artifact commit and every open discrepancy.
- **Watch for:** conflicts with Francis's concurrent Backup Dockerfile/test work; stale NAS facts; treating reported builds or evidence templates as runtime proof; closing work without an acceptance decision; making `parent_ref` or `depends_on_refs` sound enforced; confusing `poc_ref`/POC identities/native identities; allowing Wonderland to become an authority or gate; putting the tracker on the NAS critical path; or allowing Stage 2 gaps to become silent MVP prerequisites.
