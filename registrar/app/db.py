"""Ledger SQLite access bound to the reviewed ordered R7 migration contract."""
import hashlib, json, os, sqlite3
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS=Path(__file__).parents[1]/"migrations"
CONTRACT=Path(__file__).parents[2]/"contracts"/"r7"/"ledger-migrations.json"
LEDGER_SERVICE_VERSION="townsquare-ledger-v0"
LEDGER_SCHEMA_VERSION=14
LEDGER_APPLICATION_ID=1414745159  # TSLG
REGISTRY_SERVICE_VERSION="townsquare-registry-v0"
REGISTRY_SCHEMA_VERSION=2
REGISTRY_AUDIT_CONTRACT_VERSION="registry-ledger-audit-v1"

def connect(path):
    db=sqlite3.connect(path,timeout=5,isolation_level=None,check_same_thread=False); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=FULL"); db.execute("PRAGMA busy_timeout=5000")
    app_id=db.execute("PRAGMA application_id").fetchone()[0]; user_version=db.execute("PRAGMA user_version").fetchone()[0]
    has_schema=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
    if has_schema and (app_id != LEDGER_APPLICATION_ID or user_version != LEDGER_SCHEMA_VERSION):
        db.close(); raise RuntimeError(f"Ledger database identity mismatch: application_id={app_id} user_version={user_version}")
    return db

@contextmanager
def session(path):
    db=connect(path)
    try: yield db
    finally: db.close()

def _sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def _contract_rows():
    try: contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    except Exception as exc: raise RuntimeError("Ledger migration contract is unavailable") from exc
    rows=contract.get("migrations")
    if contract.get("application_id") != LEDGER_APPLICATION_ID or contract.get("user_version") != LEDGER_SCHEMA_VERSION or contract.get("head") != "14" or not isinstance(rows,list):
        raise RuntimeError("Ledger migration contract identity is invalid")
    if [row.get("ordinal") for row in rows] != list(range(1,15)) or [row.get("id") for row in rows] != [f"{i:03d}" for i in range(1,15)]:
        raise RuntimeError("Ledger migration contract order is invalid")
    paths=[]
    for row in rows:
        path=Path(__file__).parents[2]/row["path"]
        if path.parent.resolve() != MIGRATIONS.resolve() or not path.is_file() or _sha(path) != row.get("sha256"):
            raise RuntimeError(f"Ledger migration contract hash mismatch: {row.get('id')}")
        paths.append((int(row["id"]),path))
    return contract,paths

def _statements(path):
    statements=[]; current=""
    for line in path.read_text(encoding="utf-8").splitlines(True):
        if line.lstrip().upper().startswith("PRAGMA FOREIGN_KEYS="): continue
        current+=line
        if sqlite3.complete_statement(current): statements.append(current); current=""
    if current.strip(): raise RuntimeError(f"partial migration {path.name}")
    return statements

def _apply_migration(db, version, path):
    """Apply one already hash-validated migration inside the caller transaction."""
    for statement in _statements(path): db.execute(statement)
    db.execute("INSERT INTO schema_migrations VALUES (?,strftime('%Y-%m-%dT%H:%M:%SZ','now'))",(version,))

def migrate(db):
    contract,rows=_contract_rows()
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
    applied=[] if not exists else [r[0] for r in db.execute("SELECT version FROM schema_migrations ORDER BY version")]
    expected=[version for version,_ in rows]
    if applied != expected[:len(applied)]: raise RuntimeError(f"unknown or divergent Ledger migration history: {applied}")
    if len(applied)==len(expected): return verify_schema(db)
    db.execute("BEGIN EXCLUSIVE")
    try:
        for version,path in rows[len(applied):]:
            _apply_migration(db,version,path)
        db.execute(f"PRAGMA application_id={LEDGER_APPLICATION_ID}")
        db.execute(f"PRAGMA user_version={LEDGER_SCHEMA_VERSION}")
        if db.execute("PRAGMA application_id").fetchone()[0] != LEDGER_APPLICATION_ID or db.execute("PRAGMA user_version").fetchone()[0] != LEDGER_SCHEMA_VERSION: raise RuntimeError("Ledger database identity write failed")
        db.commit()
    except Exception: db.rollback(); raise
    return verify_schema(db)

def canonical_schema_sha256(db):
    rows=[{"type":r[0],"name":r[1],"tbl_name":r[2],"sql":(r[3] or "").replace("\r\n","\n").replace("\r","\n").rstrip()} for r in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name,tbl_name")]
    return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def verify_schema(db):
    contract,rows=_contract_rows(); expected=[v for v,_ in rows]
    table=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
    if not table: raise RuntimeError("Registrar schema is not migrated")
    applied=[row[0] for row in db.execute("SELECT version FROM schema_migrations ORDER BY version")]
    if applied != expected: raise RuntimeError(f"Registrar migration history mismatch: {applied}")
    if db.execute("PRAGMA application_id").fetchone()[0] != LEDGER_APPLICATION_ID or db.execute("PRAGMA user_version").fetchone()[0] != LEDGER_SCHEMA_VERSION: raise RuntimeError("Ledger application_id/user_version mismatch")
    digest=canonical_schema_sha256(db)
    if digest != contract.get("canonical_schema_sha256"): raise RuntimeError("Ledger canonical schema digest mismatch")
    return LEDGER_SCHEMA_VERSION

def registry_integration_status():
    raw=os.environ.get("REGISTRY_INTEGRATION_ENABLED")
    if raw is None or raw.strip().lower() in {"","0","false","no","off"}: return {"enabled":False,"compatible":True,"configured":None}
    enabled=raw.strip().lower() in {"1","true","yes","on"}
    configured={"service_version":os.environ.get("REGISTRY_SERVICE_VERSION",os.environ.get("REGISTRY_SERVICE_ID")),"schema_version":os.environ.get("REGISTRY_SCHEMA_VERSION",os.environ.get("REGISTRY_SCHEMA_HEAD")),"audit_contract_version":os.environ.get("REGISTRY_AUDIT_CONTRACT_VERSION")}
    expected={"service_version":REGISTRY_SERVICE_VERSION,"schema_version":str(REGISTRY_SCHEMA_VERSION),"audit_contract_version":REGISTRY_AUDIT_CONTRACT_VERSION}
    return {"enabled":True,"compatible":enabled and configured==expected,"configured":configured,"expected":expected}
