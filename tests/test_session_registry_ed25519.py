"""Successor acceptance tests for enrollment and Ed25519-owned sessions."""
import base64,hashlib,http.client,importlib,json,os,secrets,shutil,sqlite3,tempfile,threading,time,unittest,uuid
from email.message import Message
from pathlib import Path
from unittest import mock
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tests.test_session_registry_s1 import ROOT,load_app

def b64(raw):return base64.urlsafe_b64encode(raw).decode().rstrip('=')
def key_record(private,epoch=1):
 public=private.public_key().public_bytes_raw()
 return {'alg':'Ed25519','key_id':'ed25519:'+hashlib.sha256(public).hexdigest(),'key_epoch':epoch,'public_key_b64url':b64(public)}

class RegistryFixture(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.app=load_app()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db_path=Path(self.tmp.name)/'registry.db'
  db=sqlite3.connect(self.db_path);db.executescript((ROOT/'registry'/'schema.sql').read_text(encoding='utf-8'))
  for agent in ('nimrod','eddie-brock'):db.execute('INSERT INTO agents VALUES(?,?,?,?,?)',(agent,'{}',1,1,'2026-01-01T00:00:00Z'))
  db.commit();db.close();self.app.DB=self.db_path
 def tearDown(self):self.tmp.cleanup()
 def db(self):return self.app.connect()
 def grant(self,agent='nimrod',provider='codex',seat='sentinel1'):
  db=self.db()
  try:status,response=self.app.create_session_enrollment(db,{'agent_id':agent,'provider':provider,'seat_or_host':seat})
  finally:db.close()
  self.assertEqual(201,status);return response
 def body(self,private,agent='nimrod',provider='codex',seat='sentinel1'):
  return {'agent_id':agent,'provider':provider,'provider_session_id':secrets.token_urlsafe(36),'seat_or_host':seat,'runtime':'codex-runtime','model':'bounded-test-model','initial_status':'ACTIVE','work_ref':'VR-20261011-ynm-002','session_key':key_record(private)}
 def register(self,grant=None,private=None,body=None,idem=None):
  grant=grant or self.grant();private=private or Ed25519PrivateKey.generate();body=body or self.body(private);idem=idem or str(uuid.uuid4());db=self.db()
  try:result=self.app.register_enrolled_session(db,grant['enrollment_token'],idem,body)
  finally:db.close()
  return private,body,idem,result
 def headers(self,private,session,method,path,body,nonce=None,idem=None,revision=None,epoch=None,timestamp=None,key=None):
  nonce=nonce or str(uuid.uuid4());timestamp=timestamp or time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());record=key or key_record(private,epoch or session['session_key_epoch']);revision=session['revision'] if revision is None else revision;epoch=record['key_epoch'] if epoch is None else epoch
  body_hash=hashlib.sha256(self.app._canonical(body).encode()).hexdigest();fields=('townsquare.session-owning-request.v1',method,path,session['session_uuid'],idem or '',body_hash,'ed25519-v1',record['key_id'],str(epoch),str(revision),timestamp,nonce)
  headers=Message();headers.add_header('Authorization','SessionSignature '+b64(private.sign('\0'.join(fields).encode())))
  for name,value in (('X-Session-Key-Id',record['key_id']),('X-Session-Key-Epoch',str(epoch)),('X-Session-Revision',str(revision)),('X-Session-Timestamp',timestamp),('X-Session-Nonce',nonce)):headers.add_header(name,value)
  if idem is not None:headers.add_header('Idempotency-Key',idem)
  return headers
 def session(self):
  private,_,_,(status,response)=self.register();self.assertEqual(201,status);db=self.db()
  try:row=dict(db.execute('SELECT * FROM sessions WHERE session_uuid=?',(response['session_uuid'],)).fetchone())
  finally:db.close()
  return private,row
 def call(self,private,session,method,suffix,body,action,**values):
  path=f"/v1/sessions/{session['session_uuid']}"+suffix;headers=self.headers(private,session,method,path,body,**values);db=self.db()
  try:return self.app.owning_session_request(db,headers,method,path,session['session_uuid'],body,action)
  finally:db.close()
 def counts(self):
  db=self.db()
  try:return tuple(db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in ('sessions','session_enrollments','session_registration_replays','session_owning_replays','session_key_rotations','session_journal','journal','audit_outbox'))
  finally:db.close()

