"""Fail-closed binding for the exact R7 image, runtime, and public context."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

RUNTIME_FIELDS = (
    "TOWNSQUARE_RUNTIME_CLASS", "TOWNSQUARE_AUTHORITY_CLASS", "TOWNSQUARE_CANARY_LABEL",
    "TOWNSQUARE_COMPOSE_PROJECT", "TOWNSQUARE_SOURCE_COMMIT", "TOWNSQUARE_SOURCE_TREE",
    "TOWNSQUARE_R7_RELEASE_ID", "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256",
)
EMBEDDED_FIELDS = tuple("TOWNSQUARE_EMBEDDED_" + name.removeprefix("TOWNSQUARE_") for name in RUNTIME_FIELDS)
IDENTITY_FILE_ENV = "TOWNSQUARE_R7_IDENTITY_FILE"
IDENTITY_FILE_SHA256_ENV = "TOWNSQUARE_R7_IDENTITY_SHA256"
DEFAULT_IDENTITY_FILE = "/opt/townsquare/release/r7-identity.json"
DEFAULT_CONTEXT_FILE = "/run/config/canary-context-manifest.json"
FIXED_VALUES = {
    "TOWNSQUARE_RUNTIME_CLASS": "CANARY", "TOWNSQUARE_AUTHORITY_CLASS": "NON-AUTHORITATIVE",
    "TOWNSQUARE_CANARY_LABEL": "TS-CANARY-NAS1-20261007-A",
    "TOWNSQUARE_COMPOSE_PROJECT": "townsquare-canary-20261007-a",
}
_GIT_OBJECT = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_RELEASE_ID = re.compile(r"TS-R7-[0-9a-f]{64}")

class CanaryIdentityError(RuntimeError):
    """The process is not the exact reviewed R7 artifact/runtime pair."""

@dataclass(frozen=True)
class CanaryIdentity:
    runtime_class: str
    authority_class: str
    canary_label: str
    compose_project: str
    source_commit: str
    source_tree: str
    r7_release_id: str
    r7_input_manifest_sha256: str
    def as_dict(self) -> dict[str, str]: return asdict(self)

def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name)
    if not isinstance(value, str) or not value or value != value.strip():
        raise CanaryIdentityError(f"required canary identity field {name} is absent or invalid")
    return value

def _identity_from_values(values: Mapping[str, str]) -> CanaryIdentity:
    if not _GIT_OBJECT.fullmatch(values["TOWNSQUARE_SOURCE_COMMIT"]):
        raise CanaryIdentityError("TOWNSQUARE_SOURCE_COMMIT must be an exact lowercase 40-hex Git object id")
    if not _GIT_OBJECT.fullmatch(values["TOWNSQUARE_SOURCE_TREE"]):
        raise CanaryIdentityError("TOWNSQUARE_SOURCE_TREE must be an exact lowercase 40-hex Git object id")
    if not _RELEASE_ID.fullmatch(values["TOWNSQUARE_R7_RELEASE_ID"]):
        raise CanaryIdentityError("TOWNSQUARE_R7_RELEASE_ID must be an exact R7 release id")
    if not _SHA256.fullmatch(values["TOWNSQUARE_R7_INPUT_MANIFEST_SHA256"]):
        raise CanaryIdentityError("TOWNSQUARE_R7_INPUT_MANIFEST_SHA256 must be a lowercase SHA-256")
    return CanaryIdentity(
        runtime_class=values["TOWNSQUARE_RUNTIME_CLASS"], authority_class=values["TOWNSQUARE_AUTHORITY_CLASS"],
        canary_label=values["TOWNSQUARE_CANARY_LABEL"], compose_project=values["TOWNSQUARE_COMPOSE_PROJECT"],
        source_commit=values["TOWNSQUARE_SOURCE_COMMIT"], source_tree=values["TOWNSQUARE_SOURCE_TREE"],
        r7_release_id=values["TOWNSQUARE_R7_RELEASE_ID"],
        r7_input_manifest_sha256=values["TOWNSQUARE_R7_INPUT_MANIFEST_SHA256"],
    )

def verify_canary_identity(environ: Mapping[str, str]) -> CanaryIdentity:
    """Validate exact runtime and immutable image-configuration tuples."""
    runtime = {name: _required(environ, name) for name in RUNTIME_FIELDS}
    embedded = {name: _required(environ, name) for name in EMBEDDED_FIELDS}
    for name, expected in FIXED_VALUES.items():
        embedded_name = "TOWNSQUARE_EMBEDDED_" + name.removeprefix("TOWNSQUARE_")
        if runtime[name] != expected or embedded[embedded_name] != expected:
            raise CanaryIdentityError(f"canary identity field {name} does not match the reviewed value")
    for runtime_name, embedded_name in zip(RUNTIME_FIELDS, EMBEDDED_FIELDS):
        if runtime[runtime_name] != embedded[embedded_name]:
            raise CanaryIdentityError(f"runtime and embedded canary identity differ for {runtime_name}")
    return _identity_from_values(runtime)

def _pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError("duplicate JSON field")
        result[key] = value
    return result

def verify_identity_file(path: str | os.PathLike[str], expected: CanaryIdentity, expected_sha256: str) -> None:
    """Bind generated file bytes to the image hash and exact runtime tuple."""
    identity_path = Path(path)
    if identity_path.is_symlink() or not identity_path.is_file():
        raise CanaryIdentityError("R7 identity file must be a regular non-symlink file")
    if stat.S_IMODE(identity_path.stat().st_mode) & 0o222:
        raise CanaryIdentityError("R7 identity file must not be writable")
    if not _SHA256.fullmatch(expected_sha256 or ""):
        raise CanaryIdentityError("image-pinned R7 identity SHA-256 is absent or invalid")
    raw = identity_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise CanaryIdentityError("R7 identity file hash differs from the image-pinned hash")
    try: value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise CanaryIdentityError("R7 identity file is not valid closed JSON") from exc
    fields = {"schema_version","r7_release_id","r7_input_manifest_sha256","source_commit","source_tree","runtime_class","authority_class","canary_label","compose_project"}
    if not isinstance(value, dict) or set(value) != fields or value.get("schema_version") != "1":
        raise CanaryIdentityError("R7 identity file fields are incomplete or excessive")
    if {key: value.get(key) for key in expected.as_dict()} != expected.as_dict():
        raise CanaryIdentityError("R7 identity file does not match the exact runtime tuple")

def require_canary_identity() -> CanaryIdentity:
    identity = verify_canary_identity(os.environ)
    verify_identity_file(os.environ.get(IDENTITY_FILE_ENV, DEFAULT_IDENTITY_FILE), identity, _required(os.environ, IDENTITY_FILE_SHA256_ENV))
    verify_context_identity(os.environ.get("TOWNSQUARE_CONTEXT_MANIFEST", DEFAULT_CONTEXT_FILE), identity)
    return identity

def verify_context_identity(path: str | os.PathLike[str], expected: CanaryIdentity) -> str:
    """Check the public context before any component-specific file access."""
    context_path = Path(path)
    if context_path.is_symlink() or not context_path.is_file():
        raise CanaryIdentityError("R7 context must be a regular non-symlink file")
    raw = context_path.read_bytes()
    try: value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise CanaryIdentityError("R7 context is invalid JSON") from exc
    fields = {"schema_version","profile_version","r7_release_id","r7_input_manifest_sha256","source_commit","source_tree","canary_label","compose_project","runtime_class","authority_class","service_ids","ledger_contract_sha256","registry_contract_sha256","compatibility_matrix_sha256"}
    if not isinstance(value, dict) or set(value) != fields or value.get("schema_version") != "1" or value.get("profile_version") != "r7-context-v1":
        raise CanaryIdentityError("R7 context fields are incomplete or excessive")
    if any(value.get(key) != wanted for key, wanted in expected.as_dict().items()):
        raise CanaryIdentityError("R7 context does not match the exact image identity")
    return hashlib.sha256(raw).hexdigest()

def compatible_identity(payload: Mapping[str, object], identity: CanaryIdentity) -> bool:
    return all(payload.get(name) == value for name, value in identity.as_dict().items())
