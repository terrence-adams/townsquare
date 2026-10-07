# Eddie Brock review — TownSquare Charter v1.0 release identity

**review_id:** `TS-REVIEW-20261007-EDDIE-CHARTER-10-03`  
**reviewer:** Eddie Brock / OpenAI Codex seat on Venom  
**subject:** uncommitted Charter v1.0 release-candidate directory produced after operator decision `TS-OPERATOR-SCOPE-20261007-CHARTER-V1`  
**manifest SHA-256:** `9F6E9D5B99DC19628A8E7291AB3D4296F68614041B57966503A7849DF5559796`  
**decision packet SHA-256:** `8B9FF9CE15350E7F6E3EAF7A576201E173DDAFA6C2D89AC1FC2ABAAA28FD0BE5`  
**decision:** RETURN FOR RELEASE-IDENTITY CORRECTION

## Passed

- All seven required Charter components are present.
- Manifest component hashes match the current files.
- Doctrine, Rules of Engagement, Object Dictionary, Receipt Profile, Authority Resolver, and Protected Control differ from their accepted source only in identity/status/connective package wording.
- Lifecycle contains the complete accepted transition table and independent-closure predicate/case table, including protected-control cancellation and the exact protected-operator Decision boundary.
- The package remains non-effective and keeps runtime enforcement, deployment, archive action, and recovery closure outside adoption.

## Required corrections

1. The identities proposed for adoption contain `RC` and a date, for example `TS-CHARTER-1.0-RC-20261007`. If those exact bytes are adopted, the first official Charter would retain a release-candidate identity. Use stable final identities:
   - `TS-CHARTER-1.0`
   - `TS-CHARTER-1.0-DOCTRINE`
   - `TS-CHARTER-1.0-ROE`
   - `TS-CHARTER-1.0-OBJECT-DICTIONARY`
   - `TS-CHARTER-1.0-LIFECYCLE`
   - `TS-CHARTER-1.0-RECEIPT`
   - `TS-CHARTER-1.0-AUTHORITY-RESOLVER`
   - `TS-CHARTER-1.0-PROTECTED-CONTROL`
2. Governing component bodies still name superseded draft versions:
   - Lifecycle says it is a merge of `v1.1` and `v1.2`.
   - Authority Resolver says it imports no semantics from `v0.1` or `v0.2`.

Replace those two provenance statements with self-contained wording that carries the same rule meaning without importing earlier version identifiers. Preserve historical candidate/version provenance in the review record, outside the official Charter.

After the identity-only correction, recompute every component hash, manifest hash, and adoption-decision hash, then perform one exact semantic-delta review before presenting the release decision.

