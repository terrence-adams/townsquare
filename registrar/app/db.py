import sqlite3
from pathlib import Path
MIGRATIONS=Path(__file__).parents[1]/"migrations"
def connect(path):
    db=sqlite3.connect(path,timeout=5,isolation_level=None,check_same_thread=False); db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=FULL"); db.execute("PRAGMA busy_timeout=5000"); return db
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
