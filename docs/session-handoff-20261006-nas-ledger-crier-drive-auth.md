# Session handoff, 2026-10-06: Drive auth, the NAS ledger replacement, and one reconciled Crier

**Written for a new session.** The operator said "hold, and save the documentation for a new session." Nothing is running. Nothing needs doing before a new session starts, apart from the dated items in section 4. This file is the single place to resume from. Author: the orchestrating session ("New TownSquare"). Basis tags: [m] measured, [i] inferred, [r: X] reported by X.

**First actions for a new session**
1. Read this file. Do not dispatch any agent: the operator held everything and several items wait on his word (section 3).
2. Run `python C:\Repo\townsquare\tools\crier-reauth.py --check` on Venom. The Crier's Google token expires about 2026-10-13; the next one-click re-auth is due by about 2026-10-12.
3. Ask the operator which open item to pick up.

---

## 1. What happened today, in order

1. **The Crier went stale.** `/health` returned 503 with `invalid_grant`; last good poll 2026-09-29 [m]. Cause: its Google OAuth client (client id starts 416116040158) is in "Testing" status, so Google kills its refresh token every 7 days. The config was last written 09-22, exactly 7 days before the last good poll [m].
2. **The re-auth script was written and used.** `tools/crier-reauth.py` (commit `a59592f`, already pushed to `origin/internal`). It reads the remote's client settings from the NAS, runs `rclone authorize` locally, checks the consent page asks for our client and `drive.readonly`, backs up the NAS config, installs the token over ssh stdin, verifies inside the container, waits for `/health`. `--check` reports health and token age; `--dry-run` stops before the consent click. Two bugs were found and fixed while testing (Windows text-mode stdin turned `\n` into `\r\n`; rclone 1.75 prints a base64 config blob, not raw token JSON). The operator ran it himself at 2026-10-06T12:57Z and again at 13:52:50Z; the Crier is healthy and the token marker says 7.0 days left [m].
3. **A second dead login was found.** The agent-registry container's publisher remote `gdrive_rw` (`/app/secrets/rclone.conf`, scope `drive`) uses the same own client, was last written 2026-09-14, and fails `invalid_grant` today [m]. It went unnoticed because the registry journal has had no write since 2026-09-14. The Wonderland README and `publisher.py` comment saying it uses rclone's shared client are wrong [m].
4. **The operator ruled Google Drive a proof of concept.** The final solution is a dockerized framework on the NAS. ip-man drafted it (section 2).
5. **A Crier version divergence was found.** The deployed Crier is not the repo's `crier/crier.py` (section 2). ip-man ruled on one reconciled version.
6. **Helio gave the status of the NAS move** (below, section 5).

## 2. Documents produced today (all in `C:\Repo\townsquare\docs\`, branch `internal`, committed, NOT pushed)

Agent outputs were filed with `save_verbatim.py splice`; the hash is the one the tool printed. Header notes above each provenance line are by the orchestrating session.

| Document | What it is | Commit | Tool hash (sha256, first 12) | Standing |
|---|---|---|---|---|
| `ip-man-nas-ledger-design-v1-20261006.md` | ip-man's design for the NAS-hosted ledger replacing Drive: features, 25 acceptance criteria, infrastructure targets, migration, risks, slices S0–S6 (worst case about $256), doctrine impacts listed | `568701a` (+ header pointers in `f3e27f9`) | `ee74650d54f6` | DRAFT, not reviewed, not adopted. Section 8 withdrawn by delta 1.1 |
| `ip-man-nas-ledger-design-delta-1-20261006.md` | Delta 1: bridge to Google runs on any host (lease, failover, AC26) after the operator rejected a Venom-only bridge. **Erratum header**: two of its recommendations contradict operator rulings | `5952ea9` | `2e500f84af6f` | Superseded where it disagrees with delta 1.1 |
| `ip-man-nas-ledger-design-delta-1.1-20261006.md` | Delta 1.1: removes the closed routes; primary bridge = a Drive-for-desktop host (Venom today, fs backend), NAS `town-bridge` rclone container ships DORMANT as a standby; restated G3/F11/AC25/C7; risks re-rated; RK15 | `f3e27f9` | `db04356bd951` | DRAFT; governs over v1 and delta 1. Total about $261 worst case |
| `ip-man-nas-drive-shared-client-stopgap-20261006.md` | ip-man's ruling on switching both NAS Drive logins to rclone's shared client | `900f9a9` (+ withdrawal header `f3e27f9`) | `581f148209fb` | **WITHDRAWN.** Do not act on it. Its finding that `gdrive_rw` is dead and shares the Crier's client stands |
| `crier-version-comparison-20261006.md` | Measured comparison of three Crier versions, test matrix, merge trial, reproduction commands | `f5b628c` | (written by the orchestrating session, no hash) | Facts, not a ruling |
| `ip-man-crier-one-version-ruling-20261006.md` | ip-man's ruling and work order for one reconciled Crier, acceptance criteria AC1–AC9, ratings, cutover/rollback sketch, budget | `90117d2` | `e22dc09a7459` | RULING; nothing started. Budget awaiting the operator |

