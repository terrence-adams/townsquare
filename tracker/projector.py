"""TownSquare project tracker: a read-only Epic/Feature/Story projection.

Reads a TownSquare board -- <root>/Requests, Seeking, Wanted and Bulletin Board,
plus everything under <root>/Archive at any depth -- and builds the project ->
epic -> feature -> story view of docs/townsquare-project-tracker-design.md (v1)
as amended by docs/townsquare-project-tracker-design-v2.md (v2), under nesting
option (b): levels stay ordered, and parent: is optional at every level.

READ-ONLY. It never writes to the board and never calls the Crier or the
Registrar. Standard library only. Filenames go through the canonical
registrar.app.filename.parse_filename and nothing else -- including thread ids
quoted inside header values (see _thread_ids). There is no second grammar.

OUTPUT CONTRACT (v2 s2, A5; D41). The groupings here are a NON-MONOTONE view of
current state. They read newest-wins header fields, so an item moves on purpose:
a scoped ask leaves intake, and a re-parented Story moves between Features.
Nothing may use them for routing, notification or receipt, or for a Vertical
entry that does not pin the event ids it read (each node's current_event).
Every result carries the same statement machine-readably, as
result["output_contract"], so a consumer can check it instead of trusting it.

Header rules (v2 A5). Tracker fields are read only from a header block that
ends at a line that is exactly "---". Keys start at column 0 and match
case-insensitively. An indented line is a continuation and is never read. A
tracker key that appears twice in one header is flagged for that event and
ignored: the newest event that carries the field cleanly wins (G3), so an
earlier clean value stands. An empty value ("parent:" with nothing after it)
does not carry the field. Last activity is the event file's mtime, standing in
for Drive createdTime: events are never modified, and at: is display-only.

Choices the design does not pin. These are this module's own, open to review, not rulings:
  - Rollup counts are over direct children. Last activity is transitive over
    the descendant tree (tracker/tests/test_rollup_status.py pins both).
  - An "open" child is any child that is not CLOSED or CANCELLED.
  - Story readiness is reported only while the Story is not CLOSED or
    CANCELLED. The DoR is a scoping checklist, so a finished Story's readiness
    is moot, and a permanent flag would decay into noise.
  - A collided parent (two different .000 opens under one id) is ambiguous. The
    child is reported and shown at top level, not guessed under either open.
  - Top-level items without project: go in result["no_project"], and
    level: unscoped roots go in result["intake"]. Nothing is dropped silently.
  - Archive/ is read at any depth. TSD v1.5 s8 files archived threads under
    Archive/<YYYY-Qn>/, and the tests use Archive/<board>/.

Run from the repo root:  python -m tracker.projector "<board root>" [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path

if not __package__:  # run as a script: make the repo root importable, as crier.py does
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registrar.app.filename import FilenameError, parse_filename

LIVE_BOARDS = ("Requests", "Seeking", "Wanted", "Bulletin Board")
ARCHIVE = "Archive"

TRACKER_KEYS = ("level", "parent", "project", "repo", "next")
# D19 fields this projection also needs. They are read under the same A5 rules,
# but they are outside the tracker-key duplicate flag, which A5 scopes to tracker keys.
AUX_KEYS = ("acceptance", "for", "references")

# The level a parent: must name, one level up (option b). None: no parent at all.
PARENT_LEVEL = {"unscoped": None, "epic": None, "feature": "epic", "story": "feature"}
TERMINAL = ("CLOSED", "CANCELLED")

FLAGS = (  # v1 s6's ten, in its order, then the three this module adds
    "nesting_violation", "parent_not_found", "parent_collided", "cycle",
    "open_child_under_closed_parent", "closed_parent_with_open_children",
    "level_on_non_request", "project_restated_conflict", "unreadable_header",
    "story_not_ready",
    "duplicate_header_key",  # v2 A5: "flagged for that event"
    "invalid_level",         # level: set to something that is not a level
    "thread_collided",       # a tracker item whose id has two different opens (D23)
)

OUTPUT_CONTRACT = {
    "non_monotone_view": True,
    "must_not_be_used_for": ["routing", "notification", "receipt",
                             "vertical_entry_without_pinned_event_ids"],
    "statement": ("A current-state view built from newest-wins header fields. Its groupings "
                  "move on purpose and are not monotone relevance buckets (D44). Do not use "
                  "them for routing, notification or receipt, or for a Vertical entry that "
                  "does not pin the event ids it read (current_event)."),
}


# ------------------------------------------------------------------ headers
def _header_lines(text: str) -> list[str] | None:
    """The lines above the first line that is exactly '---'. None if there is no such line."""
    lines = text.splitlines()
    return lines[:lines.index("---")] if "---" in lines else None


def _single_valued(lines: list[str], keys: tuple[str, ...]) -> tuple[dict, list]:
    """Each of `keys` that appears exactly once, and each that appears more than once."""
    seen: dict[str, list[str]] = {}
    for line in lines:
        if not line or line[0].isspace() or ":" not in line:
            continue  # blank, a continuation, or not a key line
        key, value = line.split(":", 1)
        key = key.strip().lower()
        if key in keys:
            seen.setdefault(key, []).append(value.strip())
    once = {k: v[0] for k, v in seen.items() if len(v) == 1}
    return once, [k for k in keys if len(seen.get(k, ())) > 1]


def _parse_header(text: str) -> tuple[dict, dict]:
    lines = _header_lines(text)
    if lines is None:
        return {"has_header": False, "fields": {}, "duplicate_fields": []}, {}
    fields, duplicates = _single_valued(lines, TRACKER_KEYS)
    aux, _ = _single_valued(lines, AUX_KEYS)
    return {"has_header": True, "fields": fields, "duplicate_fields": duplicates}, aux


def parse_tracker_header(text: str) -> dict:
    """The five tracker fields in `text`'s header block, under v2 A5's rules.
    Returns {"has_header", "fields", "duplicate_fields"}. Does no I/O."""
    return _parse_header(text)[0]


def _read(path) -> str:
    # utf-8-sig: a BOM left by an editor must not hide the first key or the "---" line.
    return Path(path).read_text(encoding="utf-8-sig", errors="replace")


def read_event_header(path) -> dict:
    """parse_tracker_header over a file, plus "readable". Never raises: an
    OSError gives readable False and no fields."""
    try:
        text = _read(path)
    except OSError:
        return {"readable": False, "has_header": False, "fields": {}, "duplicate_fields": []}
    return {"readable": True, **parse_tracker_header(text)}


def _thread_ids(value: str) -> list[tuple[str, str]]:
    """(thread id, prefix) for each id a free-text value names. A value looks like
    "TS-20260101-venom-004.002 (evidence); BB-... (mention)". Each token is
    completed into the smallest valid filename (as a thread id, then as an event id)
    and run through parse_filename, so these ids follow the one canonical grammar."""
    found: list[tuple[str, str]] = []
    for token in re.split(r"[\s,;()]+", value):
        for completion in (".000-OPEN.txt", "-OPEN.txt"):
            try:
                parsed = parse_filename(token + completion)
            except FilenameError:
                continue
            if (parsed["thread"], parsed["prefix"]) not in found:
                found.append((parsed["thread"], parsed["prefix"]))
            break
    return found


# ------------------------------------------------------------------ the board
def _raise(exc: OSError) -> None:
    raise exc


def _event(path: Path, rel: str, parsed: dict) -> dict:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = None
    ev = {"thread": parsed["thread"], "prefix": parsed["prefix"], "seq": parsed["seq"],
          "state": parsed["state"], "filename": parsed["filename"], "slug": parsed["slug"],
          "for_token": parsed.get("for"), "path": rel, "mtime": mtime,
          "error": None, "fields": {}, "duplicate_fields": [], "aux": {}}
    try:
        text = _read(path)
    except OSError as exc:
        ev["error"] = f"{type(exc).__name__}: {exc.strerror or exc}"
        return ev
    header, ev["aux"] = _parse_header(text)
    ev["fields"], ev["duplicate_fields"] = header["fields"], header["duplicate_fields"]
    return ev


def _scan(root: Path) -> tuple[list[dict], list[dict]]:
    """Every event on the board, and every live-board .txt the canonical parser rejects.
    Archive/ also holds superseded documents (TSD s1a), so its misses are not reported."""
    events: list[dict] = []
    unparseable: list[dict] = []

    def consider(path: Path, rel: str, report: bool) -> bool:
        try:
            parsed = parse_filename(path.name, rel)
        except FilenameError as exc:
            if report and path.name.endswith(".txt"):
                unparseable.append({"path": rel, "error": str(exc)})
            return False
        events.append(_event(path, rel, parsed))  # a directory here becomes an unreadable event
        return True

    for board in LIVE_BOARDS:
        folder = root / board
        if folder.is_dir():
            for path in sorted(folder.iterdir()):
                consider(path, f"{board}/{path.name}", report=True)
    archive = root / ARCHIVE
    if archive.is_dir():
        for dirpath, dirnames, filenames in os.walk(archive, onerror=_raise):
            here = Path(dirpath)
            rel = here.relative_to(root).as_posix()
            # a directory named like an event is that event, unreadable: never descend into it
            dirnames[:] = [d for d in sorted(dirnames) if not consider(here / d, f"{rel}/{d}", False)]
            for name in sorted(filenames):
                consider(here / name, f"{rel}/{name}", report=False)
    return events, unparseable


def _threads(events: list[dict]) -> dict[str, dict]:
    """Collapse events into threads. THE NEWEST EVENT WINS, and the Crier's
    (sequence, time) tie-break decides a duplicated sequence. A field comes
    from the newest event that carries it (G3)."""
    grouped: dict[str, list[dict]] = {}
    for ev in events:
        grouped.setdefault(ev["thread"], []).append(ev)
    threads = {}
    for tid, evs in sorted(grouped.items()):
        evs.sort(key=lambda e: (e["seq"], float("-inf") if e["mtime"] is None else e["mtime"],
                                e["filename"], e["path"]))
        newest = evs[-1]

        def latest(get):
            return next((v for v in map(get, reversed(evs)) if v), None)

        openings: dict[str, str] = {}
        for e in evs:
            if e["seq"] == 0:
                openings.setdefault(e["filename"], e["path"])  # one file seen twice is not two opens
        threads[tid] = {
            "id": tid, "prefix": newest["prefix"], "events": evs, "state": newest["state"],
            "time": newest["mtime"], "current_event": f"{tid}.{newest['seq']:03d}",
            "subject": evs[0]["slug"], "openings": sorted(openings.values()),
            **{key: latest(lambda e, key=key: e["fields"].get(key)) for key in TRACKER_KEYS},
            "acceptance": latest(lambda e: e["aux"].get("acceptance")),
            "for": latest(lambda e: e["aux"].get("for") or e["for_token"]),
        }
    return threads


def _iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _claimed_by(t: dict) -> str | None:
    """v2 K4: the claimer's CLOSED event on a SEEK names its new Request in references:.
    That event may also cite the Story the SEEK serves, which is never the claim."""
    if t["prefix"] != "SEEK" or t["state"] != "CLOSED":
        return None
    refs = t["events"][-1]["aux"].get("references") or ""
    return next((tid for tid, prefix in _thread_ids(refs)
                 if prefix == "TS" and tid != t["parent"]), None)


# ------------------------------------------------------------------ projection
def build_projection(root) -> dict:
    """The projection of the board at `root`. See the module docstring for its contract."""
    root = Path(root)
    if not root.is_dir():
        raise NotADirectoryError(f"not a TownSquare board root: {root}")
    events, unparseable = _scan(root)
    threads = _threads(events)
    flags: list[dict] = []

    def flag(name: str, thread: str, **detail) -> None:
        flags.append({"flag": name, "thread": thread, "detail": detail})

    for ev in events:
        if ev["error"]:
            flag("unreadable_header", ev["thread"], path=ev["path"], error=ev["error"])
        if ev["duplicate_fields"]:
            flag("duplicate_header_key", ev["thread"], path=ev["path"], fields=ev["duplicate_fields"])

    nodes: dict[str, dict] = {}
    for tid, t in threads.items():
        if not t["level"]:
            continue
        if t["prefix"] != "TS":
            flag("level_on_non_request", tid, level=t["level"])  # never promoted into the tree
            continue
        level = t["level"].lower()
        if level not in PARENT_LEVEL:
            flag("invalid_level", tid, level=t["level"])
            continue
        if len(t["openings"]) > 1:
            flag("thread_collided", tid, openings=t["openings"])
        nodes[tid] = {"id": tid, "level": level, "state": t["state"], "parent": t["parent"],
                      "project": None, "repo": None, "next": t["next"], "subject": t["subject"],
                      "current_event": t["current_event"], "children": [], "attachments": [],
                      "rollup": {}}

    def resolve(tid: str, parent: str) -> bool:
        """True if `parent` is a tracker item to place under. Otherwise flags why not."""
        if parent in threads and len(threads[parent]["openings"]) > 1:
            flag("parent_collided", tid, parent=parent)
        elif parent not in nodes:
            flag("parent_not_found", tid, parent=parent, thread_exists=parent in threads)
        else:
            return True
        return False

    resolved: dict[str, str] = {}  # child -> the tracker item its parent: names
    for tid, node in nodes.items():
        parent = node["parent"]
        if not parent:
            continue
        expected = PARENT_LEVEL[node["level"]]
        actual = None
        if resolve(tid, parent):
            resolved[tid] = parent
            actual = nodes[parent]["level"]
        # decidable only against a resolved parent, except that epic and unscoped take none at all
        if expected is None or (tid in resolved and actual != expected):
            flag("nesting_violation", tid, parent=parent, expected_level=expected, actual_level=actual)

    # A cycle has no top-level ancestor, so its members are cut loose and shown at top level.
    on_cycle: set[str] = set()
    done: set[str] = set()
    for start in sorted(resolved):
        path: list[str] = []
        cur = start
        while cur in resolved and cur not in done and cur not in path:
            path.append(cur)
            cur = resolved[cur]
        if cur in path:
            cycle = path[path.index(cur):]
            first = cycle.index(min(cycle))
            cycle = cycle[first:] + cycle[:first]
            for member in cycle:
                flag("cycle", member, cycle=cycle)
            on_cycle.update(cycle)
        done.update(path)
    edge = {child: parent for child, parent in resolved.items() if child not in on_cycle}

    children: dict[str, list[str]] = {}
    for child, parent in sorted(edge.items()):
        children.setdefault(parent, []).append(child)
    roots = [tid for tid in nodes if tid not in edge]

    # Top down: project comes from the top-level ancestor; repo from the nearest ancestor that sets it.
    order: list[str] = []
    queue = deque(roots)
    for tid in roots:
        nodes[tid]["project"], nodes[tid]["repo"] = threads[tid]["project"], threads[tid]["repo"]
    while queue:
        tid = queue.popleft()
        order.append(tid)
        node = nodes[tid]
        for child in children.get(tid, ()):
            kid, own = nodes[child], threads[child]
            kid["project"] = node["project"]
            if own["project"] and node["project"] and own["project"] != node["project"]:
                flag("project_restated_conflict", child, inherited=node["project"], restated=own["project"])
            kid["repo"] = own["repo"] or node["repo"]
            node["children"].append(kid)
            queue.append(child)

    # Bottom up: counts over direct children; last activity over the whole subtree.
    newest: dict[str, float | None] = {}
    for tid in reversed(order):
        node, kids = nodes[tid], nodes[tid]["children"]
        times = [x for x in [threads[tid]["time"], *(newest[k["id"]] for k in kids)] if x is not None]
        newest[tid] = max(times, default=None)
        node["rollup"] = {
            "child_state_counts": dict(sorted(Counter(k["state"] for k in kids).items())),
            "blocked_children": [k["id"] for k in kids if k["state"] == "BLOCKED"],
            "awaiting_closure_children": [k["id"] for k in kids if k["state"] == "RESOLVED"],
            "last_activity": _iso(newest[tid]),
        }
        open_kids = [k["id"] for k in kids if k["state"] not in TERMINAL]
        if open_kids and node["state"] in ("CLOSED", "CANCELLED"):
            for kid in open_kids:
                flag("open_child_under_closed_parent", kid, parent=tid, parent_state=node["state"])
        if open_kids and node["state"] in ("RESOLVED", "CLOSED"):
            flag("closed_parent_with_open_children", tid, parent_state=node["state"],
                 open_children=open_kids)

    # DoR lines 1-3 (v2 A2 wording): if it has a parent, the parent is a Feature;
    # acceptance: yes; a lane in for:. v2 A3 makes line 4 (Sensei's confirmation)
    # checkable too, but no test pins it yet, so it is not checked here.
    for tid, node in nodes.items():
        if node["level"] != "story" or node["state"] in TERMINAL:
            continue
        reasons = []
        if node["parent"] and not (tid in resolved and nodes[resolved[tid]]["level"] == "feature"):
            reasons.append("parent_not_feature")
        if not re.match(r"yes\b", threads[tid]["acceptance"] or "", re.I):
            reasons.append("no_acceptance")
        if not threads[tid]["for"]:
            reasons.append("no_for")
        if reasons:
            flag("story_not_ready", tid, reasons=reasons)

    # Attachments: SEEK, WANT, BB and OFFER posts, and TS sub-requests with no level:,
    # that name a tracker item in parent:.
    for tid, t in threads.items():
        if tid in nodes or not t["parent"] or (t["prefix"] == "TS" and t["level"]):
            continue
        if resolve(tid, t["parent"]):
            nodes[t["parent"]]["attachments"].append(
                {"id": tid, "prefix": t["prefix"], "state": t["state"], "subject": t["subject"],
                 "claimed_by": _claimed_by(t)})

    projects: dict[str, list[dict]] = {}
    no_project: list[dict] = []
    intake: list[dict] = []
    for tid in roots:
        node = nodes[tid]
        if node["level"] == "unscoped":
            intake.append(node)
        elif node["project"]:
            projects.setdefault(node["project"], []).append(node)
        else:
            no_project.append(node)
    flags.sort(key=lambda f: (FLAGS.index(f["flag"]), f["thread"], f["detail"].get("path", "")))
    return {
        "output_contract": {**OUTPUT_CONTRACT,
                            "must_not_be_used_for": list(OUTPUT_CONTRACT["must_not_be_used_for"])},
        "projects": dict(sorted(projects.items())),
        "no_project": no_project,
        "intake": intake,
        "flags": flags,
        "unparseable_filenames": sorted(unparseable, key=lambda u: u["path"]),
    }


# ------------------------------------------------------------------ CLI
def render_text(result: dict) -> str:
    """The projection as a plain-text tree."""
    out = ["TownSquare project tracker (read-only). " + result["output_contract"]["statement"]]

    def emit(node: dict, depth: int, parent_repo: str | None) -> None:
        pad = "  " * depth
        out.append(f"{pad}{node['level']} {node['id']} {node['state']}"
                   + (f"  {node['subject']}" if node["subject"] else ""))
        roll = node["rollup"]
        info = [f"repo {node['repo']}"] if node["repo"] and node["repo"] != parent_repo else []
        if roll["child_state_counts"]:
            info.append("children " + ", ".join(f"{n} {s}" for s, n in roll["child_state_counts"].items()))
        info.append(f"last activity {roll['last_activity']}")
        out.append(f"{pad}  | " + "; ".join(info))
        if node["next"]:
            out.append(f"{pad}  | next: {node['next']}")
        for a in node["attachments"]:
            claim = f"  claimed by {a['claimed_by']}" if a["claimed_by"] else ""
            out.append(f"{pad}  + {a['id']} {a['state']}{claim}")
        for child in node["children"]:
            emit(child, depth + 1, node["repo"])

    sections = [(f"PROJECT {slug}", nodes) for slug, nodes in result["projects"].items()]
    sections += [("NO PROJECT (top-level items without project:)", result["no_project"]),
                 ("INTAKE (level: unscoped)", result["intake"])]
    for title, nodes in sections:
        if nodes:
            out += ["", title]
            for node in nodes:
                emit(node, 1, None)
    out += ["", f"FLAGS ({len(result['flags'])}) -- reports, never enforced"]
    out += [f"  {f['flag']}  {f['thread']}  {json.dumps(f['detail'], sort_keys=True)}"
            for f in result["flags"]]
    if result["unparseable_filenames"]:
        out += ["", f"UNPARSEABLE FILENAMES ({len(result['unparseable_filenames'])})"]
        out += [f"  {u['path']}: {u['error']}" for u in result["unparseable_filenames"]]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only Epic/Feature/Story view of a TownSquare board.")
    ap.add_argument("root", help=r'the board root, e.g. "G:\My Drive\N3rd0m\TownSquare"')
    ap.add_argument("--json", action="store_true", help="emit the projection as JSON")
    args = ap.parse_args(argv)
    try:
        result = build_projection(args.root)
    except OSError as exc:
        print(f"townsquare tracker: {exc}", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # a header's em dash must not kill a cp1252 pipe
    print(json.dumps(result, indent=2) if args.json else render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
