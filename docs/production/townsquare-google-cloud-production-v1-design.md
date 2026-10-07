# TownSquare Google Cloud production v1 design

**document_id:** TS-GCP-PROD-V1-DESIGN-20261006

**version:** 0.1 proposed architecture

**status:** PROPOSED FUTURE PRODUCTION-V1 ARCHITECTURE — NOT DEPLOYMENT AUTHORIZATION, NOT CURRENT RELEASE EVIDENCE

**owner:** Ip Man

**target:** Google Cloud

**source baseline:** `8505cf5f9e97f7661e3458e03864c77e1f486f5b`

**cloud documentation retrieved:** 2026-10-06

## 1. Decision boundary

This document defines the intended first production release on Google Cloud. It does not change or delay the NAS MVP, its acceptance criteria, its Compose/runtime package, the Doctrine, the TownSquare governance work, or any current deployment decision. It authorizes no project creation, billing, DNS, IAM, build, migration, model call, or cutover.

The production release must preserve the product boundary:

- TownSquare is the vendor-neutral coordination and auditable record layer.
- The Doctrine and its companion governance documents remain infrastructure-neutral.
- Vertical consumes TownSquare references and evidence as a work model/projection; it is not a replacement ledger.
- Wonderland consumes read-only source events and produces separately identified observations/findings; it cannot write source history, satisfy a gate, or authorize work.
- Google Cloud is a replaceable deployment target. Google Drive is not authoritative and is not a production runtime dependency.

The current source still deliberately raises `LOCAL PROTOTYPE ONLY` when `REGISTRAR_ENV=production` in `registrar/app/runtime.py`. Production v1 cannot be declared ready until a reviewed implementation replaces that guard with proven production controls; changing the environment string alone is forbidden.

## 2. Outcome

Production v1 delivers:

1. one active, stateful TownSquare core running the existing Docker Compose services and two independent SQLite domains on durable block storage;
2. private-by-default Google Cloud networking, authenticated HTTPS ingress, least-privilege workload identities, immutable image deployment, audited configuration, and tested recovery;
3. a replaceable, provider-neutral engagement gateway that calls Gemini through Vertex AI with `google-genai` and Application Default Credentials (ADC), never an embedded API key;
4. model outputs entering TownSquare only as attributed proposals or findings through the application service and existing governed-write controls; and
5. explicit integration contracts for Vertical and Wonderland without giving either the model or the observer authority over the ledger.

Horizontal scale, active-active writers, automatic regional failover, Cloud SQL/PostgreSQL, GKE, and a fully serverless core are beyond production v1. They require a separate data-layer migration and acceptance decision.

## 3. Measured current constraints

The design starts from the repository, not an idealized cloud-native rewrite:

- `compose.yml` contains Ledger, Viewer, Registry, two one-shot migrators, and an operations-profile Backup container.
- Ledger and Registry are independent SQLite databases on separate bind mounts. Both use one writable instance; Registry publishes to Ledger asynchronously through a durable outbox.
- Compose currently publishes Ledger and Viewer only on host loopback and leaves Registry internal.
- Images run as fixed non-root users with read-only root filesystems, dropped capabilities, `no-new-privileges`, process/memory/CPU limits, and local log rotation.
- The backup tooling uses SQLite online backup, separate manifests/watermarks for the two database domains, `age` encryption, external checkpoint signing, and isolated restore/replay.
- `release-manifest.json` is a template, not deployment evidence. Production must produce resolved image/config/SBOM/provenance evidence.
- `registrar/app/runtime.py` blocks production mode today.

These constraints make the first topology a controlled lift-and-harden release, not a claim that SQLite/Compose is the final cloud architecture.

## 4. Compute topology decision

### 4.1 Selected topology

Use a hybrid topology:

- **Stateful core:** one active Compute Engine Linux VM running the reviewed Docker Compose release by immutable image digest.
- **Durable data:** one regional Persistent Disk for Ledger and a separate regional Persistent Disk for Registry, mounted only to the active VM. A zonal boot disk contains no authoritative data.
- **Standby:** a tested instance template and recovery procedure can recreate the core VM in the paired zone and attach the regional disks after fencing the old VM. There is never more than one writable core.
- **Gemini gateway:** one stateless Cloud Run service with its own service identity. It has Vertex AI permission but no TownSquare ledger, database, registry, backup, or governed-write credential.
- **Ingress:** a global external Application Load Balancer with Google-managed TLS and IAP in front of the VM backend. The VM has no external IP.

