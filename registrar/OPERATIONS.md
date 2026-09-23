# Town Registrar NAS prototype operations

This runbook covers the single-leader SQLite prototype on `NASOneMic` at `192.168.2.3`.
The NAS is an infrastructure asset, not an agent. This is not a production-ready service:
availability and security hardening are intentionally limited. Commands below are examples,
not authorization. Creating directories,
starting/stopping containers, changing proxy/firewall configuration, promoting an import,
rotating secrets, or restoring data are live actions requiring explicit operator approval.

## Safety boundaries

- Run exactly one Registrar worker and one writable database volume.
- `/var/lib/town-registrar` must be durable NAS-local storage. **Never** place the live
  SQLite database/WAL on SMB, NFS, Google Drive, rclone, or synchronized storage.
- Prototype HTTP publishes as `127.0.0.1:8790:8790`. Note this NAS does not actually enforce
  host-only reachability for a loopback-bound published port — confirmed 2026-09-23, a plain
  throwaway loopback-bound container is equally reachable from another LAN host over the
  NAS's LAN IP, independent of this service's own config. Operator has accepted this: the
  loopback-only intent was a PoC-stage default, not a long-term restriction, and the LAN is
  already governed by its own controls. Still: do not add router port forwarding or a
  LAN/WAN bind beyond what the NAS itself already exposes.
- Keep token pepper and cursor signing keys distinct, root-readable, and outside Git,
  images, logs, backups, TownSquare events, and shell history.
- Registrar has no Drive credential. Import and verification are not automatic and
  `REGISTRAR_EXPERIMENTAL_VERIFICATION=0` remains set for this prototype.
- Never copy a live DB/WAL/SHM set. Use SQLite's online backup API and validate a separate
  restore.

## Offline preparation

Copy `compose.example.yml` into an operator-controlled deployment directory. Its `.env`
contains paths, not secret values:

```text
REGISTRAR_DATA_DIR=/volume1/home/batman/town-registrar/data
REGISTRAR_BACKUP_DIR=/volume1/home/batman/town-registrar/backups
REGISTRAR_UID=<literal output of id -u on NAS>
REGISTRAR_GID=<literal output of id -g on NAS>
REGISTRAR_TOKEN_PEPPER_FILE=/absolute/root-readable/path/token-pepper
REGISTRAR_CURSOR_KEY_FILE=/absolute/root-readable/path/cursor-signing-key
```

Secret files should be root-owned mode `0600`; the local data and backup directories should
be owned by the configured non-root NAS UID/GID. Verify the mount is local. Validate offline:

```bash
docker compose -f compose.example.yml config --quiet
docker build --pull=false -t town-registrar:local .
docker run --rm town-registrar:local python -m pytest
```

Running the suite locally (outside the image), invoke pytest from the repository root (the parent of `registrar/`, e.g. `python -m pytest registrar/tests/`) — `registrar` resolves as an implicit namespace package, so running pytest from inside `registrar/tests/` itself gives a spurious `ModuleNotFoundError` instead of collecting the tests.

Record source commit, image ID, migration version, test report, and rollback image ID.

## Prepared NAS prototype deployment (live actions; approval required)

Use this layout: `/volume1/home/batman/town-registrar/app` for the release and Compose file,
`data` for SQLite, and `backups` for immutable backup artifacts. From Bishop, after the
approved commit is checked out:

```bash
ssh -F /dev/null batman@192.168.2.3 'mkdir -p /volume1/home/batman/town-registrar/app /volume1/home/batman/town-registrar/data /volume1/home/batman/town-registrar/backups'
rsync -a --delete --exclude .env registrar/ batman@192.168.2.3:/volume1/home/batman/town-registrar/app/
ssh -F /dev/null batman@192.168.2.3 'cp /volume1/home/batman/town-registrar/app/compose.example.yml /volume1/home/batman/town-registrar/app/compose.yml'
```

Create `app/.env` on the NAS with the paths and literal UID/GID shown above. Then, only after the
live-action gate:

```bash
ssh -F /dev/null batman@192.168.2.3 'cd /volume1/home/batman/town-registrar/app && docker compose config --quiet && docker compose build --pull=false registrar && docker compose up -d registrar && docker compose ps registrar'
```

Access it without exposing HTTP on the LAN:

```bash
ssh -F /dev/null -N -L 8790:127.0.0.1:8790 batman@192.168.2.3
curl --fail --show-error http://127.0.0.1:8790/health/ready
```

