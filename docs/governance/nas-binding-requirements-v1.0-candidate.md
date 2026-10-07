# NAS durable-record binding requirements v1.0 — candidate

**document_id:** `TS-NAS-DURABLE-RECORD-BINDING-REQ-20261006-CANDIDATE`
**status:** CANDIDATE — NOT ACCEPTED — NO RUNTIME ACTIVATION

This infrastructure-specific document is intentionally outside the Doctrine. It specifies what a NAS-targeted implementation must demonstrate when mapped to an adopted governance package; it confers no governance authority.

| Requirement | Acceptance evidence |
|---|---|
| append-only committed record, stable identities, store order, and crash-safe write | independent write/restart/replay evidence |
| access perimeter separates operator control, writers, readers, projections, and observer | negative authorization tests and audit evidence |
| governed write resolver validates exact adoption/binding/receipt and fails closed | stale/missing/mismatch truth table |
| TownSquare source history remains authoritative; Vertical projection and Wonderland observation are read-only | denied-write and reconciliation tests |
| backup, restore, integrity, and replay preserve authoritative history | isolated restore/replay and hashes |
| notices are pointers; failure cannot change the ledger | duplicate/lost/delayed notice tests |
| secrets remain external to record/audit; transport/at-rest protection is documented | secret scan and configuration review |

The binding implementation may use containers, local storage, network services, or a different topology, but its exact version, configuration, and evidence must be separately accepted by the operator. No current candidate makes a NAS implementation active.
