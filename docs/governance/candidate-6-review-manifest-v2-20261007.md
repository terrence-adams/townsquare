# TownSquare candidate-6 review manifest v2 — recovered-evidence supplement

**document_id:** `TS-CANDIDATE-6-REVIEW-MANIFEST-V2-20261007`
**status:** REVIEW-ONLY CANDIDATE — NOT ADOPTED — NOT EFFECTIVE — NOT A LIVE-LEDGER POST

This next-version manifest preserves the frozen candidate-6 package indexed by [manifest v1](candidate-6-review-manifest-20261007.md), Git blob `2ac15aaeab63194a135ee41aaeb4cecc8ae343d3`, raw-byte SHA-256 `0D3A2E4C73173B78B64277BA8DF02C2FB87478FBB5E585AABCA0B15EC88E1711`. It adds recovered evidence only; it does not alter candidate-6 prose, rewrite the Eddie receipt, adopt any item, or cure a missing register event.

## Added exact evidence

| Component | Path | SHA-256 | Status |
|---|---|---|---|
| evidence inventory | `docs/governance/evidence-snapshots/20261007/README.md` | `CDEE3E441D9DF11D2DD01A3170ECFFA4DFED29C5B6863C2CDCA6F72B04D00088` | evidence index, not authority |
| Charter snapshot | `docs/governance/evidence-snapshots/20261007/agentic-operating-charter-snapshot-20260909T091807Z.txt` | `E3A247F9FEEE9BC8D8D5D5339487360A73B90CFF15AB51042F8EEC91701E92D4` | historical relationship evidence only |
| Charter provenance | `docs/governance/evidence-snapshots/20261007/agentic-operating-charter-provenance-20260909.json` | `F6BD13AC2A3C7276D889AFEE8CD2461C5FCE2928AE517BCD94202DA0E5CEBCDB` | provenance only |
| Bedrock source container | `docs/governance/evidence-snapshots/20261007/bedrock-source-container-page-010.json` | `932CAE84FE03E8B554F458F4C23DBFB52D466DC1E35349FFEA75721F6F6996E9` | reference-only context; not authority |
| partial register container | `docs/governance/evidence-snapshots/20261007/decisions-register-partial-source-container.json` | `5A28EE675AFCF576A31D728D946DC6C7CB335BA8401D34DB9473B6EA1D6FD96E` | 41 objects, D1–D37 partial evidence; no completeness claim |
| gap update | `docs/governance/governance-source-snapshots-and-evidence-gaps-v2-20261007.md` | `18B40407BBD74AB253ABC67EE4886D40C8A42909771D3ED59B1BF6D0B12BD47B` | current evidence-gap statement |

## Acceptance state after recovery

| Area | State | Reason |
|---|---|---|
| AC-D4 | BLOCKED | D38–D49 and complete S1–S8 are unavailable; partial D1–D37 cannot establish full decision coverage. |
| AC-D7 | PARTIAL | Charter and Bedrock evidence is now located, but relationship/conflict analysis has not yet been redone against every relevant source; Bedrock remains reference-only. |
| AC-D8 | BLOCKED | complete decision/amendment mapping awaits full corpus and per-event reconciliation. |
| AC-D10 | BLOCKED | inventory/supersession completeness awaits missing register events and remaining mapping review. |

The stale historical context manifest remains superseded for review indexing only by v1; neither v1 nor v2 changes its historical bytes or adoption status.
