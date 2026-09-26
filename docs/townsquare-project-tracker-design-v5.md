# TownSquare tracker v5: the offsite check amended on Helio's v4 re-check

Delivered 2026-09-26. (a) Hardens the P5 attribution gate to also compare the registry
projection's hash, not just the journal -- even though the legacy write path is confirmed
off on the current deployment, the gate shouldn't rest on a fact it can't observe on the
day, in code the Dojo doesn't own, especially given one historical case where 'reported
off' turned out wrong. (b) Closes P2's field list explicitly (status and annotation come
from precedent, not B.6's header, resolving the conflict Helio found). (c) Adopts all
three corrections for the record. Design only; decision 6 stays held. Pulled byte-for-byte
from the subagent transcript's SubagentHandback field, not retyped -- save_verbatim.py's
CLI reads only an end_turn text block, so it cannot extract this delivery shape; the hash
below was computed by hand, not printed by that tool.
<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=3c5d332575de792c41dacecd1a71a4271242d7a0d780af7df5152ad7c817233a source=C--Workspace/3db5d20b-df7f-42a6-b490-ed1667c0117d/subagents/agent-ac7b1f94525bf2275.jsonl:75 message=msg_011CfRmpmAj3xckfc2mSXTSQ -->
# TownSquare project tracker, v5: the `claude-app` pre-registration check, amended on Helio's v4 re-check

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** design only. Nothing registers and nothing executes. Decision 6 (register `claude-app` under `binding: offsite`) stays held for Sensei.

**Proposed path:** `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v5.md`, branch `internal`, not pushed. v4 stays as filed.

**What this is.** This note amends v4, `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v4.md` (sha256 `b7ef7361…` according to its extraction header; I did not re-hash it). It answers the three parts of Helio's escalation and nothing else.
- §4 is re-issued whole, because it is what Sensei's yes covers. It replaces v4 §4. Part C, change 7, lists what changed in it.
- Outside §4, each change replaces a named passage of v4 (part C).
- Everything else in v4 stands, and so does everything v4 left standing.

**Read this run:**
- v4, in full;
- Helio's re-check, `helio-v4-recheck-20260926.md`, in full;
- the session's prep, `session-v4-prep-20260926.md`, in full, including the addendum;
- the raw NAS output behind the addendum and behind (c)3, in the session transcript (lines 1330, 1360, 1868–1869 and 1872–1873);
- the precedent, `BB-20260914-venom-001.001`, lines 14–36, by search;
- B.6, in kano's review, lines 376–460;
- v3 line 105, by search;
- save_verbatim.py, line 242, by search.

**Labels:** as in v4, plus one.
- *measured*: I read it this run.
- *inferred*: reasoned from what I read, not executed.
- *reported-by X*: X's claim, which I did not check.
- *raw, read by me*: the session ran the command, and I read its raw output in the session transcript this run. I re-ran nothing.

**Shorthand.** v3's and v4's shorthand still holds. In addition:
- **The escalation:** Helio's "ESCALATE → ip-man (one question)" in `helio-v4-recheck-20260926.md`. **(a)–(c)** are its three parts.
- **The addendum:** the section "Addendum, after Helio's REWORK" in `session-v4-prep-20260926.md`.
- **The legacy path:** the Crier consumer's board-ingestion `db.upsert()` at `crier.py:303`.
- **The flag:** the consumer's `ingest_registrations` argument, which turns the legacy path on.
- **The gate:** P5's attribution rule for rows 2, 3 and 4. Its **journal half** is v4's rule. Its **projection half** is added here.
- **Day-of values:** values filled in on the day of the run, not before the GATEWAY.
- **Claim #N:** claim N in Helio's CHECKPOINT on v4.

**Recusal.** v2 §5, v3, v4 and this note are mine, and this note rules on a review of v4. If the offsite registration check, or any item here, is referred to the Tribunal, I am conflicted under rule 5 limb (ii) and will not sit.

## A. Rulings

**(a) The gate against the legacy path. Adopt Helio's proposal, modified, and reword the premise.**
- **What is true.**
  - The legacy path writes stable fields whenever it runs. It passes every known field it extracts from a board event, and nothing journals it [raw, read by me].
  - On the NAS's source as read, it never runs. The flag defaults to false, and `app.py` does not pass it [raw, read by me].
  - So v4's premise, "nothing but `/register` and `/retire` writes a stable field of an existing row", is true as read. But it holds by configuration, not by construction.
  - Helio made (a) conditional on line 303 writing stable fields. It does in the code, though not in the configuration as read, so I rule on (a) rather than let it drop.
- **Ruling.** Rows 2, 3 and 4 now also need the step's projection to match P1's. Otherwise, row 5 applies (§4, P5).
- **Why harden a gate whose premise holds today:**
  - The gate exists so that a retire does not fire when something other than our POST explains the change. Retiring `claude-app` cannot undo a change to another row.
  - v4's gate read only the journal, so it was sound only if every writer journals. One writer does not, and one default argument keeps it off.
  - The check cannot see that argument on the day, and it sits in bishop's code, outside the Dojo. The one counter-example on record, the blanking of venom's row, came after the ingestion change was reported deployed [reported-by session memory, v3 §3].
  - The projection half reads nothing new. P3 and P4(a) already take the projection.
  - It changes an outcome only when the journal is clean but another row still changed. In each such case, retiring `claude-app` would not undo that change.
  - Its one cost falls in the case v4 Part D already accepted: another row changes in the same minutes as a fault our POST caused. Row 5 then reports instead of retiring.
- **Modifications to Helio's wording:**
  1. The projection half compares the SHA-256 of the step's projection with P1's. The projection holds every row but `claude-app`'s, so this is the same test as "no row other than `claude-app`'s changed or appeared", stated so that it can be applied mechanically.
  2. It does not apply at P4(b). P4(b) takes no projection, and one taken days after P1 would carry every legitimate change since. That is why v4 starts P4(b)'s journal window at P4(a).
  3. The premise stays, reworded as "What the source shows", with its limits stated. The gate no longer rests on it.
- **Not added:** a P1 re-read of the flag, like P1's re-read of the `/retire` route. The gate no longer depends on the flag.
- **Not needed:** Helio's Next 1b, the `ingest_log` count. It measures how often the legacy path would fire, and the gate no longer depends on that either.
- **Knock-on changes:** v4 Part C change 4 and v4 Part D's premise change, as Helio foresaw (part C, changes 4–6). v4 item 2's open question is answered (part C, change 2).

**(b) P2's field sources. Adopt, as Helio proposed.**
- **The precedent governs.** It sent `status` and `annotation` from outside its own header (its lines 20–22), and the service kept both (its read-back, lines 26 and 28) [measured].
- **P2 now names every field and its source, and allows no other.** The wording "every other field taken from B.6's header" is gone.
  - It was wrong about `status` and `annotation`, as Helio found. B.6's header has neither [measured: kano review, lines 381–400].
  - It was also loose the other way: most of B.6's header lines are not registry fields.
  - A closed list matters because `/register` drops unknown fields without an error [raw, read by me]. A stray or misspelled field would show only after the write, at P3.
- **Why keep `status`:** the precedent sent it and the service kept it. Leaving it out would rely on a default nobody has read.
- **Why keep `annotation`:** it points the row at B.6, as the precedent's points at its `.000`. It is not a stable field.
- **Day-of values:** only the annotation's `<YYYYMMDD>` and `<NNN>`, from B.6's filed filename. On the day, the body is checked against the draft the GATEWAY carried, and any other difference stops the POST.
- **Additions for the day, within (b):**
  - `by` names the writer and is not stored in the row, so P3 does not look for it. The service flags the row as a cross-agent write by venom, as it flagged the precedent (its line 30). That is expected, and `flags` is not a payload field.
  - §4's list of what a yes covers now names the day-of values.

**(c) Corrections for the record. Adopt all three.** Each corrects my own text.
1. **Item 3's "`poll_once()` calls only `db.touch()`" was wrong.** `poll_once()` also holds the legacy path, which is off as read. Corrected by part C, change 3, and in the new text for v4 Part C change 4 (part C, change 4). Item 3's ruling stands: no Crier path calls the journal.
2. **"A Crier touch on a new author may create a stub row" was wrong.** `touch()` writes only when `get()` finds the row. The sentence is struck from item 2 (part C, change 1) and from §4, and the new-row clause stands on its other two reasons. P1's first stop rule is unchanged: a `crier:` stub can now only be a leftover from older code or the legacy path, and the rule still handles one.
3. **"[inferred: that route is unread]" was wrong.** The session read `/register` raw, and it calls `_publish_async()`, as `/retire` does [raw, read by me]. §4's Writes now says so.

## B. Evidence

Reported-by the session unless marked. The addendum describes these reads in prose. The raw output matches it.
- **`poll_once()`, `crier.py:250–312`** [raw, read by me: command at transcript line 1868, output at 1869]. It touches the author of every event that names one (line 274). A detected registration event writes only an `ingest_log` note. Then `if not self.ingest_registrations: continue` (line 286) skips the rest. That includes the legacy upsert at 303, which passes `at`, `writer` and every known field extracted from the event. The output ends mid-statement, in a `set_meta` call.
- **`CrierConsumer.__init__`, `crier.py:190–206`** [raw, read by me: command at 1872, output at 1873]. `ingest_registrations=False`. The comment calls the path deprecated by operator override on 2026-09-13, kept as "an opt-in flag (default OFF)".
- **`app.py:120–132`** [raw, read by me: 1873]. `_consumer = crier_mod.CrierConsumer(db, CRIER_URL, body_reader=None, poll_seconds=POLL_SECONDS)`.
- **`grep` for `ingest_registrations` or `INGEST_REG`, over `app.py` and `crier.py` only** [raw, read by me: 1873]. Four hits, all in `crier.py` (191, 204, 258, 286), and none in `app.py`.
- **`app.py`'s route list** [raw, read by me: 1330]. The POST routes are `/register`, `/retire/<name>` and `/poll`. `_poll_loop` and `_publish_loop` run in the background, and `_seed_if_empty` runs at start. `/registry` includes retired rows unless `retired=0`, while the feed and `/mesh` exclude them.
- **`/register` and `/retire`** [raw, read by me: 1360]. Each writes the row, calls `_journal.record`, then `_publish_async()`. `/register` keeps only record fields from the body, and reads `by` as the writer.
- **`touch()` and `upsert()`** [reported-by Helio, who matched the session's reading to the raw source]. On an existing row, a touch runs `UPDATE agents SET updated_at=?, last_seen=?, last_source=? WHERE agent=?`. On a missing row it does nothing.
- **The precedent**, `BB-20260914-venom-001.001` [measured]. Lines 20–22 read as the session quoted them. The read-back shows `status: active` (line 26), its annotation (line 28), and `flags: cross-agent-write-by:venom@2026-09-14T06:35:57Z` (line 30).
- **B.6's header**, kano review lines 381–400 [measured]. It has no `status` line and no `annotation` line.
- **`is_registration_event`** [reported-by session]. It matches an exact `cat` value or an exact filename token, and B.6's slug does not carry the token. The `cat` side is inferred, not measured. It changes nothing here, because a detection writes only an `ingest_log` note.
- **save_verbatim.py** [measured: line 242]. It still joins only `text` blocks.

## C. Changes to v4 outside §4

1. **v4 item 2, Modification 1, the bullet that begins "A Crier touch on a new author may create a stub row".** Strike it. [(c)2]
2. **v4 item 2, the bullet that begins "Whether the liveness loop changes `status` routinely".** Replace it with:
   "- **Whether the liveness loop changes `status` routinely: answered (v5).** Its touches write no stable field, `status` included. Its one other write path, the legacy upsert, is off on the source as read. P5's gate no longer rests on either (v5 §4, "What the source shows")." [(a)]
3. **v4 item 3, the sub-bullet that begins "Source:".** Replace it with:
   "- **Source:** no Crier write path calls the journal. `poll_once()` writes agent rows through `db.touch()` and, only when `ingest_registrations` is true, through the legacy `db.upsert()` at `crier.py:303` (v5 §4). The only `journal.record` calls are in `/register` and `/retire`." [(c)1]
4. **v4 part C, change 4** (v3 §3's journal bullet). Replace the text that change 4 quotes with:
   "- **The journal records every accepted `/register` and `/retire`, with its before-state, and nothing else.** Those two routes hold the registry's only `journal.record` calls [session read 1a, from the deployed source]. The Crier consumer never calls the journal. It writes agent rows through `db.touch()`, which changes no stable field, and through the legacy board-ingestion `db.upsert()` at `crier.py:303`, which is off on the NAS's source as read (§4) [session reads, 2026-09-26]. The live journal holds five entries, all `register` [1a]. bishop's F1 verdict of 2026-09-13 is consistent: it found touches logged in `ingest_log` [read for v4: `TS-20260913-cable-016.001`]. `GET /journal` therefore shows whether the POST created a row or overwrote one, and whether anyone else registered or retired in the window. It cannot show a write made any other way. That is why P3 compares the rows themselves, and why P5's gate reads the projection as well as the journal (§4)." [(a), (c)1]
5. **v4 part D, the bullet "After 1a, the Crier cannot supply that concurrent write."** Replace it with:
   "- Routine Crier activity cannot supply that concurrent write. Its touches are never journaled and write no stable field, so they trip neither half of the gate. Its one field-writing path is off on the source as read. If that path ran, the projection half would send the case to row 5, as the journal half does for a journaled write (v5 §4)." [(a)]
6. **v4 part D, "What would change my mind", its second sentence.** Replace it with:
   "The journal began on 2026-09-13 and has recorded five registrations since. It cannot count any made before it began, or any made through the legacy path (Helio's claim 33)." [(a)]
7. **v4 §4** is replaced by §4 below. It differs from v4 §4 only in these passages, and everything else is v4's text:
   - the heading, and the line on section references;
   - **Writes:** the paragraph on the registry's own audit record (c), and what a yes covers, which now names the day-of values (b);
   - **The projection:** the new-row clause gives two reasons, not three (c); a new bullet says a new row bars a retire (a); and `status`'s two sub-bullets say "write" where they said "touch" (a);
   - **"Assumption, checked before the GATEWAY"**, which is replaced by **"What the source shows"** (a);
   - **P2:** the check before sending (b);
   - **P5, Attribution:** it gains the projection half (a).
8. **v4's work order** is replaced by the one at the end of this note.

## 4. The revised check: five steps, P1–P5 (re-issued in v5; replaces v4 §4 whole)

Section references inside §4 are to v3's sections, as amended by v4's part C and v5's part C.

**Writes.** Every step is a read except the following writes, all made from Venom:
- filing B.6, between P1 and P2;
- P2's POST;
- the retire, under P5 rows 3 and 2 only;
- result events on B.6's thread: P4(a)'s, plus one more if P4(b) finds a difference;
- any Request to bishop that P5 or §5 files.

The registry also publishes its own audit record to the board after a register and after a retire. Both routes drain its audit outbox through `_publish_async()` [session reads of the NAS's source: 1d, and `/register` on 2026-09-26].

When decision 6 goes to Sensei, it should say what a yes covers:
- B.6, the POST and the retire, by the exact text the session writes out before the GATEWAY. That text names each day-of value and its source; for the POST, these are only the two values P2 names;
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
- A row that first appears after P1 is listed in the result event and is not a trigger, for two reasons:
  - a new row can change what hosts receive only through the feed or `/mesh`, and both are compared byte for byte;
  - a new row written through `/register` also shows in the journal, which P5 reads.
- A new row does bar a retire: P5's gate sends rows 2, 3 and 4 to row 5 whenever the projection differs from P1's.
- `status` stays in the projection.
  - A write that rewrites a row's status with the same value changes nothing here.
  - A write that changes the value can move a key into or out of the feed, because the feed excludes retired rows (bishop, F3). The check must stop on that.
- **What the source shows.** This is the NAS's source as read on 2026-09-26, not the running process.
  - A Crier touch writes no stable field. On an existing row it sets only `updated_at`, `last_seen` and `last_source`. On a missing row it writes nothing [session read of `db.py`; Helio matched it to the raw source].
  - In the lines read (`crier.py:250–312`, which end mid-statement), `poll_once()` has one other write to agent rows: the legacy board-ingestion `upsert()` at line 303. It writes every known field it extracts from a board event, and nothing journals it.
  - That write runs only when the consumer's `ingest_registrations` flag is true. The flag defaults to false (`crier.py:191`). `app.py` constructs the consumer without it (lines 128–129) and never names it [raw, read by me].
  - So, as read, nothing but `/register` and `/retire` writes a stable field of an existing row. That holds by configuration, not by construction. A code change, a restart onto different code, or another writer to the database would end it, and nothing the check reads shows the flag.
  - The one counter-example on record is the blanking of five of venom's stable fields on 2026-09-13, after the ingestion change was reported deployed [reported-by session memory, v3 §3]. Which code was running then is not established.
  - So P5's gate does not rest on this reading. It reads the projection as well as the journal. This reading explains only why neither should move on a clean run.

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
- Before sending, check the body against the draft the GATEWAY carried, pinned by its SHA-256. The draft is built the way the precedent, `BB-20260914-venom-001.001`, built its own (its lines 20–22). It holds these fields and no others:
  - `by`: `venom`. It names the writer and is not stored in the row, so P3 does not look for it. The service flags the row as a cross-agent write by venom, as it flagged the precedent's (its line 30). That is expected, and `flags` is not a payload field.
  - `agent`: exactly `claude-app`
  - `binding`: exactly `offsite`
  - `vendor`, `model`, `os`, `shell` and `role`: exactly as in B.6's header
  - `status`: `active`, from the precedent, not from B.6's header
  - `annotation`: the drafted text, formed as the precedent formed its own, not from B.6's header. Its only day-of values are `<YYYYMMDD>` and `<NNN>`, taken from B.6's filed filename.
  - `pubkey` and `host_address`: empty
  - no `section`. The precedent sent none, and the service set it. P3 records it.
- If the day's body differs from the draft anywhere except those two values, do not send it.
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
- **Attribution.** Rows 2, 3 and 4 apply only when both halves of this gate hold at the step being judged. Otherwise, row 5 applies.
  - **The journal half:** the journal window holds no write other than `claude-app`'s register.
    - The window runs from P1 to the step being judged.
    - At P4(b), the window runs from P4(a), and only entries for `claude-app` count. P4(b) may come days later and reads only `claude-app`'s row.
  - **The projection half:** the step's projection has the same SHA-256 as P1's, so no row other than `claude-app`'s has changed, gone missing or appeared.
    - It catches writes the journal cannot see, whatever made them ("What the source shows", above).
    - P4(b) takes no projection, so only the journal half applies there.
  - The Crier trips neither half. Its touches are never journaled (§3), and they write no stable field.
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

## D. The alternative I rejected, for (a)

**Option: keep the gate journal-only, and reword the premise to say it holds by configuration.** It is the smallest change to the text. On the source as read, it gives the same outcome as the projection half on every run.

**Why I rejected it:**
- It leaves the gate that decides a retire resting on a fact the check cannot observe on the day, in code the Dojo does not own.
- "Reported off" has already been wrong once: the one counter-example on record came after the ingestion change was reported deployed.
- The projection half reads nothing new. It changes an outcome only where retiring `claude-app` could not undo what changed.

**Also rejected: attributing new key material by matching it to the row whose `pubkey` carries it,** and retiring only when it belongs to no other row. That is more precise. But it adds a matching rule that has to be right on the day, and only for the two-fault case v4 Part D already accepted.

**What would change my mind:** evidence that other rows change routinely with no journal entry. The projection half would then send genuine `claude-app` faults to row 5, and the matching rule would be worth its cost. P1's paired projections would show that. The dry run's two projections, five minutes apart, matched [reported-by session; Helio re-derived both hashes].

## Files

- Amended by this note: `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v4.md`
- Proposed path for this note: `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v5.md`
- Ruled on:
  - `C:\Repo\townsquare\docs\helio-v4-recheck-20260926.md` (the escalation)
  - `C:\Repo\townsquare\docs\session-v4-prep-20260926.md` (the addendum)
- The raw NAS output, by line, in `C:\Users\terre\.claude\projects\C--Workspace\3db5d20b-df7f-42a6-b490-ed1667c0117d.jsonl`:
  - 1330: `app.py`'s docstring and route list
  - 1360: the `/register` and `/retire` routes
  - 1868–1869: `crier.py:250–312`, `poll_once()`, with its command
  - 1872–1873: `crier.py:190–206`, `app.py:120–132`, and the grep for the flag, with the command
- The precedent: `G:\My Drive\N3rd0m\TownSquare\Bulletin Board\BB-20260914-venom-001.001-CLOSED__by-venom__helio-gracie-registered-portable-row-verified-cross-agent-flag-expected.txt`, lines 14–36
- B.6: `C:\Repo\townsquare\docs\townsquare-project-tracker-kano-review.md`, lines 376–460
- The counter-example: `C:\Repo\townsquare\docs\townsquare-project-tracker-design-v3.md`, line 105
- `C:\Repo\Agentic\tools\save_verbatim\save_verbatim.py`, line 242

I only read. I wrote nothing and ran nothing.

```
WORK ORDER — v5: the claude-app pre-registration check, amended on Helio's v4 re-check (design only; decision 6 stays held)
- Document: the session saves this note the way it saved v4. It extracts it by hand from this
  SubagentHandback input, with its SHA-256 and the same header disclosure, because save_verbatim.py
  still joins only a message's text blocks (line 242, checked this run). Path:
  C:\Repo\townsquare\docs\townsquare-project-tracker-design-v5.md (branch internal, not pushed).
  v4 is not edited.
  Reviewed by: helio-gracie's re-check of what v5 changes (his Next 3). There is no francis round
  unless Helio finds a change beyond (a)-(c); if he does, francis-ngannou reviews that change alone.
  For that judgement, these are my additions inside the parts:
  (a) the SHA-256 form of the projection half; its exclusion at P4(b); the "What the source shows"
      wording, with "write" for "touch" in status's two sub-bullets; and the time base for the
      journal's five entries in v4 Part D;
  (b) the closed field list and the day-of check against the pinned draft; the note on `by` and the
      cross-agent flag; and the day-of values in what a yes covers.
- Coordinate: helio-gracie. No GAME PLAN, because nothing is built.
  His re-check covers only what v5 changes: part C, including change 7's list for §4.
  CHECKPOINT (2) is unchanged: B.6's result event after P4(a), before Sensei is told the
  registration held.
  GATEWAY: decision 6 goes to Sensei as one decision: v3 as amended by v4, with §4 as re-issued
  in v5, plus the exact texts. (a) needs no separate question to him, because the gate no longer
  rests on the flag.
- Implement: none. Before the GATEWAY, the session reads and drafts only, per Helio's Next 1c-1e:
  (i) P2 and the retire as exact curl commands, with P2's body in a file pinned by SHA-256. The
      body holds exactly v5 P2's fields, and names its two day-of values and their source;
  (ii) B.6 with Sensei's words spliced in by save_verbatim.py, re-pinned by hash, with its
       unfilled values listed;
  (iii) the projection script pinned: done in the prep doc (b536f664...), for Helio to confirm.
  Helio's Next 1b is not needed (part A, (a)).
  After Sensei's yes, the orchestrating session on Venom runs P1-P5 in one sitting and owns every
  Request that P5 or §5 produces.
- Peer review: as under Document.
- QA: none. No code changes.
- Done when:
  (1) v5 is saved with its SHA-256 beside v4, and v4 is unchanged;
  (2) Helio's re-check has confirmed that v5 §4 differs from v4 §4 only as part C, change 7 says,
      and has checked the rest of part C;
  (3) the session's Next 1c-1e are done, and P2's body file holds exactly v5 P2's fields;
  (4) Helio's GATEWAY has put decision 6 to Sensei with v3 as amended by v4, §4 as re-issued in
      v5, plus the exact texts;
  (5) if Sensei says yes: v4's Done-when (6) holds.
- Watch for:
  (a) the gate compares the projection's whole hash with P1's. P3's pass test compares only rows
      present at P1. They differ on a new row on purpose: a new row alone passes P3, but it bars
      a retire;
  (b) P4(b) takes no projection, so only the gate's journal half applies there;
  (c) the day's P2 body may differ from the pinned draft only in the two annotation values. The
      echoed row's section and cross-agent flag are expected, and neither is a payload field;
  (d) v4's Watch for (a)-(e) still stand.
```