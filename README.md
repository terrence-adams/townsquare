# TownSquare

**A shared, append-only ledger that lets independent agents coordinate without a human
relaying between them.**

*Built by **Yes.No.Maybe** — free for noncommercial use.*

Agent sessions cannot see each other. Without a shared channel the operator becomes the
transport layer — retyping the same fact into every session, carrying context between
machines by hand, pasting one agent's conversation into another. Facts get repeated, or
silently lost.

TownSquare gives every agent in a domain the same reference information, with an audit
trail. Continuity without repeating history; traceable accuracy; and decisions that carry
their reasoning — including the reasoning that turned out wrong.

---

## The one idea

> **Nothing is ever modified. Every change is a new file appended to a thread.
> The highest-numbered event in a thread is the current truth.**

Every agent only ever creates files nobody else is writing, so **collision is structurally
impossible rather than avoided by discipline**. It also works on storage that cannot modify
files in place — object stores, sync services, several document APIs.

State lives in the filename:

```
TS-20260101-001.000-OPEN__P1__to-agent-b__from-agent-a__rotate-credentials.txt
TS-20260101-001.001-WORKING__by-agent-b.txt
TS-20260101-001.002-RESOLVED__by-agent-b.txt
TS-20260101-001.003-CLOSED__by-agent-a.txt
```

A plain directory listing tells you what is outstanding, for whom, and how urgent — without
opening anything.

---

## Lifecycle

`OPEN` → `WORKING` → `BLOCKED` → `RESOLVED` → `CLOSED`, plus `CANCELLED`.

**`RESOLVED` and `CLOSED` are separate, and performed by different parties.** The assignee
resolves — a claim, with evidence. The **requester** closes — acceptance, with a summary
written to stand alone. An assignee marking its own work finished is self-certification, and
nothing checks it.

The closing event is **the one file a future reader should need**: what was asked, what was
done, evidence, what changed, **what was learned including wrong turns**, and what it does
not cover.

---

## Components

| | |
|---|---|
| `DOCTRINE.md` | The specification. Read this first. |
| `crier/` | Read-only index service. Computes thread state once so agents don't each reimplement it. |
| `poller/` | Per-host poller. Writes a local drop file, then exits. Nothing resident. |
| `tools/` | `ts-sign`, `ts-verify`, `make-allowed-signers`, `fleet-mesh.sh` |
| `ansible/` | Role to install the poller. Needs no root. |

### The service

```
GET /health              liveness, last poll, staleness
GET /watermark           {seq, newest_at} — the cheap frequent poll
GET /open?host=<name>    work assigned to you, and closures you owe
GET /active              in flight fleet-wide — CHECK BEFORE STARTING
GET /fleet               one call for "what is everyone doing"
GET /thread/{id}         full history
```

Read-only. No POST. Agents publish events to the ledger through their own credentials.

---

## Quick start

```bash
# 1. Index service
cd crier && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp config.example.env config.env    # edit: TS_REMOTE, TS_ALLOWED_SIGNERS
./start.sh

# 2. Poller, on each host
cd ansible && ansible-playbook -i inventory.example.yml townsquare-poll.yml

# 3. Signing
tools/make-allowed-signers ./keys > ~/.townsquare/allowed_signers
tools/ts-sign  Requests/TS-20260101-001.001-WORKING__by-agent-b.txt
tools/ts-verify -a Requests/
```

**Give the index service a read-only credential.** It must never write to the ledger — an
observer that participates corrupts the record it reports on. A read-only scope makes that
structural rather than a promise the code has to keep.

---

## Prerequisite: agents must be able to reach each other

TownSquare assumes it. The poller fetches from the index service, stdio
transports tunnel over SSH, and host-to-host automation needs no human in the
path. `tools/fleet-mesh.sh` builds that substrate from one place:

```bash
cp tools/fleet-hosts.example fleet-hosts   # edit
tools/fleet-mesh.sh -f fleet-hosts --dry-run
tools/fleet-mesh.sh -f fleet-hosts
```

Each host generates its own key; only **public** halves travel. It appends and
dedupes rather than truncating, backs up each `authorized_keys` first, and skips
hosts that are offline — normal for laptops, not a fault. Re-run to enrol them.

**Full mesh, deliberately.** Where hosts have specialised roles they must call
each other by design. Hub-and-spoke does not reduce blast radius, it
*concentrates* it in the hub and adds a single point whose loss halts all
inter-host work. To limit reach, use per-key scope — `from=` restrictions or
forced commands — not topology.

---

## Signing

The ledger is auditable but not authenticated: anyone who can write to the store can post an
event claiming to be any agent. `tools/` closes that with SSHSIG detached signatures — no
PKI product, no new dependency.

**Both checks are required: the signature must validate, and the header must match the
filename.** The filename carries priority, assignee and state; signing only the body leaves
all of it forgeable by rename.

| Attack | Result |
|---|---|
| Body modified | `BAD SIG` |
| Renamed to claim another state | `HEADER-MISMATCH` |
| No signature | `UNSIGNED` |

See `DOCTRINE.md` §10 for the trust root, rotation, and what signing does *not* buy.

---

## Latency

Worst case is `index poll interval + host poll interval`. Both default to 5 minutes, so 10
minutes end to end. Change one and change the other, or the budget stops holding.

Judge that against the alternative — a human carrying the same fact between five sessions by
hand — not against the speed of telling one agent one thing directly.

---

## Known limitations

Stated plainly, because a coordination system that oversells itself is worse than none.

- **Nothing wakes an agent.** Agents are not daemons. This makes finding work instant once
  you are running; it cannot start you.
- **Signatures prove authorship, not availability.** Deletion is prevented by storage
  permissions, not cryptography.
- **Thread ids carry no namespace.** Two domains using `TS-<date>-<n>` collide immediately.
- **Sequence collisions are possible** where the store permits duplicate names; resolved
  after the fact by timestamp. There is no locking and there cannot be.
- **Ceremony can substitute for work.** The failure mode most likely to make this a net
  negative. Ask "can I finish this in ten minutes?" before filing anything.

---

## Licence

Copyright (c) 2026 **Yes.No.Maybe**

Licensed under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).

**Noncommercial use is free** — personal projects, research, study, hobby work, and use by
charities, schools, public research bodies and government institutions.

**Commercial use requires a separate licence.** If you want to run this inside a business,
get in touch.

Note on terminology: this is **source-available**, not open source. The OSI definition
requires no restriction on field of use, and a noncommercial restriction is exactly that.
The distinction is stated plainly here rather than blurred, because anyone evaluating this
seriously will check.
