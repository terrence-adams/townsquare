# TownSquare SME Consultation and Delegated Ruling — v1.0 Candidate

**document_id:** `TS-SME-CONSULTATION-1.0-CANDIDATE`
**status:** DRAFT — NOT ADOPTED — NOT EFFECTIVE
**scope:** TownSquare governance; bounded subject-matter-expert (SME) consultation and delegated ruling
**drafted:** 2026-10-11 (UTC) by `Alpha-F001-Governance-Scribe` (Anthropic `claude-sonnet-5-5`, session `adae00ef-6e18-482d-9e37-4491f159703a`)
**authority tier:** D — document drafting only
**work item:** `F001-DRAFT-GOVERNANCE-CANDIDATE`, Story event `01a12c94-89ad-7702-b58b-4105d0d90f82`

"SME" means subject-matter expert. This candidate is a whole new artifact. It has no effect unless a separate attributable protected operator decision names its stable identity, version, exact-byte digest, scope, and effective time (Charter `TSC-REC-01`). Rule labels `TSS-SME-nn` are candidate labels, not assigned stable identifiers. Nothing here edits, re-adopts, or supersedes any adopted byte.

## 1. Pinned sources

| Source | Identity | Digest |
|---|---|---|
| Source Feature `TOWNSQUARE-SME-CONSULTATION-AND-DELEGATED-RULING-GOVERNANCE-001` | event `01a12bbe-2ef6-7495-a73e-a245c660aca4`; file `VR-20261009-ynm-001.2-OPEN.txt` | content `e5e0d6915e5190a648f8b5f4b7ca5ddebeaa9a2b89d3a6eb349e3a2f3d93d8d3`; file `346e5200866c70c41473c8975580a570d3c0fa77e62c579e07a56ae29b7668a5` |
| Story `F001-DRAFT-GOVERNANCE-CANDIDATE` | event `01a12c94-89ad-7702-b58b-4105d0d90f82` | content `55e8d2bdbca2671d2942d658c9d9972377a8d2ea6752ea861de851d3e161f898` |
| Predecessor `F001-DRAFT-WORKING-DEFAULT-AMENDMENT` (closed) | `CLOSED` event `01a12c94-8593-72c5-b663-095b6cc9cc69` | content `989b553413ee1c939a5b4d807f4d464e798fa867e5d5b4830e5cbb3edfd3ce66` |
| Working-default amendment bytes (read as source, unchanged) | `docs/townsquare-default/townsquare-working-default-sme-consultation-amendment-20261009.md` | raw `8150decfa24fea04edf472f23b82bd0c523712e70aa861d72c1a34f0d8d3164a` |
| Helio GAME PLAN | `f001-governance-candidate-helio-game-plan-20261011T200700Z.json` | raw `5bf1cf797d7402fbfe4c39a23740949bcf9d2de7fe6f5856d770aa2fad0818d0` |

Adopted Charter `TS-CHARTER-1.0` (decision `TS-CHARTER-1.0-ADOPTION-20261007T0540060363929Z`), read as source and unchanged, under `docs/governance/townsquare-charter-v1.0-release/`:

| Component | Raw SHA-256 |
|---|---|
| `CHARTER.md` | `C2BEF6A8CED30E63048C828A52DE22104FB51FE784155B831360D4BA5EA60664` |
| `DOCTRINE.md` | `006E2F14EC21566A5D0E1E4EB46EF08482087A17D858F5E6A0C718CAD102FF20` |
| `RULES-OF-ENGAGEMENT.md` | `3BD03290C703B863EB62283C31DF5D9274CFF11F69B5C642AFA36427A179CBA8` |
| `OBJECT-DICTIONARY.md` | `AC36DF4A33C3F39609831BB7F781FEF4B4581643B49C7D73252B422C0F88EE5C` |
| `LIFECYCLE.md` | `1BAB6BBBA4F000908C5DE84563102B622440BA269E2CD6D5192B7D7FEE211144` |
| `RECEIPT-PROFILE.md` | `46149CCE2DA7728A66C6C4C8D5704B386DC4506077E22C3307C6A6B9EA84F4A0` |
| `AUTHORITY-RESOLVER.md` | `CB80228C2118F691767F0225641E2734FA258B7361369E9AA61E3DCCE303B06D` |
| `PROTECTED-OPERATOR-CONTROL.md` | `BA976DA75C8997FFCD7942E41030AFA48CF1858CE1C56EDC0430896AE1979743` |

This candidate's own digest is not embedded, because a file cannot contain its own hash. It is recorded in the delivery return.

