"""Validate `docker compose config --format json` before any NAS write."""
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path
from pathlib import PurePosixPath


PROJECT = "townsquare-canary-20261007-a"
ROOT = PurePosixPath("/volume1/docker/townsquare-canary-20261007-a")
SERVICES = {"ledger-migrate", "ledger", "registry-migrate", "registry", "viewer"}
NETWORK = "canary-internal"
IMAGE_REPOSITORIES = {
    "ledger-migrate": "townsquare-canary-ledger", "ledger": "townsquare-canary-ledger",
    "registry-migrate": "townsquare-canary-registry", "registry": "townsquare-canary-registry",
    "viewer": "townsquare-canary-viewer",
}
COMMANDS = {
    "ledger-migrate": ["python", "-m", "canary.preexec", "--", "python", "-c", "from registrar.app.db import connect,migrate; import os; d=connect(os.environ['REGISTRAR_DB']); migrate(d); d.close()"],
    "registry-migrate": ["python", "-m", "canary.preexec", "--", "python", "/app/migrate.py"],
}
FIXED_IDENTITY = {
    "TOWNSQUARE_RUNTIME_CLASS": "CANARY",
    "TOWNSQUARE_AUTHORITY_CLASS": "NON-AUTHORITATIVE",
    "TOWNSQUARE_CANARY_LABEL": "TS-CANARY-NAS1-20261007-A",
    "TOWNSQUARE_COMPOSE_PROJECT": PROJECT,
}
SOURCE_FIELDS = ("TOWNSQUARE_SOURCE_COMMIT", "TOWNSQUARE_SOURCE_TREE")
RELEASE_FIELDS = ("TOWNSQUARE_R7_RELEASE_ID", "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256")
# Exact rendered maps: values are non-secret configuration or mounted file paths.
# The registry public key and viewer credential are fixed application paths;
# unused selectors (including a ledger pepper selector) are unknown keys.
SERVICE_ENVIRONMENT = {
    "ledger-migrate": {"REGISTRAR_DB": "/var/lib/townsquare/ledger.db", "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json"},
    "ledger": {
        "REGISTRAR_ENV": "canary",
        "REGISTRAR_DB": "/var/lib/townsquare/ledger.db",
        "REGISTRAR_CURSOR_KEY_FILE": "/run/secrets/ledger-cursor-signing-key",
        "TOWNSQUARE_RECEIPT_HASH_KEY_FILE": "/run/secrets/ledger-receipt-hash-key",
        "TOWNSQUARE_CANARY_TEST_PUBLIC_KEY_FILE": "/run/config/canary-test-authority.pub",
        "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json",
        "TOWNSQUARE_LEDGER_CONTEXT_MANIFEST": "/run/config/ledger-context-manifest.json",
        "REGISTRY_READINESS_TOKEN_FILE": "/run/secrets/ledger-to-registry-readiness",
        "REGISTRY_PEER_READINESS_TOKEN_FILE": "/run/secrets/registry-to-ledger-readiness",
        "TOWNSQUARE_SERVICE_ID": "townsquare-ledger-v0",
        "TOWNSQUARE_LEDGER_SCHEMA_HEAD": "14",
        "TOWNSQUARE_REGISTRY_AUDIT_CONTRACT": "registry-ledger-audit-v1",
        "REGISTRY_INTEGRATION_ENABLED": "true",
        "REGISTRY_SERVICE_ID": "townsquare-registry-v0",
        "REGISTRY_SCHEMA_HEAD": "2",
        "REGISTRY_AUDIT_CONTRACT_VERSION": "registry-ledger-audit-v1",
        "REGISTRY_READINESS_URL": "http://registry:8789/health/ready",
    },
    "registry-migrate": {"REGISTRY_DB": "/var/lib/registry/registry.db", "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json"},
    "registry": {
        "REGISTRY_DB": "/var/lib/registry/registry.db",
        "REGISTRY_TOKEN_FILE": "/run/secrets/registry-api-credential",
        "REGISTRY_LEDGER_AUDIT_TOKEN_FILE": "/run/secrets/registry-audit-credential",
        "LEDGER_READINESS_TOKEN_FILE": "/run/secrets/registry-to-ledger-readiness",
        "REGISTRY_PEER_READINESS_TOKEN_FILE": "/run/secrets/ledger-to-registry-readiness",
        "REGISTRY_CANARY_NONCE_DIRECTORY": "/var/lib/registry/canary-nonces",
        "REGISTRY_AUDIT_DELIVERY_MODE": "manual",
        "REGISTRY_AUDIT_CONTRACT_VERSION": "registry-ledger-audit-v1",
        "REGISTRY_SERVICE_ID": "townsquare-registry-v0",
        "REGISTRY_SCHEMA_HEAD": "2",
        "REGISTRY_LEDGER_SERVICE_ID": "townsquare-ledger-v0",
        "REGISTRY_LEDGER_SCHEMA_HEAD": "14",
        "REGISTRY_LEDGER_AUDIT_CONTRACT": "registry-ledger-audit-v1",
        "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json",
    },
    "viewer": {
        "TOWNSQUARE_VIEWER_PROFILE": "native-ledger-mvp",
        "REGISTRAR_BASE_URL": "http://ledger:8790",
        "HOME": "/tmp",
        "TOWNSQUARE_CONTEXT_MANIFEST": "/run/config/canary-context-manifest.json",
    },
}
UIDS = {"ledger-migrate": "10001:10001", "ledger": "10001:10001", "registry-migrate": "10003:10003", "registry": "10003:10003", "viewer": "10002:10002"}
def bind(source, target, read_only=False): return {"type": "bind", "source": str(ROOT / source), "target": target, "read_only": read_only}
EXPECTED_MOUNTS = {
    "ledger-migrate": [bind("data/ledger", "/var/lib/townsquare"), bind("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
    "ledger": [bind("data/ledger", "/var/lib/townsquare"), bind("secrets/ledger-token-pepper", "/run/secrets/ledger-token-pepper", True), bind("secrets/ledger-cursor-signing-key", "/run/secrets/ledger-cursor-signing-key", True), bind("secrets/ledger-receipt-hash-key", "/run/secrets/ledger-receipt-hash-key", True), bind("secrets/ledger-to-registry-readiness.ledger", "/run/secrets/ledger-to-registry-readiness", True), bind("secrets/registry-to-ledger-readiness.ledger", "/run/secrets/registry-to-ledger-readiness", True), bind("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True), bind("config/ledger-context-manifest.json", "/run/config/ledger-context-manifest.json", True), bind("config/canary-test-authority.pub", "/run/config/canary-test-authority.pub", True)],
    "registry-migrate": [bind("data/registry", "/var/lib/registry"), bind("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
    "registry": [bind("data/registry", "/var/lib/registry"), bind("secrets/registry-api-credential", "/run/secrets/registry-api-credential", True), bind("secrets/registry-audit-credential", "/run/secrets/registry-audit-credential", True), bind("secrets/ledger-to-registry-readiness.registry", "/run/secrets/ledger-to-registry-readiness", True), bind("secrets/registry-to-ledger-readiness.registry", "/run/secrets/registry-to-ledger-readiness", True), bind("config/canary-test-authority.pub", "/run/config/canary-test-authority.pub", True), bind("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
    "viewer": [bind("secrets/viewer-native-credential", "/run/secrets/viewer-native-credential", True), bind("config/canary-context-manifest.json", "/run/config/canary-context-manifest.json", True)],
}
FORBIDDEN_KEYS = {
    "privileged", "cap_add", "devices", "network_mode", "extra_hosts", "dns",
    "pid", "ipc", "profiles",
}


class ComposeValidationError(RuntimeError):
    pass


def _under_root(source: str) -> bool:
    try:
        path = PurePosixPath(source)
        return str(path) == source and ".." not in path.parts and path.relative_to(ROOT) is not None
    except ValueError:
        return False


def _identity(values: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(values, Mapping) or set(values) != set(FIXED_IDENTITY) | set(SOURCE_FIELDS) | set(RELEASE_FIELDS):
        raise ComposeValidationError("trusted identity must contain exactly eight identity fields")
    if any(values[key] != value for key, value in FIXED_IDENTITY.items()):
        raise ComposeValidationError("trusted identity does not identify the reviewed canary")
    if any(not isinstance(values[key], str) or not re.fullmatch(r"[0-9a-f]{40}", values[key]) for key in SOURCE_FIELDS):
        raise ComposeValidationError("trusted source commit and tree must be concrete lowercase 40-hex ids")
    if not isinstance(values["TOWNSQUARE_R7_RELEASE_ID"], str) or not re.fullmatch(r"TS-R7-[0-9a-f]{64}", values["TOWNSQUARE_R7_RELEASE_ID"]):
        raise ComposeValidationError("trusted release id is invalid")
    if not isinstance(values["TOWNSQUARE_R7_INPUT_MANIFEST_SHA256"], str) or not re.fullmatch(r"[0-9a-f]{64}", values["TOWNSQUARE_R7_INPUT_MANIFEST_SHA256"]):
        raise ComposeValidationError("trusted input-manifest digest is invalid")
    return dict(values)


def read_identity_env(path: str) -> dict[str, str]:
    """Read a separately trusted identity-only file; never expand shell/env values."""
    values = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or key in values:
            raise ComposeValidationError("identity file has a malformed or duplicate field")
        values[key] = value
    return _identity(values)


def validate(model: dict[str, object], *, expected_identity: Mapping[str, str]) -> None:
    """Check against independently trusted identity, never identity from the model."""
    identity = _identity(expected_identity)
    if model.get("name") != PROJECT:
        raise ComposeValidationError("Compose project name is not the exact canary project")
    services = model.get("services")
    networks = model.get("networks")
    if not isinstance(services, dict) or set(services) != SERVICES:
        raise ComposeValidationError("Compose service set is not the five-service canary allowlist")
    if not isinstance(networks, dict) or set(networks) != {NETWORK} or networks[NETWORK].get("internal") is not True:
        raise ComposeValidationError("Compose must define exactly one internal network")
    if model.get("volumes"):
        raise ComposeValidationError("Docker named volumes are forbidden")
    expected_ports = {"ledger": {("192.168.2.3", 18790, 8790)}, "viewer": {("192.168.2.3", 18502, 8502)}}
    for name, raw in services.items():
        if not isinstance(raw, dict):
            raise ComposeValidationError(f"service {name} is not an object")
        if any(key in raw for key in FORBIDDEN_KEYS):
            raise ComposeValidationError(f"service {name} carries a forbidden Compose option")
        environment=dict(raw.get("environment",{}))
        if name=="ledger":
            context_hash=environment.pop("TOWNSQUARE_LEDGER_CONTEXT_MANIFEST_SHA256",None)
            if not isinstance(context_hash,str) or not re.fullmatch(r"[0-9a-f]{64}",context_hash):
                raise ComposeValidationError("Ledger governed-context hash is absent or invalid")
        if environment != {**identity, **SERVICE_ENVIRONMENT[name]}:
            raise ComposeValidationError(f"service {name} environment contract is not exact")
        image = IMAGE_REPOSITORIES[name] + ":" + identity["TOWNSQUARE_SOURCE_COMMIT"]
        if "entrypoint" in raw or "build" in raw or raw.get("image") != image:
            raise ComposeValidationError(f"service {name} entrypoint/build/image is not exact")
        if name in {"ledger", "registry", "viewer"} and "command" in raw:
            raise ComposeValidationError(f"steady service {name} command override is forbidden")
        if name in COMMANDS and raw.get("command") != COMMANDS[name]:
            raise ComposeValidationError(f"migrator {name} command is not exact")
        if raw.get("restart") != "no" or raw.get("read_only") is not True or raw.get("pull_policy") != "never":
            raise ComposeValidationError(f"service {name} lacks restart/read-only/pull containment")
        if raw.get("user") != UIDS[name]:
            raise ComposeValidationError(f"service {name} UID is not exact")
        if raw.get("networks") not in ([NETWORK], {NETWORK: None}, {NETWORK: {}}):
            raise ComposeValidationError(f"service {name} is not confined to the sole internal network")
        if not raw.get("tmpfs"):
            raise ComposeValidationError(f"service {name} lacks bounded tmpfs")
        if raw.get("cap_drop") != ["ALL"] or "no-new-privileges:true" not in raw.get("security_opt", []):
            raise ComposeValidationError(f"service {name} lacks capability/no-new-privileges containment")
        mounts = raw.get("volumes", [])
        if not all(isinstance(mount, dict) and isinstance(mount.get("source"), str) and _under_root(mount["source"]) for mount in mounts):
            raise ComposeValidationError(f"service {name} mount escapes the exact canary root")
        normalized = [{"type": mount.get("type"), "source": str(PurePosixPath(mount["source"])), "target": mount.get("target"), "read_only": mount.get("read_only", False)} for mount in mounts]
        if normalized != EXPECTED_MOUNTS[name]:
            raise ComposeValidationError(f"service {name} mount contract is not exact")
        actual_ports = set()
        for port in raw.get("ports", []):
            if not isinstance(port, dict):
                raise ComposeValidationError(f"service {name} has an unstructured port mapping")
            actual_ports.add((port.get("host_ip"), int(port.get("published")), int(port.get("target"))))
        if actual_ports != expected_ports.get(name, set()):
            raise ComposeValidationError(f"service {name} port mapping is not the exact NAS LAN allowlist")
        if name not in {"ledger", "viewer"} and raw.get("ports"):
            raise ComposeValidationError(f"service {name} must not publish a host port")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rendered_json")
    parser.add_argument("--identity-env", required=True, help="independently trusted six-field canary identity file")
    args = parser.parse_args()
    with open(args.rendered_json, encoding="utf-8") as handle:
        model = json.load(handle)
    validate(model, expected_identity=read_identity_env(args.identity_env))


if __name__ == "__main__":
    main()
