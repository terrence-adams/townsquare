import os
from fastapi import FastAPI,Header,HTTPException,Query,Request
from .auth import authenticate_identity
from .db import connect,migrate
from .service import Conflict,Forbidden,Invalid,Registrar,Unavailable
from .attestation import verify as verify_attestation
from .runtime import ensure_runtime_mode,verification_enabled

ensure_runtime_mode(os.environ.get("REGISTRAR_ENV","development"))

DB_PATH=os.environ.get("REGISTRAR_DB","/data/registrar.db")
db=connect(DB_PATH); migrate(db); service=Registrar(db)
app=FastAPI(title="Town Registrar",version="1")

def identity(authorization,scope):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401,"Bearer token required")
    try: return authenticate_identity(db,authorization[7:],scope)
    except Forbidden as exc: raise HTTPException(403,str(exc)) from exc

def invoke(fn):
    try: return fn()
    except Conflict as exc: raise HTTPException(409,str(exc)) from exc
    except Forbidden as exc: raise HTTPException(403,str(exc)) from exc
    except Invalid as exc: raise HTTPException(400,str(exc)) from exc
    except Unavailable as exc: raise HTTPException(503,str(exc)) from exc

CURSOR_KEY_MIN_BYTES=32
def _load_cursor_key_material(path):
    """Read and validate cursor-signing key material from `path`. Raises
    OSError (missing/unreadable file) or ValueError (key material shorter
    than CURSOR_KEY_MIN_BYTES -- an empty/misconfigured secret must fail
    instead of silently signing forgeable-but-functioning cursors, F4
    2026-09-22) on any problem. The two call sites below decide what
    "raise" means for them: `ensure_cursor_signing_key_at_startup` lets it
    fail the boot loudly, matching `runtime.ensure_runtime_mode`'s
    fail-at-import convention; `_read_cursor_key` catches it and degrades to
    "no usable key" per request instead."""
    data=open(path,"rb").read().strip()
    if len(data)<CURSOR_KEY_MIN_BYTES: raise ValueError(f"cursor signing key material is only {len(data)} bytes (need >={CURSOR_KEY_MIN_BYTES}): {path}")
    return data
def _read_cursor_key(path):
    """Per-request key read. gsp's F1 (2026-09-22 review of 466c55d): a
    present-but-unreadable -- or, per F4, undersized -- key file must not
    500 every GET /v1/posts call. Only requests that actually send a
    `cursor` need the key at all (service.posts() itself raises Unavailable
    when the resolved current key is None); no-cursor requests must stay
    200 either way. So any failure here degrades to "no usable current
    key", exactly as if REGISTRAR_CURSOR_KEY_FILE were never set -- this
    never raises."""
    if not path: return None
    try: return _load_cursor_key_material(path)
    except (OSError,ValueError): return None
def ensure_cursor_signing_key_at_startup():
    """Fail loudly at boot if REGISTRAR_CURSOR_KEY_FILE is set but not
    actually usable -- matches `ensure_runtime_mode`'s fail-at-import
    convention above. Before this fix, a misprovisioned secret only
    surfaced as a 500 on the first GET /v1/posts call, behind a green
    /health/ready (gsp, 2026-09-22 security review of 466c55d)."""
    path=os.environ.get("REGISTRAR_CURSOR_KEY_FILE")
    if not path: return
    try: _load_cursor_key_material(path)
    except OSError as exc: raise RuntimeError(f"REGISTRAR_CURSOR_KEY_FILE={path!r} is set but unreadable: {exc}") from exc
    except ValueError as exc: raise RuntimeError(str(exc)) from exc
def cursor_keys():
    """Resolve the cursor-signing key material for this request. Read fresh
    per call (not cached at import time) so an operator can rotate the
    mounted secret file without restarting the container. `REGISTRAR_CURSOR_KEY_FILE`
    is the Docker secret OPERATIONS.md and compose.example.yml already
    declare.

    No `previous`-key env wiring lives here (F3, 2026-09-22 -- gsp's
    ownership assignment on 466c55d's review, decision made by jackie-chan):
    `Registrar.posts()`/`decode_cursor()` in service.py still accept and
    correctly isolate a `previous` key for a bounded rotation overlap
    (verify-only, never sign -- see test_cursor_key_rotation_bounded_overlap),
    so that safe primitive is intact and callable. What's removed is only
    the *unwired, unvalidated* env-var plumbing that used to live here:
    none of REGISTRAR_CURSOR_KEY_FILE_PREVIOUS/_ID_PREVIOUS were wired into
    compose.example.yml (unlike _FILE/_ID), _ID_PREVIOUS had no default and
    no startup check, and an operator setting _FILE_PREVIOUS without
    _ID_PREVIOUS (or vice versa) silently produced previous=None with no
    warning -- an untested, silently-no-op rotation path is worse than no
    rotation path. Re-add the env resolution -- wired into
    compose.example.yml, documented in OPERATIONS.md's rotation procedure,
    and validated at startup (fail loud if one of the paired vars is set
    without the other) -- in a dedicated, reviewed change when key rotation
    is actually needed operationally."""
    current_file=os.environ.get("REGISTRAR_CURSOR_KEY_FILE"); current_id=os.environ.get("REGISTRAR_CURSOR_KEY_ID","current")
    key=_read_cursor_key(current_file) if current_file else None
    current=(current_id,key) if key is not None else None
    return current,None
ensure_cursor_signing_key_at_startup()

