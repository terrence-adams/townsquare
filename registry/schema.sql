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
PRAGMA application_id=1414746695;
PRAGMA user_version=5;
