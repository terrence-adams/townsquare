# TownSquare as the Working Default — architecture decision and DRAFT Vertical package

Status: **DRAFT / PENDING_OPERATOR_APPROVAL**  
Governance review: **APPROVAL-READY — full Kano follow-up confirms all seven blockers closed**  
Planning date: 2026-10-09  
Product owner: **Eddie Brock — OpenAI agent in the current session on host Venom**  
Design owner: Ip Man  
Official development environment: **Sentinel One**  
Live production product/environment: **NAS**  

Cable and Bishop are proposed implementation resources who may work on Sentinel One. They are not environments. “Andy Brock” and “Bita” are not valid names for the product owner or current host in this package.

This document is planning only. It does not append to the authoritative NAS ledger, alter a live work-item status, dispatch an implementer, deploy, contact another session, post externally, or authorize consequential action.

## 1. Outcome and smallest coherent program

Make TownSquare—not Google Drive—the normal place where operator engagements are received, immutably receipted, routed, traced, acted on under explicit authority, and reconciled to outcomes. The MVP joins five existing boundaries without collapsing them:

1. **TownSquare** owns communication, immutable audit receipts, protected evidence, and causal trace.
2. **Registry** owns agent identity, vendor, host, exact session, parent/delegator/sub-agent lineage, lifecycle, safe public trace references, and private provider locators.
3. **Vertical** owns authorized work lifecycle and independent acceptance.
4. **Revere** owns durable directed transport, delivery leases, acknowledgement, redelivery, replay, and bilateral vendor adapters.
5. **Iron Curtain** owns policy plus canonical exact-action permit issuance, single-use opaque bearer verification/consumption, and safe `permit_id` trace for material actions.

The new program does not duplicate the approved Session Registry/Revere work under `YNM-EPIC-022`. It adds the missing default-path, authority, audit, environment, promotion, client-adoption, and Drive-reconciliation work, plus explicit amendments/migration coordination for those live items.

## 2. Evidence levels

| Level | Meaning |
| --- | --- |
| `O` | Current controlling operator statement or decision in this planning turn. |
| `A` | Authoritative NAS record independently verified by the coordinating session. |
| `R` | Repository contract/evidence previously retrieved in this pipeline and relayed with a concrete path or symbol. Direct re-read is pending because the local shell currently fails before launch. |
| `C` | Read-only preflight observation reported by Cable and supplied verbatim by the operator; useful evidence but pending independent verification where it conflicts with `A`. |
| `U` | Open verification need; do not treat as established fact. |

The shell and two read-only explorers failed before process launch with `helper_unknown_error: apply deny-read ACLs`. Therefore this note distinguishes operator-controlled facts and previously relayed repository evidence from facts still requiring a clean read-only verification pass.

## 3. Current-state findings and target state

| Area | Current finding | Level | MVP target | Open verification/evidence needed |
| --- | --- | --- | --- | --- |
| Product ownership | Eddie Brock is the OpenAI agent in this current session on Venom; exact registered ID `eddie-brock` was previously verified. | `O/R` | Every Epic/Feature/Story names Eddie as product owner/accountable coordinator where applicable. | Reconfirm active registration/revision at filing; do not substitute a display name. |
| Environments | Sentinel One is the official TownSquare/Town Watch MVP development environment; NAS is live production. Bruce's earlier local implementation was stopped after this decision. Cable reports Sentinel One reachable as `batman`, with 8 cores, 30 GiB RAM, and 366 GB free. | `O/C` | All new work occurs in isolated Sentinel One branches/worktrees after the mandatory safety/bootstrap gate; only independently verified release artifacts are promoted to NAS. | Independently verify host/resources and inventory stopped implementation by commit/diff before migration. |
| Drive/default path | Google Drive remains the operational publication interface/system of record in practice. | `O` | TownSquare native intake and receipts become the default; Drive becomes a reconciled read-only historical/reference source after cutover. | Inventory active Drive flows, clients, documents, duplicate IDs, and any facts absent from TownSquare. |
| Charter | `docs/governance/townsquare-charter-v1.0-adoption-record-20261007.md` records `ADOPTED — EFFECTIVE` at 2026-10-07T05:40:06.0363929Z, decision `TS-CHARTER-1.0-ADOPTION-20261007T0540060363929Z`, release commit `14a91f41…`, tree `842ab0…`. The adoption explicitly does not authorize implementation, deployment, activation, governed writes, or restore closure. | `A/R` | Extend the adopted Charter with the default-path binding/action matrix; do not “re-adopt” or infer implementation authority. | Verify the seven adopted component versions and append-only amendment mechanism before filing S1. |
| Vertical | Vertical uses append-only Git-tracked compatibility records; metadata records ownership/relationships but grants no authority. Normal lifecycle and independent close/acceptance apply. | `R`: `docs/vertical-poc/README.md`, `townsquare-vertical-poc-design.md` | Native TownSquare intake links to Vertical authority without becoming the authority source. | Re-read current schemas/events and verify exact append tooling before approved filing. |
| Live work | The coordinator independently verified authoritative records `VR-20261009-ynm-038.0/.1` through `VR-20261009-ynm-044.0`: `SESSION-REGISTRY-MVP` and `SESSION-REGISTRY-PERSIST-LIFECYCLE` are `WORKING`; `SESSION-REGISTRY-PROTECTED-LOOKUP` and all three Revere keys are `OPEN`. Cable's `OPEN-PARKED`/missing-Registry view conflicts and is treated as a stale read/projection discrepancy. | `A/C` | Preserve canonical live identities/states; reconcile stale projections and file explicit amendments rather than duplicates. | Retrieve current watermark/revisions again immediately before amendment; identify and repair the stale reader/projection rather than changing authoritative state to match it. |
| Registry | Current Registry owns a separate SQLite schema; its mutation pattern is authenticated/idempotent and atomically writes projection, immutable journal, and audit outbox. Registration does not grant operator authority. Cable reports Registry source in Wonderland and the live service on NAS `:8789`, not Sentinel One. | `R/C` | Add exact session/parent/delegator/lineage/private locator fields and safe public trace refs through the already-live Registry work, then establish a Sentinel One dev instance from canonical source. | Verify current branch/schema version, live NAS revision, source provenance, and whether stopped Bruce changes already implement fields or migrations. |
| Revere | Existing Revere v1 provides authenticated directed Publish/Subscribe. Authentication resolves immutable `Principal(name, agent_ids)` and enforces ownership. Cable reports live `revere.service` on Sentinel One at `192.168.2.101:50051` from `/opt/revere`, with agent inbox/dispatch/bridge tools and passing self-check. | `R/C` | Preserve the live service while isolated development completes the already-open Phase-2 durable mailbox/ACK/replay and Codex↔Claude adapters from a branchable source baseline. | Verify installed artifact/source digest, service unit/config, live traffic boundary, and a clean non-live dev port before Cable/Bishop work. |
| Iron Curtain | The canonical contract is live as `IRON-CURTAIN-PERMIT-POC-CONTRACT`, `VR-20261008-ynm-047.5-WORKING`, event UID `01a11b70-b9f3-76e2-80f6-ffdc9d6b461c`, with `implementation_authorized=false` and contract rework authorized. Bruce may correct only three contract files, followed by Jackie/GSP re-review. TESTS `VR-048`, IMPLEMENT `VR-049`, REVIEW `VR-050`, and CANARY `VR-051` are `OPEN` and dependency-blocked. Cable reports no Iron Curtain tooling on Sentinel One. | `A/R/C` | Reuse the exact-action, 120-second, single-use, opaque HMAC-hashed bearer contract after its canonical live gates pass; add a separate authenticated non-authorizing intake route without silently changing `POST /v1/events`. | Retrieve the exact three-file correction scope and current revisions before any work; do not start dependent implementation through this new package. |
| Engagement receipts | Automatic receipt creation for every operator engagement is required but not yet proven as middleware-enforced. | `O/U` | TownSquare intake commits an immutable receipt and protected exact evidence before routing or rejecting every engagement. | Locate any current intake middleware/event schema/evidence store and test receipt completeness. |
| Town Watch | Town Watch MVP belongs on Sentinel One; visibility through Crier does not prove native TownSquare use. | `O` | Town Watch becomes the first acceptance client using native intake/receipts, Registry identity, Revere delivery, and Iron Curtain material-action gates. | Inventory Town Watch clients, endpoints, Crier coupling, and current publication path. |
| Native operator interface | Incomplete or unproven. | `O/U` | A minimal native operator console/API accepts engagements, returns receipt IDs, shows delivery/outcome state, and requires no Drive publication step. | Verify any existing UI/CLI/API implementation before choosing reuse versus amendment. |
| Release/backup | Coordinator verified `release-manifest.json` schema 2 at commit `7eea350…`: images, wheelhouse, SBOM, and offline build inputs are unresolved; `evidence_status` is `TEMPLATE_NOT_RELEASE_EVIDENCE` and status is `template-not-deployable`. Independent release, backup/restore, NAS promotion, and rollback evidence remain incomplete. | `A/O` | Establish a branchable/buildable baseline, then produce content-addressed release, independent QA, pre-promotion backup, restore proof, scoped deployment permit, and bounded rollback evidence. | Inspect current release scripts, NAS topology, database locations, backup tooling, and recovery objectives; never promote the template manifest. |
| Production boundary | Cable reports `/mnt/nasonemic` is mounted read-write for `batman` with file mode `0664`/directory mode `0775`. During a purported read-only preflight, Cable accidentally created the hidden zero-byte production-ledger file `/mnt/nasonemic/Projects/Vertical/ledger/.cable-write-probe` at 2026-10-09 04:08 local; it remains present. | `C` reproducible incident | Development identities cannot write NAS. Production mutations use the gated production path only. The exact stray file is remediated only under explicit one-file operator authorization with before/after receipts. | Independently verify mount/ACL/file metadata without changing it; preserve incident evidence; determine affected directory listing/hash; obtain explicit cleanup authority. |

