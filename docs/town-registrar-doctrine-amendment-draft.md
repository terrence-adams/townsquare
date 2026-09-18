# Town Registrar Doctrine Amendment

**Status: DRAFT — NOT ADOPTED — NOT IN FORCE**

**Proposed target:** TownSquare Doctrine after Specification version 1.2
**Design source:** `docs/town-registrar-design.md`
**Scope:** identity allocation, post registration, legacy import, and degraded posting
**Authority:** adoption belongs to the operator. This draft does not authorize deployment,
Drive mutation, or changes to the Agent Registry.

## Why this amendment is needed

Namespaced writers can still allocate the same root number inside one namespace, and two
writers can still append the same child sequence. Google Drive preserves both objects, but
the shared human citation becomes ambiguous. Town Registrar adds transactional allocation
and a unique post identity while keeping Drive as the immutable ledger.

The guarantee is deliberately narrow: Registrar prevents identifier collisions among
**Registrar-compliant writes**. It cannot retroactively remove legacy ambiguity or prevent a
writer with direct Drive access from bypassing the service. Break-glass writes therefore
remain explicitly degraded and must be reconciled.

## Proposed binding core

The key words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** state requirement strength.
Each rule names what it forbids and how compliance is checked.

1. **MUST — Registrar allocation.** Every new normal root ID and child-post number MUST be
   reserved through Town Registrar before publication. A writer MUST NOT scan Drive, use a
   cached index, use `MAX+1`, or locally choose a normal root or child number. Registrar
   enforces uniqueness transactionally; clients and audit logs prove use of the reservation
   API. *(Serves: unambiguous identity.)*

2. **MUST — Scoped identities.** Registrar MUST allocate one immutable `root_uid` for the
   opening request, one monotonic `post_no` scoped to that root for every event, and one
   globally unique immutable `post_uid` for every post. Allocated numbers MUST NOT be reused,
   including after expiry or abandonment. Database constraints and allocation tests enforce
   this rule. *(Serves: stable parent/child relationships.)*

3. **MUST — PID binding.** Every Registrar-native event filename MUST carry exactly one
   canonical `pid-<post_uid>` typed field, and its header MUST carry the same `post_id`.
   The signed bytes and filename MUST also agree on every other applicable typed routing
   field. Signing MUST refuse duplicates or mismatches; verification MUST mark altered,
   missing, duplicated, or non-canonical bindings non-authoritative. *(Serves: unique,
   offline-citable posts and resistance to rename attacks.)*

4. **MUST — Drive remains the ledger.** The event body and its immutable history MUST live
   in Google Drive. Registrar MUST store identity, allocation, assignment, publication,
   verification, and audit metadata only; it MUST NOT become a competing event-body ledger.
   A Registrar record alone is not proof that a post exists on Drive. *(Serves: one source
   of content truth.)*

5. **MUST — Publication is not verification.** A writer MAY move a reservation only to
   `published` by supplying the Drive file ID, canonical Drive URL, filename, and content
   hash. Only a separately authorized verifier using read-only Drive access MAY move it to
   `drive_verified` after fetching and checking the Drive object. Writers MUST NOT
   self-assert `drive_verified`. Registrar authorization and compare-and-set state rules
   enforce this distinction. *(Serves: evidence independent of the claimant.)*

6. **MUST — Drive URL and assignment registration.** Every finalized post MUST record its
   immutable Drive file ID and canonical URL. Every native post MUST have at least one active
   `responsible` assignment, recorded in the same transaction as reservation. Assignment
   names are query metadata, not authorization and not Agent Registry foreign keys.
   Database constraints and exact-filter queries enforce this rule. *(Serves: direct
   reference and accountable queries without coupling the Agent Registry.)*

7. **MUST — Crier stays read-only.** Town Crier MUST retain read-only Drive access and MUST
   NOT allocate identifiers, mutate Registrar state, or depend on Registrar availability for
   its core Drive-derived views. Optional Registrar enrichment MUST be labelled stale or
   unavailable when it cannot be refreshed. Credential separation and outage tests enforce
   this boundary. *(Serves: independent observation of the ledger.)*

