"""WS2b taxonomy tests -- jackie-chan, Town Registrar dry-run (revision-2 work order).

Pure-fixture tests, no live Drive data (the project's #1 cost-control rule:
no agent, and no test, reads the real board corpus). Fixtures here mirror the
exact row shape tony-jaa's collector (merge_inventory.py) produces.

A second, larger, standalone fixture proving cross-PROCESS determinism (the
concern this repo-local unittest.TestCase can't exercise on its own, since
one Python process has one fixed PYTHONHASHSEED for its whole lifetime) lives
outside the repo at:

    C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\

Reproduce that proof yourself with (PowerShell, repo root):

    python "C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\build_fixture.py"
    python -m registrar.importer.legacy `
        "C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\inventory.json" `
        --output "C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\run1.json"
    python -m registrar.importer.legacy `
        "C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\inventory.json" `
        --output "C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\run2.json"
    Get-FileHash "C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\run1.json"
    Get-FileHash "C:\\Workspace\\townsquare-registrar-dryrun\\wsb2-fixtures\\run2.json"

The two SHA-256 hashes must match (they did, at the time this was written).
"""
import unittest

from registrar.importer.legacy import plan


def _row(drive_file_id, name, parent_folder_path, **overrides):
    base = {
        "drive_file_id": drive_file_id,
        "name": name,
        "parent_folder_path": parent_folder_path,
        "is_dir": False,
        "mime_type": "text/plain",
        "created_time": "2026-09-21T00:00:00Z",
        "modified_time": "2026-09-21T00:00:00Z",
        "size": 512,
        "trashed": False,
        "provider_checksum": "d41d8cd98f00b204e9800998ecf8427e",
        "provider_checksum_algo": "md5",
        "content_sha256": None,
        "content_sha256_status": "not_computed_dry_run",
        "collector_defect": None,
    }
    base.update(overrides)
    return base


def _inventory(rows):
    """Wrap rows in the real collector's dict shape (collected_at_utc,
    remote, rows, ...) so the planner is exercised against the shape it will
    actually see in the live run, not just the bare-list shape the
    pre-existing tests use."""
    return {
        "collected_at_utc": "2026-09-21T00:00:00Z",
        "remote": "gdrive:N3rd0m/TownSquare",
        "remote_scope": "drive.readonly",
        "deferred": [
            "design_step_3_header_signature_verdicts",
            "design_step_9_webviewlink_canonical_url",
        ],
        "rows": rows,
    }


