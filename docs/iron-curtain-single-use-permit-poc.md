# Iron Curtain exact-action single-use permit POC contract

**Profile:** `townsquare-action-permit-poc-v1`

**Story:** `IRON-CURTAIN-PERMIT-POC-CONTRACT`

**Vertical thread:** `01a11b47-a33e-766f-8276-55bced454714`

**Status:** corrected under the issuance amendment; Jackie Chan and GSP re-review required before implementation

**Baseline:** TownSquare commit `9772e0656a75389e98564aab6f7a0d25fe47fa65`

## Decision

The POC adds one issuance contract, `POST /v1/action-permits`, and makes one header, `X-Action-Permit`, mandatory on `POST /v1/events`. A permit is an opaque bearer credential for exactly one proposed event. It is bound to the authenticated actor, derived action capability, target thread, target revision, canonical event payload, intended mutation idempotency key, typed Vertical story fixture, verified canary proof, governance context, compact decision record, audience, 120-second lifetime, key, and single-use profile.

The permit is an authorization artifact, not proof that its claims are true or that execution succeeded. `CANARY_TEST` authenticates the fixture request in this non-authoritative canary. It is **not live Vertical enforcement** and must not be represented as such in an event, audit record, response, or retained evidence.

This contract reuses the current in-process ledger, receipt issue identifier, HMAC key plumbing, immutable tables, idempotency record, and event transaction. It adds no service, database migration, schema head, or Compose topology change.

## Canonicalization and hashes

All `*_sha256` values are lowercase hexadecimal SHA-256 digests. Canonical JSON uses the repository's existing UTF-8 serialization: object keys sorted lexicographically, separators `,` and `:` with no insignificant whitespace, Unicode emitted without ASCII escaping, and no non-JSON numeric values. The event payload digest is `SHA-256(canonical_json(request_body))`. The mutation idempotency digest is `SHA-256(UTF8(Idempotency-Key))`. The decision-record digest is `SHA-256(canonical_json(decision_record))`.

The persisted permit binding is validated by `canary/schemas/action-permit-poc-v1.schema.json`. Its top-level `schema` value is `townsquare-action-permit-poc-v1`. Every stored or compared binding uses the complete schema object; validation never drops unknown fields because the schema is closed with `additionalProperties: false` throughout.

## Permit authority story

The runtime permit authority is the typed Vertical CANARY story, not this CONTRACT story. Every permit binding uses these exact constants:

| Field | Required value |
| --- | --- |
| `story_key` | `IRON-CURTAIN-PERMIT-POC-CANARY` |
| `thread_id` | `01a11b47-a6b6-71f1-9348-0d1e9ed21c5d` |
| opening `event_id` | `01a11b47-a6b7-7372-b52f-2d2002ed2081` |
| opening `content_sha256` | `9a1cbf7ddff351494331f9da521863fa37d232093c7fe1043bd73541b3645f87` |
| `source_status` | `WORKING` |

`source_snapshot_sha256` is SHA-256 over the exact decoded canonical UTF-8 `snapshot_bytes` in the trusted authority item. The fixture packager normalizes the authoritative Vertical records into that closed object before release review; the ledger hashes the admitted bytes before parsing and never reserializes them to establish identity. `source_snapshot_ref` is the content-addressed URN `urn:ynm:vertical-story-snapshot:v1:sha256:<source_snapshot_sha256>`.

The retained snapshot must contain, or unambiguously resolve, the selected story and thread, opening event and content hash, current lifecycle state, current Vertical version or head event, satisfied REVIEW dependency, retrieval time, and source provenance. Issuance validates all four representations together: the digest suffix in the URN, the separately stored `source_snapshot_sha256`, the SHA-256 of the retained exact bytes, and the fields parsed from those bytes. Any disagreement fails closed. JSON Schema validates each represented field but cannot express this cross-field and external-byte agreement; service logic is normative for that check.

