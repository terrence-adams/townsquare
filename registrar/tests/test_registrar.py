import hashlib,json,sqlite3,tempfile,threading,unittest,uuid
from pathlib import Path
from registrar.app.db import connect,migrate
import registrar.app.db as db_module
from registrar.app.filename import FilenameError,check_header,parse_filename
from registrar.app.service import Conflict,Forbidden,Registrar
from registrar.app import auth
from registrar.importer.legacy import plan
from registrar.verifier.job import verify as run_verifier
from registrar.app.runtime import ensure_runtime_mode,verification_enabled

ASSIGN=lambda who:[{"agent_id":who,"role":"responsible"}]
class RegistrarTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.path=str(Path(self.tmp.name)/"r.db")
        self.db=connect(self.path); migrate(self.db); self.db.executemany("INSERT INTO acls VALUES (?,?,?,NULL,NULL)",[("bishop","namespace","bishop"),("bishop","board","requests")]); self.r=Registrar(self.db)
    def tearDown(self):
        self.db.close(); self.tmp.cleanup()
    def root(self,key="root"):
        return self.r.reserve_root("bishop",key,{"prefix":"TS","utc_date":"20260917","namespace":"bishop","board":"requests","creator":"bishop","state":"OPEN","assignments":ASSIGN("bishop")})
    def test_idempotency_and_changed_payload(self):
        a=self.root(); self.assertEqual(a,self.root())
        with self.assertRaises(Conflict): self.r.reserve_root("bishop","root",{"namespace":"bishop","board":"requests","creator":"bishop","assignments":ASSIGN("bishop"),"state":"BLOCKED"})
    def test_concurrent_root_allocation(self):
        results=[]; errors=[]
        def run(i):
            db=connect(self.path); reg=Registrar(db)
            try: results.append(reg.reserve_root("bishop",f"r{i}",{"prefix":"TS","utc_date":"20260917","namespace":"bishop","board":"requests","creator":"bishop","assignments":ASSIGN("bishop")})["thread_id"])
            except Exception as exc: errors.append(exc)
            finally: db.close()
        threads=[threading.Thread(target=run,args=(i,)) for i in range(100)]
        [t.start() for t in threads]; [t.join() for t in threads]
        self.assertFalse(errors); self.assertEqual(100,len(set(results)))
    def test_concurrent_children_and_publication(self):
        root=self.root(); results=[]
        def run(i):
            db=connect(self.path)
            try: results.append(Registrar(db).reserve_post("bishop",f"p{i}",root["thread_id"],{"board":"requests","author":"bishop","state":"WORKING","assignments":ASSIGN("bishop")}))
            finally: db.close()
        threads=[threading.Thread(target=run,args=(i,)) for i in range(100)]
        [t.start() for t in threads]; [t.join() for t in threads]
        self.assertEqual(100,len({x["post_no"] for x in results}))
        post=results[0]; name=f'{root["thread_id"]}.{post["post_no"]:03d}-WORKING__by-bishop__pid-{post["pid"]}.txt'
        payload={"drive_file_id":"drive-A_1","drive_url":"https://drive.google.com/file/d/drive-A_1/view","filename":name,"content_sha256":"a"*64}
        self.assertEqual("published",self.r.publish("bishop","pub",post["post_uid"],payload)["registration_state"])
        self.assertEqual(self.r.publish("bishop","pub",post["post_uid"],payload),self.r.publish("bishop","pub",post["post_uid"],payload))
        other=results[1]
        other_name=f'{root["thread_id"]}.{other["post_no"]:03d}-WORKING__by-bishop__pid-{other["pid"]}.txt'
        with self.assertRaises(Conflict): self.r.publish("bishop","pub-other",other["post_uid"],{**payload,"filename":other_name})
        self.assertEqual(post["post_uid"],self.r.aliases(name)["matches"][0]["resource_uid"])
    def test_assignment_query(self):
        root=self.root(); rows=self.r.posts(assigned_to="bishop",role="responsible",root=root["thread_id"]); self.assertEqual(1,len(rows))
    def test_parser_pid_and_exact_binding(self):
        value="01ARZ3NDEKTSV4RRFFQ69G5FAV"; name=f"TS-20260917-bishop-004.001-WORKING__by-bishop__pid-{value}.txt"; parsed=parse_filename(name)
        self.assertEqual(value,parsed["pid"]); self.assertIsNone(parsed["slug"])
        check_header(parsed,{"id":"TS-20260917-bishop-004","event":"1","state":"WORKING","by":"bishop","post_id":value})
        with self.assertRaises(FilenameError): check_header(parsed,{"id":"TS-20260917-bishop-004","event":"1","state":"WORKING","by":"bishop","post_id":"0"*26})
        with self.assertRaises(FilenameError): parse_filename(name.replace("__pid-","__by-x__pid-"))
    def test_import_duplicate_is_deterministic(self):
        objects=[{"name":"TS-20260917-bishop-004.001-WORKING__by-bishop.txt","drive_file_id":"b","created_time":"2026-09-17T01:00:00Z"},{"name":"TS-20260917-bishop-004.001-BLOCKED__by-bishop.txt","drive_file_id":"a","created_time":"2026-09-17T02:00:00Z"}]
        a=plan(objects); b=plan(objects); self.assertEqual(a,b); self.assertEqual(2,len(a["posts"])); self.assertEqual(2,len(a["collisions"])); self.assertEqual(2,len({r["post_uid"] for r in a["posts"]}))
    def test_ac20_scope_revocation_and_acl_precede_allocation(self):
        class FakeHasher:
            def hash(self,value): return "hash:"+value
            def verify(self,digest,value):
                if digest!="hash:"+value: raise ValueError()
        old=auth.PasswordHasher; auth.PasswordHasher=FakeHasher
        try:
            token=auth.create_token(self.db,"bishop",["post:read"])
            with self.assertRaises(Forbidden): auth.authenticate_identity(self.db,token,"post:write")
            self.assertEqual(0,self.db.execute("SELECT count(*) FROM root_counters").fetchone()[0])
            self.db.execute("UPDATE tokens SET revoked_at='2026-09-17T00:00:00Z'")
            with self.assertRaises(Forbidden): auth.authenticate_identity(self.db,token,"post:read")
            self.db.execute("DELETE FROM acls WHERE kind='board'")
            with self.assertRaises(Forbidden): self.root("denied")
            self.assertEqual(0,self.db.execute("SELECT count(*) FROM root_counters").fetchone()[0])
        finally: auth.PasswordHasher=old
    def _published(self):
        root=self.root(); post=self.r.reserve_post("bishop","child",root["thread_id"],{"board":"requests","author":"bishop","state":"WORKING","assignments":ASSIGN("bishop")})
        name=f'{root["thread_id"]}.{post["post_no"]:03d}-WORKING__by-bishop__pid-{post["pid"]}.txt'
        payload={"drive_file_id":"drive-verified","drive_url":"https://drive.google.com/file/d/drive-verified/view","filename":name,"content_sha256":"b"*64}
        self.r.publish("bishop","publish",post["post_uid"],payload); return post,payload
    def test_ac29_independent_verifier_cas_and_failure_evidence(self):
        post,payload=self._published(); self.assertEqual("published",self.db.execute("SELECT registration_state FROM posts WHERE post_uid=?",(post["post_uid"],)).fetchone()[0])
        failed={**payload,"content_sha256":"c"*64,"header_binding":True,"signature_valid":True,"evidence":"hash differs"}
        result=self.r.verify_publication("verifier","verify-bad",post["post_uid"],failed)
        self.assertFalse(result["valid"]); self.assertEqual("published",result["registration_state"])
        self.assertEqual("b"*64,self.db.execute("SELECT content_sha256 FROM posts WHERE post_uid=?",(post["post_uid"],)).fetchone()[0])
        good={**payload,"header_binding":True,"signature_valid":True,"evidence":"Drive read matched"}
        self.assertEqual("drive_verified",self.r.verify_publication("verifier","verify-good",post["post_uid"],good)["registration_state"])
        with self.assertRaises(Conflict): self.r.verify_publication("verifier","verify-again",post["post_uid"],good)
    def test_ac30_publication_authorization_and_audited_delegation(self):
        root=self.root(); post=self.r.reserve_post("bishop","delegate-child",root["thread_id"],{"board":"requests","author":"bishop","state":"WORKING","assignments":ASSIGN("bishop")})
        name=f'{root["thread_id"]}.{post["post_no"]:03d}-WORKING__by-bishop__pid-{post["pid"]}.txt'; payload={"drive_file_id":"delegated","drive_url":"https://drive.google.com/file/d/delegated/view","filename":name,"content_sha256":"d"*64}
        with self.assertRaises(Forbidden): self.r.publish("robin","no-scope",post["post_uid"],payload)
        with self.assertRaises(Forbidden): self.r.publish("robin","scope-no-party",post["post_uid"],payload,{"post:delegate"})
        delegated={**payload,"represented_party":"bishop","delegation_reason":"bishop unavailable"}
        self.assertEqual("published",self.r.publish("robin","delegated",post["post_uid"],delegated,{"post:delegate"})["registration_state"])
        audit=self.db.execute("SELECT detail FROM audit_log WHERE operation='delegation'").fetchone()[0]
        self.assertIn("represented=bishop",audit); self.assertIn("reason=bishop unavailable",audit)
        other=self.r.reserve_post("bishop","wrong-by-child",root["thread_id"],{"board":"requests","author":"bishop","state":"WORKING","assignments":ASSIGN("bishop")})
        wrong_name=f'{root["thread_id"]}.{other["post_no"]:03d}-WORKING__by-robin__pid-{other["pid"]}.txt'
        with self.assertRaises(Forbidden): self.r.publish("bishop","wrong-by",other["post_uid"],{"drive_file_id":"wrong-by","drive_url":"https://drive.google.com/file/d/wrong-by/view","filename":wrong_name,"content_sha256":"e"*64})
    def test_ac33_immutable_import_promotion_and_second_run(self):
        objects=[{"name":"TS-20260917-legacy-009.001-WORKING__by-legacy.txt","drive_file_id":"legacy-a"},{"name":"TS-20260917-legacy-009.001-BLOCKED__by-legacy.txt","drive_file_id":"legacy-b"}]
        manifest=plan(objects); staged=self.r.stage_import("importer",manifest)
        with self.assertRaises(Conflict): self.r.promote_import("promoter",staged["run_id"],"0"*64)
        result=self.r.promote_import("promoter",staged["run_id"],staged["manifest_digest"]); self.assertEqual(2,result["created"])
        with self.assertRaises(Conflict): self.r.promote_import("promoter",staged["run_id"],staged["manifest_digest"])
        staged2=self.r.stage_import("importer",manifest); result2=self.r.promote_import("promoter",staged2["run_id"],staged2["manifest_digest"]); self.assertEqual(0,result2["created"])
        rows=self.db.execute("SELECT legacy_seq,post_no,drive_file_id FROM posts WHERE source='legacy_import' ORDER BY post_no").fetchall()
        self.assertEqual(2,len(rows)); self.assertEqual({"legacy-a","legacy-b"},{r["drive_file_id"] for r in rows}); self.assertEqual(2,len({r["post_no"] for r in rows}))
    def test_ac29_fake_rclone_and_http_verifier(self):
        pid="01ARZ3NDEKTSV4RRFFQ69G5FAV"; filename=f"TS-20260917-bishop-004.001-WORKING__by-bishop__pid-{pid}.txt"
        body=f"id: TS-20260917-bishop-004\nevent: 1\nstate: WORKING\nby: bishop\npost_id: {pid}\n---\nbody\n".encode(); calls=[]
        class Result:
            def __init__(self,out=b"",rc=0): self.stdout=out; self.stderr=b""; self.returncode=rc
        def runner(command,**kwargs):
            calls.append(command)
            if command[0]=="rclone" and command[1]=="lsjson": return Result(json.dumps([{"ID":"drive-z","Path":"Requests/"+filename},{"ID":"sig-z","Path":"Requests/"+filename+".sig"}]).encode())
            if command[0]=="rclone" and command[1]=="cat" and command[-1].endswith(".sig"): return Result(b"signature")
            if command[0]=="rclone" and command[1]=="cat": return Result(body)
            if command[0]=="ssh-keygen": return Result()
            return Result(rc=1)
        submitted={}
        class Response:
            def read(self): return b'{"registration_state":"drive_verified","valid":true}'
        def opener(request): submitted["request"]=request; return Response()
        result=run_verifier({"post_uid":"post-z","drive_file_id":"drive-z"},"readonly:TownSquare","/signers","https://registrar","secret",runner=runner,opener=opener)
        self.assertTrue(result["valid"]); envelope=json.loads(submitted["request"].data); payload=envelope["evidence"]; self.assertTrue(payload["header_binding"] and payload["signature_valid"]); self.assertEqual(hashlib.sha256(body).hexdigest(),payload["content_sha256"]); self.assertEqual("sig-z",payload["sidecar_drive_file_id"]); self.assertIn("signature",envelope["attestation"])
        self.assertTrue(all(c[1] in {"lsjson","cat"} for c in calls if c[0]=="rclone")); self.assertEqual("POST",submitted["request"].method)
    def test_fake_verifier_submits_failure_evidence(self):
        filename="TS-20260917-bishop-004.001-WORKING__by-bishop__pid-01ARZ3NDEKTSV4RRFFQ69G5FAV.txt"; submitted={}
        class Result:
            def __init__(self,out=b"",rc=0): self.stdout=out; self.stderr=b""; self.returncode=rc
        def runner(command,**kwargs):
            if command[1]=="lsjson": return Result(json.dumps([{"ID":"drive-bad","Path":filename},{"ID":"sig-bad","Path":filename+".sig"}]).encode())
            if command[0]=="rclone": return Result(b"id: wrong\n---\n")
            return Result(rc=1)
        class Response:
            def read(self): return b'{"registration_state":"published","valid":false}'
        def opener(request): submitted["payload"]=json.loads(request.data)["evidence"]; return Response()
        result=run_verifier({"post_uid":"post-bad","drive_file_id":"drive-bad"},"ro:x","/signers","https://registrar","secret",runner=runner,opener=opener)
        self.assertFalse(result["valid"]); self.assertFalse(submitted["payload"]["header_binding"]); self.assertIn("binding invalid",submitted["payload"]["evidence"])
    def test_ac40_unresolved_legacy_responsibility_is_null_and_observed(self):
        manifest=plan([{"name":"TS-20260917-legacy-010.001-WORKING__subject.txt","drive_file_id":"unresolved"}])
        self.assertEqual(["unresolved_responsibility"],manifest["posts"][0]["warnings"]); self.assertIsNone(manifest["posts"][0]["responsible_agent"])
        staged=self.r.stage_import("importer",manifest); self.r.promote_import("promoter",staged["run_id"],staged["manifest_digest"])
        post=self.db.execute("SELECT * FROM posts WHERE drive_file_id='unresolved'").fetchone(); self.assertIsNone(post["author_agent"])
        self.assertEqual(0,self.db.execute("SELECT count(*) FROM assignments WHERE post_uid=?",(post["post_uid"],)).fetchone()[0])
        obs=self.db.execute("SELECT * FROM import_observations WHERE drive_file_id='unresolved'").fetchone(); self.assertIn("unresolved_responsibility",obs["warnings_json"])
    def test_imported_root_advances_native_counter(self):
        manifest=plan([{"name":"TS-20260917-bishop-001.000-OPEN__by-bishop.txt","drive_file_id":"opening-1"}]); staged=self.r.stage_import("importer",manifest); self.r.promote_import("promoter",staged["run_id"],staged["manifest_digest"])
        native=self.r.reserve_root("bishop","after-import",{"prefix":"TS","utc_date":"20260917","namespace":"bishop","board":"requests","creator":"bishop","assignments":ASSIGN("bishop")})
        self.assertEqual("TS-20260917-bishop-002",native["thread_id"])
        imported=self.db.execute("SELECT opening_post_uid FROM roots WHERE thread_id='TS-20260917-bishop-001'").fetchone(); self.assertIsNotNone(imported[0])
    def test_reimport_metadata_mismatch_is_persisted(self):
        original=plan([{"name":"TS-20260917-legacy-011.001-WORKING__by-legacy.txt","drive_file_id":"same-drive","content_sha256":"a"*64}]); first=self.r.stage_import("i",original); self.r.promote_import("p",first["run_id"],first["manifest_digest"])
        altered=plan([{"name":"TS-20260917-legacy-011.001-BLOCKED__by-legacy.txt","drive_file_id":"same-drive","content_sha256":"b"*64}]); second=self.r.stage_import("i",altered); self.r.promote_import("p",second["run_id"],second["manifest_digest"])
        observation=self.db.execute("SELECT result,warnings_json FROM import_observations WHERE import_run_id=?",(second["run_id"],)).fetchone(); self.assertEqual("metadata-mismatch",observation["result"]); self.assertIn("metadata_mismatch",observation["warnings_json"])
        self.assertEqual("conflict",self.db.execute("SELECT registration_state FROM posts WHERE drive_file_id='same-drive'").fetchone()[0])
    def test_sidecars_preserve_identity_and_report_ambiguity(self):
        objects=[{"name":"TS-20260917-legacy-012.001-WORKING__by-legacy.txt","drive_file_id":"event-a"},{"name":"TS-20260917-legacy-012.001-WORKING__by-legacy.txt.sig","drive_file_id":"sig-a"},{"name":"orphan.txt.sig","drive_file_id":"sig-orphan"}]
        manifest=plan(objects); self.assertEqual("sig-a",manifest["artifacts"][0]["drive_file_id"]); self.assertIsNotNone(manifest["artifacts"][0]["parent_post_uid"]); self.assertEqual(["orphan_signature"],manifest["artifacts"][1]["warnings"])
        staged=self.r.stage_import("i",manifest); self.r.promote_import("p",staged["run_id"],staged["manifest_digest"])
        self.assertEqual(2,self.db.execute("SELECT count(*) FROM artifacts").fetchone()[0]); self.assertEqual("orphan",self.db.execute("SELECT verification_state FROM artifacts WHERE drive_file_id='sig-orphan'").fetchone()[0])
        duplicate_name="TS-20260917-legacy-014.001-WORKING__by-legacy.txt"
        ambiguous=plan([{"name":duplicate_name,"drive_file_id":"dup-a"},{"name":duplicate_name,"drive_file_id":"dup-b"},{"name":duplicate_name+".sig","drive_file_id":"dup-sig"}])
        self.assertEqual(["ambiguous_signature_parent"],ambiguous["artifacts"][0]["warnings"]); self.assertIsNone(ambiguous["artifacts"][0]["parent_post_uid"])
        multiple=plan([{"name":duplicate_name,"drive_file_id":"single-event"},{"name":duplicate_name+".sig","drive_file_id":"sig-1"},{"name":duplicate_name+".sig","drive_file_id":"sig-2"}])
        self.assertTrue(all(a["warnings"]==["ambiguous_signature_parent"] and a["parent_post_uid"] is None for a in multiple["artifacts"]))
    def test_manifest_and_database_integrity_guards(self):
        bad=plan([{"name":"TS-20260917-legacy-013.001-WORKING__by-legacy.txt","drive_file_id":"bad"}]); bad["posts"][0]["post_uid"]=str(uuid.uuid4())
        with self.assertRaises(ValueError): self.r.stage_import("i",bad)
        root=self.root(); post=self.r.reserve_post("bishop","guard",root["thread_id"],{"board":"requests","author":"bishop","state":"WORKING","assignments":ASSIGN("bishop")})
        self.db.execute("DELETE FROM assignments WHERE post_uid=?",(post["post_uid"],))
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("UPDATE posts SET registration_state='published' WHERE post_uid=?",(post["post_uid"],))
        other=self.r.reserve_post("bishop","other",root["thread_id"],{"board":"requests","author":"bishop","state":"WORKING","assignments":ASSIGN("bishop")})
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("UPDATE roots SET opening_post_uid=? WHERE root_uid=?",(other["post_uid"],self.db.execute("SELECT root_uid FROM roots WHERE thread_id=?",(root["thread_id"],)).fetchone()[0]))
    def test_migration_failure_is_atomic_and_forward_nullable(self):
        self.assertEqual(0,next(r[3] for r in self.db.execute("PRAGMA table_info(posts)") if r[1]=="author_agent"))
        folder=Path(self.tmp.name)/"migrations"; folder.mkdir(); (folder/"999_bad.sql").write_text("CREATE TABLE must_rollback(x);\nTHIS IS INVALID;\n")
        old=db_module.MIGRATIONS; db_module.MIGRATIONS=folder
        try:
            with self.assertRaises(sqlite3.OperationalError): db_module.migrate(self.db)
            self.assertIsNone(self.db.execute("SELECT 1 FROM sqlite_master WHERE name='must_rollback'").fetchone())
        finally: db_module.MIGRATIONS=old
    def test_local_prototype_gates_and_total_url_validation(self):
        with self.assertRaises(RuntimeError): ensure_runtime_mode("production")
        self.assertFalse(verification_enabled(None)); self.assertTrue(verification_enabled("1"))
        root=self.root(); post=self.r.reserve_post("bishop","url",root["thread_id"],{"board":"requests","author":"bishop","state":"WORKING","assignments":ASSIGN("bishop")}); name=f'{root["thread_id"]}.{post["post_no"]:03d}-WORKING__by-bishop__pid-{post["pid"]}.txt'; base={"drive_file_id":"valid-id","filename":name,"content_sha256":"f"*64}
        for i,url in enumerate(("http://drive.google.com/file/d/valid-id/view","https://drive.google.com/file/d/valid-id/view?q=1","https://user@drive.google.com/file/d/valid-id/view","https://drive.google.com:444/file/d/valid-id/view")):
            with self.assertRaises(ValueError): self.r.publish("bishop",f"bad-url-{i}",post["post_uid"],{**base,"drive_url":url})
    def test_artifact_reimport_idempotency_and_changed_conflict(self):
        name="TS-20260917-legacy-015.001-WORKING__by-legacy.txt"
        objects=[{"name":name,"drive_file_id":"artifact-event"},{"name":name+".sig","drive_file_id":"artifact-sig","content_sha256":"1"*64}]
        manifest=plan(objects); first=self.r.stage_import("i",manifest); self.r.promote_import("p",first["run_id"],first["manifest_digest"])
        second=self.r.stage_import("i",manifest); result=self.r.promote_import("p",second["run_id"],second["manifest_digest"]); self.assertEqual(0,result["created"])
        observed={r["drive_file_id"]:r["result"] for r in self.db.execute("SELECT drive_file_id,result FROM import_observations WHERE import_run_id=?",(second["run_id"],))}; self.assertEqual({"artifact-event":"unchanged","artifact-sig":"unchanged"},observed)
        changed=plan([objects[0],{**objects[1],"content_sha256":"2"*64}]); third=self.r.stage_import("i",changed); self.r.promote_import("p",third["run_id"],third["manifest_digest"])
        obs=self.db.execute("SELECT result,warnings_json FROM import_observations WHERE import_run_id=? AND drive_file_id='artifact-sig'",(third["run_id"],)).fetchone(); self.assertEqual("conflict",obs["result"]); self.assertIn("artifact_metadata_mismatch",obs["warnings_json"])
        artifact=self.db.execute("SELECT content_sha256,verification_state FROM artifacts WHERE drive_file_id='artifact-sig'").fetchone(); self.assertEqual("1"*64,artifact["content_sha256"]); self.assertEqual("conflict",artifact["verification_state"])
    def test_import_never_reuses_burned_child_number(self):
        root=self.root(); root_uid=self.db.execute("SELECT root_uid FROM roots WHERE thread_id=?",(root["thread_id"],)).fetchone()[0]; self.db.execute("UPDATE roots SET next_post_no=10 WHERE root_uid=?",(root_uid,))
        manifest=plan([{"name":root["thread_id"]+".005-WORKING__by-bishop.txt","drive_file_id":"burned-gap"}]); staged=self.r.stage_import("i",manifest); self.r.promote_import("p",staged["run_id"],staged["manifest_digest"])
        imported=self.db.execute("SELECT post_no FROM posts WHERE drive_file_id='burned-gap'").fetchone()[0]; self.assertEqual(10,imported); self.assertEqual(11,self.db.execute("SELECT next_post_no FROM roots WHERE root_uid=?",(root_uid,)).fetchone()[0])
        self.assertIsNone(self.db.execute("SELECT 1 FROM posts WHERE root_uid=? AND post_no=5",(root_uid,)).fetchone())
    def test_opening_insert_and_cross_root_guards(self):
        root_a=self.root("root-a"); root_b=self.r.reserve_root("bishop","root-b",{"prefix":"TS","utc_date":"20260917","namespace":"bishop","board":"requests","creator":"bishop","assignments":ASSIGN("bishop")})
        row=self.db.execute("SELECT * FROM roots WHERE thread_id=?",(root_a["thread_id"],)).fetchone()
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("INSERT INTO roots VALUES (?,?,?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),"TS-20260917-bishop-999","TS","20260917","bishop",999,str(uuid.uuid4()),1,"legacy","bishop",row["created_at"]))
        root_a_uid=row["root_uid"]
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("UPDATE roots SET opening_post_uid=? WHERE root_uid=?",(root_b["post_uid"],root_a_uid))
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("UPDATE roots SET opening_post_uid=? WHERE root_uid=?",(str(uuid.uuid4()),root_a_uid))

    # --- WS3 phase A (jackie-chan, 2026-09-22): migration 009 + auth scope fix ---

    def test_migration_009_applies_forward_on_pre009_db_and_readiness_passes(self):
        """QA requirement: migration 009 applies forward on a COPY of a
        pre-009 fixture DB (mirrors the existing
        test_migration_failure_is_atomic_and_forward_nullable technique of
        swapping db_module.MIGRATIONS to a partial folder)."""
        tmp2=tempfile.TemporaryDirectory()
        try:
            path2=str(Path(tmp2.name)/"pre009.db"); db2=connect(path2)
            folder=Path(tmp2.name)/"migrations"; folder.mkdir()
            for p in sorted(db_module.MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")):
                if int(p.name[:3])<9: (folder/p.name).write_text(p.read_text())
            old=db_module.MIGRATIONS; db_module.MIGRATIONS=folder
            try: migrate(db2)
            finally: db_module.MIGRATIONS=old
            cols_before=[r[1] for r in db2.execute("PRAGMA table_info(posts)")]
            self.assertNotIn("drive_created_at",cols_before)
            migrate(db2)  # forward, with the real (009-including) migrations folder
            cols_after={r[1]:r for r in db2.execute("PRAGMA table_info(posts)")}
            self.assertIn("drive_created_at",cols_after)
            self.assertEqual(0,cols_after["drive_created_at"][3])  # nullable (notnull==0)
            self.assertIsNone(db2.execute("SELECT drive_created_at FROM posts LIMIT 1").fetchone())
            db2.execute("PRAGMA integrity_check").fetchone()  # readiness: DB still coherent
            db2.close()
        finally: tmp2.cleanup()

    def test_promote_import_populates_drive_created_at_from_manifest(self):
        manifest=plan([{"name":"TS-20260917-legacy-020.001-WORKING__by-legacy.txt","drive_file_id":"created-time-a","created_time":"2026-09-01T12:00:00Z"}])
        staged=self.r.stage_import("importer",manifest); self.r.promote_import("promoter",staged["run_id"],staged["manifest_digest"])
        row=self.db.execute("SELECT drive_created_at FROM posts WHERE drive_file_id='created-time-a'").fetchone()
        self.assertEqual("2026-09-01T12:00:00Z",row["drive_created_at"])
        manifest2=plan([{"name":"TS-20260917-legacy-021.001-WORKING__by-legacy.txt","drive_file_id":"created-time-b"}])
        staged2=self.r.stage_import("importer",manifest2); self.r.promote_import("promoter",staged2["run_id"],staged2["manifest_digest"])
        row2=self.db.execute("SELECT drive_created_at FROM posts WHERE drive_file_id='created-time-b'").fetchone()
        self.assertIsNone(row2["drive_created_at"])

    def test_native_posts_have_null_drive_created_at(self):
        root=self.root()
        self.assertIsNone(self.db.execute("SELECT drive_created_at FROM posts WHERE post_uid=?",(root["post_uid"],)).fetchone()[0])

    def test_trashed_rows_never_reach_the_database_end_to_end(self):
        """WS3 item 2, end-to-end: a mixed active+trashed inventory only
        stages/promotes the active posts. Trashed rows are structurally
        absent from the manifest's posts/artifacts (they never even reach
        stage_import), so they cannot be promoted -- confirmed by re-running
        the whole stage->promote->stage->promote cycle and asserting
        created==0 the second time, matching the pre-existing idempotency
        proof but now over a manifest that also contains excluded rows."""
        objects=[
            {"name":"TS-20260917-legacy-030.000-OPEN__by-legacy.txt","drive_file_id":"trash-e2e-active","parent_folder_path":"Requests","trashed":False},
            {"name":"TS-20260917-legacy-031.000-OPEN__by-legacy.txt","drive_file_id":"trash-e2e-trashed","parent_folder_path":"Requests","trashed":True},
        ]
        manifest=plan(objects)
        self.assertEqual(1,len(manifest["posts"]))
        self.assertEqual("trash-e2e-active",manifest["posts"][0]["drive_file_id"])
        self.assertEqual(1,manifest["counts"]["trashed_board_objects"])
        staged=self.r.stage_import("importer",manifest)
        result=self.r.promote_import("promoter",staged["run_id"],staged["manifest_digest"])
        self.assertEqual(1,result["created"])
        self.assertIsNotNone(self.db.execute("SELECT 1 FROM posts WHERE drive_file_id='trash-e2e-active'").fetchone())
        self.assertIsNone(self.db.execute("SELECT 1 FROM posts WHERE drive_file_id='trash-e2e-trashed'").fetchone())
        staged2=self.r.stage_import("importer",manifest); result2=self.r.promote_import("promoter",staged2["run_id"],staged2["manifest_digest"])
        self.assertEqual(0,result2["created"])

    def test_auth_bootstrap_scope_flag_is_not_silently_unioned_with_post_write(self):
        """WS3 item 7: --scope used to action='append' onto a
        default=['post:write'], so every minted token silently carried
        post:write regardless of what was requested. Confirms the fix
        produces an EXACTLY-least-privilege token."""
        class FakeHasher:
            def hash(self,value): return "hash:"+value
            def verify(self,digest,value):
                if digest!="hash:"+value: raise ValueError()
        old=auth.PasswordHasher; auth.PasswordHasher=FakeHasher
        tmp3=tempfile.TemporaryDirectory()
        try:
            import sys,gc
            dbpath=str(Path(tmp3.name)/"auth.db")
            old_argv=sys.argv
            sys.argv=["auth","--db",dbpath,"--principal","importer-bot","--scope","admin:import-stage"]
            try: auth.main()
            finally: sys.argv=old_argv
            gc.collect()  # release main()'s own internal db connection (Windows file lock) before cleanup
            db3=connect(dbpath)
            scopes=set(db3.execute("SELECT scopes FROM tokens WHERE principal_id='importer-bot'").fetchone()[0].split())
            self.assertEqual({"admin:import-stage"},scopes)
            self.assertNotIn("post:write",scopes)
            db3.close(); gc.collect()
        finally:
            tmp3.cleanup(); auth.PasswordHasher=old

    def test_auth_bootstrap_omitted_scope_still_defaults_to_post_write(self):
        """The convenience default must survive for the truly-unset case --
        this is a post-parse fallback, not a removal of the default."""
        class FakeHasher:
            def hash(self,value): return "hash:"+value
            def verify(self,digest,value):
                if digest!="hash:"+value: raise ValueError()
        old=auth.PasswordHasher; auth.PasswordHasher=FakeHasher
        tmp4=tempfile.TemporaryDirectory()
        try:
            import sys,gc
            dbpath=str(Path(tmp4.name)/"auth2.db")
            old_argv=sys.argv
            sys.argv=["auth","--db",dbpath,"--principal","legacy-bot"]
            try: auth.main()
            finally: sys.argv=old_argv
            gc.collect()
            db4=connect(dbpath)
            scopes=set(db4.execute("SELECT scopes FROM tokens WHERE principal_id='legacy-bot'").fetchone()[0].split())
            self.assertEqual({"post:write"},scopes)
            db4.close(); gc.collect()
        finally:
            tmp4.cleanup(); auth.PasswordHasher=old

if __name__=="__main__": unittest.main()