### 3.1 Cable preflight provenance and bootstrap gaps

The following are **Cable-reported preflight observations**, not yet independently re-run by this planning task:

- Identity: registered `cable`, Anthropic agent on host Cable/Ubuntu; Sentinel One SSH login is `batman`.
- Sentinel One has no branchable TownSquare MVP Git checkout. `~/Repo/townsquare` is clean `main` at prototype commit `4726278` (2026-09-17). MVP material exists only as extracted release trees/tars under `~/townsquare-mvp-{cc73f7c,c2440a39,aa2aeb5}-dev-20261008` and `~/townsquare-staging/{cc73f7c,aa2aeb5}/source.tar`; their manifests say `template-not-deployable`.
- Town Watch source is a clean Wonderland checkout at commit `e7990f3`, under `services/townwatch` and `services/townwatcher`; it is not running.
- Extracted TownSquare canaries exist: `cc73f7c` loopback Docker and `aa2aeb5` fix. User `batman` cannot access the Docker socket. Nginx/Docker are active; reported endpoints are loopback `18790` docs `200` with no `/health`, `18503` record-not-found JSON, and `18502` healthy Streamlit viewer. Port `8501` is Cerebro, not Town Watch.
- Revere is live on Sentinel One. Registry is live on NAS. No Iron Curtain tooling is installed on Sentinel One, although its approved/design artifacts exist on Venom.
- Vertical source/archive is staged read-only at `~/vertical-staging/40058d2`, with a separate NAS ledger mount.
- Sentinel One→Bishop SSH currently fails host-key validation; system Python 3.14.4 lacks pytest; push protection rejects the configured Git email.
- Four untracked Dojo documents exist in `~/Repo/revere/docs`; Cable also reports untracked Adjunct PoC documents outside Sentinel One. These are user-owned/unreviewed and must not be erased or silently included.
- The Adjunct PoC remains subordinate to its `WORKING` Story and Iron Curtain permit; request-hash and dispatch-count interpretation are unresolved and outside this default-cutover MVP.

These observations establish prerequisites, not permission to install, change ACLs, delete the probe, trust a host key, rewrite Git history, start services, or copy extracted trees into a canonical branch.

## 4. Target architecture and trust boundaries

### 4.1 End-to-end flow

```text
Operator / authenticated agent
        |
        v
TownSquare native intake middleware
  - immutable engagement event + safe receipt
  - protected exact evidence + exact-content digest
  - transactional outbox
        |
        +--> ordinary non-authorizing communication/audit post
        |        (authenticated append; no per-message permit)
        |
        +--> material action request
                 |
                 v
          Iron Curtain verification
          (permit -> exact-action opaque bearer -> permit_id trace)
                 |
                 +--> Vertical state mutation / Registry mutation /
                 |    Revere administrative action / release or deploy
                 |
                 v
          owning service transaction + immutable event/outbox
                 |
                 v
            outcome receipt in TownSquare
```

Imperative wording in a post never changes its class. The called operation and policy matrix decide whether an action is material. A post saying “deploy now” is still only a non-authorizing statement until a permitted deploy operation is invoked.

### 4.2 Boundary table

| System | Owns | Must not own or imply |
| --- | --- | --- |
| TownSquare | communication events, engagement receipts, safe summaries, protected evidence, causal links, routing/interpretation, outcomes | agent identity truth, provider locator disclosure, work authorization, transport delivery state, permit issuance |
| Registry | stable agent identity; vendor; host; canonical session UUID; private provider locator; parent session; delegator; lineage; lifecycle; safe public trace reference | operator authority, Vertical state, message queue, deployment authority |
| Vertical | approved scope, dependencies, state transitions, owners, evidence, acceptance | communication transport, session identity, secrets, raw content store |
| Revere | message IDs, durable per-session mailbox, send/receive/lease/ACK/replay, per-session order, adapter checkpoints | work authorization, provider locator, operator evidence, identity issuance |
| Iron Curtain | policy decisions, exact-action permit issuance/verification, single-use bearer consumption, safe `permit_id` trace | communication history, business work state, general-purpose queue, agent registration, unapproved reusable/delegated capabilities |

No cross-service transaction is claimed. Each owner commits its state plus an immutable event/outbox atomically. Downstream consumers use immutable `event_id`, idempotency keys, causal links, and inbox deduplication. A trace can be complete without pretending distributed writes were simultaneous.

## 5. Causal trace model — who, what, why, and where

Every operator engagement creates a TownSquare receipt, including a statement, request, instruction, correction, approval, stop, rejected request, or failed interpretation.

### 5.1 Safe receipt fields

- `receipt_id` and immutable `event_id`.
- `event_kind`: statement, request, instruction, correction, approval, stop, outcome, or rejection.
- `occurred_utc`, `ingested_utc`, schema version, and idempotency key.
- `actor_agent_id` or operator principal; `session_trace_ref`; `parent_session_trace_ref`; `delegator_agent_id`; lineage-root trace ref.
- vendor and host safe identifiers; never the raw provider session locator.
- faithful safe summary and declared/derived intent classification.
- `caused_by_event_id`, `corrects_event_id`, `conversation_id`, and optional `reply_to_event_id`.
- `route_from`, `route_to`, routing reason, interpretation version, and disposition.
- related Vertical references and current observed revisions.
- nullable `permit_id` safe trace reference; never the capability token.
- nullable Revere `message_id`, delivery state reference, and owning-service outcome event.
- `protected_evidence_ref`, protected exact-content digest, and canonical receipt digest.

### 5.2 Protected evidence

The exact submitted bytes and their SHA-256 digest are stored under an access-controlled evidence partition in the same TownSquare intake transaction as the receipt, avoiding a cross-store atomicity claim. If the content is sensitive, the exact-content digest is protected with the evidence rather than published, because low-entropy text can be guessed. Public/general audit readers receive only the canonical receipt digest and safe summary.

Credentials, capability tokens, raw provider locators, lease receipts, and arbitrary sensitive message bodies never enter safe receipts, logs, metrics, traces, Git-tracked evidence, or Revere observability. Evidence access itself emits a TownSquare audit receipt.

### 5.3 Attribution versus atomicity

Registry identity/session/parent/delegator/sub-agent lineage proves attributable routing and audit context, not distributed atomicity and not authority. Registry owns the lineage fact; Vertical owns current accountable work and addressee; Iron Curtain owns exact-action machine authorization. Every effect must bind the executing actor/session, current accountable work/addressee, and exact applicable authority. A parent session, delegator, lineage root, or registered agent cannot substitute for any of those checks, and derived sub-agent permits remain unsupported/rejected. Atomicity is local to the owning service transaction. End-to-end integrity comes from immutable event IDs, idempotency keys, outbox/inbox records, causal references, content/release digests, and reconciliation—not from trusting a session name or lineage chain.

## 6. Non-circular Iron Curtain/TownSquare bootstrap

### 6.1 Canonical permit contract

The existing `townsquare-action-permit-poc-v1` contract is canonical wherever it applies. This program must not replace it with a new signing scheme or generalized capability service.

Its measured contract is:

