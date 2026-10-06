-- Retire the pre-release embedded Registry authority without destroying any
-- staged data. These renamed tables are immutable legacy evidence only; the
-- Registry owns current roster state, mutation history, and delivery outbox
-- in its independent database. New ledger code never reads or writes them.
ALTER TABLE registry_agents RENAME TO legacy_embedded_registry_agents;
ALTER TABLE registry_events RENAME TO legacy_embedded_registry_events;
ALTER TABLE registry_outbox RENAME TO legacy_embedded_registry_outbox;

ALTER TABLE registry_audit_events ADD COLUMN authenticated_principal TEXT;
ALTER TABLE context_receipt_issues ADD COLUMN receipt_hash_key_id TEXT;
ALTER TABLE governance_resolution_audit ADD COLUMN resolver_key_id TEXT;
ALTER TABLE governance_resolution_audit ADD COLUMN authority_sequence INTEGER;
ALTER TABLE governance_resolution_audit ADD COLUMN authority_watermark INTEGER;
