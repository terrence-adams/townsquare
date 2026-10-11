"""Internal Registry: separate SQLite authority with append-only journal/outbox.

It deliberately uses only stdlib.  Ledger publication is asynchronous and
idempotent through the outbox; this service has no foreign key or transaction
against the Ledger database.
"""
import base64,datetime,hashlib,hmac,json,os,posixpath,re,secrets,signal,sqlite3,sys,threading,time,unicodedata,urllib.error,urllib.parse,urllib.request,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from shared.canary_authority import CanaryAuthorityError,CanaryProofVerifier,FileNonceStore,canonical_bytes,decode_proof,decode_signature,load_r7_context
from shared.canary_identity import compatible_identity,require_canary_identity
from shared.registry_outbox import acknowledge_delivery
from shared import session_registry_listener

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
 if d.execute("PRAGMA application_id").fetchone()[0] != 1414746695 or d.execute("PRAGMA user_version").fetchone()[0] != DATABASE_SCHEMA_VERSION:
  d.close(); raise RuntimeError('Registry application_id/user_version mismatch')
 return d
SERVICE_ID='townsquare-registry-v0'; SCHEMA_VERSION=2; DATABASE_SCHEMA_VERSION=10; AUDIT_CONTRACT_VERSION='registry-ledger-audit-v1'
AUDIT_INTERVAL_ENV='REGISTRY_AUDIT_INTERVAL_SECONDS';AUDIT_RELEASE_INTERVAL_SECONDS=30;AUDIT_CYCLE_LIMIT=100;AUDIT_LEASE_SECONDS=30
AUDIT_ROLES=(
 ('ledger_audit','REGISTRY_LEDGER_AUDIT_TOKEN_FILE','REGISTRY_LEDGER_AUDIT_CREDENTIAL_REVISION'),
 ('ledger_readiness_outbound','LEDGER_READINESS_TOKEN_FILE','LEDGER_READINESS_CREDENTIAL_REVISION'),
 ('registry_peer_readiness_inbound','REGISTRY_PEER_READINESS_TOKEN_FILE','REGISTRY_PEER_READINESS_CREDENTIAL_REVISION'),
)
AUDIT_PERMANENT_CODES={'CONFIGURATION_INVALID','CREDENTIAL_INVALID','PEER_IDENTITY_INVALID','REMOTE_PROTOCOL_INVALID','REMOTE_REJECTED'}
_AUDIT_CREDENTIAL_RE=re.compile(rb'[A-Za-z0-9_-]{43}')
_AUDIT_SHA256_RE=re.compile(r'[0-9a-f]{64}')
_AUDIT_GIT_RE=re.compile(r'[0-9a-f]{40}')
_AUDIT_RELEASE_RE=re.compile(r'TS-R7-[0-9a-f]{64}')
_AUDIT_UUID4_RE=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}')
def _audit_utc(epoch=None):return time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(time.time() if epoch is None else epoch))
class AuditConfigurationError(RuntimeError):
 def __init__(self,code,mask,static_fingerprint=None,role=None,revision=None,persistable=False,full_fingerprint=None,verifier=None,canonical_path=None,static_context_fingerprint=None,epoch=None):
  super().__init__(code);self.code=code;self.mask=tuple(sorted(set(mask)));self.static_fingerprint=static_fingerprint;self.role=role;self.revision=revision;self.persistable=persistable;self.full_fingerprint=full_fingerprint;self.verifier=verifier;self.canonical_path=canonical_path;self.static_context_fingerprint=static_context_fingerprint;self.epoch=epoch
 def configuration(self):
  binding={'role':self.role,'canonical_path':self.canonical_path,'revision':self.revision,'verifier':self.verifier} if self.role else None
  return {'static_fingerprint':self.static_fingerprint,'full_fingerprint':self.full_fingerprint,'full':{'credential_bindings':[binding] if binding else []},'credential_contexts':{self.role:self.static_context_fingerprint} if self.role else {},'epoch':self.epoch}
class AuditEpochError(RuntimeError):
 def __init__(self,code):super().__init__(code);self.code=code
def _audit_string(value,field,pattern=None):
 if not isinstance(value,str) or not value or value!=value.strip() or not unicodedata.is_normalized('NFC',value) or any(ord(c)<32 or 127<=ord(c)<=159 for c in value) or (pattern and not pattern.fullmatch(value)):raise AuditConfigurationError('CONFIGURATION_INVALID',(field,))
 return value
def _audit_uint(value,field):
 if not isinstance(value,str) or not re.fullmatch(r'[1-9][0-9]*',value) or int(value)>2**63-1:raise AuditConfigurationError('CONFIGURATION_INVALID',(field,))
 return int(value)
def _audit_path(value,field):
 value=_audit_string(value,field)
 if not value.startswith('/') or value!='/' and (value.endswith('/') or '//' in value or any(part in ('','.','..') for part in value.split('/')[1:])) or posixpath.normpath(value)!=value:raise AuditConfigurationError('CONFIGURATION_INVALID',(field,))
 return value
