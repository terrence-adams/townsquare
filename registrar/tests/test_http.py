"""HTTP-layer regression tests for the 2026-09-22 review of 466c55d
(GET /v1/posts stable-cursor pagination): gsp's security review and
ronda-rousey's QA pass both found real bugs in registrar.app.main's HTTP
wiring around the cursor-signing key and cursor decoding -- bugs the rest
of this suite (test_registrar.py) could never catch, because it exercises
Registrar.posts() directly and never spins up the real FastAPI app. That is
exactly how F1 (a bug in main.py, not service.py) got past the first
review round. These tests close that gap.

registrar.app.main performs its startup work -- runtime-mode check, DB
connect/migrate, and (as of this fix pass) the cursor-signing-key startup
probe added for F1 -- as *module-level* side effects at import time, the
same convention ensure_runtime_mode already used before this change.
Exercising different key-provisioning scenarios therefore means
reimporting the module fresh under a controlled os.environ for each one
(see _FreshAppCase._boot below), not monkeypatching an already-imported
app object after the fact.

Run pytest from the parent of registrar/ (the repo root, e.g.
C:\\Repo\\townsquare), not from inside registrar/tests: `registrar`
resolves as an implicit namespace package, and running from inside tests/
gives a spurious ModuleNotFoundError (noted in OPERATIONS.md).
"""
from __future__ import annotations
import base64,gc,json,os,sys,tempfile,unittest
from pathlib import Path
from fastapi.testclient import TestClient

_ENV_KEYS=("REGISTRAR_ENV","REGISTRAR_DB","REGISTRAR_CURSOR_KEY_FILE","REGISTRAR_CURSOR_KEY_ID")


class _FreshAppCase(unittest.TestCase):
    """Base class: boot a fresh registrar.app.main under a controlled,
    isolated environment and tear it back down afterward. Each test gets
    its own temp SQLite DB -- main.py's module-level `db=connect(...)` is
    otherwise process-global and would leak state between scenarios."""

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
        # NOTE: if a startup probe (e.g. ensure_cursor_signing_key_at_startup)
        # raises here, main.py's module-level `db=connect(...)` already ran,
        # orphaning an open sqlite3.Connection kept alive by the exception's
        # own traceback (a refcount cycle) until that traceback is dropped.
        # Callers expecting this to raise must gc.collect() after their
        # `assertRaises` block, or Windows' exclusive file lock on
        # registrar.db will fail tearDown's TemporaryDirectory cleanup --
        # see the two startup-probe-failure tests below, and the same
        # gc.collect() convention test_registrar.py already uses around
        # auth.main().
        import registrar.app.main as main_module  # runs main.py's import-time startup work under the env above
        # addCleanup is LIFO: registering this last means it runs *first*,
        # closing the sqlite3.Connection before the TemporaryDirectory
        # cleanup above tries to remove registrar.db -- required on
        # Windows, which (unlike POSIX) refuses to delete a file that's
        # still open, and this module-level `db` is otherwise never closed.
        self.addCleanup(main_module.db.close)
        return main_module

    def _bearer(self,main_module,scope="post:read",principal="http-test-principal"):
        from registrar.app import auth
        credential=auth.create_token(main_module.db,principal,[scope])
        return {"Authorization":f"Bearer {credential}"}


class CursorSigningKeyStartupProbeTests(_FreshAppCase):
    """F1's second half: a misprovisioned REGISTRAR_CURSOR_KEY_FILE must
    fail the boot loudly, not surface as a 500 on first use."""

    def test_fails_loudly_when_key_file_path_does_not_exist(self):
        missing=str(Path(tempfile.mkdtemp())/"does-not-exist")
        with self.assertRaises(RuntimeError):
            self._boot(cursor_key_file=missing)
        # The raised exception's traceback keeps main.py's module frame (and
        # its already-opened sqlite3.Connection) referenced in a cycle until
        # the `with` block's own context manager is itself collected; force
        # it now so tearDown's TemporaryDirectory cleanup can delete
        # registrar.db without hitting Windows' open-file lock.
        gc.collect()

    def test_fails_loudly_when_key_material_is_undersized(self):
        # F4: an empty/near-empty key must not be silently accepted as
        # valid (forgeable-but-functioning cursors) -- it must fail, and
        # per F1's startup-probe requirement, fail at boot, not at request time.
        short_key=self._key_file(b"too-short")
        with self.assertRaises(RuntimeError):
            self._boot(cursor_key_file=short_key)
        gc.collect()  # see comment in test_fails_loudly_when_key_file_path_does_not_exist

    def test_boots_cleanly_when_key_file_is_absent_from_env(self):
        # Backward compatibility: no REGISTRAR_CURSOR_KEY_FILE at all is a
        # supported, deliberate "pagination not yet provisioned" state, not
        # a misconfiguration -- must not raise.
        main_module=self._boot(cursor_key_file=None)
        self.assertIsNotNone(main_module.app)

    def test_boots_cleanly_when_key_file_is_valid(self):
        main_module=self._boot(cursor_key_file=self._key_file())
        self.assertIsNotNone(main_module.app)


