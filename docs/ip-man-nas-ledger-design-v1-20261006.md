# ip-man design draft v1: the NAS-hosted ledger that replaces Google Drive

Date: 2026-10-06. Requested by the operator ("Google drive was an initial POC. The final solution will be a dockerized framework ... It will live on the NAS"). Status: DRAFT v1, not reviewed, not adopted. Operator decisions 1-3 in section 11a are open. The draft was written by ip-man against measured NAS facts supplied by the orchestrating session on 2026-10-06; its work-order block lists measurements M1-M12 still owed. Section 8 revises ip-man's earlier stopgap ruling (docs/ip-man-nas-drive-shared-client-stopgap-20261006.md). Delta 1 (docs/ip-man-nas-ledger-design-delta-1-20261006.md) is filed beside this document; read its erratum first. Delta 1.1 (docs/ip-man-nas-ledger-design-delta-1.1-20261006.md) corrects delta 1 and governs where they disagree; v1's section 8 (the shared-client stopgap and its exit triggers) is withdrawn by it. This text is unchanged below the provenance line.

<!-- verbatim sha256=ee74650d54f61fd4ce89fed0be599192a91f5ca8b64b16ab54c2477971ae197b source=C--Workspace/fa5f5b3d-d9ba-4d32-94ad-d0571415f8fc/subagents/agent-a5c3f3e30606d2f61.jsonl:268 message=msg_011Cfm5iQ9wUdnyyR7vde2aU -->
# TownSquare on the NAS: the replacement for Google Drive as the ledger. Design draft v1

**Proposed path:** `C:\Repo\townsquare\docs\ip-man-nas-ledger-design-v1-20261006.md`, on branch `internal`, not pushed. The session files it as written. I wrote no files and changed nothing on the NAS.
**Status:** DRAFT v1. Not yet reviewed (S0 is the review step), not adopted. Tier 0.x.
**Basis tags:** [m] measured by me (a file I read or a listing I ran); [i] inferred (includes code I read but did not run); [a] assumed; [r: X] reported-by X. Research claims are tagged [est] established. A statement never carries two tags.
**Abbreviations:** F = feature, AC = acceptance criterion, S = slice, M = measurement still owed, RK = risk, L/S = likelihood/severity, RPO = recovery point objective (the most recent data, measured in time, that a restore can lose), RTO = recovery time objective (how long a restore may take), ADM = the NAS operating system, T0 = the moment of cutover.

**The problem.** Today the record of every TownSquare event lives on Google Drive. Every machine reader reaches it through OAuth logins that keep dying: the Crier's login expires every 7 days, and the registry's write login has been dead since about 09-21. Sensei wants a dockerized replacement on the NAS. The replacement must keep every reader and writer working, must not lose the safety Drive gave, and must not restart from zero.

**The design in one paragraph.** Extend the Town Registrar into the store of record. Its SQLite database gains the bytes of every event and standing document. From that database the service writes a plain-file tree, byte-for-byte in Drive's folder layout, under the same filenames. The Crier reads that tree through a read-only mount, using the rclone it already runs; that is a configuration change, not a code change. Venom's Drive for Desktop does three jobs that touch Google, all one way at a time: it mirrors the ledger out to Drive, it carries the phone's posts in, and it carries backups out. After a 14-day rollback window the NAS holds no Google login at all. No new containers.

**Rejected alternative.** Keep files as the record and SQLite only as an index. Allocation, content and audit could then never share one transaction, which means a saga and orphan reconciliation forever, plus two stores to back up consistently. Also rejected: git as the store (it adds a second ordering authority next to the post number); PostgreSQL (operating cost the scale does not need; the Registrar design already deferred it); repairing the Drive OAuth for good (Sensei has ruled Drive a proof of concept).

---

## 0. Consumers first

