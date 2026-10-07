# Protected Operator Control Contract v0.1 — candidate

**document_id:** `TS-PROTECTED-CONTROL-0.1-CANDIDATE-20261007`
**status:** CANDIDATE — NOT ADOPTED — NOT EFFECTIVE

The protected path serves stop, question, override, accept, resume, direction, bootstrap, recovery, and authority-change controls. It is implementation-neutral.

The binding MUST independently resolve a current trust anchor, operator-role assignment, authenticated actor, exact control action, scope/target, issued/evaluated/expiry time, nonce or equivalent anti-replay value, and audit sink integrity. It verifies every value before effect; client fields and agent assertions never establish them. Missing, expired, replayed, revoked, mismatched, or unverifiable material fails closed for the asserted control effect and emits durable failure evidence without exposing secrets. The operator’s legitimate control is never routed through an ordinary gate.

Required tests: valid in-scope operator stop/control; agent-supplied operator claim; revoked role; action/scope mismatch; expired/replayed nonce; audit-sink failure; and recovery/bootstrap control while ordinary resolution is unavailable. Each test distinguishes denial of a forged effect from suppression of append-only failure reporting.