@app.get("/health/live")
def live(): return {"ok":True}
@app.get("/health/ready")
def ready():
    checks={"foreign_keys":db.execute("PRAGMA foreign_keys").fetchone()[0],"journal_mode":db.execute("PRAGMA journal_mode").fetchone()[0],"synchronous":db.execute("PRAGMA synchronous").fetchone()[0]}
    if checks!={"foreign_keys":1,"journal_mode":"wal","synchronous":2}: raise HTTPException(503,checks)
    return {"ok":True,"schema_version":db.execute("SELECT max(version) FROM schema_migrations").fetchone()[0]}
@app.post("/v1/roots/reserve",status_code=201)
async def reserve_root(request:Request,authorization:str|None=Header(None),idempotency_key:str|None=Header(None)):
    who,_=identity(authorization,"post:write"); body=await request.json(); return invoke(lambda:service.reserve_root(who,idempotency_key,body))
@app.post("/v1/roots/{thread_id}/posts/reserve",status_code=201)
async def reserve_post(thread_id:str,request:Request,authorization:str|None=Header(None),idempotency_key:str|None=Header(None)):
    who,_=identity(authorization,"post:write"); body=await request.json(); return invoke(lambda:service.reserve_post(who,idempotency_key,thread_id,body))
@app.put("/v1/posts/{post_uid}/publication")
async def publish(post_uid:str,request:Request,authorization:str|None=Header(None),idempotency_key:str|None=Header(None)):
    who,scopes=identity(authorization,"post:write"); body=await request.json(); return invoke(lambda:service.publish(who,idempotency_key,post_uid,body,scopes))
@app.post("/v1/verifications/{post_uid}")
async def verify(post_uid:str,request:Request,authorization:str|None=Header(None),idempotency_key:str|None=Header(None)):
    if not verification_enabled(os.environ.get("REGISTRAR_EXPERIMENTAL_VERIFICATION")): raise HTTPException(503,"experimental verification disabled")
    who,_=identity(authorization,"admin:verify"); body=await request.json(); evidence=body.get("evidence"); attestation=body.get("attestation")
    key_file=os.environ.get("REGISTRAR_VERIFIER_KEY_FILE"); key_id=os.environ.get("REGISTRAR_VERIFIER_KEY_ID")
    if not key_file or not key_id: raise HTTPException(503,"verifier attestation not configured")
    invoke(lambda:verify_attestation(db,evidence,attestation,key_id,open(key_file,"rb").read().strip()))
    return invoke(lambda:service.verify_publication(who,idempotency_key,post_uid,evidence))
@app.post("/v1/import-runs",status_code=201)
async def import_run(request:Request,authorization:str|None=Header(None)):
    who,_=identity(authorization,"admin:import-stage"); body=await request.json(); return invoke(lambda:service.stage_import(who,body))
@app.post("/v1/import-runs/{run_id}/promote")
async def promote(run_id:str,request:Request,authorization:str|None=Header(None)):
    who,_=identity(authorization,"admin:import-promote"); body=await request.json(); return invoke(lambda:service.promote_import(who,run_id,body.get("manifest_digest","")))
@app.get("/v1/roots/{thread_id}")
def get_root(thread_id:str,authorization:str|None=Header(None)):
    identity(authorization,"post:read")
    row=db.execute("SELECT * FROM roots WHERE thread_id=?",(thread_id,)).fetchone()
    if not row: raise HTTPException(404,"unknown root")
    return dict(row)
@app.get("/v1/posts/{post_uid}")
def get_post(post_uid:str,authorization:str|None=Header(None)):
    identity(authorization,"post:read")
    row=db.execute("SELECT * FROM posts WHERE post_uid=?",(post_uid,)).fetchone()
    if not row: raise HTTPException(404,"unknown post")
    return dict(row)
@app.get("/v1/posts")
def posts(assigned_to:str|None=None,role:str|None=None,state:str|None=None,board:str|None=None,registration_state:str|None=None,root:str|None=None,limit:int=Query(100,ge=1,le=200),cursor:str|None=None,authorization:str|None=Header(None)):
    identity(authorization,"post:read")
    current,previous=cursor_keys()
    return invoke(lambda:service.posts(assigned_to=assigned_to,role=role,state=state,board=board,registration_state=registration_state,root=root,limit=limit,cursor=cursor,cursor_keys=(current,previous)))
@app.get("/v1/aliases/{alias:path}")
def aliases(alias:str,authorization:str|None=Header(None)):
    identity(authorization,"post:read"); return service.aliases(alias)
@app.get("/v1/assignments/{agent_id}")
def assignments(agent_id:str,active:bool=True,authorization:str|None=Header(None)):
    identity(authorization,"post:read")
    return {"assignments":[dict(r) for r in db.execute("SELECT * FROM assignments WHERE agent_id=? AND active=? ORDER BY post_uid,role",(agent_id,int(active)))]}
@app.get("/v1/reconciliation")
def reconciliation(status:str,authorization:str|None=Header(None)):
    identity(authorization,"post:read")
    if status=="missing-publication": rows=db.execute("SELECT * FROM posts WHERE registration_state='reserved'")
    elif status=="legacy-collision": rows=db.execute("SELECT p.* FROM posts p JOIN posts q ON p.root_uid=q.root_uid AND p.legacy_seq=q.legacy_seq AND p.post_uid<>q.post_uid WHERE p.source='legacy_import'")
    elif status=="unresolved-responsibility":
        observations=[dict(r) for r in db.execute("SELECT * FROM import_observations WHERE warnings_json LIKE '%unresolved_responsibility%' ORDER BY import_run_id,drive_file_id")]
        return {"status":status,"observations":observations}
    elif status=="artifacts":
        return {"status":status,"artifacts":[dict(r) for r in db.execute("SELECT * FROM artifacts ORDER BY filename,drive_file_id")]}
    else: rows=[]
    return {"status":status,"posts":[dict(r) for r in rows]}
