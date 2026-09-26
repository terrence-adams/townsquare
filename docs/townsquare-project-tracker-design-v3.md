# TownSquare project tracker, v3: the claude-app pre-registration check

Delivered 2026-09-26, re-deriving v2 section 5's pre-registration safety check
against the real `authorize_from_registry.sh` fetched from the NAS
(`reference-authorize_from_registry-20260926.md`) rather than the superseded
description v2 reasoned from. Design only; decision 6 stays held for the
operator. Extracted verbatim from the subagent transcript, not retyped;
save_verbatim.py's CLI reads only an end_turn text block, and this agent's
report was instead delivered as a SubagentHandback tool_use input field, so this
was pulled by hand from that same field (see the provenance line below).
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=60c382d97f575b2d3d78de40da76fba6279846460cfb865e1467ecfa44edd6f0 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-a402772e4afc630e1.jsonl:114 message=msg_011CfRdCnp1YaeKKyQ8mjbxt -->
# TownSquare project tracker, v3: the `claude-app` pre-registration check, re-derived against the sync script that actually runs

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** design only. Nothing registers and nothing executes. Decision 6 (register `claude-app` under `binding: offsite`) stays held for Sensei.

**Proposed path:** `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v3.md`, branch `internal`, not pushed.

**What this replaces in v2.** v2 is `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v2.md`, sha256 `954df5dc957aea2de168b41837ee8d4687e2fc3cef5fca98828d32f0fc0e642b` according to its first-line comment. I did not re-hash it. This note replaces these parts of v2 §5 and its work order:
- item 3's hazard bullet and its Migration line;
- item 4's premise;
- the "Pre-registration check" P0–P5;
- the "Separately… `curl -fsS`" paragraph;
- the keyring sentence in "My view on adopting the value";
- work-order Done-when (4) and Watch-for (b) and (e).

The "P0" references in items 1–2 now mean P3 and P5 row 2. Everything else in v1, v2 and kano's review stands.

**Also read:** `C:\Repo\townsquare\docs\reference-authorize_from_registry-20260926.md`. Its header records a byte-for-byte sha256 match with the NAS copy. I did not re-hash it.

**Labels:** *measured* means I read it this run. *inferred* means reasoned from what I read, not executed. *reported-by X* means X's claim, which I did not check.

**Shorthand:**
- **the script:** `authorize_from_registry.sh` as fetched from the NAS on 2026-09-26. Line numbers count its `#!/bin/sh` as line 1, as the reference file, bishop and cable all do.
- **the feed:** the registry's `GET /authorized_keys` response at `http://192.168.2.3:8789`.
- **P1–P5:** the steps of the revised check in §4. v2's P0 is withdrawn and its label is not reused.
- **A19, F1, F3:** items in cable's Wonderland review (`BB-20260913-cable-006.000`), as ruled on by bishop, who owns that code, in `TS-20260913-cable-016.001`.
- **B.6, C3:** in kano's review, Deliverable B. B.6 is his draft registration bulletin. C3 is his receipt-check clause "the id's namespace resolves to a registered agent".
- **stable fields:** these fields of a registry row: agent, vendor, model, binding, section, os, shell, role, status, pubkey, host_address. That is every field except last_source, updated_at, applied_at and flags.
- **TSD:** Town Square Doctrine v1.5.

**Recusal.** v2 §5 was mine, and this note re-answers it. If the offsite registration check is ever referred to the Tribunal, I am conflicted under rule 5 limb (ii) and will not sit.

## 1. The prior hazard claim, ruled plainly

v2 said three things:
- The fleet's published sync was `curl -s` without `-f`, so an HTTP error body would be appended to `authorized_keys` on every syncing host. It labelled this *measured* against `BB-20260912-bishop-002.000`.
- The keyring was "the one consumer whose failure reaches every host".
- The POST should therefore wait on a code read.

**I disagree with the claim. Its severity drops from "gate the POST on a code read" to "confirm with one byte comparison".**

