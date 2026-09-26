# Session reads for Helio's CHECKPOINT (1) on v3

Six read-only checks Helio delegated (`helio-checkpoint-v3-20260926.md`, "Next" 1a-1f), run
2026-09-26 directly against the NAS (192.168.2.3) and the TownSquare Drive mount. Nothing
written anywhere; no registry POST, no retire, no git operation beyond `git add`/`commit` of
this doc. Labels follow the job's own convention: **measured** = read or ran this session,
**source** = read from the registry's own code, not just its behavior.

## 1a. Are Crier liveness touches journaled? — No, by both code and history.

**Source**, `registry/crier.py` on the NAS: `CrierConsumer.poll_once()` calls
`self.db.touch(by, source=f"crier:{by}", node=tid)` — a direct DB method, never
`self.journal.record(...)`. Grepped the entire `registry/` package for any `journal.record`
call: the only two hits in the whole codebase are in `app.py`, inside `register()` (line 201)
and `retire()` (line 215). Nothing in `crier.py`, `db.py`, or elsewhere calls it.

**Measured**, `GET /journal?limit=30` against the live service: `count: 5`, every entry
`op: register`, zero entries of any other kind. Several entries' `before` snapshot shows
`last_source: crier:<agent>` (e.g. `bishop`'s entry at `2026-09-13T08:31:49Z`) — confirming a
Crier touch updates the row, and that update surfaces later as *context inside a real
register call's before-state*, but never becomes a journal entry of its own.

**Answers Helio's escalation item 3 directly: no design change is needed.** P3's "exactly
one entry newer than P1's" and rows 2-3's "claude-app's write is the only write since P1" are
both safe from Crier-poll noise — a poll between P1 and P2/P3 cannot add a journal entry, so
it cannot cause a false row-5 fallout on a clean run. ip-man's conditional wording ("if
journaled, ignore Crier entries that change no stable field") is now moot; nothing needs it.

## 1b. The §5 trailing-byte read of the live feed — ends in `\n`; the defect is latent.

`curl -s -m 10 http://192.168.2.3:8789/authorized_keys`, then `tail -c 1 | od -An -c`:
last byte is `\n`. Per v3 §5's own text, this means the defect (dropping the feed's last key
on hosts whose sync lacks the `read || [ -n "$key" ]` guard) is latent right now, not live —
no Request to bishop is warranted today on liveness grounds alone. Still worth folding into
whichever Request eventually covers item 7 of Helio's escalation (client-side guard, and/or
a server-side guaranteed-trailing-newline fix), since latent can become live if the feed's
last row ever changes.

## 1c. NAS sha256sum of authorize_from_registry.sh — unchanged, re-verified.

`ssh batman@192.168.2.3 sha256sum /share/home/batman/registry/authorize_from_registry.sh`:
`6659ac356cb8c12a4898adae8e864ea926e1d3054125b622beeb33a420df9e3b` — matches
`reference-authorize_from_registry-20260926.md` exactly, unchanged since that file was made.

## 1d. The /retire route source, read early for P1's undo call.

`registry/app.py` on the NAS, current deploy (path differs from ip-man's `e340e09` citation
of `app.py:132-138`; this is the route as it stands today):

```python
@app.post("/retire/<name>")
def retire(name):
    before = db.get(name)
    if not before:
        return jsonify({"error": "not found"}), 404
    src = request.remote_addr or "lan"
    db.retire(name, source=f"retire:{src}")
    after = db.get(name)
    _journal.record("retire", name, before, after,
                    source=f"retire:{src}",
                    applied_at=(after or {}).get("applied_at") or None)
    _publish_async()  # best-effort: drain the audit outbox to the board
    return jsonify({"ok": True, "agent": after})
```

The call is `POST http://192.168.2.3:8789/retire/<name>`, no request body needed. Returns
`{"ok": true, "agent": <after>}` on success, or `{"error": "not found"}` / 404 if the name
doesn't exist. Confirms (again, from source rather than inference) that a retire is
journaled exactly like a register — same `_journal.record(...)` call, same shape.

## 1e. BB-20260913-cable-003.000 — v3's Sensei quote checked against it: exact match.

`G:\My Drive\N3rd0m\TownSquare\Bulletin Board\BB-20260913-cable-003.000-...txt`, line 19:

> "A new agent posts to the bulletin board with its information. Then registers itself and its ssh key."

Character-for-character the same as v3 quotes it. No discrepancy.

## 1f. The search behind done-when (4) — no Request proposing the curl -fsS fix exists.

`Grep` (case-insensitive) for `curl -f|curl -fsS|authorize_from_registry|fsS` across
`G:\My Drive\N3rd0m\TownSquare\Requests\`: 13 matches across 9 files. Every `curl -f` hit is
an unrelated use in a different context (a Crier health-check reproduction, a start.sh
port-guard reproduction, a claude-cli version check) — none of them about
`authorize_from_registry.sh`. Every `authorize_from_registry` hit is inside
`TS-20260913-cable-016.000`/`.001`, cable's already-known 2026-09-13 Wonderland review of the
script, which ip-man's v3 already cites and accounts for. No Request dated 2026-09-25 or
2026-09-26, or any Request at all, proposes changing the script's curl flags. ip-man's claim
holds.
