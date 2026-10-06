# Adopted-Authority Resolution v0.1 — Candidate Specification

**document_id:** TS-ADOPTION-RESOLUTION-20261006-CANDIDATE

**version:** 0.1-candidate

**status:** CANDIDATE — NOT ADOPTED — NOT EFFECTIVE

**scope:** deciding whether one exact governance compliance manifest is genuinely adopted and effective for a proposed action

**non-effect:** this document adopts nothing, activates no manifest, arms no gate, and grants no authority

## Why this boundary exists

A manifest cannot make itself authoritative by saying `ADOPTED`, by being mounted, or by carrying a valid digest. Those facts prove only what the manifest says and which bytes were supplied. Adoption is a separate operator act. The resolver therefore establishes authority from an operator-controlled record outside the candidate manifest, then binds that authority to the manifest's exact identity, version, bytes, scope, and effective window.

## Roles

- **Operator:** the only role that may adopt, make effective, supersede, withdraw, stop, or override governance. Operator authority is never inferred from content or delegated to an agent.
- **Issuer:** prepares and publishes a manifest or adoption envelope at the operator's direction. Issuance proves publication, not adoption. The issuer may be the operator only when the protected authority evidence identifies the operator role explicitly.
- **Resolver:** read-only logic that verifies authority evidence and returns `EFFECTIVE`, `NOT_EFFECTIVE`, or `UNKNOWN`. It never creates authority or chooses between conflicting operator records.
- **Auditor:** reviews resolution evidence and implementation behavior. An auditor may report defects but cannot activate a manifest.

## Authoritative source categories

The resolver accepts exactly one of these categories, configured before the action and identified in audit evidence:

1. **Authoritative adoption register.** An append-only operator decision record obtained from the configured governance authority. The record is authenticated by the protected operator path and is retrieved by immutable event identity and authoritative sequence.
2. **Operator-signed adoption envelope.** A canonical adoption envelope whose signature verifies against a currently trusted operator verification key. The trust anchor and its revocation state are established outside the manifest. A signature proves control of that key; it counts as operator adoption only because the trust-anchor record explicitly assigns that key to the operator-adoption role.
3. **Protected operator attestation.** An append-only attestation created through the separately protected operator-control path and bound to the canonical adoption envelope. An agent-authored post quoting or paraphrasing the operator is not this category.

A deployment may support more than one category, but one successful resolution cites one exact authority record. If valid sources disagree, resolution is `UNKNOWN` and ordinary state-changing actions fail closed until the operator adjudicates the conflict.

## Required adoption envelope

The authoritative record or its referenced canonical envelope MUST contain:

| Field | Requirement |
|---|---|
| `adoption_event_id` | immutable unique identity of the operator decision |
| `authority_sequence` | monotonic position in the configured authority source |
| `operator_id` | protected operator identity; never client supplied |
| `issuer_id` | identity that published the manifest or envelope |
| `decision` | exactly `ADOPT`, `SUPERSEDE`, or `WITHDRAW` |
| `manifest_id` | exact manifest identity |
| `manifest_version` | exact version; mutable aliases are forbidden |
| `manifest_sha256` | SHA-256 of the exact canonical manifest bytes selected by the adoption decision |
| `scope` | action classes, targets, and other boundaries for which the decision applies |
| `adopted_at` | authoritative decision time for `ADOPT` |
| `effective_from` | first authoritative instant at which the manifest may govern |
| `effective_until` | exclusive end instant or `null`; it cannot be inferred from file presence |
| `supersedes_event_id` | prior adoption event when applicable |
| `reason` | operator's decision text or exact immutable reference to it |
| `authority_method` | accepted source category and, for a signature, algorithm and trusted key identity |
| `envelope_sha256` | SHA-256 of the canonical adoption envelope excluding signature bytes |
| `signature_or_attestation_ref` | verified signature plus key identity, or protected operator-attestation identity |

The resolver verifies the manifest byte digest itself. A digest copied from inside the manifest is not verification.

## Effective-state predicate

For action time `t`, manifest `m` is `EFFECTIVE` only when every clause is true:

1. `m` parses under the release-pinned manifest schema and has a unique identity and version.
2. The resolver obtains one accepted authority source and verifies its authenticity and current trust status.
3. A valid `ADOPT` record binds the operator, manifest identity, version, independently computed manifest digest, and requested action scope.
4. `effective_from <= t`, and `effective_until` is `null` or `t < effective_until`.
5. No later valid authority record, through the resolver's current authority watermark, withdraws that adoption or supersedes it for the requested scope at or before `t`.
6. No second manifest is simultaneously effective for the same exclusive scope unless the adoption record explicitly defines non-conflicting precedence.
7. The resolver's authority watermark, trust-anchor status, and clock satisfy the configured freshness bounds.
8. The exact adoption event, manifest digest, selected status history, scope match, and result are written to append-only audit evidence before the ordinary action commits.

Any false clause returns `NOT_EFFECTIVE`. Any clause that cannot be decided returns `UNKNOWN`. Both results park ordinary state-changing actions. Neither result may block the operator stop path.

## Supersession, withdrawal, and windows

