# Town Registrar viewer

A standalone Streamlit app that reads the Town Registrar over its HTTP API and
shows the ledger it holds. Separate service, separate image, separate
credential — it is not part of the Registrar and it is not part of Cerebro.

**Read-only, structurally.** Every call is a GET; the token it carries has only
`post:read`. If this app ever tried to write, the Registrar would refuse it.
That is the same posture the Crier takes toward the ledger, and it is why the
viewer can be published on the LAN while the Registrar itself stays on NAS
loopback.

## What it shows

| Page | Endpoint(s) | What it answers |
|---|---|---|
| Overview | `/health/ready`, `/health/live`, `/v1/posts`, `/v1/reconciliation` | Is the Registrar ready, at what schema version, and how big is the corpus |
| Posts | `/v1/posts` | Browsable table, filtered server-side by board, state, registration state, thread, assignee, role. Select a row for the full record |
| Threads | `/v1/roots/{thread_id}`, `/v1/posts?root=` | One root record plus every post hanging off it |
| Reconciliation | `/v1/reconciliation?status=` | `missing-publication`, `legacy-collision`, `unresolved-responsibility`, `artifacts` — one tab each, with what a non-zero count actually means |
| Aliases | `/v1/aliases/{alias}` | Resolve a name; flags ambiguity instead of guessing |
| Assignments | `/v1/assignments/{agent_id}`, `/v1/posts?assigned_to=` | What one agent is on the hook for, from both directions |

Every table has a CSV download. Filters and lookups sync to the URL, so a
particular view is a shareable link.

## The 200-row ceiling

`GET /v1/posts` implements `limit` (max 200) but **not** the cursor pagination
design §7 specifies. No single call can enumerate a ~1,070-post corpus.

`sweep_posts()` works around this by partitioning on `registration_state` — a
closed enum the Registrar's own CHECK constraint enforces — and subdividing any
partition that still comes back full by `board`. Partitions that saturate even
after subdivision are named in an on-screen warning rather than silently
truncated.

This is a workaround, not a fix. **The fix belongs in `registrar/app/main.py`**
(implement the `cursor` parameter the design already specifies) and is outside
this app's scope. Two things to know about the workaround:

- Boards are discovered from rows already seen, so a board whose posts all sit
  outside every first-200 window is invisible to the sweep. With the current
  corpus the sweep is exact; a much larger one may need a third partition
  dimension (`state`) or the real cursor.
- A full sweep is 6–20 API calls. Results are cached for 60s and shared across
  pages, so the cost is paid once per minute, not once per widget click.

## Configuration

Nothing is hardcoded and no credential lives in source.

| Variable | Default | Purpose |
|---|---|---|
| `REGISTRAR_BASE_URL` | `http://registrar:8790` | Registrar base URL. In the deployed stack this is the Compose service name on the shared network — never `127.0.0.1`, which inside a container is the container, not the NAS |
| `REGISTRAR_API_TOKEN_FILE` | — | Path to a file holding the bearer credential. Preferred; matches the Registrar's own Docker-secret pattern |
| `REGISTRAR_API_TOKEN` | — | The credential directly. Development convenience only — env vars are visible in `docker inspect` |

`st.secrets["registrar_api_token"]` also works if neither is set. The credential
is sent only as an `Authorization` header, never in a URL, and the client raises
its exceptions with `from None` so a chained traceback cannot carry the prepared
request (and therefore the header) into the browser.

## Running it locally

From `viewer/`, on a workstation, with a tunnel already open to the Registrar
(`ssh -N -L 8790:127.0.0.1:8790 batman@192.168.2.3`):

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt          # Windows: .venv/Scripts/pip
export REGISTRAR_BASE_URL=http://127.0.0.1:8790
export REGISTRAR_API_TOKEN='<token_id>.<secret>'
.venv/bin/streamlit run streamlit_app.py
```

It comes up on <http://localhost:8502>.

## Tests

```bash
.venv/bin/python test_viewer.py
```

No pytest, no browser, no Registrar: `AppTest` runs every page headless against
a canned responder. Covers each page rendering without error, server-side
filtering, sweep correctness and saturation reporting, and two AST checks that
the app contains no mutating HTTP call and builds no write-endpoint path.

## Container

```bash
docker compose config --quiet
docker compose build --pull=false viewer
docker compose up -d viewer
```

- **Network.** The service joins two: `registrar-internal` (external, created by
  the Registrar's Compose project) to reach `http://registrar:8790`, and
  `viewer-edge`, an ordinary bridge carrying the higher priority. The second one
  exists because `registrar-internal` is declared `internal: true`, and Docker's
  isolation rules for an internal network can break a published port depending
  on the daemon's `userland-proxy` setting. Joining an ordinary bridge first
  makes the published port's reachability independent of that setting.
- **Port.** `0.0.0.0:8502` — LAN-reachable on purpose, unlike the Registrar.
  8502 rather than Streamlit's default because `townwatch` holds 8501 on the NAS.
- **Hardening.** Non-root (UID 10002, distinct from the Registrar's 10001),
  read-only rootfs, `cap_drop: ALL`, `no-new-privileges`, pids/memory/CPU limits,
  bounded local logging. The only writable path is a 64 MB tmpfs at `/tmp`,
  which is also `HOME` — Streamlit insists on a writable `~/.streamlit`.
- **Secret.** Compose bind-mounts the token file as-is, preserving host
  ownership and mode, so it must be readable by UID 10002 inside the container:
  `chown root:10002 <file> && chmod 0640 <file>`.

Copy `env.example` to `.env` beside `compose.yml` and set `VIEWER_TOKEN_FILE`
and `REGISTRAR_NETWORK`. Confirm the real network name with `docker network ls`
before the first start.
