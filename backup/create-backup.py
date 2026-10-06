#!/usr/bin/env python3
"""Create independently encrypted SQLite backups; no network and no live restore."""
import hashlib, json, os, shutil, sqlite3, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

def need(name):
    value=os.environ.get(name)
    if not value: raise SystemExit(f"required environment variable is absent: {name}")
    return Path(value)
def run(args): subprocess.run(args,check=True)
def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def snapshot(source, target):
    if not source.is_file(): raise SystemExit(f"database is not a file: {source}")
    src=sqlite3.connect(f"file:{source}?mode=ro",uri=True); dst=sqlite3.connect(target)
    try: src.backup(dst); dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok" or (_ for _ in ()).throw(RuntimeError("integrity check failed"))
    finally: dst.close(); src.close()
def main():
    root=need("TOWNSQUARE_BACKUP_DIR").resolve(); recipient=need("TOWNSQUARE_BACKUP_RECIPIENT_FILE"); signing=need("TOWNSQUARE_BACKUP_SIGNING_KEY_FILE")
    root.mkdir(parents=True,exist_ok=True); stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); target=root/stamp; target.mkdir(mode=0o700)
    domains={"ledger":need("TOWNSQUARE_LEDGER_DB"),"registry":need("TOWNSQUARE_REGISTRY_DB")}; rows=[]
    with tempfile.TemporaryDirectory(prefix="townsquare-backup-") as temp:
        temp=Path(temp)
        for name, source in domains.items():
            plain=temp/f"{name}.db"; cipher=target/f"{name}.db.age"; snapshot(source,plain)
            run(["age","--encrypt","--recipient-file",str(recipient),"--output",str(cipher),str(plain)])
            rows.append({"domain":name,"ciphertext":cipher.name,"ciphertext_sha256":digest(cipher),"source_name":source.name})
        manifest={"schema":1,"created_utc":stamp,"domains":rows,"external_checkpoint":"PENDING_OPERATOR_PUBLICATION"}
        mp=target/"manifest.json"; mp.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        run(["minisign","-S","-s",str(signing),"-m",str(mp),"-x",str(target/"manifest.json.minisig")])
    print(json.dumps({"backup":str(target),"checkpoint_sha256":digest(target/"manifest.json")},sort_keys=True))
if __name__ == "__main__": main()
