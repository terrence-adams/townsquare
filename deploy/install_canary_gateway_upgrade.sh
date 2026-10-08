#!/bin/sh
set -eu

BUNDLE=${1:?bundle path required}
EXPECTED_BUNDLE_SHA256=${2:?bundle SHA-256 required}
EXPECTED_INSTALLER_SHA256=${3:?installer SHA-256 required}
DOCKER=/usr/local/bin/docker
PYTHON=/usr/local/bin/python3
TARGET=/volume1/Docker/townsquare-canary-20261007-a
PROJECT=townsquare-canary-20261007-a
PREVIOUS_COMMIT=6d0f58b8f08342040f4d03193fa95ea3fe7c6310
PYTHON_IMAGE='python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9'
PYTHON_IMAGE_ID='sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4'
STAGE=$(CDPATH= cd -- "$(dirname -- "$BUNDLE")" && pwd)
UNPACK=$STAGE/unpacked
SWAPPED=0
ARCHIVE=

rollback() {
    rc=$?
    trap - EXIT HUP INT TERM
    if [ "$rc" -ne 0 ] && [ "$SWAPPED" -eq 1 ]; then
        printf '%s\n' 'Upgrade failed after the package swap; restoring the preserved package.' >&2
        failed="$STAGE/failed-new-target-$NEW_SHORT"
        if [ -d "$TARGET" ] && [ ! -e "$failed" ]; then
            sudo "$DOCKER" compose --project-name "$PROJECT" --project-directory "$TARGET/compose" --file "$TARGET/compose/compose.canary.yml" --env-file "$TARGET/config/canary.env" --env-file "$TARGET/evidence/compose-runtime.env" down --remove-orphans >/dev/null 2>&1 || true
            sudo "$PYTHON" -c 'import os,sys; os.rename(sys.argv[1],sys.argv[2])' "$TARGET" "$failed" || true
        fi
        if [ -d "$ARCHIVE" ] && [ ! -e "$TARGET" ]; then
            sudo "$PYTHON" -c 'import os,sys; os.rename(sys.argv[1],sys.argv[2])' "$ARCHIVE" "$TARGET" || true
            sudo "$DOCKER" compose --project-name "$PROJECT" --project-directory "$TARGET/compose" --file "$TARGET/compose/compose.canary.yml" --env-file "$TARGET/config/canary.env" --env-file "$TARGET/evidence/compose-runtime.env" up -d --no-build || true
        fi
    fi
    exit "$rc"
}
trap rollback EXIT HUP INT TERM

test -x "$PYTHON"
test -x "$DOCKER"
test -f "$BUNDLE"
test "$(sha256sum "$BUNDLE" | awk '{print $1}')" = "$EXPECTED_BUNDLE_SHA256"
test "$(sha256sum "$0" | awk '{print $1}')" = "$EXPECTED_INSTALLER_SHA256"
test -d "$TARGET"
test ! -L "$TARGET"
test ! -e "$UNPACK"
mkdir -m 0700 "$UNPACK"
tar -xzf "$BUNDLE" -C "$UNPACK"
"$PYTHON" "$UNPACK/artifacts/verify_canary_upgrade_bundle.py" "$BUNDLE"
. "$UNPACK/config/canary.env"
NEW_COMMIT=$TOWNSQUARE_SOURCE_COMMIT
NEW_TREE=$TOWNSQUARE_SOURCE_TREE
NEW_SHORT=$(printf '%.7s' "$NEW_COMMIT")
ARCHIVE="/volume1/Docker/townsquare-canary-backup-$PREVIOUS_COMMIT-before-$NEW_SHORT"
test ! -e "$ARCHIVE"