Other sessions' documents in the same folder (not mine; read, not changed): Kano's doctrine passes 1–4 and drafts (`kano-townsquare-doctrine-*-pass1..4-handback-20261006.md`, `town-square-doctrine-v1.6-draft-1/2`, `town-square-doctrine-v2.0-draft-3`, `town-square-doctrine-v2.0-draft-4` and its commentary, `town-square-binding-google-drive-v1.0-draft-1`), and the Venom session's `townsquare-doctrine-project-scope.md`. **Kano's pass 4 landed in commit `727823f` after I told the operator it had not; I have not read it.** The operator asked to see Kano's proposal on the documents and their scope; start there.

### The Crier divergence, in short [m, details in the comparison doc]
- **Deployed:** NAS container `crier`, image built 2026-09-13, source `~/crier-docker/crier.py`, sha256 `055fc54ef979…`, equal to Agentic repo commit `40c65fa` on `origin/feat/agent-shuri`. It has the poller guard and thread-level `for`/`cat` routing.
- **Repo `crier/crier.py` (HEAD `4726278`):** has the Registrar's shared grammar (`pid`, `mode`, `check_header`), lacks the guard and the routing, and cannot run in today's image (it imports `registrar.app.filename`, which the image does not contain).
- **Tests:** the repo's `test_crier.py` (21 checks) passes on repo HEAD and fails on deployed (`KeyError: 'pid'`). The Docker line's three suites (in `~/crier-docker/tests/` on the NAS) pass on deployed and fail on repo HEAD.
- **A third item,** Agentic `7305c81` ("/events stops excluding"), is "NOT LANDED. NOT DEPLOYED"; ip-man leaves it out; its board thread `TS-20260913-forge-012` is still WORKING.
- **ip-man's added rule C:** at least 6 live board names (five Seeking posts with a `host-` token, one event with a duplicate `to-`) are rejected by the shared parser and would be dropped from the index; the merged Crier must index such names identity-only instead [r: ip-man, measured by Glob of the board folder].

## 3. Operator decisions: what he has said, and what is open

**Said (do not re-ask, do not re-propose):**
- Google Drive is a POC; the final solution is a dockerized framework on the NAS.
- Making Venom the ONLY machine that talks to Google: "No, I do not want this restriction." (Bridge stays host-agnostic.)
- Publishing the OAuth app "In production": closed ("now a lengthy process").
- rclone's shared client: "no shared client solution. We are taking a different approach." The different approach is the NAS replacement (confirmed "correct").
- Google service account: closed ("tried before… did not work as expected due to policy changes from Google"). Workspace "Internal" app: closed (he does not own advocationpr.com).
- Bridge until cutover: the weekly one-click re-auth. He executed it himself.
- "Hold" on the NAS ledger S0 review round until he has seen Kano's document proposal. Then, today: "hold, and save the documentation for a new session."

**Open, ranked, blockers first** (the operator's to decide):
1. **Crier job budget:** approve $96 worst case, or $116 with one fix loop? Blocks the single Crier version he asked for. ip-man's S0 (two reviews plus Helio's plan, $27) starts on his yes. Recommendation: yes.
2. **Adopt the two-document doctrine form** (Doctrine 2.0 naming no infrastructure, plus a separately adopted Google Drive binding), replacing v1.5? Blocks doctrine review. (From the Venom session's working scope, with its other four decisions: which amendments; the "try it 2 to 4 weeks" pilot question; the provenance field; Revere build go = not now.)
3. **Release the NAS ledger S0 review round** after he has seen Kano's proposal; approving S1–S6 (about $261 worst case) comes after S0. Recommendation: yes, later.
4. **Park forge's unfinished `/events` proposal (`7305c81`)?** Not blocking. Recommendation: park.
5. **The `townsquare-registry-writer@gen-lang-client-0623283501…` service account still has edit rights on the TownSquare folder** (measured via the Drive permissions listing); its key's location is unknown. Only he can see its keys or remove the grant. Not blocking; ip-man recommends removing it after checking its key list.

## 4. Dated items
- **By about 2026-10-12:** Crier one-click re-auth (`python C:\Repo\townsquare\tools\crier-reauth.py`, on Venom). The token issued 2026-10-06T13:52:50Z expires about 2026-10-13.
- **2026-10-09 (Friday):** the Doctrine request `TS-20261006-venom-001` is due for the operator's acceptance [r: the Venom session's scope file]; Kano's v1.6 question is due the same day [r: Helio]. These belong to the doctrine session, not to this one.
- The tracker trial window runs to about 2026-10-25/26 [r: earlier notes].

## 5. State of the NAS move (Helio's determination, 2026-10-06; he could not open a shell, so live facts were mine)
- **Town Registrar:** live promotion ran 2026-09-22 (1,070 posts, 197 artifacts, 313 roots) [m on the NAS DB]. The database is a frozen snapshot: no import job exists, the Registrar has no Drive credential, verification is built but off (`verification_reports=0`), native writes are built but never enabled. The viewer (port 8502) is running.
- **Agent Registry:** live on :8789 with 25 agents. The "offsite" fix for registering the operator's phone Claude app has tests only (branch `offsite-binding`, ronda's `6f2c08b`), no fix code, stalled since 09-26. Helio's re-checkpoint of `6f2c08b` was stopped before a verdict on 09-26 and still needs a fresh dispatch; it was NOT restarted today because the operator was focused on Drive.
- **Drive logins on the NAS:** Crier works (weekly click); registry `gdrive_rw` dead; Registrar none.

