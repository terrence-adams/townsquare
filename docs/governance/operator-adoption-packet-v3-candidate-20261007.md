# Operator adoption packet v3 — candidate

**document_id:** `TS-OPERATOR-ADOPTION-PACKET-3-CANDIDATE-20261007`
**status:** PRE-DECISION PACKET — NOT AN ADOPTION — NOT EFFECTIVE
**predecessor:** V1 blob `c0beb5da16d7dd5cc3073fd92c59fac4e6039570`; raw SHA-256 `37A5BDE41EC78FAB3476A860AE31C8974AEEB40F6B49ADF5F8041560592CE91C`

## Proposed governing set — seven artifacts

If approved, each is adopted separately through one singular decision, scope `TownSquare governance`, at the same effective time recorded in that decision:

1. Doctrine `TS-DOCTRINE-2.0-CANDIDATE-6-20261007` — `93A511C3679A0C6DD6531CF52C91515C6F2EFC84B72EA2072B0B44F78C21EFA8`.
2. RoE `TS-ROE-20261007-CANDIDATE-03` — `2E4B3647D6380F21721EBD23EBB5E244DB492E387BF793066DDA0238B3FE3CC8`.
3. Object Dictionary `TS-OBJECT-DICTIONARY-1.3-CANDIDATE-20261007` — `B8FD42FB093094276117C4374D2D88DD868A2F8E75D57BA85B3AF25B842B6F78`.
4. Corrected Lifecycle `TS-OBJECT-LIFECYCLE-1.4-CANDIDATE-20261007` — `3AC8C618E72FFC437EEC7D9921BA06068E7943F352C7D498D7436E8E319FD2FB`.
5. Receipt Profile `TS-GOV-EVIDENCE-RECEIPT-1.2-CANDIDATE-20261007` — `C97E5377DEBCA1663543147C45A15769F02F867FD2685AE5197EADD853767058`.
6. Authority Resolver `TS-ADOPTION-RESOLUTION-0.3-CANDIDATE-20261007` — `15ADDC665D0F956829541014E6DB36AF14FC21C7DEF45FC24A2DB79CC6701897`.
7. Protected Operator Control `TS-PROTECTED-CONTROL-0.1-CANDIDATE-20261007` — `5915A501F0A79B7A72BDF276DFE7AA9FD4707804245C2FB7E56B970D79D554FC`.

Lifecycle v1.4 is the only lifecycle proposed here. If later adopted, it supersedes lifecycle v1.1, v1.2, and v1.3 for adopted scope only; it preserves the v1.1 protected-control cancellation path, transition table, and v1.2 closure predicate/case table.

The lifecycle hold receipt is pinned: commit `a34f5e313b90516fa115401a420412001100c026`, tree `45e0bdbe5ac4718b4f12ebf07e14aad88faec014`, blob `1321ac3170c9a6f2e3d66a6b58c8b3bdcc72e624`, raw SHA `ED7AB810087E55361BDA116C1F269B1281596A144FE94442FC775EEBF4476C28`. Its decision is `RETURN FOR REVISION — DO NOT ADOPT` lifecycle v1.3 (`EB92...`); it reopens only lifecycle consolidation and this packet.

## REAL-05 evidence and readiness

REAL-05: commit `6052e7af2b5f6db26da4b1ed44c6af57f649629a`; tree `362fe7e1819ae9637f1b2daed522a8d4c7cf934d`; blob `ccdff7eecca751059e8fa1f10dc9729fe44425b4`; SHA `F90FF9D6787DE324253B32C273DA4DCBF7BF4ECCAA4A38852124243B4C82ED47`; subject head `8b39032db1144140a7460d60946463803b4eac86`. Results: Crier 21/21; Tracker 67 pass; conformance 47 pass/2 designed blockers/1 skip; missing Registrar FastAPI and Viewer Streamlit dependencies; template-only backup and stale package identity rejected. No network/NAS/container/live service.

Evidence method: 5 real instances / weighted 25 versus 10 static instances / weighted 10. This method is evaluation only, not an adoption score.

Governance packet is ready for operator decision. Runtime/release is **NOT READY**. Governed writes remain disabled until exact release identity, offline wheelhouse/SBOM/images, Registrar/Viewer in exact images, and isolated restore/replay evidence pass. Release/governance commit coupling belongs to implementation/release contract, not Doctrine.

## Operator decision

> **ADOPT** the exact seven-artifact governing set above, including corrected Lifecycle v1.4, for TownSquare governance at the effective time stated in this decision; **or DECLINE / RETURN FOR REVISION**.

This decision does not authorize archive, runtime enforcement, deployment, release, or restore/conformance closure.
