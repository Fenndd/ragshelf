"""Metadata extraction (parsed content, PDF, DOI pattern, language) and sidecars.

Precedence per field is sidecar, then parsed content (`mineru`), then the PDF's
own metadata (`pdf`); the PDF's creation year is a weaker, separately labeled
source for the year (`pdf-created`). DOI is sidecar, PDF metadata, then the
text pattern (`doi-pattern`); language comes only from the sidecar. Without a
sidecar language value it is unknown. A sidecar replaces only the fields it
supplies, and as given.

Error messages name files and fields, never values: document text and metadata
are private.
"""

import json
import logging
import re
import unicodedata
import warnings
from collections.abc import Iterable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .model import Metadata
from .normalize import clean_text

MIN_YEAR, MAX_YEAR = 1500, 2100


class MetadataError(Exception):
    """A sidecar that cannot be used. The message never contains its content."""


# --- DOI ---------------------------------------------------------------------

_DOI = re.compile(r"""\b10\.\d{4,9}/[^\s"'<>\[\]{}|\\^`]+""", re.IGNORECASE)
_DOI_TRAILING = ".,;:!?)]}>'\"*\u2013\u2014"
# Where a second DOI starts ("10.1/a,10.2/b"), and a URL query string after the DOI.
_DOI_NEXT = re.compile(r"[,;](?=10\.\d{4,9}/)|\?")


def normalize_doi(candidate: str) -> str | None:
    """The canonical (lowercase) DOI found in `candidate`, or None.

    Trailing sentence punctuation is stripped; a closing parenthesis is kept
    only when it balances one inside the DOI.
    """
    match = _DOI.search(unicodedata.normalize("NFC", candidate))
    if not match:
        return None
    doi = _DOI_NEXT.split(match[0], maxsplit=1)[0]
    while doi and doi[-1] in _DOI_TRAILING:
        if doi[-1] == ")" and doi.count("(") >= doi.count(")"):
            break
        doi = doi[:-1]
    return doi.lower() if "/" in doi and len(doi.split("/", 1)[1]) >= 1 else None


def find_doi(texts: Iterable[str]) -> str | None:
    for text in texts:
        if doi := normalize_doi(text):
            return doi
    return None


# A DOI introduced by its label ("doi:", "DOI ", "https://doi.org/"), and a text that starts with one.
_LABELED_DOI = re.compile(r"(?:\bdoi\b|doi\.org)\W{0,8}(10\.\d{4,9}/\S+)", re.IGNORECASE)
_LEADING_LABEL = re.compile(r"^\W*(?:doi\b|https?://(?:dx\.)?doi\.org)", re.IGNORECASE)


def _all_dois(text: str) -> list[str]:
    found = (normalize_doi(m[0]) for m in _DOI.finditer(unicodedata.normalize("NFC", text)))
    return [d for d in found if d]


def _labeled_doi(text: str) -> str | None:
    match = _LABELED_DOI.search(unicodedata.normalize("NFC", text))
    return normalize_doi(match[1]) if match else None


def select_doi(furniture: Sequence[str], front: Sequence[str], second_page: Sequence[str] = ()) -> str | None:
    """The document's own DOI from its first pages, or None when it is not clear.

    `furniture` is parser-labeled header, footer, and aside text (and running
    text); a DOI there is the document's own. `front` is the first body texts of
    page 1 and `second_page` those of page 2. Body prose also cites other work,
    so a DOI there counts only when labeled ("doi:", "https://doi.org/"), and a
    text that starts with such a label wins. On page 2 only such a leading label
    counts. A bare, unlabeled DOI counts only when it is the single distinct
    DOI on page 1: with several, which one is the document's own cannot be told.
    """
    labeled = [d for t in furniture if (d := _labeled_doi(t))]
    if labeled:
        return labeled[0]
    if doi := find_doi(furniture):
        return doi
    leading = [d for t in (*front, *second_page) if _LEADING_LABEL.match(t) and (d := _labeled_doi(t))]
    if leading:
        return leading[0]
    labeled = [d for t in front if (d := _labeled_doi(t))]
    if labeled:
        return labeled[0]
    distinct = list(dict.fromkeys(d for t in front for d in _all_dois(t)))
    return distinct[0] if len(distinct) == 1 else None


