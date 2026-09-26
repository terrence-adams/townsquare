# Registry `binding: offsite`: security review of R1-R6, the default-deny call, F1, F6, F7 and the secrets exclusion

**Author:** gsp (Claude) · **Date:** 2026-09-26 · **Status:** review only. I changed nothing on the NAS, in the Wonderland repo or in any live service. Everything I ran, I ran locally in my own scratch folder, against a copy of the hash-pinned baseline.

**Reviews, in the order briefed:**
- `ip-man-registry-offsite-binding-design-20260926.md` ("the note");
- `ip-man-registry-offsite-addendum-1-20260926.md` ("Addendum 1"), which supersedes the note where they conflict;
- `jackie-chan-registry-offsite-review-20260926.md`;
- `francis-ngannou-registry-deploy-prep-20260926.md`.

I also read the four `bug-report-registry-*-20260926.md` files and `reference-authorize_from_registry-20260926.md`. All of these are in `C:\Repo\townsquare\docs\`.

**Path:** `C:\Repo\townsquare\docs\gsp-registry-offsite-security-review-20260926.md`, on branch `internal`, not pushed.

**Labels**, as in the rest of the chain:
- *measured*: a file I read or a command I ran this session;
- *inferred*: reasoned, not executed;
- *reported-by X*: X's claim, which I did not check.

**Shorthand**
- **G1-G5**: my findings on the fix itself (section 4).
- **s1-s7**: my refinements to the runbook for the secrets exclusion (section 8).
- **R3a / R3b**: R3 as restated in Addendum 1. **R3c** is a new check I propose under G1.
- **Spec**: R1, R2, R3a+R3b, R4 and R6 exactly as currently specified (the note as amended by Addendum 1).
- **Hardened**: spec plus default-deny, R3c, treating `unknown` as absent in R3b, and a write lock (G1-G4).
- **Run NN**: one isolated proof-of-concept run (the PoC; method in section 2, table in section 3).
- **Offsite-presented row**: a row that `/tables` and `/registry?format=md` show under `### Offsite agents`. R6 picks that heading by `section`, so this means any row whose stored `section` is `offsite`.
- **Bound-offsite row**: a row whose stored `binding`, stripped, is `offsite`.
- **The feed** is `GET /authorized_keys`, in both of its forms. **The sync** is `authorize_from_registry.sh`. Both are as defined in the note.

---

## 0. Verdict

**This goes to ip-man for a ruling, then to Helio's GAME PLAN, then to Implement.** It does not go straight to Implement. Nothing needs to go back to jackie-chan or francis-ngannou first.

**What R1-R6 as specified already achieve.** They protect claude-app's own row through `/register`. The chain named several ways a key could reach that row, and I measured each one on a faithful implementation: every one is closed.

**Where they fall short.** The design promises more than one row, and I found two gaps inside that promise.

- **G1 (Medium, must fix, introduced by R1).**
  - R1 makes `section: offsite` a legal value on its own.
  - A body with `section: offsite`, no binding (or `binding: unknown`) and a key is accepted.
  - The row is shown under `### Offsite agents`. Under R4 as specified, its key goes into the feed. I followed that key through the real sync script into an `authorized_keys` file.
  - R3 never fires, because the row's binding is not `offsite`.
  - The note's Done-when (4) (lines 310-311) would pass with this gap in place, because its tests define an offsite row by binding.
- **G2 (must fix, a question of precision).**
  - R3b rejects a body that carries "no non-empty binding". That must mean non-empty *after stripping*.
  - Measured: if the implementation tests the raw value instead, `binding: "  "` re-binds claude-app to `unknown`/`host_bound` and its key is published.

**My call on default-deny: adopt it** (section 5).
- It closes G1 at the feed.
- It changes no byte on P1's data (measured).
- It can only remove lines from the feed, never add them.

**Recommendations for ip-man to rule on (not blockers):**
- **G3:** `unknown` should not count as a deliberate re-bind of a bound-offsite row.
- **G4:** a write lock, so that S1 holds for rows at rest, not only at the feed.
- **G5:** when the feed denies on the stored binding, normalize it first.

**The other items:**
- **F1** holds on its main point, with one correction: the townsquare repo is public (section 7).
- **F6** is Low.
- **F7:** on the documented record, the feed is the only path from the registry to a host. There are also two writers that don't touch the registry at all, and one thing I could not check.
- **The secrets exclusion** holds, with seven refinements.

| Item | Class | Owner after ip-man's ruling |
|---|---|---|
| Default-deny as R4's rule | decided here (the call was mine) | bruce-lee; ronda-rousey's tests T6b-T6d |
| G1: add R3c | required | bruce-lee; ronda (T9b); jackie optional |
| G2: R3b strips before testing for empty; one shared predicate | required | bruce-lee; ronda (T4e) |
| G3: `unknown` is not a deliberate re-bind of an offsite row | recommended | ip-man decides |
| G4: one lock from R3 through upsert | recommended | ip-man decides |
| G5: the deny side normalizes the stored binding | recommended; trivial once default-deny lands | bruce-lee |
| s1-s7 runbook refinements | s3, s6 and s7 required; the rest recommended | francis-ngannou |
| F1 correction: check the Drive folder's sharing before `internal` is pushed | before any push | Sensei (one look in Drive) |
| F6, the F7 survey, the three bug reports | outside this order | bishop's thread; the session files the F7 Request |

