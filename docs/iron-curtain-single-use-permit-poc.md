# Iron Curtain exact-action single-use permit POC contract

**Profile:** `townsquare-action-permit-poc-v1`

**Story:** `IRON-CURTAIN-PERMIT-POC-CONTRACT`

**Vertical thread:** `01a11b47-a33e-766f-8276-55bced454714`

**Status:** contract frozen for Jackie Chan data-invariant review and GSP security review

**Baseline:** TownSquare commit `9772e0656a75389e98564aab6f7a0d25fe47fa65`

## Decision

The POC adds one issuance contract, `POST /v1/action-permits`, and makes one header, `X-Action-Permit`, mandatory on `POST /v1/events`. A permit is an opaque bearer credential for exactly one proposed event. It is bound to the authenticated actor, derived action capability, target thread, target revision, canonical event payload, intended mutation idempotency key, typed Vertical story fixture, verified canary proof, governance context, compact decision record, audience, 120-second lifetime, key, and single-use profile.

The permit is an authorization artifact, not proof that its claims are true or that execution succeeded. `CANARY_TEST` authenticates the fixture request in this non-authoritative canary. It is **not live Vertical enforcement** and must not be represented as such in an event, audit record, response, or retained evidence.

This contract reuses the current in-process ledger, receipt issue identifier, HMAC key plumbing, immutable tables, idempotency record, and event transaction. It adds no service, database migration, schema head, or Compose topology change.

## Canonicalization and hashes

All `*_sha256` values are lowercase hexadecimal SHA-256 digests. Canonical JSON uses the repository's existing UTF-8 serialization: object keys sorted lexicographically, separators `,` and `:` with no insignificant whitespace, Unicode emitted without ASCII escaping, and no non-JSON numeric values. The event payload digest is `SHA-256(canonical_json(request_body))`. The mutation idempotency digest is `SHA-256(UTF8(Idempotency-Key))`. The decision-record digest is `SHA-256(canonical_json(decision_record))`.

The persisted permit binding is validated by `canary/schemas/action-permit-poc-v1.schema.json`. Its top-level `schema` value is `townsquare-action-permit-poc-v1`. Every stored or compared binding uses the complete schema object; validation never drops unknown fields because the schema is closed with `additionalProperties: false` throughout.

## Issuance: `POST /v1/action-permits`

The caller supplies its normal bearer authorization and the same proposed event body, `Idempotency-Key`, and `If-Match` value that it will later send to `/v1/events`. It also supplies the compact `decision_record`, the typed Vertical story fixture, the existing signed canary proof, and the complete retrieved governance bundle acknowledgements. The endpoint derives the actor and action capability server-side. A caller-provided actor or action never overrides those values.

Issuance succeeds with HTTP 201 and returns:

```json
{"action_permit":"<opaque bearer>","expires_at":"<RFC 3339 UTC timestamp>","permit_id":"<existing receipt issue identifier>","ttl_seconds":120}
```

`action_permit` is returned once and is never returned by a read or evidence endpoint. `permit_id` is the existing immutable `context_receipt_issues.receipt_id`; it is safe to retain as an identifier and is not a bearer secret.

Before issuing, the service must:

1. authenticate the actor and resolve its registered canary identity fixture;
2. validate the proposed event and derive its required action capability with the same rules used by `/v1/events`;
3. validate `Idempotency-Key` and `If-Match`, then calculate their exact bindings;
4. validate the decision-record shape and hash;
5. verify the signed canary proof, its signature, expiry, nonce, actor, action, target, payload context, audience, and service;
6. resolve the pinned typed `VERTICAL_STORY` fixture and verify its story key, thread and event identifiers, content hash, and source snapshot hash;
7. verify complete retrieval of the current governance bundle and bind its manifest, bundle, Charter, and required-item aggregate hashes; and
8. create the opaque 120-second bearer, persist its HMAC-SHA-256 under the distinct domain `townsquare-action-permit-poc-v1\0`, and append exactly one `action_permit_issued` audit record containing the schema binding.

