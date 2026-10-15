# Vertical Authorized Mutation Endpoint — Francis Runtime Preflight

**Date:** 2026-10-10  
**Scope:** Read-only deployment/runtime preflight for the reviewed bounded MVP  
**Status:** **OPEN admission is not blocked; deployment is blocked pending the runtime decisions listed below.**  
**Operating boundary:** No installation, configuration, deployment, port opening, certificate creation, service or credential access, permission change, network scan, or provider contact was performed.

## Decision context

- The approved idempotency policy is **Option A**: authenticate, perform exact committed-receipt lookup, and require fresh authorization only when a new mutation would occur.
- Credential revocation blocks receipt recovery and mutation. Assignment or policy changes block new mutations but do not erase access to a safe exact receipt for a transaction already committed by that authenticated identity.
- **Option C**, a separate receipt-recovery capability, is explicitly parked as a future feature and is not part of this MVP.
- Venom is not an eligible implementation or deployment owner. Eddie remains reserved for operator engagement and is not the service implementation/deployment owner.

## Executive finding

The repository evidence supports a Python 3.11-or-newer append-only ledger proof of concept packaged through `setuptools.build_meta`. It does not identify a deployment-ready runtime target, port, TLS asset, supervisor, container definition, log destination, health-check mechanism, or executable SMB permission-removal procedure.

The reviewed endpoint documents prefer either the NAS at `192.168.2.3` or another approved non-Venom host with an exclusive ledger write mount. The NAS is only a candidate: it has not been accepted or activated. No non-Venom host or namespace can be recommended by name from the retained evidence because the relevant `hosts.yml` lines were unavailable. The correct recommendation is therefore to select a target using the decision criteria below, not to infer one.

These unknowns do not prevent the work item from entering **OPEN** for implementation. They do prevent deployment, runtime verification, and cutover.

## Confirmed facts

| Area | Confirmed evidence | Preflight consequence |
| --- | --- | --- |
| Application/runtime | `pyproject.toml` declares Python `>=3.11`, uses `setuptools.build_meta`, and describes an append-only ledger POC. | Build work should begin with the existing Python/setuptools route. |
| Deployment artifacts | Among deployment/configuration patterns inspected, the Vertical repository contains only `README.md` and `pyproject.toml`. No Dockerfile, Compose file, `.service` unit, package/requirements file, deploy/infra/ops config, or service script was present in the retained inventory. | No container or service-manager route is currently evidenced. |
| Candidate placement | Final endpoint documents prefer NAS `192.168.2.3` or an approved non-Venom host with an exclusive write mount. | Placement requires an explicit owner decision. The NAS address is not deployment authorization. |
| Ownership boundary | Francis owns non-Venom packaging, deployment administration, and certificate/secret custody. Venom is excluded as implementation/deployment owner; Eddie is preserved for operator engagement. | Assign an eligible non-Venom runtime owner before deployment. |
| Transport intent | Final endpoint documents require LAN TLS with a pinned certificate. | A certificate source and pin-distribution procedure must be selected before deployment. |
| Ledger access target state | At cutover, the service becomes the sole ledger writer; clients lose direct write access or are remounted read-only. | Permission cutover is required before production mutation traffic is admitted. |
| Cutover description | The current cutover treatment is documentation only: remove client write access/remount read-only after criteria and operator cutover. | The exact SMB/ACL mechanism remains to be designed and verified. |
| Repository state | Vertical HEAD is `40058d2...`; Agentic HEAD is `5aea...`; TownSquare HEAD is `aa2a...`. All three work areas had reported dirty or untracked material. | Do not derive a release artifact from an unspecified dirty tree. Pin the intended source state first. |
| Host inventory | `hosts.yml` has reported hash prefix `7a455a...`. | The artifact exists, but no host claim may be made because its relevant raw lines were not retained. |

## Unknowns that must remain unknown

The retained evidence does not establish:

- the approved non-Venom host or namespace;
- the current owner/custodian of any candidate host or namespace;
- a service bind address;
- a listening port, current port owner, or port availability;
- a certificate issuer, existing certificate identity, certificate path, private-key location, renewal method, or pin custodian workflow;
- whether the endpoint will run directly under a host service manager or in a container;
- a service name, account, working directory, environment-file location, restart policy, or startup ordering;
- a container image definition, image registry, tag/digest convention, or Compose/orchestrator manifest;
- an application log sink, retention setting, correlation fields, or redaction configuration;
- a health endpoint, process watchdog, readiness check, or existing monitoring integration;
- the SMB share name, mount path, client identities/groups with ledger write access, effective ACLs, or exact mechanism for revoking direct writes;
- whether NAS `192.168.2.3` satisfies Python/runtime, resource, service-supervision, TLS, logging, health, exclusive-mount, and ownership requirements.

