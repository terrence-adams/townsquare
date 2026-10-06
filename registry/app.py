"""Internal Registry: separate SQLite authority with append-only journal/outbox.

It deliberately uses only stdlib.  Ledger publication is asynchronous and
idempotent through the outbox; this service has no foreign key or transaction
against the Ledger database.
"""
import hashlib,json,os,sqlite3,threading,time,uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

DB=Path(os.environ.get("REGISTRY_DB","/var/lib/registry/registry.db"))
TOKEN_FILE=os.environ.get("REGISTRY_TOKEN_FILE","/run/secrets/registry_api_token")
LEDGER_AUDIT_TOKEN_FILE=os.environ.get("REGISTRY_LEDGER_AUDIT_TOKEN_FILE","/run/secrets/ledger_registry_audit_token")
# Deliberately fixed Compose-internal origin/path; neither comes from a payload.
LEDGER_AUDIT_URL="http://ledger:8790/v1/native/registry-audit-events"
LEDGER_AUDIT_TIMEOUT_SECONDS=3
LEDGER_READINESS_URL="http://ledger:8790/health/ready"
LEDGER_READINESS_TOKEN_FILE=os.environ.get("LEDGER_READINESS_TOKEN_FILE","/run/secrets/registry_ledger_readiness_token")
def connect():
 d=sqlite3.connect(DB,timeout=5,isolation_level=None); d.row_factory=sqlite3.Row; d.execute("PRAGMA foreign_keys=ON"); d.execute("PRAGMA journal_mode=WAL"); d.execute("PRAGMA synchronous=FULL"); d.execute("PRAGMA busy_timeout=5000"); return d
SERVICE_ID='townsquare-registry-v0'; SCHEMA_VERSION=2; AUDIT_CONTRACT_VERSION='registry-ledger-audit-v1'
def compatible():
 if os.environ.get('REGISTRY_SERVICE_ID',SERVICE_ID)!=SERVICE_ID:return False
 if os.environ.get('REGISTRY_SCHEMA_HEAD',str(SCHEMA_VERSION))!=str(SCHEMA_VERSION):return False
 if os.environ.get('REGISTRY_AUDIT_CONTRACT_VERSION',AUDIT_CONTRACT_VERSION) != AUDIT_CONTRACT_VERSION:return False
 if os.environ.get('REGISTRY_LEDGER_SERVICE_ID','townsquare-ledger-v0')!='townsquare-ledger-v0':return False
 if os.environ.get('REGISTRY_LEDGER_SCHEMA_HEAD','14')!='14':return False
 if os.environ.get('REGISTRY_LEDGER_AUDIT_CONTRACT',AUDIT_CONTRACT_VERSION)!=AUDIT_CONTRACT_VERSION:return False
 try:
  d=connect(); row=d.execute('SELECT max(version) FROM registry_migrations').fetchone(); d.close(); return row and row[0]==SCHEMA_VERSION
 except Exception:return False
def token(): return Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
def ledger_audit_token():
 value=Path(LEDGER_AUDIT_TOKEN_FILE).read_text(encoding="utf-8").strip()
 if not value: raise RuntimeError('registry audit credential is empty')
 return value
def ledger_readiness_token():
 value=Path(os.environ.get('REGISTRY_PEER_READINESS_TOKEN_FILE','/run/secrets/ledger_registry_readiness_token')).read_text(encoding='utf-8').strip()
 if not value: raise RuntimeError('registry readiness credential is empty')
 return value
def peer_ready():
 """Live fixed-origin Ledger tuple exchange; never accepts an env self-claim."""
 import urllib.request
 try:
  token=Path(LEDGER_READINESS_TOKEN_FILE).read_text(encoding='utf-8').strip()
  request=urllib.request.Request(LEDGER_READINESS_URL,headers={'Authorization':'Bearer '+token})
  with urllib.request.urlopen(request,timeout=LEDGER_AUDIT_TIMEOUT_SECONDS) as response: peer=json.load(response)
  return peer.get('ok') is True and peer.get('service_version')=='townsquare-ledger-v0' and peer.get('schema_version')==14 and peer.get('audit_contract_version')==AUDIT_CONTRACT_VERSION
 except Exception:return False
def claim(db,owner):
 """Atomically lease one pending stable UUID; expired claims are recoverable."""
 now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()); until=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(time.time()+30))
 row=db.execute("SELECT event_id FROM audit_outbox WHERE delivered_utc IS NULL AND (lease_until IS NULL OR lease_until<?) ORDER BY event_id LIMIT 1",(now,)).fetchone()
 if not row:return None
 changed=db.execute("UPDATE audit_outbox SET lease_owner=?,lease_until=? WHERE event_id=? AND delivered_utc IS NULL AND (lease_until IS NULL OR lease_until<?)",(owner,until,row['event_id'],now)).rowcount
 return row['event_id'] if changed else None