- `POST /v1/action-permits` issues an opaque bearer for one exact action.
- `X-Action-Permit` is mandatory on the existing material `POST /v1/events` path.
- The bearer is HMAC-hashed for comparison and bound to exact actor, action, thread, revision, payload, idempotency key, typed Vertical `CANARY`, governance/decision context, and audience.
- It expires after 120 seconds, is single use, and issuance/consumption are transactional.
- Only safe `permit_id` is persisted/exposed; the raw bearer is never persisted.
- Exact-action retry behavior is preserved.
- The contract adds no new service or migration. Live Vertical verification, reusable permits/leases, and production hardening are explicitly deferred.

The source design is `docs/iron-curtain-single-use-permit-poc.md`, Story `IRON-CURTAIN-PERMIT-POC-CONTRACT`, based on TownSquare commit `9772e0…`, plus the referenced `C:\Workspace\iron-curtain` design/work order and issuance amendment. The issuance amendment requires Jackie Chan and GSP re-review before implementation. No Sentinel One tooling is assumed merely because designs exist on Venom.

### 6.2 Two lanes prevent the circle

1. **New audit/intake lane:** a distinct authenticated append-only, non-authorizing endpoint accepts statements, requests, instructions, corrections, approvals, stops, and malformed/rejected attempts for receipt creation without a per-message action permit. It cannot invoke `POST /v1/events`, mutate Vertical/Registry/Revere/release state, issue permits, or consume a permit. Authentication is the existing service principal/session path, not a new posting capability.
2. **Existing material-action lane:** `POST /v1/events` and other mapped state-changing/authority-bearing operations retain the exact 120-second single-use `X-Action-Permit` contract. The action matrix may add an endpoint to this lane only through an explicit reviewed amendment.

“Permit” is the governance decision. The opaque bearer is the current machine capability artifact. `permit_id` is the safe trace reference. Raw bearers and HMAC material never enter TownSquare receipts.

This is non-circular because ordinary engagement evidence is accepted through the non-authorizing lane, while the separately configured canonical permit issuer authorizes exact material calls. Permit issuance itself generates a TownSquare audit receipt but does not derive its authority from that receipt. The exact configured issuance authority/bootstrap mechanism must be taken from the approved issuance amendment and independently re-reviewed; this package does not invent an Ed25519 genesis replacement.

### 6.3 Compatibility and deferred extensions

- **Reused now:** exact-action binding, 120-second expiry, single use, transactional issue/consume, HMAC-hashed bearer handling, safe `permit_id`, and exact-action retry semantics.
- **Added by this package after approval:** the separate non-authorizing intake/receipt route and endpoint-to-lane action matrix. These do not weaken `POST /v1/events`.
- **Not in the bounded MVP:** reusable session posting leases, general capability delegation, derived sub-agent permits, offline genesis keys, and digital break-glass tokens. If later approved, each requires an explicit amendment/new Vertical Story and must preserve compatibility with issued `permit_id` traces.

Ordinary intake therefore needs neither a per-message permit nor a reusable posting lease. The policy rule for any future derived sub-agent permit remains: it may only narrow parent action/resource/audience/environment/expiry/delegation scope. Until an amendment implements and tests that rule, derivation is unsupported and rejected.

### 6.4 Emergency behavior

Material actions fail closed when permit issuance/verification is unavailable. Digital break glass is not added to this MVP because it would silently expand the canonical POC contract. Immediate physical/infrastructure containment remains an operator-controlled external procedure limited to stopping or isolating the affected service; it must not approve/start/merge/deploy or manufacture governed writes. Any such intervention creates a protected incident record and is reconciled into TownSquare before normal material operations resume.

### 6.5 Revere pre-send/delivery authority table

The existing Iron Curtain POC does not yet cover Revere operations. Every live/external row below therefore remains **disabled** until the canonical POC is accepted and an explicit Jackie/GSP-reviewed amendment defines and implements its exact-action enforcement. Synthetic local tests use no external session or network contact.

| Operation | Classifier and principal | Required work/Decision context | Permit applicability | Enforcement owner and check point | Deny/unknown result | Override and receipt |
| --- | --- | --- | --- | --- | --- | --- |
| External send / enqueue | Material external communication; existing Revere `Authenticator.authenticate` immutable `Principal.agent_ids`, exact source session, and Registry binding | Current Vertical accountable work/addressee plus protected operator Decision naming destination/session class and bounded message purpose | Exact-action permit only after explicit Revere-send amendment; until then live send is disabled | Revere ingress, before durable message/enqueue/idempotency commit | Safe failure receipt; zero message, sequence, outbox, or delivery-state write | Only a later protected operator Decision plus fresh exact permit; no agent/reviewer override |
| Lease-producing receive | Material delivery-state mutation; authenticated receiving `Principal`, exact destination session, Registry eligible state | Current accountable receiving work/addressee and accepted transport policy/Decision | Exact-action permit or another explicitly reviewed enforcement amendment; no session-auth substitution | Revere receive handler, before lease/receipt hash/attempt-count commit | Safe failure receipt; zero lease, receipt, attempt, watermark, or payload exposure | Protected operator Decision plus fresh permitted operation; safe receipt |
| ACK | Material delivery-state mutation; same immutable receiving `Principal` and destination session bound to unexpired lease receipt | Same current accountable work/addressee and accepted delivery Decision/policy | Exact-action permit or explicit reviewed ACK amendment; lease receipt is not authority | Revere ACK handler, before ACK/watermark commit | Safe failure receipt; zero ACK/watermark/lease mutation | Protected operator Decision plus fresh permitted operation; safe receipt |
| Redelivery / replay | Material automated delivery-state mutation; service principal plus original destination Registry binding | Accepted work/Decision and explicit redelivery policy tied to original message; original send permit is not silently reusable | Explicit reviewed amendment required to authorize scheduled/internal mutation; unsupported until then | Revere scheduler/receive boundary, before attempt/lease/replay commit | Safe failure receipt; zero attempt, lease, replay, or watermark mutation | No agent override; protected operator Decision/amendment and trace receipt |
| Adapter delivery to vendor session | Material external contact; authenticated adapter principal, exact Registry session, and executing actor/session | Current accountable Vertical work/addressee plus exact protected operator external-contact Decision | Fresh exact-action permit after reviewed adapter-delivery amendment | Adapter boundary, before provider API/session delivery commit | Safe failure receipt; zero external contact and zero Revere delivery advancement | Only protected operator Decision plus fresh exact permit; outcome/failure receipt |

Parent session, delegator, sub-agent lineage, agent identity, session authentication, `work_ref`, message content, delivery state, and `permit_id` are context only and cannot substitute for current accountable work, the protected Decision, or the exact machine authorization. An endpoint extension cannot be enabled merely by editing this table; it waits on accepted canonical Iron Curtain work plus its own reviewed amendment and tests.

## 7. Environment and promotion model

### 7.1 Venom

Venom hosts the current Eddie Brock product-owner session. It is an operator/coordination surface, not the TownSquare development or production environment.

### 7.2 Sentinel One — official development

No implementation may begin on Sentinel One until Story S7 proves the following prerequisites:

- The `batman`/Cable/Bishop/development identities have no write path to NAS production mounts. Read access, if still needed, is explicitly scoped read-only. Read-only verification is limited to existing probe/adjacent/mount metadata and performs no NAS content/name/metadata mutation. Production writes are possible only through the separately authenticated/gated production mechanism.
- A separate attributable operator Decision has named an already-existing authoritative, authenticated, non-authorizing append operation plus exact incident payload/digest/destination; that operation has returned the immutable incident receipt. No such operation is currently verified, so S7 and all Sentinel implementation remain blocked. The exact file is preserved until another separate Decision explicitly authorizes that one-file remediation; cleanup verifies adjacent ledger contents unchanged and emits before/after receipts.
- A canonical, branchable TownSquare MVP Git baseline is established from verified source. Extracted `template-not-deployable` trees/tars and the local `release-manifest.json` at `7eea350…` are evidence inputs, never a deployable or silently imported branch base.
- A project-local supported toolchain/test environment exists; system Python 3.14.4 is not modified merely to add pytest.
- Container build/test access is scoped. Raw Docker-socket membership is not granted by default because it is host-root equivalent; prefer a rootless or narrowly mediated runner with no NAS mount.
- Bishop SSH trust is configured only if Bishop receives an approved assignment, using a verified/pinned host fingerprint; host-key checking is never disabled.
- Repo-local Git identity uses an approved name/email accepted by push protection. History is not rewritten to conceal the earlier rejection.
- Untracked Dojo/Adjunct/contract/docs files are inventoried and preserved; none is erased, committed, or copied into a release without ownership and scope review.

After this gate, each approved Story uses an isolated branch/worktree from the verified baseline. Cable and Bishop are implementers/resources under registered identities and scoped development credentials. They receive synthetic/test data, not production credentials, raw provider locators, or release/deploy capabilities. They do not self-review, self-accept, change their own work status without the authorized lifecycle event, or deploy. Bruce's stopped local work is selectively applied after file-level mapping; the whole dirty tree is never copied or silently treated as accepted.

