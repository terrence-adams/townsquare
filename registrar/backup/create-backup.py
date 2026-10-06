"""Image copy of the encrypted two-domain backup implementation."""
import hashlib,json,os,sqlite3,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
def need(k):
 v=os.environ.get(k)
 if not v: raise SystemExit(f"required environment variable is absent: {k}")
 return Path(v)
def run(a): subprocess.run(a,check=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1048576),b''): h.update(x)
 return h.hexdigest()
def snap(src,dst):
 if not src.is_file(): raise SystemExit(f"database is not a file: {src}")
 a=sqlite3.connect(f"file:{src}?mode=ro",uri=True); b=sqlite3.connect(dst)
 try:
  a.backup(b)
  if b.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise RuntimeError('integrity check failed')
 finally: b.close(); a.close()
def main():
 root=need('TOWNSQUARE_BACKUP_DIR').resolve(); root.mkdir(parents=True,exist_ok=True); out=root/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); out.mkdir(mode=0o700)
 recipient=need('TOWNSQUARE_BACKUP_RECIPIENT_FILE'); signing=need('TOWNSQUARE_BACKUP_SIGNING_KEY_FILE'); domains={'ledger':need('TOWNSQUARE_LEDGER_DB'),'registry':need('TOWNSQUARE_REGISTRY_DB')}; rows=[]
 with tempfile.TemporaryDirectory(prefix='townsquare-backup-') as t:
  t=Path(t)
  for name,src in domains.items():
   plain=t/f'{name}.db'; crypt=out/f'{name}.db.age'; snap(src,plain); run(['age','--encrypt','--recipient-file',str(recipient),'--output',str(crypt),str(plain)]); rows.append({'domain':name,'ciphertext':crypt.name,'ciphertext_sha256':sha(crypt),'source_name':src.name})
  manifest={'schema':1,'created_utc':out.name,'domains':rows,'external_checkpoint':'PENDING_OPERATOR_PUBLICATION'}; mp=out/'manifest.json'; mp.write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n'); run(['minisign','-S','-s',str(signing),'-m',str(mp),'-x',str(out/'manifest.json.minisig')])
 print(json.dumps({'backup':str(out),'checkpoint_sha256':sha(out/'manifest.json')},sort_keys=True))
if __name__=='__main__': main()
