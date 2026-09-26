"""Reproduction tests for three EXISTING registry correctness bugs surfaced by
helio-gracie's checkpoint on ip-man's registry offsite-binding design note
(C:\\Repo\\townsquare\\docs\\ip-man-registry-offsite-binding-design-20260926.md).

These are NOT tests for the offsite-binding fix itself (that is decision 6's
T1-T12 in the design note, ss4). They reproduce-and-document three bugs found
IN THE BASELINE CODE while reviewing it, ahead of any ruling on remediation.
Each corresponds to a bug report at:
  C:\\Repo\\townsquare\\docs\\bug-report-registry-name-normalization-20260926.md
  C:\\Repo\\townsquare\\docs\\bug-report-registry-stale-write-signal-20260926.md
  C:\\Repo\\townsquare\\docs\\bug-report-registry-partial-section-bypass-20260926.md

Baseline commit under test: ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf
(terrence-adams/Wonderland, main), cloned fresh to a scratchpad - never the
NAS, never C:\\Repo\\townsquare.

Isolation: run this file BY ITSELF, in its own interpreter, separate from
tests/test_registry.py - both files set process-wide env vars and import
`app` at module scope, and `app`'s module-level state (db, journal, outbox,
background threads) is created exactly once per process on first import.
Mixing the two files in one pytest collection would let whichever imports
`app` first silently decide the other's env-var-driven paths.

    /path/to/venv/python -m pytest test_decision6_bug_reports_20260926.py -v

Every path below is a fresh temp directory created by THIS process; REG_POLL,
REG_PUBLISH and REG_PUBLISH_LOOP are all forced off; REG_SEED_MD is blanked;
no secrets/ or rclone config is present or referenced.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Isolation: set BEFORE `import app` (module-level side effects at import: ---
# --- background poll/publish threads, DB open, seed-if-empty).               ---
_HERE = os.path.dirname(os.path.abspath(__file__))
_SERVICE_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
assert not os.path.isdir(os.path.join(_SERVICE_ROOT, "secrets")), (
    "a secrets/ dir must never be present for this reproduction run")

_APPDIR = tempfile.mkdtemp(prefix="regqa_bugs_")
os.environ["REG_POLL"] = "0"               # no background crier-poll thread
os.environ["REG_PUBLISH"] = "0"            # no board-publish attempts
os.environ["REG_PUBLISH_LOOP"] = "0"       # no periodic drain thread either
os.environ["REG_SEED_MD"] = ""             # never seed from the real fleet doc
os.environ["REG_DB"] = os.path.join(_APPDIR, "registry.db")
os.environ["REG_JOURNAL"] = os.path.join(_APPDIR, "journal.log")
os.environ["REG_OUTBOX"] = os.path.join(_APPDIR, "outbox")
os.environ.pop("RCLONE_CONFIG", None)      # never point at a real rclone config
os.environ.pop("REG_CRIER_URL", None)

import app as regapp                       # noqa: E402  (import after env setup)
from registry.db import RegistryDB         # noqa: E402
from registry import schema                # noqa: E402

_client = regapp.app.test_client()

VALID_KEY_1 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOriginalKeyDataxxxxxxxxxx== test@orig"
VALID_KEY_2 = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAttemptedNewKeyDataxxxxxx== test@new"


def _fresh_db() -> RegistryDB:
    """A throwaway RegistryDB on its own temp file, for tests that need
    db.py-level access without the shared Flask app's state (matches
    tests/test_registry.py's own `_db()` convention)."""
    fd, p = tempfile.mkstemp(suffix=".db", dir=_APPDIR)
    os.close(fd)
    return RegistryDB(p)


def test_isolation_touches_nothing_outside_its_own_temp_dir():
    """Self-check (the task's own instruction): confirm every path this run
    writes to lives under this process's own temp dir, not data/, not the
    NAS, not C:\\Repo\\townsquare."""
    assert regapp.DB_PATH.startswith(_APPDIR)
    assert regapp.JOURNAL_PATH.startswith(_APPDIR)
    assert regapp.OUTBOX_DIR.startswith(_APPDIR)
    assert regapp._publisher.enabled is False
    assert "192.168.2.3" not in (os.environ.get("REG_CRIER_URL") or "")


