"""Closed proof-v2 verification with release/context binding and single-use nonces."""
from __future__ import annotations

import base64, hashlib, json, os, re, sqlite3, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Protocol
from .canary_identity import CanaryIdentity, verify_context_identity

PROOF_SCHEMA = "townsquare-canary-test-proof-v2"
CONTEXT_SCHEMA = "townsquare-r7-context-v1"
AUTHORITY_CLASS = "CANARY_TEST"
APPROVED_MINISIGN = "/usr/local/bin/minisign"
ISSUER_PREFIX = "townsquare-canary-test:"
KEY_ID_PREFIX = "townsquare-canary-test:"
_NAME = re.compile(r"[A-Za-z0-9._:/-]{1,160}")
_SHA256 = re.compile(r"[0-9a-f]{64}")

class CanaryAuthorityError(RuntimeError): pass
class NonceStore(Protocol):
    def consume(self, key_id: str, nonce: str, used_at: str) -> None: ...

class SQLiteNonceStore:
    def __init__(self, db: sqlite3.Connection): self.db = db
    def consume(self, key_id: str, nonce: str, used_at: str) -> None:
        try: self.db.execute("INSERT INTO verifier_nonces VALUES (?,?,?)", (key_id, nonce, used_at))
        except sqlite3.IntegrityError as exc: raise CanaryAuthorityError("CANARY_TEST nonce was already consumed") from exc

class FileNonceStore:
    def __init__(self, root: str | os.PathLike[str]): self.root = Path(root)
    def consume(self, key_id: str, nonce: str, used_at: str) -> None:
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        digest = hashlib.sha256((key_id + "\0" + nonce).encode()).hexdigest()
        try: fd = os.open(self.root / digest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc: raise CanaryAuthorityError("CANARY_TEST nonce was already consumed") from exc
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"key_id": key_id, "nonce_id": digest, "used_at": used_at}, handle, sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())

def canonical_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def _pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError("duplicate field")
        result[key] = value
    return result
def decode_proof(value: str) -> dict[str, object]:
    if not isinstance(value, str) or not value or len(value) > 16384 or "=" in value:
        raise CanaryAuthorityError("CANARY_TEST proof header is absent, padded, or too large")
    try:
        decoded = base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))
        proof = json.loads(decoded.decode("utf-8"), object_pairs_hook=_pairs)
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc: raise CanaryAuthorityError("CANARY_TEST proof header is invalid") from exc
    if not isinstance(proof, dict) or decoded != canonical_bytes(proof): raise CanaryAuthorityError("CANARY_TEST proof must be one canonical object")
    return proof
def decode_signature(value: str) -> bytes:
    if not isinstance(value, str) or not value or len(value) > 32768: raise CanaryAuthorityError("CANARY_TEST signature header is absent or too large")
    try: signature = base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))
    except (ValueError, UnicodeError) as exc: raise CanaryAuthorityError("CANARY_TEST signature header is invalid") from exc
    if not signature or len(signature) > 16384: raise CanaryAuthorityError("CANARY_TEST signature is empty or too large")
    return signature
