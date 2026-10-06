#!/usr/bin/env python3
"""Offline exactly-once replay drill over restored Ledger and Registry copies."""
import json,secrets,sqlite3,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from registrar.app.native_ledger import ingest_registry_audit
from registry.app import acknowledge_delivery

DRILL_OWNER="registry-audit-recovery-drill"
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
    """Isolated credential adapter over production ingestion/ack boundaries."""
    def __init__(self,ledger_db,registry_db,expected_credential):
        self.ledger=ledger_db; self.registry=registry_db; self.expected=expected_credential
        columns={row[1] for row in self.ledger.execute("PRAGMA table_info(registry_audit_events)")}
        required={"event_uuid","actor","board","canonical_payload","payload_sha256","created_at","authenticated_principal"}
        if not required <= columns: raise SystemExit("restored Ledger audit inbox is not release-compatible")
    def deliver_once(self,event_uuid,presented_credential):
        if not secrets.compare_digest(self.expected,presented_credential): raise PermissionError("invalid isolated drill credential")
        if not isinstance(event_uuid,str) or not event_uuid or len(event_uuid)>256: raise ValueError("invalid stable event UUID")
        payload={"actor":"registry","board":"BOARD-AUDIT-RECORD","event_uuid":event_uuid}
        # This is the same transaction used by the authenticated HTTP adapter.
        # The drill credential never becomes a Ledger principal or capability.
        ingest_registry_audit(self.ledger,"registry-audit",payload)
        row=self.registry.execute(
            "SELECT delivered_utc FROM audit_outbox WHERE event_id=?",(event_uuid,)
        ).fetchone()
        if row is None: raise RuntimeError("stable event UUID is absent from restored Registry outbox")
        if row["delivered_utc"] is None:
            # A restored copy has no live lease holder. Take over only this
            # isolated row, then use Registry's production acknowledgement.
            self.registry.execute(
                "UPDATE audit_outbox SET lease_owner=?,lease_until=NULL WHERE event_id=? AND delivered_utc IS NULL",
                (DRILL_OWNER,event_uuid),
            )
        return acknowledge_delivery(self.registry,event_uuid,DRILL_OWNER)

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
    registry=sqlite3.connect(f"file:{registry_path}?mode=rw",uri=True,isolation_level=None); registry.row_factory=sqlite3.Row
    ledger=sqlite3.connect(f"file:{ledger_path}?mode=rw",uri=True,isolation_level=None); ledger.row_factory=sqlite3.Row
    try:
        pending=[row[0] for row in registry.execute(
            """SELECT o.event_id FROM audit_outbox o JOIN journal j ON j.event_id=o.event_id
               WHERE o.delivered_utc IS NULL ORDER BY o.event_id"""
        )]
        if pending != prior.get("pending_event_uuids"): raise SystemExit("restored Registry pending UUIDs differ from reconciliation evidence")
        delivery=delivery_factory(ledger,registry,credential); attempts={}
        for event_uuid in pending:
            delivery.deliver_once(event_uuid,credential)
            delivery.deliver_once(event_uuid,credential)
            attempts[event_uuid]=2
        counts={event_uuid:ledger.execute(
            "SELECT count(*) FROM registry_audit_events WHERE event_uuid=?",(event_uuid,)
        ).fetchone()[0] for event_uuid in pending}
        internal_counts={event_uuid:ledger.execute(
            """SELECT count(*) FROM ledger_events e JOIN event_content c USING(event_id)
               WHERE e.thread_id='__registry_audit__' AND e.kind='REGISTRY_AUDIT'
                 AND e.state='RECORDED' AND c.content=?""",
            (canonical({"actor":"registry","board":"BOARD-AUDIT-RECORD","event_uuid":event_uuid}),),
        ).fetchone()[0] for event_uuid in pending}
        outbox={event_uuid:dict(registry.execute(
            "SELECT attempts,delivered_utc,last_error,lease_owner,lease_until FROM audit_outbox WHERE event_id=?",
            (event_uuid,),
        ).fetchone()) for event_uuid in pending}
        exactly_once=all(
            counts[event_uuid]==1 and internal_counts[event_uuid]==1
            and outbox[event_uuid]["attempts"]==1 and outbox[event_uuid]["delivered_utc"] is not None
            and outbox[event_uuid]["last_error"] is None and outbox[event_uuid]["lease_owner"] is None
            and outbox[event_uuid]["lease_until"] is None
            for event_uuid in pending
        )
        if not exactly_once: raise SystemExit("exactly-once replay assertion failed")
    finally:
        ledger.close(); registry.close()
    evidence={"schema":"townsquare-recovery-replay-v1","origin":DRILL_ORIGIN,"pending_event_uuids":pending,
              "attempts_per_event":attempts,"ledger_inbox_counts":counts,"ledger_internal_event_counts":internal_counts,
              "registry_outbox":outbox,"exactly_once":exactly_once}
    output=root/"recovery-replay.json"
    output.write_text(json.dumps(evidence,sort_keys=True)+"\n",encoding="utf-8")
    return evidence

def main():
    if len(sys.argv)!=3: raise SystemExit("usage: recovery_replay_drill.py RESTORED_DRILL_DIR DRILL_CREDENTIAL_FILE")
    print(json.dumps(run_replay(sys.argv[1],sys.argv[2]),sort_keys=True))

if __name__=="__main__": main()