# ===========================================================================
# Bug 1: name-normalization inconsistency between validation and what the
# journal/audit trail actually records for `agent`.
# ===========================================================================
# Mechanics, confirmed by reading the code (not the lead's hypothesis as-is):
#   - schema.validate_record() matches AGENT_RE against a LOCAL, STRIPPED
#     copy (`agent = str(rec.get("agent","")).strip()`) - it never writes
#     that stripped copy back into `rec`.
#   - app.register() then does `name = rec.pop("agent")`, which is the RAW,
#     UN-stripped value from the request body.
#   - db.get() and db.upsert() BOTH strip internally (db.py:166 `agent.strip()`
#     in the SQL param; db.py:98 `agent = agent.strip()` at the top of
#     upsert()). Because both call sites normalize the SAME way, `before`,
#     the upsert target, and `after` all resolve to the SAME canonical row -
#     the lead's literal "before sees no existing row" framing does NOT
#     reproduce here (asserted below as a documented negative result).
#   - What is NOT re-stripped is `name` itself, used verbatim for the
#     JOURNAL's top-level `agent` field (app.py's `_journal.record("register",
#     name, ...)`) and, through it, the rendered board-audit text artifact.
#     That IS reproducible: one audit record ends up with two different
#     spellings of the same agent.
def test_register_trailing_newline_name_row_identity_is_consistent():
    """Documents a NEGATIVE result for the literal lead as given: row
    identity (before/upsert/after) is NOT split by trailing whitespace,
    because db.get()/db.upsert() strip consistently (db.py:98, db.py:166).
    Deliberately does not assert on the HTTP status of the second request -
    see test_register_trailing_newline_name_crashes_the_audit_write for what
    that status actually is on this platform, and why. db.upsert() commits
    its write before the journal/artifact step that can raise, on every
    platform, so the row mutation is checkable regardless."""
    r1 = _client.post("/register", json={"agent": "claude-app",
                                          "binding": "portable"})
    assert r1.status_code == 200, r1.get_data(as_text=True)

    _client.post("/register", json={
        "agent": "claude-app\n",             # trailing newline
        "pubkey": VALID_KEY_1,
    })

    # Exact-key match only (not a prefix LIKE): other tests in this same
    # shared-app file register names like "claude-app-j" / "claude-app-sp",
    # and a loose 'claude-app%' pattern would collide with those depending on
    # test execution order - caught by running this suite both under
    # pytest's definition order and the file's own alphabetical-by-name
    # __main__ runner, which disagreed until this was tightened.
    rows = regapp.db.conn.execute(
        "SELECT agent, pubkey FROM agents WHERE agent IN (?, ?)",
        ("claude-app", "claude-app\n"),
    ).fetchall()
    keys = [r["agent"] for r in rows]
    assert keys == ["claude-app"], (
        f"expected exactly one canonical row 'claude-app', got {keys!r} - "
        "a split-brain row would appear here as a second, differently-keyed "
        "entry")
    assert dict(rows[0])["pubkey"] == VALID_KEY_1, (
        "the update should land on the SAME pre-existing row")


def test_register_trailing_newline_name_corrupts_journal_agent_field():
    """THE BUG (portable across OS): journal.log's own `agent` field for this
    write is the RAW, un-stripped name - not the canonical one the SAME
    entry's nested after.agent shows. journal.log's append-only line (step 1
    of Journal.record, journal.py ~84-89) is written and fsync'd BEFORE the
    outbox-artifact step that can raise (step 2, ~90-96; see the companion
    crash test), so this holds even on a platform where that later step
    fails outright."""
    r1 = _client.post("/register", json={"agent": "claude-app-j",
                                          "binding": "portable"})
    assert r1.status_code == 200, r1.get_data(as_text=True)

    _client.post("/register", json={
        "agent": "claude-app-j\n",
        "pubkey": VALID_KEY_1,
    })

    entries = regapp._journal.read()
    entry = entries[-1]
    assert entry["op"] == "register"
    assert entry["agent"] == "claude-app-j", (
        f"journal top-level agent={entry['agent']!r} does not match the "
        f"canonical name reflected in its own nested state "
        f"(after.agent={entry['after']['agent']!r}) - one audit record, two "
        "spellings of the same agent")
    assert entry["after"]["agent"] == "claude-app-j"   # the canonical side (control)


def test_register_trailing_newline_name_crashes_the_audit_write():
    """A second, more severe manifestation of the same root cause -
    confirmed on two OSes (Windows via this suite; Linux separately via a
    direct WSL2/ext4 probe, matching the production container's OS family):

      - Windows/NTFS (this interpreter, Python 3.14.6): the raw agent name
        becomes part of the OUTBOX ARTIFACT'S FILENAME
        (journal.py's _outbox_filename()/_render_artifact()). NTFS rejects a
        control character in a filename, so Journal.record() raises OSError
        AFTER the DB write is already committed and AFTER the durable
        journal.log line is already fsync'd - Flask turns this into a bare
        500, and an accepted, applied write ends up with NO board-publishable
        audit artifact at all, while the client is told the request failed.
      - Linux/ext4 (verified separately: `open()` on a path whose filename
        component contains a raw '\\n' does NOT raise - POSIX allows it).
        So in the actual production container this exact request most likely
        returns 200 with a malformed filename on disk (containing a literal
        newline byte) rather than a 500 - itself still a defect, and a
        plausible rejection point for rclone/Drive's own upload of that same
        filename, which is this artifact's whole purpose.

    This test asserts what this interpreter/OS actually does; the bug report
    carries the Linux difference explicitly rather than asserting an
    unverified claim about the deployed platform."""
    r1 = _client.post("/register", json={"agent": "claude-app-crash",
                                          "binding": "portable"})
    assert r1.status_code == 200, r1.get_data(as_text=True)

    r2 = _client.post("/register", json={
        "agent": "claude-app-crash\n",
        "pubkey": VALID_KEY_1,
    })
    assert r2.status_code == 200, (
        "a request that DID mutate the database (see the row-identity test) "
        "is reported to its caller as a hard server error, with no audit "
        f"artifact ever written for it - got {r2.status_code}: "
        f"{r2.get_data(as_text=True)[:300]}")


