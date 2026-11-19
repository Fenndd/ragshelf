"""Text normalization: Unicode form, hyphenation across line breaks, running text."""

import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Collection, Iterable

from .model import Block

# ASCII hyphen-minus, U+2010 hyphen, U+2011 non-breaking hyphen.
_HYPHEN_CHARS = "-‐‑"
_HYPHENS = r"\-‐‑"
_LETTER = r"[^\W\d_]"
_SOFT_HYPHEN = "­"
# BOM, zero-width space, word joiner. ZWNJ/ZWJ are spelling in Persian, Indic scripts, and
# emoji sequences, so they go only between Latin or Cyrillic letters (see `_STRAY_JOINER`).
_INVISIBLE = dict.fromkeys(map(ord, "\ufeff\u200b\u2060"))
_STRAY_JOINER = re.compile("(?<=[A-Za-z\u00c0-\u024f\u0400-\u04ff])[\u200c\u200d]"
                           "(?=[A-Za-z\u00c0-\u024f\u0400-\u04ff])")
# C0 and C1 controls except tab, line feed, and carriage return (which is normalized later).
_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
# A soft hyphen at a line end marks a break inside a word: the word is whole again.
_SOFT_HYPHEN_BREAK = re.compile("\u00ad[ \t]*(?:\r\n|\r|\n)[ \t]*")

# A word fragment ends a line with a hyphen and the next line continues it.
# The lookbehind makes the fragment start at a word boundary, so the inner
# pieces of "state-of-the-\nart" are never taken for a hyphenated word.
_LINE_BREAK_HYPHEN = re.compile(
    rf"(?<![\w{_HYPHENS}])(?P<left>[\w{_HYPHENS}]*?\w)[{_HYPHENS}][ \t]*\n[ \t]*(?P<right>\w+)"
)
_WORD = re.compile(rf"{_LETTER}+(?:[{_HYPHENS}]{_LETTER}+)*")

# Prefixes and suffixes that form genuine hyphenated compounds, so a hyphen
# before a line break after them is kept ("well-\nknown" is "well-known").
_COMPOUND_PREFIXES = frozenset(
    {"self", "well", "non", "anti", "quasi", "semi", "cross", "half", "ex", "all", "ill", "so"}
)
_COMPOUND_SUFFIXES = frozenset(
    {"based", "related", "specific", "dependent", "induced", "mediated", "driven", "oriented",
     "free", "wide", "thirds", "fourths", "fifths",
     # Russian particles written with a hyphen.
     "то", "либо", "нибудь", "таки", "ка"}
)
# After a hyphen at a line end these start a new word ("short-" / "and long-term"): a
# suspended hyphen, never the first half of one word.
_FUNCTION_WORDS = frozenset(
    {"and", "or", "nor", "but", "to", "of", "the", "a", "an", "at", "by", "as", "for", "from",
     "with", "vs", "versus", "и", "или"}
)
# Particles that make a compound with the word before ("built-in", "plug-in", "set-up"): never a
# suspended hyphen and never one word.
_PARTICLES = frozenset({"in", "on", "up", "out", "off", "down"})
# A hyphen inside a URL, e-mail address, or DOI may belong to it: the chunk before the break starts like
# an address, or the word after the break is followed by "@", "/", or a dotted domain tail.
_ADDRESS = re.compile(r"[/@]|^10\.\d{4,}|^www\.|^https?:", re.IGNORECASE)
_ADDRESS_TAIL = re.compile(r"[@/]|\.[A-Za-z]{2,}")
_LOOK_BACK = 256
# Opposition and range pairs written "left-right", "input-output": both halves are whole words, so the
# hyphen is part of the compound and is kept.
_PAIR_WORDS = frozenset(
    {"left", "right", "up", "down", "north", "south", "east", "west", "top", "bottom", "front", "back",
     "high", "low", "in", "out", "on", "off", "input", "output", "read", "write", "pre", "post",
     "yes", "no", "true", "false", "male", "female", "day", "night", "start", "end", "first", "last",
     "long", "short", "hot", "cold", "fast", "slow", "big", "small"}
)


