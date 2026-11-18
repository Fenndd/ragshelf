"""Checksummed parse bundles, serialized writers, and atomic publication."""

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

from .scan import content_hash

SCHEMA_VERSION = 1


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def parser_key(descriptor: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(descriptor).encode("utf-8")).hexdigest()


def validate_content_list(content: Any) -> None:
    if not isinstance(content, list):
        raise ValueError("Parser content list must be a list")
    for item in content:
        if not isinstance(item, dict) or type(item.get("page_idx")) is not int or item["page_idx"] < 0:
            raise ValueError("Every content item must have a nonnegative integer page_idx")


def safe_child(root: Path, name: str) -> Path:
    # Both separators matter on Windows; absolute paths and drive paths must
    # never turn a parser-provided asset name into a write outside the bundle.
    relative = PurePosixPath(name)
    if not name or "\\" in name or ":" in name or relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid cache asset path")
    result = root.joinpath(*relative.parts)
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError("Cache path escapes bundle")
    return result


def cache_valid(entry: Path, source_hash: str, descriptor: dict[str, Any]) -> bool:
    try:
        if entry.is_symlink() or entry.is_junction():
            return False
        manifest = json.loads((entry / "manifest.json").read_text(encoding="utf-8"))
        if (manifest["schema_version"] != SCHEMA_VERSION or manifest["content_hash"] != source_hash
                or manifest["parser"] != descriptor or manifest["parser_key"] != parser_key(descriptor)):
            return False
        files = manifest["files"]
        if not isinstance(files, dict) or not {"markdown.md", "content_list.json"} <= files.keys():
            return False
        for name, digest in files.items():
            path = safe_child(entry, name)
            if path.is_symlink() or not path.is_file() or content_hash(path) != digest:
                return False
        (entry / "markdown.md").read_text(encoding="utf-8")
        validate_content_list(json.loads((entry / "content_list.json").read_text(encoding="utf-8")))
        return True
    except (OSError, ValueError, KeyError, TypeError):
        return False


def seal_bundle(stage: Path, source_hash: str, descriptor: dict[str, Any]) -> None:
    """Validate output before writing the commit marker (manifest)."""
    (stage / "markdown.md").read_text(encoding="utf-8")
    validate_content_list(json.loads((stage / "content_list.json").read_text(encoding="utf-8")))
    files = {}
    for path in sorted(stage.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise ValueError("Parser output must not contain links")
        if path.is_file():
            files[path.relative_to(stage).as_posix()] = content_hash(path)
    manifest = {"schema_version": SCHEMA_VERSION, "content_hash": source_hash,
                "parser": descriptor, "parser_key": parser_key(descriptor), "files": files}
    (stage / "manifest.json").write_text(canonical_json(manifest), encoding="utf-8")


def publish(stage: Path, entry: Path) -> None:
    """Publish a complete sibling directory; preserve damaged old entries."""
    if entry.exists() or entry.is_symlink():
        entry.rename(entry.with_name(f".invalid-{entry.name}-{uuid4().hex}"))
    stage.rename(entry)


@contextmanager
def batch_lock(cache_root: Path):
    """OS locks survive crashes without stale-lock cleanup or PID guessing."""
    cache_root.mkdir(parents=True, exist_ok=True)
    with (cache_root / ".parse.lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt

            if lock.seek(0, os.SEEK_END) == 0:
                lock.write(b"\0")
                lock.flush()
            lock.seek(0)
            # Fail clearly if another ingestion owns the cache. Do not wait
            # indefinitely while a second model could be loading elsewhere.
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            try:
                yield
            finally:
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
