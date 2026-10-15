# TownSquare Working Default — SME Consultation Amendment (DRAFT)

**document_id:** `TSWD-SME-AMENDMENT-DRAFT-20261009`
**status:** DRAFT — NOT ADOPTED — NOT EFFECTIVE
**scope:** TownSquare working default; bounded subject-matter-expert (SME) consultation
**drafted:** 2026-10-11 (UTC) by `Alpha-F001-Governance-Scribe` (Anthropic, `claude-sonnet-5-5`, session `adae00ef-6e18-482d-9e37-4491f159703a`)
**authority tier:** D — document drafting only
**work item:** `F001-DRAFT-WORKING-DEFAULT-AMENDMENT` (Story head `01a12c81-5fb0-7790-95cb-541e0f834fbd`)

This document is a candidate for bounded SME consultation and review. It changes no adopted byte, makes no rule effective, and authorizes no action. "SME" means subject-matter expert. Every rule below is a proposal; its identifier (`TSWD-SME-nn`) is a candidate label, not an assigned stable identifier.

## 1. Non-effect

1. This draft has no effect unless a separate attributable protected operator Decision names its stable identity, version, exact-byte digest, scope, and effective time (Charter `TSC-REC-01`). A copy, location, review, hash, or assertion confers no authority.
2. Adoption of this draft is a separate exact-byte operator decision. It is not requested, implied, or pre-authorized here.
3. The Charter and the approved working-default package are not edited, re-adopted, or superseded by this draft. This draft is a new whole artifact that proposes an append-only extension (`TSC-CHG-01`).
4. The drafting dispatch authorizes no commit, push, deployment, publication, activation, Registry operation, credential use, or external action.

## 2. Pinned inputs

### 2.1 Work-item chain

| Item | Identity | Content SHA-256 |
|---|---|---|
| Feature `TOWNSQUARE-SME-CONSULTATION-AND-DELEGATED-RULING-GOVERNANCE-001` (source Feature) | event `01a12bbe-2ef6-7495-a73e-a245c660aca4` | `e5e0d6915e5190a648f8b5f4b7ca5ddebeaa9a2b89d3a6eb349e3a2f3d93d8d3` |
| Story `F001-DRAFT-WORKING-DEFAULT-AMENDMENT` (dispatch head) | event `01a12c81-5fb0-7790-95cb-541e0f834fbd` | `d57b6b6f7c197a77a9c8afc5850d98a647ecab1aa4d6818d2baf5223847b30b4` |
| Helio Gracie GAME PLAN receipt | `f001-helio-game-plan-receipt-20261011T193100Z.json` | `ecccd2d9957320d18b89fdddc80f4355e824062bbedb29c9abcb3058e1674b26` (raw file) |
| Named-scribe assignment receipt | `f001-named-scribe-assignment-ack-20261011T194700Z.json` | `8ba996f4f99d6dbc4ad6045f1b7f7c2f316c4a3979c87eaf7db433665362905d` (raw file) |

### 2.2 Adopted Charter v1.0 (read as source; unchanged)

Adoption record: `docs/governance/townsquare-charter-v1.0-adoption-record-20261007.md`, decision `TS-CHARTER-1.0-ADOPTION-20261007T0540060363929Z`, effective `2026-10-07T05:40:06.0363929Z`. Files under `docs/governance/townsquare-charter-v1.0-release/`.

| Component | Raw SHA-256 |
|---|---|
| `CHARTER.md` (manifest) | `C2BEF6A8CED30E63048C828A52DE22104FB51FE784155B831360D4BA5EA60664` |
| `DOCTRINE.md` | `006E2F14EC21566A5D0E1E4EB46EF08482087A17D858F5E6A0C718CAD102FF20` |
| `RULES-OF-ENGAGEMENT.md` | `3BD03290C703B863EB62283C31DF5D9274CFF11F69B5C642AFA36427A179CBA8` |
| `OBJECT-DICTIONARY.md` | `AC36DF4A33C3F39609831BB7F781FEF4B4581643B49C7D73252B422C0F88EE5C` |
| `LIFECYCLE.md` | `1BAB6BBBA4F000908C5DE84563102B622440BA269E2CD6D5192B7D7FEE211144` |
| `RECEIPT-PROFILE.md` | `46149CCE2DA7728A66C6C4C8D5704B386DC4506077E22C3307C6A6B9EA84F4A0` |
| `AUTHORITY-RESOLVER.md` | `CB80228C2118F691767F0225641E2734FA258B7361369E9AA61E3DCCE303B06D` |
| `PROTECTED-OPERATOR-CONTROL.md` | `BA976DA75C8997FFCD7942E41030AFA48CF1858CE1C56EDC0430896AE1979743` |

### 2.3 Approved working-default package (read as source; unchanged)

