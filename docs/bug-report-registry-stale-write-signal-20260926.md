# Bug report: the recency guard ("bug-007") gives no signal that a write was dropped

**Author:** ronda-rousey (Claude) · **Date:** 2026-09-26 · **Status:** reproduced against baseline, awaiting a remediation ruling (ip-man / jackie-chan). Reproduce-and-document only; no fix proposed or implemented here.

**Baseline:** `terrence-adams/Wonderland` @ `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf` (`main`), `services/registry/`.

**Reproduction:** `services/registry/tests/test_decision6_bug_reports_20260926.py`, tests `test_stale_upsert_gives_its_python_caller_no_signal` and `test_stale_write_via_register_endpoint_is_indistinguishable_from_success`. Run:

```
venv/Scripts/python.exe -m pytest tests/test_decision6_bug_reports_20260926.py -v
```

Both **FAIL** (red, demonstrating the bug). The existing `test_bug007_recency_guard` (`tests/test_registry.py`) already proves the guard's one job — preventing an older write from regressing a field value — works correctly; that is **not** what is being reported here. I re-ran that existing test unmodified and it still passes (43/43 in the full existing suite, see the covering-note in my handback). This report is about what the guard's *caller* is told, which is a different question the existing test does not ask.

## What I verified about the mechanics first

`db.py`'s `upsert()` recency guard (`db.py:104-111`): if an incoming `at` is strictly older than the row's stored `applied_at`, it sets `vals = {}` — the write becomes a no-op on every field, though `updated_at`/`last_seen`/`last_source` still advance (liveness always advances; only field values are protected).

`upsert()` has **no return value** (falls through to an implicit `None`). The only place the rejection is recorded at all is a free-text `note` in the **unrelated** `ingest_log` table (e.g. `"STALE-SKIPPED (at ... < applied ...)"`) — a liveness/diagnostic log, not the write-journal, and not surfaced by `/register`'s HTTP response or by `/journal` in any structured field.

Separately: `/register` (`app.py`) always computes `at` as the server's own wall-clock "now" — it never reads an `at` from the request body — so reaching the guard through the live HTTP endpoint needs either a genuine race between two concurrent requests, or (for a deterministic reproduction) control of the server's clock, which is exactly what a message arriving late relative to a newer one would look like in practice (the crier's legacy ingestion path, off by default, does read `at` from an external event and could trigger this for real: `crier.py` line ~304, `at=ev.get("at")`).

## Example

Direct (`db.py`-level, mirrors the existing `test_bug007_recency_guard`'s own style):
```python
db.upsert("stale-guard-agent", source="test", at="2026-09-20T10:00:00Z",
          binding="host:X", section="host_bound", pubkey="ssh-ed25519 AAAA...orig")
result = db.upsert("stale-guard-agent", source="test",
                    at="2026-09-19T10:00:00Z", pubkey="ssh-ed25519 AAAA...NEW-attempt")
# db.get(...)["pubkey"] correctly stayed "...orig" - the guard worked.
# result is None - nothing tells the CALLER that.
```

Through the real HTTP API (clock-frozen to force the guard, exactly reproducing what a delayed write looks like):
```
[t = 2026-09-20T10:00:00Z] POST /register {"agent":"race-agent","binding":"portable","pubkey":"...orig"}  -> 200
[t = 2026-09-19T10:00:00Z] POST /register {"agent":"race-agent","pubkey":"...NEW-attempt"}                -> 200
```
The second response is `{"ok": true, "agent": {...pubkey: "...orig"...}}` — status 200, `ok: true`, no error, no warning field. The journal entry for that second, silently-dropped write, measured raw:
```
before.pubkey == after.pubkey == "...orig"     # caller's submitted value appears NOWHERE in this entry
"stale" not in the entry at all
```
This is byte-for-byte what a normal, successful, no-op update (e.g. re-sending the same values twice) would also look like. Nothing distinguishes "your write was rejected as stale" from "you happened to send the same value again" or "your write succeeded and merged."

## Context: why this matters

- **The journal is the audit trail** (its own module docstring's words) for every accepted write. If it cannot tell a reader "this write's fields were dropped" apart from "this write's fields were applied," the audit trail is misleading by construction for any write that loses a race — independent of exactly where a fix eventually adds the missing signal.
- **This is exactly the shape of check the offsite-binding design (`ip-man-registry-offsite-binding-design-20260926.md`, R3) is about to build on.** R3 proposes a merged-row check that "builds the merged view of binding, pubkey and host_address the way upsert does: an incoming value that is not None wins." That assumption is false precisely on a stale write — `upsert` does *not* merge non-None values it judges stale; it drops all of them. A check built on the "upsert always merges" assumption, evaluated against a stale write, would compute a merged view that the actual database row will never contain.
- **A caller relying on the HTTP response's `ok: true`, which is the natural thing to rely on, will believe a rejected write succeeded.** This is squarely the LAN-trust write path for the fleet's SSH `authorized_keys` feed — a caller that can't tell "applied" from "silently dropped" has no reliable way to confirm a security-relevant field (e.g., a pubkey rotation) actually took effect.

## Potential solutions (not prescriptive — ip-man / jackie-chan to rule)

- Give `db.upsert()` a return value (e.g., a small result object or dict: applied fields, `stale: bool`) so any caller — `register()`, the crier path, a future R3-style check, or a test — can tell what actually happened without a separate re-read-and-diff.
- Surface the stale/no-op case in `/register`'s HTTP response (e.g., an explicit field alongside `ok`) and/or as a structured (not merely free-text) field on the journal entry itself, so `/journal` readers don't need to string-match a `note`.
- At minimum, if no caller-facing signal is added yet, any future check that assumes "upsert always merges what it's given" (R3, or similar) needs its own explicit stale-write case, tested against the guard's actual condition in `db.py`, not against the assumption alone.
