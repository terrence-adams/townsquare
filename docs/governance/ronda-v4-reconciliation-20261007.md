# Ronda V1/V2 QA reconciliation — V4 candidate work

**status:** DRAFT RECONCILIATION — NOT ADOPTED — NOT EFFECTIVE

| Finding | Disposition | Exact closure / remaining condition |
|---|---|---|
| GQ-01 | ACCEPTED | Receipt v1.2 contains scope through exact governing/binding dependency identities, versions and digests; retrieval/evaluation/expiry time; retrieval/policy result; action/object/current and expected revision; binding identity/digest/capability; expiry/revocation/freshness; nonce/correlation; and final `ALLOW`/`DENY`/`PARK`/`UNKNOWN`. Negative cases are stale/reused/missing/unverifiable/mismatched receipt and receipt-as-authorization. Ordering is: retrieve and evaluate, issue receipt, re-resolve/revalidate at effect commit, then record final result. |
| GQ-02 | ACCEPTED, PARTIAL | V4 manifest pins original candidate commentary blob `8224c59f434b153407111e55866cd85146fef68a`, SHA `C52E1BB88262C838C193CD3EADA0F3326582CA3BACA624A0113864A3F903ABE7`, as historical rule-key traceability input. Candidate-6 has no new commentary; it is explicitly unresolved whether a candidate-6-specific commentary is required before adoption review. |
| GQ-03 | ACCEPTED | Object Dictionary v1.3 supplies attributes, citation/linkage and authority semantics for all ten objects, including fuller Decision semantics. |
| GQ-04 | ACCEPTED | V4 manifest pins the V3 package commit, tree/component blobs where available, and immutable-local recovery bundle identity. Precedence is limited to review evidence/evidence-gap assessment. |

No reconciliation makes a candidate effective. AC-D4/D8/D10 remain BLOCKED; AC-D7 remains PARTIAL.
