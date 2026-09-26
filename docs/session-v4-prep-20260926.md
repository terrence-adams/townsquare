# Session prep for v4's pre-GATEWAY items

Three things ip-man's v4 work order asks the session to do before Helio's re-run and the
GATEWAY (`townsquare-project-tracker-design-v4.md`, "Implement"). Nothing here registers or
executes against the fleet; the two POSTs shown below are drafted for review, not sent.

## (i) The registry's `touch()` source — settles the one open assumption in v4 item 2

Fetched from the NAS (`/share/home/batman/registry/registry/db.py`), read directly, not
inferred:

```python
def touch(self, agent: str, source: str, node: str = ""):
    """Record liveness without changing fields."""
    if self.get(agent):
        self.upsert(agent, source, node)
```

`touch()` calls `upsert(agent, source, node)` with no `at`, no `writer`, and no `**fields`.
Tracing `upsert()` (same file, lines 88-152) for exactly that call shape: `vals = {}` (the
`FIELDS` dict-comprehension draws only from passed `**fields`, which is empty), `stale` stays
`False` (`at` is `None`), `flag` stays `None` (`writer` is `None`). For an existing row, the
generated SQL is exactly:

```sql
UPDATE agents SET updated_at=?, last_seen=?, last_source=? WHERE agent=?
```

No stable field (`FIELDS = ("section", "annotation", "vendor", "model", "binding", ...)`,
confirmed present at `db.py:42`) is ever in that statement. **Confirms v4's assumption
exactly: a Crier touch on an existing row writes only `updated_at`, `last_seen` and
`last_source` — never a stable field.** The only other branch is a touch on an agent with
no row at all, which creates a stub with no stable fields set — already covered by v4's own
"a new row is recorded, not treated as a trigger" clause.

## (ii) The exact P2 POST, and B.6 pinned by hash

**B.6, pinned.** Extracted the draft bulletin's fenced text block from
`townsquare-project-tracker-kano-review.md` (the `### B.6 Draft` section), byte for byte:
79 lines, sha256 `f0dac81e737b7f0ffe9ccc7c39174013b002d799e2b54579a6176b240c347a15`. This is
still a template (`<YYYYMMDD>`, `<NNN>`, and the operator-quote splice are all unfilled) — the
hash pins the current draft's wording, not a filed post; venom fills and files it only after
Sensei's yes, per B.6's own instruction.

**The P2 payload.** v3/v4 point at the precedent in `BB-20260914-venom-001.001` (venom
registering helio-gracie's portable row on its behalf) rather than describing the fields
generically, so it was read directly rather than reconstructed from memory. Its own text
(lines 20-22): "POST http://192.168.2.3:8789/register (from 192.168.2.104), JSON with by=venom
and these fields: agent, vendor, model, binding, os, shell, role (all copied from .000's
header), status, annotation, pubkey (empty), host_address (empty)." No `section` was sent;
the read-back shows the service set it from `binding` on its own. Built the same way, field
for field, using B.6's header values in place of that post's:

```json
{
  "by": "venom",
  "agent": "claude-app",
  "vendor": "Anthropic",
  "model": "unknown",
  "binding": "offsite",
  "os": "unknown",
  "shell": "unknown",
  "role": "the operator's own Claude app session (phone or web), outside the fleet's machines and LAN; files Requests to venom carrying his words; owns nothing; cannot be addressed; no key; polls nothing",
  "status": "active",
  "annotation": "offsite; registered by venom on its behalf (no seat, no key); info posted BB-<YYYYMMDD>-venom-<NNN>.000",
  "pubkey": "",
  "host_address": ""
}
```

Not sent. `<YYYYMMDD>-venom-<NNN>` in `annotation` is filled in only once B.6 is actually
filed, from its real filename, matching how the two precedents cite their own `.000` post.

**The retire call**, already sourced directly from the deployed route (`session-reads-for-v3-
checkpoint-20260926.md`, item 1d): `POST http://192.168.2.3:8789/retire/claude-app`, no body.
200 with `{"ok": true, "agent": <row>}`, or 404 if no such row exists. Journaled the same way
as register.

## (iii) The projection dry run, twice, a few minutes apart

Script (`agent`, `vendor`, `model`, `binding`, `section`, `os`, `shell`, `role`, `status`,
`pubkey`, `host_address` per row, tab-separated, one row per line, every row except
`claude-app`'s, sorted by `agent`), run against the live `GET /registry`:

- **Capture 1, 2026-09-26T08:19:29Z:** 25 rows, sha256
  `2d7bfb2e040e87a6431acd1ee4988718269abb8d8b1eaef004aafb72e93c0024`.
- **Capture 2, 2026-09-26T08:24:35Z (~5 minutes later):** 25 rows, same sha256
  `2d7bfb2e040e87a6431acd1ee4988718269abb8d8b1eaef004aafb72e93c0024`. `diff` against
  capture 1: no output — the two files are byte-identical.

**Result: the projection is stable.** No agent registered, retired, or had a liveness touch
land on a stable field in this window; row order and content held exactly across the gap.
This is the same property P1's own stop rule checks for live, just exercised once here as a
dry run of the mechanism itself before it's relied on.

Both capture files are disposable, kept in the session scratchpad, not the repo:
`...\scratchpad\v4-prep\projection-capture{1,2}.txt`.