Compute Engine is selected for the core because it preserves local block-device semantics, fixed filesystem permissions, one-writer SQLite, Compose networks, one-shot migrators, the backup container, and the current operational model. Persistent Disk is durable network block storage, and regional disks replicate across selected zones; snapshots supplement, but do not replace, application-level backups ([Persistent Disk](https://docs.cloud.google.com/compute/docs/disks/persistent-disks)).

Cloud Run is selected only for the Gemini gateway because that component is stateless, has no local durable history, and benefits from a separate workload identity. Cloud Run is rejected for the stateful core because its container filesystem is disposable and its fit guidance expects applications not to require a local persistent filesystem and to tolerate multiple instances ([Cloud Run overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run), [Cloud Run fit criteria](https://docs.cloud.google.com/run/docs/fit-for-run), [container runtime contract](https://docs.cloud.google.com/run/docs/container-contract)). Cloud Storage/FUSE or NFS is not a substitute for SQLite block storage.

GKE is rejected for production v1. GKE can operate stateful workloads using StatefulSets and persistent volumes, but it adds Kubernetes scheduling, upgrade, network policy, ingress, volume, and cluster operations without removing the current single-writer database limit ([GKE StatefulSets](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/statefulset), [GKE persistent volumes](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes)). Reconsider GKE only when multiple independently scalable services, an external database, and an operating owner justify it.

### 4.2 Migration boundary for a later topology

Cloud Run or horizontally scaled GKE may host the core only after all of the following are separately designed and accepted:

1. Ledger and Registry persistence is migrated from SQLite to a transactional external database with equivalent immutability, ordering, idempotency, receipt, and outbox guarantees.
2. Attachments and large evidence are moved to an object contract rather than a mounted SQLite-adjacent filesystem.
3. all runtime services are stateless and pass concurrent/multi-instance tests;
4. migrations, backup/restore, point-in-time recovery, and rollback are re-proven for the new stores; and
5. event IDs, hashes, audit checkpoints, and TownSquare/Vertical/Wonderland references reconcile exactly.

No production-v1 success claim implies that migration has occurred.

## 5. Resource and environment layout

Use an organization/folder when available, with separate projects so IAM, quota, billing, and lifecycle do not silently cross environments:

| Project | Purpose | Prohibited |
|---|---|---|
| `ts-build-<id>` | Cloud Build, build provenance, vulnerability analysis, build Artifact Registry | production data, runtime secrets, interactive model use |
| `ts-nonprod-<id>` | integration, migration rehearsal, synthetic Gemini tests | production records and production credentials |
| `ts-prod-<id>` | VPC, Compute Engine core, Cloud Run gateway, production Artifact Registry, disks, buckets, secrets, KMS, logs/metrics | ad hoc builds and developer experimentation |
| `ts-audit-<id>` | centralized log/backup evidence sink and KMS-backed checkpoint attestor, controlled separately | application execution, plaintext backup data, and mutable runtime state |

Environment isolation follows Google guidance to segment staging and production into separate projects ([Secret Manager best practices](https://docs.cloud.google.com/secret-manager/docs/best-practices)). If the operator does not have a Google Cloud organization, the project separation remains; organization-policy controls become documented gaps.

All resources carry `system=townsquare`, `environment`, `owner`, `data_class`, `cost_center`, and `release` labels where the service supports labels. Project IDs, billing account, folder/organization, DNS zone, and operator groups are blocking operator inputs.

## 6. Region and data residency

The proposed default is:

- primary region: `us-central1`;
- active VM zone: one `us-central1` zone selected after quota check;
- standby/recovery zone: a second zone in `us-central1`;
- Artifact Registry, KMS, Secret Manager replicas, logging buckets, disks, and Cloud Run gateway: regional in `us-central1` when supported;
- encrypted backup/evidence bucket: an operator-approved US regional or dual-region location that meets the chosen recovery boundary.

This is a recommendation, not a residency decision. Before provisioning, the operator must choose either a strict single-region boundary or a US-only multi-region DR boundary, plus retention and legal/privacy requirements. Vertex model availability, security controls, at-rest residency, and ML-processing location must be verified for the exact model and feature set. A regional API endpoint alone does not prove residency; Google's location documentation explicitly warns that endpoint choice and residency are distinct ([Vertex locations](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations), [Vertex generative AI security controls](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/security-controls), [Google Cloud data residency list](https://cloud.google.com/terms/data-residency)).

Production v1 uses no Search/Maps grounding, RAG Engine, Live session resumption, or provider file store. These features have different storage/processing behavior and require a separate review. The operator decides whether to disable Vertex's project-level in-memory data caching; the recommended privacy-first default is disabled until latency evidence justifies it ([Vertex AI zero data retention](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention)).

## 7. Network, ingress, and TLS

1. Create a custom-mode VPC and one private regional subnet with Private Google Access. Do not use the default network.
2. Give the core VM no external IP. Administrative shell access uses OS Login through IAP TCP forwarding; metadata-based SSH keys are disabled.
3. Put the active VM in a one-member unmanaged instance group for the load-balancer backend. A health check reaches only the ingress proxy health endpoint.
4. Terminate public TLS at the external Application Load Balancer using Certificate Manager or a Google-managed certificate. Google-managed certificates are provisioned and renewed by Google ([managed certificates](https://docs.cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs)).
5. Enable IAP on Viewer and API backend services. The backend validates the IAP assertion; API clients also present TownSquare's application credential/receipt. IAP is an identity perimeter, not ledger authority ([IAP for Compute Engine](https://docs.cloud.google.com/iap/docs/enabling-compute-howto)).
6. Add Cloud Armor rate limiting and deny rules at the load balancer. Application request/token/cost budgets still apply behind it.
7. Publish only the ingress proxy's private backend port. Ledger, Viewer, Registry, SQLite files, Docker socket, metrics internals, and migrators have no direct external listener.
8. Restrict VM ingress to documented load-balancer health/proxy ranges and IAP administrative access. Enable firewall-rule logging so allow/deny matches are auditable ([VPC firewall logging](https://docs.cloud.google.com/firewall/docs/vpc-firewall-rules-logging-overview)).
9. Egress is deny-by-default except DNS/NTP, approved Google APIs, Artifact Registry pulls, Cloud Logging/Monitoring, Secret Manager/KMS, backup upload, and the Cloud Run gateway. Any Cloud NAT route is logged and allowlisted; general container internet access is prohibited.
10. The Cloud Run gateway accepts requests only from the production runtime identity with `roles/run.invoker` and a Google-signed ID token whose audience is the gateway URL; it uses internal ingress where the selected configuration supports the VM path and can call only the approved regional Vertex AI endpoint ([Cloud Run service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)).

The production Compose override replaces loopback host publishing with an ingress-proxy-only internal bind. It does not publish Registry. That override is a future production artifact and must not alter the NAS Compose profile.

## 8. IAM and service identities

Use dedicated, user-managed service accounts; do not use default service accounts or service-account keys. Google recommends attached service accounts for workloads on Google Cloud and avoiding keys when possible ([service-account best practices](https://docs.cloud.google.com/iam/docs/best-practices-service-accounts), [Compute Engine service accounts](https://docs.cloud.google.com/compute/docs/access/service-accounts)).

| Identity | Minimum purpose | Explicitly denied/not granted |
|---|---|---|
| `ts-build` | read approved source; build; push to build registry; emit provenance/SBOM/scan | production secrets, disks, VM login, model invocation |
| `ts-promote` | copy reviewed digests to production registry and update release declaration | builds, data access, model invocation, arbitrary IAM changes |
| `ts-core-runtime` | pull exact images; read exact secret versions/config; write logs/metrics; upload encrypted backup objects | Vertex AI, build/push, KMS administration, broad Storage access |
| `ts-gemini-gateway` | Cloud Run execution, invoke the exact approved Vertex project/location/model, write redacted logs/metrics | TownSquare credentials, disks, buckets, registry, ledger API, Secret Manager except gateway-only configuration |
| `ts-backup-attestor` | read completed ciphertext metadata/manifests, recompute/validate checkpoint input, sign canonical checkpoint with an audit-project KMS asymmetric key, write signature/evidence | decryption, VM/disks, TownSquare writes, model invocation, deleting backup objects |
| `ts-recovery` | operator-activated read of selected backup objects, attach/restore to new disks | normal runtime use, model invocation, delete backups |
| operator groups | IAP access, release approval, recovery approval, audit viewing separated by duty | service-account keys and blanket Owner/Editor for routine work |

Compute Engine permits only one attached service account. Therefore production v1 treats any shell or container escape on the core VM as access to the `ts-core-runtime` identity. Limit shell access, block container access to the metadata server unless explicitly needed, and keep that identity narrow. The Gemini gateway's separate Cloud Run identity is the mechanism that prevents the model adapter from inheriting core data permissions.

Grant `cloud-platform` OAuth scope to the VM and enforce actual access with resource-level IAM roles, as Google recommends. Enable Data Access audit logs for Secret Manager, KMS, Storage, Artifact Registry, Vertex AI, and other supported sensitive services; these logs are not generally on by default ([Cloud Audit Logs](https://docs.cloud.google.com/logging/docs/audit), [configure Data Access logs](https://docs.cloud.google.com/logging/docs/audit/configure-data-access)).

## 9. Images, build, deployment, and IaC

### 9.1 Infrastructure as code

Terraform is the production-v1 source of truth for projects, APIs, VPC, firewall rules, service accounts/IAM, KMS, secrets, disks, buckets, Artifact Registry, Compute Engine, Cloud Run, load balancing/IAP, logging, alerts, budgets, and quotas. Pin provider versions and commit `.terraform.lock.hcl`; plans are reviewed artifacts and applies require operator authorization. Google recommends change-controlled IaC for production environments ([Google Cloud IaC overview](https://docs.cloud.google.com/docs/terraform/iac-overview)).

Terraform state resides in a dedicated secured bucket with versioning, restricted IAM, and audit logs. Runtime service accounts cannot read or write it. A plan with deletes/replacements of data, keys, projects, DNS, IAM, or the active VM/disks is a destructive change and must stop for explicit approval.

### 9.2 Supply chain

1. Cloud Build runs under `ts-build` from an exact reviewed commit with hash-locked dependencies and digest-pinned base images.
2. It produces Ledger, Viewer, Registry, Backup, ingress, and Gemini-gateway images; SBOMs; test reports; image/config digests; and build provenance.
3. Store images in regional Artifact Registry with immutable tags, but deploy only `@sha256:` digests. Artifact Registry supports immutable tags and digest pulls ([Artifact Registry push/pull](https://docs.cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling)).
4. Enable Artifact Analysis automatic scanning. High/critical findings have no silent exception; a signed, time-bounded operator variance names the exact digest and compensating controls ([container scanning](https://docs.cloud.google.com/artifact-analysis/docs/container-scanning-overview)).
5. Validate Cloud Build provenance against the approved source and builder. Cloud Build can generate SLSA provenance for Artifact Registry artifacts ([build provenance](https://docs.cloud.google.com/build/docs/securing-builds/generate-validate-build-provenance)).
6. Promotion copies the same reviewed digest into the production repository; it never rebuilds. The release manifest pins source SHA, image/SBOM/provenance/config/IaC hashes, schema heads, model/config allowlist, and governing-source hashes.
7. Deployment pulls no source or mutable package at runtime. Migrations run exactly once before matching services start.

Cloud Deploy is not selected for v1 because its standard deployment targets do not add value to the single Compose VM. A reviewed deployment script plus Terraform and systemd is smaller. Reconsider Cloud Deploy when the target becomes GKE or Cloud Run-centric.

## 10. Persistent state and database strategy

- Keep Ledger and Registry on separate regional Persistent Disks and separate mount points. Never place live SQLite/WAL files on Cloud Storage FUSE, Filestore/NFS, a shared volume, a synced folder, or the boot disk.
- Format ext4; mount with `nodev,nosuid,noexec`; reserve headroom; alert at 70%, 80%, and 90% usage. UID/GID and directory permissions match the non-root container users.
- Preserve `WAL`, `foreign_keys=ON`, `synchronous=FULL`, busy timeouts, one migrator, and one writable runtime per domain.
- The Registry/Ledger relationship remains asynchronous and idempotent. No cross-database transaction, shared rollback point, or false atomic backup is introduced.
- The active-VM lease/fencing record, disk attachment state, and health are checked before startup. Startup fails closed if a peer writer, unexpected disk, schema head, release tuple, or incomplete migration is found.
- Cloud SQL is not a drop-in target. A future PostgreSQL migration must replace SQLite-specific migrations, triggers, pragmas, backup/restore, locking, and failure tests with equivalent accepted mechanisms.

## 11. Secrets and cryptographic keys

- Store token peppers, signing/encryption material, service credentials, and gateway configuration in Secret Manager. Reference an exact secret version in the release, never `latest`.
- The application reads secrets through the Secret Manager API into memory or creates tightly controlled runtime files on tmpfs only where current Compose requires file secrets. No secret enters an image, Terraform state, environment dump, log, TownSquare event, model prompt, or backup.
- Apply secret-level IAM, enable Data Access logs, rotate by adding a version and deploying a new exact version, then revoke after overlap.
- Use Cloud KMS CMEK for production disks, backup/evidence buckets, Secret Manager, and supported logs/artifacts when the operator adopts the key hierarchy. Key location matches protected resource location; disabling/destroying a CMEK makes protected data unavailable ([Secret Manager CMEK](https://docs.cloud.google.com/secret-manager/docs/cmek)).
- Separate KMS administrators from decrypt/use principals. Runtime can use only the exact keys necessary; it cannot administer keys.
- Preserve the existing rule that the backup-checkpoint signing private key is outside the runtime and core VM. Production v1 proposes an audit-project Cloud KMS `ASYMMETRIC_SIGN` key used only by `ts-backup-attestor`; key material never leaves KMS, verification uses the separately obtained public key, and the attestor cannot decrypt backups ([Cloud KMS digital signatures](https://docs.cloud.google.com/kms/docs/create-validate-signatures)). This replaces Minisign only after signature-format compatibility, independent verification, key rotation/revocation, and restore tests pass and the operator adopts the exact key/version policy. Until then, external Minisign remains the accepted path and the measured RPO is based on the latest returned valid signature.

## 12. Gemini engagement gateway

### 12.1 Parley-derived pattern

The design reuses the useful boundaries measured in Parley, not its local-key or UI assumptions:

- `C:\Repo\ynm\utilities\parley\parley\providers\base.py`: provider-neutral `Message`, `Chunk`, `ModelInfo`, provider protocol, neutral usage keys, replay filtering, request budgets, and sanitized provider errors.
- `...\providers\gemini.py`: edge adapter using `google-genai`, neutral history conversion, bounded timeout, no SDK retries, usage/finish normalization, and error redaction.
- `...\tests\test_gemini.py`: offline fake-client tests for role translation, attachment mapping, no reasoning replay, normalized usage, stream closure, and secret-free errors.
- `...\docs\DESIGN.md` and `README.md`: provider-neutral history and provider/model fixed per conversation.

Production changes Parley's local choices:

- use Vertex AI with the `google-genai` SDK, ADC, and the Cloud Run service identity; no API key or DPAPI file;
- never list models live to users; the release manifest supplies a closed allowlist;
- do not store or display hidden reasoning/chain-of-thought;
- store history as governed TownSquare records, not a separate chat authority;
- use application-level context manifests, policy receipts, audit events, and budgets; and
- treat output as a proposal/finding, never an action or decision.

Google's Vertex AI quickstart and SDK documentation support `google-genai`, Vertex mode, and ADC ([Vertex AI quickstart](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart), [Google Gen AI SDK](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview)). ADC with the attached workload identity is mandatory; Google identifies the attached service account as the preferred ADC source for production workloads on Google Cloud ([ADC credential order](https://docs.cloud.google.com/docs/authentication/application-default-credentials)). API keys are rejected because they create a second long-lived bearer secret with weaker workload attribution.

### 12.2 Call path and authority

```text
actor/client
  -> TownSquare engagement application service
     -> validate principal, work item, context manifest, policy receipt, budgets
     -> append immutable engagement-request source event
     -> authenticated call to Cloud Run provider gateway
        -> translate provider-neutral history to pinned Vertex request
        -> Vertex AI Gemini
        <- attributed provider result + usage/finish/error metadata
     <- gateway result (no TownSquare credential)
     -> append response source event through governed TownSquare write
     -> optionally open an attributed proposal/finding for review
        -> Vertical references evidence; Wonderland observes read-only
```

Gemini and the gateway have no Ledger, Registry, database, archive, acceptance, or policy-override credential. The gateway cannot call TownSquare. Only the application service may submit a governed write, and it binds the output to the original principal, engagement ID, context manifest, policy receipt, exact model/config, request hash, response hash, and evidence receipt.

Model output never executes a tool, shell command, URL fetch, workflow transition, wake action, Registry mutation, policy change, or acceptance. A human or separately authorized agent must review and act through the ordinary TownSquare workflow.

### 12.3 Provider-neutral record contract

Each engagement has immutable records for:

- `engagement_id`, conversation/work-item references, actor/principal and represented actor;
- provider `google-vertex`, exact project/location/model resource, SDK version, adapter version, and generation/safety configuration hash;
- ordered provider-neutral message references and attachment/evidence references;
- context manifest ID/hash with ordered source event IDs/hashes and retrieval time;
- policy receipt ID/hash, governing source IDs/hashes, scope, expiry, and decision basis;
- redaction/classification report and explicit data-transfer approval class;
- idempotency key, request hash, response hash, provider request/trace ID when available;
- start/end timestamps, total latency, retry count, finish reason, safety/block status, normalized error class;
- input, cached-input, output, and thinking token counts when reported; estimated cost using a versioned price table; and budget decision;
- response source content or governed encrypted pointer, plus a separate proposal/finding event if created.

Source interaction events and Wonderland/agent findings are distinct event types. Findings cite source event IDs/hashes and model/analysis version; they never overwrite or masquerade as the source.

Do not persist hidden chain-of-thought, internal reasoning text, debug prompts, authorization headers, ADC tokens, or raw provider exceptions. Set `include_thoughts=false`. Opaque provider continuity metadata is excluded in v1 unless the pinned model requires it and an explicit operator decision classifies, encrypts, and bounds it; it is never presented as reasoning evidence.

### 12.4 Model and budget policy

- Each conversation/work item pins one allowlisted provider, exact model resource, location, adapter version, system/policy prompt hash, temperature/top-p/top-k, max output tokens, safety settings, and context limit. Changing any one opens a new engagement version; it never mutates history.
- No live arbitrary model enumeration or user-entered model ID exists in production.
- V1 is text and selected TownSquare text evidence only. Arbitrary uploads, provider file stores, grounding, browsing, code execution, and function/tool calling are disabled.
- Default request limits, finalized by the operator in the release manifest: one in-flight call per engagement; maximum 64,000 input tokens; 4,096 output tokens; 120-second total deadline; 30-second idle-stream deadline; and a maximum of one retry only when no response chunk or usage was observed and the error class is explicitly retryable.
- A 429, policy block, authentication error, budget denial, or partial response is not automatically retried. User/operator retry creates a new attempt under the same engagement and preserves the prior attempt.
- Enforce per-request, per-conversation, per-work-item, per-principal, hourly, and daily request/token/cost ceilings before the call. A versioned price table is required for cost estimates; unknown pricing fails closed for paid calls.
- Configure Vertex quotas, Cloud Run max instances/concurrency, application circuit breakers, and billing alerts/spend caps where eligible. Billing controls can lag, so application budgets remain authoritative. Google notes that spend-cap enforcement is not instantaneous ([Cloud Billing spend caps](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps)).

## 13. TownSquare, Vertical, and Wonderland integration

### TownSquare

TownSquare owns the neutral interaction history, request/result source events, content hashes, context manifest, policy receipt, governed-write result, and attributed proposal/finding. Provider metadata is an adapter detail. A future provider can implement the same gateway contract without changing Doctrine or historical records.

### Vertical

Vertical references the TownSquare engagement and proposal/finding event IDs as evidence on a unit of work. It records model-assisted work as attributed assistance, not completion. `RESOLVED` still requires current evidence for all applicable criteria; `CLOSED` still requires a cited authorized acceptance decision. A model response, token receipt, or successful API call satisfies neither by itself.

### Wonderland

Wonderland reads a redacted projection containing source IDs/hashes, actor/model/config provenance, timing, usage, error/finish categories, policy/context references, later review outcomes, and lifecycle outcomes. It stores derived behavior observations/features separately with dataset/model/version provenance. It receives no raw secrets, hidden reasoning, unapproved sensitive content, write credential, or gate capability.

## 14. Logging, monitoring, and SLOs

### 14.1 Logging and audit

- Send structured application logs to Cloud Logging through the Ops Agent or container logging driver. Logs contain IDs, hashes, state, latency, counts, and allowlisted error classes—not posts, prompts, responses, tokens, secrets, or raw exceptions.
- Enable Admin Activity, System Event, Policy Denied, and selected Data Access logs. Cloud Audit Logs records who did what, where, and when, and its audit entries are immutable ([Cloud Audit Logs](https://docs.cloud.google.com/logging/docs/audit)).
- Route security/release/audit logs to a restricted log bucket or audit project with an operator-approved retention period and no runtime delete permission.
- Log and alert on IAP denial, firewall denial, IAM changes, key/secret access, image promotion, deployment, migration, backup/restore, model quota/budget denial, abnormal token use, policy receipt failure, and operator stop/resume.

### 14.2 Initial service objectives

These are proposed measurement targets, not contractual promises:

| Indicator | Initial objective | Window/exclusions |
|---|---|---|
| Governed Ledger API availability | 99.5% successful eligible requests | rolling 30 days; approved maintenance excluded |
| Viewer availability | 99.0% | rolling 30 days |
| Core API latency | p95 reads <500 ms; p95 governed writes <1 s | excludes model calls and migrations |
| Gemini engagement completion | 95% of eligible, non-policy-blocked calls finish within 120 s | daily and 30-day views; provider outage shown separately |
| Registry audit delivery | 99% delivered within 60 s; none lost/duplicated | rolling 24 hours |
| Recovery point | <=15 minutes for accepted application backups | verified from successful signed checkpoint |
| Regional recovery time | <=4 hours | measured restore/failover drill |

Create service-level indicators and burn-rate alerts in Cloud Monitoring; Google Cloud supports SLO monitoring and alerting against service objectives ([Cloud Monitoring SLOs](https://docs.cloud.google.com/monitoring/slo-monitoring)). Alert destinations, escalation owners, and quiet hours are operator decisions. Missing telemetry is degraded, never green.

## 15. Backup, restore, retention, and disaster recovery

### 15.1 Backup layers

1. **Authoritative application backup:** every 15 minutes, run the existing online SQLite backup separately for Ledger and Registry, integrity/FK checks, row counts, domain watermark, encryption, and canonical manifest. Upload only completed encrypted artifacts and manifests. The audit-project attestor verifies object generation/checksums and canonical checkpoint input, signs with its KMS asymmetric key, and writes the signature/checkpoint to a separately controlled evidence location. A backup is `PENDING_ATTESTATION`, not recovery evidence, until that verification completes.
2. **Disk recovery aid:** daily scheduled snapshots of each data disk, with retention and location pinned. A crash-consistent snapshot is not application evidence; restored SQLite still must pass integrity, schema, release, and audit checks. Application-consistent guest-flush snapshots may be added after scripts are tested ([snapshot schedules](https://docs.cloud.google.com/compute/docs/disks/scheduled-snapshots), [snapshot consistency](https://docs.cloud.google.com/compute/docs/disks/snapshot-best-practices)).
3. **Release recovery:** retain exact images, SBOMs, provenance, Terraform plan/state history, Compose/config hashes, governing-source hashes, and restore tooling for every recoverable release.

### 15.2 Retention and immutability

Proposed starting policy, subject to operator/legal decision:

- application backups: 15-minute copies for 48 hours, daily for 35 days, monthly for 13 months;
- disk snapshots: daily for 14 days;
- release/evidence manifests and signed checkpoints: 13 months or the governing-record retention period, whichever is longer;
- application/audit logs: 90 days searchable, 13 months archived where required.

Use uniform bucket-level access, public-access prevention, versioning/soft delete, lifecycle rules, and a retention policy. Do not lock Bucket Lock until the operator accepts the irreversible period; Google documents that locking cannot be reduced or removed ([Bucket Lock](https://docs.cloud.google.com/storage/docs/bucket-lock)). Runtime has object-create only where practical; a separate recovery identity reads; deletion belongs to a separately approved retention process.

### 15.3 Restore and DR

- Quarterly and before every production cutover, restore both domains into new empty disks/paths, verify ciphertext/signature/checkpoint before decryption, run SQLite integrity/FK checks, validate schema/release tuple, compare counts/hashes/watermarks, then replay Registry delivery through the production boundary.
- A regional failover fences/stops the old VM, verifies there is no writer, attaches regional disks to a new VM in the paired zone, deploys the same digest/config, starts dark, and passes readiness before load-balancer traffic changes.
- If disks are unavailable/corrupt, restore selected application backups to new disks. Never restore over an active directory.
- Ledger and Registry remain separate consistency domains; reconciliation uses recorded correlation points and outbox state, never a fabricated shared timestamp.
- After any accepted cloud write, rollback never rewinds to the NAS database. Stop writes, preserve cloud state, and repair/migrate forward.

## 16. NAS-to-Google-Cloud migration and reconciliation

1. Inventory the accepted NAS release, source SHA, image digests, schemas, counts, event/hash chains, registry agents/journal/outbox, governing manifests, secrets/keys, and backup checkpoints. Google Drive contributes no authority and no live sync.
2. Build and deploy the Google Cloud stack dark from the exact production release. Create empty disks and run one migrator per domain.
3. Make separate signed/encrypted NAS online backups; copy them through a hash-verified, resumable channel; verify outer hashes and signatures before decrypting only inside the isolated restore environment.
4. Restore into new cloud data paths. Compare schema, row counts, IDs, canonical hashes, ledger sequence, lifecycle heads, Registry journal/outbox, audit checkpoints, and known historical boundaries.
5. Run source/container/security/recovery conformance, including an offline synthetic Gemini gateway test with fake clients. Then perform one operator-approved live synthetic Vertex call under a hard request/token/cost cap and store its complete audit envelope without sensitive content.
6. Start a final cutover window. Stop NAS writers, drain Registry outbox, take final domain backups, restore/reconcile the delta, and prove there are no divergent or duplicate IDs. No dual writer period is allowed.
7. Obtain operator approval naming exact release/model/config/IaC/image/backup/evidence hashes and the cutover moment. Change client endpoints/DNS/IAP routing. Keep NAS read-only as historical fallback.
8. Run day-0, day-1, day-7, and day-14 checks. Reconcile TownSquare evidence references used by Vertical and the read-only Wonderland projection.

If any identity, hash, sequence, lifecycle head, outbox, receipt, or policy record cannot reconcile, cutover stops. Differences become explicit findings; they are not silently normalized.

## 17. Rollout and rollback

### Phase 0 — decisions and foundations

Approve projects/billing, region/residency, DNS/IAP identities, RPO/RTO/retention, SLOs, KMS hierarchy, exact model/config/budgets, and governing sources. Review Terraform without applying it.

### Phase 1 — nonproduction

Provision `ts-nonprod`; build and scan images; exercise migrations, networking, IAM negatives, model fakes, one capped live synthetic call, backups, restore, zone recovery, and NAS migration rehearsal using synthetic/redacted data.

### Phase 2 — production dark

Provision production, restore the signed NAS backup, start with writers and Gemini disabled, and run all conformance/recovery/security checks. Load balancer/IAP is limited to the acceptance group.

### Phase 3 — read and Gemini canary

Enable Viewer/read APIs, then the gateway for a named pilot cohort and work items. One exact model/config; low budgets; no tools/uploads/grounding. Every response remains a proposal/finding.

### Phase 4 — governed writers and pilot

After exact operator approval, enable constrained governed writes. Complete the 2–4 week pilot and decide accept, extend, restrict, or roll back.

### Rollback rules

- Before the first production write: stop new services, remove traffic, preserve evidence, and return clients to NAS.
- After the first production write: stop writes/model calls, preserve cloud disks/logs, take a final verified backup, and repair forward. NAS may serve historical reads only; it does not resume authority by overwriting cloud history.
- Application rollback uses a prior image only if its manifest supports the current schema and peer contract. Database rollback uses a verified pre-write backup only inside the allowed boundary.
- Gateway rollback pins the prior adapter/model/config combination; conversation history never changes model/provider in place.

## 18. Threat model and fail-closed behavior

| Threat/failure | Required control | Degraded behavior |
|---|---|---|
| Gemini prompt injection or authority claim | fixed system policy, content classification, no tools, attributed proposal/finding, governed write | store blocked/finding metadata; no action or transition |
| Sensitive data exfiltration | context allowlist, redaction/classification, policy receipt, regional endpoint, no provider file store/grounding | deny call before network; auditable reason |
| Model/config drift | release allowlist and per-conversation pin; no live selection | deny unknown model/config |
| Token/cost abuse | identity quotas, request/token/cost budgets, Cloud Run max instances, Vertex quota, circuit breaker | 429/budget-denied event; no retry storm |
| Provider outage/timeout/partial stream | total/idle deadlines, at most one safe retry, attempt records | retain partial attempt as failed/stopped; never present as accepted answer |
| Secret/token leakage | ADC, no keys, exact Secret versions, redacted logs, fake-secret tests | fixed error class; rotate/revoke; stop gateway |
| Gateway compromise | separate SA/project boundary, no ledger credential, no TownSquare callback, restricted egress | disable Cloud Run service/identity; core continues without Gemini |
| Core VM/container escape | no external IP, narrow core SA, IAP/OS Login, metadata restrictions, hardened containers | operator stop; snapshot/backup; rebuild from clean image |
| SQLite split brain | one active VM, disk fencing/lease, one writer and migrator | fail startup/readiness; operator reconciliation |
| Image/supply-chain compromise | digest pin, provenance, SBOM, scanning, immutable promotion | promotion/deploy denied; variance required |
| Backup deletion/ransomware | create-only runtime, separate recovery identity, retention/versioning, external signed checkpoints | restore from retained copy; incident finding |
| Data-region drift | Terraform policy, resource-location constraints, model/location gate | deployment or Gemini call denied |
| Audit/log loss | missing-telemetry alerts and external evidence sink | status UNKNOWN/DEGRADED; acceptance blocked |
| Vertical/Wonderland overreach | read/reference-only contracts, no authority credential, negative tests | reject write/gate attempt and record finding |

## 19. Production-v1 acceptance criteria

Each criterion is evidence-passed or evidence-failed independently. Evidence passing does not authorize production. Final acceptance requires an operator decision citing the exact evidence package.

| ID | Preconditions and trigger | Observable expected result | Negative/failure case | Evidence | Evaluator | Acceptance authority |
|---|---|---|---|---|---|---|
| GCP-P1-001 | Reviewed Terraform plan for named projects/region | Only approved projects/resources/labels/APIs are planned; no current NAS change | unexpected delete, global/unapproved location, default network/SA | saved plan hash and policy output | Tony Jaa | Operator |
| GCP-P1-002 | Core topology provisioned dark | exactly one writable core; two separate regional data disks; no VM external IP | second writer/migrator or shared/live DB path starts | inventory, disk attachments, Compose/container inspection | Francis Ngannou | Operator |
| GCP-P1-003 | External request to production names | TLS valid; IAP and application auth required; direct VM/service ports unreachable | bypass reaches Viewer/Ledger/Registry | external probes, LB/IAP/firewall logs | GSP | Operator |
| GCP-P1-004 | IAM negative matrix executed | each identity performs only allowlisted actions | default SA/key or cross-role privilege succeeds | IAM policy snapshot and denied/success audit logs | GSP | Operator |
| GCP-P1-005 | Exact release promoted | digest, SBOM, scan, provenance, source and config hashes match manifest | mutable tag, unresolved high/critical finding, provenance mismatch | Artifact Registry/Analysis/Cloud Build evidence | GSP | Operator |
| GCP-P1-006 | Migrations run on fresh and restored domains | one migrator/domain; exact schema and peer tuple; idempotent rerun | partial migration or incompatible runtime starts | migration logs and conformance report | Jackie Chan | Operator |
| GCP-P1-007 | Governed write suite runs | ordering, immutability, idempotency, context/policy receipt, authority and lifecycle pass | replay, wrong actor, stale context or self-accept succeeds | test report plus selected immutable events | Ronda Rousey | Operator |
| GCP-P1-008 | Backup schedule and restore drill run | separate encrypted backups reach externally verified `ATTESTED` state, restore to empty disks, and reconcile; RPO measured <=15 min from the latest valid attestation | `PENDING_ATTESTATION` accepted as evidence, live-path overwrite, bad signature/hash, or shared watermark accepted | manifests, KMS/Minisign signatures and public verification, restore/replay transcript | Ronda Rousey | Operator |
| GCP-P1-009 | Paired-zone recovery drill | old writer fenced; same release recovers within 4 hours; no duplicate/divergent event | two writers or unreconciled outbox | incident timeline, disk/VM/audit logs, hashes | Francis Ngannou | Operator |
| GCP-P1-010 | Gemini gateway fake and capped live tests | ADC identity, exact model/config, budgets, timeouts, hashes, usage/finish/error audit all proven | API key, arbitrary model, unbounded retry/output, raw error/content log | gateway tests and one synthetic audit envelope | Ronda Rousey and GSP | Operator |
| GCP-P1-011 | Malicious model output test | output is inert attributed proposal/finding; no tool/write/transition executes | model output changes state or invokes external target | negative test and TownSquare audit trail | GSP | Operator |
| GCP-P1-012 | Context/policy/privacy tests | only manifest-selected/redacted context sent; policy receipt current; no hidden reasoning stored | unselected data, expired receipt, secret or thought text leaves boundary | fake-provider capture, redaction and storage scans | GSP | Operator |
| GCP-P1-013 | Vertical integration fixture | Vertical cites TownSquare evidence without treating model result as resolution/acceptance | model result alone resolves/closes work | integration events and projection output | Jackie Chan | Operator |
| GCP-P1-014 | Wonderland integration fixture | read-only derived finding preserves source/model/dataset provenance | Wonderland writes source/gate state or loses source identity | permission negatives and reproducibility fixture | Shuri | Operator |
| GCP-P1-015 | Monitoring fault injection | health, write failures, outbox lag, disk thresholds, backup age, Gemini errors/budgets, and missing telemetry alert | missing telemetry reports healthy or no escalation | alert incidents and SLO dashboards | Ronda Rousey | Operator |
| GCP-P1-016 | NAS migration rehearsal and final reconciliation | counts, IDs, hashes, sequences, lifecycle heads, receipts and outbox match; Drive absent from authority | unexplained delta or dual-writer window | signed reconciliation report | Jackie Chan | Operator |
| GCP-P1-017 | Rollback drills before and after a write | pre-write traffic returns safely; post-write preserves cloud truth and repairs forward | cloud ledger overwritten from NAS/old backup | rollback transcript and final hashes | Ronda Rousey | Operator |
| GCP-P1-018 | Governing and release manifests reviewed | exact Doctrine/ROE/governance, release, model and policy sources/hashes are current and scoped | inactive/template manifest treated as adopted | protected authority proof and manifest hashes | Jigoro Kano and GSP | Operator |

Applicability: all criteria apply to production v1. If a capability is deliberately removed—for example Gemini is disabled—the associated criterion remains `NOT APPLICABLE` only through an operator decision that also removes the capability from the accepted release; it is never silently skipped. Ronda operationalizes and executes criteria but cannot invent, relax, or reinterpret product requirements.

## 20. Blocking operator decisions

1. Google Cloud organization/folder, project IDs, billing account, and responsible groups.
2. `us-central1` or another approved primary region; strict single-region versus US-only DR boundary.
3. Domain names, DNS control, IAP user/service principals, and public-versus-organization-only access.
4. exact RPO, RTO, SLO, retention, log retention, Bucket Lock timing, and backup location.
5. CMEK/key hierarchy, administrators, users, rotation, destruction protection, and recovery ownership.
6. exact Vertex project/location/model resource, safety/generation configuration, caching setting, request/token/cost caps, and pilot cohort.
7. exact governing-source manifest and policy-receipt profile for production writes/model calls.
8. exact release SHA, image/config/IaC/SBOM/provenance hashes, vulnerability disposition, migration evidence, and cutover moment.
9. final NAS archival/read-only disposition after cloud acceptance.

## 21. Alternative rejected

**Rejected:** rewrite the core immediately for Cloud Run, GKE, or Cloud SQL. That would combine deployment, data-model, concurrency, recovery, networking, and operational rewrites in the first production move. The smallest controlled path is Compute Engine for the stateful Compose core plus Cloud Run only for the stateless Gemini gateway. The design exposes the later database/stateless migration boundary instead of hiding it.

## 22. Work order

Document · Discuss · Decide gates implementation. No production code or infrastructure is changed from this design alone.

WORK ORDER
- Document cloud contract: Ip Man — maintain this architecture and resolve operator decisions against exact product requirements.
- Peer review: Tony Jaa — independently review topology, region, network, IAM, Vertex/Cloud Run integration, IaC, cost/quota, and migration practicality; raise his own concerns.
- Data review: Jackie Chan — review SQLite/PD layout, fencing, migrations, backup/restore, NAS reconciliation, and the explicit Cloud SQL migration boundary.
- Security review: GSP — threat-model IAM, IAP, metadata, secrets/KMS, supply chain, logging privacy, Gemini data flow, prompt injection, policy receipt, and model non-authority.
- Gemini adapter design: Bruce Lee — after reviews and operator decisions, specify the provider-neutral gateway interface and application-service governed-write integration based on Parley's adapter boundary; do not copy its API-key or live-model-list behavior.
- Infrastructure implementation: Tony Jaa — Terraform for project/service/network/IAM/Vertex/Cloud Run boundaries; Francis Ngannou — images, Compose production override, deployment, storage, backups, monitoring, and recovery. They are not alone in the repo and must preserve NAS artifacts.
- Application implementation: Bruce Lee — production runtime controls, engagement records, context/policy receipt binding, gateway client, and TownSquare/Vertical/Wonderland projections. No model credential or direct model write path.
- QA: Ronda Rousey — convert every `GCP-P1-*` criterion into executable checks and evidence capture; she may sharpen test mechanics but cannot invent or relax product requirements.
- Governance review: Jigoro Kano — verify infrastructure neutrality, exact governing-source binding, policy receipts, attributed non-authoritative model output, and operator acceptance boundary.
- Coordinate: Helio Gracie — checkpoint design review, implementation, security/data review, nonproduction rehearsal, production-dark evidence, and operator gateway; do not treat this proposed document as authority to deploy.
- Watch for: changing the NAS MVP; bypassing the production runtime guard; SQLite on FUSE/NFS; more than one writer; API keys; live arbitrary model selection; hidden reasoning storage; model output treated as authority; provider content in logs; unresolved image/model/config versions; global resources that violate the chosen residency boundary; budgets mistaken for instant hard stops; Drive returning as authority; or rollback overwriting cloud-native history.

## 23. Official Google Cloud references

All sources below were retrieved 2026-10-06. Product availability, model availability, prices, quotas, and terms must be rechecked at implementation and release review.

- [Compute Engine Persistent Disk](https://docs.cloud.google.com/compute/docs/disks/persistent-disks)
- [Cloud Run overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run)
- [Cloud Run fit criteria](https://docs.cloud.google.com/run/docs/fit-for-run)
- [Cloud Run container runtime contract](https://docs.cloud.google.com/run/docs/container-contract)
- [Cloud Run service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)
- [GKE StatefulSets](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/statefulset)
- [GKE persistent volumes](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/persistent-volumes)
- [Vertex AI Gemini quickstart](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/quickstart)
- [Google Gen AI SDK for Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview)
- [Vertex generative AI security controls](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/security-controls)
- [Vertex AI zero data retention](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention)
- [Google Cloud data residency list](https://cloud.google.com/terms/data-residency)
- [IAM service-account best practices](https://docs.cloud.google.com/iam/docs/best-practices-service-accounts)
- [How Application Default Credentials works](https://docs.cloud.google.com/docs/authentication/application-default-credentials)
- [Compute Engine service accounts](https://docs.cloud.google.com/compute/docs/access/service-accounts)
- [IAP for Compute Engine](https://docs.cloud.google.com/iap/docs/enabling-compute-howto)
- [Google-managed TLS certificates](https://docs.cloud.google.com/load-balancing/docs/ssl-certificates/google-managed-certs)
- [VPC firewall rules logging](https://docs.cloud.google.com/firewall/docs/vpc-firewall-rules-logging-overview)
- [Secret Manager best practices](https://docs.cloud.google.com/secret-manager/docs/best-practices)
- [Secret Manager CMEK](https://docs.cloud.google.com/secret-manager/docs/cmek)
- [Cloud KMS digital signatures](https://docs.cloud.google.com/kms/docs/create-validate-signatures)
- [Cloud Audit Logs](https://docs.cloud.google.com/logging/docs/audit)
- [Configure Data Access audit logs](https://docs.cloud.google.com/logging/docs/audit/configure-data-access)
- [Terraform/IaC overview](https://docs.cloud.google.com/docs/terraform/iac-overview)
- [Artifact Registry push/pull and immutable tags](https://docs.cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling)
- [Artifact Analysis container scanning](https://docs.cloud.google.com/artifact-analysis/docs/container-scanning-overview)
- [Cloud Build provenance](https://docs.cloud.google.com/build/docs/securing-builds/generate-validate-build-provenance)
- [Disk snapshot schedules](https://docs.cloud.google.com/compute/docs/disks/scheduled-snapshots)
- [Snapshot consistency best practices](https://docs.cloud.google.com/compute/docs/disks/snapshot-best-practices)
- [Cloud Storage Bucket Lock](https://docs.cloud.google.com/storage/docs/bucket-lock)
- [Cloud Monitoring SLOs](https://docs.cloud.google.com/monitoring/slo-monitoring)
- [Cloud Billing spend caps](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps)