1. **v2 cited a superseded event.** `.000`'s one-liner is indeed `curl -s … | while read k; … >> ~/.ssh/authorized_keys`, with no `-f` [measured]. But the thread moved on:
   - `.001` suspended that instruction.
   - `.002` and `.003` lifted the suspension.
   - `.003` says "The sync procedure hosts should follow is announced in BB-20260913-bishop-001.000" [measured].

   That announcement's procedure is "Run authorize_from_registry.sh", and it does not repeat the one-liner [measured]. v2 cited the thread's first event, not its newest. The script's current content also predates the one-liner: its NAS mtime is 2026-09-12 23:51:20Z [reported-by the reference file], and `.000` is stamped 2026-09-13T00:57Z [measured].
2. **The script fails closed in exactly this case** [measured, lines 27–30].
   - `curl -fsS -m 10 "$URL" -o "$TMP"` runs inside `if !`.
   - An HTTP 400+, a timeout or a transport error prints a message and exits 1 before the append loop runs.
   - The body goes to a temp file, never to `authorized_keys`, so a broken feed writes nothing on any host that runs the script.
   - The result is a **stall**: that host stops gaining keys until the feed recovers.
3. **A stall cannot become a lockout.**
   - The script never removes a line (lines 33–39). This is cable's A19, confirmed by bishop.
   - Password SSH stays enabled fleet-wide by Sensei's standing decision [reported-by session memory].
4. **What v2 got right, and this note keeps:**
   - sshd skips lines it cannot parse, so junk that does land is pollution, not a lockout [inferred: general OpenSSH behaviour, not tested here].
   - The feed reaches every host. That is why the check still centres on comparing the feed.
5. **What v2 missed: the irreversible case is a *valid key* reaching the feed.**
   - A host that syncs a key keeps it after the row is retired. The ledger already has this as A19: "retired keys persist on already-synced hosts". bishop's F3 verdict puts it as "revocation is feed-side yes, host-side no".
   - `claude-app` holds no key, so this can only happen through a payload mistake.
   - So the thing to check before sending is the payload, not the service code.
6. **The `curl -fsS` Request is withdrawn.** The script already uses those flags. The Request was never filed: no Request dated 2026-09-25 or 2026-09-26 mentions `fsS`, `curl -f` or `authorize_from_registry` [measured]. Nothing needs correcting.

**Still unmeasured: whether every host runs the script.**
- `bishop-001.000` prescribes it.
- cable listed it as "built, untested" on 2026-09-13 [measured: `BB-20260913-cable-006.000`].
- No host has reported its schedule.

A host still running `.000`'s one-liner would take in an error body, as v2 said. The check is built so this does not matter: if the feed is byte-identical before and after the POST, no host can see a difference, whatever it runs.

**On the session's preliminary read** (the closing paragraph of the reference file). I agree that a failed pull never reaches `authorized_keys` and that writes are additive. Three corrections:
- **An empty pull is not caught.** `-f` rejects only HTTP 400 and above. An empty 200 runs the loop zero times and exits 0. It is harmless only because nothing is ever removed.
- **The file is rewritten on every run.** Line 42, `sort -u "$AK" -o "$AK"`, truncates and rewrites the whole file each run, in sorted order and not atomically. So "never truncated except on first creation" is wrong.
- **v2 never claimed the keyring would be emptied.** It claimed pollution by error bodies, so pollution is the right comparison.

## 2. What else in the script bears on the check

**A final line without a trailing newline is skipped.** This is a latent defect [inferred from POSIX `read` semantics].
- `while IFS= read -r key` (line 33) stops at end of file without running the loop body for an unterminated last line. `.000`'s one-liner has the same construct.
- If the feed does not end in `\n`, the script has never added the feed's last key on any host that lacked it.
- This also makes line order matter: changing which line is last changes which key the fleet silently skips. So the check compares bytes, not sets. P1 records the deciding byte.

**The error message is misleading.** Every curl failure is logged as "registry unreachable", including an HTTP 500 from a reachable registry. When diagnosing a stall, read exit 1 as "network failure or HTTP 400+".

## 3. Other ledger facts that change the check