class EnrollmentTests(RegistryFixture):
 def test_http_requires_one_exact_enrollment_header_and_returns_no_store(self):
  grant=self.grant();private=Ed25519PrivateKey.generate();body=self.body(private);raw=self.app._canonical(body).encode();server=self.app.ThreadingHTTPServer(('127.0.0.1',0),self.app.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   connection=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=3);connection.putrequest('POST','/v1/sessions');connection.putheader('Authorization','SessionEnrollment '+grant['enrollment_token']);connection.putheader('Authorization','SessionEnrollment '+grant['enrollment_token']);connection.putheader('Idempotency-Key',str(uuid.uuid4()));connection.putheader('Content-Length',str(len(raw)));connection.endheaders(raw);response=connection.getresponse();self.assertEqual(401,response.status);self.assertEqual('no-store',response.getheader('Cache-Control'));response.read();connection.close()
   connection=http.client.HTTPConnection('127.0.0.1',server.server_address[1],timeout=3);connection.request('POST','/v1/sessions',body=raw,headers={'Authorization':'SessionEnrollment '+grant['enrollment_token'],'Idempotency-Key':str(uuid.uuid4()),'Content-Type':'application/json'});response=connection.getresponse();self.assertEqual(201,response.status);self.assertEqual('no-store',response.getheader('Cache-Control'));response.read();connection.close()
  finally:server.shutdown();server.server_close();thread.join(3)
 def test_exact_token_and_idempotency_grammar_are_pre_database(self):
  grant=self.grant();decoded=base64.urlsafe_b64decode(grant['enrollment_token']+'=');self.assertEqual((43,32),(len(grant['enrollment_token']),len(decoded)));db=self.db()
  try:self.assertEqual(hashlib.sha256(grant['enrollment_token'].encode('ascii')).hexdigest(),db.execute('SELECT token_sha256 FROM session_enrollments').fetchone()[0])
  finally:db.close()
  private=Ed25519PrivateKey.generate();body=self.body(private);before=self.counts()
  for value in ('x'*42,'x'*43+'=','+'+'x'*42,'x'*42+' ','é'*43):
   db=self.db()
   try:status,response=self.app.register_enrolled_session(db,value,str(uuid.uuid4()),body)
   finally:db.close()
   self.assertEqual((401,'SESSION_ENROLLMENT_UNAUTHORIZED'),(status,response['code']))
  for value in ('not-a-uuid',str(uuid.uuid4()).upper(),str(uuid.uuid1())):
   db=self.db()
   try:status,response=self.app.register_enrolled_session(db,grant['enrollment_token'],value,body)
   finally:db.close()
   self.assertEqual((400,'SESSION_IDEMPOTENCY_KEY_INVALID'),(status,response['code']))
  malformed=dict(body,runtime='\ud800');db=self.db()
  try:status,_=self.app.register_enrolled_session(db,grant['enrollment_token'],str(uuid.uuid4()),malformed)
  finally:db.close()
  self.assertEqual(400,status)
  self.assertEqual(before,self.counts())
 def test_atomic_registration_replay_conflicts_and_no_private_material(self):
  grant=self.grant();private=Ed25519PrivateKey.generate();body=self.body(private);idem=str(uuid.uuid4());db=self.db()
  try:first=self.app.register_enrolled_session(db,grant['enrollment_token'],idem,body)
  finally:db.close()
  after=self.counts();db=self.db()
  try:db.execute("UPDATE session_enrollments SET expires_utc='2000-01-01T00:00:00Z'");db.commit()
  finally:db.close()
  db=self.db()
  try:replay=self.app.register_enrolled_session(db,grant['enrollment_token'],idem,body)
  finally:db.close()
  self.assertEqual(first,replay);self.assertEqual(after,self.counts());changed=dict(body,model='changed');db=self.db()
  try:status,response=self.app.register_enrolled_session(db,grant['enrollment_token'],idem,changed)
  finally:db.close()
  self.assertEqual((409,'SESSION_REGISTRATION_CONFLICT'),(status,response['code']));self.assertEqual(after,self.counts());raw=self.db_path.read_bytes();self.assertNotIn(b'private_key',raw);self.assertNotIn(b'private_seed',raw);self.assertNotIn(grant['enrollment_token'].encode(),raw)
 def test_injected_mid_transaction_failure_rolls_back_grant_and_session(self):
  grant=self.grant();private=Ed25519PrivateKey.generate();body=self.body(private);db=self.db();before=self.counts()
  try:
   db.execute("CREATE TRIGGER fail_session_insert BEFORE INSERT ON sessions BEGIN SELECT RAISE(ABORT,'injected'); END")
   status,response=self.app.register_enrolled_session(db,grant['enrollment_token'],str(uuid.uuid4()),body);self.assertEqual((409,'SESSION_REGISTRATION_CONFLICT'),(status,response['code']));self.assertIsNone(db.execute('SELECT consumed_utc FROM session_enrollments').fetchone()[0])
  finally:db.close()
  self.assertEqual(before,self.counts())
 def test_expiry_binding_and_duplicate_locator_are_zero_write(self):
  grant=self.grant();private=Ed25519PrivateKey.generate();body=self.body(private);db=self.db();db.execute("UPDATE session_enrollments SET expires_utc='2000-01-01T00:00:00Z'");db.close();before=self.counts();db=self.db()
  try:status,response=self.app.register_enrolled_session(db,grant['enrollment_token'],str(uuid.uuid4()),body)
  finally:db.close()
  self.assertEqual((409,'SESSION_ENROLLMENT_EXPIRED'),(status,response['code']));self.assertEqual(before,self.counts());grant=self.grant();body['seat_or_host']='venom';db=self.db()
  try:status,response=self.app.register_enrolled_session(db,grant['enrollment_token'],str(uuid.uuid4()),body)
  finally:db.close()
  self.assertEqual((409,'SESSION_REGISTRATION_CONFLICT'),(status,response['code']))
 def test_cleanup_is_bounded_and_never_removes_mutation_replay(self):
  db=self.db()
  try:
   rows=[(str(uuid.uuid4()),hashlib.sha256(str(index).encode()).hexdigest(),'nimrod','codex','sentinel1','1999-01-01T00:00:00Z','2000-01-01T00:00:00Z') for index in range(501)]
   db.executemany('INSERT INTO session_enrollments(grant_id,token_sha256,agent_id,provider,seat_or_host,created_utc,expires_utc) VALUES(?,?,?,?,?,?,?)',rows);db.commit();self.assertEqual(500,self.app.cleanup_session_artifacts(db,'2000-01-03T00:00:00Z'));self.assertEqual(1,db.execute('SELECT count(*) FROM session_enrollments').fetchone()[0])
  finally:db.close()
 def test_active_registration_replay_is_never_cleaned_early(self):
  _,_,_,(status,response)=self.register();self.assertEqual(201,status);db=self.db()
  try:
   db.execute("UPDATE session_registration_replays SET retain_until_utc='2000-01-01T00:00:00Z'");db.commit();self.app.cleanup_session_artifacts(db,'2099-01-01T00:00:00Z');self.assertEqual(1,db.execute('SELECT count(*) FROM session_registration_replays').fetchone()[0]);self.assertEqual('ACTIVE',db.execute('SELECT status FROM sessions WHERE session_uuid=?',(response['session_uuid'],)).fetchone()[0])
  finally:db.close()

