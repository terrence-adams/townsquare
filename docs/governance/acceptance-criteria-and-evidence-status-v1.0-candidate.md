# Governance acceptance criteria and evidence status v1.0 — candidate

**document_id:** `TS-GOV-CRITERIA-STATUS-20261006-CANDIDATE`
**status:** CANDIDATE — REGISTRY NOT YET IMPLEMENTED

## Stable criterion rule

An acceptance criterion is an atomic, observable, falsifiable required outcome. It has stable `criterion_id`, outcome reference, applicability, preconditions, trigger, expected and negative result, evidence method, evaluator, acceptance authority, validity/version, and status. IDs are never reused; change appends a successor/supersession record and identifies stale evidence.

## Current status

| Set | Status | What it proves / does not prove |
|---|---|---|
| AC-D1–AC-D18 | RATIFIED working acceptance contract | pass-5 content readiness, not adoption |
| AC-B1–AC-B4 | ratified binding gate | binding completeness, not binding acceptance |
| AC-IC1–AC-IC5 | ratified conformance requirements | required implementation behavior, not current conformance |
| AC-PILOT1–AC-PILOT4 | post-adoption gate | pilot evidence only after adoption |
| machine-readable registry | NOT CREATED | no criterion can yet be automatically resolved/closed |

Evidence states are `REPORTED`, `VERIFIED`, `STALE`, `SUPERSEDED`, `REVOKED`, or `UNKNOWN`; templates and candidate manifests are never runtime proof. A work item can be resolved only when all applicable criteria have current evidence. It can close only with an independent authorized acceptance decision that cites those criterion versions and evidence. The future registry is a shared-contract implementation item, not a prerequisite for dark MVP health validation.