# --- authors -----------------------------------------------------------------

_MATH = re.compile(r"\$[^$]*\$")
_MARKERS = re.compile(r"[*†‡§¶#∗⁎²³¹⁰-₟]|\^\{?[\d,*†]*\}?")
_PAREN = re.compile(r"\([^)]*\)")
# An address ends at a comma or semicolon (it separates authors), not only at whitespace.
_EMAIL = re.compile(r"<[^<>\s]+@[^<>\s]+>|[^\s,;<>()]+@[^\s,;<>()]+")
_SEPARATOR = re.compile(r"\s*;\s*|\s+(?:and|und|и)\s+|\s*&\s*|\s*,\s*(?:and|und|и)\s+")
_SUFFIXES = frozenset({"jr", "sr", "ii", "iii", "iv", "phd", "md", "msc", "dphil", "esq"})
_INITIALS = re.compile(r"^(?:[^\W\d_]\.\s*){1,3}$")
_INITIALS_ONLY = re.compile(r"(?:[^\W\d_]\.)+")


def _is_suffix(piece: str) -> bool:
    return piece.replace(".", "").strip().casefold() in _SUFFIXES


def _is_initials(piece: str) -> bool:
    piece = piece.strip()
    if _is_suffix(piece):
        return False
    return bool(_INITIALS.match(piece)) or (piece.isalpha() and (len(piece) == 1 or (piece.isupper() and len(piece) <= 3)))


def _top_level_commas(text: str) -> list[str]:
    """Split on commas outside brackets."""
    pieces, depth, current = [], 0, []
    for char in text:
        depth += char in "([{"
        depth -= char in ")]}" and depth > 0
        if char == "," and depth == 0:
            pieces.append("".join(current))
            current = []
        else:
            current.append(char)
    pieces.append("".join(current))
    return [re.sub(r"\s+", " ", p).strip() for p in pieces if p.strip()]


def _split_commas(chunk: str) -> tuple[list[str], bool]:
    """Comma-separated names; also whether the split is a guess.

    A suffix ("Jr.", "PhD") stays with the name before it. A surname followed
    by initials ("Smith, J., Jones, K.") or, in a pair, by a single given name
    ("Smith, John") is one "Last, First" author. Pieces of several words are
    separate authors. A lone single word or lone initials cannot be told from
    part of such a pair, so the result is flagged ambiguous.
    """
    merged: list[str] = []
    for piece in _top_level_commas(chunk):
        if merged and _is_suffix(piece):
            merged[-1] += f", {piece}"
        else:
            merged.append(piece)
    parts: list[str] = []
    ambiguous = False
    i = 0
    while i < len(merged):
        piece = merged[i]
        following = merged[i + 1] if i + 1 < len(merged) else None
        single = len(piece.split()) == 1
        if single and not _is_initials(piece) and following is not None and (
            _is_initials(following) or (len(merged) == 2 and len(following.split()) == 1)
        ):
            parts.append(f"{piece}, {following}")
            i += 2
            continue
        ambiguous = ambiguous or (len(merged) > 1 and (single or _is_initials(piece)))
        parts.append(piece)
        i += 1
    return parts, ambiguous


def split_authors(text: str) -> tuple[str, ...]:
    """Split an extracted author line into names, dropping affiliation marks and emails.

    ";" separates authors ("Last, First; Last, First"); otherwise "and", "&"
    and commas do, except that "Last, First" and "Last, F., Last, F." pairs and
    name suffixes stay with their author. Extracted lines are heuristic: names
    that are too short or too long are dropped. Sidecar values are not run
    through this (see `split_sidecar_authors`).
    """
    text = clean_text(text)
    text = _EMAIL.sub(" ", _PAREN.sub(" ", _MATH.sub(" ", text)))
    text = _MARKERS.sub(" ", text)
    text = re.sub(r"(?<=[^\W\d_])\d+(?:\s*,\s*\d+)*", " ", text)  # "Smith1,2" -> "Smith"
    text = re.sub(r"(?<![\w.])\d+(?![\w.])", " ", text)  # stray affiliation numbers
    parts: list[str] = []
    for chunk in _SEPARATOR.split(text):
        if ";" in text:
            parts.append(", ".join(p.strip() for p in chunk.split(",") if p.strip()))
        else:
            parts.extend(_split_commas(chunk)[0])
    names = []
    for part in parts:
        name = re.sub(r"\s+", " ", part).strip(" ,;:-–—")
        tail = (name.split() or [""])[-1]
        if name.endswith(".") and not _is_suffix(tail) and not _INITIALS_ONLY.fullmatch(tail):
            name = name.rstrip(".")  # "Smith." but not the initials in "Smith, J." or "Smith J.A." or "King, Jr."
        if (any(c.isalpha() for c in name) and 2 <= len(name) <= 80 and len(name.split()) <= 6 and name not in names):
            names.append(name)
    return tuple(names)


