"""Internal Registry: separate SQLite authority with append-only journal/outbox.

It deliberately uses only stdlib.  Ledger publication is asynchronous and
idempotent through the outbox; this service has no foreign key or transaction
against the Ledger database.
"""
import hashlib,hmac,json,os,re,secrets,sqlite3,sys,time,uuid
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
 if d.execute("PRAGMA application_id").fetchone()[0] != 1414746695 or d.execute("PRAGMA user_version").fetchone()[0] != 5:
  d.close(); raise RuntimeError('Registry application_id/user_version mismatch')
 return d
SERVICE_ID='townsquare-registry-v0'; SCHEMA_VERSION=2; DATABASE_SCHEMA_VERSION=5; AUDIT_CONTRACT_VERSION='registry-ledger-audit-v1'
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
_SESSION_STATES={'STARTING','ACTIVE','IDLE','ENDED','LOST'}
def _utc(): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
def _utc_at(epoch): return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(epoch))
def _canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'))
def _sha256_text(value): return hashlib.sha256(value.encode('utf-8')).hexdigest()
def _nonempty_string(value,limit=512):
 return isinstance(value,str) and 0<len(value)<=limit
def _provider_session_id(value):
 return _nonempty_string(value) and all(0x20 <= ord(char) <= 0x7e for char in value)
def _optional_string(value,limit=512):
 return value is None or _nonempty_string(value,limit)
def _redacted_session(row):
 return {name:row[name] for name in ('session_uuid','agent_id','provider','seat_or_host','runtime','model','status','started_utc','last_seen_utc','ended_utc','work_ref','revision','updated_utc')}
def _redacted_history(row):
 body=json.loads(row['body_json']); body.pop('provider_session_id',None)
 return {'seq':row['seq'],'event_id':row['event_id'],'session_uuid':row['session_uuid'],'agent_id':row['agent_id'],'action':row['action'],'body':body,'committed_utc':row['committed_utc']}
def _operator_authorized(headers):
 configured=operator_token(); provided=headers.get('X-Registry-Operator-Token','')
 return bool(configured) and hmac.compare_digest(provided.encode(),configured.encode())
def _authorization(headers):
 value=headers.get('Authorization','')
 scheme,separator,credential=value.partition(' ')
 if separator!=' ' or not credential or credential!=credential.strip(): return '', ''
 return scheme,credential
def _lookup_authorized(headers):
 scheme,credential=_authorization(headers)
 if scheme!='Bearer': return False
 try: verifier=Path(LOOKUP_TOKEN_SHA256_FILE).read_text(encoding='ascii').strip()
 except OSError:return False
 return bool(_SHA256.fullmatch(verifier)) and hmac.compare_digest(_sha256_text(credential),verifier)
def _legacy_authorized(headers):
 scheme,credential=_authorization(headers)
 if scheme!='Bearer': return False
 try: configured=token()
 except OSError:return False
 return bool(configured) and hmac.compare_digest(credential.encode(),configured.encode())
def _session_proof(headers):
 scheme,credential=_authorization(headers)
 return credential if scheme=='SessionProof' and _SHA256.fullmatch(credential) else None
def _enrollment_credential_sha256(headers):
 scheme,credential=_authorization(headers)
 return _sha256_text(credential) if scheme=='Enrollment' else None
def _session_proof_payload(method,path,key,body):
 body_sha256=hashlib.sha256(_canonical(body).encode()).hexdigest()
 return f'registry-session-proof-v1\n{method}\n{path}\n{key or ""}\n{body_sha256}'.encode()
def _proof_matches(verifier,proof,method,path,key,body):
 if not verifier or not proof:return False
 expected=hmac.new(bytes.fromhex(verifier),_session_proof_payload(method,path,key,body),hashlib.sha256).hexdigest()
 return hmac.compare_digest(expected,proof)
def _session_request_valid(body,action):
 if not isinstance(body,dict): return False
 if action=='register':
  allowed={'agent_id','provider','provider_session_id','initial_status','seat_or_host','runtime','model','work_ref','session_credential_sha256'}
  if not set(body)<=allowed:return False
  if not _nonempty_string(body.get('agent_id'),128) or not isinstance(body.get('provider'),str) or not _PROVIDER.fullmatch(body['provider']): return False
  if not _provider_session_id(body.get('provider_session_id')) or body.get('initial_status') not in ('STARTING','ACTIVE'): return False
  if body.get('session_credential_sha256') is not None and (not isinstance(body['session_credential_sha256'],str) or not _SHA256.fullmatch(body['session_credential_sha256'])):return False
  return all(_optional_string(body.get(name)) for name in ('seat_or_host','runtime','model','work_ref'))
 if action=='heartbeat': return body.get('status') in ('ACTIVE','IDLE') and set(body) <= {'status','session_uuid'}
 return body.get('terminal_status') in ('ENDED','LOST') and set(body) <= {'terminal_status','session_uuid'}