def clean_text(text: str, *, keep_lines: bool = False) -> str:
    """NFC, no invisible characters, soft hyphens, or control characters, normalized spaces.

    A soft hyphen right before a line break joins the two halves of the word.
    Line breaks survive when `keep_lines` is true (tables, equations, and text
    that still awaits dehyphenation); otherwise all whitespace collapses.
    """
    text = _SOFT_HYPHEN_BREAK.sub("", unicodedata.normalize("NFC", text)).translate(_INVISIBLE)
    text = _CONTROL.sub("", _STRAY_JOINER.sub("", text.replace(_SOFT_HYPHEN, "")))
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    if keep_lines:
        return "\n".join(line.rstrip() for line in text.split("\n")).strip("\n")
    return collapse_spaces(text)


def clean_code(text: str) -> str:
    """Code keeps its characters: NFC, line endings, and trailing spaces only.

    Invisible characters (a zero-width joiner in a string literal) and control
    characters are not removed, so literals survive.
    """
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip("\n")


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def word_vocabulary(texts: Iterable[str]) -> tuple[Counter[str], Counter[str]]:
    """Count plain and hyphenated words that occur unbroken inside lines."""
    plain: Counter[str] = Counter()
    hyphenated: Counter[str] = Counter()
    for text in texts:
        for word in _WORD.findall(text.casefold()):
            if any(h in word for h in _HYPHEN_CHARS):
                hyphenated[word.replace("‐", "-").replace("‑", "-")] += 1
            else:
                plain[word] += 1
    return plain, hyphenated


def dehyphenate(text: str, vocabulary: tuple[Counter[str], Counter[str]]) -> tuple[str, int]:
    """Repair words split across line breaks; return the text and the join count.

    A break "left-" + newline + "right" is joined into one word only when
    "right" starts in lowercase and nothing says the hyphen belongs to the word:

    1. The left token is already compound, ends in a digit, or "right" starts
       in uppercase ("Smith-\\nJones"): the hyphen stays, the newline goes.
    2. The document itself spells the joined word unbroken elsewhere: join.
       It spells only the hyphenated form elsewhere: keep the hyphen.
    3. Without such evidence, a known compound prefix or suffix ("well-",
       "-based") keeps the hyphen.
    4. Otherwise the hyphen is typesetting: join.

    Cases that are never joined: a function word after the break ("short-\\nand
    long-term" stays "short- and long-term", but "end-\\nto-end" is one
    compound), a particle ("built-\\nin"), a one-letter or all-capitals left
    part ("x-ray", "DNA-binding"), and a fragment inside a URL, e-mail address,
    or DOI (the hyphen stays; it may be part of the address). Soft hyphens at a
    line end were already joined by `clean_text`.

    Newlines without a hyphen are left to whitespace collapsing.
    """
    plain, hyphenated = vocabulary
    joined = 0

    def repair(match: re.Match[str]) -> str:
        nonlocal joined
        left, right = match["left"], match["right"]
        if any(h in left for h in _HYPHEN_CHARS) or not left[-1].isalpha() or not right[0].islower():
            return f"{left}-{right}"
        # A one-letter left part ("x-ray", "t-test", "e-mail"), a one-letter continuation, or an
        # acronym ("DNA-binding") is a compound: typesetters do not break after one letter.
        if len(left) == 1 or len(right) < 2 or left.isupper():
            return f"{left}-{right}"
        text = match.string
        start = match.start("left")
        window = max(0, start - _LOOK_BACK)  # bounded: a rfind to offset 0 makes long paragraphs quadratic
        cut = max(text.rfind(c, window, start) for c in " \t\n")
        chunk_start = cut + 1 if cut >= 0 else window
        if _ADDRESS.search(text[chunk_start:match.end("left")]) or _ADDRESS_TAIL.match(text, match.end("right")):
            return f"{left}-{right}"
        low_left, low_right = left.casefold(), right.casefold()
        if low_right in _FUNCTION_WORDS:
            # "end-\nto-end" is one compound; "short-\nand long-term" is a suspended hyphen.
            if text[match.end():match.end() + 1] and text[match.end()] in _HYPHEN_CHARS:
                return f"{left}-{right}"
            return f"{left}- {right}"
        if low_right in _PARTICLES or (low_left in _PAIR_WORDS and low_right in _PAIR_WORDS):
            return f"{left}-{right}"
        together, apart = plain[low_left + low_right], hyphenated[f"{low_left}-{low_right}"]
        if together != apart:
            keep = apart > together
        else:
            keep = low_left in _COMPOUND_PREFIXES or low_right in _COMPOUND_SUFFIXES
        if keep:
            return f"{left}-{right}"
        joined += 1
        return left + right

    return _LINE_BREAK_HYPHEN.sub(repair, text), joined


