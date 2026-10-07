# Governance Evidence and Policy Receipt Profile v1.2 — candidate

**document_id:** `TS-GOV-EVIDENCE-RECEIPT-1.2-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT EFFECTIVE

A receipt is audit evidence, not authorization. Authorization is independently resolved at effect commit.

Required fields: `receipt_id`, correlation ID, nonce/single-use marker, issued/evaluated/retrieved/expiry times; authenticated actor and represented authority; action, exact object identity/revision and expected revision; exact governing and binding dependency identities, versions, and digests; binding identity/digest/capability scope; criteria/evidence identities; adoption/role/delegation resolution, expiry/revocation/freshness outcomes; rule/predicate results; final `ALLOW`, `DENY`, `PARK`, or `UNKNOWN` result and reason codes; immutable audit reference.

The binding revalidates object revision, dependency currency, nonce/single-use, authority, and revocation at commit. A stale, reused, missing, unverifiable, or mismatched receipt denies/parks the effect and audits it. A valid receipt does not itself authorize an action, impersonate the operator, prove comprehension, or override current resolution.
