"""Database-only Registry outbox state transitions.

This module deliberately has no service, network, credential, or canary-runtime
initialization.  The live Registry and the isolated recovery drill therefore
exercise the same durable acknowledgement boundary without the drill importing
or starting the network service.
"""
from __future__ import annotations

import time


def acknowledge_delivery(db, event_id, owner, delivered_utc=None):
    """Durably acknowledge one successful fixed delivery, exactly once."""
    delivered_utc = delivered_utc or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    changed = db.execute(
        """UPDATE audit_outbox SET attempts=attempts+1,delivered_utc=?,last_error=NULL,
             lease_owner=NULL,lease_until=NULL
           WHERE event_id=? AND delivered_utc IS NULL AND lease_owner=?""",
        (delivered_utc, event_id, owner),
    ).rowcount
    if changed:
        return True
    row = db.execute(
        "SELECT delivered_utc,lease_owner,lease_until FROM audit_outbox WHERE event_id=?",
        (event_id,),
    ).fetchone()
    if (
        row
        and row["delivered_utc"] is not None
        and row["lease_owner"] is None
        and row["lease_until"] is None
    ):
        return False
    raise RuntimeError("registry audit acknowledgement lost its fixed outbox lease")
