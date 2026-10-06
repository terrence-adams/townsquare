# TownSquare Vertical-model tracking proof of concept

**document_id:** TS-VERTICAL-POC-DESIGN-20261006

**version:** 0.1-design

**status:** DESIGN DECISION FOR INTERNAL POC — NOT NATIVE VERTICAL ENFORCEMENT

**owner:** ip-man

**project:** TownSquare

**repository_baseline:** `d7cc247`

**implementation_baseline:** `ca6eaeeaf1f72383599738ed135a60bcb022ae7f`

**scope:** Internal, Git-tracked representation of current TownSquare work in the new Vertical model until native Vertical tracking is available.

**exclusions:** This note does not deploy TownSquare, create Vertical events, adopt governance, accept the MVP, enforce hierarchy or blockers, or authorize Stage 2.

## Decision

Track TownSquare through an append-only JSONL event ledger and generate a Markdown roadmap from it. The POC will model one Epic as a project-level goal-or-priority decision and every Feature and Story as a Vertical `unit-of-work`.

Vertical currently has no enforced Epic → Feature → Story hierarchy. Therefore `vertical_level`, `parent_ref`, and `depends_on_refs` are transparent POC body metadata only. `event_uid` remains the authoritative link. No roadmap view, rollup, dependency marker, or owner field grants authority or changes native lifecycle state.

The POC artifacts will be added only after this design is independently reviewed. This note creates none of them.

## Current deployment status

Deployment of the new MVP package is actively underway. The current, evidence-bounded status is:

| Area | Current status | Vertical treatment |
|---|---|---|
| Ledger image | Built successfully during the active deployment | Source/build work may be evidenced, but runtime and acceptance work remains `OPEN` |
| Viewer image | Built successfully during the active deployment | Same boundary |
| Registry image | Built successfully during the active deployment | Same boundary |
| Backup image | Blocked only on the service-account naming decision/correction | `OPEN`, with `delivery_status: blocked-service-account-name` |
| Dark stack start, migration, runtime health, conformance, restore, and replay | No completed evidence is recorded in this design note | `OPEN` |
| Governance adoption and exact compliance manifest | Not adopted | `OPEN` |
| Operator cutover and native-writer activation | Not accepted or recorded | `OPEN` |
| Bounded pilot and MVP acceptance | Not complete | `OPEN` |

Image build success is not container-runtime proof, cutover, recovery readiness, pilot readiness, or MVP acceptance. No work item in this POC is `CLOSED`.

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

All IDs use `VR-<date>-<namespace>-<NNN>`, with the initial namespace `townsquare`, for example `VR-20261006-townsquare-010`.

### Required event headers

| Field | Rule |
|---|---|
| `schema_version` | Exact target Vertical schema version. Never use a POC-only substitute. |
| `event_uid` | Unique authoritative event identifier and the target of all authoritative links. |
| `event_type` | Feature and Story openings use native `unit-of-work`. The Epic uses Vertical's existing project-level goal-or-priority decision event. The implementer must copy the exact event-type token from the target schema rather than inventing an enum in this POC. |
| `project` | `townsquare`. |
| `actor` | Actor creating the event. |
| `actor_provenance` | Provenance in the native Vertical shape. |
| `base_event_id` | Required for every transition and points to the immediately preceding event in that work item's chain. Omitted on an opening event. |

### Native lifecycle body fields

| Field | Rule |
|---|---|
| `goal` | Required on `OPEN`. |
| `definition_of_done` | Required JSON object on `OPEN`; includes testable results, acceptance references, and required evidence. |
| `workflow_ref` | Required on `OPEN`; pins the applicable workflow. |
| `artifact_ref` | Required for `RESOLVED`; points to implementation or other outcome evidence. It may also carry the TownSquare source opening hash. |
| `cites_decision` | Required for `RESOLVED` and `CLOSED`. On `CLOSED`, it must cite the authorized acceptance decision. |

### POC metadata: visible but non-enforced

