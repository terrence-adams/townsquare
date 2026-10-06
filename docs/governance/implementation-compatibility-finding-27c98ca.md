# Governance Compatibility Finding — `27c98ca`

**status:** REVIEW FINDING — NOT ADOPTION — NOT RELEASE APPROVAL

**basis:** measured from `registrar/app/native_ledger.py`, `registrar/app/auth.py`, migrations `010`–`011`, and lifecycle/context tests at commits `8787d25` and `27c98ca`

**comparison:** MVP design 0.4-draft, Doctrine 2.0 draft 4, and the Rules of Engagement v0.1 candidate

**overall:** **MISMATCH — release-blocking for governed native writes**

The implementation has useful foundations: immutable event/content pairs, append-only context receipt issue/use evidence, revision binding, single-use expiry, evidence checks for resolution, criterion dispositions for closure, separate stop/resume capabilities, and an audited operator stop. Those are matches to observable parts of the candidate controls.

The following are the release-blocking governance mismatches; this list intentionally excludes packaging, interface, deployment, and other owners' findings.

| ID | Release-blocking mismatch | Measured evidence | Required close |
|---|---|---|---|
| GOV-RB-01 | The bundle does not retrieve or bind the active thread, applicable operator notes, applicable scope, or acceptance criteria. It copies only static manifest arrays. | `NativeLedger.create_context_bundle`; `context_bundles`; `_validate_receipt` | Build required items from authoritative current reads for the action and target; persist and transactionally revalidate their exact identities/hashes and control generation. |
| GOV-RB-02 | Bundle issuance records every static item as `item_retrieved` without serving or observing retrieval of its content. The resulting audit claim is stronger than the measured event. | `create_context_bundle` loop calling `_context_audit("item_retrieved", ...)` | Record `required_item_selected` at bundle issue; record `item_retrieved` only when exact bytes/canonical content are actually returned or otherwise evidenced. Keep the comprehension limitation explicit. |
| GOV-RB-03 | The service ignores candidate/adoption/effective status. Any hash-valid, `pinned: true` manifest can enable writes, including a non-adopted candidate. | `_manifest` checks only shape, hashes, and `pinned` | Require an operator adoption reference and effective status resolved from authority; reject candidate, superseded, withdrawn, or unverified manifests. Do not mount this candidate manifest. |
| GOV-RB-04 | Lifecycle vocabulary conflicts with the candidate rules: `CANCELLED` is missing and `CORRECTED` is treated as a state. | `_validate_event.allowed` | Implement the six-state lifecycle; represent correction as an append-only event purpose/reference, not a seventh state. |
| GOV-RB-05 | Opening Requests can omit owner, addressee, and acceptance criteria, and later claim/block/resolve actions are not bound to owner, addressee, or delegation. | `_validate_event.required`; actor checks occur only under `state == "CLOSED"` | Require immutable/carry-forward ownership and criteria facts and authorize each transition against server-resolved assignment/delegation. |
| GOV-RB-06 | Closure authority and independence can be changed through client-supplied latest-event metadata, and the check only excludes the principal who wrote the immediately prior event. | `_validate_event` reads `latest["owner"]`, `latest["addressee"]`, and `latest["principal"]` | Resolve owner/addressee and accepted-work authorship from authoritative history; reject self-acceptance across the complete work being accepted. |
| GOV-RB-07 | One Request state machine is applied to every unconstrained `kind`, contrary to the explicit design boundary for other post kinds. | `_validate_event` neither restricts `kind` nor branches lifecycle by kind | Allowlist kinds and bind each to its adopted lifecycle; until then, enable governed writes only for Request events. |
| GOV-RB-08 | Archive bypasses required context and does not test terminal state or policy eligibility. | `archive_thread` | Require an exact current receipt and enforce the adopted archive predicate before committing the archive event. |
| GOV-RB-09 | Terminal continuation is not required to carry a typed link to the prior thread. | terminal rejection exists, but no continuation-reference validation exists | Require a new thread with a server-validated `continues` reference to the terminal thread. |

## Disposition

- Keep the manifest and Rules of Engagement candidate **unmounted and inactive**.
- Do not claim compliance, comprehension, adoption, or release readiness from the current receipt tests.
- The operator stop path remains usable and must stay outside any ordinary context gate.
- Implementation belongs to the software owner; independent QA must replay the lifecycle truth table and candidate/adoption negative cases. A reviewer other than the gate author must review the built controls before any blocking enforcement is armed.

This finding stops being current after code, manifest, or governing-text changes and must then be repeated against exact versions.
