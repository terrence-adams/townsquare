<!-- extracted (not save_verbatim.py: SubagentHandback delivers its report as a tool_use input field, not an end_turn text block, which that tool's CLI does not read) sha256=64f14c4de4ca41548b41a21bc43081d73f2062e161c88e370308441007db0607 source=C--Workspace/6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb/subagents/agent-afe32c973b4c7192d.jsonl:517 message=msg_011CfSi5pv9mceJwwmCGrF1d -->
# Registry `binding: offsite`: Addendum 1, rulings on francis-ngannou's Prepare flags

**Author:** ip-man (Claude) · **Date:** 2026-09-26 · **Status:** design only. This addendum builds, copies and deploys nothing, and I only read.
**Amends:** `C:\Repo\townsquare\docs\ip-man-registry-offsite-binding-design-20260926.md` (SHA-256 `3f86d159…`, per its header). The note itself is not edited.
**Proposed path:** `C:\Repo\townsquare\docs\ip-man-registry-offsite-addendum-1-20260926.md`, on branch `internal`, not pushed.
**Recusal:** the note's recusal carries over to this addendum.

**New sources.** Labels are as in the note.
- **TF** is francis-ngannou's transcript: `C:\Users\terre\.claude\projects\C--Workspace\6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb\subagents\agent-a82d386d7fbbc6541.jsonl`. It holds three files in full, raw:
  - line 87: `app.py` (342 lines);
  - line 109: `registry/render.py` (86 lines);
  - line 114: `registry/schema.py` (150 lines).

  All three are at `ede80e1`, which francis matched to the NAS by hash.
- **TH** is Helio's CHECKPOINT on the note: `…\6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb\subagents\agent-ac1e7ce555e58c194.jsonl`, line 163. His flags there are **F1–F8**.
- francis's report is `C:\Repo\townsquare\docs\francis-ngannou-registry-deploy-prep-20260926.md` (commit `dc32913`).

**Why one addendum now.** Helio paced my ruling to come after gsp's review, because F2 depended on code nobody had read yet (TH:163). francis's reads have since put all of `app.py`, `schema.py` and `render.py` on record. That means the questions that were waiting on the code can be settled now. jackie-chan and gsp then review the note and this addendum together, so they review the design as it will actually be built. Anything they raise still comes to me once, after gsp, as Helio's Next 6 says.

## 1. francis's three flags

### Flag 1: branch from `ede80e1`

This corrects which commit to branch from; the instruction itself stands.
- §5's rule was "the commit that matches the NAS byte for byte". `f5a7c8b` was bishop's report, and the note labelled it as such.
- francis measured all 8 files as equal at `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf`. That commit is also the tip of `main` and of `origin/main`.

What follows from that:
- The branch `offsite-binding` is cut from `ede80e1`. The townsquare fallback is not used.
- The branch will be ahead of `main` by only this job's commits. bishop's merge is therefore a fast-forward, unless `main` moves in the meantime. The board note can say so.
- `terrence-adams/Wonderland` is private [reported-by francis, from `gh repo list`], so pushing a branch there publishes nothing outside.
- The working copy must be durable, not in a scratchpad. It will be a sparse checkout of `services/registry` at `C:\Repo\Wonderland`.
  - A full checkout hit Windows path-length limits on an unrelated `services/townwatcher` fixture [reported-by francis].
  - ronda makes the checkout as the first step of Implement (1). She checks all 8 files against francis's D5 hashes before writing any test.

### Flag 2: yes, R6 needs `render.py`

What the code does today [measured, TF:109 and TF:87]:
- `render_tables(host_rows, portable_rows)` renders exactly two tables.
- `/registry?format=md` (app.py 159–163) and `/tables` (228–231) each build exactly two lists, by section.
- An offsite row falls into neither list, so it disappears from both endpoints.

**R6, amended:**
- `render.py`: `render_tables(host_rows, portable_rows, offsite_rows=None)`, with the new argument as a trailing keyword.
  - When `offsite_rows` holds rows, append `"\n### Offsite agents\n\n" + _table(offsite_rows) + "\n"` after the portable table.
  - When it is `None` or empty, the output is byte-identical to today's.
  - Extend the docstring to say so.
- `app.py`: each of the two call sites adds `off = [r for r in rows if r["section"] == "offsite"]` and passes `offsite_rows=off`. It selects by section, like the two lists beside it.

**Why the heading is unnumbered.** The service's tables mirror the document's §2.1 and §2.2, and the document's §2.3 is already Hosts.
- Numbering an offsite section is the document's decision, at kano's reissue (Queue 3).
- The Forge ruling quoted in `render_tables`' docstring points the same way: the service generates the facts, not the document.

**Why the section appears only when it has rows.** Both endpoints then stay byte-identical on today's data, and after the deploy until claude-app registers. That lets T8 compare the markdown output too.

**`render_snapshot` stays unchanged.** `app.py` never calls it: no `/snapshot` route exists, even though the module docstring (lines 22–24) still lists one. How the versioned document shows offsite agents belongs to the reissue. So does `parse_md`. It would need the new heading only if an empty DB were ever re-seeded from a document that contains one.

**Rejected alternatives:**
- Folding offsite rows into the portable table. That misfiles them, which R6 forbids.
- Leaving them dropped. The facts the service generates would then omit a registered agent.

### Flag 3: R7 is withdrawn, and the deploy proof moves to `/health`'s `build`

**bishop's own code settles it.** The docstring of `_build_id()` (app.py 65–70, TF:87) reads: "db version is the DATA schema, not the code; there was no way to ask the service which commit it runs … Deployers should set one of the first two so /health answers it." The first two are the `REG_BUILD` environment variable and a `BUILD` file.

**The version number records data lineage, not code:**
- `_seed_if_empty` sets it from the seed document's filename (app.py 117–120).
- `render.py`'s `bump_minor` and `snapshot_filename` tie it to document issuance (TF:109).
- The Drive document is at v1.6, and a v1.3 already sits in `Archive/` [measured]. A service version of "1.3" would claim an issuance that never happened.
- For the same reason I reject bumping it through a startup migration, or by hand-editing the `meta` table. Both write live data in order to say something about code.

**`build` already does the job R7 was meant to do.**
- `_BUILD = _build_id()` runs once, when the module is imported (app.py 93).
- So a new value in `/health` shows that the serving process started after the `BUILD` file was written.
- D1 established that the image holds no code; the bind mount supplies all of it. Together, the two facts show that the running process imported the files copied before it started.

**Consequences:**
- bruce writes no version code.
- The runbook writes `BUILD` = the fix commit's short SHA. It does this after the three files are copied and hash-checked in place, and before the restart. Rollback writes `ede80e1`.
- Step 6 and Done-when (5) expect:
  - `build` = the fix commit's short SHA;
  - `version` = "1.2", unchanged;
  - `agents` unchanged from step 2's read (25 when francis read it).
- In §7's follow-on, the second send's P1 checks `build`, not "1.3".

## 2. What the code now on record changes

### A partial `/register` is not a merge

`normalize_record` fills in defaults for every field the body omits (schema.py 105–118, TF:114):
- `binding`, `vendor`, `model`, `os`, `shell` and `role` become `unknown`;
- `status` becomes `active`;
- `annotation` becomes empty;
- `section` is derived from `binding`, and falls back to `host_bound` when nothing derives.

So a partial `/register` re-binds the row to `unknown`/`host_bound` and blanks its identity fields. `pubkey` and `host_address` are the only fields it leaves alone when they are absent.

This is the same kind of fault as the blanking of venom's row on 2026-09-13. It also explains bishop's row, which reads `binding: unknown`, `section: host_bound`.

### That breaks R3 as I placed it

The note put R3 after `normalize_record`. Take the body `{agent: claude-app, pubkey: K}`, which carries no binding:
1. normalize turns the missing binding into an explicit `binding: unknown`, so R3 sees no offsite row and passes;
2. upsert re-binds claude-app to `unknown`/`host_bound` and stores K;
3. the feed publishes K, because it filters on nothing except active status and a non-empty key (app.py 240–247; see U5 below);
4. R4 cannot catch it, because the binding is no longer offsite.

So the naive fix's second path was real, and the R3 I placed did not close it. That is my error. The code puts it beyond doubt.

### R3, restated (replaces the note's R3)

R3 becomes one pure function in `schema.py`. It checks the **raw body, before `normalize_record`**, against the existing row.

**Where it runs:** in `/register`, after `validate_record` passes (app.py 183–185) and before `normalize_record` (186):

```python
existing = db.get(str(rec["agent"]).strip())
errors = schema_mod.offsite_violations(existing, rec)
if errors:
    return jsonify({"ok": False, "errors": errors}), 400
```

`db.get` strips the name exactly as upsert does (db.py; raw at T3:1593 and T3:1597). R3 therefore sees the row the write will land on.

**R3a: a body that binds a row offsite carries no host properties.**
- This applies when the body's stripped `binding` is `offsite`.
- For each of `pubkey` and `host_address`, the value that will be stored must be empty after stripping.
- That stored value is the body's, if the body carries the field and it is not `None`. Otherwise it is the existing row's.
- So it also catches a keyed host row being converted to offsite without clearing its key (T5).

**R3b: an offsite row is never re-bound silently.**
- If the existing row's stripped `binding` is `offsite`, and the body carries no non-empty `binding`, reject with: "agent '<name>' is bound offsite: send binding explicitly".
- A body that states a binding (`host:X`, `portable` or `unknown`) is a deliberate re-bind. That is allowed under D34, as it is today (S5).

**What R3 guarantees through `/register`:**
- an offsite row stays offsite until a body re-binds it explicitly;
- while it is offsite, it holds no key and no address.

### S2 and S3, corrected

- **S2** now holds on the code as read. R3a and R3b close all three of Q3's paths through `/register`, including the one that normalize opened.
- **S3's list of other writers** gains `_seed_if_empty` (Helio's F8). It seeds only an empty DB, from a v1.2 document that has no offsite rows.
- **The deprecated legacy path.** If it is switched on, it can still re-bind any row through normalize's defaults.
  - It cannot write a key, because `_KNOWN` excludes it (inferred; U10).
  - Where it re-binds a keyed row *to* offsite, R4 keeps that key out of the feed.
  - The path is off by default (crier.py 190–206), and it stays a residual.