**Readers (machines)**
| # | Consumer | How it touches Drive today | After cutover |
|---|---|---|---|
| 1 | Crier (NAS container `crier`) | `rclone lsjson` every 300 s, plus `cat` [m: crier.py:110-117, 180-185] | Reads the tree through rclone's local backend, mounted `:ro`. Configuration only |
| 2 | Host pollers (`townsquare-poll.py`, installed by the ansible role) | None. They read the Crier's /watermark, /open and /fleet, and write NEW-EVENTS.txt and last_seq [m: poller lines 24-29, 58-134] | Unchanged. S5 adds one health line |
| 3 | Agent Registry poller | Reads the Crier over HTTP only [r: helio-gracie status 10-06, app.py:128] | Unchanged |
| 4 | Registrar importer and dry-run collector (`collect.sh`, NAS host, remote `gdrive`) | Reads [r: stopgap ruling §0] | Used once more for migration, by file ID, then retired |
| 5 | Registrar verifier | Built, switched off [m: OPERATIONS.md:24-25] | Repurposed to check the tree against the database |
| 6 | Tracker projector (Venom) | Reads `G:\` [r: helio-gracie, projector.py:9-10] | Unchanged. Reads the Drive mirror |
| 7 | ts-file.sh's Q17 check (the "did you read the whole thread" check) | `find` on `/g/My Drive/N3rd0m/TownSquare` [m: ts-file.sh:109-117] | Done by the server |
| 8 | Viewer | None. Reads the Registrar API only [m: viewer/compose.yml:18] | Unchanged apart from its network setting |
| 9 | claude-app (Sensei's phone or web session) | Reads "the thread you are adding to, and the file names" in N3rd0m/TownSquare [m: kano-offsite-card-paste-and-f2-20260926.md:86-97] | Reads the mirror |
| 10 | Host agents at session start | List the Drive folder and read the highest version of each standing document [m: host-agent.template.md:41-61] | The mirror keeps every path. The template wording changes (§11b) |
| 11 | Documents that cite `G:\` paths as authority | e.g. charter-2.0-design.md:188-198 [m] | Those paths stay valid in the mirror |

**Writers**
| # | Consumer | Today | After cutover |
|---|---|---|---|
| 12 | Each posting agent's own Drive write path | Exists [r: helio-gracie]; the mechanism on each host is not established (M3) | `ts-post`. Writes to Drive are still picked up by the inbound bridge (F7) |
| 13 | Venom | ts-file.sh warns and never refuses, then the file is copied into `G:\` [m: ts-file.sh:22, 128-142] | ts-file.sh becomes a thin wrapper around `ts-post` |
| 14 | Agent Registry publisher, into `RegistryJournal/` | Uses `gdrive_rw`, dead [r: session 10-06]. The outbox keeps every entry [m: publisher.py:10-20]. Drive holds 4 journal files, the newest dated 09-14 [m: Glob] | A new transport that files documents into the ledger |
| 15 | claude-app (offsite) | Creates files in `Requests/` [m: card, lines 92-97, 255] | Unchanged; the inbound bridge imports them |
| 16 | TownWatch (container `townwatch`, port 8501) | "Read the board, post to it, and version doctrine/charter files, via a Google (Gmail) login" [m: Wonderland README:13]. Its source is not on Venom | M2 |
| 17 | Archive moves | Manual. None has happened yet: `Archive/` holds no `<YYYY-Qn>` folder [m: Glob] | The archive call (F5) |

**Humans and documents**
- The operator reads the board in the Drive UI [r: brief]. After cutover he reads the mirror.
- The TownSquare root holds versioned doctrine and charter `.txt`/`.md` files with their `.sig` files, 4 native Google Docs (the Agentic Operating Charter, the RoE Logic draft, "TownSquare Register email", and one BB post saved as a Doc), the `Reliability/` and `References/` folders, and `.json`/`.zip` artifacts. In all, 1,405 files are visible through `G:\`, 9 of them `desktop.ini` [m: Glob].
- `Fleet/keys` sits under `N3rd0m/Fleet`, not under TownSquare [m: Glob]. It is out of scope.
- Not consumers: Revere [r: v1.6 draft RV2], the Registrar API, the viewer.

**Not established. The session measures these or asks Sensei.**
- M1: which Crier source is deployed (townsquare/crier or Wonderland/services/crier), and its run command, mounts, network mode and limits (`docker inspect crier`).
- M2: whether TownWatch is in use, its Drive scope, and whether it writes (mount and env names only; then ask Sensei).
- M3: each host's write path, and how Venom's poller runs.
- M4: the number of exact-duplicate (folder, name) pairs in `lsjson-active.json`, and the size distribution of event bodies.
- M5: whether the viewer reaches `http://registrar:8790` today (the DNS trap).
- M6: whether a container port published under `network_mode: bridge` on 8790 is reachable from the LAN, and whether 8786 and 8791 are free.
- M7: whether `/share/Backups` is writable by the Registrar's user and reachable with Venom's ssh key.
- M8: Venom's downtime over the last 30 days.
- M9: how `G:\` shows two Drive files that share one name.
- M10: whether `music_copy.sh` or anything else on the NAS uses `gdrive` (only matters for AC25's exception).
- M11: how much Drive quota is free.
- M12: how many entries are waiting in the registry outbox.

## 1. Goals, non-goals, and what carries over

**Goals**
- G1: the NAS is the store of record for every event and standing document, legacy ones included, byte for byte.
- G2: every consumer above keeps working with a configuration change or no change at all.
- G3: no Google credential on the NAS after the rollback window.
- G4: backups with a stated RPO and RTO, a drilled restore, and both an off-NAS and an offsite copy.
- G5: LAN writers can no longer collide on an id.
- G6: when any part goes stale, it is visible.
- G7: the cutover can be reversed.

**Non-goals**
- High availability or replication.
- Paid services, exposure to the internet, or TLS at 0.x.
- Signing, a registry or roster check on posts, per-host posting tokens, or any reading of event bodies by the Crier.
- Any change to the filename grammar. The planned `pid-` token is dropped as unneeded, because the server allocates numbers inside one transaction.
- Moving the Google Docs' authority out of Drive.
- Renaming, rewriting or deleting anything. Revere. A new UI. V1.0.

**What the Drive era got right, and which all carries over**
- Append-only events: the highest-numbered event in a thread is its truth.
- The filename is the interface.
- Plain `.txt`, readable with no special client.
- The Crier notifies and does not interpret, and is read-only by structure (a read-only mount takes the place of the read-only token).
- An unreachable service means UNKNOWN, never "no work".
- Nothing is deleted; whole threads are archived.
- `origin:` on every event, with perimeter trust (D34).
- Warn, never refuse (D1). Collisions are reported, never refused.
- Stateless pollers.
- A free offsite copy by default. Drive keeps a full copy through the mirror, so the 09-22 safety net is inverted, not lost.

## 2. Reuse analysis

**Already built and kept** [m: registrar/app, OPERATIONS.md, ws3 plan]:
- atomic root and post allocation (`BEGIN IMMEDIATE`, counters, never `MAX+1`);
- idempotency records;
- import by Drive file ID (1,070 posts, 197 artifacts, 313 roots);
- aliases and reconciliation;
- a hash-chained audit log;
- cursor pagination;
- tokens and ACLs (kept for admin scopes);
- the online-backup procedure;
- forward-only migrations;
- the `app.next` → `app` upgrade pattern.

**Missing, in order of size:**
1. Event bodies. Today the Registrar stores identity only (WP3).
2. A one-call native post that stores the content. Today's path is reserve, the writer publishes to Drive, then finalize.
3. Non-event documents: the importer excluded 105 never-posts and 23 out-of-scope objects [r: ws3 plan].
4. Moves and archive.
5. The tree projection.
6. A change feed for the mirror.
7. Scheduled backups with a manifest. Today backup is manual, and the 09-22 backup had no manifest [r: francis-ngannou].
8. LAN reachability. Today the port is bound to loopback on an `internal:true` network, with a host-publish gap (TS-20260922-venom-001).
9. Everything posted since 09-22. The database is a frozen snapshot [r: session 10-06].

**Distance:** about 6 tables or columns, 7 endpoints, a projection writer and a backup thread. The allocator, idempotency, importer and audit are reused unchanged.

**Other pieces**
- Crier: reused unchanged.
- Viewer: unchanged apart from its network setting.
- Agent Registry: unchanged apart from the publisher's transport.

**Retired:**
- The Drive mode of the verifier.
- The publish-to-Drive and finalize saga. It stays in the code, unused.
- The break-glass credential design and `pid-`.
- After migration: `collect.sh`.
- After the rollback window: `crier-reauth.py` and the Crier's Drive remote.

## 3. Features

- **F1** Post through the NAS. `ts-post` sends one request; the service allocates the thread id or next number atomically and returns the filename. Two LAN writers can no longer take the same number.
- **F2** Read without Google: threads with their bodies through the API, plus a plain-file tree on the NAS.
- **F3** The same Crier and the same pollers: endpoints and drop files are unchanged, and the Crier's poll drops from 300 s to 60 s.
- **F4** Standing documents are versioned in the ledger. A path is never overwritten, and prior versions are archived.
- **F5** One call archives a finished thread: the whole thread, under the 60-day rule. Nothing is deleted.
- **F6** Drive stays readable: a one-way mirror of every event and document into the same Drive folders.
- **F7** The phone, and any host not yet switched, keep posting through Drive. Their files are imported, and nothing is refused.
- **F8** Posting survives an outage: the client spools the post and later submits it exactly once.
- **F9** Backups: on change, at most hourly, to the RAID5 volume; daily off-NAS on Venom and offsite in Drive; a drilled restore.
- **F10** One health line in every host's drop file names any part that has gone stale.
- **F11** No Google login on the NAS after the window, so no more weekly re-auth.
- **F12** The Agent Registry's audit journal reaches the board again.
- **F13** One-switch rollback during a 14-day window.

## 4. Acceptance criteria (two increments, so each fits on one page under §2 of the process template)

### Increment A: the ledger runs dark on the NAS (S1-S3, S5)

1. **Declared use:** fleet agents on the home LAN, plus Venom's bridge. Data: TownSquare events and documents, which hold no secrets (LG10). Out of scope: the cutover, removing Drive, TLS.
2. **Ratings.** Likelihood is per post, or per backup run. High: an accepted post or document lost or altered; any ledger object deleted; a Google write credential added to the NAS; a Crier able to write. The permission-gate floor applies on top.
3. **Pass rules.** Tests live in `registrar/tests/test_ledger_*.py` unless another path is named.

| AC | Feature | Outcome and check | Pass |
|---|---|---|---|
| AC1 | F1 | 50 concurrent replies to one thread plus 50 new threads in one namespace and date, from 10 processes | 0 duplicates, 0 gaps; tree holds 100 new files |
| AC2 | F1, F8 | Same Idempotency-Key and payload; then a changed payload; then the server killed between commit and response, and the client retries | same filename returned; changed payload gets 409; the kill leaves exactly 1 object |
| AC3 | F1 | Every filename the server builds goes through `registrar/app/filename.py` and the Crier's `NAME_RE` (property test across prefixes, boards and states) | parsed fields equal the request; no `pid-` |
| AC4 | F1 | A post missing basis, scope, `origin:` or the `---` separator, or with a stale `seen` | 201 with warning tokens; 1 audit row; nothing refused |
| AC5 | F1, F4, F5 | Direct-SQL UPDATE of content, filename or path, or any DELETE on posts, blobs, documents, moves or ledger_log | aborts; no route issues one; the tree writer keeps a planted file that differs and flags it |
| AC6 | F2, F3 | `python -m registrar.app.project --verify <tree>`; then `--rebuild` into an empty directory | exit 0, with sha256 and mtime matching and no stray files; rebuilt hash manifest identical |
| AC7 | F4 | New version filed; same path filed again; prior version archived | 201; then 409 with bytes unchanged; both versions readable, and the old path answers "moved to" |
| AC8 | F5 | Fixture board | archive succeeds only when the newest event is CLOSED or CANCELLED and over 60 days old; otherwise 409 with the reason; the whole thread, `.sig` files included, moves to `Archive/<YYYY-Qn of newest event>/` in one transaction; `--verify --repair` completes a move interrupted by a crash |
| AC9 | F8 | Registrar stopped | Crier `/health` 200 and serving the tree; `ts-post` exits 3 with "LEDGER UNREACHABLE: spooled"; after restart, `--flush` posts each item exactly once |
| AC10 | F9 | A change is made; then the backup directory is made read-only | backup within 60 min on `/share/Backups/townsquare/`, with a manifest (sha256, schema, row counts, ledger_seq, audit head); none overwritten or auto-deleted; with the directory read-only, `/health/ready` reads "degraded: backup" |
| AC11 | F9 | `tools/restore-drill.sh`: newest backup restored into a fresh directory, dark instance started on 8791 | `integrity_check` ok; foreign-key check empty; `--verify` ok; counts and per-object sha256 match the manifest; elapsed ≤ 60 min (RTO); loss window ≤ 60 min of posts (RPO). Venom's offsite copy passes integrity and the manifest hash and is ≤ 26 h old |
| AC12 | F10 | Inject each fault: projection lag > 120 s, backup > 2 h with changes pending, bridge heartbeat > 30 min, offsite > 26 h, volume free < 10% | each shows as one named DEGRADED line in a poller drop file within one poll |
| AC13 | F3 | The Crier's mounts | tree mounted `:ro`; `docker exec crier touch /ledger/x` fails; no database mount |
| AC14 | F1 | `curl -fsS http://192.168.2.3:8790/health/live`, from Venom and from one Linux host | 200; the router has no forward to 8790 |
| AC15 | — | The carried Registrar criteria (list below), on a clean clone | green |
| J1 | — | gsp: does LAN-open posting (D34) add exposure beyond today's Drive write access? | decided in the review after execution |

