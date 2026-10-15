# TownSquare working default — filing-ready Vertical drafts

Status: **DRAFT / NOT FILED**  
Product owner: `eddie-brock` — OpenAI on Venom  
Development environment: Sentinel One  
Production environment: NAS  

This directory contains the semantic opening events for the reviewed TownSquare-working-default program. It contains one Epic, five Features, and ten Stories. Nothing here is an authoritative ledger event, a `WORKING` transition, an Iron Curtain permit, a deployment instruction, an external-contact instruction, or probe-cleanup authority.

## Files

- `townsquare-working-default-open-events.json` — 16 filing payloads with stable keys, parents, dependencies, owners/addressees, acceptance criteria, evidence, and native `OPEN` event bodies.
- `vertical-filing-draft.schema.json` — local structural schema for the draft manifest.
- `operator-ruling-and-security-delta-20261009.md` — narrow controlling delta for later operator rulings and GSP M-1/L-1.

## Filing model

Each `native_open_event` matches the repository's native opening boundary in `registrar/app/native_ledger.py`:

- `revision` is `new`;
- `kind` is `REQUEST`;
- `state` is `OPEN`;
- `thread_id` is the stable immutable work-item key;
- `owner` is the authenticated filing principal `eddie-brock`;
- `addressee` is the proposed fulfillment owner;
- `criteria_refs` are complete and immutable at opening;
- server-generated event ID, ledger sequence, ordinal, predecessor, commit/content/metadata hashes, and committed time are intentionally absent and must be allocated by the authoritative append operation.

`implementation_authorized: true` records the operator's program-level implementation authorization. `dispatch_authorized_by_this_draft: false` makes the lifecycle boundary explicit. Filing produces `OPEN`, not `WORKING`. The addressee must later append an independently authorized `OPEN -> WORKING` event against the current head after explicit dependencies are satisfied.

Authoritative filing is a serialized, one-writer operation. The designated writer is `eddie-brock`, coordinated through the `operator-designated Eddie Brock coordination hub`. Any session-to-hub mapping belongs only in protected Registry evidence; it must never appear in filing drafts or native events. For **each** proposed opening, the writer must:

1. immediately re-scan the authoritative ledger for the stable key and retrieve the current head of every declared parent and dependency;
2. append exactly one event through the authorized operation, with no concurrent or batch appender;
3. read back and verify the exact event ID, key, state, content hash, parent/dependency bindings, and resulting authoritative head;
4. only then consider the next opening; and
5. stop without another append if a key collision, new head, stale revision, or verification mismatch appears, then coordinate with the Eddie hub and rebase plus re-review the affected draft.

Recommended filing order remains parent before child:

1. `TOWNSQUARE-WORKING-DEFAULT`
2. the five Feature keys
3. `TOWNSQUARE-SENTINEL-DEVELOPMENT-BASELINE` and the other Stories in dependency order

The scan is per-event, not one preflight for the batch. A newer authoritative event wins over this draft.

## Stable keys

| Proposal | Stable work-item key | Level | Addressee |
| --- | --- | --- | --- |
| DRAFT-TSDEF-E1 | `TOWNSQUARE-WORKING-DEFAULT` | Epic | `bruce-lee` |
| DRAFT-TSDEF-F1 | `TOWNSQUARE-GOVERNANCE-AUTHORITY-BOOTSTRAP` | Feature | `bruce-lee` |
| DRAFT-TSDEF-S1 | `TOWNSQUARE-CHARTER-ACTION-MATRIX` | Story | `jigoro-kano` |
| DRAFT-TSDEF-S2 | `TOWNSQUARE-EXACT-ACTION-PERMIT-INTEGRATION` | Story | `bruce-lee` |
| DRAFT-TSDEF-F2 | `TOWNSQUARE-NATIVE-OPERATOR-INTAKE` | Feature | `bruce-lee` |
| DRAFT-TSDEF-S3 | `TOWNSQUARE-ENGAGEMENT-RECEIPTS` | Story | `bruce-lee` |
| DRAFT-TSDEF-S4 | `TOWNSQUARE-OPERATOR-CONSOLE-INTAKE` | Story | `chuck-norris` |
| DRAFT-TSDEF-F3 | `TOWNSQUARE-REGISTRY-REVERE-INTEGRATION` | Feature | `eddie-brock` (coordination only) |
| DRAFT-TSDEF-S5 | `TOWNSQUARE-SESSION-REGISTRY-RECONCILIATION` | Story | `bruce-lee` |
| DRAFT-TSDEF-S6 | `TOWNSQUARE-REVERE-CAUSAL-INTEGRATION` | Story | `cable` |
| DRAFT-TSDEF-F4 | `TOWNSQUARE-SENTINEL-RELEASE-PROMOTION` | Feature | `francis-ngannou` |
| DRAFT-TSDEF-S7 | `TOWNSQUARE-SENTINEL-DEVELOPMENT-BASELINE` | Story | `francis-ngannou` |
| DRAFT-TSDEF-S8 | `TOWNSQUARE-NAS-RELEASE-PROMOTION` | Story | `francis-ngannou` |
| DRAFT-TSDEF-F5 | `TOWNSQUARE-CLIENT-DRIVE-CUTOVER` | Feature | `bruce-lee` |
| DRAFT-TSDEF-S9 | `TOWNSQUARE-CLIENT-ADOPTION` | Story | `cable` |
| DRAFT-TSDEF-S10 | `TOWNSQUARE-DRIVE-CUTOVER` | Story | `bruce-lee` |

