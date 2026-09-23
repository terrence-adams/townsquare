"""Shared boot harness for HTTP-layer tests against the real FastAPI app.

Extracted from `test_http.py` (where it lived as the private `_FreshAppCase`)
per Addendum A3 of docs/town-registrar-connection-concurrency.md, so
`test_http.py`'s fast single-threaded security regressions and
`test_http_concurrency.py`'s slow thread-pool trials can share one boot
harness without importing a private class across test modules. Moved
behavior-for-behavior: the env save/restore, the per-test temp DB, the
`sys.modules.pop` + fresh re-import, and the LIFO `addCleanup` ordering that
solves the Windows open-file lock are all load-bearing.

Run pytest from the parent of registrar/ (the repo root, e.g.
C:\\Repo\\townsquare), not from inside registrar/tests: `registrar` resolves
as an implicit namespace package, and running from inside tests/ gives a
spurious ModuleNotFoundError (noted in OPERATIONS.md).
"""
from __future__ import annotations
import os,sys,tempfile,unittest
from pathlib import Path

_ENV_KEYS=("REGISTRAR_ENV","REGISTRAR_DB","REGISTRAR_CURSOR_KEY_FILE","REGISTRAR_CURSOR_KEY_ID")


class FreshAppCase(unittest.TestCase):
    """Base class: boot a fresh registrar.app.main under a controlled,
    isolated environment and tear it back down afterward. Each test gets
    its own temp SQLite DB -- main.py migrates at import time, and the
    schema/rows that produces are process-global state that would otherwise
    leak between scenarios."""

    def _key_file(self,data=b"unit-test-http-cursor-signing-key-0123456789"):
        """A standalone temp key file (independent of _boot/self.tmp, so it
        can be created either before or after _boot is called -- some tests
        need the file to exist and be deleted again mid-test)."""
        fd,path=tempfile.mkstemp(); os.close(fd)
        with open(path,"wb") as fh: fh.write(data)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def _boot(self,cursor_key_file=None,cursor_key_id=None):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        saved={k:os.environ.get(k) for k in _ENV_KEYS}
        def restore():
            for k,v in saved.items():
                if v is None: os.environ.pop(k,None)
                else: os.environ[k]=v
        self.addCleanup(restore)
        os.environ["REGISTRAR_ENV"]="development"
        os.environ["REGISTRAR_DB"]=str(Path(self.tmp.name)/"registrar.db")
        if cursor_key_file is None: os.environ.pop("REGISTRAR_CURSOR_KEY_FILE",None)
        else: os.environ["REGISTRAR_CURSOR_KEY_FILE"]=cursor_key_file
        if cursor_key_id is None: os.environ.pop("REGISTRAR_CURSOR_KEY_ID",None)
        else: os.environ["REGISTRAR_CURSOR_KEY_ID"]=cursor_key_id
        sys.modules.pop("registrar.app.main",None)
        self.addCleanup(sys.modules.pop,"registrar.app.main",None)
        # NOTE: main.py no longer keeps a connection past import -- it
        # migrates on a boot connection it closes on the same line, and every
        # request-serving connection is opened and closed by the per-request
        # `get_db` dependency (docs/town-registrar-connection-concurrency.md).
        # So there is nothing for this harness to close afterward, and a
        # startup probe raising below (e.g. ensure_cursor_signing_key_at_startup,
        # which runs after the migration) no longer orphans an open
        # sqlite3.Connection in the exception's traceback. The `gc.collect()`
        # calls in the startup-probe tests are kept anyway: they are harmless,
        # and the Windows open-file-lock knowledge they encode -- Windows,
        # unlike POSIX, refuses to delete a file that is still open, so a
        # leaked connection breaks tearDown's TemporaryDirectory cleanup
        # rather than failing where it was leaked -- is worth keeping around.
        import registrar.app.main as main_module  # runs main.py's import-time startup work under the env above
        return main_module

    def _bearer(self,main_module,scope="post:read",principal="http-test-principal"):
        # `main_module` is still taken (and its boot is what makes the DB and
        # env below meaningful) even though minting no longer goes through it:
        # there is no module-global connection to borrow, so mint on a
        # short-lived connection of our own and close it in `finally` --
        # `auth.create_token` accepts any connection, and the Windows lock
        # described in _boot applies to this one too.
        from registrar.app import auth
        from registrar.app.db import connect
        db=connect(os.environ["REGISTRAR_DB"])
        try: credential=auth.create_token(db,principal,[scope])
        finally: db.close()
        return {"Authorization":f"Bearer {credential}"}