def minisign_verify(payload: bytes, signature: bytes, public_key_path: str) -> bool:
    if not os.path.isabs(APPROVED_MINISIGN) or not os.path.isfile(APPROVED_MINISIGN): return False
    public_key = Path(public_key_path)
    if not public_key.is_file() or public_key.stat().st_size > 16384: return False
    try:
        with tempfile.TemporaryDirectory(prefix="townsquare-canary-proof-") as directory:
            message, detached = Path(directory)/"proof.json", Path(directory)/"proof.minisig"
            message.write_bytes(payload); detached.write_bytes(signature)
            return subprocess.run([APPROVED_MINISIGN,"-Vm",str(message),"-x",str(detached),"-p",str(public_key)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False, shell=False).returncode == 0
    except (OSError, subprocess.SubprocessError): return False
def _parse_utc(value: object) -> datetime | None:
    if not isinstance(value, str): return None
    try: return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError: return None

def load_r7_context(path: str | os.PathLike[str], identity: CanaryIdentity) -> str:
    try: return verify_context_identity(path, identity)
    except Exception as exc: raise CanaryAuthorityError(str(exc)) from exc

class CanaryProofVerifier:
    def __init__(self, identity: CanaryIdentity, nonce_store: NonceStore, public_key_path: str, *, r7_context_sha256: str, signature_verifier: Callable[[bytes, bytes, str], bool] = minisign_verify):
        if not _SHA256.fullmatch(r7_context_sha256): raise CanaryAuthorityError("R7 context SHA-256 is invalid")
        self.identity, self.nonce_store, self.public_key_path = identity, nonce_store, public_key_path
        self.r7_context_sha256, self.signature_verifier = r7_context_sha256, signature_verifier
    def verify_and_consume(self, proof: Mapping[str, object], signature: bytes, *, audience: str, service_id: str, action: str, object_id: str, context_sha256: str, now: datetime | None = None) -> dict[str, object]:
        expected_keys = {"schema","authority_class","canary_label","compose_project","source_commit","source_tree","r7_release_id","r7_input_manifest_sha256","r7_context_sha256","audience","service_id","issuer","key_id","scope","context_sha256","issued_at","expires_at","nonce"}
        if set(proof) != expected_keys or not isinstance(proof.get("scope"), Mapping) or set(proof["scope"]) != {"action","object_id"}: raise CanaryAuthorityError("CANARY_TEST proof fields are incomplete or excessive")
        if proof.get("schema") != PROOF_SCHEMA or proof.get("authority_class") != AUTHORITY_CLASS: raise CanaryAuthorityError("only proof-v2 CANARY_TEST authority is accepted")
        if not self.signature_verifier(canonical_bytes(proof), signature, self.public_key_path): raise CanaryAuthorityError("CANARY_TEST signature is invalid")
        for name in ("canary_label","compose_project","source_commit","source_tree","r7_release_id","r7_input_manifest_sha256"):
            expected=getattr(self.identity,name)
            if proof.get(name) != expected: raise CanaryAuthorityError(f"CANARY_TEST proof {name} does not match the R7 image")
        if proof.get("r7_context_sha256") != self.r7_context_sha256: raise CanaryAuthorityError("CANARY_TEST proof context does not match the mounted R7 context")
        if proof.get("audience") != audience or proof.get("service_id") != service_id: raise CanaryAuthorityError("CANARY_TEST proof audience or service is wrong")
        issuer, key_id = proof.get("issuer"), proof.get("key_id")
        if not isinstance(issuer,str) or not issuer.startswith(ISSUER_PREFIX) or not _NAME.fullmatch(issuer): raise CanaryAuthorityError("CANARY_TEST issuer is outside the canary namespace")
        if not isinstance(key_id,str) or not key_id.startswith(KEY_ID_PREFIX) or not _NAME.fullmatch(key_id): raise CanaryAuthorityError("CANARY_TEST key id is outside the canary namespace")
        if proof.get("scope") != {"action":action,"object_id":object_id}: raise CanaryAuthorityError("CANARY_TEST proof scope is missing, excessive, or wrong")
        if proof.get("context_sha256") != context_sha256: raise CanaryAuthorityError("CANARY_TEST proof request context is wrong")
        issued_at, expires_at, instant = _parse_utc(proof.get("issued_at")), _parse_utc(proof.get("expires_at")), now or datetime.now(timezone.utc)
        if issued_at is None or expires_at is None or issued_at > instant or expires_at <= instant or expires_at <= issued_at: raise CanaryAuthorityError("CANARY_TEST proof is not currently valid")
        nonce = proof.get("nonce")
        if not isinstance(nonce,str) or len(nonce)<24 or len(nonce)>256 or not _NAME.fullmatch(nonce): raise CanaryAuthorityError("CANARY_TEST nonce is invalid")
        self.nonce_store.consume(key_id, nonce, instant.strftime("%Y-%m-%dT%H:%M:%SZ"))
        return dict(proof)

def reject_canary_test_in_normal_domain(proof: Mapping[str, object]) -> None:
    if proof.get("authority_class") == AUTHORITY_CLASS or proof.get("schema") == PROOF_SCHEMA: raise CanaryAuthorityError("CANARY_TEST proof is forbidden outside the canary verifier")