def _session_outbox_body(row,action,when):
 return {'kind':'session_lifecycle','session_uuid':row['session_uuid'],'agent_id':row['agent_id'],'provider':row['provider'],'status':row['status'],'work_ref':row['work_ref'],'action':action,'committed_utc':when}
def _enrollment_request_valid(body):
 return (
  isinstance(body,dict) and set(body)=={'agent_id','provider','seat_or_host'} and
  _nonempty_string(body.get('agent_id'),128) and isinstance(body.get('provider'),str) and
  bool(_PROVIDER.fullmatch(body['provider'])) and _nonempty_string(body.get('seat_or_host'),512)
 )
def create_session_enrollment(db,body):
 """Create a ten-minute one-use grant; only the verifier is persisted."""
 if not _enrollment_request_valid(body):return 400,{'detail':'invalid session enrollment request'}
 db.execute('BEGIN IMMEDIATE')
 try:
  agent=db.execute('SELECT active FROM agents WHERE agent_id=?',(body['agent_id'],)).fetchone()
  if not agent or not agent['active']:
   db.rollback();return 409,{'detail':'session enrollment conflict','code':'SESSION_ENROLLMENT_CONFLICT'}
  grant_id=str(uuid.uuid4()); enrollment_token=secrets.token_urlsafe(32); expires_utc=_utc_at(time.time()+600)
  db.execute('INSERT INTO session_enrollments(grant_id,token_sha256,agent_id,provider,seat_or_host,expires_utc) VALUES(?,?,?,?,?,?)',(grant_id,_sha256_text(enrollment_token),body['agent_id'],body['provider'],body['seat_or_host'],expires_utc))
  db.commit()
  return 201,{'grant_id':grant_id,'enrollment_token':enrollment_token,'agent_id':body['agent_id'],'provider':body['provider'],'seat_or_host':body['seat_or_host'],'expires_utc':expires_utc}
 except Exception:
  db.rollback();raise
def _registration_conflict(db):
 db.rollback();return 409,{'detail':'session registration conflict','code':'SESSION_REGISTRATION_CONFLICT'}
