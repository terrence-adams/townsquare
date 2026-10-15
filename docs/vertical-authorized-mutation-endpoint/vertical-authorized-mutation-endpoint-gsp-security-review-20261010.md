# GSP security design review — Vertical authorized mutation endpoint MVP

**Verdict: REWORK — one bounded contract correction required**  
Date: 2026-10-10  
Reviewer: GSP (security design review only)  
Scope: design package only; no code, ledger, credential, deployment, or ACL action was performed.

## Reviewed immutable inputs

| Artifact | SHA-256 verified |
| --- | --- |
| `vertical-authorized-mutation-endpoint-mvp-design-20261010.md` | `9def649bd2dd03523222bf121f99eb6d865f290a04ef87188c5c30ef2eebf935` |
| `vertical-authorized-mutation-endpoint-draft-work-items-20261010.md` | `080adbe4a8dd488e3e144d94665211ab604282ab89c3b87584e0a8362ea4f643` |
| `vertical-authorized-mutation-endpoint-work-order-20261010.md` | `888158ab046d5c05e1d575a1e6bf9cbfd5e41a379bdf9c4ea7bb0e37c69a4df1` |

## Threat model and observed controls

Protected assets are authoritative Vertical events, the project-owner/Gate decision, permit single-use semantics, and credential/signing material. The relevant adversary is a credentialed or replaying client attempting a confused-deputy mutation, a changed semantic payload, or a direct-SMB bypass. Trust crosses from the enrolled client into the authenticated endpoint, then into VR-048/Gate, and finally to the exclusive ledger writer.

The amended package addresses the prior payload-binding concern: issuance and execution carry the exact typed payload; the service recomputes canonical payload and complete-request hashes at both boundaries; it validates authority-reference coverage at issuance and immediately pre-append; and hash-only or changed payloads fail before a write. It also bounds retries to unrelated global-head movement, requires current actor/owner/Gate revalidation, records durable non-secret consumption markers, confines exact retries to the same permit/principal/request/idempotency tuple, keeps secrets and provider locators out of evidence, and reserves the post-acceptance direct-SMB prohibition for an explicit cutover decision.

Eddie/Venom is correctly limited to operator-decision and receipt relay, without endpoint operation or credential custody. Logan/Wolverine is correctly usable for facilitation and handoffs, without implicit authority, self-approval, sole review, administration, or credentials. Iron Curtain is explicitly reference-only; no TownSquare code or acceptance reuse is assumed.

## Required correction

### SEC-001 — execution-envelope field ownership is contradictory

**Severity: medium. Likelihood: medium.**

The permit request's canonical envelope requires `project`, and both mutation routes require the *same complete canonical request envelope*. Yet the routes also say they reject caller-supplied `project`. A compliant execution request must therefore both carry and not carry `project`. In addition, `authority_ref` is top-level while the typed payload is described as also including authority reference. This leaves two representations of authority-bearing inputs.

Concrete failure path: an implementer resolves the contradiction by dropping `project` during execution hashing or by accepting/ignoring one duplicated authority reference. The permit can then be checked against a different complete-request representation from the one used to construct the event, defeating the stated exact-binding guarantee and creating a confused-deputy/cross-project mismatch risk.

**Required document-only amendment before approval:**

1. Define one canonical source for each field. Keep `project` as a client request selector that must exactly equal the permit-bound and server-resolved project, but do not copy it as a caller-authoritative event field; or alternatively make it fully server-derived and remove it from both client execution-envelope and complete-request hashing. Do not require it and reject it in the same request.
2. Place `authority_ref` in exactly one canonical envelope location, or state the required equality rule and reject a top-level/payload disagreement before any write.
3. Add bounded S2/S4 fixtures proving project-selector and duplicated-authority mismatch rejection with zero writes, while retaining a same-envelope exact retry.

This is a contract clarification, not a new persistence, identity platform, ACL control, or production-hardening requirement.

## MVP and acceptance-boundary assessment

- Authenticated permit issuance/use, canonical payload/request bindings, replay handling, actor/owner resolution, immediate Gate reauthorization, semantic-stop versus harmless global-head retry, receipt recovery, secret hygiene, direct-SMB cutover, custody separation, and Iron Curtain non-reuse are otherwise **PASS in design**.
- The documented criteria remain binary and bounded. The requested amendment fits S2/S4 and does not add out-of-scope hardening.
- Cost control is **PASS in design**: governance/review estimate (9–16 hours) remains below implementation/delivery (26–40 hours). Actual time/cost: unknown.

## Release condition

After SEC-001 is amended consistently across all three documents and new SHA-256 values are supplied, rerun this focused review. Until then, the package is **not APPROVAL-READY** and does not authorize implementation or any live action.
