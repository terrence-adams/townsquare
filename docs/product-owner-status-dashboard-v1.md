# Product-owner status dashboard v1

**Status:** accepted design pending independent contract review  
**Decision owner:** operator / Eddie Brock  
**Operator decision:** “accepted and agreed.” — 2026-10-09  
**Architect:** ip-man  
**Feature:** `PO-STATUS-001 — Cross-project product-owner status surface`  
**Demo target:** 2026-10-23

## 1. Purpose and boundary

Provide Eddie Brock a read-only Streamlit page that periodically surfaces current cross-project work with context: lifecycle status, responsible owner, evidence and time, blocker, next step, freshness, decisions, dependencies, and conflicts.

This is a separate feature. It does not reopen, widen, reinterpret, or add acceptance criteria to the accepted Sentinel1/Bishop synthetic investigation milestone. In particular, it does not add real-data ingestion, polling, notification, authentication, deployment, or production-hardening requirements to that completed milestone and does not modify its artifacts or evidence.

The UI consumes one neutral status-snapshot object. The object is independent of Codex, email, mobile, GUI, TownSquare, or any particular provider. Any future verified producer can emit the same object without changing the viewer.

The feature contains three initial stories:

1. `PO-STATUS-001.1` — v1 contract, validator, read-only file adapter, transforms, and atomic publisher.
2. `PO-STATUS-001.2` — read-only Product owner Streamlit page.
3. `PO-STATUS-001.3` — hourly coordination heartbeat as the first producer.

Every future producer or source adapter requires its own approved story.

## 2. Controlling Unknown rule

`UNKNOWN` is an evidence condition. It is not failure, denial, blocking, completion, or required action.

> An agent may block or refuse because of an Unknown field only when it cites the exact acceptance criterion or explicit safety boundary that requires the missing information.

The closed Unknown reason set is:

- `NOT_RECORDED`
- `SOURCE_UNAVAILABLE`
- `RESTRICTED`
- `AMBIGUOUS`
- `CONFLICTING_SOURCES`

The consumer never turns Unknown into `NONE`, selects a winner among conflicting sources, or derives a fact from activity, commentary, authored prose, or a recent heartbeat.

## 3. Canonical snapshot

The top-level object is closed and contains exactly:

```json
{
  "schema": "ynm.product-owner-status",
  "version": 1,
  "generated_at": "2026-10-09T15:00:00Z",
  "product_owner": {
    "id": "eddie-brock",
    "display_name": "Eddie Brock"
  },
  "producer": {
    "id": "hourly-product-owner-status",
    "kind": "SCHEDULED_COORDINATOR"
  },
  "coverage": {
    "state": "COMPLETE"
  },
  "sources": [],
  "workstreams": []
}
```

Rules:

- `schema` is exactly `ynm.product-owner-status`.
- `version` is integer `1`.
- `generated_at` is a UTC RFC 3339 timestamp ending in `Z` for the completed, validated snapshot.
- More than two hours old is globally stale. More than five minutes in the future is invalid.
- `product_owner.id` is a stable public logical identity. v1 uses `eddie-brock`.
- `producer.kind` is `SCHEDULED_COORDINATOR`, `SERVICE`, or `MANUAL_EXPORT`.
- `producer.id` is a stable logical name and may not contain a run UUID, Codex thread ID, provider session ID, process ID, token, or credential reference.
- `coverage.state` is `COMPLETE` or `DEGRADED`.
- All undeclared keys fail validation.

An empty `workstreams` array with complete coverage means verified no current work. An empty array with degraded coverage means current work is unknown. Counts in degraded coverage are lower bounds and render as `≥N`.

## 4. Source records

Each closed source object contains:

```json
{
  "id": "townsquare-native",
  "kind": "NATIVE_LEDGER",
  "state": "AVAILABLE",
  "observed_at": "2026-10-09T14:59:55Z",
  "ref": "townsquare:projection:ledger-seq-842"
}
```

- `kind` is `NATIVE_LEDGER`, `STRUCTURED_STATUS_FEED`, or `MANUAL_VERIFIED`.
- `state` is `AVAILABLE`, `UNAVAILABLE`, `RESTRICTED`, or `UNKNOWN`.
- `observed_at` and `ref` are required for `AVAILABLE` and null otherwise.
- `ref` is an inert evidence locator, never a fetched URL.
- Source IDs are unique. Every workstream source reference resolves to one source object.

