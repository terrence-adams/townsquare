# Ip Man ratification of TownSquare Doctrine acceptance criteria

**document_id:** TS-GOV-ACD-RATIFICATION-20261006

**version:** 1.0 prerequisite decision artifact

**status:** RATIFIED WORKING ACCEPTANCE CONTRACT — NOT GOVERNANCE AUTHORITY, NOT ADOPTION, NOT A BINDING, NOT CONFORMANCE EVIDENCE

**owner:** Ip Man

**draft owner after this gate:** Jigoro Kano

**source scope:** `docs/townsquare-doctrine-project-scope.md` version 2, `docs/helio-checkpoint-scope-20261006.md`, and the operator decisions supplied with this assignment

**prepared:** 2026-10-06

## 1. Decision and boundary

The AC-D set is ratified with amendments below. It is suitable as the content-readiness contract for Kano's next Doctrine pass only after the exact amended wording in this note replaces the earlier wording for evaluation.

This note has no governing force. It does not:

- adopt or activate the Doctrine, Rules of Engagement, TownSquare governance, any binding, or any manifest;
- alter a candidate governance text;
- accept a storage, wake, cloud, or model implementation;
- authorize Revere, a deployment, a governed write, or a pilot; or
- turn architecture or POC fields into rules.

Only the operator can adopt governance or accept a binding. A deployed service, repository commit, file location, hash, review, or passing test cannot substitute for that decision.

## 2. Decisions this ratification preserves

1. Jigoro Kano owns the Doctrine, Rules of Engagement, and TownSquare governance drafts. Ip Man defines this acceptance contract; he does not write Kano's governance text.
2. The Doctrine must remain true across NAS, Google Cloud, AWS, Azure, another cloud, or a later storage/runtime implementation.
3. TownSquare is the authoritative coordination and record layer. Vertical is a work model/projection. Wonderland is a read-only observation and behavioral-modeling layer. Neither Vertical nor Wonderland can authorize, mutate, block, accept, or replace TownSquare records.
4. A wake mechanism is replaceable infrastructure. Revere may implement the capability, but `Revere` is not a Doctrine literal and is never authoritative.
5. Google Drive is neither authority nor a required review substrate. Existing Drive-derived documents, hashes, posts, or mappings are historical inputs until reconciled into the declared package; their absence cannot block review of an otherwise complete local package.
6. Context and policy receipts can prove which sources were selected and retrieved, which versions/hashes were evaluated, and which policy outcome controlled an action. They cannot prove reading comprehension, agreement, intent, or future obedience.
7. Criterion and rule identities are stable. An identity is never reused for a different requirement; amendment or retirement leaves a traceable tombstone.
8. The 2–4 week pilot starts only after adoption and required binding/conformance acceptance. It gathers evidence; it does not silently amend or adopt governance.
9. The NAS MVP may remain deployed dark. Governed writes fail closed until the required governance is adopted and an accepted active binding can be resolved. This governance track does not delay dark-deployment engineering or health verification.

## 3. Acceptance classes

The class column below uses:

| Code | Meaning |
|---|---|
| `M` | Machine-checkable structure, identity, mapping, scan, or recorded evidence. A machine result does not settle meaning. |
| `J` | Reviewer judgment with a written rationale and cited text. |
| `O` | Explicit operator decision; no reviewer or runtime may infer it. |
| `P` | Evidence gathered during the post-adoption pilot. |

No AC-D criterion depends on pilot evidence. AC-D is the Doctrine-package readiness gate; the pilot is later and separately identified in section 6.

## 4. Ratified AC-D set

The wording in this table is final for Kano pass 5. Earlier AC-D wording remains historical context, not a competing criterion.

