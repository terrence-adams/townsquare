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
LEDGER_AUDIT_URL=os.environ.get("LEDGER_AUDIT_URL","")
def connect():
 d=sqlite3.connect(DB,timeout=5,isolation_level=None); d.row_factory=sqlite3.Row; d.execute("PRAGMA foreign_keys=ON"); d.execute("PRAGMA journal_mode=WAL"); d.execute("PRAGMA synchronous=FULL"); d.execute("PRAGMA busy_timeout=5000"); return d
SCHEMA_VERSION=1; AUDIT_CONTRACT_VERSION='1'
def compatible():
 if os.environ.get('REGISTRY_AUDIT_CONTRACT_VERSION','1') != AUDIT_CONTRACT_VERSION:return False
 try:
  d=connect(); row=d.execute('SELECT max(version) FROM registry_migrations').fetchone(); d.close(); return row and row[0]==SCHEMA_VERSION
 except Exception:return False
def token(): return Path(TOKEN_FILE).read_text(encoding="utf-8").strip()
def deliver_once():
 if not compatible(): return # retain outbox rows; mismatch is never a drop condition
 if not LEDGER_AUDIT_URL:return
 import urllib.request
 d=connect()
 try:
  for r in d.execute("SELECT j.* FROM journal j JOIN audit_outbox o ON o.event_id=j.event_id WHERE o.delivered_utc IS NULL ORDER BY j.seq LIMIT 20"):
   data=json.dumps({"registry_event":dict(r)}).encode()
   try:
    req=urllib.request.Request(LEDGER_AUDIT_URL,data=data,headers={"Content-Type":"application/json","Idempotency-Key":"registry-"+r['event_id']},method="POST")
    with urllib.request.urlopen(req,timeout=3) as response:
     if response.status//100!=2:raise RuntimeError(str(response.status))
    d.execute("UPDATE audit_outbox SET attempts=attempts+1,delivered_utc=strftime('%Y-%m-%dT%H:%M:%SZ','now'),last_error=NULL WHERE event_id=?",(r['event_id'],))
   except Exception as e:d.execute("UPDATE audit_outbox SET attempts=attempts+1,last_error=? WHERE event_id=?",(str(e)[:500],r['event_id']))
 finally:d.close()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def reply(self,status,value):
  data=json.dumps(value,sort_keys=True).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  if self.path=="/health/live":return self.reply(200,{"ok":True})
  if self.path=="/health/ready":
   try:
    d=connect(); version=d.execute("SELECT max(version) FROM registry_migrations").fetchone()[0]; pending=d.execute("SELECT count(*) FROM audit_outbox WHERE delivered_utc IS NULL").fetchone()[0];d.close();
    if not compatible(): return self.reply(503,{"ok":False,"schema_version":version,"audit_contract_version":AUDIT_CONTRACT_VERSION,"detail":"incompatible schema/audit contract"})
    return self.reply(200,{"ok":True,"schema_version":version,"audit_contract_version":AUDIT_CONTRACT_VERSION,"pending_audit":pending})
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
   d.execute("INSERT INTO journal(event_id,agent_id,action,body_json,committed_utc) VALUES(?,?,?,?,?)",(event,agent,action,canonical,now));d.execute("INSERT INTO audit_outbox(event_id) VALUES(?)",(event,)); out={"event_id":event,"agent_id":agent,"revision":rev,"action":action};d.execute("INSERT INTO requests VALUES(?,?,?,?)",(principal,key,h,json.dumps(out,sort_keys=True)));d.commit();self.reply(201,out)
  except Exception as e:d.rollback();self.reply(503,{"detail":str(e)})
  finally:d.close()
def main():
 if not compatible(): raise SystemExit('Registry schema/audit contract incompatible; run registry-migrate')
 ThreadingHTTPServer(("0.0.0.0",8789),Handler).serve_forever()
if __name__=="__main__":main()