_SIDECAR_SEPARATOR = re.compile(r"\s+(?:and|und|и)\s+|\s*&\s*|\s*,\s*(?:and|und|и)\s+")


def split_sidecar_authors(text: str) -> tuple[str, ...]:
    """The authors of a sidecar string, verbatim.

    A sidecar is the user's own correction, so nothing is filtered or stripped:
    names are never dropped for length, and parentheses stay. A string is cut
    only at ";" (when present), otherwise at " and "/" und "/" и ", "&", and
    commas that clearly separate full names. A comma list that cannot be told
    from "Last, First" parts ("Plato, Aristotle") stays one verbatim author.
    """
    text = re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()
    if ";" in text:
        return tuple(p for p in (piece.strip() for piece in text.split(";")) if p)
    names: list[str] = []
    for chunk in _SIDECAR_SEPARATOR.split(text):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts, ambiguous = _split_commas(chunk)
        names.extend([chunk] if ambiguous else parts)
    return tuple(names)


# --- parsed content ------------------------------------------------------------

_SECTION_NAMES = (
    "abstract|contents|table of contents|introduction|keywords?|key words|references|"
    "аннотация|содержание|оглавление|введение|ключевые слова|abstrakt|obsah|úvod|uvod|zusammenfassung|inhalt|"
    "résumé|resume"
)
# A heading that is only a section name ("1. Introduction", "Abstract:"), or a label
# introducing text ("Abstract: we study ..."). A title that merely starts with the
# word ("Introduction to Algorithms", "Abstract Algebra") is a title.
# Generic section names are not a title either, but only when they are the whole heading (a book can
# be called "Methods: A Practical Guide").
_BARE_SECTIONS = (
    "background|methods?|methodology|materials and methods|results?|discussion|conclusions?|summary|"
    "preface|foreword|acknowledg(?:e)?ments?|einleitung|wst[e\u0119]p|"
    "\u0432\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u0435|"
    "\u043f\u0440\u0435\u0434\u0438\u0441\u043b\u043e\u0432\u0438\u0435|"
    "\u0437\u0430\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435"
)
_NOT_A_TITLE = re.compile(
    rf"^(?:{_SECTION_NAMES}|{_BARE_SECTIONS})\W*$|^(?:{_SECTION_NAMES})(?:\s*[:\u2013\u2014]|\s+-\s)",
    re.IGNORECASE,
)
_HEADING_NUMBER = re.compile(r"^\W*(?:\d+(?:\.\d+)*|[ivx]+(?=\W))\W*", re.IGNORECASE)
_NOT_AUTHORS = re.compile(
    r"^(abstract|keywords?|key words|received|accepted|published|doi\b|article|research article|"
    r"correspondence|e-?mail|copyright|©|http|www\.|in this|this |аннотация|ключевые|abstrakt|kľúčové|"
    r"schlüsselwörter|mots-clés|review|original|available online)",
    re.IGNORECASE,
)
# A line after the title that labels the document rather than naming its authors.
_BYLINE_STOP = re.compile(
    r"^(?:chapter|technical report|lecture notes|report|draft|version|volume|vol\.|edition|proceedings|"
    r"working paper|preprint|notes|kapitola|kapitel|\u0433\u043b\u0430\u0432\u0430)\b",
    re.IGNORECASE,
)
_AFFILIATION = re.compile(
    r"univers|department|dept\.|institut|school of|faculty|laborator|hospital|college|cent(?:er|re)\b|"
    r"academy|ministry|corporation|\binc\b|\bltd\b|gmbh|klinik|университет|институт|кафедр|факультет|"
    r"академи|лаборатор|univerzit|katedra|fakult|akademi|http|"
    # Czech/Slovak "ústav" is a word of its own: it must not match inside a given name (Gustav, Gustavo).
    # The accent-free "Ustav informatiky" counts only before a lowercase word, so the given name
    # "Ustav Patel" stays an author.
    r"\b\u00fastav(?:u|e|y|ov)?\b|\bustav(?:u|e|y|ov)?\s+(?-i:[a-z])",
    re.IGNORECASE,
)
# Contact details are not part of a name or an affiliation: "Jane Smith (jane@x.org)", "Jane Smith jane@x.org".
_CONTACT = re.compile(rf"\(\s*{_EMAIL.pattern}\s*\)|{_EMAIL.pattern}")
_CONNECTORS = frozenset({"and", "und", "и", "&", "de", "van", "von", "der", "den", "da", "di", "del", "la", "le", "bin", "ibn", "el"})
_YEAR_MARK = re.compile(
    r"(?P<kind>©|\(c\)|copyright|published|publication date|accepted|received|vydané|опубликовано|"
    r"veröffentlicht|publié)[^0-9]{0,40}?(?:\d{1,2}[\s./-]+(?:[^\W\d_]+[\s./-]+)?)?(?P<year>(?:1[5-9]|20)\d{2})\b",
    re.IGNORECASE,
)