| Field | Meaning |
|---|---|
| `vertical_level` | `Feature` or `Story`; display grouping only. |
| `parent_ref` | Opening `event_uid` of the display parent; not an enforced hierarchy. |
| `depends_on_refs` | Opening `event_uid` values for transparent sequencing; not a cross-story blocker mechanism. |
| `phase` | `MVP` or `VERTICAL_STAGE_2`. |
| `owner` | Accountable owner; assignment metadata, not authorization. |
| `delivery_status` | Operational nuance such as `source-implemented`, `deployment-active`, `runtime-evidence-pending`, or `blocked-service-account-name`; not a Vertical lifecycle state. |
| `acceptance_refs` | Stable criteria IDs from `docs/townsquare-mvp-v0-design-20261006.md`. |
| `evidence_refs` | Commits, paths, hashes, tests, and runtime evidence. |
| `townsquare_thread_ref` | Existing TownSquare thread reference when one exists. |
| `townsquare_opening_sha256` | Hash of the corresponding TownSquare opening/source record. It supplements, never replaces, `event_uid`. |

## Lifecycle and status rules

1. A Feature or Story begins with an `OPEN` `unit-of-work` event containing `goal`, JSON `definition_of_done`, and `workflow_ref`.
2. An outcome with sufficient evidence appends a `RESOLVED` transition. It receives its own `event_uid`, names the preceding event in `base_event_id`, supplies `artifact_ref`, and cites the resolution decision.
3. Acceptance appends `CLOSED` only after an authorized acceptance decision. It must cite that decision and chain from the immediately preceding event.
4. `in-progress`, `blocked`, `source-implemented`, `deployment-active`, and `runtime-evidence-pending` are `delivery_status` values, not Vertical lifecycle states.
5. Existing source-complete work may be `RESOLVED` where commits/tests and a resolution decision are available. Deployment, adoption, runtime, pilot, and future-phase work remains `OPEN`.
6. No item is `CLOSED` in the initial POC.
7. Feature rollups are projections only. A child transition does not mechanically transition its Feature.

## Work inventory

The references below are opening-event IDs. Later resolution or acceptance events receive different `event_uid` values and chain through `base_event_id`.

### Epic

**`VR-20261006-townsquare-001` — Deliver and accept the NAS-first TownSquare MVP, then enter Vertical Stage 2**

- Representation: project-level goal-or-priority decision, not `unit-of-work`.
- POC phase status: active.
- Owner: operator; Helio coordinates gates.
- Outcome: authoritative native ledger, governed writes, Registry, read surfaces, recovery, NAS activation, and bounded pilot, followed by separately gated Stage 2.
- Acceptance: an operator acceptance decision after the required core MVP criteria and bounded-pilot evidence pass.
- Evidence: `d7cc247`, `docs/townsquare-mvp-v0-design-20261006.md`.

### MVP Feature 1 — Native ledger and governed lifecycle

**`VR-20261006-townsquare-010` — Native ledger and governed lifecycle — `RESOLVED`**

- Owner: Bruce Lee. Parent metadata: `VR-20261006-townsquare-001`.
- Outcome/DoD: immutable native content/envelopes, Request lifecycle, archive, exact context retrieval, receipts, authority, idempotency, and crash atomicity; MVP-LDG-01–10, MVP-CMP-01–08, and MVP-ARC-01.
- Evidence: `4983c11`, `27c98ca`, `768fc0b`, `3818dee`, `7eea350`; migrations 010–014; Registrar native-ledger, lifecycle, context, governed-write, security, and conformance tests.

Stories:

- **`VR-20261006-townsquare-011` — Immutable native event/content core — `RESOLVED`.** Owner Bruce. DoD: canonical hashes, monotonic sequence, immutable envelope/content pairing, idempotent requests, and all-or-none transaction behavior. Evidence: `4983c11` and native-ledger tests.
- **`VR-20261006-townsquare-012` — Governed Request lifecycle and archive — `RESOLVED`.** Owner Bruce. Depends metadata on `VR-20261006-townsquare-011`. DoD: valid lifecycle succeeds; wrong actor, self-close, terminal reopen, and unauthorized override fail; logical archive preserves history. Evidence: `3818dee`, `7eea350`, lifecycle and security tests.
- **`VR-20261006-townsquare-013` — Context, receipt, and authority enforcement — `RESOLVED`.** Owner Bruce. Depends metadata on `VR-20261006-townsquare-011`. DoD: exact selected/retrieved context, action-bound single-use receipts, detached external authority proof, and reconstructable audit. Evidence: `768fc0b`, `1b0e315`, context and governed-write tests.

