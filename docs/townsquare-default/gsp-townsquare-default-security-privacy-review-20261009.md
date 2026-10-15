# TownSquare Working Default — independent security and privacy review

**Review date:** 2026-10-09  
**Reviewer:** GSP (security)  
**Verdict:** **APPROVAL-READY for planning and operator decision only**  
**Implementation authority:** none granted by this review

## Scope, evidence, and threat model

Reviewed in full:

- `docs/townsquare-default/townsquare-working-default-architecture-and-draft-vertical.md` — SHA-256 verified as `2016DCC680DC90CE788894E6F24D38BE65FD94CF999FA77D6B35BF8BFAABDE2A`.
- Kano's full REWORK review and bounded PASS addendum.
- Canonical `docs/iron-curtain-single-use-permit-poc.md`.
- Canonical `docs/session-registry/session-registry-mvp-design-and-draft-work-items.md`.
- Adopted Charter record `docs/governance/townsquare-charter-v1.0-adoption-record-20261007.md` and its decision request.

Evidence statements below are labeled **verified** when read directly from the saved artifacts, **reported** when they originate in Cable's supplied preflight, and **unverified** where the package deliberately requires future independent evidence. No live service, NAS share, ledger, ACL, provider, or external session was contacted by this review.

Protected assets are NAS production integrity; exact operator evidence; provider locators; credentials, permit bearers, lease receipts, and HMAC material; immutable lifecycle/authority records; and the distinction between attribution and authorization. The relevant adversaries are an untrusted message body, an authenticated but over-privileged development identity, a compromised or stale agent/session, a confused deputy through lineage or `work_ref`, a replaying client, and an observer of logs, traces, backups, Git evidence, or public receipts.

## Decision summary

The package has a sound separation of responsibilities: TownSquare records communication/evidence, Registry holds identity and private locators, Vertical owns work lifecycle, Revere owns delivery state, and Iron Curtain owns exact-action authority. The separate authenticated, non-authorizing intake lane avoids the receipt/permit circularity, while the existing exact-action POC remains canonical for material operations.

The package does **not** authorize implementation, issue or consume a permit, append a ledger event, perform external contact, make a provider call, delete the probe, change a mount/ACL, deploy, restore, roll back, or declare a live system compliant. Its proposed Stories remain draft and S7 remains BLOCKED until the separately attributable operator Decision identifies a pre-existing safe receipt append operation.

## Question-by-question assessment

| Question | Result | Basis |
| --- | --- | --- |
| 1. Can unpermitted intake reach a material path? | **PASS, design-gated** | The distinct intake lane is explicitly unable to invoke `/v1/events`, issue/consume permits, mutate Registry/Vertical/Revere/release state, or contact providers. S1 requires exhaustive route coverage and a dependency-isolation test; unknown writing routes default-deny. |
| 2. Are public receipts and exact evidence separated? | **PASS, design-gated** | Safe receipt versus protected exact bytes/evidence are separate; low-entropy exact digests are protected; locators, bearers, lease receipts, arbitrary bodies, and HMAC material are prohibited from public events and observability. |
| 3. Does lineage attribute without delegating power? | **PASS, design-gated** | Actor/session/parent/delegator/subagent/lineage are Registry context only. Every effect must separately bind executing actor/session, current accountable work/addressee, and exact authority; derived permits are rejected. |
| 4. Do replay/staleness/reconciliation fail closed? | **PASS, design-gated** | Local owner transactions, immutable IDs, idempotency, inbox/outbox, Registry freshness revision, and zero-mutation failure paths are specified. Revere requires a fresh redacted Registry lookup for every send/receive/ack. |
| 5. Does S7 stop Sentinel identities from mutating NAS? | **PASS as a dispatch gate; not yet proven in reality** | S7 forbids NAS writes during verification, requires developer write removal, a gated production path, and non-production-only denial testing. It blocks every Sentinel implementation until independently accepted. |
| 6. Is incident bootstrap safe? | **PASS, intentionally blocked** | No safe existing append operation has been verified. The package correctly refuses temporary endpoints, NAS writes, file drops, and self-bootstrap; it returns the missing decision to the operator. |
| 7. Are canonical Iron Curtain/Revere boundaries preserved? | **PASS** | Canonical `/v1/events` exact-action POC is not generalized. Every live/external Revere operation is disabled pending accepted POC work plus a reviewed amendment; synthetic tests have no external contact. |
| 8. Are release/backup/rollback boundaries adequate for this MVP? | **PASS, acceptance-gated** | Non-template artifact binding, independent QA/leak scan, isolated restore proof, permit-bound promotion, and two exact rollback predicates are required. Secrets must not be exported in release artifacts. |

## Findings

### HIGH H-1 — Proven development-to-production NAS write path

**Evidence:** **reported** by Cable and recorded in the design: `batman` had read-write CIFS access and created `/mnt/nasonemic/Projects/Vertical/ledger/.cable-write-probe` during a purported read-only preflight. The coordinator separately verified the file metadata. The file must remain untouched pending a distinct operator authorization.

**Attack path:** any process acting as a development identity with that mount can create, alter, or delete a production ledger object outside Vertical's lifecycle controls. This defeats the claimed development/production boundary and can impair ledger integrity or conceal activity.

**Severity / likelihood:** **HIGH / proven**. This is an existing boundary failure, not a hypothetical defect.

**Required remediation sequence:**

