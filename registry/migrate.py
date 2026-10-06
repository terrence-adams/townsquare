"""Exclusive transactional Registry v1→v2 migrator; runtime never performs DDL."""
import os,sqlite3
from pathlib import Path
DB=Path(os.environ['REGISTRY_DB']);LOCK=DB.with_suffix('.migration.lock');SCHEMA=Path('/app/schema.sql')
V2=("ALTER TABLE audit_outbox ADD COLUMN lease_owner TEXT;","ALTER TABLE audit_outbox ADD COLUMN lease_until TEXT;","CREATE TRIGGER audit_outbox_lease_guard BEFORE UPDATE OF lease_owner,lease_until ON audit_outbox WHEN NEW.delivered_utc IS NOT NULL AND (NEW.lease_owner IS NOT NULL OR NEW.lease_until IS NOT NULL) BEGIN SELECT RAISE(ABORT,'delivered outbox cannot be leased'); END;","CREATE TRIGGER audit_outbox_no_delete BEFORE DELETE ON audit_outbox BEGIN SELECT RAISE(ABORT,'outbox is append-only'); END;","CREATE TRIGGER journal_no_update BEFORE UPDATE ON journal BEGIN SELECT RAISE(ABORT,'journal is append-only'); END;","CREATE TRIGGER journal_no_delete BEFORE DELETE ON journal BEGIN SELECT RAISE(ABORT,'journal is append-only'); END;")
def migrate(db):
 db.execute('BEGIN EXCLUSIVE')
 try:
  if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='registry_migrations'").fetchone(): db.executescript(SCHEMA.read_text()); db.commit(); return
  versions=[r[0] for r in db.execute('SELECT version FROM registry_migrations ORDER BY version')]
  if versions==[1]:
   for statement in V2: db.execute(statement)
   db.execute("INSERT INTO registry_migrations VALUES(2,strftime('%Y-%m-%dT%H:%M:%SZ','now'))")
  elif versions != [1,2]: raise RuntimeError(f'unsupported registry schema versions: {versions}')
  db.commit()
 except Exception: db.rollback(); raise
def main():
 DB.parent.mkdir(parents=True,exist_ok=True)
 try: fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 except FileExistsError: raise SystemExit(f'exclusive registry migration lock exists: {LOCK}')
 try:
  d=sqlite3.connect(DB,isolation_level=None); migrate(d); d.close()
 finally: os.close(fd);LOCK.unlink(missing_ok=True)
if __name__=='__main__':main()