# A number that tracks the page: "12", "page 3", "p. 3 of 10", "12-14". The digits are masked to 0.
_PAGE_LIKE = re.compile(
    r"^(?:(?:page|pages|p|pp|str|\u0441\u0442\u0440|\u0441|s|seite)\.?\s*)?0(?:\s*[-\u2013\u2014]\s*0)?"
    r"(?:\s*(?:of|/|\u0438\u0437|von)\s*0)?$"
)
# A page number in Roman numerals ("iv", "page xii"): no digits to mask, so the whole key is one token.
_ROMAN_PAGE = re.compile(r"^(?:(?:page|p)\.?\s*)?(?=[ivxlc])c{0,3}(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})$")


def _running_key(text: str) -> str:
    """The text compared across pages: casefolded, with page numbers masked.

    Digits are masked only when the whole paragraph is page-number-like (a bare
    number, "page N", "N of M", a range of pages), and a Roman numeral page
    number becomes one token. Everything else keeps its digits, so a numbered
    label ("Example 1."), a footnote ("1 Ibid."), a caption ("Fig. 2"), or a
    short paragraph that differs in a number does not look repeated.
    """
    strip = " \t.,:;|-\u2013\u2014_*[]()"
    text = re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).casefold()).strip(strip)
    masked = re.sub(r"\s+", " ", re.sub(r"\d+", "0", text)).strip(strip)
    if masked != text and _PAGE_LIKE.match(masked):
        return masked
    if _ROMAN_PAGE.match(text):
        return "<roman>"
    return text


def find_running_text(
    blocks: list[Block], *, edge: int = 2, max_chars: int = 120, min_pages: int = 6,
    exclude: Collection[int] = frozenset(),
) -> set[int]:
    """Indexes of paragraphs that repeat at page edges on many distinct pages.

    Only paragraphs among the first or last `edge` blocks of a page count, so
    headings, captions, tables, and a section title repeated inside one page
    are never candidates; neither are blocks in `exclude` (footnotes) or a
    paragraph directly under a table (a table note or source line). A repeated
    key is running text when it appears on at least a quarter of the pages (and
    three), or fills at least 80% of its own page span over five or more pages
    (chapter headers in long books). Documents of fewer than `min_pages` pages
    are left alone: too little evidence to tell a header from a refrain.
    """
    by_page: dict[int, list[int]] = defaultdict(list)
    for index, block in enumerate(blocks):
        by_page[block.page].append(index)
    if len(by_page) < min_pages:
        return set()
    needed = max(3, math.ceil(0.25 * len(by_page)))
    pages_of: dict[str, set[int]] = defaultdict(set)
    members: dict[str, list[int]] = defaultdict(list)
    for page, indexes in by_page.items():
        for index in {*indexes[:edge], *indexes[-edge:]}:
            block = blocks[index]
            if (block.type == "paragraph" and len(block.text) <= max_chars and index not in exclude
                    and not (index > 0 and blocks[index - 1].type == "table")):
                key = _running_key(block.text)
                if key:
                    pages_of[key].add(page)
                    members[key].append(index)
    removed: set[int] = set()
    for key, pages in pages_of.items():
        span = max(pages) - min(pages) + 1
        if len(pages) >= needed or (len(pages) >= 5 and len(pages) / span >= 0.8):
            removed.update(members[key])
    return removed
