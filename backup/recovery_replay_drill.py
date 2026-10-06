#!/usr/bin/env python3
"""Offline exactly-once replay drill over restored Ledger and Registry copies."""
import hashlib,json,secrets,sqlite3,sys,time
from pathlib import Path

DRILL_PRINCIPAL="registry-audit-recovery-drill"
DRILL_ORIGIN="isolated-restored-sqlite"

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def _inside(root,path,label):
    resolved=Path(path).resolve()
    try: resolved.relative_to(root)
    except ValueError: raise SystemExit(f"{label} must remain inside the restored drill directory")
    if not resolved.is_file() or resolved.is_symlink(): raise SystemExit(f"{label} must be a regular drill file")
    return resolved

def _credential(path):
    value=path.read_bytes().strip()
    if len(value)<32 or len(value)>4096: raise SystemExit("isolated drill credential must contain 32 to 4096 bytes")
    return value

class FixedDrillDelivery:
    """Authenticated fixed-envelope adapter scoped to one restored Ledger DB."""
    def __init__(self,ledger_db,expected_credential):
        self.db=ledger_db; self.expected=expected_credential
        columns={row[1] for row in self.db.execute("PRAGMA table_info(registry_audit_events)")}
        required={"event_uuid","actor","board","canonical_payload","payload_sha256","created_at","authenticated_principal"}
        if not required <= columns: raise SystemExit("restored Ledger audit inbox is not release-compatible")
    def deliver_once(self,event_uuid,presented_credential):
        if not secrets.compare_digest(self.expected,presented_credential): raise PermissionError("invalid isolated drill credential")
        if not isinstance(event_uuid,str) or not event_uuid or len(event_uuid)>256: raise ValueError("invalid stable event UUID")
        payload=canonical({"actor":"registry","board":"BOARD-AUDIT-RECORD","event_uuid":event_uuid})
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing=self.db.execute(
                "SELECT canonical_payload,authenticated_principal FROM registry_audit_events WHERE event_uuid=?",(event_uuid,)
            ).fetchone()
            if existing:
                if existing[0]!=payload or existing[1]!=DRILL_PRINCIPAL: raise RuntimeError("stable event UUID conflicts with restored Ledger inbox")
                self.db.commit(); return False
            self.db.execute(
                """INSERT INTO registry_audit_events(
                     event_uuid,actor,board,canonical_payload,payload_sha256,created_at,authenticated_principal)
                   VALUES (?,?,?,?,?,?,?)""",
                (event_uuid,"registry","BOARD-AUDIT-RECORD",payload,hashlib.sha256(payload.encode()).hexdigest(),
                 time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),DRILL_PRINCIPAL),
            )
            self.db.commit(); return True
        except Exception:
            self.db.rollback(); raise

def run_replay(drill_directory,credential_file,delivery_factory=FixedDrillDelivery):
    root=Path(drill_directory).resolve()
    if not root.is_dir(): raise SystemExit("restored drill directory is required")
    ledger_path=_inside(root,root/"ledger.db","restored Ledger DB")
    registry_path=_inside(root,root/"registry.db","restored Registry DB")
    token_path=_inside(root,credential_file,"isolated drill credential")
    reconciliation=_inside(root,root/"reconciliation.json","offline reconciliation evidence")
    prior=json.loads(reconciliation.read_text(encoding="utf-8"))
    if prior.get("schema")!="townsquare-offline-reconciliation-v1" or prior.get("origin")!="restored-drill-only" or prior.get("replay_performed") is not False:
        raise SystemExit("offline reconciliation evidence is not replay-ready")
    credential=_credential(token_path)
    registry=sqlite3.connect(f"file:{registry_path}?mode=rw",uri=True)
    ledger=sqlite3.connect(f"file:{ledger_path}?mode=rw",uri=True)
    try:
        pending=[row[0] for row in registry.execute(
            """SELECT o.event_id FROM audit_outbox o JOIN journal j ON j.event_id=o.event_id
               WHERE o.delivered_utc IS NULL ORDER BY o.event_id"""
        )]
        if pending != prior.get("pending_event_uuids"): raise SystemExit("restored Registry pending UUIDs differ from reconciliation evidence")
        delivery=delivery_factory(ledger,credential); attempts={}
        for event_uuid in pending:
            delivery.deliver_once(event_uuid,credential)
            delivery.deliver_once(event_uuid,credential)
            attempts[event_uuid]=2
        counts={event_uuid:ledger.execute(
            "SELECT count(*) FROM registry_audit_events WHERE event_uuid=?",(event_uuid,)
        ).fetchone()[0] for event_uuid in pending}
        exactly_once=all(count==1 for count in counts.values())
        if not exactly_once: raise SystemExit("exactly-once replay assertion failed")
    finally:
        ledger.close(); registry.close()
    evidence={"schema":"townsquare-recovery-replay-v1","origin":DRILL_ORIGIN,"pending_event_uuids":pending,
              "attempts_per_event":attempts,"ledger_inbox_counts":counts,"exactly_once":exactly_once}
    output=root/"recovery-replay.json"
    output.write_text(json.dumps(evidence,sort_keys=True)+"\n",encoding="utf-8")
    return evidence

def main():
    if len(sys.argv)!=3: raise SystemExit("usage: recovery_replay_drill.py RESTORED_DRILL_DIR DRILL_CREDENTIAL_FILE")
    print(json.dumps(run_replay(sys.argv[1],sys.argv[2]),sort_keys=True))

if __name__=="__main__": main()
