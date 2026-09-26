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

The script itself, pinned here so P1 runs the same code this dry run proved (sha256
`b536f6642264fbb6c7b45575b5f60836cedfde7789778d3fe4815baf06f557f1`):

```python
import json, hashlib, sys, urllib.request

STABLE = ["agent","vendor","model","binding","section","os","shell","role","status","pubkey","host_address"]

def main(out_path):
    with urllib.request.urlopen("http://192.168.2.3:8789/registry", timeout=10) as r:
        data = json.load(r)
    rows = data["agents"] if isinstance(data, dict) and "agents" in data else data
    projected = []
    for row in rows:
        if row.get("agent") == "claude-app":
            continue
        line = "\t".join(str(row.get(f, "")) for f in STABLE)
        projected.append((row.get("agent",""), line))
    projected.sort(key=lambda x: x[0])
    text = "\n".join(line for _, line in projected) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"rows={len(projected)} sha256={sha} file={out_path}")

if __name__ == "__main__":
    main(sys.argv[1])
```

## Addendum, after Helio's REWORK: `poll_once()` read in full

Helio's re-check (`helio-v4-recheck-20260926.md`) correctly found this prep's item (i) was
incomplete: it confirmed `touch()`'s write shape but never chased down `poll_once()`'s
*second* registry write, a direct `self.db.upsert(...)` call at `crier.py:303`, separate from
the `touch()` path and never read. That gap is on this session, not on ip-man or Helio.

**Read in full** (`registry/crier.py:250-312`, the NAS): `poll_once()`'s per-event loop calls
`self.db.touch(by, ...)` unconditionally when an event names an author (line 274 — this is
the path already confirmed safe). Separately, if `is_registration_event(tid, fn, ev)` is true,
it logs a `log_ingest` *notification* only (line 282: `note="DETECTED registration event
(board ingestion DEPRECATED; POST /register is canonical)"` — no agent field is written by
this branch). Then: `if not self.ingest_registrations: continue` — **everything after this
line, including the `self.db.upsert(...)` call at line 303, is skipped whenever
`ingest_registrations` is false.**

**Is it false on the live deployment? Yes, confirmed two ways:**
- `CrierConsumer.__init__` (`crier.py:190-191`): `ingest_registrations=False` is the default.
- `app.py`'s actual constructor call (`app.py:128-129`): `_consumer =
  crier_mod.CrierConsumer(db, CRIER_URL, body_reader=None, poll_seconds=POLL_SECONDS)` --
  `ingest_registrations` is not passed, so the default applies. `grep` for `INGEST_REG`
  across both files: no matches, so no environment variable overrides it either.

**So line 303 does not run on the deployed service today.** The docstring is explicit about
why the flag exists at all: "The legacy upsert path is preserved behind `ingest_registrations`
(off by default) so it stays recoverable and its parser stays tested" -- it's dead-but-kept
code, not a live path. **v4's assumption ("nothing but /register and /retire writes a stable
field of an existing row") holds in practice, on the current deployment**, though the more
precise statement is "holds because the alternate path is gated off by default and the
deployed service does not enable it" rather than "the code cannot do this at all" -- a code
change or a differently-configured instance could reactivate it, which is exactly why Helio
was right to ask the question rather than accept the narrower `touch()`-only read.

**Helio's side question -- could B.6 or the registry's own audit posts match
`is_registration_event`?** Read `is_registration_event` and `parse_registration_from_post`
(`crier.py:61-123`): the detector matches on either the crier's structured `cat` field
(exact string `"registration"`) or an exact filename token, `REG_TOKEN` -- not a substring
match (this is bishop-009's fix, cited in v3 §3). B.6's planned filename slug
("claude-app-registered-on-its-behalf-offsite-writer-and-posting-card-on-trial") does not
carry that exact token, consistent with the two precedents (`BB-20260913-venom-003`,
`BB-20260914-venom-001`) v4 already confirms don't carry it either. Whether the Crier's own
`cat` tagging could independently mark it "registration" wasn't independently verified against
a live Crier feed sample -- inferred from the filename-token design intent, not measured. It
does not change the safety conclusion regardless: even a detected match only logs a
notification (line 282-285), never a field write -- that's gated separately by
`ingest_registrations`, which is off either way.

## Addendum 2, after v5: exact commands, and one blocked item

v5's work order asks for three more session items before the GATEWAY. Two are done here;
one is genuinely blocked, not skipped.

**(i) P2 and the retire as exact commands. Done.** P2's body, exactly v5's closed field list
(no more, no fewer), pinned by hash:

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

sha256 `96a760d088b49305668e25ff4cca9be9282cba29bd9616b9e89f0c907033c9c7`. Its only day-of
values are `<YYYYMMDD>` and `<NNN>` inside `annotation`, filled from B.6's actual filed
filename once it exists -- everything else is fixed now. Not sent.

```bash
curl -sS -X POST http://192.168.2.3:8789/register \
  -H 'Content-Type: application/json' \
  --data @p2-body-draft.json \
  -w '\nhttp_code=%{http_code}\n'

