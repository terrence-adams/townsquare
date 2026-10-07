"""Real-shape, deterministic rehearsal of the historical 009 -> 014 upgrade.

The checked-in fixture is intentionally generated from the recorded aggregate
inventory, not a copied NAS database.  See fixtures/schema_009_1070.py and
its metadata sidecar for the disclosure boundary and source measurements.
"""
from __future__ import annotations

import inspect
import importlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from registrar.app import db as db_module
from registrar.app.db import MIGRATIONS, migrate, verify_schema
from registrar.tests.fixtures import schema_009_1070 as fixture
from registrar.tests.mvp_fixture import NativeLedgerCase


EXPECTED_HEAD = 14
CANONICAL_COMPATIBILITY_TUPLE = {
    "ledger_service": "townsquare-ledger-v0",
    "ledger_schema": "14",
    "registry_service": "townsquare-registry-v0",
    "registry_schema": "2",
    "audit_contract": "registry-ledger-audit-v1",
}
EXPECTED_LEGACY_COUNTS = {
    "roots": 313,
    "posts": 1070,
    "assignments": 1062,
    "artifacts": 197,
    "import_runs": 2,
    "import_observations": 1267,
}
EXPECTED_BOARD_COUNTS = {
    "requests": 743,
    "bulletin-board": 307,
    "seeking": 16,
    "wanted": 4,
}
MIGRATION_TABLES = {
    "ledger_events", "event_content", "native_requests", "notice_intents", "notice_attempts", "ledger_audit",
    "context_bundles", "context_receipt_issues", "context_receipt_consumptions", "context_audit", "control_events",
    "logical_archives", "context_bundle_items", "governance_resolution_audit", "thread_continuations", "archive_requests",
    "legacy_embedded_registry_agents", "legacy_embedded_registry_events", "legacy_embedded_registry_outbox",
}
ACTIVE_EMBEDDED_REGISTRY_TABLES = {"registry_agents", "registry_events", "registry_outbox"}


def versions(db):
    return [row[0] for row in db.execute("SELECT version FROM schema_migrations ORDER BY version")]


def schema_snapshot(db):
    return [tuple(row) for row in db.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    )]


