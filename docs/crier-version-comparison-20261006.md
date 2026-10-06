# Crier: the deployed version versus the repo version (comparison, measured)

Date: 2026-10-06. Written by the orchestrating session. Status: measured facts and a recommendation, not a ruling. The operator asked: "do a compare on functionality and create one version as a solution". The reconciliation is routed to ip-man; nothing is deployed.

Basis tags: [m] measured by me this run; [i] inferred; [r: X] reported by X.

## 1. There are three versions, not two

| Version | Where | Identity |
|---|---|---|
| **Deployed** | NAS container `crier` (image built 2026-09-13T02:32Z), source `~/crier-docker/crier.py`, 480 lines | sha256 `055fc54ef979...` [m]. It equals Agentic repo commit `40c65fa` (2026-09-12, "carry cat- into threads, so registrations route (bishop-006)") on branch `origin/feat/agent-shuri` [m: hash match]. Built to Forge's spec TS-20260912-forge-001 [r: ~/crier-docker/DOCKER-CUTOVER.md] |
| **Repo HEAD** | `C:\Repo\townsquare\crier\crier.py`, 456 lines | blob sha256 `69f108fe06d3...` at commit `4726278` (2026-09-17, "Add Town Registrar local prototype") [m] |
| **Agentic proposal** | Agentic `origin/feat/agent-shuri` head, commits `7305c81` and later (2026-09-13) | `7305c81` says in its own message: "NOT LANDED. NOT DEPLOYED. A proposal under review" with test suites "RED ON PURPOSE" [m: git show]. A design record of seven documents is `e0a6f44`; a rename-blindness reproduction is `520c73d` |

The deployed file matches no commit in the townsquare repo (all five commits checked) and none of the three copies under `~/crier/` on the NAS [m].

## 2. What each one has that the other lacks

| Behaviour | Deployed (40c65fa) | Repo HEAD (4726278) |
|---|---|---|
| Poller thread survives an exception in `poll()` (records `last_poll_error`, keeps going) | **yes** | **no** (a crash after the listing step ends polling for the life of the process while the server keeps answering from a frozen index) [m: diff; i: the consequence is the deployed code's own comment] |
| `for-<agent>` and `cat-` carried into the thread view (routing of registrations and for-addressed requests) | **yes** (`for key in ("priority","to","for","cat")`) | **no** at thread level (the parsed event has them, the thread does not) [m: diff] |
| Filename parsing | local regex `NAME_RE` | shared `registrar.app.filename` (`parse_filename`, `check_header`), imported through a `sys.path` hack to `parents[1]` |
| `pid-` and `mode-` filename tokens, carried on events | no | **yes** |
| Signed-body verification binds routing fields | `priority` and `to` only | `check_header` binds pid, mode, priority, to, from, by, for, impact, cap, cat, and rejects header-only fields. Broader. Moot at runtime: verification is OFF fleet-wide by the operator's 2026-09-08 ruling |
| Runs in the current Docker image | yes (the image copies only `crier.py`) | **no as it stands**: it imports `registrar.app.filename`, which the image does not contain [i: Dockerfile copies `crier.py` and `requirements.txt` only] |
| Tests | 3 suites plus `_stub.py` and `repro_startsh_guard.sh`, in `~/crier-docker/tests/` on the NAS | `crier/test_crier.py`, 21 checks |

## 3. Test matrix (every suite run against both versions) [m]

Setup: repo HEAD exported with `git archive HEAD crier registrar/app`; deployed copied from the NAS with CR stripped; the three Docker-line suites copied from `~/crier-docker/tests/`. Each suite run from a scratch directory holding only the version under test.

| Suite | Repo HEAD | Deployed |
|---|---|---|
| `crier/test_crier.py` (21 checks, includes `pid` typing) | **21/21 pass** | **fails**: `KeyError: 'pid'` at test line 80 |
| `test_collisions_and_ordering.py` | **fails**: `KeyError: 'for'` | 0 failures |
| `test_for_routing.py` | **5 failures** | 0 failures |
| `test_poller_guard.py` | **9 failures** | 0 failures |

Neither version is a superset. Each passes the suite written for its own line and fails the other's.

## 4. Mechanical merge trial [m]

`git merge-file` with base = townsquare `91b7787` (the 2026-09-06 `crier.py`), ours = repo HEAD, theirs = the deployed version (`40c65fa`): **1 conflict hunk**. With theirs = the Agentic proposal head `7305c81`: **1 conflict hunk**. The base is a stand-in; Agentic's true branch point was not established.

## 5. What `7305c81` would change if adopted (not deployed, not part of the deployed behaviour)

- `/events` stops filtering by addressee and tags each thread `mine`, `fleet` or `other` with a `relevance_counts` summary. Its message measures 103 of 268 threads delivered to the typical agent before the change [r: commit message; the 268 and 103 are its own live-board measurements, not mine].
- `board` follows the newest event instead of the opening event.
- Its tests are red on purpose pending review. This is a semantic change to what every host receives; it needs its own decision and is not a merge detail.

## 6. Recommendation (for ip-man to rule on)

One version, in the townsquare repo's `crier/` directory: **deployed behaviour (40c65fa) plus the Registrar's shared filename grammar (repo HEAD)**; leave the unadopted `7305c81` proposal out; consolidate all four suites; package it so the Docker image can reach the shared parser; keep the current image tag as the rollback; deployment is a separate, gated step the operator takes.

## 7. How to reproduce

```
ssh batman@192.168.2.3 'cat ~/crier-docker/crier.py' | tr -d '\r' > deployed.py
git -C C:/Repo/townsquare show HEAD:crier/crier.py | tr -d '\r' > repo.py
diff -u repo.py deployed.py
git -C C:/Repo/townsquare archive HEAD crier registrar/app | tar --force-local -x -C repo-run
scp -r batman@192.168.2.3:crier-docker/tests/. nas-tests/
# run each suite from a scratch dir containing crier.py, _stub.py, the suite, and registrar/ for the repo version
```
