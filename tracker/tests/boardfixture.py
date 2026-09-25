"""Test-only fixture builder for the project-tracker's board reader.

This module is NOT the tracker implementation (that is bruce-lee's, in
tracker/projector.py, after these tests exist and correctly fail against
nothing). It only writes small, synthetic, on-disk TownSquare board
directories -- a handful of files per fixture -- so tracker tests exercise
real file I/O (real header text, real filenames run through the canonical
registrar.app.filename.parse_filename) without ever touching the real Drive
mount. This mirrors the "pure-fixture... no live Drive data" rule
registrar/tests/test_legacy_taxonomy.py states for its own corpus.

Layout built: <root>/<board>/<filename>, where <board> is one of the five
folder names this module and the design docs both use verbatim:
    "Requests", "Seeking", "Wanted", "Bulletin Board", "Archive"
The first four match registrar/tests/test_legacy_taxonomy.py's own fixture
folder names exactly. "Archive" is this suite's own assumption -- flagged in
the ronda-rousey handback -- that TSD s8's post-60-day archive mirrors the
same per-board subfolders live boards use (e.g. Archive/Requests/...), since
nothing in the design docs pins Archive's internal shape and this suite has
no access to the real Drive mount to check it directly.

Every fixture file's mtime is pinned explicitly with os.utime() right after
writing. This suite's tracker/projector contract (see test_header_parsing.py)
reads "last-activity" from the filesystem's own timestamp as the local stand-
in for Drive's createdTime, per design v2 doc s2 A5 ("last-activity time
comes from Drive createdTime, not the at: field"). That is a fixture-author
choice this suite makes explicit, not a design-doc ruling: the design only
pins WHICH field is authoritative for display (createdTime, never at:), not
how a local, non-Drive test fixture should manufacture a stand-in for it.
The choice is deliberate rather than arbitrary: design v1 doc s6 states the
trial itself runs the projector directly against a Drive-Desktop-synced
local folder (G:\\My Drive\\N3rd0m\\TownSquare on venom), so plain filesystem
timestamps are what the real trial deployment reads too, not a separate
Drive-API metadata channel.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

BOARD_NAMES = ("Requests", "Seeking", "Wanted", "Bulletin Board", "Archive")

# Fixed synthetic base epoch (2026-09-21T00:00:00Z-ish) so fixtures are
# byte-for-byte deterministic across machines and runs; never wall-clock now().
BASE_TS = 1_790_000_000


def expected_last_activity(minutes_after_base: int = 0) -> str:
    """The one place that turns a fixture's minutes_after_base into the
    exact string this suite expects build_projection's rollup.last_activity
    to carry: seconds-precision ISO 8601 UTC with a trailing "Z" (matching
    the `at:` field's own style in every design-doc template, e.g.
    "2026-09-25T15:00Z"). This is this suite's own interface choice -- the
    design docs pin WHICH source is authoritative (Drive createdTime, never
    at:), not a wire format for it -- kept in one place so every test file
    that checks last_activity agrees with write_event's own timestamp math
    by construction, not by four separately hand-derived date strings."""
    ts = BASE_TS + minutes_after_base * 60
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_event(
    root: Path,
    board: str,
    filename: str,
    header: dict | None = None,
    extra_header_lines: list | None = None,
    body: str = "BODY.\n",
    minutes_after_base: int = 0,
    no_terminator: bool = False,
    as_directory: bool = False,
) -> Path:
    """Write one synthetic TownSquare event file inside <root>/<board>/.

    `header` is an ordered mapping of header-line key -> value, written one
    per line as "key:  value" (two-space gap after the colon, matching the
    cosmetic look of the design docs' own templates -- a reader must not
    depend on column alignment, and no test here does). `extra_header_lines`
    are raw strings written verbatim right after the mapped ones -- the only
    way to construct a deliberately-duplicated key (a plain dict can't hold
    two values for one key) or a hand-crafted indented continuation line.

    A header block is only "closed" by a line that is EXACTLY "---". Pass
    `no_terminator=True` to omit it entirely (an old, header-less file).

    `minutes_after_base` pins this file's mtime deterministically, standing
    in for Drive createdTime (see module docstring). Later minutes = later
    "last activity", and the (sequence, time) tie-break reads this too.

    `as_directory=True` creates a directory at this path instead of a file --
    the fixture for an object the projector cannot read as text at all (see
    test_flags.py::FlagsTests.test_unreadable_header_is_reported_not_raised).
    Fully portable: opening a directory as a text file raises IsADirectoryError
    on POSIX and PermissionError on Windows, and both are OSError subclasses,
    which is the only thing this suite's contract for read_event_header pins.
    """
    board_dir = root / board
    board_dir.mkdir(parents=True, exist_ok=True)
    path = board_dir / filename
    if as_directory:
        path.mkdir(parents=True, exist_ok=True)
        return path
    lines = [f"{key}:  {value}" for key, value in (header or {}).items()]
    lines.extend(extra_header_lines or [])
    if not no_terminator:
        lines.append("---")
    text = "\n".join(lines)
    if lines:
        text += "\n"
    text += body
    path.write_text(text, encoding="utf-8")
    ts = BASE_TS + minutes_after_base * 60
    os.utime(path, (ts, ts))
    return path


def new_board(root: Path) -> None:
    """Pre-create all five board folders, even ones a given fixture leaves
    empty, so a board-wide walk never has to special-case a missing folder."""
    for name in BOARD_NAMES:
        (root / name).mkdir(parents=True, exist_ok=True)