### 7.3 Independent release verification

An independently built candidate must bind:

- source commit(s), dependency lockfiles, schema/migration digests, policy/genesis digest, and artifact digest;
- acceptance-test results mapped only to approved criteria;
- secrets/locator/payload leak-scan result;
- migration compatibility and previous-release rollback/restore procedure;
- release owner, independent reviewer, QA result, and operator acceptance state.

The material deployment event payload names the exact artifact digest, NAS environment, migration set, permitted action/context, and operator-approved work references. The canonical 120-second single-use permit binds that exact payload plus actor/thread/revision/idempotency/audience claims. Any changed or unbound deployment payload fails verification.

### 7.4 NAS — production promotion

Before promotion, take an application-consistent backup of the affected TownSquare/Registry/Revere data and configuration metadata without exporting secrets into the release artifact. Prove restore in an isolated environment. Promotion uses the verified artifact only and emits receipts for permit verification, backup, migration, service health, and cutover outcome.

Rollback is required only for cutover-impacting changes, and production rollback is itself a material action. It may execute only under one of two predicates:

1. The protected deployment Decision and a still-valid exact-action permit pre-authorize the named rollback artifact/snapshot, NAS target, objective trigger, rollback action, idempotency key, and bounded window; or
2. A later protected operator Decision names those fields and a fresh exact-action permit binds the rollback request.

| Rollback condition | Result |
| --- | --- |
| Predicate 1 or 2 fully valid | Restore the named previous artifact when schema-compatible, or execute the specifically named verified snapshot restore. Emit outcome receipt. |
| No, expired, mismatched, or replayed permit | Zero NAS/data mutation; safe failure receipt. |
| Wrong artifact/snapshot, NAS target, trigger, action, idempotency key, or time window | Zero NAS/data mutation; safe failure receipt. |
| Failed health/migration/receipt check without rollback authority | Stop or isolate only; do not manufacture rollback authority. Emit safe failure/containment receipt. |
| Operator stop | Stop/isolate remains immediately under operator control, but does not itself authorize rollback or another governed write. |

Operator Decisions are never gated by ordinary agent review. Machine execution of rollback still requires its exact permit. Failed migration or receipt-path verification stops promotion. No agent may improvise a NAS write path.

## 8. Reconcile already-live Registry, Revere, and Iron Curtain work

### 8.1 What remains valid

- The canonical live Epic and item keys remain authoritative; this package does not mint replacements.
- Registry remains the identity/session/lineage/private-locator owner and keeps atomic projection + immutable journal + outbox semantics.
- Revere remains the transport owner; v1 behavior remains backward compatible while Phase 2 supplies durable session mailboxes, idempotent send, server-owned ordering, lease/ACK/redelivery/replay, at-least-once delivery with durable adapter deduplication, and bilateral Codex↔Claude proof.
- Locator, identity, delivery, permit, and Vertical authority remain separate concepts.
- Existing acceptance criteria that do not conflict with the Sentinel One environment decision remain valid.

### 8.2 Required amendment/reconciliation, not duplication

Before further implementation:

1. Retrieve the authoritative NAS event history and current revision for all six named keys and `YNM-EPIC-022`.
2. Verify `SESSION-REGISTRY-PROTECTED-LOOKUP` status and all live owners.
3. Append operator-approved correction/amendment events—never edit history—to name Sentinel One as development environment, NAS as production, Eddie/Venom product ownership, and Cable/Bishop as resources rather than environments.
4. Amend the Registry criteria to cover vendor, host, exact session, parent session, delegator, sub-agent lineage, lifecycle, safe trace reference, and private provider locator without treating identity as authority.
5. Amend Revere integration criteria to consume canonical session UUIDs/safe identity records, preserve v1, and produce causal links/receipts without storing locators or authority.
6. Inventory Bruce's stopped implementation exactly: modified `registry/app.py`, `registry/migrate.py`, and `registry/schema.sql` (reported total 131 insertions/14 deletions) plus untracked `tests/test_session_registry_s1.py`. Preserve unrelated pre-existing modified `contracts/r7/registry-schema.json` and untracked `contracts/r8/`, `docs/session-registry/`, and `docs/townsquare-default/`. Map verified changes to existing Stories and selectively migrate only mapped files/hunks to Sentinel One; never revert or wholesale-copy the shared dirty tree.
7. Preserve existing live states until an authorized transition event is appended. This document does not transition them.

### 8.3 Canonical Iron Curtain dependency

The live `VR-047.5` contract-rework chain through `VR-051` remains canonical. This package adds no competing permit implementation Story. The sequence is:

1. Bruce corrects only the three files authorized by the live contract-rework item.
2. Jackie Chan and GSP independently re-review the corrected contract.
3. Existing TESTS/IMPLEMENT/REVIEW/CANARY items may proceed only through their recorded dependencies and separate authority.
4. After the bounded POC is accepted, this program may integrate it with the new non-authorizing intake route and action matrix.

Reusable leases, delegation, general capability issuance, new services/migrations, Compose changes, fleet deployment, and production hardening remain excluded unless the operator approves an explicit later amendment/Story.

## 9. DRAFT Vertical hierarchy

All identifiers below are stable proposal keys, not live references. Every item is **DRAFT / PENDING_OPERATOR_APPROVAL**. On approval, the intake owner must verify exact registered owners, retrieve current live records, and append parent-before-child `OPEN` events or amendments through the authorized mechanism. No metadata grants authority by itself.

### DRAFT-TSDEF-E1 — Epic: TownSquare Working Default

- `vertical_level`: `EPIC`
- `parent_ref`: none
- `depends_on_refs`: `YNM-EPIC-022` (existing live dependency; do not duplicate)
- `product_owner`: verified registered ID `eddie-brock` on Venom
- `creation_owner`: `eddie-brock`
- `fulfillment_owner`: verified registered ID `bruce-lee` (program integration; proposed assignment)
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: make TownSquare the normal operator engagement, communication, audit, routing, and outcome interface while Drive becomes reconciled history and all material actions remain permit-gated.
- Acceptance criteria:
  1. Every supported operator engagement type creates one immutable TownSquare receipt with protected exact evidence and complete causal attribution before routing/rejection returns.
  2. Ordinary authenticated audit/intake posting needs no per-message action permit; every material action fails without the canonical valid exact-action single-use bearer and safe `permit_id` trace.
  3. Registry/Revere live items are reconciled without duplicate replacement items and complete on Sentinel One under their own accepted criteria.
  4. Town Watch plus the approved agent clients use native TownSquare intake/receipts and Revere transport without a Drive publication step.
  5. An independently verified release is backed up, restored in isolation, promoted to NAS under a digest-bound permit, and cut over with no unreconciled accepted Drive record.
  6. Operator records independent acceptance; Crier visibility alone is not acceptance evidence.
- Evidence required: accepted Feature references, end-to-end causal trace, permit negative/positive matrix, live-item reconciliation map, client receipt compliance report, Drive reconciliation report, release/restore/promotion evidence, operator Decision.

### DRAFT-TSDEF-F1 — Feature: Trio governance and non-circular authority bootstrap

- `parent_ref`: `DRAFT-TSDEF-E1`
- `depends_on_refs`: none
- `creation_owner`: `eddie-brock`
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: extend the adopted Charter with TownSquare/Vertical/Iron Curtain bindings and integrate the canonical exact-action permit POC without blocking ordinary audit intake.
- Acceptance criteria: S1 and S2 pass; the action matrix is complete for MVP endpoints; the canonical POC retains its exact contract; material actions fail closed; operator override remains explicit and auditable; no reusable/generalized permit subsystem is introduced.

#### DRAFT-TSDEF-S1 — Story: Extend the adopted Charter with trio bindings and action matrix