## 2. Lineage and placement

- **Predecessors, unchanged:** Charter `TS-CHARTER-1.0` and the working-default amendment above.
- **Successor:** none. No artifact is superseded.
- **Identifier lineage:** `TSS-SME-01` to `TSS-SME-14` are new and reuse no Charter or amendment identifier (`TSC-CHG-01`). The amendment's `TSWD-SME-nn` rules are working-default-level counterparts. Where a rule here restates one, the amendment states the working-default binding and this candidate states the governance rule.
- **Conflict rule:** this is governance detail that cannot change Charter normative rules (`TSC-NEU-01`, `TSC-BND-01`). If a rule here appears to conflict with the Charter, the Charter governs and the conflict is escalated to the operator, not settled by choosing a convenient artifact.
- **Undefined term:** the source Feature speaks of a "fourth tribunal seat". Neither the Charter release nor the approved working-default package defines "tribunal" or its three seats. TSS-SME-03 reproduces the Feature's constraint without defining the seats. Reviewers must name the defining artifact (§9, item 1).

## 3. Governance rules

### TSS-SME-01 — Consultation is a profile of existing objects (AC-SME-02)

An SME consultation is a profile over existing Charter objects. It creates no new primary governance object, and an object name alone grants no authority (`TSC-OBJ-01`).

| Element | Existing object | Source |
|---|---|---|
| Question and accountable asker | Request: accountable agent, current addressee, criteria | `TSC-WRK-01` |
| SME counsel | Statement (claim, basis, scope, subject), or Evidence Pointer for cited material | Object Dictionary |
| Disposition | Receipt (evaluation evidence) or Decision (attributable choice) | Object Dictionary |
| Challenge, dissent, withdrawal | Correction, appended and never edited in place | `TSC-REC-02` |
| SME identity and profile | Registration, which grants no operator authority | Object Dictionary |

### TSS-SME-02 — Counsel is advisory by default (AC-SME-03)

1. SME counsel is a Statement. It is not a Decision, acceptance, or closure, and it changes no Request state by itself.
2. A consultation never satisfies independent closure. `CLOSED` still requires an authorized acceptor outside the complete authorship set, with a disposition for every criterion (`TSC-WRK-02`; Lifecycle predicate).
3. A result presented as binding without TSS-SME-04 authority is counsel, whatever its wording.

### TSS-SME-03 — SME is not a tribunal seat (AC-SME-03)

An SME is not a seat on any decision tribunal or review panel, and cannot become a fourth seat beyond the three named in the source Feature. The SME's counsel does not count as any seat's vote. Recording an SME does not change who decides.

### TSS-SME-04 — Delegated ruling needs exact prior operator authority (AC-SME-03)

1. A result may be treated as a binding delegated ruling only if a prior protected operator Decision names all four: the exact **question**, the **scope**, the **term** (effective window), and the **permitted outcome(s)** (`TSC-REC-01`, `TSC-CTL-01`; Object Dictionary: Decision).
2. The Decision predates the ruling. An SME's claim of delegation, a Registry row, or a later ratification does not make an earlier result binding.
3. A delegated ruling is binding only within the named question, scope, term, and outcomes. Anything else is counsel.
4. Operator control is never gated by this process, and no SME may invoke, impersonate, delay, or reinterpret it (`TSC-CTL-01`, `TSC-ROE-06`).

### TSS-SME-05 — Evidence-bearing challenge or refusal (AC-SME-04)

A challenge to, or refusal of, a question, an SME result, or a requested action blocks only if it states all of:

1. the exact rule or acceptance criterion at issue;
2. the conflicting fact;
3. reproducible evidence for that fact (a re-runnable check, or a cited record with locator and digest); and
4. the narrowest compliant path forward.

An objection resting on inference, preference, or repetition alone is **nonblocking**. It stays appendable as a Correction (`TSC-ROE-02`) and grants no effect.

### TSS-SME-06 — Question lock (AC-SME-05)

Each consultation locks four values when opened:

| Field | Purpose |
|---|---|
| `case_id` | durable identity of the consultation |
| `question_key` | stable key for the question asked |
| `scope_hash` | digest of the exact scope |
| `input_set_hash` | digest of the exact input set |

A question with the same `question_key`, `scope_hash`, and `input_set_hash` is the same question. Paraphrase or semantic restatement does not make a new consultation or reopen a finalized one. Hash method and canonical form are left to a later accepted binding (`TSC-NEU-01`).

### TSS-SME-07 — One SME by default (AC-SME-06)

