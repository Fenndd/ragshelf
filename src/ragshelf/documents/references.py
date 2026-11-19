"""Find the reference list by its heading and keep it apart from the body."""

import re
import unicodedata

from .model import Block

# Headings that name a reference list, lowercase and without accents (the
# comparison strips accents from both sides). Only an exact match counts, so
# "Literature Review" or "A Review of the Literature" are ordinary headings.
_UNAMBIGUOUS = frozenset({
    # en
    "references", "reference list", "list of references", "references cited", "works cited",
    "literature cited", "cited literature", "bibliography", "selected bibliography",
    "references and notes", "notes and references", "selected references",
    "cited references", "references and further reading", "bibliographical references",
    "references and bibliography", "bibliography and references", "sources cited", "works consulted",
    # ru
    "список литературы", "список использованной литературы", "список источников",
    "список использованных источников", "библиография", "использованная литература",
    "литература и источники", "библиографический список", "список источников и литературы",
    # uk, bg
    "список літератури", "список використаної літератури", "список використаних джерел", "бібліографія",
    "използвана литература",
    # sk, cs
    "zoznam literatury", "zoznam pouzitej literatury", "pouzita literatura", "referencie",
    "bibliografia", "zoznam bibliografickych odkazov", "zoznam zdrojov", "seznam literatury",
    "seznam pouzite literatury", "pouzite zdroje", "zoznam pouzitych zdrojov", "pouzite zdroje a literatura",
    # de
    "literaturverzeichnis", "quellenverzeichnis", "bibliographie", "referenzen", "literaturangaben",
    # fr
    "references bibliographiques", "bibliographie", "liste des references", "ouvrages cites",
    # es, it, pl
    "referencias", "bibliografia", "referencias bibliograficas", "riferimenti", "riferimenti bibliografici",
    "pismiennictwo",
    # pt, nl, hu, tr, ro, el, sv, da, no
    "obras citadas", "bibliografia consultada", "referenties", "literatuurlijst", "bronnenlijst", "bibliografie",
    "irodalomjegyzek", "felhasznalt irodalom", "hivatkozasok", "kaynakca", "referinte bibliografice",
    "βιβλιογραφια", "referenser", "kallforteckning", "referanser", "litteraturliste", "kildeliste",
    # zh, ja, ko
    "参考文献", "参考资料", "参考书目", "参考書目", "主要参考文献", "引用文献", "참고문헌", "참고 문헌",
})
# A bare word that is often a literature-review chapter rather than the list.
# It names the list only when the entries that follow look like references.
_AMBIGUOUS = frozenset({
    "literature", "literatura", "литература", "literatur", "literatura", "sources", "quellen",
    "источники", "zdroje", "sources bibliographiques",
    "література", "джерела", "literatuur", "bronnen", "irodalom", "kaynaklar", "litteratur", "lahteet",
    "kirjallisuus", "fontes", "reference",
})
# Headings that start material after the list, whatever their level.
_TERMINATORS = re.compile(
    r"^(appendix|appendices|annex|annexes|supplement|supplementary|supporting information|"
    r"acknowledg|acknowledgement|acknowledgment|author contributions|funding|"
    r"приложение|приложения|благодарност|"
    r"priloha|prilohy|podakovanie|dakujeme|"
    r"anhang|anlage|danksagung|"
    r"annexe|remerciements|apendice|anexo|"
    # Material that follows a list but is not part of it, whatever its level.
    r"about the author|author biograph|biograph|notes on contributors|index|glossary|"
    r"\u043e\u0431 \u0430\u0432\u0442\u043e\u0440\u0430\u0445|\u0441\u0432\u0435\u0434\u0435\u043d\u0438\u044f \u043e\u0431 \u0430\u0432\u0442\u043e\u0440\u0430\u0445|"
    r"uber die autor|\u00fcber die autor)"
)
# Blocks that cannot be reference entries: a list ends where a figure, table, formula, or code begins.
_NON_ENTRY = frozenset({"table", "equation", "code", "caption"})
_NUMBER = r"(?:(?:\d+(?:\.\d+)*|[ivxlc]+)(?:\s*[.):\-–—、]\s*|\s+)|[一二三四五六七八九十]+\s*[、.]\s*)"
_NUMBERING = re.compile(
    rf"^(?:(?:chapter|section|kapitola|kapitel|chapitre|glava|глава|раздел|часть)\s+{_NUMBER}"
    rf"|第\s*[\d一二三四五六七八九十]+\s*[章节節部分]\s*(?:{_NUMBER})?|{_NUMBER})",
)
_YEAR = re.compile(r"\b(?:1[5-9]|20)\d{2}\b")
_ENTRY_NUMBER = re.compile(r"^\s*(?:\[\d+\]|\d+[.)])\s")
# What a citation has that ordinary prose with a date does not.
_DOI_OR_URL = re.compile(r"\bdoi\b|\b10\.\d{4,9}/|https?://|www\.", re.IGNORECASE)
_AUTHOR_INITIALS = re.compile(
    r"[^\W\d_]{2,},?\s+(?:[^\W\d_]\.\s*){1,3}|\b(?:[^\W\d_]\.\s*){1,3}[^\W\d_]{2,}"
)
_CITATION_MARK = re.compile(r"\bet al\b|\bи др\.|\ba kol\.|^\s*\[\d+\]|\[[JMDCRSNPGZ]\]")
# What only a bibliographic entry has, not a sentence that mentions a year and a person. Used where the
# heading alone is no evidence (a bare "Literature" chapter): numbering, volume/issue or page ranges,
# a source separator, or a leading "Surname, I." / "I. Surname," that starts the entry.
_NAME = r"[^\W\d_][^\W\d_'’-]+(?:[-'’][^\W\d_]+)*"
_INITIALS = r"(?:[^\W\d_]\.\s*){1,3}"
_BIBLIOGRAPHIC_MARK = re.compile(
    r"\bpp?\.\s*\d|\b[сСSs]\.\s*\d|\bvol\.\s*\d|\bт\.\s*\d|\b\d+\s*\(\d+\)|\b\d+\s*:\s*\d+|\s//\s"
)
_ENTRY_START = re.compile(
    rf"^\s*(?:{_NAME}\s*,\s*{_INITIALS}|{_NAME}\s+{_INITIALS}(?=[,.(\[\d])"
    rf"|{_INITIALS}{_NAME}\s*[,.])"
)


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(c for c in decomposed if not unicodedata.combining(c)))