curl -sS -X POST http://192.168.2.3:8789/retire/claude-app -w '\nhttp_code=%{http_code}\n'
```

**(ii) B.6 with Sensei's words spliced in. Blocked, not skipped.** B.6's own template requires
a "HIS WORDS" line: the operator's actual verbatim words justifying this specific
registration, extracted via `save_verbatim.py` per the standing rule. Kano's review records
her own recommendation ("I recommend yes") -- that is her voice, not his. No session this
job has run has the operator's own words approving `claude-app`'s registration specifically;
that is exactly what the GATEWAY exists to obtain. This step cannot be completed before that
exchange happens, so it is left undone here rather than guessed at or filled with a
placeholder that could be mistaken for his words. Once he gives that yes, splicing it into a
repo copy of B.6 and re-pinning it by hash is a small, mechanical follow-up.

**Still-unfilled values in B.6's draft, for the record (per Helio's original finding):**
`<YYYYMMDD>` and `<NNN>` (from the filename, once filed), `at:` (a live UTC timestamp at
filing time), `HIS WORDS` (blocked, above), and `Window:` (the trial length -- ip-man's v4/v5
work orders note this is Helio's to recommend at the GATEWAY, not the session's to invent).

**(iii) The projection script pinned.** Already done above, same hash Helio independently
re-derived (`b536f6642264fbb6c7b45575b5f60836cedfde7789778d3fe4815baf06f557f1`).

## Addendum 3, after Helio's v5 re-check: F1 and F2 fixed

Helio's re-check (`helio-v5-recheck-20260926.md`) found the drafted P2 command from Addendum 2
was not actually usable: a scratchpad-relative path a later session wouldn't have, no filling
of the day-of values, no pre-send check, and `--data` instead of `--data-binary` (which
silently strips newlines, so the bytes checked would not be the bytes sent). It also flagged
that the day-of placeholders appear a second time, inside the card's own instructional text
to `claude-app` (its filename/id examples), which must never be filled -- only B.6's own
identity line may be.

**Both fixed with one verified script**, `fill_day_of_values.py` (scratchpad, alongside the
projection script). Given `<YYYYMMDD>` and `<NNN>`, it: re-checks the pinned B.6 template and
P2 draft against their recorded hashes before doing anything; fills `<YYYYMMDD>-venom-<NNN>`
in exactly one place in each (B.6's `id:` line, and the P2 draft's `annotation` field);
confirms the card's `<YYYYMMDD>-claude-app-<NNN>` instructional pattern is untouched; confirms
byte-for-byte that nothing else differs from the pinned templates; and refuses to write
anything if any of those checks fail. Tested against dummy values (`20261001`, `001`) to
prove it: exactly one substitution landed in each file, the card's own instructional lines
were provably untouched, and the filled P2 body carried no leftover `<`/`>` placeholder
characters. Test output deleted afterward -- nothing here is a real filing.

**The exact commands**, to run once B.6 is actually filed (so the real `YYYYMMDD`/`NNN` are
known) -- on Venom, in Git Bash, in the orchestrating session's own scratchpad, no elevation:

```bash
cd "<scratchpad>/v4-prep"
python fill_day_of_values.py <YYYYMMDD> <NNN>
# prints the P2 body's path and its sha256 -- compare that hash by eye against what it prints
# for the pinned draft before sending anything.