1. One qualified, nonconflicted SME is the default.
2. A second SME is admitted only on a recorded conflict, concrete counter-evidence, a reproducible method defect, or a direct operator instruction. The trigger and its evidence are recorded.
3. No SME is selected, ranked, or scored automatically, and no SME spawns further supportive agents.

### TSS-SME-08 — One correction round, then one terminal outcome (AC-SME-07)

1. One evidence-supported correction round is allowed. It needs evidence under TSS-SME-05.
2. After that the consultation records exactly one terminal outcome:

| Outcome | Required content |
|---|---|
| `PROCEED` | the counsel relied on and the disposition |
| `REWORK` | the failed criterion |
| `BLOCKED` | the named external condition and its owner |
| `UNKNOWN` | the missing evidence |

3. These are consultation dispositions in a Receipt or Decision, not Request lifecycle states. `BLOCKED` here does not move a Request to `BLOCKED`, and `PROCEED` is not `RESOLVED` or `CLOSED`. A Request transition still needs its own actor, evidence, and authority (Lifecycle table).

### TSS-SME-09 — Finality and reopening (AC-SME-08)

A final consultation may reopen only for: a changed fact at a later revision; concrete counter-evidence; a reproducible method defect; or an operator instruction. Dissent stays appendable as a Correction. It does not silently reopen the case or alter the recorded outcome.

### TSS-SME-10 — SME disclosure (AC-SME-09)

Every result states: the SME's capability basis; material conflicts (or an explicit "none"); evidence and method boundaries; uncertainty; and whether the result is counsel or an expressly delegated ruling under TSS-SME-04. A result missing any item is preserved as labelled evidence and is not a complete consultation (Object Dictionary closing note).

### TSS-SME-11 — Registry is the SME catalog, pinned per case (AC-SME-10)

1. The Agent Registry is the reusable catalog for SME identities and profiles.
2. Each consultation pins the exact **registry record revision** and **registry record content SHA-256** it used. Later Registry changes cannot rewrite case history (`TSC-REC-02`).
3. This candidate specifies what a consultation records about the Registry. It implements, migrates, or changes no Registry service.

### TSS-SME-12 — Registration before reuse (AC-SME-11)

A newly created supportive SME is registered before reuse with: identity; provenance; capability scope and non-capability scope; conflict status; allowed tools; budget; lifecycle status; sunset rule; and reuse eligibility. An SME missing any field is not eligible for reuse.

### TSS-SME-13 — Registry discovery never grants authority (AC-SME-12)

1. A Registry row or discovery result is a pointer, never an assignment, authorization, or ruling (`TSC-NOT-01`; Object Dictionary: Registration).
2. Operator approval and exact delegation are separate evidence. A capability row alone cannot authorize an action or a binding ruling.
3. A parent relationship, session, lineage, `permit_id`, or consultation result is context only. It cannot substitute for current accountable work and addressee plus the exact authority a material action requires (working-default package §5.3, §6.2).

### TSS-SME-14 — Non-effect and separate adoption

1. This candidate is not adopted and not effective. It authorizes no action.
2. Adoption is a separate exact-byte operator decision and is not requested or implied here.
3. Review route per the source Feature: Ip Man reviews scope and architecture; Jigoro Kano reviews the actual candidate bytes against adopted governance; Helio Gracie performs the checkpoint. A change to these bytes after review makes the review stale.

## 4. Anti-cycle contract (summary)

| Control | Rule |
|---|---|
| Question lock | TSS-SME-06 |
| Default SME count | one (TSS-SME-07) |
| Correction rounds | one (TSS-SME-08) |
| Terminal outcomes | `PROCEED`, `REWORK`, `BLOCKED`, `UNKNOWN` (TSS-SME-08) |
| Reopen only for | changed fact at a later revision, concrete counter-evidence, reproducible method defect, operator instruction (TSS-SME-09) |
| Dissent | appendable, never silently reopens (TSS-SME-09) |

## 5. Authority separation (summary)

| Fact | Owner | Never substitutes for |
|---|---|---|
| Counsel | SME Statement | Decision, acceptance, closure (TSS-SME-02) |
| Binding ruling | prior protected operator Decision (TSS-SME-04) | an SME's self-claim or Registry row |
| Identity and profile | Registry (TSS-SME-11) | authority (TSS-SME-13) |
| Closure | independent acceptor (TSS-SME-02) | any consultation outcome |
| Operator control | protected control path | any SME or gate |

## 6. Conformance cases (proposed)