| ID | Disposition | Class | Exact ratified wording | Required evidence |
|---|---|---|---|---|
| AC-D1 | Amended | `J` | **Infrastructure-neutral line test.** Every normative rule remains true if the storage system, host, cloud, wake mechanism, model provider, user interface, or implementation service changes. A clause that fails this test belongs in a binding, implementation profile, or historical mapping—not the Doctrine. | Kano records the test result per rule; Eddie independently re-applies it and cites any failure. |
| AC-D2 | Amended | `M+J` | **No infrastructure dependency in normative rule text.** The normative Doctrine may name TownSquare and approved governance roles or objects, but may not depend on a vendor, product implementation, host, path, filename, file extension, protocol adapter, storage engine, deployment unit, or service implementation. The minimum case-insensitive scan covers `Google`, `Drive`, `Google Cloud`, `GCP`, `Azure`, `AWS`, `NAS`, `Docker`, `SQLite`, `rclone`, `Revere`, `Cloud Run`, `Compute Engine`, `GKE`, `Kubernetes`, `S3`, `Crier`, `Registrar`, `Viewer`, `folder`, `filename`, `.txt`, `.md`, drive-letter paths, and absolute slash paths. Commentary, citations, historical inventory, and binding mappings are excluded. Zero hits is necessary but not sufficient; every exception or false positive is recorded. | Reproducible scan command, exact input hash, result, exclusions, and reviewer line-test rationale. |
| AC-D3 | Amended | `M+J` | Every normative rule has a stable rule ID, a stated reason, and one or more traceable sources in Commentary keyed to that ID. Structural completeness is machine-checked; source sufficiency and faithful interpretation are reviewer judgments. | Complete rule-to-reason-to-source map and independent review findings. |
| AC-D4 | Amended | `M+J` | The candidate declares the exact decision-register version or content hash it reviewed and accounts for every decision in that snapshot as carried, deferred, superseded, not applicable, or excluded with a reason. A newer operator decision makes the mapping stale until reconciled. No sampling may support a claim that no ruling was lost. | Full decision-to-rule/disposition matrix, register identity, stale-input check, and reviewer exceptions. |
| AC-D5 | Retained | `J` | The founding text is short, plain, and quotable. It states purpose, authority, relationship to companion documents, conflict interpretation, amendment, and retirement without turning operational procedure into founding law. | Eddie performs a cold read and records ambiguity, missing concepts, and unnecessary operational detail. |
| AC-D6 | Amended | `M+O` | The Doctrine contains an infrastructure-neutral recognition rule. A governance artifact becomes active only through a valid, non-revoked operator adoption decision naming its stable identity, version, and content hash. The package defines the adoption-record format, but the candidate and format do not constitute adoption. | Recognition rule, adoption-record schema/example marked inactive, negative test for missing/revoked/mismatched adoption, and the later operator decision if adopted. |
| AC-D7 | Amended | `M+J` | The governance inventory declares its search manifest and accounts for every discovered in-scope artifact with identity/hash where available, status, proposed fate, and reason. Required live inputs are the declared repository/package sources. Drive-derived materials are classified `HISTORICAL_EXTERNAL_INPUT` or `HISTORICAL_BINDING_EVIDENCE`; Drive access is not required, and no Drive copy is authoritative. | Search manifest, inventory coverage check, historical classifications, unresolved-input list, and reviewer coverage judgment. |
| AC-D8 | Amended | `M+J+O` | Every in-scope amendment input is traceably accounted for. Governance requirements are carried into the Doctrine, Rules of Engagement, or TownSquare governance; implementation-specific material is routed to a binding or implementation profile; rejected, deferred, superseded, and operator-choice items retain reasons. P8 remains an operator choice and is not silently resolved. | Amendment disposition matrix, destination IDs, no-orphan check, reviewer assessment, and explicit operator decision for P8 if the package depends on it. |
| AC-D9 | Amended | `M` | Rule and criterion IDs are unique, stable across versions, and never reassigned. Amendment preserves lineage; retirement creates a tombstone with reason and successor when one exists. Wonderland and other readers cite ID plus adopted version/content hash rather than display text alone. | Uniqueness/lineage check, tombstone registry, and citation examples. |
| AC-D10 | Retained | `M+J` | The Agentic Operating Charter, Bedrock, and Charter 2.0 are mapped for relationship and conflict analysis but are not altered by this package. | Inventory/mapping rows, repository diff proving no edits, and reviewer conflict findings. |
| AC-D11 | Amended | `M+J` | Eddie's independent review is filed with a cited artifact version/hash and evidence for every objection. Kano answers each objection as accepted, rejected with reason, deferred, or dissent recorded. No objection disappears through rewriting. | Review and response records, objection reconciliation table, and final unresolved dissent list. |
| AC-D12 | Retained | `M` | Helio's checkpoint is filed after Kano's response and before the package reaches the operator for adoption. | Checkpoint record citing the exact reviewed package hashes and prior review/response records. |
| AC-D13 | Amended | `M+J` | **Neutrality under another binding.** A second durable-record binding can satisfy the Doctrine without changing any Doctrine rule. The NAS design may serve as a conformance fixture, but no NAS path, product, commit, or design hash is a governance requirement. Exact implementation versions belong only in the binding/conformance evidence. | Abstract binding-requirement matrix applied to at least two implementations or one implementation plus a complete hypothetical substitute; Doctrine diff must be empty. Eddie reviews the result. |
| AC-D14 | Amended | `O+M` | The operator adopts each governance artifact separately and in writing by stable identity, version, and content hash. Doctrine adoption does not accept a durable-record binding, wake binding, runtime implementation, pilot result, or companion document unless the operator decision names it. | Separate operator decisions and mechanical identity/hash verification. Before those decisions, every artifact remains inactive. |
| AC-D15 | Amended | `J` | TownSquare's vendor-neutral records and community workflows are the organizing concepts. The text explains how approved object classes—such as Bulletin, Statement, Request, Decision, Notice, and Receipt—enter, cite, transition, and remain auditable without making a particular UI board, service, or storage layout normative. The object dictionary, not incidental code, controls exact object/state vocabulary. | Eddie traces the founding articles to the candidate object dictionary and identifies any UI/infrastructure coupling or undefined object/state. |
| AC-D16 | Amended | `J+O` | The package recommends canonical placement, issuance, citation, supersession, and mirroring without making a storage substrate authoritative. TownSquare records adoption and authoritative governance events; Vertical may project work/evidence; Wonderland may observe and model read-only. A mirror never becomes authority through location alone. The operator decides final physical placement and issuance configuration. | Boundary/placement recommendation, authority matrix, negative cases, and unresolved operator choice. |
| AC-D17 | Retired | `M` | **Tombstone: Drive-binding completeness is no longer a Doctrine acceptance criterion.** Google Drive is not an authority or required binding. The former Drive binding and its mappings are preserved only as `HISTORICAL_BINDING_EVIDENCE`; useful requirements must be reclassified into the neutral binding contract or another candidate with traceable provenance. AC-D17 is never reused. | Tombstone, historical inventory entry, and requirement-reclassification map with no assertion that Drive must be available or complete. |
| AC-D18 | Amended | `M+J` | **Wake substitutability.** Replacing one compliant wake mechanism with another requires no Doctrine amendment. Normative text names no wake product. It states only that an authorized, replaceable mechanism may alert or start an agent when durable work exists; the mechanism is a pointer, not the record or authority; the agent retrieves the authoritative record and applicable policy before acting; and wake failure never changes the record, authorization, or obligation. | AC-D2 scan, abstract wake-clause review, substitution thought experiment, and mapping to a separate wake binding. |

