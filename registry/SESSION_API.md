# Session Registry scoped credential API

This API is additive to the existing operator-authorized Registry path. The
Registry database stores SHA-256 verifiers only. A runtime creates and protects
its own session credential, then sends only the 64-character lowercase verifier
in the registration or rotation JSON. No endpoint accepts a clear session
credential in JSON or returns one.

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

The Registry creates a random 256-bit-or-stronger enrollment token, stores only
its SHA-256 verifier, binds it to the three request fields, and expires it after
ten minutes. The clear enrollment token is returned once in a no-store response
for protected operator transfer. It is not written to idempotency, journal, or
outbox data.

## Registration

`POST /v1/sessions` uses `Authorization: Enrollment <enrollment credential>` and
an `Idempotency-Key`. The body contains the existing registration fields plus
`session_credential_sha256`; the clear runtime credential is absent. The
enrollment identity is inferred from authorization, not from a caller-supplied
principal header.

One `BEGIN IMMEDIATE` transaction validates the active agent and exact
agent/provider/seat binding, consumes the unexpired grant, creates the session,
appends the safe lifecycle journal and audit outbox records, and stores the
redacted replay response. An exact retry after a lost response returns that
response, including after grant consumption. A changed verifier, changed body,
or different idempotency key returns `SESSION_REGISTRATION_CONFLICT` without a
write. An unused expired grant returns `SESSION_ENROLLMENT_EXPIRED` without a
write.

## Owning lifecycle and rotation

The clear session credential never leaves the runtime, including in an HTTP
header. The runtime derives its lowercase SHA-256 verifier and sends
`Authorization: SessionProof <proof>`, where `proof` is lowercase
HMAC-SHA-256 keyed by the 32 verifier bytes over:

```text
registry-session-proof-v1\n<METHOD>\n<PATH>\n<IDEMPOTENCY_KEY_OR_EMPTY>\n<SHA256_CANONICAL_JSON_BODY>
```

Canonical JSON uses sorted keys and compact separators; a GET body is JSON
`null`. The proof therefore binds the method, exact path, idempotency identity,
and request body without transmitting either the clear credential or verifier.
This proof authorizes:

- `POST /v1/sessions/{session_uuid}/heartbeat`
- `POST /v1/sessions/{session_uuid}/terminate`
- `POST /v1/sessions/{session_uuid}/credential-rotations`

The server recomputes the proof from its stored verifier and never receives,
persists, or returns the clear credential. Session proofs are UUID-bound and
cannot read or mutate another session.

Rotation uses the request `Idempotency-Key` as the durable rotation ID. The body
is exactly `{"session_credential_sha256":"<replacement verifier>"}`. A single
transaction binds the session, rotation ID, old verifier, replacement verifier,
safe journal/outbox event, updated revision, and redacted replay response. After
commit, a proof derived from either the old or replacement credential can
authenticate only an exact retry of that rotation ID and replacement verifier. Changed reuse returns
`SESSION_ROTATION_CONFLICT` without a write.

## Lookup-only access

`GET /v1/sessions/{session_uuid}` accepts a lookup-only Bearer credential. The
Registry configuration supplies only its lowercase SHA-256 verifier through
`REGISTRY_LOOKUP_TOKEN_SHA256_FILE`; the broker retains the clear credential.
This scope may use redacted session GET routes and cannot register, heartbeat,
terminate, rotate credentials, or retrieve `/provider-locator`.

An owning Session proof may read only its own redacted session and history.
Enrollment credentials cannot read sessions. The existing Registry API Bearer
and canary-proof behavior remains available for current administrative clients.

## Release identity and migration

The peer-facing Registry protocol schema remains version 2, matching the Ledger
compatibility contract. Database migration version 5 is reported separately as
`database_schema_version`. Registry internal readiness performs the live,
directional, same-R7-identity Ledger exchange; deployments must roll Registry
and Ledger from the same generated release context.

`registry-migrate` upgrades v1 through v4 databases atomically to v5 under its
exclusive migration lock. Rollback is restore-from-copy only: preserve the
pre-migration database copy, stop the candidate, and restore that copy with the
matching previous release. Runtime code never performs DDL.