Missing or malformed decision records, event fields, fixture fields, or hash fields return HTTP 400 and create no receipt issue or issuance audit. Missing, invalid, expired, replayed, or mismatched canary proof, Vertical fixture, or governance evidence returns HTTP 428 and creates no permit. Authentication or capability failure uses the existing native authentication response and creates no permit.

The compact decision record contains exactly these required meanings:

- `objective`: the understood objective or requested outcome;
- `evidence_references`: one or more stable references supporting the decision;
- `assumptions`: one or more statements labeled `stated`, `inferred`, or `verified`;
- `selected_action`: the exact proposed action, expressed compactly;
- `applicable_rules`: one or more rule or directive references;
- `expected_outcome`: the expected observable result.

Schema validation establishes shape and exact binding only. It does not establish factual truth, sound reasoning, or a wise choice.

## Persisted identity and secret handling

The raw permit bearer must never be written to the database, audit detail, event, response other than its one-time issuance response, returned evidence, log, metric label, trace, diagnostic, or exception text. Request logging must redact `X-Action-Permit` before formatting either headers or errors.

The persisted credential identity is the existing receipt issue identifier plus the HMAC-hashed bearer. `context_receipt_issues.token_hash` holds only `HMAC-SHA-256(receipt_key, "townsquare-action-permit-poc-v1\\0" || UTF8(raw_permit))`; `receipt_hash_key_id` identifies the HMAC key. The immutable `context_audit` row with `kind = "action_permit_issued"` uses that receipt ID and stores the complete schema-valid binding in `detail_json`. A receipt issue is an action permit only when this audit binding exists, is unique for the receipt ID, and validates completely. A legacy context receipt therefore cannot pass as an action permit even if it was minted with the same underlying key.

The binding's `bearer_hmac_sha256` is the stored HMAC value, never an unhashed bearer digest. Database uniqueness is not added in this POC; issuance logic and evidence verification must fail closed unless exactly one issuance audit exists for the permit ID.

## Mutation gate: `POST /v1/events`

Every new mutation requires `X-Action-Permit`. `X-Context-Receipt`, `X-Canary-Test-Proof`, and `X-Canary-Test-Signature` cannot satisfy the mutation gate and are not mutation authority. The canary proof is consumed by permit issuance only.

For a request whose `(authenticated principal, "post", Idempotency-Key)` has no `native_requests` record, the service validates the bearer HMAC and the complete immutable binding, re-computes every request binding, and consumes the permit in the existing event transaction. Validation covers:

- authenticated principal and registered actor fixture;
- server-derived action capability;
- event `thread_id` and `If-Match` revision (`new` when omitted under the existing create contract);
- canonical request-body SHA-256;
- SHA-256 of the exact `Idempotency-Key` bytes;
- typed Vertical story fixture and verified canary-proof references and hashes;
- current governance manifest, bundle, Charter, and required-item aggregate hashes;
- canonical decision record and digest;
- audience `townsquare-canary-ledger-api`, service `townsquare-ledger-v0`, and endpoint `/v1/events`;
- `ttl_seconds = 120`, `expires_at` strictly after validation time, configured key ID, `single_use = true`, and `max_uses = 1`; and
- exactly one valid `action_permit_issued` record and no prior consumption.

Missing, malformed, expired, mismatched, invalidly persisted, or already-consumed permits return HTTP 428. These denials create no event, native request, consumption, ledger outcome, or notice intent and do not consume an otherwise unused permit. A mismatch in any bound dimension is fail-closed and leaves the permit available only for its exact bound request until expiry.

Once validation passes, the existing single `BEGIN IMMEDIATE` transaction appends the event content and envelope, the `native_requests` result, exactly one receipt consumption linked by `permit_id`, one `action_permit_consumed` context audit, the matching `ledger_audit` outcome, and the notice intent. Any failure at an existing atomic boundary rolls the transaction back, leaving no partial event or outcome and leaving the permit unconsumed.

