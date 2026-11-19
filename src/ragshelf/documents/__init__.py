"""Normalized documents built from the parse cache: blocks, references, metadata."""

from .build import build_document
from .loader import (
    DocumentError,
    LoadResult,
    ParseCacheMissingError,
    UnknownDocumentError,
    find_source,
    load_bundle,
    load_document,
    load_library,
    load_source,
    locate_bundle,
)
from .metadata import MetadataError, normalize_doi
from .model import Block, BuildReport, Document, Metadata

__all__ = [
    "Block", "BuildReport", "Document", "DocumentError", "LoadResult", "Metadata", "MetadataError",
    "ParseCacheMissingError", "UnknownDocumentError", "build_document", "find_source", "load_bundle",
    "load_document", "load_library", "load_source", "locate_bundle", "normalize_doi",
]
