# Eddie Brock review — Lifecycle v1.3 consolidation

**review_id:** `TS-REVIEW-20261007-EDDIE-LIFECYCLE-13-01`  
**reviewer:** Eddie Brock / OpenAI Codex seat on Venom  
**subject commit:** `f318b722469749b5a5ec3b4037e35537eb8e3a13`  
**subject artifact:** `TS-OBJECT-LIFECYCLE-1.3-CANDIDATE-20261007`  
**subject SHA-256:** `EB92B50B0A968A907EA5FC42B0A9748BFD1C22048D3365165C1366E515383379`  
**decision:** RETURN FOR REVISION — DO NOT ADOPT THESE BYTES

## Finding

The v1.3 artifact claims to consolidate v1.1 object/lifecycle semantics and v1.2 independent closure authorization, but it is an editorial compression rather than a demonstrably semantics-preserving merge.

The load-bearing loss is cancellation authority:

- v1.1 permits `OPEN/WORKING/BLOCKED/RESOLVED → CANCELLED` when authority is declared by an adopted profile **or protected operator control**.
- v1.3 says only that cancellation requires adopted-profile authority and reason.

The consolidated text therefore omits the protected-operator-control cancellation path that its source artifact explicitly preserves.

V1.3 also removes:

- v1.1’s per-transition actor/authority, minimum-evidence, and prohibited-outcome table; and
- v1.2’s explicit `EFFECTIVE` / `NOT_EFFECTIVE` / `UNKNOWN` result semantics and case table.

Those omissions may be restated elsewhere, but a document described as a consolidation must show that it carries its source semantics. Adoption should not require reconstructing omitted lifecycle rules from other artifacts.

## Required correction

Create a new immutable v1.3 candidate that:

1. preserves the complete v1.1 object table and Request lifecycle table;
2. preserves the complete v1.2 independent-closure predicate and case table;
3. changes only the header, document identity, successor metadata, and minimal connective text required to form one artifact; and
4. receives a new raw hash, adoption-packet update, exact-delta review, and final checkpoint.

This finding reopens only the consolidated lifecycle candidate and the adoption packet that names it. It does not reopen the previously reviewed Doctrine candidate 6, Rules of Engagement v0.3, Object Dictionary v1.3, Receipt v1.2, Resolver v0.3, Protected Control v0.1, or V6 scope decision.

