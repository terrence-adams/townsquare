# Adopted Authority Resolution v0.3 — candidate

**document_id:** `TS-ADOPTION-RESOLUTION-0.3-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT EFFECTIVE

This is self-contained; it imports no unpinned semantics from v0.1 or v0.2. For each ordinary consequential action, independently resolve each governing artifact and binding dependency by stable identity, version, raw-byte digest, action/object scope, effective window, revocation/supersession status, required acceptance, and freshness. A package cannot adopt a member.

`EFFECTIVE` requires authenticated non-revoked authority for the exact action, scope, target revision, and time, with complete current dependency status and durable audit record. `NOT_EFFECTIVE` applies to a false predicate; `UNKNOWN` applies to an undecidable predicate. Both deny/park the ordinary effect, preserve append-only correction/dispute/escalation/failure reporting, and audit the failed predicate. A manifest, receipt, digest, mount, test, review, or assertion never authorizes itself.

Conflicting authority, stale/rolled-back source state, trust-anchor uncertainty, digest mismatch, scope mismatch, missing dependency, replayed nonce, or unavailable audit persistence is not `EFFECTIVE`. Protected operator control is separately authenticated under the protected-control contract and cannot be invoked by an agent assertion.