- `parent_ref`: `DRAFT-TSDEF-F1`
- `depends_on_refs`: none
- `fulfillment_owner`: `jigoro-kano`
- `review_owner`: `gsp`
- Goal: extend, without re-adopting or superseding, the Charter already effective under decision `TS-CHARTER-1.0-ADOPTION-20261007T0540060363929Z` with the default-path ownership/action mapping.
- Acceptance criteria:
  1. An append-only amendment references the adopted release commit/tree and states that Charter adoption itself did not authorize implementation, deployment, activation, governed writes, or restore closure.
  2. A versioned, exhaustive matrix maps every registered/reachable endpoint, method, and action to owner, authenticated-principal source, non-authorizing/material class, exact-action permit rule, fixed structured receipt type, data/service dependencies, and failure response.
  3. Classification is closed/default-deny: every unknown, renamed, or unmapped route/action that could write is material and is rejected/parked with no owning-service mutation. An automated route-coverage test fails the build if any registered route is unmapped or an intake route can reach a material/permit issue/consume dependency.
  4. It states that imperative content, identity, session, `parent_session`, delegator, sub-agent/all lineage, `work_ref`, `permit_id`, permit-issuance receipt, message delivery, and Crier visibility are context only and never self-authorize or substitute for current accountable work/addressee plus the exact opaque bearer.
  5. Correction, stop, operator override, and independent acceptance semantics match the adopted Charter and append-only lifecycle. An operator stop engagement may be receipted without a permit, but the intake route cannot transform it into a governed write; ordinary software state mutation still uses the canonical exact-action permit, while emergency physical stop/isolation remains external and narrowly reconciled.
  6. Public versus protected fields are explicit, including prohibited credentials, locators, tokens, receipts, and payloads; unknown receipt kinds are rejected into a fixed safe rejection receipt rather than dynamically creating a new action class.
- Evidence required: reviewed binding document, exhaustive route/action inventory, automated route-coverage/default-deny test, intake dependency-isolation test, negative authorization-substitute matrix, dissent/resolution record.

#### DRAFT-TSDEF-S2 — Story: Integrate the accepted exact-action permit POC with the two-lane TownSquare path

- `parent_ref`: `DRAFT-TSDEF-F1`
- `depends_on_refs`: `DRAFT-TSDEF-S1`, `DRAFT-TSDEF-S7`, canonical `VR-20261008-ynm-047.5-WORKING` through dependency-blocked `VR-051`
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- Goal: after the canonical Iron Curtain POC passes its existing correction/review/test/implementation/canary gates, integrate it unchanged for material actions and add only the separate non-authorizing receipt intake path.
- Acceptance criteria:
  1. This Story cannot enter implementation until the canonical POC contract correction and Jackie/GSP re-review pass and the existing TESTS→IMPLEMENT→REVIEW→CANARY lifecycle records independently authorize/accept each step; neither Bruce nor a POC implementer may self-review or self-accept, and no duplicate permit service/code path is created.
  2. Material `POST /v1/events` retains `townsquare-action-permit-poc-v1`: mandatory `X-Action-Permit`, 120-second single-use opaque bearer, exact actor/action/thread/revision/payload/idempotency/typed-Vertical/governance/decision/audience binding, transactional issue/consume, HMAC-hashed comparison, safe `permit_id`, and no raw bearer persistence.
  3. A distinct authenticated non-authorizing intake endpoint creates immutable receipts without a per-message permit and is technically incapable of invoking material mutations or issuing/consuming a permit.
  4. Missing, expired, replayed, mismatched, wrong-audience, or wrong-action permits fail with no material mutation; exact-action retries follow the canonical contract. `permit_id`, issuance receipt, Vertical reference, Crier item, identity/session claim, imperative body, or intake receipt cannot substitute for the bearer.
  5. Reusable posting leases, parent/child or derived capabilities, broader/narrower alternate permits, new permit services/migrations, digital break glass, Compose changes, fleet deployment, and production hardening are absent and actively rejected by this MVP. Any future derived permit remains unsupported unless an explicit amendment implements and tests the narrow-only rule.
- Evidence required: canonical POC live-gate references and Jackie/GSP results, v1 contract regression matrix, exhaustive route coverage, non-authorizing-lane dependency isolation, authorization-substitute and unsupported-mechanism rejection tests, permit failure/no-write tests, duplicate-implementation scan.

### DRAFT-TSDEF-F2 — Feature: Native operator intake and immutable engagement receipts

- `parent_ref`: `DRAFT-TSDEF-E1`
- `depends_on_refs`: none at Feature level; authoritative dispatch dependencies are declared on each child Story
- `creation_owner`: `eddie-brock`
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: make TownSquare the usable operator interface and automatically receipt every engagement and outcome.
- Acceptance criteria: S3 and S4 pass; receipt creation is middleware-enforced; safe/public and protected evidence paths are separated; no supported engagement needs a Drive publication step.

**Child-dependency dispatch rule:** Feature-level planning order does not add an unstated transitive dependency to a child. Dispatch is decided from the child Story's explicit `depends_on_refs` plus its live Vertical state. Therefore accepted S1 + accepted S7 permits S3 to be considered for authorized dispatch even while S2 is blocked; S4 remains nondispatchable until both S2 and S3 are accepted. Material `POST /v1/events` remains nondispatchable/unusable before the canonical Iron Curtain POC chain accepts it. Automated dependency tests must prove these three cases and reject any attempt to infer authority from parent/Feature metadata.

#### DRAFT-TSDEF-S3 — Story: Commit mandatory receipts, protected evidence, and causal trace

- `parent_ref`: `DRAFT-TSDEF-F2`
- `depends_on_refs`: `DRAFT-TSDEF-S1`, `DRAFT-TSDEF-S7`
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- Goal: atomically receipt operator inputs and reliably link routing and outcomes.
- Acceptance criteria:
  1. Statement, request, instruction, correction, approval, stop, malformed, rejected, and failed engagements each create exactly one immutable receipt under idempotent replay.
  2. The local intake transaction commits event ID, safe receipt, protected exact bytes/digest, actor/session/lineage, causal links, route/interpretation, related Vertical refs, and outbox before returning accepted/rejected disposition.
  3. Update/delete attempts fail; corrections append and link; exact replay creates no second receipt/outbox record; changed replay conflicts without partial writes.
  4. Credentials, provider locators, capability/lease tokens, sensitive exact digests, and arbitrary payloads do not enter public events or observability; protected evidence reads are authorized and receipted.
  5. Outcome events reconcile to the originating event/permit/message/work references, and unresolved routes are queryable without claiming distributed atomicity.
- Evidence required: schema/migration tests, event-kind matrix, DB count/idempotency assertions, protected-access tests, leak scan, causal-trace sample using synthetic content.

#### DRAFT-TSDEF-S4 — Story: Deliver the native operator console and client intake contract

- `parent_ref`: `DRAFT-TSDEF-F2`
- `depends_on_refs`: `DRAFT-TSDEF-S2`, `DRAFT-TSDEF-S3`
- `fulfillment_owner`: `chuck-norris`
- `review_owner`: `bruce-lee`
- Goal: let the operator submit, correct, approve, stop, and inspect engagement delivery/outcome without Google Drive.
- Acceptance criteria:
  1. The minimal native interface accepts every supported event kind and immediately returns `receipt_id`, safe summary, classification, related work/permit references, and current routing state.
  2. Material actions visibly request/attach a permit-derived capability; non-authorizing posts do not prompt for per-message operator approval.
  3. Correction and stop actions create linked receipts and never edit history; protected evidence remains inaccessible without its separate authorization.
  4. Failure or timeout shows the durable receipt and unresolved/retry state rather than silently falling back to Drive or file drop.
  5. Accessibility and keyboard-only smoke tests pass for the bounded operator workflow.
- Evidence required: interface tests/screens, API contract tests, accessibility smoke result, no-Drive end-to-end trace.

### DRAFT-TSDEF-F3 — Feature: Reconcile and integrate live Registry/Revere work

- `parent_ref`: `DRAFT-TSDEF-E1`
- `depends_on_refs`: `DRAFT-TSDEF-F1`, existing `YNM-EPIC-022`
- `creation_owner`: `eddie-brock`
- `fulfillment_owner`: `eddie-brock` (coordination only)
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: amend, migrate, and integrate the canonical live Session Registry/Revere work without duplicating or silently superseding it.
- Acceptance criteria: S5 and S6 pass; all six live keys have a revision/status/owner/criteria map; valid stopped work is migrated to Sentinel One; duplicate implementation ownership is zero.

#### DRAFT-TSDEF-S5 — Story: Reconcile Session Registry state, lineage scope, and stopped implementation

