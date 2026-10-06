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
def main():
 if len(sys.argv)!=3: raise SystemExit("usage: restore-drill.py BACKUP_DIR EMPTY_DRILL_DIR")
 source=Path(sys.argv[1]).resolve(); drill=Path(sys.argv[2]).resolve()
 if not source.is_dir() or (not drill.is_dir()) or any(drill.iterdir()): raise SystemExit("backup must exist and drill directory must exist and be empty")
 key=os.environ.get("TOWNSQUARE_BACKUP_RECIPIENT_FILE"); public=os.environ.get("TOWNSQUARE_BACKUP_SIGNING_PUBLIC_KEY_FILE")
 if not key or not public: raise SystemExit("recipient and manifest public key files are required")
 run(["minisign","-Vm",str(source/'manifest.json'),"-p",public,"-x",str(source/'manifest.json.minisig')])
 for item in json.loads((source/'manifest.json').read_text())["domains"]:
  cipher=source/item['ciphertext']
  if sha(cipher)!=item['ciphertext_sha256']: raise SystemExit(f"ciphertext hash mismatch: {cipher.name}")
  output=drill/f"{item['domain']}.db"; run(["age","--decrypt","--identity",key,"--output",str(output),str(cipher)])
  db=sqlite3.connect(output)
  try:
   if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok": raise SystemExit(f"integrity failure: {item['domain']}")
  finally: db.close()
 print("restore drill verified; no live data was changed")
if __name__=='__main__': main()
