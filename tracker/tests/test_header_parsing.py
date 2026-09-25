"""Header-reading rules for the project tracker (design v2 doc, s2, A5).

No implementation exists yet (tracker/projector.py is bruce-lee's, after
these tests exist and fail correctly against nothing -- see the ronda-rousey
work order in design v1 doc s9, Track 2). This file pins the contract at two
layers:

  parse_tracker_header(text: str) -> dict
      Pure, no I/O. Scans `text` for the five tracker header fields
      (level, parent, project, repo, next) inside the header block only.
      Returns {"has_header": bool, "fields": {...}, "duplicate_fields": [...]}.

  read_event_header(path) -> dict
      File-level wrapper. Never raises -- on any OSError it returns
      {"readable": False, "has_header": False, "fields": {}, "duplicate_fields": []}.
      On success it returns {"readable": True, **parse_tracker_header(text)}.

A5's rules, each with its own test below:
  - only a header block that ends at a line that is EXACTLY "---" counts;
    a file with no such line contributes no tracker fields at all.
  - keys match case-insensitively, starting at column 0.
  - an indented line is a continuation, never a key -- and never mutates a
    field's value that was already read from an unindented line.
  - a tracker key that appears twice in one header's block is flagged in
    duplicate_fields and excluded from fields: never guessed at, not even
    when the two occurrences happen to carry the same value (this suite's
    own reading of "appears twice ... never guessed at" as carrying no
    exception for identical repeats -- flagged as an interpretive call a
    reviewer could relax later, not a design-doc ruling).

Also pinned here: which event's header the projector reads at all, per G3
("a field is carried on the opening event and on any event that changes it,
and the newest event carrying it wins") and the Crier's own (sequence, time)
tie-break for a genuine sequence collision on the same thread.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tracker.projector import build_projection, parse_tracker_header, read_event_header
from tracker.tests.boardfixture import write_event


class ParseTrackerHeaderTests(unittest.TestCase):
    """Pure-function tests: no filesystem involved at all."""

    def test_no_terminator_line_contributes_no_tracker_fields(self):
        text = "level:  epic\nparent: TS-20260101-venom-001\nsubject: an old post\n"
        result = parse_tracker_header(text)
        self.assertFalse(result["has_header"])
        self.assertEqual({}, result["fields"])
        self.assertEqual([], result["duplicate_fields"])

    def test_body_line_next_in_a_header_less_file_is_never_read_as_a_key(self):
        """kano's A5 finding (review doc, F5/A5): NEXT:/Next: already occur
        organically as body lines in old-style Requests with no D19 header
        at all -- e.g. TS-20260913-venom-005.001. Such a file must yield
        nothing, not a false 'next' field."""
        text = (
            "State update, 2026-09-13.\n"
            "Next: ronda-rousey writes tests, then bruce-lee builds.\n"
            "Pace: whenever helio-gracie says go.\n"
        )
        result = parse_tracker_header(text)
        self.assertFalse(result["has_header"])
        self.assertNotIn("next", result["fields"])

    def test_body_line_next_after_a_real_terminator_is_also_never_read(self):
        """The header/body split still applies when a real D19 header IS
        present: content after "---" is body, full stop, even if a line
        there happens to look exactly like a tracker key."""
        text = "level:  story\nparent: TS-20260101-venom-001\n---\nNext: this is body text, not a header.\n"
        result = parse_tracker_header(text)
        self.assertTrue(result["has_header"])
        self.assertEqual("story", result["fields"]["level"])
        self.assertNotIn("next", result["fields"])

    def test_keys_match_case_insensitively_at_column_zero(self):
        text = "LEVEL:  epic\nParent:  TS-20260101-venom-001\nPROJECT: townsquare\n---\nbody\n"
        result = parse_tracker_header(text)
        self.assertEqual("epic", result["fields"]["level"])
        self.assertEqual("TS-20260101-venom-001", result["fields"]["parent"])
        self.assertEqual("townsquare", result["fields"]["project"])

    def test_one_leading_space_disqualifies_a_line_as_a_key_the_column_zero_boundary(self):
        """The boundary at exactly one leading space: 0 leading spaces is a
        key, 1 is a continuation. No unindented 'parent:' exists anywhere in
        this text, so the field must be absent entirely, not merely
        unindented-preferred."""
        text = "level:  epic\n parent: TS-20260101-venom-001\n---\nbody\n"
        result = parse_tracker_header(text)
        self.assertEqual("epic", result["fields"]["level"])
        self.assertNotIn("parent", result["fields"])
        self.assertNotIn("parent", result["duplicate_fields"])

    def test_indented_continuation_never_overwrites_the_value_read_above_it(self):
        """A real, unindented parent: line, immediately followed by an
        indented line that itself looks like a different parent: -- the
        continuation must never be picked up as a second occurrence (it is
        not a duplicate-key case) and must never mutate the first value."""
        text = (
            "level:  story\n"
            "parent: TS-20260101-venom-001\n"
            "    parent: TS-20260101-venom-999 (this is a continuation, not a key)\n"
            "---\nbody\n"
        )
        result = parse_tracker_header(text)
        self.assertEqual("TS-20260101-venom-001", result["fields"]["parent"])
        self.assertEqual([], result["duplicate_fields"])

    def test_indented_line_that_is_the_only_occurrence_of_a_key_is_still_never_read(self):
        """No unindented version exists at all here -- the field must be
        absent, not picked up from the sole indented occurrence."""
        text = "level:  epic\n    parent: TS-20260101-venom-001\n---\nbody\n"
        result = parse_tracker_header(text)
        self.assertNotIn("parent", result["fields"])

    def test_tab_indented_line_is_also_a_continuation(self):
        """Whitespace, not specifically the space character, marks a
        continuation -- a tab-indented line must be treated identically."""
        text = "level:  epic\n\tparent: TS-20260101-venom-001\n---\nbody\n"
        result = parse_tracker_header(text)
        self.assertNotIn("parent", result["fields"])

    def test_duplicate_tracker_key_is_flagged_and_excluded_from_fields(self):
        text = (
            "level:  story\n"
            "parent: TS-20260101-venom-001\n"
            "parent: TS-20260101-venom-002\n"
            "---\nbody\n"
        )
        result = parse_tracker_header(text)
        self.assertEqual(["parent"], result["duplicate_fields"])
        self.assertNotIn("parent", result["fields"])
        # the sibling field on the same header is unaffected
        self.assertEqual("story", result["fields"]["level"])

    def test_duplicate_key_is_flagged_even_when_both_occurrences_agree(self):
        """This suite's own strict reading (flagged in the module docstring):
        A5 carves out no exception for an identical repeat, so one is not
        silently assumed to be a harmless echo of the other."""
        text = "level:  story\nparent: TS-20260101-venom-001\nparent: TS-20260101-venom-001\n---\nbody\n"
        result = parse_tracker_header(text)
        self.assertEqual(["parent"], result["duplicate_fields"])
        self.assertNotIn("parent", result["fields"])

    def test_duplicate_key_case_insensitively_still_counts_as_duplicate(self):
        text = "level:  story\nparent: TS-20260101-venom-001\nPARENT: TS-20260101-venom-002\n---\nbody\n"
        result = parse_tracker_header(text)
        self.assertEqual(["parent"], result["duplicate_fields"])

    def test_non_tracker_header_key_repeated_does_not_affect_tracker_fields(self):
        """A5 scopes the duplicate-flag rule to tracker keys. A duplicated
        NON-tracker key (e.g. 'to:') is out of this module's business
        entirely and must never crash or leak into duplicate_fields."""
        text = "to: venom\nto: forge\nlevel: epic\n---\nbody\n"
        result = parse_tracker_header(text)
        self.assertEqual("epic", result["fields"]["level"])
        self.assertEqual([], result["duplicate_fields"])

    def test_empty_text_has_no_header(self):
        result = parse_tracker_header("")
        self.assertFalse(result["has_header"])
        self.assertEqual({}, result["fields"])

    def test_terminator_as_the_very_first_line_is_an_empty_but_present_header(self):
        """Boundary: a header block of zero field lines is still a
        genuine, present header (has_header True), just with no tracker
        fields in it -- distinct from no terminator existing at all."""
        result = parse_tracker_header("---\nbody only\n")
        self.assertTrue(result["has_header"])
        self.assertEqual({}, result["fields"])

    def test_terminator_line_with_trailing_whitespace_is_not_exactly_dash_dash_dash(self):
        """A5: the terminator is a line that IS EXACTLY '---'. Trailing
        spaces make it a different line, so this text has no terminator at
        all under a byte-exact reading -- flagged here as this suite's
        strict interpretation of "exactly ---", since the design text gives
        no leniency clause for trailing whitespace."""
        text = "level: epic\n--- \nbody\n"
        result = parse_tracker_header(text)
        self.assertFalse(result["has_header"])


class ReadEventHeaderTests(unittest.TestCase):
    """File-level wrapper: real files on disk, real OS-level failure modes."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_reads_a_real_file_and_delegates_to_the_pure_parser(self):
        path = write_event(self.root, "Requests", "x.txt", header={"level": "epic", "project": "townsquare"})
        result = read_event_header(path)
        self.assertTrue(result["readable"])
        self.assertEqual("epic", result["fields"]["level"])

    def test_nonexistent_path_is_reported_unreadable_never_raises(self):
        result = read_event_header(self.root / "Requests" / "does-not-exist.txt")
        self.assertEqual(
            {"readable": False, "has_header": False, "fields": {}, "duplicate_fields": []},
            result,
        )

    def test_a_directory_standing_where_a_file_is_expected_is_unreadable_never_raises(self):
        path = write_event(self.root, "Requests", "a-directory.txt", as_directory=True)
        result = read_event_header(path)
        self.assertFalse(result["readable"])
        self.assertEqual({}, result["fields"])