- **Retiring removes a row from the feed.** bishop, at code level: "/authorized_keys excludes retired (app.py:161)" [reported-by bishop, `TS-20260913-cable-016.001`, Wonderland `e340e09`]. v2 made P0 mandatory to find out whether retiring would repair a broken feed. For the feed, this answers it. For `/mesh`, it does not.
- **The feed looks per-row, not per-host.** F3 says "/register writes pubkey for any named agent" [reported-by bishop]. If so, a row with no pubkey cannot change the feed, whatever its binding [inferred]. P3 confirms this by observation.
- **`/register` overwrites any named agent's row, pubkey included, with no ownership check** [reported-by bishop, F3]. So the payload's `agent` field matters as much as its `pubkey`.
- **v2's item-4 premise is stale.**
  - bishop-007 is CLOSED, with its recency guard live (`.002`, 2026-09-13T02:35Z) [measured].
  - bishop-009 replaced substring detection with exact-token detection, and disabled board ingestion as a write path [measured: `.005`; its deployment reported-by bishop in `.006`].
  - Two earlier on-behalf registrations are precedents: `BB-20260913-venom-003` and `BB-20260914-venom-001`. Their slugs contain "registration", and neither carries a `cat-registration` token. B.6 has no token and nothing the exact-token detector reads, so those precedents cover it.
  - One risk remains. The Crier liveness loop is intact by design and "touches every author" on each poll [reported-by bishop, F1]. A crier-sourced upsert blanked five of venom's stable fields after the ingestion change was reported deployed (2026-09-13T09:16:38Z) [reported-by session memory].
  - So a re-read after the Crier has polled is still warranted. Its target is venom's row and `claude-app`'s row, not the slug.
- **Sensei's onboarding order is bulletin first, then register.** In his words: "A new agent posts to the bulletin board with its information. Then registers itself and its ssh key." [measured: `BB-20260913-cable-003.000`]. B.6 already follows this order. So the baseline must come before the bulletin, not just before the POST.
- **The journal records every accepted write, with its before-state** [reported-by bishop, `TS-20260912-bishop-009.005`/`.006`]. `GET /journal` therefore shows whether the POST created a row or overwrote one, and whether anyone else wrote in the window.
- **The fleet had already reviewed the script.** cable reviewed it on 2026-09-13 and bishop ruled on the findings the same day. v2's gap was that it did not search the ledger. The script itself had been read.

## 4. The revised check: five steps, P1–P5

Every step is a read except P2. When decision 6 goes to Sensei, it should say that a yes covers P1–P5 as written, including P5's retire. Anything else P5 might need goes back to him.

**P0 — withdrawn.**
- It gated the POST on reading the service code, and its fallback held the POST on a Request to bishop.
- Its purpose was to learn in advance whether retiring would repair a broken feed. bishop's verdict answers that for the feed. The script makes a broken feed harmless to hosts, and P3 sees the rest within seconds.
- Its fallback also made a Dojo step wait on a non-Dojo host that is offline.
- The code read survives only as P5's last resort.

**P1 — baseline.** Reads only. Take it in the same sitting as filing B.6, immediately before filing it.
- `GET /authorized_keys` and `GET /authorized_keys?exclude=venom`: record status, SHA-256, line count, and whether the last byte is a newline. Take each twice, about a minute apart.
- `GET /mesh`: status and SHA-256, twice.
- `GET /registry`: any `claude-app` row, and venom's stable fields.
- `GET /journal?limit=5`: the newest entry.
- **Have the undo ready.** Know the exact `POST /retire` call for `claude-app` before P2. The board records no example, so take it from the service's own `/retire` route on the NAS, fetched the same way the script was. bishop placed it at app.py:132–138 at `e340e09`; it may have moved.
- **Stop rules:**
  - If a `claude-app` row exists and its `last_source` is not a `crier:` stub, stop and report. Do not overwrite it.
  - If the two feed captures differ, stop and retake later. P3 cannot work against an unstable feed, and a feed that changes with no journal entry is itself a finding.
  - If the two `/mesh` captures differ, P3 compares `/mesh` only on the lines that stayed the same.

**P2 — the POST** (decision 6).
- Before sending, check the payload against the precedent in `BB-20260914-venom-001.001`:
  - `by=venom`
  - `agent` exactly `claude-app`
  - `binding` exactly `offsite`
  - `pubkey` and `host_address` empty
  - every other field taken from B.6's header
- Send it once. Record the status and the echoed row.

