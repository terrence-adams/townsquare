"""Final Registry-v2 and recovery contracts.

These tests deliberately exercise release seams, not a particular framework.
They name the public boundaries needed to reproduce an upgrade or recovery
failure in a disposable deployment.
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class RegistryV2ReleaseContracts(unittest.TestCase):
    def text(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def _seed_registry_v1(self, db):
        """Exact populated v1 predecessor, before the reviewed v2 lease step."""
        statements=[]; current=""
        for line in self.text("registry/schema.sql").splitlines(True):
            current+=line
            if sqlite3.complete_statement(current): statements.append(current); current=""
        for statement in statements[:6]: db.execute(statement)
        db.execute("INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES('pending-v1','agent-1','register','{}','2026-10-06T00:00:00Z')")
        db.execute("INSERT INTO audit_outbox(event_id) VALUES('pending-v1')")
        db.commit()

    @contextmanager
    def registry_migrator(self, db_path):
        """Load the CLI's callable migration boundary against a disposable DB."""
        with patch.dict(os.environ, {"REGISTRY_DB": str(db_path)}, clear=False):
            module = importlib.reload(importlib.import_module("registry.migrate"))
            yield module

    def test_populated_registry_v1_upgrades_to_v2_and_rerun_preserves_pending_work(self):
        """A normal v1 DB upgrades once; re-running changes neither head nor outbox UUID."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry-v1.db"
            db = sqlite3.connect(path)
            try:
                self._seed_registry_v1(db)
                with self.registry_migrator(path) as migrator:
                    migrate = getattr(migrator, "migrate", None)
                    self.assertTrue(callable(migrate), "registry migrator must expose migrate(db) for a populated-v1 upgrade rehearsal")
                    if not callable(migrate):
                        return
                    migrate(db)
                    self.assertEqual([(1,), (2,)], list(db.execute("SELECT version FROM registry_migrations ORDER BY version")))
                    self.assertEqual(["pending-v1"], [r[0] for r in db.execute("SELECT event_id FROM audit_outbox")])
                    columns = {r[1] for r in db.execute("PRAGMA table_info(audit_outbox)")}
                    self.assertTrue({"lease_owner", "lease_until"} <= columns)
                    triggers = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
                    self.assertTrue(any("lease" in name for name in triggers), "v2 leases require DB-enforced transition guards")
                    migrate(db)
                    self.assertEqual([(1,), (2,)], list(db.execute("SELECT version FROM registry_migrations ORDER BY version")))
            finally:
                db.close()

    def test_registry_v2_failure_rolls_back_head_and_rows_then_clean_retry_succeeds(self):
        """Denying v2's version write is a concrete injected mid-upgrade failure."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry-v1-failure.db"
            db = sqlite3.connect(path)
            try:
                self._seed_registry_v1(db)
                with self.registry_migrator(path) as migrator:
                    migrate = getattr(migrator, "migrate", None)
                    self.assertTrue(callable(migrate), "registry migrator must expose migrate(db) for injected rollback/retry rehearsal")
                    if not callable(migrate):
                        return
                    def deny_v2_version_write(action, table, *_):
                        return sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_INSERT and table == "registry_migrations" else sqlite3.SQLITE_OK
                    db.set_authorizer(deny_v2_version_write)
                    with self.assertRaises(sqlite3.DatabaseError):
                        migrate(db)
                    db.set_authorizer(None)
                    self.assertEqual([(1,)], list(db.execute("SELECT version FROM registry_migrations")))
                    self.assertEqual(["pending-v1"], [r[0] for r in db.execute("SELECT event_id FROM audit_outbox")])
                    self.assertNotIn("lease_owner", {r[1] for r in db.execute("PRAGMA table_info(audit_outbox)")})
                    migrate(db)
                    self.assertEqual([(1,), (2,)], list(db.execute("SELECT version FROM registry_migrations ORDER BY version")))
            finally:
                db.close()

    def test_schema_and_v2_migration_allow_ack_but_reject_post_delivery_lease(self):
        from shared.registry_outbox import acknowledge_delivery
        with tempfile.TemporaryDirectory() as tmp:
            trigger_sql=[]
            for origin in ("fresh","migrated"):
                path=Path(tmp)/f"registry-{origin}.db"
                db=sqlite3.connect(path); db.row_factory=sqlite3.Row
                try:
                    if origin=="fresh":
                        event_id="event-1"
                        db.executescript(self.text("registry/schema.sql"))
                        db.execute("INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES('event-1','agent-1','register','{}','2026-10-06T00:00:00Z')")
                        db.execute("INSERT INTO audit_outbox(event_id) VALUES('event-1')")
                    else:
                        event_id="pending-v1"
                        self._seed_registry_v1(db); db.commit()
                        with self.registry_migrator(path) as migrator:migrator.migrate(db)
                    db.execute("UPDATE audit_outbox SET lease_owner='worker-1',lease_until='2026-10-06T00:01:00Z' WHERE event_id=?",(event_id,))
                    self.assertTrue(acknowledge_delivery(db,event_id,"worker-1","2026-10-06T00:02:00Z"))
                    self.assertFalse(acknowledge_delivery(db,event_id,"worker-1","2026-10-06T00:02:01Z"))
                    self.assertEqual((1,None,None),tuple(db.execute("SELECT attempts,lease_owner,lease_until FROM audit_outbox WHERE event_id=?",(event_id,)).fetchone()))
                    db.commit()
                    with self.assertRaisesRegex(sqlite3.IntegrityError,"delivered outbox cannot be leased"):
                        db.execute("UPDATE audit_outbox SET lease_owner='late-worker' WHERE event_id=?",(event_id,))
                    db.rollback()
                    trigger_sql.append(" ".join(db.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name='audit_outbox_lease_guard'").fetchone()[0].split()))
                finally:db.close()
            self.assertEqual(trigger_sql[0],trigger_sql[1],"fresh schema and v2 migrator must install the same lease guard")

    def test_registry_migration_owner_is_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "registry-v1-lock.db"
            db = sqlite3.connect(path)
            try:
                self._seed_registry_v1(db)
            finally:
                db.close()
            lock = path.with_suffix(".migration.lock")
            lock.write_text("held", encoding="utf-8")
            try:
                with self.registry_migrator(path) as migrator:
                    with self.assertRaisesRegex(SystemExit, "exclusive registry migration lock"):
                        migrator.main()
            finally:
                lock.unlink(missing_ok=True)

    def test_ledger_readiness_has_a_directional_registry_peer_credential(self):
        source = self.text("registrar/app/main.py")
        compose = self.text("compose.yml")
        self.assertIn("REGISTRY_PEER_READINESS_TOKEN_FILE", source,
                      "Ledger readiness must require a Registry-to-Ledger credential, not just query Registry")
        self.assertIn("registry peer readiness authorization required", source)
        self.assertIn("/health/ready", source)
        self.assertIn("registry_ledger_readiness_token", compose)
        self.assertIn("ledger_registry_readiness_token", compose,
                      "directions must use distinct secret material")
        self.assertIn("ledger_registry_readiness_token", self.text("registry/app.py"))

    def test_peer_readiness_credential_is_not_a_general_ledger_bearer_token(self):
        source = self.text("registrar/app/main.py")
        audit = self.text("registry/app.py")
        self.assertIn("REGISTRY_PEER_READINESS_TOKEN_FILE", source)
        self.assertIn("registry:audit:append", source,
                      "fixed Registry audit ingestion must keep a separately scoped credential")
        self.assertNotIn("post:write", source[source.index("def ready("):source.index("@app.post(\"/v1/roots/reserve\"")],
                         "peer readiness must not flow through normal write authorization")
        self.assertIn("LEDGER_AUDIT_TOKEN_FILE", audit)

    def test_restore_manifest_compares_every_domain_parity_field_before_replay(self):
        restore = self.text("backup/restore-drill.py")
        fields = ("row_counts", "schema_head", "ledger_watermark", "registry_journal_watermark", "lease_state")
        missing = [field for field in fields if field not in restore]
        self.assertEqual([], missing, f"restore must reject every tampered manifest parity field; missing checks: {missing}")
        self.assertIn("non_atomic_domains", restore,
                      "the independent domain restore must be explicitly labeled non-atomic")
        self.assertIn("manifest parity", restore.lower(),
                      "restore must compare captured metadata, not only SQLite integrity")

    def test_restore_replays_pending_event_through_fixed_authenticated_endpoint_once(self):
        restore = self.text("backup/restore-drill.py")
        replay = self.text("backup/recovery_replay_drill.py")
        self.assertNotIn("registry.app", restore,
                         "generic restore must stay offline and cannot import production delivery")
        self.assertNotIn("deliver_once", restore,
                         "generic restore reports pending UUIDs; a separate harness owns replay")
        self.assertIn("pending_event_uuids", restore)
        self.assertIn("deliver_once", replay)
        self.assertIn("exactly_once", replay.lower(),
                      "isolated recovery evidence must assert second replay leaves one Ledger inbox row")


if __name__ == "__main__":
    unittest.main()