class Schema009To014RehearsalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "generated-schema-009.db"
        self.db = fixture.build(self.path)
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(lambda: self.db.close())

    def _replace_fixture(self, label):
        self.db.close()
        self.path = Path(self.tmp.name) / f"generated-schema-009-{label}.db"
        self.db = fixture.build(self.path)

    def _legacy_assertions(self, before_hash):
        self.assertEqual(EXPECTED_LEGACY_COUNTS, fixture.counts(self.db))
        self.assertEqual(before_hash, fixture.logical_sha256(self.db))
        self.assertEqual(
            EXPECTED_BOARD_COUNTS,
            dict(self.db.execute("SELECT board,count(*) FROM posts GROUP BY board ORDER BY board")),
        )
        self.assertEqual(0, self.db.execute("SELECT count(*) FROM posts WHERE drive_created_at IS NULL").fetchone()[0])
        self.assertEqual(1070, self.db.execute("SELECT count(*) FROM posts WHERE source='legacy_import'").fetchone()[0])
        if self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ledger_events'").fetchone():
            self.assertEqual(0, self.db.execute("SELECT count(*) FROM ledger_events").fetchone()[0])
        self.assertGreater(self.db.execute("SELECT count(*) FROM posts WHERE state='IN_PROGRESS'").fetchone()[0], 0)

    def _copy_migrations(self, folder, first, last, broken=None):
        for version in range(first, last + 1):
            source = next(MIGRATIONS.glob(f"{version:03d}_*.sql"))
            content = source.read_text(encoding="utf-8")
            if version == broken:
                content += "\nCREATE TABLE migration_must_rollback(x);\nTHIS IS INVALID SQL;\n"
            (folder / source.name).write_text(content, encoding="utf-8")

    def _seed_pre014_registry_evidence(self):
        payload = "{\"fixture\":\"registry-evidence\"}"
        digest = "a" * 64
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT INTO registry_agents VALUES (?,?,?,?,?)", ("fixture-agent", "active", payload, "registry-event-1", "2026-10-06T00:00:00Z"))
            self.db.execute("INSERT INTO registry_events VALUES (?,?,?,?,?,?)", ("registry-event-1", "register", "fixture-agent", "registry", payload, "2026-10-06T00:00:00Z"))
            self.db.execute("INSERT INTO registry_outbox VALUES (?,?,?,?)", ("registry-event-1", payload, digest, "2026-10-06T00:00:00Z"))
            self.db.execute("INSERT INTO registry_audit_events(event_uuid,actor,board,canonical_payload,payload_sha256,created_at) VALUES (?,?,?,?,?,?)", ("registry-audit-1", "registry", "BOARD-AUDIT-RECORD", payload, digest, "2026-10-06T00:00:00Z"))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def test_generated_fixture_is_schema_009_and_records_the_measured_legacy_shape(self):
        metadata = json.loads((Path(__file__).parent / "fixtures" / "schema_009_1070_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual("generated-representative-schema-009", metadata["fixture_kind"])
        self.assertEqual(list(range(1, 10)), versions(self.db))
        self.assertEqual(EXPECTED_LEGACY_COUNTS, fixture.counts(self.db))
        self.assertEqual(EXPECTED_BOARD_COUNTS, metadata["board_counts"])
        self.assertEqual(metadata["logical_sha256"], fixture.logical_sha256(self.db))
        self.assertEqual(["ok"], [row[0] for row in self.db.execute("PRAGMA integrity_check")])
        self.assertEqual([], list(self.db.execute("PRAGMA foreign_key_check")))

    def test_upgrade_preserves_every_historical_row_and_re_run_is_a_noop(self):
        historical_hash = fixture.logical_sha256(self.db)
        migrate(self.db)
        self._legacy_assertions(historical_hash)
        self.assertEqual(list(range(1, EXPECTED_HEAD + 1)), versions(self.db))
        self.assertEqual(EXPECTED_HEAD, verify_schema(self.db))
        names = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue(MIGRATION_TABLES <= names)
        self.assertFalse(ACTIVE_EMBEDDED_REGISTRY_TABLES & names)
        self.assertEqual(["ok"], [row[0] for row in self.db.execute("PRAGMA integrity_check")])
        self.assertEqual([], list(self.db.execute("PRAGMA foreign_key_check")))
        before_versions, before_schema = versions(self.db), schema_snapshot(self.db)
        migrate(self.db)
        self.assertEqual(before_versions, versions(self.db))
        self.assertEqual(before_schema, schema_snapshot(self.db))
        self._legacy_assertions(historical_hash)

    def test_every_010_to_014_failure_is_atomic_and_a_clean_retry_succeeds(self):
        historical_hash = fixture.logical_sha256(self.db)
        contract_rows = dict(db_module._contract_rows()[1])
        real_apply = db_module._apply_migration
        for target in range(10, 15):
            with self.subTest(failing_migration=target):
                if target > 10:
                    self.db.execute("BEGIN EXCLUSIVE")
                    for version in range(10, target):
                        real_apply(self.db, version, contract_rows[version])
                    self.db.commit()
                if target == 14:
                    self._seed_pre014_registry_evidence()
                expected_versions = list(range(1, target))
                before_schema = schema_snapshot(self.db)

                def fail_at_target(db, version, path):
                    if version == target:
                        raise sqlite3.OperationalError("injected migration failure")
                    return real_apply(db, version, path)

                with patch.object(db_module, "_apply_migration", fail_at_target):
                    with self.assertRaises(sqlite3.OperationalError):
                        migrate(self.db)
                self.assertEqual(expected_versions, versions(self.db))
                self.assertEqual(before_schema, schema_snapshot(self.db), "failing migration left DDL behind")
                self._legacy_assertions(historical_hash)
                if target == 14:
                    names = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    self.assertTrue(ACTIVE_EMBEDDED_REGISTRY_TABLES <= names)
                    self.assertFalse({name for name in names if name.startswith("legacy_embedded_registry_")})
                    self.assertEqual(1, self.db.execute("SELECT count(*) FROM registry_audit_events").fetchone()[0])
                migrate(self.db)
                self.assertEqual(list(range(1, EXPECTED_HEAD + 1)), versions(self.db))
                self._legacy_assertions(historical_hash)
                self.assertEqual(["ok"], [row[0] for row in self.db.execute("PRAGMA integrity_check")])
                self.assertEqual([], list(self.db.execute("PRAGMA foreign_key_check")))
                if target == 14:
                    names = {row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    self.assertFalse(ACTIVE_EMBEDDED_REGISTRY_TABLES & names)
                    self.assertEqual(1, self.db.execute("SELECT count(*) FROM legacy_embedded_registry_outbox").fetchone()[0])
                    self.assertIsNone(self.db.execute("SELECT authenticated_principal FROM registry_audit_events").fetchone()[0])
            self._replace_fixture(target)

    def test_storage_rejects_an_obsolete_native_request_state_without_rewriting_legacy_projection(self):
        historical_hash = fixture.logical_sha256(self.db)
        migrate(self.db)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "unsupported Request lifecycle state"):
            self.db.execute(
                "INSERT INTO ledger_events(event_id,thread_id,thread_ordinal,post_uid,predecessor_event_id,predecessor_commit_sha256,kind,state,owner,addressee,sensitivity,metadata_json,metadata_sha256,body_sha256,body_byte_length,principal,represented_actor,claimed_origin,authority_scope,committed_at,commit_sha256) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("invalid-native-state", "native-fixture-thread", 0, None, None, None, "REQUEST", "IN_PROGRESS", "owner", "addressee", "INTERNAL", "{}", "b" * 64, "c" * 64, 0, "fixture", "fixture", "fixture", "fixture", "2026-10-06T00:00:00Z", "d" * 64),
            )
        self.assertEqual(0, self.db.execute("SELECT count(*) FROM ledger_events").fetchone()[0])
        self._legacy_assertions(historical_hash)

    def test_ledger_has_one_schema_writer_and_runtime_only_verifies_the_exact_release(self):
        main_source = (Path(__file__).parents[1] / "app" / "main.py").read_text(encoding="utf-8")
        db_source = inspect.getsource(db_module)
        self.assertIn("def migrate(", db_source)
        self.assertIn("def verify_schema(", db_source)
        self.assertIn("_verify_schema_at_boot", main_source)
        self.assertNotIn("migrate(", main_source)

    def test_ledger_runtime_advertises_the_pinned_tuple_and_fails_closed_before_audit_write(self):
        main_source = (Path(__file__).parents[1] / "app" / "main.py").read_text(encoding="utf-8")
        ledger_source = (Path(__file__).parents[1] / "app" / "native_ledger.py").read_text(encoding="utf-8")
        db_source = (Path(__file__).parents[1] / "app" / "db.py").read_text(encoding="utf-8")
        for expected in (
            "REGISTRY_INTEGRATION_ENABLED", "REGISTRY_SERVICE_VERSION", "REGISTRY_SCHEMA_VERSION",
            "REGISTRY_AUDIT_CONTRACT_VERSION",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, main_source + ledger_source + db_source)
        for expected in (CANONICAL_COMPATIBILITY_TUPLE["ledger_service"], CANONICAL_COMPATIBILITY_TUPLE["audit_contract"]):
            self.assertIn(expected, main_source + ledger_source + db_source)
        canonical = {
            "REGISTRY_INTEGRATION_ENABLED": "true",
            "REGISTRY_SERVICE_VERSION": CANONICAL_COMPATIBILITY_TUPLE["registry_service"],
            "REGISTRY_SCHEMA_VERSION": CANONICAL_COMPATIBILITY_TUPLE["registry_schema"],
            "REGISTRY_AUDIT_CONTRACT_VERSION": CANONICAL_COMPATIBILITY_TUPLE["audit_contract"],
        }
        with patch.dict(os.environ, canonical, clear=False):
            self.assertTrue(db_module.registry_integration_status()["compatible"])
        for key, expected in canonical.items():
            if key == "REGISTRY_INTEGRATION_ENABLED":
                continue
            with self.subTest(mismatched_member=key), patch.dict(os.environ, {**canonical, key: "wrong-" + expected}, clear=False):
                self.assertFalse(db_module.registry_integration_status()["compatible"])
        self.assertLess(ledger_source.index("registry = registry_integration_status()"), ledger_source.index("existing = self.db.execute", ledger_source.index("def append_registry_audit")))

    def test_compose_names_two_isolated_one_shot_migrators_and_runtime_dependencies(self):
        """Rendered Compose must make the per-domain ownership boundary visible."""
        compose = (Path(__file__).parents[2] / "compose.yml").read_text(encoding="utf-8")
        self.assertIn("  ledger-migrate:\n", compose)
        self.assertIn("  registry-migrate:\n", compose)
        self.assertIn("ledger-migrate: {condition: service_completed_successfully}", compose)
        self.assertIn("registry-migrate: {condition: service_completed_successfully}", compose)
        ledger_service = compose[compose.index("  ledger-migrate:\n"):compose.index("  ledger:\n")]
        registry_service = compose[compose.index("  registry-migrate:\n"):compose.index("  backup:\n")]
        self.assertIn("TOWNSQUARE_LEDGER_DATA_DIR", ledger_service)
        self.assertNotIn("TOWNSQUARE_REGISTRY_DATA_DIR", ledger_service)
        self.assertIn("TOWNSQUARE_REGISTRY_DATA_DIR", registry_service)
        self.assertNotIn("TOWNSQUARE_LEDGER_DATA_DIR", registry_service)
        self.assertNotIn("ports:", registry_service)

    def test_release_pins_the_full_service_schema_and_audit_contract_tuple(self):
        """An audit-contract-only check is insufficient: the release pins all five values."""
        compose = (Path(__file__).parents[2] / "compose.yml").read_text(encoding="utf-8")
        ledger_source = (Path(__file__).parents[1] / "app" / "main.py").read_text(encoding="utf-8")
        registry_source = (Path(__file__).parents[2] / "registry" / "app.py").read_text(encoding="utf-8")
        release_inputs = compose + ledger_source + registry_source
        for expected in CANONICAL_COMPATIBILITY_TUPLE.values():
            with self.subTest(expected=expected):
                self.assertIn(expected, release_inputs)
        self.assertIn("TOWNSQUARE_SERVICE_ID: townsquare-ledger-v0", compose)
        self.assertIn('TOWNSQUARE_LEDGER_SCHEMA_HEAD: "14"', compose)
        self.assertIn("TOWNSQUARE_REGISTRY_AUDIT_CONTRACT: registry-ledger-audit-v1", compose)
        self.assertIn("REGISTRY_SERVICE_ID: townsquare-registry-v0", compose)
        self.assertIn('REGISTRY_SCHEMA_HEAD: "2"', compose)
        self.assertIn("REGISTRY_LEDGER_SERVICE_ID: townsquare-ledger-v0", compose)
        self.assertIn('REGISTRY_LEDGER_SCHEMA_HEAD: "14"', compose)
        self.assertIn("REGISTRY_AUDIT_CONTRACT_VERSION: registry-ledger-audit-v1", compose)
        self.assertIn("REGISTRY_LEDGER_AUDIT_CONTRACT: registry-ledger-audit-v1", compose)

    def test_competing_ledger_migrator_cannot_enter_the_same_domain(self):
        lock_holder = sqlite3.connect(self.path, timeout=0, isolation_level=None)
        contender = sqlite3.connect(self.path, timeout=0, isolation_level=None)
        try:
            lock_holder.execute("BEGIN EXCLUSIVE")
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                migrate(contender)
            self.assertEqual(list(range(1, 10)), versions(self.db))
        finally:
            lock_holder.rollback()
            lock_holder.close()
            contender.close()

    def test_registry_migrator_lock_and_compatibility_mismatch_retain_the_outbox(self):
        registry_db = Path(self.tmp.name) / "registry.db"
        schema = (Path(__file__).parents[2] / "registry" / "schema.sql").read_text(encoding="utf-8")
        db = sqlite3.connect(registry_db)
        try:
            db.executescript(schema)
            db.execute("INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES (?,?,?,?,?)", ("event-1", "agent-1", "register", "{}", "2026-10-06T00:00:00Z"))
            db.execute("INSERT INTO audit_outbox(event_id) VALUES ('event-1')")
            db.commit()
        finally:
            db.close()
        lock = registry_db.with_suffix(".migration.lock")
        lock.write_text("held", encoding="utf-8")
        old_db = os.environ.get("REGISTRY_DB")
        try:
            os.environ["REGISTRY_DB"] = str(registry_db)
            migrate_module = importlib.reload(importlib.import_module("registry.migrate"))
            with self.assertRaisesRegex(SystemExit, "exclusive registry migration lock"):
                migrate_module.main()
        finally:
            if old_db is None:
                os.environ.pop("REGISTRY_DB", None)
            else:
                os.environ["REGISTRY_DB"] = old_db
            lock.unlink(missing_ok=True)
        identity = SimpleNamespace(
            runtime_class="CANARY", authority_class="NON-AUTHORITATIVE",
            canary_label="TS-CANARY-NAS1-20261007-A",
            compose_project="townsquare-canary-20261007-a",
            source_commit="a" * 40, source_tree="b" * 40,
            r7_release_id="TS-R7-" + "c" * 64,
            r7_input_manifest_sha256="d" * 64,
        )
        with patch("shared.canary_identity.require_canary_identity", return_value=identity), patch(
            "shared.canary_authority.load_r7_context", return_value="e" * 64
        ):
            registry_app = importlib.import_module("registry.app")
        canonical_environment = {
            "REGISTRY_SERVICE_ID": CANONICAL_COMPATIBILITY_TUPLE["registry_service"],
            "REGISTRY_SCHEMA_HEAD": CANONICAL_COMPATIBILITY_TUPLE["registry_schema"],
            "REGISTRY_AUDIT_CONTRACT_VERSION": CANONICAL_COMPATIBILITY_TUPLE["audit_contract"],
            "REGISTRY_LEDGER_SERVICE_ID": CANONICAL_COMPATIBILITY_TUPLE["ledger_service"],
            "REGISTRY_LEDGER_SCHEMA_HEAD": CANONICAL_COMPATIBILITY_TUPLE["ledger_schema"],
            "REGISTRY_LEDGER_AUDIT_CONTRACT": CANONICAL_COMPATIBILITY_TUPLE["audit_contract"],
        }
        for key, expected in canonical_environment.items():
            with self.subTest(mismatched_member=key), patch.object(registry_app, "DB", registry_db), patch.object(registry_app, "LEDGER_AUDIT_URL", "http://127.0.0.1:1/never"), patch.dict(os.environ, {**canonical_environment, key: "wrong-" + expected}, clear=False):
                self.assertFalse(registry_app.compatible())
                registry_app.deliver_once()
            check = sqlite3.connect(registry_db)
            try:
                self.assertEqual((0, None), check.execute("SELECT attempts,delivered_utc FROM audit_outbox WHERE event_id='event-1'").fetchone())
            finally:
                check.close()


class LedgerRegistryCompatibilityGateTests(NativeLedgerCase):
    """The Ledger rejects an enabled mismatched Registry before its audit inbox."""

    def test_enabled_registry_tuple_gates_audit_before_lookup_or_write(self):
        canonical = {
            "REGISTRY_INTEGRATION_ENABLED": "true",
            "REGISTRY_SERVICE_ID": CANONICAL_COMPATIBILITY_TUPLE["registry_service"],
            "REGISTRY_SCHEMA_HEAD": CANONICAL_COMPATIBILITY_TUPLE["registry_schema"],
            "REGISTRY_AUDIT_CONTRACT_VERSION": CANONICAL_COMPATIBILITY_TUPLE["audit_contract"],
        }
        payload = {"board": "BOARD-AUDIT-RECORD", "actor": "registry", "event_uuid": "compatible-audit-event"}
        with patch.dict(os.environ, canonical, clear=False):
            self.assertEqual("compatible-audit-event", self.ledger.append_registry_audit("registry-audit", payload)["event_uuid"])
        before = self.db.execute("SELECT count(*) FROM registry_audit_events").fetchone()[0]
        bad_payload = {**payload, "event_uuid": "blocked-audit-event"}
        with patch.dict(os.environ, {**canonical, "REGISTRY_SCHEMA_HEAD": "wrong-2"}, clear=False):
            self.assert_code("unavailable", self.ledger.append_registry_audit, "registry-audit", bad_payload)
        self.assertEqual(before, self.db.execute("SELECT count(*) FROM registry_audit_events").fetchone()[0])
        self.assertIsNone(self.db.execute("SELECT 1 FROM registry_audit_events WHERE event_uuid=?", (bad_payload["event_uuid"],)).fetchone())


if __name__ == "__main__":
    unittest.main()