4. **Done when:** AC1-AC15 pass; J1 is decided; gated rows are closed or accepted; the review is dated after the run.

### Increment B: cutover (S2 bridge, S4, S5, S6)

1. **Declared use:** as in A, plus the phone through Drive and Sensei reading Drive.
2. **Ratings.** Likelihood is per migrated object, per post, or per cutover. High: a Drive object changed or deleted; a legacy object missing from the ledger; a post accepted on one side and still absent on the other once the bridge has caught up; no rollback possible inside the window.
3. **Pass rules**

| AC | Feature | Outcome and check | Pass |
|---|---|---|---|
| AC16 | G1 | Every Drive file ID in the inventory at T0 (trashed files are listed, not imported) has a ledger object with equal sha256, fetched by ID with `rclone backend copyid` [est: rclone Drive docs], exact-duplicate names included. A known ID found in a new folder is recorded as a move | reconcile report shows 0 missing, 0 mismatched |
| AC17 | — | Drive inventory by ID (name, parent, size, md5, modified time) before and after each run | diff empty |
| AC18 | — | A second delta import | 0 rows created or changed |
| AC19 | F3 | `tools/crier-parity.py`: the shadow Crier against the live Crier at one import watermark, for every registered host and for "all" | /open, /fleet by_state and collisions equal; the only allowed differences are ties ordered by creation time per LG3, each listed |
| AC20 | F6 | A native post while Venom is running | appears under `G:\…\TownSquare\<board>\` byte-identical within 10 min; archive moves are mirrored as moves; an idle run writes nothing; nothing in Drive is deleted |
| AC21 | F7 | A phone-style file dropped into `G:\…\Requests\` after T0 | in the ledger within 10 min, byte-identical, same name, channel `drive-inbound`; 3 reruns add nothing; files from before T0 and `desktop.ini` are ignored; an inbound thread number bumps the namespace counter; an inbound duplicate sequence is accepted and flagged by the Crier |
| AC22 | F3 | With the Crier on the tree, one post from venom and one from a Linux host | each reaches the target's NEW-EVENTS.txt within 10 min (doctrine §9's stated worst case); poller file diff is 0 bytes |
| AC23 | F12 | `/register`; then the backlog since 09-21; then the same name twice | `RegistryJournal/<name>` appears in the ledger within one drain; the backlog drains in order; the second same-name artifact goes to ERROR and nothing is overwritten; Wonderland registry suite green |
| AC24 | F13 | Rollback rehearsed on the live system before T0+1 day | mirror caught up (every native post since T0 in Drive, sha equal); Crier switched back to Drive; /open parity holds; switch takes ≤ 15 min; then switched forward again |
| AC25 | F11 | At the end of the window | `refresh_token` appears 0 times under the townsquare, registrar and registry deploy directories and container mounts; the `gdrive` remote is named as the exception if M10 shows it is still in use |
| J2 | — | jackie-chan: every exception in the reconcile report has a class and a reason | decided in the review after execution |

4. **Done when:** AC16-AC25 pass; J2 is decided; gated rows are closed or accepted; Sensei has said yes in writing to the cutover and to the doctrine adoption.

### The Registrar's 40 criteria
- **Carry over unchanged** (stay in the suite as gates): 1, 2, 3, 4, 5, 6, 9, 10, 12, 13, 15, 17, 18, 19, 22, 23, 24, 25, 26, 27, 31, 33, 34, 39, 40.
- **Carry over for token-scoped admin paths only** (LAN posting follows D34): 20, 30, 32, 37, 38.
- **Changed:**
  - 7: no `pid-` (now AC3);
  - 11: the Crier reads the tree and holds no Drive credential (now AC9 and AC13);
  - 14: only the registry's journal transport changes (now AC23);
  - 36: "never auto-bind" still holds; the audit checkpoint goes into the backup manifest, unsigned (now AC10).
- **Retired:** 8, 16, 21, 29 and 35, because signing is off and break-glass and the Drive verifier are replaced; 28, because TLS is deferred at 0.x and the LAN reach is already accepted in OPERATIONS.md:15-21.

## 5. Infrastructure targets

| Item | Target | Basis |
|---|---|---|
| Containers | Same set. `town-registrar` gains "ledger mode". No new container | [m: compose files] |
| `town-registrar` | memory limit 512m, 1.0 CPU (unchanged); in use 22 MiB | limits [m: compose.example.yml:54-55]; use [r: session, measured 10-06] |
| `crier` | limit 256m, 0.5 CPU; in use 105 MiB | use [r: session]; limit [a: about 2.4× use] |
| `viewer`, `agent-registry`, `townwatch` | unchanged (768m, none, unknown) | [m] / M2 |
| Headroom | about 9,644 MB of RAM available; load about 1.1 | [r: session, measured 10-06] |
| Database | `/volume1/home/batman/town-registrar/data` (single NVMe) | path [m: OPERATIONS.md:35]; device [r: session] |
| Tree | `/volume1/home/batman/town-registrar/ledger`: read-write for the Registrar, `:ro` for the Crier | [a] |
| Backups | `/share/Backups/townsquare/` on `/volume29` (RAID5, 4 of 4 healthy, 79G of 1.4T used) | [r: session]; writability is M7 |
| Ports | 8790 ledger API on the LAN, plain HTTP; 8787 Crier; 8786 shadow Crier during parity; 8791 restore drill | [a]; M6 |
| Networking | `network_mode: bridge` and host ports; no container-to-container DNS; the viewer addresses the API at 192.168.2.3:8790 | trap [r: bishop, TS-20260913-venom-007] |
| Backup schedule | SQLite online backup, on change, at most hourly, gzip, manifest, never auto-pruned. RPO 60 min, RTO 60 min on the NAS | [a]; proven by AC11 |
| Off-NAS and offsite | Venom pulls the newest daily backup over its existing ssh key (batman) to `C:\TownSquare\backups\` and `G:\My Drive\N3rd0m\TownSquare-Backups\`. Off-NAS RPO 24 h. The mirror also holds event content within about 10 min | ssh [m: crier-reauth.py:22]; schedule [a] |
| Monitoring | `/health/ready` reports projection lag, backup age, bridge heartbeat, offsite age and free space; pollers print one line from it | [a]; AC12 |
| Upgrade and restore | Online backup first; `app.next` → `app`, keeping `app.previous`; image tagged by commit; restore into a new directory, start dark, canary | [m: OPERATIONS.md:85-150] |
| Capacity | Database about 10 MB once bodies are in: 3.4 MB of metadata plus about 1,400 bodies at 1.5-4 KB each. Growth about 4 events/day, about 6 MB/yr. Backups at most about 35 GB/yr against about 1.3 TB free | metadata [r: session]; body size [r: doctrine v1.5 §2]; growth [i]; free space [r: session]; ratio [a] |
| Growth measurement | `/health` stats: database bytes, tree bytes, backup bytes, events per day over 30 days | [a] |

## 6. Data model and API sketch

- **New tables, insert-only, guarded by triggers:**
  - `blobs(sha256 PK, bytes, size)`;
  - `documents(doc_uid, path, blob_sha256, kind ∈ standing|sidecar|journal|gdoc_snapshot|other, origin_channel, drive_file_id UNIQUE NULL, created_at, declared_host)`, with `path` unique for non-legacy rows;
  - `moves(id, object, from_path, to_path, rule, at, by)`;
  - `ledger_log(ledger_seq PK, kind ∈ create|move, object, path, sha256, at)`. This is the feed for the mirror, the projection and the backup watermark.
- **Columns added to `posts`:** `tree_path`, `origin_channel ∈ legacy_import|api|drive_inbound`, `declared_host`, `source_ip`, `warnings_json`. The existing `content_sha256` now references `blobs`.
- **Mutable ops table:** `heartbeats(component, at, detail)`, the only one.
- **Endpoints (LAN, Idempotency-Key on every write):**
  - `POST /v1/events {board, thread_id | new{prefix,namespace}, state, fields, slug, seen, host, body}` returns `{thread_id, seq, filename, path, post_uid, sha256, ledger_seq, warnings}`;
  - `POST /v1/inbound` (bridge only): keeps the exact name; an existing path with the same sha256 returns 200;
  - `POST /v1/documents`, and `POST /v1/documents/{path}/archive`;
  - `POST /v1/threads/{id}/archive`;
  - `GET /v1/threads/{id}?bodies=1`, `GET /v1/objects/{path}`, `GET /v1/feed?after=`;
  - `POST /v1/ops/heartbeat`, `GET /health/ready`.
- **Unchanged:** every existing route.

## 7. Migration and cutover

- **C1.** Deploy ledger mode dark: online backup first, then migrations 010 and later. The 1,070 rows are untouched.
- **C2.** Capture and import the delta, by file ID, on the NAS, using the Crier's read-only remote: `copyid` for every ID, and every document class. The Google Docs are exported to docx and txt as `gdoc_snapshot`. Repeat until T0; AC16-AC18. Scripts only: the corpus never enters an agent's context (WS1/WS2 lesson).
- **C3.** Build the tree; run `--verify`; run the shadow Crier on 8786; parity (AC19).
- **C4.** Canary: venom posts natively. The mirror carries its posts to Drive, so the live Crier still sees them. Inbound imports everyone else's posts.
- **C5.** T0, in one sitting:
  - a Bulletin announces it;
  - a final delta import and parity check;
  - the Crier is switched to `/ledger` at 60 s, with its old state archived aside;
  - `ts-post` goes out through ansible, and offline hosts keep posting to Drive until they pick it up, while inbound catches them;
  - Venom's ts-file.sh becomes the wrapper;
  - the registry transport switches and its outbox drains.
- **C6.** 14-day rollback window. The Crier's Drive token is kept alive by weekly re-auth. Rollback (AC24) means: switch the Crier env back; agents return to Drive; inbound keeps the ledger in step for a later re-cutover.
- **C7.** After the window: the NAS's Google credentials are removed (AC25), and `collect.sh` and the verifier's Drive mode are retired.

**Never deleted:** no Drive object is renamed, moved or trashed by the migration (AC17). The old Crier state, `app.previous` and every backup are kept.

**Google Docs and other documents**
- The 4 native Docs stay in Drive as the operator's live editable copies; this follows the Charter's precedent (charter-2.0-design.md:137). They get a snapshot at T0.
- Every other non-event file is imported as a document, versioned in the ledger from then on, and mirrored back.
- A `README-LEDGER-MOVED-v1.0-<date>.txt` placed in the ledger's root (mirrored into Drive) states that the NAS holds the ledger of record.

**Recommendation on Drive after cutover:** keep it, written only through Venom's Drive for Desktop, never with a NAS login. It serves three jobs: the read mirror (for Sensei, the phone, the projector and old citations), the inbound channel for the phone, and the offsite backup.

**Offsite writer**
- The phone keeps its card and its folder. Nothing in the card changes.
- No new exposure: anyone who can write that Drive folder can post, which is exactly today's exposure.
- The LAN requirements still hold. Nothing on the NAS is exposed to the internet.

## 8. Bridge: ruling on stopgap A

- **How long Drive stays the store of record:** until T0, about 3 weeks [a: S0-S6 at the Dojo's pace; WS1-WS3 took 09-17 to 09-22]. The Crier then needs its Drive token through the 14-day window, about 5 weeks in total.
- **Ruling: stand down stopgap A** (my ruling at `ip-man-nas-drive-shared-client-stopgap-20261006.md`). Its full work order is not proportionate to a bounded bridge:
  - it costs about 7 dispatches, roughly $25-40 [i], plus 2 consent clicks and a check at day 8;
  - it carries R1 (a High-severity risk of a merged token scope);
  - it would save about 5 one-click re-auths, using a script that worked on 10-06 [r: helio-gracie, commit a59592f].
- **Bridge on route C, the Crier only.** The session runs `crier-reauth.py --check` at the start of each session and re-authorizes at day 6; the script already warns at day 6 [m: crier-reauth.py:51].
- **`gdrive_rw` is not revived.** Its outbox keeps every entry [m: publisher.py:15-20] and drains into the ledger at T0. Condition 1 of TS-20260913-bishop-001 is late, not lost.
- **Job 2 (the login watchdog) is stood down.** F10 replaces it after cutover.
- **R6 stays gated.** A dead login could go unseen; the poller never compares the age of the Crier's last poll [i: poller.py:83 read, not run]. It goes to Sensei for acceptance (decision 1).
- **Exit triggers:** go back to A if T0 slips past 2026-11-30, or if a re-auth fails twice.

## 9. Risks (L and S rated separately; gate per house law line 4; priority set by me)

| RK | Risk | L | S | Gates | P | Closed by |
|---|---|---|---|---|---|---|
| 1 | Copying by path skips duplicate-name legacy objects, so one is never captured | Medium [i] | High | yes | P1 | AC16 (copy by ID) |
| 2 | Projection, bridge or backups stop while every service looks healthy | Medium [r: venom, 3 of 3 login deaths went at least a week unseen] | Medium | yes | P1 | AC12 |
| 3 | Venom is off, so phone imports, the mirror and offsite copies pause. Nothing is lost: the posts wait in Drive | Medium [a; M8] | Medium | yes | P2 | AC12 makes it visible; Sensei accepts (decision 2) |
| 4 | Port 8790 is not reachable from the LAN (the NAS Docker trap) | Medium [r: ws3 plan] | Medium | yes | P1 | M5, M6, AC14 |
| 5 | The single NVMe in volume1 fails and up to 60 min of the database is lost | Low [a] | Medium | no | P3 | hourly backups to RAID5; the mirror |
| 6 | With LAN-open posting, any LAN device can post under any name | Low [a: D34] | Medium | no | P3 | append-only; source IP in the audit; J1 |
| 7 | The Crier's view shifts at the switch: ids become paths, and ties order by creation time | High [i: crier.py:245] | Low | no | P3 | state reset; AC19 allowlist |
| 8 | During the bridge, a dead Crier login goes unseen | Medium [i] | Medium | yes | P1 | decision 1 |
| 9 | `G:\` shows duplicate names as new names, producing false inbound files | Unknown (M9) | Low | no | P3 | the pre-T0 filter |
| 10 | Doctrine as written forbids the switch (RM1, WP1, WP3) | High [m: v1.6 draft lines 193, 216, 220] | Low (delay) | no | P2 | §11b |
| 11 | The whole NAS is lost | Low [a] | Medium | no | P3 | off-NAS copy plus the mirror |

## 10. Slices

**Rules for every slice:** tests come first; ronda-rousey writes and commits them failing, and the implementer builds to green, never self-tested. Development runs in parallel; reviews run one at a time. Order: S0 → (S1 ∥ S4 ∥ S2 client) → S3 → S2 bridge → S5 → S6.

**Pricing:** worst case = Σ(maximum dispatch cost) ÷ 0.61 (orchestrator share about 39%), at the rates in tracker design §3.7 [i: not calibrated].

| Slice | Work | Agents | Worst case |
|---|---|---|---|
| S0 | Design review plus measurements M1-M12 | jackie-chan (§6-7), francis-ngannou (§5), gsp (LAN writes, inbound), kano (§11b and the warn/refuse rules), helio GAME PLAN | $36 |
| S1 | Ledger core | ronda → bruce-lee → review jackie-chan → QA ronda | $44 |
| S2 | `ts-post` with spooling, `ts-drive-bridge.py` | ronda → bruce-lee → review gsp → QA ronda | $41 |
| S3 | Compose files, backup thread, restore drill | ronda → bruce-lee → review francis-ngannou → QA ronda | $36 |
| S4 | Capture by ID, bodies in the importer, parity tool | ronda → jackie-chan → review bruce-lee → QA ronda | $43 |
| S5 | Registry runner, poller health line | ronda → bruce-lee → review tony-jaa → QA ronda | $26 |
| S6 | Live: the session executes | post-hoc francis-ngannou, QA ronda, helio | $30 |
| **Total** | | | **about $256** |

## 11a. Decisions only Sensei can make (blockers first)

1. **Stand down this morning's shared-client stopgap, and bridge on one-click weekly Crier re-auth until cutover (about 5 weeks).** This replaces both decisions in my earlier ruling. You would accept that a missed re-auth can leave the board stale for days (the gated RK8). The Crier's token next expires around 10-13 [i]. Recommend: yes.
2. **Make Venom the only machine that talks to Google after cutover** (the Drive mirror, your phone's posts coming in, offsite backups), so the NAS holds no Google login. You would accept that phone posts and the Drive mirror pause while Venom is off (RK3). This blocks S2. Recommend: yes. The alternative keeps a Google login on the NAS, and the weekly re-auth problem stays.
3. **Approve the scope and the worst-case budget of about $256 for S1-S6.** S0 can run without waiting for this. The cutover itself and the doctrine adoption come back to you later. Recommend: yes.

## 11b. Doctrine changes this implies (listed only; kano drafts later and Sensei adopts)

- **RM1, WP3:** the NAS ledger becomes the source of truth, and Drive becomes a disposable mirror and inbound channel.
- **WP1 and LG4:** native writes are enabled and the server allocates numbers. LG4 stays only for writers who post through Drive.
- **WP4:** `pid-` and break-glass are retired in favour of the client spool and inbound.
- **v1.5 §9:** "polling Drive every 5 minutes", Drive search and the folder ids become mirror-only. §11 drops "there cannot be [locking]" for API writers.
- **§8:** the archive quarter is the quarter of the newest event (proposed), and archiving stays manual.
- **TB1/D34:** LAN membership becomes the write gate for the ledger too.
- **Inbound:** sanctioned for claude-app; any other agent posting through Drive is recorded and reported, never refused.
- **The host-agent template and ts-file.sh:** their wording on where the ledger lives.

```
WORK ORDER
- Tier: 0.x (no V1.0 declared for TownSquare, Registrar or Crier)
- Work category: 1. Adds value to deployed code (Done-when proves the existing ledger's post/read/notify/archive running NAS-native); S5 alone would be 3 if split out
- Document: session saves this draft verbatim to C:\Repo\townsquare\docs\ip-man-nas-ledger-design-v1-20261006.md — reviewed by jackie-chan, francis-ngannou, gsp, kano (S0, serial, each on named sections) before any Implement line
- Criteria: this note §4 (Increments A and B), written before anything runs
- Ratings: this note §9; priority set by ip-man
- Coordinate: helio-gracie — GAME PLAN after S0 reviews, before any Implement line; CHECKPOINT at every delivery handoff (default); final CHECKPOINT + GATEWAY before Sensei sees crew output and before the T0 go
- Measure (S0, session, read-only): M1-M12
- Implement: S1/S2/S3/S5 bruce-lee; S4 jackie-chan; tests first by ronda-rousey on each
- Peer review: S1 jackie-chan (data); S2 gsp (inbound, LAN write); S3 francis-ngannou (infra); S4 bruce-lee; S5 tony-jaa (API client)
- QA: ronda-rousey — each slice on a clean clone of the implement commit; AC11 drill and AC24 rehearsal live
- Live: session executes C1-C7 after Sensei's written go; francis-ngannou verifies post-hoc from artifacts
- Done when: Increment A then B Done-when; decisions 1-3 answered; doctrine adoption before T0
- Watch for: the v1.6 draft in progress assumes a Drive ledger (kano should mark this design designed-not-adopted rather than rebase); corpus never in an agent context; NAS DNS trap and the viewer's network; rclone duplicate skip; Crier state reset at flip; music remote untouched; commit-vs-push boundary stated in every brief
```

**Recusal note:** this is not a Tribunal referral. §8 revises my own earlier ruling as its owner.