Issuance requires the retained snapshot to show the CANARY story in `WORKING`. The CANARY story may enter `WORKING` only after REVIEW acceptance and Helio's checkpoint. Until all three predicates are present in the trusted retained fixture, no valid live permit fixture exists. A synthetic `WORKING` object can validate the schema for contract testing, but it is not authority to issue a live permit.

The pinned snapshot is a retained point-in-time fixture for this non-authoritative proof. It is not live Vertical verification. Git commit and tree hashes identify build or contract provenance only and must never be used as Vertical authority snapshots. This clarification is part of the approved design and does not amend the work order.

## Issuance: `POST /v1/action-permits`

The caller supplies its normal bearer authorization and the same proposed event body, `Idempotency-Key`, and `If-Match` value that it will later send to `/v1/events`. It also supplies the compact `decision_record`, the signed permit-proof representation and signature, complete retrieved governance bundle acknowledgements, and at most the opaque `source_snapshot_ref` it expects. It cannot supply snapshot bytes, a file path, manifest identity or bytes, lifecycle state, REVIEW or checkpoint status, source version, or head event. The endpoint derives the credential ID, actor, action, and authority values server-side.

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
6. resolve the pinned typed `VERTICAL_STORY` CANARY fixture and verify its story key, thread and opening event identifiers, opening content hash, `WORKING` state, current version, retrieval time, and exact-byte source snapshot binding;
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

## Side-effect-free pre-validation

Before the write lock, the route may perform only bounded work with no durable side effect:

1. Parse the closed request and headers, rejecting duplicate JSON fields, unknown fields, malformed hashes, oversized values, and non-canonical proof bytes.
2. Authenticate the bearer and obtain the server-resolved principal, credential ID, capability set, policy version, and credential expiry. Request JSON has no accepted credential-ID override.
3. Validate the proposed event and derive the action capability with the same function used on first execution.
4. Canonicalize the event, mutation idempotency key, expected revision, compact decision record, and governance references.
5. Load `/run/config/ledger-context-manifest.json` through the existing read-only regular-file and configured expected-byte-hash checks, then select the one authority item defined below.
6. Construct the expected proof preimage from server and trusted-store values; verify its closed shape, canonical bytes, signature, issuer/key allowlist, and coarse time bounds without reserving its nonce.
7. Generate the random bearer in memory and calculate its domain-separated HMAC. Neither value is returned before commit, and only the HMAC may be persisted.

Malformed input returns 400. Authentication failure uses the existing 401 or 403 response. Invalid, expired, mismatched, untrusted, or replayed authorization material returns 428. Pre-validation creates no nonce, receipt issue, or audit.

## Atomic issuance transaction

`NativeLedger` owns one transaction on the request's SQLite connection and performs exactly these steps in order:

1. Execute `BEGIN IMMEDIATE`.
2. Capture one service `transaction_now` in UTC whole seconds. Every issuance comparison and stored issuance timestamp uses it.
3. Re-read `auth_credentials` by the authenticated credential ID and require the same principal, unexpired credential, no revocation, the same authorization policy, and the derived capability.
4. Revalidate the persisted governance bundle, every retrieved-item acknowledgement, cardinality and hashes, and trusted manifest identity and byte hash; reconstruct and compare every signed proof binding.
5. Search committed valid `action_permit_issued` bindings for the tuple `(principal, credential_id, operation, capability, target thread, expected revision, canonical payload SHA-256, mutation idempotency-key SHA-256)`. A match returns 409 `issuance_already_committed`, optionally with only its permit ID and expiry, and performs no write.
6. Reserve `(key_id, nonce)` with one insert into `verifier_nonces`. A primary-key collision is 428 `proof_replay` and aborts. The stateless verifier never performs this insert.
7. Set `issued_at = transaction_now` and `expires_at = transaction_now + 120 seconds`, then insert one `context_receipt_issues` row using the `townsquare-action-permit-poc-v1\0` HMAC domain.
8. Insert one immutable `context_audit` row with `kind = "action_permit_issued"` and the complete schema-valid permit binding.
9. Query by receipt ID and require exactly one matching issue plus exactly one schema-valid issuance audit. Zero, duplicate, malformed, or contradictory evidence is an invariant failure.
10. Commit. Only after successful commit may the route build the 201 response containing the raw bearer.

