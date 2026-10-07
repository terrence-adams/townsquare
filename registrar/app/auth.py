import secrets
from datetime import datetime,timedelta,timezone
from .service import Forbidden,now
try:
    from argon2 import PasswordHasher
except ImportError:  # startup reports the missing deployment dependency
    PasswordHasher=None

def _validate_scope(scope):
    if not isinstance(scope,str) or not scope or any(char.isspace() for char in scope):
        raise Forbidden("invalid scope")
    return scope

def create_token(db,principal,scopes):
    if isinstance(scopes,str): raise Forbidden("invalid scope")
    try: scopes=[_validate_scope(scope) for scope in scopes]
    except TypeError as exc: raise Forbidden("invalid scope") from exc
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

# Release-pinned native capability policy. Native endpoints intentionally do
# not inherit mutable legacy token scopes; changing this matrix is a release
# decision, while each credential pins the policy version it was issued for.
NATIVE_CAPABILITY_POLICIES={
    "townsquare-mvp-v1":{
        "writer-a":{"post:read","context:read","context:attest","request:open","request:work","request:resolve","request:correct"},
        "writer-b":{"post:read","context:read","context:attest","request:work","request:block","request:resolve","request:cancel","request:correct"},
        "reviewer":{"post:read","context:read","context:attest","request:accept"},
        "viewer":{"post:read","notice:read"},
        "crier":{"post:read","notice:read"},
        "projector":{"post:read","notice:read"},
        "operator":{"post:read","notice:read","context:read","context:attest","content:restricted:read","operator:stop","request:cancel","request:archive"},
        "operator-resume":{"operator:resume"},
        "registry-audit":{"registry:audit:append"},
    }
}

def create_native_credential(db,principal,*,policy_version="townsquare-mvp-v1",ttl_seconds=3600):
    """Offline-only native credential issuer; no HTTP route calls this."""
    if PasswordHasher is None: raise RuntimeError("argon2-cffi is required")
    policy=NATIVE_CAPABILITY_POLICIES.get(policy_version)
    if policy is None or principal not in policy: raise Forbidden("principal is not in the pinned capability policy")
    if not isinstance(ttl_seconds,int) or ttl_seconds<1: raise Forbidden("credential lifetime must be positive")
    credential_id=secrets.token_urlsafe(12); secret=secrets.token_urlsafe(32); issued=now()
    expires=(datetime.now(timezone.utc)+timedelta(seconds=ttl_seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")
    db.execute("INSERT INTO auth_credentials VALUES (?,?,?,?,?,?)",(credential_id,principal,PasswordHasher().hash(secret),policy_version,issued,expires))
    return credential_id+"."+secret

def revoke_native_credential(db,credential_id,reason,revoked_by):
    """Append revocation evidence; the immutable credential row is untouched."""
    if not db.execute("SELECT 1 FROM auth_credentials WHERE credential_id=?",(credential_id,)).fetchone(): raise Forbidden("unknown native credential")
    db.execute("INSERT INTO credential_revocations VALUES (?,?,?,?,?)",(secrets.token_urlsafe(12),credential_id,str(reason),revoked_by,now()))

def authenticate_native_identity(db,credential,capability):
    if PasswordHasher is None: raise RuntimeError("argon2-cffi is required")
    try: credential_id,secret=credential.split(".",1)
    except (AttributeError,ValueError) as exc: raise Forbidden("invalid credential") from exc
    row=db.execute("SELECT * FROM auth_credentials WHERE credential_id=?",(credential_id,)).fetchone()
    instant=now()
    revoked=db.execute("SELECT 1 FROM credential_revocations WHERE credential_id=? LIMIT 1",(credential_id,)).fetchone() if row else None
    if not row or revoked or row["expires_at"]<=instant: raise Forbidden("invalid credential")
    try: PasswordHasher().verify(row["token_hash"],secret)
    except Exception as exc: raise Forbidden("invalid credential") from exc
    capabilities=NATIVE_CAPABILITY_POLICIES.get(row["authorization_policy_version"],{}).get(row["principal"],set())
    if capability not in capabilities: raise Forbidden("missing capability")
    return row["principal"],set(capabilities)

def main():
    """Offline bootstrap; run only from the protected Registrar container console."""
    import argparse,sys
    from .db import connect,verify_schema
    ap=argparse.ArgumentParser(); ap.add_argument("--db",required=True); ap.add_argument("--principal",required=True)
    ap.add_argument("--namespace",action="append",default=[]); ap.add_argument("--board",action="append",default=[])
    def scope(value):
        try: return _validate_scope(value)
        except Forbidden:
            raise argparse.ArgumentTypeError("--scope must be a non-empty capability")
    # Minting is fail-closed: a caller must deliberately name every capability.
    # In particular, omission must never create a post:write credential.
    ap.add_argument("--scope",action="append",required=True,type=scope); args=ap.parse_args()
    db=connect(args.db)
    try:
        verify_schema(db)
        for kind,values in (("namespace",args.namespace),("board",args.board)):
            for value in values: db.execute("INSERT OR IGNORE INTO acls VALUES (?,?,?,NULL,NULL)",(args.principal,kind,value.lower()))
        token=create_token(db,args.principal,args.scope)
    finally:
        db.close()
    # gsp's NEW-2 (WS3 post-review, 2026-09-22): the class of bug item 7
    # just fixed (a token silently minted with MORE scope than requested)
    # was invisible at mint time -- only the credential itself ever printed.
    # One line to stderr (never stdout, so it can't be captured/piped as if
    # it were the credential) makes exactly what was granted observable,
    # not just what the caller asked for.
    print(f"minted token principal={args.principal!r} scopes={sorted(set(args.scope))} namespaces={sorted(set(args.namespace))} boards={sorted(set(v.lower() for v in args.board))}",file=sys.stderr)
    print(token)
if __name__=="__main__": main()