## 6. Measurements and concerns worth keeping [m unless tagged]
- **NAS (ASUSTOR, 192.168.2.3):** Celeron N5105, 4 cores; 11.7 GB RAM (~9.6 GB available; Kollective uses ~3.1 GiB); Docker 28.1.1. Volumes: `/volume1` 1.9 TB single NVMe (no redundancy), `/volume2` 230 GB, `/volume3` 1.9 TB single NVMe, `/volume4` 9.1 TB single disk, `/volume29` 1.4 TB RAID5 4/4 healthy (also `/share/Backups`, writable by batman). Drive account: 6 TiB total, 5.3 TiB free.
- **Ledger scale:** 1,345 files in the 09-22 inventory, total 4.4 MB; median `.txt` 3,010 B, max 36,916 B; zero duplicate full paths in that inventory. Growth about 4 events/day [i].
- **Venom:** 9 shutdown/start cycles in 30 days, about 0.2 h recorded stopped; no sleep/wake events logged in 30 days. No Docker on Venom (Windows or its stopped WSL2 Ubuntu), so the NAS is the only Docker host.
- **Ports:** 8786 and 8791 free on the NAS; the Registrar is published on loopback only (`127.0.0.1:8790`), so not reachable from the LAN yet.
- **CONCERN (unsaved probe, not a bug):** from inside the viewer container, `registrar:8790` refuses connections and the name resolves to the viewer's own address on the shared network (`172.23.0.2`); the viewer may not be reading the Registrar. Route to the infrastructure reviewer.
- **NAS Docker trap [r: bishop]:** ADM runs dockerd with `--iptables=false`, which kills Docker's embedded DNS on user-defined networks; containers there use `network_mode: bridge`.
- The `rclone.conf` backups from today sit beside the config on the NAS: `.bak-20261006T125714Z`, `.bak-20261006T135249Z`. Nothing deleted.

## 7. Rules a new session must carry
- **No push without the operator and the pre-push check** (`git log --oneline origin/internal..HEAD`, confirm every commit is recognised). When this file was written, 11 local commits were unpushed, plus this file's own commit: six of mine (`900f9a9`, `568701a`, `f5b628c`, `5952ea9`, `f3e27f9`, `90117d2`) and five by the doctrine session (author "QA": `4ad944c`, `9d80d33`, `1c0aa61`, `c870fc1`, `727823f`). The only commit of mine already pushed is `a59592f` (the re-auth script). The repo `terrence-adams/townsquare` is **public**.
- **The tree is shared** with the doctrine session (Kano's drafts commit here). `git add` explicit paths only; never `-A`, `commit -a`, stash, reset or branch switches. Stay on `internal`.
- **The word "verbatim"** appears only next to a hash the tool printed. Today's first two briefs to Helio and ip-man labelled the operator's words "verbatim" although I had copied them by hand; later briefs did not.
- **No proof, no bug:** a defect needs a saved re-runnable script or test failing on a clean clone of a named commit; anything less is a CONCERN and is not built for. The Crier differences above are measured test results, not filed defects.
- **Tests before implementation** (ronda-rousey commits failing tests, then bruce-lee builds, never self-tested); reviews run one at a time; Helio checkpoints each handoff; core work goes through ip-man's work order, not the orchestrating session.
- **Deployment of any Crier change is the operator's own step** (gated). Nothing was deployed or changed on the NAS today except the Crier's rclone config (the operator's two re-auths, backed up).
- Filing an agent's output: `python C:\Repo\Agentic\tools\save_verbatim\save_verbatim.py splice <subagent transcript.jsonl> <target.md> --header <my-header.md>`, then `verify`. Transcripts live at `C:\Users\terre\.claude\projects\C--Workspace\<session-id>\subagents\agent-<agentId>.jsonl`.

## 8. Where things physically are
- The re-auth script: `C:\Repo\townsquare\tools\crier-reauth.py`. Deployed Crier source and packaging on the NAS: `~/crier-docker/` (Dockerfile, docker-compose.yml, README.md, DOCKER-CUTOVER.md, `tests/`). Live Crier state: `~/crier-data/state.json`. Rclone config the Crier mounts: `~/.config/rclone/rclone.conf`.
- Scratch copies used for the comparison were under the session scratchpad (`...\scratchpad\crier-cmp\`), which may not survive. Everything needed to rebuild them is in the "How to reproduce" section of `crier-version-comparison-20261006.md`.
- Memory notes written today: `project-crier-gdrive-reauth.md`, `project-nas-ledger-replacement.md` (both indexed in `MEMORY.md`), and corrections to `project-townsquare-registrar.md` (phase C did run on 09-22).
