#!/usr/bin/env python3
#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
# Smoke tests for the viewer. No pytest, no browser, no Registrar: the HTTP
# layer is replaced with a canned responder, which is the only input the app
# has. Run it directly:  python test_viewer.py
#
# What this is for: every page is a script that runs top to bottom, so a typo
# in a Streamlit keyword argument is a runtime error on a page nobody opened
# until the operator opened it. AppTest executes each one headless and fails
# here instead.
import ast
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("REGISTRAR_API_TOKEN", "test.token")

from streamlit.testing.v1 import AppTest  # noqa: E402

import registrar_client  # noqa: E402

BOARDS = ("open", "requests", "decisions")
POSTS = [
    {
        "post_uid": f"post-{t:03d}-{n:03d}",
        "root_uid": f"root-{t:03d}",
        "post_no": n,
        "legacy_seq": n,
        "state": "decided",
        "board": BOARDS[(t + n) % len(BOARDS)],
        "filename": f"TS-20260901-{t:03d}#{n:03d} - note.md",
        "header_at": None,
        "created_at": f"2026-09-0{(t % 9) + 1}T0{n}:00:00Z",
        "author_agent": "ip-man" if n % 2 else None,
        "content_sha256": "0" * 64,
        "drive_file_id": f"drv{t:03d}{n:03d}",
        "drive_url": f"https://drive.google.com/file/d/drv{t:03d}{n:03d}/view",
        "registration_state": "legacy" if n else "reserved",
        "reserved_until": None,
        "source": "legacy_import",
        "drive_created_at": None,
        "thread_id": f"TS-20260901-{t:03d}",
    }
    for t in range(6)
    for n in range(4)
]


class Canned:
    """Stands in for registrar_client._get. Records every path it was asked for."""

    def __init__(self):
        self.calls = []

    def __call__(self, path, params=None):
        params = params or {}
        self.calls.append((path, dict(params)))
        if path == "/health/ready":
            return {"ok": True, "schema_version": 9}
        if path == "/health/live":
            return {"ok": True}
        if path == "/v1/posts":
            rows = POSTS
            for key, col in (
                ("state", "state"),
                ("board", "board"),
                ("registration_state", "registration_state"),
                ("root", "thread_id"),
            ):
                if params.get(key):
                    rows = [r for r in rows if r[col] == params[key]]
            if params.get("assigned_to"):
                rows = [r for r in rows if r["author_agent"] == params["assigned_to"]]
            return {"posts": rows[: int(params.get("limit", 100))]}
        if path.startswith("/v1/posts/"):
            return POSTS[0]
        if path.startswith("/v1/roots/"):
            return {
                "root_uid": "root-000",
                "thread_id": "TS-20260901-000",
                "prefix": "TS",
                "utc_date": "2026-09-01",
                "namespace": "legacy",
                "local_number": 0,
                "opening_post_uid": POSTS[0]["post_uid"],
                "next_post_no": 4,
                "status": "legacy",
                "created_by": "importer",
                "created_at": "2026-09-01T00:00:00Z",
            }
        if path.startswith("/v1/aliases/"):
            return {
                "alias": "x",
                "ambiguous": True,
                "matches": [
                    {"alias": "x", "resource_type": "post", "resource_uid": POSTS[0]["post_uid"]},
                    {"alias": "x", "resource_type": "root", "resource_uid": "root-000"},
                ],
            }
        if path.startswith("/v1/assignments/"):
            return {
                "assignments": [
                    {"post_uid": POSTS[1]["post_uid"], "agent_id": "ip-man",
                     "role": "responsible", "active": 1}
                ]
            }
        if path == "/v1/reconciliation":
            status = params.get("status")
            if status == "unresolved-responsibility":
                return {"status": status, "observations": [
                    {"import_run_id": "r1", "drive_file_id": "d1", "post_uid": POSTS[0]["post_uid"],
                     "metadata_hash": "a" * 64, "result": "warning",
                     "warnings_json": '["unresolved_responsibility"]'}]}
            if status == "artifacts":
                return {"status": status, "artifacts": [
                    {"drive_file_id": "sig1", "parent_post_uid": POSTS[0]["post_uid"],
                     "kind": "signature", "drive_url": "https://drive.google.com/file/d/sig1/view",
                     "filename": "1.sig", "content_sha256": None,
                     "verification_state": "observed"}]}
            return {"status": status, "posts": POSTS[:2]}
        raise AssertionError(f"unexpected path {path}")


def run_page(page: str) -> AppTest:
    """Run the whole app on one page, with caches cleared between tests."""
    app = AppTest.from_file(str(HERE / "streamlit_app.py"), default_timeout=30)
    app.switch_page(f"app_pages/{page}")
    app.run()
    return app


