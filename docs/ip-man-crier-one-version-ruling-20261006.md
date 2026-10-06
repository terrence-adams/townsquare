# ip-man ruling and work order: one reconciled Crier

Date: 2026-10-06. Requested by the orchestrating session after the operator asked: "do a compare on functionality and create one version as a solution" (copied from the chat, not tool-extracted). Facts it rests on: docs/crier-version-comparison-20261006.md. Status: RULING and WORK ORDER, not yet started. Nothing built, nothing deployed. ip-man had no shell for this run, so his "passes" and "fails" are inferences unless he marks them measured. Two budget decisions at the end are the operator's.

<!-- verbatim sha256=e22dc09a745950af384479d0607474527eb81bd8eb4b223fe45973d0e7f473de source=C--Workspace/fa5f5b3d-d9ba-4d32-94ad-d0571415f8fc/subagents/agent-af5812f3abbdcdcc5.jsonl:216 message=msg_011Cfm7P9SrF3QAD56b2Uigs -->
**Crier: one version. My ruling, design note and work order (2026-10-06)**

**Where to save it:** the session saves this note verbatim to `C:\Repo\townsquare\docs\ip-man-crier-one-version-ruling-20261006.md`. I changed nothing, on the NAS or anywhere else. Tier 0.x.

**Basis tags:** [m] measured by me this run (a file read, a Glob or a grep). [i] inferred, which includes code I read but did not run. [a] assumed. [r: X] reported by X. Each claim carries one tag. I had no shell this run, so I could not run git or any test. Every "fails" or "passes" in this note is [i], unless the session measured it.

**Abbreviations:**
- AC = acceptance criterion.
- L/S/P = likelihood, severity, priority.
- S0–S2 = the slices of this job.
- `pid-` = the Registrar's post-id filename token. Its value is a ULID, a 26-character sortable id.
- OFFER = the Seeking board's post type.

**The problem.** The live Crier (Agentic `40c65fa`) and the repo Crier (townsquare `4726278`) each have fixes the other lacks, and each fails the other's tests [r: session]. Sensei wants one version: it keeps all live behaviour, adds the Registrar's shared filename grammar, has one home, and ships safely.

---

## 0. Who depends on the Crier

