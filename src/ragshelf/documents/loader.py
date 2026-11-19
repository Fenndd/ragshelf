"""Load documents from the parse cache.

Identity is the parse stage's: `doc_id` is the library-relative POSIX path and
the cache is keyed by the file's SHA-256, so a document is found through
`scan_library`. Cache validation reuses `ragshelf.parse.cache.cache_valid`; no
checksum logic lives here. Nothing here loads a parser or model runtime.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from ragshelf.config import Settings
from ragshelf.parse import DocumentSource, content_hash, scan_library
from ragshelf.parse.cache import cache_valid
from ragshelf.parse.html import HTML_EXTENSIONS, html_dependencies
from ragshelf.parse.pipeline import TEXT_DESCRIPTOR

from .build import build_document
from .markdown import markdown_items
from .metadata import MetadataError, PdfInfo, read_pdf_metadata, read_sidecar, sidecar_path
from .model import Document


class DocumentError(Exception):
    """Base for failures to produce a document. Messages never contain content."""


class UnknownDocumentError(DocumentError):
    pass


class ParseCacheMissingError(DocumentError):
    pass


@dataclass(frozen=True)
class LoadResult:
    source: DocumentSource
    document: Document | None = None
    error: str | None = None


def find_source(settings: Settings, doc_id: str) -> DocumentSource:
    """The scanned source with `doc_id`.

    This scans (and hashes) the whole library, so it suits one-off lookups. A
    caller handling many documents uses `load_library`, or scans once and
    passes each source to `load_source`.
    """
    for source in scan_library(settings.paths.library):
        if source.doc_id == doc_id:
            return source
    raise UnknownDocumentError(f"unknown document id: {doc_id!r}")


def locate_bundle(settings: Settings, source: DocumentSource) -> Path:
    """The newest valid bundle applicable to this source, whatever the parser version.

    HTML identity also includes the original URI and consumed local resources,
    using the same discovery contract as the parse stage.
    """
    root = settings.paths.cache / "parse" / source.content_hash
    html_context = (html_dependencies(source.path, original=source.path)
                    if source.path.suffix.lower() in HTML_EXTENSIONS else None)
    found: list[tuple[float, str, Path]] = []
    if root.is_dir() and not (root.is_symlink() or root.is_junction()):
        for entry in root.iterdir():
            if entry.name.startswith(".") or not entry.is_dir():
                continue
            try:
                manifest = json.loads((entry / "manifest.json").read_text(encoding="utf-8"))
                descriptor = manifest["parser"]
                valid = (manifest["parser_key"] == entry.name and isinstance(descriptor, dict)
                         and (html_context is None or descriptor.get("html_context") == html_context)
                         and cache_valid(entry, source.content_hash, descriptor))
                modified = (entry / "manifest.json").stat().st_mtime
            except (OSError, ValueError, KeyError, TypeError):
                continue
            if valid:
                found.append((modified, entry.name, entry))
    if (not found or (html_context is not None
                      and html_dependencies(source.path, original=source.path) != html_context)
            or content_hash(source.path) != source.content_hash):
        raise ParseCacheMissingError(
            f"{source.doc_id}: no valid parse cache entry; run 'ragshelf ingest --parse-only' first")
    return max(found)[2]


def load_bundle(source: DocumentSource, bundle: Path) -> Document:
    """Build a document from a validated cache bundle, its sidecar, and the PDF."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest["parser"] == TEXT_DESCRIPTOR:
        items = markdown_items((bundle / "markdown.md").read_text(encoding="utf-8"))
    else:
        items = json.loads((bundle / "content_list.json").read_text(encoding="utf-8"))
    sidecar = read_sidecar(sidecar_path(source.path))
    pdf = read_pdf_metadata(source.path) if source.path.suffix.lower() == ".pdf" else PdfInfo()
    return build_document(items, doc_id=source.doc_id, content_hash=source.content_hash,
                          parser_key=manifest["parser_key"], sidecar=sidecar, pdf=pdf)


def load_source(settings: Settings, source: DocumentSource) -> Document:
    return load_bundle(source, locate_bundle(settings, source))


def load_document(settings: Settings, doc_id: str) -> Document:
    return load_source(settings, find_source(settings, doc_id))


def _describe(error: Exception) -> str:
    # Only our own errors have content-free messages; others report the class.
    return str(error) if isinstance(error, (DocumentError, MetadataError)) else type(error).__name__


def load_library(settings: Settings) -> list[LoadResult]:
    """Load every document; one failure never stops the others."""
    results = []
    for source in scan_library(settings.paths.library):
        try:
            results.append(LoadResult(source, load_source(settings, source)))
        except Exception as exc:
            results.append(LoadResult(source, error=_describe(exc)))
    return results
