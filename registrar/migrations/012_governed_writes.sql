-- Additive evidence for governed context selection/retrieval, external
-- authority resolution, continuation links, and context-gated archives.
CREATE TABLE context_bundle_items(
  bundle_id TEXT NOT NULL REFERENCES context_bundles(bundle_id) ON DELETE RESTRICT,
  item_id TEXT NOT NULL,
  ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
  ref TEXT NOT NULL,
  source TEXT NOT NULL CHECK(source IN ('governance','operator_note','thread','scope','acceptance_criterion')),
  content_json TEXT NOT NULL,
  content_sha256 TEXT NOT NULL CHECK(length(content_sha256) = 64),
  PRIMARY KEY(bundle_id,item_id),
  UNIQUE(bundle_id,content_sha256)
);

CREATE TABLE governance_resolution_audit(
  resolution_id TEXT PRIMARY KEY,
  native_request_principal TEXT NOT NULL,
  native_request_operation TEXT NOT NULL,
  native_request_key TEXT NOT NULL,
  action_capability TEXT NOT NULL,
  target_thread TEXT NOT NULL,
  manifest_id TEXT,
  manifest_sha256 TEXT,
  authority_ref TEXT,
  authority_digest TEXT,
  disposition TEXT NOT NULL CHECK(disposition IN ('EFFECTIVE','NOT_EFFECTIVE','UNKNOWN')),
  reason_code TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  resolved_at TEXT NOT NULL
);

CREATE TABLE thread_continuations(
  new_thread_id TEXT PRIMARY KEY,
  predecessor_thread_id TEXT NOT NULL,
  relation TEXT NOT NULL CHECK(relation = 'continues'),
  opening_event_id TEXT NOT NULL UNIQUE REFERENCES ledger_events(event_id) ON DELETE RESTRICT,
  created_at TEXT NOT NULL
);

CREATE TABLE archive_requests(
  thread_id TEXT PRIMARY KEY REFERENCES logical_archives(thread_id) ON DELETE RESTRICT,
  receipt_id TEXT NOT NULL UNIQUE REFERENCES context_receipt_issues(receipt_id) ON DELETE RESTRICT,
  principal TEXT NOT NULL,
  request_sha256 TEXT NOT NULL CHECK(length(request_sha256) = 64),
  created_at TEXT NOT NULL
);

CREATE INDEX idx_context_bundle_items_hash ON context_bundle_items(bundle_id,content_sha256);
CREATE INDEX idx_governance_resolution_request ON governance_resolution_audit(native_request_principal,native_request_operation,native_request_key);
CREATE INDEX idx_thread_continuations_predecessor ON thread_continuations(predecessor_thread_id);

CREATE TRIGGER context_bundle_items_no_update BEFORE UPDATE ON context_bundle_items BEGIN SELECT RAISE(ABORT,'immutable context bundle item'); END;
CREATE TRIGGER context_bundle_items_no_delete BEFORE DELETE ON context_bundle_items BEGIN SELECT RAISE(ABORT,'immutable context bundle item'); END;
CREATE TRIGGER governance_resolution_audit_no_update BEFORE UPDATE ON governance_resolution_audit BEGIN SELECT RAISE(ABORT,'immutable governance resolution'); END;
CREATE TRIGGER governance_resolution_audit_no_delete BEFORE DELETE ON governance_resolution_audit BEGIN SELECT RAISE(ABORT,'immutable governance resolution'); END;
CREATE TRIGGER thread_continuations_no_update BEFORE UPDATE ON thread_continuations BEGIN SELECT RAISE(ABORT,'immutable continuation'); END;
CREATE TRIGGER thread_continuations_no_delete BEFORE DELETE ON thread_continuations BEGIN SELECT RAISE(ABORT,'immutable continuation'); END;
CREATE TRIGGER archive_requests_no_update BEFORE UPDATE ON archive_requests BEGIN SELECT RAISE(ABORT,'immutable archive request'); END;
CREATE TRIGGER archive_requests_no_delete BEFORE DELETE ON archive_requests BEGIN SELECT RAISE(ABORT,'immutable archive request'); END;
