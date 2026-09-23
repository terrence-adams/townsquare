"""Deterministic regression coverage for the `sqlite3.OperationalError`
app-level exception handler registered in `registrar/app/main.py`
(`@app.exception_handler(sqlite3.OperationalError)`), closing the gap
ip-man found in Addendum C3 of
docs/town-registrar-connection-concurrency.md: no committed test asserted
the handler exists or behaves correctly against the real app. The existing
structural tripwires in `test_http_concurrency.py` cover async write
routes, module-level connections, the `connect` import, `_migrate_at_boot`,
and the `invoke()`-wrapping AST check -- nothing there touches the handler
itself. Deleting the `@app.exception_handler(...)` decorator today passes
the entire suite.

It is worse than "could be deleted unnoticed": B4's first two Done-when
criteria --

  - "No sqlite3.OperationalError with a locked/busy message ... surfaces
    as a 500"
  - "A non-locked/busy OperationalError still surfaces with its
    traceback, verified empirically, not assumed"

-- had ONLY jackie-chan's uncommitted, now-discarded scratch probes as
evidence. `test_dependency_exception_handling.py` already proved the
*general* FastAPI/Starlette mechanism (a synthetic app, a synthetic
exception type, `get_db`-shaped generator dependencies). This file is the
same shape of proof, but against the real `registrar.app.main` -- the
production handler, not a stand-in for it.

Deterministic by construction: every case raises a scripted exception from
a `dependency_overrides` entry or a monkeypatched module attribute, so the
outcome is identical on every run. No threads, no timing, no flakiness
risk -- unlike test_http_concurrency.py, this file never needs to induce
real lock contention to prove the handler works.

Built on `FreshAppCase` from `app_harness.py` (not modified here -- Addendum
A3). Every `dependency_overrides` entry and every monkeypatch is undone in
`addCleanup`, so no test in this file leaks state into another, even though
`FreshAppCase._boot()`'s fresh-import-per-test already provides a second,
independent layer of isolation (a new `main.app` object every time).

Run pytest from the parent of registrar/ (the repo root), matching every
other file in this suite -- see the note in app_harness.py.
"""
from __future__ import annotations
import sqlite3
import unittest
from fastapi.testclient import TestClient
from registrar.tests.app_harness import FreshAppCase


def _raise_before_yield(message):
    """A `Depends()` override matching `get_db`'s real shape (a generator
    that raises before its `yield`) -- mimicking `connect()` failing during
    dependency resolution, before any route body exists and before
    `invoke()`'s per-call-site mapping could ever reach it (Addendum B1)."""
    def dependency():
        raise sqlite3.OperationalError(message)
        yield None  # pragma: no cover -- unreachable; keeps this a generator dependency, matching get_db's actual shape
    return dependency


class OperationalErrorHandlerRegistrationTests(FreshAppCase):
    """Case 1: the literal tripwire for someone deleting the decorator.
    Weakest of the four cases on its own (it proves a handler exists, not
    that it behaves correctly) -- cases 2-4 below are what actually cover
    B4's Done-when bullets -- but it is the one that fails loudest and
    fastest if `@app.exception_handler(sqlite3.OperationalError)` is ever
    simply removed."""

    def test_operational_error_is_a_registered_exception_handler(self):
        main_module = self._boot()
        self.assertIn(
            sqlite3.OperationalError,
            main_module.app.exception_handlers,
            "sqlite3.OperationalError has no registered exception handler on "
            "main.app -- the @app.exception_handler(sqlite3.OperationalError) "
            "decorator in main.py appears to have been removed",
        )


class DependencySetupOriginTests(FreshAppCase):
    """Case 2: `get_db`'s `connect()` failing before `yield` -- an exception
    that originates during dependency resolution, before any route body
    exists. This is B1 condition 3's contract: the 503 body shape
    `viewer/registrar_client.py` (and every other consumer) depends on,
    previously verified only against jackie-chan's synthetic probe apps and
    never against the real `registrar.app.main`.

    `GET /health/ready` is the simplest DB-touching route -- it takes `db`
    via `Depends(get_db)` and needs no bearer token -- so this isolates the
    dependency-setup origin from the auth-path origin covered separately in
    `AuthPathOriginTests` below."""

    def setUp(self):
        self.main_module = self._boot()
        self.main_module.app.dependency_overrides[self.main_module.get_db] = _raise_before_yield("database is locked")
        self.addCleanup(self.main_module.app.dependency_overrides.clear)

    def test_locked_error_from_get_db_maps_to_503_with_exact_body(self):
        client = TestClient(self.main_module.app)  # bare -- no `with` block, deliberately; matches main.py having no lifespan handler (Addendum A1)
        r = client.get("/health/ready")
        self.assertEqual(503, r.status_code, r.text)
        self.assertEqual({"detail": "database is locked"}, r.json())