Nonce reservation, receipt issue, and issuance audit commit together or all disappear. Validation errors, failpoints, SQLite errors, process exceptions before commit, and failed commits roll back and return no bearer. Rollback failure or indeterminate database state returns 503; the client treats issuance as unknown pending evidence inspection and does not retry with altered material automatically.

`BEGIN IMMEDIATE` serializes the tuple search. Existing nonce and receipt primary keys, the post-insert exactly-one check, and fail-closed evidence verification form the accepted POC cardinality control. No migration is authorized. If measured concurrency disproves it, implementation stops for Ip Man and Jackie.

### Response loss after commit

The bearer is neither stored nor reconstructable. If commit succeeds and the response is lost, the nonce, issue, and issuance audit remain. A retry of the same tuple returns `issuance_already_committed` before nonce insertion and never reveals or replaces the bearer. The same proof with another tuple reaches nonce insertion and returns `proof_replay`. A fresh proof for the same tuple still returns `issuance_already_committed`. The caller abandons that mutation key and may construct a new mutation with a new key only after the orphan permit expires and authority still permits the work.

## Trusted CANARY authority admission

The issuer-controlled source is the existing hash-pinned, read-only `/run/config/ledger-context-manifest.json`. The service admits exactly one top-level `required_items` entry with `kind = "VERTICAL_STORY_AUTHORITY_POC_V1"`; zero or multiple matches fail closed. Its closed shape is:

```json
{"encoding":"base64url-unpadded","kind":"VERTICAL_STORY_AUTHORITY_POC_V1","profile":"townsquare-vertical-story-authority-poc-v1","ref":"urn:ynm:vertical-story-snapshot:v1:sha256:<64-lowercase-hex>","sha256":"<SHA-256 of decoded snapshot_bytes>","snapshot_bytes":"<base64url-unpadded canonical UTF-8 JSON>"}
```

The service derives `authority_manifest_id` from the manifest's top-level `id` and derives `authority_manifest_file_sha256` from the separately configured exact file digest. It strictly decodes the item bytes, rejects duplicate or unknown fields and non-canonical JSON, and requires the decoded-byte SHA-256 to equal both item `sha256` and the `ref` suffix. The parsed snapshot must match the CANARY constants, state `WORKING`, a non-empty `source_version` equal to `head_event_id`, a valid head content hash, strict retrieval time, and these exact predicates:

- REVIEW: story `IRON-CURTAIN-PERMIT-POC-REVIEW`, relationship `DEPENDS_ON`, disposition `ACCEPTED`, and a valid event ID and content hash.
- Helio: scope `IRON-CURTAIN-PERMIT-POC-CANARY`, gate `CANARY_HANDOFF`, disposition `PROCEED`, and a valid immutable event reference and content hash.

The selected authority values are compared with any caller-supplied opaque snapshot reference. No fallback item exists. Missing, writable, symlinked, unreadable, hash-mismatched, malformed, duplicate, stale, inconsistent, or inadmissible authority fails before nonce reservation. Unreadable service configuration may return 503; it never opens the event gate. The retained fixture is point-in-time proof data and is not live Vertical verification.

## Signed permit-proof profile

`townsquare-action-permit-canary-proof-v1` is an additive detached-signature profile. Its complete closed preimage is defined by `canary/schemas/action-permit-canary-proof-v1.schema.json`. The server constructs the expected object from the authenticated credential row, derived event capability, request and headers, trusted authority item, and persisted governance bundle. The proof contributes only signed representations plus the allowlisted issuer, key, nonce, and proof times. The server requires the exact key set, exact canonical UTF-8 bytes, equality of every derived field, and a valid detached signature.