### MVP Feature 2 — Agent Registry integration

**`VR-20261006-townsquare-020` — Registry integration — `RESOLVED`**

- Owner: Bruce Lee. Parent metadata: Epic.
- Outcome/DoD: schema-2 Registry, durable journal/outbox, exactly-once Ledger audit delivery, and authenticated compatibility; MVP-REG-01–03 and MVP-OPS-11.
- Evidence: `8235a59`, `b308f21`, `4684276`, `91fd48c`, `ca6eaee`; Registry and conformance release suites.

Stories:

- **`VR-20261006-townsquare-021` — Registry roster lifecycle — `RESOLVED`.** DoD: register, update, retire, query; retirement never deletes history.
- **`VR-20261006-townsquare-022` — Atomic audit outbox and delivery acknowledgement — `RESOLVED`.** DoD: mutation/outbox atomicity, retry without duplicates, production-boundary acknowledgement. Evidence: `b308f21`, `ca6eaee`.
- **`VR-20261006-townsquare-023` — Directional peer readiness — `RESOLVED`.** DoD: distinct credentials and exact Ledger/Registry/audit-contract tuple fail closed when wrong or missing. Evidence: `4684276`, `91fd48c`.

### MVP Feature 3 — Read surfaces and notices

**`VR-20261006-townsquare-030` — Viewer, Crier, and projections — `RESOLVED`**

- Owner: Chuck Norris for Viewer; Bruce Lee for ledger projections.
- Outcome/DoD: read-only human views, deterministic projections, honest degraded state, and durable pointer notices; MVP-READ-01–03 and MVP-NTF-01–04.
- Evidence: `bcfef94`, `a0c6ef9`; Viewer, tracker, Registrar Crier, and notice tests.

Stories:

- **`VR-20261006-townsquare-031` — Native/historical Viewer boundary — `RESOLVED`.** Owner Chuck. DoD: native authority and historical metadata are distinguishable; Viewer cannot write.
- **`VR-20261006-townsquare-032` — Deterministic project/Crier projections — `RESOLVED`.** Owner Bruce. DoD: repeated projections are byte-identical and dependency loss renders UNKNOWN/DEGRADED.
- **`VR-20261006-townsquare-033` — Durable notice intents and attempts — `RESOLVED`.** Owner Bruce. DoD: pointer-only immutable intent/attempt history without shipping a notifier in the core profile.

### MVP Feature 4 — Secure portable release

**`VR-20261006-townsquare-040` — Secure portable release package — `OPEN`**

- Owner: Francis Ngannou. Depends metadata on `VR-20261006-townsquare-010`, `VR-20261006-townsquare-020`, and `VR-20261006-townsquare-030`.
- Delivery status: deployment active; Ledger, Viewer, and Registry images built; Backup image blocked on service-account naming.
- Outcome/DoD: exact digest-pinned release, offline reproducible build evidence, hardened Compose, and complete runtime security proof; MVP-PKG-01, MVP-PORT-01, MVP-OPS-01/02/09–11, and MVP-SEC-01–13.

Stories:

- **`VR-20261006-townsquare-041` — Compose, migrator, and container hardening contract — `RESOLVED`.** Evidence: `7756488`, `8235a59`, `cac8007`, release-blocker tests.
- **`VR-20261006-townsquare-042` — Offline build inputs and supply-chain tooling — `RESOLVED`.** Evidence: `24ee012`, `22a97f7`, offline-build tests.
- **`VR-20261006-townsquare-043` — Build and pin the exact release images — `OPEN`.** Delivery status: three service images built; Backup image blocked only on service-account naming. DoD: all images built, manifest image/config/SBOM digests resolved, clean Compose config recorded, no mutable tags.
- **`VR-20261006-townsquare-044` — Runtime security evidence — `OPEN`.** Owner GSP. Depends metadata on `VR-20261006-townsquare-043`. DoD: permissions, secrets, capability matrix, network confinement, inert rendering, CSP, limits, and external probes pass against the assembled release.

