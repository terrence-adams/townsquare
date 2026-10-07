# Adopted Authority Resolution v0.2 — candidate amendment

**document_id:** `TS-ADOPTION-RESOLUTION-0.2-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT EFFECTIVE
**relationship:** replaces v0.1 only if separately adopted

This amendment retains v0.1's authority-source and fail-closed rules, and adds the following mandatory predicate before an ordinary consequential action can be effective.

For each governing artifact and binding dependency named by the selected governance set, the resolver independently verifies: stable identity, version, exact-byte digest, scope, active adoption, current effective window, no revocation/supersession for that scope, and any required acceptance. A manifest adoption does not adopt its members. A missing, unadopted, wrong-digest, expired, revoked, out-of-scope, conflicting, or unaccepted member returns `NOT_EFFECTIVE`; undecidable current status returns `UNKNOWN`. Both outcomes prevent the ordinary consequential action and record the failed dependency.

Before ordinary adoption resolution exists, the protected attributable operator-control path remains available for stop, question, override, accept, resume, direction, bootstrap, recovery, and authority change. It is independently authenticated and audited; an agent assertion cannot invoke it. Reads and append-only correction, dispute, escalation, and failure reporting remain available. This is not permission to activate a candidate.

Minimum additional cases: (1) adopted manifest with an unadopted companion → `NOT_EFFECTIVE`; (2) adopted manifest with a revoked binding → `NOT_EFFECTIVE`; (3) valid member with wrong scope/digest → `NOT_EFFECTIVE`; (4) current dependency status unavailable → `UNKNOWN`; (5) operator recovery or authority-change control before bootstrap → succeeds through protected path and is audited; (6) agent-supplied control claim → rejected and audited.
