"""RED contracts for release-blocking TownSquare safety boundaries.

These tests describe externally observable security and integrity facts.  They
intentionally fail against the single-DB MVP until the corresponding boundary
is implemented; they do not bless a particular ORM, HTTP framework, or worker.
"""
from __future__ import annotations

import os
import tempfile
from unittest.mock import patch

from registrar.tests.mvp_fixture import GOVERNED_MANIFEST, MANIFEST, NativeLedgerCase, OPENING


class ReleaseBlockerNativeContracts(NativeLedgerCase):
    def test_rb_reg_01_registry_is_not_a_ledger_table_or_cross_db_transaction(self):
        tables = {row[0] for row in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        embedded = {"registry_agents", "registry_events", "registry_outbox"} & tables
        self.assertFalse(
            embedded,
            "RB-REG-01 requires a separate authenticated Registry service/DB with "
            "its own journal and retryable outbox; Registry rows in the Ledger DB "
            "permit cross-domain transaction/FK coupling and cannot prove independent restore.",
        )

    def test_rb_rcpt_02_persisted_receipt_bundle_and_item_hashes_are_revalidated(self):
        receipt = self.receipt()
        # This is a fault-injection copy of the local test DB, not a supported
        # mutation path.  A receipt must fail closed if its persisted binding
        # no longer names the original selected bundle.
        self.db.execute("DROP TRIGGER context_receipt_issues_no_update")
        self.db.execute(
            "UPDATE context_receipt_issues SET bundle_sha256=?",
            ("0" * 64,),
        )
        self.assert_code("context_required", self.post, receipt=receipt)

    def test_rb_rcpt_02_startup_rejects_default_missing_weak_or_unreadable_key_files(self):
        ledger_type = type(self.ledger)
        with tempfile.TemporaryDirectory() as directory:
            weak = os.path.join(directory, "weak.key")
            with open(weak, "w", encoding="utf-8") as handle:
                handle.write("weak")
            cases = {
                "missing": {"TOWNSQUARE_RECEIPT_HASH_KEY_FILE": os.path.join(directory, "absent.key")},
                "weak": {"TOWNSQUARE_RECEIPT_HASH_KEY_FILE": weak},
                # A directory is not a readable regular secret file on any
                # supported host, and avoids permission-mode assumptions.
                "unreadable": {"TOWNSQUARE_RECEIPT_HASH_KEY_FILE": directory},
            }
            for name, environment in cases.items():
                with self.subTest(key_file=name), patch.dict(os.environ, environment, clear=True):
                    with self.assertRaises(Exception, msg=(
                        "RB-RCPT-02 requires fail-closed receipt-key-file startup; "
                        "a compiled default key is forbidden and rotation must identify "
                        "the active persisted key."
                    )):
                        ledger_type(self.db, context_manifest=MANIFEST)

    def test_rb_chain_03_verification_follows_the_referenced_predecessor_hash(self):
        first = self.post()
        second = self.post(
            {**OPENING, "state": "WORKING"},
            principal="writer-b", key="chain-working", revision=first["event_id"],
        )
        # Corrupt the predecessor's stored commitment while retaining the
        # child's signed envelope.  Local envelope hashing alone is not a
        # chain verification; the referenced stored commitment must match.
        self.db.execute("DROP TRIGGER ledger_events_no_update")
        self.db.execute(
            "UPDATE ledger_events SET commit_sha256=? WHERE event_id=?",
            ("f" * 64, first["event_id"]),
        )
        self.assertFalse(
            self.ledger.verify_event(second["event_id"]),
            "RB-CHAIN-03 requires predecessor_commit_sha256 to be compared with "
            "the referenced predecessor's persisted commit hash.",
        )

    def test_rb_life_04_correction_needs_its_own_capability_and_target_authority(self):
        self.ledger.set_context_manifest(GOVERNED_MANIFEST)
        first = self.post(key="correction-open")
        correction = {
            **OPENING,
            "purpose": "CORRECTION",
            "corrects_event": first["event_id"],
            "body": "corrected wording",
        }
        # The fixture deliberately grants writer-a request:open but not a
        # correction capability.  A correction must not return early after a
        # normal state-action check and bypass separate target authority.
        receipt = self.receipt("writer-a", "request:open", "thread-alpha", first["event_id"])
        self.assert_code(
            "forbidden", self.ledger.post_event,
            "writer-a", "correction-without-capability", receipt, first["event_id"], correction,
        )

    def test_rb_restrict_05_every_restricted_row_requires_restricted_read_capability(self):
        self.post(
            {**OPENING, "thread_id": "restricted-release-blocker", "sensitivity": "RESTRICTED"},
            key="restricted-release-blocker",
        )
        for principal in ("writer-a", "writer-b", "reviewer", "viewer", "crier", "projector"):
            with self.subTest(principal=principal):
                self.assert_code(
                    "forbidden", self.ledger.get_thread,
                    "restricted-release-blocker", principal=principal,
                )
        self.assertEqual(
            "restricted-release-blocker",
            self.ledger.get_thread("restricted-release-blocker", principal="operator")["thread_id"],
        )

    def test_rb_auth_06_mounted_authority_flags_are_not_adoption_proof(self):
        # A manifest can name a candidate, but its own JSON flags must never
        # self-authorize writes without separately pinned authenticated
        # adoption bytes, signature, scope/window, revocation, and watermark.
        receipt = self.receipt()
        self.assert_code(
            "context_required", self.ledger.post_event,
            "writer-a", "mounted-authority-is-not-proof", receipt, "new", OPENING,
        )
