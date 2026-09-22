r"""Read-only inventory planner for legacy Drive metadata JSON.

jackie-chan / WS2b (Town Registrar dry-run, revision-2 work order).

Scope discipline (see docs/town-registrar-ws1-ws2-plan.md, "Implement (WS2b)"):
  - Pure function over `inventory.json`. No Drive access, no content reads.
  - `registrar/app/filename.py` is UNTOUCHED. Grammar-B objects (the OFFER
    `host-` field and the standalone `.md` WANT shape) are classified and
    counted by pattern-matching in THIS file, never by extending the shared
    parser. That parser is shared with Crier by design.
  - `check_header` is never called here. Its zero-padding/missing-priority
    defect (filename.py ~line 45: `str(int(parsed["seq"]))` vs a zero-padded
    legacy header, and a `priority:` header legacy posts never carry) means
    design step 3 (header/signature verdicts) is explicitly deferred this
    pass, not silently skipped. Recorded below under `known_defects`.
  - `content_sha256` is never computed here. Every row that doesn't already
    carry its own `content_sha256_status` (i.e. every real dry-run row, since
    the collector never reads content either) is stamped `not_computed_dry_run`.

Taxonomy design notes (why the branching order below is what it is):

  1. Collector defects are separated FIRST, before anything else looks at a
     row. tony-jaa's merge_inventory.py pre-tags a missing Drive file ID with
     `collector_defect: "missing_drive_file_id"`, but this planner does not
     trust that tag alone — it independently re-checks `drive_file_id`
     truthiness, because a bug in the tagging would otherwise crash post_uid
     generation (`uuid.uuid5` on `None`) instead of being reported. A
     collector defect is a fact about the tool that produced inventory.json,
     never a fact about TownSquare's history, so it is excluded from every
     corpus-exception bucket, not merged into `quarantined`.

  2. Folder branches BEFORE extension (jigoro-kano's WS1 finding). The board
     root and folders like `Reliability` hold standing documents (doctrine,
     protocols, registers) in any extension, including `.txt` — a bare
     extension check would misclassify `TOWN-SQUARE-DOCTRINE-v1.5-...txt` and
     `ACCURACY-PROTOCOL-v0.2-...md` alike as corpus exceptions. Only rows
     inside a recognized post-bearing folder (`Requests`, `Bulletin Board`,
     `Seeking`, `Wanted` — the four boards the design and WS1 note cite) are
     even considered post candidates. Everything else, of any extension
     including `.sig`, is `non_post_artifact` — deliberately broader than the
     `.md`/`.gdoc` example in the work order, because the same folder logic
     applies to a board-root doctrine `.sig` exactly as it does to a
     board-root doctrine `.md`: neither is a fact about a post.

     Rows with no `parent_folder_path` key at all (as opposed to an empty
     string) are treated as folder-unknown, not folder-excluded. Real
     collector rows always carry the key (merge_inventory.py sets it to ""
     for board-root objects); its total absence only happens on the older,
     simplified fixtures already exercised by registrar/tests/test_registrar.py
     (e.g. `{"name": ..., "drive_file_id": ...}` with no folder metadata at
     all). Those fixtures predate the collector schema and are preserved
     as-is rather than silently reclassified as non-post artifacts.

  3. Extension branches next (R7). `NAME_RE` anchors on `\.txt$`, so every
     `.gdoc`/`.md` row would otherwise raise the same generic
     "invalid TownSquare filename" as genuine corruption. `.gdoc` rows never
     reach the parser at all (native-Doc class). `.md` rows in a board folder
     never reach the parser either (`legacy_nonconforming`, the standalone
     WANT shape, per jigoro-kano's WS1 ruling).

  4. Within the surviving `.txt`-and-unrecognized-extension set, an OFFER
     filename carrying a `host-` token is diverted before parsing too — not
     because it would error (sometimes it wouldn't: if there's no second slug
     token, `host-<x>` would be silently absorbed as *the* slug, which is
     wrong data with no signal, same failure shape as class 6 below) but
     because W1-5/jigoro-kano's WS1 finding makes it a confirmed-doctrine
     grammar, not a corruption. Scoped to `OFFER-` names specifically,
     matching where the doctrine confirmation applies (design §7b); a
     `host-` token elsewhere is unexpected and correctly falls through to
     the generic parser.

  5. Only what's left is handed to the unmodified `parse_filename`. Two
     distinct failure shapes from there (the R7 finding, "not one class"):
       - silent: `for-`/`cap-`/`cat-` ARE legitimate typed fields in the
         design's own list, so the parser cannot tell a correctly-typed
         field from a slug that coincidentally starts with the same prefix.
         Every occurrence is counted for human review (`silent_typed_field_
         absorption`) without being pulled out of `posts` — the parse did
         succeed, the risk is just that its data may be wrong.
       - loud: `mode-<x != break-glass>` and `pid-<non-ULID>` raise
         `FilenameError` with the exact messages "unsupported mode" /
         "noncanonical pid". Those two messages are routed to
         `hard_rejections`, a class distinct from generic `quarantined`
         (any other parse failure — truly unparseable names).

  6. `shortcut_objects` (gsp's CP1 finding, 2026-09-21) is a structurally
     SEPARATE input list from `rows` — the collector (merge_inventory.py)
     isolates it at the source via a Path-diff against a third `lsjson` pass,
     because rclone v1.75.1 dereferences Drive shortcuts by default (keeps
     the shortcut's own Path/Parents, substitutes the TARGET's file ID/MIME/
     size/checksum). Left unmitigated, that made the collector's effective
     read boundary the declared root PLUS the transitive closure of every
     shortcut target anywhere in the `drive.readonly`-scoped account — a
     disclosure-boundary containment issue, not merely a de-dup bug. This
     planner never merges `shortcut_objects` into `posts`, `non_post_
     artifacts`, or anything else: every row is counted, visible, and
     labeled with the fact that its `drive_file_id`/`mime_type`/`size`
     describe the shortcut's target, not the shortcut itself.

  7. Trashed-ness (WS3 item 2, 2026-09-22) is checked immediately AFTER the
     folder gate and BEFORE every other board-folder branch (sidecar/
     native-doc/`.md`/host-field/parse) — deliberately, so a trashed object
     is diverted to `trashed_board_objects` regardless of what shape it
     would otherwise have been classified as. This is what makes trashed-
     ness and native-Doc-ness (point 3's detection) compose correctly when
     they intersect on the same real object: native-doc-ness is still
     computed and carried as a cross-cutting `native_doc` tag on whichever
     bucket the row actually lands in, but ROUTING is decided by trashed-
     ness first, so an object can never be double-counted across
     `trashed_board_objects` and `native_doc_objects`, and can never fall
     between the two. `trashed_board_objects` rows never reach `posts` or
     `artifacts` — Drive purges trash on a schedule this collector cannot
     observe exactly (bounded above by ~30 days from collection), so this
     class carries full per-object Drive metadata, not just a count: it may
     be the only surviving record of these objects once that window closes.

Backward compatibility with the pre-existing report shape (relied on by
registrar/app/service.py's `stage_import`, which parses `manifest["posts"]`
and `manifest.get("artifacts", [])` again on its own and by
registrar/tests/test_registrar.py):
  - `posts` keeps exactly the prior per-row shape/field set. Only rows that
    parsed successfully through the unmodified shared parser ever appear
    here — `stage_import` calls `parse_filename(item["filename"])` on every
    post again, so anything grammar-B/native-doc/quarantined/hard-rejected
    MUST NOT be placed in `posts`, or staging a real manifest later would
    crash instead of reporting.
  - `artifacts` keeps its prior shape (`stage_import` requires
    `{"drive_file_id","filename","kind","parent_post_uid","warnings"}` with
    `kind == "signature"`).
  - `collisions` is kept as a deprecated superset alias
    (`duplicate_openings + duplicate_sequences`) so the existing
    `test_import_duplicate_is_deterministic` assertion continues to hold;
    new code should read `duplicate_openings`/`duplicate_sequences` instead.
  - `dry_run` and `objects` are unchanged in meaning.

Determinism (design §9 step 11 / R2's "3a"): every list below is built either
by a single pass over the input in its original (JSON-array, hence
insertion-preserving) order, or by an explicit `sorted(..., key=...)` before
being appended to the report. Python `set`/`Counter` objects are used only
for O(1) membership/count lookups in this file, never iterated directly into
output — CPython randomizes `hash(str)` per process by default
(`PYTHONHASHSEED`), so iterating a `set` of strings can silently differ
between two separate `python` invocations even on identical input. `dict`
iteration order is insertion order (language-guaranteed, not hash-order), and
`json.dumps(..., sort_keys=True)` additionally normalizes every dict's key
order recursively; the one thing that guarantee does NOT cover is array
(list) element order, which is why every list here is explicitly ordered.
"""
import argparse, json, uuid
from collections import Counter, defaultdict
from registrar.app.filename import FilenameError, parse_filename

