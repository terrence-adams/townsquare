# Registry `binding: offsite` fix: final deploy runbook

**Author:** francis-ngannou (Claude) · **Date:** 2026-09-26 · **Status:** prep only. Nothing below was run against the live NAS, the live registry service (`:8789`), or the Wonderland repo's tracked history this session. Every command that writes to the NAS or restarts the service is marked **[SENSEI'S HANDS]** below and is reserved for Sensei himself, or someone he names, run one command at a time — never by a subagent on a relayed yes. See "Who runs what," and the callout repeated immediately before Step 6.

**Supersedes** the "Runbook sketch" section of `francis-ngannou-registry-deploy-prep-20260926.md` (commit `dc32913`). That document's D1–D5 findings (bind-mount confirmation, DB location and safe-backup method, restart behaviour, the `ede80e1` branch point, the 8-file hash table) are the underlying evidence and are **not** restated here in full — they're cited by section label, because jackie-chan, gsp and ip-man's ruling already cite D1–D5 by number. This document is the operational procedure built on that evidence, updated for everything ruled since.

**Read, in order, to build this version:**
1. `ip-man-registry-offsite-addendum-1-20260926.md` §4 — BUILD-file write timing, `?exclude=venom`, the sqlite3-on-NAS fallback.
2. `jackie-chan-registry-offsite-review-20260926.md` — U11 (widen the byte-identical exemption to `outbox_pending` and `publisher.pending`/`publisher.published`), and the `core.autocrlf` hash hazard (§0).
3. `gsp-registry-offsite-security-review-20260926.md` §8 — runbook refinements s1–s7.
4. `ip-man-registry-offsite-security-ruling-20260926.md` §5 — s3/s6/s7 ruled **required**, with the Git-Bash-not-PowerShell detail and "run the actual `key_publishable` function, never a reimplemented copy" for s7.

**Labels**, matching the rest of the chain: *measured* = I ran this, this session, read-only/local-only, never against the live NAS. *inferred* = reasoned, not executed. *reported-by X* = X's claim, not independently re-checked by me.

