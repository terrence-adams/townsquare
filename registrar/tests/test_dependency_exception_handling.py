"""Independent verification of the FastAPI/Starlette mechanism jackie-chan's
Issue-1 ruling (docs/town-registrar-connection-concurrency.md, commit
8b1ae27) depends on, and which helio-gracie flagged as UNSUPPORTED because
her original evidence for it was an uncommitted, discarded scratch probe:

    "an app-level exception handler catches an exception raised inside a
    Depends() dependency before its `yield` ... via a bare TestClient(app)
    (no `with` block)."

Two rulings that are still open (the narrow-vs-generalized exception-handler
scope question, currently with ip-man; and by extension bruce-lee's not-yet-
started follow-up commit) are downstream of this claim being true. If it
isn't, that has to reach the coordinating session before implementation
starts, not after -- see ronda-rousey's QA report for 2026-09-22.

This file does NOT test registrar's actual `main.py`/`get_db` -- those don't
have this mechanism wired in yet (that's the pending follow-up commit this
file exists to de-risk in advance). It builds the smallest possible FastAPI
apps that reproduce the exact shape of the real scenario:

  - a `Depends()` dependency that is a generator (`yield`-based), matching
    `get_db`'s actual shape in registrar/app/main.py, raising *before*
    reaching its `yield` (mimicking `connect()` failing inside `get_db`,
    which happens before any route body runs and so can never be reached by
    `invoke()`'s existing per-call-site exception mapping);
  - registered via `@app.exception_handler(...)`, the mechanism under review;
  - exercised via a bare `TestClient(app)`, no `with` block -- this matters
    independently of ip-man's Addendum A1 (which withdrew `lifespan` from
    this change): Starlette only runs the ASGI lifespan protocol inside
    `TestClient.__enter__`, so if the exception-handler mechanism secretly
    needed lifespan to be running, that would be a second, independent
    reason it couldn't be relied on here. It doesn't -- exception handlers
    are unrelated to the lifespan protocol, and this file proves that rather
    than assuming it.

Run against this repo's actual pinned dependency versions (verified at
collection time by the `test_versions_match_pinned_requirements` test below,
not merely asserted in prose): fastapi==0.116.1 (registrar/requirements.txt),
starlette==0.47.3 (fastapi 0.116.1's resolved transitive pin).

Run pytest from the parent of registrar/ (the repo root), matching every
other file in this suite -- see the note in app_harness.py.
"""
from __future__ import annotations

import sqlite3
import unittest

import fastapi
import starlette
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient


class PinnedVersionTests(unittest.TestCase):
    """The work order requires verifying against this repo's *actual* pinned
    versions, not an assumption about what's installed. Fail loudly, rather
    than silently validating a mechanism against the wrong dependency
    versions, if the environment ever drifts from what registrar/requirements.txt
    declares."""

    def test_versions_match_pinned_requirements(self):
        self.assertEqual("0.116.1", fastapi.__version__)
        self.assertEqual("0.47.3", starlette.__version__)


class _Boom(Exception):
    """Stand-in for whatever a real `connect()` failure would raise inside
    `get_db`. Registrar doesn't have a single dedicated exception type for
    this yet -- that's part of what the still-open scope ruling covers -- a
    custom type is the right probe shape regardless of what type is
    eventually chosen."""


def _dependency_that_raises_before_yield():
    raise _Boom("connect() failed before yield")
    yield None  # pragma: no cover -- unreachable; keeps this a generator/yield dependency, matching get_db's shape