---

## 1. Threat model

**What is protected.** The `~/.ssh/authorized_keys` file on every host that syncs.
- The sync only appends and never removes (script lines 32-42).
- So a key that appears in the feed for one sync cycle becomes permanent on every host that synced during that cycle.
- Retiring or editing the row afterwards removes the key from the feed only, not from those hosts.
- That makes prevention at write time the primary control. The feed filter is a second line of defence.

**The property decision 6 needs.**
- No row the registry presents as offsite ever puts a key into any host's `authorized_keys`.
- A bound-offsite row holds no key and no address. This is S1.

**Actors and trust boundaries.**
- **LAN writers.** This means every fleet agent, and anything else on the LAN.
  - Any of them can call `POST /register` for any name, with no credential. That is D34, a standing operator ruling, and I don't re-raise it.
  - The adversary R3 exists for is the *accidental* LAN writer: the host-agent template tells every agent to register itself and its host's SSH key (template line 175).
- **claude-app.**
  - It is off the LAN and cannot reach `:8789`.
  - Its registered role is to file Requests to venom, which means it writes to the TownSquare board on Drive.
  - So decision 6 makes it the first registered off-LAN writer to the board. That matters for F7 (section 7).
- **Root on the NAS** can edit the DB and the code directly. That is out of scope here; the feed filter limits the damage a direct edit can do.
- **Concurrency.** The service runs Flask's threaded server (jackie section 3(d)), so two `/register` calls can interleave.

**Not a concern here.** Public keys are not secrets. The only question is who ends up authorized.

---

## 2. What I verified myself, and how

**Baseline**
- In jackie's scratch clone, `HEAD`, `main` and `origin/main` are all `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf`. [measured]
- `git show ede80e1:services/registry/<file> | sha256sum` reproduces all 8 of francis's D5 hashes exactly. [measured]
- The Wonderland copy of `authorize_from_registry.sh` equals the NAS reference copy byte for byte; its SHA-256 starts `6659ac35`. [measured]

**Code read in full.** I read every file from its `git show` blob, so line endings are the repo's LF:
- `app.py`;
- `registry/schema.py`, `db.py`, `crier.py`, `journal.py`, `publisher.py`, `render.py` and `parse_md.py`;
- the sync script;
- `docker-compose.yml`, `config.env` and the repo's `.gitignore`;
- the setup section and the runner of `tests/test_registry.py`.

**P1, re-derived.**
- My model of the feed reproduces `ak-1a.txt` byte for byte from `registry-1.json`. [measured]
- That data has 24 active rows. 8 of them carry a key, and all 8 are `host_bound`. [measured]
- bishop's row carries a key and has `binding: unknown`. [measured]
- None of the 8 keys contains a newline. [measured]

**The PoC.**
- I wrote a minimal, faithful implementation of R1, R2, R3a+R3b, R4 as specified and R6 as amended, on a copy of the baseline. R3 sits exactly where Addendum 1 places it.
- Environment switches select the variants I propose, so one tree shows spec and hardened side by side.
- That gave 21 scenario runs, plus 5 re-runs under the full hardened set. Each ran in a fresh subprocess through Flask's test client.
- The full results are in section 3.

**End to end.**
- For runs 00, 02 and 05, I served the feed's exact bytes to the **real** sync script, over `file://` and with a temporary `HOME`.
- I then ran `ssh-keygen -lf` on the `authorized_keys` file the script produced.
- So where I say below that a key "reaches `authorized_keys`", that is measured, not inferred from the feed.

**Regression.** The existing suite, `tests/test_registry.py`, passes **43/43** on the baseline, on spec and on hardened. [measured]

**Isolation.**
- Every run had its own temporary DB, journal and outbox.
- Every run set:
  - `REG_POLL=0`, `REG_PUBLISH=0` and `REG_PUBLISH_LOOP=0`;
  - `REG_CRIER_URL=http://127.0.0.1:9`;
  - a seed path and an rclone config that do not exist;
  - `PYTHONDONTWRITEBYTECODE=1`.
- Any `REG_*` variables inherited from my environment were cleared first.
- The endpoints I called were `/register`, `/agent`, the feed, `/tables`, `/mesh` and `/journal`. None of them contacts the Crier.
- Afterwards I checked modification times. Nothing outside my own folder changed during the runs, including ronda's venv (its newest file is from 16:02, before my first run) and jackie's clone.
- The test keys were three throwaway ED25519 pairs. I deleted each private half the moment it was generated, so none exists anywhere. [measured]

**Interpreter.**
- I used ronda's venv, read-only: Python 3.14.6 with Flask 3.1.3. Production runs CPython 3.12.
- Nothing I tested depends on that difference: the regex, `str.strip`, dict and SQLite behaviour are the same. [inferred]

