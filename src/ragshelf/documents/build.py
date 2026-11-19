"""Build a `Document` from content-list items (MinerU's shape) and metadata sources."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .metadata import (
    Candidates,
    PdfInfo,
    merge_metadata,
    mineru_title_authors,
    mineru_year,
    select_doi,
)
from .model import Block, BuildReport, Document
from .normalize import clean_code, clean_text, collapse_spaces, dehyphenate, find_running_text, word_vocabulary
from .references import count_reference_like, split_references

_AUX_TYPES = frozenset({"header", "footer", "page_number", "aside_text"})
_FLOWING = frozenset({"heading", "paragraph", "caption"})
# Early body paragraphs count as a publication notice only when they start like one.
_NOTICE = re.compile(r"\s*(?:©|\(c\)|copyright|published|accepted|received|available online)", re.IGNORECASE)


@dataclass(frozen=True)
class _Piece:
    type: str
    text: str
    page: int
    level: int | None = None
    items: tuple[str, ...] = ()
    reference: bool = False
    footnote: bool = False


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _convert(item: Mapping[str, Any]) -> list[_Piece]:
    kind, page = item.get("type"), int(item["page_idx"]) + 1

    def text(key: str = "text") -> str:
        value = item.get(key)
        return value if isinstance(value, str) else ""

    def captions(*keys: str) -> list[_Piece]:
        return [_Piece("caption", c, page) for key in keys for c in _strings(item.get(key))]

    if kind == "text":
        level = item.get("text_level")
        if isinstance(level, int) and not isinstance(level, bool) and level >= 1:
            return [_Piece("heading", text(), page, level=min(level, 6))]
        return [_Piece("paragraph", text(), page)]
    if kind == "caption":
        return [_Piece("caption", text(), page)]
    if kind == "page_footnote":
        return [_Piece("paragraph", text(), page, footnote=True)]
    if kind == "ref_text":
        return [_Piece("paragraph", text(), page, reference=True)]
    if kind == "equation":
        return [_Piece("equation", text(), page)]
    if kind == "list":
        entries = tuple(_strings(item.get("list_items")))
        return [_Piece("list", "", page, items=entries, reference=item.get("sub_type") == "ref_text")]
    if kind == "image":
        return captions("image_caption", "image_footnote")
    if kind == "chart":
        return captions("chart_caption", "chart_footnote")
    if kind == "table":
        return captions("table_caption") + [_Piece("table", text("table_body"), page)] + captions("table_footnote")
    if kind == "code":
        return captions("code_caption") + [_Piece("code", text("code_body"), page)] + captions("code_footnote")
    if kind in _AUX_TYPES or kind == "index":
        return []
    return [_Piece("paragraph", text(), page)] if text() else []


def _finish(piece: _Piece, vocabulary, counter: list[int]) -> Block | None:
    if piece.type == "list":
        entries = []
        for entry in piece.items:
            cleaned, joined = dehyphenate(clean_text(entry, keep_lines=True), vocabulary)
            counter[0] += joined
            if cleaned := collapse_spaces(cleaned):
                entries.append(cleaned)
        return Block("list", "\n".join(entries), piece.page, items=tuple(entries)) if entries else None
    if piece.type in _FLOWING:
        cleaned, joined = dehyphenate(clean_text(piece.text, keep_lines=True), vocabulary)
        counter[0] += joined
        cleaned = collapse_spaces(cleaned)
    elif piece.type == "code":
        cleaned = clean_code(piece.text)
    else:
        cleaned = clean_text(piece.text, keep_lines=True)
    if not cleaned:
        return None
    return Block(piece.type, cleaned, piece.page, level=piece.level)


def build_document(
    items: Sequence[Mapping[str, Any]],
    *,
    doc_id: str,
    content_hash: str,
    parser_key: str = "",
    sidecar: Mapping[str, Any] | None = None,
    pdf: PdfInfo | None = None,
) -> Document:
    """Normalize `items` into blocks, split off the references, and merge metadata.

    `sidecar` is the normalized override mapping from `read_sidecar`; `pdf` is
    the PDF's own metadata when the original is a PDF.
    """
    pieces: list[_Piece] = []
    furniture: list[str] = []
    footnotes: list[str] = []
    labeled = indexes = 0
    for item in items:
        kind = item.get("type")
        if kind in _AUX_TYPES:
            labeled += 1
        elif kind == "index":
            indexes += 1
        if kind in _AUX_TYPES and item["page_idx"] <= 1:
            furniture.extend(clean_text(s) for s in _strings(item.get("text")))
        elif kind == "page_footnote" and item["page_idx"] <= 1:
            footnotes.extend(clean_text(s) for s in _strings(item.get("text")))
        pieces.extend(_convert(item))

    cleaned_texts = [clean_text(p.text, keep_lines=True) for p in pieces if p.type in _FLOWING]
    cleaned_texts += [clean_text(e, keep_lines=True) for p in pieces for e in p.items]
    vocabulary = word_vocabulary(cleaned_texts)
    dehyphenated = [0]
    blocks: list[Block] = []
    flags: list[bool] = []
    footnote_blocks: set[int] = set()
    for piece in pieces:
        block = _finish(piece, vocabulary, dehyphenated)
        if block is not None:
            if piece.footnote:
                footnote_blocks.add(len(blocks))
            blocks.append(block)
            flags.append(piece.reference)

    # Footnotes are content (notes, citations), never running headers or footers.
    running = find_running_text(blocks, exclude=footnote_blocks)
    footnote_ids = {id(blocks[i]) for i in footnote_blocks}
    removed_front = [b.text for i, b in enumerate(blocks) if i in running and b.page <= 2]
    kept = [(b, f) for i, (b, f) in enumerate(zip(blocks, flags)) if i not in running]
    body, refs = split_references([b for b, _ in kept], [f for _, f in kept])

    # Only the first few body blocks can state the document's own DOI; footnotes and later prose cite others.
    window = [b for b in body[:12] if id(b) not in footnote_ids]
    front_texts = [t for b in window if b.page == 1 for t in (b.items or (b.text,))]
    second_page_texts = [t for b in window if b.page == 2 for t in (b.items or (b.text,))]
    notices = [b.text for b in body[:12] if b.type == "paragraph" and len(b.text) <= 200 and _NOTICE.match(b.text)]
    year_texts = furniture + footnotes + removed_front + notices
    title, authors = mineru_title_authors(items)
    candidates = Candidates(
        sidecar=dict(sidecar or {}),
        mineru={"title": title, "authors": authors, "year": mineru_year(year_texts)},
        pdf={"title": pdf.title, "authors": pdf.authors, "doi": pdf.doi} if pdf else {},
        pdf_created={"year": pdf.created_year} if pdf else {},
        doi_pattern={"doi": select_doi(furniture + removed_front, front_texts, second_page_texts)},
    )
    page_count = max((int(item["page_idx"]) for item in items), default=-1) + 1
    return Document(
        doc_id=doc_id,
        content_hash=content_hash,
        metadata=merge_metadata(candidates),
        blocks=tuple(body),
        references=tuple(refs),
        page_count=page_count,
        parser_key=parser_key,
        report=BuildReport(dehyphenated[0], len(running), labeled, indexes, count_reference_like(body)),
    )
