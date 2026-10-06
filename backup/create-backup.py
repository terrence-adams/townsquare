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
    try:
        src.backup(dst)
        integrity=dst.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys=dst.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != "ok" or foreign_keys: raise RuntimeError("integrity or foreign-key check failed")
        tables=[r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        counts={name:dst.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0] for name in tables}
        return {"integrity_check":integrity,"foreign_key_check":[],"row_counts":counts}
    finally: dst.close(); src.close()
def main():
    root=need("TOWNSQUARE_BACKUP_DIR").resolve(); recipient=need("TOWNSQUARE_BACKUP_RECIPIENT_FILE")
    root.mkdir(parents=True,exist_ok=True); stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); target=root/stamp; target.mkdir(mode=0o700)
    domains={"ledger":need("TOWNSQUARE_LEDGER_DB"),"registry":need("TOWNSQUARE_REGISTRY_DB")}; rows=[]
    with tempfile.TemporaryDirectory(prefix="townsquare-backup-") as temp:
        temp=Path(temp)
        for name, source in domains.items():
            plain=temp/f"{name}.db"; cipher=target/f"{name}.db.age"; checks=snapshot(source,plain)
            with plain.open("rb") as f: os.fsync(f.fileno())
            run(["age","--encrypt","--recipient-file",str(recipient),"--output",str(cipher),str(plain)])
            rows.append({"domain":name,"ciphertext":cipher.name,"plaintext_sha256":digest(plain),"ciphertext_sha256":digest(cipher),"source_name":source.name,"closed_fsynced_copy":True,**checks})
        manifest={"schema":2,"created_utc":stamp,"domains":rows,"external_checkpoint":"REQUIRED_EXTERNAL_SIGNATURE","signing_boundary":"NAS emits unsigned canonical checkpoint; an external operator signs it; NAS verifies with public material only"}
        mp=target/"manifest.json"; mp.write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        checkpoint={"manifest_sha256":digest(mp),"created_utc":stamp,"domains":[{"domain":x["domain"],"ciphertext_sha256":x["ciphertext_sha256"]} for x in rows]}
        (target/"checkpoint.request.json").write_text(json.dumps(checkpoint,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps({"backup":str(target),"checkpoint_sha256":digest(target/"manifest.json")},sort_keys=True))
if __name__ == "__main__": main()