- **A remaining race, under LAN trust.** Two concurrent writes to a new name can both pass R3 before either lands: one binding the row offsite, the other carrying a key but no binding. If the keyed write lands last, normalize re-binds the row to `unknown` and the key is published. This is S5's "any writer can re-bind any row", reached by timing. It is a residual.

### R4 stays, and it carries weight

U5 is now settled: the feed publishes every active row's non-empty `pubkey`, with no filter on section or binding (app.py 240–247, TF:87).
- Without R4, a keyed row converted to offsite by the legacy path, or by a direct DB edit, would be published.
- S5's portable half is live today: any portable row that carried a key would be published. No such row exists (P1).
- gsp's default-deny call still changes no byte on P1's data. Default-deny means section `host_bound` *and* binding not `offsite`. It would now close a path that is open today.
  - My lean is still to adopt it, but the call is his.
  - Reconciling it with Helio's F8: if gsp adopts it, it sits inside this order as R4's rule, and Watch-for (j) narrows to the rest of S5.

### R5 is withdrawn as a code change

- `/mesh` already lists only rows where `section == "host_bound"` (app.py 256).
- With R2 and R3b in place, every offsite row the API can produce has `section: offsite`.
- Only a direct DB edit or the legacy path could put an offsite row on `/mesh`, and it would carry no key.
- T7 stays, as a regression check.

