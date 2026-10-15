# TownSquare integration candidate, 2026-10-15

Local, unreviewed integration candidate. It is not a deployment, release or approval claim.

## Lineage

- Base: `origin/main` 4726278ede36f3a151322f88f417925dd3535301.
- Fast-forwarded to `workspace-import/codex/session-registry-s2-protected-lookup` 873a7cf7b0062041fa4907b927886dc458250921 (238 commits ahead of main). Feature tip aa2aeb5fc4f337ab45af0bcc73177cecf30d1143 is an ancestor of 873a7cf.
- Dirty-source snapshot: recovery branch `codex/townsquare-workspace-recovery-20261015` at e09be63b4968f53060c8c8d66d653181e46bdd1e (file checksums in its `recovery-inputs/SHA256SUMS.txt`).

## Incorporated (47 files, byte-identical to the recorded SHA-256 sums)

All were absent from 873a7cf; none changes executable code.

- `contracts/r8/` (12 files): R8 delivery/routing schemas, protocol registry, compatibility manifest, design note.
- `docs/governance/` (2), `docs/product-owner-status-dashboard-v1.md` (1).
- `docs/session-registry/` (13), `docs/townsquare-default/` (12, incl. `vertical-drafts/`), `docs/vertical-authorized-mutation-endpoint/` (10).

## Omitted

- `contracts/r7/registry-schema.json`, `registry/app.py`, `registry/migrate.py`, `registry/schema.sql`, `tests/conformance/test_registry_v2_release_red.py`: the tracked dirty diff (`recovery-inputs/Originals/TownSquare.patch`) targets registry schema head 4. Superseded by migration head 10 in 873a7cf. Not reapplied.
- `tests/test_session_registry_s1.py`: the dirty copy is an older variant. It drops the listener module load and the random locators that 873a7cf's version uses. 873a7cf's version is kept.
- `recovery-inputs/**` (patches, VR008 test, checksums, README): preservation artifacts that live only on the recovery branch.

## VR008 hold

VR008 is held and not applied. Its test `tests/test_registry_relay_routes.py` is not included.

- Preserved at e09be63 on `codex/townsquare-workspace-recovery-20261015`: `recovery-inputs/VR008/TownSquareVR008.patch` (sha256 272d1c2a3e14e471d9961d955250d842749b07dde6097aad860ea38eecf53aba) and `recovery-inputs/VR008/tests/test_registry_relay_routes.py` (sha256 be9d509b19f69875a5ea2a8cb11bac065043076baa6175d8665af4a5d209a5a3).
- Conflict: it was written against the coordinator-route source state. It conflicts at migration step 5 and overlaps session registry state.
- Required reconciliation: rebase the VR008 migration onto the head-10 chain, with its next number after 10. Re-derive its route changes against the current session registry. Then re-run its test and the registry/session suites.

## Tests

See the commit message for the commands and results. 3 failures and 2 skips are open, recorded there.
