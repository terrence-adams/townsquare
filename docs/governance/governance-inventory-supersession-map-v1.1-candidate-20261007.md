# Governance inventory, conflict, and decision map v1.1 — candidate

**document_id:** `TS-GOV-INVENTORY-1.1-CANDIDATE-20261007`
**status:** REVIEW EVIDENCE — NOT AUTHORITY

## Search manifest and limits

Reviewed repository inputs are the exact committed files under `docs/governance/`, `docs/kano-townsquare-doctrine-v1.6-pass1-handback-20261006.md`, `docs/kano-townsquare-doctrine-v2.0-pass4-handback-20261006.md`, `DOCTRINE.md`, and the named external-charter relationship records. The source register snapshot itself was not available in this worktree; therefore this map is a traceable reconciliation index, not a claim that every register event has been independently dereferenced. Adoption review is blocked until an immutable register snapshot (identity, sequence/watermark, digest, retrieval time) is attached and every `UNVERIFIED` row is resolved.

| Input / class | Status/fate | Candidate-6 relationship | Conflict disposition |
|---|---|---|---|
| TownSquare Doctrine v1.5, draft 4, candidate.5 | historical candidate inputs | candidate.6 uses new `TS2-*` stable IDs; candidate.5 is withdrawn as a review candidate | no old short ID is reused |
| decisions register D1–D49, selections S1–S8 | authoritative input pending pinned snapshot | mapped by ranges below | later explicit operator decision controls its stated scope |
| Agentic Operating Charter | external charter, not edited | relationship analysis required before adoption | unresolved material conflict escalates; physical placement never decides |
| Bedrock Doctrine / Charter 2.0 | external reference/charter, not edited | no authority is inferred here | explicit scope/adoption controls; otherwise escalate |
| Herding Cats | companion candidate/input | keep separate pending full conformance | no implicit adoption |
| Night Shift instruments | scoped input | keep separate pending conformance | no implicit adoption |
| RoE export | candidate companion | v0.3 below is successor candidate | no implicit adoption |
| townsquare-protocol | historical protocol | proposed archive decision remains operator-only | preserved until operator decides |
| Wonderland inventory | consumer/input | observation only | cannot authorize or mutate |
| historical external notes | historical evidence only | may inform, never confer authority | unavailable history is recorded, not invented |

## Decision/amendment reconciliation index

| Decision range | Disposition / destination | Status |
|---|---|---|
| D1–D3 | post/action boundary and record semantics → TS2-REC-02, TS2-GATE-01 | mapped; snapshot required |
| D4–D15 | registry/charter/field concerns → external or object-profile inputs | UNVERIFIED; no absorption claim |
| D16–D21 | headers, lifecycle, evidence → TS2-CLM-01, TS2-WRK-01/02, object profile | mapped; snapshot required |
| D22–D26 | routing, work and reporting → TS2-WRK-01, TS2-REC-03 | mapped; snapshot required |
| D27–D31a | unverified historical range | UNVERIFIED; no adoption review pass |
| D32–D37 | gates, evidence, independent QA → TS2-GATE-01, TS2-WRK-02 | mapped; snapshot required |
| D38–D47 | model/reporting/gate constraints → TS2-NOT-01, TS2-GATE-01 | mapped; snapshot required |
| D48–D49 | addressing/registry input → TS2-WRK-01 and object profile | mapped; snapshot required |
| S1–S8 | field/relay/input selections | retained as object/profile or unresolved input | snapshot required |

No row silently retires a decision. `UNVERIFIED` means “not asserted as carried”; it does not mean “discarded.” The reviewer must attach the register snapshot and replace each range with per-decision rows before any adoption decision.
