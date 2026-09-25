"""The ten report-only flags, design v1 doc s6 ("Flags. These are D43
reports: shown, never enforced."), adapted where v2 doc's option (b)
(parent optional at every level, design v2 doc s0/s1 decision 2) changes
what the underlying rule even means. Every adaptation is called out in the
test that needs it -- flagged, not silently carried over from v1's
strict-lineage (option a) wording.

The ten, in v1 doc s6's own order, and where each is covered:
    1. Nesting violation                                    -- test_nesting.py
       (a light representative case is repeated here too, for this file's
       own one-fixture-per-flag completeness)
    2. Parent not found                                      -- below
    3. A parent id that resolves to a collided thread        -- below
    4. A cycle                                                -- below
    5. An open child under a CLOSED or CANCELLED parent       -- below
    6. A RESOLVED or CLOSED parent that still has open children -- below
    7. level: on something that is not a Request              -- below
    8. project: restated below an [ancestor] with a different value -- below
    9. An unreadable header                                   -- below
   10. A Story that is not ready                               -- below

ADAPTATION FLAGGED for flag 8: v1 doc s6 says "restated below an EPIC".
This suite generalizes that to "below its nearest top-level ancestor",
for the same reason test_nesting.py generalizes project inheritance itself
under option (b) (a top-level item need not be an epic) -- kept consistent
with that choice rather than leaving a special case that only fires when
the top-level ancestor happens to be an epic specifically.

ADAPTATION FLAGGED for flag 10 (Story readiness): v1 doc s8's DoR line 1 is
"its parent is a Feature", unconditionally. design v2 doc s2 (A2) rewrites
this for option (b) to "if it has a parent, the parent is a Feature" --
Sensei approved option (b), so THIS is the rule under test, not v1's
original wording. The other two projector-checkable DoR lines are
unchanged: acceptance: yes with criteria, and a lane in for:. (The fourth
DoR line, "its Epic carries Sensei's confirmation", is explicitly named in
both design docs as NOT projector-checkable and is not tested here.)
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tracker.projector import build_projection
from tracker.tests.boardfixture import write_event


def _flags_named(result, name):
    return [f for f in result["flags"] if f["flag"] == name]


def _all_ids(nodes):
    out = []
    for n in nodes:
        out.append(n["id"])
        out.extend(_all_ids(n["children"]))
    return out


class FlagsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # 0. sanity: a fully well-formed board raises no flags at all. Guards
    # against an over-eager implementation that flags everything, which
    # would make every OTHER test in this file trivially "pass" for the
    # wrong reason.
    def test_well_formed_board_has_no_flags_at_all(self):
        write_event(self.root, "Requests", "TS-20260101-venom-500.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-501.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-500"})
        write_event(self.root, "Requests", "TS-20260101-venom-502.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-501",
                            "acceptance": "yes", "for": "bruce-lee"})
        result = build_projection(self.root)
        self.assertEqual([], result["flags"])

    # 1. nesting violation (primary coverage: test_nesting.py) -----------
    def test_1_nesting_violation_representative_case(self):
        write_event(self.root, "Requests", "TS-20260101-venom-510.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-511.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-510"})
        result = build_projection(self.root)
        self.assertEqual(1, len(_flags_named(result, "nesting_violation")))

    # 2. parent not found --------------------------------------------------
    def test_2_parent_not_found(self):
        write_event(self.root, "Requests", "TS-20260101-venom-520.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-999"})
        result = build_projection(self.root)
        flags = _flags_named(result, "parent_not_found")
        self.assertEqual(1, len(flags))
        self.assertEqual("TS-20260101-venom-520", flags[0]["thread"])
        self.assertEqual("TS-20260101-venom-999", flags[0]["detail"]["parent"])

    # 2b. the negative case design v1 doc s9's own watch-for (d) names by
    # name: "read Archive/ too... TSD s8 moves CLOSED threads there after
    # 60 days" -- an archived parent must NOT spuriously read as missing.
    def test_2b_a_parent_that_has_moved_to_archive_is_found_not_reported_missing(self):
        write_event(self.root, "Archive/Requests", "TS-20260101-venom-525.004-CLOSED__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-526.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-525"})
        result = build_projection(self.root)
        self.assertEqual([], _flags_named(result, "parent_not_found"))
        epic = result["projects"]["townsquare"][0]
        self.assertEqual("TS-20260101-venom-525", epic["id"])
        self.assertEqual(["TS-20260101-venom-526"], [c["id"] for c in epic["children"]])

    # 3. parent id resolves to a collided thread ---------------------------
    def test_3_parent_id_resolves_to_a_collided_thread(self):
        """Two genuinely different opens sharing one id (D23), mirroring
        crier's own "duplicate openings are never benign" case -- then a
        third thread names that id as its parent."""
        write_event(self.root, "Requests", "TS-20260101-venom-530.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-530.000-OPEN__by-forge.txt",
                    header={"level": "feature", "project": "kollective"})
        write_event(self.root, "Requests", "TS-20260101-venom-531.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-530"})
        result = build_projection(self.root)
        flags = _flags_named(result, "parent_collided")
        self.assertEqual(1, len(flags))
        self.assertEqual("TS-20260101-venom-531", flags[0]["thread"])
        self.assertEqual("TS-20260101-venom-530", flags[0]["detail"]["parent"])

    # 4. a cycle -------------------------------------------------------------
    def test_4_a_cycle_between_two_features(self):
        write_event(self.root, "Requests", "TS-20260101-venom-540.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-541"})
        write_event(self.root, "Requests", "TS-20260101-venom-541.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-540"})
        result = build_projection(self.root)
        flags = _flags_named(result, "cycle")
        threads_flagged = {f["thread"] for f in flags}
        self.assertEqual({"TS-20260101-venom-540", "TS-20260101-venom-541"}, threads_flagged)
        for f in flags:
            self.assertEqual({"TS-20260101-venom-540", "TS-20260101-venom-541"}, set(f["detail"]["cycle"]))

    # 5. open child under a CLOSED or CANCELLED parent -----------------------
    def test_5_open_child_under_a_closed_parent(self):
        write_event(self.root, "Requests", "TS-20260101-venom-550.004-CLOSED__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-551.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-550"})
        result = build_projection(self.root)
        flags = _flags_named(result, "open_child_under_closed_parent")
        self.assertEqual(1, len(flags))
        self.assertEqual("TS-20260101-venom-551", flags[0]["thread"])
        self.assertEqual("CLOSED", flags[0]["detail"]["parent_state"])

    def test_5_open_child_under_a_cancelled_parent(self):
        write_event(self.root, "Requests", "TS-20260101-venom-552.002-CANCELLED__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-553.001-WORKING__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-552"})
        result = build_projection(self.root)
        flags = _flags_named(result, "open_child_under_closed_parent")
        self.assertEqual(1, len(flags))
        self.assertEqual("CANCELLED", flags[0]["detail"]["parent_state"])
        # CANCELLED is not in flag 6's own state list -- it must not also
        # fire the RESOLVED/CLOSED-parent flag
        self.assertEqual([], _flags_named(result, "closed_parent_with_open_children"))

    # 6. RESOLVED or CLOSED parent that still has open children -------------
    def test_6_resolved_parent_with_an_open_child(self):
        write_event(self.root, "Requests", "TS-20260101-venom-560.003-RESOLVED__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-561.001-WORKING__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-560"})
        result = build_projection(self.root)
        flags = _flags_named(result, "closed_parent_with_open_children")
        self.assertEqual(1, len(flags))
        self.assertEqual("TS-20260101-venom-560", flags[0]["thread"])
        self.assertEqual("RESOLVED", flags[0]["detail"]["parent_state"])
        self.assertEqual(["TS-20260101-venom-561"], flags[0]["detail"]["open_children"])
        # RESOLVED is not in flag 5's own state list
        self.assertEqual([], _flags_named(result, "open_child_under_closed_parent"))

    def test_6_and_5_both_fire_together_when_the_parent_is_closed(self):
        """CLOSED is the one state common to both flags' triggering lists
        (5: CLOSED/CANCELLED: 6: RESOLVED/CLOSED) -- both must fire, not
        just one, since they report different things (the child's
        perspective vs. the parent's)."""
        write_event(self.root, "Requests", "TS-20260101-venom-562.004-CLOSED__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-563.002-BLOCKED__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-562"})
        result = build_projection(self.root)
        self.assertEqual(1, len(_flags_named(result, "open_child_under_closed_parent")))
        self.assertEqual(1, len(_flags_named(result, "closed_parent_with_open_children")))

    # 7. level: on something that is not a Request ---------------------------
    def test_7_level_on_a_bulletin_board_post(self):
        write_event(self.root, "Bulletin Board", "BB-20260101-venom-570.000-POST__by-venom.txt",
                    header={"level": "story"})
        result = build_projection(self.root)
        flags = _flags_named(result, "level_on_non_request")
        self.assertEqual(1, len(flags))
        self.assertEqual("BB-20260101-venom-570", flags[0]["thread"])
        # never promoted into the hierarchy on the strength of its own level:
        self.assertEqual({}, result["projects"])

    def test_7_level_on_a_seeking_post(self):
        write_event(self.root, "Seeking", "SEEK-20260101-venom-571.000-OPEN__by-venom.txt",
                    header={"level": "feature"})
        result = build_projection(self.root)
        flags = _flags_named(result, "level_on_non_request")
        self.assertEqual(1, len(flags))
        self.assertEqual("SEEK-20260101-venom-571", flags[0]["thread"])

    # 8. project: restated below its ancestor with a different value --------
    def test_8_project_restated_with_a_different_value_is_flagged(self):
        write_event(self.root, "Requests", "TS-20260101-venom-580.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "alpha"})
        write_event(self.root, "Requests", "TS-20260101-venom-581.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-580", "project": "beta"})
        result = build_projection(self.root)
        flags = _flags_named(result, "project_restated_conflict")
        self.assertEqual(1, len(flags))
        self.assertEqual("TS-20260101-venom-581", flags[0]["thread"])
        self.assertEqual("alpha", flags[0]["detail"]["inherited"])
        self.assertEqual("beta", flags[0]["detail"]["restated"])

    def test_8_project_restated_with_the_same_value_is_not_flagged(self):
        write_event(self.root, "Requests", "TS-20260101-venom-582.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "alpha"})
        write_event(self.root, "Requests", "TS-20260101-venom-583.000-OPEN__by-venom.txt",
                    header={"level": "feature", "parent": "TS-20260101-venom-582", "project": "alpha"})
        result = build_projection(self.root)
        self.assertEqual([], _flags_named(result, "project_restated_conflict"))

    # 9. an unreadable header -------------------------------------------------
    def test_9_unreadable_header_is_reported_not_raised_and_does_not_sink_the_rest_of_the_board(self):
        write_event(self.root, "Requests", "TS-20260101-venom-590.000-OPEN__by-venom.txt",
                    as_directory=True)
        # a perfectly normal item elsewhere on the board must still process
        write_event(self.root, "Requests", "TS-20260101-venom-591.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})

        result = build_projection(self.root)  # must not raise

        flags = _flags_named(result, "unreadable_header")
        self.assertEqual(1, len(flags))
        self.assertEqual("TS-20260101-venom-590", flags[0]["thread"])
        self.assertNotIn("TS-20260101-venom-590", _all_ids(sum(result["projects"].values(), [])))
        self.assertEqual(["TS-20260101-venom-591"], _all_ids(result["projects"]["townsquare"]))

    # 10. a Story that is not ready ------------------------------------------
    def test_10_story_ready_with_a_feature_parent_acceptance_and_for(self):
        write_event(self.root, "Requests", "TS-20260101-venom-600.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-601.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-600",
                            "acceptance": "yes", "for": "bruce-lee"})
        result = build_projection(self.root)
        self.assertEqual([], _flags_named(result, "story_not_ready"))

    def test_10_story_ready_top_level_with_no_parent_under_option_b(self):
        """The option (b) behavior change from v1's DoR: a parentless,
        top-level Story is allowed to be ready."""
        write_event(self.root, "Requests", "TS-20260101-venom-602.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "townsquare",
                            "acceptance": "yes", "for": "bruce-lee"})
        result = build_projection(self.root)
        self.assertEqual([], _flags_named(result, "story_not_ready"))

    def test_10_story_not_ready_when_its_parent_is_not_a_feature(self):
        write_event(self.root, "Requests", "TS-20260101-venom-603.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-604.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-603",
                            "acceptance": "yes", "for": "bruce-lee"})
        result = build_projection(self.root)
        flags = _flags_named(result, "story_not_ready")
        self.assertEqual(1, len(flags))
        self.assertIn("parent_not_feature", flags[0]["detail"]["reasons"])
        # this is simultaneously a nesting violation -- both must be visible
        self.assertEqual(1, len(_flags_named(result, "nesting_violation")))

    def test_10_story_not_ready_missing_acceptance(self):
        write_event(self.root, "Requests", "TS-20260101-venom-605.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-606.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-605", "for": "bruce-lee"})
        result = build_projection(self.root)
        flags = _flags_named(result, "story_not_ready")
        self.assertEqual(1, len(flags))
        self.assertIn("no_acceptance", flags[0]["detail"]["reasons"])

    def test_10_story_not_ready_missing_for(self):
        write_event(self.root, "Requests", "TS-20260101-venom-607.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"})
        write_event(self.root, "Requests", "TS-20260101-venom-608.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": "TS-20260101-venom-607", "acceptance": "yes"})
        result = build_projection(self.root)
        flags = _flags_named(result, "story_not_ready")
        self.assertEqual(1, len(flags))
        self.assertIn("no_for", flags[0]["detail"]["reasons"])


if __name__ == "__main__":
    unittest.main()
