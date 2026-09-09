"""notify_core - the shared notification/consumption contract, as PURE LOGIC.

TS-20260909-wolverine-018, first increment.

WHY THIS FILE EXISTS. The poller mixes transport (urllib) with notification
logic in one script, so the only way to test it is to execute it. The
pre-execution guard refused that, correctly: a component that can only be
verified by running it against a live Crier is not a shared system, it is a
script each host copies. Separating the decision from the fetch is what makes
one contract testable on every host and provider.

NOTHING HERE PERFORMS I/O. No sockets, no subprocess, no filesystem. Callers
fetch, callers write. This module only decides, and returns what should happen.

THIS VERSION DELIBERATELY REPRODUCES TODAY'S BEHAVIOUR, defects included, so
ts-conformance can be shown to FAIL before anything is repaired. The operator's
authorization at .002 is conditional on verification; a fixture that passed
before the fix would verify nothing. Defects preserved on purpose:
  D1 a cold run records nothing durable
  D2 a FAILED sweep still advances the watermark
  D3 the drop loses the pointer to where a notice persisted
and two criteria that were never implemented at all:
  D4 no delivered-vs-consumed distinction
  D5 no per-agent receipts on a shared host
"""


class Decision(object):
    """What the caller should write. The caller does the writing."""

    def __init__(self):
        self.watermark = None      # str or None -> None means "do not advance"
        self.drop_lines = []       # replaces the drop file
        self.log_appends = []      # appended to the durable log, never truncated
        self.seen_add = []         # filenames now known
        self.receipts = {}         # agent -> filename it consumed
        self.notes = []            # diagnostics for the caller, not for the drop


SWEEP_OK = "ok"
SWEEP_FAILED = "failed"


def consume(prior_seen, prior_watermark, watermark, sweep_status, threads,
            host, agent=None, is_cold=None):
    """Decide what a poll should record.

    prior_seen        set of filenames already known
    prior_watermark   str or None
    watermark         str reported by the crier now
    sweep_status      SWEEP_OK | SWEEP_FAILED
    threads           list of thread dicts from /events (ignored if failed)
    host              this host's name
    agent             consuming agent id, if the caller knows one
    is_cold           True when no prior seen-state existed
    """
    d = Decision()
    if is_cold is None:
        is_cold = not prior_seen

    # D2 PRESERVED: the watermark advances regardless of sweep outcome, so a
    # failed sweep consumes the change that triggered it and is never retried.
    d.watermark = watermark

    if sweep_status == SWEEP_FAILED:
        d.drop_lines.append("  Bulletin sweep unavailable. Fleet-wide notices "
                            "are UNKNOWN, not absent.")
        d.notes.append("sweep failed; watermark still advanced (D2)")
        return d

    fresh = []
    for t in threads or []:
        if t.get("board") != "Bulletin Board":
            continue
        if t.get("to") not in ("all", host):
            continue
        for e in t.get("events", []):
            fn = e.get("filename")
            if fn and fn not in prior_seen:
                fresh.append(fn)

    if not fresh:
        return d

    d.seen_add = sorted(fresh)

    if is_cold:
        # D1 PRESERVED: a cold run seeds the seen-set and writes NO durable
        # record, so the very first poll on a new host persists nothing.
        d.drop_lines.append("  Bulletin baseline established: %d existing "
                            "bulletin(s) recorded as seen." % len(fresh))
        d.notes.append("cold seed wrote no durable log (D1)")
        return d

    d.log_appends = sorted(fresh)
    d.drop_lines.append("  ** %d BULLETIN(S) YOU HAVE NOT SEEN:" % len(fresh))
    for fn in sorted(fresh):
        d.drop_lines.append("     %s" % fn)
    # D3 PRESERVED: the pointer to the durable log is emitted only on the poll
    # that discovered something, so a later reader has no way back to it.
    # D4 PRESERVED: nothing distinguishes DELIVERED from CONSUMED.
    # D5 PRESERVED: receipts stay empty even when an agent is named.
    d.notes.append("no consumed/unconsumed distinction (D4); "
                   "no per-agent receipt (D5)")
    return d