_UNAMBIGUOUS = frozenset(map(_strip_accents, _UNAMBIGUOUS))
_AMBIGUOUS = frozenset(map(_strip_accents, _AMBIGUOUS))


def heading_key(text: str) -> str:
    """Casefolded, accent-free heading text without numbering or edge punctuation."""
    key = _strip_accents(unicodedata.normalize("NFC", text).casefold())
    key = re.sub(r"\s+", " ", key).strip(" \t.:;*#_()[]-–—")
    # Numbering is only a prefix: "7. references", "vii references", "chapter 9: references".
    stripped = _NUMBERING.sub("", key, count=1).strip(" \t.:;*#_()[]-–—")
    return stripped or key


def is_reference_heading(text: str) -> bool:
    key = heading_key(text)
    return key in _UNAMBIGUOUS or key in _AMBIGUOUS


def _is_ambiguous(text: str) -> bool:
    return heading_key(text) in _AMBIGUOUS


def _is_terminator(text: str) -> bool:
    return bool(_TERMINATORS.match(heading_key(text)))


def _entries(blocks: list[Block]) -> list[str]:
    return [item for block in blocks for item in (block.items if block.type == "list" else (block.text,))
            if block.type in {"paragraph", "list"} and item]


def _citation_shaped(entry: str, strict: bool = False) -> bool:
    """Short, with a year and either a DOI/URL, author initials, "et al.", or a [n] mark.

    A year alone is not enough ("In 1850 the author published a novel" is
    prose), and neither is a link alone (a data-availability statement).
    `strict` is for a heading that is often a chapter title ("Literature"):
    "a year and an author's initials somewhere in the sentence" is also
    literary history ("In 1837 A. S. Pushkin wrote a poem"), so the entry must
    carry something prose lacks: a DOI/URL, "et al.", a numbered or [n] lead-in,
    a volume/page pattern, or the author in the entry position ("Smith, J.").
    """
    if len(entry) > 450 or not _YEAR.search(entry):
        return False
    if not strict:
        return bool(_DOI_OR_URL.search(entry) or _AUTHOR_INITIALS.search(entry) or _CITATION_MARK.search(entry))
    return bool(_DOI_OR_URL.search(entry) or _CITATION_MARK.search(entry) or _ENTRY_NUMBER.match(entry)
                or _BIBLIOGRAPHIC_MARK.search(entry) or _ENTRY_START.match(entry))


def _share_citation_shaped(entries: list[str], strict: bool = False) -> bool:
    """At least two thirds of the entries are citation-shaped (and there is at least one)."""
    return bool(entries) and sum(_citation_shaped(e, strict) for e in entries) * 3 >= len(entries) * 2


def _block_citation_shaped(block: Block, flagged: bool, strict: bool = False) -> bool:
    return flagged or _share_citation_shaped(_entries([block]), strict)