### The remaining U items, settled by the code on record

jackie-chan confirms each of these from the checkout.
- **U1:** `derive_section` returns `""` for anything other than `portable` and `host:…` (schema.py 53–62). R2 adds `offsite` → `offsite`.
- **U2:** normalize derives the section through `derive_section`; its own comment at line 115 says "binding is authoritative". So R2 alone stores `section: offsite`, and `normalize_record` needs no change. normalize does not strip `agent`; `db.get` and upsert do.
- **U3:** `RECORD_FIELDS` includes `pubkey` and `host_address` (schema.py 43–44). A `pubkey` of `unknown` fails `PUBKEY_RE`. `host_address` has no format check.
- **U5 and U6:** as above.
- **U7:** see flag 2.
- **U8:** seeding runs only when `db.count() == 0` and the seed file exists (app.py 110–125).
- **U9:** see flag 3.
- **U13:** `/health` has no per-section counts (app.py 132–150), so nothing there needs to change.

**Helio's F2 does not arise.**
- Validation strips `agent` before matching it (schema.py 76–77), and `db.get` and upsert both strip.
- The journal does record the name unstripped (app.py 201). That is cosmetic and pre-existing, and it goes to bishop's thread.
- T4's adversarial names stay in the tests.

**F8's route question is settled.** `app.py` is on record in full and registers no blueprint. The routes are the ones it declares.

**Still open for jackie-chan:**
- U4. francis measured plain `TEXT` columns and no `CHECK`; the sign-off is jackie's.
- U10, U11 and U12.
- F3, the recency guard. It errs safe for R3, because a stale write changes no field.

**Still for gsp:**
- S1–S5 as corrected here;
- the default-deny call;
- F1, F6 and F7;
- the secrets exclusion.

## 3. Test changes to §4

**T4, replaced.** After T1, `{agent: claude-app, pubkey: <valid>}` → 400 (R3b). The row, the journal and the feed are all unchanged.
- **T4b:** `{agent: claude-app, role: "x"}` → 400 (R3b). The row is not re-bound to `unknown`.
- **T4c (F4):** `{agent: claude-app, section: host_bound}` → 400 (R3b). The row is unchanged.
- **T4d:** T4 repeated with the names `"claude-app\n"` and `" claude-app "` → 400 each time.

**T5** is unchanged. It now exercises R3a's existing-row branch.

**T7:** after T1, `/mesh` does not list claude-app. This rests on the existing whitelist plus R2; there is no R5 code.

