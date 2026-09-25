"""The output contract, design v2 doc s2 (A5): "The projector's output
contract states that its groupings are non-monotone by design and must not
be used for routing, notification or receipt. Stating it lets a consumer
detect a violation (D41)." Design v1 doc s6 gives the same rule in its own
words: "I read these groupings as a current-state view that nothing routes
or notifies on... D44 requires relevance buckets to be monotone... these
are not relevance buckets."

This suite encodes the contract two ways, per the task brief's own
suggestion ("a docstring assertion, a schema note, whatever fits the actual
interface you're designing tests against") -- belt and suspenders, since
neither alone is fully satisfying on its own:
  - a MACHINE-READABLE marker on every build_projection() result, so a
    future consumer (a Vertical entry writer, a notifier) can assert
    against it programmatically and a static check could flag a caller
    that never reads it (D41's "lets a consumer detect a violation");
  - a human-readable statement in tracker.projector's own module docstring,
    since the design's own wording ("the projector's output contract
    states...") is itself a documentation requirement, not only a data one.

This is this suite's own interface choice for HOW to encode an
undisputed, explicitly-stated design rule -- not a guess at an unpinned
design question.
"""
from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import tracker.projector as projector_module
from tracker.projector import build_projection
from tracker.tests.boardfixture import new_board


class OutputContractTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_result_carries_a_machine_readable_non_monotone_view_marker(self):
        new_board(self.root)  # all five board folders, deliberately empty
        result = build_projection(self.root)
        contract = result["output_contract"]
        self.assertIs(True, contract["non_monotone_view"])
        self.assertTrue(
            {"routing", "notification", "receipt"} <= set(contract["must_not_be_used_for"]),
            f"expected routing/notification/receipt all disclaimed, got {contract['must_not_be_used_for']!r}",
        )

    def test_projector_module_docstring_states_the_contract_in_words(self):
        doc = (projector_module.__doc__ or "").lower()
        self.assertIn("non-monotone", doc)
        self.assertIn("routing", doc)
        self.assertIn("notification", doc)
        self.assertIn("receipt", doc)

    def test_empty_board_still_produces_well_formed_empty_output_not_none_or_a_crash(self):
        """Lower-bound board-size boundary: zero events anywhere."""
        new_board(self.root)
        result = build_projection(self.root)
        self.assertEqual({}, result["projects"])
        self.assertEqual([], result["flags"])
        self.assertEqual([], result["unparseable_filenames"])

    def test_a_board_root_with_no_board_folders_at_all_is_also_well_formed_empty(self):
        """Lower-bound boundary below that: the root exists but is
        completely bare, not even the five expected folders -- must not be
        treated as an error, since a brand-new project's board may not
        have populated every folder yet."""
        result = build_projection(self.root)
        self.assertEqual({}, result["projects"])
        self.assertEqual([], result["flags"])


if __name__ == "__main__":
    unittest.main()