## Retry and replay ordering

The lookup of `(principal, "post", Idempotency-Key)` remains first inside the event transaction:

- If the key and canonical request hash match an existing committed request, return its original HTTP 201 response. This exact same-key retry does not require the bearer still to be unexpired, does not validate or consume it again, and creates no second row.
- If the key exists but the canonical request hash differs, return HTTP 409 and create or consume nothing.
- If no committed request exists, validate the permit. Reuse of the permit with a different idempotency key is replay, returns HTTP 428, and creates or consumes nothing.

An exact retry means the same authenticated principal, operation, `Idempotency-Key`, `If-Match`, and canonical event payload. Permit and proof headers are authorization transport and are excluded from the existing canonical request hash.

## Persistence and acceptance mapping

| # | Required observable behavior |
| --- | --- |
| 1 | Missing `X-Action-Permit` returns 428 and creates no event, native request, consumption, outcome, or notice. |
| 2 | A legacy context receipt returns 428 because it has no unique, valid `action_permit_issued` binding. |
| 3 | A canary authority proof alone returns 428; proof verification occurs at issuance, not mutation. |
| 4 | One exact unexpired permit commits one mutation and one consumption. |
| 5 | The immutable receipt issue, issuance audit, consumption, ledger outcome, native request, and event remain linked and readable after database close and reopen. |
| 6 | The raw permit is absent from the database, evidence, logs, metrics, traces, and exception text. Only its one-time issuance response contains it. |
| 7 | Same key and same request return the original event/result with no second consumption. |
| 8 | The same permit with another key returns 428 as replay. |
| 9 | Actor, action, target, revision, payload, idempotency, authority, governance, or decision-record mismatch returns 428 without consumption. |
| 10 | Missing or malformed decision records return 400 before issuance and persist nothing. |
| 11 | Changed governance or an invalid persisted binding returns 428 and fails closed without consumption. |
| 12 | Failure at each existing atomic boundary rolls back the event, request, consumption, outcome, and notice. The permit remains unconsumed. |
| 13 | The accepted action has exactly one issuance audit, one consumption, one ledger event, and one matching ledger outcome, all joined through the permit/request/event identifiers and binding hashes. |

Expiry is checked only for a first execution attempt. Expiry never erases issuance evidence and does not alter an immutable state row. Effective state is derived append-only: `ISSUED` after issuance, `CONSUMED` when one linked consumption exists, otherwise `EXPIRED` after `expires_at`. Any impossible multiplicity or contradictory persisted binding is `INVALID` and fails closed.

## Workflow and boundaries

The client retrieves the exact current context, constructs its proposed event and compact decision record, obtains a signed `CANARY_TEST` proof for that fixture request, calls `/v1/action-permits`, and then submits the unchanged event/key/revision with the returned bearer to `/v1/events`. Evidence verification joins the immutable issuance, consumption, native request, ledger event, and outcome after commit.

No application behavior, migration, deployment, or topology change is part of this contract story. Live Vertical verification, reusable or renewable permits, batch authorization, leases, production identity hardening, and database-level uniqueness for the profile-specific issuance audit remain deferred.

## References

- `C:\Workspace\iron-curtain\docs\IP-MAN-MVP-WORK-ORDER.md` at Iron Curtain commit `8bdcd6c72ae73e9747ceafabb30b5fdfd0a10fe9`
- `C:\Workspace\iron-curtain\docs\IRON-CURTAIN-DESIGN.md`
- `C:\Workspace\iron-curtain\docs\SHURI-DISCOVERY-BASELINE.md`
- `C:\Workspace\iron-curtain\docs\MISSION-AND-SCOPE.md`
- TownSquare `registrar/app/native_ledger.py`, `registrar/app/main.py`, and migrations 010, 011, and 014 at commit `9772e0656a75389e98564aab6f7a0d25fe47fa65`
