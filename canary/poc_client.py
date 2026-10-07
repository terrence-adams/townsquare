"""Minimal authenticated client for the non-authoritative TownSquare canary."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


ACTIONS = {
    "OPEN": "request:open",
    "WORKING": "request:work",
    "BLOCKED": "request:block",
    "RESOLVED": "request:resolve",
    "CLOSED": "request:accept",
    "CANCELLED": "request:cancel",
}


class ClientError(RuntimeError):
    pass


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _read_secret(path: str) -> str:
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value:
        raise ClientError("credential file is empty")
    return value


def _request(base_url: str, path: str, credential: str, *, method: str = "GET", body=None, headers=None):
    payload = None if body is None else canonical_bytes(body)
    request_headers = {"Authorization": "Bearer " + credential, "Accept": "application/json"}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    request_headers.update(headers or {})
    request = urllib.request.Request(base_url.rstrip("/") + path, data=payload, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", errors="replace")
        raise ClientError(f"TownSquare returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ClientError("TownSquare request failed: " + str(exc)) from exc


def _load_identity(identity_path: str, context_path: str) -> tuple[dict[str, object], str]:
    identity = json.loads(Path(identity_path).read_text(encoding="utf-8"))
    context_bytes = Path(context_path).read_bytes()
    required = {
        "r7_release_id", "r7_input_manifest_sha256", "source_commit", "source_tree",
        "canary_label", "compose_project",
    }
    if not isinstance(identity, dict) or not required <= set(identity):
        raise ClientError("canary identity file is incomplete")
    return identity, hashlib.sha256(context_bytes).hexdigest()


def _sign(proof: dict[str, object], *, minisign: str, secret_key: str) -> tuple[str, str]:
    payload = canonical_bytes(proof)
    with tempfile.TemporaryDirectory(prefix="townsquare-canary-client-") as directory:
        message = Path(directory) / "proof.json"
        signature = Path(directory) / "proof.minisig"
        message.write_bytes(payload)
        result = subprocess.run(
            [minisign, "-S", "-W", "-q", "-s", secret_key, "-m", str(message), "-x", str(signature)],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=10, check=False, shell=False,
        )
        if result.returncode != 0 or not signature.is_file():
            raise ClientError("Minisign could not create the canary proof")
        return _b64url(payload), _b64url(signature.read_bytes())


def post_event(args) -> dict[str, object]:
    credential = _read_secret(args.credential_file)
    body = json.loads(Path(args.event).read_text(encoding="utf-8"))
    if not isinstance(body, dict) or not isinstance(body.get("thread_id"), str):
        raise ClientError("event must be a JSON object with thread_id")
    state = str(body.get("state", "")).upper()
    action = "request:correct" if str(body.get("purpose", "")).upper() == "CORRECTION" else ACTIONS.get(state)
    if action is None:
        raise ClientError("event state is outside the canary Request lifecycle")
    revision = args.revision
    query = urllib.parse.urlencode({"action": action, "revision": revision})
    thread = urllib.parse.quote(body["thread_id"], safe="")
    bundle = _request(args.base_url, f"/v1/context-bundles/{thread}?{query}", credential)
    items = bundle.get("required_items")
    if not isinstance(items, list) or not items:
        raise ClientError("context bundle did not contain required items")
    hashes = []
    for item in items:
        digest = item.get("sha256") if isinstance(item, dict) else None
        if not isinstance(digest, str):
            raise ClientError("context item hash is invalid")
        _request(args.base_url, f"/v1/context-bundle-items/{bundle['bundle_id']}/{digest}", credential)
        hashes.append(digest)
    receipt = _request(
        args.base_url, "/v1/context-receipts", credential, method="POST",
        body={"bundle_id": bundle["bundle_id"], "acknowledged_hashes": hashes},
    ).get("receipt")
    if not isinstance(receipt, str) or not receipt:
        raise ClientError("context receipt was not issued")

    identity, context_sha256 = _load_identity(args.identity, args.context)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    proof = {
        "schema": "townsquare-canary-test-proof-v2",
        "authority_class": "CANARY_TEST",
        "canary_label": identity["canary_label"],
        "compose_project": identity["compose_project"],
        "source_commit": identity["source_commit"],
        "source_tree": identity["source_tree"],
        "r7_release_id": identity["r7_release_id"],
        "r7_input_manifest_sha256": identity["r7_input_manifest_sha256"],
        "r7_context_sha256": context_sha256,
        "audience": "townsquare-canary-ledger-api",
        "service_id": "townsquare-ledger-v0",
        "issuer": "townsquare-canary-test:" + args.issuer,
        "key_id": "townsquare-canary-test:" + args.key_id,
        "scope": {"action": action, "object_id": body["thread_id"]},
        "context_sha256": hashlib.sha256(canonical_bytes(body)).hexdigest(),
        "issued_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "expires_at": (now + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nonce": "poc-" + secrets.token_urlsafe(24),
    }
    proof_header, signature_header = _sign(proof, minisign=args.minisign, secret_key=args.secret_key)
    return _request(
        args.base_url, "/v1/events", credential, method="POST", body=body,
        headers={
            "Idempotency-Key": args.idempotency_key,
            "If-Match": revision,
            "X-Context-Receipt": receipt,
            "X-Canary-Test-Proof": proof_header,
            "X-Canary-Test-Signature": signature_header,
        },
    )


def read_thread(args) -> dict[str, object]:
    credential = _read_secret(args.credential_file)
    thread = urllib.parse.quote(args.thread_id, safe="")
    return _request(args.base_url, f"/v1/native/threads/{thread}?include_archived=true", credential)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://192.168.2.3:18790")
    subparsers = parser.add_subparsers(dest="command", required=True)

    post = subparsers.add_parser("post")
    post.add_argument("--credential-file", required=True)
    post.add_argument("--secret-key", required=True)
    post.add_argument("--minisign", required=True)
    post.add_argument("--identity", required=True)
    post.add_argument("--context", required=True)
    post.add_argument("--event", required=True)
    post.add_argument("--revision", default="new")
    post.add_argument("--idempotency-key", required=True)
    post.add_argument("--issuer", required=True)
    post.add_argument("--key-id", required=True)
    post.set_defaults(handler=post_event)

    read = subparsers.add_parser("read")
    read.add_argument("--credential-file", required=True)
    read.add_argument("thread_id")
    read.set_defaults(handler=read_thread)

    args = parser.parse_args()
    print(json.dumps(args.handler(args), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    try:
        main()
    except ClientError as exc:
        raise SystemExit(str(exc))