**T11, replaced:**
- With an offsite row present, `/tables` and `/registry?format=md` show it under `### Offsite agents`, after the portable table, and in neither of the other two tables.
- `?section=offsite&format=md` shows the row under `### Offsite agents`, with the other two tables empty, as `?section=` already renders them today.
- With no offsite row present, both outputs are byte-identical to the baseline's.
- `/health` returns 200.

**T12, the isolation list** (Helio's F5). Every run sets all of the following:
- `REG_DB=<tmp>/registry.db`, `REG_JOURNAL=<tmp>/journal.log` and `REG_OUTBOX=<tmp>/outbox`;
- `REG_SEED_MD` pointing at a path that does not exist, so nothing is seeded, unless a test seeds on purpose;
- `REG_POLL=0` and `REG_PUBLISH=0`;
- `REG_CRIER_URL=http://127.0.0.1:9`, because `/health` and `/registry` call the Crier consumer and the default URL is the live Crier (app.py 42);
- no rclone config.

`app.py` builds `db`, the journal, the publisher and `_BUILD` when it is imported. Each isolated DB therefore needs a fresh import, or a subprocess. The run must prove that it wrote nothing outside `<tmp>` and opened no connection off the machine.

**Error messages.** The section error prints the `SECTIONS` tuple, which now has three values, and R1 changes the binding message. Any existing test that asserts either message must be listed and updated (U12).

## 4. Runbook changes (francis-ngannou, Implement (3))

- **Step 4:** write `BUILD` = the fix commit's short SHA. Do it after the copy and the in-place hash check, and before the restart. Rollback writes `ede80e1`.
- **Step 6:** expect `build` = that SHA, `version` = "1.2", and `agents` unchanged from step 2.
  - Compare `/journal`'s newest entry by its op, agent and `applied_at`, not by its bytes. Its `publishing` status can change once the restart drains the outbox.
- **Steps 2 and 6:** use `?exclude=venom`, which matches the P1 captures. `exclude=claude-app` excludes nothing today, so it only repeats the plain feed.
- **Step 3:** the NAS (ADM) may have no `sqlite3` command at all. The standing practice on that host is to copy a database off and query it with Python.
  - If there is no `sqlite3`, use the container's own Python sqlite3 backup API through `docker exec`, then bring the copy out with `docker cp`.
  - That path runs as root, which also settles the open question of whether batman can read the DB file.
  - The choice is francis's.

## 5. Pre-existing faults, outside this order (the session files them on bishop's thread)

- A partial `/register` resets the row's binding, section and identity fields to defaults (§2). R3b protects offsite rows only.
  - ronda's bug 3, which she is running now on Sensei's instruction, is the same mechanism seen through `section`.
  - Nothing here changes her task.
- The journal records the agent name unstripped.
- The module docstring advertises `/snapshot` routes that do not exist.
- Helio's F6 (`PUBKEY_RE` also matches a newline) stays with gsp to rate. It is ronda's bug 4, which is documentation only.

## 6. Work-order lines amended (every other line stands)

- **Implement (1), ronda-rousey:**
  1. Make the sparse checkout at `C:\Repo\Wonderland`, on branch `offsite-binding` from `ede80e1`, and check all 8 files against D5.
  2. Then write T1–T12 as amended here, plus the adversarial cases, and commit them before any fix code exists.
- **Implement (2), bruce-lee:** R1, R2, R3 as restated, R4 (with gsp's default-deny if he adopts it), and R6 as amended. The change touches three files: `schema.py`, `app.py` and `render.py`. R5 and R7 are withdrawn; R8 stands.
- **Implement (3), francis-ngannou:** the runbook, with §4's changes.
- **Done when (5):** Sensei has given his go and the deploy is done, and all of the following hold:
  - the SHA-256 of the three deployed files equals the reviewed files';
  - the other five files still equal D5;
  - `/health` is ok, with `build` = the fix commit's short SHA, `version` "1.2", and `agents` unchanged from step 2;
  - both forms of the feed, `/mesh` and the projection are byte-identical to the pre-deploy reads;
  - the journal's newest entry is the same entry as before.
- **Document:** the session saves this addendum byte for byte, with its SHA-256, next to the note. jackie-chan reviews the two together, then gsp. Helio's Next 3–7 order is unchanged.
- **Watch for (k):** a check placed after `normalize_record` sees defaults, not what the caller sent. Anything that asks "did the caller send a binding?" must look before normalize runs.

Files read for this addendum:
- `C:\Repo\townsquare\docs\francis-ngannou-registry-deploy-prep-20260926.md`
- `C:\Repo\townsquare\docs\ip-man-registry-offsite-binding-design-20260926.md` (header only)
- TF lines 87, 109 and 114
- TH line 163
- the first prompt line of ronda's transcript, `…\subagents\agent-a4b6af7a3a9a46148.jsonl`, to confirm what she is doing

I wrote nothing and ran nothing.