def _audit_url(value,field):
 value=_audit_string(value,field)
 try:parts=urllib.parse.urlsplit(value);port=parts.port
 except ValueError:raise AuditConfigurationError('CONFIGURATION_INVALID',(field,)) from None
 if parts.scheme not in ('http','https') or parts.scheme!=parts.scheme.lower() or not parts.hostname or parts.hostname!=parts.hostname.lower() or port is None or parts.username is not None or parts.password is not None or parts.query or parts.fragment:raise AuditConfigurationError('CONFIGURATION_INVALID',(field,))
 try:parts.hostname.encode('ascii')
 except UnicodeEncodeError:raise AuditConfigurationError('CONFIGURATION_INVALID',(field,)) from None
 host='['+parts.hostname+']' if ':' in parts.hostname else parts.hostname;path=parts.path or '/'
 escapes=re.findall(r'%([0-9A-Fa-f]{2})',path)
 if not path.startswith('/') or posixpath.normpath(path)!=path or re.search(r'%(?![0-9A-F]{2})|%[0-9A-F][a-f]|%[a-f][0-9A-Fa-f]',path) or any(chr(int(item,16)) in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~' for item in escapes):raise AuditConfigurationError('CONFIGURATION_INVALID',(field,))
 if value!=f'{parts.scheme}://{host}:{port}{path}':raise AuditConfigurationError('CONFIGURATION_INVALID',(field,))
 return value
def _jcs(value):
 def closed(item):
  if item is None or isinstance(item,(str,bool,int)):return
  if isinstance(item,list):
   for child in item:closed(child)
   return
  if isinstance(item,dict) and all(isinstance(key,str) for key in item):
   for child in item.values():closed(child)
   return
  raise AuditConfigurationError('CONFIGURATION_INVALID',('canonical_json',))
 closed(value);return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def _domain_fingerprint(domain,value):return hashlib.sha256(domain.encode()+b'\0'+_jcs(value).encode()).hexdigest()
def validate_audit_credential(raw):
 if not isinstance(raw,bytes) or len(raw)!=43 or not _AUDIT_CREDENTIAL_RE.fullmatch(raw):raise AuditConfigurationError('CREDENTIAL_INVALID',('credential',))
 try:decoded=base64.b64decode(raw+b'=',altchars=b'-_',validate=True)
 except Exception:raise AuditConfigurationError('CREDENTIAL_INVALID',('credential',)) from None
 if len(decoded)!=32 or base64.urlsafe_b64encode(decoded).rstrip(b'=')!=raw:raise AuditConfigurationError('CREDENTIAL_INVALID',('credential',))
 weak=len(set(decoded))==1 or decoded in (bytes(range(32)),bytes(range(31,-1,-1))) or any(decoded==decoded[:size]*(32//size) for size in (1,2,4,8,16))
 if weak:raise AuditConfigurationError('CREDENTIAL_INVALID',('credential',))
 return decoded
def generate_audit_credential(path,rng=secrets.token_bytes):
 raw=base64.urlsafe_b64encode(rng(32)).rstrip(b'=');validate_audit_credential(raw);fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 try:os.write(fd,raw);os.fsync(fd)
 finally:os.close(fd)
 return None
def _audit_static_config(environ=None):
 values=os.environ if environ is None else environ
 identity={
  'runtime_class':_audit_string(values.get('TOWNSQUARE_RUNTIME_CLASS'),'identity.runtime_class'),
  'authority_class':_audit_string(values.get('TOWNSQUARE_AUTHORITY_CLASS'),'identity.authority_class'),
  'canary_label':_audit_string(values.get('TOWNSQUARE_CANARY_LABEL'),'identity.canary_label'),
  'compose_project':_audit_string(values.get('TOWNSQUARE_COMPOSE_PROJECT'),'identity.compose_project'),
  'source_commit':_audit_string(values.get('TOWNSQUARE_SOURCE_COMMIT'),'identity.source_commit',_AUDIT_GIT_RE),
  'source_tree':_audit_string(values.get('TOWNSQUARE_SOURCE_TREE'),'identity.source_tree',_AUDIT_GIT_RE),
  'r7_release_id':_audit_string(values.get('TOWNSQUARE_R7_RELEASE_ID'),'identity.r7_release_id',_AUDIT_RELEASE_RE),
  'r7_input_manifest_sha256':_audit_string(values.get('TOWNSQUARE_R7_INPUT_MANIFEST_SHA256'),'identity.r7_input_manifest_sha256',_AUDIT_SHA256_RE),
  'r7_identity_sha256':_audit_string(values.get('TOWNSQUARE_R7_IDENTITY_SHA256'),'identity.r7_identity_sha256',_AUDIT_SHA256_RE),
 }
 expected={'runtime_class':'CANARY','authority_class':'NON-AUTHORITATIVE','canary_label':'TS-CANARY-NAS1-20261007-A','compose_project':'townsquare-canary-20261007-a'}
 bad=['identity.'+name for name,wanted in expected.items() if identity[name]!=wanted]
 if bad:raise AuditConfigurationError('CONFIGURATION_INVALID',bad)
 registry={'service_id':_audit_string(values.get('REGISTRY_SERVICE_ID'),'registry.service_id'),'api_schema_head':_audit_uint(values.get('REGISTRY_SCHEMA_HEAD'),'registry.api_schema_head'),'database_schema_version':DATABASE_SCHEMA_VERSION,'audit_contract_version':_audit_string(values.get('REGISTRY_AUDIT_CONTRACT_VERSION'),'registry.audit_contract_version')}
 peer={'service_id':_audit_string(values.get('REGISTRY_LEDGER_SERVICE_ID'),'peer_expected.service_id'),'schema_head':_audit_uint(values.get('REGISTRY_LEDGER_SCHEMA_HEAD'),'peer_expected.schema_head'),'audit_contract_version':_audit_string(values.get('REGISTRY_LEDGER_AUDIT_CONTRACT'),'peer_expected.audit_contract_version')}
 registry_expected={'service_id':SERVICE_ID,'api_schema_head':SCHEMA_VERSION,'database_schema_version':DATABASE_SCHEMA_VERSION,'audit_contract_version':AUDIT_CONTRACT_VERSION}
 peer_expected={'service_id':'townsquare-ledger-v0','schema_head':14,'audit_contract_version':AUDIT_CONTRACT_VERSION}
 if registry!=registry_expected:raise AuditConfigurationError('CONFIGURATION_INVALID',tuple('registry.'+name for name in registry_expected if registry.get(name)!=registry_expected[name]))
 if peer!=peer_expected:raise AuditConfigurationError('CONFIGURATION_INVALID',tuple('peer_expected.'+name for name in peer_expected if peer.get(name)!=peer_expected[name]))
 interval=_audit_uint(values.get(AUDIT_INTERVAL_ENV),'transport.interval_seconds')
 if not 5<=interval<=300:raise AuditConfigurationError('CONFIGURATION_INVALID',('transport.interval_seconds',))
 transport={'audit_url':_audit_url(LEDGER_AUDIT_URL,'transport.audit_url'),'readiness_url':_audit_url(LEDGER_READINESS_URL,'transport.readiness_url'),'timeout_seconds':LEDGER_AUDIT_TIMEOUT_SECONDS,'interval_seconds':interval,'cycle_limit':AUDIT_CYCLE_LIMIT,'lease_seconds':AUDIT_LEASE_SECONDS}
 bindings=[]
 for role,path_env,revision_env in AUDIT_ROLES:
  raw_revision=values.get(revision_env);revision=_audit_uint(raw_revision,'credential_bindings.'+role+'.declared_revision') if isinstance(raw_revision,str) and re.fullmatch(r'[1-9][0-9]*',raw_revision) else None
  bindings.append({'role':role,'canonical_path':_audit_path(values.get(path_env),'credential_bindings.'+role+'.canonical_path'),'declared_revision':revision})
 static={'schema':'townsquare-registry-audit-static-config-v1','identity':identity,'registry':registry,'peer_expected':peer,'transport':transport,'credential_bindings':bindings}
 return static,_domain_fingerprint('townsquare-registry-audit-static-config-fingerprint-v1',static)
def _credential_verifier(role,salt,decoded):return hashlib.sha256(b'townsquare-registry-audit-credential-verifier-v1\0'+role.encode()+b'\0'+salt+b'\0'+decoded).hexdigest()
def _credential_context_fingerprint(static,role):
 normalized=json.loads(_jcs(static))
 for binding in normalized['credential_bindings']:
  if binding['role']==role:binding['declared_revision']=None
 return _domain_fingerprint('townsquare-registry-audit-credential-static-context-v1',normalized)
def _accepted_context(static):
 identity=static['identity'];registry=static['registry'];peer=static['peer_expected']
 return {'accepted_context_schema_version':1,'r7_release_id':identity['r7_release_id'],'r7_input_manifest_sha256':identity['r7_input_manifest_sha256'],'r7_identity_sha256':identity['r7_identity_sha256'],'r7_context_sha256':R7_CONTEXT_SHA256,'source_commit':identity['source_commit'],'source_tree':identity['source_tree'],'runtime_class':identity['runtime_class'],'authority_class':identity['authority_class'],'canary_label':identity['canary_label'],'compose_project':identity['compose_project'],'registry_service_id':registry['service_id'],'registry_api_schema_head':registry['api_schema_head'],'registry_database_schema_version':registry['database_schema_version'],'registry_audit_contract_version':registry['audit_contract_version'],'ledger_service_id':peer['service_id'],'ledger_schema_head':peer['schema_head'],'ledger_audit_contract_version':peer['audit_contract_version']}
def _claim_durable_context(db,static,release_start_uuid,runtime):
 expected=_accepted_context(static);attempt_started=time.time();now=_audit_utc(attempt_started);db.execute('BEGIN IMMEDIATE')
 try:
  rows=db.execute('SELECT * FROM audit_accepted_context').fetchall()
  if not rows:
   columns=('singleton',*expected);db.execute('INSERT INTO audit_accepted_context('+','.join(columns)+') VALUES('+','.join('?' for _ in columns)+')',(1,*expected.values()))
  elif len(rows)!=1 or any(rows[0][name]!=value for name,value in expected.items()):raise AuditEpochError('IMMUTABLE_CONTEXT_MISMATCH')
  epoch=db.execute('SELECT * FROM audit_boot_epoch WHERE singleton=1').fetchone()
  claimed=runtime.get('epoch')
  if claimed:
   if claimed['release_start_uuid']!=release_start_uuid or not epoch or epoch['release_start_uuid']!=release_start_uuid or epoch['boot_epoch_revision']!=claimed['boot_epoch_revision'] or epoch['epoch_state']!='ACTIVE':raise AuditEpochError('BOOT_EPOCH_LOST')
   db.commit();return claimed
  if db.execute('SELECT 1 FROM audit_boot_epoch_history WHERE release_start_uuid=?',(release_start_uuid,)).fetchone():raise AuditEpochError('BOOT_EPOCH_REPLAY')
  stale=_audit_utc(time.time()-90)
  if epoch['epoch_state']=='ACTIVE' and epoch['heartbeat_utc'] and epoch['heartbeat_utc']>stale:raise AuditEpochError('BOOT_EPOCH_CAS_CONFLICT' if epoch['heartbeat_utc']>=_audit_utc(attempt_started-1) else 'BOOT_EPOCH_ACTIVE_CONFLICT')
  observed=(epoch['release_start_uuid'],epoch['boot_epoch_revision'],epoch['epoch_state'],epoch['heartbeat_utc']);revision=epoch['boot_epoch_revision']+1
  db.execute('INSERT INTO audit_boot_epoch_history VALUES(?,?,?)',(release_start_uuid,revision,now))
  changed=db.execute('UPDATE audit_boot_epoch SET release_start_uuid=?,boot_epoch_revision=?,epoch_state=\'ACTIVE\',heartbeat_utc=? WHERE singleton=1 AND release_start_uuid IS ? AND boot_epoch_revision=? AND epoch_state=? AND heartbeat_utc IS ?',(release_start_uuid,revision,now,*observed)).rowcount
  if changed!=1:raise AuditEpochError('BOOT_EPOCH_CAS_CONFLICT')
  claim={'release_start_uuid':release_start_uuid,'boot_epoch_revision':revision};db.commit();runtime['epoch']=claim;return claim
 except Exception:db.rollback();raise
def _prepare_audit_configuration(environ=None,reader=None,db_factory=None,salt_source=secrets.token_bytes,runtime=None):
 values=os.environ if environ is None else environ;reader=(lambda path:Path(path).read_bytes()) if reader is None else reader;db_factory=connect if db_factory is None else db_factory
 release_start_uuid=values.get('TOWNSQUARE_RELEASE_START_UUID')
 if not isinstance(release_start_uuid,str) or not _AUDIT_UUID4_RE.fullmatch(release_start_uuid):raise AuditConfigurationError('CONFIGURATION_INVALID',('release_start_uuid',))
 runtime={} if runtime is None else runtime;static,static_fingerprint=_audit_static_config(values);decoded={};contexts={binding['role']:_credential_context_fingerprint(static,binding['role']) for binding in static['credential_bindings']}
 for binding in static['credential_bindings']:
  role=binding['role']
  try:decoded[role]=validate_audit_credential(reader(binding['canonical_path']))
  except (OSError,AuditConfigurationError):
   claimed=runtime.get('epoch');raise AuditConfigurationError('CREDENTIAL_INVALID' if claimed else 'AUDIT_BOOTSTRAP_CREDENTIAL_REJECTED',('credential_bindings.'+role,),static_fingerprint if claimed else None,role,binding['declared_revision'],bool(claimed),canonical_path=binding['canonical_path'],static_context_fingerprint=contexts[role],epoch=claimed) from None
 if hmac.compare_digest(decoded['ledger_readiness_outbound'],decoded['registry_peer_readiness_inbound']):
  role='registry_peer_readiness_inbound';binding=next(item for item in static['credential_bindings'] if item['role']==role);claimed=runtime.get('epoch');raise AuditConfigurationError('CREDENTIAL_INVALID',('credential_bindings.'+role,),static_fingerprint if claimed else None,role,binding['declared_revision'],bool(claimed),canonical_path=binding['canonical_path'],static_context_fingerprint=contexts[role],epoch=claimed)
 if any(binding['declared_revision'] is None for binding in static['credential_bindings']):
  binding=next(binding for binding in static['credential_bindings'] if binding['declared_revision'] is None);role=binding['role'];claimed=runtime.get('epoch');raise AuditConfigurationError('CREDENTIAL_INVALID' if claimed else 'AUDIT_BOOTSTRAP_CREDENTIAL_REJECTED',('credential_bindings.'+role,),static_fingerprint if claimed else None,role,None,bool(claimed),canonical_path=binding['canonical_path'],static_context_fingerprint=contexts[role],epoch=claimed)
 db=db_factory();full_bindings=[];candidates={};accepted={}
 try:
  epoch=_claim_durable_context(db,static,release_start_uuid,runtime)
  db.execute('BEGIN IMMEDIATE')
  for binding in static['credential_bindings']:
   role=binding['role'];row=db.execute('SELECT * FROM audit_credential_bindings WHERE role=?',(role,)).fetchone()
   if row is None:
    salt=salt_source(32)
    if not isinstance(salt,bytes) or len(salt)!=32 or len(set(salt))==1:raise AuditConfigurationError('CREDENTIAL_INVALID',('credential_bindings.'+role,),static_fingerprint,role,binding['declared_revision'])
    db.execute('INSERT INTO audit_credential_bindings(role,salt) VALUES(?,?)',(role,salt));accepted_revision=None;accepted_verifier=None
   else:salt=row['salt'];accepted_revision=row['accepted_revision'];accepted_verifier=row['verifier']
   verifier=_credential_verifier(role,salt,decoded[role]);revision=binding['declared_revision']
   full_bindings.append({'role':role,'canonical_path':binding['canonical_path'],'revision':revision,'verifier':verifier});accepted[role]={'revision':accepted_revision,'verifier':accepted_verifier};candidates[role]=accepted_revision is None or revision>accepted_revision
  full={'schema':'townsquare-registry-audit-config-v1','identity':static['identity'],'registry':static['registry'],'peer_expected':static['peer_expected'],'transport':static['transport'],'credential_bindings':full_bindings};fingerprint=_domain_fingerprint('townsquare-registry-audit-config-fingerprint-v1',full)
  for binding in full_bindings:
   role=binding['role'];revision=binding['revision'];verifier=binding['verifier'];prior=accepted[role];highwater=db.execute('SELECT highest_failed_revision FROM audit_credential_failure_highwater WHERE role=?',(role,)).fetchone()
   invalid=(highwater is not None and revision<=highwater['highest_failed_revision']) or (prior['revision'] is not None and (revision<prior['revision'] or revision==prior['revision'] and not hmac.compare_digest(verifier,prior['verifier']))) or (candidates[role] and prior['verifier'] is not None and hmac.compare_digest(verifier,prior['verifier']))
   if invalid:raise AuditConfigurationError('CREDENTIAL_INVALID',('credential_bindings.'+role,),static_fingerprint,role,revision,True,fingerprint,verifier,binding['canonical_path'],contexts[role],epoch)
  db.commit()
 except Exception:db.rollback();raise
 finally:db.close()
 return {'static':static,'static_fingerprint':static_fingerprint,'full':full,'full_fingerprint':fingerprint,'decoded':decoded,'candidates':candidates,'credential_contexts':contexts,'epoch':epoch}
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
 return base64.urlsafe_b64encode(validate_audit_credential(Path(LEDGER_AUDIT_TOKEN_FILE).read_bytes())).rstrip(b'=').decode()
def ledger_readiness_token():
 path=os.environ.get('REGISTRY_PEER_READINESS_TOKEN_FILE','/run/secrets/ledger_registry_readiness_token');return base64.urlsafe_b64encode(validate_audit_credential(Path(path).read_bytes())).rstrip(b'=').decode()
def require_directional_tokens():
 inbound=ledger_readiness_token()
 outbound=base64.urlsafe_b64encode(validate_audit_credential(Path(LEDGER_READINESS_TOKEN_FILE).read_bytes())).rstrip(b'=').decode()
 if hashlib.sha256(inbound.encode()).digest()==hashlib.sha256(outbound.encode()).digest():
  raise RuntimeError('directional readiness credentials must be distinct')
def peer_ready(configuration=None):
 """Live fixed-origin Ledger tuple exchange; never accepts an env self-claim."""
 try:
  if configuration is None:require_directional_tokens();token=base64.urlsafe_b64encode(validate_audit_credential(Path(LEDGER_READINESS_TOKEN_FILE).read_bytes())).rstrip(b'=').decode()
  else:
   token=base64.urlsafe_b64encode(configuration['decoded']['ledger_readiness_outbound']).rstrip(b'=').decode()
  request=urllib.request.Request(LEDGER_READINESS_URL,headers={'Authorization':'Bearer '+token})
  with urllib.request.urlopen(request,timeout=LEDGER_AUDIT_TIMEOUT_SECONDS) as response: peer=json.load(response)
  compatible=peer.get('ok') is True and compatible_identity(peer,CANARY_IDENTITY) and peer.get('service_id')=='townsquare-ledger-v0' and peer.get('schema_version')==14 and peer.get('audit_contract_version')==AUDIT_CONTRACT_VERSION
  expected={'service_id','schema_version','audit_contract_version',*CANARY_IDENTITY.as_dict()};mask=tuple(sorted((('peer_expected.ok',) if peer.get('ok') is not True else ())+tuple('peer_expected.'+name for name in expected if name=='service_id' and peer.get(name)!='townsquare-ledger-v0' or name=='schema_version' and peer.get(name)!=14 or name=='audit_contract_version' and peer.get(name)!=AUDIT_CONTRACT_VERSION or name in CANARY_IDENTITY.as_dict() and peer.get(name)!=CANARY_IDENTITY.as_dict()[name])))
  return {'compatible':compatible,'failure_code':None if compatible else 'PEER_IDENTITY_INVALID','failure_field_mask':mask,'service_id':peer.get('service_id'),'schema_version':peer.get('schema_version'),**{name:peer.get(name) for name in CANARY_IDENTITY.as_dict()}}
 except urllib.error.HTTPError as error:
  if error.code in (400,401,403,409):return {'compatible':False,'failure_code':'REMOTE_REJECTED','failure_field_mask':('credential_bindings.ledger_readiness_outbound','transport.readiness_url')}
  if error.code in (408,425,429) or 500<=error.code<=599:return {'compatible':False,'failure_code':'REMOTE_UNAVAILABLE','failure_field_mask':('transport.readiness_url',)}
  return {'compatible':False,'failure_code':'REMOTE_PROTOCOL_INVALID','failure_field_mask':('transport.readiness_url','response.status')}
 except (OSError,TimeoutError,urllib.error.URLError):return {'compatible':False,'failure_code':'REMOTE_UNAVAILABLE','failure_field_mask':('transport.readiness_url',)}
 except Exception:return {'compatible':False,'failure_code':'REMOTE_PROTOCOL_INVALID','failure_field_mask':('transport.readiness_url','peer_expected')}
def audit_interval(environ=None):
 values=os.environ if environ is None else environ;raw=values.get(AUDIT_INTERVAL_ENV)
 if not isinstance(raw,str) or not re.fullmatch(r'[1-9][0-9]*',raw) or not 5<=int(raw)<=300:raise RuntimeError('Registry audit interval configuration invalid')
 return int(raw)
def claim(db,owner,lease_seconds=AUDIT_LEASE_SECONDS,excluded=()):
 """Atomically lease one pending stable UUID; expired claims are recoverable."""
 now=_audit_utc();until=_audit_utc(time.time()+lease_seconds);db.execute('BEGIN IMMEDIATE')
 try:
  exclusion="" if not excluded else " AND o.event_id NOT IN ("+",".join("?" for _ in excluded)+")"
  row=db.execute("SELECT o.event_id FROM audit_outbox o JOIN journal j USING(event_id) WHERE o.delivered_utc IS NULL AND (o.lease_until IS NULL OR o.lease_until<?)"+exclusion+" ORDER BY j.seq LIMIT 1",(now,*excluded)).fetchone()
  if not row:db.commit();return None
  changed=db.execute("UPDATE audit_outbox SET lease_owner=?,lease_until=? WHERE event_id=? AND delivered_utc IS NULL AND (lease_until IS NULL OR lease_until<?)",(owner,until,row['event_id'],now)).rowcount;db.commit();return row['event_id'] if changed else None
 except Exception:db.rollback();raise
class AuditDeliveryFailure(RuntimeError):
 def __init__(self,code,permanent=False,mask=()):super().__init__(code);self.code=code;self.permanent=permanent;self.mask=tuple(sorted(set(mask)))
def _audit_failure(error,event_id=None):
 if isinstance(error,AuditDeliveryFailure):code,permanent,mask=error.code,error.permanent,error.mask
 elif isinstance(error,urllib.error.HTTPError):
  if error.code in (401,403):code,permanent,mask='REMOTE_REJECTED',True,('credential_bindings.ledger_audit',)
  elif error.code in (400,409):code,permanent,mask='REMOTE_REJECTED',True,('event.'+str(event_id)+'.identity',)
  elif error.code in (408,425,429) or 500<=error.code<=599:code,permanent,mask='REMOTE_UNAVAILABLE',False,('transport.audit_url',)
  else:code,permanent,mask='REMOTE_PROTOCOL_INVALID',True,('transport.audit_url','response.status')
 elif isinstance(error,(OSError,TimeoutError,urllib.error.URLError)):code,permanent,mask='REMOTE_UNAVAILABLE',False,('transport.audit_url',)
 else:code,permanent,mask='REMOTE_PROTOCOL_INVALID',True,('transport.audit_url','response.schema')
 digest=hashlib.sha256((code+':'+type(error).__name__).encode()).hexdigest()
 return code,digest,permanent,mask
def _deliver_claimed(event_id,configuration=None):
 data=_canonical({'board':'BOARD-AUDIT-RECORD','actor':'registry','event_uuid':event_id}).encode()
 credential=ledger_audit_token() if configuration is None else base64.urlsafe_b64encode(configuration['decoded']['ledger_audit']).rstrip(b'=').decode()
 request=urllib.request.Request(LEDGER_AUDIT_URL,data=data,headers={'Content-Type':'application/json','Authorization':'Bearer '+credential,'Idempotency-Key':'registry-'+event_id},method='POST')
 with urllib.request.urlopen(request,timeout=LEDGER_AUDIT_TIMEOUT_SECONDS) as response:
  if response.status//100!=2:raise AuditDeliveryFailure('REMOTE_REJECTED',True)
  raw=response.read(65537)
 if len(raw)>65536:raise AuditDeliveryFailure('REMOTE_PROTOCOL_INVALID',True,('transport.audit_url','response.schema'))
 try:value=json.loads(raw.decode('utf-8'))
 except (UnicodeError,ValueError):raise AuditDeliveryFailure('REMOTE_PROTOCOL_INVALID',True,('transport.audit_url','response.schema')) from None
 if not isinstance(value,dict) or set(value)!={'event_uuid','ledger_event_id'} or value.get('event_uuid')!=event_id or not isinstance(value.get('ledger_event_id'),str) or not value['ledger_event_id']:raise AuditDeliveryFailure('REMOTE_PROTOCOL_INVALID',True,('transport.audit_url','response.schema','response.event_uuid'))
def _binding(configuration,role):return next((item for item in configuration.get('full',{}).get('credential_bindings',()) if item.get('role')==role),None)
def _field_value(configuration,path):
 parts=path.split('.')
 if parts[0]=='credential_bindings' and len(parts)>=2:
  value=_binding(configuration,parts[1])
  for part in parts[2:]:value=value.get(part) if isinstance(value,dict) else None
  return value
 value=configuration.get('full') or configuration.get('static') or {}
 for part in parts:value=value.get(part) if isinstance(value,dict) else None
 return value
def _field_fingerprint(configuration,mask):
 value={path:_field_value(configuration,path) for path in sorted(set(mask))}
 return _domain_fingerprint('townsquare-registry-audit-failure-fields-v1',value)
def _credential_recovery(db,row,configuration,proof,role,mask):
 expected_proof='event_accept' if role=='ledger_audit' else 'peer_identity';binding=_binding(configuration,role)
 if proof!=expected_proof or mask!=(f'credential_bindings.{role}',) or not binding:return False
 accepted=db.execute('SELECT accepted_revision,verifier FROM audit_credential_bindings WHERE role=?',(role,)).fetchone();failed=db.execute('SELECT * FROM audit_credential_failure_highwater WHERE role=?',(role,)).fetchone()
 if not accepted or accepted['accepted_revision'] is None:return False
 context=configuration.get('credential_contexts',{}).get(role)
 highest=max(accepted['accepted_revision'],failed['highest_failed_revision'] if failed else 0);static_match=bool(failed and binding['canonical_path']==failed['canonical_path'] and context==failed['static_context_fingerprint'])
 if row['full_fingerprint'] is None:
  normalized=json.loads(_jcs(configuration['static']))
  for candidate in normalized['credential_bindings']:
   if candidate['role']==role:candidate['declared_revision']=row['declared_revision']
  static_match=bool(row['failed_canonical_path'] and row['static_context_fingerprint'] and binding['canonical_path']==row['failed_canonical_path'] and context==row['static_context_fingerprint'] and _domain_fingerprint('townsquare-registry-audit-static-config-fingerprint-v1',normalized)==row['static_fingerprint'])
  durable_match=row['failure_code']=='CREDENTIAL_INVALID' and row['credential_role']==role and row['failed_verifier'] is None;failed_verifier=None
 else:
  durable_match=bool(failed and row['declared_revision']==failed['highest_failed_revision'] and row['failed_verifier']==failed['failed_verifier'] and row['failed_canonical_path']==failed['canonical_path'] and row['static_context_fingerprint']==failed['static_context_fingerprint'] and row['static_fingerprint']==failed['static_fingerprint'] and row['full_fingerprint']==failed['full_fingerprint']);failed_verifier=failed['failed_verifier'] if failed else None
 return bool(static_match and durable_match and binding['revision']>highest and not hmac.compare_digest(binding['verifier'],accepted['verifier']) and (failed_verifier is None or not hmac.compare_digest(binding['verifier'],failed_verifier)) and configuration.get('full_fingerprint')!=row['full_fingerprint'])
def _record_latch(db,key,code,configuration,mask,event_id=None,role=None,revision=None):
 if code not in AUDIT_PERMANENT_CODES:raise RuntimeError('invalid permanent audit failure code')
 mask=tuple(sorted(set(mask)));now=_audit_utc();static=configuration.get('static_fingerprint') if configuration else hashlib.sha256(('static:'+code).encode()).hexdigest();full=configuration.get('full_fingerprint') if configuration else None;binding=_binding(configuration or {},role) if role else None;verifier=binding.get('verifier') if binding else None;fields=_field_fingerprint(configuration or {},mask);context=(configuration or {}).get('credential_contexts',{}).get(role) if role else None
 credential_masks={(f'credential_bindings.{role}',), (f'credential_bindings.{role}','transport.readiness_url')} if role else set()
 credential_failure=role and revision and context and binding and code in ('CREDENTIAL_INVALID','REMOTE_REJECTED') and mask in credential_masks
 if credential_failure:
  durable_path=binding['canonical_path'];durable_context=context
  db.execute("INSERT INTO audit_credential_failure_highwater(role,highest_failed_revision,failed_verifier,static_fingerprint,full_fingerprint,canonical_path,static_context_fingerprint,failure_code,updated_utc) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(role) DO UPDATE SET highest_failed_revision=MAX(highest_failed_revision,excluded.highest_failed_revision),failed_verifier=CASE WHEN excluded.highest_failed_revision>=highest_failed_revision THEN excluded.failed_verifier ELSE failed_verifier END,static_fingerprint=CASE WHEN excluded.highest_failed_revision>=highest_failed_revision THEN excluded.static_fingerprint ELSE static_fingerprint END,full_fingerprint=CASE WHEN excluded.highest_failed_revision>=highest_failed_revision THEN excluded.full_fingerprint ELSE full_fingerprint END,canonical_path=CASE WHEN excluded.highest_failed_revision>=highest_failed_revision THEN excluded.canonical_path ELSE canonical_path END,static_context_fingerprint=CASE WHEN excluded.highest_failed_revision>=highest_failed_revision THEN excluded.static_context_fingerprint ELSE static_context_fingerprint END,failure_code=CASE WHEN excluded.highest_failed_revision>=highest_failed_revision THEN excluded.failure_code ELSE failure_code END,updated_utc=excluded.updated_utc",(role,revision,verifier,static,full,durable_path,durable_context,code,now))
  highwater=db.execute('SELECT * FROM audit_credential_failure_highwater WHERE role=?',(role,)).fetchone();revision=highwater['highest_failed_revision'];verifier=highwater['failed_verifier'];static=highwater['static_fingerprint'];full=highwater['full_fingerprint'];code=highwater['failure_code']
 db.execute("INSERT INTO audit_failure_latches(latch_key,event_id,failure_code,static_fingerprint,full_fingerprint,failure_field_mask_json,credential_role,declared_revision,created_utc,updated_utc,failed_verifier,failure_field_fingerprint,failed_canonical_path,static_context_fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(latch_key) DO UPDATE SET event_id=excluded.event_id,failure_code=excluded.failure_code,static_fingerprint=excluded.static_fingerprint,full_fingerprint=excluded.full_fingerprint,failure_field_mask_json=excluded.failure_field_mask_json,credential_role=excluded.credential_role,declared_revision=excluded.declared_revision,updated_utc=excluded.updated_utc,failed_verifier=excluded.failed_verifier,failure_field_fingerprint=excluded.failure_field_fingerprint,failed_canonical_path=excluded.failed_canonical_path,static_context_fingerprint=excluded.static_context_fingerprint",(key,event_id,code,static,full,_jcs(list(mask)),role,revision,now,now,verifier,fields,durable_path if credential_failure else binding.get('canonical_path') if binding else None,durable_context if credential_failure else context))
def _accept_bindings(db,configuration,roles):
 for binding in configuration['full']['credential_bindings']:
  role=binding['role']
  if role in roles and configuration['candidates'].get(role):db.execute('UPDATE audit_credential_bindings SET accepted_revision=?,verifier=?,full_fingerprint=? WHERE role=?',(binding['revision'],binding['verifier'],configuration['full_fingerprint'],role));configuration['candidates'][role]=False
def _recover_latch(db,key,configuration,proof,event_id=None,role=None):
 row=db.execute('SELECT * FROM audit_failure_latches WHERE latch_key=?',(key,)).fetchone()
 if row is None:return True
 try:mask=tuple(json.loads(row['failure_field_mask_json']))
 except (TypeError,ValueError):return False
 if not mask or mask!=tuple(sorted(set(mask))) or not all(isinstance(item,str) and item for item in mask):return False
 current_static=configuration.get('static_fingerprint');current_full=configuration.get('full_fingerprint');binding=_binding(configuration,role) if role else None
 fingerprints_compared=(row['static_fingerprint'],row['full_fingerprint'],current_static,current_full)
 if key.startswith('event:'):
  protocol_masks={tuple(sorted(items)) for items in ((f'event.{event_id}.identity',),('transport.audit_url','response.schema'),('transport.audit_url','response.schema','response.event_uuid'),('transport.audit_url','response.schema','response.status'))}
  valid=proof=='event_accept' and row['event_id']==event_id and event_id and (mask in protocol_masks or role=='ledger_audit' and row['failure_code']=='REMOTE_REJECTED' and _credential_recovery(db,row,configuration,proof,role,mask))
 elif key=='peer':
  peer_leaves={'peer_expected.'+name for name in ('ok','service_id','schema_version','audit_contract_version',*CANARY_IDENTITY.as_dict())};protocol_masks={('peer_expected','transport.readiness_url'),('response.status','transport.readiness_url')};pure=(row['failure_code']=='PEER_IDENTITY_INVALID' and set(mask)<=peer_leaves and bool(mask) or row['failure_code']=='REMOTE_PROTOCOL_INVALID' and mask in protocol_masks) and current_static==row['static_fingerprint'] and current_full==row['full_fingerprint'];credential=row['failure_code']=='REMOTE_REJECTED' and mask==('credential_bindings.ledger_readiness_outbound','transport.readiness_url') and _credential_recovery(db,row,configuration,proof,'ledger_readiness_outbound',('credential_bindings.ledger_readiness_outbound',))
  valid=proof=='peer_identity' and (pure or credential)
 elif key=='configuration':
  identity_leaves={'identity.'+name for name in ('runtime_class','authority_class','canary_label','compose_project','source_commit','source_tree','r7_release_id','r7_input_manifest_sha256','r7_identity_sha256')};registry_leaves={'registry.'+name for name in ('service_id','api_schema_head','database_schema_version','audit_contract_version')};peer_leaves={'peer_expected.'+name for name in ('service_id','schema_head','audit_contract_version')};transport_leaves={'transport.'+name for name in ('audit_url','readiness_url','timeout_seconds','interval_seconds','cycle_limit','lease_seconds')};binding_leaves={f'credential_bindings.{item}{suffix}' for item in ('ledger_audit','ledger_readiness_outbound','registry_peer_readiness_inbound') for suffix in ('','.canonical_path','.declared_revision')}
  valid=proof=='peer_identity' and row['failure_code']=='CONFIGURATION_INVALID' and set(mask)<=(identity_leaves|registry_leaves|peer_leaves|transport_leaves|binding_leaves) and current_static!=row['static_fingerprint'] and current_full!=row['full_fingerprint'] and _field_fingerprint(configuration,mask)!=row['failure_field_fingerprint']
 elif key.startswith('credential:'):
  expected=key.split(':',1)[1];valid=role==expected and _credential_recovery(db,row,configuration,proof,role,mask)
 else:return False
 if not valid:return False
 if key.startswith('credential:') and not valid:return False
 if any(value is None for value in fingerprints_compared[:1]) or current_static is None or current_full is None:return False
 db.execute('DELETE FROM audit_failure_latches WHERE latch_key=?',(key,));return True
def _current_latch(db):return db.execute('SELECT failure_code,latch_key FROM audit_failure_latches ORDER BY created_utc,latch_key LIMIT 1').fetchone()
def _epoch_heartbeat(db,epoch,heartbeat):
 if not epoch:return
 changed=db.execute("UPDATE audit_boot_epoch SET heartbeat_utc=? WHERE singleton=1 AND release_start_uuid=? AND boot_epoch_revision=? AND epoch_state='ACTIVE'",(heartbeat,epoch['release_start_uuid'],epoch['boot_epoch_revision'])).rowcount
 if changed!=1:raise AuditEpochError('BOOT_EPOCH_LOST')
def _close_epoch(db,epoch):
 if not epoch:return True
 db.execute('BEGIN IMMEDIATE')
 try:
  changed=db.execute("UPDATE audit_boot_epoch SET epoch_state='CLOSED' WHERE singleton=1 AND release_start_uuid=? AND boot_epoch_revision=? AND epoch_state='ACTIVE'",(epoch['release_start_uuid'],epoch['boot_epoch_revision'])).rowcount
  if changed!=1:raise AuditEpochError('BOOT_EPOCH_LOST')
  db.commit();return True
 except Exception:db.rollback();raise
def _worker_state(db,started,completed=None,attempts=0,failure=None,epoch=None):
 heartbeat=completed or started;latch=_current_latch(db);code=latch['failure_code'] if latch else None;digest=hashlib.sha256((code+':'+latch['latch_key']).encode()).hexdigest() if latch else None
 _epoch_heartbeat(db,epoch,heartbeat)
 db.execute("UPDATE audit_worker_state SET heartbeat_utc=?,last_cycle_started_utc=?,last_cycle_completed_utc=?,last_cycle_attempts=?,permanent_failure_code=?,permanent_failure_digest=? WHERE singleton=1",(heartbeat,started,completed,attempts,code,digest))
def audit_worker_cycle(interval=AUDIT_RELEASE_INTERVAL_SECONDS,stop_event=None,runtime=None):
 started=_audit_utc();attempted=0;delivered=0;failed=0;seen=[]
 try:configuration=_prepare_audit_configuration() if runtime is None else _prepare_audit_configuration(runtime=runtime)
 except AuditEpochError as error:return {'heartbeat_utc':None,'attempted':0,'delivered':0,'failed':0,'failure_code':error.code}
 except AuditConfigurationError as error:
  if not error.persistable and (error.code=='CREDENTIAL_INVALID' or not error.static_fingerprint):return {'heartbeat_utc':None,'attempted':0,'delivered':0,'failed':0,'failure_code':error.code,'static_fingerprint':error.static_fingerprint,'credential_role':error.role,'declared_revision':error.revision}
  d=connect()
  try:
   d.execute('BEGIN IMMEDIATE');_record_latch(d,'credential:'+error.role if error.role else 'configuration',error.code,error.configuration(),error.mask,role=error.role,revision=error.revision);_worker_state(d,started,started,0,epoch=error.epoch);d.commit()
  except Exception:d.rollback();raise
  finally:d.close()
  return {'heartbeat_utc':started,'attempted':0,'delivered':0,'failed':0,'failure_code':error.code}
 d=connect();permanent=None
 try:
  _worker_state(d,started,epoch=configuration.get('epoch'))
  if not compatible():_record_latch(d,'configuration','CONFIGURATION_INVALID',configuration,('registry.service_id','registry.api_schema_head','registry.audit_contract_version'));permanent='CONFIGURATION_INVALID'
  else:
   peer=peer_ready(configuration)
   if not peer.get('compatible'):
    if peer.get('failure_code') in AUDIT_PERMANENT_CODES:
     mask=peer.get('failure_field_mask',('peer_expected.service_id',));role='ledger_readiness_outbound' if 'credential_bindings.ledger_readiness_outbound' in mask else None;revision=_binding(configuration,role)['revision'] if role else None;_record_latch(d,'peer',peer['failure_code'],configuration,mask,role=role,revision=revision);permanent=peer['failure_code']
   else:
    d.execute('BEGIN IMMEDIATE')
    recovered=_recover_latch(d,'peer',configuration,'peer_identity',role='ledger_readiness_outbound') and _recover_latch(d,'configuration',configuration,'peer_identity')
    for role in ('ledger_readiness_outbound','registry_peer_readiness_inbound'):recovered=recovered and _recover_latch(d,'credential:'+role,configuration,'peer_identity',role=role)
    if recovered:_accept_bindings(d,configuration,{'ledger_readiness_outbound','registry_peer_readiness_inbound'});d.commit()
    else:d.rollback();permanent=(_current_latch(d) or {'failure_code':'CONFIGURATION_INVALID'})['failure_code']
    owner=str(uuid.uuid4())
    while recovered and attempted<AUDIT_CYCLE_LIMIT and not (stop_event and stop_event.is_set()):
     event_id=claim(d,owner,excluded=seen)
     if not event_id:break
     attempted+=1;seen.append(event_id)
     if stop_event and stop_event.is_set():break
     try:
      _deliver_claimed(event_id,configuration);d.execute('BEGIN IMMEDIATE');recovered=_recover_latch(d,'credential:ledger_audit',configuration,'event_accept',event_id,'ledger_audit') and _recover_latch(d,'event:'+event_id,configuration,'event_accept',event_id,'ledger_audit')
      if recovered:acknowledge_delivery(d,event_id,owner);_accept_bindings(d,configuration,{'ledger_audit'});d.commit();delivered+=1
      else:d.rollback();d.execute('BEGIN IMMEDIATE');d.execute("UPDATE audit_outbox SET attempts=attempts+1,last_error=?,lease_owner=NULL,lease_until=? WHERE event_id=? AND delivered_utc IS NULL AND lease_owner=?",('CONFIGURATION_INVALID:'+hashlib.sha256(b'latch-recovery-rejected').hexdigest(),_audit_utc(time.time()+interval),event_id,owner));d.commit();failed+=1
     except Exception as error:
      d.rollback();code,digest,is_permanent,mask=_audit_failure(error,event_id);cooldown=_audit_utc(time.time()+interval);d.execute('BEGIN IMMEDIATE');d.execute("UPDATE audit_outbox SET attempts=attempts+1,last_error=?,lease_owner=NULL,lease_until=? WHERE event_id=? AND delivered_utc IS NULL AND lease_owner=?",(code+':'+digest,cooldown,event_id,owner));
      if is_permanent:_record_latch(d,'event:'+event_id,code,configuration,mask,event_id,'ledger_audit',next(item['revision'] for item in configuration['full']['credential_bindings'] if item['role']=='ledger_audit'));permanent=permanent or code
      d.commit();failed+=1
  completed=_audit_utc();_worker_state(d,started,completed,attempted,permanent,configuration.get('epoch'))
  latch=_current_latch(d);return {'heartbeat_utc':completed,'attempted':attempted,'delivered':delivered,'failed':failed,'failure_code':latch['failure_code'] if latch else None,'configuration_fingerprint':configuration['full_fingerprint']}
 finally:d.close()
def deliver_once():return audit_worker_cycle(AUDIT_RELEASE_INTERVAL_SECONDS)
def audit_worker(environ=None,stop_event=None,monotonic=time.monotonic):
 """Run the durable periodic Registry audit-delivery loop."""
 interval=audit_interval(environ);stop=stop_event or threading.Event();runtime={}
 def stopping(*_):stop.set()
 previous={}
 if stop_event is None:
  for name in (signal.SIGINT,signal.SIGTERM):previous[name]=signal.signal(name,stopping)
 try:
  deadline=monotonic()
  while not stop.is_set():
   metrics=audit_worker_cycle(interval,stop,runtime);print(_canonical({'kind':'registry_audit_worker_cycle',**metrics}),flush=True);deadline+=interval
   if metrics.get('heartbeat_utc') is None:raise SystemExit('Registry audit worker startup rejected')
   if stop.wait(max(0,deadline-monotonic())):break
 finally:
  if runtime.get('epoch'):
   d=connect()
   try:_close_epoch(d,runtime['epoch'])
   finally:d.close()
  if stop_event is None:
   for name,handler in previous.items():signal.signal(name,handler)
def audit_delivery_health(db,now_epoch=None,environ=None):
 now_epoch=time.time() if now_epoch is None else now_epoch;stale=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(now_epoch-90));old=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(now_epoch-120));state=db.execute('SELECT * FROM audit_worker_state WHERE singleton=1').fetchone();oldest=db.execute('SELECT min(j.committed_utc) FROM audit_outbox o JOIN journal j USING(event_id) WHERE o.delivered_utc IS NULL').fetchone()[0]
 values=os.environ if environ is None else environ;expected_uuid=values.get('TOWNSQUARE_RELEASE_START_UUID');epoch_ready=False
 if isinstance(expected_uuid,str) and _AUDIT_UUID4_RE.fullmatch(expected_uuid):
  try:static,_=_audit_static_config(values);context=_accepted_context(static);rows=db.execute('SELECT * FROM audit_accepted_context').fetchall();epoch=db.execute('SELECT * FROM audit_boot_epoch WHERE singleton=1').fetchone();epoch_ready=bool(_AUDIT_UUID4_RE.fullmatch(expected_uuid) and len(rows)==1 and all(rows[0][name]==value for name,value in context.items()) and epoch and epoch['release_start_uuid']==expected_uuid and epoch['epoch_state']=='ACTIVE' and epoch['heartbeat_utc'] and epoch['heartbeat_utc']>stale)
  except Exception:epoch_ready=False
 ready=bool(epoch_ready and state and state['heartbeat_utc'] and state['heartbeat_utc']>stale and state['permanent_failure_code'] is None and (oldest is None or oldest>old))
 return {'ready':ready,'worker_heartbeat_utc':state['heartbeat_utc'] if state else None,'oldest_pending_utc':oldest,'failure_code':state['permanent_failure_code'] if state else 'WORKER_HEARTBEAT_MISSING'}
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
def session_listener_config(environ=None):
 values=os.environ if environ is None else environ
 try:
  canonical=_canonical({'schema':session_registry_listener.SCHEMA,'bind_host':session_registry_listener.BIND_HOST,'bind_port':session_registry_listener.BIND_PORT,'public_url':session_registry_listener.PUBLIC_URL})
  if canonical!=session_registry_listener.CANONICAL_JSON or not hmac.compare_digest(_sha256_text(canonical),session_registry_listener.SHA256):raise ValueError()
  if any(not isinstance(values.get(name),str) or not hmac.compare_digest(values[name],expected) for name,expected in session_registry_listener.environment().items()):raise ValueError()
 except (TypeError,ValueError):raise RuntimeError('session Registry listener configuration invalid') from None
 return session_registry_listener.BIND_HOST,session_registry_listener.BIND_PORT
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
   elif action=='provider_locator':response={'session_uuid':row['session_uuid'],'provider':row['provider'],'provider_session_id':row['provider_session_id']}
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
    d=connect(); version=d.execute("SELECT max(version) FROM registry_migrations").fetchone()[0]; pending=d.execute("SELECT count(*) FROM audit_outbox WHERE delivered_utc IS NULL").fetchone()[0]; failed=d.execute("SELECT count(*) FROM audit_outbox WHERE delivered_utc IS NULL AND last_error IS NOT NULL").fetchone()[0];delivery=audit_delivery_health(d);d.close();
    tuple={"registry_service":SERVICE_ID,"registry_schema":SCHEMA_VERSION,"ledger_service":"townsquare-ledger-v0","ledger_schema":14,"audit_contract":AUDIT_CONTRACT_VERSION}
    expected_peer={"service_id":"townsquare-ledger-v0","schema_version":14,**CANARY_IDENTITY.as_dict()}
    base={**identity_metadata(),"database_schema_version":version,"compatibility":tuple,"compatible_peer":expected_peer}
    if not compatible(): return self.reply(503,{"ok":False,**base,"detail":"incompatible schema/audit contract"})
    if failed or not delivery['ready']:return self.reply(503,{"ok":False,**base,"pending_audit":pending,"delivery_failures":failed,"audit_worker":delivery,"detail":"registry audit delivery degraded"})
    return self.reply(200,{"ok":True,**base,"pending_audit":pending,"delivery_failures":0})
   except Exception:return self.reply(503,{"ok":False,"detail":"registry readiness unavailable"})
  if self.path=="/health/internal/ready":
   if self.client_address[0] not in ('127.0.0.1','::1'): return self.reply(404,{"detail":"not found"})
   try:d=connect();delivery=audit_delivery_health(d);d.close()
   except Exception:delivery={'ready':False}
   if compatible() and peer_ready().get('compatible') and delivery['ready']: return self.reply(200,{"ok":True})
   return self.reply(503,{"ok":False})
  session_match=re.fullmatch(r'/v1/sessions/([0-9a-f-]{36})(?:/(history|provider-locator))?',self.path)
  if session_match:
   session_uuid,view=session_match.groups(); sensitive=view=='provider-locator'
   if not _UUID4_RE.fullmatch(session_uuid):return self.reply(404,{'detail':'not found'},True)
   lookup=_lookup_authorized(self.headers);scheme,_=_authorization(self.headers);signed=scheme=='SessionSignature'
   if sensitive and not signed:return self.reply(404,{'detail':'not found'},True)
   if view=='history' and not signed:return self.reply(401,{'detail':'unauthorized','code':'SESSION_SIGNATURE_INVALID'},True)
   if view is None and not (lookup or signed):return self.reply(401,{'detail':'unauthorized'},True)
   d=None
   try:
    d=connect()
    if signed:
     action='history' if view=='history' else 'provider_locator' if sensitive else 'get'
     status,out=owning_session_request(d,self.headers,'GET',self.path,session_uuid,None,action)
     return self.reply(status,out,True)
    row=d.execute('SELECT * FROM sessions WHERE session_uuid=?',(session_uuid,)).fetchone()
    if not row:return self.reply(404,{'detail':'not found'},sensitive)
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
 if sys.argv[1:]==['--audit-worker']:
  audit_worker();return
 require_manual_delivery_mode()
 if not compatible(): raise SystemExit('Registry schema/audit contract incompatible; run registry-migrate')
 if sys.argv[1:]==['--deliver-audit-once']:
  deliver_once();return
 if sys.argv[1:]: raise SystemExit('usage: app.py [--audit-worker|--deliver-audit-once]')
 ThreadingHTTPServer(session_listener_config(),Handler).serve_forever()
if __name__=="__main__":main()
