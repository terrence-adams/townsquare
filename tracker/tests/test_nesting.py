"""Nesting under option (b): design v2 doc s0/s1 decision 2, and s4 A2.

Sensei approved option (b) -- levels stay ordered (epic -> feature ->
story) but parent: is optional at every level. A top-level item (no
parent:) carries project: itself and shows directly under that project.
This file pins build_projection's tree shape for that decision and its two
violation classes: a child pointing at the wrong level, and an epic given a
parent at all.

Tree shape asserted here (this suite's own interface choice, since no
implementation exists yet):
    result["projects"] == {<project-slug>: [<top-level node>, ...]}
    node == {
        "id": <thread id>, "level": "epic"|"feature"|"story",
        "state": <lifecycle state, from the filename, per README's "state
                  lives in the filename">,
        "parent": <thread id or None>, "project": <slug>,
        "repo": <str or None>, "next": <str or None>,
        "children": [<node>, ...],       # direct children only
        "attachments": [...], "rollup": {...},
    }
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tracker.projector import build_projection
from tracker.tests.boardfixture import write_event


class NestingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_story_with_parent_pointing_at_a_feature_rolls_up_correctly(self):
        write_event(self.root, "Requests", "TS-20260101-venom-001.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-002.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-001"})
        write_event(self.root, "Requests", "TS-20260101-venom-003.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-002"})

        result = build_projection(self.root)
        top = result["projects"]["townsquare"]
        self.assertEqual(1, len(top))
        epic = top[0]
        self.assertEqual("TS-20260101-venom-001", epic["id"])
        self.assertEqual(1, len(epic["children"]))
        feature = epic["children"][0]
        self.assertEqual("TS-20260101-venom-002", feature["id"])
        self.assertEqual(1, len(feature["children"]))
        story = feature["children"][0]
        self.assertEqual("TS-20260101-venom-003", story["id"])
        self.assertEqual([], story["children"])

    def test_story_without_parent_and_its_own_project_shows_directly_under_that_project(self):
        """The option (b) behavior v1's strict lineage (option a) would have
        forbidden outright: a one-story ask needs exactly one thread."""
        write_event(self.root, "Requests", "TS-20260101-venom-050.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "kollective", "for": "bruce-lee",
                            "acceptance": "yes"})

        result = build_projection(self.root)
        top = result["projects"]["kollective"]
        self.assertEqual(1, len(top))
        self.assertEqual("TS-20260101-venom-050", top[0]["id"])
        self.assertEqual("story", top[0]["level"])
        self.assertIsNone(top[0]["parent"])

    def test_feature_parent_pointing_at_a_story_is_a_nesting_violation_reported_not_refused(self):
        write_event(self.root, "Requests", "TS-20260101-venom-060.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-061.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-060"})

        result = build_projection(self.root)
        # reported, not refused: the feature still shows nested where its
        # (wrong) parent: says, per design v1 doc s4 ("the projector flags
        # any violation but never refuses the post", D1).
        story = result["projects"]["townsquare"][0]
        self.assertEqual([c["id"] for c in story["children"]], ["TS-20260101-venom-061"])
        violations = [f for f in result["flags"] if f["flag"] == "nesting_violation"]
        self.assertEqual(1, len(violations))
        self.assertEqual("TS-20260101-venom-061", violations[0]["thread"])
        self.assertEqual("TS-20260101-venom-060", violations[0]["detail"]["parent"])
        self.assertEqual("epic", violations[0]["detail"]["expected_level"])
        self.assertEqual("story", violations[0]["detail"]["actual_level"])

    def test_feature_parent_pointing_at_another_feature_is_also_a_nesting_violation(self):
        """A peer-level parent (one level over, not one level under) is a
        distinct wrong-target shape from the story case above -- both are
        violations of the same "exactly one level up" rule."""
        write_event(self.root, "Requests", "TS-20260101-venom-070.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-071.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-070"})

        result = build_projection(self.root)
        violations = [f for f in result["flags"] if f["flag"] == "nesting_violation"]
        self.assertEqual(1, len(violations))
        self.assertEqual("TS-20260101-venom-071", violations[0]["thread"])
        self.assertEqual("feature", violations[0]["detail"]["actual_level"])

    def test_epic_given_a_parent_at_all_is_a_nesting_violation(self):
        """Epics have no level above them, so parent: on an epic is always
        a violation regardless of what it points at."""
        write_event(self.root, "Requests", "TS-20260101-venom-080.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-081.000-OPEN__by-venom.txt",
                    header={"level": "epic", "parent": "TS-20260101-venom-080", "project": "townsquare"})

        result = build_projection(self.root)
        violations = [f for f in result["flags"] if f["flag"] == "nesting_violation"]
        self.assertEqual(1, len(violations))
        self.assertEqual("TS-20260101-venom-081", violations[0]["thread"])
        self.assertIsNone(violations[0]["detail"]["expected_level"])

    def test_project_is_inherited_from_the_nearest_top_level_ancestor_not_hardcoded_to_epic(self):
        """Under option (b) any level can be the top-level item -- here a
        Feature is the orphan/top-level item, and its Story child (which
        sets no project: of its own) must inherit the Feature's project,
        not fail to resolve one just because the ancestor is not an epic."""
        write_event(self.root, "Requests", "TS-20260101-venom-090.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "kollective"})
        write_event(self.root, "Requests", "TS-20260101-venom-091.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-090"})

        result = build_projection(self.root)
        feature = result["projects"]["kollective"][0]
        story = feature["children"][0]
        self.assertEqual("kollective", story["project"])

    def test_repo_is_inherited_from_the_nearest_ancestor_that_sets_it(self):
        """design v1 doc s4's field table: repo: is "optional; the nearest
        ancestor's value applies" -- named as one of the five tracker
        fields the task brief itself calls out, so it gets its own test
        even though it is not one of the required six checklist items."""
        write_event(self.root, "Requests", "TS-20260101-venom-095.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare", "repo": "terrence-adams/townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-096.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-095"})
        write_event(self.root, "Requests", "TS-20260101-venom-097.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-096",
                            "repo": "terrence-adams/townsquare-tools"})

        result = build_projection(self.root)
        epic = result["projects"]["townsquare"][0]
        feature = epic["children"][0]
        story = feature["children"][0]
        self.assertEqual("terrence-adams/townsquare", epic["repo"])
        # unset on the feature -- inherits from the epic, its nearest ancestor
        self.assertEqual("terrence-adams/townsquare", feature["repo"])
        # the story sets its OWN repo -- an explicit override, not inherited
        self.assertEqual("terrence-adams/townsquare-tools", story["repo"])


if __name__ == "__main__":
    unittest.main()