1. Do not delete, rename, touch, or otherwise mutate the probe during review or bootstrap.
2. Obtain the separate attributable operator Decision naming an already-existing authenticated non-authorizing incident-receipt operation, destination, fixed payload digest, principal, and expected evidence.
3. Record the protected incident receipt through that named operation only.
4. Independently inspect only the existing probe, adjacent entries, and mount/ACL metadata without NAS mutation.
5. Remove development write authority; provide read-only access only where necessary and a separately authenticated, permit-gated production mutation identity/path.
6. Prove denial only against a named non-production synthetic target. A second production write probe fails S7.
7. Only then, under a separate exact one-file operator cleanup Decision, remove the named probe and record before/after receipts proving adjacent entries unchanged.

**Disposition:** This is already a hard S7 prerequisite. It is therefore not a defect that blocks approval of the planning package, but it blocks every Sentinel One implementation or dispatch until independently accepted.

### MEDIUM M-1 — “Safe summary” needs an explicit hostile-content rendering and redaction contract

**Evidence:** **verified**: the draft requires a faithful safe summary and forbids sensitive bodies/locators/tokens from public receipts and observability. It does not yet specify an executable rule for summaries derived from untrusted operator content before S4 presents them in an operator UI.

**Attack path:** an adversarial or malformed input can place active markup, terminal/control sequences, a bearer-shaped value, or a raw provider locator into a “summary.” If persisted or rendered without structured escaping/redaction, it can become stored UI injection, log/trace pollution, or a sensitive-data disclosure despite protected exact-evidence storage.

**Severity / likelihood:** **MEDIUM / plausible**. No implementation or rendered UI was reviewed; this is not evidence of an existing exploit.

**Required edit before S3/S4 implementation:** add to S3's acceptance criteria and S1's receipt-field policy: safe summaries are server-generated from a closed structured schema; raw operator text is never copied into a safe summary by default; all renderers use context-appropriate escaping; control characters are normalized/rejected; token/credential/provider-locator patterns are redacted before persistence to public receipt/log/trace surfaces; and tests cover markup, control characters, a generated sentinel locator, and a generated bearer sentinel. Protected exact evidence retains original bytes only under its access policy.

**Disposition:** nonblocking for planning/operator decision; required before implementation acceptance of S3/S4.

### LOW L-1 — Protected evidence retention and backup-access policy remains a later explicit implementation choice

**Evidence:** **verified**: protected evidence reads are authorized and receipted; S8 excludes secret export from release artifacts. The bounded package intentionally does not yet set retention/deletion/backup-reader policy.

**Risk:** an implementation could over-retain sensitive exact evidence or include it in a backup/access path broader than the protected evidence partition.

**Required checkable edit:** when S3/S8 are implemented, name the protected evidence retention class, backup encryption/location, and restore-reader authorization in the implementation acceptance evidence; assert no general release artifact or ordinary support backup contains protected evidence, provider locators, permit bearers, lease receipts, or HMAC material.

**Disposition:** parked as an implementation acceptance check, not a new production-hardening Story.

## Specific boundary confirmations

- The adopted Charter is effective governance only. **Verified:** its adoption record expressly withholds runtime/release implementation, deployment, activation, governed writes, and restore closure; nothing in this package treats adoption as authority.
- The canonical Iron Curtain POC stays exact-action and single use. **Verified:** its bearer is opaque, HMAC-compared, bound to exact request data, expires after 120 seconds, and has a transactional issue/consume path. The package correctly does not stretch it to Revere without a reviewed amendment.
- The non-authorizing route must authenticate and append-authorize even though it has no per-message permit. **Verified:** the draft states this; S1 must turn it into endpoint-level tests.
- Revere send, receive/lease, ACK, replay, and adapter delivery are correctly material before their respective commits. **Verified:** live/external operations are disabled until the independent amendment and exact authority exist; receipt, session authentication, `work_ref`, message body, or lineage cannot stand in.
- Registry locator protection is compatible with the canonical Session Registry design. **Verified:** raw provider IDs remain private, redacted APIs use UUIDs, and logs/traces/errors/evidence are prohibited from carrying locators or credentials.
- The status/owner discrepancy observed by Cable is handled correctly. **Verified:** it is treated as an untrusted/stale reader projection to reconcile, never as a reason to rewrite authoritative NAS history.

## Minimum acceptance evidence for future implementers

This review does not add scope. For the existing Stories, it expects the already-specified negative evidence: exhaustive endpoint map; zero-mutation tests for unpermitted/unknown routes; receipt idempotency/changed-replay tests; protected-evidence access audit; actor/session/lineage confused-deputy tests; fresh Registry revision failures; Revere pre-commit authorization failures; secret/locator/bearer/lease/payload leak scan; S7 non-production write-denial test; release backup/isolated restore; and rollback truth-table results.

## Final decision

**APPROVAL-READY for the trio's planning/operator-decision checkpoint.** Kano's seven prior blockers are closed in the saved draft. H-1 is a proven operational incident but is accurately isolated as a nondispatchable S7 gate with a safe, decision-bound remediation sequence. M-1 and L-1 are bounded, checkable acceptance additions; neither grants authority or permits implementation before the package's stated gates.

This verdict does not convert drafts into live Vertical items, satisfy S7, approve an incident receipt or probe deletion, authorize Iron Curtain implementation, enable Revere external contact, or authorize Sentinel/NAS configuration or deployment.

## Validation record

- Read-only file hash: architecture SHA-256 matches the coordinator-supplied value.
- Read-only review: full architecture, Kano review/addendum, canonical Iron Curtain and Session Registry designs, and Charter adoption record were read.
- Local write: this review artifact only.
- Git whitespace check: `git diff --check -- docs/townsquare-default/gsp-townsquare-default-security-privacy-review-20261009.md` completed with no output (PASS).
- External/state-changing actions: none.
- Elapsed time: unknown.
- Model actually used: GPT-5 Codex (exact deployment SKU not exposed to this review role).
