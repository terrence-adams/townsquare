"""Exclusive atomic Registry v1→v2 migrator; runtime never performs DDL."""
import hashlib, json, os, sqlite3
from pathlib import Path

DB=Path(os.environ['REGISTRY_DB']); LOCK=DB.with_suffix('.migration.lock')
ROOT=Path(__file__).resolve().parents[1]; SCHEMA=Path(__file__).with_name('schema.sql')
CONTRACT=ROOT/'contracts'/'r7'/'registry-schema.json'
APPLICATION_ID=1414746695; USER_VERSION=2
def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def _statements(path):
 statements=[]; current=''
 for line in path.read_text(encoding='utf-8').splitlines(True):
  current+=line
  if sqlite3.complete_statement(current): statements.append(current); current=''
 if current.strip(): raise RuntimeError('partial Registry schema statement')
 return statements
def _v2_statements():
 return tuple(statement for statement in _statements(SCHEMA) if statement.lstrip().upper().startswith(('ALTER TABLE AUDIT_OUTBOX','CREATE TRIGGER')))
def _contract():
 try: value=json.loads(CONTRACT.read_text(encoding='utf-8'))
 except Exception as exc: raise RuntimeError('Registry schema contract unavailable') from exc
 if value.get('application_id')!=APPLICATION_ID or value.get('user_version')!=USER_VERSION or value.get('head')!='2' or value.get('schema_sha256')!=_sha(SCHEMA) or value.get('migrator_sha256')!=_sha(Path(__file__)):
  raise RuntimeError('Registry schema contract hash or identity mismatch')
 return value
def canonical_schema_sha256(db):
 rows=[{'type':r[0],'name':r[1],'tbl_name':r[2],'sql':(r[3] or '').replace('\r\n','\n').replace('\r','\n').rstrip()} for r in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name,tbl_name")]
 return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def verify(db):
 contract=_contract(); versions=[r[0] for r in db.execute('SELECT version FROM registry_migrations ORDER BY version')]
 if versions!=[1,2] or db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or db.execute('PRAGMA user_version').fetchone()[0]!=USER_VERSION: raise RuntimeError('Registry migration history or database identity mismatch')
 if canonical_schema_sha256(db)!=contract.get('canonical_schema_sha256'): raise RuntimeError('Registry canonical schema digest mismatch')
 return USER_VERSION
def migrate(db):
 _contract(); db.execute('BEGIN EXCLUSIVE')
 try:
  exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='registry_migrations'").fetchone()
  if not exists:
   for statement in _statements(SCHEMA): db.execute(statement)
  else:
   versions=[r[0] for r in db.execute('SELECT version FROM registry_migrations ORDER BY version')]
   if versions==[1]:
    for statement in _v2_statements(): db.execute(statement)
    db.execute("INSERT INTO registry_migrations VALUES(2,strftime('%Y-%m-%dT%H:%M:%SZ','now'))")
    db.execute(f'PRAGMA application_id={APPLICATION_ID}'); db.execute(f'PRAGMA user_version={USER_VERSION}')
   elif versions != [1,2]: raise RuntimeError(f'unsupported registry schema versions: {versions}')
  db.commit()
 except Exception: db.rollback(); raise
 return verify(db)
def main():
 DB.parent.mkdir(parents=True,exist_ok=True)
 try: fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 except FileExistsError: raise SystemExit(f'exclusive registry migration lock exists: {LOCK}')
 try:
  d=sqlite3.connect(DB,isolation_level=None)
  try: migrate(d)
  finally: d.close()
 finally: os.close(fd); LOCK.unlink(missing_ok=True)
if __name__=='__main__': main()
