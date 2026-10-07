# Fresh NAS canary implementation

This directory is implementation material for `CANARY / NON-AUTHORITATIVE`
only. It does not authorize a build, NAS write, start, activation, archive,
restore, cleanup, or legacy inspection. The source commit/tree and cached
Python base digest remain deliberately unfilled until review and checkpoint.

## Required order

1. From a clean checkout of the reviewed commit, record and independently
   verify its exact commit and tree object IDs. Do not derive either value from
   a mutable branch name or from the runtime environment.
2. Run the zero-write checks from the reviewed design. Any missing, stale, or
   ambiguous check is `BLOCKED_BEFORE_NAS_WRITE`. Do not inspect a legacy
   path/container as a workaround.
3. Validate the source archive with `python -m canary.safe_archive ARCHIVE DEST --validate-only`.
   Create/extract only under `/volume1/Docker/townsquare-canary-20261007-a`
   after the gate, then revalidate the root and every resolved mount.
4. Build all three images from the exact source archive with the nine identity
   build arguments, an already-cached `python@sha256:<reviewed-digest>` base,
   `--network=none`, and `--pull=false`. Tag them with the exact reviewed
   source commit. Record image IDs/config digests and labels; never invent a
   RepoDigest.
5. Populate `config/canary.env` from `canary.env.example` with only the exact
   eight non-secret identity fields. Treat that independently reviewed file as
   the trusted release identity, render Compose as JSON, and run
   `python -m canary.validate_compose RENDERED.json --identity-env config/canary.env`
   before any listener. The validator rejects extra, missing, duplicate,
   placeholder, or mismatched identity fields.
6. Run both migrators manually. Run `python -m canary.bootstrap` only against
   the empty migrated Ledger DB and absent destinations; its stdout is
   non-secret metadata. Provision separate consumer-owned copies of each
   directional readiness value and confirm the two directions differ without
   printing either value.
7. Start services manually. Registry delivery remains `manual`; the only
   delivery action is the named one-shot `python /app/app.py --deliver-audit-once`.
   No periodic or post-trigger thread exists.

## Stop without deletion

```sh
docker compose --project-name townsquare-canary-20261007-a \
  --project-directory /volume1/Docker/townsquare-canary-20261007-a/compose \
  --file /volume1/Docker/townsquare-canary-20261007-a/compose/compose.canary.yml \
  --env-file /volume1/Docker/townsquare-canary-20261007-a/config/canary.env \
  stop --timeout 30

docker compose --project-name townsquare-canary-20261007-a \
  --project-directory /volume1/Docker/townsquare-canary-20261007-a/compose \
  --file /volume1/Docker/townsquare-canary-20261007-a/compose/compose.canary.yml \
  --env-file /volume1/Docker/townsquare-canary-20261007-a/config/canary.env \
  ps --all
```

Verify the NAS LAN listeners on ports `18790` and `18502` are closed. Do not
run `down`, remove, prune, rename, archive, restore, or delete.