class AppLevelHandlerCatchesPreYieldDependencyExceptionTests(unittest.TestCase):
    """Part 1-3 of the work order: does an app-level handler actually catch
    an exception raised inside a Depends() dependency before its `yield`,
    reached via a bare (non-`with`) TestClient?"""

    def setUp(self):
        self.app = FastAPI()

        @self.app.exception_handler(_Boom)
        def handle_boom(request: Request, exc: _Boom):
            return JSONResponse(status_code=503, content={"detail": str(exc)})

        @self.app.get("/dep-fails")
        def route_dep(db=Depends(_dependency_that_raises_before_yield)):
            return {"unreachable": True}  # pragma: no cover -- dependency raises first

        # Control: same exception type, raised from the route body instead of
        # the dependency. Confirms the handler does real work at both sites,
        # not that it coincidentally matches one of them.
        @self.app.get("/body-fails")
        def route_body():
            raise _Boom("route body failed")

        # Matches the real app's shape more closely: get_db is a sync
        # (non-async) yield dependency, but it's `Depends()`-injected into
        # both async (`write`) and sync (`read`) routes in main.py. Prove the
        # handler reaches the exception regardless of which kind of route
        # consumes the dependency.
        @self.app.post("/dep-fails-async-route")
        async def route_dep_async(db=Depends(_dependency_that_raises_before_yield)):
            return {"unreachable": True}  # pragma: no cover

        self.client = TestClient(self.app)  # bare -- no `with` block, deliberately

    def test_dependency_raised_exception_is_caught_by_app_handler(self):
        r = self.client.get("/dep-fails")
        self.assertEqual(503, r.status_code, r.text)
        self.assertEqual("connect() failed before yield", r.json()["detail"])

    def test_route_body_raised_exception_is_also_caught_by_same_handler(self):
        r = self.client.get("/body-fails")
        self.assertEqual(503, r.status_code, r.text)
        self.assertEqual("route body failed", r.json()["detail"])

    def test_dependency_raised_exception_caught_for_async_route_too(self):
        r = self.client.post("/dep-fails-async-route")
        self.assertEqual(503, r.status_code, r.text)


class AppLevelHandlerDiscriminatesByConditionTests(unittest.TestCase):
    """Part 4 of the work order: jackie-chan's original (discarded) probe
    tested one exception type mapping to one outcome. The actual design
    question -- narrow-vs-generalized exception-handler scope -- depends on a
    handler being able to *selectively* map one error condition (e.g. only a
    "locked"/"busy" sqlite3.OperationalError) to 503 while leaving every
    other condition of the same exception type to propagate as a genuine,
    un-reclassified 500. That discrimination, not just "a handler can catch
    something," is what's under test here. Mirrors invoke()'s existing
    locked/busy string check in main.py exactly, so this is a faithful probe
    of the real discrimination logic, not a simplified stand-in for it."""

    def setUp(self):
        self.app = FastAPI()

        @self.app.exception_handler(sqlite3.OperationalError)
        def handle_operational_error(request: Request, exc: sqlite3.OperationalError):
            message = str(exc).lower()
            if "locked" in message or "busy" in message:
                return JSONResponse(status_code=503, content={"detail": str(exc)})
            raise exc  # anything else falls through to the default unhandled-exception path

        @self.app.get("/locked")
        def route_locked():
            raise sqlite3.OperationalError("database is locked")

        @self.app.get("/other")
        def route_other():
            raise sqlite3.OperationalError("no such table: posts")

        self.app_state = self.app  # kept for readability at call sites below

    def test_matching_condition_maps_to_503(self):
        client = TestClient(self.app)
        r = client.get("/locked")
        self.assertEqual(503, r.status_code, r.text)

    def test_non_matching_condition_propagates_as_unhandled_python_exception_under_strict_client(self):
        # TestClient's default (raise_server_exceptions=True) re-raises an
        # unhandled server exception into the calling test rather than
        # returning it as an HTTP response -- this is what a test asserting
        # "this must NOT be silently handled" should see.
        client = TestClient(self.app)  # default: raise_server_exceptions=True
        with self.assertRaises(sqlite3.OperationalError):
            client.get("/other")

    def test_non_matching_condition_is_a_genuine_500_not_reclassified_or_swallowed(self):
        # The other side of the same coin: what an actual deployed server's
        # caller sees is a 500 response, not a raised Python exception.
        # raise_server_exceptions=False surfaces that response instead of
        # re-raising, so this asserts the *outcome* a real client gets is an
        # honest, unhandled 500 -- not silently swallowed into a 200/503/
        # anything else.
        client = TestClient(self.app, raise_server_exceptions=False)
        r = client.get("/other")
        self.assertEqual(500, r.status_code)


if __name__ == "__main__":
    unittest.main()