| Case | Required result |
|---|---|
| SME asserts a binding result with no prior operator Decision | Counsel only (TSS-SME-02.3, 04.2) |
| Decision names question and scope but no term | Not a delegated ruling (TSS-SME-04.1) |
| Ruling issued, Decision recorded afterwards | Counsel only (TSS-SME-04.2) |
| SME counted as a vote or seat | Rejected (TSS-SME-03) |
| Same question restated in new words, same three hashes | Same case (TSS-SME-06) |
| Second SME requested with no recorded trigger | Not admitted (TSS-SME-07.2) |
| Challenge with no reproducible evidence | Appended, nonblocking (TSS-SME-05) |
| Second correction round without a reopen condition | Not allowed (TSS-SME-08, 09) |
| `PROCEED` recorded, no independent acceptance | Request not `CLOSED` (TSS-SME-02.2, 08.3) |
| Registry row marks an SME "ruling-capable" | No authority (TSS-SME-13.2) |
| Registry record changes after case close | Case history unchanged (TSS-SME-11.2) |
| New SME missing sunset rule or conflict status | Not reusable (TSS-SME-12) |
| Result omits conflict disclosure | Labelled evidence, incomplete (TSS-SME-10) |
| Consultation posted while dependency resolution fails | Append succeeds, no consequential effect (`TSC-ROE-02`) |

## 7. Source-to-rule traceability

| Source criterion | Rule(s) | Charter rule(s) relied on |
|---|---|---|
| AC-SME-02 existing objects, no new primary object | TSS-SME-01 | `TSC-OBJ-01` |
| AC-SME-03 advisory; no fourth seat; delegation needs exact prior authority | TSS-SME-02, 03, 04 | `TSC-REC-01`, `TSC-CTL-01`, `TSC-WRK-02` |
| AC-SME-04 evidenced challenge or refusal | TSS-SME-05 | `TSC-ROE-02` |
| AC-SME-05 question lock | TSS-SME-06 | `TSC-REC-03` |
| AC-SME-06 one SME by default | TSS-SME-07 | process rule |
| AC-SME-07 one correction round; four terminal outcomes | TSS-SME-08 | `TSC-WRK-02`; Lifecycle |
| AC-SME-08 finality and reopen conditions | TSS-SME-09 | `TSC-REC-02` |
| AC-SME-09 SME disclosure | TSS-SME-10 | `TSC-CLM-01` |
| AC-SME-10 Registry catalog and pin | TSS-SME-11 | `TSC-REC-02` |
| AC-SME-11 registration before reuse | TSS-SME-12 | Object Dictionary: Registration |
| AC-SME-12 discovery never grants authority | TSS-SME-13 | `TSC-NOT-01`, `TSC-GATE-01` |

AC-SME-01 and AC-SME-14/15 are met by the file's existence, §1 and §10, and TSS-SME-14. AC-SME-13 (template and pilot) belongs to the sibling Story `F001-TEMPLATE-AND-PILOT` and is not evidenced here.

## 8. Explicit exclusions

No edit to Charter v1.0 or approved-package bytes; no effect without exact-byte operator adoption; no automated SME selection, ranking, scoring, or marketplace; no Registry service implementation, migration, deployment, credential, ACL, or firewall change; no hidden chain-of-thought collection or requirement; no production runtime enforcement or Vertical UI; no recursive supportive-agent spawning; no second SME or extra review layer without a trigger or operator direction; no commit, push, merge, deployment, publication, or activation.

## 9. Open points for reviewers (not operator decisions)

1. **"Tribunal" is undefined** in adopted bytes (§2). A reviewer must name the defining artifact or supply a definition.
2. **Identifiers** `TSS-SME-nn` are placeholders. Final stable identifiers belong to whichever artifact is adopted.
3. **Outcome naming overlap:** `BLOCKED` appears as a consultation outcome and as a Request state. TSS-SME-08.3 separates them. Confirm the separation suffices.
4. **Question-lock hashing** is left to a later binding (TSS-SME-06). Confirm that is acceptable at candidate level.
5. **Relationship to the working-default amendment:** the amendment restates several rules at binding level. Confirm no wording diverges.

## 10. Review route and effort

Ip Man reviews scope and architecture; Jigoro Kano reviews these exact bytes against adopted governance; Helio Gracie performs the delivery checkpoint. Drafting effort and review effort are reported separately; the drafting figure is in the delivery return. Optional review stops before it exceeds drafting effort unless a criterion fails, a reproducible defect is found, or the operator authorizes more (AC-SME-15).