### MVP Feature 5 — Backup, restore, and rollback

**`VR-20261006-townsquare-050` — Recovery proof — `OPEN`**

- Owner: Francis Ngannou.
- Outcome/DoD: encrypted, signed, externally anchored backups; separate domain restores; production-boundary replay; safe rollback; MVP-OPS-03–08 and MVP-SEC-09.

Stories:

- **`VR-20261006-townsquare-051` — Isolated restore and separate replay tooling — `RESOLVED`.** Evidence: `67e89eb`, `e3903df`, `ca6eaee`; recovery suites.
- **`VR-20261006-townsquare-052` — Build and exercise the Backup image — `OPEN`.** Delivery status: blocked only on service-account naming. Depends metadata on `VR-20261006-townsquare-043`. DoD: image build, encrypted domain backups, signature, external checkpoint, empty-directory restore, and exactly-once replay evidence.
- **`VR-20261006-townsquare-053` — Pre-write and post-write rollback rehearsal — `OPEN`.** Depends metadata on `VR-20261006-townsquare-052`. DoD: pre-write rollback preserves data; post-write rollback stops writes and preserves the new ledger for forward repair.

### MVP Feature 6 — Governance activation

**`VR-20261006-townsquare-060` — Adopt the compliance manifest — `OPEN`**

- Owner: operator; main session prepares; GSP reviews.
- Outcome/DoD: exact Doctrine, Rules of Engagement, binding, workflow, scope/work order, notes, and acceptance documents are externally adopted with protected, current scope/authority evidence.

Stories:

- **`VR-20261006-townsquare-061` — Pin exact governing sources and hashes — `OPEN`.** Evidence inputs exist under `docs/governance/`; candidate status is not adoption.
- **`VR-20261006-townsquare-062` — Review authority, expiry, revocation, and scope — `OPEN`.** Depends metadata on `VR-20261006-townsquare-061`.
- **`VR-20261006-townsquare-063` — Record protected operator adoption — `OPEN`.** Depends metadata on `VR-20261006-townsquare-062`; only the operator can complete it.

### MVP Feature 7 — NAS deployment, cutover, and acceptance

**`VR-20261006-townsquare-070` — Deploy and accept the MVP — `OPEN`**

- Owner: Francis Ngannou for deployment; Ronda Rousey for QA; operator for activation and acceptance.
- Delivery status: deployment active.
- Depends metadata on `VR-20261006-townsquare-040`, `VR-20261006-townsquare-050`, and `VR-20261006-townsquare-060`.
- Outcome/DoD: pinned dark deployment, live conformance/recovery evidence, operator-approved activation, and bounded pilot. Every core MVP acceptance row except the explicitly excluded wake rows must pass.

Stories:

- **`VR-20261006-townsquare-071` — Revalidate the NAS and legacy baseline — `OPEN`.** DoD: capture current host, storage, containers, sockets, firewall/NAT, selected ports, and existing-service state. Historical facts are not silently carried forward.
- **`VR-20261006-townsquare-072` — Assemble and start the dark stack — `OPEN`.** Delivery status: image-build phase active. DoD: Backup image blocker cleared, exact release assembled, each domain migrated once, runtime schemas and directional compatibility healthy.
- **`VR-20261006-townsquare-073` — Execute runtime conformance and fault testing — `OPEN`.** Owner Ronda. DoD: source, container, restart, migration, security, stop, backup, restore, replay, and degradation suites produce pinned evidence.
- **`VR-20261006-townsquare-074` — Approve exact cutover — `OPEN`.** Owner operator. DoD: decision cites exact SHA, image digests, commands, ports, transport mode, trust material, rollback boundary, and cutover moment.
- **`VR-20261006-townsquare-075` — Activate constrained native writers — `OPEN`.** Depends metadata on `VR-20261006-townsquare-074`. DoD: loopback/SSH-tunnel profile enabled, Drive removed from normal runtime authority, legacy source preserved as historical fallback.
- **`VR-20261006-townsquare-076` — Complete bounded pilot and accept MVP — `OPEN`.** DoD: day-0, day-7, day-14, and any selected day-28 evidence recorded; operator acceptance decision required for `CLOSED`.