def _looks_like_author_line(text: str) -> bool:
    text = text.strip()
    if (not text or len(text) > 400 or len(text.split()) > 60 or _NOT_AUTHORS.match(text)
            or _BYLINE_STOP.match(text) or _AFFILIATION.search(_CONTACT.sub(" ", text))):
        return False
    words = [w for name in split_authors(text) for w in name.split()]
    # Scripts without case (Chinese, Japanese, Arabic, Hebrew) have no capitals to test: a letter that
    # is not lowercase passes.
    capitalized = [w for w in words if (w[:1].isalpha() and not w[:1].islower()) or w.lower() in _CONNECTORS]
    return len(words) >= 2 and len(capitalized) >= 0.8 * len(words)


_AUX_TYPES = frozenset({"header", "footer", "page_number", "aside_text"})


def mineru_title_authors(items: Sequence[Mapping[str, Any]]) -> tuple[str | None, tuple[str, ...]]:
    """The first top-level heading on the first two pages, and the author line after it.

    Only the first such heading is considered: if it is "Abstract" or the like,
    the title is unknown rather than a later section heading.
    """
    for position, item in enumerate(items):
        text = item.get("text")
        if not (item.get("type") == "text" and item.get("text_level") == 1 and isinstance(text, str)
                and item.get("page_idx", 0) <= 1):
            continue
        title = clean_text(text)
        if (not title or not any(c.isalpha() for c in title)
                or _NOT_A_TITLE.match(_HEADING_NUMBER.sub("", title, count=1))):
            return None, ()
        candidates = 0
        for follow in items[position + 1:]:
            if follow.get("type") in _AUX_TYPES:
                continue
            if follow.get("type") != "text" or follow.get("text_level") or candidates == 4:
                break
            candidates += 1
            line = follow.get("text")
            if isinstance(line, str) and _looks_like_author_line(line):
                return title, split_authors(line)
        return title, ()
    return None, ()


def mineru_year(texts: Iterable[str]) -> int | None:
    """A publication year from copyright/publication notices; the clearest notice wins."""
    priority = {"published": 0, "©": 0, "(c)": 0, "copyright": 0, "publication date": 0,
                "accepted": 1, "received": 2}
    best: tuple[int, int] | None = None
    for text in texts:
        for match in _YEAR_MARK.finditer(text):
            rank = priority.get(match["kind"].casefold(), 0)
            year = int(match["year"])
            if MIN_YEAR <= year <= MAX_YEAR and (best is None or rank < best[0]):
                best = (rank, year)
    return best[1] if best else None