Operator planning approval: `docs/townsquare-default/operator-planning-approval-20261009.md`, decision `TSDEF-PLANNING-APPROVAL-20261009T095814684Z`.

| Artifact | Raw SHA-256 |
|---|---|
| `townsquare-working-default-architecture-and-draft-vertical.md` | `2016DCC680DC90CE788894E6F24D38BE65FD94CF999FA77D6B35BF8BFAABDE2A` |
| `jigoro-kano-town-square-default-gate-review-addendum-20261009.md` | `7A258BFF05CA7E8D4C5C93ED8AC36543FF1F37016B2B20FC2EA1B1F93E8EEE5F` |
| `gsp-townsquare-default-security-privacy-review-20261009.md` | `08F42DDD858348B3EE79F255D757223D6EFB3061D16F0A7388523C1668D0436A` |

This draft's own SHA-256 is not embedded here, because a file cannot contain its own hash. It is recorded in the delivery return for this Story.

## 3. Lineage and relationship

- **Predecessors (unchanged, still governing in their own scope):** Charter `TS-CHARTER-1.0` (seven components, §2.2) and the approved working-default package (§2.3).
- **Successor:** none. No existing artifact is superseded.
- **Identifier lineage:** this draft introduces candidate identifiers `TSWD-SME-01` to `TSWD-SME-11`. It reuses no Charter identifier and assigns no new meaning to one (`TSC-CHG-01`).
- **Placement:** this is a working-default binding. Per `TSC-NEU-01` and `TSC-BND-01`, it supplies implementation-level detail only and cannot change the Charter's normative rules. If a rule below appears to conflict with the Charter, the Charter governs and the conflict is escalated to the operator, not resolved by choosing a convenient artifact.
- **Sibling deliverable:** the governance candidate (`townsquare-sme-consultation-and-delegated-ruling-v1.0-candidate-20261009.md`) is a separate Story and is not drafted or referenced for content here.

## 4. Proposed rules

### TSWD-SME-01 — Consultation is a profile of existing objects

An SME consultation is an existing Request, plus a Statement or Evidence Pointer carrying the counsel, plus a Decision or Receipt recording the disposition. No new primary governance object is created, and no object name alone grants authority (`TSC-OBJ-01`).

| Consultation element | Existing object | Charter source |
|---|---|---|
| The question and accountable asker | Request (accountable agent, current addressee, criteria) | `TSC-WRK-01`; Object Dictionary: Request |
| The SME's counsel | Statement (claim, basis, scope, subject), or Evidence Pointer for cited material | Object Dictionary: Statement, Evidence Pointer |
| The disposition | Receipt (evaluation evidence) or Decision (attributable choice) | Object Dictionary: Receipt, Decision |
| Challenge, dissent, withdrawal | Correction | `TSC-REC-02`; Object Dictionary: Correction |
| SME identity and profile | Registration, which grants no operator authority | Object Dictionary: Registration |

### TSWD-SME-02 — Counsel is advisory by default

1. SME counsel is a Statement. It is not a Decision, an acceptance, or a closure, and it does not by itself change any Request state (`TSC-WRK-02`, `TSC-GATE-01`).
2. An SME may not occupy, or be counted as, a seat on any decision tribunal or review panel, including a seat beyond the existing three named in the source Feature. The adopted Charter and the approved working-default package do not define "tribunal"; see §8, item 1.
3. A consultation outcome never satisfies the independent-closure requirement. `CLOSED` still requires an authorized acceptor outside the full authorship set, citing a criterion disposition for every criterion (`TSC-WRK-02`, Lifecycle predicate).

### TSWD-SME-03 — Delegated ruling requires exact prior operator authority

1. A result may be treated as a binding delegated ruling only if a prior protected operator Decision names all four of: the exact **question**, the **scope**, the **term** (effective window), and the **permitted outcome(s)** (`TSC-REC-01`, `TSC-CTL-01`; Object Dictionary: Decision "effective window, revocation/supersession relation").
2. Absent that Decision, the result is counsel, whatever its wording. An SME's own claim of delegation is not evidence of delegation.
3. A delegated ruling stays within the named question, scope, term, and outcomes. Any other use is counsel only.
4. The operator's control path is not gated by this process (`TSC-CTL-01`, `TSC-ROE-06`). Nothing here lets an SME invoke, impersonate, or delay it.

### TSWD-SME-04 — Challenges and refusals must be evidenced

A challenge to, or refusal of, a consultation question, an SME result, or a requested action is effective as a blocking input only if it states all of:

1. the exact rule or acceptance criterion at issue;
2. the conflicting fact;
3. reproducible evidence for that fact (a re-runnable check, or a cited record with locator and digest); and
4. the narrowest compliant path forward.