class OwningRequestTests(RegistryFixture):
 def test_heartbeat_replay_nonce_stale_and_revision(self):
  private,session=self.session();nonce=str(uuid.uuid4());idem=str(uuid.uuid4());stamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());first=self.call(private,session,'POST','/heartbeat',{'status':'IDLE'},'heartbeat',nonce=nonce,idem=idem,timestamp=stamp);self.assertEqual((200,2),(first[0],first[1]['revision']));after=self.counts()
  with mock.patch.object(self.app.time,'time',return_value=time.time()+1000):replay=self.call(private,session,'POST','/heartbeat',{'status':'IDLE'},'heartbeat',nonce=nonce,idem=idem,timestamp=stamp)
  self.assertEqual(first,replay);self.assertEqual(after,self.counts());status,response=self.call(private,session,'POST','/heartbeat',{'status':'ACTIVE'},'heartbeat',nonce=nonce,idem=idem);self.assertEqual((409,'SESSION_NONCE_CONFLICT'),(status,response['code']));current=dict(session,revision=2);status,response=self.call(private,current,'POST','/heartbeat',{'status':'ACTIVE'},'heartbeat',idem=str(uuid.uuid4()),revision=1);self.assertEqual((409,'SESSION_REVISION_CONFLICT'),(status,response['code']));before=self.counts();status,response=self.call(private,current,'POST','/heartbeat',{'status':'ACTIVE'},'heartbeat',idem=str(uuid.uuid4()),timestamp='2000-01-01T00:00:00Z');self.assertEqual((401,'SESSION_SIGNATURE_STALE'),(status,response['code']));future=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(time.time()+300));status,response=self.call(private,current,'POST','/heartbeat',{'status':'ACTIVE'},'heartbeat',idem=str(uuid.uuid4()),timestamp=future);self.assertEqual((401,'SESSION_SIGNATURE_STALE'),(status,response['code']));self.assertEqual(before,self.counts())
 def test_get_one_use_and_database_exfiltration_cannot_forge(self):
  private,session=self.session();nonce=str(uuid.uuid4());first=self.call(private,session,'GET','',None,'get',nonce=nonce);self.assertEqual(200,first[0]);status,response=self.call(private,session,'GET','',None,'get',nonce=nonce);self.assertEqual((409,'SESSION_NONCE_CONFLICT'),(status,response['code']));attacker=Ed25519PrivateKey.generate();before=self.counts();status,response=self.call(attacker,session,'GET','',None,'get',key=key_record(private));self.assertEqual((401,'SESSION_SIGNATURE_INVALID'),(status,response['code']));self.assertEqual(before,self.counts())
 def test_rotation_cutoff_replay_and_terminate(self):
  private,session=self.session();replacement=Ed25519PrivateKey.generate();nonce=str(uuid.uuid4());idem=str(uuid.uuid4());stamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());body={'new_key':key_record(replacement,2)};first=self.call(private,session,'POST','/credential-rotations',body,'credential_rotate',nonce=nonce,idem=idem,timestamp=stamp);self.assertEqual((200,2),(first[0],first[1]['revision']));after=self.counts()
  with mock.patch.object(self.app.time,'time',return_value=time.time()+1000):replay=self.call(private,session,'POST','/credential-rotations',body,'credential_rotate',nonce=nonce,idem=idem,timestamp=stamp)
  self.assertEqual(first,replay);self.assertEqual(after,self.counts());changed={'new_key':key_record(Ed25519PrivateKey.generate(),2)};status,response=self.call(private,session,'POST','/credential-rotations',changed,'credential_rotate',nonce=nonce,idem=idem,timestamp=stamp);self.assertEqual((409,'SESSION_ROTATION_CONFLICT'),(status,response['code']));self.assertEqual(after,self.counts());current=dict(session,revision=2,session_key_epoch=2,session_key_id=body['new_key']['key_id']);status,response=self.call(private,current,'POST','/heartbeat',{'status':'IDLE'},'heartbeat',idem=str(uuid.uuid4()),key=body['new_key']);self.assertEqual((401,'SESSION_SIGNATURE_INVALID'),(status,response['code']));status,response=self.call(replacement,current,'POST','/heartbeat',{'status':'IDLE'},'heartbeat',idem=str(uuid.uuid4()),key=body['new_key'],epoch=1);self.assertEqual((401,'SESSION_SIGNATURE_INVALID'),(status,response['code']));status,ended=self.call(replacement,current,'POST','/terminate',{'terminal_status':'ENDED'},'terminate',idem=str(uuid.uuid4()),key=body['new_key']);self.assertEqual((200,'ENDED',3),(status,ended['status'],ended['revision']))