def test_register_leading_and_trailing_space_name_same_journal_defect():
    """The same defect for plain leading/trailing spaces (not just \\n),
    since AGENT_RE's `$`-before-newline quirk is a red herring here - the
    actual cause is that validate_record()'s .strip() is never written back,
    which applies to ANY leading/trailing whitespace, not only a newline."""
    r1 = _client.post("/register", json={"agent": "claude-app-sp",
                                          "binding": "portable"})
    assert r1.status_code == 200, r1.get_data(as_text=True)

    r2 = _client.post("/register", json={
        "agent": "  claude-app-sp  ",       # leading AND trailing spaces
        "pubkey": VALID_KEY_2,
    })
    assert r2.status_code == 200, r2.get_data(as_text=True)

    # Row identity still consistent (same root cause as the newline case).
    row = regapp.db.get("claude-app-sp")
    assert row is not None and row["pubkey"] == VALID_KEY_2

    entry = regapp._journal.read()[-1]
    assert entry["agent"] == "claude-app-sp", (
        f"journal agent field retained whitespace: {entry['agent']!r}")


# ===========================================================================
# Bug 2: the recency guard (bug-007) leaves its caller with no accurate
# signal that a "stale" write was silently dropped.
# ===========================================================================
def test_stale_upsert_gives_its_python_caller_no_signal():
    """db.upsert() correctly refuses to regress field values on a stale
    write (this part is already covered by test_bug007_recency_guard) - but
    it communicates that decision to its OWN caller in no structured way at
    all: it has no return value."""
    db = _fresh_db()
    db.upsert("stale-guard-agent", source="test", at="2026-09-20T10:00:00Z",
              binding="host:X", section="host_bound", pubkey=VALID_KEY_1)
    assert db.get("stale-guard-agent")["pubkey"] == VALID_KEY_1

    # A write that arrives "late" (older `at`) tries to change the pubkey.
    result = db.upsert("stale-guard-agent", source="test",
                        at="2026-09-19T10:00:00Z", pubkey=VALID_KEY_2)

    # The guard did its one job: no regression.
    assert db.get("stale-guard-agent")["pubkey"] == VALID_KEY_1

    # THE BUG: nothing tells the caller the write was a no-op.
    assert result is not None, (
        "db.upsert() returned None for a stale, silently-dropped write - "
        "its caller has no return value to inspect, and can only discover "
        "the drop by separately re-reading the row and diffing it "
        "themselves against what they just sent")


def test_stale_write_via_register_endpoint_is_indistinguishable_from_success():
    """Same guard, exercised through the real public API. /register always
    computes `at` as the server's own wall-clock 'now' (it never reads an
    `at` from the request body), so reaching the guard through HTTP needs
    either a genuine race between concurrent requests, or - deterministically,
    for this reproduction - control of the server's clock, exactly the way a
    request that is delayed in flight relative to a newer one would. The
    journal is the audit trail (its own docstring's word) for accepted
    writes; if it cannot tell a caller "your fields were dropped" apart from
    "your fields were applied", the audit trail is misleading by
    construction, independent of whatever surface a fix eventually adds this
    signal to."""
    import datetime as _dtmod
    from unittest.mock import patch

    class _Frozen(_dtmod.datetime):
        _t = None

        @classmethod
        def now(cls, tz=None):
            return cls._t

    t_new = _dtmod.datetime(2026, 9, 20, 10, 0, 0, tzinfo=_dtmod.timezone.utc)
    t_old = _dtmod.datetime(2026, 9, 19, 10, 0, 0, tzinfo=_dtmod.timezone.utc)

    with patch("datetime.datetime", _Frozen):
        _Frozen._t = t_new
        r1 = _client.post("/register", json={"agent": "race-agent",
                                              "binding": "portable",
                                              "pubkey": VALID_KEY_1})
        assert r1.status_code == 200, r1.get_data(as_text=True)

        _Frozen._t = t_old
        r2 = _client.post("/register", json={"agent": "race-agent",
                                              "pubkey": VALID_KEY_2})
    assert r2.status_code == 200, r2.get_data(as_text=True)

    # Sanity: the guard really did fire - the later-arriving-but-older write
    # did not win.
    assert regapp.db.get("race-agent")["pubkey"] == VALID_KEY_1

    entry = regapp._journal.read()[-1]
    assert entry["agent"] == "race-agent" and entry["op"] == "register"

    # THE BUG: this accepted-write journal entry is indistinguishable from a
    # normal successful update. before/after both show the OLD pubkey (the
    # caller's submitted value never appears anywhere in the entry), and
    # nothing in the entry says the write was rejected as stale.
    dropped_silently = (
        entry["before"]["pubkey"] == entry["after"]["pubkey"] == VALID_KEY_1
        and "stale" not in json.dumps(entry).lower()
    )
    assert not dropped_silently, (
        f"a stale write journaled as if it had been applied: {entry!r}")


