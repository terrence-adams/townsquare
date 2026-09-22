import secrets
from .service import Forbidden,now
try:
    from argon2 import PasswordHasher
except ImportError:  # startup reports the missing deployment dependency
    PasswordHasher=None

def create_token(db,principal,scopes):
    if PasswordHasher is None: raise RuntimeError("argon2-cffi is required")
    token_id=secrets.token_urlsafe(9); secret=secrets.token_urlsafe(32)
    db.execute("INSERT INTO tokens VALUES (?,?,?,?,?,NULL,NULL)",(token_id,principal,PasswordHasher().hash(secret)," ".join(sorted(set(scopes))),now()))
    return token_id+"."+secret

def authenticate(db,credential,scope=None):
    if PasswordHasher is None: raise RuntimeError("argon2-cffi is required")
    try: token_id,secret=credential.split(".",1)
    except ValueError as exc: raise Forbidden("invalid credential") from exc
    row=db.execute("SELECT * FROM tokens WHERE token_id=? AND revoked_at IS NULL",(token_id,)).fetchone()
    if not row:
        raise Forbidden("invalid credential")
    try: PasswordHasher().verify(row["secret_hash"],secret)
    except Exception as exc: raise Forbidden("invalid credential") from exc
    scopes=set(row["scopes"].split())
    if scope and scope not in scopes: raise Forbidden("missing scope")
    db.execute("UPDATE tokens SET last_used_at=? WHERE token_id=?",(now(),token_id)); return row["principal_id"]

def authenticate_identity(db,credential,scope):
    """Authenticate and return principal plus scopes after mandatory scope check."""
    principal=authenticate(db,credential,scope)
    token_id=credential.split(".",1)[0]
    scopes=set(db.execute("SELECT scopes FROM tokens WHERE token_id=?",(token_id,)).fetchone()[0].split())
    return principal,scopes

def main():
    """Offline bootstrap; run only from the protected Registrar container console."""
    import argparse,sys
    from .db import connect,migrate
    ap=argparse.ArgumentParser(); ap.add_argument("--db",required=True); ap.add_argument("--principal",required=True)
    ap.add_argument("--namespace",action="append",default=[]); ap.add_argument("--board",action="append",default=[])
    # WS3 item 7: `action="append"` APPENDS to `default`, so the old
    # default=["post:write"] meant every minted token silently carried the
    # writer scope regardless of what --scope was actually requested on the
    # command line -- the exact scope Decision 1's decoupling invariant
    # ("no post:write token exists until adoption") requires stay closed.
    # default=[] matches the (correct) pattern --namespace/--board already
    # use one line above; the explicit post-parse fallback below restores
    # the convenience default ONLY when --scope was truly never passed at
    # all, instead of silently unioning it into every invocation.
    ap.add_argument("--scope",action="append",default=[]); args=ap.parse_args()
    if not args.scope: args.scope=["post:write"]
    db=connect(args.db); migrate(db)
    for kind,values in (("namespace",args.namespace),("board",args.board)):
        for value in values: db.execute("INSERT OR IGNORE INTO acls VALUES (?,?,?,NULL,NULL)",(args.principal,kind,value.lower()))
    token=create_token(db,args.principal,args.scope)
    # gsp's NEW-2 (WS3 post-review, 2026-09-22): the class of bug item 7
    # just fixed (a token silently minted with MORE scope than requested)
    # was invisible at mint time -- only the credential itself ever printed.
    # One line to stderr (never stdout, so it can't be captured/piped as if
    # it were the credential) makes exactly what was granted observable,
    # not just what the caller asked for.
    print(f"minted token principal={args.principal!r} scopes={sorted(set(args.scope))} namespaces={sorted(set(args.namespace))} boards={sorted(set(v.lower() for v in args.board))}",file=sys.stderr)
    print(token)
if __name__=="__main__": main()
