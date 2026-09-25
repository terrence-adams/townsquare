"""Bonus coverage beyond the task brief's minimum six items, directly
requested by its own "Read first" framing: design v2 doc s3, K4, corrects
v1's mechanism for how a Seeking claim links back to the tracker item that
needed it.

v1 doc s4/s5 (SUPERSEDED, do not test this): the claimer's new Request
carries parent: pointing at the Story.

v2 doc s3 K4 (the current ruling -- test THIS): "I take kano's cheaper
link. The claimer's CLOSED event on the SEEK names the claimer's new
Request in references: (D19; any type), and the projector follows
SEEK -> Request. Other hosts learn no new field." parent: on the new
Request is not required and is deliberately absent from this fixture, to
make the proof unambiguous: if this test passed only because the projector
ALSO fell back to reading a parent: field, it would not be proving v2's
mechanism at all.

Out of scope here (covered elsewhere, not conflated with this test):
whether parent: still works for venom's OWN ordinary sub-request
attachment -- v2 doc s3 K4 keeps that meaning unchanged, and
test_nesting.py already exercises plain parent: attachment.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tracker.projector import build_projection
from tracker.tests.boardfixture import write_event


class SeekingClaimLinkTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_claim_link_travels_via_references_on_the_seeks_closed_event_not_parent_on_the_new_request(self):
        write_event(self.root, "Requests", "TS-20260101-venom-800.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "townsquare", "for": "bruce-lee",
                            "acceptance": "yes"})
        write_event(self.root, "Seeking", "SEEK-20260101-venom-801.000-OPEN__by-venom.txt",
                    header={"parent": "TS-20260101-venom-800"}, minutes_after_base=1)
        write_event(self.root, "Seeking", "SEEK-20260101-venom-801.001-CLOSED__by-forge.txt",
                    header={"references": "TS-20260101-forge-900 (evidence)"}, minutes_after_base=2)
        # the claimer's own new Request -- deliberately carries NO parent:
        write_event(self.root, "Requests", "TS-20260101-forge-900.000-OPEN__by-forge.txt",
                    header={"for": "forge"}, minutes_after_base=2)

        result = build_projection(self.root)
        story = result["projects"]["townsquare"][0]
        seek = next(a for a in story["attachments"] if a["id"] == "SEEK-20260101-venom-801")
        self.assertEqual("CLOSED", seek["state"])
        self.assertEqual("TS-20260101-forge-900", seek["claimed_by"])

    def test_an_unclaimed_open_seek_carries_no_claimed_by(self):
        write_event(self.root, "Requests", "TS-20260101-venom-810.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "townsquare"})
        write_event(self.root, "Seeking", "SEEK-20260101-venom-811.000-OPEN__by-venom.txt",
                    header={"parent": "TS-20260101-venom-810"})

        result = build_projection(self.root)
        story = result["projects"]["townsquare"][0]
        seek = next(a for a in story["attachments"] if a["id"] == "SEEK-20260101-venom-811")
        self.assertEqual("OPEN", seek["state"])
        self.assertIsNone(seek.get("claimed_by"))


if __name__ == "__main__":
    unittest.main()