- `parent_ref`: `DRAFT-TSDEF-F3`
- `depends_on_refs`: `DRAFT-TSDEF-S7`, existing `SESSION-REGISTRY-MVP`, `SESSION-REGISTRY-PERSIST-LIFECYCLE`, `SESSION-REGISTRY-PROTECTED-LOOKUP`
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `gsp`
- Goal: bring the existing Registry work onto the approved environment and complete the trace model under its canonical live items.
- Acceptance criteria:
  1. Authoritative records `VR-20261009-ynm-038.0/.1` through `VR-20261009-ynm-044.0` are re-retrieved at the current watermark before amendment; F1/S1 remain `WORKING`, protected lookup remains `OPEN`, and the three Revere items remain `OPEN` unless newer authoritative events prove otherwise.
  2. Cable's missing-Registry/`OPEN-PARKED` observation is traced to its source/read model and reconciled as a stale-reader/projection discrepancy; authoritative NAS history is not rewritten to match the stale view.
  3. Approved append-only amendments to the canonical Registry items—not this draft alone—add vendor, host, exact session, parent, delegator, sub-agent/all lineage, lifecycle, safe trace ref, and private locator criteria. They state: Registry owns lineage facts; Vertical owns accountable work/addressee; Iron Curtain owns exact-action authorization; every effect binds executing actor/session + current accountable work/addressee + exact authority; parent/delegator/lineage cannot substitute; derived sub-agent permits are unsupported/rejected. No deferred lineage graph is described as already accepted.
  4. Bruce's stopped changes in `registry/app.py`, `registry/migrate.py`, `registry/schema.sql`, and `tests/test_session_registry_s1.py` are inventoried by file/hunk, mapped criterion-by-criterion, peer-reviewed, and selectively applied on an isolated Sentinel One branch; modified `contracts/r7/registry-schema.json` and untracked `contracts/r8/`, `docs/session-registry/`, and `docs/townsquare-default/` remain untouched unless separately owned.
  5. Registry mutation tests retain immutable event ID, exact idempotent replay, projection+journal+outbox transaction, private locator protection, and no cross-service transaction claim. Negative tests prove parent/delegator/lineage/identity/session cannot authorize an effect or replace Vertical accountable work and exact permit.
- Evidence required: live-record retrieval, amendment events, change-to-criterion map, branch/commit list, focused tests, leak scan.

#### DRAFT-TSDEF-S6 — Story: Integrate accepted Revere transport with TownSquare causal receipts

