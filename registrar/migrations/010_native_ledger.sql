-- Additive native-ledger authority. Existing roots/posts remain untouched and
-- continue to represent the historical/legacy compatibility projection.
CREATE TABLE ledger_events(
  ledger_seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  thread_id TEXT NOT NULL,
  thread_ordinal INTEGER NOT NULL CHECK(thread_ordinal >= 0),
  post_uid TEXT REFERENCES posts(post_uid) ON DELETE RESTRICT,
  predecessor_event_id TEXT REFERENCES ledger_events(event_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
  predecessor_commit_sha256 TEXT,
  kind TEXT NOT NULL,
  state TEXT NOT NULL,
  owner TEXT,
  addressee TEXT,
  sensitivity TEXT NOT NULL CHECK(sensitivity IN ('INTERNAL','RESTRICTED')),
  metadata_json TEXT NOT NULL,
  metadata_sha256 TEXT NOT NULL CHECK(length(metadata_sha256) = 64),
  body_sha256 TEXT NOT NULL CHECK(length(body_sha256) = 64),
  body_byte_length INTEGER NOT NULL CHECK(body_byte_length >= 0),
  principal TEXT NOT NULL,
  represented_actor TEXT NOT NULL,
  claimed_origin TEXT NOT NULL,
  authority_scope TEXT NOT NULL,
  committed_at TEXT NOT NULL,
  commit_sha256 TEXT NOT NULL UNIQUE CHECK(length(commit_sha256) = 64),
  UNIQUE(thread_id, thread_ordinal),
  FOREIGN KEY(event_id, body_sha256, body_byte_length)
    REFERENCES event_content(event_id, content_sha256, content_byte_length)
    ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE event_content(
  event_id TEXT PRIMARY KEY,
  content TEXT NOT NULL,
  media_type TEXT NOT NULL,
  content_byte_length INTEGER NOT NULL CHECK(content_byte_length >= 0),
  content_sha256 TEXT NOT NULL CHECK(length(content_sha256) = 64),
  UNIQUE(event_id, content_sha256, content_byte_length),
  FOREIGN KEY(event_id) REFERENCES ledger_events(event_id)
    ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE native_requests(
  principal TEXT NOT NULL,
  operation TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  canonical_request_sha256 TEXT NOT NULL CHECK(length(canonical_request_sha256) = 64),
  event_id TEXT NOT NULL REFERENCES ledger_events(event_id) ON DELETE RESTRICT,
  ledger_seq INTEGER NOT NULL REFERENCES ledger_events(ledger_seq) ON DELETE RESTRICT,
  response_status INTEGER NOT NULL,
  response_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(principal, operation, idempotency_key)
);

CREATE TABLE notice_intents(
  notice_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE REFERENCES ledger_events(event_id) ON DELETE RESTRICT,
  ledger_seq INTEGER NOT NULL REFERENCES ledger_events(ledger_seq) ON DELETE RESTRICT,
  eligible INTEGER NOT NULL CHECK(eligible IN (0,1)),
  destination TEXT,
  adapter_profile TEXT NOT NULL,
  pointer_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE notice_attempts(
  attempt_id TEXT PRIMARY KEY,
  notice_id TEXT NOT NULL REFERENCES notice_intents(notice_id) ON DELETE RESTRICT,
  attempt_number INTEGER NOT NULL CHECK(attempt_number >= 1),
  adapter TEXT NOT NULL,
  attempted_at TEXT NOT NULL,
  outcome TEXT NOT NULL,
  error_detail TEXT,
  transport_receipt TEXT,
  UNIQUE(notice_id, attempt_number)
);

CREATE TABLE ledger_audit(
  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL REFERENCES ledger_events(event_id) ON DELETE RESTRICT,
  principal TEXT NOT NULL,
  operation TEXT NOT NULL,
  detail_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_ledger_events_thread ON ledger_events(thread_id, thread_ordinal);
CREATE INDEX idx_ledger_events_sequence ON ledger_events(ledger_seq);
CREATE INDEX idx_notice_attempts_notice ON notice_attempts(notice_id, attempt_number);

CREATE TRIGGER ledger_events_no_update BEFORE UPDATE ON ledger_events BEGIN SELECT RAISE(ABORT,'immutable ledger event'); END;
CREATE TRIGGER ledger_events_no_delete BEFORE DELETE ON ledger_events BEGIN SELECT RAISE(ABORT,'immutable ledger event'); END;
CREATE TRIGGER event_content_no_update BEFORE UPDATE ON event_content BEGIN SELECT RAISE(ABORT,'immutable event content'); END;
CREATE TRIGGER event_content_no_delete BEFORE DELETE ON event_content BEGIN SELECT RAISE(ABORT,'immutable event content'); END;
CREATE TRIGGER native_requests_no_update BEFORE UPDATE ON native_requests BEGIN SELECT RAISE(ABORT,'immutable native request'); END;
CREATE TRIGGER native_requests_no_delete BEFORE DELETE ON native_requests BEGIN SELECT RAISE(ABORT,'immutable native request'); END;
CREATE TRIGGER notice_intents_no_update BEFORE UPDATE ON notice_intents BEGIN SELECT RAISE(ABORT,'immutable notice intent'); END;
CREATE TRIGGER notice_intents_no_delete BEFORE DELETE ON notice_intents BEGIN SELECT RAISE(ABORT,'immutable notice intent'); END;
CREATE TRIGGER notice_attempts_no_update BEFORE UPDATE ON notice_attempts BEGIN SELECT RAISE(ABORT,'immutable notice attempt'); END;
CREATE TRIGGER notice_attempts_no_delete BEFORE DELETE ON notice_attempts BEGIN SELECT RAISE(ABORT,'immutable notice attempt'); END;
CREATE TRIGGER ledger_audit_no_update BEFORE UPDATE ON ledger_audit BEGIN SELECT RAISE(ABORT,'immutable ledger audit'); END;
CREATE TRIGGER ledger_audit_no_delete BEFORE DELETE ON ledger_audit BEGIN SELECT RAISE(ABORT,'immutable ledger audit'); END;
CREATE TRIGGER native_post_index_no_update BEFORE UPDATE ON posts
  WHEN EXISTS(SELECT 1 FROM ledger_events WHERE post_uid=OLD.post_uid)
  BEGIN SELECT RAISE(ABORT,'native committed post index is immutable'); END;
CREATE TRIGGER native_post_index_no_delete BEFORE DELETE ON posts
  WHEN EXISTS(SELECT 1 FROM ledger_events WHERE post_uid=OLD.post_uid)
  BEGIN SELECT RAISE(ABORT,'native committed post index is immutable'); END;
