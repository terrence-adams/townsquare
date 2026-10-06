import os,sqlite3
from contextlib import contextmanager
from pathlib import Path
MIGRATIONS=Path(__file__).parents[1]/"migrations"
LEDGER_SERVICE_VERSION="townsquare-ledger-v0"
LEDGER_SCHEMA_VERSION=14
REGISTRY_SERVICE_VERSION="townsquare-registry-v0"
REGISTRY_SCHEMA_VERSION=1
REGISTRY_AUDIT_CONTRACT_VERSION="registry-ledger-audit-v1"
def connect(path):
    db=sqlite3.connect(path,timeout=5,isolation_level=None,check_same_thread=False); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=FULL"); db.execute("PRAGMA busy_timeout=5000"); return db
@contextmanager
def session(path):
    """One connection for one unit of work, always closed -- what main.py's
    per-request `get_db` dependency yields, so a request cannot leak a
    connection down an error path (Windows holds an exclusive lock on an open
    DB file, so a leak is not merely untidy). All four PRAGMAs are re-applied
    by `connect` on every call, so a session-scoped connection carries the
    full posture `/health/ready` asserts."""
    db=connect(path)
    try: yield db
    finally: db.close()
def migrate(db):
    exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
    applied=set() if not exists else {r[0] for r in db.execute("SELECT version FROM schema_migrations")}
    for path in sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")):
        version=int(path.name[:3])
        if version not in applied:
            statements=[]; current=""
            for line in path.read_text().splitlines(True):
                if line.lstrip().upper().startswith("PRAGMA FOREIGN_KEYS="): continue
                current+=line
                if sqlite3.complete_statement(current): statements.append(current); current=""
            if current.strip(): raise RuntimeError(f"partial migration {path.name}")
            db.execute("BEGIN EXCLUSIVE")
            try:
                for statement in statements: db.execute(statement)
                db.execute("INSERT INTO schema_migrations VALUES (?,strftime('%Y-%m-%dT%H:%M:%SZ','now'))",(version,)); db.commit()
            except Exception: db.rollback(); raise

def verify_schema(db):
    """Fail closed unless the canonical migrator has applied this release exactly."""
    expected={int(path.name[:3]) for path in MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")}
    table=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'").fetchone()
    if not table: raise RuntimeError("Registrar schema is not migrated")
    applied={row[0] for row in db.execute("SELECT version FROM schema_migrations")}
    if applied != expected:
        missing=sorted(expected-applied); unexpected=sorted(applied-expected)
        raise RuntimeError(f"Registrar schema is not release-ready: missing={missing} unexpected={unexpected}")
    version=max(expected) if expected else 0
    if version != LEDGER_SCHEMA_VERSION:
        raise RuntimeError(f"Ledger release schema mismatch: expected={LEDGER_SCHEMA_VERSION} actual={version}")
    return version

def registry_integration_status():
    """Compare configured Registry identity with the Ledger audit contract."""
    raw=os.environ.get("REGISTRY_INTEGRATION_ENABLED")
    if raw is None or raw.strip().lower() in {"","0","false","no","off"}:
        return {"enabled":False,"compatible":True,"configured":None}
    enabled=raw.strip().lower() in {"1","true","yes","on"}
    configured={
        "service_version":os.environ.get("REGISTRY_SERVICE_VERSION",os.environ.get("REGISTRY_SERVICE_ID")),
        "schema_version":os.environ.get("REGISTRY_SCHEMA_VERSION",os.environ.get("REGISTRY_SCHEMA_HEAD")),
        "audit_contract_version":os.environ.get("REGISTRY_AUDIT_CONTRACT_VERSION"),
    }
    expected={
        "service_version":REGISTRY_SERVICE_VERSION,
        "schema_version":str(REGISTRY_SCHEMA_VERSION),
        "audit_contract_version":REGISTRY_AUDIT_CONTRACT_VERSION,
    }
    return {
        "enabled":True,
        "compatible":enabled and configured==expected,
        "configured":configured,
        "expected":expected,
    }
