"""Internal Registry: separate SQLite authority with append-only journal/outbox.

It deliberately uses only stdlib.  Ledger publication is asynchronous and
idempotent through the outbox; this service has no foreign key or transaction
against the Ledger database.
"""
import base64,datetime,hashlib,hmac,json,os,re,secrets,sqlite3,sys,time,unicodedata,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from shared.canary_authority import CanaryAuthorityError,CanaryProofVerifier,FileNonceStore,canonical_bytes,decode_proof,decode_signature,load_r7_context
from shared.canary_identity import compatible_identity,require_canary_identity
from shared.registry_outbox import acknowledge_delivery

# Verified before a database path is resolved, a token is read, or a server
# (and therefore any request thread) can be created.
CANARY_IDENTITY=require_canary_identity()
R7_CONTEXT_SHA256=load_r7_context(os.environ.get("TOWNSQUARE_CONTEXT_MANIFEST","/run/config/canary-context-manifest.json"),CANARY_IDENTITY)

DB=Path(os.environ.get("REGISTRY_DB","/var/lib/registry/registry.db"))
TOKEN_FILE=os.environ.get("REGISTRY_TOKEN_FILE","/run/secrets/registry-api-credential")
LEDGER_AUDIT_TOKEN_FILE=os.environ.get("REGISTRY_LEDGER_AUDIT_TOKEN_FILE","/run/secrets/registry-audit-credential")
# Deliberately fixed Compose-internal origin/path; neither comes from a payload.
LEDGER_AUDIT_URL="http://ledger:8790/v1/native/registry-audit-events"
LEDGER_AUDIT_TIMEOUT_SECONDS=3
LEDGER_READINESS_URL="http://ledger:8790/health/ready"
LEDGER_READINESS_TOKEN_FILE=os.environ.get("LEDGER_READINESS_TOKEN_FILE","/run/secrets/registry_ledger_readiness_token")
CANARY_NONCE_DIRECTORY=os.environ.get("REGISTRY_CANARY_NONCE_DIRECTORY","/var/lib/registry/canary-nonces")
LOOKUP_TOKEN_SHA256_FILE=os.environ.get("REGISTRY_LOOKUP_TOKEN_SHA256_FILE","/run/secrets/registry-lookup-credential-sha256")
def connect():
 d=sqlite3.connect(DB,timeout=5,isolation_level=None); d.row_factory=sqlite3.Row; d.execute("PRAGMA foreign_keys=ON"); d.execute("PRAGMA journal_mode=WAL"); d.execute("PRAGMA synchronous=FULL"); d.execute("PRAGMA busy_timeout=5000")
 if d.execute("PRAGMA application_id").fetchone()[0] != 1414746695 or d.execute("PRAGMA user_version").fetchone()[0] != 6:
  d.close(); raise RuntimeError('Registry application_id/user_version mismatch')
 return d
SERVICE_ID='townsquare-registry-v0'; SCHEMA_VERSION=2; DATABASE_SCHEMA_VERSION=6; AUDIT_CONTRACT_VERSION='registry-ledger-audit-v1'
def compatible():
 if os.environ.get('REGISTRY_SERVICE_ID',SERVICE_ID)!=SERVICE_ID:return False
 if os.environ.get('REGISTRY_SCHEMA_HEAD',str(SCHEMA_VERSION))!=str(SCHEMA_VERSION):return False
 if os.environ.get('REGISTRY_AUDIT_CONTRACT_VERSION',AUDIT_CONTRACT_VERSION) != AUDIT_CONTRACT_VERSION:return False
 if os.environ.get('REGISTRY_LEDGER_SERVICE_ID','townsquare-ledger-v0')!='townsquare-ledger-v0':return False
 if os.environ.get('REGISTRY_LEDGER_SCHEMA_HEAD','14')!='14':return False
 if os.environ.get('REGISTRY_LEDGER_AUDIT_CONTRACT',AUDIT_CONTRACT_VERSION)!=AUDIT_CONTRACT_VERSION:return False
 try:
  d=connect(); row=d.execute('SELECT max(version) FROM registry_migrations').fetchone(); d.close(); return row and row[0]==DATABASE_SCHEMA_VERSION
 except Exception:return False
def token(): return Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
def operator_token(): return os.environ.get('REGISTRY_OPERATOR_TOKEN','')
def ledger_audit_token():
 value=Path(LEDGER_AUDIT_TOKEN_FILE).read_text(encoding="utf-8").strip()
 if not value: raise RuntimeError('registry audit credential is empty')
 return value
def ledger_readiness_token():
 value=Path(os.environ.get('REGISTRY_PEER_READINESS_TOKEN_FILE','/run/secrets/ledger_registry_readiness_token')).read_text(encoding='utf-8').strip()
 if not value: raise RuntimeError('registry readiness credential is empty')
 return value
def require_directional_tokens():
 inbound=ledger_readiness_token()
 outbound=Path(LEDGER_READINESS_TOKEN_FILE).read_text(encoding='utf-8').strip()
 if not outbound: raise RuntimeError('ledger readiness credential is empty')
 if hashlib.sha256(inbound.encode()).digest()==hashlib.sha256(outbound.encode()).digest():
  raise RuntimeError('directional readiness credentials must be distinct')
def peer_ready():
 """Live fixed-origin Ledger tuple exchange; never accepts an env self-claim."""
 import urllib.request
 try:
  require_directional_tokens()
  token=Path(LEDGER_READINESS_TOKEN_FILE).read_text(encoding='utf-8').strip()
  request=urllib.request.Request(LEDGER_READINESS_URL,headers={'Authorization':'Bearer '+token})
  with urllib.request.urlopen(request,timeout=LEDGER_AUDIT_TIMEOUT_SECONDS) as response: peer=json.load(response)
  compatible=peer.get('ok') is True and compatible_identity(peer,CANARY_IDENTITY) and peer.get('service_id')=='townsquare-ledger-v0' and peer.get('schema_version')==14 and peer.get('audit_contract_version')==AUDIT_CONTRACT_VERSION
  return {'compatible':compatible,'service_id':peer.get('service_id'),'schema_version':peer.get('schema_version'),**{name:peer.get(name) for name in CANARY_IDENTITY.as_dict()}}
 except Exception:return {'compatible':False,'detail':'ledger readiness exchange failed'}