- `ADOPT` may be recorded before `effective_from`; it remains adopted but not effective until that instant.
- `SUPERSEDE` names the prior adoption event and the successor manifest. The prior manifest ceases to be effective at the supersession's `effective_from`, limited to the superseded scope.
- `WITHDRAW` names the adoption event being withdrawn and an `effective_from`. It requires no successor.
- Records are append-only. Supersession and withdrawal never edit or erase the earlier adoption.
- A future-dated, expired, superseded, withdrawn, or out-of-scope manifest is not effective.
- Ambiguous overlap, missing sequence history, rollback to an older authority watermark, or an unresolvable status event returns `UNKNOWN`.

## Offline and bootstrap handling

Before the first manifest can become effective, the operator establishes a bootstrap record outside all candidate manifests. It pins the accepted source category, authority identity, manifest schema version, operator verification key or protected attestation path, revocation source, and initial authority watermark. Until that record exists and verifies, the system is read-only except for the operator stop path.

An offline resolver may use a previously exported authority checkpoint only when the checkpoint is canonical, authenticated by the pinned operator trust anchor, carries its authority watermark and creation/expiry times, contains all adoption/supersession/withdrawal events needed for the selected scope, and is within its configured freshness window. Loss of connectivity, an expired checkpoint, or inability to check revocation never converts a candidate into an adopted manifest. It returns `UNKNOWN`.

Trust-anchor rotation or revocation is itself a protected operator act. A manifest may reference a key, but it cannot add, replace, or restore its own trust anchor.

## Fail-closed conditions

Ordinary state-changing actions park with a machine-readable reason when any of these occurs:

- authority source absent, unavailable, stale, rolled back, or not configured;
- missing, malformed, duplicate, or unknown adoption identity/version;
- manifest byte digest or adoption-envelope digest mismatch;
- missing, invalid, expired, revoked, untrusted, or wrong-role signature/attestation;
- adoption record has not reached `effective_from`, has expired, is withdrawn, is superseded, or does not cover the action scope;
- later authority status cannot be determined through the current watermark;
- overlapping effective manifests have no operator-defined precedence;
- clock or freshness cannot be trusted;
- the manifest, client, agent, issuer, or mounted configuration supplies the asserted operator identity or authority result;
- resolver or audit persistence fails.

The response reports the failed predicate and current requirements without exposing credentials, signing secrets, or protected attestation material.

## What never counts as adoption

- `status: ADOPTED`, `effective: true`, `pinned: true`, or similar self-declared manifest fields;
- a mounted, bundled, configured, copied, or discoverable file by itself;
- an agent, issuer, service, auditor, test, or reviewer assertion that the operator approved it;
- a quotation attributed to the operator without a protected operator authority record;
- a valid content hash without an adoption record;
- a signature by a key not currently assigned to the operator-adoption role;
- a passing test, successful trial, release label, commit, tag, or deployment;
- an old adoption record when a later status event cannot be checked;
- silence, missing data, inability to connect, or absence of a withdrawal record in a stale snapshot.

## Audit evidence

Each resolution attempt records append-only:

- resolver version and policy/schema version;
- action class, target, scope, authenticated principal, and decision time;
- authority source category, source identity, authority watermark, and freshness result;
- manifest identity/version and independently computed SHA-256;
- adoption, supersession, and withdrawal event identities used;
- operator identity and issuer identity as resolved from authority;
- trust-anchor/key identity, signature or attestation verification result, and revocation watermark without secret material;
- effective-window and scope-match results;
- final `EFFECTIVE`, `NOT_EFFECTIVE`, or `UNKNOWN` disposition and reason code.

Audit evidence proves what the resolver checked. It does not prove comprehension, wisdom, or substantive correctness of the adopted rules.

## Minimum truth table

| Case | Result |
|---|---|
| Exact manifest digest, protected operator adoption, current trust, in-window, in-scope, complete status history | `EFFECTIVE` |
| Manifest says `ADOPTED`; no external operator record | `NOT_EFFECTIVE` |
| Manifest is mounted and hash-valid; adoption reference is absent | `NOT_EFFECTIVE` |
| Agent or issuer asserts operator approval | `NOT_EFFECTIVE`; audit spoofed authority claim |
| Valid adoption for a different digest, version, action, or scope | `NOT_EFFECTIVE` |
| Future `effective_from` or passed `effective_until` | `NOT_EFFECTIVE` |
| Later valid withdrawal or supersession covers the action | `NOT_EFFECTIVE` |
| Authority unavailable, watermark stale, revocation unknown, or effective manifests conflict | `UNKNOWN`; ordinary action parks |
| Candidate status and valid signature by an unassigned key | `NOT_EFFECTIVE` |
| Operator stop during any resolution result | stop succeeds and is audited |

## GOV-RB-03 close condition

`GOV-RB-03` is closed only when implementation independently computes the manifest digest, resolves the predicate above from a configured authoritative source, rejects self-declared or mounted-only authority, persists the full audit evidence, and passes this truth table under independent QA. Building this candidate specification does not close the finding. No current candidate is activated by this artifact.

## Source boundary and handoff

This candidate refines `GOV-RB-03` in `implementation-compatibility-finding-27c98ca.md`, the operator/adoption boundary in `rules-of-engagement-v0.1-candidate.md`, and the inactive authority boundary in `context-compliance-manifest-v0.1-candidate.json`. It does not amend the doctrine draft or infer adoption from it.

Software implementation belongs to the implementation owner. Security reviews authority spoofing, trust-anchor substitution, rollback, signature/attestation bypass, and offline replay. Independent QA owns the truth table. A reviewer other than the author reviews the built resolver before any blocking enforcement is armed. The operator alone decides adoption and activation.
