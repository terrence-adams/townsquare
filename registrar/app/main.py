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

def cursor_keys():
    """Resolve the cursor-signing key material for this request. Read fresh
    per call (not cached at import time) so an operator can rotate the
    mounted secret file without restarting the container -- the same
    live-rotation posture the /v1/verifications key lookup below already
    uses. `REGISTRAR_CURSOR_KEY_FILE` is the Docker secret OPERATIONS.md and
    compose.example.yml already declare; the `_PREVIOUS` pair is optional and
    only needed while a key rotation's bounded overlap window is open
    (design.md §11) -- absent by default, no compose change required to keep
    working exactly as today."""
    def read(path): return open(path,"rb").read().strip() if path else None
    current_file=os.environ.get("REGISTRAR_CURSOR_KEY_FILE"); current_id=os.environ.get("REGISTRAR_CURSOR_KEY_ID","current")
    previous_file=os.environ.get("REGISTRAR_CURSOR_KEY_FILE_PREVIOUS"); previous_id=os.environ.get("REGISTRAR_CURSOR_KEY_ID_PREVIOUS")
    current=(current_id,read(current_file)) if current_file else None
    previous=(previous_id,read(previous_file)) if previous_file and previous_id else None
    return current,previous

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
