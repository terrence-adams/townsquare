# ip-man ruling: switch the NAS Drive logins to rclone's shared client (stopgap A)

Date: 2026-10-06. Requested by the orchestrating session after the Crier went stale (invalid_grant, last good poll 2026-09-29) and the registry publisher login `gdrive_rw` was found dead the same day. **WITHDRAWN 2026-10-06 by its author (ip-man, delta 1.1 section 1), after the operator rejected the shared client: "no shared client solution. We are taking a different approach." Kept for the record only; do not act on it. Its finding that the registry login `gdrive_rw` is dead and shares the Crier's client stands.** Status: RULING, withdrawn. Its decisions 1 and 2 are void. Written before the operator said Google Drive is a proof of concept to be replaced by a NAS-hosted dockerized framework, so the bridge lifetime it assumes is not yet bounded.

<!-- verbatim sha256=581f148209fb3cc4c70cf60c7acdb7ca174d9090ca2497992f99c7bb2021cb7c source=C--Workspace/fa5f5b3d-d9ba-4d32-94ad-d0571415f8fc/subagents/agent-ae2ead528be14a900.jsonl:170 message=msg_011Cfm4FcyF4NBhXodk5ZN2w -->
RULING: Mr. Ip on stopgap A (rclone's shared client), now for BOTH NAS Drive logins. Revised after your correction.

**Short answer.** I approve A for both remotes, as two separate remotes with separate scopes. Both swaps go through one script change, done in order: the Crier first, then `gdrive_rw` the same day once the Crier's checks pass. Nothing is dispatched until Sensei says yes (decision 1). The Crier swap also waits for measurements M1, M2 and M4 below. A swaps which OAuth client issues each token. It does not change the scope, the Google account or the files either token can touch. Today both remotes already hang off one Testing-mode client (measured by you: both client_ids start 416116040158), so A adds no coupling. What it does is trade a weekly failure that is certain for a rare one that is announced 90 days ahead.

**0. Consumers (what the repos establish)**
- Crier `gdrive` (`/home/batman/.config/rclone/rclone.conf`):
  1. The `crier` container: `lsjson` every 300 s, plus `cat` (read in source: `C:\Repo\townsquare\crier\crier.py` lines 110-117, 180-185).
  2. `crier-reauth.py` (read in source).
  3. The Registrar dry-run collector `C:\Workspace\townsquare-registrar-dryrun\collector\collect.sh` lines 30-32. It runs on the NAS host, only when the operator approves a run, and re-runs are planned (`town-registrar-ws1-ws2-plan.md` line 120).
  4. `~/music_copy.sh` on the NAS: "the same gdrive: remote" (reported-by tony-jaa, collect.sh lines 64-65). The remote was first made for the 329 GB music pull (reported-by auto-memory project-n3rd0m).
  5. The Registrar verifier job: designed, not deployed (`registrar/OPERATIONS.md` line 111).
- `gdrive_rw` (`/app/secrets/rclone.conf`): the `agent-registry` publisher only (read in source: Wonderland `publisher.py` lines 29-37).
- **Please measure:**
  - M1: crontabs for batman, root and `/etc/crontab`, plus ADM's scheduler: anything that calls rclone or music_copy.
  - M2: is music_copy.sh scheduled or one-shot, and which remote does it use?
  - M3: `listremotes` on both config files, names only.
  - M4: mounts and env of kollective, night-shift-auditors x2, OpenWebUI, Transmission and OllamaCCC.
  - M5: rclone version on Venom, on the NAS host, and inside both containers.
  - M6: how many files are unpublished in the registry outbox.
  - M7: anything on the host that reads the registry config file.
- If M1, M2 or M4 turns up a scheduled heavy user of `gdrive`, stop and bring it back. It would share the per-user quota on the shared client (inferred), and I would likely give the Crier a remote of its own.

**1. Is A sound? (L = likelihood, S = severity)**
- R1. The Crier's new token could come back broader than read-only, merged with `gdrive_rw`'s full-Drive grant on the same client. L Low (inferred), S High (breaks D26, the rule that the Crier stays read-only). **Gated.** Closed by checking the token's actual scope with Google at install and again at day 8 (PR2, PR8). The consent-page check alone does not prove the scope.
- R2. Retirement of the shared client kills both remotes at once. L Low per week (reported-by the rclone maintainer on 2026-09-19: the notice has not started). S Medium. This is an exit trigger, not a blocker.
- R3. Shared-quota throttling causes failed Crier polls. L Unknown; the check is rate-limit errors in `docker logs crier` from the swap to day 8. S Medium (inferred).
- R4. Today's script leaves a failed swap in place (read in source: `crier-reauth.py` lines 295-310 have no restore). L Low, S Medium. The design adds a restore.
- R5. On the no-refresh-token path, the script tells you to revoke the old grant (lines 266-268). In shared mode that would revoke every rclone grant on the account, so both remotes would die. L Low, S Medium. Reworded in the build at no extra cost.
- R6. Dead logins go unnoticed: 3 of 3 deaths ran a week or more unseen (reported-by venom, TS-20260921-venom-002.000, and by you today). L High, S Medium. **Gated by the gate rule**, and A does not fix it. It is closed by Job 2 (a watchdog) or by Sensei's written acceptance.
- R7. Backups holding the old secret pile up on the NAS. L High, S Low. Recorded only.

A shared-client token with full `drive` scope for `gdrive_rw` is acceptable at 0.x. It has the same power as today's token, on the same account; only the revocation handle changes. Narrowing that scope is a separate idea (speculative), on the backlog as P3.

**2. Ranking the routes**
1. **A.** The smallest change, reversible for each remote, and it covers both.
2. **C (weekly re-auth).** The fallback for A. It now means two clicks a week, and the registry fails silently.
3. **D (Cloud Run relay).** Defer until the retirement notice starts. Its viability depends on why the earlier service-account attempt failed, which is not recorded. The service account is also a writer on the folder, so the Crier's read-only status would rest on code, not on the grant.
4. **B (Venom copies the folder to the NAS).** Rejected. A filesystem copy cannot hold two same-named files the way Drive can, so the Crier's collision detection (crier.py lines 126-130, 142-169) loses what it exists to catch (inferred). That breaks RM1, the rule that a read model agrees with Drive. B also does nothing for the registry's writes.

**3. Changes, rollback, exit, proof**
- Script changes (`C:\Repo\townsquare\tools\crier-reauth.py`):
  - A `--shared-client` flag. The authorize request carries only the scope, and the consent client_id must be non-empty and not 416116040158.
  - A container-config mode, so config dump, update, backup, restore and verify run through `docker exec <container>`. The registry config is root-owned (reported-by gsp's 2026-09-21 check in TS-20260921-venom-003), so batman cannot touch it directly.
  - A Google tokeninfo check before any NAS write: scope exactly equal to the remote's own scope. The token travels in the request body, never printed.
  - One `config update <remote> client_id "" client_secret "" token "$T"` call.
  - An automatic restore of the backup, then a re-check, if anything fails.
  - The re-auth marker records the client mode, and `--check` stops counting down 7 days in shared mode.
  - The revoke advice is reworded (R5).
- Your open question (does `client_id ""` delete the key or store an empty value?) is untested. It matters less than it seems: rclone's documentation (established) says a blank client_id means the shared client. PR4 measures what actually happens.
- **Rollback, per remote:** `cp -p` the `.bak-<stamp>` file back, then re-run the listing. The Crier's restored token stays valid until about 10-13 12:57Z (inferred), so swap before then and rollback costs nothing. `gdrive_rw` restores to a token that is already dead, so its rollback is the restore plus an own-client click.
- **Exit triggers:**
  - E1: either remote fails with invalid_grant or invalid_client → roll that one back.
  - E2: the 90-day notice starts (GitHub issue #9580 or forum thread 54005). tony-jaa owns reading it; Job 2 flags it. Both remotes then move together.
  - E3: the Crier's /health is not ok for more than an hour because of rate limits → roll back the Crier only.
  - E4: PR7 fails → A's premise is false; roll both back and C stands.
- **Proof:** PR1-PR6 on swap day. PR7 and PR8 at swap + 8 days. The "fleet precedent" proof no longer exists.
- **Docs:** fix the Wonderland README lines 58-61 now. The comments in publisher.py lines 34-37 and compose lines 24-27 wait for the next change that redeploys those files, because deployed files are SHA-pinned (reported-by gsp review line 530). P3.
- **Interim:** no own-client re-auth of `gdrive_rw` now. Publishes queue in the outbox and retry (reported-by Wonderland README lines 45-49), so the claude-app registration can proceed.

**Criteria** (save in the design note, one document of record)
1. Declared use: the Crier (read-only) and the registry publisher (write) on the home LAN; Drive stays the source of truth. Out of scope: crier.py and publisher logic, containers, routes B and D.
2. Ratings: likelihood per re-auth run, or per week of operation. High: the Crier with any scope other than drive.readonly, or either remote with a scope other than its own; a broken config left with no restore attempted; plus the permission-gate floor (the consent click is his).
3. Pass rules (PR):
   - PR1: shared mode mints from the built-in client; checked by a test plus saved live `--dry-run` output.
   - PR2: a token with a planted wrong or merged scope is refused before any NAS write; test.
   - PR3: a failed check triggers the restore and a re-verify; test.
   - PR4: a scratch-config script on rclone v1.75.1 shows `client_id ""` takes effect; raw output saved.
   - PR5: own-client mode is unchanged; test.
   - PR6: on each live swap, the in-container listing works, the tokeninfo scope is exact, and the Crier's /health is ok within 6 minutes.
   - PR7: at swap + 8 days, with the marker unchanged, the Crier's /health is ok and the `gdrive_rw` listing works.
   - PR8: at swap + 8 days, the Crier's live token is exactly drive.readonly.
   - J1 (judgment clause): gsp rules on credential handling.
4. Done when: PR1-PR8 pass, and R1 and R6 are closed or accepted.

```
WORK ORDER
- Tier: 0.x (no V1.0 declared for Crier or registry)
- Work category: 3. Fixes a known issue (TS-20260921-venom-002)
- Document: session saves this ruling verbatim (save_verbatim.py) to C:\Repo\townsquare\docs\ip-man-nas-drive-shared-client-stopgap-20261006.md, reviewed by tony-jaa (rclone version parity, shared-client issuance on 1.75.x) before any Implement line
- Criteria: same file, Criteria section
- Ratings: same file, R1-R7; priority set by ip-man: R1 P1, R4 P1, R5 P2, R6 P2, R2/R3/R7 P3
- Coordinate: helio-gracie, GAME PLAN after tony-jaa's review; CHECKPOINT at every delivery handoff and after each live swap; final CHECKPOINT + GATEWAY at swap + 8 days
- Tests first: ronda-rousey, PR1-PR5 offline with a fake NAS runner, committed failing
- Implement: bruce-lee, script changes + Wonderland README fix, built to green
- Peer review: gsp, the credential-handling hunks only (stdin token path, tokeninfo call, container backup/restore keeping root 600, revoke wording)
- QA: ronda-rousey, suite on a clean clone of the implement commit; live --dry-run on both remotes
- Live: session runs the swaps, Crier then gdrive_rw; the operator clicks consent (signed in as the gmail account that owns N3rd0m)
- Job 2 (separate, after decision 2): francis-ngannou, daily read-only check of both logins plus an alert, and a flag on #9580 changes
- Done when: PR1-PR8 pass; R1 and R6 closed or accepted
- Watch for: rclone version mismatch (M5); consent given from the advocationpr account; nobody revokes "rclone" in Google account permissions
```

**Decisions only Sensei can make (blockers first)**
1. **Approve A for both NAS Drive logins?** This blocks the build and both swaps. Each login keeps its own scope (read-only for the Crier, full Drive for the registry); only the client that issues the token changes, and each one rolls back with a single file restore. It needs two consent clicks from you on swap day. Recommend: yes, ideally swapped before 10-12.
2. **Add a daily check that alerts you when either Drive login dies (Job 2), or accept the risk in writing?** It is gated: all three past deaths ran a week or more before anyone noticed, and the registry fails silently by design. Recommend: yes, add the check.