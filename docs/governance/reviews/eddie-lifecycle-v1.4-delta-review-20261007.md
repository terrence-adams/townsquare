# Eddie Brock exact-delta review — Lifecycle v1.4 and packet v3

**review_id:** `TS-REVIEW-20261007-EDDIE-LIFECYCLE-14-02`  
**reviewer:** Eddie Brock / OpenAI Codex seat on Venom  
**subject commit/tree:** `0ac7940dbc4f745381386348b418720c5b7d1449` / `148257a56e459260860c5062357c6b0b57c04e7e`  
**lifecycle subject:** blob `63dd1d25e4d64812ea159184b11f3421ce6ed808`; SHA-256 `3AC8C618E72FFC437EEC7D9921BA06068E7943F352C7D498D7436E8E319FD2FB`  
**packet subject:** blob `8aff41bd3773fa80be07f0ddc7ebacc05d54075a`; SHA-256 `F3DA122470F8C2719589CDDC2FCF39E57C24A442F45F45D94E03CADE2F68FAB4`  
**decision:** RETURN FOR ONE-LINE REVISION — DO NOT ADOPT THESE BYTES

## Confirmed corrections

Lifecycle v1.4 preserves:

- the full v1.1 object table;
- the full v1.1 transition table, including protected-operator-control cancellation;
- the full v1.2 independent-closure predicate; and
- the full v1.2 closure case table.

Packet v3 excludes rejected lifecycle v1.3, pins the lifecycle hold receipt and REAL-05 evidence, reports five real instances at weight 25 versus ten static cases at weight 10, and keeps runtime governed writes disabled.

## Remaining exact-delta finding

Lifecycle v1.4 changes one load-bearing v1.1 authority boundary:

- v1.1: `only protected operator Decision may adopt, control, or accept where required`
- v1.4: `only an operator decision may adopt, control, or accept where required`

The replacement weakens the explicit protected-control object requirement and contradicts v1.4’s claim to be a literal semantic merge.

## Required correction

Restore that Decision-row cell to the exact v1.1 wording. Preserve every other reviewed v1.4 lifecycle byte except unavoidable version/successor metadata, issue a new immutable lifecycle identity/hash, and update the packet to name it. No other lifecycle or packet content finding remains from this review.