Confirm the container is non-root, runs one Uvicorn worker, and has no Drive credential or
automatic import/verifier job.

For an update, first make a validated online backup and record the current commit and image
ID. Stage the new tree under `/volume1/home/batman/town-registrar/app.next`, copy the existing
`.env`, validate and build there, then—only after approval—stop `app`, preserve it as
`app.previous`, rename `app.next` to `app`, and start/canary the replacement. Do not remove
`app.previous` or the pre-update backup until acceptance.

```bash
rsync -a --delete --exclude .env registrar/ batman@192.168.2.3:/volume1/home/batman/town-registrar/app.next/
ssh -F /dev/null batman@192.168.2.3 'cp /volume1/home/batman/town-registrar/app/.env /volume1/home/batman/town-registrar/app.next/.env && cp /volume1/home/batman/town-registrar/app.next/compose.example.yml /volume1/home/batman/town-registrar/app.next/compose.yml && cd /volume1/home/batman/town-registrar/app.next && docker compose config --quiet && docker compose build --pull=false registrar'
```

## Prototype acceptance (live actions; approval required)

1. Confirm a validated online backup and restore drill.
2. Confirm loopback-only publishing, secrets, local volume, image ID, and disabled normal
   writers.
3. Start dark, then inspect readiness and logs:

   ```bash
   docker compose -f compose.yml up -d --no-deps registrar
   docker compose -f compose.yml ps registrar
   docker compose -f compose.yml logs --since 10m registrar
   ```

4. Test health through the SSH tunnel. Port 8790 must be unreachable directly from another
   LAN host. Readiness must validate SQLite pragmas and schema.
5. Do not start a Drive import or verifier as part of prototype deployment.
6. Canary local reserve/query behavior without publishing or modifying Drive content.
7. Gradually enable writers. Alert on readiness, allocation/finalization, expired
   reservations, orphans/conflicts, verification lag, rate limits, audit/checkpoint issues,
   and backup failure.

Crier remains read-only and independent. Do not change the Agent Registry.

## Online backup and restore validation

Use Python's SQLite online backup API, creating a new immutable artifact each time. The
example deliberately opens the source read-only and fails if the destination exists:

```bash
docker compose -f compose.yml exec -T registrar python -c \
  "import os,sqlite3; s=sqlite3.connect('file:/var/lib/town-registrar/registrar.db?mode=ro',uri=True); p='/var/backups/town-registrar/registrar-YYYYMMDDTHHMMSSZ.db'; assert not os.path.exists(p); d=sqlite3.connect(p); s.backup(d); d.close(); s.close()"
```

The manifest records SHA-256, UTC time, schema/migrations, row counts, audit checkpoint,
and retention state. Copy DB, manifest, and signed checkpoint to protected append-only
storage outside the Registrar volume; never overwrite an earlier backup.

Restore into a fresh, non-production location. Generate and check the release manifest with
the release tooling when available; until that exists, SHA-256, schema/migration, row-count,
and audit-checkpoint recording is a manual release gate rather than an omitted check.
At minimum, validate SQLite independently:

```bash
docker compose -f compose.yml run --rm --no-deps --volume /restore:/restore:ro registrar \
  python -c "import sqlite3; c=sqlite3.connect('file:/restore/registrar.db?mode=ro',uri=True); assert c.execute('pragma integrity_check').fetchone()==('ok',); assert not list(c.execute('pragma foreign_key_check')); print('SQLite checks: OK')"
```

Validation must require `integrity_check=ok`, empty `foreign_key_check`, supported schema
and migrations, matching hash/row counts, and a valid audit chain through the checkpoint.

Restore is destructive and requires explicit approval. Halt allocations; preserve the
current volume and logs; revalidate the selected artifact; restore to a **new** NAS-local
directory; use the recorded compatible image; start dark; reconcile Drive activity; and
canary before reopening writers. Secrets are restored separately. Migration backout uses
the validated pre-migration backup, never an improvised down migration.

## Backout (live action; approval required)

```bash
docker compose -f compose.yml stop registrar
# Select the recorded rollback digest and compatible validated database.
docker compose -f compose.yml up -d --no-deps registrar
```

Backout stops allocations but never deletes/renames Drive objects or rewinds the ledger.
Preserve DB/WAL, logs, audit evidence, image digest, and migration artifacts. Disable only
optional Crier enrichment. P0/P1 work may use the signed, auditable break-glass path; later
reconcile published-but-unfinalized and break-glass posts.