**Where the PoC lives.**
- `C:\Users\terre\AppData\Local\Temp\claude\C--Workspace\6e6cb5f4-3f6f-4870-bf90-c7795b59dbcb\scratchpad\gsp-review\`
- It holds `apply_poc_patch.py`, `poc_harness.py`, `poc_driver.py` and `runs\results.json`.
- It is scratch, and it will not last.
- I deliberately did **not** commit it here. The patch script embeds excerpts of the private Wonderland code, and this repo is public (section 7, F1).
- If ronda wants the race harness for T13, its lasting home is the private `offsite-binding` branch.

---

## 3. Results

All outcomes below are measured.

| Run | Variant | Input | Outcome |
|---|---|---|---|
| 01 | spec | the pinned P2 draft's shape (T1) | 200. Row is `offsite`/`offsite` with empty key and address. Not on `/mesh`. Shown under `### Offsite agents`. |
| 16 | spec | the design's adversarial set: `Offsite`, ` offsite` and `offsite\n`, each with a key; T4, T4b, T4c, T4d (space-padded name); both halves of T5 and of T9; offsite with a two-line key | Every case returns the 400 or 200 the design expects. `offsite\n` sent without a key is **stored with its padding**, confirming jackie section 3(b). A later write adding a key is still refused by R3b. |
| 02 | spec | new name: `{section: offsite, pubkey: A}` | **200. Row is `unknown`/`offsite` and holds A. Shown under `### Offsite agents`. A is in the feed. The sync added A, and `ssh-keygen` lists it in `authorized_keys`.** |
| 03 | spec | new name: `{binding: unknown, section: offsite, pubkey: A}` | Same as 02. |
| 04 | spec | existing host row with a key: `{agent: hostx, section: offsite}` | **200. Row becomes `unknown`/`offsite` and keeps its key. Shown under Offsite. The key stays in the feed. hostx drops off `/mesh`.** |
| 05-07 | + default-deny | same as 02-04 | The writes still return 200, but **no offsite-presented row's key is in the feed**. The sync from 05 added only the unrelated host key. |
| 08-10 | + default-deny + R3c | same as 02-04 | **400** ("section 'offsite' requires binding 'offsite'"). hostx unchanged. |
| 11 / 12 | spec | claude-app offsite, then `{binding: "" or "  ", pubkey: A}` | 400 and 400, with R3b stripping. |
| 13 | spec, R3b not stripping | same as 12 | **200. claude-app re-bound to `unknown`/`host_bound`. A is in the feed.** |
| 14 / 15 | spec / + G3 | claude-app offsite, then `{binding: "unknown", pubkey: A}` | Spec: **200, claude-app re-bound, A in the feed.** With G3: 400. |
| 17 | spec | rows with keys written straight to the DB: `offsite`/`offsite`; `" Offsite\n"`/`host_bound`; `unknown`/`offsite` | The first is dropped from the feed. **The second and third are published.** |
| 18 | + default-deny | same as 17 | **None of the three is published.** |
| 19 | spec | race on a new name: `{binding: offsite}` and `{pubkey: A}`, both past R3, with the key write landing first | Both 200. **At rest the row is `offsite`/`offsite` and holds A.** The feed excludes it, but **`/agent/<name>` serves A, and the journal's `after` records an offsite row holding A.** |
| 20 | + lock | same as 19 | One write 200, the other 400. The row at rest is clean. |
| hardened | all four changes | re-runs of T1, the adversarial set, 12, 17 and 19 | T1 and the adversarial set identical to spec. The rest closed, as in 08-10, 12, 18 and 20. |
| suite | baseline / spec / hardened | `tests/test_registry.py` | 43/43 each. |
| 00 | baseline | F6 (section 7) | See F6. |

**How runs 19 and 20 force the race.** A barrier inside the R3 call holds both requests there, then the two upserts run in a fixed order. The window is real, because Flask is threaded. Hitting it by accident needs two writers on the same name within milliseconds.

---

## 4. Findings on the fix

### G1 (Medium, must fix): R1 lets a row be presented as offsite while its key is published

**Example** (runs 02-04, above).
- Under spec, `POST /register {"agent":"sneaky","section":"offsite","pubkey":"ssh-ed25519 ..."}` returns 200.
- The row is listed under `### Offsite agents`.
- Its key lands in the `authorized_keys` of every host that syncs.

**Mechanism.** This is the baseline plus R1, read at `schema.py` lines 80-90 and 105-118.
1. Once R1 adds `offsite` to `SECTIONS`, `section: offsite` passes the membership check.
2. The contradiction check runs only when the body carries a binding that derives to a section. Here the binding is absent (or `unknown`), and `derive_section("unknown")` returns `""`, so the check is skipped.
3. R3a fires only when the *body's* binding is offsite, and R3b only when the *existing row's* binding is. Neither applies to this row.
4. `normalize_record` fills the missing binding with `unknown`, then keeps the body's `section` through `setdefault` (line 117).
5. R4 as specified tests only `binding != offsite`, so the key is published.

The same path turns an existing host row with a key into an offsite-presented row that keeps publishing that key (run 04). That is the mechanism of ronda's bug 3, now carrying the new label.

**Why it matters for this fix.**
- `offsite` is the security-bearing label decision 6 introduces, and R6 renders it by section. Before R1, this body got a 400.
- Two things make it a plausible accident, not a contrived one:
  - R1's own error message will list `offsite` as a valid section value (the message prints the whole `SECTIONS` tuple);
  - the reissued document's heading will say "Offsite agents".
- So an agent that registers with `section: offsite` plus its host key, as the template asks, gets a 200.