## 5. Workstream records

The array contains current, nonterminal work only. Absence never proves completion when coverage is degraded.

Every closed workstream object contains:

- stable `id` and inert `title`;
- `project`;
- `lifecycle`;
- `responsible`;
- `evidence`;
- `blocker`;
- `next_step`;
- `freshness`;
- `decision`;
- `dependencies`;
- `conflicts`;
- `source_ids`.

### Project and responsible identity

`project.state` and `responsible.state` are `KNOWN` or `UNKNOWN`.

- `KNOWN` project requires stable `id` and `display_name`.
- `KNOWN` responsible requires `kind` of `HUMAN`, `AGENT`, or `TEAM`, plus stable logical `id` and `display_name`.
- `UNKNOWN` requires one closed Unknown reason.
- Agent identities such as `bruce-lee` are permitted. Provider session IDs are prohibited.

### Lifecycle

`lifecycle.status` is one of:

- `PLANNED` — explicitly accepted or scheduled; execution not started.
- `ACTIVE` — explicitly in progress.
- `BLOCKED` — explicit source evidence says progress cannot continue.
- `AWAITING_DECISION` — the next transition requires recorded acceptance or another decision.
- `PAUSED` — an authorized source explicitly placed work on hold.
- `UNKNOWN` — cited evidence does not establish the current state.

`changed_at` is the source transition time or null only for `UNKNOWN`. There are no terminal statuses in v1; terminally evidenced work disappears only from a complete snapshot.

### Evidence

`evidence.refs` contains closed `{ref, recorded_at}` objects. `verified_at` records when the producer checked them.

- Every non-Unknown lifecycle requires at least one evidence reference and `verified_at`.
- Activity, commentary, an agent’s running state, or heartbeat recency is not evidence of lifecycle or completion.
- When no verified evidence exists, lifecycle is `UNKNOWN`, refs are empty, and `verified_at` is null.

### Blocker

`blocker.state` is `NONE`, `KNOWN`, or `UNKNOWN`.

- `NONE` requires structured authoritative evidence that no blocker exists.
- `KNOWN` requires lifecycle `BLOCKED` and a 1–500 character inert summary copied from an explicit structured blocker or lifecycle field.
- `BLOCKED` requires blocker `KNOWN` or `UNKNOWN`; it cannot use `NONE`.
- A semantically explicit TownSquare `BLOCKED` event body may be copied verbatim and capped. Other prose is never interpreted as a blocker.

### Next step

`next_step.state` is `KNOWN` or `UNKNOWN`.

- `KNOWN` requires an explicit structured 1–500 character summary.
- `UNKNOWN` requires one Unknown reason.
- There is no inference from lifecycle name, comments, activity, or authored prose.
- `UNKNOWN / NOT_RECORDED` is the safe value when no structured next step exists.

### Freshness

`freshness` is `FRESH`, `STALE`, or `UNKNOWN`.

- `FRESH`: `verified_at` exists and was no more than 24 hours old at publication.
- `STALE`: `verified_at` exists and was older than 24 hours.
- `UNKNOWN`: verification time is absent or conflicting.
- The viewer recomputes age and may downgrade but never upgrade producer freshness.
- A globally stale snapshot makes every displayed workstream at least stale.

### Decisions

`decision.state` is `NONE`, `REQUIRED`, or `UNKNOWN`.

- `REQUIRED` requires a structured 1–500 character summary.
- `AWAITING_DECISION` requires decision `REQUIRED`.
- The KPI counts only `REQUIRED`; Unknown is neutral.

### Dependencies and conflicts

Each dependency has `ref`, `state`, and an Unknown reason only when state is `UNKNOWN`. State is `READY`, `WAITING`, or `UNKNOWN`. Waiting or Unknown never implies lifecycle `BLOCKED`.

Each conflict contains a field and at least two valid source IDs. Conflict fields are `PROJECT`, `LIFECYCLE`, `RESPONSIBLE`, `EVIDENCE`, `BLOCKER`, `NEXT_STEP`, `DECISION`, or `DEPENDENCY`. The affected field becomes `UNKNOWN / CONFLICTING_SOURCES`, workstream freshness becomes `UNKNOWN`, and neither producer nor viewer selects a winner.