# --- language ------------------------------------------------------------------

# Language names a sidecar may use, mapped to their base codes.
_LANGUAGE_NAMES = {
    "english": "en", "russian": "ru", "slovak": "sk", "czech": "cs", "german": "de", "french": "fr",
    "spanish": "es", "italian": "it", "polish": "pl", "ukrainian": "uk", "portuguese": "pt",
    "dutch": "nl", "chinese": "zh", "japanese": "ja", "korean": "ko",
}


def normalize_language(value: str) -> str:
    """A language as its base code ("en_US" and "English" give "en"), for consistent sidecar metadata.

    A value that is neither a known name nor a code with an optional region is
    kept lowercased.
    """
    value = value.strip().casefold().replace("_", "-")
    if value in _LANGUAGE_NAMES:
        return _LANGUAGE_NAMES[value]
    base, _, region = value.partition("-")
    return base if 2 <= len(base) <= 3 and base.isalpha() and (not region or region.isalnum()) else value


# --- PDF metadata ----------------------------------------------------------------

# Tool and template placeholders that PDF generators write into the metadata.
_JUNK_TITLE = re.compile(
    r"^(?:microsoft word|untitled|document\d*$|powerpoint presentation|presentation\d*$|slide \d+|"
    r"layout \d+|adobe acrobat|stdin|arxiv:|book\d+$|doc\d+$)|\.(?:pdf|docx?|tex|indd|pptx?|xlsx?)$",
    re.IGNORECASE,
)
_JUNK_AUTHOR = frozenset({
    "", "unknown", "admin", "administrator", "user", "author", "windows user", "owner", "microsoft office user",
    "acrobat distiller", "pdfcreator", "pc", "default", "root", "none", "anonymous", "your name",
})
# PDF did not exist before 1993: an earlier creation date is a placeholder (the epoch default).
MIN_PDF_YEAR = 1993


@dataclass(frozen=True)
class PdfInfo:
    """What the PDF itself says. `created_year` is the year of the PDF's creation date: when the file was
    made, which may be long after publication, so it is a weaker source than the others."""

    title: str | None = None
    authors: tuple[str, ...] = ()
    created_year: int | None = None
    doi: str | None = None


@contextmanager
def _quiet_pypdf():
    """pypdf reports damage through `logging` and `warnings`; with no handler Python prints it to stderr."""
    logger = logging.getLogger("pypdf")
    saved = logger.level
    logger.setLevel(logging.CRITICAL + 1)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            yield
    finally:
        logger.setLevel(saved)


def read_pdf_metadata(path: Path) -> PdfInfo:
    """Read-only; a missing, encrypted, or corrupt PDF yields no information."""
    from pypdf import PdfReader  # a missing dependency must fail loudly, not look like a PDF without metadata

    values: dict[str, str] = {}
    try:
        with _quiet_pypdf(), path.open("rb") as stream:
            reader = PdfReader(stream, strict=False)
            if reader.is_encrypted and not reader.decrypt(""):
                return PdfInfo()
            info = reader.metadata
            for key in list(info or ()):
                value = info[key]
                if isinstance(value, str):
                    values[str(key).lstrip("/").casefold()] = value
    except Exception:
        return PdfInfo()
    title = clean_text(values.get("title", ""))
    if len(title) < 4 or _JUNK_TITLE.search(title) or "\\" in title or not any(c.isalpha() for c in title):
        title = ""
    author = clean_text(values.get("author", ""))
    authors = () if author.casefold() in _JUNK_AUTHOR else tuple(
        a for a in split_authors(author) if a.casefold() not in _JUNK_AUTHOR)
    created = None
    if match := re.match(r"^D:(\d{4})", values.get("creationdate", "")):
        created = int(match[1]) if MIN_PDF_YEAR <= int(match[1]) <= date.today().year else None
    return PdfInfo(title or None, authors, created, find_doi(values.values()))


# --- sidecar ------------------------------------------------------------------------