**Fix, in two parts.**
1. **At the feed: default-deny** (section 5). This is my call, and I have made it. Measured in runs 05-07.
2. **At write time: R3c.**
   - Rule: if a body carries `section` equal to `offsite`, its binding, stripped, must be `offsite`. Otherwise 400. Measured in runs 08-10.
   - I would put it in `validate_record`, next to the contradiction check, because it is that check's missing offsite case. That way every write path that validates inherits it, including the legacy path if anyone ever enables it.
   - `offsite_violations` would also be an acceptable home.
   - With R2 in place, every `/register` write then has binding offsite exactly when it has section offsite.
   - The P2 draft sends no section, so it is unaffected (hardened T1, measured).

**If ip-man declines R3c,** record it as an accepted residual, with this consequence:
- Default-deny alone keeps the key out of the feed.
- But the row still *displays* as an offsite agent while holding a key.
- A later partial write can flip it to `unknown`/`host_bound`, and the key is then published.
- R3b cannot catch that, because the row's binding was never offsite.

**Proposed rule text, so the question needs no definitional round:**
- An *offsite row* is one whose stripped binding is `offsite` **or** whose section is `offsite`.
- S1 applies to both kinds.
- R3c makes the two coincide on every `/register` write, and default-deny covers both at the feed.

### G2 (must fix): R3b must strip before testing for empty, and every offsite comparison should use one predicate

**Example.**
- Run 13: claude-app is offsite, and the body is `{binding: "  ", pubkey: K}`. If R3b tests the raw value, this returns 200.
- `normalize_record` treats `"  "` as empty (line 110), re-binds the row to `unknown`/`host_bound`, and the key is published.
- With the strip, the same body gets 400 (run 12).

**Fix.**
- Word R3b as: reject when "the body carries no binding whose stripped value is non-empty". Addendum 1 line 133 is ambiguous on this point.
- Add **T4e**: after T1, a binding of `""`, `"  "` or `"\t"`, each with a valid key, returns 400.
- Answer jackie's section 3(b) concern by structure rather than by care:
  - put one pure predicate in `schema.py`, for example `is_offsite(v) -> bool` meaning `str(v or "").strip().lower() == "offsite"`;
  - call it from R3a, R3b, R3c and the feed, so that no call site can forget the strip.
- `derive_section` keeps its current test: exact match after stripping. It has to stay consistent with `BINDING_RE`, which rejects `Offsite` anyway.

### G3 (Low, recommended): `unknown` should not count as a deliberate re-bind of a bound-offsite row

**Example.** Run 14: claude-app is offsite, and `{binding: "unknown", pubkey: K}` returns 200. The row is re-bound to `unknown`/`host_bound` and K is published. Addendum 1 line 134 allows this on purpose: it lists `unknown` among the deliberate re-binds.

**Why change it.**
- `unknown` is what `normalize_record` writes when a binding isn't stated (line 111), and what the service returns for every unset field.
- So a body sending `unknown` most likely comes from a template or a default. It has not made a decision to re-bind.
- R3b's stated purpose is that an offsite row is never re-bound silently.

**Fix.**
- For an existing bound-offsite row, only `host:<Name>`, `portable` or `offsite` count as an explicit binding.
- An absent, empty, whitespace-only or `unknown` binding returns 400. Measured in run 15.

**Cost.**
- A deliberate re-bind has to state a real binding, which a deliberate re-bind has anyway.
- No baseline behaviour changes, since no offsite rows exist at baseline, and the suite stays at 43/43.
- This stays inside D34: nothing blocks a deliberate re-bind, so it targets only the accident.

### G4 (Low, recommended): one lock from R3 through upsert, so S1 also holds for rows at rest

**Example.** Run 19 reproduces the race in Addendum 1 (line 148), in the order the addendum did not trace:
1. The write carrying the key, with no binding, lands first.
2. The offsite write, which has no `pubkey` field, lands second and merges onto the row that now holds the key.

The row ends up bound offsite and holding the key.
- R4 keeps it out of the feed, as designed.
- But `/agent/<name>` and `/registry` still serve the key.
- The journal's `after` for that write records an offsite row holding it.
- Those are exactly the reads F7 cannot vouch for (section 7).

**Fix.** Add a module-level `threading.Lock` in `app.py`, held from R3's `db.get` through `db.upsert` and the read of `after`. Compute `at` inside the lock.
- R3 then sees the row the write actually lands on. In run 20 one of the two writes gets 400, and the row stays clean.
- Computing `at` inside the lock has a second benefit.
  - `at` has one-second resolution, and `upsert` drops any write whose `at` is older than the stored `applied_at` (`db.py` lines 103-111).
  - So today two concurrent `/register` calls can silently drop one of the two writes. The lock stops that too.
- The service is a single `python app.py` process, so an in-process lock is enough. Record that as an assumption: a server with several worker processes would need a transaction in the DB instead.

**Why it is worth the few lines.**
- It turns S1 from "enforced at the feed" into "true at rest", for every writer that can reach the service.
- What remains are a direct DB edit (root on the NAS) and a code change that enables the legacy path. Both are outside the LAN-writer model.

### G5 (Low, recommended; trivial once default-deny lands): normalize on the deny side, match exactly on the allow side

**Example.**
- Run 17: a row stored with binding `" Offsite\n"` is published under R4 as specified, because R4's comparison strips but is case-sensitive. That value can only get there through a direct edit.
- Run 18: the same row is dropped under default-deny with `.lower()`.