IMPORT_NAMESPACE = uuid.UUID("b8a04d34-91ab-51b5-a12d-4e9994793b38")

# The four post-bearing boards named in the design and the WS1 note's live
# examples. A row's folder is compared against the FIRST path segment only,
# so a recognized board's subfolder (if one ever exists) still counts as
# board-bearing; anything else -- including the board root ("") and
# `Reliability` -- does not.
POST_BOARD_FOLDERS = {"Requests", "Bulletin Board", "Seeking", "Wanted"}

# The two FilenameError messages that are loud, structural rejections
# (R7: "opposite failure modes, separate counts" from the silent class).
HARD_ERROR_MESSAGES = {"noncanonical pid", "unsupported mode"}

# Typed fields that are legitimate in the design's own field list but that
# the parser cannot distinguish from a same-prefixed slug (R7's silent class).
# "mode" is deliberately excluded: R7 reclassifies mode-<non-break-glass> as
# a HARD error, not a silent absorption; mode-break-glass is a fully valid,
# doctrine-sanctioned value and is not flagged at all.
SILENT_ABSORPTION_KEYS = ("for", "cap", "cat")

DEFERRED_DESIGN_STEPS = [
    "design_step_3_header_signature_verdicts",
    "design_step_9_webviewlink_canonical_url",
]