## Vertical Stage 2 boundary and roadmap

Stage 2 is not required for MVP acceptance unless a later operator decision explicitly changes scope. Its design may begin after the deployed runtime contracts freeze. Its implementation begins only after MVP acceptance unless the operator knowingly authorizes parallel risk. No calendar estimate is asserted while the active deployment still has an unresolved Backup image identity blocker and pending runtime evidence.

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

1. service-account naming is settled and the Backup image builds;
2. the exact release manifest and all image/config/SBOM digests are captured;
3. dark runtime health, migrations, backup, restore, and replay pass;
4. the operator records governance, transport, trust-material, and cutover decisions; and
5. the bounded pilot starts, establishing its actual day-7/day-14/day-28 dates.

Stage 2 design begins after runtime contracts freeze. Stage 2 implementation begins after the MVP acceptance decision unless separately authorized. This milestone-based forecast is more honest than converting remaining gates into an unsupported calendar date.

## Migration into native Vertical

1. Freeze and SHA-256 hash `townsquare-work-events.jsonl` at the migration boundary.
2. Validate required headers, native event types, unique `event_uid` values, ID format, opening fields, transition fields, and all references.
3. Create the Epic through Vertical's native project-level goal-or-priority decision type.
4. Replay each Feature and Story opening as `unit-of-work`, preserving evidence and TownSquare source hashes.
5. Replay `RESOLVED` and any later `CLOSED` events in order, using distinct event IDs and the immediately preceding `base_event_id`.
6. Preserve `vertical_level`, `parent_ref`, and `depends_on_refs` as visibly non-enforced metadata unless the target Vertical release has adopted explicit corresponding contracts.
7. Write `docs/vertical-poc/migration-map.json`, mapping every POC `event_uid` to the accepted native `event_uid` when preservation is not possible.
8. Compare source/native event counts, latest lifecycle state per opening, artifact hashes, citations, and generated roadmap.
9. Mark the POC ledger read-only. Never delete it or rewrite its history to imitate native IDs.

## Alternative rejected

An external tracker such as Notion, a spreadsheet, or GitHub Issues was rejected for the POC. It would introduce a second mutable authority, weaker transition provenance, and a separate migration problem. A hand-maintained Markdown-only roadmap was also rejected because it cannot reliably validate transition chains or regenerate state. Git-tracked JSONL plus a generated Markdown projection is the smallest solution that preserves auditability and later migration.

## WORK ORDER

- **Document:** main session — retain this design note as the single decision record for the POC; update it only through reviewed design changes.
- **Decision review:** Jackie Chan — independently examine event identity, transition ordering, JSON field shapes, evidence/reference integrity, and native migration mapping; raise her own concerns before implementation.
- **Implement:** Bruce Lee — only after the decision review gate, create the JSONL ledger, schema, deterministic projector, and generated roadmap at the exact paths above; do not modify TownSquare runtime code.
- **Peer review:** Ip Man — verify the artifacts match the reviewed design and do not imply enforced hierarchy, blockers, acceptance, or deployment results.
- **QA:** Ronda Rousey — validate schema conformance, unique `VR-*` IDs, required headers, opening/transition requirements, `base_event_id` chains, no dangling references, status/evidence consistency, deterministic rendering, and exact regeneration from a clean worktree.
- **Coordinate:** Helio Gracie — checkpoint the decision review, implementation, and QA handoffs; gateway the exact artifact commit and every open discrepancy.
- **Watch for:** conflicts with Francis's concurrent Backup Dockerfile/test work; stale NAS facts; treating image builds as runtime proof; closing work without an acceptance decision; making `parent_ref` or `depends_on_refs` sound enforced; replacing `event_uid` with TownSquare hashes; or allowing Stage 2 gaps to become silent MVP prerequisites.
