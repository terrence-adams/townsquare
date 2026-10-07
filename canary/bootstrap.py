"""Issue fresh canary-only credentials without printing any secret material."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path

from canary.safe_archive import require_no_follow_directory
from registrar.app.auth import create_native_credential
from registrar.app.db import connect, verify_schema


SECRET_FILES = {
    "token_pepper": "ledger-token-pepper",
    "cursor_signing_key": "ledger-cursor-signing-key",
    "receipt_hash_key": "ledger-receipt-hash-key",
    "viewer_native_credential": "viewer-native-credential",
    "venom_native_credential": "venom-native-credential",
    "wolverine_native_credential": "wolverine-native-credential",
    "bishop_native_credential": "bishop-native-credential",
    "registry_api_credential": "registry-api-credential",
    "registry_audit_credential": "registry-audit-credential",
    "ledger_to_registry_readiness_ledger": "ledger-to-registry-readiness.ledger",
    "ledger_to_registry_readiness_registry": "ledger-to-registry-readiness.registry",
    "registry_to_ledger_readiness_ledger": "registry-to-ledger-readiness.ledger",
    "registry_to_ledger_readiness_registry": "registry-to-ledger-readiness.registry",
}
EMPTY_TABLES = (
    "ledger_events", "event_content", "native_requests", "registry_audit_events",
    "auth_credentials", "credential_revocations", "verifier_nonces",
)


class BootstrapError(RuntimeError):
    pass


def _opaque_id(key: bytes, purpose: str, identifier: str) -> str:
    return hmac.new(key, (purpose + "\0" + identifier).encode("utf-8"), hashlib.sha256).hexdigest()


def _write_no_clobber(path: Path, value: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(value)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, 0o600)


def _assert_fresh_database(db) -> None:
    verify_schema(db)
    for table in EMPTY_TABLES:
        try:
            count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception as exc:
            raise BootstrapError(f"required fresh-database table is unavailable: {table}") from exc
        if count:
            raise BootstrapError(f"fresh canary database contains rows in {table}")


def bootstrap(db_path: str, secret_directory: str, evidence_key_path: str, ttl_seconds: int) -> dict[str, object]:
    secrets_root = require_no_follow_directory(secret_directory)
    evidence_key_file = Path(evidence_key_path)
    if evidence_key_file.parent.resolve() == secrets_root.resolve():
        raise BootstrapError("the non-runtime evidence key must not be placed in the runtime secrets directory")
    evidence_key = evidence_key_file.read_bytes()
    if len(evidence_key) < 32:
        raise BootstrapError("the non-runtime evidence key must contain at least 32 bytes")
    destinations = {purpose: secrets_root / filename for purpose, filename in SECRET_FILES.items()}
    if any(path.exists() or path.is_symlink() for path in destinations.values()):
        raise BootstrapError("a canary secret destination already exists; refusing to overwrite")

    db = connect(db_path)
    try:
        _assert_fresh_database(db)
        db.execute("BEGIN IMMEDIATE")
        viewer = create_native_credential(
            db, "viewer", policy_version="townsquare-canary-v1", ttl_seconds=ttl_seconds,
        )
        registry_audit = create_native_credential(
            db, "registry-audit", policy_version="townsquare-canary-v1", ttl_seconds=ttl_seconds,
        )
        venom = create_native_credential(
            db, "venom", policy_version="townsquare-canary-v1", ttl_seconds=ttl_seconds,
        )
        wolverine = create_native_credential(
            db, "wolverine", policy_version="townsquare-canary-v1", ttl_seconds=ttl_seconds,
        )
        bishop = create_native_credential(
            db, "bishop", policy_version="townsquare-canary-v1", ttl_seconds=ttl_seconds,
        )
        values = {
            "token_pepper": secrets.token_urlsafe(48),
            "cursor_signing_key": secrets.token_urlsafe(48),
            "receipt_hash_key": secrets.token_urlsafe(48),
            "viewer_native_credential": viewer,
            "venom_native_credential": venom,
            "wolverine_native_credential": wolverine,
            "bishop_native_credential": bishop,
            "registry_api_credential": secrets.token_urlsafe(48),
            "registry_audit_credential": registry_audit,
        }
        ledger_to_registry = secrets.token_urlsafe(48)
        registry_to_ledger = secrets.token_urlsafe(48)
        if hmac.compare_digest(ledger_to_registry, registry_to_ledger):
            raise BootstrapError("directional readiness credentials unexpectedly collided")
        values.update({
            "ledger_to_registry_readiness_ledger": ledger_to_registry,
            "ledger_to_registry_readiness_registry": ledger_to_registry,
            "registry_to_ledger_readiness_ledger": registry_to_ledger,
            "registry_to_ledger_readiness_registry": registry_to_ledger,
        })
        for purpose, destination in destinations.items():
            _write_no_clobber(destination, values[purpose])
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    issued = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = []
    for purpose, destination in destinations.items():
        identifier = values[purpose].split(".", 1)[0] if "credential" in purpose else purpose
        records.append({
            "purpose": purpose,
            "filename": destination.name,
            "mode": "0600",
            "opaque_metadata_id": _opaque_id(evidence_key, purpose, identifier),
        })
    return {
        "schema": "townsquare-canary-bootstrap-metadata-v1",
        "policy_version": "townsquare-canary-v1",
        "issued_at": issued,
        "ttl_seconds": ttl_seconds,
        "credentials": records,
        "directional_readiness_tokens_distinct": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--secret-dir", required=True)
    parser.add_argument("--evidence-key-file", required=True)
    parser.add_argument("--ttl-seconds", required=True, type=int)
    args = parser.parse_args()
    if args.ttl_seconds < 60 or args.ttl_seconds > 86400:
        raise SystemExit("--ttl-seconds must be between 60 and 86400")
    metadata = bootstrap(args.db, args.secret_dir, args.evidence_key_file, args.ttl_seconds)
    print(json.dumps(metadata, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