"$PYTHON" - "$UNPACK" "$PREVIOUS_COMMIT" <<'PY'
import hashlib, json, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
previous = sys.argv[2]
manifest = json.loads((root / "artifacts/DEPLOY-MANIFEST.json").read_text(encoding="utf-8"))
identity = json.loads((root / "build/r7-identity.json").read_text(encoding="utf-8"))
evidence = json.loads((root / "artifacts/STAGING-EVIDENCE.json").read_text(encoding="utf-8"))
assert manifest["previous_source_commit"] == previous
assert manifest["source_commit"] == identity["source_commit"] == evidence["prepared_from_commit"]
assert manifest["source_tree"] == identity["source_tree"] == evidence["prepared_from_tree"]
assert re.fullmatch(r"[0-9a-f]{40}", manifest["source_commit"])
assert re.fullmatch(r"[0-9a-f]{40}", manifest["source_tree"])
assert hashlib.sha256((root / "build/r7-identity.json").read_bytes()).hexdigest() == evidence["r7_identity_sha256"]
assert hashlib.sha256((root / "compose/compose.canary.yml").read_bytes()).hexdigest() == evidence["compose_sha256"]
assert (root / "config/ledger-context-manifest.sha256").read_text(encoding="ascii").strip() == evidence["ledger_context_sha256"]
PY

LEDGER_CONTEXT_SHA256=$(cat "$UNPACK/config/ledger-context-manifest.sha256")
printf 'TOWNSQUARE_LEDGER_CONTEXT_MANIFEST_SHA256=%s\n' "$LEDGER_CONTEXT_SHA256" > "$UNPACK/runtime.env"
"$DOCKER" compose --project-name "$PROJECT" --project-directory "$UNPACK/compose" --file "$UNPACK/compose/compose.canary.yml" --env-file "$UNPACK/config/canary.env" --env-file "$UNPACK/runtime.env" config --format json > "$UNPACK/rendered.json"
"$PYTHON" - "$UNPACK/rendered.json" "$UNPACK/normalized.json" <<'PY'
import json, pathlib, sys
source, destination = map(pathlib.Path, sys.argv[1:])
model = json.loads(source.read_text(encoding="utf-8"))
steady = {"ledger", "registry", "viewer"}
services = set(model.get("services", {}))
assert services == {"ledger-migrate", "ledger", "registry-migrate", "registry", "viewer", "read-gateway"}
for name, service in model["services"].items():
    if "entrypoint" in service:
        assert service["entrypoint"] is None
        del service["entrypoint"]
    if service.get("command", "absent") is None:
        assert name in steady
        del service["command"]
