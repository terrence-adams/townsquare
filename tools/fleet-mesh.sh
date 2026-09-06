#!/usr/bin/env bash
#
# TownSquare — Copyright (c) 2026 Yes.No.Maybe
# Licensed under the PolyForm Noncommercial License 1.0.0. See LICENSE.
# Noncommercial use is free. Commercial use requires a separate licence.
#
# fleet-mesh.sh — build and maintain an SSH mesh across a fleet, from one place.
#
# TownSquare assumes agents can reach each other: the poller fetches from the
# index service, stdio transports tunnel over SSH, and host-to-host automation
# needs no human in the path. This builds that substrate.
#
#   1. ensures every host has its own ed25519 key (creates one only if absent)
#   2. collects every PUBLIC key into one canonical set
#   3. installs that set on every host — appending and deduping, never
#      truncating, with a timestamped backup taken first
#   4. skips hosts that are offline; re-run later to enrol them
#
# PRIVATE KEYS NEVER MOVE. Each host generates its own; only public halves travel.
#
# Usage:
#   fleet-mesh.sh [-f HOSTSFILE] [-u USER] [--dry-run]
#
# HOSTSFILE format — one host per line, "name [address]".
# Omit the address to resolve by name, which is what you want for machines that
# move between networks.
#
#     server-a   10.0.0.11
#     server-b   10.0.0.12
#     laptop-a
#
# WHY A FULL MESH: where hosts have specialised roles, they must call each other
# by design. Hub-and-spoke does not reduce blast radius, it CONCENTRATES it in
# the hub and adds a single point whose loss halts all inter-host work. If you
# need to limit reach, the control is per-key scope — from= restrictions or
# forced commands in authorized_keys — not topology.
set -uo pipefail

HOSTSFILE="./fleet-hosts"
SSH_USER="${FLEET_USER:-$USER}"
DRY_RUN=0

while [ $# -gt 0 ]; do
    case "$1" in
        -f) HOSTSFILE="$2"; shift 2 ;;
        -u) SSH_USER="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) sed -n '7,32p' "$0"; exit 0 ;;
        *) echo "unknown argument: $1" >&2; exit 2 ;;
    esac
done

[ -f "$HOSTSFILE" ] || { echo "no hosts file: $HOSTSFILE" >&2; exit 1; }

LOCAL="${FLEET_LOCAL:-$(hostname -s 2>/dev/null | tr '[:upper:]' '[:lower:]')}"
SSH="ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
KEYS="$WORK/fleet_authorized_keys"; : > "$KEYS"

names=(); addrs=()
while read -r name addr _; do
    case "$name" in ''|\#*) continue ;; esac
    names+=("$name"); addrs+=("${addr:-$name}")
done < "$HOSTSFILE"

target() {  # target <index> -> user@address, or empty for the local host
    local n="${names[$1]}"
    [ "$(echo "$n" | tr '[:upper:]' '[:lower:]')" = "$LOCAL" ] && return 1
    echo "$SSH_USER@${addrs[$1]}"
}

run() {  # run <index> <command> — locally for this host, over ssh otherwise
    local t; if t=$(target "$1"); then $SSH "$t" "$2"; else bash -c "$2"; fi
}

[ "$DRY_RUN" -eq 1 ] && echo "== DRY RUN — no host will be modified =="

echo "== 1. ensure every host has a fleet key =="
for i in "${!names[@]}"; do
    h="${names[$i]}"
    printf '  %-14s ' "$h"
    out=$(run "$i" "
        [ -f \$HOME/.ssh/id_ed25519.pub ] || {
          $([ "$DRY_RUN" -eq 1 ] && echo 'echo WOULD-GENERATE; exit 0')
          mkdir -p \$HOME/.ssh && chmod 700 \$HOME/.ssh
          ssh-keygen -q -t ed25519 -f \$HOME/.ssh/id_ed25519 -N '' -C '$SSH_USER@$h-fleet'
          echo GENERATED
        }
        cat \$HOME/.ssh/id_ed25519.pub 2>/dev/null" 2>&1)
    case "$out" in *GENERATED*) printf 'generated  ' ;; *WOULD-GENERATE*) printf 'would generate  ' ;; esac
    pub=$(echo "$out" | grep -E '^ssh-' | head -1)
    if [ -n "$pub" ]; then
        echo "$pub" >> "$KEYS"; echo "ok"
    elif echo "$out" | grep -qiE 'timed out|no route|refused|could not resolve|name or service'; then
        # A host that is off is NORMAL, not a fault. Laptops come and go.
        echo "offline — skipped, will enrol on a later run"
    else
        echo "FAILED: $(echo "$out" | tail -1)"
    fi
done

echo
echo "== 2. canonical fleet key set =="
sort -u "$KEYS" -o "$KEYS"
ssh-keygen -lf "$KEYS" 2>/dev/null | sed 's/^/  /' || echo "  (none collected)"
[ -s "$KEYS" ] || { echo; echo "no keys collected — nothing to install"; exit 1; }

echo
echo "== 3. install on every reachable host =="
for i in "${!names[@]}"; do
    h="${names[$i]}"
    printf '  %-14s ' "$h"
    if [ "$DRY_RUN" -eq 1 ]; then
        echo "would install $(grep -c . "$KEYS") keys"; continue
    fi
    if t=$(target "$i"); then
        scp -q -o BatchMode=yes "$KEYS" "$t:/tmp/_fleet_keys" 2>/dev/null \
            || { echo "offline or unreachable — skipped"; continue; }
    else
        cp "$KEYS" /tmp/_fleet_keys
    fi
    run "$i" "
        mkdir -p \$HOME/.ssh && chmod 700 \$HOME/.ssh
        touch \$HOME/.ssh/authorized_keys
        cp \$HOME/.ssh/authorized_keys \$HOME/.ssh/authorized_keys.bak.$STAMP 2>/dev/null
        cat /tmp/_fleet_keys >> \$HOME/.ssh/authorized_keys
        sort -u \$HOME/.ssh/authorized_keys -o \$HOME/.ssh/authorized_keys
        chmod 600 \$HOME/.ssh/authorized_keys
        rm -f /tmp/_fleet_keys" >/dev/null 2>&1 \
        && echo "installed" || echo "install FAILED"
done

echo
echo "== 4. verify every direction =="
for i in "${!names[@]}"; do
    printf '  from %-12s ' "${names[$i]}"
    for j in "${!names[@]}"; do
        probe="ssh -o BatchMode=yes -o ConnectTimeout=6 $SSH_USER@${addrs[$j]} true"
        if [ "$DRY_RUN" -eq 1 ]; then printf '%s=skip ' "${names[$j]}"; continue; fi
        if out=$(run "$i" "$probe" 2>&1); then printf '%s=OK ' "${names[$j]}"
        elif echo "$out" | grep -q 'Permission denied'; then printf '%s=DENY ' "${names[$j]}"
        else printf '%s=- ' "${names[$j]}"; fi
    done
    echo
done
