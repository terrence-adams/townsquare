"""notify_candidate - the PROPOSED repair of the shared notification contract.

TS-20260909-wolverine-018. Same interface as notify_core, same purity: no
sockets, no subprocess, no filesystem. Callers fetch, callers write.

notify_core reproduces today's behaviour with defects D1-D5 preserved.
This module is the candidate that should pass ts-conformance. Both are kept so
the fixture can be run against each and the difference shown, rather than
asking anyone to take a repair on trust.

STATUS. Both fixtures have been run, by wolverine and independently reproduced
by Eddie Brock at revision b2e4cb3. The earlier note here saying the guard
refused execution was true when written and is now STALE - it was Logan's
control defect L-002 and was removed. Under TS-20260909-wolverine-018.002 the
operator's authorization is still conditional on verification of the INTEGRATED
path, so this remains a CANDIDATE and nothing is applied to any host.

THE FIVE REPAIRS
  D1 cold run now appends to the durable log. Seeding the seen-set is a
     convenience for the drop file; it must never be the only record. A host's
     first poll is exactly when losing the history matters most.
  D2 the watermark advances ONLY on a successful sweep. A failed sweep must
     leave the trigger unconsumed so the next poll retries it without waiting
     for the board to move again.
  D3 the pointer to the durable log is emitted whenever anything is
     unconsumed, not only on the poll that discovered it.
  D4 DELIVERED and CONSUMED are separate. Fetching a filename is delivery.
     Consumption is an identified agent recording a receipt. A notice with no
     receipt is reported as unconsumed on every poll until one exists.
  D5 receipts are PER AGENT. Two agents on one host each carry their own, so
     neither infers the other's consumption from a shared drop file.
"""

SWEEP_OK = "ok"
SWEEP_FAILED = "failed"


def mine_of(prior_receipts, agent):
    """What THIS agent has acknowledged. Never another agent's receipts."""
    if not agent:
        return set()
    return set((prior_receipts or {}).get(agent, ()))


class Decision(object):
    """What the caller should write. The caller does the writing."""

    def __init__(self):
        self.watermark = None      # None means DO NOT ADVANCE
        self.drop_lines = []
        self.log_appends = []
        self.seen_add = []
        self.receipts = {}         # agent -> [filenames it has now consumed]
        self.notes = []


def consume(prior_seen, prior_watermark, watermark, sweep_status, threads,
            host, agent=None, is_cold=None, prior_receipts=None,
            acknowledged=None):
    """Decide what a poll should record.

    prior_receipts   {agent: [filenames]} already consumed, per agent
    agent            WHO the notice is for. Knowing this is DELIVERY ONLY.
    acknowledged     filenames this agent has EXPLICITLY acknowledged reading.
                     Receipts derive from here and nowhere else.

    L-003, found by Logan on 018.006: an earlier version minted a receipt
    whenever an agent name and unconsumed filenames were both present. That
    made "the poller knows who it is for" equivalent to "that agent read it",
    which defeats the delivered/consumed split this module exists to create.
    An identified reader that never starts must accumulate NO receipts.
    """
    d = Decision()
    prior_seen = set(prior_seen or ())
    prior_receipts = dict(prior_receipts or {})
    if is_cold is None:
        is_cold = not prior_seen
    mine = mine_of(prior_receipts, agent)

    # D2: a failed sweep consumes nothing. The watermark is the record of what
    # has been SUCCESSFULLY examined, not of what the crier last reported.
    if sweep_status == SWEEP_FAILED:
        d.watermark = None
        d.drop_lines.append("  Bulletin sweep FAILED. FRESH notices are UNKNOWN, "
                            "not absent. Watermark held at %r so the next poll "
                            "retries without waiting for the board to move."
                            % prior_watermark)
        # E-002, found by Eddie on 018.009: drop_lines REPLACES the drop file,
        # so returning only the failure message erased every previously known
        # unread notice from the reader's view. A failed sweep must not consume
        # work that was already discovered - losing sight of known unread items
        # is the exact failure this system exists to remove, and a transport
        # error is no excuse for it.
        known_unread = sorted(set(prior_seen) - mine_of(prior_receipts, agent))
        if known_unread:
            d.drop_lines.append("  ** %d PREVIOUSLY DISCOVERED, STILL NOT "
                                "CONSUMED%s (freshness unknown this poll):"
                                % (len(known_unread),
                                   " by %s" % agent if agent else ""))
            for fn in known_unread:
                d.drop_lines.append("     %s" % fn)
            d.drop_lines.append("     Durable record: BULLETINS.log (never truncated)")
        d.notes.append("sweep failed; watermark not advanced; %d known-unread "
                       "notice(s) preserved" % len(known_unread))
        return d

    d.watermark = watermark

    # E-001, found by Eddie on 018.009: a filename repeated twice WITHIN one
    # sweep produced two identical log entries and two seen_add values.
    # Across-poll idempotence never covered within-sweep repetition, and the
    # duplicate reached disk. Deduplicated here rather than assuming an
    # upstream uniqueness contract nobody has stated.
    applicable = []
    for t in threads or []:
        if t.get("board") != "Bulletin Board":
            continue
        if t.get("to") not in ("all", host):
            continue
        for e in t.get("events", []):
            fn = e.get("filename")
            if fn and fn not in applicable:
                applicable.append(fn)

    fresh = sorted({fn for fn in applicable if fn not in prior_seen})
    d.seen_add = fresh

    # D1: whatever was discovered is written durably, cold run included.
    d.log_appends = sorted(fresh)
    if is_cold and fresh:
        d.drop_lines.append("  Baseline: %d existing bulletin(s) recorded. All "
                            "are in the durable log; none is marked consumed."
                            % len(fresh))

    # D4/D5: delivery is knowing the filename. Consumption is THIS agent having
    # a receipt for it. Anything without one stays visible on every poll -
    # including items discovered on an EARLIER poll, not just this sweep's.
    unconsumed = sorted((set(applicable) | prior_seen) - mine)

    if unconsumed:
        d.drop_lines.append("  ** %d BULLETIN(S) DELIVERED AND NOT YET CONSUMED"
                            "%s:" % (len(unconsumed),
                                     " by %s" % agent if agent else
                                     " - NO CONSUMING AGENT IDENTIFIED"))
        for fn in unconsumed:
            d.drop_lines.append("     %s" % fn)
        # D3: the pointer is present whenever something is outstanding.
        d.drop_lines.append("     Durable record: BULLETINS.log (never truncated)")
        if not agent:
            # The failure this system exists to remove: a notice delivered to a
            # host where nothing was running is NOT the same as a quiet board.
            d.drop_lines.append("     WARNING: no agent identity supplied, so "
                                "nothing can be marked consumed. An uninvoked "
                                "reader is indistinguishable from a read one "
                                "until an identity is provided.")
            d.notes.append("delivered but no agent identity; consumption unprovable")

    # RECEIPTS COME ONLY FROM AN EXPLICIT ACKNOWLEDGEMENT. Being the intended
    # recipient is delivery; reading it is consumption; nothing here may
    # promote the first into the second. A receipt is recorded for THIS agent
    # only and never speaks for a co-resident agent.
    acked = set(acknowledged or ()) & set(applicable)
    if agent and acked:
        d.receipts = {agent: sorted(mine | acked)}
        d.notes.append("receipt recorded for %s over %d acknowledged notice(s)"
                       % (agent, len(acked)))
    elif agent and unconsumed:
        d.notes.append("%s has %d unconsumed notice(s) and acknowledged none; "
                       "no receipt minted" % (agent, len(unconsumed)))

    return d