Signature verification is stateless. It returns verified canonical material and never consumes the nonce; transaction step 6 owns the only nonce reservation. The permit audit retains the proof profile, canonical-preimage SHA-256, signature evidence reference and SHA-256, key ID, and nonce SHA-256. It stores no private key, raw signature where the evidence reference suffices, or raw permit.

`CANARY_TEST` authenticates this non-authoritative fixture request. It does not become Vertical authority. Existing registry proof-v2 behavior remains separate and compatible.

## Exact clock contract

Every timestamp uses `YYYY-MM-DDTHH:MM:SSZ`: uppercase `T` and `Z`, fixed-width components, whole seconds, no offset, no fraction, and no leap second. Parsing rejects normalization, trailing data, naive values, impossible dates, and alternate offsets.

One injectable service UTC clock supplies issuance and first-use comparisons. Permit times are server-generated: `issued_at = transaction_now`, `expires_at = issued_at + 120 seconds`, and `ttl_seconds = 120`. First use is valid only for `issued_at <= use_now < expires_at`; equality at expiry is expired and there is no grace. Persisted strings are parsed back and the exact arithmetic is rechecked before first use.

Only the externally signed proof permits future skew: `proof.issued_at` may be at most five seconds after `transaction_now`; six seconds fails. Its interval must be positive and at most 300 seconds, and `proof.expires_at` must be strictly later than `transaction_now`. There is no post-expiry grace. Tests use a fixed injected clock.

## Credential binding and retry

The server derives `credential_id` only after secret verification plus revocation and expiry checks, then binds it into the expected proof, permit, issuance audit, tuple search, and first-use comparison. If one principal owns credentials A and B, B cannot first-use A's permit: the service returns 428 `credential_mismatch`, creates no event, and leaves the permit unused. Revocation or expiry of A before first use also fails closed.

After A has committed the mutation, the idempotency lookup remains first. A valid B for the same principal and required capability may receive the original 201 only when principal, operation, mutation key, expected revision, and canonical request hash match. This is a result lookup, creates no event or consumption, and does not revalidate A's permit. A different principal, request hash, or missing capability cannot use the committed-retry rule.

## Permit-only mutation boundary

Every ordinary `/v1/events` first attempt requires `X-Action-Permit` in both the HTTP route and `NativeLedger.post_event`. `X-Context-Receipt`, `X-Canary-Test-Proof`, `X-Canary-Test-Signature`, `verified_canary_test_proof`, legacy receipt validation, and direct service invocation without a permit cannot satisfy, supplement, or bypass the gate. The route may return 400 when legacy authorization headers appear. Separate `/v1/operator/*` and archive controls remain unavailable with 403; no internal bypass is enabled.

The future runtime boundary is limited to `registrar/app/auth.py`, `registrar/app/native_ledger.py`, `registrar/app/main.py`, `canary/poc_client.py`, `canary/verify_action_permit_evidence.py`, and additive permit-proof support in `shared/canary_authority.py`. `shared/ledger_context.py`, database setup, migrations, R7 contracts, Compose, and deployment topology remain unchanged. No new service or migration is authorized.

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

## Golden vectors

Each one-line code block below is the exact compact UTF-8 JSON byte string with no trailing newline. These values are synthetic contract data. The CANARY `WORKING`, REVIEW, and checkpoint fields demonstrate schema and binding behavior and are never live authority.

### Decision record

SHA-256: `c497e77257a14add339c7ae2852edad893ad8b2a9211e841e62ed1c7f151ea7b`

```json
{"applicable_rules":["rule:exact-action-permit"],"assumptions":[{"label":"verified","statement":"Trusted fixture predicates passed"}],"evidence_references":["urn:evidence:fixture"],"expected_outcome":"One governed event commits","objective":"Append one exact CANARY event","selected_action":"request:work"}
```