| Consumer | What it reads | Basis |
|---|---|---|
| Host pollers (`poller/townsquare-poll.py` and the ansible template) | `/watermark` (seq, last_poll_ok); `/open?host=` (threads' priority, thread, action, verified, state, subject); `/fleet` (collisions: unresolved, duplicate_openings, duplicate_sequences) | [m: poller lines 61-129] |
| Agent Registry poller | `/events?since=` **with no host**, so the host filter never applies to it. Per-event seq, by and filename; it looks for `cat` on the event and falls back to the filename token `cat-registration`. Top-level seq. `/health` ok, stale, poll_seconds | [m: Wonderland/services/registry/registry/crier.py:104-317] |
| Docker HEALTHCHECK | the `/health` status code | [m: NAS Dockerfile:30-31] |
| Registrar | No runtime calls. Its design requires one parser "shared by Registrar, `ts-sign`, `ts-verify`, and Crier". Its criterion 7: "New filenames parse in compatible Crier versions and PID is not mistaken for subject" | [m: town-registrar-design.md:158-163, 558] |
| Thread-level `for` and `cat` | Agent routing (operator, 2026-09-12) and the registration token contract (bishop-006) | [r: NAS README] |
| Viewer | Does not call the Crier | [m: grep of viewer/ with .venv excluded found no matches] |
| Tracker projector | Reads `G:\` through `parse_filename`, not the Crier. Any edit to `filename.py` would reach it | [m: tracker/tests/test_filename_token_reproduction.py] |
| My NAS ledger draft v1 (not adopted) | Reuses the Crier "unchanged", reading a local tree. Its AC3 names "the Crier's NAME_RE". It retires `pid-` | [m: ledger draft §2, AC3] |
| Humans | `/thread` and `/active`, via curl from the drop file | [m: poller:103-104] |

**What I could not establish:**
- Which poller each host actually runs. The NAS README says one renders a `for` column [r: NAS README]. A comment in `7305c81` says one writes BULLETINS.log, filtered on board [r: 7305c81]. Neither poller is in the townsquare repo.
- Whether TownWatch or any dashboard calls the Crier.
- What the `e0a6f44` design record says. I had no shell to run `git show`.
- The live Crier's health today.
- Whether there is a Docker host other than the NAS for QA.
- The ledger draft's measurement M1 (which Crier source is deployed) is now answered: it is Agentic `40c65fa` [r: session, sha256 match].

## 1. What the one version contains

**Ruling.** I confirm your recommendation: deployed behaviour, plus the shared grammar, with `7305c81` left out. I add one amendment, which I call **rule C**.

**Why rule C is needed.** The shared parser rejects names that the deployed Crier indexes. At least 6 such names are on the board today [m: Glob of G:\, 10-06]:
- **Five OFFER openings named `__host-<x>__<summary>`:** jeangrey-001, venom-001, bishop-001, bishop-002 and cable-001. Doctrine §7b defines `host-`, but the parser's typed list lacks it. The summary then reads as a second slug and the parse fails with "duplicate slug field" [r: town-registrar-ws1-ws2-plan.md:79].
- **One event with a duplicate `to-`:** `TS-20260913-forge-005.002` carries `to-forge__to-wolverine` [m].

Repo HEAD would drop all six from the index. Five OFFER threads would vanish, and forge-005 would lose its head event [i]. Every future OFFER post would vanish too.

Forge reports the operator's premise as: "it's a closed system. The point of it is visibility and traceability.", which makes missed delivery the only harm [r: forge, TS-20260913-forge-012.001].

**Rule C:**
- `parse_name` uses the shared parser and returns None when it rejects a name, so `test_crier.py` stays as written.
- `poll()` then indexes that event **identity-only**:
  - thread, seq, state, namespace and board come from the shared module's `NAME_RE`;
  - every typed field is None;
  - the reason is kept as `parse_error` in the event record, and no endpoint serves it.
- Nothing is dropped. No token value wins by first or last position, and the Crier keeps no second token parser.

**Alternatives I rejected:**
- **(A) Repo HEAD as it is.** It drops the six live names and every future OFFER post.
- **(B) Fall back to the deployed, tolerant parser.** That would give exact parity, but it means a second token parser and last-wins routing. The Registrar design forbids both (town-registrar-design.md:159-163).

**Live effect at cutover: none on existing events** [i]. `poll()` skips every ID already in `seen`, and the state file carries over, so old events keep their deployed parse. Rule C acts only on new names, or after a state reset. After a reset, the 5 OFFER threads show no subject until `filename.py` learns `host-`. The WS3 plan deferred that fix: "`filename.py` is shared with Crier and carries regression risk" [m: town-registrar-ws3-plan.md:74].

**Behaviour, by where it comes from:**
- **In both versions, identical:**
  - configuration and lifecycle constants;
  - newest-event-wins, with a timestamp tie-break;
  - board and subject taken from the opening event;
  - priority and `to` carried forward; claimed_by;
  - collision detection, with its unresolved/historical split;
  - the signed/verified roll-up;
  - verification returns None when it is off;
  - a transport failure counts as None, not as forgery;
  - `poll()`: a listing error is recorded, verification runs outside the lock, pruning happens only on a non-empty listing, the first run seeds silently, the watermark advances;
  - atomic save and load;
  - the endpoints `/health`, `/watermark`, `/open`, `/active`, `/fleet`, `/events` (including its host filter) and `/thread`.
- **From deployed:** the poller guard; thread-level `for` and `cat`.
- **From repo HEAD:**
  - `parse_filename`;
  - `pid` and `mode` on events and in the per-event view;
  - rejection of duplicate, empty or non-canonical tokens;
  - `check_header` inside `verify_event`;
  - the `sys.path` import.
- **New:** rule C.
- **Dropped:**
  - the deployed local `NAME_RE` and its tolerant parsing loop;
  - the event key `host`, which no endpoint ever serves [i].

**Where the two disagree, and which wins:**

| # | Point | Deployed | Repo HEAD | Winner, and why |
|---|---|---|---|---|
| 1 | Token parsing | local regex, last wins | shared parser, rejects | Repo HEAD plus rule C: one grammar, nothing dropped |
| 2 | `host-` | event key, never served | becomes the slug, or is rejected next to a summary | Repo HEAD. Nothing served changes while the state carries over [i]. R5 records what happens after a reset |
| 3 | `for` and `cat` on the thread | yes | no | Deployed: the consumers above depend on them |
| 4 | `pid` and `mode` in the per-event view | no | yes | Repo HEAD: an addition only, and null on every live event (no `__pid-` or `__mode-` name exists [m: Glob]) |
| 5 | Poller guard | yes | no | Deployed |
| 6 | Header binding when verifying | priority and to only | every typed field | Repo HEAD: one grammar, and no live effect (see below) |
| 7 | requirements.txt | exact pins | version ranges | Deployed: keeps parity; its own stated reason is that "a silent dependency bump is not worth the risk" |
| 8 | Example names in comments | live agent names | generic | Repo HEAD |
| 9 | start.sh | not used by the image | present | Keep it, marked legacy, and leave it out of the image |

**Can the stricter verification change a live outcome? No.**
- `verify_event` returns None before it reaches `check_header` whenever `TS_ALLOWED_SIGNERS` is unset [i: crier.py:195-196].
- The live compose file sets no `TS_ALLOWED_SIGNERS`, and the image ships no ssh-keygen [m: NAS docker-compose.yml:40, Dockerfile].
- Switching verification on later would change outcomes; R8 records that.

**`7305c81` is left out. It was never adopted:**
- Its own commit message says "NOT LANDED. NOT DEPLOYED" [r: session].
- Its board thread `TS-20260913-forge-012` ends at `.003 WORKING` and was never resolved or closed [m: Glob].
- Its author measured that its `board` change "trades one dropped bulletin for another … Neither lands" [r: forge, forge-012.001].

## 2. Where it lives and how it ships

**One home: `C:\Repo\townsquare\crier\`.**
- `crier.py`: the merged file.
- `test_crier.py`: stays where it is, because it imports from its own directory.
- `tests/`:
  - the Docker line's three test suites, `_stub.py` and `repro_startsh_guard.sh`;
  - the new rule tests and the parity test;
  - `fixtures/`.
- `tests/oracle/crier_deployed_055fc54e.py`: the deployed file, byte for byte, pinned by sha256.
  - It is the oracle for the parity test and the archive of the deployed version.
  - `crier.py` never imports it, and it never goes into the image.
- Packaging files:
  - `Dockerfile` and `docker-compose.yml`;
  - `README.md`: the NAS README, brought up to date;
  - `DOCKER-CUTOVER.md`: rewritten;
  - `requirements.txt`: the NAS pins;
  - `config.example.env` and `start.sh`.

**How the image gets the shared parser:**
- The build context is the repo root, and the Dockerfile sits at `crier/Dockerfile`.
- The image layout mirrors the repo: `/app/crier/crier.py` and `/app/registrar/app/{__init__,filename}.py`. The existing `parents[1]` import then works unchanged, and the image runs `python crier/crier.py`.
- A context filter lets in only those files. `registrar/app/__init__.py` is a docstring and nothing else, so the import pulls in nothing more [m].
- I rejected a vendored copy of the parser: two copies of the grammar is exactly the drift this job removes.

**Pins.** Pin the rclone version (with a checksum) and the base image. Today the build fetches `rclone-current` [m: NAS Dockerfile:13].

**Agentic's copy.** Unchanged. `feat/agent-shuri` stays as history. The townsquare README records the provenance: `40c65fa`, sha256 `055fc54e...`, `7305c81` excluded, thread forge-012. There is no commit in Agentic: its working tree is shared and that branch is not checked out.

**The NAS directories.** Nothing changes now. At cutover:
- The old container is stopped and renamed, never removed, and its image gets a rollback tag.
- `~/crier-docker` stays as the rollback project until Sensei closes the rollback window.
- Then it moves into `~/crier-archive/<name>-<date>/`, with a `MANIFEST.sha256` written first.
- `~/crier` gets the same treatment, after `crontab -l` is checked for an `@reboot` line.
- Nothing is deleted.

## 3. Acceptance criteria (0.x, one page)

1. **Declared use.** Hosts and agents on the home LAN read the Crier over HTTP. The data is board filenames, which hold no secrets.
   - In scope: the source, its tests and its image.
   - Out of scope: deployment, `7305c81`, the `host-` parser fix, rename blindness, state-file validation, and the NAS ledger work.
2. **Ratings.** Likelihood is counted per board name for parsing, per rebuild for packaging, and per cutover for rollback. These outcomes are High:
   - an event the deployed Crier indexes is missing from the merged index;
   - a thread's state, to, for, cat, from or collision flags differ from the deployed Crier's outside the allowed list;
   - the rollback image or the state is lost;
   - the Crier gains a write path.
3. **Pass rules**, each run on a clean clone of the build commit:
   - **AC1 – the four suites pass.** `python3 crier/test_crier.py` gives 21/21. `python3 crier/tests/test_collisions_and_ordering.py`, `test_for_routing.py` and `test_poller_guard.py` each exit 0.
   - **AC2 – the merge rules hold** (`crier/tests/test_merge_rules.py`):
     - `pid` and `mode` are typed, and appear in the per-event view;
     - `for` and `cat` carry to the thread;
     - a rejected name is indexed identity-only: the thread exists, its state and seq count, its typed fields are None, and `parse_error` is set;
     - `crier.py` has no grammar regex of its own and imports `registrar.app.filename`.
   - **AC3 – parity with the live Crier** (`crier/tests/test_parity.py`):
     - (i) The merged Crier is loaded with the captured live state. Its answers to `/open` (for every host named in the state, plus "all"), `/events` (with no host and with each host), `/fleet` and `/watermark` equal the captured live answers.
     - (ii) A fresh seed from the listing rebuilt out of that state gives the same thread views from the merged Crier as from the oracle.
     - Only these differences are allowed:
       - the `pid` and `mode` keys;
       - the order of the `/events` list;
       - timestamps;
       - in (ii) only: the watermark, and threads that hold a rejected name, which the test lists one by one.
     - At least 6 rejected names exist today; the test measures the full set.
   - **AC4 – the image builds clean:**
     - `docker build -f crier/Dockerfile .` exits 0;
     - `docker run --rm <img> find /app -type f` lists only `crier.py`, the two registrar files and `requirements.txt`;
     - `pip freeze` matches `crier/requirements.txt`;
     - rclone is pinned, and its checksum is verified during the build.
   - **AC5 – health.** Run with a fake rclone that serves the fixture listing, `/health` returns 200 within 30 s, and Docker reports the container healthy.
   - **AC6 – the poller guard holds.** The fake rclone injects these faults:
     - it exits 1 → `/health` returns 503 and names the rclone error;
     - it sleeps past `TS_RCLONE_TIMEOUT` → 503, naming the timeout;
     - a fault after the listing (a failing save) → 503, naming "poller:".
     - Once the faults clear, `/health` returns 200 within two polls, and RestartCount stays 0.
   - **AC7 – rollback keeps the current image.** A script rehearses the runbook on a stand-in image: tag, build, swap by rename, roll back. The rollback tag's image Id equals the Id captured before the build, and `/health` returns 200 after the rollback.
   - **AC8 – the state works in both directions.** The oracle loads a state file written by the merged Crier, including a `pid-` name and a rejected name. It then serves `/open`, `/events` and `/fleet` without error.
   - **AC9 – verification stays off.** With `TS_ALLOWED_SIGNERS` unset, `verify_event` returns None and fetches nothing.
4. **Done when:** AC1–AC9 pass, R1–R4 are closed, and Helio's GATEWAY has gone to Sensei. Deployment is not part of Done.

**Ratings table:**

| R | Finding | L | S | Gates | P | Closed by |
|---|---|---|---|---|---|---|
| 1 | The shared parser rejects names the deployed Crier indexes; repo HEAD drops them (at least 6 on the board [m]) | Low [i] | High | yes | P1 | rule C; AC2, AC3 |
| 2 | A rebuild picks up the newest rclone and python:3.12-slim | High [i] | Medium | yes | P1 | AC4 |
| 3 | A repo-root build context would ship `viewer/` (about 10,000 files [m]) and anything else in the shared tree | Medium [i] | Medium | yes | P2 | AC4 |
| 4 | Rebuilding `image: crier` moves the tag, and the container name collides, so the rollback is lost | Medium [i] | High | yes | P1 | AC7 and the runbook |
| 5 | After a state reset, 5 OFFER threads lose their subject | Low [i] | Medium | no | P3 | the deferred `host-` parser fix |
| 6 | A corrupt `state.json` wedges the Crier, in both versions [r: forge, TS-20260913-forge-013] | Unknown; check: forge's `test_state_persistence.py` §6 on a clean clone | Medium | no | P3 | deferred |
| 7 | Rename blindness, in both versions [r: sentinel1, TS-20260913-sentinel1-006] | Unknown; check: Agentic `520c73d` reproduction on a clean clone | Medium | no | P3 | deferred |
| 8 | Switching verification on would flag legacy signed events, and the image has no ssh-keygen | Low [i] | Medium | no | P3 | recorded |

R6–R8 are concerns that fall outside this job's criteria. They are deferred to V1.0 under Sensei's standing 0.x answer (house law, line 5).

## 4. Cutover and rollback sketch (the operator's hands, after QA; nothing now)

**What still holds from `~/crier-docker/DOCKER-CUTOVER.md`:** announce the window; the read-only rclone mount; verification off; the Crier runs in the foreground as process 1; port 8787; log rotation; and its step-6 checks (`/health` ok, and the watermark continues rather than resetting to 0).

**What changes:** the build source is a townsquare commit; there is no nohup Crier to kill; and there is no state seeding, because the bind mount is the same.

**Steps:**
1. Record the image Id, `docker inspect crier`, `docker exec crier rclone version` and a copy of `state.json` into `~/crier-archive/<date>/`.
2. `sudo docker tag crier crier:rollback-055fc54e`
3. On Venom, run `git archive <commit> crier registrar/app/__init__.py registrar/app/filename.py` and pipe it over ssh into `~/crier-build/<commit>/`.
4. Build only, under a new tag.
5. `sudo docker stop crier && sudo docker rename crier crier-055fc54e`, then bring up the new container.
6. Verify with step 6 of the old runbook, and compare `/open` for two hosts against the step-1 record.

**Rollback:** `sudo docker stop crier && sudo docker rename crier crier-<commit> && sudo docker rename crier-055fc54e crier && sudo docker start crier`, then check `/health` and the watermark. The state works in both directions (AC8); the step-1 copy is the fallback.

## 5. Work order

**Measure first (session only, read-only, before S1):**
- **MS1 – the parity fixture:**
  - `ssh batman@192.168.2.3 'cat ~/crier-data/state.json'`;
  - capture `/health`;
  - capture `/watermark` before and after the other captures (the two must match);
  - capture `/fleet`, `/events`, and `/events?host=h` and `/open?host=h` for every to/from value in the state, plus "all".
  - If reading the state file needs sudo, it becomes a request to the operator.
- **MS2 – a Docker host other than the NAS:** run `docker version` on Venom and in WSL2. If neither has Docker, AC4–AC7 move into the cutover runbook as pre-swap checks (build only, run on port 8786). Helio flags this at the GAME PLAN.

**Budget** (tracker design §3.7: worst case = the sum of each dispatch's maximum cost ÷ 0.61; a review costs $6, a Helio check $4, a build or test $4 [i: not calibrated]):

| Slice | Dispatches | Cost |
|---|---|---|
| S0 | jackie-chan $6, francis-ngannou $6, Helio GAME PLAN $4 | **$27** |
| S1 | ronda $4, Helio $4, bruce $4, Helio $4, jackie $6, francis $6, ronda QA $4, Helio $4 | **$59** |
| S2 | GATEWAY | **$10** |
| **Total** | | **$96** |

One fix loop would add $20, for **$116**.

**Every builder brief carries these rules:**
- `C:\Repo\townsquare` is a **shared working tree**, and Kano is committing doctrine drafts there.
  - `git add` explicit paths only.
  - Never `-A`, `commit -a`, stash, reset or a branch switch.
  - Check that the branch is `internal`, and stop if it is `main`, because the fixture holds live board names.
- Commit, never push.
- No proof, no bug: a defect needs a saved test that fails on a clean clone of a named commit; anything less is a concern and is not built for.
- Quote other agents only through `python C:\Repo\Agentic\tools\save_verbatim\save_verbatim.py`.
- Never touch the NAS.

```
WORK ORDER
- Tier: 0.x (no V1.0 declared for the Crier) [Working process, line 1]
- Work category: 1. Adds value to deployed code: Done-when proves the installed Crier does what it did, from one source, with the shared grammar (dojo-working-process.md §5)
- Document: session saves this note verbatim — C:\Repo\townsquare\docs\ip-man-crier-one-version-ruling-20261006.md — reviewed by jackie-chan (§1, §3), then francis-ngannou (§2, §4), serially, before any Implement line
- Criteria: this note §3, written before anything runs
- Ratings: this note §3 table; priority set by ip-man
- Coordinate: helio-gracie — GAME PLAN after S0, before any Implement line; CHECKPOINT at tests-first, implement and QA handoffs, and at review only if a finding would start a fix dispatch (proof check); final CHECKPOINT + GATEWAY before Sensei sees crew output
- Measure: session, MS1 and MS2, read-only, before S1
- Implement: ronda-rousey writes and commits AC1-AC9 tests first, failing; bruce-lee merges crier.py (rule C), imports the suites and oracle, and builds Dockerfile/compose/pins/README/DOCKER-CUTOVER.md to green; never self-tested
- Peer review: jackie-chan — rule C, parity allowed-difference list, state compatibility; then francis-ngannou — context filter, pins, rollback-by-rename runbook. gsp not dispatched: no hunk touches credentials, mounts, ports, network or live verification; Helio adds gsp if a diff does
- QA: ronda-rousey — clean clone of the implement commit: AC1-AC9, container ACs on the MS2 host
- Done when: §3 item 4; deployment stays with Sensei
- Watch for: shared tree (Kano); fixture on `internal` only; NAS untouched; no Docker host off the NAS; post nothing on forge-012; my ledger draft's AC3 wording ("the Crier's NAME_RE") now means filename.py — raise at that draft's S0
```

**Recusal note.** This is not a Tribunal referral. It touches my own NAS ledger draft only at M1, which is now answered, and at AC3's wording.

## 6. Decisions only Sensei can make

1. **Approve this job's worst-case budget: $96, or $116 if one fix loop is needed.** S0, the design review, can run now. The build waits for his yes, under his own budget rule. Recommend: yes.
2. **Not blocking: should forge's unfinished `/events` change stay parked?** That change (Agentic `7305c81`, thread `TS-20260913-forge-012`, still WORKING) would send every thread to every host. Its author found that it drops bulletins, and the NAS ledger work will change what the Crier reads anyway. Recommend: park it, and bring it back as its own job only if he wants it.

After QA, the cutover comes to him with the runbook. That is not a decision for today.

**Files I read for this ruling:**
- `C:\Repo\townsquare\docs\crier-version-comparison-20261006.md`
- `C:\Repo\townsquare\registrar\app\filename.py`
- `C:\Repo\townsquare\crier\test_crier.py`
- `C:\Repo\townsquare\poller\townsquare-poll.py`
- `C:\Repo\Wonderland\services\registry\registry\crier.py`
- `C:\Repo\townsquare\docs\town-registrar-design.md`
- `C:\Repo\townsquare\docs\town-registrar-ws3-plan.md`
- `C:\Repo\townsquare\docs\ip-man-nas-ledger-design-v1-20261006.md`
- `C:\Repo\townsquare\docs\ip-man-tracker-budget-roadmap-design-20260926.md`
- The scratch `crier-cmp\` files: `deployed.py`, `repo.py`, `theirs_7305c81.py`, `merged_try2.py`, `nas-pkg\`, `nas-tests\`
- Board threads read in full: `G:\My Drive\N3rd0m\TownSquare\Requests\TS-20260913-forge-012.001-…` and `TS-20260913-forge-013.000-…`