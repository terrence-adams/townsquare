# Session Registry Ed25519 ownership API

This API is additive to the existing operator-authorized Registry path. A
runtime creates and protects its own Ed25519 private key. The Registry receives
and persists only the raw 32-byte public key in canonical unpadded base64url,
its SHA-256-derived key ID, and its epoch. A private seed is never accepted,
persisted, logged, journaled, or returned.

All JSON request bodies are closed: unknown fields are rejected. Responses and
ordinary history omit provider locators and all credential verifiers. The
provider-locator view remains available only through the existing operator
authorization path and returns `Cache-Control: no-store`.

## Enrollment

`POST /v1/session-enrollments` is restricted to loopback plus the existing
`X-Registry-Operator-Token`. Its body is exactly:

```json
{"agent_id":"nimrod","provider":"codex","seat_or_host":"sentinel1"}
```

The Registry creates a random 256-bit enrollment token encoded as exactly 43
canonical unpadded base64url characters, stores only its SHA-256 verifier,
binds it to the three request fields, and expires it after
ten minutes. The clear enrollment token is returned once in a no-store response
for protected operator transfer. It is not written to idempotency, journal, or
outbox data.

## Registration

`POST /v1/sessions` uses exactly one
`Authorization: SessionEnrollment <43-character token>` header and a canonical
lowercase UUIDv4 `Idempotency-Key`. The body contains the existing registration
fields plus an exact `session_key` object:

```json
{"alg":"Ed25519","key_id":"ed25519:<sha256 raw public key>","key_epoch":1,"public_key_b64url":"<43 characters>"}
```

Malformed authorization and noncanonical tokens fail uniformly before hashing
or database access. Registration replays bind the grant ID, token verifier,
idempotency UUID, and canonical request digest. They are retained for at least
90 days after consumption and, for terminal sessions, at least 30 days after
termination. Expired unused grants become cleanup-eligible after 24 hours.

One `BEGIN IMMEDIATE` transaction validates the active agent and exact
agent/provider/seat binding, consumes the unexpired grant, creates the session,
appends the safe lifecycle journal and audit outbox records, and stores the
redacted replay response. An exact retry after a lost response returns that
response, including after grant consumption. A changed verifier, changed body,
or different idempotency key returns `SESSION_REGISTRATION_CONFLICT` without a
write. An unused expired grant returns `SESSION_ENROLLMENT_EXPIRED` without a
write.

## Owning lifecycle, reads, and rotation

Owning calls send `Authorization: SessionSignature <86-character signature>`
plus exact key ID, key epoch, expected revision, UTC timestamp, and lowercase
UUIDv4 nonce headers. Mutations also require `Idempotency-Key`; signed GET does
not permit one. The Ed25519 signature covers these NUL-delimited fields with no
trailing NUL:

```text
townsquare.session-owning-request.v1
<UPPERCASE_METHOD>
<CANONICAL_PATH>
<LOWERCASE_SESSION_UUID>
<IDEMPOTENCY_KEY_OR_EMPTY>
<SHA256_JCS_BODY>
ed25519-v1
<KEY_ID>
<KEY_EPOCH>
<EXPECTED_REVISION>
<UTC_TIMESTAMP>
<NONCE>
```

JSON bodies are closed, strict UTF-8/NFC, integer-only where numeric, and hashed
as compact sorted-key canonical JSON; a GET body is JSON `null`. First use must
be within plus or minus 120 seconds. The durable nonce ledger is committed in
the same transaction as each mutation. Exact mutation replay returns the stored
response even after the timestamp window; changed nonce reuse fails. It covers:

- `POST /v1/sessions/{session_uuid}/heartbeat`
- `POST /v1/sessions/{session_uuid}/terminate`
- `POST /v1/sessions/{session_uuid}/credential-rotations`
- `GET /v1/sessions/{session_uuid}`
- `GET /v1/sessions/{session_uuid}/history`

Rotation is signed by the current key and has body
`{"new_key":{"alg":"Ed25519","key_id":"...","key_epoch":<current+1>,"public_key_b64url":"..."}}`.
The new key becomes authoritative on commit. The prior key can authenticate
only the exact stored rotation replay; changed reuse returns
`SESSION_ROTATION_CONFLICT` without a write.

## Lookup-only access

`GET /v1/sessions/{session_uuid}` accepts a lookup-only Bearer credential. The
Registry configuration supplies only its lowercase SHA-256 verifier through
`REGISTRY_LOOKUP_TOKEN_SHA256_FILE`; the broker retains the clear credential.
This scope may use redacted session GET routes and cannot register, heartbeat,
terminate, rotate credentials, or retrieve `/provider-locator`.

An owning signature may read only its own redacted session and history.
Enrollment credentials cannot read sessions. The existing Registry API Bearer
and canary-proof behavior remains available for current administrative clients.

## Release identity and migration

The peer-facing Registry protocol schema remains version 2, matching the Ledger
compatibility contract. Database migration version 6 is reported separately as
`database_schema_version`. Registry internal readiness performs the live,
directional, same-R7-identity Ledger exchange; deployments must roll Registry
and Ledger from the same generated release context.

`registry-migrate` upgrades v1 through v5 databases atomically to v6 under its
exclusive migration lock. Rollback is restore-from-copy only: preserve the
pre-migration database copy, stop the candidate, and restore that copy with the
matching previous release. Existing sessions are atomically marked `LOST`,
receive `credential_scheme_retired` lifecycle/audit events, and must re-enroll
under a new session UUID. Runtime code never performs DDL.
