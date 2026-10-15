# Story 189 notification contract bundle design note

## Decision

Create a schema-only, version-1 JSON contract bundle under `contracts/r8`. Each wire contract is a closed JSON Schema (draft 2020-12), while one closed registry document records normative enums and protocol semantics that JSON Schema cannot fully express. A compatibility manifest identifies every member by relative path, contract identity/version, and SHA-256 digest; the manifest excludes itself to avoid a self-reference cycle.

The bundle models immutable routing evidence and pointer-only delivery. It does not define database migrations, service routes, runtime configuration, implementation status, or fixture outcomes.

## Justification

The approved Story 189 design requires exact versioned bytes for `target-ref/1`, `registry-routing/1`, `notice-pointer/1`, claim/deposit/ack/fail envelopes, state/event enums, capability/error/version registries, canonicalization, idempotency, leases, retries, receipts, server-bound subjects and revocation, anti-rollback evidence, failure/redrive authority, audit views, courier profiles, and rolling compatibility. Closed schemas reject caller-invented authority fields and keep subsequent Registry, Ledger, and courier lanes on one deterministic interface.

## Interfaces and files

- `target-ref.v1.schema.json`: typed source audience.
- `registry-routing.v1.schema.json`: authenticated snapshot origin, anti-rollback watermark, and frozen recipient routing evidence.
- `notice-pointer.v1.schema.json`: content-free delivery pointer.
- `delivery-claim.v1.schema.json`, `delivery-deposit.v1.schema.json`, `delivery-ack.v1.schema.json`, `delivery-fail.v1.schema.json`: closed caller-request and server-result forms. Caller request bytes contain delivery/claim/idempotency facts only and cannot carry principal, host, seat, capability, or revocation authority. Server-result/audit forms add the authenticated server-bound subject evidence and mismatch/revocation disposition.
- `delivery-redrive.v1.schema.json`: separately authorized, linked-generation redrive request/result.
- `delivery-view.v1.schema.json`: recipient and auditor projections with explicit field partitions.
- `protocol-registry.v1.json`: exact states, append-only events, capabilities, errors, versions, courier profiles, and normative protocol rules.
- `compatibility-manifest.v1.json`: rolling service compatibility and member hashes, excluding itself. Its member set is provisional until the fixture owner adds and hashes the required positive/negative corpus and any registry artifacts; Story 189 cannot be declared frozen or accepted before that final re-hash.

Shared schema definitions stay in the owning schema rather than a cross-file `$ref`, so every member can be parsed and validated in isolation. Identifiers use conservative printable token patterns; timestamps use RFC 3339 `date-time`; digests are lowercase SHA-256 hex. This bundle selects RFC 8785/JCS as the r8 canonicalization profile; it does not claim that profile was already implemented. Arrays whose order is not semantic are explicitly sorted before hashing.

## References

- `C:\Workspace\TOWNSQUARE-REGISTRY-AGENT-NOTIFICATION-MVP-DESIGN-20261008.md`, especially “Frozen contract prerequisite,” “Delivery semantics,” “Courier trust profiles,” and Story 189.
- Existing `contracts/r7/compatibility-matrix.json` for repository packaging precedent only; r7 is not modified.

## Workflow and checks

1. Peer-review this note before schema authoring.
2. Author only the listed r8 files.
3. Parse every JSON member and validate every JSON Schema with a draft-2020-12 validator when available.
4. Verify every schema closes objects with `additionalProperties: false` and every manifest digest matches the exact member bytes.
5. Report mapping to Story 189 DoD without declaring acceptance.

## Peer-review record

- Reviewed: 2026-10-09 by the coordinating Story 189 agent before schema authoring.
- Concern: caller request schemas must not accept principal, host, seat, capability, or revocation fields as authority; authenticated subject evidence belongs only in server-issued result or audit forms.
- Concern: the final compatibility manifest must hash the positive and negative fixture corpus and fixture registry, not only the initial schemas and protocol registry.
- Disposition: both concerns were incorporated into the interface definitions and provisional-manifest rule above before schema authoring proceeded.

## Parked / excluded

- Positive/negative fixtures and their acceptance results (fixture owner lane).
- Registry v3 and Ledger v15 migrations or ORM models (Stories 190–191).
- Courier/service/runtime implementation (Stories 190–193).
- Revere wake payloads, post-MVP timing equalization, production hardening, and broad rollout.
- Product policy for lifecycle recipients and any automatic courier-profile fallback.