### Authority item

SHA-256: `e665244aa3d0cbf6b878c010184b7cc83d1516c9f29bdb49b4bfd0edef4b2497`

```json
{"encoding":"base64url-unpadded","kind":"VERTICAL_STORY_AUTHORITY_POC_V1","profile":"townsquare-vertical-story-authority-poc-v1","ref":"urn:ynm:vertical-story-snapshot:v1:sha256:686e50e1247ae9040ebafa070bf8bd02d32db35a6fe350de6027e7e3180e4dda","sha256":"686e50e1247ae9040ebafa070bf8bd02d32db35a6fe350de6027e7e3180e4dda","snapshot_bytes":"eyJoZWFkX2NvbnRlbnRfc2hhMjU2IjoiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYmJiYiIsImhlYWRfZXZlbnRfaWQiOiIwMWExMWI0Ny1hNmI4LTcwMDAtODAwMC0wMDAwMDAwMDAwMDEiLCJoZWxpb19jaGVja3BvaW50Ijp7ImNvbnRlbnRfc2hhMjU2IjoiZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZGRkZCIsImRpc3Bvc2l0aW9uIjoiUFJPQ0VFRCIsImV2ZW50X2lkIjoiaGVsaW8tY2hlY2twb2ludC0xIiwiZ2F0ZSI6IkNBTkFSWV9IQU5ET0ZGIiwic2NvcGVfc3Rvcnlfa2V5IjoiSVJPTi1DVVJUQUlOLVBFUk1JVC1QT0MtQ0FOQVJZIn0sIm9wZW5pbmdfY29udGVudF9zaGEyNTYiOiI5YTFjYmY3ZGRmZjM1MTQ5NDMzMWY5ZGE1MjE4NjNmYTM3ZDIzMjA5M2M3ZmUxMDQzYmQ3MzU0MWIzNjQ1Zjg3Iiwib3BlbmluZ19ldmVudF9pZCI6IjAxYTExYjQ3LWE2YjctNzM3Mi1iNTJmLTJkMjAwMmVkMjA4MSIsInJldHJpZXZlZF9hdCI6IjIwMjYtMTAtMDhUMTg6MDA6MDBaIiwicmV2aWV3X2dhdGUiOnsiY29udGVudF9zaGEyNTYiOiJjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjY2NjIiwiZGlzcG9zaXRpb24iOiJBQ0NFUFRFRCIsImV2ZW50X2lkIjoicmV2aWV3LWFjY2VwdGVkLTEiLCJyZWxhdGlvbnNoaXAiOiJERVBFTkRTX09OIiwic3Rvcnlfa2V5IjoiSVJPTi1DVVJUQUlOLVBFUk1JVC1QT0MtUkVWSUVXIn0sInNvdXJjZV9wcm92ZW5hbmNlIjoidmVydGljYWw6YXV0aG9yaXRhdGl2ZS1yZXRyaWV2YWwiLCJzb3VyY2Vfc3RhdHVzIjoiV09SS0lORyIsInNvdXJjZV92ZXJzaW9uIjoiMDFhMTFiNDctYTZiOC03MDAwLTgwMDAtMDAwMDAwMDAwMDAxIiwic3Rvcnlfa2V5IjoiSVJPTi1DVVJUQUlOLVBFUk1JVC1QT0MtQ0FOQVJZIiwidGhyZWFkX2lkIjoiMDFhMTFiNDctYTZiNi03MWYxLTkzNDgtMGQxZTllZDIxYzVkIn0"}
```

### Signed proof preimage

SHA-256: `b5d7a7ce9bcca548026d4e21a764af39697e9664bcb5933f0f8c4ef96dafe628`

