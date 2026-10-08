"""Build the secret-free, repository-native NAS read-gateway upgrade bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


PROJECT = "townsquare-canary-20261007-a"
TARGET = "/volume1/Docker/townsquare-canary-20261007-a"
RUNTIME_CLASS = "CANARY"
AUTHORITY_CLASS = "NON-AUTHORITATIVE"
CANARY_LABEL = "TS-CANARY-NAS1-20261007-A"
PYTHON_IMAGE = "python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
PYTHON_IMAGE_ID = "sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4"
SOURCE_PATHS = (
    ".dockerignore", ".gitignore", "LICENSE", "README.md", "backup", "canary",
    "contracts", "docs", "registrar", "registry", "requirements", "shared", "tests", "tools", "viewer",
)


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: object) -> str:
    raw = canonical(value)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def safe_extract(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, "r:") as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise SystemExit("unsafe source archive member: " + member.name)
        archive.extractall(destination)


def regular_files(root: Path):
    return sorted((path for path in root.rglob("*") if path.is_file() and not path.is_symlink()), key=lambda path: path.relative_to(root).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-package", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output = (args.output or root / "deploy/out").resolve()
    seed = args.seed_package.resolve()
    if git(root, "status", "--porcelain"):
        raise SystemExit("the repository must be clean before packaging")
    commit = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", "HEAD^{tree}")
    if len(commit) != 40 or len(tree) != 40:
        raise SystemExit("Git did not return full source identities")
    required_seed = (
        seed / "build/wheelhouse", seed / "config/canary-test-authority.pub",
        seed / "config/ledger-context-manifest.json", seed / "config/ledger-context-manifest.sha256",
    )
    if any(not path.exists() for path in required_seed):
        raise SystemExit("seed package lacks a required public or cached build input")

    output.mkdir(parents=True, exist_ok=True)
    final = output / ("townsquare-canary-upgrade-" + commit[:7])
    if final.exists():
        raise SystemExit("output already exists: " + str(final))
    with tempfile.TemporaryDirectory(prefix="townsquare-upgrade-", dir=output) as temp_name:
        stage = Path(temp_name)
        build, compose, config, artifacts = (stage / name for name in ("build", "compose", "config", "artifacts"))
        for directory in (build, compose, config, artifacts):
            directory.mkdir()

        source_archive = artifacts / f"source-{commit}.tar"
        existing_paths = [path for path in SOURCE_PATHS if (root / path).exists()]
        subprocess.run(["git", "archive", "--format=tar", f"--output={source_archive}", "HEAD", "--", *existing_paths], cwd=root, check=True)
        safe_extract(source_archive, build)
        shutil.copytree(seed / "build/wheelhouse", build / "wheelhouse")
        shutil.copy2(build / "canary/compose.canary.yml", compose / "compose.canary.yml")
        for name in ("canary-test-authority.pub", "ledger-context-manifest.json", "ledger-context-manifest.sha256"):
            shutil.copy2(seed / "config" / name, config / name)
        for name in ("install_canary_gateway_upgrade.sh", "verify_canary_upgrade_bundle.py"):
            shutil.copy2(root / "deploy" / name, artifacts / name)

        rows = []
        for path in regular_files(build):
            relative = path.relative_to(build).as_posix()
            if relative == "r7-identity.json":
                raise SystemExit("identity output must not feed its input manifest")
            rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)})
        input_manifest = {
            "schema_version": "1", "profile_version": "townsquare-core-poc-input-v1",
            "source_commit": commit, "source_tree": tree, "runtime_class": RUNTIME_CLASS,
            "authority_class": AUTHORITY_CLASS, "canary_label": CANARY_LABEL, "compose_project": PROJECT,
            "python_image": PYTHON_IMAGE, "python_image_id": PYTHON_IMAGE_ID,
            "source_archive": {"path": source_archive.name, "bytes": source_archive.stat().st_size, "sha256": digest(source_archive)},
            "files": rows,
        }
        input_sha = write_json(config / "R7-INPUT-MANIFEST.json", input_manifest)
        release_id = "TS-R7-" + input_sha
        identity = {
            "schema_version": "1", "r7_release_id": release_id, "r7_input_manifest_sha256": input_sha,
            "source_commit": commit, "source_tree": tree, "runtime_class": RUNTIME_CLASS,
            "authority_class": AUTHORITY_CLASS, "canary_label": CANARY_LABEL, "compose_project": PROJECT,
        }
        identity_sha = write_json(build / "r7-identity.json", identity)
        contract_hashes = {
            "ledger_contract_sha256": digest(build / "contracts/r7/ledger-migrations.json"),
            "registry_contract_sha256": digest(build / "contracts/r7/registry-schema.json"),
            "compatibility_matrix_sha256": digest(build / "contracts/r7/compatibility-matrix.json"),
        }
        context = {
            "schema_version": "1", "profile_version": "r7-context-v1",
            **{key: value for key, value in identity.items() if key != "schema_version"},
            "service_ids": [
                {"role": "ledger", "service_id": "townsquare-ledger-v0"},
                {"role": "registry", "service_id": "townsquare-registry-v0"},
                {"role": "viewer", "service_id": "townsquare-viewer-v0"},
                {"role": "backup", "service_id": "townsquare-backup-v0"},
            ],
            **contract_hashes,
        }
        context_sha = write_json(config / "canary-context-manifest.json", context)
        ledger_context_sha = digest(config / "ledger-context-manifest.json")
        if (config / "ledger-context-manifest.sha256").read_text(encoding="ascii").strip() != ledger_context_sha:
            raise SystemExit("seed governed-context hash is inconsistent")
        env = {
            "TOWNSQUARE_RUNTIME_CLASS": RUNTIME_CLASS, "TOWNSQUARE_AUTHORITY_CLASS": AUTHORITY_CLASS,
            "TOWNSQUARE_CANARY_LABEL": CANARY_LABEL, "TOWNSQUARE_COMPOSE_PROJECT": PROJECT,
            "TOWNSQUARE_SOURCE_COMMIT": commit, "TOWNSQUARE_SOURCE_TREE": tree,
            "TOWNSQUARE_R7_RELEASE_ID": release_id, "TOWNSQUARE_R7_INPUT_MANIFEST_SHA256": input_sha,
        }
        (config / "canary.env").write_text("".join(f"{key}={value}\n" for key, value in env.items()), encoding="ascii", newline="\n")
        evidence = {
            "schema_version": "1", "prepared_from_commit": commit, "prepared_from_tree": tree,
            "input_manifest_sha256": input_sha, "r7_release_id": release_id,
            "r7_identity_sha256": identity_sha, "canary_context_sha256": context_sha,
            "ledger_context_sha256": ledger_context_sha, **contract_hashes,
            "python_image": PYTHON_IMAGE, "python_image_id": PYTHON_IMAGE_ID,
            "compose_sha256": digest(compose / "compose.canary.yml"),
        }
        write_json(artifacts / "STAGING-EVIDENCE.json", evidence)

        selected = []
        for directory in (build, compose, config):
            selected.extend(regular_files(directory))
        selected.extend((source_archive, artifacts / "STAGING-EVIDENCE.json", artifacts / "install_canary_gateway_upgrade.sh", artifacts / "verify_canary_upgrade_bundle.py"))
        selected = sorted(set(selected), key=lambda path: path.relative_to(stage).as_posix())
        manifest = {
            "schema_version": "1", "profile_version": "townsquare-canary-gateway-upgrade-v1",
            "target": TARGET, "previous_source_commit": "6d0f58b8f08342040f4d03193fa95ea3fe7c6310",
            "source_commit": commit, "source_tree": tree, "contains_runtime_secrets": False,
            "contains_canary_test_secret_key": False,
            "files": [{"path": path.relative_to(stage).as_posix(), "bytes": path.stat().st_size, "sha256": digest(path)} for path in selected],
        }
        manifest_path = artifacts / "DEPLOY-MANIFEST.json"
        manifest_path.write_bytes(canonical(manifest))
        bundle = artifacts / f"townsquare-canary-gateway-upgrade-{commit[:7]}.tar.gz"
        with tarfile.open(bundle, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            for path in [*selected, manifest_path]:
                archive.add(path, arcname=path.relative_to(stage).as_posix(), recursive=False)
        sidecar = {
            "bundle": bundle.name, "bytes": bundle.stat().st_size, "sha256": digest(bundle),
            "installer": "install_canary_gateway_upgrade.sh",
            "installer_sha256": digest(artifacts / "install_canary_gateway_upgrade.sh"),
            "source_commit": commit, "source_tree": tree,
        }
        (artifacts / "DEPLOY-BUNDLE.json").write_bytes(canonical(sidecar))
        shutil.move(str(stage), final)

    result = {**sidecar, "output": str(final), "bundle_path": str(final / "artifacts" / sidecar["bundle"]), "installer_path": str(final / "artifacts" / sidecar["installer"])}
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
