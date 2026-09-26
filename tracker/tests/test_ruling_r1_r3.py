"""Fixtures for ip-man's ruling on jackie-chan's projector findings 1-3
(docs/ip-man-projector-ruling-20260926.md, R1-R3, section 5's fixture
table), reviewed with no blockers in docs/jackie-chan-review-of-ruling-
20260926.md. This file adds R1a, R1b, R1c (the boundary guard), R2a, R2b
and R3 exactly as that table specifies -- one test per row, board setup and
expected-after-the-fix result taken directly from it. Ids and test names
are this file's own choice, per the ruling's own delegation ("Ids and test
names are hers").

R1 -- parent: must be a bare thread id (complete it as
"<value>.000-OPEN.txt", it must parse, and the thread id that comes back
must equal the value itself). Any other value is flagged parent_malformed,
with the raw value and ids_found (from _thread_ids, the module's existing
free-text scanner), and places nothing -- no node child, no attachment.
R1c is the boundary this rule must NOT move: a bare id naming a real,
non-tracker-item thread stays parent_not_found (thread_exists: true),
exactly as today.

R2 -- a thread whose id has two different .000-OPEN opens is never placed,
as a node or as an attachment. It is reported once as thread_collided, with
both openings in the detail, wherever the projector would otherwise have
placed it (R2a: the node case, jackie's original finding; R2b: the
attachment case, which jackie-chan's review found produces ZERO flags at
all today -- worse than the node case, since thread_collided today only
fires inside the level:-bearing node loop, which a SEEK/WANT/BB/OFFER
thread never enters).

R3 -- intake is by level:, never by tree position. Every item whose
current level: is unscoped is listed in intake and nowhere else; its
parent:, if it has one, is never followed for placement, whether or not
that parent resolves.

No implementation of R1-R3 exists yet (that is bruce-lee's pass, in
tracker/projector.py only, after this file is committed and its red run is
recorded). No existing test file is edited here. At this commit:
R1a, R1b, R2a, R2b and R3 are each expected to FAIL BY ASSERTION against
today's projector.py (not error/collection-fail -- every fixture here runs
against already-shipped code paths, just not yet the rules this ruling
adds); R1c and the pre-existing 61 tests are expected to PASS.

Per the ruling's own section 5 ("Each red failure should print what the
projector actually produced: the flags, and the placement the assertion
checked"): every test below prints the projector's flags and the specific
placement structure its assertions check, unconditionally, before any
assertion. pytest's default output capture only shows a test's captured
stdout for a test that FAILS (see this file's own `python -m pytest
tracker/tests -q` run) -- so this is silent for R1c and the existing 61,
and is the raw evidence behind every red failure here. The ruling notes
this same run also serves as the measurement for two of jackie-chan's
earlier run-claims that Helio's checkpoint flagged as unsupported.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tracker.projector import build_projection
from tracker.tests.boardfixture import write_event


def _flags_named(result: dict, name: str) -> list[dict]:
    return [f for f in result["flags"] if f["flag"] == name]


def _dump(result: dict, checked: str) -> None:
    print(f"\n--- build_projection output checked by: {checked} ---")
    print("flags:", json.dumps(result["flags"], indent=2, sort_keys=True))


class RulingR1R3Tests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # R1a -----------------------------------------------------------------
    def test_r1a_annotated_parent_is_flagged_malformed_and_placed_nowhere(self):
        """Board: Feature F (project: townsquare). Story S with
        parent: <F> (its Feature) -- jackie's own original F1 shape,
        reproduced by ip-man's ruling and by jackie-chan's review, both by
        execution, against a real thread id."""
        f_id = "TS-20260101-venom-900"
        s_id = "TS-20260101-venom-901"
        raw_parent = f"{f_id} (its Feature)"
        write_event(self.root, "Requests", f"{f_id}.000-OPEN__by-venom.txt",
                    header={"level": "feature", "project": "townsquare"})
        write_event(self.root, "Requests", f"{s_id}.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": raw_parent,
                            "acceptance": "yes", "for": "bruce-lee"})

        result = build_projection(self.root)
        feature = result["projects"]["townsquare"][0]
        feature_children = [c["id"] for c in feature["children"]]
        no_project_ids = [n["id"] for n in result["no_project"]]
        not_ready = _flags_named(result, "story_not_ready")
        _dump(result, "R1a -- S's parent_malformed; F's children; no_project; S's story_not_ready")
        print("F.children:", feature_children)
        print("no_project ids:", no_project_ids)
        print("S's story_not_ready flags:", json.dumps(not_ready, indent=2, sort_keys=True))

        malformed = _flags_named(result, "parent_malformed")
        self.assertEqual(1, len(malformed), "expected exactly one parent_malformed flag")
        self.assertEqual(s_id, malformed[0]["thread"])
        self.assertEqual(raw_parent, malformed[0]["detail"]["parent"])
        self.assertEqual([f_id], malformed[0]["detail"]["ids_found"])
        self.assertEqual([], _flags_named(result, "parent_not_found"))

        self.assertEqual([], feature_children, "S must not be among F's children")
        self.assertEqual([s_id], no_project_ids, "S must fall to no_project")

        self.assertEqual(1, len(not_ready))
        self.assertIn("parent_not_feature", not_ready[0]["detail"]["reasons"])

    # R1b -----------------------------------------------------------------
    def test_r1b_event_id_parent_is_flagged_malformed_not_parent_not_found(self):
        """Board: Story S (project: townsquare). SEEK K with
        parent: <S>.001 -- an event id, not a thread id."""
        s_id = "TS-20260101-venom-910"
        k_id = "SEEK-20260101-venom-911"
        raw_parent = f"{s_id}.001"
        write_event(self.root, "Requests", f"{s_id}.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "townsquare"})
        write_event(self.root, "Seeking", f"{k_id}.000-OPEN__by-venom.txt",
                    header={"parent": raw_parent})

        result = build_projection(self.root)
        story = result["projects"]["townsquare"][0]
        attachment_ids = [a["id"] for a in story["attachments"]]
        _dump(result, "R1b -- K's parent_malformed; S's attachments")
        print("S.attachments:", attachment_ids)

        malformed = _flags_named(result, "parent_malformed")
        self.assertEqual(1, len(malformed), "expected exactly one parent_malformed flag")
        self.assertEqual(k_id, malformed[0]["thread"])
        self.assertEqual([s_id], malformed[0]["detail"]["ids_found"])
        self.assertEqual([], _flags_named(result, "parent_not_found"))

        self.assertEqual([], attachment_ids, "K must not be in S's attachments")

    # R1c (guard) -----------------------------------------------------------
    def test_r1c_guard_bare_parent_naming_a_non_tracker_thread_stays_parent_not_found(self):
        """Board: BB post B with no tracker fields. Story S with a bare
        parent: <B>. This must NOT become parent_malformed -- it pins R1's
        boundary, and (unlike the other five rows) is expected to PASS both
        before and after the fix: a bare id naming a real, non-tracker-item
        thread is unchanged by R1 (ruling section 3, "Unchanged")."""
        b_id = "BB-20260101-venom-920"
        s_id = "TS-20260101-venom-921"
        write_event(self.root, "Bulletin Board", f"{b_id}.000-POST__by-venom.txt", header={})
        write_event(self.root, "Requests", f"{s_id}.000-OPEN__by-venom.txt",
                    header={"level": "story", "parent": b_id})

        result = build_projection(self.root)
        not_found = _flags_named(result, "parent_not_found")
        _dump(result, "R1c guard -- S's parent_not_found")
        print("S's parent_not_found flags:", json.dumps(not_found, indent=2, sort_keys=True))

        self.assertEqual([], _flags_named(result, "parent_malformed"))
        self.assertEqual(1, len(not_found), "expected exactly one parent_not_found flag")
        self.assertEqual(s_id, not_found[0]["thread"])
        self.assertEqual(b_id, not_found[0]["detail"]["parent"])
        self.assertEqual(True, not_found[0]["detail"]["thread_exists"])

    # R2a -------------------------------------------------------------------
    def test_r2a_collided_thread_is_excluded_from_placement_entirely(self):
        """Board: one TS id with two .000-OPEN opens -- by-venom (epic,
        townsquare) and by-forge (feature, kollective). jackie's own
        original F2 shape."""
        tid = "TS-20260101-venom-930"
        write_event(self.root, "Requests", f"{tid}.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", f"{tid}.000-OPEN__by-forge.txt",
                    header={"level": "feature", "project": "kollective"})

        result = build_projection(self.root)
        collided = _flags_named(result, "thread_collided")
        _dump(result, "R2a -- placement in projects / no_project / intake")
        print("projects:", json.dumps(result["projects"], indent=2, sort_keys=True))
        print("no_project:", json.dumps(result["no_project"], indent=2, sort_keys=True))
        print("intake:", json.dumps(result["intake"], indent=2, sort_keys=True))

        self.assertEqual(1, len(collided), "expected exactly one thread_collided flag")
        self.assertEqual(tid, collided[0]["thread"])
        self.assertEqual(
            ["Requests/TS-20260101-venom-930.000-OPEN__by-forge.txt",
             "Requests/TS-20260101-venom-930.000-OPEN__by-venom.txt"],
            sorted(collided[0]["detail"]["openings"]),
        )

        # Nowhere in projects (at any depth), no_project or intake -- the
        # whole board here is just this one collided id, so a correct fix
        # leaves all three buckets completely empty.
        self.assertEqual({}, result["projects"])
        self.assertEqual([], result["no_project"])
        self.assertEqual([], result["intake"])

    # R2b -------------------------------------------------------------------
    def test_r2b_collided_seek_attachment_is_excluded_not_silently_attached(self):
        """Board: Story S (project: townsquare). One SEEK id with two
        .000-OPEN opens, each with parent: <S> -- the attachment shape R2
        extends to. jackie-chan's review found this produces zero flags at
        all today, worse than the node case (R2a), and a silent newest-wins
        attachment."""
        s_id = "TS-20260101-venom-940"
        k_id = "SEEK-20260101-venom-941"
        write_event(self.root, "Requests", f"{s_id}.000-OPEN__by-venom.txt",
                    header={"level": "story", "project": "townsquare"})
        write_event(self.root, "Seeking", f"{k_id}.000-OPEN__by-venom.txt",
                    header={"parent": s_id})
        write_event(self.root, "Seeking", f"{k_id}.000-OPEN__by-forge.txt",
                    header={"parent": s_id})

        result = build_projection(self.root)
        story = result["projects"]["townsquare"][0]
        attachment_ids = [a["id"] for a in story["attachments"]]
        collided = _flags_named(result, "thread_collided")
        _dump(result, "R2b -- S's attachments; thread_collided on the SEEK id")
        print("S.attachments:", attachment_ids)

        self.assertEqual(1, len(collided), "expected exactly one thread_collided flag")
        self.assertEqual(k_id, collided[0]["thread"])
        self.assertEqual([], attachment_ids, "the collided SEEK must not be attached to S")

    # R3 ----------------------------------------------------------------------
    def test_r3_unscoped_item_with_a_resolving_parent_still_goes_to_intake_never_nested(self):
        """Board: Epic E (project: townsquare). U1: level: unscoped,
        parent: <E>. U2: level: unscoped, no parent. jackie's own original
        F3 shape is U1 -- intake is by level:, so U1 must land there even
        though its parent: resolves to a real Epic, and must never be
        nested under it."""
        e_id = "TS-20260101-venom-950"
        u1_id = "TS-20260101-venom-951"
        u2_id = "TS-20260101-venom-952"
        write_event(self.root, "Requests", f"{e_id}.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})
        write_event(self.root, "Requests", f"{u1_id}.000-OPEN__by-venom.txt",
                    header={"level": "unscoped", "parent": e_id})
        write_event(self.root, "Requests", f"{u2_id}.000-OPEN__by-venom.txt",
                    header={"level": "unscoped"})

        result = build_projection(self.root)
        epic = result["projects"]["townsquare"][0]
        epic_children = [c["id"] for c in epic["children"]]
        intake_ids = [n["id"] for n in result["intake"]]
        nesting = _flags_named(result, "nesting_violation")
        _dump(result, "R3 -- intake; E's children; nesting_violation on U1")
        print("E.children:", epic_children)
        print("intake ids:", intake_ids)

        self.assertEqual(sorted([u1_id, u2_id]), sorted(intake_ids), "intake must hold U1 and U2")
        self.assertEqual([], epic_children, "U1 must not be among E's children")

        self.assertEqual(1, len(nesting), "expected exactly one nesting_violation flag")
        self.assertEqual(u1_id, nesting[0]["thread"])
        self.assertEqual(e_id, nesting[0]["detail"]["parent"])
        self.assertIsNone(nesting[0]["detail"]["expected_level"])
        self.assertEqual("epic", nesting[0]["detail"]["actual_level"])


if __name__ == "__main__":
    unittest.main()
