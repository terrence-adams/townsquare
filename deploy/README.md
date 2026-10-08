# Deployment boundary

This directory contains templates only. `release.env` and every secret/config it
references stay outside Git. The ledger and Viewer listen only on host loopback;
remote use is an authenticated SSH tunnel. Do not change a port mapping to a LAN
address without a separately reviewed TLS/mTLS, firewall, and no-DNAT evidence set.

`TOWNSQUARE_RECEIPT_HASH_KEY_FILE` and `TOWNSQUARE_CONTEXT_MANIFEST` are mandatory.
The service must fail closed when either is absent or unreadable. Provision distinct
release principals/tokens through the documented offline credential procedure; do
not reuse fixtures, developer identities, or the Viewer token for writes.

Revere, wake/runner, and any notifier are intentionally absent from the core profile.

## NAS canary read-gateway upgrade

`prepare_canary_gateway_upgrade.py` builds a verified, secret-free upgrade bundle
from the current clean Git commit. It reuses only the cached wheelhouse and public
governance inputs from a previously verified canary package. Generated bundles go
under `deploy/out/`, which is intentionally ignored by Git.

The matching `install_canary_gateway_upgrade.sh` installer is scoped to the
`townsquare-canary-20261007-a` non-authoritative canary. It builds the three images
offline before downtime, preserves the current package as a rollback directory,
reuses the verified databases and credential files without printing them, starts
the six-service Compose profile, and runs the bounded public-read acceptance suite.

Example preparation command (the seed path contains no credential reads):

```text
python deploy/prepare_canary_gateway_upgrade.py --seed-package <verified-package-directory>
```

The command prints the bundle path, bundle SHA-256, installer path, and installer
SHA-256 required by the NAS installer. The generated bundle contains no runtime
credentials and no canary signing secret.
