from __future__ import annotations
import hashlib,json,re,secrets,sqlite3,time,uuid
from datetime import datetime,timedelta,timezone
from urllib.parse import urlparse,unquote
from pathlib import Path
from .filename import parse_filename

VALID=re.compile(r"^[a-z][a-z0-9-]{0,62}$"); PREFIXES={"TS","BB","SEEK","OFFER","WANT"}; CROCKFORD="0123456789ABCDEFGHJKMNPQRSTVWXYZ"
class Conflict(Exception): pass
class Invalid(ValueError): pass
class Forbidden(PermissionError): pass
def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def uuid7():
    value=(int(time.time()*1000)<<80)|(0x7<<76)|(secrets.randbits(12)<<64)|(0b10<<62)|secrets.randbits(62); return uuid.UUID(int=value)
def pid(value):
    n=value.int; chars=[]
    for _ in range(26): chars.append(CROCKFORD[n&31]); n>>=5
    return "".join(reversed(chars))
def canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)

class Registrar:
    def __init__(self,db): self.db=db
    def norm(self,value,label="value"):
        value=value.strip().lower()
        if not VALID.fullmatch(value): raise Invalid(f"invalid {label}")
        return value
    def authorize(self,principal,namespace,board):
        instant=now()
        for kind,value in (("namespace",namespace),("board",board)):
            row=self.db.execute("SELECT 1 FROM acls WHERE principal_id=? AND kind=? AND value=? AND (not_before IS NULL OR not_before<=?) AND (expires_at IS NULL OR expires_at>?)",(principal,kind,value,instant,instant)).fetchone()
            if not row: raise Forbidden(f"{kind} not allowed")
    def idem(self,principal,operation,key,payload,create):
        if not key or len(key)>200: raise Invalid("Idempotency-Key required")
        digest=hashlib.sha256(canonical(payload).encode()).hexdigest(); self.db.execute("BEGIN IMMEDIATE")
        try:
            old=self.db.execute("SELECT * FROM idempotency_records WHERE principal_id=? AND operation=? AND idempotency_key=?",(principal,operation,key)).fetchone()
            if old:
                if old["canonical_payload_sha256"]!=digest: raise Conflict("idempotency key payload mismatch")
                self.db.commit(); return json.loads(old["response_json"])
            result,kind,uid=create()
            self.db.execute("INSERT INTO idempotency_records VALUES (?,?,?,?,?,?,?,?,?,NULL)",(principal,operation,key,digest,201,canonical(result),kind,uid,now()))
            self.db.execute("INSERT INTO audit_log(at,principal_id,operation,outcome,detail) VALUES (?,?,?,?,?)",(now(),principal,operation,"ok",kind+":"+uid)); self.db.commit(); return result
        except Exception: self.db.rollback(); raise
    def assign(self,post_uid,items,principal):
        rows=[]
        for item in items:
            agent=self.norm(item["agent_id"],"agent_id"); role=item["role"]
            if role not in {"responsible","requester","assignee","reviewer","observer"}: raise Invalid("invalid role")
            rows.append((post_uid,agent,role,1))
        if not any(r[1]==principal and r[2]=="responsible" for r in rows): raise Forbidden("principal must be responsible")
        self.db.executemany("INSERT INTO assignments VALUES (?,?,?,?)",rows)
    def reserve_root(self,principal,key,payload):
        p=dict(payload); prefix=p.get("prefix","TS").upper(); ns=self.norm(p["namespace"],"namespace"); board=self.norm(p["board"],"board")
        if prefix not in PREFIXES: raise Invalid("invalid prefix")
        if self.norm(p.get("creator",principal))!=principal: raise Forbidden("creator mismatch")
        self.authorize(principal,ns,board); p.update(prefix=prefix,namespace=ns,board=board,creator=principal)
        def create():
            date=p.get("utc_date") or datetime.now(timezone.utc).strftime("%Y%m%d"); self.db.execute("INSERT OR IGNORE INTO root_counters VALUES (?,?,?,1)",(prefix,date,ns))
            number=self.db.execute("SELECT next_local_number FROM root_counters WHERE prefix=? AND utc_date=? AND namespace=?",(prefix,date,ns)).fetchone()[0]
            self.db.execute("UPDATE root_counters SET next_local_number=? WHERE prefix=? AND utc_date=? AND namespace=?",(number+1,prefix,date,ns))
            ru,pu=str(uuid7()),str(uuid7()); thread=f"{prefix}-{date}-{ns}-{number:03d}"; created=now()
            self.db.execute("INSERT INTO roots VALUES (?,?,?,?,?,?,?,?,?,?,?)",(ru,thread,prefix,date,ns,number,None,1,"reserved",principal,created))
            self.db.execute("INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(pu,ru,0,0,p.get("state","OPEN"),board,None,None,created,principal,None,None,None,"reserved",(datetime.now(timezone.utc)+timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),"native"))
            self.db.execute("UPDATE roots SET opening_post_uid=? WHERE root_uid=?",(pu,ru))
            self.assign(pu,p["assignments"],principal)
            self.db.execute("INSERT INTO aliases VALUES (?,?,?)",(thread,"root",ru))
            self.db.execute("INSERT INTO aliases VALUES (?,?,?)",(thread+"#000","post",pu))
            return {"root_uid":ru,"thread_id":thread,"post_uid":pu,"post_no":0,"pid":pid(uuid.UUID(pu))},"root",ru
        return self.idem(principal,"reserve_root",key,p,create)
    def reserve_post(self,principal,key,thread,payload):
        p=dict(payload); root=self.db.execute("SELECT * FROM roots WHERE thread_id=?",(thread,)).fetchone()
        if not root: raise Invalid("unknown root")
        board=self.norm(p["board"],"board"); self.authorize(principal,root["namespace"],board)
        if self.norm(p.get("author",principal))!=principal: raise Forbidden("author mismatch")
        p.update(board=board,author=principal,thread_id=thread)
        def create():
            no=self.db.execute("SELECT next_post_no FROM roots WHERE root_uid=?",(root["root_uid"],)).fetchone()[0]; self.db.execute("UPDATE roots SET next_post_no=? WHERE root_uid=?",(no+1,root["root_uid"]))
            pu,created=str(uuid7()),now(); self.db.execute("INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(pu,root["root_uid"],no,no,p["state"],board,None,None,created,principal,None,None,None,"reserved",(datetime.now(timezone.utc)+timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),"native"))
            self.assign(pu,p["assignments"],principal)
            self.db.execute("INSERT INTO aliases VALUES (?,?,?)",(f"{thread}#{no:03d}","post",pu))
            return {"post_uid":pu,"thread_id":thread,"post_no":no,"pid":pid(uuid.UUID(pu))},"post",pu
        return self.idem(principal,"reserve_post",key,p,create)
    def publish(self,principal,key,post_uid,payload,scopes=frozenset()):
        p=dict(payload)
        def create():
            row=self.db.execute("SELECT p.*,r.thread_id FROM posts p JOIN roots r USING(root_uid) WHERE post_uid=?",(post_uid,)).fetchone()
            if not row: raise Invalid("unknown post")
            if row["registration_state"]!="reserved": raise Conflict("post is not reserved")
            responsible=self.db.execute("SELECT 1 FROM assignments WHERE post_uid=? AND agent_id=? AND role='responsible' AND active=1",(post_uid,principal)).fetchone()
            represented=p.get("represented_party")
            if row["author_agent"]!=principal or not responsible:
                if "post:delegate" not in scopes or represented!=row["author_agent"]: raise Forbidden("publisher is not author/responsible")
                reason=p.get("delegation_reason","").strip()
                if not reason: raise Invalid("delegation_reason required")
                self.db.execute("INSERT INTO audit_log(at,principal_id,operation,outcome,detail) VALUES (?,?,?,?,?)",(now(),principal,"delegation","ok",f"represented={represented};post={post_uid};reason={reason}"))
            fid=p["drive_file_id"]
            if not isinstance(fid,str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,200}",fid): raise Invalid("invalid Drive file ID")
            try: parsed=urlparse(p["drive_url"]); port=parsed.port
            except (TypeError,ValueError) as exc: raise Invalid("invalid Drive URL") from exc
            if parsed.scheme!="https" or parsed.hostname!="drive.google.com" or parsed.username or parsed.password or port not in (None,443) or parsed.query or parsed.fragment or parsed.path!=f"/file/d/{fid}/view": raise Invalid("Drive URL/file ID mismatch")
            if not isinstance(p.get("filename"),str) or len(p["filename"])>255 or Path(p["filename"]).name!=p["filename"]: raise Invalid("filename must be a basename")
            meta=parse_filename(p["filename"])
            if meta["thread"]!=row["thread_id"] or meta["seq"]!=row["post_no"] or meta.get("pid")!=pid(uuid.UUID(post_uid)): raise Invalid("filename does not bind reservation")
            if meta.get("by") != row["author_agent"]: raise Forbidden("filename by field does not match post author")
            sha=p["content_sha256"].lower()
            if not re.fullmatch(r"[0-9a-f]{64}",sha): raise Invalid("invalid sha256")
            url=f"https://drive.google.com/file/d/{fid}/view"
            try:
                self.db.execute("UPDATE posts SET drive_file_id=?,drive_url=?,filename=?,content_sha256=?,registration_state='published' WHERE post_uid=?",(fid,url,p["filename"],sha,post_uid))
                self.db.execute("INSERT INTO aliases VALUES (?,?,?)",(p["filename"],"post",post_uid))
            except sqlite3.IntegrityError as exc: raise Conflict("Drive file already bound") from exc
            return {"post_uid":post_uid,"registration_state":"published","drive_file_id":fid,"drive_url":url},"post",post_uid
        return self.idem(principal,"publish",key,p,create)
    def verify_publication(self,principal,key,post_uid,payload):
        p=dict(payload)
        def create():
            row=self.db.execute("SELECT * FROM posts WHERE post_uid=?",(post_uid,)).fetchone()
            if not row: raise Invalid("unknown post")
            if row["registration_state"]!="published": raise Conflict("verification requires published state")
            observed={k:p.get(k) for k in ("drive_file_id","drive_url","filename","content_sha256")}
            metadata_ok=all(observed[k]==row[k] for k in observed)
            checks=metadata_ok and p.get("header_binding") is True and p.get("signature_valid") is True
            evidence=str(p.get("evidence","")).strip()
            if not evidence: raise Invalid("verification evidence required")
            self.db.execute("INSERT INTO verification_reports(post_uid,verifier_principal,observed_json,valid,evidence,created_at) VALUES (?,?,?,?,?,?)",(post_uid,principal,canonical(observed),int(checks),evidence,now()))
            if checks:
                changed=self.db.execute("UPDATE posts SET registration_state='drive_verified' WHERE post_uid=? AND registration_state='published'",(post_uid,)).rowcount
                if changed!=1: raise Conflict("verification compare-and-set failed")
                state="drive_verified"
            else:
                state="published"
            return {"post_uid":post_uid,"registration_state":state,"valid":checks,"evidence":evidence},"verification",post_uid
        return self.idem(principal,"verify_publication",key,p,create)
    def stage_import(self,principal,manifest):
        if not isinstance(manifest,dict) or manifest.get("dry_run") is not True or not isinstance(manifest.get("posts"),list) or not isinstance(manifest.get("artifacts",[]),list): raise Invalid("invalid import manifest schema")
        seen_drive=set(); seen_uid=set(); valid_uids=set()
        import_ns=uuid.UUID("b8a04d34-91ab-51b5-a12d-4e9994793b38")
        for item in manifest["posts"]:
            required={"thread_id","post_uid","post_no","legacy_seq","drive_file_id","filename","warnings"}
            if not required.issubset(item) or not isinstance(item["warnings"],list): raise Invalid("incomplete import post")
            meta=parse_filename(item["filename"]); expected=str(uuid.uuid5(import_ns,item["drive_file_id"]))
            if item["post_uid"]!=expected or item["thread_id"]!=meta["thread"] or int(item["legacy_seq"])!=meta["seq"]: raise Invalid("non-deterministic import relationship")
            if item["drive_file_id"] in seen_drive or item["post_uid"] in seen_uid: raise Invalid("duplicate import identity")
            seen_drive.add(item["drive_file_id"]); seen_uid.add(item["post_uid"]); valid_uids.add(item["post_uid"])
            if item.get("content_sha256") and not re.fullmatch(r"[0-9a-f]{64}",item["content_sha256"]): raise Invalid("invalid import content hash")
        for artifact in manifest.get("artifacts",[]):
            if not {"drive_file_id","filename","kind","parent_post_uid","warnings"}.issubset(artifact) or artifact["kind"]!="signature": raise Invalid("invalid artifact manifest")
            if artifact["drive_file_id"] in seen_drive: raise Invalid("duplicate Drive identity")
            if artifact["parent_post_uid"] is not None and artifact["parent_post_uid"] not in valid_uids: raise Invalid("artifact parent outside manifest")
            seen_drive.add(artifact["drive_file_id"])
        body=canonical(manifest); digest=hashlib.sha256(body.encode()).hexdigest(); run_id=str(uuid7())
        self.db.execute("INSERT INTO import_runs VALUES (?,?,?,?,?,?,NULL)",(run_id,digest,body,"validated",principal,now()))
        self.db.execute("INSERT INTO audit_log(at,principal_id,operation,outcome,detail) VALUES (?,?,?,?,?)",(now(),principal,"import_stage","ok",run_id+":"+digest))
        return {"run_id":run_id,"manifest_digest":digest,"status":"validated"}
    def promote_import(self,principal,run_id,digest):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            run=self.db.execute("SELECT * FROM import_runs WHERE run_id=?",(run_id,)).fetchone()
            if not run or run["status"]!="validated" or run["manifest_digest"]!=digest: raise Conflict("immutable validated import run/digest required")
            if hashlib.sha256(run["manifest_json"].encode()).hexdigest()!=digest: raise Conflict("stored manifest mutated")
            manifest=json.loads(run["manifest_json"]); created=0
            for item in manifest.get("posts",[]):
                metadata_hash=hashlib.sha256(canonical(item).encode()).hexdigest()
                existing=self.db.execute("SELECT p.*,r.thread_id FROM posts p JOIN roots r USING(root_uid) WHERE drive_file_id=?",(item["drive_file_id"],)).fetchone()
                if existing:
                    previous=self.db.execute("SELECT metadata_hash FROM import_observations WHERE drive_file_id=? ORDER BY rowid DESC LIMIT 1",(item["drive_file_id"],)).fetchone()
                    same=(existing["post_uid"]==item["post_uid"] and existing["filename"]==item["filename"] and existing["thread_id"]==item["thread_id"] and existing["legacy_seq"]==item["legacy_seq"] and existing["content_sha256"]==item.get("content_sha256") and (previous is None or previous[0]==metadata_hash))
                    result="unchanged" if same else "metadata-mismatch"; warnings=item.get("warnings",[])+([] if same else ["metadata_mismatch"])
                    self.db.execute("INSERT INTO import_observations VALUES (?,?,?,?,?,?)",(run_id,item["drive_file_id"],existing["post_uid"],metadata_hash,result,canonical(warnings)))
                    if not same: self.db.execute("UPDATE posts SET registration_state='conflict' WHERE post_uid=?",(existing["post_uid"],))
                    continue
                thread=item["thread_id"]; root=self.db.execute("SELECT * FROM roots WHERE thread_id=?",(thread,)).fetchone(); new_root=False
                meta=parse_filename(item["filename"])
                if not root:
                    ru=str(uuid.uuid5(uuid.UUID("8ed61424-d37f-5bc4-876b-7e5fe2457ed8"),thread)); ns=meta["namespace"] or "legacy"
                    self.db.execute("INSERT INTO roots VALUES (?,?,?,?,?,?,?,?,?,?,?)",(ru,thread,meta["prefix"],meta["date"],ns,meta["local_number"],None,1,"legacy",principal,now())); root=self.db.execute("SELECT * FROM roots WHERE root_uid=?",(ru,)).fetchone(); new_root=True
                    self.db.execute("INSERT OR IGNORE INTO aliases VALUES (?,?,?)",(thread,"root",ru))
                wanted=int(item["post_no"]); current_next=self.db.execute("SELECT next_post_no FROM roots WHERE root_uid=?",(root["root_uid"],)).fetchone()[0]
                occupied=self.db.execute("SELECT 1 FROM posts WHERE root_uid=? AND post_no=?",(root["root_uid"],wanted)).fetchone()
                if not new_root and (occupied or wanted<current_next): wanted=current_next
                post_uid=item["post_uid"]; author=item.get("responsible_agent")
                url=f'https://drive.google.com/file/d/{item["drive_file_id"]}/view'
                self.db.execute("INSERT INTO posts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(post_uid,root["root_uid"],wanted,item["legacy_seq"],meta["state"],item.get("board","legacy"),item["filename"],item.get("header_at"),now(),author,item.get("content_sha256"),item["drive_file_id"],url,"legacy",None,"legacy_import"))
                if author:
                    self.db.execute("INSERT INTO assignments VALUES (?,?,?,1)",(post_uid,author,"responsible"))
                self.db.execute("INSERT OR IGNORE INTO aliases VALUES (?,?,?)",(item["filename"],"post",post_uid)); self.db.execute("UPDATE roots SET next_post_no=CASE WHEN next_post_no<? THEN ? ELSE next_post_no END WHERE root_uid=?",(wanted+1,wanted+1,root["root_uid"])); created+=1
                if wanted==0: self.db.execute("UPDATE roots SET opening_post_uid=COALESCE(opening_post_uid,?) WHERE root_uid=?",(post_uid,root["root_uid"]))
                self.db.execute("INSERT INTO root_counters(prefix,utc_date,namespace,next_local_number) VALUES (?,?,?,?) ON CONFLICT(prefix,utc_date,namespace) DO UPDATE SET next_local_number=CASE WHEN next_local_number<excluded.next_local_number THEN excluded.next_local_number ELSE next_local_number END",(meta["prefix"],meta["date"],meta["namespace"] or "legacy",meta["local_number"]+1))
                result="warning" if item.get("warnings") else "imported"
                self.db.execute("INSERT INTO import_observations VALUES (?,?,?,?,?,?)",(run_id,item["drive_file_id"],post_uid,metadata_hash,result,canonical(item.get("warnings",[]))))
            for artifact in manifest.get("artifacts",[]):
                warnings=artifact.get("warnings",[]); parent=artifact.get("parent_post_uid")
                state="orphan" if parent is None else ("conflict" if warnings else "observed")
                url=f'https://drive.google.com/file/d/{artifact["drive_file_id"]}/view'
                ahash=hashlib.sha256(canonical(artifact).encode()).hexdigest(); result="orphan-artifact" if parent is None else "artifact"
                existing_artifact=self.db.execute("SELECT * FROM artifacts WHERE drive_file_id=?",(artifact["drive_file_id"],)).fetchone()
                if existing_artifact:
                    prior=self.db.execute("SELECT metadata_hash FROM import_observations WHERE drive_file_id=? ORDER BY rowid DESC LIMIT 1",(artifact["drive_file_id"],)).fetchone()
                    same=(existing_artifact["parent_post_uid"]==parent and existing_artifact["kind"]=="signature" and existing_artifact["drive_url"]==url and existing_artifact["filename"]==artifact["filename"] and existing_artifact["content_sha256"]==artifact.get("content_sha256") and (prior is None or prior[0]==ahash))
                    if same: result="unchanged"
                    else:
                        result="conflict"; warnings=warnings+["artifact_metadata_mismatch"]
                        self.db.execute("UPDATE artifacts SET verification_state='conflict' WHERE drive_file_id=?",(artifact["drive_file_id"],))
                else:
                    self.db.execute("INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)",(artifact["drive_file_id"],parent,"signature",url,artifact["filename"],artifact.get("content_sha256"),state))
                self.db.execute("INSERT INTO import_observations VALUES (?,?,?,?,?,?)",(run_id,artifact["drive_file_id"],parent,ahash,result,canonical(warnings)))
            self.db.execute("UPDATE import_runs SET status='promoted',promoted_at=? WHERE run_id=? AND status='validated'",(now(),run_id))
            self.db.execute("INSERT INTO audit_log(at,principal_id,operation,outcome,detail) VALUES (?,?,?,?,?)",(now(),principal,"import_promote","ok",f"{run_id}:{digest}:created={created}")); self.db.commit()
            return {"run_id":run_id,"manifest_digest":digest,"status":"promoted","created":created}
        except Exception: self.db.rollback(); raise
    def posts(self,**filters):
        sql="SELECT p.*,r.thread_id FROM posts p JOIN roots r USING(root_uid)"; where=[]; args=[]
        if filters.get("assigned_to"):
            sql+=" JOIN assignments a ON a.post_uid=p.post_uid"; where.append("a.agent_id=? AND a.active=1"); args.append(filters["assigned_to"])
            if filters.get("role"): where.append("a.role=?"); args.append(filters["role"])
        for key,col in (("state","p.state"),("board","p.board"),("registration_state","p.registration_state"),("root","r.thread_id")):
            if filters.get(key): where.append(col+"=?"); args.append(filters[key])
        if where: sql+=" WHERE "+" AND ".join(where)
        sql+=" ORDER BY p.created_at,p.post_uid LIMIT ?"; args.append(min(int(filters.get("limit",100)),200)); return [dict(r) for r in self.db.execute(sql,args)]
    def aliases(self,alias):
        rows=[dict(r) for r in self.db.execute("SELECT * FROM aliases WHERE alias=? ORDER BY resource_uid",(alias,))]; return {"alias":alias,"ambiguous":len(rows)>1,"matches":rows}