def claim(db,owner):
 """Atomically lease one pending stable UUID; expired claims are recoverable."""
 now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()); until=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(time.time()+30))
 row=db.execute("SELECT event_id FROM audit_outbox WHERE delivered_utc IS NULL AND (lease_until IS NULL OR lease_until<?) ORDER BY event_id LIMIT 1",(now,)).fetchone()
 if not row:return None
 changed=db.execute("UPDATE audit_outbox SET lease_owner=?,lease_until=? WHERE event_id=? AND delivered_utc IS NULL AND (lease_until IS NULL OR lease_until<?)",(owner,until,row['event_id'],now)).rowcount
 return row['event_id'] if changed else None
def deliver_once():
 if not compatible() or not peer_ready().get('compatible'): return # retain queue on mismatch/failure
 import urllib.request
 d=connect()
 try:
  owner=str(uuid.uuid4())
  while (event_id:=claim(d,owner)):
   r=d.execute("SELECT j.* FROM journal j WHERE j.event_id=?",(event_id,)).fetchone()
   # Ledger accepts only this fixed three-field envelope. The Registry actor is
   # server-bound by Ledger's scoped credential, not by the original caller.
   data=json.dumps({"board":"BOARD-AUDIT-RECORD","actor":"registry","event_uuid":r['event_id']},sort_keys=True,separators=(',',':')).encode()
   try:
    req=urllib.request.Request(LEDGER_AUDIT_URL,data=data,headers={"Content-Type":"application/json","Authorization":"Bearer "+ledger_audit_token(),"Idempotency-Key":"registry-"+r['event_id']},method="POST")
    with urllib.request.urlopen(req,timeout=LEDGER_AUDIT_TIMEOUT_SECONDS) as response:
     if response.status//100!=2:raise RuntimeError(str(response.status))
    acknowledge_delivery(d,r['event_id'],owner)
   except Exception as e:
    # Never retain exception text: HTTP libraries can include request details.
    d.execute("UPDATE audit_outbox SET attempts=attempts+1,last_error=?,lease_owner=NULL,lease_until=NULL WHERE event_id=? AND lease_owner=?",(type(e).__name__[:80],r['event_id'],owner))
 finally:d.close()
def require_manual_delivery_mode():
 if os.environ.get('REGISTRY_AUDIT_DELIVERY_MODE')!='manual':
  raise RuntimeError('REGISTRY_AUDIT_DELIVERY_MODE must be exactly manual for this canary')
def identity_metadata():
 return {'service_id':SERVICE_ID,'schema_version':SCHEMA_VERSION,**CANARY_IDENTITY.as_dict()}
def require_canary_test_proof(headers,body,action,object_id):
 public_key='/run/config/canary-test-authority.pub'
 verifier=CanaryProofVerifier(CANARY_IDENTITY,FileNonceStore(CANARY_NONCE_DIRECTORY),public_key,r7_context_sha256=R7_CONTEXT_SHA256)
 verifier.verify_and_consume(
  decode_proof(headers.get('X-Canary-Test-Proof')),decode_signature(headers.get('X-Canary-Test-Signature')),
  audience='townsquare-canary-registry-api',service_id=SERVICE_ID,action=action,object_id=object_id,
  context_sha256=hashlib.sha256(canonical_bytes(body)).hexdigest(),
 )
