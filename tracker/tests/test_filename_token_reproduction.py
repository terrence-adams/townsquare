"""The filename-token reproduction, design v1 doc s3 (rejected option D) and
the ronda-rousey work order in v1 doc s9: "one test that pins the duplicate-
slug behaviour from s3."

This pins that the projector NEVER tries to read tracker data (level,
parent, project, repo, next) from filename tokens -- only from headers.
The proof has three legs:

  1. Today, right now, with zero tracker code written, the CANONICAL
     parser (registrar/app/filename.py, already shipped, unrelated to this
     job) already rejects a level-story-shaped filename token as a
     duplicate slug field. This leg tests EXISTING, already-shipped code
     and is therefore expected to PASS today -- see the ronda-rousey
     handback for why that is not a contradiction of "these tests fail
     against nothing".
  2. The exact CLI command the design doc gives, byte for byte, reproduces
     the documented "townsquare filename: duplicate slug field" / exit 2.
     Also passes today, for the same reason as leg 1.
  3. Because leg 1 is true, a file whose NAME carries that token is already
     unparseable at the filename-grammar layer -- so the projector, which
     design v1 doc s9 requires to use "the canonical parse_filename", can
     never legally reach a point where it would consider inventing a
     level from that token. This leg calls the not-yet-built
     tracker.projector.build_projection and is therefore expected to ERROR
     (ModuleNotFoundError) today, exactly like every other test file here.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from registrar.app.filename import FilenameError, parse_filename

# The exact filename design v1 doc s3 gives as its reproduction case.
SPURIOUS_TOKEN_FILENAME = (
    "TS-20260925-venom-001.000-OPEN__P3__to-venom__for-ip-man"
    "__level-story__from-venom__demo.txt"
)


class ExistingParserRejectsTheSpuriousTokenTests(unittest.TestCase):
    """Leg 1 and leg 2: exercises only already-shipped code. Expected to
    PASS today, with no tracker implementation whatsoever."""

    def test_canonical_parser_raises_duplicate_slug_field_today(self):
        with self.assertRaises(FilenameError) as ctx:
            parse_filename(SPURIOUS_TOKEN_FILENAME)
        self.assertEqual("duplicate slug field", str(ctx.exception))

    def test_documented_cli_command_reproduces_byte_for_byte(self):
        """design v1 doc s3's exact reproduction command, run for real."""
        result = subprocess.run(
            [sys.executable, "registrar/app/filename.py", "--json", SPURIOUS_TOKEN_FILENAME],
            cwd=str(Path(__file__).resolve().parents[2]),
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(2, result.returncode)
        self.assertEqual("townsquare filename: duplicate slug field\n", result.stderr)


class ProjectorNeverReadsFilenameTokensTests(unittest.TestCase):
    """Leg 3: needs tracker.projector, which does not exist yet. Expected
    to ERROR (collection-time ModuleNotFoundError) today."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_filename_shaped_like_the_spurious_token_never_yields_a_story_level_item(self):
        # local import: keep this file's leg-1/leg-2 tests importable and
        # passable even while tracker.projector does not exist yet.
        from tracker.projector import build_projection
        from tracker.tests.boardfixture import write_event

        # the header carries NO level: at all -- if the projector ever
        # fell back to sniffing the filename, this is where it would show.
        write_event(self.root, "Requests", SPURIOUS_TOKEN_FILENAME, header={"for": "ip-man"})
        # one ordinary, valid item elsewhere, to prove one bad filename
        # does not sink the rest of the board (D1: report, never refuse).
        write_event(self.root, "Requests", "TS-20260101-venom-700.000-OPEN__by-venom.txt",
                    header={"level": "epic", "project": "townsquare"})

        result = build_projection(self.root)  # must not raise

        self.assertEqual(["TS-20260101-venom-700"], [n["id"] for n in result["projects"]["townsquare"]])
        unparseable = [u for u in result["unparseable_filenames"] if u["path"].endswith(SPURIOUS_TOKEN_FILENAME)]
        self.assertEqual(1, len(unparseable))
        self.assertIn("duplicate slug field", unparseable[0]["error"])


if __name__ == "__main__":
    unittest.main()