No live checks were performed to resolve these items. In particular, this report contains no evidence of port availability, reachable services, certificate contents, current permissions, or NAS capability.

## Packaging and build route

### Evidenced route

Use the repository's existing Python packaging boundary:

1. Python 3.11 or newer.
2. PEP 517 build through `setuptools.build_meta`.
3. Produce an immutable application artifact from a specifically approved, clean source revision.
4. Record the resulting artifact hash and the exact source commit used.

### Not yet evidenced

There is no retained evidence for a wheel-build command, lockfile, dependency-install policy, executable entry point, runtime environment, container image, deployment bundle, or release pipeline. These should be implemented only after the runtime target and supervisor route are decided. A container should not be introduced solely by assumption; likewise, direct host installation should not be assumed.

## Recommended target decision criteria

Do not select the NAS or any other host by inference. The project owner should approve a named non-Venom target only after read-only evidence confirms all of the following:

1. **Ownership:** A named non-Venom administrator accepts runtime ownership; Eddie remains outside deployment ownership and available for operator engagement.
2. **Isolation:** The service can run under a dedicated identity and namespace without granting agents direct ledger-write credentials.
3. **Exclusive write path:** The target can hold the sole read-write mount to the ledger at cutover while agent/client mounts are removed or made read-only.
4. **Runtime fit:** Python 3.11+ and the selected packaging/supervision route are supported without an unapproved host modification.
5. **Network fit:** A project-owner-approved bind address and port are available and can be exposed only to the intended LAN clients.
6. **TLS fit:** An approved LAN certificate source, private-key custodian, renewal procedure, and client pin-distribution mechanism exist.
7. **Lifecycle:** The target has an approved service manager or container supervisor with startup, restart, stop, and rollback behavior.
8. **Observability:** Existing logging and health facilities can capture availability and mutation-path failures without logging credentials, permit secrets, raw Registry data, or event content.
9. **Recoverability:** The deployment can be rolled back without restoring direct client write permission automatically or risking two concurrent ledger writers.

If the NAS satisfies these criteria and its owner accepts custody, it remains a viable candidate. Otherwise, choose another approved non-Venom host. The retained evidence does not support ranking candidates.

## Service manager/container, logging, and health

No current route is confirmed. The project owner and runtime owner must select one of these bounded patterns:

- **Existing host supervisor:** package the Python service for the target's already-approved service manager, using its native log capture and health/watchdog facility.
- **Existing container supervisor:** add a minimal image and deployment manifest only if the selected target already has an approved container runtime and ownership model.

The MVP needs a minimal health signal sufficient to distinguish process availability from mutation-path readiness. The exact endpoint or watchdog is undecided. Logs should include safe correlation identifiers, outcome, latency, and retry/replay classification while excluding secrets and ledger/event content. These are implementation inputs after a route is selected, not evidence that such facilities already exist.

## Direct SMB ledger-write permission surface and cutover

### Confirmed target state

- Before cutover, agents/clients may still possess a direct SMB ledger-write path.
- After approved cutover, the Vertical service is the sole writer.
- Agent/client access is removed or remounted read-only.

### Unknown permission surface

The retained evidence does not name the share, mount, ACL entries, groups, service identity, or client identities. It also does not prove that existing agent writes use filesystem ACLs, share permissions, mount flags, stored credentials, or a combination. Therefore no exact removal command can be recommended yet.

### Required later cutover evidence

Before cutover, the runtime owner must produce a redacted read-only inventory showing:

- the ledger share and canonical mount path;
- every identity or group with effective write permission;
- the dedicated service identity and its exclusive required access;
- the approved mechanism that removes direct client writes or remounts clients read-only;
- a negative write test for a representative client after the change;
- a positive authorized-write test through the service;
- confirmation that only one service instance can hold the write role.

Permission changes themselves require explicit operator authorization and are outside this preflight.

## Decisions required before deployment

The project owner/operator must decide or approve each item below. Implementation may proceed while these are open when the code can remain target-neutral; deployment may not.

1. **Target:** Name and approve the non-Venom host and namespace. Explicitly accept or reject NAS `192.168.2.3` after capability evidence is available.
2. **Runtime owner:** Name the non-Venom administrator accountable for deploy, rollback, service health, and certificate/secret custody. Confirm Eddie remains the operator-engagement path only.
3. **Network contract:** Approve bind address, port, allowed LAN client scope, and the owner responsible for resolving any port conflict.
4. **TLS contract:** Approve certificate source/issuer, service identity/SAN, key custodian and storage, renewal, client pin distribution, and pin rollover.
5. **Packaging/supervision:** Choose host service manager or existing container supervisor, and approve the artifact form and immutable version identifier.
6. **Runtime configuration:** Approve service identity, working directory, ledger mount, Registry dependency location, secret injection source, and restart/startup policy.
7. **Logging/health:** Approve the existing log destination, retention/redaction boundary, minimal health/readiness mechanism, and alert owner.
8. **Source baseline:** Choose the exact clean commit and disposition of reported dirty/untracked files before producing a release artifact.
9. **SMB cutover:** Approve the exact ACL/share/mount changes, the client identities affected, validation tests, sequencing, and rollback boundary.
10. **Activation:** Give a separate explicit deployment and cutover authorization after build/test evidence exists. This preflight is not that authorization.

