# Cable agent Vertical story gate — operator directive 2026-10-08

## Status and scope

This is an operator-directed operating rule for work performed by agents on Cable. It applies to implementation, investigation, design, review, testing, and operational changes. It is a Cable workflow control for the current Vertical proof of concept; it is not a Charter amendment and does not claim that the POC tracker is a native enforcement engine.

The operator directed:

> No work should be done or operated or conceived of unless it has a matching approved story as part of the vertical process going forward. I think we should adopt that with the cable agent as well.

## Admission rule

Before an agent on Cable begins work, all of the following must be true:

1. A matching Feature or Story exists in the Vertical record with a stable `VR-*` reference.
2. The latest valid event places the item in `WORKING`.
3. The record names the accountable work, the assigned fulfillment agent or host, the bounded goal, definition of done, evidence requirement, and review owner.
4. The story carries an attributable approval basis from the operator or an authority the operator delegated for that work.
5. The agent retrieves the current story and applicable adopted governance before acting, then cites the `VR-*` reference in its implementation plan, commits, evidence, and status reports.

If any condition is absent, the agent does not investigate, design, implement, review, test, or operate the proposed work. It may report the missing story or record a concise intake proposal for approval; that report is not authorization to perform the proposed work.

## Scope control

- Work is limited to the approved story's goal, definition of done, files or systems, and evidence requirements.
- A finding outside the story may be reported once. It receives no analysis, recommendation, design, fix, or follow-on execution until a separate approved story assigns that work.
- Optional improvements, hardening, cleanup, and framework expansion require their own approved story when they are not necessary to satisfy the current definition of done.
- The assigned agent may produce a completion claim and evidence. It may not approve or close its own work.
- Operator stop, correction, override, and direction remain controlling. The story record captures that direction; it does not reinterpret or gate the operator.

## Current authorized Cable work

`VR-20261008-townsquare-181` is the current approved Story for Cable: deliver a read-only Cable host client for the NAS TownSquare canary and prove cross-host retrieval. Its latest state is `WORKING`; fulfillment is assigned to `Cable / Sentinel One`; review is assigned to `Eddie Brock / independent QA`; operator acceptance remains with the operator.

No adjacent TownSquare, NAS, authentication, writer, wake, governance, deployment, Wonderland, Riviera, or general host work is admitted under `VR-20261008-townsquare-181`.

## Supporting adopted rules

- `TSC-ROE-01`: retrieve current record, adopted governance, dependencies, scope, criteria, and evidence before consequential action.
- `TSC-WRK-01`: keep accountable work, current addressee, and criteria explicit.
- `TSC-WRK-02` and `TSC-ROE-05`: require evidence-backed completion and independent acceptance.
- `TSC-CTL-01` and `TSC-ROE-06`: preserve attributable operator control.