def register_enrolled_session(db,enrollment_sha256,key,body):
 """Consume one enrollment and create its verifier-bound session atomically."""
 if not key or not enrollment_sha256 or not _session_request_valid(body,'register') or not _SHA256.fullmatch(body.get('session_credential_sha256','')) or not _nonempty_string(body.get('seat_or_host')):
  return 400,{'detail':'invalid session registration request'}
 request_sha256=hashlib.sha256(_canonical(body).encode()).hexdigest()
 db.execute('BEGIN IMMEDIATE')
 try:
  enrollment=db.execute('SELECT * FROM session_enrollments WHERE token_sha256=?',(enrollment_sha256,)).fetchone()
  if not enrollment:
   db.rollback();return 401,{'detail':'unauthorized'}
  replay=db.execute('SELECT * FROM session_registration_replays WHERE grant_id=?',(enrollment['grant_id'],)).fetchone()
  if enrollment['consumed_utc'] is not None:
   if replay and hmac.compare_digest(replay['idem_key'],key) and hmac.compare_digest(replay['request_sha256'],request_sha256):
    db.rollback();return replay['response_status'],json.loads(replay['response_json'])
   return _registration_conflict(db)
  if enrollment['expires_utc']<=_utc():
   db.rollback();return 409,{'detail':'session enrollment expired','code':'SESSION_ENROLLMENT_EXPIRED'}
  if any(body.get(name)!=enrollment[name] for name in ('agent_id','provider','seat_or_host')):
   return _registration_conflict(db)
  agent=db.execute('SELECT active FROM agents WHERE agent_id=?',(body['agent_id'],)).fetchone()
  if not agent or not agent['active'] or db.execute('SELECT 1 FROM sessions WHERE provider=? AND provider_session_id=?',(body['provider'],body['provider_session_id'])).fetchone():
   return _registration_conflict(db)
  now=_utc();session_uuid=str(uuid.uuid4());status=body['initial_status']
  db.execute('INSERT INTO sessions(session_uuid,agent_id,provider,provider_session_id,seat_or_host,runtime,model,status,started_utc,last_seen_utc,ended_utc,work_ref,revision,updated_utc,session_credential_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(session_uuid,body['agent_id'],body['provider'],body['provider_session_id'],body['seat_or_host'],body.get('runtime'),body.get('model'),status,now,now,None,body.get('work_ref'),1,now,body['session_credential_sha256']))
  row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone();event_id=str(uuid.uuid4());audit_id=str(uuid.uuid4())
  db.execute('INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?,?)',(event_id,session_uuid,row['agent_id'],'register',_canonical(_redacted_session(row)),now))
  db.execute('INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)',(audit_id,row['agent_id'],'session_register',_canonical(_session_outbox_body(row,'register',now)),now))
  db.execute('INSERT INTO audit_outbox(event_id) VALUES(?)',(audit_id,))
  response={'event_id':event_id,**_redacted_session(row),'action':'register'}
  db.execute('UPDATE session_enrollments SET consumed_utc=?,session_uuid=? WHERE grant_id=? AND consumed_utc IS NULL',(now,session_uuid,enrollment['grant_id']))
  db.execute('INSERT INTO session_registration_replays(grant_id,idem_key,request_sha256,response_json,response_status,committed_utc) VALUES(?,?,?,?,?,?)',(enrollment['grant_id'],key,request_sha256,_canonical(response),201,now))
  db.commit();return 201,response
 except Exception:
  db.rollback();raise
def mutate_session(db,principal,key,body,action,session_proof=None):
 """Apply one S1 lifecycle mutation in the Registry's existing transaction boundary."""
 if not _session_request_valid(body,action): return 400,{'detail':'invalid session lifecycle request'}
 request_hash=hashlib.sha256(_canonical(body).encode()).hexdigest()
 db.execute('BEGIN IMMEDIATE')
 if session_proof is not None:
  owner=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(body.get('session_uuid'),)).fetchone()
  proof_body={name:value for name,value in body.items() if name!='session_uuid'}
  proof_path=f"/v1/sessions/{body.get('session_uuid')}/{action}"
  if not owner or not _proof_matches(owner['session_credential_sha256'],session_proof,'POST',proof_path,key,proof_body):
   db.rollback();return 401,{'detail':'unauthorized'}
 old=db.execute('SELECT * FROM requests WHERE principal=? AND idem_key=?',(principal,key)).fetchone()
 if old:
  if old['request_hash']!=request_hash: db.rollback(); return 409,{'detail':'idempotency key reused with different request'}
  db.rollback(); return old['response_status'],json.loads(old['response_json'])
 try:
  now=_utc()
  if action=='register':
   agent=db.execute('SELECT active FROM agents WHERE agent_id=?',(body['agent_id'],)).fetchone()
   if not agent or not agent['active']: db.rollback(); return 409,{'detail':'session registration conflict'}
   if db.execute('SELECT 1 FROM sessions WHERE provider=? AND provider_session_id=?',(body['provider'],body['provider_session_id'])).fetchone(): db.rollback(); return 409,{'detail':'session registration conflict'}
   session_uuid=str(uuid.uuid4()); status=body['initial_status']
   db.execute('INSERT INTO sessions(session_uuid,agent_id,provider,provider_session_id,seat_or_host,runtime,model,status,started_utc,last_seen_utc,ended_utc,work_ref,revision,updated_utc,session_credential_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(session_uuid,body['agent_id'],body['provider'],body['provider_session_id'],body.get('seat_or_host'),body.get('runtime'),body.get('model'),status,now,now,None,body.get('work_ref'),1,now,body.get('session_credential_sha256')))
   row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
  else:
   session_uuid=body.get('session_uuid')
   row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
   if not row or row['status'] in ('ENDED','LOST'): db.rollback(); return 409,{'detail':'session lifecycle conflict'}
   if action=='heartbeat':
    wanted=body['status']; allowed=(row['status']=='STARTING' and wanted=='ACTIVE') or (row['status']=='ACTIVE' and wanted in ('ACTIVE','IDLE')) or (row['status']=='IDLE' and wanted in ('ACTIVE','IDLE'))
    if not allowed: db.rollback(); return 409,{'detail':'session lifecycle conflict'}
    db.execute('UPDATE sessions SET status=?,last_seen_utc=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(wanted,now,now,session_uuid))
   else:
    wanted=body['terminal_status']; action='mark_lost' if wanted=='LOST' else 'terminate'
    db.execute('UPDATE sessions SET status=?,last_seen_utc=?,ended_utc=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(wanted,now,now,now,session_uuid))
   row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
  event_id=str(uuid.uuid4()); audit_id=str(uuid.uuid4())
  private_body=dict(_redacted_session(row)); private_body['provider_session_id']=body.get('provider_session_id',row['provider_session_id'])
  db.execute('INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?,?)',(event_id,row['session_uuid'],row['agent_id'],action,_canonical(private_body),now))
  audit_body=_session_outbox_body(row,action,now)
  db.execute('INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)',(audit_id,row['agent_id'],'session_'+action,_canonical(audit_body),now))
  db.execute('INSERT INTO audit_outbox(event_id) VALUES(?)',(audit_id,))
  response={'event_id':event_id,**_redacted_session(row),'action':action}
  response_status=201 if action=='register' else 200
  db.execute('INSERT INTO requests(principal,idem_key,request_hash,response_json,response_status) VALUES(?,?,?,?,?)',(principal,key,request_hash,_canonical(response),response_status))
  db.commit(); return response_status,response
 except Exception:
  db.rollback(); raise
def rotate_session_credential(db,session_uuid,rotation_id,session_proof,body):
 """Commit a client-generated replacement verifier with response-loss replay."""
 if not rotation_id or not session_proof or not isinstance(body,dict) or set(body)!={'session_credential_sha256'} or not isinstance(body.get('session_credential_sha256'),str) or not _SHA256.fullmatch(body['session_credential_sha256']):
  return 400,{'detail':'invalid session credential rotation request'}
 new_sha256=body['session_credential_sha256'];request_sha256=hashlib.sha256(_canonical(body).encode()).hexdigest()
 path=f'/v1/sessions/{session_uuid}/credential-rotations'
 db.execute('BEGIN IMMEDIATE')
 try:
  replay=db.execute('SELECT * FROM session_credential_rotations WHERE session_uuid=? AND rotation_id=?',(session_uuid,rotation_id)).fetchone()
  if replay:
   authenticated=_proof_matches(replay['old_credential_sha256'],session_proof,'POST',path,rotation_id,body) or _proof_matches(replay['new_credential_sha256'],session_proof,'POST',path,rotation_id,body)
   if authenticated and hmac.compare_digest(replay['request_sha256'],request_sha256):
    db.rollback();return replay['response_status'],json.loads(replay['response_json'])
   db.rollback();return 409,{'detail':'session credential rotation conflict','code':'SESSION_ROTATION_CONFLICT'}
  row=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
  if not row or not _proof_matches(row['session_credential_sha256'],session_proof,'POST',path,rotation_id,body):
   db.rollback();return 401,{'detail':'unauthorized'}
  old_sha256=row['session_credential_sha256']
  if row['status'] in ('ENDED','LOST') or hmac.compare_digest(old_sha256,new_sha256):
   db.rollback();return 409,{'detail':'session credential rotation conflict','code':'SESSION_ROTATION_CONFLICT'}
  now=_utc();event_id=str(uuid.uuid4());audit_id=str(uuid.uuid4())
  db.execute('UPDATE sessions SET session_credential_sha256=?,revision=revision+1,updated_utc=? WHERE session_uuid=?',(new_sha256,now,session_uuid))
  updated=db.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
  db.execute('INSERT INTO session_journal(event_id,session_uuid,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?,?)',(event_id,session_uuid,updated['agent_id'],'credential_rotate',_canonical(_redacted_session(updated)),now))
  db.execute('INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)',(audit_id,updated['agent_id'],'session_credential_rotate',_canonical(_session_outbox_body(updated,'credential_rotate',now)),now))
  db.execute('INSERT INTO audit_outbox(event_id) VALUES(?)',(audit_id,))
  response={'event_id':event_id,**_redacted_session(updated),'action':'credential_rotate','rotation_id':rotation_id}
  db.execute('INSERT INTO session_credential_rotations(session_uuid,rotation_id,old_credential_sha256,new_credential_sha256,request_sha256,response_json,response_status,event_id,committed_utc) VALUES(?,?,?,?,?,?,?,?,?)',(session_uuid,rotation_id,old_sha256,new_sha256,request_sha256,_canonical(response),200,event_id,now))
  db.commit();return 200,response
 except Exception:
  db.rollback();raise
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,status,value,no_store=False):
  data=json.dumps(value,sort_keys=True).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store') if no_store else None;self.end_headers();self.wfile.write(data)
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
  session_match=re.fullmatch(r'/v1/sessions/([0-9a-f-]{36})(?:/(history|provider-locator))?',urlsplit(self.path).path)
  if session_match:
   session_uuid,view=session_match.groups(); sensitive=view=='provider-locator'
   legacy=_legacy_authorized(self.headers);lookup=_lookup_authorized(self.headers);session_proof=_session_proof(self.headers)
   if sensitive and (not legacy or not _operator_authorized(self.headers)): return self.reply(404,{'detail':'not found'},True)
   if not sensitive and not (legacy or lookup or session_proof):return self.reply(401,{'detail':'unauthorized'})
   d=None
   try:
    d=connect()
    row=d.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
    if not row:return self.reply(404,{'detail':'not found'},sensitive)
    if session_proof and not _proof_matches(row['session_credential_sha256'],session_proof,'GET',urlsplit(self.path).path,'',None):return self.reply(404,{'detail':'not found'})
    if sensitive:return self.reply(200,{'session_uuid':row['session_uuid'],'provider':row['provider'],'provider_session_id':row['provider_session_id']},True)
    if view=='history':
     events=[_redacted_history(event) for event in d.execute('SELECT * FROM session_journal WHERE session_uuid=? ORDER BY seq',(session_uuid,))]
     return self.reply(200,{'session_uuid':session_uuid,'events':events})
    return self.reply(200,_redacted_session(row))
   except Exception:return self.reply(503,{'detail':'session lookup unavailable'},sensitive)
   finally:
    if d:d.close()
  self.reply(404,{"detail":"not found"})
 def do_POST(self):
  session_match=re.fullmatch(r'/v1/sessions/([0-9a-f-]{36})/(heartbeat|terminate)',self.path)
  rotation_match=re.fullmatch(r'/v1/sessions/([0-9a-f-]{36})/credential-rotations',self.path)
  enrollment_path=self.path=='/v1/session-enrollments'
  if self.path!="/v1/agents" and not session_match and not rotation_match and self.path!='/v1/sessions' and not enrollment_path:return self.reply(404,{"detail":"not found"})
  if enrollment_path and (self.client_address[0] not in ('127.0.0.1','::1') or not _operator_authorized(self.headers)):
   return self.reply(404,{"detail":"not found"},True)
  key=self.headers.get("Idempotency-Key")
  if not enrollment_path and not key:return self.reply(400,{"detail":"Idempotency-Key required"})
  try: body=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))))
  except Exception:return self.reply(400,{"detail":"invalid json"})
  if enrollment_path:
   d=connect()
   try:
    status,out=create_session_enrollment(d,body);return self.reply(status,out,True)
   except Exception:return self.reply(503,{"detail":"session enrollment unavailable"},True)
   finally:d.close()
  if self.path=='/v1/sessions':
   d=connect()
   try:
    enrollment_sha256=_enrollment_credential_sha256(self.headers)
    if enrollment_sha256:
     status,out=register_enrolled_session(d,enrollment_sha256,key,body);return self.reply(status,out)
    if not _legacy_authorized(self.headers):return self.reply(401,{"detail":"unauthorized"})
    principal=self.headers.get("X-Registry-Principal")
    if not principal:return self.reply(400,{"detail":"X-Registry-Principal required"})
    try:require_canary_test_proof(self.headers,body,'registry:session:register',body.get('agent_id',''))
    except CanaryAuthorityError as e:return self.reply(403,{"detail":str(e)})
    status,out=mutate_session(d,principal,key,body,'register');return self.reply(status,out)
   except Exception:return self.reply(503,{"detail":"session lifecycle unavailable"})
   finally:d.close()
  if session_match:
   session_uuid,action=session_match.groups()
   body=dict(body);body['session_uuid']=session_uuid
   d=connect()
   try:
    session_proof=_session_proof(self.headers)
    if session_proof:
     status,out=mutate_session(d,'session:'+session_uuid,key,body,action,session_proof);return self.reply(status,out)
    if not _legacy_authorized(self.headers):return self.reply(401,{"detail":"unauthorized"})
    principal=self.headers.get("X-Registry-Principal")
    if not principal:return self.reply(400,{"detail":"X-Registry-Principal required"})
    try:require_canary_test_proof(self.headers,body,'registry:session:'+action,session_uuid)
    except CanaryAuthorityError as e:return self.reply(403,{"detail":str(e)})
    status,out=mutate_session(d,principal,key,body,action);return self.reply(status,out)
   except Exception:return self.reply(503,{"detail":"session lifecycle unavailable"})
   finally:d.close()
  if rotation_match:
   session_uuid=rotation_match.group(1);session_proof=_session_proof(self.headers)
   if not session_proof:return self.reply(401,{"detail":"unauthorized"})
   d=connect()
   try:
    status,out=rotate_session_credential(d,session_uuid,key,session_proof,body);return self.reply(status,out)
   except Exception:return self.reply(503,{"detail":"session credential rotation unavailable"})
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