KNOWN_DEFECTS_RECORDED_NOT_FIXED = [
    {
        "id": "check_header_zero_padding_and_missing_priority",
        "location": "registrar/app/filename.py check_header (~line 45)",
        "finding": (
            "check_header compares str(int(parsed['seq'])) (e.g. '2') against "
            "zero-padded legacy headers (e.g. '002'), and expects a 'priority:' "
            "header line that legacy posts never carry (filenames carry P2 "
            "instead). This fails on effectively every legacy post."
        ),
        "action_this_pass": (
            "check_header is never called by this planner. Design section 9 "
            "step 3 (header/signature verdicts) is explicitly deferred, not "
            "silently skipped."
        ),
        "owner": "WS7 (future pass, per the WS1-2 work order)",
    }
]


def _extract_rows(objects):
    """Accept either the real collector's wrapped inventory (a dict with a
    'rows' list) or a bare list (the shape used by pre-existing fixtures in
    registrar/tests/test_registrar.py). Never mutates the input."""
    if isinstance(objects, dict):
        rows = objects.get("rows")
        if not isinstance(rows, list):
            raise ValueError("inventory dict is missing a 'rows' list")
        return rows
    if isinstance(objects, list):
        return objects
    raise ValueError("inventory must be a list of objects or a dict with a 'rows' list")


def _extract_shortcut_rows(objects):
    """gsp's CP1 finding (2026-09-21): merge_inventory.py now emits a
    separate, explicitly-quarantined `shortcut_objects` list -- Drive
    shortcuts, detected via a Path diff, whose drive_file_id/mime_type/size
    describe the shortcut's TARGET (rclone v1.75.1 dereferences by default),
    never the shortcut itself. Bare-list fixtures (pre-existing tests, and
    this planner's own pre-CP1 fixtures) predate this class entirely -- there
    is nothing to report for them, not an error."""
    if isinstance(objects, dict):
        rows = objects.get("shortcut_objects")
        if rows is None:
            return []
        if not isinstance(rows, list):
            raise ValueError("inventory dict 'shortcut_objects' must be a list")
        return rows
    return []


def _board_folder_status(obj):
    """Tri-state: 'board' (post-bearing folder), 'non_board' (anything else,
    including root), or 'unknown' (no folder metadata present at all -- only
    true for pre-collector-schema fixtures; treated permissively, i.e. as if
    board-bearing, to preserve their existing behavior)."""
    if "parent_folder_path" not in obj:
        return "unknown"
    path = obj.get("parent_folder_path") or ""
    first_segment = path.split("/", 1)[0] if path else ""
    return "board" if first_segment in POST_BOARD_FOLDERS else "non_board"


def _board_of(obj):
    """First path segment of parent_folder_path -- the actual board name
    ('Requests', 'Bulletin Board', ...) for a row the folder gate already
    let through, or the standing-document folder name for a non_board row.
    Returns None (never the string 'legacy') when parent_folder_path is
    absent or empty, so callers can tell "no real board could be derived"
    apart from a genuine board name and decide explicitly how loud to be
    about it, instead of a silent string default.

    WS3 CP-A1 finding (2026-09-22): legacy.py:526's prior
    `item.get("board","legacy")` was a DEFAULT for a field this planner
    never populated anywhere -- not a hardcode with the same name, a
    different bug shape entirely. `merge_inventory.py`'s collector never
    emits a "board" key at all (it emits `parent_folder_path`, which this
    function derives "board" FROM), so that fallback fired on every single
    row, unconditionally, silently turning `posts.board` -- a NOT NULL
    column the read API filters on -- into one useless constant for all of
    history. This helper is the actual fix; the five call sites below (plus
    the posts pipeline itself) populate `item["board"]` with it so the old
    fallback becomes the genuine last-resort it was designed to be, not the
    only code path that ever ran."""
    path = obj.get("parent_folder_path")
    if not path:
        return None
    return path.split("/", 1)[0]


def _extension(name):
    lower = name.lower()
    if lower.endswith(".gdoc"):
        return ".gdoc"
    if lower.endswith(".md"):
        return ".md"
    if lower.endswith(".txt"):
        return ".txt"
    return None


GOOGLE_NATIVE_MIME_PREFIX = "application/vnd.google-apps."
GOOGLE_NATIVE_MIME_EXCLUDED = {
    GOOGLE_NATIVE_MIME_PREFIX + "folder",
    GOOGLE_NATIVE_MIME_PREFIX + "shortcut",
}

# WS3 CP-A1 finding #3 (2026-09-22): the LIVE collector run never observes a
# bare `application/vnd.google-apps.*` mimetype on a native Doc at all.
# Confirmed by direct inspection of lsjson-active.json/lsjson-trashed.json:
# all 5 real native Docs in this corpus (4 active, 1 trashed) carry
# `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
# (Google's default Office-export mimetype for Docs), a `.docx` name,
# `Size: -1` (-> null after merge_inventory.py's normalization), and no
# `Hashes.md5` at all -- rclone v1.75.1 with no --drive-export-formats flag
# set reports the export shape, not the true `google-apps.document` type
# (which is buried in `Metadata.content-type`, which the collector
# discards). The two GOOGLE_NATIVE_MIME_* checks above are kept as-is (they
# still fire correctly if a future run ever passes --drive-export-formats
# gdoc, or the true mimetype becomes available some other way); this set
# and the check below are the corroborating signal for the shape this run
# actually produces.
OFFICE_EXPORT_MIME_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # Docs -> .docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",        # Sheets -> .xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # Slides -> .pptx
}


