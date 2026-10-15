# TownSquare Working Default — gate-review addendum

**Review date:** 2026-10-09  
**Original review:** `jigoro-kano-town-square-default-gate-review-20261009.md`  
**Bounded verdict:** **PASS** — all seven original REWORK blockers are closed  
**Scope:** correction review only; no re-review of unrelated architecture or work-item scope

## Evidence limitation

The filesystem command runner remains unavailable to this reviewer. This addendum relies on the coordinating session's exact correction readback from the saved amended draft. The evidence basis is therefore **reported-by coordinator**, not independent file readback or diff. This PASS stops being reliable if the saved text differs materially from that correction evidence.

This addendum authorizes no filing, authoritative-ledger append, state transition, implementation, deployment, publication, external contact, incident Receipt append, live proof, or probe cleanup.

## Closure of the seven original blockers

| # | Original blocker | Correction evaluated | Result |
| --- | --- | --- | --- |
| 1 | F2 inherited F1 and overblocked S3 | F2 now has no Feature-level dispatch dependency; child Story dependencies are authoritative. S1+S7 permits consideration of S3 while S2 remains blocked; S4 requires S2+S3; parent metadata grants no authority. Tests preserve the canonical POC block on material `/v1/events`. | **CLOSED**. The intended two-lane sequencing is decidable without weakening the material lane. |
| 2 | S7 incident Receipt lacked a non-circular bootstrap path | S7 is explicitly `BLOCKED` until a separate attributable operator Decision names an already-existing safe Receipt system and authenticated non-authorizing append operation, destination, fixed payload/digest, principal, and expected Receipt. Package approval is not that Decision. No verified operation returns the matter to the operator; temporary endpoint, NAS write, file drop, and self-bootstrap are forbidden. | **CLOSED**. The missing bootstrap fact fails closed without treating the future S3 implementation as its own prerequisite. |
| 3 | S7 “probe” wording could authorize another production write | S7 now forbids every named NAS content/name/metadata mutation, limits inspection of the existing probe to read-only operations, and permits write-denial testing only on a named non-production target after isolation. Any unauthorized syscall or parent change fails the gate; cleanup remains a separate Decision. | **CLOSED**. The trigger, forbidden effects, failure result, and cleanup boundary are explicit and testable. |
| 4 | S6 duplicated canonical live Revere work | S6 is narrowed to integration of **accepted** Revere transport with TownSquare causal Receipts. Base mailbox, lease, ACK, replay, deduplication, v1, bilateral proof, and adapters are excluded. It depends on independently accepted, normally CLOSED canonical Revere keys and requires a duplicate key/scope scan; amendments are integration-only. | **CLOSED**. Canonical work retains ownership; S6 no longer creates a competing implementation or acceptance path. |
| 5 | Revere checked authority after external contact could already occur | New §6.5 enumerates send/enqueue, lease receive, ACK, redelivery/replay, and vendor-adapter delivery. Existing POC coverage is expressly denied; live/external rows remain disabled until the POC is accepted and a Jackie/GSP-reviewed amendment is adopted. Each row resolves principal, current accountable work/Decision, exact authority, enforcement before commit, zero-mutation denial, protected override, and Receipt. Synthetic tests cannot contact external sessions; live proof needs a separate Decision. | **CLOSED**. External contact and delivery-state mutation are gated before commit, without silently extending the canonical POC. |
| 6 | Lineage could be mistaken for delegated authority | §5.3 and S1/S5 now classify parent session, delegator, subagent, and every lineage field as context only. Registry owns the fact, Vertical owns accountable work/addressee, and Iron Curtain owns exact action authority. Every effect binds executing actor/session, current accountable work/addressee, and exact authority. Derived permits are unsupported/rejected, and the deferred Registry graph is amended rather than described as previously accepted. | **CLOSED**. Attribution and authority are independently resolved; no lineage edge delegates power. |
| 7 | Rollback lacked an exact authority predicate | §7.4/S8 now allows rollback only under a protected deployment Decision and still-valid exact permit that preauthorizes every named rollback binding, or under a later protected Decision and fresh permit. The negative truth table produces zero mutation plus a safe Receipt. Failed checks may stop/isolate only, and operator Decisions are never ordinarily gated. | **CLOSED**. Rollback is exact-action authorized and non-self-certifying. |

## Bounded validation

The correction evidence was replayed only against the seven original failures:

- Dependency truth cases: S3 permitted for consideration after S1+S7 while S2 is blocked; S4 remains blocked; material `/v1/events` remains unavailable.
- Bootstrap failure: absent or mismatched incident Receipt keeps every Sentinel implementation Story nondispatchable and returns control to the operator.
- Production-boundary failure: any NAS mutation attempt or observed probe/parent change fails S7; cleanup authority remains independent.
- Duplicate-work check: S6 cannot own any canonical Revere base behavior and cannot start before normal independent acceptance of the canonical keys.
- Transport default-deny: every unknown writing route and every live/external Revere row without the reviewed amendment yields zero mutation.
- Authority separation: lineage, identity, session, parent/delegator relationship, message, Receipt, delivery, and `work_ref` remain non-authorizing context.
- Rollback truth table: missing, expired, mismatched, replayed, wrong-target, wrong-artifact, wrong-trigger, and out-of-window authority cannot mutate production; operator stop/isolate remains available.

The new exhaustive closed/default-deny route matrix and automated coverage support closure of Blocker 5; they do not themselves authorize or arm a live gate.

## Final bounded decision

**PASS.** All seven findings in the original REWORK are closed by checkable text and tests. **Exact remaining edits for those seven findings: none.**

This means only that the amended planning package may proceed to its next governance checkpoint. It does not approve the hierarchy, append any event, satisfy S7, authorize the incident Receipt or cleanup Decision, move a Story to WORKING, accept canonical dependencies, arm a gate, implement code, deploy, cut over, roll back, publish, or contact any external session.

