"""Deterministic generated schema-009 fixture for the 009 -> 014 rehearsal.

This is deliberately *not* an export of the NAS database.  No sanitized
historical SQLite export exists in this repository.  The fixture therefore
uses only the aggregate measurements recorded in town-registrar-ws3-plan.md:
1,070 legacy posts, 313 roots, 197 signature artifacts, 1,062 assignments,
two promoted import runs, zero null ``drive_created_at`` values, and the
measured board distribution.  Every identifier, URL, filename, and hash is
synthetic and deterministic; it contains no production bodies, credentials,
or Drive identifiers.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from registrar.app.db import MIGRATIONS, connect

POST_COUNT = 1070
ROOT_COUNT = 313
ARTIFACT_COUNT = 197
ASSIGNMENT_COUNT = 1062
BOARD_COUNTS = {
    "requests": 743,
    "bulletin-board": 307,
    "seeking": 16,
    "wanted": 4,
}
FIXTURE_KIND = "generated-representative-schema-009"


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _statements(path: Path):
    current = ""
    for line in path.read_text(encoding="utf-8").splitlines(True):
        if line.lstrip().upper().startswith("PRAGMA FOREIGN_KEYS="):
            continue
        current += line
        if sqlite3.complete_statement(current):
            yield current
            current = ""
    if current.strip():
        raise RuntimeError(f"partial fixture migration {path.name}")


def apply_schema_009(db: sqlite3.Connection) -> None:
    """Apply the released 001--009 schema, matching the old DB boundary."""
    for path in sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")):
        version = int(path.name[:3])
        if version > 9:
            break
        db.execute("BEGIN EXCLUSIVE")
        try:
            for statement in _statements(path):
                db.execute(statement)
            db.execute(
                "INSERT INTO schema_migrations VALUES (?,?)",
                (version, "2026-09-22T00:00:00Z"),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise


def _boards():
    for board, count in BOARD_COUNTS.items():
        yield from (board for _ in range(count))


def build(path: str | Path) -> sqlite3.Connection:
    """Create and return an open generated schema-009 database at *path*."""
    db = connect(str(path))
    apply_schema_009(db)
    db.execute("BEGIN IMMEDIATE")
    try:
        for number in range(ROOT_COUNT):
            root_uid = f"legacy-root-{number:04d}"
            db.execute(
                "INSERT INTO roots(root_uid,thread_id,prefix,utc_date,namespace,local_number,"
                "opening_post_uid,next_post_no,status,created_by,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    root_uid, f"TS-20260922-legacy-{number + 1:03d}", "TS", "20260922",
                    "legacy", number + 1, None, 1, "legacy", "legacy-import",
                    "2026-09-22T00:00:00Z",
                ),
            )
        per_root = [0] * ROOT_COUNT
        for sequence, board in enumerate(_boards(), start=1):
            root_number = (sequence - 1) % ROOT_COUNT
            root_uid = f"legacy-root-{root_number:04d}"
            post_no = per_root[root_number]
            per_root[root_number] += 1
            post_uid = f"legacy-post-{sequence:04d}"
            # IN_PROGRESS is intentionally a historical label.  It is not a
            # native Request state and must survive as legacy projection data.
            state = ("OPEN", "WORKING", "BLOCKED", "RESOLVED", "CLOSED", "CANCELLED", "IN_PROGRESS")[(sequence - 1) % 7]
            db.execute(
                "INSERT INTO posts(post_uid,root_uid,post_no,legacy_seq,state,board,filename,header_at,created_at,"
                "author_agent,content_sha256,drive_file_id,drive_url,registration_state,reserved_until,source,drive_created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    post_uid, root_uid, post_no, sequence, state, board,
                    f"TS-20260922-legacy-{root_number + 1:03d}.{post_no:03d}-{state}__generated.txt",
                    "2026-09-22T00:00:00Z", "2026-09-22T00:00:00Z",
                    f"legacy-agent-{sequence % 25:02d}", _sha(f"legacy-content-metadata:{sequence}"),
                    f"generated-drive-post-{sequence:04d}",
                    f"https://drive.invalid/generated/post/{sequence:04d}", "legacy", None,
                    "legacy_import", f"2026-09-22T00:{sequence % 60:02d}:00Z",
                ),
            )
            if sequence <= ASSIGNMENT_COUNT:
                db.execute(
                    "INSERT INTO assignments(post_uid,agent_id,role,active) VALUES (?,?,?,1)",
                    (post_uid, f"legacy-agent-{sequence % 25:02d}", "responsible"),
                )
        for number in range(ROOT_COUNT):
            db.execute(
                "UPDATE roots SET opening_post_uid=? WHERE root_uid=?",
                (f"legacy-post-{number + 1:04d}", f"legacy-root-{number:04d}"),
            )
        for sequence in range(1, ARTIFACT_COUNT + 1):
            db.execute(
                "INSERT INTO artifacts(drive_file_id,parent_post_uid,kind,drive_url,filename,content_sha256,verification_state) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    f"generated-drive-signature-{sequence:04d}", f"legacy-post-{sequence:04d}", "signature",
                    f"https://drive.invalid/generated/signature/{sequence:04d}",
                    f"legacy-{sequence:04d}.sig", _sha(f"legacy-signature:{sequence}"),
                    "orphan" if sequence <= 2 else "verified",
                ),
            )
        for run_number in (1, 2):
            db.execute(
                "INSERT INTO import_runs(run_id,manifest_digest,manifest_json,status,created_by,created_at,promoted_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    f"generated-import-run-{run_number}", _sha(f"generated-manifest:{run_number}"),
                    json.dumps({"fixture": FIXTURE_KIND, "run": run_number}, sort_keys=True), "promoted",
                    "legacy-import", "2026-09-22T00:00:00Z", "2026-09-22T00:01:00Z",
                ),
            )
        for sequence in range(1, POST_COUNT + 1):
            run = 1 if sequence <= 23 else 2
            db.execute(
                "INSERT INTO import_observations(import_run_id,drive_file_id,post_uid,metadata_hash,result,warnings_json) "
                "VALUES (?,?,?,?,?,?)",
                (
                    f"generated-import-run-{run}", f"generated-drive-post-{sequence:04d}",
                    f"legacy-post-{sequence:04d}", _sha(f"legacy-observation:{sequence}"),
                    "warning" if 16 <= sequence <= 23 else "imported", "[]",
                ),
            )
        for sequence in range(1, ARTIFACT_COUNT + 1):
            run = 1 if sequence <= 5 else 2
            db.execute(
                "INSERT INTO import_observations(import_run_id,drive_file_id,post_uid,metadata_hash,result,warnings_json) "
                "VALUES (?,?,?,?,?,?)",
                (
                    f"generated-import-run-{run}", f"generated-drive-signature-{sequence:04d}",
                    None if sequence <= 2 else f"legacy-post-{sequence:04d}", _sha(f"legacy-artifact-observation:{sequence}"),
                    "orphan-artifact" if sequence <= 2 else "artifact", "[]",
                ),
            )
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        raise
    return db


def _table_rows(db: sqlite3.Connection, table: str):
    columns = [row[1] for row in db.execute(f"PRAGMA table_info({table})")]
    return [list(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY rowid")], columns


def logical_sha256(db: sqlite3.Connection) -> str:
    """Stable content hash of every generated historical row and key field."""
    tables = ("roots", "posts", "assignments", "artifacts", "import_runs", "import_observations")
    material = {table: {"columns": columns, "rows": rows} for table in tables for rows, columns in [_table_rows(db, table)]}
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def counts(db: sqlite3.Connection) -> dict[str, int]:
    return {
        name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        for name in ("roots", "posts", "assignments", "artifacts", "import_runs", "import_observations")
    }