```json
{"action":{"capability":"request:work"},"actor":{"authenticated_principal":"bruce","credential_id":"cred-a"},"audience":{"api":"townsquare-canary-ledger-api","endpoint":"/v1/action-permits","service_id":"townsquare-ledger-v0"},"authority":{"evidence_manifest_file_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","evidence_manifest_id":"ledger-context-1","kind":"VERTICAL_STORY","source_snapshot_ref":"urn:ynm:vertical-story-snapshot:v1:sha256:686e50e1247ae9040ebafa070bf8bd02d32db35a6fe350de6027e7e3180e4dda","source_snapshot_sha256":"686e50e1247ae9040ebafa070bf8bd02d32db35a6fe350de6027e7e3180e4dda","source_version":"01a11b47-a6b8-7000-8000-000000000001"},"authority_class":"CANARY_TEST","canary":{"compose_project":"townsquare-canary-20261007-a","label":"TS-CANARY-NAS1-20261007-A","r7_context_sha256":"2222222222222222222222222222222222222222222222222222222222222222","r7_input_manifest_sha256":"1111111111111111111111111111111111111111111111111111111111111111","r7_release_id":"TS-R7-3333333333333333333333333333333333333333333333333333333333333333","source_commit":"4444444444444444444444444444444444444444","source_tree":"5555555555555555555555555555555555555555"},"decision_record_sha256":"c497e77257a14add339c7ae2852edad893ad8b2a9211e841e62ed1c7f151ea7b","expires_at":"2026-10-08T18:05:00Z","governance":{"bundle_id":"bundle-1","bundle_sha256":"6666666666666666666666666666666666666666666666666666666666666666","charter_version":"1.0","manifest_id":"governance-manifest-1","manifest_sha256":"7777777777777777777777777777777777777777777777777777777777777777","required_items_sha256":"8888888888888888888888888888888888888888888888888888888888888888"},"issued_at":"2026-10-08T18:00:00Z","issuer":{"issuer_id":"townsquare-canary-test:issuer-1","key_id":"townsquare-canary-test:key-1"},"mutation":{"idempotency_key_sha256":"9999999999999999999999999999999999999999999999999999999999999999","operation":"post"},"nonce":"nonce-0123456789abcdefghij","payload":{"canonical_payload_sha256":"0000000000000000000000000000000000000000000000000000000000000000","canonicalization_profile":"townsquare-json-v1"},"schema":"townsquare-action-permit-canary-proof-v1","target":{"expected_revision":"new","thread_id":"thread-1"}}
```

### Persisted permit binding

SHA-256: `fac1af904cbfac01f9e712c08a7d32079a6980e43b30d3408d0507f634ae1c63`

