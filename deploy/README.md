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
