# ip-man delta 1 to the NAS ledger design v1: Google access from any host

Date: 2026-10-06. Applies to docs/ip-man-nas-ledger-design-v1-20261006.md (commit 568701a). Cause: the operator answered decision 2 with "No, I do not want this restriction" (copied by the orchestrating session from the chat, not tool-extracted). Filed as a separate document so the v1 text and its provenance stay unchanged; ip-man asked for it to be applied in place, and the orchestrating session did not do that.

ERRATUM BY THE ORCHESTRATING SESSION, same day, before any reader acts on this: ip-man was not told that the operator had already ruled out two routes this delta recommends. (1) "Move the OAuth client from Testing to In production" (its decision 1): the operator said that route is now a lengthy process on Google's side, so it is closed. (2) The rclone shared client (its option 3 and decision 2): the operator said "no shared client solution. We are taking a different approach", and confirmed the different approach is the NAS-hosted replacement. Those recommendations, the "Primary" status of a NAS rclone bridge that depends on them, and the decision list at the end are therefore SUPERSEDED by delta 1.1 (requested, not yet received). The host-agnostic bridge, the lease, the failover on a dead credential, and AC26 stand for review.

<!-- verbatim sha256=2e500f84af6f5394532908c1b08f8f7b5338233684e932b3a57d594522bfa1e2 source=C--Workspace/fa5f5b3d-d9ba-4d32-94ad-d0571415f8fc/subagents/agent-a5c3f3e30606d2f61.jsonl:284 message=msg_011Cfm6rKqZZAKrwsi3JG5VN -->
# Delta 1 to the NAS ledger design v1: Google access from any host

**Applies to:** `C:\Repo\townsquare\docs\ip-man-nas-ledger-design-v1-20261006.md` (commit 568701a).

**How to file it:** apply it in place, as the process template asks for one document of record. Add this line to the v1 header: "Delta 1 applied 2026-10-06: the operator answered decision 2, 'No, I do not want this restriction' (relayed by the session, not tool-extracted)." Sections not named below stay as they are.