# The prototype's sidecars used `authors` and `year`; the others are the obvious fields of `Metadata`.
# There are deliberately no looser aliases for the year ("date", "published"): an unrelated key must not
# be read as a year (and fail the document).
_SIDECAR_KEYS = {
    "title": "title", "authors": "authors", "author": "authors", "year": "year", "doi": "doi",
    "language": "language", "lang": "language",
}


def sidecar_path(original: Path) -> Path:
    return original.with_name(original.name + ".metadata.json")


def read_sidecar(path: Path) -> dict[str, Any]:
    """The overrides a sidecar supplies, normalized; {} when no sidecar exists.

    Empty values do not override. A malformed file raises `MetadataError` naming
    the file (and the line/column of a syntax error), never its content.
    """
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeDecodeError) as exc:
        raise MetadataError(f"{path.name}: cannot be read as UTF-8 text ({type(exc).__name__})") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MetadataError(f"{path.name}: invalid JSON at line {exc.lineno}, column {exc.colno}") from None
    if not isinstance(data, dict):
        raise MetadataError(f"{path.name}: the top level must be a JSON object")
    # An alias ("author") loses to the exact key ("authors") when both appear.
    chosen: dict[str, tuple[int, Any]] = {}
    for key, value in data.items():
        canonical = _SIDECAR_KEYS.get(str(key).casefold())
        if canonical is not None:
            rank = 0 if str(key).casefold() == canonical else 1
            if canonical not in chosen or rank < chosen[canonical][0]:
                chosen[canonical] = (rank, value)
    supplied: dict[str, Any] = {}
    for name, (_, value) in chosen.items():
        if value is None or value == [] or (isinstance(value, str) and not value.strip()):
            continue
        parsed = _sidecar_value(path, name, value)
        if parsed not in (None, "", ()):
            supplied[name] = parsed
    return supplied


def _sidecar_value(path: Path, name: str, value: Any) -> Any:
    def bad(reason: str) -> MetadataError:
        return MetadataError(f"{path.name}: field '{name}' {reason}")

    if name in {"title", "language", "doi"}:
        if not isinstance(value, str):
            raise bad("must be a string")
        value = re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()
        if name == "doi":
            doi = normalize_doi(value)
            if doi is None:
                raise bad("is not a valid DOI")
            return doi
        return normalize_language(value) if name == "language" else value
    if name == "authors":
        if isinstance(value, str):
            names = split_sidecar_authors(value)
            if not names:
                raise bad("has no author name")
            return names
        if isinstance(value, list) and all(isinstance(a, str) for a in value):
            return tuple(re.sub(r"\s+", " ", unicodedata.normalize("NFC", a)).strip() for a in value if a.strip())
        raise bad("must be a string or a list of strings")
    if isinstance(value, bool):
        raise bad("is not a valid year")
    if isinstance(value, int):
        year = value
    elif isinstance(value, str) and (match := re.search(r"(?<!\d)(\d{4})(?!\d)", value)):
        year = int(match[1])
    else:
        raise bad("is not a valid year")
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise bad("is not a valid year")
    return year


# --- merging --------------------------------------------------------------------------

@dataclass
class Candidates:
    """Values per source, in decreasing precedence within each field."""

    sidecar: dict[str, Any] = field(default_factory=dict)
    mineru: dict[str, Any] = field(default_factory=dict)
    pdf: dict[str, Any] = field(default_factory=dict)
    pdf_created: dict[str, Any] = field(default_factory=dict)
    doi_pattern: dict[str, Any] = field(default_factory=dict)


_PRECEDENCE = {
    "title": ("sidecar", "mineru", "pdf"),
    "authors": ("sidecar", "mineru", "pdf"),
    "year": ("sidecar", "mineru", "pdf_created"),
    "doi": ("sidecar", "pdf", "doi_pattern"),
    "language": ("sidecar",),
}


def merge_metadata(candidates: Candidates) -> Metadata:
    values: dict[str, Any] = {}
    sources: list[tuple[str, str]] = []
    for name, order in _PRECEDENCE.items():
        for source in order:
            value = getattr(candidates, source).get(name)
            if value not in (None, "", ()):
                values[name] = value
                sources.append((name, source.replace("_", "-")))
                break
    return Metadata(sources=tuple(sources), **values)