**P3 — immediate comparison.** Reads, right after P2. It passes only if all of these hold:
- The POST returned 200 with `ok: true`, and the echoed row matches the payload. Record its `section` as information; it is not a trigger.
- The journal has exactly one entry newer than P1's: `register` for `claude-app`, with an empty before-state (or the stub P1 recorded).
- Both feed captures are byte-identical to P1, with the same status.
- `/mesh` has the same status and is byte-identical to P1, or identical on the lines that stayed the same.
- venom's stable fields are unchanged.

**P4 — settled comparison.** Reads.
- **(a)** At least 10 minutes after P2 (v2 cited this as the TSD §9 worst-case Crier latency):
  - Repeat P3's comparisons of the feed, `/mesh` and venom's row, and re-read `claude-app`'s stable fields.
  - Then venom appends B.6's result event. It carries P1's, P3's and P4's hashes and outcomes, the section, and the journal entry.
- **(b)** Once, the first time venom acts on a `claude-app` post that follows the card: re-read `claude-app`'s stable fields. That is the first time the liveness loop meets an offsite author.

**P5 — response.** Rows 2 and 3 apply only when the journal shows `claude-app`'s write as the only write since P1. Otherwise, row 5 applies.

| # | Observation | Response |
|---|---|---|
| 1 | The POST is rejected (4xx) | Nothing was written. Stop and report: registration needs a service change, which is bishop's code (a Request, not a dependency). The card can run unregistered meanwhile; C3 flags each post. |
| 2 | An endpoint's status changed, or the feed's bytes changed with no new key material | Retire `claude-app` at once and re-capture. If restored: record it, and file a Request to bishop. If not: sync is stalled or `/mesh` is broken, and no host is harmed. The session fetches the deployed route from the NAS, jackie-chan reads it (it is a query question), and it goes to Sensei. |
| 3 | The feed carries key material that was absent at P1 | Retire at once. This removes it from the feed only; hosts that already synced it keep it (A19). Removing it from each host is a live change and needs Sensei's go. |
| 4 | Only `/mesh` content, or `claude-app`'s section or stable fields, differ | Keep the row. Record the difference in the result event, and file a Request to bishop. |
| 5 | Another write appears in the journal window, another row's stable fields changed, or anything else not covered above | Stop and do nothing further. Report through Helio with the captures and the journal entries. Restoring any other row is a registry write and needs Sensei's go. |

## 5. One finding for bishop, only if P1 shows it is live

- **If the feed lacks a trailing newline:** the script, and `.000`'s one-liner, have been skipping the feed's last key on every host that lacked it. That is live, fleet-wide, and unrelated to `claude-app`. The session files one Request to bishop, naming the key and suggesting the one-line fix `while IFS= read -r key || [ -n "$key" ]`.
- **If the feed ends in a newline:** the defect is latent, and nothing is filed.

Deciding which case applies takes one read, and reads need no approval, so it can be measured now. That read does not replace P1's baseline. This finding never gates decision 6.

## 6. v2 to v3

| v2 | v3 | Why |
|---|---|---|
| Item 3: `curl -s` without `-f` writes error bodies into `authorized_keys` on every host | Withdrawn | The procedure in force runs the script, which uses `-fsS` and exits before writing (§1) |
| Item 4: bishop-007 and bishop-009 open; slug substring match | Liveness loop; venom's and `claude-app`'s rows | §3 |
| P0: mandatory code read; hold the POST on bishop | Withdrawn; last resort in P5 row 2 | §4 |
| P1: capture before P2 | Before the bulletin; twice; journal; trailing byte; `?exclude=`; undo ready | Sensei's order; stability; §2 |
| P2: POST | Payload checked first | `agent` and `pubkey` are the costly mistakes (§1.5, §3) |
| P3: byte-identical; one new row; section not host-bound | The journal decides new vs. overwrite and sole writer; section recorded, not a trigger | Attribution; a label harms nothing |
| P4: re-read after 10 minutes | Also re-runs the feed comparison; one more read at the first `claude-app` post | Liveness loop |
| P5: retire, plus a Request to bishop | Five-row table | Retiring does not remove a key hosts already synced |
| `curl -fsS` Request | Withdrawn; it was never filed | §1.6 |
| — | Trailing-newline finding, conditional | §5 |

## 7. The alternative I rejected

