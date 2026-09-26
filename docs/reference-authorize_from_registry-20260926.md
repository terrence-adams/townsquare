# Reference copy: `authorize_from_registry.sh`, as it actually runs today

Fetched 2026-09-26 directly from the NAS (192.168.2.3, user `batman`), path
`/share/home/batman/registry/authorize_from_registry.sh` (same file also visible
at `/share/User Homes/batman/registry/...` and `/volume1/home/batman/registry/...`
-- three mount aliases, one inode). Remote `sha256sum`: matches this copy exactly
(verified byte-for-byte after transfer). Remote `stat` mtime: 2026-09-12 23:51:20 UTC.

This exists because helio-gracie's checkpoint on the TownSquare tracker's offsite-
registration design (decision 6) found that design cited a superseded description of
this script, and nobody doing that design had read the real file. Fetched here so
ip-man (Read/Grep/Glob only, no Bash) can read it without needing NAS access himself,
per [[dojo-scoped-work-assignment]].

```sh
#!/bin/sh
# authorize-from-registry: the fleet mesh sync.
#
# Pulls every ACTIVE registered agent's SSH public key from the registry (the
# single source of authority) and appends any that are missing to this host's
# ~/.ssh/authorized_keys. Idempotent, additive, never removes. This is the
# doctrine's per-host local-authorize step (fleet-key-exchange.md), automated
# and sourced from one authority instead of N hand-appends.
#
# Usage:  authorize_from_registry.sh [registry_url] [this_agent_name]
#   registry_url   default http://192.168.2.3:8789
#   this_agent     if given, the host's own key is excluded (no self-authorize)
#
# Run it on a cadence, or on a Revere "new key" backhaul notice.
set -eu
REG="${1:-${REG_URL:-http://192.168.2.3:8789}}"
SELF="${2:-${REG_SELF:-}}"
AK="$HOME/.ssh/authorized_keys"

mkdir -p "$HOME/.ssh"; chmod 700 "$HOME/.ssh"
[ -f "$AK" ] || { : > "$AK"; chmod 600 "$AK"; }

URL="$REG/authorized_keys"
[ -n "$SELF" ] && URL="$URL?exclude=$SELF"

TMP="$(mktemp)"
if ! curl -fsS -m 10 "$URL" -o "$TMP"; then
    echo "authorize_from_registry: registry unreachable at $REG (UNKNOWN, not empty)" >&2
    rm -f "$TMP"; exit 1
fi

added=0
while IFS= read -r key; do
    [ -z "$key" ] && continue
    if ! grep -qxF "$key" "$AK"; then
        printf '%s\n' "$key" >> "$AK"
        added=$((added + 1))
    fi
done < "$TMP"
rm -f "$TMP"

sort -u "$AK" -o "$AK"
chmod 600 "$AK"
echo "authorize_from_registry: $added key(s) added from $REG; authorized_keys now $(wc -l < "$AK") lines"
```

**Orchestrating session's own read, offered only as a starting point for ip-man's
own judgment, not a ruling:** line 27 uses `curl -fsS -m 10 ... -o "$TMP"`, checked
by `if ! curl ...`, so a failed or empty pull is caught before anything touches
`authorized_keys` (line 28-29 warn and exit 1 untouched). Writes are additive only
(`grep -qxF` before each append, line 35), deduplicated at the end (line 42), and
`authorized_keys` is never truncated except on first creation when absent (line 21).
This looks like the opposite of a script that silently empties the keyring on a bad
pull -- worth checking whether that changes what the prior, superseded-script-based
design assumed.
