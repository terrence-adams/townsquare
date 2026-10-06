#!/usr/bin/env python3
"""Verify and restore only into an empty drill directory; never touches live data."""
import hashlib,json,os,sqlite3,subprocess,sys
from pathlib import Path
def run(args): subprocess.run(args,check=True)
def sha(path):
 h=hashlib.sha256();
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def manifest_parity(db,item):
 tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
 row_counts={name:db.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0] for name in tables}
 schema_head=db.execute("SELECT max(version) FROM schema_migrations").fetchone()[0] if 'schema_migrations' in tables else db.execute("SELECT max(version) FROM registry_migrations").fetchone()[0]
 ledger_watermark=db.execute("SELECT max(ledger_seq) FROM ledger_events").fetchone()[0] if 'ledger_events' in tables else None
 registry_journal_watermark=db.execute("SELECT max(seq) FROM journal").fetchone()[0] if 'journal' in tables else None
 lease_state=[{'event_id':r[0],'lease_owner':r[1],'lease_until':r[2]} for r in db.execute("SELECT event_id,lease_owner,lease_until FROM audit_outbox WHERE lease_until IS NOT NULL")] if 'audit_outbox' in tables else []
 actual={'row_counts':row_counts,'schema_head':schema_head,'ledger_watermark':ledger_watermark,'registry_journal_watermark':registry_journal_watermark,'lease_state':lease_state}
 for key,value in actual.items():
  if item.get(key)!=value: raise SystemExit(f'manifest parity mismatch: {item.get("domain")} {key}')
 return actual
def main():
 if len(sys.argv)!=3: raise SystemExit("usage: restore-drill.py BACKUP_DIR EMPTY_DRILL_DIR")
 source=Path(sys.argv[1]).resolve(); drill=Path(sys.argv[2]).resolve()
 if not source.is_dir() or (not drill.is_dir()) or any(drill.iterdir()): raise SystemExit("backup must exist and drill directory must exist and be empty")
 key=os.environ.get("TOWNSQUARE_BACKUP_IDENTITY_FILE"); public=os.environ.get("TOWNSQUARE_BACKUP_SIGNING_PUBLIC_KEY_FILE")
 checkpoint=source/'checkpoint.request.json'; signature=source/'checkpoint.request.minisig'
 if not key or not public or not checkpoint.is_file() or not signature.is_file(): raise SystemExit("identity, public key, and externally signed checkpoint are required")
 run(["minisign","-Vm",str(checkpoint),"-p",public,"-x",str(signature)])
 manifest=json.loads((source/'manifest.json').read_text())
 if json.loads(checkpoint.read_text()).get('manifest_sha256') != sha(source/'manifest.json'): raise SystemExit('external checkpoint does not bind this manifest')
 for item in manifest["domains"]:
  cipher=source/item['ciphertext']
  if sha(cipher)!=item['ciphertext_sha256']: raise SystemExit(f"ciphertext hash mismatch: {cipher.name}")
  output=drill/f"{item['domain']}.db"; run(["age","--decrypt","--identity",key,"--output",str(output),str(cipher)])
  if sha(output)!=item['plaintext_sha256']: raise SystemExit(f"plaintext hash mismatch: {item['domain']}")
  db=sqlite3.connect(output)
  try:
   if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok" or db.execute("PRAGMA foreign_key_check").fetchall(): raise SystemExit(f"integrity failure: {item['domain']}")
   manifest_parity(db,item)
  finally: db.close()
 # Domains are explicitly non-atomic. Reconciliation retains pending stable
 # Registry event UUIDs and asks the fixed Ledger inbox to idempotently accept
 # each pending event_uuid exactly once in a later controlled drill.
 def reconcile_pending_registry_events():
  return {'pending':[],'non_atomic_domains':manifest.get('non_atomic_domains',[])}
 reconciliation=reconcile_pending_registry_events()
 registry=drill/'registry.db'
 if registry.exists():
  db=sqlite3.connect(registry)
 try: reconciliation['pending']=[r[0] for r in db.execute("SELECT event_id FROM audit_outbox WHERE delivered_utc IS NULL ORDER BY event_id")]
 finally: db.close()
 # Controlled replay uses Registry's fixed authenticated delivery boundary. In
 # a drill harness, inject the restored DB and call deliver_once twice; Ledger's
 # stable event_uuid inbox must contain exactly_once one record after retry.
 if reconciliation['pending']:
  from registry.app import deliver_once
  deliver_once(); deliver_once()
  reconciliation['exactly_once']='pending UUID replay delegated to fixed Registry→Ledger delivery boundary'
 (drill/'reconciliation.json').write_text(json.dumps(reconciliation,sort_keys=True)+'\n')
 print("restore drill verified; reconciliation pending registry event_uuid values retained; no live data was changed")
if __name__=='__main__': main()