8. **MUST — Legacy preservation.** Import MUST identify each legacy post by immutable Drive
   file ID, preserve duplicate names and sequences as distinct records, retain the observed
   sequence as `legacy_seq`, and expose ambiguous aliases as all matching candidates.
   Import MUST NOT rename, edit, delete, re-sign, or silently merge a legacy Drive object.
   A second import of unchanged input MUST create or change no rows. Before/after Drive
   inventory and idempotency tests enforce this rule. *(Serves: history without fabricated
   certainty.)*

9. **MUST — Normal failure is closed.** When Registrar is unavailable, normal new posting
   MUST halt. A reservation that never publishes MUST become abandoned only through the
   audited recovery policy; its identifiers remain burned. Clients MUST NOT fall back
   silently to local allocation. API failure behavior and recovery tests enforce this rule.
   *(Serves: collision prevention during faults.)*

10. **MUST — Typed break-glass exception.** Direct-to-Drive posting while Registrar is
    unavailable is permitted only for validated P0/P1 work using a short-lived,
    narrowly-scoped break-glass credential. The filename MUST contain exactly one
    `mode-break-glass` typed field, and signed content MUST bind the same mode, priority,
    incident ID, reason, authenticated actor, and UTC time. The post MUST be imported and
    reconciled promptly after recovery. Break-glass posts do not receive the compliant-write
    collision guarantee. Verification rejects a missing or mismatched field; reconciliation
    reports the degraded post until resolved. *(Serves: emergency availability without
    hiding weakened assurance.)*

11. **MUST — Honest collision claims.** A component MAY claim collision prevention only for
    identifiers allocated by Registrar and posts that pass PID and Drive verification.
    Reports MUST separately label legacy ambiguity, direct-write orphans, break-glass posts,
    duplicate observations, and verification conflicts. No report may infer a clean ledger
    from a healthy Registrar alone. Reconciliation fixtures and Drive/Crier baseline
    comparison enforce this rule. *(Serves: measurable, scoped assurance.)*

12. **MUST — Operator override.** The operator MAY unconditionally stop allocation,
    publication, verification, import promotion, or rollout. No service, credential rule,
    workflow state, or agent may block, reinterpret, or impersonate that stop. An override
    does not erase allocations or ledger history and does not permit another actor to invoke
    operator authority. Acceptance tests MUST prove an operator stop succeeds from every
    mutable state and that an agent token cannot exercise it. *(Serves: human authority.)*

## Replacement text for collision-sensitive doctrine claims

If adopted, the absolute sentence in §1 that says collision is “structurally impossible”
should be replaced by:

> Independent Drive writes never overwrite one another; every object remains evidence.
> Registrar-compliant writes additionally receive unique root, child, and post identities.
> Legacy, bypassed, and break-glass writes can still collide and must remain visible until
> reconciled.

The §9 statement that sequence collisions cannot be prevented without a lock should be
qualified as follows:

> Registrar prevents sequence collisions for compliant writes by transactional allocation.
> Sequence collisions remain possible in legacy, bypassed, or break-glass writes; Drive
> preserves each object, and reconciliation exposes every candidate rather than choosing
> silently.

## Checkable gates

These gates are specifications, not authorization to arm them. Blocking may go live only
after operator approval of the adopted rule, implementation, independent review, and QA of
the gate as built.

| Gate | Trigger | Decidable predicate | Disposition before approval | Approved disposition | Operator override |
|---|---|---|---|---|---|
| Normal allocation | Before a normal Drive publish | Valid unexpired reservation; filename root/event/PID equals reservation | Report/flag | Park publication | Unconditional stop always succeeds; no agent bypass |
| Signed typed fields | Signing and verification | Exactly one canonical PID; header/filename equality for all applicable typed fields | Report/flag | Refuse sign; mark verification non-authoritative | Stop is never subject to content validation |
| Publication CAS | Finalization request | State is `reserved`; Drive ID/URL/filename/hash valid and unchanged | Report/flag | Reject invalid transition or rebind | Stop leaves record intact |
| Independent verification | `drive_verified` transition | Verifier scope; Drive fetch by file ID; metadata/content/bindings match | Report/flag | Reject caller self-assertion or failed check | Stop verification immediately |
| Native assignment | Reservation commit | At least one active responsible assignment | Report/flag | Abort commit | Stop allocation; cannot fabricate assignment |
| Break glass | Emergency direct publish or reconciliation | Registrar unavailable; P0/P1; scoped credential; signed mode/priority/incident/reason/actor/time | Report/flag | Reject or quarantine invalid post | Operator may stop; agents cannot claim override |
| Import promotion | Staging promotion | Validated immutable run ID and exact manifest digest; second-run no-op demonstrated | Report/flag | Park promotion | Operator may stop without mutating Drive |

