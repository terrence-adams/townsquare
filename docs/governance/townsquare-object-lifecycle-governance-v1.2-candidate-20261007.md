# TownSquare Object and Lifecycle Governance v1.2 — candidate

**document_id:** `TS-OBJECT-LIFECYCLE-1.2-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT IN FORCE

This succeeds v1.1 only on separate adoption. Its vocabulary and transitions remain as v1.1 except the following acceptance control is mandatory.

## Independent closure authorization predicate

Before a `RESOLVED → CLOSED` effect commits, an independent resolver MUST establish all of: (1) authenticated actor identity; (2) represented authority, if any; (3) non-revoked role/delegation assignment; (4) scope covering `accept`; (5) exact Request identity and current revision; (6) the cited acceptance Decision identity; and (7) acceptor exclusion from the full authorship set. The assignment is independently resolved, not supplied by the actor or receipt.

`EFFECTIVE` requires every predicate true. `NOT_EFFECTIVE` or `UNKNOWN`, including stale, revoked, missing, mismatched, or unverifiable authorization, denies or parks the `CLOSED` effect, records a reason and correlation, and preserves an append-only correction, dispute, escalation, or failure report. Receipt presence never authorizes closure. Protected operator control follows its separate contract.

| Case | Result |
|---|---|
| authorized independent acceptor, current revision, complete evidence | `CLOSED` effect may commit |
| coauthor, delegated coauthor, or authorship identity mismatch | deny/park effect; append remains available |
| role assignment revoked, out of scope, or wrong action/revision | deny effect; audit |
| assignment status cannot be resolved | park effect; audit |