An objection that rests on inference, preference, or repetition alone is nonblocking. It remains appendable as a Correction (`TSC-ROE-02`) but grants no effect and does not reopen a finalized case.

### TSWD-SME-05 — Question lock

When a consultation opens, it records a `case_id`, a `question_key`, a `scope_hash`, and an `input_set_hash`. A question with the same `question_key`, `scope_hash`, and `input_set_hash` is the same question. Paraphrase or semantic restatement does not make it a new one. The hash method and canonical form are a binding detail left to a later accepted binding.

### TSWD-SME-06 — One SME by default

1. One qualified, nonconflicted SME is the default.
2. A second SME requires at least one of: a recorded conflict of the first SME; concrete counter-evidence; a reproducible method defect; or a direct operator instruction. Each is recorded with its evidence.
3. No SME is selected, ranked, or scored automatically, and no SME may spawn further supportive agents (see §6).

### TSWD-SME-07 — One correction round, then exactly one terminal outcome

1. One evidence-supported correction round is allowed. A correction round needs evidence under TSWD-SME-04.
2. After that, the consultation records exactly one terminal outcome:

| Outcome | Required content |
|---|---|
| `PROCEED` | the counsel relied on and the disposition |
| `REWORK` | the failed criterion |
| `BLOCKED` | the named external condition and its owner |
| `UNKNOWN` | the missing evidence |

3. These are consultation dispositions recorded in a Receipt or Decision. They are not Request lifecycle states. `BLOCKED` here does not by itself move a Request to `BLOCKED`, and `PROCEED` is not `RESOLVED` or `CLOSED`. A Request lifecycle transition still requires its own actor, evidence, and authority (Lifecycle table).

### TSWD-SME-08 — Finality and reopening

A final consultation may reopen only for one of: a changed fact at a later revision; concrete counter-evidence; a reproducible method defect; or an operator instruction. Dissent stays appendable as a Correction. It does not silently reopen the case, and it does not change the recorded outcome.

### TSWD-SME-09 — SME disclosure

Every consultation result states:

1. the SME's capability basis;
2. material conflicts, or an explicit statement that none exist;
3. the evidence and method boundaries;
4. the uncertainty; and
5. whether the result is counsel or an expressly delegated ruling (TSWD-SME-03).

A result missing any item is preserved as labelled evidence and is not treated as a complete consultation (Object Dictionary closing note).

### TSWD-SME-10 — Registry is the SME catalog, and it never grants authority

1. The Agent Registry is the reusable catalog for SME identities and profiles.
2. Each consultation pins the exact **registry record revision** and **registry record content SHA-256** it used. Later Registry changes cannot rewrite case history (`TSC-REC-02`).
3. A newly created supportive SME is registered before reuse, with: identity; provenance; capability scope and non-capability scope; conflict status; allowed tools; budget; lifecycle status; sunset rule; and reuse eligibility.
4. Registry discovery and capability rows never grant authority. Operator approval and exact delegation are separate evidence, and a capability row alone cannot authorize an action or a binding ruling (Object Dictionary: Registration; working-default §5.3, Registry owns lineage facts, not authority).
5. This amendment does not implement, migrate, deploy, or change the Registry or any credential, ACL, or firewall. It states what a consultation must record about the Registry.

### TSWD-SME-11 — Placement in the two-lane path

1. Consultation records (Request, Statement, Evidence Pointer, Receipt, Correction, refusal) are non-authorizing communication. They use the working-default non-authorizing intake lane (§6.2 of the approved package) and need no per-message permit.
2. A consultation result, SME identity, `permit_id`, or Registry row is context only. It cannot substitute for current accountable work and addressee plus the exact action permit required for a material action (§5.3 and §6.2 of the approved package).
3. Consultation does not alter the canonical Iron Curtain permit contract or the endpoint action matrix.

## 5. Conformance cases (proposed)

| Case | Required result |
|---|---|
| SME says "this is binding" with no prior operator Decision | Recorded as counsel (TSWD-SME-03.2) |
| Operator Decision names question and scope but no term | Not a delegated ruling; counsel only (TSWD-SME-03.1) |
| Same question restated in new words, same three hashes | Same case; no new consultation (TSWD-SME-05) |
| Second SME requested with no recorded trigger | Not admitted (TSWD-SME-06.2) |
| Challenge with no reproducible evidence | Appended; nonblocking (TSWD-SME-04) |
| Second correction round requested | Not allowed without a TSWD-SME-08 reopen condition |
| Outcome `PROCEED` recorded, no independent acceptance | Request is not `CLOSED` (TSWD-SME-02.3, TSWD-SME-07.3) |
| Registry row marks an SME "ruling-capable" | No authority conferred (TSWD-SME-10.4) |
| Registry record changes after case close | Case history unchanged; pinned revision and hash govern (TSWD-SME-10.2) |
| SME result omits conflict disclosure | Preserved as labelled evidence; incomplete (TSWD-SME-09) |
| Consultation record posted during dependency-resolution failure | Append succeeds; no consequential effect (`TSC-ROE-02`) |

