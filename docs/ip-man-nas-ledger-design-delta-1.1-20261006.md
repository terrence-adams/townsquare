# ip-man delta 1.1: corrects delta 1 of the NAS ledger design

Date: 2026-10-06. Corrects docs/ip-man-nas-ledger-design-delta-1-20261006.md (sha256 2e500f84...), which amends docs/ip-man-nas-ledger-design-v1-20261006.md. Requested by the orchestrating session after delta 1 recommended two routes the operator had closed. ip-man asked for this to be applied in place; it is filed as its own document so the earlier files and their provenance stay unchanged. Read in this order: v1, delta 1 (with its erratum), this document. Where they disagree, this document governs. Status: DRAFT, not reviewed. The S0 review round is on hold until the operator has seen Kano's document proposal.

<!-- verbatim sha256=db04356bd951bcfa711e049d01a29b89d1a8b1a134e5234ee28f9318a7fbcfbb source=C--Workspace/fa5f5b3d-d9ba-4d32-94ad-d0571415f8fc/subagents/agent-a5c3f3e30606d2f61.jsonl:288 message=msg_011Cfm77XTEikcCcWs3nc6jX -->
# Delta 1.1: corrects Delta 1 of the NAS ledger design

**Applies to:** `docs/ip-man-nas-ledger-design-delta-1-20261006.md` (sha256 2e500f84…), which amends `ip-man-nas-ledger-design-v1-20261006.md`. File it the same way, in place, with a header note.

**What still stands for review:** the bridge that runs on any host, the lease, failover when a credential dies, and AC26.

**What is withdrawn:**
- Delta 1's recommendation to move the OAuth client to "In production".
- Every trace of the rclone shared client, both as an option and as stopgap A.

**Tags and abbreviations:**
- Basis: [m] measured by me, [i] inferred, [a] assumed, [r: X] reported-by X, [est] established, [spec] speculative.
- fs backend: the bridge works through a Drive for desktop folder.
- Testing status: a Google OAuth client still unpublished; its refresh tokens expire after 7 days [est: developers.google.com/identity/protocols/oauth2].

## 1. Routes Sensei has closed (removed from the design, not only from the recommendation)

All four are [r: operator, relayed by the session, 2026-10-06]:
- **Production publishing of the own client:** Google's requirements changed and it is now a lengthy process.
- **The rclone shared client:** "no shared client solution. We are taking a different approach."
- **A service account:** "tried before, did not work as expected due to policy changes from Google".
- **A Workspace "Internal" app:** he does not own advocationpr.com.

**What to delete:**
- In Delta 1 §6a, the shared-client row of the hosts table.
- Every mention of "In production".
- In v1 §8, "Exit triggers: go back to A…".
- My stopgap ruling `ip-man-nas-drive-shared-client-stopgap-20261006.md`, with its work order and "Job 2", is **withdrawn**. The session adds that word to its header. It is my ruling, so this is withdrawal by its owner, not a Tribunal matter.

## 2. Bridge hosts and credentials, worked out again from what remains

Two credential kinds remain:
- **The Drive for desktop sign-in**, which is Google's own client. It has no 7-day rule [i: it has served `G:\` continuously, r: session]. It runs on Windows and macOS only, so it cannot run on the NAS [a].
- **An rclone token from the own client in Testing status.** It dies 7 days after each re-authorization [est].

| Role | Host and credential | What it costs Sensei |
|---|---|---|
| **Primary** | Venom, fs backend, Drive for desktop sign-in. Any Windows or macOS host signed in to the account that owns N3rd0m qualifies the same way | Nothing routine. It fails on sign-out or a stalled sync, and the fs probe sees only a missing or unwritable folder (see RK2) |
| **Warm standby** (if one exists) | A second Drive for desktop host, failing over through the lease | Nothing routine. M14 below checks whether such a host exists |
| **Dormant standby** | NAS container `town-bridge`, rclone backend, own client in Testing status. It ships in the compose file but is not started (`restart: "no"`) | One re-authorization buys 7 days of cover. Run continuously, it would mean a click every week, the same burden that started this design. So Sensei starts it only when he wants the NAS to cover, for example before Venom will be away for days |

**Whether to ship the NAS standby: yes, dormant.** It lives in the same package, and its rclone backend is already in S2 (AC20 and AC21 test both backends), so it costs no extra build [i]. It honours "no restriction" on hosts, and it costs nothing until he starts it.

**Behaviour when a credential is dead.**
- The holder releases the lease, as Delta 1 already says.
- A standby that is dormant, or that reports a dead credential, shows as a plain information line, not DEGRADED.
- The poller line says DEGRADED only when **no bridge holds the lease with a live credential**. That keeps a dormant NAS standby from crying wolf every week.

