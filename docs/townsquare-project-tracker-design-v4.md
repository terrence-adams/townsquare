# TownSquare tracker v4: the offsite check amended on Helio's CHECKPOINT (1)

Delivered 2026-09-26. Rules on all 8 items from Helio's checkpoint: adopts modified
versions of the P5 row-precedence fix and the row-5 projection instrument (items 1-2),
declines Helio's own proposed Crier-journal filtering rule as unnecessary -- 1a already
settles it, touches are never journaled, so v3 section 3 is rewritten to state that
premise directly (item 3) -- and adopts the remaining items (4, 5, 7, 8) largely as
francis proposed, with item 6 answered by the session's own /retire read. Re-issues
section 4 (the P1-P5 check) whole; everything else changes as a named replacement to a
v3 passage. One item left open before the GATEWAY: whether the registry's touch() ever
writes a stable field of an existing row -- the session reads its source before Helio's
re-run. Design only; decision 6 stays held. Extracted verbatim from the subagent
transcript, not retyped; save_verbatim.py's CLI reads only an end_turn text block, and
this agent's report was instead delivered as a SubagentHandback tool_use input field, so
this was pulled by hand from that same field.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=b7ef7361eca41c080352bf1741e37c9cc197fc731a90628fa9edd3341c32f2b8 source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-afb84e2cc7d8cf788.jsonl:80 message=msg_011CfRiHcC1iaSgPKVKcauvb -->
# TownSquare project tracker, v4: the `claude-app` pre-registration check, amended on Helio's CHECKPOINT (1)

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** design only. Nothing registers and nothing executes. Decision 6 (register `claude-app` under `binding: offsite`) stays held for Sensei.

**Proposed path:** `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v4.md`, branch `internal`, not pushed.

**What this is.** This note amends v3, `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v3.md` (sha256 `60c382d9…` according to its extraction header; I did not re-hash it). It rules on the eight items in Helio's CHECKPOINT (1). It changes only what those items require, plus the two optional wording points he offered.
- §4 is re-issued whole because it is what Sensei's yes covers. It replaces v3 §4.
- Outside §4, each change is given as a replacement for a named passage of v3 (part C).
- Everything else in v3 stands. So do v1, v2 outside what v3 replaced, and kano's review.

**Read this run:**
- v3;
- francis-ngannou's review;
- Helio's CHECKPOINT (1);
- the session's reads;
- bishop's verdicts in `TS-20260913-cable-016.001`;
- B.6's filename in kano's review;
- save_verbatim.py's source.

**Labels:** as in v3.
- *measured*: I read it this run.
- *inferred*: reasoned from what I read, not executed.
- *reported-by X*: X's claim, which I did not check.

**Shorthand.** v3's shorthand still holds. In addition:
- **CHECKPOINT (1):** Helio's checkpoint on v3, `helio-checkpoint-v3-20260926.md`. **Items 1–8** use his numbering from its closing question.
- **(a)–(i):** the items in francis-ngannou's review, `francis-ngannou-review-v3-20260926.md`, §5. **His feed-side fix** is the one in his §4.
- **1a–1f:** the session's six reads, in `session-reads-for-v3-checkpoint-20260926.md`. I did not re-run them, so each is reported-by the session.
- **The projection:** defined in §4.
- **The journal window:** defined in §4, P5.

**Recusal.** v2 §5 and v3 were mine, and this note rules on reviews of v3. If the offsite registration check, or any item here, is referred to the Tribunal, I am conflicted under rule 5 limb (ii) and will not sit.

## A. Rulings

**Item 1: which P5 row wins (francis (b)). Adopt, modified.**
- **One order for the whole table.** Rows are checked in the order 1, 3, 2, 5, 4, and the first row that holds decides. The table is printed in that order and keeps v3's row numbers.
- **The journal gate now covers rows 2, 3 and 4,** as francis worded it. Its window is now defined, including at P4(b).
- **Row 5's catch-all now reads "anything else no other row covers".** Under the new order, v3's wording, "not covered above", would have swallowed row 4.
- **A new after-retire rule** says what the retire's own journal entry means, what happens if the retire fails, and where anything left over goes.
- **Why modified:**
  - francis's fix settles row 4 against row 5 and nothing else. Once item 2 measures other rows, a clean journal can coincide with an unjournaled change to another row. Rows 2–3 then overlap row 5 as well.
  - Row 3 is checked first because it is the irreversible case.
  - The after-retire rule is needed because the retire is journaled (1d). Without it, the retire's own entry would read as "another write".
  - The window rule is needed because P4(b) can come days after P2. If row 4 were gated on "no other write since P1", any unrelated registration in between would send a P4(b) finding to row 5.