destination.write_text(json.dumps(model, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
PY
PYTHONPATH="$UNPACK/build" "$PYTHON" -m canary.validate_compose "$UNPACK/normalized.json" --identity-env "$UNPACK/config/canary.env"

printf '%s\n' "Enter batman's NAS sudo password to build and install the verified read-gateway upgrade."
sudo -v
test "$(sudo "$DOCKER" image inspect "$PYTHON_IMAGE" --format '{{.Id}}')" = "$PYTHON_IMAGE_ID"

. "$UNPACK/config/canary.env"
R7_IDENTITY_SHA256=$(sha256sum "$UNPACK/build/r7-identity.json" | awk '{print $1}')
build_image() {
    dockerfile=$1
    tag=$2
    sudo "$DOCKER" build --network=none --pull=false \
      --build-arg "PYTHON_IMAGE=$PYTHON_IMAGE" \
      --build-arg "TOWNSQUARE_RUNTIME_CLASS=$TOWNSQUARE_RUNTIME_CLASS" \
      --build-arg "TOWNSQUARE_AUTHORITY_CLASS=$TOWNSQUARE_AUTHORITY_CLASS" \
      --build-arg "TOWNSQUARE_CANARY_LABEL=$TOWNSQUARE_CANARY_LABEL" \
      --build-arg "TOWNSQUARE_COMPOSE_PROJECT=$TOWNSQUARE_COMPOSE_PROJECT" \
      --build-arg "TOWNSQUARE_SOURCE_COMMIT=$NEW_COMMIT" \
      --build-arg "TOWNSQUARE_SOURCE_TREE=$NEW_TREE" \
      --build-arg "TOWNSQUARE_R7_RELEASE_ID=$TOWNSQUARE_R7_RELEASE_ID" \
      --build-arg "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256=$TOWNSQUARE_R7_INPUT_MANIFEST_SHA256" \
      --build-arg "TOWNSQUARE_R7_IDENTITY_SHA256=$R7_IDENTITY_SHA256" \
      --file "$UNPACK/build/$dockerfile" --tag "$tag" "$UNPACK/build"
}
build_image registrar/Dockerfile "townsquare-canary-ledger:$NEW_COMMIT"
build_image registry/Dockerfile "townsquare-canary-registry:$NEW_COMMIT"
build_image viewer/Dockerfile "townsquare-canary-viewer:$NEW_COMMIT"

"$PYTHON" - "$TARGET" "$PREVIOUS_COMMIT" <<'PY'
import hashlib, json, os, pathlib, sqlite3, stat, sys
root = pathlib.Path(sys.argv[1]); expected = sys.argv[2]
manifest = json.loads((root / "artifacts/DEPLOY-MANIFEST.json").read_text(encoding="utf-8"))
assert manifest["source_commit"] == expected
expected_secrets = {
 "ledger-token-pepper", "ledger-cursor-signing-key", "ledger-receipt-hash-key", "viewer-native-credential",
 "venom-native-credential", "wolverine-native-credential", "bishop-native-credential", "registry-api-credential",
 "registry-audit-credential", "ledger-to-registry-readiness.ledger", "ledger-to-registry-readiness.registry",
 "registry-to-ledger-readiness.ledger", "registry-to-ledger-readiness.registry",
}
actual = {path.name for path in (root / "secrets").iterdir()}
assert actual == expected_secrets
assert all(stat.S_ISREG(os.lstat(path).st_mode) and path.stat().st_size for path in (root / "secrets").iterdir())
for relative, versions, application_id, user_version in (
 ("data/ledger/ledger.db", list(range(1,15)), 1414745159, 14),
 ("data/registry/registry.db", [1,2], 1414746695, 2),
):
    path = root / relative
    assert stat.S_ISREG(os.lstat(path).st_mode)
    db = sqlite3.connect(path)
    try:
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        table = "schema_migrations" if "ledger" in relative else "registry_migrations"
        assert [row[0] for row in db.execute(f"SELECT version FROM {table} ORDER BY version")] == versions
        assert db.execute("PRAGMA application_id").fetchone()[0] == application_id
        assert db.execute("PRAGMA user_version").fetchone()[0] == user_version
    finally: db.close()
PY

compose_current() {
    sudo "$DOCKER" compose --project-name "$PROJECT" --project-directory "$TARGET/compose" --file "$TARGET/compose/compose.canary.yml" --env-file "$TARGET/config/canary.env" --env-file "$TARGET/evidence/compose-runtime.env" "$@"
}
compose_current down --remove-orphans

sudo "$PYTHON" - "$TARGET" <<'PY'
import pathlib, sqlite3, sys
root = pathlib.Path(sys.argv[1])
for relative in ("data/ledger/ledger.db", "data/registry/registry.db"):
    db = sqlite3.connect(root / relative)
    try:
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    finally: db.close()
    for suffix in ("-wal", "-shm", "-journal"):
        path = pathlib.Path(str(root / relative) + suffix)
        assert not path.exists() or path.stat().st_size == 0
PY

sudo "$PYTHON" -c 'import os,sys; os.rename(sys.argv[1],sys.argv[2])' "$TARGET" "$ARCHIVE"
sudo "$PYTHON" -c 'import os,sys; os.rename(sys.argv[1],sys.argv[2])' "$UNPACK" "$TARGET"
SWAPPED=1
sudo install -d -m 0700 -o 10001 -g 10001 "$TARGET/data/ledger"
sudo install -d -m 0700 -o 10003 -g 10003 "$TARGET/data/registry"
sudo install -d -m 0700 -o 10001 -g 10001 "$TARGET/secrets"
BATMAN_GROUP=$(id -gn)
sudo install -d -m 0700 -o batman -g "$BATMAN_GROUP" "$TARGET/evidence"
sudo install -o 10001 -g 10001 -m 0600 "$ARCHIVE/data/ledger/ledger.db" "$TARGET/data/ledger/ledger.db"
sudo install -o 10003 -g 10003 -m 0600 "$ARCHIVE/data/registry/registry.db" "$TARGET/data/registry/registry.db"
for secret in "$ARCHIVE"/secrets/*; do sudo install -o 10001 -g 10001 -m 0400 "$secret" "$TARGET/secrets/$(basename "$secret")"; done
sudo chown 10003:10003 "$TARGET/secrets/registry-api-credential" "$TARGET/secrets/registry-audit-credential" "$TARGET/secrets/ledger-to-registry-readiness.registry" "$TARGET/secrets/registry-to-ledger-readiness.registry"
sudo chown 10002:10002 "$TARGET/secrets/viewer-native-credential"
printf 'TOWNSQUARE_LEDGER_CONTEXT_MANIFEST_SHA256=%s\n' "$LEDGER_CONTEXT_SHA256" | sudo tee "$TARGET/evidence/compose-runtime.env" >/dev/null
sudo chown batman:"$BATMAN_GROUP" "$TARGET/evidence/compose-runtime.env"
sudo chmod 0400 "$TARGET/evidence/compose-runtime.env"

compose() {
    sudo "$DOCKER" compose --project-name "$PROJECT" --project-directory "$TARGET/compose" --file "$TARGET/compose/compose.canary.yml" --env-file "$TARGET/config/canary.env" --env-file "$TARGET/evidence/compose-runtime.env" "$@"
}
compose run --rm ledger-migrate
compose run --rm registry-migrate
compose up -d --no-build
compose ps --all

healthy=0
attempt=0
while [ "$attempt" -lt 24 ]; do
    attempt=$((attempt + 1))
    if "$PYTHON" -c "import urllib.request; urllib.request.urlopen('http://192.168.2.3:18790/openapi.json',timeout=3).read(); urllib.request.urlopen('http://192.168.2.3:18502/_stcore/health',timeout=3).read(); urllib.request.urlopen('http://192.168.2.3:18503/health/ready',timeout=5).read()" >/dev/null 2>&1; then healthy=1; break; fi
    sleep 5
done
test "$healthy" -eq 1

sudo "$PYTHON" - "$TARGET" <<'PY'
import json, pathlib, sqlite3, sys, urllib.error, urllib.request
root = pathlib.Path(sys.argv[1]); base = "http://192.168.2.3:18503"
db_path = root / "data/ledger/ledger.db"
def count():
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try: return db.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0]
    finally: db.close()
def request(path, method="GET", headers=None):
    req = urllib.request.Request(base + path, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()
before = count()
checks = {}
for name, path, expected in (
    ("live", "/health/live", 200), ("ready", "/health/ready", 200),
    ("discovery", "/v1/native/discovery", 200), ("docs_hidden", "/docs", 404),
    ("invalid_thread", "/v1/native/threads/bad!id", 404),
):
    status, headers, body = request(path); assert status == expected, (name, status, body[:200]); checks[name] = status
    assert headers.get("Cache-Control") == "no-store"
status, _, body = request("/health/live", method="POST"); assert status == 405, (status, body); checks["write_rejected"] = status
status, _, body = request("/health/live?x=1"); assert status == 400, (status, body); checks["query_rejected"] = status
status, _, body = request("/health/live", headers={"Authorization":"Bearer client"}); assert status == 400, (status, body); checks["client_auth_rejected"] = status
status, _, raw = request("/v1/native/discovery"); discovery = json.loads(raw)
candidates = []
for key in ("history", "open_work"):
    candidates.extend(row.get("thread_id") for row in discovery.get(key, []) if isinstance(row, dict))
for values in discovery.get("boards", {}).values(): candidates.extend(values)
candidates = [value for value in candidates if isinstance(value, str)]
assert candidates, "discovery returned no readable thread for exact-read acceptance"
thread_id = candidates[0]
status, headers, raw = request("/v1/native/threads/" + thread_id); assert status == 200, (status, raw[:200]); assert json.loads(raw).get("thread_id") == thread_id; assert headers.get("Cache-Control") == "no-store"
checks["exact_thread"] = status
after = count(); assert before == after, (before, after)
result = {"status":"PASS", "gateway":base, "thread_id":thread_id, "ledger_events_before":before, "ledger_events_after":after, "checks":checks}
(root / "evidence/read-gateway-live-acceptance.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
print(json.dumps(result, sort_keys=True))
PY

SWAPPED=0
trap - EXIT HUP INT TERM
printf '%s\n' 'NAS_CANARY_GATEWAY_UPGRADE_PASS'
