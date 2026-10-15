# TownSquare working default — operator ruling and security delta

Status: **DRAFT FILING INPUT / NOT FILED**  
Date: 2026-10-09  
Applies to: the filing-ready Vertical drafts derived from `townsquare-working-default-architecture-and-draft-vertical.md`  
Product owner: `eddie-brock` — OpenAI on Venom

This delta preserves the reviewed architecture as historical evidence and records the operator's later controlling rulings. It does not alter the approved artifact's recorded hash, append a Vertical event, authorize a NAS mutation, or move any work item to `WORKING`.

## Controlling operator rulings

1. `batman` is the operator's human account. It retains the operator-controlled NAS write access that Sensei intentionally granted.
2. Sentinel One's present NAS access is sufficient for the current bounded MVP. It is worthy of concern but is **not an implementation blocker or an MVP acceptance criterion**.
3. The accidental zero-byte `.cable-write-probe` remains an auditable incident/concern. Its deletion, rename, permission change, touch, or other mutation still requires a separate exact-file operator decision.
4. The planned remediation is a dedicated NAS service-account model instituted when the program is ready for full deployment to NAS as production. It is a future production-promotion/cutover prerequisite, not current MVP scope.
5. NAS supports service accounts. Exact account names, secret provisioning, rotation mechanism, and server paths are deployment-time fields unless an existing project standard supplies them.

## Superseding interpretation of S7

The reviewed architecture described S7 as blocked by an incident-receipt bootstrap and as a prerequisite for every Sentinel implementation. The later operator ruling supersedes that interpretation only as follows:

- S7 is a **high-priority, nonblocking** branchable-development-baseline and incident-preservation Story.
- The accepted concern does not prevent filing or authorized implementation of other Stories when their own explicit dependencies pass.
- S7 closure does not require service-account provisioning or migration for the bounded MVP.
- The existing probe remains evidence and receives no cleanup authority from this delta.
- No deployment, rollback, cutover, external Revere contact, or future production write is authorized by this delta.

## Required future NAS identity model

The following requirements apply at full NAS production deployment/cutover, under S8, not to current MVP implementation or acceptance:

- Preserve `batman` as the human operator identity and do not narrow its existing operator-controlled access through these Stories.
- Create a dedicated read-only NAS service identity for development/evidence reads where NAS access is necessary after production cutover. Server-side permissions and the client mount are read-only for that identity.
- Create a distinct production-promotion writer identity, preferred over one combined account. It is deny-by-default outside the exact approved production paths and actions.
- The production writer's credential is unavailable to development agents, ordinary shells, source trees, logs, environment dumps, and build/test containers. A trusted promotion mechanism acquires it only after exact-action authorization.
- Every service use is attributable by service identity, host, operation, approved work/decision, permit reference where material, target, timestamp, and outcome without exposing the credential.
- If implementation proposes one service account instead of two, it must first prove independently enforced, separable server-side read and write authorization with no reusable write credential exposed to agents. Otherwise acceptance fails.
- Write-denial tests target only an explicitly named non-production synthetic path.

## Security-review additions carried into filing

- GSP M-1 is added to S1, S3, and S4: public safe summaries are server-generated from a closed structured schema; raw operator text is not copied by default; renderers escape for their context; control characters are normalized or rejected; token, credential, and provider-locator patterns are redacted before public persistence/logging/tracing; hostile markup, control characters, a generated locator sentinel, and a generated bearer sentinel are tested. Original bytes remain only in protected evidence.
- GSP L-1 is added to S3 and S8: implementation evidence names the protected-evidence retention class, encrypted backup location, and restore-reader authorization, and proves ordinary release/support backups exclude protected evidence, provider locators, permit bearers, lease receipts, and HMAC material.

## Lifecycle interpretation

Every artifact in this directory is an `OPEN` event draft. `implementation_authorized: true` records the operator's program-level authorization to implement accepted scope; it is not a filed event, an `OPEN -> WORKING` transition, a permit, or proof that dependencies passed. A future implementer begins work only after the opening is filed and that implementer appends an authorized `WORKING` transition to the current authoritative head.

## Product-owner evidence and coordination boundary

A later controlling operator ruling names Eddie Brock product owner for all ongoing projects and names the `operator-designated Eddie Brock coordination hub` as the coordination boundary. This TownSquare/Revere session is only an execution lane. New cross-project priority, scope, ownership, acceptance-criteria, or sequencing conflicts route to that hub. Any session-to-hub mapping belongs only in protected Registry evidence and must never appear in filing drafts or native events.

A read-only scan of the authoritative Vertical ledger found no literal `product_owner:` field. The `RESOLVED` records listed in `README.md` are historical product-owner-role evidence only, not active/nonterminal ownership evidence and not the current authority basis.

Under the operator ruling, Eddie may coordinate code freezes and work assignments for this program. Coordination does not grant Eddie implementer self-review, independent acceptance, permit issuance, deployment/rollback/cutover authority, external-contact authority, credential disclosure, or probe-cleanup authority.

## Serialized authoritative filing binding

`eddie-brock` is the one designated authoritative append writer for this draft package, coordinated through the hub. Immediately before **each** append, the writer re-scans the proposed stable key and retrieves current parent/dependency heads; appends exactly one event; reads back and verifies the exact event and resulting head; and only then considers the next event. Any key collision, new head, stale revision, or mismatch stops filing. The affected draft must be rebased and re-reviewed through the hub before another append. A single preflight followed by a batch append does not satisfy this binding.