## 6. Bounds and frontend minimization

- File: at most 1 MiB.
- Workstreams: at most 256.
- Sources: at most 32.
- Evidence refs, dependencies, and conflicts: at most 20 each per workstream.
- Stable IDs: 1–200 characters.
- Display names and titles: 1–300 characters.
- Blocker, next-step, and decision summaries: 1–500 characters.
- Reference strings: 1–500 characters.
- IDs are unique within scope.
- All timestamps are UTC and end in `Z`.

The viewer constructs new scalar strings and lists for these frontend columns only: Project, Workstream, Status, Responsible, Evidence refs, Evidence recorded, Verified at, Blocker, Next step, Freshness, Decision, Dependencies, Conflicts, and Sources. Raw dictionaries, raw JSON, undeclared keys, credentials, provider/session identifiers, and hidden sensitive columns never reach Streamlit elements.

## 7. Runtime file interface

The viewer reads the absolute path in `PRODUCT_OWNER_STATUS_PATH`.

Recommended container path:

```text
/run/product-owner-status/product-owner-status-v1.json
```

The host setting `PRODUCT_OWNER_STATUS_DIR` mounts the directory read-only at `/run/product-owner-status`. The directory is mounted rather than the file because atomic replacement changes the target inode.

Consumer rules:

- no directory scan, glob, fallback discovery, or write;
- read at most 1 MiB plus one byte;
- require UTF-8 JSON with a top-level object;
- validate the complete closed contract before returning data;
- expose only sanitized typed errors, never host path, raw payload, or traceback;
- cache only the validated load with five-minute TTL, maximum two entries;
- manual refresh clears only this loader cache.

## 8. Atomic publisher

Exactly one producer owns the configured target in v1. The standard-library publisher:

1. assembles and validates the complete snapshot in memory;
2. creates a unique temporary file in the same directory;
3. writes UTF-8 JSON plus a trailing newline;
4. flushes and `fsync`s the temporary file;
5. revalidates the exact bytes to publish;
6. replaces the target with `os.replace`;
7. `fsync`s the containing directory where supported;
8. preserves the previous valid target on any failure;
9. never truncates or rewrites the live target in place.

The publisher has no ledger-write capability. Publication of a runtime snapshot does not change governance state.

## 9. Initial hourly producer

The coordination heartbeat is the first scheduler, not part of the contract identity. It invokes the publisher once per hour using only verified structured interfaces.

It must not:

- read Codex internal databases, transcript stores, provider metadata, or process state;
- expose Codex thread IDs or provider session IDs;
- treat recent commentary, activity, or a running agent as progress or completion;
- summarize prose into lifecycle, blocker, next step, decision, dependency, or conflict;
- overwrite the last valid snapshot after validation or publication failure.

TownSquare native projection is one permitted source. Initial mapping is:

| Native value | Snapshot value |
|---|---|
| `OPEN` | `PLANNED` |
| `WORKING` | `ACTIVE` |
| `BLOCKED` | `BLOCKED` |
| `RESOLVED` | `AWAITING_DECISION` with decision `REQUIRED` |
| authoritative addressee | responsible |
| current event ID and committed time | evidence reference and recorded time |
| producer observation time | evidence `verified_at` |
| explicit blocked-event body | blocker `KNOWN` |
| explicit structured `next_step` | next step `KNOWN` |
| absent next step | `UNKNOWN / NOT_RECORDED` |

Restricted or unavailable data produces degraded coverage and typed Unknown values. Closed/cancelled work disappears only with terminal lifecycle evidence and complete coverage.

## 10. Streamlit page

Add “Product owner” to the current top navigation while retaining “Native ledger” as default.

One sequential fragment owns live content:

```python
@st.fragment(run_every="5m", key="product_owner_status")
```

It shows snapshot generation and viewer refresh-completion times in UTC, plus a `Refresh status` button with `:material/refresh:` that clears only the snapshot loader cache.

Metrics:

- Active: `PLANNED` + `ACTIVE`.
- Blocked: explicit `BLOCKED` only.
- Decisions required: decision `REQUIRED` only.
- Stale/unknown: the union of stale/unknown freshness, unknown lifecycle, unresolved conflicts, or a globally stale snapshot.