## 3. Restated items (these replace Delta 1's versions)

- **G3:** The ledger's core path (the Registrar, the Crier and the pollers) holds no Google credential and keeps working with the bridge down. Google access is confined to the bridge. Among the routes still open, the only credential with no weekly expiry is a Drive for desktop sign-in on a Windows or macOS host [i].
- **F11:** No weekly re-auth after cutover, **for as long as a Drive for desktop host holds the bridge lease.** Starting the NAS bridge costs one re-auth for every 7 days it runs.
- **What a bridge host that is off costs: delay only, never data.**
  - The ledger keeps accepting LAN posts.
  - The mirror catches up from its stored cursor.
  - The phone's posts wait in Drive until a holder imports them.
  - Nothing is lost.
- **AC25:** At the end of the window:
  - `refresh_token` appears 0 times under the Crier, Registrar and registry deploy directories and container mounts;
  - `town-bridge` is not running unless Sensei started it, and if it is running, its token sits in `town-bridge/secrets/rclone.conf` with mode 0600 and its age shows in `/health`;
  - a Drive for desktop bridge holds the lease with a live credential;
  - the `gdrive` exception for `music_copy.sh` applies as before.
- **C7:** The Crier's Drive remote comes out of its mounts, and `collect.sh` and the verifier's Drive mode are retired. Venom's sign-in stays. The NAS holds no Google token unless the dormant bridge is started.
- **AC12, second fault (mirror watermark lag):** it runs only when a second bridge with a live credential exists. Otherwise it is recorded as not exercisable.
- **New measurements:**
  - **M14:** which fleet hosts run Drive for desktop signed in to the account that owns N3rd0m.
  - **M15:** whether Drive for desktop exposes sync or upload errors locally where a probe could read them [spec].

## 4. Bridge period (replaces v1 §8)

- The weekly one-click Crier re-auth is in use; Sensei ran it himself at 2026-10-06T13:52Z [r: session].
- The session runs `crier-reauth.py --check` at the start of each session; the script already warns at day 6 [m: crier-reauth.py:51].
- `gdrive_rw` stays dead. Its outbox drains into the ledger at T0 (the cutover moment).

## 5. Risks re-rated (§9; priority set by me)

| RK | Risk | L | S | Gates | P |
|---|---|---|---|---|---|
| 2 (one failure mode added) | The fs backend cannot see a stalled Drive for desktop upload, and when only Venom is live, no second credential can cross-check it | Medium [i] | Medium | yes | P1. Closed by AC12 and M15, or by acceptance at the final GATEWAY |
| 3 | No bridge holds a live credential, so phone posts and the mirror wait | Unknown. Venom recorded about 0.2 h stopped across 9 cycles in 30 days [r: session], but sleep and hibernation were not counted. Check: Venom's sleep and hibernate hours over 30 days (M8b). It gates if the result is 5% or more | Medium (delay only) | not unless M8b ≥ 5% | P2 |
| 8 | During the bridge period, a dead Crier login goes unseen | Medium [i: weekly manual re-auth; 3 of 3 earlier deaths went unseen for a week or more, r: venom TS-20260921-venom-002] | Medium | yes | P2. It goes to Sensei at the final GATEWAY if still open. Mitigated by the session's `--check` |
| 12 | The NAS bridge's token dies | High per week of use [est] | Low (a dormant standby; the primary still holds) | no | P3 |
| 15 (new) | The `townsquare-registry-writer` service account still has edit rights on the TownSquare folder, and where its key lives is unknown [r: session]. After cutover, anything that writes into the folder is imported by the inbound bridge | Unknown. Check: the key list for that account in the Google Cloud console (created and last-used dates) | Medium | not until measured | P2 |

## 6. Changes to §10 and the work order

- §10 is unchanged; S2 is still $44, and the total is still about $261 [i].
- In the WORK ORDER, the Document and Coordinate lines get one line added: "S0 ON HOLD until Sensei has seen Kano's document proposal [r: session]."
- The S2 review line becomes: "gsp: credential handling, inbound, and the dormant NAS bridge's `drive` scope."
- In Measure, add M8b, M14 and M15.
- Done-when becomes: "Increment A then B Done-when; S0 released by Sensei; doctrine adopted before T0."

## Decisions only Sensei can make

Nothing blocks today: S0 stays held at his word. When it is relevant:
1. **When you release S0, after Kano's proposal:** approve the S1–S6 scope at about $261 worst case. The cutover itself comes back to you separately. Recommend: yes.
2. **Not blocking:** remove the `townsquare-registry-writer` service account's edit access to the TownSquare folder, or tell us it is still needed. It is a writer outside the LAN, and after cutover the inbound bridge would import whatever it writes (RK15). Only you can see its keys or remove the grant. Recommend: remove it once its key list is checked.
