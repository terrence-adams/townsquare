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
import hashlib,json,os,stat,sys,tempfile,unittest
from pathlib import Path

_ENV_KEYS=(
    "REGISTRAR_ENV", "REGISTRAR_DB", "REGISTRAR_CURSOR_KEY_FILE", "REGISTRAR_CURSOR_KEY_ID",
    "TOWNSQUARE_RECEIPT_HASH_KEY_FILE", "TOWNSQUARE_RECEIPT_HASH_KEY_ID",
    "TOWNSQUARE_CONTEXT_MANIFEST", "TOWNSQUARE_LEDGER_CONTEXT_MANIFEST", "TOWNSQUARE_LEDGER_CONTEXT_MANIFEST_SHA256", "TOWNSQUARE_GOVERNANCE_AUTHORITY",
    "TOWNSQUARE_R7_IDENTITY_FILE", "TOWNSQUARE_R7_IDENTITY_SHA256",
    "TOWNSQUARE_RUNTIME_CLASS", "TOWNSQUARE_AUTHORITY_CLASS", "TOWNSQUARE_CANARY_LABEL",
    "TOWNSQUARE_COMPOSE_PROJECT", "TOWNSQUARE_SOURCE_COMMIT", "TOWNSQUARE_SOURCE_TREE",
    "TOWNSQUARE_R7_RELEASE_ID", "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256",
    "TOWNSQUARE_EMBEDDED_RUNTIME_CLASS", "TOWNSQUARE_EMBEDDED_AUTHORITY_CLASS",
    "TOWNSQUARE_EMBEDDED_CANARY_LABEL", "TOWNSQUARE_EMBEDDED_COMPOSE_PROJECT",
    "TOWNSQUARE_EMBEDDED_SOURCE_COMMIT", "TOWNSQUARE_EMBEDDED_SOURCE_TREE",
    "TOWNSQUARE_EMBEDDED_R7_RELEASE_ID", "TOWNSQUARE_EMBEDDED_R7_INPUT_MANIFEST_SHA256",
    "REGISTRY_READINESS_TOKEN_FILE", "REGISTRY_PEER_READINESS_TOKEN_FILE",
    "TOWNSQUARE_CANARY_TEST_PUBLIC_KEY_FILE",
)

_TEST_IDENTITY={
    "TOWNSQUARE_RUNTIME_CLASS":"CANARY",
    "TOWNSQUARE_AUTHORITY_CLASS":"NON-AUTHORITATIVE",
    "TOWNSQUARE_CANARY_LABEL":"TS-CANARY-NAS1-20261007-A",
    "TOWNSQUARE_COMPOSE_PROJECT":"townsquare-canary-20261007-a",
    "TOWNSQUARE_SOURCE_COMMIT":"a"*40,
    "TOWNSQUARE_SOURCE_TREE":"b"*40,
    "TOWNSQUARE_R7_RELEASE_ID":"TS-R7-"+"c"*64,
    "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256":"d"*64,
}


