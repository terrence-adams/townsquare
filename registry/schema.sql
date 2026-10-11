CREATE TABLE registry_migrations(version INTEGER PRIMARY KEY, applied_utc TEXT NOT NULL);
CREATE TABLE agents(agent_id TEXT PRIMARY KEY, body_json TEXT NOT NULL, revision INTEGER NOT NULL, active INTEGER NOT NULL, updated_utc TEXT NOT NULL);
CREATE TABLE requests(principal TEXT NOT NULL, idem_key TEXT NOT NULL, request_hash TEXT NOT NULL, response_json TEXT NOT NULL, PRIMARY KEY(principal,idem_key));
CREATE TABLE journal(seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL, agent_id TEXT NOT NULL, action TEXT NOT NULL, body_json TEXT NOT NULL, committed_utc TEXT NOT NULL);
CREATE TABLE audit_outbox(event_id TEXT PRIMARY KEY REFERENCES journal(event_id), attempts INTEGER NOT NULL DEFAULT 0, delivered_utc TEXT, last_error TEXT);
INSERT INTO registry_migrations VALUES(1,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
ALTER TABLE audit_outbox ADD COLUMN lease_owner TEXT;
ALTER TABLE audit_outbox ADD COLUMN lease_until TEXT;
CREATE TRIGGER journal_no_update BEFORE UPDATE ON journal BEGIN SELECT RAISE(ABORT,'journal is append-only'); END;
CREATE TRIGGER journal_no_delete BEFORE DELETE ON journal BEGIN SELECT RAISE(ABORT,'journal is append-only'); END;
CREATE TRIGGER audit_outbox_no_delete BEFORE DELETE ON audit_outbox BEGIN SELECT RAISE(ABORT,'outbox is append-only'); END;
CREATE TRIGGER audit_outbox_delivered_immutable BEFORE UPDATE ON audit_outbox WHEN OLD.delivered_utc IS NOT NULL BEGIN SELECT RAISE(ABORT,'delivered outbox is immutable'); END;
CREATE TRIGGER audit_outbox_transition_guard BEFORE UPDATE ON audit_outbox WHEN NOT (
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NULL AND OLD.lease_until IS NULL AND NEW.delivered_utc IS NULL AND NEW.lease_owner IS NOT NULL AND NEW.lease_until IS NOT NULL AND NEW.attempts=OLD.attempts AND NEW.last_error IS OLD.last_error)
  OR
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NOT NULL AND OLD.lease_until IS NOT NULL AND NEW.delivered_utc IS NULL AND NEW.lease_owner IS NOT NULL AND NEW.lease_until IS NOT NULL AND NEW.attempts=OLD.attempts AND NEW.last_error IS OLD.last_error)
  OR
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NOT NULL AND OLD.lease_until IS NOT NULL AND NEW.delivered_utc IS NOT NULL AND NEW.lease_owner IS NULL AND NEW.lease_until IS NULL AND NEW.attempts=OLD.attempts+1 AND NEW.last_error IS NULL)
  OR
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NOT NULL AND OLD.lease_until IS NOT NULL AND NEW.delivered_utc IS NULL AND NEW.lease_owner IS NULL AND NEW.lease_until IS NULL AND NEW.attempts=OLD.attempts+1 AND NEW.last_error IS NOT NULL)
) BEGIN SELECT RAISE(ABORT,'illegal outbox state transition'); END;
CREATE TRIGGER audit_outbox_lease_guard BEFORE UPDATE OF lease_owner,lease_until ON audit_outbox WHEN NEW.delivered_utc IS NOT NULL AND (NEW.lease_owner IS NOT NULL OR NEW.lease_until IS NOT NULL) BEGIN SELECT RAISE(ABORT,'delivered outbox cannot be leased'); END;
INSERT INTO registry_migrations VALUES(2,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
CREATE TABLE sessions(
 session_uuid TEXT PRIMARY KEY,
 agent_id TEXT NOT NULL REFERENCES agents(agent_id),
 provider TEXT NOT NULL,
 provider_session_id TEXT NOT NULL,
 seat_or_host TEXT,
 runtime TEXT,
 model TEXT,
 status TEXT NOT NULL CHECK(status IN ('STARTING','ACTIVE','IDLE','ENDED','LOST')),
 started_utc TEXT NOT NULL,
 last_seen_utc TEXT NOT NULL,
 ended_utc TEXT,
 work_ref TEXT,
 revision INTEGER NOT NULL,
 updated_utc TEXT NOT NULL,
 UNIQUE(provider,provider_session_id),
 CHECK((status IN ('ENDED','LOST') AND ended_utc IS NOT NULL) OR (status NOT IN ('ENDED','LOST') AND ended_utc IS NULL))
);
CREATE TABLE session_journal(
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id TEXT UNIQUE NOT NULL,
 session_uuid TEXT NOT NULL REFERENCES sessions(session_uuid),
 agent_id TEXT NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('register','heartbeat','terminate','mark_lost')),
 body_json TEXT NOT NULL,
 committed_utc TEXT NOT NULL
);
CREATE TRIGGER session_journal_no_update BEFORE UPDATE ON session_journal BEGIN SELECT RAISE(ABORT,'session journal is append-only'); END;
CREATE TRIGGER session_journal_no_delete BEFORE DELETE ON session_journal BEGIN SELECT RAISE(ABORT,'session journal is append-only'); END;
INSERT INTO registry_migrations VALUES(3,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
ALTER TABLE requests ADD COLUMN response_status INTEGER NOT NULL DEFAULT 200;
INSERT INTO registry_migrations VALUES(4,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
ALTER TABLE sessions ADD COLUMN session_credential_sha256 TEXT CHECK(
 session_credential_sha256 IS NULL OR (
  length(session_credential_sha256)=64 AND
  session_credential_sha256=lower(session_credential_sha256) AND
  session_credential_sha256 NOT GLOB '*[^0-9a-f]*'
 )
);
CREATE TABLE session_enrollments(
 grant_id TEXT PRIMARY KEY,
 token_sha256 TEXT UNIQUE NOT NULL CHECK(length(token_sha256)=64 AND token_sha256=lower(token_sha256) AND token_sha256 NOT GLOB '*[^0-9a-f]*'),
 agent_id TEXT NOT NULL REFERENCES agents(agent_id),
 provider TEXT NOT NULL,
 seat_or_host TEXT NOT NULL,
 expires_utc TEXT NOT NULL,
 consumed_utc TEXT,
 session_uuid TEXT REFERENCES sessions(session_uuid),
 CHECK((consumed_utc IS NULL AND session_uuid IS NULL) OR (consumed_utc IS NOT NULL AND session_uuid IS NOT NULL))
);
CREATE TABLE session_registration_replays(
 grant_id TEXT PRIMARY KEY REFERENCES session_enrollments(grant_id),
 idem_key TEXT NOT NULL,
 request_sha256 TEXT NOT NULL CHECK(length(request_sha256)=64 AND request_sha256=lower(request_sha256) AND request_sha256 NOT GLOB '*[^0-9a-f]*'),
 response_json TEXT NOT NULL,
 response_status INTEGER NOT NULL,
 committed_utc TEXT NOT NULL
);
CREATE TABLE session_credential_rotations(
 session_uuid TEXT NOT NULL REFERENCES sessions(session_uuid),
 rotation_id TEXT NOT NULL,
 old_credential_sha256 TEXT NOT NULL CHECK(length(old_credential_sha256)=64 AND old_credential_sha256=lower(old_credential_sha256) AND old_credential_sha256 NOT GLOB '*[^0-9a-f]*'),
 new_credential_sha256 TEXT NOT NULL CHECK(length(new_credential_sha256)=64 AND new_credential_sha256=lower(new_credential_sha256) AND new_credential_sha256 NOT GLOB '*[^0-9a-f]*'),
 request_sha256 TEXT NOT NULL CHECK(length(request_sha256)=64 AND request_sha256=lower(request_sha256) AND request_sha256 NOT GLOB '*[^0-9a-f]*'),
 response_json TEXT NOT NULL,
 response_status INTEGER NOT NULL,
 event_id TEXT UNIQUE NOT NULL,
 committed_utc TEXT NOT NULL,
 PRIMARY KEY(session_uuid,rotation_id)
);
DROP TRIGGER session_journal_no_update;
DROP TRIGGER session_journal_no_delete;
ALTER TABLE session_journal RENAME TO session_journal_v4;
CREATE TABLE session_journal(
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id TEXT UNIQUE NOT NULL,
 session_uuid TEXT NOT NULL REFERENCES sessions(session_uuid),
 agent_id TEXT NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('register','heartbeat','terminate','mark_lost','credential_rotate')),
 body_json TEXT NOT NULL,
 committed_utc TEXT NOT NULL
);
INSERT INTO session_journal(seq,event_id,session_uuid,agent_id,action,body_json,committed_utc)
 SELECT seq,event_id,session_uuid,agent_id,action,body_json,committed_utc FROM session_journal_v4;
DROP TABLE session_journal_v4;
CREATE TRIGGER session_journal_no_update BEFORE UPDATE ON session_journal BEGIN SELECT RAISE(ABORT,'session journal is append-only'); END;
CREATE TRIGGER session_journal_no_delete BEFORE DELETE ON session_journal BEGIN SELECT RAISE(ABORT,'session journal is append-only'); END;
INSERT INTO registry_migrations VALUES(5,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
DROP TRIGGER session_journal_no_update;
DROP TRIGGER session_journal_no_delete;
ALTER TABLE session_journal RENAME TO session_journal_v5;
CREATE TABLE session_journal(
 seq INTEGER PRIMARY KEY AUTOINCREMENT,
 event_id TEXT UNIQUE NOT NULL,
 session_uuid TEXT NOT NULL REFERENCES sessions(session_uuid),
 agent_id TEXT NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('register','heartbeat','terminate','mark_lost','credential_rotate','credential_scheme_retired')),
 body_json TEXT NOT NULL,
 committed_utc TEXT NOT NULL
);
INSERT INTO session_journal(seq,event_id,session_uuid,agent_id,action,body_json,committed_utc)
 SELECT seq,event_id,session_uuid,agent_id,action,body_json,committed_utc FROM session_journal_v5;
DROP TABLE session_journal_v5;
CREATE TRIGGER session_journal_no_update BEFORE UPDATE ON session_journal BEGIN SELECT RAISE(ABORT,'session journal is append-only'); END;
CREATE TRIGGER session_journal_no_delete BEFORE DELETE ON session_journal BEGIN SELECT RAISE(ABORT,'session journal is append-only'); END;
ALTER TABLE sessions ADD COLUMN credential_scheme TEXT NOT NULL DEFAULT 'retired' CHECK(credential_scheme IN ('ed25519-v1','retired'));
ALTER TABLE sessions ADD COLUMN session_key_id TEXT;
ALTER TABLE sessions ADD COLUMN session_key_epoch INTEGER CHECK(session_key_epoch IS NULL OR session_key_epoch>0);
ALTER TABLE sessions ADD COLUMN session_public_key_b64url TEXT CHECK(session_public_key_b64url IS NULL OR length(session_public_key_b64url)=43);
CREATE TEMP TABLE retired_session_events(session_uuid TEXT PRIMARY KEY,event_id TEXT NOT NULL,audit_id TEXT NOT NULL);
INSERT INTO retired_session_events SELECT session_uuid,lower(hex(randomblob(16))),lower(hex(randomblob(16))) FROM sessions;
UPDATE sessions SET status='LOST',ended_utc=COALESCE(ended_utc,strftime('%Y-%m-%dT%H:%M:%SZ','now')),last_seen_utc=strftime('%Y-%m-%dT%H:%M:%SZ','now'),updated_utc=strftime('%Y-%m-%dT%H:%M:%SZ','now'),revision=revision+1,session_credential_sha256=NULL,credential_scheme='retired',session_key_id=NULL,session_key_epoch=NULL,session_public_key_b64url=NULL;
INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc)
 SELECT e.event_id,s.session_uuid,s.agent_id,'credential_scheme_retired','{"reason":"credential_scheme_retired","status":"LOST"}',strftime('%Y-%m-%dT%H:%M:%SZ','now') FROM sessions s JOIN retired_session_events e USING(session_uuid);
INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc)
 SELECT e.audit_id,s.agent_id,'session_credential_scheme_retired','{"kind":"session_lifecycle","reason":"credential_scheme_retired","status":"LOST"}',strftime('%Y-%m-%dT%H:%M:%SZ','now') FROM sessions s JOIN retired_session_events e USING(session_uuid);
INSERT INTO audit_outbox(event_id) SELECT audit_id FROM retired_session_events;
DROP TABLE retired_session_events;
DROP TABLE session_credential_rotations;
DROP TABLE session_registration_replays;
DROP TABLE session_enrollments;
ALTER TABLE sessions DROP COLUMN session_credential_sha256;
CREATE TABLE session_enrollments(
 grant_id TEXT PRIMARY KEY,
 token_sha256 TEXT UNIQUE NOT NULL CHECK(length(token_sha256)=64 AND token_sha256=lower(token_sha256) AND token_sha256 NOT GLOB '*[^0-9a-f]*'),
 agent_id TEXT NOT NULL REFERENCES agents(agent_id),
 provider TEXT NOT NULL,
 seat_or_host TEXT NOT NULL,
 created_utc TEXT NOT NULL,
 expires_utc TEXT NOT NULL,
 consumed_utc TEXT,
 session_uuid TEXT REFERENCES sessions(session_uuid),
 CHECK((consumed_utc IS NULL AND session_uuid IS NULL) OR (consumed_utc IS NOT NULL AND session_uuid IS NOT NULL))
);
CREATE TABLE session_registration_replays(
 grant_id TEXT PRIMARY KEY REFERENCES session_enrollments(grant_id),
 token_sha256 TEXT UNIQUE NOT NULL,
 idempotency_key TEXT UNIQUE NOT NULL,
 canonical_request_sha256 TEXT NOT NULL CHECK(length(canonical_request_sha256)=64),
 response_body_jcs TEXT NOT NULL,
 response_status INTEGER NOT NULL,
 session_uuid TEXT UNIQUE NOT NULL REFERENCES sessions(session_uuid),
 committed_utc TEXT NOT NULL,
 retain_until_utc TEXT NOT NULL
);
CREATE TABLE session_owning_replays(
 session_uuid TEXT NOT NULL REFERENCES sessions(session_uuid),
 nonce TEXT NOT NULL,
 request_sha256 TEXT NOT NULL CHECK(length(request_sha256)=64),
 signature_sha256 TEXT NOT NULL CHECK(length(signature_sha256)=64),
 timestamp_utc TEXT NOT NULL,
 idempotency_key TEXT,
 response_status INTEGER NOT NULL,
 response_json TEXT NOT NULL,
 expires_utc TEXT NOT NULL,
 is_mutation INTEGER NOT NULL CHECK(is_mutation IN (0,1)),
 action TEXT NOT NULL,
 PRIMARY KEY(session_uuid,nonce)
);
CREATE TABLE session_key_rotations(
 session_uuid TEXT NOT NULL REFERENCES sessions(session_uuid),
 nonce TEXT NOT NULL,
 old_key_id TEXT NOT NULL,
 old_key_epoch INTEGER NOT NULL,
 new_key_id TEXT NOT NULL,
 new_key_epoch INTEGER NOT NULL,
 event_id TEXT UNIQUE NOT NULL,
 committed_utc TEXT NOT NULL,
 PRIMARY KEY(session_uuid,nonce)
);
INSERT INTO registry_migrations VALUES(6,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
DROP TRIGGER audit_outbox_transition_guard;
CREATE TRIGGER audit_outbox_transition_guard BEFORE UPDATE ON audit_outbox WHEN NOT (
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NULL AND NEW.delivered_utc IS NULL AND NEW.lease_owner IS NOT NULL AND NEW.lease_until IS NOT NULL AND NEW.attempts=OLD.attempts AND NEW.last_error IS OLD.last_error)
  OR
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NOT NULL AND OLD.lease_until IS NOT NULL AND NEW.delivered_utc IS NULL AND NEW.lease_owner IS NOT NULL AND NEW.lease_until IS NOT NULL AND NEW.attempts=OLD.attempts AND NEW.last_error IS OLD.last_error)
  OR
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NOT NULL AND OLD.lease_until IS NOT NULL AND NEW.delivered_utc IS NOT NULL AND NEW.lease_owner IS NULL AND NEW.lease_until IS NULL AND NEW.attempts=OLD.attempts+1 AND NEW.last_error IS NULL)
  OR
  (OLD.delivered_utc IS NULL AND OLD.lease_owner IS NOT NULL AND OLD.lease_until IS NOT NULL AND NEW.delivered_utc IS NULL AND NEW.lease_owner IS NULL AND NEW.lease_until IS NOT NULL AND NEW.attempts=OLD.attempts+1 AND NEW.last_error IS NOT NULL)
) BEGIN SELECT RAISE(ABORT,'illegal outbox state transition'); END;
DROP TRIGGER audit_outbox_lease_guard;
CREATE TRIGGER audit_outbox_lease_guard BEFORE UPDATE OF lease_owner,lease_until ON audit_outbox WHEN NEW.delivered_utc IS NOT NULL AND (NEW.lease_owner IS NOT NULL OR NEW.lease_until IS NOT NULL) BEGIN SELECT RAISE(ABORT,'delivered outbox cannot be leased'); END;
CREATE TABLE audit_worker_state(
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),
 heartbeat_utc TEXT,
 last_cycle_started_utc TEXT,
 last_cycle_completed_utc TEXT,
 last_cycle_attempts INTEGER NOT NULL DEFAULT 0 CHECK(last_cycle_attempts BETWEEN 0 AND 100),
 permanent_failure_code TEXT,
 permanent_failure_digest TEXT,
 CHECK((permanent_failure_code IS NULL AND permanent_failure_digest IS NULL) OR (permanent_failure_code IS NOT NULL AND length(permanent_failure_digest)=64))
);
INSERT INTO audit_worker_state(singleton) VALUES(1);
INSERT INTO registry_migrations VALUES(7,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
CREATE TABLE audit_credential_bindings(
 role TEXT PRIMARY KEY CHECK(role IN ('ledger_audit','ledger_readiness_outbound','registry_peer_readiness_inbound')),
 salt BLOB NOT NULL CHECK(length(salt)=32),
 accepted_revision INTEGER CHECK(accepted_revision IS NULL OR accepted_revision>0),
 verifier TEXT CHECK(verifier IS NULL OR (length(verifier)=64 AND verifier NOT GLOB '*[^0-9a-f]*')),
 full_fingerprint TEXT CHECK(full_fingerprint IS NULL OR (length(full_fingerprint)=64 AND full_fingerprint NOT GLOB '*[^0-9a-f]*')),
 CHECK((accepted_revision IS NULL AND verifier IS NULL AND full_fingerprint IS NULL) OR (accepted_revision IS NOT NULL AND verifier IS NOT NULL AND full_fingerprint IS NOT NULL))
);
CREATE TABLE audit_failure_latches(
 latch_key TEXT PRIMARY KEY,
 event_id TEXT,
 failure_code TEXT NOT NULL CHECK(failure_code IN ('CONFIGURATION_INVALID','CREDENTIAL_INVALID','PEER_IDENTITY_INVALID','REMOTE_PROTOCOL_INVALID','REMOTE_REJECTED')),
 static_fingerprint TEXT NOT NULL CHECK(length(static_fingerprint)=64 AND static_fingerprint NOT GLOB '*[^0-9a-f]*'),
 full_fingerprint TEXT CHECK(full_fingerprint IS NULL OR (length(full_fingerprint)=64 AND full_fingerprint NOT GLOB '*[^0-9a-f]*')),
 failure_field_mask_json TEXT NOT NULL,
 credential_role TEXT CHECK(credential_role IS NULL OR credential_role IN ('ledger_audit','ledger_readiness_outbound','registry_peer_readiness_inbound')),
 declared_revision INTEGER CHECK(declared_revision IS NULL OR declared_revision>0),
 created_utc TEXT NOT NULL,
 updated_utc TEXT NOT NULL
);
CREATE INDEX audit_failure_latches_event ON audit_failure_latches(event_id);
INSERT INTO registry_migrations VALUES(8,strftime('%Y-%m-%dT%H:%M:%SZ','now'));
PRAGMA application_id=1414746695;
PRAGMA user_version=8;