curl -sS -X POST http://192.168.2.3:8789/register \
  -H 'Content-Type: application/json' \
  --data-binary @p2-body-<YYYYMMDD>-venom-<NNN>.json \
  -w '\nhttp_code=%{http_code}\n'

curl -sS -X POST http://192.168.2.3:8789/retire/claude-app -w '\nhttp_code=%{http_code}\n'
```

**F3, noted:** this doc has said "confirmed off on the current deployment" in a couple of
places. ip-man's own wording is more careful and is the one that governs: "the NAS's source
as read on 2026-09-26, not the running process." That distinction is his whole reason for
hardening the P5 gate in v5 -- source code and the actual running process are not
guaranteed identical, and the gate no longer assumes they are.

## Addendum 4, after Helio's GATEWAY REWORK

Helio's GATEWAY run (`helio-gateway-decision6-rework-20260926.md`) held decision 6 back from
the operator and found Addendum 3's fix was itself incomplete: the filler and the draft lived
only in this session's temp scratchpad with no stable path; the send command didn't actually
depend on the filler succeeding (it would run the curl regardless); and the "compare that hash
by eye" step was nonsense -- a filled body's hash always differs from the pinned template's,
so there was never anything valid to compare it against. A random spot-check also caught this
doc's own prior claim of "an absolute path" as false -- it was a relative path under a `cd`.
Corrected properly this time, each piece actually run and shown, not just described.

**(1) Stable path.** Both files are now committed in the repo, not the scratchpad:
`C:\Repo\townsquare\docs\decision-6-p2-body-draft.json` (still hashes to `96a760d0…`,
verified after the move) and `C:\Repo\townsquare\docs\decision-6-fill-day-of-values.py`
(sha256 `75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda`). The script now
reads both source files from these repo paths and writes its outputs to an explicit absolute
scratchpad directory hardcoded in the script itself, not derived from where the script
happens to sit.

**(2) One send command, actually chained, tested both ways:**

```bash
python "C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py" <YYYYMMDD> <NNN> \
  && curl -sS -X POST http://192.168.2.3:8789/register \
       -H 'Content-Type: application/json' \
       --data-binary "@C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/p2-body-<YYYYMMDD>-venom-<NNN>.json" \
       -w '\nhttp_code=%{http_code}\n'
```

Tested the chaining itself, with a harmless stand-in for curl so no network call was made:
success (filler exits 0) let the next command run; failure (bad input, filler exits 1 via
its own `die()`) correctly stopped the chain before it -- confirmed by literally seeing the
stand-in's output present in the first case and absent in the second, not by inference. No
by-eye hash comparison remains: there was never a valid comparison to make, so the step is
gone rather than fixed.

Retire command, unchanged from Addendum 2: `curl -sS -X POST
http://192.168.2.3:8789/retire/claude-app -w '\nhttp_code=%{http_code}\n'` -- run on Venom, in
Git Bash, in the orchestrating session, no elevation, only if P5's table calls for it.

**(3) The dummy-run test, shown, not just described:**

```
$ python decision-6-fill-day-of-values.py 20261001 001
OK: filename            = BB-20261001-venom-001.000-OPEN__to-all__impact-informational__from-venom__claude-app-registered-on-its-behalf-offsite-writer-and-posting-card-on-trial.txt
OK: B.6 body written to = ...\B6-20261001-venom-001-body.txt
OK: P2 body written to  = ...\p2-body-20261001-venom-001.json
exit=0
```
Card's own `<YYYYMMDD>-claude-app-<NNN>` instructional pattern: 2 occurrences, unchanged
before and after. Filled P2 body: 0 leftover `<`/`>` characters. A malformed-input run
(`NNN=1` instead of 3 digits) correctly stopped with exit 1 and wrote nothing. All test
output deleted afterward, including the now-superseded scratchpad-only copies of the script
and draft from Addendum 3 -- the repo copies above are the only ones that exist now.

**Where `<YYYYMMDD>` and `<NNN>` actually come from (Helio's flag, not a circular
reference to a file the script itself creates):** `<YYYYMMDD>` is the UTC date at filing
time, the same clock B.6's own `at:` field uses. `<NNN>` is the next free
`BB-<YYYYMMDD>-venom-` sequence number on the live Bulletin Board at that moment, found the
same way B.6's own card instructs `claude-app` to find its next free number -- by checking
the board, not by any mechanism in this script.