```json
{"action":{"capability":"request:work"},"actor":{"authenticated_principal":"bruce","credential_id":"cred-a","registered_identity_fixture_ref":"fixture:bruce","registered_identity_fixture_sha256":"ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"},"audience":{"api":"townsquare-canary-ledger-api","endpoint":"/v1/events","service_id":"townsquare-ledger-v0"},"authority_basis":{"authority_manifest_file_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","authority_manifest_id":"ledger-context-1","kind":"VERTICAL_STORY","verified_canary_proof":{"canonical_preimage_sha256":"b5d7a7ce9bcca548026d4e21a764af39697e9664bcb5933f0f8c4ef96dafe628","key_id":"townsquare-canary-test:key-1","nonce_sha256":"02e19d2f400d967829745331e4e6eb86448c441ad1181634dcb833a52c2914e0","profile":"townsquare-action-permit-canary-proof-v1","schema":"townsquare-action-permit-canary-proof-v1","signature_evidence_ref":"signature:permit-proof-1","signature_evidence_sha256":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"},"vertical_story":{"head_content_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","head_event_id":"01a11b47-a6b8-7000-8000-000000000001","helio_checkpoint":{"content_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","disposition":"PROCEED","event_id":"helio-checkpoint-1","gate":"CANARY_HANDOFF","scope_story_key":"IRON-CURTAIN-PERMIT-POC-CANARY"},"opening_content_sha256":"9a1cbf7ddff351494331f9da521863fa37d232093c7fe1043bd73541b3645f87","opening_event_id":"01a11b47-a6b7-7372-b52f-2d2002ed2081","retrieved_at":"2026-10-08T18:00:00Z","review_gate":{"content_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","disposition":"ACCEPTED","event_id":"review-accepted-1","relationship":"DEPENDS_ON","story_key":"IRON-CURTAIN-PERMIT-POC-REVIEW"},"source_snapshot_ref":"urn:ynm:vertical-story-snapshot:v1:sha256:686e50e1247ae9040ebafa070bf8bd02d32db35a6fe350de6027e7e3180e4dda","source_snapshot_sha256":"686e50e1247ae9040ebafa070bf8bd02d32db35a6fe350de6027e7e3180e4dda","source_status":"WORKING","source_version":"01a11b47-a6b8-7000-8000-000000000001","story_key":"IRON-CURTAIN-PERMIT-POC-CANARY","thread_id":"01a11b47-a6b6-71f1-9348-0d1e9ed21c5d"}},"bearer_hmac_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","decision_record":{"canonical_sha256":"c497e77257a14add339c7ae2852edad893ad8b2a9211e841e62ed1c7f151ea7b","record":{"applicable_rules":["rule:exact-action-permit"],"assumptions":[{"label":"verified","statement":"Trusted fixture predicates passed"}],"evidence_references":["urn:evidence:fixture"],"expected_outcome":"One governed event commits","objective":"Append one exact CANARY event","selected_action":"request:work"}},"governance":{"bundle_id":"bundle-1","bundle_sha256":"6666666666666666666666666666666666666666666666666666666666666666","charter_version":"1.0","manifest_id":"governance-manifest-1","manifest_sha256":"7777777777777777777777777777777777777777777777777777777777777777","required_items_sha256":"8888888888888888888888888888888888888888888888888888888888888888"},"lifetime":{"expires_at":"2026-10-08T18:02:00Z","issued_at":"2026-10-08T18:00:00Z","key_id":"receipt-key-1","max_uses":1,"single_use":true,"state":"ISSUED","ttl_seconds":120},"mutation":{"idempotency_key_sha256":"9999999999999999999999999999999999999999999999999999999999999999","operation":"post"},"payload":{"canonical_payload_sha256":"0000000000000000000000000000000000000000000000000000000000000000","canonicalization_profile":"townsquare-json-v1"},"permit_id":"permit-1","schema":"townsquare-action-permit-poc-v1","target":{"expected_revision":"new","thread_id":"thread-1"}}
```

## References

- `C:\Workspace\iron-curtain\docs\IP-MAN-MVP-WORK-ORDER.md` at Iron Curtain commit `8bdcd6c72ae73e9747ceafabb30b5fdfd0a10fe9`
- `C:\Workspace\iron-curtain\docs\IRON-CURTAIN-DESIGN.md`
- `C:\Workspace\iron-curtain\docs\SHURI-DISCOVERY-BASELINE.md`
- `C:\Workspace\iron-curtain\docs\MISSION-AND-SCOPE.md`
- `C:\Workspace\iron-curtain\docs\IP-MAN-MVP-WORK-ORDER-ISSUANCE-AMENDMENT.md` at Iron Curtain commit `34b788b146a2802534b1316bdd401913862d0cb6`, SHA-256 `e8db4b47eb3c4df0852b5db21ec04e2988b295c9c3e5559a06842a07e0f0f6b0`
- Amendment Drive evidence: `https://drive.google.com/file/d/1JeLrwfv8EYkZOCw8ncmOBC2Qq60sWXJO/view?usp=drivesdk`
- TownSquare `registrar/app/native_ledger.py`, `registrar/app/main.py`, and migrations 010, 011, and 014 at commit `9772e0656a75389e98564aab6f7a0d25fe47fa65`
