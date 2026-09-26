# Bug report: `/register`'s `agent` name is validated stripped but stored/journaled raw

**Author:** ronda-rousey (Claude) · **Date:** 2026-09-26 · **Status:** reproduced against baseline, awaiting a remediation ruling (ip-man / jackie-chan). This is reproduce-and-document only; no fix is proposed or implemented here.

**Baseline:** `terrence-adams/Wonderland` @ `ede80e18c3b1fe6ff6a29874e4c6fd64572bcccf` (`main`), `services/registry/`. Confirmed by `git rev-parse HEAD` on a fresh clone to a scratchpad (never the NAS, never `C:\Repo\townsquare`).

**Reproduction:** `services/registry/tests/test_decision6_bug_reports_20260926.py`, tests `test_register_trailing_newline_name_row_identity_is_consistent`, `test_register_trailing_newline_name_corrupts_journal_agent_field`, `test_register_trailing_newline_name_crashes_the_audit_write`, `test_register_leading_and_trailing_space_name_same_journal_defect`. Run in isolation (`REG_POLL=0`, `REG_PUBLISH=0`, `REG_PUBLISH_LOOP=0`, fresh temp DB/journal/outbox, no seed, no rclone config):

```
venv/Scripts/python.exe -m pytest tests/test_decision6_bug_reports_20260926.py -v
```

Raw result: **7 failed, 2 passed** (2 of the 7 failures belong to bugs 2 and 3, covered in their own reports). For this bug specifically: `corrupts_journal_agent_field` and `crashes_the_audit_write` **FAIL** (red, demonstrating the bug); `row_identity_is_consistent` **PASSES** (a deliberate negative-result check, see "What does NOT reproduce" below).

## What I verified about the mechanics first

The originating lead framed this as "`before` may see no existing row when one exists." Reading `app.py`'s `/register` and `db.py`'s `get`/`upsert` directly, that specific framing does **not** hold:

- `schema.validate_record()` matches `AGENT_RE` against a **local, stripped copy** (`agent = str(rec.get("agent","")).strip()`) — it never writes that stripped value back into `rec`.
- `app.register()` then does `name = rec.pop("agent")`, which is the **raw, un-stripped** value from the request body.
- But `db.get()` (`db.py:166`, `agent.strip()` inside the SQL parameter) and `db.upsert()` (`db.py:98`, `agent = agent.strip()` at the top of the function) **both** strip internally, and identically. Because `before = db.get(name)`, the upsert target, and `after = db.get(name)` all normalize the same raw `name` the same way, they all resolve to the **same** canonical row — there is no split-brain "duplicate row" or "before wrongly says nothing exists." `test_register_trailing_newline_name_row_identity_is_consistent` asserts and confirms this directly (passes).

What **is** real: `name` itself — raw, un-stripped — is used verbatim downstream of validation for the **journal** and the **rendered board-audit artifact**, neither of which re-strips it. That is the actual, reproducible bug, and it is worse than the original framing in one respect (a crash, not just a data mismatch).

## Example 1: journal/audit-record self-inconsistency (portable, no crash)

```
POST /register {"agent": "claude-app", "binding": "portable"}          -> 200
POST /register {"agent": "claude-app\n", "pubkey": "ssh-ed25519 AAAA...=="}  -> 200
```
or, without even a newline:
```
POST /register {"agent": "  claude-app-sp  ", "pubkey": "ssh-ed25519 AAAA...=="}
```

The row itself updates correctly (single canonical row, new pubkey applied). But the **journal entry** for the second write is internally inconsistent — measured directly:

```
entry["agent"]         == "  claude-app-sp  "     # raw, as sent
entry["after"]["agent"] == "claude-app-sp"          # canonical, from db.get()
```

One audit record, two spellings of the same agent, in the same JSON object.

## Example 2: a trailing newline in `agent` crashes the write's own audit step (HTTP 500)

```
POST /register {"agent": "claude-app-crash", "binding": "portable"}            -> 200
POST /register {"agent": "claude-app-crash\n", "pubkey": "ssh-ed25519 AAAA...=="}  -> 500
```

`journal.py`'s `_outbox_filename()` builds the board-audit artifact's **filename** directly from the raw agent value (`f"...__agent-{ag}__registry-write-audit.txt"`, only `_ascii()`-encoded, never stripped). Raw traceback observed:

```
File "registry/journal.py", line 93, in record
    with open(path, "w", encoding="ascii") as f:
OSError: [Errno 22] Invalid argument: '...\\outbox\\TS-20260926-bishop-regaudit.003-LOG__by-bishop__op-register__agent-claude-app-crash\n__registry-write-audit.txt'
```

By the time this raises, `db.upsert()` has **already committed** the row mutation (confirmed: `db.get("claude-app-crash")["pubkey"]` is already the new value), and `journal.log`'s append-only line has **already been written and fsync'd** (step 1 of `Journal.record`, before the crashing step 2) — so the write is applied and durably logged in the raw journal file, but the client is told `500 Internal Server Error`, and the board-publishable outbox artifact for this write is **never created**.

**Cross-platform check (I did not assume this, I verified it):** this exact `OSError` is specific to this reproduction's interpreter (Windows/NTFS, Python 3.14.6 — see also the interpreter-mismatch note below). I confirmed separately, directly on a real Linux filesystem (WSL2/ext4, matching the production container's OS family, `python:3.12-slim`), that `open()` on a path whose filename component contains a raw `\n` does **not** raise — POSIX permits it:

```
$ wsl.exe -e bash -c 'python3 -c "open(\"/tmp/x/TS-agent-claude-app-j\n__foo.txt\", \"w\").write(\"hello\")"'
SUCCESS: file written without error   # (ls -b shows the literal \n byte in the filename)
```

So in the actual deployed container this specific request most likely returns **200** with a **malformed filename on disk** (a literal newline byte embedded in it) rather than a 500 — itself still a real defect, and a plausible rejection point the first time that filename is handed to `rclone copyto` for the Drive upload, which is this artifact's entire purpose.

## Context: why this matters

- **Audit-trail integrity.** The journal is documented as "the audit trail" (journal.py's own module docstring) for every accepted canonical write. An entry whose own `agent` field doesn't match its own `after.agent` breaks any downstream tooling that does exact-match lookups/grouping by agent name (e.g., "find every write for `claude-app`" would miss this entry, since its top-level key is technically `"claude-app\n"` or `"  claude-app-sp  "`).
- **Header injection into a fixed-format artifact.** `_render_artifact()` builds a `key: value`-per-line header block, terminated by `---`, that other TownSquare tooling presumably parses. A raw newline in `entry['agent']` injects an extra (blank, in the newline case) line into that block, splitting what should be one `agent: ...` line. A more actively adversarial multi-line agent value (which validation, as shown in the sibling `pubkey-multiline` bug report, is also too permissive about) could inject a **fabricated header field** into a document meant to be an authoritative audit record.
- **A write can be applied, logged in the raw journal, and yet reported to the caller as a failure, with no board-publishable record.** That is a worse failure mode than "cosmetic corruption": an operator or automated caller reading only the HTTP response has no way to know the mutation actually happened.
- **This is LAN-trust, register-anyone infrastructure** (per `app.py`'s own module docstring, "LAN trust is the write model") feeding an `authorized_keys` file appended to every fleet host — the audit trail around who registered what, when, is precisely the layer that is supposed to make that trust model reviewable after the fact.

**Interpreter/OS disclosure:** this reproduction ran on Windows, Python 3.14.6, Flask 3.1.3 (the production container is `python:3.12-slim`, per the `Dockerfile`). The journal/artifact self-inconsistency (Example 1) is OS- and version-independent (pure string/dict logic). The 500-crash (Example 2) is Windows-filesystem-specific, confirmed not to reproduce identically on a real Linux filesystem — see above for exactly what does happen there instead.

## Potential solutions (not prescriptive — ip-man / jackie-chan to rule)

- Normalize (`.strip()`, and decide on case/other rules) the `agent` value **once**, immediately after `validate_record` passes, and use that single canonical value for everything downstream in `register()`: `db.get()`, `db.upsert()`, and `_journal.record()`. This is the smallest change and removes the raw value from circulation entirely.
- Alternatively, make `AGENT_RE` reject (rather than let `.strip()` silently launder) any value that isn't already byte-identical to its stripped form, so a client that sends whitespace-padded names gets a clear 400 instead of quiet normalization.
- Separately, `journal.py`'s `_outbox_filename()`/`_render_artifact()` should not trust that any value handed to it is filename-safe or single-line, regardless of what `register()` does upstream (defense in depth for the crier/legacy or any future write path that might call `_journal.record()` with a less-validated agent value).
