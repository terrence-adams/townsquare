"""No-follow root checks and fail-closed source-archive validation/extraction."""
from __future__ import annotations

import argparse
import os
import stat
import tarfile
from pathlib import Path, PurePosixPath
from typing import Callable


ALLOWED_TOP_LEVEL = {
    ".dockerignore", ".gitignore", "LICENSE", "README.md", "backup", "canary",
    "docs", "registrar", "registry", "requirements", "shared", "tests", "tools", "viewer",
}
REQUIRED_EMPTY = ("data/ledger", "data/registry", "backups", "evidence")


class CanaryPathError(RuntimeError):
    pass


def _parts(path: Path) -> list[Path]:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    result = []
    for part in absolute.parts[1:]:
        current = current / part
        result.append(current)
    return result


def require_no_follow_directory(path: str | os.PathLike[str], *, must_exist: bool = True) -> Path:
    candidate = Path(path).absolute()
    for segment in _parts(candidate):
        try:
            metadata = os.lstat(segment)
        except FileNotFoundError:
            if must_exist:
                raise CanaryPathError(f"required path does not exist: {segment}")
            break
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise CanaryPathError(f"path segment is not a no-follow directory: {segment}")
    return candidate


def require_beneath(root: Path, candidate: Path) -> None:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise CanaryPathError(f"resolved path escapes the exact canary root: {candidate}") from exc


def validate_root_layout(root: str | os.PathLike[str], *, require_empty: bool = True) -> Path:
    exact = require_no_follow_directory(root)
    for relative in ("build", "compose", "config", "secrets", "data", "data/ledger", "data/registry", "backups", "evidence", "logs"):
        leaf = require_no_follow_directory(exact / relative)
        require_beneath(exact, leaf)
    if require_empty:
        for relative in REQUIRED_EMPTY:
            leaf = exact / relative
            if any(leaf.iterdir()):
                raise CanaryPathError(f"required initially-empty canary directory is not empty: {relative}")
    return exact


def validated_members(archive: tarfile.TarFile) -> list[tarfile.TarInfo]:
    accepted: list[tarfile.TarInfo] = []
    names: set[str] = set()
    for member in archive.getmembers():
        raw = member.name.replace("\\", "/")
        path = PurePosixPath(raw)
        if not raw or raw.startswith("/") or path.is_absolute() or ".." in path.parts:
            raise CanaryPathError(f"archive member has an absolute or traversal path: {raw!r}")
        normalized = str(path)
        if normalized in names:
            raise CanaryPathError(f"archive member would overwrite a duplicate: {normalized}")
        names.add(normalized)
        if not path.parts or path.parts[0] not in ALLOWED_TOP_LEVEL:
            raise CanaryPathError(f"archive member has an unexpected top-level entry: {normalized}")
        if member.issym() or member.islnk():
            raise CanaryPathError(f"archive links are forbidden: {normalized}")
        if member.ischr() or member.isblk() or member.isfifo() or member.isdev():
            raise CanaryPathError(f"archive device/FIFO members are forbidden: {normalized}")
        if not (member.isdir() or member.isfile()):
            raise CanaryPathError(f"unsupported archive member type: {normalized}")
        accepted.append(member)
    return accepted


def extract_validated(
    archive_path: str | os.PathLike[str],
    destination: str | os.PathLike[str],
    *,
    before_write: Callable[[Path], None] | None = None,
) -> None:
    root = require_no_follow_directory(destination)
    if any(root.iterdir()):
        raise CanaryPathError("archive destination must be empty")
    with tarfile.open(archive_path, "r:*") as archive:
        members = validated_members(archive)
        for member in members:
            target = root.joinpath(*PurePosixPath(member.name.replace("\\", "/")).parts)
            require_beneath(root, target)
            if before_write is not None:
                before_write(target)
            require_no_follow_directory(root)
            if target.exists() or target.is_symlink():
                raise CanaryPathError(f"archive extraction refuses an overwrite: {member.name}")
            if member.isdir():
                target.mkdir(mode=0o750, parents=True, exist_ok=False)
                continue
            target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
            require_no_follow_directory(target.parent)
            require_beneath(root, target)
            source = archive.extractfile(member)
            if source is None:
                raise CanaryPathError(f"regular archive member has no content: {member.name}")
            fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o640)
            with source, os.fdopen(fd, "wb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
        require_no_follow_directory(root)
        for member in members:
            require_beneath(root, root.joinpath(*PurePosixPath(member.name.replace("\\", "/")).parts))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive")
    parser.add_argument("destination")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        with tarfile.open(args.archive, "r:*") as archive:
            validated_members(archive)
        return
    extract_validated(args.archive, args.destination)


if __name__ == "__main__":
    main()
