# GSP V1/V2 review reconciliation — V3 candidate work

**status:** DRAFT RECONCILIATION — NOT ADOPTED — NOT EFFECTIVE

| Finding | Disposition | V3 correction |
|---|---|---|
| GSP-C6-01 | ACCEPTED | lifecycle v1.2 requires independently resolved, non-revoked scoped authorization/role/delegation for actor, represented authority, action, object revision, and acceptance decision; invalid, mismatch, or `UNKNOWN` denies only the effect, preserves append, and audits. |
| GSP-C6-02 | ACCEPTED | receipt profile v1.2 defines evaluation/retrieval time, action/object revision, binding identity/digest, exact dependencies, expiry/revocation, freshness/nonce/correlation, and final disposition; receipt presence never authorizes. |
| GSP-C6-03 | ACCEPTED | resolver v0.3 is self-contained and expressly does not import unpinned v0.1 semantics. |
| GSP-C6-04 | ACCEPTED | V3 plan pins V2 evidence commit/tree/component blobs and limits their precedence to evidence-gap assessment. |
| GSP-C6-05 | ACCEPTED | protected-control contract v0.1 defines abstract trust-anchor/role assignment, action/scope binding, anti-replay, audit integrity, fail-closed rejection, and tests. |

V1/V2, the original Eddie receipt, and candidate-6 prose remain unchanged. AC-D4, AC-D8, and AC-D10 remain BLOCKED; AC-D7 remains PARTIAL.