class FreshAppCase(unittest.TestCase):
    """Boot a fresh app against a schema prepared by the one canonical migrator."""

    def _key_file(self,data=b"unit-test-http-cursor-signing-key-0123456789"):
        """A standalone temp key file (independent of _boot/self.tmp, so it
        can be created either before or after _boot is called -- some tests
        need the file to exist and be deleted again mid-test)."""
        fd,path=tempfile.mkstemp(); os.close(fd)
        with open(path,"wb") as fh: fh.write(data)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def _boot(self,cursor_key_file=None,cursor_key_id=None,*,context_manifest=None,authority_proof=None):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        saved={k:os.environ.get(k) for k in _ENV_KEYS}
        def restore():
            for k,v in saved.items():
                if v is None: os.environ.pop(k,None)
                else: os.environ[k]=v
        self.addCleanup(restore)
        os.environ["REGISTRAR_ENV"]="development"
        for name,value in _TEST_IDENTITY.items():
            os.environ[name]=value
            os.environ["TOWNSQUARE_EMBEDDED_"+name.removeprefix("TOWNSQUARE_")]=value
        identity={"schema_version":"1",**{name.removeprefix("TOWNSQUARE_").lower():value for name,value in _TEST_IDENTITY.items()}}
        identity_path=Path(self.tmp.name)/"r7-identity.json"; identity_raw=json.dumps(identity,sort_keys=True,separators=(",",":")).encode(); identity_path.write_bytes(identity_raw); os.chmod(identity_path,0o444)
        os.environ["TOWNSQUARE_R7_IDENTITY_FILE"]=str(identity_path); os.environ["TOWNSQUARE_R7_IDENTITY_SHA256"]=hashlib.sha256(identity_raw).hexdigest()
        r7_context={"schema_version":"1","profile_version":"r7-context-v1",**{key:value for key,value in identity.items() if key!="schema_version"},"service_ids":[{"role":"ledger","service_id":"townsquare-ledger-v0"},{"role":"registry","service_id":"townsquare-registry-v0"},{"role":"viewer","service_id":"townsquare-viewer-v0"},{"role":"backup","service_id":"townsquare-backup-v0"}],"ledger_contract_sha256":"1"*64,"registry_contract_sha256":"2"*64,"compatibility_matrix_sha256":"3"*64}
        r7_context_path=Path(self.tmp.name)/"r7-context.json"; r7_context_path.write_text(json.dumps(r7_context,sort_keys=True,separators=(",",":")),encoding="utf-8"); os.chmod(r7_context_path,0o444)
        os.environ["TOWNSQUARE_CONTEXT_MANIFEST"]=str(r7_context_path)
        os.environ["REGISTRAR_DB"]=str(Path(self.tmp.name)/"registrar.db")
        receipt_key=self._key_file(b"unit-test-http-receipt-hash-key-0123456789-abcdef")
        os.environ["TOWNSQUARE_RECEIPT_HASH_KEY_FILE"]=receipt_key
        os.environ["TOWNSQUARE_RECEIPT_HASH_KEY_ID"]="http-test-receipt-key-v1"
        if cursor_key_file is None: os.environ.pop("REGISTRAR_CURSOR_KEY_FILE",None)
        else: os.environ["REGISTRAR_CURSOR_KEY_FILE"]=cursor_key_file
        if cursor_key_id is None: os.environ.pop("REGISTRAR_CURSOR_KEY_ID",None)
        else: os.environ["REGISTRAR_CURSOR_KEY_ID"]=cursor_key_id
        if context_manifest is None:
            os.environ.pop("TOWNSQUARE_LEDGER_CONTEXT_MANIFEST",None)
            os.environ.pop("TOWNSQUARE_LEDGER_CONTEXT_MANIFEST_SHA256",None)
        else:
            manifest_path=Path(self.tmp.name)/"context-manifest.json"
            manifest_path.write_text(json.dumps(context_manifest),encoding="utf-8")
            raw=json.dumps(context_manifest,sort_keys=True,separators=(",",":")).encode(); manifest_path.write_bytes(raw); os.chmod(manifest_path,0o444)
            os.environ["TOWNSQUARE_LEDGER_CONTEXT_MANIFEST"]=str(manifest_path)
            os.environ["TOWNSQUARE_LEDGER_CONTEXT_MANIFEST_SHA256"]=hashlib.sha256(raw).hexdigest()
        if authority_proof is None:
            os.environ.pop("TOWNSQUARE_GOVERNANCE_AUTHORITY",None)
        else:
            proof_path=Path(self.tmp.name)/"authority-proof.json"
            proof_path.write_text(json.dumps(authority_proof),encoding="utf-8")
            os.environ["TOWNSQUARE_GOVERNANCE_AUTHORITY"]=str(proof_path)
        # The application is a schema verifier only.  Run the canonical
        # migrator here before importing main so HTTP tests never rely on
        # import-time DDL or race a real deployment migrator.
        from registrar.app.db import connect,migrate
        bootstrap=connect(os.environ["REGISTRAR_DB"])
        try: migrate(bootstrap)
        finally: bootstrap.close()
        sys.modules.pop("registrar.app.main",None)
        self.addCleanup(sys.modules.pop,"registrar.app.main",None)
        # NOTE: main.py performs no DDL at import.  It only verifies the
        # schema prepared above, and every request-serving connection is
        # opened and closed by the per-request `get_db` dependency.
        # So there is nothing for this harness to close afterward, and a
        # startup probe raising below (e.g. ensure_cursor_signing_key_at_startup,
        # which runs after schema verification) no longer orphans an open
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
