"""Plain-text views of documents for `ragshelf inspect`."""

import unicodedata
from collections.abc import Sequence

from .loader import LoadResult
from .model import METADATA_FIELDS, Document

_BIDI_CONTROLS = frozenset("\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


def _safe(text: str) -> str:
    """Printable text: control characters (a terminal escape sequence in a title) and bidirectional
    overrides are shown as "?". Applied to everything printed, whatever its source."""
    return "".join("?" if c in _BIDI_CONTROLS or (unicodedata.category(c) == "Cc" and c != "\n") else c
                   for c in text)


def _value(document: Document, field: str) -> str:
    value = getattr(document.metadata, field)
    if field == "authors":
        return "; ".join(value)
    return "" if value is None else str(value)


def format_inspect(document: Document) -> str:
    """Metadata with provenance, then the heading outline indented by level."""
    lines = [f"doc_id: {_safe(document.doc_id)}", f"content_hash: {document.content_hash}",
             f"pages: {document.page_count}", "", "Metadata:"]
    for field in METADATA_FIELDS:
        value = _safe(_value(document, field))
        lines.append(f"  {field}: {value or '-'}  [{document.metadata.source_of(field)}]")
    lines += ["", f"Outline ({len(document.outline)} headings):"]
    for heading in document.outline:
        lines.append(f"{'  ' * (heading.level - 1)}{_safe(heading.text)}  (p. {heading.page})")
    if not document.outline:
        lines.append("  (no headings)")
    if document.references:
        entries = sum(len(b.items) if b.type == "list" else b.type == "paragraph" for b in document.references)
        first = document.references[0]
        lines += ["", f"References: {entries} entries from p. {first.page} (kept apart from the body)"]
    else:
        lines += ["", "References: none detected"]
    if document.report.reference_like_in_body:
        lines.append(f"  Check: {document.report.reference_like_in_body} numbered, citation-shaped entries "
                     "remain in the body")
    return "\n".join(lines)


def _one_line(text: str) -> str:
    return " ".join(_safe(text).split())


def format_table(results: Sequence[LoadResult]) -> str:
    """One record per document: doc_id, then title, authors, year, and DOI on labeled lines.

    Nothing is shortened: this listing is how extracted titles and author lists
    are checked, and a clipped value hides exactly the errors to look for (a
    merged title, a truncated author list). One record per document, instead of
    padded columns, keeps a 300-character title readable. The doc_id is what
    `ragshelf inspect <doc_id>` takes; a document that failed shows its error.
    """
    blocks = []
    for number, result in enumerate(results, start=1):
        header = f"[{number}] {_one_line(result.source.doc_id)}"
        if result.document is None:
            blocks.append(f"{header}\n    ERROR: {_one_line(result.error or 'unknown error')}")
            continue
        doc = result.document
        blocks.append("\n".join([
            header,
            f"    title:   {_one_line(_value(doc, 'title')) or '-'}",
            f"    authors: {_one_line(_value(doc, 'authors')) or '-'}",
            f"    year:    {_value(doc, 'year') or '-'}",
            f"    doi:     {_one_line(_value(doc, 'doi')) or '-'}",
        ]))
    failed = sum(r.document is None for r in results)
    blocks.append(f"{len(results)} documents, {failed} failed.")
    return "\n\n".join(blocks)