**Rule.**
- When the feed *denies* on a stored value, normalize it first: strip it and lower-case it, via `is_offsite`.
- When the feed *allows* on a stored value, match exactly: `section == "host_bound"` with no strip, so a malformed stored section fails closed.
- Stored bindings can carry padding (jackie section 3(b), and the `a4` row in run 16).

### What I confirm as specified, without change

- **Where R3 sits and how it merges** (Addendum 1 lines 113-129).
  - R3 runs between `validate_record` (app.py lines 183-185) and `normalize_record` (line 186), and reads the row through the stripped name.
  - R3a takes the body's value when the field is present and not `None`, and the stored value otherwise. That matches what `upsert` does (`db.py` line 101).
  - jackie's re-derivation holds on my runs.
- **R3a catches:**
  - a host row with a key being converted to offsite without clearing the key (T5);
  - an offsite body carrying a two-line key (run 16, case j).
- **`/register` is the only route that writes field values.** [measured]
  - `/retire` writes status only.
  - `/poll` reaches the DB only through `touch`, which records liveness only (`db.py` lines 153-156).
- **The legacy path is more locked down than "off by default".**
  - `ingest_registrations` can only be set as a constructor argument.
  - `app.py` (lines 128-129) never passes it, and no environment variable sets it (checked with `git grep` at `ede80e1`).
  - So in the deployed app it cannot run without a code change.
  - Even if it were enabled, `_keep_known` drops `pubkey` and `host_address` (jackie's U10).
- **`_seed_if_empty` cannot write a key.** `parse_registry_md` produces no `pubkey` or `host_address` column (`parse_md.py` lines 63-73).
- **Withdrawing R5 and R7:** I agree.
  - `/mesh` is not a key path: it exposes `has_key`, not the key itself.
  - With R3c in place, `/register` cannot put an offsite row on `/mesh`.
  - `/mesh` could reuse `is_offsite` at no cost if ip-man wants it, but I am not asking for R5 back.

---

## 5. The default-deny call: adopt it

**R4's rule.** The feed publishes a row's key only if all four hold:
- the row is active (the feed's loop already checks this);
- its stripped `pubkey` is non-empty;
- `row["section"] == "host_bound"`, matched exactly;
- `not is_offsite(row["binding"])`.

Put this in `schema.py` as a pure function, `key_publishable(row) -> bool`, so it can be tested without Flask. Both forms of the feed use it.

**Benefits** (measured; section 3):
1. It closes G1 at the feed (runs 05-07).
2. It closes the portable half of S5: a portable row with a key is no longer published. That path is open today, because the baseline feed has no filter at all (Addendum 1 lines 152-154).
3. A key is published only when two separately stored fields both say "host". If either field drifts, or is edited directly, the result fails closed (run 18).
4. It enforces D28 on the fleet's only automated key path.

**Costs:**
1. **It trusts the stored `section` on the allow side.**
   - A row with a key whose section drifts off `host_bound` stops being published. ronda's bug-3 partial write `{section: portable}` is one way that happens.
   - That fails closed. Hosts that already synced keep the key, because the sync never removes anything.
   - Only hosts that sync afterwards miss it. That is a cost to availability, not to security.
2. **It does not stop drift *into* `host_bound`.**
   - `normalize_record` gives `host_bound` to any partial write that states no section (line 117).
   - So both rules publish such a row. That is the S5 re-bind residual, and it stays with bishop's thread.
3. **The deploy must re-prove on the day that the feed is unchanged**: see s7.
4. **One more condition to test**, covered by T6b-T6d.

It adds a condition, so it can only ever remove lines from the feed. It cannot grant anything that R4 as specified would not.

**The alternative I considered: a rule keyed on binding.** Publish only if the stripped binding starts with `host:`.
- It is the purer form of D28.
- But on P1's data it **drops bishop's key**: his row is `unknown`/`host_bound` and carries a key [measured].
- That would change the feed at deploy, which breaks Done-when (5).
- I recommend it for bishop's thread, once two things are fixed:
  - the bindings on rows with keys are repaired;
  - partial writes stop resetting bindings to `unknown`.

**Why not section alone.** The note's Watch-for (b) already rejects it, because a stored section drifts; bishop's row shows it. I agree.

---

## 6. S1-S5, as corrected in Addendum 1

- **S1.**
  - Through `/register`, it holds for bound-offsite rows once G2 is in, and for offsite-presented rows once G1 is in.
  - For rows at rest it holds only with G4. Without the lock, the race in run 19 breaks it.
- **S2.**
  - It holds as restated, with G2's wording.
  - I found no fourth way to put a key on a bound-offsite row that gets past R3a or R3b.
  - G1 is a path around R3, not through it.
- **S3.**
  - The list of other writers is right.
  - The legacy path is weaker than the list gives it credit for (section 4).
  - With default-deny, the feed drops the key from any row where either field says "not a host", whoever wrote it.
- **S4.** Agree.
- **S5.**
  - "Any LAN writer can re-bind any row" is D34. It is an accepted residual, and I don't re-raise it.
  - "Host and portable rows can take a key through a partial write" still holds for host rows. For rows that explicitly say portable, default-deny now keeps the key out of the feed.
  - If G4 lands, the race residual shrinks to nothing reachable through `/register`.

### Charter note

**What was routed to me.** Addendum 1 (lines 190-194) routes these items to me: S1-S5, the default-deny call, F1, F6, F7 and the secrets exclusion. So G1-G5 are review of routed items. None of them re-opens anything already ruled.

**What I do not re-open:**
- F6's out-of-scope ruling;
- the routing of pre-existing faults to bishop's thread (Addendum 1, section 5);
- D34;
- the withdrawal of R5 and R7.

**Labels.** This review is the first round on G1-G5, so under C1 no question needs a label yet. If ip-man's ruling disputes any of them, his reply is the second round, and it carries the label. My expectation:
- **G1:** DEFINITIONAL, if the dispute is about what an offsite row is. The rule text proposed under G1 is meant to settle that in advance.
- **G3 and G4:** PREFERENTIAL, with ip-man deciding, as the work order routes review concerns to him.
- **G2:** I would not expect a dispute, since the measured failure is in section 3.

---

## 7. F1, F6, F7

### F1: no secret in the environment dump, confirmed, with one correction

**Confirmed.**
- I re-read the environment block in francis's report (D3). It holds configuration values and the path to the rclone config. It contains no token, no client secret and no password.
- The token lives only in `secrets/rclone.conf`, which nobody opened.
- The repo's `.gitignore` excludes `secrets/`, `rclone.conf` and `data/`.

**The correction.** The chain describes the Drive folder ID as already used openly elsewhere. For the internet, that is not so. [measured]
- `terrence-adams/townsquare` is a **public** repository.
- Across all of `C:\Repo`, the RegistryJournal folder ID (the value of `REG_PUBLISH_FOLDER_ID`) appears in exactly one file: francis's deploy-prep document.
- That document sits in `internal` commits that have not been pushed.
- None of this repo's pushed branches has ever contained the ID: I checked `main`, `internal`, `external` and `feat/ts-welfare` with `git log -S`.
- Outside this repo it is committed only in the private Wonderland repo's `docker-compose.yml`.
- So pushing `internal` would publish the ID to the internet for the first time.

**What that exposure means.**
- A folder ID alone grants nothing, unless the folder is shared by link. If it is shared by link, the ID *is* the key to it.
- **Before `internal` is next pushed, Sensei should check that the folder's General access is set to Restricted.**
  - If it is, publishing the ID reveals an identifier only. That is Low.
  - If it is not, the finding is Medium. The fix is either to restrict the folder, or to keep that commit out of the push.
- If a wider audit of Drive sharing is wanted, that is TJ's area.
- I kept the ID out of this document.

In the same unpushed commits, the key-like strings in ronda's bug reports and tests are fake placeholders, not fleet keys. [measured]

### F6 (the `PUBKEY_RE` newline gap): Low, cheap to fix, fast-follow on bishop's thread

**Proven end to end** (run 00, baseline).
- One row, `hostx`, with one `pubkey` value:
  - line 1 is `<type> <base64>`, with no comment;
  - line 2 is a complete second key.
- The value is accepted (200).
- `/mesh` shows one host, with `has_key: true`.
- The feed emits two lines, and the real sync appends both.
- `ssh-keygen -lf` lists **two valid ED25519 keys** in the resulting `authorized_keys`.

**Refinements to the bug report** [measured]:
- The hidden line rides in the regex's optional comment group, so **line 1 must carry no comment**.
- The usual accidental paste is **rejected** (400). That paste is two ordinary `.pub` lines with comments, as `cat a.pub b.pub` would produce.
- A value with three lines that are each a well-formed key is also rejected.
- So an accepted value contains at most two lines that are well-formed keys, which means at most one hidden extra key per row.
- The mechanism is therefore mainly a way to hide a key on purpose. It does little to make accidents worse.

**Rating: Low overall.**
- The impact is Medium. The result is a permanent extra credential on every host that syncs, hidden inside a row that looks like it holds one key.
- The likelihood is Low. It needs a LAN writer who builds the value on purpose, and under D34 such a writer can already publish a key openly. So F6 adds a way to hide, not a new capability.

**Fix, one line.**
- In `validate_record`, reject a `pubkey` that, after its ends are stripped, still contains `\n` or `\r`.
- A defensive twin in the feed would skip any such value.
- On P1's data neither change alters a byte, since no stored key contains a newline [measured].

**Routing.** bishop's thread, as already ruled. If ip-man wants to fold the one-liner into this diff because bruce is already editing `schema.py`, that is his call. I am not asserting a C4 ground to re-open the scope ruling.

### F7 (is the feed the only automated path into `authorized_keys`?): answered as far as Venom can see, with one unknown

**What I found** [measured]:
1. **The only path from the registry to a host that the fleet has announced is the feed, through the sync.**
   - The announcement is BB-20260913-bishop-001.000; the host-agent template (line 178) tells agents to follow the sync procedure bishop announces on the board.
   - This is exactly the path R4 and default-deny guard.
2. **`C:\Repo\townsquare\tools\fleet-mesh.sh` is a second automated writer into every host's `authorized_keys`.**
   - The operator runs it by hand.
   - It collects each host's own `~/.ssh/id_ed25519.pub` over SSH (lines 79-101), then appends the whole set on every host (lines 110-132).
   - The note is right that it does not read the registry, so it cannot carry any registry row's key, offsite or not.
   - But it does mean the feed is not literally the only automated path.
3. **The Drive doctrine is a manual path.**
   - It is `N3rd0m\Fleet\fleet-key-exchange.md` plus the files in `Fleet\keys\*.pub`.
   - Keys are appended by hand, with a fingerprint check that halts on a mismatch.
   - It does not involve the registry, and claude-app has no file there.
4. **Unknown: whether any host runs its own version of the sync that reads something other than `GET /authorized_keys`.**
   - The candidates are `/registry` JSON, `/agent/<name>`, `/journal`, or the audit artifacts that rclone publishes.
   - All four serve `pubkey` **whatever the binding**, and R4 protects none of them.
   - Run 19 shows an offsite row's key served by `/agent` and recorded in the journal's `after`.

**What limits the risk.**
- Once G4 lands, no writer that can reach the service can leave an offsite row holding a key. Those reads then have nothing offsite to leak.
- Without G4, the limit is only that the race is unlikely.

**The off-LAN angle that decision 6 adds.**
- claude-app writes to the board from outside the LAN.
- So **any host automation that takes SSH trust from board or Drive content would be a path from off the LAN that bypasses the LAN write gate.**
- Inside the registry, only two things keep board content out of `pubkey`:
  - `crier.py`'s `_KNOWN` list omits `pubkey` and `host_address`;
  - the legacy board ingestion can only be switched on by a code change.
- Both are now load-bearing. R8 leaves them unchanged.
- Add one line to the Watch-for list: **`_KNOWN` must never gain `pubkey` or `host_address`, and board ingestion must stay off, for as long as the board has writers outside the LAN.**

**Action, not blocking this order.** The session files a TownSquare Request to the fleet, or one per host. It asks each host agent to report its `authorized_keys` automation:
- the output of `crontab -l`;
- its systemd timers;
- any script that writes `~/.ssh/authorized_keys`;
- for each one found, the source it reads keys from.

**Rating:** this is an open unknown, not a finding. The remaining risk is Low.

---

## 8. The secrets exclusion: holds, with refinements s1-s7

**What holds.**
- francis's prep never listed or opened `secrets/` or `data/` (reported-by francis; his list of commands agrees).
- His runbook copies code files by name.
- It keeps every backup on the NAS, outside the bind mount.
- It never moves `data/` or `secrets/` off the NAS.

**Confirmed**, with these refinements:

- **s1 (confirm).** No step archives or recursively copies the registry root, which contains `secrets/`. Keep it that way: name every file explicitly, and never run `tar`, `cp -r` or `rsync` on the root.
- **s2 (recommended).** In step 3, remove `2>/dev/null || true` from the copy of the journal and outbox. A failed backup must be visible before the restart. This is about safety, not secrecy.
- **s3 (required, if this fallback is used).** Addendum 1's fallback backs up SQLite through `docker exec` and then `docker cp`.
  - That runs as root, inside a container whose environment points at the rclone config and whose `/app` directory holds `secrets/`.
  - Pin it in the runbook to one exact command: Python's `sqlite3` backup API, copying `/app/data/registry.db` to a path on the NAS.
  - The `docker cp` destination must be the NAS backup directory.
  - At no step run `env`, `printenv`, `ls` or `cat` against `/app/secrets`.
- **s4 (recommended).** Don't paste raw `docker inspect` or `docker logs` output into repo documents.
  - Filter to what is needed, such as Mounts and Binds, or the tail of a traceback.
  - Before committing, scan for `token`, `refresh_token`, `client_secret` or `password`.
  - Today's environment is clean. But rclone accepts a remote's token through environment variables, so a future environment could carry one.
- **s5 (confirm).** The DB copy made in step 3 holds public keys, addresses and inventory, none of it secret. It stays on the NAS, as written.
- **s6 (required).** Hash-check what is deployed against the reviewed commit's blobs. This is a secrets control, not only an integrity one.
  - Why: the deployed code runs as root, and it can read `secrets/rclone.conf` through the same bind mount. So it matters that the deployed files are exactly the reviewed ones.
  - Hash the reviewed commit's **blobs**, never the files in a Windows working tree, because `core.autocrlf=true` here (jackie section 0).
  - In practice:
    1. Export the three files with `git show <fix-sha>:services/registry/<path> > <staging>\<file>`.
    2. Check that the exported files contain no CR bytes.
    3. Compare their SHA-256 with `git show <fix-sha>:... | sha256sum`.
    4. `scp` the exported files, not the working-tree copies.
    5. Compare the NAS copies' SHA-256 with the same blob hashes.
  - Never hash and copy from a working tree. An uncommitted local edit would then be "verified" and deployed.
- **s7 (required, now that default-deny is adopted).** Add a pre-check to step 2.
  - From the live `/registry` JSON, list every active row that has a non-empty key and either a `section` other than `host_bound` or an offsite binding.
  - **The list must be empty.**
  - If it isn't, default-deny will change the live feed. Stop and bring it to Sensei, rather than finding out at step 6.
  - On P1's data the list was empty [measured], but the live DB can change before the deploy.

---

## 9. Ratings for the other findings in the chain

**A stale write gives no signal** (ronda's bug report). **Low**: a gap in observability.
- It does not weaken R3. jackie's all-or-nothing argument holds, and nothing in my runs contradicts it.
- Where it touches security: a write that clears a key (T5's conversion, for example) can be dropped while the caller still gets `ok: true`. The key then keeps reaching new hosts.
- The caller can detect this, because the response's `agent` object is the row as actually stored.
- So the second send's P3 check (in ip-man's v5 section 4 amendment) should compare that object field by field with the body it sent.
- G4's lock removes the way a single process can cause this.
- The structural fix, a return value from `upsert` plus a field in the journal, is bishop's.
- Worth recording here, but not a blocker.

**The agent name is stored unstripped** (ronda's bug report). **Low**: audit integrity.
- Measured limit: after stripping, `AGENT_RE` constrains every non-whitespace character. So only leading or trailing whitespace can be injected.
- That can split the audit artifact's `agent:` line, add blank lines to it, or put a raw newline in the filename rclone uploads.
- It **cannot forge a header field**, because `:` and spaces are refused inside the name.
- For this fix:
  - R3 reads the stripped name, matching `db.get` and `upsert`;
  - a padded name on an offsite row is refused before any journal step (T4d; run 16, the space-padded case).
- Routing unchanged: bishop's thread. I rate it; I don't re-open Addendum 1's routing.

**The `core.autocrlf` hash hazard** (jackie section 0). **Required**, as s6.

**Partial writes fill defaults** (ronda's bug 3; Addendum 1 section 5).
- This is the root mechanism behind run 04, and behind the S5 re-bind residual.
- It stays with bishop's thread.
- R3c (from G1) and default-deny contain its offsite consequence.

---

## 10. Test additions for ronda-rousey, as ip-man rules

**How every test should be built:**
- it creates its own rows (jackie's point about the runner's alphabetical order);
- it asserts the stored row, the journal, and both forms of the feed.

**The tests:**
- **T4e (G2).** With an offsite row in place, send a binding of `""`, then `"  "`, then `"\t"`, each with a valid key. Each returns 400, and the row, the journal and the feed are unchanged.
- **T4f (G3, if adopted).** `binding: "unknown"` plus a valid key returns 400.
- **T6b (default-deny).** This is the note's own T6b:
  - a portable row with a key is absent from the feed;
  - a row with a key and bishop's shape (`unknown`/`host_bound`) is present.
- **T6c.** A row with a key and `unknown`/`offsite`, written straight to the DB, is absent from the feed.
- **T6d (G5).** A row with a key and `" Offsite\n"`/`host_bound`, written straight to the DB, is absent from the feed.
- **T9b (R3c).** Each returns 400:
  - `{section: offsite, pubkey: K}` on a new name;
  - `{binding: unknown, section: offsite}`;
  - `{section: offsite}` on a host row with a key. The row is also unchanged: it stays on `/mesh`, and its key stays in the feed.
- **T13 (G4, if adopted).** Force the interleaving from runs 19-20. One write returns 400, and the row never ends up bound offsite and holding a key.
- **Optional end-to-end check.**
  - Serve the feed's bytes to the real sync script over `file://`, with a temporary `HOME`, then run `ssh-keygen -lf`.
  - This proves a key reaches `authorized_keys`, not just the feed.
  - It needs no network.

---

## 11. What I will check when the R3 and R4 hunks come back for review

1. R3 sits between `app.py`'s `validate_record` return and `normalize_record`, and reads `existing` through the stripped name.
2. R3a's merge rule: the body's value if present and not `None`, else the stored value; each converted with `str()`, then stripped.
3. R3b strips before testing for empty. If G3 is ruled in, it also rejects `unknown`.
4. R3c is present.
5. Every offsite comparison goes through the one predicate.
6. R4 is `key_publishable`, with an exact section match and a normalized binding, in both forms of the feed.
7. If G4 is ruled in, the lock spans R3 through the read of `after`, and `at` is computed inside it.
8. The diff adds no file reads, no routes, and no logging of request bodies. The process runs next to `secrets/`.
9. The hunks I review are hashed from `git show` blobs.

---

## 12. What I did not do

- I did not touch the NAS, the live registry (`:8789`), the Crier, Drive or rclone.
- I pushed nothing, and wrote nothing to Wonderland.
- I did not read the RegistryJournal folder's sharing setting. I have no access to Drive permissions from here, so that check is Sensei's.
- I could not survey other hosts' crontabs or scripts (F7 item 4).
- I did not measure what rclone and Drive do with a newline in an uploaded filename.
- My only change to this repo is this file.

**Files read:**
- the four documents in the chain;
- the four bug reports;
- `reference-authorize_from_registry-20260926.md` and `decision-6-p2-body-draft.json`;
- the Wonderland `services/registry` files at `ede80e1`, through `git show` in jackie's clone;
- the P1 captures;
- `C:\Repo\townsquare\tools\fleet-mesh.sh`;
- `C:\Repo\Agentic\host-agents\templates\host-agent.template.md` (lines 150-194);
- `G:\My Drive\N3rd0m\Fleet\fleet-key-exchange.md`;
- BB-20260913-bishop-001.000;
- `C:\Repo\Agentic\docs\charter-2.0-part-c.md` (C1 and C2).

**Commands run.** All were local and read-only, except for my own scratch folder and this commit.
- In jackie's clone: `git rev-parse`, `git show | sha256sum` and `git grep`.
- In this repo: `git grep` and `git log -S` across its branches.
- `gh repo view --json visibility`, on two repos.
- `ssh-keygen`, to make the throwaway keys and read fingerprints.
- The PoC runs, the existing suite and the sync script, each isolated as described in section 2.
