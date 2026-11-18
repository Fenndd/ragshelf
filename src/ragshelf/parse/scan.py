"""Discover originals without reading sidecars or following filesystem links."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

PASSTHROUGH_EXTENSIONS = frozenset({".md", ".txt"})


@dataclass(frozen=True)
class DocumentSource:
    doc_id: str
    path: Path
    content_hash: str


def content_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def supported_extensions() -> frozenset[str]:
    # This registry loads no parser or models. Follow the installed version's
    # accepted inputs instead of maintaining a second, drifting format list.
    from mineru.filetypes import PARSEABLE_EXTENSIONS

    return frozenset("." + ext for ext in PARSEABLE_EXTENSIONS) | PASSTHROUGH_EXTENSIONS


def scan_library(library: Path) -> list[DocumentSource]:
    """Return deterministic identities; missing libraries are configuration errors.

    Symlinks and junctions are not originals owned by this library and are not
    traversed. Metadata JSON and unsupported formats are ignored.
    """
    library = library.resolve(strict=True)
    if not library.is_dir():
        raise NotADirectoryError(library)
    extensions = supported_extensions()
    paths = []
    for root, dirs, files in library.walk(follow_symlinks=False, on_error=_raise):
        dirs[:] = sorted(name for name in dirs if not _is_link(root / name))
        for name in files:
            path = root / name
            if path.suffix.lower() in extensions and not _is_link(path) and path.is_file():
                # Office creates temporary lock files alongside documents.
                if name.startswith("~$"):
                    continue
                paths.append(path)
    return [DocumentSource(p.relative_to(library).as_posix(), p, content_hash(p)) for p in sorted(paths)]


def _is_link(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _raise(error: OSError) -> None:
    raise error