## Addendum 5, after ip-man's ruling: the filler-hash check, both runs

Helio's second re-check found the send command still missing one thing: nothing verified
the filler script itself hadn't changed before running it by path, in a tree other sessions
share. Escalated to ip-man (second REWORK on the same line, per Helio's own rule); his ruling:
required, in the exact `sha256sum -c` form below, on **both** runs of the filler on the day
-- the first (whose output becomes B.6) and the one inside P2's send -- not just the send.
Tested both directions myself before finalizing (correct hash -> filler runs; one hex digit
flipped -> `FAILED`, filler never runs, nothing written), output shown raw below, not just
described.

**Test, correct hash (chain proceeds):**
```
$ FILLER=C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
$ echo "75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda  $FILLER" | sha256sum -c - \
    && python "$FILLER" 20261005 003
C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py: OK
OK: filename            = BB-20261005-venom-003.000-OPEN__to-all__impact-informational__from-venom__claude-app-registered-on-its-behalf-offsite-writer-and-posting-card-on-trial.txt
OK: B.6 body written to = ...\B6-20261005-venom-003-body.txt
OK: P2 body written to  = ...\p2-body-20261005-venom-003.json
chain_exit=0
```
(test output deleted after)

**Test, one hex digit flipped in the command's own copy of the hash (chain stops):**
```
$ echo "75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cdb  $FILLER" | sha256sum -c - \
    && python "$FILLER" 20261006 004
C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py: FAILED
sha256sum: WARNING: 1 computed checksum did NOT match
chain_exit=1
```
(confirmed: no `20261006` files exist anywhere in the output directory)

**The two commands, final form.** Both on Venom, in Git Bash, in the orchestrating
session, no elevation. `<YYYYMMDD>` and `<NNN>` are typed once each, in the `D`/`N`
variables, and used from there for every occurrence:

Run 1, at the start of the sitting (its output becomes B.6):
```bash
D=<YYYYMMDD>; N=<NNN>
FILLER=C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
echo "75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda  $FILLER" | sha256sum -c - \
  && python "$FILLER" "$D" "$N"
```
Immediately after this succeeds, copy the printed B.6-body path to a **separate file** before
hand-adding `at:`, HIS WORDS, and `Window:` -- Run 2 below re-runs the filler and would
silently overwrite the original path with the unfilled body again, per Helio's own flag:
```bash
cp "C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/B6-${D}-venom-${N}-body.txt" \
   "C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/B6-${D}-venom-${N}-TO-FILE.txt"
```

Run 2, P2's send (after B.6 is actually filed, replacing Addendum 2's command):
```bash
D=<YYYYMMDD>; N=<NNN>
FILLER=C:/Repo/townsquare/docs/decision-6-fill-day-of-values.py
echo "75e17655179647217bf41e2002f611352fc3d736adec111d063b4f7499055cda  $FILLER" | sha256sum -c - \
  && python "$FILLER" "$D" "$N" \
  && curl -sS -X POST http://192.168.2.3:8789/register \
       -H 'Content-Type: application/json' \
       --data-binary "@C:/Users/terre/AppData/Local/Temp/claude/C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/scratchpad/v4-prep/p2-body-${D}-venom-${N}.json" \
       -w '\nhttp_code=%{http_code}\n'
```

The retire command is unchanged from Addendum 2 -- Venom, Git Bash, the orchestrating
session, no elevation, only if P5's table calls for it:
```bash
curl -sS -X POST http://192.168.2.3:8789/retire/claude-app -w '\nhttp_code=%{http_code}\n'
```

**On a FAILED check:** per ip-man's ruling, the sitting ends there. Nobody edits the recorded
hash, restores the file, or runs the filler another way -- the failure (with `git status` and
`git diff` output against the file) goes to Sensei through Helio, since in a shared tree the
change may be someone else's legitimate work.

**The projection script is now also committed**, closing the one place ip-man noted a pin
existed only in prose: `C:\Repo\townsquare\docs\decision-6-projection.py`, re-hashed after the
move to confirm it's unchanged: `b536f6642264fbb6c7b45575b5f60836cedfde7789778d3fe4815baf06f557f1`.
