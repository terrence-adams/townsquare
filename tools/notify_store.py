"""notify_store - the durable half of the shared notification contract.

TS-20260909-wolverine-018, milestone 3. notify_candidate DECIDES; this WRITES.
Keeping them apart is what let the decision layer be tested at all, but Logan is
right in .006 that a returned log_appends list proves nothing about disk. This
module is where that claim becomes checkable.

RULES IT ENFORCES, not merely intends:
  the durable log is APPEND-ONLY and never truncated
  the seen-set only ever grows
  the watermark is written ONLY when the decision says to advance it, so a
    failed sweep leaves the trigger unconsumed on disk and the next poll retries
  receipts live in PER-AGENT files, so one agent's acknowledgement cannot mark
    a notice consumed for a co-resident agent

No network. The caller fetches; the caller passes a Decision; this puts it on
disk and reads it back.
"""
import json
import os


class Store(object):
    def __init__(self, dirpath):
        self.dir = dirpath
        self.drop = os.path.join(dirpath, "NEW-EVENTS.txt")
        self.log = os.path.join(dirpath, "BULLETINS.log")
        self.seen = os.path.join(dirpath, "seen_bulletins")
        self.wm = os.path.join(dirpath, "last_seq")
        self.receipt_dir = os.path.join(dirpath, "receipts")

    # ---- read -------------------------------------------------------------
    def load_seen(self):
        try:
            with open(self.seen) as f:
                return set(l.strip() for l in f if l.strip())
        except OSError:
            return set()

    def load_watermark(self):
        try:
            with open(self.wm) as f:
                return f.read().strip() or None
        except OSError:
            return None

    def load_receipts(self):
        out = {}
        try:
            names = os.listdir(self.receipt_dir)
        except OSError:
            return out
        for n in names:
            if not n.endswith(".json"):
                continue
            try:
                with open(os.path.join(self.receipt_dir, n)) as f:
                    out[n[:-5]] = json.load(f)
            except (OSError, ValueError):
                continue
        return out

    def log_lines(self):
        try:
            with open(self.log) as f:
                return [l.rstrip("\n") for l in f if l.strip()]
        except OSError:
            return []

    def drop_text(self):
        try:
            with open(self.drop) as f:
                return f.read()
        except OSError:
            return ""

    # ---- write ------------------------------------------------------------
    def apply(self, decision, header=None, stamp="-"):
        os.makedirs(self.dir, exist_ok=True)

        # APPEND-ONLY. Opened in "a" and never in "w": there is no code path in
        # this module that shortens BULLETINS.log.
        if decision.log_appends:
            with open(self.log, "a") as f:
                for name in decision.log_appends:
                    f.write("%s  %s\n" % (stamp, name))

        if decision.seen_add:
            merged = self.load_seen() | set(decision.seen_add)
            tmp = self.seen + ".tmp"
            with open(tmp, "w") as f:
                f.write("\n".join(sorted(merged)) + "\n")
            os.replace(tmp, self.seen)

        # PER AGENT. A file each, so nothing can consume on another's behalf.
        for agent, names in (decision.receipts or {}).items():
            os.makedirs(self.receipt_dir, exist_ok=True)
            path = os.path.join(self.receipt_dir, "%s.json" % agent)
            prior = []
            try:
                with open(path) as f:
                    prior = json.load(f)
            except (OSError, ValueError):
                prior = []
            tmp = path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(sorted(set(prior) | set(names)), f, indent=2)
            os.replace(tmp, path)

        lines = list(header or [])
        lines.extend(decision.drop_lines)
        tmp = self.drop + ".tmp"
        with open(tmp, "w") as f:
            f.write("\n".join(lines) + "\n")
        os.replace(tmp, self.drop)

        # LAST, and CONDITIONALLY. decision.watermark is None when the sweep
        # failed; not writing it is what makes the next poll retry the same
        # change instead of skipping past it.
        if decision.watermark is not None:
            tmp = self.wm + ".tmp"
            with open(tmp, "w") as f:
                f.write(str(decision.watermark))
            os.replace(tmp, self.wm)
