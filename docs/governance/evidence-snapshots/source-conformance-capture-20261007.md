# TownSquare MVP source-conformance capture

**record_id:** `TS-EVIDENCE-20261007-EDDIE-REAL-05`  
**collector:** Eddie Brock / OpenAI Codex seat on Venom  
**captured_at:** `2026-10-06T23:44:49.9637157-05:00`  
**classification:** verified captured operational instance; weight `5`  
**status:** evidence of current source state; not adoption, binding acceptance, release, deployment, or runtime conformance

## Exact subject

- Isolated local clone: `work/townsquare-mvp-verification-20261007`
- Git commit: `8b39032db1144140a7460d60946463803b4eac86`
- Clone was clean after the run (`git status --short` produced no output).
- Python: bundled Codex workspace Python; bytecode writes disabled.
- No network, NAS, container, or live service was used.

## Results

| Suite | Result | Captured evidence |
|---|---|---|
| Crier regression | PASS | `21/21 passed` |
| Tracker | PASS | `Ran 67 tests`; `OK` |
| Unified source conformance | BLOCKED AS DESIGNED | `Ran 50 tests`; 47 passed, 2 failed, 1 skipped. The failures are `RB-BACKUP-08` because `evidence/permissions-and-backup.json` is still `TEMPLATE_NOT_EVIDENCE`, and `RB-PKG-09` because the release manifest pins `7eea350...` while the exact reviewed head is `8b39032...`. |
| Registrar | ENVIRONMENT INCOMPLETE | `Ran 170 tests`; four import errors for absent `fastapi`. All loaded cases completed without a test failure. This run cannot certify the HTTP subset. |
| Viewer | ENVIRONMENT INCOMPLETE | One import error for absent `streamlit`; no Viewer test executed. |

Relevant exact file hashes:

| File | SHA-256 |
|---|---|
| `release-manifest.json` | `CC078C881AA7FC7B5B5716BE05E6E09DF1FDC043D04DADF10C347C91F9BBC6CF` |
| `evidence/permissions-and-backup.json` | `A36F634C0E36A43D0D2C20F4A97E8B48019B8A746A222AC4E096881DF99611CF` |
| `tests/conformance/test_release_blockers.py` | `A34803280371965B846C4E80584564EA09D307B13AFB0637D4704F977CF49F09` |
| `registrar/requirements.txt` | `8BF5CB7B8DFFE3BFC3AD2311A9FC15A38FDFBF62C11C2E7DDC050D0188FAF947` |
| `viewer/requirements.txt` | `2DA52AFE87411CE4551AC537EFA3A75F995F789E49AA06AF4F3991D355E7F8CC` |

## Finding

The package correctly refuses a release claim because executed restore evidence and resolved release inputs do not exist. This is a successful fail-closed enforcement result, not an implementation acceptance.

The `RB-PKG-09` check also demonstrates a concrete coupling problem: governance-only commits after the implementation baseline make a release manifest that requires `manifest.commit == HEAD` fail even when no release code changed. Before a release candidate is frozen, the implementation needs one exact release identity that is updated deliberately, or a separately defined source-tree identity that excludes later review-only documentation. The choice belongs in the implementation binding or release contract, not in Doctrine.

Missing `fastapi` and `streamlit` are also concrete proof that the current local verification environment is not the promised offline reproducible release environment. Installing them ad hoc would not satisfy the unresolved wheelhouse/SBOM gate.

## Required next captured cases

1. Freeze an exact release candidate with resolved image digests, dependency inputs, wheelhouse, SBOM, and release identity; rerun `RB-PKG-09`.
2. Execute encrypted Ledger and Registry backups, isolated restores, parity/integrity checks, reconciliation, and separate replay; replace the template with immutable evidence and rerun `RB-BACKUP-08`.
3. Run Registrar and Viewer suites inside that exact offline image set.
4. Continue the seven doctrine/MVP behavior cases already listed in `captured-operational-instances-v1-20261007.md` before enabling governed writes.

