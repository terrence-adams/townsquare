-- Context, operator control, logical archive, and Registry audit contracts.
CREATE TABLE auth_credentials(
  credential_id TEXT PRIMARY KEY,
  principal TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  authorization_policy_version TEXT NOT NULL,
  issued_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE TABLE credential_revocations(
  revocation_id TEXT PRIMARY KEY,
  credential_id TEXT NOT NULL REFERENCES auth_credentials(credential_id) ON DELETE RESTRICT,
  reason TEXT NOT NULL,
  revoked_by TEXT NOT NULL,
  revoked_at TEXT NOT NULL
);

CREATE TABLE delegation_grants(
  grant_id TEXT PRIMARY KEY,
  delegator TEXT NOT NULL,
  delegate_principal TEXT NOT NULL,
  represented_actor TEXT NOT NULL,
  permitted_actions_json TEXT NOT NULL,
  target_scope_json TEXT NOT NULL,
  issued_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);

CREATE TABLE delegation_revocations(
  revocation_id TEXT PRIMARY KEY,
  grant_id TEXT NOT NULL REFERENCES delegation_grants(grant_id) ON DELETE RESTRICT,
  reason TEXT NOT NULL,
  revoked_by TEXT NOT NULL,
  revoked_at TEXT NOT NULL
);

CREATE TABLE context_bundles(
  bundle_id TEXT PRIMARY KEY,
  principal TEXT NOT NULL,
  permitted_action TEXT NOT NULL,
  target_thread TEXT NOT NULL,
  expected_revision TEXT NOT NULL,
  manifest_id TEXT NOT NULL,
  manifest_sha256 TEXT NOT NULL CHECK(length(manifest_sha256) = 64),
  bundle_sha256 TEXT NOT NULL CHECK(length(bundle_sha256) = 64),
  required_item_hashes_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE context_receipt_issues(
  receipt_id TEXT PRIMARY KEY,
  token_hash TEXT NOT NULL UNIQUE CHECK(length(token_hash) = 64),
  principal TEXT NOT NULL,
  permitted_action TEXT NOT NULL,
  target_thread TEXT NOT NULL,
  expected_revision TEXT NOT NULL,
  manifest_id TEXT NOT NULL,
  manifest_sha256 TEXT NOT NULL CHECK(length(manifest_sha256) = 64),
  bundle_id TEXT NOT NULL REFERENCES context_bundles(bundle_id) ON DELETE RESTRICT,
  bundle_sha256 TEXT NOT NULL CHECK(length(bundle_sha256) = 64),
  required_item_hashes_json TEXT NOT NULL,
  required_items_sha256 TEXT NOT NULL CHECK(length(required_items_sha256) = 64),
  issued_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  ttl_seconds INTEGER NOT NULL CHECK(ttl_seconds BETWEEN 1 AND 900)
);

CREATE TABLE context_receipt_consumptions(
  receipt_id TEXT PRIMARY KEY REFERENCES context_receipt_issues(receipt_id) ON DELETE RESTRICT,
  native_request_principal TEXT NOT NULL,
  native_request_operation TEXT NOT NULL,
  native_request_key TEXT NOT NULL,
  resulting_event_id TEXT NOT NULL REFERENCES ledger_events(event_id) ON DELETE RESTRICT,
  consumed_at TEXT NOT NULL,
  UNIQUE(native_request_principal, native_request_operation, native_request_key),
  FOREIGN KEY(native_request_principal, native_request_operation, native_request_key)
    REFERENCES native_requests(principal, operation, idempotency_key)
    ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE context_audit(
  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  principal TEXT NOT NULL,
  bundle_id TEXT,
  receipt_id TEXT,
  target_thread TEXT,
  detail_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE control_events(
  control_seq INTEGER PRIMARY KEY AUTOINCREMENT,
  generation INTEGER NOT NULL UNIQUE CHECK(generation >= 1),
  state TEXT NOT NULL CHECK(state IN ('STOPPED','RESUMED')),
  operator_principal TEXT NOT NULL,
  reason TEXT NOT NULL,
  event_id TEXT NOT NULL UNIQUE,
  committed_at TEXT NOT NULL
);

CREATE TABLE logical_archives(
  thread_id TEXT PRIMARY KEY,
  archive_event_id TEXT NOT NULL UNIQUE,
  reason TEXT NOT NULL,
  actor TEXT NOT NULL,
  archived_at TEXT NOT NULL
);

CREATE TABLE registry_agents(
  agent_id TEXT PRIMARY KEY,
  status TEXT NOT NULL CHECK(status IN ('active','retired')),
  record_json TEXT NOT NULL,
  updated_event_uuid TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE registry_events(
  event_uuid TEXT PRIMARY KEY,
  operation TEXT NOT NULL CHECK(operation IN ('register','retire')),
  agent_id TEXT NOT NULL,
  principal TEXT NOT NULL,
  canonical_payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE registry_outbox(
  event_uuid TEXT PRIMARY KEY REFERENCES registry_events(event_uuid) ON DELETE RESTRICT,
  canonical_payload TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256) = 64),
  created_at TEXT NOT NULL
);

CREATE TABLE registry_audit_events(
  audit_seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_uuid TEXT NOT NULL UNIQUE,
  actor TEXT NOT NULL CHECK(actor = 'registry'),
  board TEXT NOT NULL CHECK(board = 'BOARD-AUDIT-RECORD'),
  canonical_payload TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256) = 64),
  created_at TEXT NOT NULL
);

CREATE TABLE projection_dependencies(
  dependency TEXT PRIMARY KEY,
  available INTEGER NOT NULL CHECK(available IN (0,1)),
  detail TEXT NOT NULL,
  checked_at TEXT NOT NULL
);

CREATE INDEX idx_context_receipts_principal ON context_receipt_issues(principal, target_thread, expected_revision);
CREATE INDEX idx_context_audit_kind ON context_audit(kind, audit_id);
CREATE INDEX idx_registry_events_agent ON registry_events(agent_id, created_at);

CREATE TRIGGER auth_credentials_no_update BEFORE UPDATE ON auth_credentials BEGIN SELECT RAISE(ABORT,'immutable auth credential'); END;
CREATE TRIGGER auth_credentials_no_delete BEFORE DELETE ON auth_credentials BEGIN SELECT RAISE(ABORT,'immutable auth credential'); END;
CREATE TRIGGER credential_revocations_no_update BEFORE UPDATE ON credential_revocations BEGIN SELECT RAISE(ABORT,'immutable credential revocation'); END;
CREATE TRIGGER credential_revocations_no_delete BEFORE DELETE ON credential_revocations BEGIN SELECT RAISE(ABORT,'immutable credential revocation'); END;
CREATE TRIGGER delegation_grants_no_update BEFORE UPDATE ON delegation_grants BEGIN SELECT RAISE(ABORT,'immutable delegation grant'); END;
CREATE TRIGGER delegation_grants_no_delete BEFORE DELETE ON delegation_grants BEGIN SELECT RAISE(ABORT,'immutable delegation grant'); END;
CREATE TRIGGER delegation_revocations_no_update BEFORE UPDATE ON delegation_revocations BEGIN SELECT RAISE(ABORT,'immutable delegation revocation'); END;
CREATE TRIGGER delegation_revocations_no_delete BEFORE DELETE ON delegation_revocations BEGIN SELECT RAISE(ABORT,'immutable delegation revocation'); END;
CREATE TRIGGER context_bundles_no_update BEFORE UPDATE ON context_bundles BEGIN SELECT RAISE(ABORT,'immutable context bundle'); END;
CREATE TRIGGER context_bundles_no_delete BEFORE DELETE ON context_bundles BEGIN SELECT RAISE(ABORT,'immutable context bundle'); END;
CREATE TRIGGER context_receipt_issues_no_update BEFORE UPDATE ON context_receipt_issues BEGIN SELECT RAISE(ABORT,'immutable context receipt'); END;
CREATE TRIGGER context_receipt_issues_no_delete BEFORE DELETE ON context_receipt_issues BEGIN SELECT RAISE(ABORT,'immutable context receipt'); END;
CREATE TRIGGER context_receipt_consumptions_no_update BEFORE UPDATE ON context_receipt_consumptions BEGIN SELECT RAISE(ABORT,'immutable context consumption'); END;
CREATE TRIGGER context_receipt_consumptions_no_delete BEFORE DELETE ON context_receipt_consumptions BEGIN SELECT RAISE(ABORT,'immutable context consumption'); END;
CREATE TRIGGER context_audit_no_update BEFORE UPDATE ON context_audit BEGIN SELECT RAISE(ABORT,'immutable context audit'); END;
CREATE TRIGGER context_audit_no_delete BEFORE DELETE ON context_audit BEGIN SELECT RAISE(ABORT,'immutable context audit'); END;
CREATE TRIGGER control_events_no_update BEFORE UPDATE ON control_events BEGIN SELECT RAISE(ABORT,'immutable control event'); END;
CREATE TRIGGER control_events_no_delete BEFORE DELETE ON control_events BEGIN SELECT RAISE(ABORT,'immutable control event'); END;
CREATE TRIGGER logical_archives_no_update BEFORE UPDATE ON logical_archives BEGIN SELECT RAISE(ABORT,'immutable logical archive'); END;
CREATE TRIGGER logical_archives_no_delete BEFORE DELETE ON logical_archives BEGIN SELECT RAISE(ABORT,'immutable logical archive'); END;
CREATE TRIGGER registry_events_no_update BEFORE UPDATE ON registry_events BEGIN SELECT RAISE(ABORT,'immutable registry event'); END;
CREATE TRIGGER registry_events_no_delete BEFORE DELETE ON registry_events BEGIN SELECT RAISE(ABORT,'immutable registry event'); END;
CREATE TRIGGER registry_outbox_no_update BEFORE UPDATE ON registry_outbox BEGIN SELECT RAISE(ABORT,'immutable registry outbox'); END;
CREATE TRIGGER registry_outbox_no_delete BEFORE DELETE ON registry_outbox BEGIN SELECT RAISE(ABORT,'immutable registry outbox'); END;
CREATE TRIGGER registry_audit_events_no_update BEFORE UPDATE ON registry_audit_events BEGIN SELECT RAISE(ABORT,'immutable registry audit'); END;
CREATE TRIGGER registry_audit_events_no_delete BEFORE DELETE ON registry_audit_events BEGIN SELECT RAISE(ABORT,'immutable registry audit'); END;