**Option: keep a code read before the POST, fetched from the NAS instead of held on bishop.** It would tell us in advance whether the service accepts `offsite`, what section the row gets, and whether `/mesh` derives a host from it.

**Why I rejected it:**
- P3 learns all three within seconds.
- Every outcome the read would prevent is either harmless to hosts or undone by retiring the row.
- The one exception is a key reaching the feed, and the P2 payload check prevents that. A code read would not.

**What would change my mind:** if Sensei wants no chance at all of a brief `/mesh` break or a fleet-wide sync stall. Then the read comes first, at the cost of one NAS fetch and one reading.

## 8. Limits

- I have not read the registry code. The service facts in §3 are bishop's code-level verdicts at `e340e09`. The later deploys (`8b7f03e`, `f5a7c8b`) are reported to leave the served-record contract unchanged.
- Whether each host runs the script, and how often, is unmeasured. The check is designed so that it does not need to know.
- Two claims rest on general knowledge and were not tested here: that sshd skips lines it cannot parse, and that POSIX `read` drops an unterminated final line. francis-ngannou should confirm or refute both.

## 9. Commands

Run these after Sensei's yes. The §5 byte check may be read now. Run on Venom, in Git Bash, in the orchestrating session, with no elevation, from the session's scratch directory.

- **Capture.** Deliberately *without* `-f`, so both the error status and its body are kept. Repeat for each endpoint and each P-step, changing the file name:
  `curl -sS -o keys-p1a.txt -w '%{http_code}\n' 'http://192.168.2.3:8789/authorized_keys'`
- **Hash:** `sha256sum keys-p1a.txt`
- **Last byte:** `tail -c 1 keys-p1a.txt | od -An -c` prints `\n` when the feed ends in a newline.
- **Other reads:** the same capture for `'…/authorized_keys?exclude=venom'`, `'…/mesh'`, `'…/registry'` and `'…/journal?limit=5'`.
- **P2:** the precedent call from `BB-20260914-venom-001.001`, with P2's values.

```
WORK ORDER — v3: the claude-app pre-registration check, re-derived (design only; decision 6 stays held)
- Document: the session saves this note verbatim with save_verbatim.py, printing its SHA-256, to
  C:\Repo\townsquare\docs\townsquare-project-tracker-design-v3.md (branch internal, not pushed) —
  reviewed by francis-ngannou before Helio's CHECKPOINT. Brief: how §1–§2 read the script, the
  P1–P5 criteria and the P5 table; he raises his own concerns. He owns how the fleet's sync runs
  and stays up, and the claims here most likely to be wrong are about shell, curl and sshd behaviour.
- Coordinate: helio-gracie — no GAME PLAN (nothing is built). CHECKPOINT at two named handoffs:
  (1) v3, after francis's review; (2) B.6's result event after P4(a), before Sensei is told the
  registration held. GATEWAY: decision 6 goes to Sensei as one decision, with v3 in place of v2 §5,
  stating that a yes covers P1–P5 as written, including P5's retire, and nothing else in P5.
- Implement: none. After Sensei's yes, the orchestrating session on Venom runs P1–P5 in one sitting
  and owns every Request that P5 or §5 produces.
- Peer review: francis-ngannou, as above. No second round; any disagreement goes to Helio as an ESCALATE.
- QA: none — no code changes.
- Done when: (1) v3 is saved with its SHA-256; (2) francis's review is filed; (3) Helio's GATEWAY
  has put decision 6 to Sensei with v3; (4) no curl -fsS Request has been filed; (5) if Sensei says
  yes, P1 comes before the bulletin, P3 follows the POST at once, and B.6's result event carries
  P1, P3 and P4(a) and has been checkpointed.
- Watch for:
  (a) a baseline taken after the bulletin is contaminated — retake it or stop;
  (b) the payload's agent and pubkey — a wrong agent overwrites another row (recoverable from the
      journal's before-state); a pubkey reaches every syncing host and stays there;
  (c) the §5 finding — one read, filed only if live, never a gate;
  (d) bishop is outside the Dojo and offline — every Request to him is fire-and-forget; nothing here waits on him;
  (e) v2 §5 consumer items 5–11 are unchanged; this note does not reopen them.
```