def _is_native_google_doc(name, mime_type, size=None, provider_checksum=None):
    """Native-Doc detection by multiple corroborating signals, not filename
    extension alone.

    Part 1 review finding: ip-man's design note already flags that rclone's
    Drive backend "can synthesize export extensions on native Google Docs,
    distorting four observed names" -- and tony-jaa's collector runs with no
    --drive-export-formats/--drive-formats set, so what suffix (if any)
    v1.75.1 actually puts on a bare-named native Doc in `lsjson` output is
    exactly as unconfirmed as the shortcut-handling question he flagged.
    A `.gdoc`-suffix check alone would silently misroute a bare-named native
    Doc into generic `quarantined_invalid_name` instead of
    `native_doc_objects` if rclone's real behavior doesn't match the assumed
    suffix. `mime_type`, by contrast, comes straight from the Drive API's own
    `files.list` response (`application/vnd.google-apps.document/
    spreadsheet/presentation/...`) -- rclone doesn't synthesize or distort
    it. Checking both makes this classification robust to whatever the live
    run's actual naming turns out to be, at zero extra cost (mime_type is
    already collected on every row).

    WS3 addition (item 3): an Office-export mimetype ALONE is not a safe
    signal -- a genuinely uploaded .docx file also carries that exact
    mimetype. What makes a native Doc's export row distinguishable is that
    Drive never computed a real size or a real content checksum for it (the
    export is generated on read, not stored) -- so all three together (null
    size AND null provider checksum AND an Office-export mimetype) is the
    corroborating signal; any one alone would false-positive on an ordinary
    Word upload that happens to share the mimetype."""
    if _extension(name) == ".gdoc":
        return True
    if mime_type and mime_type.startswith(GOOGLE_NATIVE_MIME_PREFIX) and mime_type not in GOOGLE_NATIVE_MIME_EXCLUDED:
        return True
    if mime_type in OFFICE_EXPORT_MIME_TYPES and size is None and not provider_checksum:
        return True
    return False


def _has_host_field(name):
    """Detect the confirmed-doctrine OFFER `host-` typed field (design section
    7b / W1-5 / jigoro-kano's WS1 finding) without touching filename.py's
    token grammar. Scoped to OFFER names, matching where the doctrine
    confirmation actually applies."""
    if not name.startswith("OFFER-"):
        return False
    tokens = name.split("__")
    return any(t.startswith("host-") for t in tokens)


def _hash_status(obj):
    """content_sha256_status pass-through. Defaults to not_computed_dry_run
    (this planner never reads content), but preserves an explicit status
    already present on the row rather than overwriting it -- some
    pre-existing tests construct rows with a real content_sha256 already
    attached and expect it to flow through unclaimed."""
    return obj.get("content_sha256_status", "not_computed_dry_run")


def _is_collector_defect(obj):
    """Independently re-verify the collector's own tag rather than trusting
    it blindly (Part 1 review point: confirm the pre-tag actually catches the
    case). Missing/falsy drive_file_id is ALWAYS a collector defect here,
    whether or not merge_inventory.py remembered to mark it -- this keeps the
    planner from crashing on uuid5(None) if that upstream tagging ever has
    its own bug."""
    tagged = obj.get("collector_defect")
    if tagged:
        return tagged
    if not obj.get("drive_file_id"):
        return "missing_drive_file_id"
    return None


def _trashed_kind(name):
    """Coarse shape tag for a trashed board object -- 'post' (.txt),
    'sidecar' (.txt.sig), or 'other' (anything else a trashed board-folder
    object could in principle be, e.g. a native Doc export). Used only for
    routing the two required cross-checks below (rewrite-and-trash name
    intersection, sidecar-to-parent resolution); never touches DB import."""
    if name.endswith(".txt.sig"):
        return "sidecar"
    if name.endswith(".txt"):
        return "post"
    return "other"


def _full_drive_metadata(obj, name, board, is_native):
    """Full per-object Drive metadata, for classes where the row itself --
    not just a count -- IS the surviving record (WS3 item 2: Drive purges
    trash on a schedule bounded above by ~30 days from collection, so
    `trashed_board_objects` may be the only place this data still exists
    once that window closes)."""
    return {
        "drive_file_id": obj.get("drive_file_id"),
        "name": name,
        "parent_folder_path": obj.get("parent_folder_path"),
        "board": board,
        "mime_type": obj.get("mime_type"),
        "size": obj.get("size"),
        "provider_checksum": obj.get("provider_checksum"),
        "provider_checksum_algo": obj.get("provider_checksum_algo"),
        "created_time": obj.get("created_time"),
        "modified_time": obj.get("modified_time"),
        "native_doc": is_native,
    }