## 5. Separate acceptance gates

The following stable gate identities prevent a review or deployment artifact from being mistaken for governance authority. The AC-D9 no-reuse/tombstone rule applies to them. They are package/checklist requirements, not text that must be copied verbatim into the Doctrine.

### 5.1 Binding acceptance

| ID | Requirement | Class |
|---|---|---|
| AC-B1 | A binding names the adopted Doctrine identity/version/hash it implements, its capability scope, its implementation/version, and every abstract obligation it maps. It cannot add governance authority. | `M+J` |
| AC-B2 | A durable-record or wake binding is replaceable without a Doctrine edit and documents authority boundaries, failures, recovery, evidence, and migration. A wake binding contains pointers only. | `M+J` |
| AC-B3 | Each binding is accepted separately by the operator. Acceptance names the exact binding hash/version and does not accept the runtime that implements it. | `O+M` |
| AC-B4 | Drive artifacts remain historical evidence. A current binding cannot require Drive availability, Drive review, or a Drive identifier to resolve authority. | `M` |

### 5.2 Implementation conformance

| ID | Requirement | Class |
|---|---|---|
| AC-IC1 | Governed writes fail closed unless the runtime resolves a current, non-revoked operator adoption for the applicable governance artifact and a separately accepted active binding. Missing, stale, ambiguous, or hash-mismatched authority cannot degrade to permissive behavior. | `M` |
| AC-IC2 | Before a governed action, a context/policy receipt records actor and represented authority, action/scope, ordered governing source identities/versions/hashes, retrieval time/result, policy evaluation/result, binding identity, expiry/revocation status, and resulting allow/deny decision. The receipt may assert retrieval, integrity, evaluation, acknowledgement, and declared adherence; it must never assert comprehension, agreement, intent, or guaranteed future compliance. | `M+J` |
| AC-IC3 | TownSquare remains the authoritative record. Vertical consumes references/evidence as a projection/work model. Wonderland consumes a read-only, provenance-preserving observation feed. Neither consumer can authorize, accept, block, close, mutate, or overwrite TownSquare source history. | `M+J` |
| AC-IC4 | Negative tests prove that a wake event, projection field, observer finding, model output, file location, repository state, context receipt, or successful retrieval cannot by itself authorize a governed action or claim operator acceptance. | `M` |
| AC-IC5 | A dark NAS deployment may run migration, health, backup/restore, read-only, and conformance checks, but governed writes remain disabled until AC-IC1 passes. Dark deployment evidence does not adopt governance. | `M` |