class NewestEventWinsTests(unittest.TestCase):
    """G3 ("newest event carrying a field wins") and the Crier's
    (sequence, time) tie-break, exercised through build_projection end to
    end -- this is what every other test file relies on to pick "the"
    header for a thread that has more than one event."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_reparenting_a_story_moves_it_between_features_newest_sequence_wins(self):
        """Design v1 doc s6's own example: "a re-parented Story moves
        between Features." event .001 (WORKING) must win over the opening
        .000 (OPEN), so the Story shows under Feature B, not Feature A."""
        write_event(self.root, "Requests", "TS-20260101-venom-010.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"}, minutes_after_base=0)
        write_event(self.root, "Requests", "TS-20260101-venom-011.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-010"}, minutes_after_base=1)
        write_event(self.root, "Requests", "TS-20260101-venom-012.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-010"}, minutes_after_base=2)
        write_event(self.root, "Requests", "TS-20260101-venom-020.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-011"}, minutes_after_base=3)
        write_event(self.root, "Requests", "TS-20260101-venom-020.001-WORKING__by-venom.txt",
                    header={"parent": "TS-20260101-venom-012"}, minutes_after_base=4)

        result = build_projection(self.root)
        epic = result["projects"]["townsquare"][0]
        feature_a = next(c for c in epic["children"] if c["id"] == "TS-20260101-venom-011")
        feature_b = next(c for c in epic["children"] if c["id"] == "TS-20260101-venom-012")
        self.assertEqual([], feature_a["children"])
        self.assertEqual(["TS-20260101-venom-020"], [c["id"] for c in feature_b["children"]])

    def test_same_sequence_collision_breaks_tie_on_later_timestamp(self):
        """Two events both claim to be .001 on the same thread (a genuine
        collision, not a re-parenting) -- the later-timestamp one is the
        current truth, mirroring crier's own tie-break."""
        write_event(self.root, "Requests", "TS-20260101-venom-030.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"}, minutes_after_base=0)
        write_event(self.root, "Requests", "TS-20260101-venom-030.001-WORKING__by-venom.txt",
                    header={"next": "the earlier collision loser"}, minutes_after_base=5)
        write_event(self.root, "Requests", "TS-20260101-venom-030.001-BLOCKED__by-forge.txt",
                    header={"next": "the later collision winner"}, minutes_after_base=6)

        result = build_projection(self.root)
        feature = result["projects"]["townsquare"][0]
        self.assertEqual("BLOCKED", feature["state"])
        self.assertEqual("the later collision winner", feature["next"])


if __name__ == "__main__":
    unittest.main()
