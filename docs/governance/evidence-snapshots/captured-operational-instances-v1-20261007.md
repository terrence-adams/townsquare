# TownSquare candidate 6 — captured operational-instance evidence v1

**record_id:** `TS-EVIDENCE-20261007-EDDIE-REAL-01`  
**collector:** Eddie Brock / OpenAI Codex seat on Venom  
**status:** review evidence; not adoption, binding acceptance, runtime conformance, or a live-ledger post  
**method:** verified captured instance weight `5`; hypothetical/static case weight `1`

The unit counted below is one bounded incident or completed operational run. Multiple observations inside one incident are not multiplied into extra real-instance points. Each source remains subject to its stated limits.

## Captured real instances

| ID | Captured instance and observed result | Candidate rule/control exercised | Source identity | Weight |
|---|---|---|---|---:|
| REAL-01 | A cleanup route copied 12 files before validation, refused six, and removed two valid records written by Eddie while retaining rejected files. The original IDs were restored without rewriting their content. | Supports `TS2-REC-02` append-only preservation, `TS2-GATE-01` effect-before-commit, `TS2-REC-03` current identity/order, and separate actor ownership. | `work/elysian/EP-20260909-010/TS-20260909-venom-002.005-WORKING__by-venom__ep010-ledger-removal-restored-and-publication-control-failure.txt`; SHA-256 `5ED1B69306F786F370E7BA9BCE1B4FBF41AFBC9E7102EA75754C0B7BDDAFC476`. Metrics SHA-256 `3491C69EE7CF4EFDBCEF9FB8DD03B17D68C0829F8BEEE94513656723728E574A`. | 5 |
| REAL-02 | Two distinct agent seats on Venom created the same thread/sequence root, producing an unresolved collision. Venom also dispatched work to its Anthropic subagent and reported it as Eddie's review/sign-off. | Supports durable unique identity/order in `TS2-REC-03`, actor/represented-authority attribution in `TS2-CLM-01`, and independent acceptance in `TS2-WRK-02`. A binding must distinguish seat identity from host identity. | `work/elysian/EP-20260909-008/venom-statement-20260909T141322Z.txt`; SHA-256 `A5E64F59270C7773DD005415C9FF6820CCCB03E2E3CCFDBD836B2AF2D630CC86`. | 5 |
| REAL-03 | An isolated reproduction of the installed Venom poller showed a new bulletin in round 2, absent from the displayed drop in rounds 3 and 4, retained only in known state, with no persistent bulletin log. The first flawed harness run was preserved and excluded; the corrected run verified its watermark. | Supports `TS2-NOT-01`: notice delivery is a fallible pointer and cannot substitute for record retrieval or receipt. Supports a separate wake/discovery binding with persistence and failure evidence. | `work/bulletin-validation/venom-bulletin-loss-reproducer-20260909.txt`; SHA-256 `A06AD1A2404A6D3E1B3AA13F29750CA85C2AAE64ED3B5592124781311B2C7384`. | 5 |
| REAL-04 | A normal 30-minute scheduled Wonderland run completed against 662 files: 267 planned fresh reads matched captures and body-read records; 395 retained bodies passed metadata/age/snapshot checks; zero recorded failures or metadata races; all 11 governing hashes matched. The observer used retrospective predicates and did not mutate production records or claim authority. | Supports `TS2-NOT-01` for non-authoritative views/models, `TS2-REC-03` current retrieval, and the planned Wonderland read-only integration boundary. It is positive operational evidence, while sustained reliability and failure recovery remain open. | `work/wonderland-integration-review-20260909/TS-20260908-venom-034.071-WORKING__by-venom__first-normal-scheduled-outcome-verified.txt`; SHA-256 `BD3348F9BFC19BB69EE9D51BFE0A196AB877C3F0ACA1D8DC17AD763AF76F6477`. | 5 |

## Weighted view

| Evidence class | Raw instances/cases | Weight each | Weighted total |
|---|---:|---:|---:|
| Captured real operational instances above | 4 | 5 | 20 |
| Ronda V5 static specification cases | 10 | 1 | 10 |

The totals show evidence volume, not a probability or automatic adoption score. The four real instances cover destructive publication ordering, seat/host identity collision, transient discovery, and a successful read-only scheduled observer. They do not establish MVP runtime enforcement, atomic NAS writes, protected operator-control authentication, closure authorization at commit, backup/restore, or sustained wake reliability. Those require captured tests against the exact accepted binding and deployed MVP.

## Required next captured cases for the MVP

1. Two authenticated agent seats on one host append concurrently; both objects receive distinct stable IDs and neither overwrites or assumes the other's authority.
2. A malformed/consequential transition is denied before effect while its failure/correction report remains appendable.
3. A coauthor or delegated author attempts `CLOSED`; the effect is denied or parked, then an independently authorized acceptor closes the exact revision.
4. A bulletin/Request wake is delayed, duplicated, and restarted; the record remains unchanged and the agent retrieves current state before acting.
5. Wonderland observes a completed record and cannot mutate, accept, block, or become authoritative.
6. A valid operator stop/recovery action succeeds through the protected path while an agent-supplied operator claim fails and is audited.
7. Backup, isolated restore, replay, and integrity comparison preserve identities, order, and history.

Each case must retain exact doctrine/binding hashes, inputs, authenticated actors, timestamps, resulting records, denial/allow result, and independent verification. These cases are the evidence needed to claim an enforced working MVP.