def plan(objects):
    rows_in = _extract_rows(objects)

    collector_defects = []
    directories_excluded = 0
    non_post_artifacts = []
    native_doc_objects = []
    grammar_b_offer_host_field = []
    legacy_nonconforming = []
    hard_rejections = []
    quarantined = []
    sidecars = []          # board-folder .txt.sig objects, kept for the
                            # existing sidecar-matching pass below
    parsed = []             # successfully parsed .txt posts, pre-post_no
    trashed_board_objects = []  # WS3 item 2: Drive-trashed objects inside a
                                 # post-bearing board folder -- excluded from
                                 # posts/artifacts, full metadata retained

    # Shortcut objects (gsp's CP1 finding): a structurally SEPARATE input
    # list from the collector, already isolated at the source from the
    # canonical `rows_in` -- never merge these into any other bucket. Still
    # re-verified for a collector defect first, same as every other row,
    # since "we don't even know the target's real ID" and "we don't know
    # this row's drive_file_id at all" are the same underlying failure mode.
    shortcut_objects = []
    for obj in _extract_shortcut_rows(objects):
        defect = _is_collector_defect(obj)
        if defect:
            collector_defects.append({"object": obj, "collector_defect": defect})
            continue
        shortcut_objects.append({
            "drive_file_id": obj.get("drive_file_id"),
            "name": obj.get("name"),
            "parent_folder_path": obj.get("parent_folder_path"),
            "board": _board_of(obj),
            "mime_type": obj.get("mime_type"),
            "reason": "shortcut_object",
            "note": obj.get("collector_note") or (
                "shortcut object; recorded drive_file_id/mime_type/size describe "
                "the shortcut's TARGET, not the shortcut itself. Never a corpus "
                "(TownSquare history) fact."
            ),
        })

    # First pass: collector-defect / directory / folder / extension routing.
    # A single left-to-right scan over rows_in, so list order below is
    # exactly the deterministic JSON-array input order (see module docstring
    # on determinism).
    for obj in rows_in:
        defect = _is_collector_defect(obj)
        if defect:
            collector_defects.append({"object": obj, "collector_defect": defect})
            continue
        if obj.get("is_dir"):
            directories_excluded += 1
            continue

        name = obj.get("name") or (obj.get("path", "").rsplit("/", 1)[-1])
        folder_status = _board_folder_status(obj)
        board = _board_of(obj)
        trashed = bool(obj.get("trashed"))
        is_native = _is_native_google_doc(name, obj.get("mime_type"), obj.get("size"), obj.get("provider_checksum"))
        if folder_status == "non_board":
            non_post_artifacts.append({
                "drive_file_id": obj.get("drive_file_id"),
                "name": name,
                "parent_folder_path": obj.get("parent_folder_path"),
                "board": board,
                "native_doc": is_native,
                "trashed": trashed,
                "reason": "non_post_artifact",
                "note": (
                    "outside every recognized post-bearing folder "
                    f"({sorted(POST_BOARD_FOLDERS)}); a standing/administrative "
                    "document (doctrine, protocol, register, ...), never a "
                    "corpus exception"
                ),
            })
            continue

        # WS3 item 2 (trashed policy) -- checked BEFORE sidecar/native-doc/
        # .md/host-field/parse routing, so ANY trashed object inside a
        # post-bearing board folder is diverted here regardless of shape.
        # This is what makes items 2 and 3 (native-Doc detection) compose
        # correctly when they intersect on the same real object: native-doc-
        # ness is still computed above (`is_native`) and carried as a
        # cross-cutting tag on this row, but ROUTING is decided by trashed-
        # ness first -- a trashed native Doc is classified once, here, never
        # also appended to `native_doc_objects` (no double count, and it
        # can't fall between the two since there is only one branch it can
        # take). `posts`/`artifacts` never see this row.
        if trashed:
            trashed_board_objects.append({
                **_full_drive_metadata(obj, name, board, is_native),
                "kind": _trashed_kind(name),
                "reason": "trashed_board_object",
                "note": (
                    "Drive-trashed object inside a post-bearing board folder; "
                    "excluded from posts/artifacts per the operator's confirmed "
                    "2026-09-22 disposition ('record, don't register'). Drive's "
                    "purge schedule for this object is UNKNOWN, bounded above by "
                    "~30 days from collection (the exact date depends on this "
                    "object's own trash time, which lsjson does not report) -- "
                    "this row's full metadata may be the only surviving record "
                    "after that window closes. Never silently imported."
                ),
            })
            continue

        if name.endswith(".txt.sig"):
            sidecars.append(obj)
            continue

        ext = _extension(name)
        if is_native:
            native_doc_objects.append({
                "drive_file_id": obj.get("drive_file_id"),
                "name": name,
                "mime_type": obj.get("mime_type"),
                "parent_folder_path": obj.get("parent_folder_path"),
                "board": board,
                "reason": "native_google_doc",
                "content_sha256": None,
                "content_sha256_status": "native_google_doc",
                "reissued_as_txt": False,
            })
            continue
        if ext == ".md":
            legacy_nonconforming.append({
                "drive_file_id": obj.get("drive_file_id"),
                "name": name,
                "parent_folder_path": obj.get("parent_folder_path"),
                "board": board,
                "reason": "legacy_nonconforming",
                "note": "grammar-B standalone .md post shape; classified only, parser not extended",
            })
            continue

        if _has_host_field(name):
            grammar_b_offer_host_field.append({
                "drive_file_id": obj.get("drive_file_id"),
                "name": name,
                "parent_folder_path": obj.get("parent_folder_path"),
                "board": board,
                "reason": "grammar_b_offer_host_field",
                "note": (
                    "OFFER host- typed field, confirmed doctrine per section 7b "
                    "(jigoro-kano's WS1 finding); classified only, parser not extended"
                ),
            })
            continue

        try:
            meta = parse_filename(name)
        except (FilenameError, KeyError) as exc:
            message = str(exc)
            if message in HARD_ERROR_MESSAGES:
                hard_rejections.append({
                    "object": obj,
                    "reason": message,
                    "class": "hard_rejection",
                    "note": "loud parser rejection (mode/pid validation); quarantined separately from generic invalid-name corruption",
                })
            else:
                quarantined.append({"object": obj, "warning": message})
            continue

        responsible = meta.get("by") or meta.get("to")
        warnings = [] if responsible else ["unresolved_responsibility"]
        silent_fields = [k for k in SILENT_ABSORPTION_KEYS if meta.get(k) is not None]
        parsed.append({
            **obj,
            "parsed": meta,
            "post_uid": str(uuid.uuid5(IMPORT_NAMESPACE, obj["drive_file_id"])),
            "responsible_agent": responsible,
            "warnings": warnings,
            "silent_absorption_fields": silent_fields,
            # WS3 item 4: explicit key AFTER the **obj spread, so it always
            # wins over any stray "board" the input happened to carry, and
            # so line ~526's rows.append below receives a real value derived
            # from parent_folder_path instead of relying on a key the
            # collector never emits (see _board_of's docstring).
            "board": board,
        })

    # Silent-absorption class: counted separately, not removed from `parsed`
    # (the parse succeeded; the risk is that its data may be wrong -- see
    # module docstring point 5).
    silent_typed_field_absorption = []
    for item in parsed:
        for key in item["silent_absorption_fields"]:
            silent_typed_field_absorption.append({
                "thread_id": item["parsed"]["thread"],
                "drive_file_id": item["drive_file_id"],
                "filename": item["parsed"]["filename"],
                "field": key,
                "value": item["parsed"][key],
                "note": (
                    f"'{key}' is a legitimate typed field in the design's own list; "
                    "the parser cannot distinguish correct use from a slug that "
                    "coincidentally starts with the same prefix. Counted for human "
                    "review, not assumed wrong."
                ),
            })

    # Ambiguous un-namespaced aliases: a bare (namespace=None) thread sharing
    # (prefix, date, local_number) with at least one namespaced thread. Two
    # DIFFERENT namespaces with no bare variant at all is normal and expected
    # under the design's per-namespace uniqueness scoping (section 5) -- not
    # ambiguous, so not flagged. This condition is an interpretive call (the
    # design/WS1 note name the class but do not spell out the exact test);
    # flagged here for gsp/ronda-rousey to challenge if they read it
    # differently.
    namespace_groups = defaultdict(list)
    for item in parsed:
        key = (item["parsed"]["prefix"], item["parsed"]["date"], item["parsed"]["local_number"])
        namespace_groups[key].append(item)
    ambiguous_unnamespaced_aliases = []
    for key in sorted(namespace_groups):
        group = namespace_groups[key]
        namespaces = {g["parsed"]["namespace"] for g in group}
        if None in namespaces and len(namespaces) > 1:
            for g in sorted(group, key=lambda x: (x["parsed"]["namespace"] or "", x["drive_file_id"])):
                ambiguous_unnamespaced_aliases.append({
                    "prefix": key[0],
                    "date": key[1],
                    "local_number": key[2],
                    "thread_id": g["parsed"]["thread"],
                    "namespace": g["parsed"]["namespace"],
                    "drive_file_id": g["drive_file_id"],
                    "filename": g["parsed"]["filename"],
                })

    # Group by full thread string (existing behavior, unchanged) and assign
    # post_no, splitting seq==0 collisions (duplicate_openings) from every
    # other seq collision (duplicate_sequences) -- R7/the work order's "never
    # merged" instruction. `collisions` is kept as a deprecated superset
    # alias for the pre-existing test.
    groups = defaultdict(list)
    for item in parsed:
        groups[item["parsed"]["thread"]].append(item)

    rows = []
    duplicate_openings = []
    duplicate_sequences = []
    board_fallback_fired = []  # WS3 item 4: LOUD record of every time the
                                # 'legacy' fallback below actually fires,
                                # instead of the silent default it used to be
                                # (posts.board is NOT NULL; a silent default
                                # here is the same fail-open shape flagged
                                # elsewhere in this project).
    for thread, items in sorted(groups.items()):
        counts = Counter(x["parsed"]["seq"] for x in items)
        maximum = max(counts, default=-1)
        extra = maximum + 1
        items.sort(key=lambda x: (x["parsed"]["seq"], x.get("header_at") or "", x.get("created_time") or "", x["drive_file_id"]))
        used = set()
        for item in items:
            seq = item["parsed"]["seq"]
            if counts[seq] == 1 and seq not in used:
                post_no = seq
            else:
                post_no = extra
                extra += 1
                entry = {"thread_id": thread, "legacy_seq": seq, "drive_file_id": item["drive_file_id"], "assigned_post_no": post_no}
                (duplicate_openings if seq == 0 else duplicate_sequences).append(entry)
            used.add(post_no)
            board = item.get("board")
            if board is None:
                # Only reachable today via the "unknown" folder-status path
                # (pre-collector-schema fixtures with no parent_folder_path
                # key at all -- see _board_folder_status). Every real
                # collector row now carries a derived board from item 4's
                # fix, so this branch firing on live data is itself a signal
                # something upstream regressed -- hence it is recorded, not
                # just silently patched over.
                board = "legacy"
                board_fallback_fired.append({
                    "thread_id": thread,
                    "drive_file_id": item["drive_file_id"],
                    "filename": item["parsed"]["filename"],
                    "note": "no board could be derived from parent_folder_path; defaulted to 'legacy'",
                })
            rows.append({
                "thread_id": thread,
                "post_uid": item["post_uid"],
                "post_no": post_no,
                "legacy_seq": seq,
                "drive_file_id": item["drive_file_id"],
                "filename": item["parsed"]["filename"],
                "content_sha256": item.get("content_sha256"),
                "content_sha256_status": _hash_status(item),
                "header_at": item.get("header_at"),
                "board": board,
                "responsible_agent": item["responsible_agent"],
                "warnings": item["warnings"],
                # WS3 item 5: Drive's own createdTime, passed through so
                # migration 009's posts.drive_created_at can be populated at
                # promotion -- the only moment this value is in hand (posts
                # are immutable after import). Optional/nullable end to end;
                # never validated or required by stage_import.
                "created_time": item.get("created_time"),
            })
    collisions = duplicate_openings + duplicate_sequences  # deprecated superset alias

    # WS3 item 2's two required cross-checks (jigoro-kano's Q2 review),
    # computed now that `rows` (the surviving, importable posts) is final.
    #
    # (a) Rewrite-and-trash candidates: exact-filename intersection between
    #     a trashed post and the ACTIVE, importable post set. Doctrine
    #     section 1's REWRITE-AND-TRASH prohibition is about the SAME
    #     logical post being deleted and silently replaced -- an exact
    #     filename match (same thread, same seq, same state, same slug) is
    #     the strongest, least-ambiguous signal of that, and a materially
    #     more serious finding than an ordinary trashed post: it means an
    #     object with that identity exists TWICE in Drive's history, once
    #     trashed and once live.
    trashed_post_names = {t["name"] for t in trashed_board_objects if t["kind"] == "post"}
    active_post_filenames = {row["filename"]: row["drive_file_id"] for row in rows}
    trashed_rewrite_and_trash_candidates = []
    for t in trashed_board_objects:
        if t["kind"] == "post" and t["name"] in active_post_filenames:
            trashed_rewrite_and_trash_candidates.append({
                "filename": t["name"],
                "trashed_drive_file_id": t["drive_file_id"],
                "active_drive_file_id": active_post_filenames[t["name"]],
                "reason": "rewrite_and_trash_candidate",
                "note": (
                    "identical filename observed both trashed and active in "
                    "the same collection pass -- candidate doctrine section 1 "
                    "REWRITE-AND-TRASH violation, materially different from an "
                    "ordinary trashed post. Not auto-adjudicated; for Sensei's "
                    "disposition decision."
                ),
            })

    # (b) Sidecar-to-parent resolution for the trashed .txt.sig objects.
    #     Two OPPOSITE classes, per jigoro-kano's review -- must not be
    #     collapsed into one number:
    #       - orphan_sidecar: the parent post is ALSO trashed (or missing
    #         entirely) -- the signature has no live post to attest to.
    #       - live_post_lost_signature: the parent post is STILL ACTIVE --
    #         the signature vanished out from under a live post. This is the
    #         more serious of the two and must never be silently folded into
    #         "orphan".
    trashed_sidecar_resolution = []
    for t in trashed_board_objects:
        if t["kind"] != "sidecar":
            continue
        parent_name = t["name"][:-4]  # strip ".sig", keep ".txt"
        if parent_name in active_post_filenames:
            classification, parent_status = "live_post_lost_signature", "active"
        elif parent_name in trashed_post_names:
            classification, parent_status = "orphan_sidecar", "trashed"
        else:
            classification, parent_status = "orphan_sidecar", "missing"
        trashed_sidecar_resolution.append({
            "filename": t["name"],
            "drive_file_id": t["drive_file_id"],
            "parent_filename": parent_name,
            "parent_status": parent_status,
            "classification": classification,
        })

    # Sidecar matching (board-folder .txt.sig only -- non-board .sig objects
    # were already routed to non_post_artifacts above). Original shape
    # preserved exactly for registrar/app/service.py's stage_import.
    by_name = defaultdict(list)
    for row in rows:
        by_name[row["filename"]].append(row)
    sidecar_parent_counts = Counter()
    for obj in sidecars:
        filename = obj.get("name") or obj.get("path", "").split("/")[-1]
        sidecar_parent_counts[filename[:-4]] += 1  # strip ".sig", keep ".txt"

    artifacts = []
    orphan_sidecars = []
    ambiguous_sidecar_parents = []
    for obj in sidecars:
        filename = obj.get("name") or obj.get("path", "").split("/")[-1]
        parent_name = filename[:-4]
        matches = by_name.get(parent_name, [])
        warnings = []
        if not matches:
            warnings = ["orphan_signature"]
        elif len(matches) > 1 or sidecar_parent_counts[parent_name] > 1:
            warnings = ["ambiguous_signature_parent"]
        parent_post_uid = matches[0]["post_uid"] if len(matches) == 1 and sidecar_parent_counts[parent_name] == 1 else None
        artifact = {
            "drive_file_id": obj["drive_file_id"],
            "filename": filename,
            "kind": "signature",
            "parent_post_uid": parent_post_uid,
            "content_sha256": obj.get("content_sha256"),
            "content_sha256_status": _hash_status(obj),
            "warnings": warnings,
        }
        artifacts.append(artifact)
        if "orphan_signature" in warnings:
            orphan_sidecars.append({"drive_file_id": obj["drive_file_id"], "filename": filename, "reason": "orphan_signature"})
        if "ambiguous_signature_parent" in warnings:
            ambiguous_sidecar_parents.append({
                "drive_file_id": obj["drive_file_id"],
                "filename": filename,
                "candidate_post_uids": [m["post_uid"] for m in matches],
                "reason": "ambiguous_signature_parent",
            })

    # Unsigned posts: a class, not an error (ip-man's design note). A post
    # row with zero matching board-folder sidecars, regardless of ambiguity.
    unsigned_posts = []
    for row in rows:
        if sidecar_parent_counts.get(row["filename"], 0) == 0:
            unsigned_posts.append({
                "thread_id": row["thread_id"],
                "post_uid": row["post_uid"],
                "drive_file_id": row["drive_file_id"],
                "filename": row["filename"],
            })

    # next_post_no per root/thread: max assigned post_no in that thread + 1.
    # Order-independent (max), so no determinism concern here even though the
    # dict itself is built via a plain loop -- json.dumps(sort_keys=True)
    # normalizes dict key order regardless.
    next_post_no = {}
    for row in rows:
        candidate = row["post_no"] + 1
        thread_id = row["thread_id"]
        if thread_id not in next_post_no or candidate > next_post_no[thread_id]:
            next_post_no[thread_id] = candidate

    trashed_sidecar_orphan_count = sum(1 for r in trashed_sidecar_resolution if r["classification"] == "orphan_sidecar")
    trashed_sidecar_live_post_lost_signature_count = sum(1 for r in trashed_sidecar_resolution if r["classification"] == "live_post_lost_signature")

    counts = {
        "posts": len(rows),
        "artifacts_signature": len(artifacts),
        "duplicate_openings": len(duplicate_openings),
        "duplicate_sequences": len(duplicate_sequences),
        "ambiguous_unnamespaced_aliases": len(ambiguous_unnamespaced_aliases),
        "orphan_sidecars": len(orphan_sidecars),
        "ambiguous_sidecar_parents": len(ambiguous_sidecar_parents),
        "unsigned_posts": len(unsigned_posts),
        "non_post_artifacts": len(non_post_artifacts),
        "grammar_b_offer_host_field": len(grammar_b_offer_host_field),
        "legacy_nonconforming": len(legacy_nonconforming),
        "silent_typed_field_absorption": len(silent_typed_field_absorption),
        "hard_rejections": len(hard_rejections),
        "quarantined_invalid_name": len(quarantined),
        "native_doc_objects": len(native_doc_objects),
        "collector_defects": len(collector_defects),
        "directories_excluded": directories_excluded,
        "shortcut_objects": len(shortcut_objects),
        "trashed_board_objects": len(trashed_board_objects),
        "trashed_rewrite_and_trash_candidates": len(trashed_rewrite_and_trash_candidates),
        "trashed_sidecar_orphan": trashed_sidecar_orphan_count,
        "trashed_sidecar_live_post_lost_signature": trashed_sidecar_live_post_lost_signature_count,
        "board_fallback_fired": len(board_fallback_fired),
    }

    return {
        "dry_run": True,
        "planner_schema_version": 1,
        "deferred": list(DEFERRED_DESIGN_STEPS),
        "known_defects_recorded_not_fixed": KNOWN_DEFECTS_RECORDED_NOT_FIXED,
        "objects": len(rows_in),
        "counts": counts,
        "posts": rows,
        "artifacts": artifacts,
        "collisions": collisions,  # deprecated superset alias; see module docstring
        "duplicate_openings": duplicate_openings,
        "duplicate_sequences": duplicate_sequences,
        "ambiguous_unnamespaced_aliases": ambiguous_unnamespaced_aliases,
        "orphan_sidecars": orphan_sidecars,
        "ambiguous_sidecar_parents": ambiguous_sidecar_parents,
        "unsigned_posts": unsigned_posts,
        "non_post_artifacts": non_post_artifacts,
        "grammar_b_offer_host_field": grammar_b_offer_host_field,
        "legacy_nonconforming": legacy_nonconforming,
        "silent_typed_field_absorption": silent_typed_field_absorption,
        "hard_rejections": hard_rejections,
        "quarantined": quarantined,
        "native_doc_objects": native_doc_objects,
        "collector_defects": collector_defects,
        "shortcut_objects": shortcut_objects,
        "trashed_board_objects": trashed_board_objects,
        "trashed_rewrite_and_trash_candidates": trashed_rewrite_and_trash_candidates,
        "trashed_sidecar_resolution": trashed_sidecar_resolution,
        "board_fallback_fired": board_fallback_fired,
        "next_post_no": next_post_no,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inventory")
    ap.add_argument("--output")
    args = ap.parse_args()
    # gsp's nit (CP1 review, 2026-09-21): both handles opened via `with`
    # rather than a bare open(...).write(...)/open(...).read() -- the latter
    # relies on CPython's refcounting GC to close the file promptly, which is
    # not a language guarantee and can leave output truncated/unflushed on a
    # non-refcounting interpreter (or simply delayed under any GC pause).
    with open(args.inventory, "r", encoding="utf-8") as f:
        inventory = json.load(f)
    report = plan(inventory)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
