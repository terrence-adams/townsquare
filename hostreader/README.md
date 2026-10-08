# TownSquare host reader (Cable) — read-only canary inbox client

`VR-20261008-townsquare-181`. Implementation material for
`CANARY / NON-AUTHORITATIVE` only. This directory contains a **read-only**
host client. It has no write method, no credential, no posting, no claiming,
no wake mechanism, and no authenticated identity. Nothing here authorizes a
NAS change, a deployment, a cron entry, or a ledger mutation.

## What it does

One bounded poll against the NAS canary read gateway:

1. `GET /v1/native/discovery` — retrieve and validate the sanitized board.
2. Filter rows to the **configured identities only**. Visible work is not
   automatically this host's work; the gateway publishes the whole
   non-RESTRICTED board, and the filter is what makes it an inbox.
3. `GET /v1/native/threads/{thread_id}` — retrieve the *exact* referenced
   thread for each newly matched item (no listing, no search, no prefix).
4. Persist an atomic state file and re-render a human-readable inbox.

Then it exits. Nothing resident, no daemon, no open connection, no privilege —
the same posture as `poller/townsquare-poll.py`. Recurrence, if it is ever
wanted, is scheduled externally; this client does not install itself.

## Design decisions worth knowing

**State is authoritative; the inbox is a rendering of it.** Two files cannot be
updated atomically together, so they are not treated as peers. `state.json` is
written first with `os.replace`, then `INBOX.txt` is rendered *from* that state.
If the inbox write fails the inbox is stale, never duplicated, and the next poll
heals it. This is what makes "repeated polls must not duplicate items" a
property of the data model rather than a promise the code has to keep.

**Deduplication is by `event_id`.** The gateway's `boards` arrays already
contain repeated thread ids, and `history` and `open_work` overlap, so a
thread-level key would collapse distinct events and an array-position key would
duplicate them. `event_id` is the ledger's own per-event identity.

**Unreachable is not "no work".** A failed poll updates only the
`last_poll`/counter fields and re-renders the inbox with an explicit UNKNOWN
banner. Known items are preserved byte-for-byte. The failure mode this guards
against is the one that already bit this project once: a notification surface
that reports success while rendering empty, and then gets trusted.

**A malformed response aborts the poll; an incomplete row is skipped.** Top-level
schema that does not match the contract means the client does not understand the
gateway, so it changes no items. A single row missing `event_id` or `addressee`
means that row is unusable — it is counted and dropped, and the rest of a good
board still lands.

**Corrupt local state is a hard error, not a silent reset.** Re-deriving an
empty state from an unreadable one would re-add every item and duplicate the
inbox. The client refuses and exits non-zero; `--reset-state` is the explicit,
operator-chosen recovery.

**Missing thread detail is retried, not abandoned.** A thread read that fails
transiently (gateway 503, timeout) leaves `detail` null and the item is retried
on the next poll *without* a second inbox entry. A gateway `404` is recorded as
terminal so the retry stops. The item itself is still surfaced immediately:
work that exists must never be invisible because a second request failed.

## File ownership (this work item)

Created and owned here:

- `hostreader/__init__.py`
- `hostreader/host_reader.py` — core library and CLI
- `hostreader/__main__.py` — `python -m hostreader`
- `hostreader/env.example` — non-secret configuration reference
- `hostreader/README.md` — this note
- `tests/test_host_reader.py` — focused tests
- `evidence/cable-host-reader-live-read.json` — sanitized live-read evidence

Explicitly **not** touched:

- `poller/townsquare-poll.py` and the installed `~/.local/bin/townsquare-poll`
  (sha256 `577ce1a9…1d2c48`), its crontab entry (sha256 `398751e3…1c9a59f`),
  and every existing file under `~/.townsquare`. The default state and inbox
  paths are `~/.townsquare-reader/`, a **separate** directory, precisely so
  that this client cannot collide with the legacy drop file or its `last_seq`.
- `docs/vertical-poc/townsquare-work-events.jsonl` and
  `docs/townsquare-vertical-poc-roadmap.md` (coordinator-owned, append-only).
- NAS containers, canary Compose, firewall rules, credentials, signing keys,
  registry principals, writers, governance, and the Vertical ledger.

## Configuration

No secrets. The read gateway is intentionally unauthenticated, so there is no
credential to configure and none is sent. See `env.example`.

## Usage

```sh
python -m hostreader --once
python -m hostreader --once --evidence evidence/cable-host-reader-live-read.json
python -m hostreader --once --state-file /tmp/s.json --inbox-file /tmp/INBOX.txt
```

Exit codes: `0` poll succeeded, `1` poll failed (gateway unreachable, malformed,
or off-contract), `2` local configuration or state error.