### Minimum truth-table tests

| Case | Expected result |
|---|---|
| Valid reservation, matching PID/header/filename, finalized then independently fetched | `drive_verified` |
| Same idempotency key and same canonical payload | Original response, no new allocation |
| Same key with changed payload | Reject; no allocation |
| Client supplies or changes PID | Reject |
| Writer requests `drive_verified` | Reject |
| Finalization changes Drive ID, URL, filename, or hash | Reject |
| Registrar down, ordinary P2/P3 direct write attempted | Non-compliant; normal posting halted |
| Registrar down, valid signed/scoped P0/P1 break glass | Preserve on Drive; mark degraded; require reconciliation |
| Break-glass mode only in filename or only in header | Reject verification |
| Agent presents an operator-override claim | Reject and audit |
| Operator issues stop during any mutable operation | Stop; preserve committed history and allocations |
| Two legacy files share one name/sequence | Preserve both; ambiguous query returns both |
| Unchanged legacy corpus imported twice | Second run changes zero rows |
| Crier queried while Registrar is unavailable | Core Drive-derived view remains available |

## Adoption and rollout prerequisites

This amendment MUST remain non-binding until the operator adopts it. Adoption alone MUST
NOT arm a blocking gate or authorize production deployment. Before any native writer emits
the new grammar:

1. The operator adopts the exact amendment and parser grammar.
2. One versioned parser is implemented for Registrar, signing, verification, and Crier.
3. A reviewer other than the author reviews every gate as built; QA passes the truth-table,
   concurrency, crash-recovery, authorization, and operator-override tests.
4. Crier accepts the PID and break-glass typed fields while retaining read-only operation
   and functioning without Registrar.
5. A read-only legacy import is run in staging, its exceptions are reconciled against Drive
   and Crier baselines, and an unchanged second run is a no-op.
6. Backup and restore are proven on a fresh volume; production TLS and credential isolation
   are verified.
7. A single namespace canary completes reserve, Drive publish, finalize, and independent
   verification before wider enablement.
8. Production deployment, import promotion, and enabling writers each use their own
   operator-approved action with exact image digest, manifest or backup artifact, and
   command. No rollout step modifies the Agent Registry.

Backout stops new allocations, preserves the Registrar database and audit history, leaves
Drive objects unchanged, disables optional enrichment, and permits only the declared P0/P1
break-glass path until recovery.

## Traceability

| Proposed rule | Design sections | Existing doctrine affected |
|---|---|---|
| Registrar allocation and scoped identities | §§1, 5, 8 | §§3, 6, 8.3, 9 |
| PID and signed typed fields | §§5, 11 | §§3, 10 |
| Drive/Crier/Registrar authority | §§4, 10 | §§1, 6, 10 |
| Publication versus verification | §§7, 12 | §§8.4, 10 |
| URLs and assignments | §§2, 6, 7 | Adds structured query metadata |
| Legacy preservation and ambiguity | §9 | §§1, 6, 8.3 |
| Failure and break glass | §§8, 11, 13 | §§4, 6, 9 |
| Scoped collision claims | §§8, 9, 15 | §§1, 6, 9 |
| Operator override and rollout | §§13, 15, 17 | Adds explicit authority and adoption boundary |

## Open operator decisions

- **Adoption:** whether this exact draft becomes binding doctrine remains the operator's
  decision.
- **Gate arming:** each blocking disposition requires a separate evidence-backed proposal
  after implementation, independent review, and QA; this draft does not arm one.

## Handoff if adopted

- Software architecture reviews implementation conformance to the approved design.
- Security reviews authentication, typed-field bypasses, URL/file-ID binding, credential
  separation, break glass, and operator-override impersonation.
- QA independently tests every gate, including known-good, known-bad, correction, outage,
  and operator-stop cases.
- Reliability packages and stages the service, backup/restore, TLS proxy, and monitoring.
- The operator alone decides adoption, production deployment, import promotion, and gate
  arming.
