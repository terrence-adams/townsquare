# Eddie Brock — TownSquare Charter v1.0 final release acceptance review

**reviewer:** Eddie Brock / OpenAI Codex on Venom  
**review date:** 2026-10-07 America/Chicago  
**release commit:** `14a91f41da3f63a14e427e573f3fe4e0a40f1925`  
**release tree:** `842ab02659c6e2548e58e713f0074add72ffd288`  
**decision-request commit:** `6bc3e3c48a4a845d0e84bc9dc785da847aaa6ef7`  
**decision-request tree:** `ddcd1020121d6d5356f6a96b5821ace564d48c3e`  
**decision:** **PASS — READY FOR ONE EXPLICIT OPERATOR ADOPTION DECISION**

This is release-readiness evidence. It is not adoption, implementation acceptance, deployment approval, activation, archive authorization, governed-write authorization, or restore closure.

## Exact final release

| Artifact | Git blob | Raw SHA-256 |
|---|---|---|
| `CHARTER.md` | `fa2f18088ef117a4558e43ec2fec1edadce484da` | `C2BEF6A8CED30E63048C828A52DE22104FB51FE784155B831360D4BA5EA60664` |
| `DOCTRINE.md` | `a9bbc599edb795cd43aa519876aeb3a7f03e428b` | `006E2F14EC21566A5D0E1E4EB46EF08482087A17D858F5E6A0C718CAD102FF20` |
| `RULES-OF-ENGAGEMENT.md` | `280b60da9f4ea1310dc11925781aa8f5e5a7e901` | `3BD03290C703B863EB62283C31DF5D9274CFF11F69B5C642AFA36427A179CBA8` |
| `OBJECT-DICTIONARY.md` | `db48d8b6a405cd320eb3ac5b22dc8796f05af165` | `AC36DF4A33C3F39609831BB7F781FEF4B4581643B49C7D73252B422C0F88EE5C` |
| `LIFECYCLE.md` | `83576dee68e6c1c02b2f03ba48e6887c8cb4287b` | `1BAB6BBBA4F000908C5DE84563102B622440BA269E2CD6D5192B7D7FEE211144` |
| `RECEIPT-PROFILE.md` | `7f8aa7809274495f8cfd5214d84b3f53772782c1` | `46149CCE2DA7728A66C6C4C8D5704B386DC4506077E22C3307C6A6B9EA84F4A0` |
| `AUTHORITY-RESOLVER.md` | `777bc66871242afd02fd3cdbbaa3ff29895a4e30` | `CB80228C2118F691767F0225641E2734FA258B7361369E9AA61E3DCCE303B06D` |
| `PROTECTED-OPERATOR-CONTROL.md` | `5cb114729be5a2737c4e38a961c747e2e0241b64` | `BA976DA75C8997FFCD7942E41030AFA48CF1858CE1C56EDC0430896AE1979743` |

The manifest contains the same seven component IDs and raw hashes. The release directory has stable filenames. No final filename, title, status, document identity, or governing body contains `RC`, `candidate`, a dated candidate identity, `TS2-*`, or `ROE3-*`.

## Identity and status correction

The release uses one official identity: `TS-CHARTER-1.0`, with seven component identities under that namespace. Each component states that it contains final release bytes and that effect depends on a separate attributable protected operator adoption record. That wording remains true before and after adoption and creates no self-contradictory `NOT EFFECTIVE` status in the adopted bytes.

The rule-ID conversion is mechanical:

- `TS2-*` became `TSC-*`.
- `ROE3-*` became `TSC-ROE-*`.

The complete mapping is retained outside the Charter as non-authoritative review evidence at `docs/governance/reviews/townsquare-charter-v1.0-rule-id-provenance-map.md`. Exact diffs show no normative change from the reviewed release candidate beyond final release identity/status wording, the rule-ID rename, and the Doctrine's adoption-anchor statement.

## Semantic acceptance checks

1. The seven components preserve the reviewed Doctrine, Rules of Engagement, object semantics, lifecycle, receipt, authority-resolution, and protected-control behavior.
2. The Lifecycle retains the full object table, transition/evidence/prohibited-outcome table, protected-control cancellation route, independent closure predicate, closure cases, and the exact boundary: `only protected operator Decision may adopt, control, or accept where required`.
3. Informational correction, dispute, escalation, and failure reporting remain appendable when a consequential effect is denied or parked.
4. A package, manifest, receipt, digest, deployment, test, review, or assertion cannot authorize itself.
5. The release remains implementation-neutral. The 5:1 captured-real/hypothetical weighting is not a Charter rule or adoption score.

## Decision-request acceptance

The adoption decision request is blob `b69bf9cf6833dcc5cae13c558d28617bd76bdce3`, raw SHA-256 `908CF996F4E1FD62754CE2AD0527675C3D80021877A73D5252D3E1651054A1E4`. It pins:

- Charter identity `TS-CHARTER-1.0`;
- exact release commit and tree;
- manifest path, Git blob, and raw SHA-256;
- all seven component IDs and raw SHA-256 values;
- scope `TownSquare governance`;
- an explicit operator-supplied UTC effective time.

It explicitly leaves archival, runtime/release implementation, deployment, activation, governed writes, and restore closure disabled pending separate authorization and evidence.

## Result

The three blockers in Eddie's prior receipt, raw SHA-256 `53D06078EDE51097F5BC6E082A8F93C2D67E8C89580B83E74FB497D88D886BA2`, are closed. The exact release is ready to be presented for one explicit operator decision. No operator decision is inferred from prior instructions, review activity, or this PASS.

