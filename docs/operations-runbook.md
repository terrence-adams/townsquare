# TownSquare MVP operations

This is a prepared package, not authorization to deploy. Before any NAS action,
obtain operator approval, execute the read-only preflight, and retain its evidence.
Run `docker compose --env-file /secure/release.env -f compose.yml -f compose.nas.yml config`
and reject output with a non-loopback published port, an image tag, or a missing
secret/config. Then pull the exact release-manifest digests using an approved
offline cache, start the core stack, and inspect health from NAS loopback only.

The `migrate` one-shot service is the only migration runner. Do not scale `ledger`
above one replica: SQLite has one writer. A busy/locked response is retryable only
with the same idempotency key; investigate sustained readiness failure rather than
restarting blindly. The aggregate release check is ledger readiness plus Viewer
health and current backup-manifest verification; it does not pretend registry and
ledger share a transaction.

Provision distinct offline-issued principals for operator, writer, Viewer reader,
notifier, registry mutation, and registry audit append. Load secret files with
owner-only host permissions; do not use fixture identities. `TOWNSQUARE_RECEIPT_HASH_KEY`
is mounted from the required secret file and context comes only from the required
manifest config. Google Drive is neither a source of authority nor a runtime dependency.

To execute an encrypted backup use the `operations` profile and retain the output
checkpoint in the approved external signed journal. Perform a restore drill into a
new empty directory before accepting a release. Revere/wake is not shipped or
available in this core stack.