## Admission and dependency assessment

| Gate | Result | Reason |
| --- | --- | --- |
| Admit endpoint work item to OPEN | **PASS** | The approved behavior and Python packaging baseline are sufficient to begin target-neutral implementation. Runtime unknowns can be maintained as explicit interfaces/configuration inputs. |
| Begin packaging implementation | **PASS WITH CONSTRAINT** | Build around the existing Python/setuptools route only; do not assume container or service-manager specifics. |
| Produce a deployable target-specific bundle | **BLOCKED** | Target, supervisor/container route, configuration, source baseline, TLS, and artifact contract are undecided. |
| Deploy or open a listening endpoint | **BLOCKED** | No approved target, owner, bind address, port, or TLS asset is evidenced. |
| Perform SMB sole-writer cutover | **BLOCKED** | Effective permission surface and exact revocation mechanism are unknown, and operator authorization is required. |

These are deployment dependencies, not grounds to expand the bounded MVP acceptance criteria or delay OPEN admission.

## Evidence and reproducibility record

This report was produced from the retained Ip Man read-only evidence payload supplied by the parent task. No new workspace read or shell command was run during report creation.

### Complete retained outputs

The retained payload states that the exact repository inventory, Git, and file-hash command outputs were complete. Reported identifiers available to this report are:

- Vertical HEAD: `40058d2...`
- Agentic HEAD: `5aea...`
- TownSquare HEAD: `aa2a...`
- `hosts.yml` hash: `7a455a...`

Only prefixes were included in the supplied summary; this report does not expand them or claim full SHA values. Key evidence-file hashes were reported in the parent context but were not included verbatim in the payload available to this report, so they are not reproduced here.

### Search-output limitation

The broad and narrowed `rg` outputs were truncated. Only the visible search lines summarized in the retained payload are treated as evidence. This report does **not** claim a complete raw search transcript or prove the absence of every possible operational reference outside the inspected patterns. The exact inventory result is the basis for the statement that no named deployment artifact was present.

### Commands represented by the retained evidence

The retained payload describes these read-only evidence categories; exact command strings and full raw outputs were not included in the supplied summary and therefore are not fabricated here:

- repository file inventory;
- broad and narrowed `rg` searches for runtime, host, port, TLS, packaging, service, health, logging, SMB, ledger, permissions, Venom, and Eddie terms;
- Git status and `rev-parse HEAD` for Vertical, Agentic, and TownSquare;
- hashes of cited evidence files.

### Francis process flag

Before the retained evidence was supplied, Francis made five read-only shell attempts. Each was rejected before process creation with `helper_unknown_error: apply deny-read ACLs`; no command executed. The attempted categories were:

1. PowerShell project inventory plus `rg --files` from the default working directory.
2. PowerShell project inventory plus `rg --files` from the project working directory.
3. `cmd.exe dir` from the project working directory.
4. PowerShell `Get-Location` from `C:\Workspace`.
5. Default-shell `pwd`.

After instruction to stop, no shell route was retried. One MCP resource-list call had returned plugin catalog metadata only and supplied no workspace evidence. No runtime mutation resulted from any attempt.

## Cost comparison

| Cost class | Best-current estimate |
| --- | --- |
| MVP implementation | **Unknown.** No implementation timing or accepted artifact build record was included in the retained evidence. |
| Governance/review for this preflight | One bounded Francis evidence review and one Markdown report, plus five failed pre-evidence shell-launch attempts that executed no command. Exact elapsed engineering time and token cost are unavailable. |
| Delta | **Unknown.** A numeric comparison would be invented. Optional production-hardening review is deferred; this report limits itself to runtime decisions necessary for deployment and the required implementation-versus-governance disclosure. |

## Recommendation

Admit the endpoint work item to **OPEN** and implement it target-neutrally against the approved Option A behavior, with Option C recorded as a future feature. In parallel, have the project owner resolve the ten deployment decisions above from read-only host and permission evidence. Do not authorize deployment until a named non-Venom target, owner, network/TLS contract, supervisor route, source baseline, observability path, and SMB sole-writer cutover procedure are approved.