class ViewerPages(unittest.TestCase):
    def setUp(self):
        self.canned = Canned()
        self._real_get = registrar_client._get
        registrar_client._get = self.canned
        import streamlit as st

        st.cache_data.clear()

    def tearDown(self):
        registrar_client._get = self._real_get

    def assert_clean(self, app: AppTest):
        self.assertFalse(app.exception, [str(e) for e in app.exception])
        self.assertFalse(app.error, [e.value for e in app.error])

    def test_overview(self):
        app = run_page("overview.py")
        self.assert_clean(app)
        labels = {m.label: m.value for m in app.metric}
        self.assertEqual(labels["Posts"], str(len(POSTS)))
        self.assertEqual(labels["Threads"], "6")
        self.assertEqual(labels["Schema version"], "9")

    def test_posts(self):
        app = run_page("posts.py")
        self.assert_clean(app)
        self.assertEqual(len(app.dataframe[0].value), len(POSTS))

    def test_posts_filter_is_server_side(self):
        app = run_page("posts.py")
        app.selectbox(key="posts_registration_state").select("reserved").run()
        self.assert_clean(app)
        queries = [q for p, q in self.canned.calls if p == "/v1/posts"]
        self.assertTrue(queries)
        # Every list call carried a registration_state and a limit: the app
        # never asks for "everything" and narrows it in the browser.
        self.assertTrue(all(q.get("registration_state") for q in queries))
        self.assertTrue(all(q.get("limit") == registrar_client.API_MAX_LIMIT for q in queries))
        shown = app.dataframe[0].value
        self.assertEqual(len(shown), 6)
        self.assertEqual(set(shown["registration_state"]), {"reserved"})

    def test_threads(self):
        app = run_page("threads.py")
        app.text_input(key="thread_id").set_value("TS-20260901-000").run()
        self.assert_clean(app)
        self.assertEqual(len(app.dataframe[0].value), 4)

    def test_reconciliation_tabs(self):
        app = run_page("reconciliation.py")
        self.assert_clean(app)
        self.assertEqual(len(app.tabs), 4)
        # Only the open tab's query runs; the other three cost nothing.
        queried = [q.get("status") for p, q in self.canned.calls if p == "/v1/reconciliation"]
        self.assertEqual(queried, ["missing-publication"])

    def test_aliases_flags_ambiguity(self):
        app = run_page("aliases.py")
        app.text_input(key="alias").set_value("x").run()
        self.assert_clean(app)
        self.assertTrue(any("Ambiguous" in w.value for w in app.warning))

    def test_assignments(self):
        app = run_page("assignments.py")
        app.text_input(key="agent_id").set_value("ip-man").run()
        self.assert_clean(app)
        self.assertEqual({m.label for m in app.metric} & {"Assignments"}, {"Assignments"})


class Sweep(unittest.TestCase):
    """The sweep is the only non-obvious logic in the app; test it directly."""

    def setUp(self):
        self._real_get = registrar_client._get
        import streamlit as st

        st.cache_data.clear()

    def tearDown(self):
        registrar_client._get = self._real_get

    def test_unions_partitions_without_duplicates(self):
        registrar_client._get = Canned()
        rows, saturated = registrar_client.sweep_posts()
        self.assertEqual(len(rows), len(POSTS))
        self.assertEqual(len({r["post_uid"] for r in rows}), len(POSTS))
        self.assertEqual(saturated, [])

    def test_reports_saturation_it_cannot_subdivide(self):
        # Every call comes back exactly full, so no partition can ever be
        # proved complete. The app must say so rather than show 200 rows as
        # if they were all of them.
        big = [dict(POSTS[0], post_uid=f"p{i}", board="open") for i in range(400)]

        def always_full(path, params=None):
            if path == "/v1/posts":
                return {"posts": big[: registrar_client.API_MAX_LIMIT]}
            raise AssertionError(path)

        registrar_client._get = always_full
        rows, saturated = registrar_client.sweep_posts()
        self.assertEqual(len(rows), registrar_client.API_MAX_LIMIT)
        self.assertTrue(saturated)
        # Subdivision by board happened and still came back full, so the report
        # names the board, not just the registration state.
        self.assertTrue(all("board=open" in s for s in saturated))
        self.assertEqual(len(saturated), len(registrar_client.REGISTRATION_STATES))


class Readonly(unittest.TestCase):
    """The read-only guarantee should be checkable, not just intended.

    Parsed rather than grepped: prose in a docstring that *names* the write
    endpoints is exactly what this file should contain, while a call to one is
    exactly what it should not. A regex cannot tell those apart; the AST can.
    """

    WRITE_VERBS = {"post", "put", "patch", "delete", "request"}
    WRITE_PATHS = ("reserve", "publication", "import-runs", "verifications", "abandon")

    def sources(self):
        for path in sorted(HERE.glob("*.py")) + sorted((HERE / "app_pages").glob("*.py")):
            if path.name != Path(__file__).name:
                yield path, ast.parse(path.read_text(encoding="utf-8"))

    def test_no_mutating_http_call(self):
        for path, tree in self.sources():
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(
                        node.func.attr,
                        self.WRITE_VERBS,
                        f"{path.name}:{node.lineno} calls .{node.func.attr}()",
                    )

    def test_no_write_endpoint_is_ever_built(self):
        """No URL path literal in the app names a write route.

        Scoped to strings that start with `/`, which is what a path literal
        looks like and what a docstring or a widget label never does. Prose
        naming the write endpoints — as registrar_client's docstring does, on
        purpose — is not the thing being tested.
        """
        for path, tree in self.sources():
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                    continue
                if not node.value.startswith("/"):
                    continue
                for token in self.WRITE_PATHS:
                    self.assertNotIn(
                        token,
                        node.value,
                        f"{path.name}:{node.lineno} builds a path naming {token!r}",
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
