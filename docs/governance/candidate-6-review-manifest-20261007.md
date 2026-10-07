# TownSquare candidate-6 review manifest — 2026-10-07

**document_id:** `TS-CANDIDATE-6-REVIEW-MANIFEST-20261007`
**status:** REVIEW-ONLY CANDIDATE — NOT ADOPTED — NOT EFFECTIVE — NOT A LIVE-LEDGER POST
**package commit:** `7fe0af9f0cf0564c8cced3f147dec32fcaa517b3`

## Purpose and recognition boundary

This manifest names the complete review package for candidate 6. It is not an adoption envelope, binding, policy receipt, implementation manifest, or authority source. Inclusion does not adopt, activate, accept, supersede, or grant effect to any listed item. Reviewers cite the listed exact bytes; a path, title, package inclusion, successful review, or digest alone does not confer authority.

For review purposes only, this manifest **supersedes** `docs/governance/context-compliance-manifest-v0.1-candidate.json` as the package index. That stale historical candidate remains preserved, unchanged, inactive, and non-authoritative. This limited supersession neither retires it nor changes any adoption state.

## Exact review inputs

`Git blob` means the blob at package commit `7fe0af9`. `Local evidence` means a pending-ingestion local file that is not yet a Git object; its working-byte hash is reported, not asserted as a permanent record identity. All SHA-256 values are of raw bytes, not text-normalized bytes.

| Role | Path | Status | Identity basis | SHA-256 |
|---|---|---|---|---|
| governing candidate | `docs/governance/town-square-doctrine-v2.0-candidate-6-20261007.md` | candidate; not adopted | Git blob `f77dedd0239f2188737e41e7c4aa8accab9caac6` | `93A511C3679A0C6DD6531CF52C91515C6F2EFC84B72EA2072B0B44F78C21EFA8` |
| RoE companion | `docs/governance/rules-of-engagement-v0.3-candidate-20261007.md` | candidate; not adopted | Git blob `9729703d79008b90070d9d1d223bcb850947d0b9` | `2E4B3647D6380F21721EBD23EBB5E244DB492E387BF793066DDA0238B3FE3CC8` |
| object/lifecycle companion | `docs/governance/townsquare-object-lifecycle-governance-v1.1-candidate-20261007.md` | candidate; not adopted | Git blob `150c5e6f2d8e1fedab874761c9dc24b67e4f39ed` | `E021DA86A785FEDCDA085031F04AC3FFE541218435ACCD882B2E7853F838EA35` |
| authority-resolution companion | `docs/governance/adopted-authority-resolution-v0.2-candidate-20261007.md` | candidate; not adopted/effective | Git blob `9b8df5fddae4922b65b57437326630e449cc92ce` | `74CA5A5A0FAAB14E82BE80F047AE92903BA4D80FAE86B03181E8E6E0AAED3802` |
| inventory and decision map | `docs/governance/governance-inventory-supersession-map-v1.1-candidate-20261007.md` | review evidence; not authority | Git blob `477c1f18989e82bf94d407c2542b09e73cb9d828` | `7D1FAFA0C3CEC7B6527A2B3E67B736E00F9D7457778F5EF4468DA1043D1D37B7` |
| evidence/receipt profile | `docs/governance/governance-evidence-policy-receipt-profile-v1.1-candidate-20261007.md` | candidate; not adopted | Git blob `2d0a4f664df10355458718448f0788efc7e192b2` | `6E5DD32FF33B00E6EA12F57E578613A0DD368852037CAF580B82A184D9AB116A` |
| Eddie reconciliation | `docs/governance/kano-reconciliation-eddie-review-6239f12-20261007.md` | review response; not authority | Git blob `3139cae977e1d7c7e105fb4fb2cac60099d4d612` | `A46775441CE758AFF2A9A8C2AC665202DA8D62AB9515A9D0887CE9325368361F` |
| source snapshots / gaps | `docs/governance/governance-source-snapshots-and-evidence-gaps-20261007.md` | review evidence; not authority | Git blob `9bd23e766ff6b628dd6a3e7340121c12b20c30dc` | `FC04EA562FBC5D71F31DF6C7E613DF4BD80BA93C34741FBA7582BD397CE0B0FA` |
| ratified acceptance source | `docs/governance/ip-man-doctrine-acceptance-ratification-20261006.md` | acceptance input; not candidate adoption | Git blob `0bc13e8ccfb0da0fa134f5802510d17c25810c8d` | `CB70D91131F2F418A88AEBAD52A4D15EB1F1ADF38DD17888ECA3D2B6CE88AF2C` |
| Eddie direct review receipt | `docs/governance/reviews/eddie-brock-governance-review-6239f12-20261006.md` | local pending ingestion; immutable by this work | local evidence, no Git blob | `9A503268FD1C6180D25D4DA822DB8174BA2378EE7ED32F5795FD85005FEAD104` |
| Eddie review evidence | `docs/governance/reviews/eddie-brock-governance-review-6239f12-20261006.evidence.json` | local pending ingestion; immutable by this work | local evidence, no Git blob | `D6CE826F70A017E84759C8602398F27E9C5438088CB1AEF18651B05153E53EE2` |

The older review index is intentionally not a package component:

| Historical item | Status | Git blob | SHA-256 |
|---|---|---|---|
| `docs/governance/context-compliance-manifest-v0.1-candidate.json` | stale candidate; preserved, unchanged, review-index superseded only | `3511d4351468a1365d04397854de4f687e8524a5` | `498977116BF368A99D3B7511A042B15997C972B6872A3A8C8678D1126C00ECAE` |

## Required review outcomes and blocked acceptance state

| Acceptance area | State | Reason |
|---|---|---|
| AC-D4 — source/decision coverage | BLOCKED | the decisions register snapshot with event corpus, identity, watermark, digest, and retrieval time is unavailable; the per-decision map remains provisional. |
| AC-D7 — relationship/conflict analysis | BLOCKED | canonical Agentic Operating Charter and Bedrock Doctrine snapshots are unavailable; no relationship or conflict claim may be completed from secondary mentions. |
| AC-D8 — traceable decision/amendment mapping | BLOCKED | the missing register snapshot prevents verification that every decision/amendment disposition is complete and current. |
| AC-D10 — inventory/supersession completeness | BLOCKED | unavailable canonical sources prevent a complete inventory and conflict/supersession determination. |

All other acceptance findings remain subject to independent review; a non-blocked row is not an adoption finding. The specific source gaps, search boundary, and stale-input check are recorded in `governance-source-snapshots-and-evidence-gaps-20261007.md`.

## Reviewer procedure

1. Obtain each tracked item from commit `7fe0af9` and recompute its raw-byte SHA-256 against this table.
2. Recompute local Eddie receipt/evidence hashes before relying on them; do not treat their current local presence as ledger publication.
3. Reject this review package if a listed value differs, a required item is absent, an unlisted modified governance artifact is represented as package content, or any blocked evidence gap is presented as closed.
4. Do not adopt, activate, deploy, or file this package based on this manifest. Those actions require separate authorized records.
