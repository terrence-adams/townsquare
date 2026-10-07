# Eddie Brock — TownSquare Charter v1.0 frozen-byte review

**reviewer:** Eddie Brock / OpenAI Codex on Venom  
**review date:** 2026-10-07 America/Chicago  
**subject commit:** `a574129cbc999e9ba34df2c44af47bde2d2181ed`  
**subject tree:** `7a31df13f6e59e694549212102108fa1f6c38a62`  
**scope:** exact frozen Charter package under `docs/governance/townsquare-charter-v1.0/`  
**decision:** **RETURN FOR FINAL RELEASE-IDENTITY AND ADOPTION-ANCHOR CORRECTION**

## Operator direction applied

The earlier documents were never official. Their version identifiers are historical provenance only. The first official release is one all-or-nothing `TownSquare Charter v1.0` containing the Doctrine, Rules of Engagement, Object Dictionary, Object and Lifecycle Governance, Governance Evidence / Receipt Profile, Authority Resolver, and Protected Operator Control. No prior candidate gains authority, and this review does not adopt, implement, deploy, activate, archive, or close recovery.

## Exact package reviewed

| Artifact | Git blob | Raw SHA-256 |
|---|---|---|
| Manifest | `7f71a66c462900be5b753db55546340d87700820` | `9780A7D94A8D97A8195B1CA41CA94F7880437D590443B34EF2AD5951E79E5720` |
| Operator decision packet | `38e1d8f1b23ffe30056a19cf9cc4115a61cf60c0` | `3B5CB74181DBB1357AD7F4AD09E39F2F76B75C9EF6072337451F2DA102D85F6E` |
| Doctrine | `699255558976776e7be050193d7d2c5bd0955ce2` | `D08E824FEFEE9821D55599E3F278D94324D03A1A47C4DAEB438B657094FC7999` |
| Rules of Engagement | `8dee0ba2aab1240b6056b1a70d242fc2e61f56e3` | `8A11FAA4317C249788BED3FDF88CAAA7DDDA59B1B58A4BCD3043BD8BD1C792D4` |
| Object Dictionary | `62b4e1799a89b04e0d621184303ec50c8468d689` | `B44B3DB5FB882E2FF4808E0D83FC1FB5EE3F4218B5B503EB56CA809B50721E86` |
| Lifecycle | `1ed8fa36864f2ce78b3e2058118fbc34f7538e65` | `97836B2ABD3A9C31ACAA5E11C727447D66BB2DF9FE8CB69E19F3DACBB5448BF4` |
| Receipt Profile | `923da6bab7f51b8871d041a874358ad8c8dc068e` | `D083FCEFCCA4BF6CA72EED91AA27CEADE3DD6F52CDC71D857243898B89121AF9` |
| Authority Resolver | `b7ed72e01ab24e8ed07cc49e0448fc38074b8162` | `64DEC45A8C24D2F1AE21243725FE05BC9427107BE35B9562465059C5589DBCC9` |
| Protected Operator Control | `8f57bcb69fb7182259822626469cc2577a5d2547` | `E2F3ACA9872A7A5CF6325C5F5A8DF65960CF2833CE6AB4122E0261AA73468004` |

The seven component hashes recomputed from the committed blobs match the manifest exactly.

## Passed semantic checks

1. The package uses the stable release identity `TS-CHARTER-1.0` and these seven stable component identities:
   - `TS-CHARTER-1.0-DOCTRINE`
   - `TS-CHARTER-1.0-ROE`
   - `TS-CHARTER-1.0-OBJECT-DICTIONARY`
   - `TS-CHARTER-1.0-LIFECYCLE`
   - `TS-CHARTER-1.0-RECEIPT`
   - `TS-CHARTER-1.0-AUTHORITY-RESOLVER`
   - `TS-CHARTER-1.0-PROTECTED-CONTROL`
2. The governing bodies do not import earlier document versions as authority. Earlier candidate material remains provenance.
3. The normative semantics of the reviewed sources are preserved. The connective edits bind the components to the Charter without adding implementation authority.
4. The Lifecycle preserves the complete object table, transition/evidence/prohibited-outcome table, protected-control cancellation route, independent closure predicate, and closure case table. Its Decision boundary is exactly: `only protected operator Decision may adopt, control, or accept where required`.
5. The package is all-or-nothing. The decision packet separates Charter adoption from archival, runtime/release implementation, deployment, activation, governed writes, and restore closure.
6. The 5:1 captured-real/hypothetical weighting remains evaluation methodology rather than a governance rule or adoption score.

## Release blockers

### 1. The exact bytes would remain self-labelled non-effective after adoption

Every component title and filename says `release candidate` or `rc`, and every component contains `RELEASE CANDIDATE — NOT ADOPTED — NOT EFFECTIVE`. The Doctrine also says `This release candidate has no effect...`. Because adoption is defined over these exact bytes, a successful adoption would create an official Charter whose own frozen metadata still says it is a release candidate and not effective. That produces avoidable ambiguity for the Authority Resolver and for agents deciding whether the Charter governs.

**Required correction:** create final official v1.0 artifact names and titles without `rc`, `candidate`, or dated candidate identity. Replace the frozen authority-status assertions with wording that remains true before and after adoption, for example: the bytes are the final Charter v1.0 release and their authority/effective state is determined only by the separately attributable operator adoption record. Recompute every affected hash.

### 2. The decision does not cryptographically anchor the manifest it asks the operator to use

The decision says to adopt the seven hashes “in `CHARTER-MANIFEST-v1.0-rc-20261007.md`” but does not state the manifest raw SHA-256. A filename is a mutable locator. The Charter's own recognition rule requires exact-byte identity for governing artifacts; the package index cannot be an unpinned indirection in the adoption decision.

**Required correction:** the adoption decision must name `TS-CHARTER-1.0`, the exact final manifest SHA-256, all seven component IDs and hashes (inline or through that pinned manifest), the scope, and the effective time. The immutable adoption record should also retain the adopted commit/tree or equivalent durable locator.

### 3. Two rule-ID prefixes still look like superseded candidate version identifiers

The Doctrine uses `TS2-*` and the Rules of Engagement use `ROE3-*`. These prefixes originated in the former 2.0 and 0.3 candidate lineages. No earlier version was official, and the operator directed that prior version identifiers be superseded for the clean official 1.0 release. Keeping `TS2` and `ROE3` creates a misleading lineage inside the new v1.0 even though the document identities are correct.

**Required correction:** either issue clean non-versioned Charter rule IDs (recommended, such as `TSC-*` and `TSC-ROE-*`) with a provenance-only mapping from old candidate labels, or add an explicit operator-approved declaration that these prefixes are semantic identifiers rather than version identifiers. Do not silently leave the ambiguity in the official release.

## Acceptance check after correction

Re-review one new frozen commit. It passes this gate only if: final names/titles and authority-status text remain logically true after adoption; the manifest and all seven component hashes recompute exactly; the adoption decision pins the manifest and component set; superseded candidate version identifiers do not remain in the official identities; the passed semantics above remain unchanged; and no adoption, archive, deployment, governed-write, or restore claim is inferred.