**Tags and abbreviations:**
- Basis: [m] measured by me, [i] inferred, [a] assumed, [r: X] reported-by X, [est] established, [spec] speculative.
- Lease: a time-limited claim held in the ledger database that lets exactly one bridge act at a time.
- TTL (time to live): how long a lease lasts without renewal.
- fs backend: the bridge works through a Drive for Desktop folder such as `G:\`.
- rclone backend: the bridge works through an rclone remote with an OAuth token.

---

## Replace the design paragraph's Venom sentence with

> One small bridge component carries every Google-facing job: the mirror out (F6), the inbound import (F7) and the offsite backup (F9). It runs on any host that has Drive access, the NAS included. A lease in the ledger makes exactly one copy active at a time, and the others stand by. The ledger's core path (the Registrar, the Crier and the pollers) never holds or needs a Google credential, and it keeps working while the bridge is down.

## New §6a: the bridge, independent of host

**Packaging.**
- One Python package (`townsquare/bridge/`), standard library only, plus the rclone binary when the rclone backend is used. It runs two ways:
  - **(1) Container `town-bridge` on the NAS.** It loops every 300 s, restarts unless stopped, uses `network_mode: bridge`, and reaches the ledger at 192.168.2.3:8790. It mounts its own `secrets/rclone.conf` (mode 0600, read-only) and `/share/Backups/townsquare` (read-only).
  - **(2) A plain scheduled job on any other host.** On Venom that is Windows Task Scheduler with the fs backend on `G:\`. A Linux host can run either form.
- **Configuration** is one env file per host:
  - `BRIDGE_ID` (unique; the service rejects a duplicate);
  - `BRIDGE_BACKEND=fs|rclone`;
  - `BRIDGE_DRIVE_ROOT` (`G:\My Drive\N3rd0m\TownSquare` or `gdrive_bridge:N3rd0m/TownSquare`);
  - `BRIDGE_LEDGER_URL`;
  - `BRIDGE_JOBS=mirror,inbound,backup_out`;
  - `BRIDGE_LEASE_TTL=900`.
- The bridge keeps no local state. Its mirror cursor (the position in the ledger's change feed) is stored with the lease on the server, so a standby resumes where the last holder stopped.

**More than one bridge at a time.**
- **The lease.** `POST /v1/ops/lease {name: drive-bridge, holder, ttl_s, cursor}` is a compare-and-set in SQLite. Expiry is computed on the server's clock alone, so clock skew between hosts does not matter. The holder renews the lease every run; any other bridge only sends heartbeats and probes its own credential. This is added to S1.
- **Inbound is safe even with two active.** The server treats an object with the same path and sha256 as a no-op (§6), so a double import cannot happen.
- **The mirror is not safe with two active, and that is why the lease exists.** Drive allows two files with one name, and `rclone copyto` replaces a file that already has the name [m: publisher.py:199-205]. So every mirror and backup write checks first, the way the registry publisher's R3 guard does:
  - the same path with the same size and hash is skipped;
  - the same path with different content is flagged and never overwritten.
- **Dead credential.** Every run starts with a probe:
  - rclone backend: `rclone lsf` on the root, so `invalid_grant` shows up directly;
  - fs backend: the mount exists, can be listed and accepts writes.

  If the probe fails, the holder releases the lease at once and sends a heartbeat of `credential: dead (<error class>)`. Then the standby takes over within one TTL plus one interval, and the poller line names the host and the error (F10). Nothing is deleted. The ledger keeps accepting posts, the mirror catches up from the stored cursor, and the phone's posts wait in Drive until a healthy holder imports them.
- **Known limit of the fs backend.** It cannot see a Drive for Desktop upload that has stalled. When the other host has a working credential, it checks for this: it compares the watermark file the holder writes into a `N3rd0m/TownSquare-Bridge/` folder with the ledger's feed (AC12).

**Recommended hosts and credentials**
| Option | Credential | Expiry story | Role |
|---|---|---|---|
| NAS, rclone backend, its own remote `gdrive_bridge` | A token from Sensei's own OAuth client, with `drive` scope (the bridge has to read the phone's files and write the mirror) | Google applies the 7-day expiry only to clients in "Testing" status [est: developers.google.com/identity/protocols/oauth2]. That is today's failure: the Crier's token dies weekly and `gdrive_rw` has been dead since about 09-21 [r: session]. Moved to "In production", the token dies only if revoked or if the per-client token cap is hit [est, same page] | **Primary.** It is always on. It needs decision 1 below. If the client stays in Testing, this option fails every week, so I do not recommend it in that state |
| Venom, fs backend on `G:\` | The Drive for Desktop sign-in (Google's own client) | No 7-day rule [i: it has served ts-file.sh and the projector continuously; I found no re-sign-in on record]. It dies on sign-out or a stalled sync | **Standby.** It takes over automatically when the NAS bridge's credential dies |
| The rclone shared client (stopgap A) | Shared client | No weekly expiry; Google is retiring the client [r: stopgap ruling R2] | Not recommended |

**Power.** The NAS bridge's token has the same reach `gdrive_rw` has today: full Drive on the same account [r: stopgap ruling §1]. I accept that at 0.x, as that ruling did for `gdrive_rw`. gsp reviews it in S2.

## Restated items

- **G3:** No Google credential in the ledger's core path: the Registrar, the Crier and the pollers neither hold one nor need one. Only the bridge talks to Google, the ledger works with the bridge down, and the bridge's credential comes from a client that does not expire weekly (a preference, proven by AC25).
- **F11:** No weekly re-auth. The one Google credential on the NAS belongs to the bridge and does not expire weekly. When it dies, the health line says so and the standby takes over.
- **AC25 (F11):** At the end of the window:
  - under the Crier, Registrar and registry deploy directories and container mounts, `refresh_token` appears 0 times;
  - the only token on the NAS is in `town-bridge/secrets/rclone.conf`, mode 0600;
  - a bridge token minted at least 8 days earlier still lists the root;
  - `gdrive` is named as the exception if M10 shows `music_copy.sh` still uses it.
- **C7:** After the window, the Crier's Drive remote comes out of its mounts, and `collect.sh` and the verifier's Drive mode are retired. The bridge's credential stays.
- **Dropped:** the sentence "the NAS holds no Google login at all", in the design paragraph, §7 and G3.
- **§7, "Recommendation on Drive":** "written only through Venom's Drive for Desktop" becomes "written only by whichever bridge holds the lease".

## Changed criteria

- **AC11:** "Venom's offsite copy" becomes "the Drive offsite copy written by the lease holder". The off-NAS copy that Venom pulls over ssh stays as a separate job that does not need the lease.
- **AC12:** add two faults:
  - the holder's credential is dead: a named DEGRADED line within one poll, and the lease passes to the standby within TTL plus 300 s;
  - the mirror watermark in Drive lags more than 30 min (checked by the standby): DEGRADED "mirror not reaching Google".
- **AC20 and AC21:** "while Venom runs" becomes "while a bridge holds the lease". Both run once with each backend (fs against a scratch folder; rclone against a fake remote).
- **New AC26 (F6, F7):** two bridges, one per backend, run 20 cycles at the same time against a fake Drive. Then the holder is killed. Then the run is repeated with the lease switched off.
  - Pass: 0 duplicate Drive objects and 0 duplicate ledger imports; the standby holds the lease within TTL plus one interval, and the mirror resumes from the stored cursor with no gaps.
  - With the lease off, the duplicates must appear. That run proves the test can fail.
  - Test path: `bridge/tests/test_lease_concurrency.py`.

## The Crier this design assumes (§2, AC13, AC19, AC22)

The tree switch is configuration only for any Crier that keeps two properties:
- **P1:** `TS_REMOTE` is an rclone path, and it may be a local directory.
- **P2:** events are keyed by `ID or Path`.

Where each version stands:
- **Repo HEAD:** P1 and P2 hold [m: crier.py:110-117, 245].
- **Deployed `40c65fa`:** P1 and P2 are likely [i: `crier-version-comparison-20261006.md` §2 lists no change to the listing step; I did not read `40c65fa`]. M13 checks it: grep the deployed `~/crier-docker/crier.py` for `lsjson` and `get("ID") or`.

**What the merged-Crier ruling must carry:** keep P1 and P2, and add one test that polls a local-tree fixture. AC13, AC19 and AC22 then run against the merged Crier's image. S6 runs with the merged Crier, or with `40c65fa` if M13 passes.

## Risks, re-rated and added (§9)

| RK | Risk | L | S | Gates | P | Closed by |
|---|---|---|---|---|---|---|
| 3 (re-scoped from "Venom off") | No healthy bridge holder: both hosts down, or both credentials dead | Low [i: needs the NAS bridge and Venom out together; Venom recorded about 0.2 h stopped across 9 cycles in 30 days, r: session; sleep and hibernate not counted] | Medium | no | P3 | AC12; the posts wait in Drive |
| 8 (bridge period) | A dead Crier login goes unseen | Low if decision 1 holds [i]; Medium if it does not [i] | Medium | yes until decision 1 | P1 | decision 1, then its day-8 check |
| 9 | `G:\` shows duplicate names as new files | Unknown (M9); applies only while Venom holds the lease | Low | no | P3 | unchanged |
| 12 (new) | The NAS bridge's credential dies | Low per month in Production status [i]; High per week in Testing status [est] | Medium | gates only in Testing status | P1 | decision 1; failover (AC12) |
| 13 (new) | Two bridges active at once duplicate mirror objects | Low [i: server-side compare-and-set; one clock] | Low (the mirror only; the ledger and Crier are unaffected) | no | P3 | AC26 |

## §10 slices (only the changes)

- **S1:** adds the lease endpoint.
- **S2:** no longer waits on a decision. It is the bridge package with both backends, the lease client and the probes. Tests by ronda first, bruce-lee builds, gsp reviews (credential handling, inbound, the bridge's `drive` scope), QA by ronda. Worst case **$44**.
- **S3:** adds the `town-bridge` container: 128 MB memory, 0.5 CPU [a]. Worst case **$38**.
- **Total:** about **$261** worst case [i: tracker design §3.7 rates; not calibrated].
- **§5 table:** the "Containers" row becomes "one new container, `town-bridge`". The "Off-NAS and offsite" row reads "the lease holder writes the Drive offsite copy; Venom pulls an off-NAS copy over ssh".

```
WORK ORDER (updated by Delta 1)
- Tier: 0.x (no V1.0 declared for TownSquare, Registrar or Crier)
- Work category: 1. Adds value to deployed code; S5 alone would be 3 if split out
- Document: session applies Delta 1 in place to C:\Repo\townsquare\docs\ip-man-nas-ledger-design-v1-20261006.md, header noted — reviewed in S0 by jackie-chan, francis-ngannou, gsp (now incl. §6a bridge credential), kano, serial, before any Implement line
- Criteria: v1 §4 as amended (AC11, AC12, AC20, AC21, AC25 changed; AC26 added)
- Ratings: v1 §9 as amended (RK3, RK8 re-rated; RK12, RK13 added); priority set by ip-man
- Coordinate: helio-gracie — GAME PLAN after S0, before any Implement line; CHECKPOINT at every delivery handoff (default); final CHECKPOINT + GATEWAY before Sensei sees crew output and before the T0 go
- Measure (S0, session, read-only): M1-M12, plus M13 (deployed Crier keeps P1/P2)
- Implement: S1/S2/S3/S5 bruce-lee; S4 jackie-chan; tests first by ronda-rousey on each
- Peer review: S1 jackie-chan; S2 gsp; S3 francis-ngannou; S4 bruce-lee; S5 tony-jaa
- QA: ronda-rousey — each slice on a clean clone of the implement commit; AC11 drill, AC24 rehearsal and AC26 live
- Live: session executes C1-C7 after Sensei's written go; francis-ngannou verifies post-hoc from artifacts
- Done when: Increment A then B Done-when; decisions 1-3 answered; doctrine adoption before T0
- Watch for: merged-Crier ruling must keep P1/P2; never a second active mirror writer; rclone copyto overwrites, so check-before-write; corpus never in an agent context; NAS DNS trap; commit-vs-push boundary in every brief
```

## 11a. Decisions only Sensei can make (blockers first)

Decision 2 (Venom-only) is answered: no restriction. The bridge now runs on any host.

1. **Move your own Google OAuth client (client id starting 416116040158) from "Testing" to "In production" in Google Cloud Console, then re-authorize the Crier once with `crier-reauth.py`.**
   - Google applies the 7-day token expiry only to clients in Testing status [est]. So this one change ends the weekly re-auth now, and it makes the NAS bridge's login durable later.
   - The proof is a day-8 check. The consent screen may show an "unverified app" warning [spec].
   - The Crier's token runs out around 10-13 [i].
   - Recommend: yes.
2. **Stand down the shared-client stopgap A.**
   - Weekly re-auth stays as the fallback, used only if item 1 fails its day-8 check.
   - Accept that a dead Crier login could leave the board stale until cutover (RK8, Low if item 1 holds).
   - Recommend: yes.
3. **Start the S0 review round, and approve the S1-S6 scope at about $261 worst case.**
   - The cutover and the doctrine adoption come back to you later.
   - Recommend: yes.