def _citation_run_end(blocks: list[Block], flags: list[bool], start: int, strict: bool = False) -> int:
    """End of the run of citation-shaped paragraphs/lists beginning at `start` (`start` if there is none).

    One entry that does not look like a citation may sit inside the run, but
    two in a row end it, and so does any block that is not a paragraph or a
    list. The run ends after its last citation-shaped block.
    """
    last = end = start
    while end < len(blocks) and blocks[end].type in {"paragraph", "list"}:
        if _block_citation_shaped(blocks[end], flags[end], strict):
            last = end + 1
        elif end - last >= 1:
            break
        end += 1
    return last


def _trailing_unlabeled_list(blocks: list[Block], in_references: list[bool]) -> int | None:
    """Start of an unheaded reference list at the end of the document, or None.

    Language-independent fallback for a heading outside the keyword set: the
    paragraphs and lists after the last heading (or after the last separated
    section) are references when there are at least three entries and four in
    five are citation-shaped. The heading just before them, if any, goes with
    them. Something must remain in the body.
    """
    k = len(blocks)
    while k > 0 and not in_references[k - 1] and blocks[k - 1].type in {"paragraph", "list"}:
        k -= 1
    entries = _entries(blocks[k:])
    if len(entries) < 3 or sum(_citation_shaped(e) for e in entries) * 5 < len(entries) * 4:
        return None
    start = k - 1 if k > 0 and blocks[k - 1].type == "heading" and not in_references[k - 1] else k
    return start if start > 0 else None


def count_reference_like(blocks: list[Block]) -> int:
    """Entries of the given (body) blocks that look like references: numbered and citation-shaped.

    A content-free measure of what the separation missed; a body with a few numbered, cited
    sentences is normal, hundreds on the pages of the reference list are not.
    """
    return sum(bool(_ENTRY_NUMBER.match(e)) and _citation_shaped(e)
               for b in blocks for e in _entries([b]))


def _candidate_heading(block: Block) -> bool:
    # A bare keyword in a paragraph (a heading the parser did not label) counts
    # only when it is short; real paragraphs never equal a heading phrase.
    return block.type == "heading" or (block.type == "paragraph" and len(block.text) <= 60)


def _run_after(blocks: list[Block], heading: int) -> int:
    """End of the paragraphs and lists that directly follow the heading at `heading`."""
    end = heading + 1
    while end < len(blocks) and blocks[end].type in {"paragraph", "list"}:
        end += 1
    return end


def _run_is_list(blocks: list[Block], flags: list[bool], lo: int, hi: int, strict: bool = False) -> bool:
    """Whether the blocks `lo:hi` are mostly reference entries: two thirds citation-shaped, entries the
    parser labeled as reference text counting as such. Two entries at least, or a labeled one."""
    total = shaped = 0
    labeled = False
    for k in range(lo, hi):
        entries = _entries([blocks[k]])
        total += len(entries)
        if flags[k] and entries:
            labeled = True
            shaped += len(entries)
        else:
            shaped += sum(_citation_shaped(e, strict) for e in entries)
    return total > 0 and (total >= 2 or labeled) and shaped * 3 >= total * 2


def _section_end(blocks: list[Block], flags: list[bool], i: int, level: int) -> int:
    """End of the reference section that the heading at `i` opens: the next heading at a higher level
    (or an appendix-like one), the first block that cannot be an entry, or a same-level heading that is
    not itself a sub-heading of the list.

    A heading at the same level may be a sub-heading ("Journal articles", "Books", "Web sources")
    when the document uses one heading level throughout, as MinerU's output often does. It
    continues the list when the entries right after it are mostly citations.
    """
    end = i + 1
    while end < len(blocks):
        nxt = blocks[end]
        if nxt.type in _NON_ENTRY:
            break
        if nxt.type == "heading":
            if _is_terminator(nxt.text):
                break
            if nxt.level <= level and not is_reference_heading(nxt.text) and not (
                    nxt.level == level and _run_is_list(blocks, flags, end + 1, _run_after(blocks, end))):
                break
        end += 1
    return end


def _numbered_entry(entry: str) -> bool:
    """"12. Ibid., 45." or "[3] Smith ...": numbered, and a note rather than a numbered section title.

    Notes run from a few words ("Ibid., 45.") to several lines. A short numbered line that does not end
    like a note ("5. Conclusions") is a title.
    """
    if not _ENTRY_NUMBER.match(entry) or len(entry) > 1500:
        return False
    return len(entry) >= 25 or (len(entry) >= 8 and entry.rstrip()[-1] in ".)0123456789")