class LegacyTaxonomyTests(unittest.TestCase):
    def test_accepts_bare_list_and_wrapped_dict_identically(self):
        rows = [_row("a1", "TS-20260921-cable-001.000-OPEN__by-cable.txt", "Requests")]
        self.assertEqual(plan(rows), plan(_inventory(rows)))

    def test_duplicate_sequence_same_thread_different_authors(self):
        rows = [
            _row("d01", "TS-20260906-016.002-RESOLVED__by-cable.txt", "Requests"),
            _row("d02", "TS-20260906-016.002-WORKING__by-forge.txt", "Requests"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(2, report["counts"]["duplicate_sequences"])
        self.assertEqual(0, report["counts"]["duplicate_openings"])
        self.assertEqual({"d01", "d02"}, {c["drive_file_id"] for c in report["duplicate_sequences"]})
        # both still importable posts, just renumbered above the observed max
        self.assertEqual(2, len(report["posts"]))
        post_nos = sorted(p["post_no"] for p in report["posts"])
        # Design section 9 step 7: duplicate/conflicting observations receive
        # stable post_no values strictly ABOVE the root's maximum observed
        # legacy sequence -- both colliding duplicates are bumped (neither
        # retains legacy_seq=2 as its post_no), matching the pre-existing,
        # unmodified collision-assignment logic in this file.
        self.assertEqual([3, 4], post_nos)
        self.assertTrue(all(p["legacy_seq"] == 2 for p in report["posts"]))

    def test_duplicate_opening_is_a_separate_class_from_duplicate_sequence(self):
        rows = [
            _row("d18", "TS-20260917-cable-030.000-OPEN__by-cable.txt", "Requests"),
            _row("d19", "TS-20260917-cable-030.000-WORKING__by-forge.txt", "Requests"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(2, report["counts"]["duplicate_openings"])
        self.assertEqual(0, report["counts"]["duplicate_sequences"])
        # never merged: appearing in one bucket excludes the other
        self.assertEqual([], report["duplicate_sequences"])

    def test_grammar_b_offer_host_field_classified_without_touching_parser(self):
        rows = [_row(
            "d03",
            "OFFER-20260907-jeangrey-001.000-OPEN__host-jeangrey__client-work-laptop-full-capability-intermittent.txt",
            "Seeking",
        )]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["grammar_b_offer_host_field"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])
        self.assertEqual(0, report["counts"]["hard_rejections"])
        self.assertEqual(0, len(report["posts"]))  # never silently imported with wrong data

    def test_standalone_md_want_is_legacy_nonconforming_not_quarantined(self):
        rows = [_row("d04", "WANT-20260907-001__skill__kollective-display-timeout-debugging.md", "Wanted")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["legacy_nonconforming"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])

    def test_gdoc_txt_pair_native_doc_isolated_from_its_txt_sibling(self):
        rows = [
            _row("d05", "BB-20260911-forge-001.000-POST__pending-confirmation.gdoc", "Bulletin Board",
                 mime_type="application/vnd.google-apps.document", provider_checksum=None, provider_checksum_algo=None),
            _row("d06", "BB-20260911-forge-001.000-POST__pending-confirmation.txt", "Bulletin Board"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["native_doc_objects"])
        native = report["native_doc_objects"][0]
        self.assertIsNone(native["content_sha256"])
        self.assertEqual("native_google_doc", native["reason"])
        self.assertFalse(native["reissued_as_txt"])
        # the sibling .txt parses normally and is untouched by the .gdoc
        self.assertEqual(1, len(report["posts"]))
        self.assertEqual("d06", report["posts"][0]["drive_file_id"])

    def test_native_doc_detected_by_mime_type_even_with_no_gdoc_suffix(self):
        """Part 1 review finding: rclone's actual native-Doc naming in
        v1.75.1 (no --drive-export-formats set) is exactly as unconfirmed as
        the shortcut question tony-jaa flagged. A bare Drive name with no
        synthesized extension at all must still classify correctly via
        mime_type, which the Drive API always reports accurately."""
        rows = [_row("d05x", "BB-20260911-forge-001.000-POST__pending-confirmation", "Bulletin Board",
                      mime_type="application/vnd.google-apps.document",
                      provider_checksum=None, provider_checksum_algo=None)]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["native_doc_objects"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])

    def test_folder_and_shortcut_mime_types_are_not_native_docs(self):
        rows = [
            _row("f1", "Requests", "", is_dir=True, mime_type="application/vnd.google-apps.folder"),
            _row("s1", "TS-20260920-cable-060.000-OPEN__by-cable.txt", "Requests",
                 mime_type="application/vnd.google-apps.shortcut"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(0, report["counts"]["native_doc_objects"])
        # the shortcut-mimetype row still has a normal post-shaped .txt name,
        # so it parses as an ordinary post -- see the review notes on why
        # shortcut RESOLUTION itself can't be verified without a live run.
        self.assertEqual(1, len(report["posts"]))

    def test_md_in_non_board_folder_is_non_post_artifact_not_a_corpus_exception(self):
        rows = [_row("d07", "ACCURACY-PROTOCOL-v0.2-20260909.md", "Reliability")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["non_post_artifacts"])
        self.assertEqual(0, report["counts"]["legacy_nonconforming"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])

    def test_txt_at_board_root_is_also_non_post_artifact(self):
        """jigoro-kano's WS1 finding generalized: the folder gate isn't
        extension-specific. A .txt at board root (the real doctrine file's
        own shape) must not be attempted against the post parser at all."""
        rows = [_row("d08", "TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt", "")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["non_post_artifacts"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])

    def test_unsigned_post_is_a_class_not_an_error(self):
        rows = [_row("d09", "TS-20260910-cable-002.000-OPEN__by-cable.txt", "Requests")]
        report = plan(_inventory(rows))
        self.assertEqual(1, len(report["posts"]))  # still imported
        self.assertEqual(1, report["counts"]["unsigned_posts"])

    def test_orphan_sidecar(self):
        rows = [_row("d10", "TS-20260910-cable-099.000-OPEN__by-cable.txt.sig", "Requests")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["orphan_sidecars"])
        self.assertEqual(["orphan_signature"], report["artifacts"][0]["warnings"])
        self.assertIsNone(report["artifacts"][0]["parent_post_uid"])

    def test_for_slug_is_silent_absorption_counted_but_still_imported(self):
        rows = [_row("d11", "TS-20260912-cable-005.000-OPEN__by-cable__for-teardown-notes.txt", "Requests")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["silent_typed_field_absorption"])
        self.assertEqual("for", report["silent_typed_field_absorption"][0]["field"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])
        self.assertEqual(0, report["counts"]["hard_rejections"])
        self.assertEqual(1, len(report["posts"]))  # parse succeeded; flagged, not rejected

    def test_mode_x_is_hard_rejection_distinct_from_silent_absorption(self):
        rows = [_row("d12", "TS-20260913-cable-006.000-OPEN__by-cable__mode-urgent.txt", "Requests")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["hard_rejections"])
        self.assertEqual("unsupported mode", report["hard_rejections"][0]["reason"])
        self.assertEqual(0, report["counts"]["silent_typed_field_absorption"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])
        self.assertEqual(0, len(report["posts"]))

    def test_noncanonical_pid_is_also_hard_rejection(self):
        rows = [_row("d12b", "TS-20260913-cable-006.000-OPEN__by-cable__pid-not-a-ulid.txt", "Requests")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["hard_rejections"])
        self.assertEqual("noncanonical pid", report["hard_rejections"][0]["reason"])

    def test_genuinely_corrupt_name_still_reaches_generic_quarantine(self):
        rows = [_row("d25", "NOT-A-VALID-POST-NAME.txt", "Requests")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["quarantined_invalid_name"])
        self.assertEqual(0, report["counts"]["hard_rejections"])

    def test_missing_drive_file_id_pre_tagged_is_collector_defect_not_corpus_exception(self):
        rows = [_row(None, "TS-20260914-cable-007.000-OPEN__by-cable.txt", "Requests",
                      collector_defect="missing_drive_file_id")]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["collector_defects"])
        for bucket in ("posts", "quarantined", "hard_rejections", "non_post_artifacts"):
            self.assertEqual([], report[bucket], f"collector defect leaked into {bucket}")

    def test_missing_drive_file_id_without_upstream_tag_is_still_caught(self):
        """Part 1 review point: the planner must not blindly trust the
        collector's own collector_defect tag -- it independently re-verifies
        drive_file_id truthiness, so a bug in the tagging can't crash uuid5
        generation or silently misclassify the row."""
        rows = [_row(None, "TS-20260919-cable-050.000-OPEN__by-cable.txt", "Requests")]  # no collector_defect key value
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["collector_defects"])
        self.assertEqual("missing_drive_file_id", report["collector_defects"][0]["collector_defect"])
        self.assertEqual([], report["posts"])

    def test_directory_entries_excluded_from_every_bucket(self):
        rows = [_row("d23", "Requests", "", is_dir=True, mime_type="application/vnd.google-apps.folder",
                      provider_checksum=None, provider_checksum_algo=None)]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["directories_excluded"])
        for key, value in report["counts"].items():
            if key != "directories_excluded":
                self.assertEqual(0, value, f"directory leaked into {key}")

    def test_ambiguous_unnamespaced_alias(self):
        rows = [
            _row("d16", "TS-20260916-020.000-OPEN__by-cable.txt", "Requests"),
            _row("d17", "TS-20260916-cable-020.000-OPEN__by-forge.txt", "Requests"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(2, report["counts"]["ambiguous_unnamespaced_aliases"])
        namespaces = {a["namespace"] for a in report["ambiguous_unnamespaced_aliases"]}
        self.assertEqual({None, "cable"}, namespaces)

    def test_two_different_namespaces_alone_are_not_ambiguous(self):
        """No bare/un-namespaced variant present -> not ambiguous, per the
        design's per-namespace uniqueness scoping (section 5). This is an
        interpretive call on an underspecified class name; documented here
        so a reviewer who reads it differently has a concrete test to argue
        against."""
        rows = [
            _row("d17a", "TS-20260916-cable-020.000-OPEN__by-forge.txt", "Requests"),
            _row("d17b", "TS-20260916-sentinel1-020.000-OPEN__by-sentinel1.txt", "Requests"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(0, report["counts"]["ambiguous_unnamespaced_aliases"])

    def test_ambiguous_sidecar_parent_from_duplicate_filename(self):
        rows = [
            _row("d20", "TS-20260918-cable-040.001-OPEN__by-cable.txt", "Requests"),
            _row("d21", "TS-20260918-cable-040.001-OPEN__by-cable.txt", "Requests"),
            _row("d22", "TS-20260918-cable-040.001-OPEN__by-cable.txt.sig", "Requests"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["ambiguous_sidecar_parents"])
        self.assertEqual(0, report["counts"]["unsigned_posts"])  # a sidecar DOES exist, just ambiguous
        self.assertEqual(2, len(report["posts"]))  # both duplicate-name observations preserved distinctly

    def test_clean_signed_post_has_no_warnings_no_flags(self):
        rows = [
            _row("d14", "TS-20260915-cable-008.000-OPEN__by-cable.txt", "Requests"),
            _row("d15", "TS-20260915-cable-008.000-OPEN__by-cable.txt.sig", "Requests"),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(1, len(report["posts"]))
        self.assertEqual([], report["posts"][0]["warnings"])
        self.assertEqual(0, report["counts"]["unsigned_posts"])
        self.assertEqual("not_computed_dry_run", report["posts"][0]["content_sha256_status"])
        self.assertIsNone(report["posts"][0]["content_sha256"])

    def test_check_header_is_never_called_and_defect_is_recorded(self):
        rows = [_row("d14", "TS-20260915-cable-008.000-OPEN__by-cable.txt", "Requests")]
        report = plan(_inventory(rows))  # must not raise, must not call check_header
        ids = {d["id"] for d in report["known_defects_recorded_not_fixed"]}
        self.assertIn("check_header_zero_padding_and_missing_priority", ids)

    def test_deferred_design_steps_recorded_in_header(self):
        report = plan(_inventory([]))
        self.assertIn("design_step_3_header_signature_verdicts", report["deferred"])
        self.assertIn("design_step_9_webviewlink_canonical_url", report["deferred"])

    def test_content_sha256_stays_null_with_marker_on_every_row(self):
        rows = [
            _row("d14", "TS-20260915-cable-008.000-OPEN__by-cable.txt", "Requests"),
            _row("d15", "TS-20260915-cable-008.000-OPEN__by-cable.txt.sig", "Requests"),
            _row("d05", "BB-20260911-forge-001.000-POST__x.gdoc", "Bulletin Board",
                 mime_type="application/vnd.google-apps.document", provider_checksum=None, provider_checksum_algo=None),
        ]
        report = plan(_inventory(rows))
        for post in report["posts"]:
            self.assertIsNone(post["content_sha256"])
            self.assertEqual("not_computed_dry_run", post["content_sha256_status"])
        for artifact in report["artifacts"]:
            self.assertIsNone(artifact["content_sha256"])
            self.assertEqual("not_computed_dry_run", artifact["content_sha256_status"])
        for doc in report["native_doc_objects"]:
            self.assertIsNone(doc["content_sha256"])
            self.assertEqual("native_google_doc", doc["content_sha256_status"])

    def test_next_post_no_per_thread(self):
        rows = [
            _row("d18", "TS-20260917-cable-030.000-OPEN__by-cable.txt", "Requests"),
            _row("d19", "TS-20260917-cable-030.000-WORKING__by-forge.txt", "Requests"),
        ]
        report = plan(_inventory(rows))
        # both seq==0 collide, so post_no lands at 1 and 2 -> next is 3
        self.assertEqual(3, report["next_post_no"]["TS-20260917-cable-030"])

    def test_repeated_calls_are_byte_identical_same_process(self):
        """Weaker in-process half of the determinism proof (pure-function,
        no accumulated state across calls). The stronger, load-bearing proof
        is the cross-PROCESS SHA-256 comparison documented in this file's
        module docstring, since PYTHONHASHSEED is fixed per-process and
        can't vary within a single unittest run."""
        import hashlib, json
        rows = [
            _row("d01", "TS-20260906-016.002-RESOLVED__by-cable.txt", "Requests"),
            _row("d02", "TS-20260906-016.002-WORKING__by-forge.txt", "Requests"),
            _row("d03",
                 "OFFER-20260907-jeangrey-001.000-OPEN__host-jeangrey__client-work-laptop-full-capability-intermittent.txt",
                 "Seeking"),
            _row("d12", "TS-20260913-cable-006.000-OPEN__by-cable__mode-urgent.txt", "Requests"),
            _row(None, "TS-20260919-cable-050.000-OPEN__by-cable.txt", "Requests"),
        ]
        inventory = _inventory(rows)
        a = json.dumps(plan(inventory), indent=2, sort_keys=True)
        b = json.dumps(plan(inventory), indent=2, sort_keys=True)
        self.assertEqual(hashlib.sha256(a.encode()).hexdigest(), hashlib.sha256(b.encode()).hexdigest())
        self.assertEqual(a, b)

    def test_shortcut_objects_isolated_from_every_other_bucket(self):
        """gsp's CP1 finding (2026-09-21): rclone v1.75.1 dereferences Drive
        shortcuts by default, substituting the TARGET's file ID/mime_type/
        size. merge_inventory.py now isolates these into a separate
        `shortcut_objects` input list at the source; this planner must never
        merge them into `posts`, `non_post_artifacts`, or anywhere else."""
        rows = [_row("native-1", "TS-20260921-cable-090.000-OPEN__by-cable.txt", "Requests")]
        inventory = _inventory(rows)
        inventory["shortcut_objects"] = [
            _row("foreign-target-1", "shortcut-to-something-else.txt", "Requests",
                 collector_note="shortcut object detected via Path diff; ID is the target's",
                 mime_type="text/plain"),
        ]
        report = plan(inventory)
        self.assertEqual(1, report["counts"]["shortcut_objects"])
        self.assertEqual(1, len(report["shortcut_objects"]))
        self.assertEqual("shortcut_object", report["shortcut_objects"][0]["reason"])
        self.assertEqual("foreign-target-1", report["shortcut_objects"][0]["drive_file_id"])
        # never leaked into the canonical post/exception buckets
        self.assertEqual(1, len(report["posts"]))  # only the real native row
        self.assertEqual([], report["non_post_artifacts"])
        self.assertEqual([], report["collector_defects"])

    def test_shortcut_object_missing_drive_file_id_is_still_a_collector_defect(self):
        inventory = _inventory([])
        inventory["shortcut_objects"] = [
            _row(None, "shortcut-to-something-else.txt", "Requests", collector_note="x"),
        ]
        report = plan(inventory)
        self.assertEqual(0, report["counts"]["shortcut_objects"])
        self.assertEqual(1, report["counts"]["collector_defects"])

    def test_bare_list_input_has_no_shortcut_objects_not_an_error(self):
        """Pre-existing bare-list fixtures (test_registrar.py) predate the
        shortcut_objects class entirely -- must not raise, must report zero."""
        rows = [{"name": "TS-20260921-cable-091.000-OPEN__by-cable.txt", "drive_file_id": "x"}]
        report = plan(rows)
        self.assertEqual(0, report["counts"]["shortcut_objects"])
        self.assertEqual([], report["shortcut_objects"])

    def test_backcompat_collisions_alias_matches_old_test_shape(self):
        """Guards the exact scenario the pre-existing
        test_import_duplicate_is_deterministic in test_registrar.py exercises,
        so the deprecated `collisions` superset alias keeps working for any
        caller still reading it."""
        rows = [
            {"name": "TS-20260917-bishop-004.001-WORKING__by-bishop.txt", "drive_file_id": "b", "created_time": "2026-09-17T01:00:00Z"},
            {"name": "TS-20260917-bishop-004.001-BLOCKED__by-bishop.txt", "drive_file_id": "a", "created_time": "2026-09-17T02:00:00Z"},
        ]
        report = plan(rows)
        self.assertEqual(2, len(report["posts"]))
        self.assertEqual(2, len(report["collisions"]))
        self.assertEqual(2, len({r["post_uid"] for r in report["posts"]}))


class WS3TrashedNativeDocBoardTests(unittest.TestCase):
    """WS3 phase A taxonomy extensions (jackie-chan, 2026-09-22): trashed
    board-object policy (item 2), native-Doc detection via the Office-export
    corroborating signal (item 3), and board derivation from
    parent_folder_path (item 4). All fixtures here are synthetic -- no real
    corpus content, per the disclosure-boundary rule (gsp's CP1/WS3 review
    item 4: row-level output stays outside C:\\Repo\\townsquare\\)."""

    def test_trashed_txt_post_is_excluded_from_posts_and_recorded(self):
        rows = [_row("t1", "TS-20260929-sample-090.002-CLOSED__by-sample.txt", "Requests", trashed=True)]
        report = plan(_inventory(rows))
        self.assertEqual(0, len(report["posts"]))
        self.assertEqual(1, report["counts"]["trashed_board_objects"])
        obj = report["trashed_board_objects"][0]
        self.assertEqual("post", obj["kind"])
        self.assertEqual("Requests", obj["board"])
        self.assertFalse(obj["native_doc"])
        # full Drive metadata, not just a count (Drive purges trash; this
        # row may be the only surviving record)
        for key in ("drive_file_id", "mime_type", "size", "provider_checksum", "created_time", "modified_time"):
            self.assertIn(key, obj)

    def test_trashed_sig_sidecar_is_excluded_from_artifacts_and_recorded(self):
        rows = [_row("t2", "TS-20260929-sample-090.002-CLOSED__by-sample.txt.sig", "Requests", trashed=True)]
        report = plan(_inventory(rows))
        self.assertEqual(0, len(report["artifacts"]))
        self.assertEqual(1, report["counts"]["trashed_board_objects"])
        self.assertEqual("sidecar", report["trashed_board_objects"][0]["kind"])

    def test_trashed_sidecar_orphan_when_parent_also_trashed(self):
        rows = [
            _row("t3", "TS-20260910-cable-030.000-OPEN__by-cable.txt", "Requests", trashed=True),
            _row("t4", "TS-20260910-cable-030.000-OPEN__by-cable.txt.sig", "Requests", trashed=True),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["trashed_sidecar_orphan"])
        self.assertEqual(0, report["counts"]["trashed_sidecar_live_post_lost_signature"])
        res = report["trashed_sidecar_resolution"][0]
        self.assertEqual("orphan_sidecar", res["classification"])
        self.assertEqual("trashed", res["parent_status"])

    def test_trashed_sidecar_orphan_when_parent_missing_entirely(self):
        rows = [_row("t5", "TS-20260910-cable-031.000-OPEN__by-cable.txt.sig", "Requests", trashed=True)]
        report = plan(_inventory(rows))
        res = report["trashed_sidecar_resolution"][0]
        self.assertEqual("orphan_sidecar", res["classification"])
        self.assertEqual("missing", res["parent_status"])

    def test_trashed_sidecar_live_post_lost_signature_is_a_distinct_more_serious_class(self):
        """The opposite class from orphan_sidecar (jigoro-kano's Q2 review):
        the POST is still active/importable, but its signature is the thing
        that's trashed -- must never be folded into 'orphan'."""
        rows = [
            _row("t6", "TS-20260910-cable-032.000-OPEN__by-cable.txt", "Requests", trashed=False),
            _row("t7", "TS-20260910-cable-032.000-OPEN__by-cable.txt.sig", "Requests", trashed=True),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(1, len(report["posts"]))  # the active post still imports
        self.assertEqual(0, report["counts"]["trashed_sidecar_orphan"])
        self.assertEqual(1, report["counts"]["trashed_sidecar_live_post_lost_signature"])
        res = report["trashed_sidecar_resolution"][0]
        self.assertEqual("live_post_lost_signature", res["classification"])
        self.assertEqual("active", res["parent_status"])

    def test_rewrite_and_trash_candidate_detected_by_exact_filename_match(self):
        """jigoro-kano's Q2 review, check (a): identical filename observed
        both trashed and active is a candidate doctrine section 1
        REWRITE-AND-TRASH violation -- materially different from an
        ordinary trashed post, and must be labeled distinctly. Filename here
        is a fabricated synthetic pattern (same style as every other
        fixture in this file), not a real corpus name."""
        name = "BB-20260930-sample-777.000-POST__to-all__impact-fleet__from-sample__widget-status-update.txt"
        rows = [
            _row("active-copy", name, "Bulletin Board", trashed=False),
            _row("trashed-copy", name, "Bulletin Board", trashed=True),
        ]
        report = plan(_inventory(rows))
        self.assertEqual(1, len(report["posts"]))
        self.assertEqual("active-copy", report["posts"][0]["drive_file_id"])
        self.assertEqual(1, report["counts"]["trashed_rewrite_and_trash_candidates"])
        candidate = report["trashed_rewrite_and_trash_candidates"][0]
        self.assertEqual("active-copy", candidate["active_drive_file_id"])
        self.assertEqual("trashed-copy", candidate["trashed_drive_file_id"])

    def test_ordinary_trashed_post_with_no_active_namesake_is_not_a_rewrite_candidate(self):
        rows = [_row("t8", "TS-20260910-cable-033.000-OPEN__by-cable.txt", "Requests", trashed=True)]
        report = plan(_inventory(rows))
        self.assertEqual(0, report["counts"]["trashed_rewrite_and_trash_candidates"])

    def test_native_doc_detected_via_office_export_mime_null_size_null_checksum(self):
        """WS3 item 3: the live collector run never observes a bare
        google-apps mimetype -- it observes the Office-export mimetype with
        null size and null checksum. This is the corroborating signal that
        makes that safe to trust."""
        rows = [_row(
            "nd1", "BB-20260929-sample-050.000-POST__to-all__impact-fleet__from-sample__draft-pending-confirmation.docx",
            "Bulletin Board",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size=None, provider_checksum=None, provider_checksum_algo=None,
        )]
        report = plan(_inventory(rows))
        self.assertEqual(1, report["counts"]["native_doc_objects"])
        self.assertEqual(0, report["counts"]["quarantined_invalid_name"])
        self.assertEqual("Bulletin Board", report["native_doc_objects"][0]["board"])

    def test_genuine_docx_upload_with_real_size_and_checksum_is_not_misclassified(self):
        """Guard against a false positive: an ordinary uploaded Word file
        shares the Office-export mimetype but has a REAL size and checksum
        -- it must still fall through to generic quarantine (extension not
        .txt), never be reported as a native Doc."""
        rows = [_row(
            "nd2", "BB-20260911-forge-002.000-POST__to-all__impact-fleet__from-forge__real-upload.docx",
            "Bulletin Board",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size=48213, provider_checksum="abc123def456", provider_checksum_algo="md5",
        )]
        report = plan(_inventory(rows))
        self.assertEqual(0, report["counts"]["native_doc_objects"])
        self.assertEqual(1, report["counts"]["quarantined_invalid_name"])

    def test_trashed_native_doc_in_board_folder_is_classified_once_not_double_counted(self):
        """The required intersection fixture (Helio's CP-A1 / jigoro-kano's
        Q2+Q3): a native Doc that is BOTH trashed AND inside a post-bearing
        board folder must land in exactly one bucket (trashed_board_objects,
        tagged native_doc=True), never also in native_doc_objects, and never
        falling between the two (i.e. dropped from both)."""
        rows = [_row(
            "nd3", "BB-20260912-forge-003.000-POST__intersection-case.docx",
            "Bulletin Board",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            size=None, provider_checksum=None, provider_checksum_algo=None,
            trashed=True,
        )]
        report = plan(_inventory(rows))
        self.assertEqual(0, report["counts"]["native_doc_objects"])
        self.assertEqual([], report["native_doc_objects"])
        self.assertEqual(1, report["counts"]["trashed_board_objects"])
        obj = report["trashed_board_objects"][0]
        self.assertTrue(obj["native_doc"])
        self.assertEqual("other", obj["kind"])  # .docx is neither .txt nor .txt.sig

    def test_board_is_derived_from_parent_folder_path_not_hardcoded_legacy(self):
        rows = [_row("b1", "TS-20260910-cable-034.000-OPEN__by-cable.txt", "Requests")]
        report = plan(_inventory(rows))
        self.assertEqual(1, len(report["posts"]))
        self.assertEqual("Requests", report["posts"][0]["board"])
        self.assertEqual(0, report["counts"]["board_fallback_fired"])

    def test_board_fallback_fires_loudly_only_for_folder_unknown_fixtures(self):
        """Pre-collector-schema bare-list fixtures (no parent_folder_path key
        at all) still fall back to 'legacy' -- but the fallback firing is now
        RECORDED, not silent (posts.board is NOT NULL; a silent default here
        is the same fail-open shape flagged elsewhere in this project)."""
        rows = [{"name": "TS-20260910-cable-035.000-OPEN__by-cable.txt", "drive_file_id": "b2"}]
        report = plan(rows)
        self.assertEqual(1, len(report["posts"]))
        self.assertEqual("legacy", report["posts"][0]["board"])
        self.assertEqual(1, report["counts"]["board_fallback_fired"])
        self.assertEqual("b2", report["board_fallback_fired"][0]["drive_file_id"])

    def test_non_post_artifact_and_legacy_nonconforming_and_grammar_b_carry_board_tag(self):
        rows = [
            _row("nb1", "TOWN-SQUARE-DOCTRINE-v1.5-20260908.txt", ""),
            _row("nb2", "WANT-20260907-001__skill__x.md", "Wanted"),
            _row("nb3", "OFFER-20260907-jeangrey-001.000-OPEN__host-jeangrey__x.txt", "Seeking"),
        ]
        report = plan(_inventory(rows))
        self.assertIsNone(report["non_post_artifacts"][0]["board"])  # board root -> no board
        self.assertEqual("Wanted", report["legacy_nonconforming"][0]["board"])
        self.assertEqual("Seeking", report["grammar_b_offer_host_field"][0]["board"])


if __name__ == "__main__":
    unittest.main()
