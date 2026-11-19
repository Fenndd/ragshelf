"""Immutable document model: ordered typed blocks, references, and metadata."""

from dataclasses import dataclass
from typing import Literal

BlockType = Literal["heading", "paragraph", "list", "table", "equation", "code", "caption"]
BLOCK_TYPES: tuple[str, ...] = ("heading", "paragraph", "list", "table", "equation", "code", "caption")

METADATA_FIELDS: tuple[str, ...] = ("title", "authors", "year", "doi", "language")
# Where a metadata value came from. "mineru" means the parsed content in the
# cache bundle, whichever parser produced it (also UTF-8 text passthrough).
# "pdf-created" is the year of the PDF's creation date: when the file was made, not necessarily when the
# work was published, so it is labeled apart from the other sources.
SOURCES: tuple[str, ...] = ("sidecar", "mineru", "pdf", "pdf-created", "doi-pattern")
NO_SOURCE = "none"


@dataclass(frozen=True, slots=True)
class Block:
    """One structural unit of a document.

    `page` is the 1-based page number (`page_idx + 1`); text and Markdown
    inputs have a single logical page 1. `level` is set for headings only.
    `items` holds the entries of a list block (`text` joins them with newlines).
    """

    type: BlockType
    text: str
    page: int
    level: int | None = None
    items: tuple[str, ...] = ()

    def __post_init__(self):
        if self.type not in BLOCK_TYPES:
            raise ValueError(f"Unknown block type: {self.type!r}")
        if self.page < 1:
            raise ValueError("Block page numbers start at 1")
        if (self.type == "heading") != (self.level is not None):
            raise ValueError("Exactly the headings carry a level")
        if self.level is not None and not 1 <= self.level <= 6:
            raise ValueError("Heading level must be between 1 and 6")


@dataclass(frozen=True, slots=True)
class Metadata:
    """Bibliographic metadata; `sources` records the origin of each non-empty field."""

    title: str | None = None
    authors: tuple[str, ...] = ()
    year: int | None = None
    doi: str | None = None
    # Supplied by the sidecar only; absent values stay unknown.
    language: str | None = None
    sources: tuple[tuple[str, str], ...] = ()

    def source_of(self, field: str) -> str:
        """The origin of `field`, or "none" when the field is empty."""
        return dict(self.sources).get(field, NO_SOURCE)


@dataclass(frozen=True, slots=True)
class BuildReport:
    """Content-free counters describing what normalization did."""

    dehyphenated: int = 0
    running_text_removed: int = 0
    labeled_boilerplate_removed: int = 0
    index_removed: int = 0
    # Body entries that read like references (numbered and citation-shaped): a leakage measure for `inspect`.
    reference_like_in_body: int = 0


@dataclass(frozen=True, slots=True)
class Document:
    """A normalized document. `references` is kept apart from the body `blocks`."""

    doc_id: str
    content_hash: str
    metadata: Metadata
    blocks: tuple[Block, ...]
    references: tuple[Block, ...] = ()
    page_count: int = 0
    parser_key: str = ""
    report: BuildReport = BuildReport()

    @property
    def outline(self) -> tuple[Block, ...]:
        """The body headings in reading order."""
        return tuple(block for block in self.blocks if block.type == "heading")
