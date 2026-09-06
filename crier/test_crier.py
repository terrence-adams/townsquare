#!/usr/bin/env python3
#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
# Regression tests for the Crier index. No pytest, no network, no rclone:
# list_remote is replaced with a literal board, which is the only input the
# index has. Run it directly:  python3 crier/test_crier.py
#
# Every case here is a bug that actually reached the live board, not a
# hypothetical.
import os
import sys
import tempfile
import types

# Stub FastAPI so the module imports without its serving dependencies. The index
# under test is plain data manipulation; the web layer is not what is being
# exercised.
_fa = types.ModuleType("fastapi")
_fa.FastAPI = type("FastAPI", (), {
    "__init__": lambda self, *a, **k: None,
    "get": lambda self, *a, **k: (lambda f: f),
})
_fa.Query = lambda *a, **k: None
_fr = types.ModuleType("fastapi.responses")
_fr.JSONResponse = type("JSONResponse", (), {
    "__init__": lambda self, content=None, **k: setattr(self, "content", content)})
_fa.responses = _fr
sys.modules.setdefault("fastapi", _fa)
sys.modules.setdefault("fastapi.responses", _fr)

os.environ["TS_STATE"] = os.path.join(tempfile.mkdtemp(), "state.json")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crier  # noqa: E402

crier.verify_event = lambda ev: None  # signing is covered by ts-verify


def f(path, fid, mod="2026-01-01T00:00:00Z"):
    return {"Path": path, "Name": path.split("/")[-1], "ID": fid, "ModTime": mod}


def board(files):
    crier.list_remote = lambda: files
    crier.poll()


def reset():
    crier._state["events"].clear()
    crier._state["seen"].clear()
    crier._state["newest_at"] = None


R = "Requests/"
checks = []


def check(name, cond):
    checks.append((name, bool(cond)))
    print(("  PASS  " if cond else "  FAIL  ") + name)


print("parsing")
reset()
board([f(R + "TS-20260101-001.000-OPEN__P1__to-b__from-a__legacy.txt", "l"),
       f(R + "TS-20260101-agent-a-001.000-OPEN__P1__to-b__from-a__namespaced.txt", "n")])
v = crier.threads_view()
check("legacy un-namespaced id still parses", "TS-20260101-001" in v)
check("namespaced id parses as its own thread", "TS-20260101-agent-a-001" in v)
check("namespace is extracted",
      v.get("TS-20260101-agent-a-001", {}).get("namespace") == "agent-a")
check("legacy id has no namespace", v.get("TS-20260101-001", {}).get("namespace") is None)

# Two agents both appended .002. Sorting on sequence alone silently dropped one,
# so a reviewer's claim showed as unclaimed. Ties must break on timestamp.
print("\nduplicate sequence at the head of a thread")
reset()
board([f(R + "TS-20260101-a-001.000-OPEN__P1__to-b__from-a__x.txt", "1"),
       f(R + "TS-20260101-a-001.002-DONE__by-a.txt", "2", "2026-01-01T04:00:00Z"),
       f(R + "TS-20260101-a-001.002-CLOSED__by-a.txt", "3", "2026-01-01T06:00:00Z")])
t = crier.threads_view()["TS-20260101-a-001"]
check("duplicate sequence is flagged", t["collision"]["duplicate_sequences"] == [2])
check("head collision is unresolved", t["collision"]["unresolved"] is True)
check("neither event is dropped", len(t["events"]) == 3)
check("later timestamp wins the tie", t["events"][-1]["state"] == "CLOSED")
check("COLLISIONS counts it", crier.fleet()["integrity"]["COLLISIONS"] == 1)

# Reconciling means APPENDING a correctly numbered event, never deleting one.
# The duplicate stays on the ledger; what must clear is the alarm.
print("\nreconciliation clears the alarm without erasing history")
board([f(R + "TS-20260101-a-001.000-OPEN__P1__to-b__from-a__x.txt", "1"),
       f(R + "TS-20260101-a-001.002-DONE__by-a.txt", "2", "2026-01-01T04:00:00Z"),
       f(R + "TS-20260101-a-001.002-CLOSED__by-a.txt", "3", "2026-01-01T06:00:00Z"),
       f(R + "TS-20260101-a-001.003-CLOSED__by-a.txt", "4", "2026-01-01T07:00:00Z")])
t = crier.threads_view()["TS-20260101-a-001"]
fl = crier.fleet()
check("collision is still recorded", t["collision"]["duplicate_sequences"] == [2])
check("but no longer unresolved", t["collision"]["unresolved"] is False)
check("COLLISIONS falls to zero", fl["integrity"]["COLLISIONS"] == 0)
check("history is kept separately", fl["integrity"]["collisions_historical"] == 1)

# Two DISTINCT requests wearing one id. The second is invisible while appearing
# filed. Age never makes this benign, so it is always unresolved.
print("\nduplicate openings are never benign")
reset()
board([f(R + "TS-20260101-a-002.000-OPEN__P1__to-b__from-a__first.txt", "1"),
       f(R + "TS-20260101-a-002.000-OPEN__P1__to-c__from-a__second.txt", "2"),
       f(R + "TS-20260101-a-002.001-WORKING__by-b.txt", "3"),
       f(R + "TS-20260101-a-002.002-RESOLVED__by-b.txt", "4")])
t = crier.threads_view()["TS-20260101-a-002"]
check("two openings are flagged", t["collision"]["duplicate_openings"] == 2)
check("stays unresolved despite later events", t["collision"]["unresolved"] is True)

# poll() only ever added, so anything archived or withdrawn stayed in the index
# forever and the index diverged permanently from the ledger.
print("\nthe index forgets what left the store")
reset()
board([f(R + "TS-20260101-a-003.000-OPEN__P1__to-b__from-a__x.txt", "1"),
       f(R + "TS-20260101-a-003.001-WORKING__by-b.txt", "2")])
check("both events indexed", len(crier._state["events"]) == 2)
board([f(R + "TS-20260101-a-003.000-OPEN__P1__to-b__from-a__x.txt", "1")])
check("withdrawn event is pruned", len(crier._state["events"]) == 1)
check("removal is reported", crier._state["last_removed"] == 1)

# A successful-but-empty listing is far more likely to be a broken remote than a
# genuinely emptied board. Pruning on it would erase everything in one poll.
print("\nan empty listing must not wipe the index")
board([])
check("index survives an empty listing", len(crier._state["events"]) == 1)

bad = [n for n, ok in checks if not ok]
print(f"\n{len(checks) - len(bad)}/{len(checks)} passed")
if bad:
    print("FAILED: " + "; ".join(bad))
sys.exit(1 if bad else 0)