**What changed since dc32913's sketch** (so a reviewer doesn't have to diff it by hand):
- `?exclude=claude-app` → `?exclude=venom` in every pre/post-deploy feed read, to match the P1 captures (Addendum 1 §4).
- R7 (version bump to "1.3") is **withdrawn**. The deploy's outside proof is now `/health`'s `build` field, sourced from a `BUILD` file the runbook writes with the fix commit's short SHA, immediately before the restart. `version` stays `"1.2"`. Rollback writes `BUILD=ede80e1`.
- The `/journal` byte-identical check is narrowed to op/agent/applied_at of the newest entry, and now **also** excludes `outbox_pending` and `publisher.pending`/`publisher.published` from any byte-identical claim (jackie's U11), not just the per-entry `publishing` field Addendum 1 already excluded.
- The DB backup step now branches on whether the NAS has a `sqlite3` CLI at all; if not, it uses a `docker exec` Python-`sqlite3`-API backup, copying out via `docker cp`, touching nothing under `/app/secrets` (gsp's s3, ruled required).
- Every hash of a to-be-deployed file is now taken from the reviewed commit's **git blob** (`git show <sha>:<path>`, run in **Git Bash, not PowerShell**), never from a Windows working-tree checkout — this machine has `core.autocrlf=true`, which silently changes hashes on checkout (jackie §0; gsp's s6; ip-man's ruling §5, Watch-for (o)).
- A new pre-deploy gate (s7, required): before touching anything on the NAS, run the actual reviewed `key_publishable` function against a saved live `/registry?retired=0` snapshot, and confirm no active keyed row would lose its key under the new default-deny rule.
- Backup-command error suppression (`2>/dev/null || true`) is removed; a failed backup must stop the run, visibly, before Step 7 (gsp's s2).
- Three small verification scripts are added and tested this session (see "Tooling," below) so the pre/post comparisons are exact commands, not remembered-by-eye terminal scrollback.

---

## Who runs what

- **Steps 1–5 and 9 are read-only or local-only.** They touch nothing on the NAS except plain reads (or, for Step 3, nothing on the NAS at all — it reads only the local Wonderland git checkout). The orchestrating session may run these itself.
- **Steps 6, 7, 8 and 10 write to the live NAS or restart the live container.** Per every ruling in this chain (the design note §5, the work order's Deploy line, Helio's GAME PLAN): **these are run by Sensei himself, at the terminal, one command at a time as they're handed to him, or by someone he names. A subagent never runs them on a relayed yes.** This document does not authorize the deploy; it only prepares it. The callout is repeated immediately before Step 6.

---

## Fixed reference values

| Name | Value |
|---|---|
| NAS SSH alias | `nas` (192.168.2.3, user `batman`) |
| Container | `agent-registry` (host port 8789 → container port 8788, runs as root, single `python app.py` process) |
| Code root (3 aliases, 1 inode) | `/share/home/batman/registry/` = `/home/batman/registry/` = `/volume1/home/batman/registry/` |
| DB | `/share/home/batman/registry/data/registry.db` |
| Backup dir (NAS-local, outside the bind-mounted `/app` tree) | `/share/home/batman/registry-backups/preoffsite-<ts>/` |
| Reviewed source | `C:\Repo\Wonderland` (sparse checkout of `services/registry`, branch `offsite-binding`, cut from `ede80e1`) |
| Staging dir (Venom-local, never committed, never inside Wonderland's own tree) | `C:\Repo\registry-deploy-stage\<ts>\` |
| Helper scripts (this repo, tested this session — see "Tooling") | `C:\Repo\townsquare\docs\registry-offsite-s7-precheck.py`, `...-verify-export.py`, `...-journal-diff.py` |
| `<ts>` | `date -u +%Y%m%dT%H%M%SZ`, set once at the start of a run and reused throughout it |
| `<fix-sha>` | short SHA of the commit on `offsite-binding` that jackie-chan's diff review and gsp's hunk confirmation both signed off on. Does not exist yet — filled in once Implement + Peer review land (Helio's GAME PLAN: ronda → bruce → jackie → gsp → CHECKPOINT) |

All Venom-side commands below run in **Git Bash**, not PowerShell — this is a hard requirement for the export step (see Step 3) and this document uses it throughout for consistency, so nobody has to context-switch shells mid-run. All NAS-side commands run over `ssh nas "..."` as `batman`. No step needs elevation on either host; the one nuance (a `docker exec` command that runs as root *inside* the container) is called out at Step 6b.

---

## Tooling verified this session (measured, local-only, nothing live)

Before writing these into the runbook, I tested all three against real inputs — not just read them back:

- **`registry-offsite-verify-export.py`** — checked against a real `git show ede80e1:services/registry/registry/schema.py` export in Git Bash on this machine: 0 CR bytes, SHA-256 `8ac1fa80…` — matching my own D5 table, jackie's independent re-derivation, and gsp's. Also checked against the **working-tree** copy of the same file (`core.autocrlf=true` in effect): different hash, CR bytes correctly flagged, exit 1 — independently reproducing jackie's §0 finding a third time, on this exact machine.
- **`registry-offsite-journal-diff.py`** — checked against synthetic `/journal` captures with the entries array in different orders and in both envelope shapes (bare list vs. `{"entries": [...]}`): correctly finds the true newest entry by `seq` either way, correctly ignores a `publishing`/`outbox_pending`/`publisher.*` change, correctly flags a real new entry as MISMATCH.
- **`registry-offsite-s7-precheck.py`** — checked against a passing fixture (no losers), a failing fixture (two rows that would lose their key), a schema file missing `key_publishable` (today's real baseline, since the fix doesn't exist yet — correctly reported as a clean error, not a crash), and both POSIX- and Windows-style paths.
- **A genuinely new finding along the way:** a Python one-liner run via `python -c "..."` in Git Bash on this machine fails with `FileNotFoundError` if a POSIX-style path (`/c/...`) is embedded *inside* the `-c` string body — native Windows `python.exe` doesn't understand it, and Git Bash's automatic path-mangling only rewrites genuine argv tokens, not text inside a quoted script blob. Passing the same path as a separate argv (`sys.argv[1]`), in either path style, works. All three scripts above take their paths as argv for exactly this reason, and every inline one-liner below follows the same rule — **never embed a file path inside a `python -c` string; always pass it as a separate argument.**

---

## The 8-file baseline (from `dc32913`'s D5, re-derived by jackie-chan, gsp, and again by me this session — all four agree exactly)

| File | NAS path | `ede80e1` blob SHA-256 | Changes in this fix? |
|---|---|---|---|
| `app.py` | `/share/home/batman/registry/app.py` | `d9717f3b6fddbd19b04934fff014e7440a3bf32549fc8e461b618c40b24de3b8` | Yes |
| `registry/schema.py` | `/share/home/batman/registry/registry/schema.py` | `8ac1fa806d4811fcc96fa3ffe24ba407b86608472b4ab8f01cd4e84a8b80377c` | Yes |
| `registry/render.py` | `/share/home/batman/registry/registry/render.py` | `3173a3f6a04627c2599af007318308908208f5484def491dc5148a9075c449f4` | Yes |
| `registry/db.py` | `/share/home/batman/registry/registry/db.py` | `7f16d6967828b6c44d19dcf9d3acb34ccbfe3a92aaaab83120d0d923678f0877` | No |
| `registry/crier.py` | `/share/home/batman/registry/registry/crier.py` | `688fcaad1b0a4afb54f4efa9b5eda5ef5855bbf4edbc0d0d85ec8e26778cc8fc` | No |
| `registry/journal.py` | `/share/home/batman/registry/registry/journal.py` | `2f3acf5d6bc7518fcb31cf046d4f4897d0ace1db2ad529bef2e8fa7a2d450abc` | No |
| `registry/publisher.py` | `/share/home/batman/registry/registry/publisher.py` | `c4e839be8c0084c695ea7a78465a028f3be0d6bea2104e261065a78b9a607208` | No |
| `registry/parse_md.py` | `/share/home/batman/registry/registry/parse_md.py` | `e6fa206a8977659d88d5be522be19ea5910eed121c22bfff233586237024bf3b` | No |

---

## STOP conditions, at a glance

| Step | Condition | Action |
|---|---|---|
| 2 | Any of the 8 live NAS hashes differs from the table above | STOP. Bishop may have redeployed independently (Watch-for (f)). Do not continue; bring it to Sensei/ip-man. |
| 3 | An exported file contains a CR byte, or its hash doesn't equal `git show <fix-sha>:<path> \| sha256sum` | STOP. The export was corrupted (Watch-for (o)). Re-export in Git Bash. |
| 3 | An exported file's hash doesn't equal the hash jackie-chan/gsp actually signed off on at hunk review | STOP. Wrong commit checked out. |
| 5 | `registry-offsite-s7-precheck.py` exits 1 (any active keyed row listed) | STOP. Default-deny would change the live feed today. Bring it to Sensei (s7) — do not proceed to Step 6. |
| 6 | Any backup command errors (sqlite3 backup, docker exec/cp fallback, journal/outbox copy, code-file copy) | STOP. Do not proceed to Step 7 (s2 — errors must be visible, never swallowed). |
| 7 | Post-copy NAS hash doesn't equal the Step 3 exported hash | STOP. Do not restart (Step 8). Investigate the transfer before going further. |
| 9 | `/health` not ok; wrong `build`; `version`/`agents` changed; feed/mesh/registry/projection diverge outside the named exemptions; journal newest entry mismatches; a traceback in the logs | Deploy failed. Go to Step 10 (rollback). |

---

## Step 1 — set up this run, confirm reachability

*Where:* Venom, Git Bash. *Elevation:* none.

```bash
export TS=$(date -u +%Y%m%dT%H%M%SZ)
export STAGE="/c/Repo/registry-deploy-stage/$TS"
mkdir -p "$STAGE/pre-1" "$STAGE/pre-2" "$STAGE/post" "$STAGE/reviewed"
ssh nas "echo ok"                                   # confirm SSH reachability
git -C /c/Repo/Wonderland status                    # confirm the checkout exists, working tree clean
git -C /c/Repo/Wonderland log --oneline -1          # confirm HEAD is the reviewed <fix-sha>
```
Set `FIX_SHA` to the short SHA confirmed by the last command, and use it for the rest of this run:
```bash
export FIX_SHA=<fix-sha>
```
**If this Git Bash session ever closes and reopens partway through the run** (e.g. a pause for Sensei's decision at a STOP gate), `$TS`, `$STAGE` and `$FIX_SHA` are gone — re-`export` all three with the **same** values recorded from this step, not a freshly-generated `$TS`. A new `$TS` starts a new, empty `$STAGE`, orphaning whatever `pre-1`/`pre-2`/`reviewed` captures already exist from earlier in the same run. Write the three values down somewhere durable the moment they're set.

---

## Step 2 — confirm the live NAS files still match the baseline

*Where:* Venom, Git Bash (runs `ssh` remotely; nothing is written on either side). *Elevation:* none.

```bash
ssh nas "sha256sum /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py \
  /share/home/batman/registry/registry/db.py \
  /share/home/batman/registry/registry/crier.py \
  /share/home/batman/registry/registry/journal.py \
  /share/home/batman/registry/registry/publisher.py \
  /share/home/batman/registry/registry/parse_md.py"
```
Compare line-by-line against "The 8-file baseline" table above. **Any mismatch → STOP.**

---

## Step 3 — export and verify the reviewed fix files (s6)

*Where:* Venom, **Git Bash — not PowerShell.** PowerShell's `>` redirection can silently re-encode a command's output (e.g. to UTF-16) on this machine; `git show` itself never applies a checkout filter, so Git Bash's plain `>` is safe and PowerShell's is the one to avoid (ip-man's ruling §5, s6, Watch-for (o) — measured this session, see "Tooling"). *Elevation:* none.

```bash
cd /c/Repo/Wonderland
git rev-parse --short HEAD        # must equal FIX_SHA -- if not, stop and re-check out the right commit

git show ${FIX_SHA}:services/registry/app.py             > "$STAGE/reviewed/app.py"
git show ${FIX_SHA}:services/registry/registry/schema.py > "$STAGE/reviewed/schema.py"
git show ${FIX_SHA}:services/registry/registry/render.py > "$STAGE/reviewed/render.py"

python /c/Repo/townsquare/docs/registry-offsite-verify-export.py \
  "$STAGE/reviewed/app.py" "$STAGE/reviewed/schema.py" "$STAGE/reviewed/render.py"
```
**STOP if this script exits non-zero (a CR byte was found).** Otherwise, compare each printed SHA-256 against a fresh direct pipe, which never touches disk in between:
```bash
git show ${FIX_SHA}:services/registry/app.py             | sha256sum
git show ${FIX_SHA}:services/registry/registry/schema.py | sha256sum
git show ${FIX_SHA}:services/registry/registry/render.py | sha256sum
```
These must equal the export script's printed hashes exactly. **Then** compare all three against the specific hashes jackie-chan and gsp actually signed off on for `<fix-sha>` at hunk review (from Helio's CHECKPOINT/GATEWAY note) — not a re-derivation of what the diff *should* hash to, the number they actually approved. **Any mismatch anywhere in this step → STOP.**

---

## Step 4 — pre-deploy reads, twice, about a minute apart

*Where:* Venom, Git Bash (plain HTTP reads; the projection script needs Python; nothing SSH, nothing written to the NAS). *Elevation:* none.

Run this whole block once into `$STAGE/pre-1`, wait about a minute, then run it again unchanged except `$STAGE/pre-2`:

```bash
CAP="$STAGE/pre-1"     # then repeat into "$STAGE/pre-2"
curl -s http://192.168.2.3:8789/authorized_keys                 -o "$CAP/ak-plain.txt"
curl -s "http://192.168.2.3:8789/authorized_keys?exclude=venom" -o "$CAP/ak-exvenom.txt"
curl -s http://192.168.2.3:8789/mesh                             -o "$CAP/mesh.json"
curl -s "http://192.168.2.3:8789/journal?limit=5"                -o "$CAP/journal.json"
curl -s http://192.168.2.3:8789/health                           -o "$CAP/health.json"
curl -s "http://192.168.2.3:8789/registry?retired=0"             -o "$CAP/registry.json"
python /c/Repo/townsquare/docs/decision-6-projection.py "$CAP/projection.txt"
```
(`?exclude=venom`, not `?exclude=claude-app` — this matches the P1 captures; excluding `claude-app` excludes nothing today since it isn't registered yet, per Addendum 1 §4.)

---

## Step 5 — run the s7 pre-check

*Where:* Venom, Git Bash (plain Python, local files only — no NAS contact). *Elevation:* none.

```bash
python /c/Repo/townsquare/docs/registry-offsite-s7-precheck.py \
  "$STAGE/reviewed/schema.py" "$STAGE/pre-2/registry.json"
```
**If this exits non-zero: STOP here.** Do not proceed to Step 6. Default-deny would change the live feed beyond what Done-when (5) expects, on data that changed since gsp measured it clean (his own check was against a since-superseded P1 capture). Bring the printed agent list to Sensei.

---

> **Everything from here on writes to the live NAS or restarts the live service.**
> Per the design note §5, the work order's Deploy line, and Helio's GAME PLAN: **Sensei runs these himself, at the terminal, one command at a time as they're handed to him — or someone he names does. A subagent never runs Steps 6–8 or 10 on a relayed yes.** Nothing in this document is authorization to run them; it is preparation for when he says go.

---

## Step 6 — back up code files and the DB [SENSEI'S HANDS]

*Where:* NAS, SSH session as `batman` (from Venom's Git Bash). *Elevation:* none on the NAS host; Step 6b's `docker exec` runs as root *inside* the container, which is inherent to this container's own image (`CMD ["python","app.py"]`, no user set) and needs no extra privilege from `batman` beyond the docker-group membership already confirmed in D1.

**6a. Decide which DB-backup method applies:**
```bash
ssh nas "command -v sqlite3"
```
- **If this prints a path:** use 6b-direct.
- **If it prints nothing / exits non-zero:** use 6b-fallback (gsp's s3).

(This only tests whether the binary exists, not whether `batman` can read `registry.db` — the permissions question dc32913 flagged as open. If 6b-direct's `.backup` command then fails on a permission error, that's still caught by the no-suppression rule below: it will be visible, and the fix is to switch to 6b-fallback, which reads the DB as the container's root user instead and sidesteps the question entirely.)

**6b-direct (sqlite3 CLI present):**
```bash
ssh nas "mkdir -p /share/home/batman/registry-backups/preoffsite-$TS"
ssh nas "cp /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py \
  /share/home/batman/registry-backups/preoffsite-$TS/"
ssh nas "sqlite3 /share/home/batman/registry/data/registry.db \
  \".backup '/share/home/batman/registry-backups/preoffsite-$TS/registry.db'\""
ssh nas "cp -a /share/home/batman/registry/data/journal.log \
  /share/home/batman/registry/data/outbox \
  /share/home/batman/registry-backups/preoffsite-$TS/"
```

**6b-fallback (no sqlite3 CLI — s3, required if used).** Backs up through the container's own Python, entirely outside `/app`, never touching `/app/secrets`:
```bash
ssh nas "mkdir -p /share/home/batman/registry-backups/preoffsite-$TS"
ssh nas "cp /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py \
  /share/home/batman/registry-backups/preoffsite-$TS/"
ssh nas "docker exec agent-registry python3 -c \"import sqlite3; s=sqlite3.connect('/app/data/registry.db'); d=sqlite3.connect('/tmp/registry-backup.db'); s.backup(d); d.close(); s.close()\""
ssh nas "docker cp agent-registry:/tmp/registry-backup.db /share/home/batman/registry-backups/preoffsite-$TS/registry.db"
ssh nas "docker exec agent-registry rm -f /tmp/registry-backup.db"
ssh nas "cp -a /share/home/batman/registry/data/journal.log \
  /share/home/batman/registry/data/outbox \
  /share/home/batman/registry-backups/preoffsite-$TS/"
```
No step in either branch runs `env`, `printenv`, `ls` or `cat` against `/app/secrets` (s3). Neither branch ever runs `tar`, `cp -r` or `rsync` against the registry root (s1) — every file is named explicitly.

**Do not suppress errors on any of the above (s2).** If a command fails, it must be visible. **STOP — do not proceed to Step 7 — and bring the failure to Sensei.**

---

## Step 7 — copy the reviewed files to the NAS; verify; write BUILD [SENSEI'S HANDS]

*Where:* Venom, Git Bash, for the `scp`s; NAS via SSH for the hash check and the `BUILD` write. *Elevation:* none.

```bash
scp "$STAGE/reviewed/schema.py" batman@192.168.2.3:/share/home/batman/registry/registry/schema.py
scp "$STAGE/reviewed/app.py"    batman@192.168.2.3:/share/home/batman/registry/app.py
scp "$STAGE/reviewed/render.py" batman@192.168.2.3:/share/home/batman/registry/registry/render.py

ssh nas "sha256sum /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py"
```
Compare against Step 3's exported-file hashes. **Any mismatch → STOP. Do not restart.**

Only once that matches, write `BUILD` (Addendum 1 §4 — after the copy and hash check, before the restart):
```bash
ssh nas "echo -n '$FIX_SHA' > /share/home/batman/registry/BUILD"
ssh nas "cat /share/home/batman/registry/BUILD"      # visual check: exactly FIX_SHA, no trailing newline
```

---

## Step 8 — restart the container [SENSEI'S HANDS]

*Where:* NAS, SSH session as `batman`. *Elevation:* none.

```bash
ssh nas "docker restart agent-registry"
```
Per D3, this is **not** a quiet reload: it immediately restarts the Crier poll thread (first poll near-instant, then every 60s) and immediately attempts an outbox-drain to the live `gdrive_rw` Google Drive remote, then every 120s thereafter. Expect this in Step 9's verification — it is why `/journal`'s volatile fields are exempted below, not a sign of a broken deploy.

---

## Step 9 — verify, read-only

*Where:* Venom, Git Bash. *Elevation:* none. (This step itself is read-only; it may be run by the session, per "Who runs what.")

```bash
CAP="$STAGE/post"
curl -s http://192.168.2.3:8789/authorized_keys                 -o "$CAP/ak-plain.txt"
curl -s "http://192.168.2.3:8789/authorized_keys?exclude=venom" -o "$CAP/ak-exvenom.txt"
curl -s http://192.168.2.3:8789/mesh                             -o "$CAP/mesh.json"
curl -s "http://192.168.2.3:8789/journal?limit=5"                -o "$CAP/journal.json"
curl -s http://192.168.2.3:8789/health                           -o "$CAP/health.json"
curl -s "http://192.168.2.3:8789/registry?retired=0"             -o "$CAP/registry.json"
python /c/Repo/townsquare/docs/decision-6-projection.py "$CAP/projection.txt"
ssh nas "docker logs agent-registry --since 5m"
```

**Checks:**
```bash
diff "$STAGE/pre-2/ak-plain.txt"    "$STAGE/post/ak-plain.txt"    && echo "feed (plain) unchanged"    || echo "MISMATCH -- feed (plain)"
diff "$STAGE/pre-2/ak-exvenom.txt"  "$STAGE/post/ak-exvenom.txt"  && echo "feed (exclude=venom) unchanged" || echo "MISMATCH -- feed (exclude=venom)"
diff "$STAGE/pre-2/mesh.json"       "$STAGE/post/mesh.json"       && echo "mesh unchanged"            || echo "MISMATCH -- mesh"
diff "$STAGE/pre-2/registry.json"   "$STAGE/post/registry.json"   && echo "registry unchanged"        || echo "MISMATCH -- registry"
diff "$STAGE/pre-2/projection.txt"  "$STAGE/post/projection.txt"  && echo "projection unchanged"      || echo "MISMATCH -- projection"

python /c/Repo/townsquare/docs/registry-offsite-journal-diff.py \
  "$STAGE/pre-2/journal.json" "$STAGE/post/journal.json"

python -c "
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
print('ok:', d.get('ok'))
print('build:', d.get('build'))
print('version:', d.get('version'))
print('agents:', d.get('agents'))
" "$STAGE/post/health.json"
```

**Expected:**
- feed (both forms), mesh, registry and projection: byte-identical to `pre-2` (nothing today registers between pre-2 and post, and s7 already confirmed default-deny changes no live row).
- `registry-offsite-journal-diff.py` exits 0 (op/agent/applied_at of the newest entry unchanged). Its own printed note about `publishing`/`outbox_pending`/`publisher.*` is expected, not a failure — D3's automatic drain.
- `/health`: `ok: True`, `build: <FIX_SHA>`, `version: 1.2` (unchanged — R7 withdrawn), `agents:` the same count Step 4 captured.
- `docker logs --since 5m`: no traceback.

**If everything above holds, the deploy is verified.** If anything doesn't, go to Step 10.

Per s4: don't paste this step's raw `docker inspect`/`docker logs` output into any board note or repo document — summarize ("no traceback") or filter to the specific lines that matter, and scan for `token`/`refresh_token`/`client_secret`/`password` before committing anything that came from a live read.

---

## Step 10 — rollback, if anything fails [SENSEI'S HANDS]

*Where:* NAS, SSH session as `batman` — this is a same-host copy from the Step 6 backup, no `scp`/Venom round-trip needed. *Elevation:* none.

```bash
ssh nas "cp /share/home/batman/registry-backups/preoffsite-$TS/app.py    /share/home/batman/registry/app.py"
ssh nas "cp /share/home/batman/registry-backups/preoffsite-$TS/schema.py /share/home/batman/registry/registry/schema.py"
ssh nas "cp /share/home/batman/registry-backups/preoffsite-$TS/render.py /share/home/batman/registry/registry/render.py"
ssh nas "sha256sum /share/home/batman/registry/app.py \
  /share/home/batman/registry/registry/schema.py \
  /share/home/batman/registry/registry/render.py"
```
Compare against "The 8-file baseline" table — must match exactly (back to `ede80e1`'s code).
```bash
ssh nas "echo -n 'ede80e1' > /share/home/batman/registry/BUILD"
ssh nas "docker restart agent-registry"
```
Re-run Step 9 afterward. The DB backup should not be needed for this fix (no schema/data migration) — restoring it is a break-glass extra, only if data corruption is actually observed, not a default rollback action:
```bash
ssh nas "cp /share/home/batman/registry-backups/preoffsite-$TS/registry.db /share/home/batman/registry/data/registry.db"
```

---

## Runbook status

**Complete and ready to execute once (a) `<fix-sha>` exists — bruce-lee's code committed, jackie-chan's diff review and gsp's hunk confirmation both landed — and (b) Sensei gives his go on Steps 6–8/10.** Nothing else is blocking this document.

**The sqlite3-on-NAS question I flagged as open last time (dc32913, Flag 5) is resolved procedurally, not by learning the answer.** Step 6a tests for `sqlite3` live and branches; either branch is fully specified and was reviewed (6b-direct is D2's original method, 6b-fallback is gsp's s3, ruled required by ip-man). Whether the NAS actually has `sqlite3` installed is still unknown until Step 6a runs — that's fine, the runbook no longer needs the answer in advance.

**Explicitly out of scope for this document, not gaps in it:**
- F1's Drive-folder-sharing check, before any push of `internal` — Sensei's own look in Drive, unrelated to the NAS deploy.
- The `offsite-binding` branch push to Wonderland (private repo) — the session's Board duty, only after the deploy is verified, never to `main`.
- The actual claude-app registration (the "second send") — a separate action under ip-man's v5 §4 amendment, needing its own separate go from Sensei. This runbook ends at Step 9's verification.

---

## Files read this session

`C:\Repo\townsquare\docs\`: `francis-ngannou-registry-deploy-prep-20260926.md`, `ip-man-registry-offsite-binding-design-20260926.md`, `ip-man-registry-offsite-addendum-1-20260926.md`, `jackie-chan-registry-offsite-review-20260926.md`, `gsp-registry-offsite-security-review-20260926.md`, `ip-man-registry-offsite-security-ruling-20260926.md`, `helio-gameplan-registry-offsite-fix-20260926.md`, `decision-6-projection.py`, `reference-authorize_from_registry-20260926.md`.

**Commands run this session (all read-only or scratch-local; nothing against the live NAS, nothing written to Wonderland's tracked history):**
- `git -C C:\Repo\Wonderland status/log/branch/sparse-checkout list` — read-only, to confirm ronda's checkout state without disturbing it.
- `git show ede80e1:services/registry/{app.py,registry/schema.py,registry/render.py}` in Git Bash, piped to `sha256sum` and exported to a scratch dir, cross-checked against a working-tree read of the same files — reproducing jackie's `core.autocrlf` finding independently and confirming all three hashes equal `dc32913`'s D5 table.
- The three helper scripts, run repeatedly against synthetic and real fixtures in the scratchpad (pass/fail/error paths for each), then smoke-tested again from their final committed location in `C:\Repo\townsquare\docs\`.

I wrote nothing to the NAS, restarted nothing, and pushed nothing.