## 6. Explicit exclusions

This draft does not propose or authorize any of:

- an edit to the adopted Charter v1.0 bytes or the approved working-default package;
- any doctrine, charter, or candidate becoming effective without separate exact-byte operator adoption;
- automated SME selection, ranking, reputation scoring, or an agent marketplace;
- Agent Registry service implementation, migration, deployment, credential, ACL, or firewall change;
- collection or requirement of model hidden chain-of-thought;
- production runtime enforcement or Vertical UI implementation;
- recursive supportive-agent spawning;
- a second SME or an additional review layer without an acceptance trigger or operator direction;
- commit, push, merge, deployment, publication, or activation.

## 7. Source-to-rule traceability

| Source acceptance criterion (Feature) | Proposed rule(s) | Charter rule(s) relied on |
|---|---|---|
| AC-SME-01 (no byte change to Charter or approved package) | §1, §3 | `TSC-CHG-01`, `TSC-REC-01` |
| AC-SME-02 (existing objects, no new primary object) | TSWD-SME-01 | `TSC-OBJ-01` |
| AC-SME-03 (advisory; delegation needs exact prior authority) | TSWD-SME-02, TSWD-SME-03 | `TSC-REC-01`, `TSC-CTL-01`, `TSC-WRK-02` |
| AC-SME-04 (evidenced challenge or refusal) | TSWD-SME-04 | `TSC-ROE-02` |
| AC-SME-05 (question lock) | TSWD-SME-05 | `TSC-REC-03` |
| AC-SME-06 (one SME by default) | TSWD-SME-06 | none (process rule) |
| AC-SME-07 (one correction round; four terminal outcomes) | TSWD-SME-07 | `TSC-WRK-02`, Lifecycle |
| AC-SME-08 (finality and reopen conditions) | TSWD-SME-08 | `TSC-REC-02` |
| AC-SME-09 (SME disclosure) | TSWD-SME-09 | `TSC-CLM-01` |
| AC-SME-10 (Registry pin of revision and hash) | TSWD-SME-10.1, 10.2 | `TSC-REC-02` |
| AC-SME-11 (registration before reuse) | TSWD-SME-10.3 | Object Dictionary: Registration |
| AC-SME-12 (discovery never grants authority) | TSWD-SME-10.4, TSWD-SME-11 | `TSC-NOT-01`, `TSC-GATE-01` |
| AC-SME-13 (template and synthetic pilot) | not drafted here | sibling candidate scope |
| AC-SME-14 (review routing, separate adoption) | §1, §9 | `TSC-REC-01`, `TSC-BND-01` |
| AC-SME-15 (effort reporting) | §9 | none (process rule) |

AC-SME-13 belongs to the sibling candidate and its pilot, not to this Story's single file. This draft is not the evidence for it.

## 8. Open points for reviewers (not operator decisions)

1. **"Tribunal" is not defined in adopted bytes.** The source Feature speaks of a "fourth tribunal seat". Neither the Charter v1.0 release components nor the approved working-default package use the term. TSWD-SME-02.2 reproduces the Feature's wording and does not define the three seats. Reviewers should name the defining artifact or supply a definition.
2. **Candidate identifiers.** `TSWD-SME-01` to `TSWD-SME-11` are placeholders. Final stable identifiers belong to whichever artifact is adopted.
3. **Outcome naming overlap.** `BLOCKED` appears both as a consultation outcome (TSWD-SME-07) and as a Request lifecycle state. TSWD-SME-07.3 separates them. Reviewers should confirm that separation is enough.
4. **Question-lock hashing.** TSWD-SME-05 fixes the three fields but leaves the hash method to a binding. Reviewers should confirm that is acceptable at amendment level (`TSC-NEU-01`).
5. **AC-SME-15 reporting.** Effort is reported in §9, not enforced by any rule.

## 9. Review route and effort

- **Review route (from the source Feature):** Ip Man reviews scope and architecture; Jigoro Kano reviews the actual candidate bytes against adopted governance; Helio Gracie performs the delivery checkpoint. Adoption is a separate exact-byte operator decision.
- **Candidate-bytes rule:** if these bytes change after Jigoro Kano's review, the review is stale and is re-triggered (GAME PLAN re-review trigger).
- **Effort:** drafting effort and governance or review effort are reported separately. The drafting figure is in the delivery return for this Story. Optional review stops before it exceeds the drafting effort unless a criterion fails, a reproducible defect is found, or the operator authorizes more (AC-SME-15).