- **Unchanged:** the retire still fires only when the journal is clean, as Helio expected. Part D gives the alternative I rejected.

**Item 2: row 5's uninstrumented trigger (francis (a)). Adopt, modified.**
- **The projection (§4).** It covers every row except `claude-app`'s, with stable fields only and rows sorted by `agent` (francis (g)). It is kept as a file as well as a hash, so a report can name the row that changed.
  - It is taken twice at P1 and once each at P3 and P4(a), from the `/registry` reads those steps make. P1 now reads `/registry` twice, as it reads the feeds.
  - P1's two projections must match, just as the two feed captures must.
- **Modification 1: a row that appears after P1 is recorded, not treated as a trigger.**
  - A new row can change what hosts receive only through the feed or `/mesh`, and both are compared byte for byte.
  - A new row written through `/register` shows in the journal.
  - A Crier touch on a new author may create a stub row. That is routine, and counting it as a trigger would stop a clean run for nothing.
- **Modification 2: P4(a) now re-reads the journal.** Row 5 triggers on another write in the journal window, but v3's P4(a) never read the journal. That is the same gap item 2 names, so it gets the same fix.
- **`status` stays a stable field.**
  - A touch that rewrites a status with the same value changes nothing in the projection.
  - A touch that changes the value can move a key into or out of the feed, because the feed excludes retired rows (bishop, F3). The check must stop on that.
- **Whether the liveness loop changes `status` routinely,** I cannot settle from what I have read. The check assumes the loop writes no stable field of an existing row. The session reads the source of `touch` before the GATEWAY. If the assumption fails, this note comes back to me.

**Item 3: Crier journal entries against the attribution gate (Helio). Decline the rule, and state the premise instead.**
- 1a shows that touches are never journaled, from two directions:
  - **Source:** `poll_once()` calls only `db.touch()`, and the only `journal.record` calls are in `/register` and `/retire`.
  - **Live history:** the journal holds five entries, all `register`.
- bishop's F1 verdict of 2026-09-13 is consistent with this: it found touches logged in `ingest_log` [measured].
- The proposed rule would filter journal entries that cannot exist.
- v3 §3 now states which writes the journal records (part C, change 4). It also states the converse, which matters more: the journal cannot see a touch that changes a row. That is why item 2's projection is the instrument for row 5.

**Item 4: row 1's "Nothing was written" (francis (c)). Adopt.** Row 1 now confirms this from P3's `/registry` and `/journal` reads. If those reads show a write, the check continues down the table.

**Item 5: "Both feed captures" (francis (d)). Adopt.** It becomes a parenthetical in P3, with francis's reading.

**Item 6: is `/retire` journaled? (francis (e)). Answered by 1d: yes, through the same call as `/register`.** The only change is to use that fact:
- the after-retire rule expects the retire's journal entry;
- P1's undo line now carries 1d's call, and P1 re-reads the route, as v3 already required.

