# Governance Evidence and Policy Receipt Profile v1.0 — candidate

**document_id:** `TS-GOV-EVIDENCE-RECEIPT-20261006-CANDIDATE`
**status:** CANDIDATE — NOT ADOPTED — NO GATE ARMED

## Purpose

This profile makes the observable evidence for a governed action reconstructable. It does not define a transport, storage product, schema implementation, or authority source.

## Required policy receipt fields

| Field | Meaning |
|---|---|
| `receipt_id`, `issued_at`, `expires_at`, `single_use` | stable receipt and bounded validity |
| `actor`, `represented_authority` | authenticated actor and any claimed delegation, separately resolved |
| `action`, `target`, `expected_revision` | exact operation and record version |
| `governance_set` | ordered document IDs, versions, byte hashes, adoption references, and revocation outcome |
| `context_set` | selected/retrieved object identities, versions, hashes, timestamps, and outcome |
| `criteria_set` | applicable stable criterion IDs, versions/hashes, and required evidence |
| `binding_set` | accepted binding identity/version/hash and capability scope |
| `policy_evaluation` | rule IDs evaluated, decidable inputs, allow/deny/park result, reason codes |
| `authority_resolution` | adoption/control identity, scope, freshness, and result |
| `audit_ref` | immutable event/evidence reference |

The profile prohibits secret bearer values and hidden reasoning. `retrieved`, `evaluated`, `allowed`, `denied`, and `parked` are observable claims only; none means understood, agreed, intended, or compliant beyond the recorded action.

## Evidence status

`CANDIDATE`, `REPORTED`, `VERIFIED`, `STALE`, `SUPERSEDED`, `REVOKED`, and `UNKNOWN` are evidence statuses, not lifecycle or authority states. A result is `STALE` when its governing/criterion/binding hash no longer applies. A result is `UNKNOWN` when retrieval or resolution cannot be decided.

## Validation and disposition

The binding must re-resolve authoritative current state at commit. Missing, mismatched, expired, revoked, reused, or unverifiable material parks an ordinary governed action and appends an audit result. Operator control remains available. An implementation maps the profile to exact fields only after separate review, QA, and operator approval.