class NoCursorRequestBackwardCompatibilityTests(_FreshAppCase):
    """F1's core regression: gsp proved that a GET /v1/posts call with no
    `cursor` param at all -- including plain, pre-pagination clients --
    500'd whenever the cursor-signing key was present in env but unreadable
    on disk, behind a green /health/ready. It must stay 200 in every
    key-provisioning state."""

    def test_no_key_configured_at_all(self):
        main_module=self._boot(cursor_key_file=None)
        client=TestClient(main_module.app); headers=self._bearer(main_module)
        r=client.get("/v1/posts",headers=headers)
        self.assertEqual(200,r.status_code)
        self.assertIsNone(r.json()["next_cursor"])

    def test_key_file_present_at_boot_then_becomes_unreadable(self):
        # The exact scenario gsp reproduced: REGISTRAR_CURSOR_KEY_FILE is
        # set (as compose.example.yml always sets it in a real deployment)
        # and valid at boot -- the startup probe passes -- but the file
        # then becomes unreadable while the app keeps running (NAS hiccup,
        # a botched secret rotation, permissions drift). cursor_keys()
        # reads fresh per request by design (to support live rotation
        # without a restart), so this is reachable in production and must
        # degrade gracefully rather than 500.
        key_path=self._key_file()
        main_module=self._boot(cursor_key_file=key_path)
        client=TestClient(main_module.app)
        self.assertEqual(200,client.get("/health/ready").status_code)
        os.remove(key_path)  # simulate the secret going unreadable post-boot
        headers=self._bearer(main_module)
        r=client.get("/v1/posts",headers=headers)
        self.assertEqual(200,r.status_code,r.text)
        self.assertIsNone(r.json()["next_cursor"])
        # /health/ready never probed the cursor key and stays green -- this
        # is exactly the "500s behind a green /health/ready" gap gsp flagged.
        self.assertEqual(200,client.get("/health/ready").status_code)
        # An actual cursor= request in this degraded state still fails
        # *closed* (503 Unavailable), never a 500 and never silently
        # accepted with an unverifiable key.
        r2=client.get("/v1/posts",params={"cursor":"whatever"},headers=headers)
        self.assertEqual(503,r2.status_code)


class MalformedCursorRejectionTests(_FreshAppCase):
    """F2 and the cursor="" minor finding: every malformed cursor shape
    must land on Invalid->400, never an unhandled 500 or a silent
    fresh-start. Requires a valid signing key configured so decode_cursor()
    is actually reached (current is not None)."""

    def setUp(self):
        self.main_module=self._boot(cursor_key_file=self._key_file())
        self.client=TestClient(self.main_module.app)
        self.headers=self._bearer(self.main_module)

    def test_non_ascii_sig_is_rejected_as_400_not_500(self):
        # F2 (gsp): hmac.compare_digest raises TypeError on a non-ASCII str
        # sig, and the pre-fix try/except only covered hmac.new, not the
        # comparison -- so this used to be an unhandled 500. The sig here is
        # exactly 64 characters (matching a real hex digest's length) with a
        # non-hex, non-ASCII character embedded in the middle, so this
        # exercises the hex-content check itself, not just a length
        # mismatch.
        sig="café"+"0"*60
        self.assertEqual(64,len(sig))
        envelope={"payload":{"v":1,"created_at":"2026-01-01T00:00:00Z","post_uid":"x","filter_hash":"0"*64,"kid":"current","iat":0},"sig":sig}
        body=json.dumps(envelope,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
        token=base64.urlsafe_b64encode(body).rstrip(b"=").decode("ascii")
        r=self.client.get("/v1/posts",params={"cursor":token},headers=self.headers)
        self.assertEqual(400,r.status_code,r.text)

    def test_empty_string_cursor_is_rejected_not_silently_page_one(self):
        # ronda-rousey's adversarial probing: cursor="" was falsy under the
        # old `if cursor:` check and silently treated as page one, unlike
        # every other malformed cursor shape (which all correctly 400).
        r=self.client.get("/v1/posts",params={"cursor":""},headers=self.headers)
        self.assertEqual(400,r.status_code,r.text)

    def test_garbage_cursor_is_still_rejected_as_400(self):
        # Sanity check alongside the two regressions above: an ordinary
        # malformed (non-empty, non-base64) cursor must still 400.
        r=self.client.get("/v1/posts",params={"cursor":"not-a-real-cursor"},headers=self.headers)
        self.assertEqual(400,r.status_code,r.text)


if __name__=="__main__": unittest.main()
