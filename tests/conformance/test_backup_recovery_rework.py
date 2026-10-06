from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT=Path(__file__).resolve().parents[2]

def load(name,relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class BackupRecoveryReworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.create=load("backup_create",Path("backup/create-backup.py"))
        cls.restore=load("backup_restore",Path("backup/restore-drill.py"))
        cls.replay=load("backup_replay",Path("backup/recovery_replay_drill.py"))

    def registry(self,path,*,version,lease=False):
        db=sqlite3.connect(path)
        db.executescript("""
            PRAGMA foreign_keys=ON;
            CREATE TABLE registry_migrations(version INTEGER PRIMARY KEY, applied_utc TEXT NOT NULL);
            CREATE TABLE journal(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,agent_id TEXT NOT NULL,action TEXT NOT NULL,body_json TEXT NOT NULL,committed_utc TEXT NOT NULL);
            CREATE TABLE audit_outbox(event_id TEXT PRIMARY KEY REFERENCES journal(event_id),attempts INTEGER NOT NULL DEFAULT 0,delivered_utc TEXT,last_error TEXT);
            INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES('pending-1','agent-1','register','{}','2026-10-06T00:00:00Z');
            INSERT INTO audit_outbox(event_id) VALUES('pending-1');
        """)
        db.execute("INSERT INTO registry_migrations VALUES(?,?)",(version,"2026-10-06T00:00:00Z"))
        if lease:
            db.execute("ALTER TABLE audit_outbox ADD COLUMN lease_owner TEXT")
            db.execute("ALTER TABLE audit_outbox ADD COLUMN lease_until TEXT")
            db.execute("UPDATE audit_outbox SET lease_owner='worker-1',lease_until='2026-10-06T00:01:00Z'")
        db.commit(); db.close()

    def test_registry_v1_backup_and_restore_parity_do_not_query_missing_lease_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"registry-v1.db"; copy=root/"copy.db"; self.registry(source,version=1)
            item=self.create.snapshot(source,copy)
            self.assertEqual({"supported":False,"rows":[]},item["lease_state"])
            db=sqlite3.connect(copy)
            try:self.assertEqual(item["lease_state"],self.restore.manifest_parity(db,{"domain":"registry",**item})["lease_state"])
            finally:db.close()

    def test_registry_v2_backup_and_restore_compare_exact_lease_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/"registry-v2.db"; copy=root/"copy.db"; self.registry(source,version=2,lease=True)
            item=self.create.snapshot(source,copy)
            self.assertEqual({"supported":True,"rows":[{"event_id":"pending-1","lease_owner":"worker-1","lease_until":"2026-10-06T00:01:00Z"}]},item["lease_state"])
            db=sqlite3.connect(copy)
            try:
                self.restore.manifest_parity(db,{"domain":"registry",**item})
                altered={"domain":"registry",**item,"lease_state":{"supported":True,"rows":[]}}
                with self.assertRaisesRegex(SystemExit,"manifest parity mismatch"):self.restore.manifest_parity(db,altered)
            finally:db.close()

    def test_generic_restore_is_offline_and_only_reports_pending_uuid_reconciliation(self):
        source=(ROOT/"backup/restore-drill.py").read_text(encoding="utf-8")
        self.assertNotIn("registry.app",source); self.assertNotIn("deliver_once",source)
        self.assertNotIn("urllib",source); self.assertIn("pending_event_uuids",source); self.assertIn("replay_performed",source)

    def test_isolated_replay_calls_fixed_delivery_twice_and_leaves_one_inbox_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            drill=Path(tmp); self.registry(drill/"registry.db",version=2,lease=True)
            ledger=sqlite3.connect(drill/"ledger.db")
            ledger.execute("""CREATE TABLE registry_audit_events(
                audit_seq INTEGER PRIMARY KEY AUTOINCREMENT,event_uuid TEXT NOT NULL UNIQUE,
                actor TEXT NOT NULL,board TEXT NOT NULL,canonical_payload TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,created_at TEXT NOT NULL,authenticated_principal TEXT)""")
            ledger.commit(); ledger.close()
            (drill/"reconciliation.json").write_text(json.dumps({"schema":"townsquare-offline-reconciliation-v1","origin":"restored-drill-only","pending_event_uuids":["pending-1"],"replay_performed":False}),encoding="utf-8")
            token=drill/"drill-replay.token"; token.write_bytes(b"isolated-recovery-drill-token-0123456789")
            evidence=self.replay.run_replay(drill,token)
            self.assertTrue(evidence["exactly_once"]); self.assertEqual({"pending-1":2},evidence["attempts_per_event"])
            ledger=sqlite3.connect(drill/"ledger.db")
            try:
                self.assertEqual(1,ledger.execute("SELECT count(*) FROM registry_audit_events WHERE event_uuid='pending-1'").fetchone()[0])
                boundary=self.replay.FixedDrillDelivery(ledger,token.read_bytes())
                with self.assertRaises(PermissionError):boundary.deliver_once("pending-1",b"wrong-drill-credential")
                self.assertEqual(1,ledger.execute("SELECT count(*) FROM registry_audit_events WHERE event_uuid='pending-1'").fetchone()[0])
            finally:ledger.close()

    def test_replay_rejects_non_drill_credentials_and_has_no_network_origin(self):
        source=(ROOT/"backup/recovery_replay_drill.py").read_text(encoding="utf-8")
        for forbidden in ("urllib","http://","https://","LEDGER_AUDIT_URL","REGISTRY_LEDGER_AUDIT_TOKEN_FILE"):
            self.assertNotIn(forbidden,source)
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            drill=Path(tmp); (drill/"ledger.db").write_bytes(b""); (drill/"registry.db").write_bytes(b"")
            (drill/"reconciliation.json").write_text("{}",encoding="utf-8")
            token=Path(outside)/"token"; token.write_bytes(b"isolated-recovery-drill-token-0123456789")
            with self.assertRaisesRegex(SystemExit,"inside the restored drill"):self.replay.run_replay(drill,token)

    def test_backup_image_packages_both_offline_restore_entrypoints(self):
        dockerfile=(ROOT/"backup/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("restore-drill.py",dockerfile); self.assertIn("recovery_replay_drill.py",dockerfile)
        self.assertIn("/usr/local/bin/age",dockerfile); self.assertIn("/usr/local/bin/minisign",dockerfile)


if __name__=="__main__":unittest.main()