Doctrine readiness, binding acceptance, and implementation conformance are independent results. The operator may adopt a Doctrine before accepting a binding; a binding may be technically complete but inactive; and an implementation may conform to a candidate yet still lack authority to write.

## 6. Post-adoption pilot gate

| ID | Requirement | Class |
|---|---|---|
| AC-PILOT1 | The pilot begins only after the operator adopts the applicable governance, accepts the active binding, and accepts sufficient conformance evidence for the named cohort and scope. | `O+M` |
| AC-PILOT2 | The pilot runs for an operator-selected duration within 2–4 weeks and names start/end, owner, cohort, workflows, stop conditions, measures, and evidence location. | `O+P` |
| AC-PILOT3 | Evidence distinguishes rule ambiguity, noncompliance, receipt/retrieval failure, binding failure, implementation defect, wake failure, and observer/model finding. No category silently changes another. | `P+J` |
| AC-PILOT4 | Pilot completion produces a cited report and explicit operator decision to retain, amend, extend, restrict, suspend, or retire. No elapsed time or success metric automatically amends or adopts governance. | `O+P` |

## 7. Vertical POC boundary

The Vertical POC is a work-tracking and migration design, not a governance source. These are not Doctrine, Rules of Engagement, or TownSquare-governance requirements:

- `VR-*`/`poc_ref`, `poc_event_uid`, `poc_thread_uid`, native UUIDv7 mappings, or POC order/hash fields;
- literal `schema_version: "1"` and JSON-string `actor_provenance`;
- `base_event_id`, `expected_head`, `workflow_ref`, `artifact_ref`, or `cites_decision` field names;
- `definition_of_done` JSON shape;
- Epic/Feature/Story labels, `vertical_level`, `parent_ref`, `depends_on_refs`, or ownership metadata; and
- the POC's native event types, lifecycle encodings, migration map, and renderer rules.

