# Operator adoption packet — candidate

**document_id:** `TS-OPERATOR-ADOPTION-PACKET-1-CANDIDATE-20261007`
**status:** PRE-DECISION PACKET — NOT AN ADOPTION — NOT EFFECTIVE

## Proposed governing set

If approved, each artifact below is adopted separately but through one singular operator decision, with scope `TownSquare governance` and effective time exactly as recorded in that decision. Every listed dependency must be adopted at the same effective time or the package remains non-effective.

| Proposed artifact | Document ID / version | Raw SHA-256 | Dependencies |
|---|---|---|---|
| Doctrine | `TS-DOCTRINE-2.0-CANDIDATE-6-20261007` / candidate 6 | `93A511C3679A0C6DD6531CF52C91515C6F2EFC84B72EA2072B0B44F78C21EFA8` | RoE, Object Dictionary, Lifecycle v1.3, Receipt, Resolver, Protected Control |
| Rules of Engagement | `TS-ROE-20261007-CANDIDATE-03` / v0.3 | `2E4B3647D6380F21721EBD23EBB5E244DB492E387BF793066DDA0238B3FE3CC8` | Doctrine, Receipt, Resolver, Lifecycle |
| Object Dictionary | `TS-OBJECT-DICTIONARY-1.3-CANDIDATE-20261007` / v1.3 | `B8FD42FB093094276117C4374D2D88DD868A2F8E75D57BA85B3AF25B842B6F78` | Doctrine, Lifecycle v1.3 |
| Consolidated Lifecycle | `TS-OBJECT-LIFECYCLE-1.3-CANDIDATE-20261007` / v1.3 | `EB92B50B0A968A907EA5FC42B0A9748BFD1C22048D3365165C1366E515383379` | Doctrine, Object Dictionary, Resolver |
| Receipt Profile | `TS-GOV-EVIDENCE-RECEIPT-1.2-CANDIDATE-20261007` / v1.2 | `C97E5377DEBCA1663543147C45A15769F02F867FD2685AE5197EADD853767058` | Doctrine, Resolver |
| Authority Resolver | `TS-ADOPTION-RESOLUTION-0.3-CANDIDATE-20261007` / v0.3 | `15ADDC665D0F956829541014E6DB36AF14FC21C7DEF45FC24A2DB79CC6701897` | Doctrine, Protected Control, Receipt |
| Protected Operator Control | `TS-PROTECTED-CONTROL-0.1-CANDIDATE-20261007` / v0.1 | `5915A501F0A79B7A72BDF276DFE7AA9FD4707804245C2FB7E56B970D79D554FC` | Doctrine, Resolver |

## Review/evidence inputs — not proposed governing members

- Candidate-6 Commentary/traceability: `TS-DOCTRINE-2.0-CANDIDATE-6-COMMENTARY-V5-20261007`, SHA `FC5B7A5A32EC629C3E63EC074E17728DEC5016F79B5694BB1DF38B4F18238243`.
- V6 scope binding, SHA `530FEC055C6F89FB84B515D8763B628E758CF39B4C1651A1F81160985C0E1778`, and V6 index, SHA `F282A1294921A9A41702D2BABD166D75D77F36A10E4351BCFCA1E280FC884464`.
- V6 commit/tree: `3132194b2fe7522d9b489a99180b83b3978ecab8` / `abdffc114c61c7441c19576fa588e4d4d8cb4a73`.
- Filed confirmations: GSP blob `269f537affd9682b998926ec2fa281eb8046b6ea`, SHA `84CC80F2F820FBAD7B57CC332DF1ACE3E49E61FA408D2E38B5F6D9C73346FACB`; Ronda blob `b9e580c47fd5de9d549a0b7974aa091609cd937f`, SHA `50301098502D25C1DF69058F1684D86F9AB33C0CB7A635A83B27A1B762B4B234`.
- Evaluation method: verified captured operational instance weight 5; hypothetical/adversarial thought case weight 1. Counts and provenance remain visible; a hypothesis may prompt a test but cannot outweigh contrary verified operational evidence. This is not an adoption score.

## Operator decision

**Decide one:**

> **ADOPT** the exact proposed governing set above, including consolidated Lifecycle v1.3, for TownSquare governance at the effective time stated in this decision; **or DECLINE / RETURN FOR REVISION**.

This decision does not authorize archival, runtime enforcement, NAS deployment, implementation activation, or closure of restore/conformance REWORK. Any archive needs a separate operator authorization naming exact targets/hashes, preservation destination, and exclusion of active/current governance.
