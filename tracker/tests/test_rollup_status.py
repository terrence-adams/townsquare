"""Rollup and status: design v1 doc s6's table row for "status" gives the
ingredients -- "each item's state by the newest-event rule ... for each
epic and feature: child counts by state, blocked children, children
awaiting closure (RESOLVED), and last-activity time" -- but does not pin a
single derived status enum for a Feature or Epic. The task brief that
commissioned this test suite says as much explicitly and asks for the gap
to be flagged, not silently guessed. This file documents and pins the
concrete semantics this suite picked, so bruce-lee has one unambiguous
target and a reviewer has a concrete thing to argue against.

ASSUMPTIONS PINNED HERE (flagged, not silently guessed):

1. An Epic or Feature's own `state` is ALWAYS its own newest event's state
   (the ordinary six-state Dojo lifecycle, unchanged per design v1 doc s4:
   "What stays unchanged: The six lifecycle states."). It is never silently
   overwritten by a computed aggregate of its children's states.
   Textual support, not just a guess: design v1 doc s6 lists "A RESOLVED or
   CLOSED parent that still has open children" as one of the ten report-
   only flags. That condition is a structural impossibility if a parent's
   state were mechanically derived from its children -- the flag's very
   existence in the design is evidence the parent's state is read
   independently of its children's states.

2. `rollup.child_state_counts`, `rollup.blocked_children` and
   `rollup.awaiting_closure_children` are computed over DIRECT children
   only, one level at a time. Nothing in s6's table row says direct vs.
   transitive; this suite picked direct-only because it composes cleanly
   with the containment structure Sensei asked for ("an Epic contains
   multiple Features; a Feature contains multiple Stories") -- an Epic's
   view of "child counts" is a summary of its Features, each of which
   already summarizes its own Stories, rather than double-counting through
   two levels at once.

3. `rollup.last_activity`, by contrast, IS transitive: it is the maximum
   timestamp across the item's own current event and its entire descendant
   subtree, recursively. This suite picked transitive-for-activity but
   direct-only-for-counts DELIBERATELY, not inconsistently: s6's own
   reasoning for last-activity is "the reader judges the age" of a whole
   area of work with no staleness alarm (s6, "why last-activity time but no
   staleness alarm") -- a freshness signal is more useful pooled across an
   entire Epic's subtree than reset at each level, where child counts are a
   structural breakdown that IS most useful per level.

4. "Children awaiting closure" is read literally as RESOLVED children,
   exactly as s6's own parenthetical states ("children awaiting closure
   (RESOLVED)").

Not pinned, and explicitly left alone by this file: whether a Feature/Epic's
`acceptance:` criteria are themselves satisfied by the state of its
children (a Definition-of-Done rollup). Design v1 doc s8 only writes a DoR
for Stories; nothing analogous is given for Epics/Features, so this suite
does not invent one.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tracker.projector import build_projection
from tracker.tests.boardfixture import expected_last_activity, write_event


class RollupStatusTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_parent_state_is_its_own_event_never_mechanically_derived_from_children(self):
        write_event(self.root, "Requests", "TS-20260101-venom-100.001-WORKING__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-101.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-100"})

        result = build_projection(self.root)
        feature = result["projects"]["townsquare"][0]
        self.assertEqual("WORKING", feature["state"])  # its OWN state, not "OPEN" from its only child

    def test_child_state_counts_are_computed_per_level_over_direct_children_only(self):
        write_event(self.root, "Requests", "TS-20260101-venom-110.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-111.001-WORKING__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-110"})
        write_event(self.root, "Requests", "TS-20260101-venom-112.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-111"})
        write_event(self.root, "Requests", "TS-20260101-venom-113.001-WORKING__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-111"})

        result = build_projection(self.root)
        epic = result["projects"]["townsquare"][0]
        feature = epic["children"][0]
        # the epic counts its ONE direct child (the feature, WORKING) -- it
        # does not reach through to the feature's two stories
        self.assertEqual({"WORKING": 1}, epic["rollup"]["child_state_counts"])
        # the feature counts its own two direct children
        self.assertEqual({"OPEN": 1, "WORKING": 1}, feature["rollup"]["child_state_counts"])

    def test_blocked_children_and_awaiting_closure_children_are_listed_by_id(self):
        write_event(self.root, "Requests", "TS-20260101-venom-120.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-121.002-BLOCKED__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-120"})
        write_event(self.root, "Requests", "TS-20260101-venom-122.003-RESOLVED__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-120"})
        write_event(self.root, "Requests", "TS-20260101-venom-123.001-WORKING__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-120"})

        result = build_projection(self.root)
        feature = result["projects"]["townsquare"][0]
        self.assertEqual(["TS-20260101-venom-121"], feature["rollup"]["blocked_children"])
        self.assertEqual(["TS-20260101-venom-122"], feature["rollup"]["awaiting_closure_children"])

    def test_last_activity_is_the_max_over_the_entire_descendant_subtree_not_just_direct_children(self):
        write_event(self.root, "Requests", "TS-20260101-venom-130.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"}, minutes_after_base=0)
        write_event(self.root, "Requests", "TS-20260101-venom-131.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-130"}, minutes_after_base=1)
        write_event(self.root, "Requests", "TS-20260101-venom-132.001-WORKING__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-131"}, minutes_after_base=50)

        result = build_projection(self.root)
        epic = result["projects"]["townsquare"][0]
        feature = epic["children"][0]
        story = feature["children"][0]
        # the leaf's own last_activity is just its own event's time
        self.assertEqual(expected_last_activity(50), story["rollup"]["last_activity"])
        # the epic's, two levels up, reaches all the way down to the story
        self.assertEqual(expected_last_activity(50), epic["rollup"]["last_activity"])
        self.assertEqual(expected_last_activity(50), feature["rollup"]["last_activity"])

    def test_last_activity_is_the_items_own_event_when_it_is_the_most_recent_thing_in_its_subtree(self):
        """The complementary case: the PARENT is the freshest thing, not a
        child -- last_activity must not get stuck at an old child's time."""
        write_event(self.root, "Requests", "TS-20260101-venom-140.001-WORKING__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"}, minutes_after_base=99)
        write_event(self.root, "Requests", "TS-20260101-venom-141.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-140"}, minutes_after_base=1)

        result = build_projection(self.root)
        feature = result["projects"]["townsquare"][0]
        self.assertEqual(expected_last_activity(99), feature["rollup"]["last_activity"])


if __name__ == "__main__":
    unittest.main()