Categories may overlap and metric help text states that fact. Degraded coverage renders lifecycle counts as lower bounds. The page uses native Streamlit containers, metrics, captions, warnings, and a read-only dataframe. It uses no custom HTML/CSS, `st.data_editor`, row actions, approval controls, or deprecated `use_container_width`.

## 11. Failure behavior

- Missing environment path or unavailable/oversize/malformed/invalid file: four `—` metrics, sanitized unavailable message, and no rows.
- Globally stale valid file: render with a strong warning and count every row stale/unknown.
- Complete empty snapshot: zero metrics and verified-no-current-work message.
- Degraded empty snapshot: `≥0` metrics and current-work-unknown message.
- Restricted source: no restricted content or identity; aggregate warning only.
- Ambiguous/conflicting field: Unknown with reason; no source winner.
- Unknown blocker, next step, dependency, or decision: neutral display, not red failure.
- Producer failure: prior valid snapshot remains and ages visibly into stale.

## 12. Acceptance criteria

1. Strict validator enforces the closed v1 shape, bounds, enums, timestamps, references, and cross-field invariants.
2. Every Unknown reason renders neutrally and never increments blocked or decisions-required counts.
3. No contract field names Codex, a provider, a provider session, or TownSquare-specific structure.
4. Publisher validates before same-directory atomic replacement and preserves the previous valid file on simulated failure.
5. Viewer reads only `PRODUCT_OWNER_STATUS_PATH`, applies the 1 MiB bound, and never scans or writes.
6. Product owner page is registered in existing top navigation.
7. Every row exposes only the documented frontend allowlist.
8. Four KPIs and degraded lower-bound behavior match this design.
9. Page-only five-minute refresh and manual cache-local refresh work; both refresh times are visible.
10. Every failure/empty/stale/restricted/ambiguous/conflicting case degrades distinctly without fabricated zeroes.
11. Pure and AppTest tests prove undeclared/raw/provider/session/credential fields cannot reach the dataframe.
12. No code parses commentary, authored prose, activity, or internal session state into factual status.
13. Existing AST checks continue to find no mutating HTTP calls or ledger-write endpoints in viewer code.
14. No Sentinel1/Bishop file, criterion, evidence artifact, status, or implementation changes.
15. Pure contract/transform/atomic-publish tests and first-party Streamlit navigation/render/manual-refresh tests pass.

Validation from `C:\Workspace\TownSquare-MVP`:

```powershell
python -m unittest viewer.test_product_owner_status -v
python -m unittest tests.test_publish_product_owner_status -v
python -m unittest viewer.test_viewer -v
python -m unittest viewer.test_read_gateway -v
```

Do not start or deploy the app, modify the scheduler, or publish a live snapshot during acceptance.

## 13. Ownership and handoffs

**Contract and publisher — bruce-lee:**

- `viewer/product_owner_status.py`
- `tools/publish_product_owner_status.py`

**UI and runtime wiring — chuck-norris:**

- `viewer/streamlit_app.py`
- `viewer/app_pages/product_owner.py`
- `viewer/compose.yml`
- `viewer/env.example`
- `viewer/README.md`

**QA — ronda-rousey:**

- `viewer/test_product_owner_status.py`
- `viewer/test_viewer.py`
- `tests/test_publish_product_owner_status.py`

No one changes `viewer/registrar_client.py`, Registrar or Registry schema, ledger schema, accepted Sentinel1/Bishop artifacts, or unrelated dirty-tree files.

Before implementation, jackie-chan independently reviews this exact contract, cross-field invariants, atomic handoff, coverage semantics, and Unknown/conflict behavior. After implementation, bruce-lee reviews the UI and jackie-chan reviews the validator/publisher. Ronda then performs independent QA. Helio checkpoints every handoff.

## 14. Cost and stop conditions

- Accepted functionality: maximum six engineering hours.
- Mandatory acceptance tests: maximum 2.5 hours.
- Decision documentation and independent review: maximum 1.5 hours.
- Optional hardening or additional producers: zero hours in this feature.

Stop and create a separate work item if any producer requires an upstream schema change, authentication project, background service, Codex-internal read, or interface beyond an existing verified structured source.