class AuthPathOriginTests(FreshAppCase):
    """Case 3: `identity()`'s call to `authenticate_identity()` raising --
    Issue 1's actual finding. `identity()`'s own `try/except` catches only
    `Forbidden`; nothing wraps its call in `invoke()` (Addendum B1's
    partition: domain exceptions map in `invoke()` at the call site that
    raises them, driver exceptions map structurally at the app boundary
    because they can originate anywhere -- `identity()` is exactly the
    auth-path proof that partition needs). This is the origin most likely
    to silently regress if someone "cleans up" `identity()` later without
    realizing `authenticate()`'s `last_used_at` UPDATE is a write on the
    read path.

    Monkeypatches `main.authenticate_identity` specifically, not
    `auth.authenticate_identity`: `main.py` imports it with
    `from .auth import authenticate_identity`, and `identity()` calls the
    bare name -- Python resolves that against `main`'s own module globals
    at call time, so rebinding the name on the `auth` module would not be
    observed here. `GET /v1/posts` is used only because it is a `post:read`
    route with no path parameters; `identity()` raises before the route
    reaches `cursor_keys()` or any `Registrar` call, so the specific route
    chosen otherwise doesn't matter."""

    def setUp(self):
        self.main_module = self._boot()
        self._original_authenticate_identity = self.main_module.authenticate_identity
        def _raiser(db, credential, scope):
            raise sqlite3.OperationalError("database is locked")
        self.main_module.authenticate_identity = _raiser
        self.addCleanup(setattr, self.main_module, "authenticate_identity", self._original_authenticate_identity)
        self.client = TestClient(self.main_module.app)

    def test_locked_error_from_identity_maps_to_503_with_exact_body(self):
        r = self.client.get("/v1/posts", headers={"Authorization": "Bearer does-not-matter.never-checked"})
        self.assertEqual(503, r.status_code, r.text)
        self.assertEqual({"detail": "database is locked"}, r.json())


class NonLockedOperationalErrorNegativeControlTests(FreshAppCase):
    """Case 4, the most important of the four: a non-locked/busy
    `OperationalError` (schema skew -- "no such table", "no such column")
    must NOT be converted into a tidy, falsely-reassuring retryable 503. It
    must re-raise as a genuine, unhandled exception, with its traceback,
    exactly as B1 condition 2 requires ("must re-raise from inside the
    handler, not be converted to a tidy 500 response ... swallowing it
    would hide schema skew behind a clean error body"). This is the
    assertion that stops a future "improvement" -- widening the
    locked/busy substring match, or converting the handler to a blanket
    `except OperationalError: return 503` -- from turning a real defect
    into the exact silent-wrongness this whole change exists to remove.

    Reuses the same `get_db`-dependency-override technique as
    `DependencySetupOriginTests` (schema skew is exactly as reachable from
    `get_db`'s `connect()` as a lock timeout is), with a message that does
    not contain "locked" or "busy" so the handler's discrimination takes
    the re-raise branch instead of the 503 branch."""

    def setUp(self):
        self.main_module = self._boot()
        self.main_module.app.dependency_overrides[self.main_module.get_db] = _raise_before_yield("no such table: posts")
        self.addCleanup(self.main_module.app.dependency_overrides.clear)

    def test_non_locked_error_reraises_under_strict_client(self):
        # TestClient's default (raise_server_exceptions=True) re-raises an
        # unhandled server exception into the calling test rather than
        # converting it into a response -- this is what "the handler does
        # NOT swallow this" looks like from a test's point of view.
        client = TestClient(self.main_module.app)  # default: raise_server_exceptions=True
        with self.assertRaises(sqlite3.OperationalError):
            client.get("/health/ready")

    def test_non_locked_error_is_a_genuine_500_not_reclassified_or_swallowed(self):
        # The other side of the same coin: what an actual deployed server's
        # caller sees is a real 500 response, not a raised Python exception
        # -- raise_server_exceptions=False surfaces that response instead of
        # re-raising it (Starlette's ServerErrorMiddleware path, what a real
        # ASGI server without debug mode does).
        client = TestClient(self.main_module.app, raise_server_exceptions=False)
        r = client.get("/health/ready")
        self.assertEqual(500, r.status_code)


if __name__ == "__main__":
    unittest.main()
