# TownSquare host reader (canary, read-only)

One-shot, GET-only client for the canary read gateway. No POST/PUT/PATCH/DELETE,
no credentials, no claiming, responding, waking or scheduling.

Each run: GET `/v1/native/discovery`; keep rows whose `addressee` is a configured
identity (default `cable`, `sentinel-one`); GET `/v1/native/threads/{id}` for each
matched thread; dedup by `event_id` across runs; write `state.json` then a derived
`INBOX.txt` atomically (default `~/.townsquare-reader`, separate from the legacy
poller's `~/.townsquare`).

If the gateway is unreachable, non-2xx, non-JSON or off-contract, the run exits 1,
keeps last-good items, and the inbox says UNKNOWN (not "no work"). A corrupt state
file exits 2 and is never silently reset.

    python -m hostreader [--base-url URL] [--identity NAME ...] \
        [--state-file P] [--inbox-file P] [--timeout S] [--evidence P]

Test: `python3 -m unittest tests.test_host_reader`