def acknowledge_delivery(db,event_id,owner,delivered_utc=None):
 """Durably acknowledge one successful fixed delivery, exactly once."""
 delivered_utc=delivered_utc or time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
 changed=db.execute(
  """UPDATE audit_outbox SET attempts=attempts+1,delivered_utc=?,last_error=NULL,
       lease_owner=NULL,lease_until=NULL
     WHERE event_id=? AND delivered_utc IS NULL AND lease_owner=?""",
  (delivered_utc,event_id,owner),
 ).rowcount
 if changed:return True
 row=db.execute("SELECT delivered_utc,lease_owner,lease_until FROM audit_outbox WHERE event_id=?",(event_id,)).fetchone()
 if row and row['delivered_utc'] is not None and row['lease_owner'] is None and row['lease_until'] is None:return False
 raise RuntimeError('registry audit acknowledgement lost its fixed outbox lease')
def deliver_once():
 if not compatible() or not peer_ready(): return # retain queue on mismatch/failure
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
def periodic_worker():
 while True:
  deliver_once(); time.sleep(5) # bounded periodic retry; attempts are durable
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,status,value):
  data=json.dumps(value,sort_keys=True).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  if self.path=="/health/live":return self.reply(200,{"ok":True})
  if self.path=="/health/ready":
   try:
    if self.headers.get('Authorization')!='Bearer '+ledger_readiness_token(): return self.reply(401,{"ok":False,"detail":"readiness authorization required"})
   except OSError:return self.reply(503,{"ok":False,"detail":"readiness credential unavailable"})
   try:
    d=connect(); version=d.execute("SELECT max(version) FROM registry_migrations").fetchone()[0]; pending=d.execute("SELECT count(*) FROM audit_outbox WHERE delivered_utc IS NULL").fetchone()[0]; failed=d.execute("SELECT count(*) FROM audit_outbox WHERE delivered_utc IS NULL AND last_error IS NOT NULL").fetchone()[0];d.close();
    tuple={"registry_service":SERVICE_ID,"registry_schema":SCHEMA_VERSION,"ledger_service":"townsquare-ledger-v0","ledger_schema":14,"audit_contract":AUDIT_CONTRACT_VERSION}
    if not compatible(): return self.reply(503,{"ok":False,"schema_version":version,"compatibility":tuple,"detail":"incompatible schema/audit contract"})
    if failed:return self.reply(503,{"ok":False,"schema_version":version,"compatibility":tuple,"pending_audit":pending,"delivery_failures":failed,"detail":"registry audit delivery degraded"})
    return self.reply(200,{"ok":True,"schema_version":version,"compatibility":tuple,"pending_audit":pending,"delivery_failures":0})
   except Exception as e:return self.reply(503,{"ok":False,"error":str(e)})
  self.reply(404,{"detail":"not found"})
 def do_POST(self):
  if self.path!="/v1/agents":return self.reply(404,{"detail":"not found"})
  if self.headers.get("Authorization")!="Bearer "+token():return self.reply(401,{"detail":"unauthorized"})
  key=self.headers.get("Idempotency-Key"); principal=self.headers.get("X-Registry-Principal")
  if not key or not principal:return self.reply(400,{"detail":"Idempotency-Key and X-Registry-Principal required"})
  try: body=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))))
  except Exception:return self.reply(400,{"detail":"invalid json"})
  agent=body.get("agent_id"); action=body.get("action")
  if not isinstance(agent,str) or action not in ("register","retire"):return self.reply(400,{"detail":"agent_id and action required"})
  canonical=json.dumps(body,sort_keys=True,separators=(',',':')); h=hashlib.sha256(canonical.encode()).hexdigest();d=connect()
  try:
   d.execute("BEGIN IMMEDIATE"); old=d.execute("SELECT * FROM requests WHERE principal=? AND idem_key=?",(principal,key)).fetchone()
   if old:
    if old['request_hash']!=h: d.rollback();return self.reply(409,{"detail":"idempotency key reused with different request"})
    d.rollback();return self.reply(200,json.loads(old['response_json']))
   current=d.execute("SELECT revision FROM agents WHERE agent_id=?",(agent,)).fetchone(); rev=(current['revision'] if current else 0)+1; event=str(uuid.uuid4());now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
   d.execute("INSERT INTO agents VALUES(?,?,?,?,?) ON CONFLICT(agent_id) DO UPDATE SET body_json=excluded.body_json,revision=excluded.revision,active=excluded.active,updated_utc=excluded.updated_utc",(agent,canonical,rev,int(action=="register"),now))
   d.execute("INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)",(event,agent,action,canonical,now));d.execute("INSERT INTO audit_outbox(event_id) VALUES(?)",(event,)); out={"event_id":event,"agent_id":agent,"revision":rev,"action":action};d.execute("INSERT INTO requests VALUES(?,?,?,?)",(principal,key,h,json.dumps(out,sort_keys=True)));d.commit();threading.Thread(target=deliver_once,daemon=True).start();self.reply(201,out)
  except Exception as e:d.rollback();self.reply(503,{"detail":str(e)})
  finally:d.close()
def main():
 if not compatible(): raise SystemExit('Registry schema/audit contract incompatible; run registry-migrate')
 threading.Thread(target=periodic_worker,daemon=True).start()
 ThreadingHTTPServer(("0.0.0.0",8789),Handler).serve_forever()
if __name__=="__main__":main()
