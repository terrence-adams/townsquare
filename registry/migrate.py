"""The sole Registry schema writer. An exclusive lock prevents split-brain DDL."""
import os,sqlite3,sys
from pathlib import Path
DB=Path(os.environ['REGISTRY_DB']);LOCK=DB.with_suffix('.migration.lock');SCHEMA=Path('/app/schema.sql')
def main():
 DB.parent.mkdir(parents=True,exist_ok=True)
 try: fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 except FileExistsError: raise SystemExit(f'exclusive registry migration lock exists: {LOCK}')
 try:
  d=sqlite3.connect(DB,isolation_level=None); exists=d.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='registry_migrations'").fetchone()
  if exists:
   version=d.execute('SELECT max(version) FROM registry_migrations').fetchone()[0]
   if version!=1:raise SystemExit(f'unsupported registry schema version: {version}')
  else:
   d.executescript(SCHEMA.read_text());d.execute('PRAGMA wal_checkpoint(FULL)')
  d.close()
 finally:
  os.close(fd);LOCK.unlink(missing_ok=True)
if __name__=='__main__':main()