Cable and Bishop are resources, not environments. Bishop receives no assignment until the exact registered ID is verified and a separate subtask is opened.

## Operator access and future service accounts

The current bounded MVP may use the operator-authorized access already present. This access is not an implementation blocker and service-account provisioning is not an MVP acceptance criterion. `batman` remains Sensei's human operator account, with its existing access unchanged.

Dedicated NAS service identities become mandatory under `TOWNSQUARE-NAS-RELEASE-PROMOTION` before full NAS production deployment/cutover: a read-only identity for necessary evidence/reference reads and a distinct narrowly scoped promotion writer. Exact names and secret provisioning are deployment-time fields. Agent-visible reusable writer credentials fail acceptance.

The existing `.cable-write-probe` is historical audit evidence and an accepted concern. Nothing in this package authorizes its mutation or deletion.

## Product-owner basis and historical evidence

The controlling current basis is the operator ruling that Eddie Brock is product owner for all ongoing projects and that the `operator-designated Eddie Brock coordination hub` is the coordination boundary. This TownSquare/Revere session is an execution lane, not the cross-project coordination hub. Any session-to-hub mapping belongs only in protected Registry evidence; it is excluded from these filing drafts and all native events.

A read-only ledger scan on 2026-10-09 found no literal `product_owner:` field. The following `RESOLVED` records are historical product-owner-role evidence only. They are not active/nonterminal ownership evidence and do not establish the current ruling by themselves. Each names `eddie-brock`; no other explicit product-owner-role value was found in that bounded scan.

| Work-item key | Current status | Current authoritative head | Explicit role evidence |
| --- | --- | --- | --- |
| `WONDERLAND-SENTINEL1-DEV-MIRROR-001` | RESOLVED | `VR-20261008-ynm-046.16-RESOLVED.txt` | `VR-20261008-ynm-046.0-OPEN.txt` |
| `YNM-EPIC-021` | RESOLVED | `VR-20261008-ynm-077.8-RESOLVED.txt` | same file |
| `REVERE-BOUNDED-EXECUTION-RESULT` | RESOLVED | `VR-20261008-ynm-084.2-RESOLVED.txt` | same file |
| `REVERE-BOUNDED-EXECUTION-RESULT-IMPLEMENTATION` | RESOLVED | `VR-20261008-ynm-085.2-RESOLVED.txt` | same file |
| `REVERE-PERSISTENT-USER-INBOX` | RESOLVED | `VR-20261008-ynm-086.2-RESOLVED.txt` | same file |
| `REVERE-PERSISTENT-USER-INBOX-IMPLEMENTATION` | RESOLVED | `VR-20261008-ynm-087.2-RESOLVED.txt` | same file |
| `REVERE-BOUNDED-RELIABLE-DELIVERY` | RESOLVED | `VR-20261008-ynm-090.2-RESOLVED.txt` | same file |
| `REVERE-BOUNDED-RELIABLE-DELIVERY-IMPLEMENTATION` | RESOLVED | `VR-20261008-ynm-091.2-RESOLVED.txt` | same file |
| `REVERE-FLEET-ONBOARDING-AUTOMATION` | RESOLVED | `VR-20261008-ynm-092.2-RESOLVED.txt` | same file |

Under the operator ruling, Eddie coordinates code freezes and work assignments through the hub. Product ownership is distinct from addressee, implementer, reviewer, host, and operator. It does not authorize Eddie to self-review, independently accept, issue a permit by role alone, deploy, roll back, cut over, contact an external session, disclose credentials, or clean up the probe. New cross-project priority, scope, ownership, acceptance-criteria, or sequencing conflicts route to the hub.

## Separate authorities retained

The following remain outside these `OPEN` drafts:

- mutation or removal of the exact `.cable-write-probe`;
- live/external Codex-to-Claude or other Revere proof;
- production promotion, deployment, rollback, or cutover;
- Drive scope/shadow duration and the timestamped default cutover;
- clear provider-locator access or secret disclosure;
- any `OPEN -> WORKING`, `RESOLVED`, or `CLOSED` transition.