_PROVIDER=re.compile(r'^[a-z0-9._-]{1,64}$')
_SHA256=re.compile(r'^[0-9a-f]{64}$')
_TOKEN_RE=re.compile(r'^[A-Za-z0-9_-]{43}$')
_SIGNATURE_RE=re.compile(r'^[A-Za-z0-9_-]{86}$')
_UUID4_RE=re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')
_DECIMAL_RE=re.compile(r'^[1-9][0-9]*$')
_TIMESTAMP_RE=re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')
_KEY_ID_RE=re.compile(r'^ed25519:[0-9a-f]{64}$')
_Q=2**255-19;_L=2**252+27742317777372353535851937790883648493;_D=(-121665*pow(121666,_Q-2,_Q))%_Q;_I=pow(2,(_Q-1)//4,_Q)
def _xrecover(y,sign):
 x=pow((y*y-1)*pow((_D*y*y+1)%_Q,_Q-2,_Q)%_Q,(_Q+3)//8,_Q)
 if (x*x-((y*y-1)*pow((_D*y*y+1)%_Q,_Q-2,_Q)))%_Q:x=x*_I%_Q
 if x&1!=sign:x=_Q-x
 return x if (x*x*(_D*y*y+1)-y*y+1)%_Q==0 else None
def _point(raw):
 if len(raw)!=32:return None
 value=int.from_bytes(raw,'little');sign=value>>255;y=value&((1<<255)-1)
 if y>=_Q:return None
 x=_xrecover(y,sign)
 if x is None or (x==0 and sign):return None
 return (x,y,1,x*y%_Q)
def _point_add(p,q):
 x1,y1,z1,t1=p;x2,y2,z2,t2=q
 a=(y1-x1)*(y2-x2)%_Q;b=(y1+x1)*(y2+x2)%_Q;c=2*_D*t1*t2%_Q;d=2*z1*z2%_Q;e=b-a;f=d-c;g=d+c;h=b+a
 return (e*f%_Q,g*h%_Q,f*g%_Q,e*h%_Q)
def _point_mul(p,n):
 q=(0,1,1,0)
 while n:
  if n&1:q=_point_add(q,p)
  p=_point_add(p,p);n>>=1
 return q
_BY=4*pow(5,_Q-2,_Q)%_Q;_BX=_xrecover(_BY,0);_BASE=(_BX,_BY,1,_BX*_BY%_Q)
def _point_equal(a,b):return a[0]*b[2]%_Q==b[0]*a[2]%_Q and a[1]*b[2]%_Q==b[1]*a[2]%_Q
def _ed25519_verify(public_key,signature,message):
 if len(public_key)!=32 or len(signature)!=64:return False
 a=_point(public_key);r=_point(signature[:32]);s=int.from_bytes(signature[32:],'little')
 if a is None or r is None or s>=_L or _point_equal(a,(0,1,1,0)) or not _point_equal(_point_mul(a,_L),(0,1,1,0)):return False
 h=int.from_bytes(hashlib.sha512(signature[:32]+public_key+message).digest(),'little')%_L
 return _point_equal(_point_mul(_BASE,s),_point_add(r,_point_mul(a,h)))
def _utc(): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def _utc_at(epoch): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(epoch))
def _canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def _sha256_text(value): return hashlib.sha256(value.encode('utf-8')).hexdigest()
def _nonempty_string(value,limit=512): return isinstance(value,str) and 0<len(value)<=limit and unicodedata.is_normalized('NFC',value) and all(not 0xd800<=ord(char)<=0xdfff for char in value)
def _provider_session_id(value): return _nonempty_string(value) and all(0x20<=ord(char)<=0x7e for char in value)
def _optional_string(value,limit=512): return value is None or _nonempty_string(value,limit)
def _decode_unpadded(value,size,pattern):
 if not isinstance(value,str) or not pattern.fullmatch(value):return None
 try:raw=base64.b64decode(value+'='*((4-len(value)%4)%4),altchars=b'-_',validate=True)
 except Exception:return None
 return raw if len(raw)==size and base64.urlsafe_b64encode(raw).decode().rstrip('=')==value else None
def _single_header(headers,name):
 values=headers.get_all(name) if hasattr(headers,'get_all') else [value for key,value in headers.items() if key.lower()==name.lower()]
 if values is None:values=[]
 return values[0] if len(values)==1 else None
def _authorization(headers):
 value=_single_header(headers,'Authorization')
 if not isinstance(value,str):return '',''
 scheme,separator,credential=value.partition(' ')
 if separator!=' ' or not credential or ' ' in credential or '\t' in value:return '',''
 return scheme,credential
def _operator_authorized(headers):
 configured=operator_token();provided=_single_header(headers,'X-Registry-Operator-Token') or ''
 return bool(configured) and hmac.compare_digest(provided.encode(),configured.encode())
def _lookup_authorized(headers):
 scheme,credential=_authorization(headers)
 if scheme!='Bearer':return False
 try:verifier=Path(LOOKUP_TOKEN_SHA256_FILE).read_text(encoding='ascii').strip()
 except OSError:return False
 return bool(_SHA256.fullmatch(verifier)) and hmac.compare_digest(_sha256_text(credential),verifier)
def _legacy_authorized(headers):
 scheme,credential=_authorization(headers)
 if scheme!='Bearer':return False
 try:configured=token()
 except OSError:return False
 return bool(configured) and hmac.compare_digest(credential.encode(),configured.encode())
def _redacted_session(row):
 return {name:row[name] for name in ('session_uuid','agent_id','provider','seat_or_host','runtime','model','status','started_utc','last_seen_utc','ended_utc','work_ref','revision','updated_utc')}
def _redacted_history(row):
 body=json.loads(row['body_json']);body.pop('provider_session_id',None);body.pop('session_public_key_b64url',None)
 return {'seq':row['seq'],'event_id':row['event_id'],'session_uuid':row['session_uuid'],'agent_id':row['agent_id'],'action':row['action'],'body':body,'committed_utc':row['committed_utc']}
def _session_outbox_body(row,action,when):return {'kind':'session_lifecycle','session_uuid':row['session_uuid'],'agent_id':row['agent_id'],'provider':row['provider'],'status':row['status'],'work_ref':row['work_ref'],'action':action,'committed_utc':when}
def _enrollment_request_valid(body):
 return isinstance(body,dict) and set(body)=={'agent_id','provider','seat_or_host'} and _nonempty_string(body.get('agent_id'),128) and isinstance(body.get('provider'),str) and bool(_PROVIDER.fullmatch(body['provider'])) and _nonempty_string(body.get('seat_or_host'),512)
def _session_key(value,expected_epoch=None):
 if not isinstance(value,dict) or set(value)!={'alg','key_id','key_epoch','public_key_b64url'} or value.get('alg')!='Ed25519' or type(value.get('key_epoch')) is not int or value['key_epoch']<1:return None
 raw=_decode_unpadded(value.get('public_key_b64url'),32,_TOKEN_RE)
 point=_point(raw) if raw is not None else None
 if point is None or _point_equal(point,(0,1,1,0)) or not _point_equal(_point_mul(point,_L),(0,1,1,0)):return None
 key_id='ed25519:'+hashlib.sha256(raw).hexdigest()
 if value.get('key_id')!=key_id or (expected_epoch is not None and value['key_epoch']!=expected_epoch):return None
 return raw,key_id,value['key_epoch']
def _registration_body_valid(body):
 required={'agent_id','provider','provider_session_id','initial_status','seat_or_host','session_key'};optional={'runtime','model','work_ref'}
 if not isinstance(body,dict) or not required<=set(body) or not set(body)<=required|optional:return False
 return _nonempty_string(body.get('agent_id'),128) and isinstance(body.get('provider'),str) and bool(_PROVIDER.fullmatch(body['provider'])) and _provider_session_id(body.get('provider_session_id')) and body.get('initial_status') in ('STARTING','ACTIVE') and _nonempty_string(body.get('seat_or_host')) and all(_optional_string(body.get(name)) for name in optional) and _session_key(body.get('session_key'),1) is not None
def _session_request_valid(body,action):
 if action=='register':return _registration_body_valid(body)
 if not isinstance(body,dict):return False
 if action=='heartbeat':return set(body)=={'status'} and body.get('status') in ('ACTIVE','IDLE')
 if action=='terminate':return body=={'terminal_status':'ENDED'}
 if action=='credential_rotate':return set(body)=={'new_key'} and _session_key(body.get('new_key')) is not None
 return False
def _enrollment_token(headers):
 scheme,value=_authorization(headers)
 return value if scheme=='SessionEnrollment' and _decode_unpadded(value,32,_TOKEN_RE) is not None else None
def create_session_enrollment(db,body):
 if not _enrollment_request_valid(body):return 400,{'detail':'invalid session enrollment request'}
 db.execute('BEGIN IMMEDIATE')
 try:
  agent=db.execute('SELECT active FROM agents WHERE agent_id=?',(body['agent_id'],)).fetchone()
  if not agent or not agent['active']:db.rollback();return 409,{'detail':'session enrollment conflict','code':'SESSION_ENROLLMENT_CONFLICT'}
  grant_id=str(uuid.uuid4());value=base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip('=');now=_utc();expires=_utc_at(time.time()+600)
  db.execute('INSERT INTO session_enrollments(grant_id,token_sha256,agent_id,provider,seat_or_host,created_utc,expires_utc) VALUES(?,?,?,?,?,?,?)',(grant_id,_sha256_text(value),body['agent_id'],body['provider'],body['seat_or_host'],now,expires));db.commit()
  return 201,{'grant_id':grant_id,'enrollment_token':value,'agent_id':body['agent_id'],'provider':body['provider'],'seat_or_host':body['seat_or_host'],'expires_utc':expires}
 except Exception:db.rollback();raise
def _registration_conflict(db):db.rollback();return 409,{'detail':'session registration conflict','code':'SESSION_REGISTRATION_CONFLICT'}
def register_enrolled_session(db,enrollment_token,key,body):
 if not isinstance(key,str) or not _UUID4_RE.fullmatch(key):return 400,{'detail':'invalid session idempotency key','code':'SESSION_IDEMPOTENCY_KEY_INVALID'}
 if _decode_unpadded(enrollment_token,32,_TOKEN_RE) is None:return 401,{'detail':'unauthorized','code':'SESSION_ENROLLMENT_UNAUTHORIZED'}
 if not _registration_body_valid(body):return 400,{'detail':'invalid session registration request'}
 token_sha256=_sha256_text(enrollment_token);request_sha256=hashlib.sha256(_canonical(body).encode()).hexdigest();public,key_id,epoch=_session_key(body['session_key'],1)
 db.execute('BEGIN IMMEDIATE')
 try:
  enrollment=db.execute('SELECT * FROM session_enrollments WHERE token_sha256=?',(token_sha256,)).fetchone()
  if not enrollment:db.rollback();return 401,{'detail':'unauthorized','code':'SESSION_ENROLLMENT_UNAUTHORIZED'}
  replay=db.execute('SELECT * FROM session_registration_replays WHERE grant_id=? OR idempotency_key=?',(enrollment['grant_id'],key)).fetchone()
  if replay:
   exact=all(hmac.compare_digest(replay[name],value) for name,value in (('grant_id',enrollment['grant_id']),('token_sha256',token_sha256),('idempotency_key',key),('canonical_request_sha256',request_sha256)))
   if exact:db.rollback();return replay['response_status'],json.loads(replay['response_body_jcs'])
   return _registration_conflict(db)
  if enrollment['consumed_utc'] is not None:return _registration_conflict(db)
  if enrollment['expires_utc']<=_utc():db.rollback();return 409,{'detail':'session enrollment expired','code':'SESSION_ENROLLMENT_EXPIRED'}
  if any(body[name]!=enrollment[name] for name in ('agent_id','provider','seat_or_host')):return _registration_conflict(db)
  agent=db.execute('SELECT active FROM agents WHERE agent_id=?',(body['agent_id'],)).fetchone()
  if not agent or not agent['active'] or db.execute('SELECT 1 FROM sessions WHERE provider=? AND provider_session_id=?',(body['provider'],body['provider_session_id'])).fetchone():return _registration_conflict(db)
  now=_utc();session_uuid=str(uuid.uuid4());status=body['initial_status']
  db.execute('INSERT INTO sessions(session_uuid,agent_id,provider,provider_session_id,seat_or_host,runtime,model,status,started_utc,last_seen_utc,ended_utc,work_ref,revision,updated_utc,credential_scheme,session_key_id,session_key_epoch,session_public_key_b64url) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(session_uuid,body['agent_id'],body['provider'],body['provider_session_id'],body['seat_or_host'],body.get('runtime'),body.get('model'),status,now,now,None,body.get('work_ref'),1,now,'ed25519-v1',key_id,epoch,body['session_key']['public_key_b64url']))
  row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone();event_id=str(uuid.uuid4());audit_id=str(uuid.uuid4())
  db.execute('INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?,?)',(event_id,session_uuid,row['agent_id'],'register',_canonical(_redacted_session(row)),now));db.execute('INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)',(audit_id,row['agent_id'],'session_register',_canonical(_session_outbox_body(row,'register',now)),now));db.execute('INSERT INTO audit_outbox(event_id) VALUES(?)',(audit_id,))
  response={'event_id':event_id,**_redacted_session(row),'action':'register'};retain=_utc_at(time.time()+90*86400)
  db.execute('UPDATE session_enrollments SET consumed_utc=?,session_uuid=? WHERE grant_id=?',(now,session_uuid,enrollment['grant_id']));db.execute('INSERT INTO session_registration_replays VALUES(?,?,?,?,?,?,?,?,?)',(enrollment['grant_id'],token_sha256,key,request_sha256,_canonical(response),201,session_uuid,now,retain));db.commit();return 201,response
 except sqlite3.IntegrityError:return _registration_conflict(db)
 except Exception:db.rollback();raise
def _signed_request(headers,method,path,session_uuid,body):
 scheme,encoded=_authorization(headers);signature=_decode_unpadded(encoded,64,_SIGNATURE_RE) if scheme=='SessionSignature' else None
 names=('X-Session-Key-Id','X-Session-Key-Epoch','X-Session-Revision','X-Session-Timestamp','X-Session-Nonce');values={name:_single_header(headers,name) for name in names};idem=_single_header(headers,'Idempotency-Key')
 if signature is None or not _UUID4_RE.fullmatch(session_uuid) or not _KEY_ID_RE.fullmatch(values['X-Session-Key-Id'] or '') or not _DECIMAL_RE.fullmatch(values['X-Session-Key-Epoch'] or '') or not _DECIMAL_RE.fullmatch(values['X-Session-Revision'] or '') or not _TIMESTAMP_RE.fullmatch(values['X-Session-Timestamp'] or '') or not _UUID4_RE.fullmatch(values['X-Session-Nonce'] or ''):return None
 if method=='GET':
  if idem is not None:return None
  idem=''
 elif not _nonempty_string(idem,128) or any(ord(char)<0x21 or ord(char)>0x7e for char in idem):return None
 try:stamp=datetime.datetime.strptime(values['X-Session-Timestamp'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()
 except ValueError:return None
 body_sha256=hashlib.sha256(_canonical(body).encode()).hexdigest();fields=('townsquare.session-owning-request.v1',method,path,session_uuid,idem,body_sha256,'ed25519-v1',values['X-Session-Key-Id'],values['X-Session-Key-Epoch'],values['X-Session-Revision'],values['X-Session-Timestamp'],values['X-Session-Nonce']);payload='\0'.join(fields).encode()
 return {'signature':signature,'signature_sha256':hashlib.sha256(signature).hexdigest(),'request_sha256':hashlib.sha256(payload).hexdigest(),'payload':payload,'key_id':values['X-Session-Key-Id'],'key_epoch':int(values['X-Session-Key-Epoch']),'revision':int(values['X-Session-Revision']),'timestamp':values['X-Session-Timestamp'],'timestamp_epoch':stamp,'nonce':values['X-Session-Nonce'],'idempotency_key':idem}
def _signed_error(db,code,status=401,detail='unauthorized'):db.rollback();return status,{'detail':detail,'code':code}
def owning_session_request(db,headers,method,path,session_uuid,body,action):
 if method=='GET':body=None
 elif not _session_request_valid(body,action):return 400,{'detail':'invalid session lifecycle request'}
 signed=_signed_request(headers,method,path,session_uuid,body)
 if signed is None:return 401,{'detail':'unauthorized','code':'SESSION_SIGNATURE_INVALID'}
 db.execute('BEGIN IMMEDIATE')
 try:
  replay=db.execute('SELECT * FROM session_owning_replays WHERE session_uuid=? AND nonce=?',(session_uuid,signed['nonce'])).fetchone()
  if replay:
   exact=replay['is_mutation'] and replay['request_sha256']==signed['request_sha256'] and replay['signature_sha256']==signed['signature_sha256'] and (replay['idempotency_key'] or '')==signed['idempotency_key'] and replay['action']==action
   if exact:db.rollback();return replay['response_status'],json.loads(replay['response_json'])
   if action=='credential_rotate' and replay['action']=='credential_rotate':return _signed_error(db,'SESSION_ROTATION_CONFLICT',409,'session key rotation conflict')
   return _signed_error(db,'SESSION_NONCE_CONFLICT',409,'session nonce conflict')
  row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
  if not row:return _signed_error(db,'SESSION_SIGNATURE_INVALID')
  if row['credential_scheme']!='ed25519-v1':return _signed_error(db,'SESSION_LEGACY_CREDENTIAL_RETIRED',409,'legacy session credential retired')
  if signed['key_id']!=row['session_key_id'] or signed['key_epoch']!=row['session_key_epoch']:return _signed_error(db,'SESSION_SIGNATURE_INVALID')
  if signed['revision']!=row['revision']:return _signed_error(db,'SESSION_REVISION_CONFLICT',409,'session revision conflict')
  if abs(time.time()-signed['timestamp_epoch'])>120:return _signed_error(db,'SESSION_SIGNATURE_STALE')
  public=_decode_unpadded(row['session_public_key_b64url'],32,_TOKEN_RE)
  if public is None or not _ed25519_verify(public,signed['signature'],signed['payload']):return _signed_error(db,'SESSION_SIGNATURE_INVALID')
  now=_utc()
  if method=='GET':
   if action=='history':response={'session_uuid':session_uuid,'events':[_redacted_history(event) for event in db.execute('SELECT * FROM session_journal WHERE session_uuid=? ORDER BY seq',(session_uuid,))]}
   else:response=_redacted_session(row)
   db.execute('INSERT INTO session_owning_replays VALUES(?,?,?,?,?,?,?,?,?,?,?)',(session_uuid,signed['nonce'],signed['request_sha256'],signed['signature_sha256'],signed['timestamp'],None,200,_canonical(response),_utc_at(time.time()+600),0,action));db.commit();return 200,response
  if row['status'] in ('ENDED','LOST'):return _signed_error(db,'SESSION_REVISION_CONFLICT',409,'session lifecycle conflict')
  journal_action=action
  if action=='heartbeat':
   wanted=body['status'];allowed=(row['status']=='STARTING' and wanted=='ACTIVE') or (row['status']=='ACTIVE' and wanted in ('ACTIVE','IDLE')) or (row['status']=='IDLE' and wanted in ('ACTIVE','IDLE'))
   if not allowed:return _signed_error(db,'SESSION_REVISION_CONFLICT',409,'session lifecycle conflict')
   db.execute('UPDATE sessions SET status=?,last_seen_utc=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(wanted,now,now,session_uuid))
  elif action=='terminate':
   db.execute('UPDATE sessions SET status="ENDED",last_seen_utc=?,ended_utc=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(now,now,now,session_uuid));terminal_retain=_utc_at(time.time()+30*86400);db.execute('UPDATE session_registration_replays SET retain_until_utc=CASE WHEN retain_until_utc>? THEN retain_until_utc ELSE ? END WHERE session_uuid=?',(terminal_retain,terminal_retain,session_uuid))
  else:
   parsed=_session_key(body['new_key'],row['session_key_epoch']+1)
   if parsed is None or parsed[1]==row['session_key_id']:return _signed_error(db,'SESSION_ROTATION_CONFLICT',409,'session key rotation conflict')
   _,new_id,new_epoch=parsed;db.execute('UPDATE sessions SET session_key_id=?,session_key_epoch=?,session_public_key_b64url=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(new_id,new_epoch,body['new_key']['public_key_b64url'],now,session_uuid));journal_action='credential_rotate'
  updated=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone();event_id=str(uuid.uuid4());audit_id=str(uuid.uuid4())
  db.execute('INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?,?)',(event_id,session_uuid,updated['agent_id'],journal_action,_canonical(_redacted_session(updated)),now));db.execute('INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)',(audit_id,updated['agent_id'],'session_'+journal_action,_canonical(_session_outbox_body(updated,journal_action,now)),now));db.execute('INSERT INTO audit_outbox(event_id) VALUES(?)',(audit_id,))
  response={'event_id':event_id,**_redacted_session(updated),'action':journal_action}
  if action=='credential_rotate':db.execute('INSERT INTO session_key_rotations VALUES(?,?,?,?,?,?,?,?)',(session_uuid,signed['nonce'],row['session_key_id'],row['session_key_epoch'],updated['session_key_id'],updated['session_key_epoch'],event_id,now))
  db.execute('INSERT INTO session_owning_replays VALUES(?,?,?,?,?,?,?,?,?,?,?)',(session_uuid,signed['nonce'],signed['request_sha256'],signed['signature_sha256'],signed['timestamp'],signed['idempotency_key'],200,_canonical(response),'9999-12-31T23:59:59Z',1,action));db.commit();return 200,response
 except Exception:db.rollback();raise
def cleanup_session_artifacts(db,now=None):
 now=now or _utc();cutoff=_utc_at(datetime.datetime.strptime(now,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp()-86400);db.execute('BEGIN IMMEDIATE')
 try:
  expired=[row[0] for row in db.execute('SELECT grant_id FROM session_enrollments WHERE consumed_utc IS NULL AND expires_utc<=? ORDER BY grant_id LIMIT 500',(cutoff,))];db.executemany('DELETE FROM session_enrollments WHERE grant_id=?',((value,) for value in expired))
  remaining=500-len(expired);retained=[row[0] for row in db.execute('SELECT r.grant_id FROM session_registration_replays r JOIN sessions s ON s.session_uuid=r.session_uuid WHERE r.retain_until_utc<=? AND s.status IN ("ENDED","LOST") ORDER BY r.grant_id LIMIT ?',(now,remaining))];db.executemany('DELETE FROM session_registration_replays WHERE grant_id=?',((value,) for value in retained));db.executemany('DELETE FROM session_enrollments WHERE grant_id=?',((value,) for value in retained));db.execute('DELETE FROM session_owning_replays WHERE rowid IN (SELECT rowid FROM session_owning_replays WHERE is_mutation=0 AND expires_utc<=? ORDER BY rowid LIMIT 500)',(now,));db.commit();return len(expired)+len(retained)
 except Exception:db.rollback();raise
def mutate_session(db,principal,key,body,action):
 """Preserved S1 internal/admin lifecycle; it never creates an owning credential."""
 valid=isinstance(body,dict) and ((action=='register' and {'agent_id','provider','provider_session_id','initial_status'}<=set(body)) or (action=='heartbeat' and body.get('status') in ('ACTIVE','IDLE')) or (action=='terminate' and body.get('terminal_status') in ('ENDED','LOST')))
 if not key or not valid or (action=='register' and (not _provider_session_id(body.get('provider_session_id')) or body.get('initial_status') not in ('STARTING','ACTIVE'))):return 400,{'detail':'invalid session lifecycle request'}
 request_hash=hashlib.sha256(_canonical(body).encode()).hexdigest();db.execute('BEGIN IMMEDIATE');old=db.execute('SELECT * FROM requests WHERE principal=? AND idem_key=?',(principal,key)).fetchone()
 if old:
  if old['request_hash']!=request_hash:db.rollback();return 409,{'detail':'idempotency key reused with different request'}
  db.rollback();return old['response_status'],json.loads(old['response_json'])
 try:
  now=_utc()
  if action=='register':
   agent=db.execute('SELECT active FROM agents WHERE agent_id=?',(body['agent_id'],)).fetchone()
   if not agent or not agent['active'] or db.execute('SELECT 1 FROM sessions WHERE provider=? AND provider_session_id=?',(body['provider'],body['provider_session_id'])).fetchone():db.rollback();return 409,{'detail':'session registration conflict'}
   session_uuid=str(uuid.uuid4());db.execute('INSERT INTO sessions(session_uuid,agent_id,provider,provider_session_id,seat_or_host,runtime,model,status,started_utc,last_seen_utc,ended_utc,work_ref,revision,updated_utc,credential_scheme) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(session_uuid,body['agent_id'],body['provider'],body['provider_session_id'],body.get('seat_or_host'),body.get('runtime'),body.get('model'),body['initial_status'],now,now,None,body.get('work_ref'),1,now,'retired'))
  else:
   session_uuid=body.get('session_uuid');row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
   if not row or row['status'] in ('ENDED','LOST'):db.rollback();return 409,{'detail':'session lifecycle conflict'}
   if action=='heartbeat':
    wanted=body['status'];allowed=(row['status']=='STARTING' and wanted=='ACTIVE') or (row['status']=='ACTIVE' and wanted in ('ACTIVE','IDLE')) or (row['status']=='IDLE' and wanted in ('ACTIVE','IDLE'))
    if not allowed:db.rollback();return 409,{'detail':'session lifecycle conflict'}
    db.execute('UPDATE sessions SET status=?,last_seen_utc=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(wanted,now,now,session_uuid))
   else:db.execute('UPDATE sessions SET status=?,last_seen_utc=?,ended_utc=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(body['terminal_status'],now,now,now,session_uuid));action='mark_lost' if body['terminal_status']=='LOST' else 'terminate'
  row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone();event_id=str(uuid.uuid4());audit_id=str(uuid.uuid4());private=dict(_redacted_session(row));private['provider_session_id']=row['provider_session_id'];db.execute('INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?,?)',(event_id,session_uuid,row['agent_id'],action,_canonical(private),now));db.execute('INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)',(audit_id,row['agent_id'],'session_'+action,_canonical(_session_outbox_body(row,action,now)),now));db.execute('INSERT INTO audit_outbox(event_id) VALUES(?)',(audit_id,));response={'event_id':event_id,**_redacted_session(row),'action':action};status=201 if action=='register' else 200;db.execute('INSERT INTO requests(principal,idem_key,request_hash,response_json,response_status) VALUES(?,?,?,?,?)',(principal,key,request_hash,_canonical(response),status));db.commit();return status,response
 except Exception:db.rollback();raise
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,status,value,no_store=False):
  data=_canonical(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store') if no_store else None;self.end_headers();self.wfile.write(data)
 def read_json(self):
  try:
   size=int(_single_header(self.headers,'Content-Length') or '0')
   if size<1 or size>65536:raise ValueError()
   text=self.rfile.read(size).decode('utf-8','strict')
   if not unicodedata.is_normalized('NFC',text):raise ValueError()
   def pairs(values):
    result={}
    for key,value in values:
     if key in result:raise ValueError()
     result[key]=value
    return result
   return json.loads(text,object_pairs_hook=pairs,parse_float=lambda value:(_ for _ in ()).throw(ValueError()),parse_constant=lambda value:(_ for _ in ()).throw(ValueError()))
  except Exception:return None
 def do_GET(self):
  if self.path=="/health/live":return self.reply(200,{"ok":True})
  if self.path=="/health/ready":
   try:
    require_directional_tokens()
    if self.headers.get('Authorization')!='Bearer '+ledger_readiness_token(): return self.reply(401,{"ok":False,"detail":"readiness authorization required"})
   except (OSError,RuntimeError):return self.reply(503,{"ok":False,"detail":"readiness credential unavailable"})
   try:
    d=connect(); version=d.execute("SELECT max(version) FROM registry_migrations").fetchone()[0]; pending=d.execute("SELECT count(*) FROM audit_outbox WHERE delivered_utc IS NULL").fetchone()[0]; failed=d.execute("SELECT count(*) FROM audit_outbox WHERE delivered_utc IS NULL AND last_error IS NOT NULL").fetchone()[0];d.close();
    tuple={"registry_service":SERVICE_ID,"registry_schema":SCHEMA_VERSION,"ledger_service":"townsquare-ledger-v0","ledger_schema":14,"audit_contract":AUDIT_CONTRACT_VERSION}
    expected_peer={"service_id":"townsquare-ledger-v0","schema_version":14,**CANARY_IDENTITY.as_dict()}
    base={**identity_metadata(),"database_schema_version":version,"compatibility":tuple,"compatible_peer":expected_peer}
    if not compatible(): return self.reply(503,{"ok":False,**base,"detail":"incompatible schema/audit contract"})
    if failed:return self.reply(503,{"ok":False,**base,"pending_audit":pending,"delivery_failures":failed,"detail":"registry audit delivery degraded"})
    return self.reply(200,{"ok":True,**base,"pending_audit":pending,"delivery_failures":0})
   except Exception:return self.reply(503,{"ok":False,"detail":"registry readiness unavailable"})
  if self.path=="/health/internal/ready":
   if self.client_address[0] not in ('127.0.0.1','::1'): return self.reply(404,{"detail":"not found"})
   if compatible() and peer_ready().get('compatible'): return self.reply(200,{"ok":True})
   return self.reply(503,{"ok":False})
  session_match=re.fullmatch(r'/v1/sessions/([0-9a-f-]{36})(?:/(history|provider-locator))?',self.path)
  if session_match:
   session_uuid,view=session_match.groups(); sensitive=view=='provider-locator'
   if not _UUID4_RE.fullmatch(session_uuid):return self.reply(404,{'detail':'not found'},True)
   legacy=_legacy_authorized(self.headers);lookup=_lookup_authorized(self.headers);scheme,_=_authorization(self.headers);signed=scheme=='SessionSignature'
   if sensitive and (not legacy or not _operator_authorized(self.headers)): return self.reply(404,{'detail':'not found'},True)
   if view=='history' and not signed and not legacy:return self.reply(401,{'detail':'unauthorized','code':'SESSION_SIGNATURE_INVALID'},True)
   if not sensitive and not (legacy or lookup or signed):return self.reply(401,{'detail':'unauthorized'},True)
   d=None
   try:
    d=connect()
    if signed:
     status,out=owning_session_request(d,self.headers,'GET',self.path,session_uuid,None,'history' if view=='history' else 'get')
     return self.reply(status,out,True)
    row=d.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
    if not row:return self.reply(404,{'detail':'not found'},sensitive)
    if sensitive:return self.reply(200,{'session_uuid':row['session_uuid'],'provider':row['provider'],'provider_session_id':row['provider_session_id']},True)
    if view=='history':return self.reply(200,{'session_uuid':session_uuid,'events':[_redacted_history(event) for event in d.execute('SELECT * FROM session_journal WHERE session_uuid=? ORDER BY seq',(session_uuid,))]},True)
    return self.reply(200,_redacted_session(row),True)
   except Exception:return self.reply(503,{'detail':'session lookup unavailable'},sensitive)
   finally:
    if d:d.close()
  self.reply(404,{"detail":"not found"},self.path.startswith('/v1/sessions/'))
 def do_POST(self):
  session_match=re.fullmatch(r'/v1/sessions/([0-9a-f-]{36})/(heartbeat|terminate)',self.path)
  rotation_match=re.fullmatch(r'/v1/sessions/([0-9a-f-]{36})/credential-rotations',self.path)
  enrollment_path=self.path=='/v1/session-enrollments'
  if self.path!="/v1/agents" and not session_match and not rotation_match and self.path!='/v1/sessions' and not enrollment_path:return self.reply(404,{"detail":"not found"},self.path.startswith('/v1/session'))
  if enrollment_path and (self.client_address[0] not in ('127.0.0.1','::1') or not _operator_authorized(self.headers)):
   return self.reply(404,{"detail":"not found"},True)
  key=_single_header(self.headers,'Idempotency-Key')
  if self.path=='/v1/sessions':
   enrollment_token=_enrollment_token(self.headers)
   if enrollment_token is None:return self.reply(401,{'detail':'unauthorized','code':'SESSION_ENROLLMENT_UNAUTHORIZED'},True)
   if not isinstance(key,str) or not _UUID4_RE.fullmatch(key):return self.reply(400,{'detail':'invalid session idempotency key','code':'SESSION_IDEMPOTENCY_KEY_INVALID'},True)
  elif not enrollment_path and not key:return self.reply(400,{"detail":"Idempotency-Key required"},self.path.startswith('/v1/session'))
  body=self.read_json()
  if body is None:return self.reply(400,{"detail":"invalid json"},self.path.startswith('/v1/session'))
  if enrollment_path:
   d=connect()
   try:
    status,out=create_session_enrollment(d,body);return self.reply(status,out,True)
   except Exception:return self.reply(503,{"detail":"session enrollment unavailable"},True)
   finally:d.close()
  if self.path=='/v1/sessions':
   d=connect()
   try:
    status,out=register_enrolled_session(d,enrollment_token,key,body);return self.reply(status,out,True)
   except Exception:return self.reply(503,{"detail":"session lifecycle unavailable"},True)
   finally:d.close()
  if session_match:
   session_uuid,action=session_match.groups()
   if not _UUID4_RE.fullmatch(session_uuid):return self.reply(404,{'detail':'not found'},True)
   d=connect()
   try:
    status,out=owning_session_request(d,self.headers,'POST',self.path,session_uuid,body,action);return self.reply(status,out,True)
   except Exception:return self.reply(503,{"detail":"session lifecycle unavailable"},True)
   finally:d.close()
  if rotation_match:
   session_uuid=rotation_match.group(1)
   if not _UUID4_RE.fullmatch(session_uuid):return self.reply(404,{'detail':'not found'},True)
   d=connect()
   try:
    status,out=owning_session_request(d,self.headers,'POST',self.path,session_uuid,body,'credential_rotate');return self.reply(status,out,True)
   except Exception:return self.reply(503,{"detail":"session credential rotation unavailable"},True)
   finally:d.close()
  if not _legacy_authorized(self.headers):return self.reply(401,{"detail":"unauthorized"})
  principal=self.headers.get("X-Registry-Principal")
  if not principal:return self.reply(400,{"detail":"X-Registry-Principal required"})
  agent=body.get("agent_id"); action=body.get("action")
  if not isinstance(agent,str) or action not in ("register","retire"):return self.reply(400,{"detail":"agent_id and action required"})
  try:require_canary_test_proof(self.headers,body,'registry:'+action,agent)
  except CanaryAuthorityError as e:return self.reply(403,{"detail":str(e)})
  canonical=json.dumps(body,sort_keys=True,separators=(',',':')); h=hashlib.sha256(canonical.encode()).hexdigest();d=connect()
  try:
   d.execute("BEGIN IMMEDIATE"); old=d.execute("SELECT * FROM requests WHERE principal=? AND idem_key=?",(principal,key)).fetchone()
   if old:
    if old['request_hash']!=h: d.rollback();return self.reply(409,{"detail":"idempotency key reused with different request"})
    d.rollback();return self.reply(200,json.loads(old['response_json']))
   current=d.execute("SELECT revision FROM agents WHERE agent_id=?",(agent,)).fetchone(); rev=(current['revision'] if current else 0)+1; event=str(uuid.uuid4());now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
   d.execute("INSERT INTO agents VALUES(?,?,?,?,?) ON CONFLICT(agent_id) DO UPDATE SET body_json=excluded.body_json,revision=excluded.revision,active=excluded.active,updated_utc=excluded.updated_utc",(agent,canonical,rev,int(action=="register"),now))
   d.execute("INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)",(event,agent,action,canonical,now));d.execute("INSERT INTO audit_outbox(event_id) VALUES(?)",(event,)); out={"event_id":event,"agent_id":agent,"revision":rev,"action":action};d.execute("INSERT INTO requests(principal,idem_key,request_hash,response_json) VALUES(?,?,?,?)",(principal,key,h,json.dumps(out,sort_keys=True)));d.commit();self.reply(201,out)
  except Exception as e:d.rollback();self.reply(503,{"detail":str(e)})
  finally:d.close()
def main():
 require_manual_delivery_mode()
 if not compatible(): raise SystemExit('Registry schema/audit contract incompatible; run registry-migrate')
 if sys.argv[1:]==['--deliver-audit-once']:
  deliver_once();return
 if sys.argv[1:]: raise SystemExit('usage: app.py [--deliver-audit-once]')
 ThreadingHTTPServer(("0.0.0.0",8789),Handler).serve_forever()
if __name__=="__main__":main()