class FixtureAndMigrationTests(unittest.TestCase):
 def test_public_fixture_is_byte_exact_and_identity_coherent(self):
  app=load_app();fixture=json.loads((ROOT/'tests'/'fixtures'/'session_ed25519_v1_cases.json').read_text(encoding='utf-8'));public=base64.urlsafe_b64decode(fixture['key']['public_key_b64url']+'=');self.assertEqual('ed25519:'+hashlib.sha256(public).hexdigest(),fixture['key']['key_id']);self.assertEqual(hashlib.sha256(app._canonical(fixture['registration']).encode()).hexdigest(),fixture['registration_sha256']);self.assertEqual(('nimrod','codex','sentinel1'),tuple(fixture['registration'][name] for name in ('agent_id','provider','seat_or_host')))
  self.assertEqual({'signed_get','heartbeat','terminate','rotation'},{case['name'] for case in fixture['cases']})
  for case in fixture['cases']:
   payload=base64.urlsafe_b64decode(case['canonical_payload_b64url']+'==');signature=base64.urlsafe_b64decode(case['signature_b64url']+'==');self.assertEqual(hashlib.sha256(app._canonical(case['body']).encode()).hexdigest(),case['body_sha256']);self.assertTrue(app._ed25519_verify(public,signature,payload))
  rfc_public=bytes.fromhex('d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a');rfc_signature=bytes.fromhex('e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b');self.assertTrue(app._ed25519_verify(rfc_public,rfc_signature,b''));self.assertFalse(app._ed25519_verify(rfc_public,rfc_signature,b'changed'))
 def test_v5_copy_migrates_to_lost_and_rollback_copy_is_unchanged(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'registry.db';os.environ['REGISTRY_DB']=str(path);import registry.migrate as migrate;importlib.reload(migrate);db=sqlite3.connect(path,isolation_level=None)
   for statement in migrate._statements(migrate.SCHEMA):
    db.execute(statement)
    if statement.lstrip().upper().startswith('INSERT INTO REGISTRY_MIGRATIONS VALUES(5,'):break
   db.execute(f'PRAGMA application_id={migrate.APPLICATION_ID}');db.execute('PRAGMA user_version=5');db.execute("INSERT INTO agents VALUES('legacy','{}',1,1,'2026-01-01T00:00:00Z')");db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),'legacy','vendor','locator','seat',None,None,'ACTIVE','2026-01-01T00:00:00Z','2026-01-01T00:00:00Z',None,None,1,'2026-01-01T00:00:00Z','a'*64));db.commit();rollback=Path(td)/'rollback.db';shutil.copy2(path,rollback);before=rollback.read_bytes();migrate.migrate(db);self.assertEqual(6,db.execute('PRAGMA user_version').fetchone()[0]);self.assertEqual(('LOST','retired'),db.execute('SELECT status,credential_scheme FROM sessions').fetchone());self.assertNotIn('session_credential_sha256',{row[1] for row in db.execute('PRAGMA table_info(sessions)')});self.assertEqual('credential_scheme_retired',db.execute('SELECT action FROM session_journal').fetchone()[0]);self.assertEqual(before,rollback.read_bytes());db.close()
 def test_v5_shape_mismatch_fails_closed_without_advancing(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'registry.db';os.environ['REGISTRY_DB']=str(path);import registry.migrate as migrate;importlib.reload(migrate);db=sqlite3.connect(path,isolation_level=None)
   for statement in migrate._statements(migrate.SCHEMA):
    db.execute(statement)
    if statement.lstrip().upper().startswith('INSERT INTO REGISTRY_MIGRATIONS VALUES(5,'):break
   db.execute(f'PRAGMA application_id={migrate.APPLICATION_ID}');db.execute('PRAGMA user_version=5');db.execute('DROP TABLE session_credential_rotations');before=db.serialize()
   with self.assertRaisesRegex(RuntimeError,'shape mismatch'):migrate.migrate(db)
   self.assertEqual(before,db.serialize());self.assertEqual(5,db.execute('PRAGMA user_version').fetchone()[0]);db.close()
 def test_runtime_source_has_no_private_or_symmetric_credential(self):
  source=(ROOT/'registry'/'app.py').read_text(encoding='utf-8');self.assertNotIn('private_seed',source);self.assertNotIn('private_key',source);self.assertNotIn('SessionProof',source);self.assertNotIn('session_credential_sha256',source)
