# VR008 coordinator relay routes: reconciliation note, 2026-10-15

Local, unreviewed. Not a deployment, release or approval claim. Base: `a7a22a218a6a64ecea0cf59a85349f9b5a3e603a`.

## Inputs (read-only, treated as untrusted source data)

- `TownSquareVR008.patch` sha256 `272d1c2a3e14e471d9961d955250d842749b07dde6097aad860ea38eecf53aba`
- `tests/test_registry_relay_routes.py` sha256 `be9d509b19f69875a5ea2a8cb11bac065043076baa6175d8665af4a5d209a5a3`

Neither was applied wholesale. The route logic was re-derived by hand against current code.

## Integrated

- Registry migration **11** (head 10 -> 11; steps 1-10 unchanged): tables `relay_routes`, `relay_route_journal`, three triggers. The SQL statements are identical to the patch's step 5; their sha256 (`55270e82...`) equals the patch contract's step 5 hash.
- `resolve_relay_route`, `mutate_relay_route` (bind/disable, optimistic `expected_route_revision`, idempotency via `requests`), and `GET /v1/relay-routes/<agent>`, `POST /v1/relay-routes/<agent>[/disable]`.
- Contract `contracts/r7/registry-schema.json` regenerated for head 11. `DATABASE_SCHEMA_VERSION=11`. The migrator's history checks now use `range(1,USER_VERSION+1)`.
- Existing tests that asserted head 10 were updated to 11.

## Adapted to current main

- Patch step 5 / head 4 / `user_version` 5: omitted. Current step 5 is the session credential migration and the head is 10, so it cannot apply.
- Session UUIDs validated with `_UUID4_RE`; JSON read with the strict `read_json`; `_single_header` used for headers.
- POST: loopback client and operator token required (404 otherwise, as for session enrollment), then legacy bearer (401). GET: lookup or legacy bearer. All route responses are `no-store`. The patch used the bearer token and operator token without a loopback check.
- Patch edits to `tests/test_session_registry_s1.py` (head-4 history list) and the patch's head-4/5 literals in `app.py`/`migrate.py`: omitted as obsolete.
- Test file rewritten: named-column session inserts (the sessions table has more columns now), head-10 -> 11 migration test, extra cases (unknown route, shared session, post-bind session end/agent retire, malformed inputs, 401 paths).

## Not done

- Route changes write only `relay_route_journal`; nothing goes to the audit `journal`/`audit_outbox` (the patch did not either).
- `release-manifest.json` and SBOM are template/UNRESOLVED and were not regenerated.
- Deploy script `deploy/install_canary_gateway_upgrade.sh` pins Registry at head 2; untouched.