**Item 7: the feed-side fix (francis's §4 and (f)). Adopt the feed-side fix; decline (f) here.**
- The §5 Request now offers both fixes.
- Its trigger is unchanged: it is filed only if the feed lacks a trailing newline. 1b found that the feed has one, so nothing is filed today.
- (f), the atomic `sort` rewrite, is not added:
  - it is unrelated to this finding;
  - its window is milliseconds and it heals itself;
  - it stays recorded in francis's review for whoever next files on the script.

**Item 8: "Every step is a read except P2" (Helio). Adopt.** §4 now lists every write and says which ones Sensei's yes covers by exact text.

**Optional wording (francis's two §1 precisions). Adopt both,** in v3 §1 item 2 and v3 §2 (part C). Both correct my own text.

**No action:**
- (h) and (i), as Helio said.
- (g), which item 2 already uses.
- francis's §2 note on monitoring by exit code alone. It is outside this job and stays in his review.
- Helio's note on claim #16: a short break between two samples can still reach a host. I agree. The effect is bounded, so nothing changes.

## B. Evidence now in hand

Everything here is reported-by the session (1a–1f) or by francis-ngannou. I re-ran none of it.
- **1a:** Crier touches are not journaled. This settles item 3.
- **1b:** the feed ends in `\n`. §5's defect is latent today, and nothing is filed.
- **1c:** the NAS copy of the script hashes to `6659ac356cb8c12a4898adae8e864ea926e1d3054125b622beeb33a420df9e3b`. Helio computed the same hash for the fetched copy and matched it line for line to the reference file. This supplies the hash value he found missing (his claim 4).
- **1d:** the undo call is `POST /retire/<name>`, with no body. It is journaled like a register, and the route then drains the registry's audit outbox to the board. This settles item 6.
- **1e:** Sensei's words in v3 §3 match `BB-20260913-cable-003.000`, line 19, character for character. This closes Helio's claim 23.
- **1f:** no Request proposes changing the script's curl flags. v3 §1 item 6 holds, and v3's Done-when (4) is met.
- **francis-ngannou:**
  - He measured two claims directly: that `read` drops an unterminated last line, and that the script fails closed.
  - He confirmed the sshd claim from expertise, not by test. That answers v3 §8's last bullet.
  - Helio made two corrections to his report, for the record. First, `$TMP` does exist, because line 26 runs `mktemp` before curl. Second, francis's hash change reflected changed content. Neither correction changes v3 or v4.

## C. Changes to v3 outside §4

1. **v3 §1 item 2, third bullet.** Replace it with:
   "- The body goes to a temp file, never to `authorized_keys`, so a broken feed adds nothing to `authorized_keys` and removes nothing from it, on any host that runs the script. On a new host's first run, lines 20–21 create an empty `authorized_keys` before curl runs, whatever curl then does; that is harmless (francis-ngannou's review, §1)."
2. **v3 §2, the paragraph that begins "The error message is misleading".** Replace it with:
   "**The script's own error message is misleading; curl's is not.** Every curl failure makes the script log "registry unreachable", including an HTTP 500 from a reachable registry. But `-S` makes curl print its own line just before that, and curl's line names the failure: `curl: (22) The requested URL returned error: 500` in francis-ngannou's loopback test [measured by him; Helio found the line in his raw output]. When diagnosing a stall, read curl's line, not the script's."
3. **v3 §3, the sub-bullet that begins "So a re-read after the Crier has polled".** Replace its second sentence with:
   "Its targets are `claude-app`'s row and every other row's stable fields (the projection, §4), venom's among them; not the slug."
4. **v3 §3, the bullet that begins "The journal records every accepted write".** Replace it with:
   "- **The journal records every accepted `/register` and `/retire`, with its before-state, and nothing else.** Those two routes hold the registry's only `journal.record` calls, and the Crier consumer's `poll_once()` calls `db.touch()`, never the journal [session read 1a, from the deployed source]. The live journal holds five entries, all `register` [1a]. bishop's F1 verdict of 2026-09-13 is consistent: it found touches logged in `ingest_log` [measured: `TS-20260913-cable-016.001`]. `GET /journal` therefore shows whether the POST created a row or overwrote one, and whether anyone else registered or retired in the window. It cannot show a Crier touch, whatever the touch changes. That is why P3 compares the rows themselves (the projection, §4)."
5. **v3 §5, first bullet.** Replace its last sentence with:
   "The session files one Request to bishop, naming the key and offering two fixes, either sufficient alone: the loop guard `while IFS= read -r key || [ -n "$key" ]`, which protects each host once it runs the corrected script; and serving the feed so that it always ends in a newline, which protects every host at once, whatever it runs (francis-ngannou's review, §4)."
6. **v3 §5, after the second bullet.** Add:
   "- **Measured 2026-09-26:** the feed ends in a newline [session read 1b], so nothing is filed today. P1 reads the byte again on the day."
7. **v3's work order** is replaced by the one at the end of this note.

## 4. The revised check: five steps, P1–P5 (re-issued; replaces v3 §4 whole)

Section references inside §4 are to v3's sections, as amended in part C.

**Writes.** Every step is a read except the following writes, all made from Venom:
- filing B.6, between P1 and P2;
- P2's POST;
- the retire, under P5 rows 3 and 2 only;
- result events on B.6's thread: P4(a)'s, plus one more if P4(b) finds a difference;
- any Request to bishop that P5 or §5 files.

The registry also publishes its own audit record to the board after a retire (session read 1d: the route drains its audit outbox through `_publish_async()`). It probably does the same after a register [inferred: that route is unread].

When decision 6 goes to Sensei, it should say what a yes covers:
- B.6, the POST and the retire, by the exact text the session writes out before the GATEWAY;
- the result events and any Request, in the shape this note gives them.

Anything else P5 might need goes back to him.

**P0 — withdrawn.**
- It gated the POST on reading the service code, and its fallback held the POST on a Request to bishop.
- Its purpose was to learn in advance whether retiring would repair a broken feed. bishop's verdict answers that for the feed. The script makes a broken feed harmless to hosts, and P3 sees the rest within seconds.
- Its fallback also made a Dojo step wait on a non-Dojo host that is offline.
- The code read survives only as P5's last resort.

**The projection.** Build it from one `/registry` response:
1. Take every row except `claude-app`'s.
2. Keep only the stable fields, in the order the shorthand lists them.
3. Sort the rows by `agent` and save them one row per line.
4. Keep the file as well as its SHA-256, so that a diff can name the row that changed.

How it is compared:
- A row present at P1 is compared field by field. A row missing later counts as changed.
- A row that first appears after P1 is listed in the result event and is not a trigger, for three reasons:
  - a new row can change what hosts receive only through the feed or `/mesh`, and both are compared byte for byte;
  - a new row written through `/register` also shows in the journal, which P5 reads;
  - a Crier touch on a new author may create a stub row, and P1's first stop rule already allows for one.
- `status` stays in the projection.
  - A touch that rewrites a row's status with the same value changes nothing here.
  - A touch that changes the value can move a key into or out of the feed, because the feed excludes retired rows (bishop, F3). The check must stop on that.
- **Assumption, checked before the GATEWAY:** nothing but `/register` and `/retire` writes a stable field of an existing row. In particular, a Crier touch writes none.
  - The one counter-example on record is the blanking of venom's row on 2026-09-13 [reported-by session memory]. That is why v3 watched venom's row.
  - The session reads the source of `touch` in the NAS's `registry/db.py`. If it writes any stable field of an existing row, this note comes back to me before the GATEWAY.

**P1 — baseline.** Reads only. Take it in the same sitting as filing B.6, immediately before filing it.
- `GET /authorized_keys` and `GET /authorized_keys?exclude=venom`: record status, SHA-256, line count, and whether the last byte is a newline. Take each twice, about a minute apart.
- `GET /mesh`: status and SHA-256, twice.
- `GET /registry`, twice, with the feed captures: any `claude-app` row, and the projection.
- `GET /journal?limit=5`: the newest entry.
- **Have the undo ready.** The call is `POST http://192.168.2.3:8789/retire/claude-app`, with no body.
  - It answers 200 with `{"ok": true, "agent": <row>}`, or 404 if there is no such row.
  - It is journaled like a register [session read 1d, from the deployed route].
  - At P1, re-read the route on the NAS. If it no longer matches 1d, stop: the yes covered 1d's call.
- **Stop rules:**
  - If a `claude-app` row exists and its `last_source` is not a `crier:` stub, stop and report. Do not overwrite it.
  - If the two feed captures differ, stop and retake later. P3 cannot work against an unstable feed, and a feed that changes with no journal entry is itself a finding.
  - If the two projections differ, stop and retake later, for the same reasons.
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
- Both feed captures are byte-identical to P1, with the same status. (That means the two feed endpoints, `/authorized_keys` and `/authorized_keys?exclude=venom`. Each is compared with its own P1 capture, which P1's stop rule has shown to be stable.)
- `/mesh` has the same status and is byte-identical to P1, or identical on the lines that stayed the same.
- The projection matches P1's on every row present at P1. That includes venom's row, which the Crier touches when B.6 is filed.

**P4 — settled comparison.** Reads.
- **(a)** At least 10 minutes after P2 (v2 cited this as the TSD §9 worst-case Crier latency):
  - Repeat P3's comparisons of the journal, the feed, `/mesh` and the projection, and re-read `claude-app`'s stable fields.
  - Then venom appends B.6's result event. It carries:
    - P1's, P3's and P4's hashes and outcomes, including the projections';
    - the section;
    - the journal entries since P1;
    - any row that has appeared since P1.
- **(b)** Once, the first time venom acts on a `claude-app` post that follows the card: re-read `claude-app`'s stable fields. That is the first time the liveness loop meets an offsite author.

**P5 — response.**
- **Order.** Check the rows from the top of the table down. The first row whose observation holds decides the response. No later row applies, except as the after-retire rule says.
  - The rows keep v3's numbers, so they are printed in the order 1, 3, 2, 5, 4.
  - Row 3, the irreversible case, is checked before row 2. Both retire.
  - Row 5 is checked before row 4, because a row may be kept only when nothing else is unexplained.
- **Attribution.** Rows 2, 3 and 4 apply only when the journal window holds no write other than `claude-app`'s register. Otherwise, row 5 applies.
  - The window runs from P1 to the step being judged.
  - At P4(b), the window runs from P4(a), and only entries for `claude-app` count. P4(b) may come days later and reads only `claude-app`'s row.
  - The Crier cannot trip this gate, because its touches are never journaled (§3).
- **After a retire** (rows 3 and 2). Re-capture everything P3 reads.
  - The retire's own journal entry and `claude-app`'s retired row are expected.
  - If the retire does not return 200 with `ok: true`, row 5 applies at once.
  - Nothing more is written to the registry, and the retire is never repeated.
  - If everything else matches P1, record it as the row says. After a row-3 retire, report through Helio in every case, because hosts may already hold the key.
  - Anything that still differs from P1 was not undone by the retire:
    - new key material still in the feed goes to row 5, and the report says that hosts may be syncing it;
    - any other change still showing in an endpoint or the feed takes row 2's "If not" branch;
    - anything else goes to row 5.

| # | Observation | Response |
|---|---|---|
| 1 | The POST is rejected (4xx) | Confirm from P3's reads that nothing was written: no journal entry for `claude-app` newer than P1's, and `claude-app`'s row as P1 recorded it, or still absent. Then stop and report: registration needs a service change, which is bishop's code (a Request, not a dependency). The card can run unregistered meanwhile; C3 flags each post. If the reads show a write, go on down the table. |
| 3 | The feed carries key material that was absent at P1 | Retire at once. This removes it from the feed only; hosts that already synced it keep it (A19). Removing it from each host is a live change and needs Sensei's go. |
| 2 | An endpoint's status changed, or the feed's bytes changed with no new key material | Retire `claude-app` at once and re-capture. If restored: record it, and file a Request to bishop. If not: sync is stalled or `/mesh` is broken, and no host is harmed. The session fetches the deployed route from the NAS, jackie-chan reads it (it is a query question), and it goes to Sensei. |
| 5 | Another write appears in the journal window, another row's stable fields changed (the projection), or anything else no other row covers | Stop and do nothing further. Report through Helio with the captures and the journal entries. Restoring any other row is a registry write and needs Sensei's go. |
| 4 | Only `/mesh` content, or `claude-app`'s section or stable fields, differ | Keep the row. Record the difference in the result event, and file a Request to bishop. |

## D. The alternative I rejected

**Option: let rows 2 and 3 retire whatever the journal shows.** Retiring `claude-app` undoes only our own write, and it is the one lever against a key spreading.

**Why I rejected it:**
- The likeliest concurrent write that adds key material is another agent's own registration. The retire would not undo it, and it would leave `claude-app` retired and waiting on a new yes.
- The case the option protects against needs two things at once: a concurrent write, and a service bug that ships a key for a row that has none.
- After 1a, the Crier cannot supply that concurrent write.
- Row 5 still reports at once.

**What would change my mind:** registrations frequent enough that one is likely to land inside the check's window. In its whole history, the journal holds five entries.

## Files

- Amended by this note: `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v3.md`
- Proposed path for this note: `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v4.md`
- Reviews and reads ruled on:
  - `C:\Repo\townsquare\docs\francis-ngannou-review-v3-20260926.md`
  - `C:\Repo\townsquare\docs\helio-checkpoint-v3-20260926.md`
  - `C:\Repo\townsquare\docs\session-reads-for-v3-checkpoint-20260926.md`
- bishop's F1 and F3 verdicts, read this run: `G:\My Drive\N3rd0m\TownSquare\Requests\TS-20260913-cable-016.001-RESOLVED__by-bishop__wonderland-review-verdicts-with-evidence.txt`
- B.6's filename, which shows it is filed `from-venom`, so the Crier touches venom and not `claude-app`: `C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md`, §B.6.
- `C:\Repo\Agentic\tools\save_verbatim\save_verbatim.py`, lines 45–56 and 189–239. It saves only the `text` blocks of one assistant message, so it cannot extract a report delivered as a SubagentHandback input.

I only read. I wrote nothing and ran nothing.

```
WORK ORDER — v4: the claude-app pre-registration check, amended on CHECKPOINT (1) (design only; decision 6 stays held)
- Document: the session saves this note the way it saved v3. It extracts it by hand from this
  SubagentHandback input, with its SHA-256 and the same header disclosure, because save_verbatim.py
  joins only a message's text blocks (checked in its source this run). Path:
  C:\Repo\townsquare\docs\townsquare-project-tracker-design-v4.md (branch internal, not pushed).
  Reviewed by: francis-ngannou's review of v3, whose proposals this note adopts, and then Helio's re-run
  below. There is no second francis round unless Helio finds a change beyond items 1–8; if he does,
  francis reviews that change alone. For that judgement, these are my additions inside the items:
  the check order, the journal window and the after-retire rule (item 1); the new-row clause, the
  journal read at P4(a) and the touch read (item 2).
- Coordinate: helio-gracie. No GAME PLAN, because nothing is built.
  CHECKPOINT (1) is re-run on what v4 changes, together with the raw touch source.
  CHECKPOINT (2) is unchanged: B.6's result event after P4(a), before Sensei is told the registration held.
  GATEWAY: decision 6 goes to Sensei as one decision, with v3 as amended by v4 in place of v2 §5. It
  states that a yes covers the writes §4 lists (B.6, the POST and the retire by their exact text)
  and nothing else in P5.
- Implement: none. Before the GATEWAY, the session makes reads only:
  (i) it pastes the source of the registry's touch (the NAS's registry/db.py), raw, for Helio's re-run;
  (ii) following Helio's Next 4, it writes out the exact P2 POST, the retire call from 1d, and B.6's
       text pinned by hash;
  (iii) it writes the projection command and runs it twice against the live /registry, a few minutes
        apart, recording both hashes.
  After Sensei's yes, the orchestrating session on Venom runs P1–P5 in one sitting and owns every
  Request that P5 or §5 produces.
- Peer review: as under Document.
- QA: none. No code changes.
- Done when:
  (1) v4 is saved with its SHA-256;
  (2) Helio's re-run has checked v4's changes and the raw touch source;
  (3) touch writes no stable field of an existing row, or v4 has come back to me;
  (4) the two projection dry-run hashes match, or the difference has come back to me;
  (5) Helio's GATEWAY has put decision 6 to Sensei with v3 as amended by v4, plus the exact texts;
  (6) if Sensei says yes: P1 comes before the bulletin ("A new agent posts to the bulletin board with
      its information. Then registers itself and its ssh key."), P3 follows the POST at once, and
      B.6's result event carries P1, P3 and P4(a), including the projections, and has been checkpointed.
- Watch for:
  (a) the table is printed in check order (1, 3, 2, 5, 4). Anyone who applies it by row number will
      keep a row that row 5 should stop on;
  (b) a projection that will not hold still at P1 is a stop. Do not filter it out as noise on the day;
  (c) Sensei's yes covers one retire. It is never repeated, and no further registry write happens
      without Sensei;
  (d) P4(b) can come days after P2, so its journal window starts at P4(a). A window from P1 would
      send it to row 5 whenever anyone else had registered since;
  (e) carried over from v3:
      - a baseline taken after the bulletin is contaminated;
      - check the payload's agent and pubkey;
      - bishop is outside the Dojo and offline, so every Request to him is fire-and-forget;
      - v2 §5 items 5–11 are not reopened.
```