- `parent_ref`: `DRAFT-TSDEF-F3`
- `depends_on_refs`: `DRAFT-TSDEF-S1`, `DRAFT-TSDEF-S2`, `DRAFT-TSDEF-S3`, `DRAFT-TSDEF-S5`, `DRAFT-TSDEF-S7`, and canonical `REVERE-PHASE2-DURABLE-SESSION-RELAY`, `REVERE-DURABLE-SESSION-MAILBOX`, `REVERE-CODEX-CLAUDE-BILATERAL-ADAPTERS` each with an independent acceptance record and normal accepted `CLOSED` state (not rejection, cancellation, or administrative closure)
- `fulfillment_owner`: verified registered ID `cable` (Bishop may receive separately scoped subtasks only after Bishop's exact registered ID is verified)
- `review_owner`: `gsp`
- Goal: integrate already-accepted canonical Revere outcomes with TownSquare causal receipts and the reviewed authority matrix without taking ownership of any transport implementation.
- Scope exclusion: this Story does **not** implement or modify mailbox storage, lease issuance, ACK, redelivery, replay, deduplication, v1 compatibility, bilateral adapters, or their proofs. Those remain owned exclusively by the canonical existing Revere items.
- Acceptance criteria:
  1. A work-key/scope duplicate scan proves no DRAFT item overlaps the canonical Revere Feature/Stories; append-only amendments add only lineage/receipt-link/authority-matrix integration criteria and keep transport ownership on the existing keys.
  2. Environment/owner/dependency amendments separate Sentinel One from Cable/Bishop and require every canonical Revere item to have an independent acceptance record plus normal accepted `CLOSED` state before this integration dispatches; rejection, cancellation, or administrative closure does not satisfy the dependency.
  3. TownSquare stores only safe causal references to Revere `message_id`, `conversation_id`, delivery/outcome event, session trace refs, accountable work/Decision, and `permit_id`; it stores no locator, bearer, lease receipt, or arbitrary payload.
  4. For each operation in the S1 Revere authority table, denied/unknown/unverified authority produces a safe failure receipt and zero Revere delivery-state mutation; session authentication or lineage alone never authorizes.
  5. Integration tests use synthetic local endpoints with no external contact. A live Codex↔Claude bilateral proof or any external send/delivery requires a separate exact attributable operator authorization after canonical items and the Revere authority amendment are accepted.
- Evidence required: canonical-key/scope duplicate scan, append-only amendment map, accepted canonical Revere references, synthetic causal-link contract tests, zero-delivery-mutation negative matrix, leak scan, proof of no external contact.

### DRAFT-TSDEF-F4 — Feature: Sentinel One release verification and NAS promotion

- `parent_ref`: `DRAFT-TSDEF-E1`
- `depends_on_refs`: none; S7 is the mandatory first implementation gate, while S8 carries downstream dependencies
- `creation_owner`: `eddie-brock`
- `fulfillment_owner`: `francis-ngannou`
- `review_owner`: `gsp`
- `operator_acceptance_owner`: `operator`
- Goal: first make Sentinel One incapable of accidental NAS production writes and establish canonical development source, then produce an independently verified recoverable release and promote only its exact digest to NAS.
- Acceptance criteria: S7 passes before any Sentinel One implementation; S8 then passes; no implementer can self-promote; template manifests cannot release; backup restore is proven; the canonical exact-action permit binds the approved deployment event payload and artifact/migrations.

#### DRAFT-TSDEF-S7 — Story: Isolate Sentinel One from NAS and establish a branchable development baseline

- `parent_ref`: `DRAFT-TSDEF-F4`
- `depends_on_refs`: none
- `dispatch_status`: **BLOCKED pending a separate attributable operator Decision naming an already-existing safe incident-receipt system and append operation**
- `fulfillment_owner`: `francis-ngannou`
- `review_owner`: `bruce-lee`
- Goal: close the reproduced production-write boundary and create the minimum safe, branchable, buildable Sentinel One development baseline before any MVP implementation.
- Acceptance criteria:
  1. Before S7 dispatch, the operator records a **separate** attributable Decision naming: the existing authoritative receipt system; its exact existing authenticated non-authorizing append operation; destination; fixed incident receipt payload and digest; authorized submitting principal; and expected receipt ID/evidence. Approval of this package is not that Decision. No permit is required because the append is non-authorizing, but ordinary authentication and append authorization remain mandatory. No currently verified safe operation has been named, so S7 remains `BLOCKED`. If none exists, work returns to the operator; no temporary endpoint, NAS direct write, file drop, or self-bootstrap is allowed.
  2. Using only the Decision-named existing operation, a protected immutable incident receipt records Cable, host/session lineage, 2026-10-09 04:08 local occurrence, purported read-only context, RW CIFS boundary, exact existing probe path/metadata, safe summary, cause, and remediation status without hiding the accidental write. Missing, mismatched, or unverifiable receipt leaves S7 failed and every Sentinel One implementation Story nondispatchable.
  3. Independent read-only verification may inspect only the existing `.cable-write-probe`, its parent/adjacent entries, and mount/ACL metadata. It performs no create, write, touch, rename, move, chmod, chown, truncate, delete, or other content/name/metadata mutation on any NAS object. The existing file remains untouched until the operator separately authorizes that exact one-file deletion; controlled remediation then emits before/after receipts and proves adjacent files unchanged.
  4. `batman`, `cable`, Bishop, Bruce, and ordinary development identities cannot create/modify/delete under NAS production mounts. Required reads use explicit read-only mounts/ACLs; production mutation is available only through the gated production identity/path. Write-denial testing occurs only after isolation against an explicitly named non-production synthetic target. Any NAS syscall or content/name/metadata/parent change without the separate cleanup authority fails acceptance.
  5. A canonical TownSquare MVP Git checkout with verified provenance is branchable on Sentinel One. Prototype `4726278`, extracted `cc73f7c`/`c2440a39`/`aa2aeb5` trees/tars, and manifest commit `7eea350…` are inventoried/digested but not treated as deployable; `template-not-deployable`/`TEMPLATE_NOT_RELEASE_EVIDENCE` remains visible until a real clean build replaces it.
  6. A project-local supported runtime/test environment supplies required tools (including pytest) without modifying system Python 3.14.4. Container builds/tests use a rootless or narrowly mediated runner with no NAS mount; raw Docker-socket access is not granted to solve convenience.
  7. Repo-local Git identity passes push-protection policy. Bishop SSH is configured only after assignment with independently verified/pinned host key; disabling host-key verification fails acceptance.
  8. The four untracked Revere Dojo docs, Adjunct docs, `vertical-staging`, and shared TownSquare modified/untracked files are inventoried and preserved; no unrelated content is reverted, committed, or silently included.
- Evidence required: separate operator receipt-operation Decision; exact incident payload/digest/destination; returned immutable receipt; independent read-only mount/ACL/existing-probe inventory; syscall/no-change audit; explicit one-file cleanup Decision and receipts if later authorized; non-production negative write-boundary evidence; canonical-source/digest map; clean branch/worktree proof; rootless/scoped container test; project test-environment result; Git identity check; optional pinned Bishop fingerprint; untracked-file inventory.

#### DRAFT-TSDEF-S8 — Story: Back up, restore, promote, verify, and roll back NAS release

- `parent_ref`: `DRAFT-TSDEF-F4`
- `depends_on_refs`: `DRAFT-TSDEF-S2`, `DRAFT-TSDEF-S4`, `DRAFT-TSDEF-S5`, `DRAFT-TSDEF-S6`, `DRAFT-TSDEF-S7`
- `fulfillment_owner`: `francis-ngannou`
- `review_owner`: `gsp`
- Goal: promote a recoverable exact release without turning approval into blanket environment access.
- Acceptance criteria:
  1. A clean build emits one non-template manifest binding canonical source, dependencies, schemas/migrations, adopted Charter/policy, artifact digest, and approved work refs; unresolved image/wheelhouse/SBOM/build inputs fail the release gate.
  2. Independent QA reruns mandatory acceptance tests and leak scan from that exact candidate digest; implementer self-review/self-acceptance cannot satisfy the gate.
  3. Pre-promotion application-consistent backups cover affected data/config metadata, exclude secret export, and restore successfully in isolation.
  4. The canonical exact-action permit binds the approved deployment event payload to the artifact/migration digests, NAS target, permitted action/context, and idempotency key; changed/unbound payloads fail closed.
  5. Promotion emits receipts for permit, backup, migration, health, and outcome; failed migration or receipt path stops before cutover.
  6. Rollback executes only when either the protected deployment Decision plus still-valid exact permit pre-authorizes the exact rollback artifact/snapshot, NAS target, objective trigger, action, idempotency key, and window, or a later protected operator Decision plus fresh exact permit names them. It restores only that artifact/snapshot and emits an outcome receipt.
  7. No/expired/mismatched/replayed permit, wrong artifact/target/trigger/action/idempotency/window, or operator stop alone produces zero rollback mutation and a safe receipt. Failed checks may stop/isolate but cannot manufacture rollback authority. Operator Decisions remain under operator control and are never gated by ordinary agent review.
  8. No Cable/Bishop/Bruce development credential can deploy to or roll back NAS.
- Evidence required: clean-build transcript, resolved manifest/digest, independent QA/leak report, backup/restore transcript, deployment permit negative/positive tests, promotion rehearsal, complete rollback truth-table tests, receipt chain, implementation-versus-governance cost record.

### DRAFT-TSDEF-F5 — Feature: Client adoption, Drive reconciliation, and default cutover

- `parent_ref`: `DRAFT-TSDEF-E1`
- `depends_on_refs`: `DRAFT-TSDEF-F2`, `DRAFT-TSDEF-F3`, `DRAFT-TSDEF-F4`
- `creation_owner`: `eddie-brock`
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `jackie-chan`
- `operator_acceptance_owner`: `operator`
- Goal: move Town Watch and approved agent clients to TownSquare, reconcile Drive, then make TownSquare the default without losing audit history.
- Acceptance criteria: S9 and S10 pass; supported clients emit receipts; Drive inventory reconciles; the cutover/rollback decision is evidence-backed and operator-accepted.

#### DRAFT-TSDEF-S9 — Story: Adopt TownSquare in Town Watch and approved agent clients

- `parent_ref`: `DRAFT-TSDEF-F5`
- `depends_on_refs`: `DRAFT-TSDEF-S4`, `DRAFT-TSDEF-S6`
- `fulfillment_owner`: verified `cable`; Bishop only as a separately assigned resource after exact registered-ID verification, both on Sentinel One
- `review_owner`: `bruce-lee`
- Goal: prove TownSquare is the working interface, not merely visible through Crier.
- Acceptance criteria:
  1. Town Watch and each in-scope agent client register identity/session, use native intake, retain receipt IDs, and use Revere for directed delivery where required.
  2. Every test operator engagement and outcome appears exactly once under idempotent replay with complete actor/session/lineage/causal references.
  3. Material client actions require the canonical exact-action permit verification; non-authorizing posts use authenticated intake without a permit and cannot cross into the material path.
  4. Synthetic local end-to-end flows complete without Drive publication, manual file drop, manual prompt relay, Crier-as-proof substitution, or external contact. Live client/vendor proof runs only under a separate exact protected operator Decision and accepted Revere authority amendment.
  5. Client outage/reconnect preserves durable receipts/messages and exposes unresolved state to the operator; lease/ACK/replay mutations obey the §6.5 authority checks rather than treating session authentication as authority.
- Evidence required: per-client contract tests, receipt coverage report, material-action negative tests, no-Drive/no-manual-relay trace, reconnect result.

#### DRAFT-TSDEF-S10 — Story: Reconcile Drive and cut over the operational default

- `parent_ref`: `DRAFT-TSDEF-F5`
- `depends_on_refs`: `DRAFT-TSDEF-S8`, `DRAFT-TSDEF-S9`
- `fulfillment_owner`: `bruce-lee`
- `review_owner`: `jackie-chan`
- Goal: reconcile existing operational records and stop using Drive as the default publication interface.
- Acceptance criteria:
  1. A bounded inventory classifies every in-scope Drive operational record as matched, imported with provenance, superseded/corrected, historical-only, or explicitly unresolved; no silent overwrite occurs.
  2. Imported records receive immutable TownSquare event IDs, source/provenance links, protected evidence where needed, and idempotent import keys; imports never manufacture past permits or authority.
  3. A finite shadow period shows 100% receipt coverage and zero unexplained accepted-record mismatch for the agreed client/event set.
  4. Operator approves a timestamped cutover; clients switch TownSquare to default and Drive to read-only historical/reference use. No indefinite dual-write remains.
  5. During the bounded rollback window, a TownSquare release failure may restore only the Decision/permit-named prior artifact or snapshot under the S8 rollback predicate; absent that authority it stops/isolates with no rollback mutation. Only an explicit operator continuity Decision may temporarily use Drive, and all such records reconcile before normal material actions resume; the continuity Decision does not authorize NAS rollback.
- Evidence required: Drive inventory/reconciliation report, import idempotency/provenance tests, shadow coverage result, cutover Decision, post-cutover smoke tests, rollback/continuity rehearsal.

## 10. Deployment and cutover gates

The following are hard gates, in order:

1. Operator approves this hierarchy and any amendments to existing live items.
2. S7 independently verifies the NAS incident, removes development write authority, establishes canonical branchable source/toolchain, and—only under a separate exact-file Decision—remediates the probe. No Sentinel One implementation precedes this gate.
3. The adopted Charter amendment/action matrix passes review, and canonical Iron Curtain `VR-047.5`→`VR-051` gates authorize and accept the exact-action POC before S2 integration.
4. Native receipt middleware and interface pass privacy/idempotency/causal-trace tests.
5. Existing Registry/Revere work is reconciled and accepted on Sentinel One under canonical items.
6. In-scope clients pass native TownSquare/permit/Revere adoption tests.
7. Drive inventory and shadow reconciliation meet S10 criteria.
8. A non-template clean candidate, independent QA, leak scan, backup restore, and rollback rehearsal pass.
9. Operator issues the canonical exact-action permit for the exact deployment event payload/artifact and later records cutover acceptance.

No lower gate implies the next. A release approval is not a deployment permit; deployment success is not cutover acceptance; cutover is not Epic closure.

## 11. Explicit MVP non-goals

- Replacing Google Drive as a general document repository.
- Replacing Vertical with TownSquare posts or using TownSquare/Revere as authority.
- General RBAC redesign beyond the bounded principals, canonical exact-action permits, and protected-evidence access.
- Exactly-once distributed delivery or cross-service ACID transactions.
- Multi-region/high-availability queueing, automatic scaling, dead-letter operations, or generalized retention automation.
- Additional vendor adapters beyond the approved Codex and Anthropic Claude proof.
- Autonomous consequential action from message content.
- Production observability/hardening not required by a reproducible acceptance failure.
- Treating Cable, Bishop, Venom, Crier, or Google Drive as an environment substitute for Sentinel One or NAS.

## 12. Cost-proportional MVP estimate

Best-current engineering-time estimate; replace with actual elapsed time in delivery evidence.

| Work | Implementation + mandatory tests | Governance/review/acceptance |
| --- | ---: | ---: |
| F1 Charter binding/exact-action POC integration after canonical gates | 8–16 h | 4–8 h |
| F2 receipts/native interface | 24–36 h | 4–6 h |
| F3 live Registry/Revere reconciliation and remaining accepted work | 24–40 h, excluding already-completed valid code | 4–6 h |
| F4 production-boundary remediation, safe dev bootstrap, release/backup/promotion | 24–36 h | 4–7 h |
| F5 clients/Drive/cutover | 24–40 h | 4–6 h |
| **Total** | **104–168 h** | **20–33 h** |

Mandatory acceptance tests, credential protection, backup/restore, and narrowly necessary safety checks are implementation delivery cost. Optional production hardening remains at **0 authorized hours**. Governance/review remains below the implementation estimate. Token and monetary cost are unknown and must not be inferred.

## 13. Operator decisions still required

Recommendations are first.

1. **Approve the five-Feature hierarchy and keep `YNM-EPIC-022` canonical (recommended).** Alternative: create duplicate Registry/Revere items; rejected because it splits authority and history.
2. **Name the existing authoritative incident-receipt system and exact authenticated non-authorizing append operation, then issue a separate attributable Decision containing the exact incident payload/digest/destination/principal (required before S7).** No safe existing operation has been verified, so there is no responsible default recommendation. If none exists, S7 stays blocked and the design returns to the operator.
3. **Keep `townsquare-action-permit-poc-v1` canonical and add only the distinct authenticated non-authorizing intake lane (recommended).** Do not introduce Ed25519 genesis, reusable posting leases, general delegation, or digital break glass in this bounded MVP. Any such extension requires a later explicit amendment/Story after the canonical POC is accepted.
4. **After canonical POC acceptance, approve or reject a separate Revere-operation authority amendment covering send, lease receive, ACK, redelivery/replay, and adapter delivery (required before live Revere integration).** Recommendation: preserve the fail-closed table in §6.5 and authorize only synthetic local tests until the amendment is reviewed. A live Codex↔Claude proof needs its own exact external-contact Decision.
5. **Approve fail-closed material action with no digital break glass in this MVP (recommended).** Emergency physical/infrastructure stop or isolation remains operator-controlled and requires protected incident reconciliation before normal governed operations resume.
6. **Select the in-scope Drive sources and shadow-period duration. Recommendation: only operational publication records used by TownSquare/Town Watch/agent workflow, with a 7-day or 100-engagement shadow period, whichever is later.** General Drive document migration is out of scope.
7. **Approve proposed owners.** `eddie-brock`, `cable`, and `bruce-lee` are verified; Bishop must be verified before assignment. Cable/Bishop assignments must be separate, scoped Stories on Sentinel One; no shared environment identity.
8. **Approve a bounded rollback window. Recommendation: 24 hours after NAS cutover, but require the exact S8 rollback Decision/permit predicate; expiry or mismatch stops/isolate only.**
9. **Later authorize or reject controlled remediation of only `/mnt/nasonemic/Projects/Vertical/ledger/.cable-write-probe` after the separate incident receipt and independent read-only metadata/directory verification.** This destructive one-file Decision is distinct from package approval and the incident-receipt Decision.

## 14. Work order after operator approval

**DOCUMENT · DISCUSS · DECIDE gate**

- Document: Ip Man — this architecture, boundaries, causal trace, hierarchy, dependencies, criteria, and cost split.
- Independent design review: GSP — threat/authority/privacy/receipt review; Jigoro Kano — binding/permit/override logic review; each records concerns independently.
- Decide: Operator — approve/reject the package and choices above. Review gates constrain agents, never the operator's right to accept, reject, or explicitly override a named finding.

**WORK ORDER**

- Product owner: Eddie Brock on Venom — prioritize, resolve scope, approve proposed assignments for filing, and present evidence for operator acceptance; do not implement by virtue of ownership.
- Implement governance: Jigoro Kano documents the S1 Charter amendment/binding; Bruce Lee integrates S2 only after the canonical `VR-047.5`→`VR-051` correction/review/dependency gates authorize it. Jackie Chan and GSP review the POC delta before dependent work.
- Implement TownSquare: Bruce Lee owns S3; Chuck Norris owns S4; work only on approved Sentinel One branches.
- Reconcile identity/transport: Bruce Lee owns S5 under the existing Registry items; Cable owns S6 under the existing Revere items; Bishop may take a separately scoped adapter/test subtask. Neither is an environment.
- Implement safety/release path: Francis Ngannou owns S7 first; no Sentinel One implementation begins until NAS write isolation and branchable/toolchain prerequisites pass. Francis then owns S8 and the verified Sentinel One→NAS procedure; no deployment occurs without the exact-action operator permit bound by the approved action matrix.
- Implement adoption/cutover: Cable/Bishop own separately assigned S9 client changes; Bruce owns S10 reconciliation/cutover logic.
- Peer review: GSP reviews Iron Curtain, receipts, Registry/Revere security, and deployment authority; Bruce reviews client integration; Jackie Chan reviews reconciliation/import integrity. One relevant peer review per nontrivial change; no implementer self-review.
- QA: Ronda Rousey maps every approved acceptance criterion to `PASS` or `FAIL`, reruns from the candidate digest, and performs negative authority, idempotency, replay/reconnect, leak, backup/restore, rollback, and cutover tests.
- Watch for: duplicate live items; environment/owner conflation; Drive remaining the hidden default; receipt bypasses; public secret/locator/token leakage; posts treated as authority; derived permit widening; stale Registry/Revere binding; unbound release artifacts; Crier visibility presented as native-use evidence; and optional hardening exceeding accepted MVP scope/cost.

## 15. Validation and accounting

- Artifact path: `docs/townsquare-default/townsquare-working-default-architecture-and-draft-vertical.md`.
- Structural review re-run after the Cable/operator evidence amendment: requirements-to-section mapping; `A/R/C/O/U` provenance check; Eddie/Venom and environment/owner separation; stable-key/no-duplicate-live-work check; acyclic Story dependency walk (`S7` first safety gate → `S1` policy → `S2/S3/S5/S6` implementation/integration → `S4/S8/S9` → `S10`); canonical Charter/Iron Curtain compatibility check; dirty-file preservation check; exact-file incident-remediation boundary; bounded-scope/cost check; and explicit no-authority-from-posts check.
- Amendment summary: recorded Sentinel One source/service/tooling gaps; added authoritative live status/projection discrepancy; recorded the NAS RW/probe incident; converted S7 into the mandatory production-write-isolation and branchable-baseline gate; bound all Sentinel implementation to S7; preserved exact stopped-work files; made the adopted Charter and live exact-action Iron Curtain POC canonical; removed proposed Ed25519/reusable posting-lease/derived-capability/digital-break-glass implementation from MVP; strengthened non-template release and deployment-payload gates.
- Governance review history: the earlier narrow Kano delta review cleared the closed/default-deny matrix correction, but a later full independent review superseded that result with seven `REWORK` blockers. This revision applies all seven corrections. Kano's bounded follow-up confirms **all seven blockers closed; planning-only package approval-ready**. This authorizes no implementation, configuration, permit issuance, probe deletion, live transition, external proof, rollback, or deployment.
- Bounded correction checks re-run:
  - Dependency walk: F2 has no inherited Feature gate; S3 depends only on S1+S7; S4 depends on S2+S3; material `/v1/events` still waits on canonical POC acceptance. No Story cycle was introduced.
  - Canonical-key duplicate scan: S6 is integration-only and explicitly excludes mailbox/lease/ACK/replay/dedup/v1/bilateral ownership; canonical Revere keys must be accepted/closed first.
  - S7 no-write review: no NAS create/write/touch/rename/move/chmod/chown/truncate/delete is permitted; any mutation without separate exact cleanup authority fails; missing safe incident receipt keeps all Sentinel implementation nondispatchable.
  - Revere pre-send table: send, lease receive, ACK, redelivery/replay, and adapter delivery each name classifier/principal, work/Decision context, permit/amendment status, enforcement owner/check point, zero-mutation denial, override, and receipt.
  - Lineage non-authority review: parent/delegator/sub-agent/all lineage remain Registry facts only; negative tests bind each effect to executing actor/session + current Vertical accountable work/addressee + exact authority and reject derived permit substitution.
  - Rollback truth table: only the two protected Decision + exact-permit predicates mutate NAS; every missing/expired/mismatch/replay/wrong target/artifact/window/stop-only case yields zero rollback mutation and safe receipt.
- Repository read-only validation: **blocked in this task context** by the pre-launch ACL-helper failure; a shell-enabled coordinator must run file readback, `git diff --check`, Markdown/link checks, and authoritative live-record retrieval before submission.
- External/state-changing actions: none.
- Elapsed time: unknown in this task context.
- Models used: Ip Man planning role on `gpt-5.6-sol`; two narrow read-only evidence attempts on `gpt-6-luna` (both blocked before shell launch). No model cost/token telemetry was available.