# ===========================================================================
# Bug 3: a partial write can change `section` without being checked against
# the row's EXISTING binding.
# ===========================================================================
def test_partial_section_only_update_bypasses_binding_contradiction_check():
    """schema.validate_record()'s contradiction check ("section ...
    contradicts binding") only runs when BOTH fields are present in the SAME
    request body (schema.py ~85-90). A request supplying only `section` (no
    `binding`) is validated against nothing but itself, so it is accepted
    even when it contradicts the row's real, existing binding."""
    r1 = _client.post("/register", json={"agent": "sect-test-1",
                                          "binding": "host:TestHost"})
    assert r1.status_code == 200, r1.get_data(as_text=True)
    row1 = regapp.db.get("sect-test-1")
    assert row1["binding"] == "host:TestHost" and row1["section"] == "host_bound"
    assert schema.derive_section(row1["binding"]) == row1["section"]  # consistent so far

    # Partial update naming ONLY `section`, contradicting the EXISTING
    # binding; `binding` is entirely absent from this request body.
    r2 = _client.post("/register", json={"agent": "sect-test-1",
                                          "section": "portable"})

    # THE BUG: accepted. A check that considered the row's real, existing
    # binding (not just this request's own body) would reject this the same
    # way test_forge_amendment2_section_derived_and_contradiction already
    # proves a same-body contradiction is rejected.
    assert r2.status_code == 400, (
        "partial update silently reclassified the section without checking "
        f"it against the row's existing binding: {r2.get_data(as_text=True)}")

    row2 = regapp.db.get("sect-test-1")
    assert schema.derive_section(row2["binding"]) == row2["section"], (
        f"stored row is now internally inconsistent: binding={row2['binding']!r} "
        f"derives {schema.derive_section(row2['binding'])!r}, but "
        f"section={row2['section']!r}")


def test_partial_write_also_resets_omitted_binding_to_unknown():
    """Related compounding effect found while reproducing bug 3, flagged
    here for the record (see the bug report's "context" section): the
    partial update above does not just fail to validate the section against
    the EXISTING binding - normalize_record() cannot tell "this request
    omitted binding" from "this is a brand-new record with no binding yet",
    so it defaults the OMITTED field to 'unknown' and that gets upserted,
    discarding the row's real prior binding. This means bug 3 is not just a
    validation gap; the write itself clobbers a field the request never
    mentioned."""
    r1 = _client.post("/register", json={"agent": "sect-test-2",
                                          "binding": "host:AnotherHost",
                                          "vendor": "Anthropic"})
    assert r1.status_code == 200, r1.get_data(as_text=True)
    before = regapp.db.get("sect-test-2")
    assert before["binding"] == "host:AnotherHost"
    assert before["vendor"] == "Anthropic"

    r2 = _client.post("/register", json={"agent": "sect-test-2",
                                          "section": "portable"})
    assert r2.status_code == 200, r2.get_data(as_text=True)  # accepted (bug 3)

    after = regapp.db.get("sect-test-2")
    assert after["binding"] == "host:AnotherHost", (
        "a partial write that never mentioned `binding` silently reset it "
        f"to {after['binding']!r} - the row's real binding is gone")
    assert after["vendor"] == "Anthropic", (
        "a partial write that never mentioned `vendor` silently reset it "
        f"to {after['vendor']!r}")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed, failed = 0, []
    for fn in fns:
        try:
            fn()
            print("  ok  ", fn.__name__)
            passed += 1
        except AssertionError as e:
            print("  FAIL", fn.__name__, "-", e)
            failed.append(fn.__name__)
    print(f"\n{passed}/{len(fns)} passed")
    if failed:
        print("FAILED:", ", ".join(failed))