Governance may require semantic outcomes such as stable identity, provenance, current evidence, explicit authority, concurrency-safe writes, lifecycle integrity, and authorized acceptance. A binding or integration profile may then map those outcomes to exact Vertical fields. POC metadata never grants authority, and the tracker remains off the NAS MVP/deployment critical path.

## 8. Unresolved operator choices

This ratification does not decide:

1. P8: `MAY`, `SHOULD`, or omit.
2. The final physical placement, mirroring, and issuance configuration for adopted governance, while preserving TownSquare's authority boundary.
3. Which exact durable-record binding/version and wake binding/version to accept after separate review.
4. Whether or when to authorize Revere implementation, installation, settings/hooks, agent reply authority, or unattended spend.
5. Pilot start date, duration within 2–4 weeks, owner, cohort, workflows, measures, thresholds, and stop conditions.
6. The final document partition if Kano recommends additional scoped companions; the ownership boundary remains Kano's.
7. The disposition of unresolved historical inputs that cannot be independently recovered from Drive, beyond classifying them as unavailable historical evidence.

## 9. Kano pass-5 work order

Document · Discuss · Decide remains the gate. Kano owns the governance drafts but cannot adopt them.

WORK ORDER
- Dispatch: coordinating session — send Kano this ratification and the complete pass-5 package as one consolidated brief after confirming his prior report is saved and he is ready; confirm receipt before treating the pass as started.
- Draft Doctrine: Jigoro Kano — produce one infrastructure-neutral founding candidate and Commentary using AC-D1 through AC-D18 exactly as ratified here; preserve stable rule IDs and full decision/amendment mappings.
- Draft companions: Jigoro Kano — own the Rules of Engagement and TownSquare governance candidates; decide the smallest clear document partition and cross-reference stable IDs without duplicating or conflicting rules.
- Durable-record package: Jigoro Kano — replace the Drive-as-current premise with a neutral durable-record binding contract; preserve the former Drive binding/mapping as historical evidence only; do not choose or approve NAS/cloud implementation details.
- Wake package: Jigoro Kano — create the replaceable wake-mechanism binding; keep Doctrine wording abstract; classify the Revere design as a proposed implementation/trial plan under that binding, never as doctrine or authority.
- Evidence and enforcement: Jigoro Kano — specify the abstract context/policy-receipt obligation and fail-closed authority rule without claiming comprehension and without importing implementation field names into governance.
- Complete Helio's package: Jigoro Kano — read Herding Cats in full; perform Night Shift conformance; reconcile the RoE export; recommend the `townsquare-protocol` archive disposition; correct the Wonderland inventory finding; carry forward every open dissent and unavailable historical input.
- Deliver review bundle: Jigoro Kano — provide candidate hashes/versions, inventory, decision and amendment matrices, AC-D result matrix, separate binding candidates, historical Drive tombstone/mapping, unresolved operator choices, and an explicit statement that nothing is adopted or activated.
- Peer review: Eddie Brock — independently review the exact bundle against AC-D, file evidence for each objection, and test infrastructure/wake substitutability and product authority boundaries.
- Security review when applicable: GSP — review authority resolution, receipt claims, fail-closed behavior, identity/role boundaries, and any clause that could allow privilege or policy bypass.
- Coordinate: Helio Gracie — checkpoint after Eddie's review and Kano's recorded response, then present the exact package and unresolved operator decisions at the final gateway.
- Operator: adopt or reject each governance artifact and binding separately; later authorize the named 2–4 week pilot.
- Watch for: Drive returning as authority; Revere appearing in normative Doctrine; Vertical POC fields becoming rules; Wonderland or Vertical becoming a gate; a receipt claiming comprehension; review evidence being mistaken for adoption; or the dark NAS deployment enabling governed writes before accepted authority resolves.

## 10. Alternative rejected

**Rejected:** keep AC-D17 as a live Drive-binding requirement and pin AC-D13 to particular NAS design commits. That would make the acceptance contract depend on two infrastructure snapshots and would contradict the operator's portability and authority decisions. Historical mappings and implementation hashes remain evidence at the binding/conformance layers instead.
