# Canary communications high-value backlog — 2026-10-08

## Operator direction

The operator authorized Eddie Brock to select high-value TownSquare canary work, create the required Vertical Stories, assign implementation to Cable, and coordinate review and follow-on work. The objective is useful cross-host communication with less operator relay. This record does not broaden any Story beyond its stated goal and definition of done.

The existing Vertical Feature is `VR-20261006-townsquare-180`, **Implement and verify the approved cross-project integrations**. The backlog adds five Stories beneath that Feature. The append-only JSONL ledger remains the proof-of-concept source of truth; this document is a readable execution plan.

## Ranked delivery order

| Priority | Story | Outcome | Initial lifecycle | Dependency |
|---|---|---|---|---|
| 1 | `VR-20261008-townsquare-183` | Install and prove reliable Cable delivery from the NAS canary | `WORKING` | integrated read client (`VR-181`) |
| 2 | `VR-20261008-townsquare-184` | Sustain canary credentials without daily operator intervention | `OPEN` | accepted delivery |
| 3 | `VR-20261008-townsquare-185` | Deliver pointer-only notices with durable attempt evidence | `OPEN` | reliable delivery and approved stop interlock |
| 4 | `VR-20261008-townsquare-186` | Enable a canary-only authenticated Cable response path | `OPEN` | accepted delivery and credential rotation |
| 5 | `VR-20261008-townsquare-187` | Package repeatable onboarding for Wolverine, Bishop, and Venom | `OPEN` | accepted delivery and response |

Only `VR-183` is admitted for Cable implementation now. An `OPEN` backlog Story is not permission to investigate, design, implement, test, or operate it. Eddie will advance one Story at a time after reviewing its dependencies and the preceding evidence.

## Eight-hour target

The primary target is to complete implementation and evidence for `VR-183`, independently review it, and begin the credential-rotation design in `VR-184` only if the review passes. If that path is smaller than expected, Cable may implement and test it within the same eight-hour window after Eddie advances the Story to `WORKING`.

The likely eight-hour result is reliable one-minute Cable delivery, a durable local inbox, deduplication, observable failure behavior, tested disable/rollback, and a pushed evidence branch. A tested credential-rotation implementation is possible; live Cable response and reusable fleet onboarding remain continuation work. True dormant-session activation remains governed by the existing wake decomposition and is not implied by pointer delivery.

## Oversight split

- **Cable / Sentinel One:** implementation, focused tests, sanitized evidence, branch commit, and push for the one `WORKING` Story.
- **Eddie Brock:** Story control, scope monitoring, independent validation, correction requests, integration decision, and subsequent Story admission.
- **Independent quality assurance:** adversarial confirmation of material acceptance claims when required.
- **Operator:** acceptance and any action involving a human-held credential, destructive or irreversible change, exposure beyond the local network, or a material scope decision.

## Adopted Charter controls

- `TSC-ROE-01`: retrieve the current record, adopted governance, dependencies, scope, criteria, and evidence before consequential action.
- `TSC-WRK-01`: keep accountable work, current addressee, and criteria explicit.
- `TSC-WRK-02` and `TSC-ROE-05`: implementation evidence does not authorize self-acceptance or self-closure.
- `TSC-NOT-01`: a notice or wake is a pointer and never the work, assignment, acceptance, policy, or authority.
- `TSC-REC-02`: committed evidence is corrected by later linked records rather than edited or deleted.
