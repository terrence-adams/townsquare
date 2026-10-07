# TownSquare Charter v1.0 — Protected Operator Control

**document_id:** `TS-CHARTER-1.0-PROTECTED-CONTROL`
**charter_release:** `TS-CHARTER-1.0`
**status:** FINAL RELEASE BYTES — effective only through a separate attributable protected operator adoption record
**scope:** TownSquare governance

The protected path serves stop, question, override, accept, resume, direction, bootstrap, recovery, and authority-change controls. It is implementation-neutral.

The binding MUST independently resolve a current trust anchor, operator-role assignment, authenticated actor, exact control action, scope/target, issued/evaluated/expiry time, nonce or equivalent anti-replay value, and audit sink integrity. It verifies every value before effect; client fields and agent assertions never establish them. Missing, expired, replayed, revoked, mismatched, or unverifiable material fails closed for the asserted control effect and emits durable failure evidence without exposing secrets. The operator’s legitimate control is never routed through an ordinary gate.

Required tests: valid in-scope operator stop/control; agent-supplied operator claim; revoked role; action/scope mismatch; expired/replayed nonce; audit-sink failure; and recovery/bootstrap control while ordinary resolution is unavailable. Each test distinguishes denial of a forged effect from suppression of append-only failure reporting.
