# TownSquare governance adoption package v1.0 — inactive template

**document_id:** `TS-ADOPTION-PACKAGE-20261006-TEMPLATE`
**status:** TEMPLATE — NOT AN ADOPTION — NOT EFFECTIVE

## Operator decision template

```text
I, [protected operator identity], decide [ADOPT|SUPERSEDE|WITHDRAW].
Artifact: [document_id]
Version: [version]
Exact SHA-256: [byte hash]
Scope: [specific governed actions/objects]
Effective from/until: [time|null]
Supersedes/withdraws: [adoption event|null]
Reason: [operator words or immutable reference]
Authority method/reference: [protected operator decision record]
```

One record adopts one artifact. Doctrine adoption does not adopt a companion, binding, runtime, deployment, pilot, or production release. A post, commit, test, review, package, or template field does not fill this template.

## Required package checklist

1. Exact byte hashes for each proposed artifact, computed independently of its self-declared metadata.
2. Eddie Brock independent review, cited against those hashes, with every objection retained.
3. Kano disposition of each objection: accepted, rejected with reason, deferred, or dissent retained.
4. Helio checkpoint naming the reviewed hashes and unresolved items.
5. Separate decision for each candidate artifact and, later, each binding.
6. Resolver/QA evidence for the adoption predicate before ordinary governed writes are enabled.

## Operator choices still open

- P8 provenance force (`MAY`, `SHOULD`, or omit).
- Physical issuance/mirroring configuration.
- Exact durable-record and wake bindings to accept.
- Pilot cohort, dates, duration, measures, thresholds, and stop conditions.
- Whether/when any runtime is activated for governed writes.