def _entry_like(block: Block, flagged: bool) -> bool:
    """A paragraph or list that sits well in a reference or endnote list: parser-labeled, mostly
    citation-shaped, or mostly numbered ("12. ...", "[12] ...") entries of reasonable length."""
    if block.type not in {"paragraph", "list"}:
        return False
    if flagged:
        return True
    entries = _entries([block])
    if not entries:
        return False
    numbered = sum(_numbered_entry(e) for e in entries)
    return numbered * 3 >= len(entries) * 2 or _share_citation_shaped(entries)


def _heading_bridges(blocks: list[Block], flags: list[bool], like: list[bool], in_references: list[bool],
                     heading: int) -> bool:
    """Whether the heading at `heading`, right after reference entries, sits inside the list.

    True when the entries after it are mostly citations (`_run_is_list`), or when they are all
    entry-like and lead into more of the list: a parser-labeled block in the run, or a heading
    that belongs to the list right after it. A heading followed by plain numbered paragraphs
    alone (a numbered exercise list under the next chapter) is not.
    """
    end = _run_after(blocks, heading)
    if _run_is_list(blocks, flags, heading + 1, end):
        return True
    if end == heading + 1 or not all(like[heading + 1:end]):
        return False
    return any(flags[heading + 1:end]) or (end < len(blocks) and in_references[end])


def _extend_parser_labeled(blocks: list[Block], flags: list[bool], in_references: list[bool]) -> None:
    """Pull the entries around parser-labeled reference text into the list.

    The parser labels some entries and not others: a list can be interleaved with
    plain numbered or citation-shaped paragraphs, and with sub-headings of its own
    ("Journal articles", chapter names of a note section). Going back and forth from each
    labeled block, the neighbouring entry-like paragraphs and lists join the references;
    after a labeled block a heading joins too when entries follow it, so the list does not
    stop at the first heading. An appendix-like heading and any table, figure, formula, or code
    block end the run. Linear: a scan never revisits blocks that an earlier labeled block covered.
    """
    n = len(blocks)
    like = [_entry_like(b, f) for b, f in zip(blocks, flags)]
    forward_end = 0
    for k in range(n):
        if not flags[k]:
            continue
        j = k - 1
        while j >= 0 and like[j] and not in_references[j]:
            in_references[j] = True
            j -= 1
        if k < forward_end:
            continue
        j = k + 1
        while j < n:
            block = blocks[j]
            if like[j]:
                in_references[j] = True
            elif (block.type == "heading" and not _is_terminator(block.text)
                  and _heading_bridges(blocks, flags, like, in_references, j)):
                in_references[j] = True
            else:
                break
            j += 1
        forward_end = j


def split_references(blocks: list[Block], reference_flags: list[bool]) -> tuple[list[Block], list[Block]]:
    """Return (body, references) in reading order.

    A reference section starts at a heading naming the list (any listed
    language, numbered or uppercase) and runs to the next heading that is at
    a higher level, or that starts an appendix/acknowledgements
    section, so a reference list followed by appendices ends where the
    appendices begin. Sub-headings inside the list ("Books", "Articles") belong
    to it, also at the same level when entries follow them; a figure, table,
    formula, or code block ends it. A short paragraph
    that merely reads like such a heading (a line of an unlabeled contents
    page) opens a list only when citation-shaped paragraphs follow it, and
    holds only that run. A bare word that is often a chapter title ("Literature")
    needs bibliographic markers in its entries, not just a year and a name.
    Lists the parser labeled as reference text
    (`reference_flags`) are references even outside a detected section, and
    the entries around them (plain numbered or citation-shaped paragraphs
    between and beside the labeled ones) go with them. An unheaded run of
    citation-shaped entries at the end of the document counts
    too (any language).
    """
    n = len(blocks)
    in_references = [False] * n
    i = 0
    while i < n:
        block = blocks[i]
        if not (_candidate_heading(block) and is_reference_heading(block.text)):
            i += 1
            continue
        strict = _is_ambiguous(block.text)
        if block.type == "heading":
            end = _section_end(blocks, reference_flags, i, block.level)
            if strict and not _run_is_list(blocks, reference_flags, i + 1, end, True):
                i += 1
                continue
        else:
            end = _citation_run_end(blocks, reference_flags, i + 1, strict)
            if end == i + 1:
                i += 1
                continue
        for k in range(i, end):
            in_references[k] = True
        i = end
    for k, flagged in enumerate(reference_flags):
        if flagged:
            in_references[k] = True
    _extend_parser_labeled(blocks, reference_flags, in_references)
    if (start := _trailing_unlabeled_list(blocks, in_references)) is not None:
        for k in range(start, n):
            in_references[k] = True
    body = [b for b, ref in zip(blocks, in_references) if not ref]
    refs = [b for b, ref in zip(blocks, in_references) if ref]
    return body, refs
