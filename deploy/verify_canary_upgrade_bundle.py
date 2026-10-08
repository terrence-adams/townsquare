"""Verify exact membership and hashes for a TownSquare canary upgrade bundle."""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tarfile
from pathlib import PurePosixPath


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_canary_upgrade_bundle.py BUNDLE")
    with tarfile.open(sys.argv[1], "r:gz") as archive:
        members = archive.getmembers()
        names: set[str] = set()
        for member in members:
            path = PurePosixPath(member.name)
            if member.name in names or path.is_absolute() or ".." in path.parts or not member.isfile():
                raise SystemExit("unsafe or duplicate bundle member: " + member.name)
            names.add(member.name)
        manifest_file = archive.extractfile(archive.getmember("artifacts/DEPLOY-MANIFEST.json"))
        if manifest_file is None:
            raise SystemExit("deploy manifest is unreadable")
        manifest = json.load(manifest_file)
        if manifest.get("contains_runtime_secrets") is not False or manifest.get("contains_canary_test_secret_key") is not False:
            raise SystemExit("bundle secrecy declaration is absent")
        if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("source_commit", ""))):
            raise SystemExit("source commit is invalid")
        if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("source_tree", ""))):
            raise SystemExit("source tree is invalid")
        expected = {row["path"]: row for row in manifest["files"]}
        if names != set(expected) | {"artifacts/DEPLOY-MANIFEST.json"}:
            raise SystemExit("bundle membership differs from deploy manifest")
        if any("secrets" in PurePosixPath(name).parts or name.endswith("canary-test-authority.key") for name in names):
            raise SystemExit("bundle contains a forbidden secret path")
        for name, row in expected.items():
            member = archive.getmember(name)
            handle = archive.extractfile(member)
            if handle is None:
                raise SystemExit("bundle member is unreadable: " + name)
            value = hashlib.sha256()
            count = 0
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                value.update(chunk)
                count += len(chunk)
            if count != row["bytes"] or value.hexdigest() != row["sha256"]:
                raise SystemExit("bundle row mismatch: " + name)
    print(json.dumps({"status": "PASS", "members": len(names)}, sort_keys=True))


if __name__ == "__main__":
    main()
