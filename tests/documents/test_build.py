"""Golden tests on synthetic content lists: block types, pages, headings, normalization."""

import pytest

from ragshelf.documents import Block, Document, build_document
from ragshelf.documents.normalize import dehyphenate, word_vocabulary

PAGES = 6
PROSE = " with enough additional words that the paragraph is clearly real prose and not a short running line of any kind."


def build(items, **kwargs) -> Document:
    return build_document(items, doc_id="d.pdf", content_hash="0" * 64, **kwargs)


def text(value, page=0, level=None):
    item = {"type": "text", "text": value, "page_idx": page}
    if level is not None:
        item["text_level"] = level
    return item


def signature(document):
    return [(b.type, b.page, b.level, b.text) for b in document.blocks]


def test_block_types_pages_and_headings_in_reading_order():
    items = [
        text("Synthetic Title", 0, 1),
        text("Opening paragraph.", 0),
        text("Methods", 1, 2),
        {"type": "list", "sub_type": "text", "list_items": ["first item", "second item"], "page_idx": 1},
        {"type": "table", "table_caption": ["Table 1. Counts"], "table_body": "<table><tr><td>1</td></tr></table>",
         "table_footnote": ["Note: synthetic"], "img_path": "images/t.png", "page_idx": 2},
        {"type": "equation", "text": "E = mc^2", "text_format": "latex", "img_path": "", "page_idx": 2},
        {"type": "code", "sub_type": "code", "code_caption": ["Listing 1"], "code_body": "x = 1\n\ty = 2",
         "code_footnote": [], "page_idx": 3},
        {"type": "image", "img_path": "images/f.png", "image_caption": ["Figure 1. A plot"], "image_footnote": [],
         "page_idx": 3},
        {"type": "chart", "img_path": "", "content": "", "chart_caption": ["Figure 2. Trend"], "chart_footnote": [],
         "page_idx": 4},
        {"type": "page_footnote", "text": "1 A footnote.", "page_idx": 4},
        text("Level zero is not a heading.", 5) | {"text_level": 0},
    ]
    document = build(items)
    assert signature(document) == [
        ("heading", 1, 1, "Synthetic Title"),
        ("paragraph", 1, None, "Opening paragraph."),
        ("heading", 2, 2, "Methods"),
        ("list", 2, None, "first item\nsecond item"),
        ("caption", 3, None, "Table 1. Counts"),
        ("table", 3, None, "<table><tr><td>1</td></tr></table>"),
        ("caption", 3, None, "Note: synthetic"),
        ("equation", 3, None, "E = mc^2"),
        ("caption", 4, None, "Listing 1"),
        ("code", 4, None, "x = 1\n\ty = 2"),
        ("caption", 4, None, "Figure 1. A plot"),
        ("caption", 5, None, "Figure 2. Trend"),
        ("paragraph", 5, None, "1 A footnote."),
        ("paragraph", 6, None, "Level zero is not a heading."),
    ]
    assert document.blocks[3].items == ("first item", "second item")
    assert document.page_count == 6
    assert [(h.level, h.text, h.page) for h in document.outline] == [(1, "Synthetic Title", 1), (2, "Methods", 2)]


def test_labeled_page_furniture_and_contents_pages_are_dropped_and_counted():
    items = [
        {"type": "header", "text": "Journal header", "page_idx": 0},
        {"type": "footer", "text": "Footer", "page_idx": 0},
        {"type": "page_number", "text": "1", "page_idx": 0},
        {"type": "aside_text", "text": "arXiv sidebar", "page_idx": 0},
        {"type": "index", "list_items": ["- 1 Intro", "- 2 Methods"], "page_idx": 0},
        text("Body.", 0),
        {"type": "image", "img_path": "x.png", "image_caption": [], "image_footnote": [], "page_idx": 0},
        {"type": "unknown-future-type", "page_idx": 0},
        {"type": "unknown-with-text", "text": "kept as a paragraph", "page_idx": 0},
    ]
    document = build(items)
    assert signature(document) == [("paragraph", 1, None, "Body."), ("paragraph", 1, None, "kept as a paragraph")]
    assert document.report.labeled_boilerplate_removed == 4
    assert document.report.index_removed == 1


def test_models_are_immutable_and_validate():
    document = build([text("Heading", 0, 1)])
    with pytest.raises(AttributeError):
        document.blocks = ()
    with pytest.raises(AttributeError):
        document.blocks[0].text = "changed"
    assert isinstance(document.blocks, tuple) and isinstance(document.references, tuple)
    with pytest.raises(ValueError):
        Block("paragraph", "x", 1, level=2)
    with pytest.raises(ValueError):
        Block("heading", "x", 1)
    with pytest.raises(ValueError):
        Block("paragraph", "x", 0)
    with pytest.raises(ValueError):
        Block("figure", "x", 1)


def test_empty_content_list_gives_an_empty_document():
    document = build([])
    assert document.blocks == () and document.references == () and document.page_count == 0
    assert document.metadata.title is None and document.metadata.language is None


def test_unicode_is_normalized_to_nfc_in_every_text_field():
    decomposed = "Café Résumé"
    document = build([
        text(decomposed, 0, 2),
        text(decomposed, 0),
        {"type": "list", "sub_type": "text", "list_items": [decomposed], "page_idx": 0},
        {"type": "code", "code_body": decomposed, "page_idx": 0},
    ])
    expected = "Café Résumé"
    assert [b.text for b in document.blocks] == [expected] * 4
    assert document.blocks[2].items == (expected,)


def test_invisible_characters_and_soft_hyphens_are_removed_and_spaces_collapsed():
    document = build([text("exam­ple​  of ﻿text\n spacing", 0)])
    assert document.blocks[0].text == "example of text spacing"


@pytest.mark.parametrize(("raw", "expected"), [
    ("an attach-\nment style", "an attachment style"),                      # typesetting hyphen: join
    ("Smith-\nJones agree", "Smith-Jones agree"),                           # uppercase next: a real compound
    ("a well-\nknown result", "a well-known result"),                       # known compound prefix
    ("evidence-\nbased care", "evidence-based care"),                       # known compound suffix
    ("the state-of-the-\nart", "the state-of-the-art"),                     # already compound
    ("COVID19-\nrelated", "COVID19-related"),                               # digit before the hyphen
    ("plain\nbreak", "plain break"),                                        # no hyphen: just a space
    ("a dash -\nnext", "a dash - next"),                                    # spaced dash is not a hyphen
    ("пока-\nзать", "показать"),                                            # Cyrillic typesetting hyphen
    ("кто-\nто", "кто-то"),                                                 # Russian hyphenated particle
    ("hyphen at end-\n", "hyphen at end-"),                                 # nothing follows
    ("rear-\n42 items", "rear-42 items"),                                   # digit after: not a word break
])
def test_dehyphenation_decisions(raw, expected):
    document = build([text(raw, 0)])
    assert document.blocks[0].text == expected


def test_document_vocabulary_decides_between_join_and_hyphen():
    kept = build([text("The co-operation grew. Co-operation helped; co-\noperation ended.", 0)])
    assert "co-operation ended" in kept.blocks[0].text
    joined = build([text("Cooperation grew. Cooperation helped; co-\noperation ended.", 0)])
    assert "cooperation ended" in joined.blocks[0].text
    # Prefix evidence loses to the document's own spelling of the joined word.
    assert "nonlinear" in build([text("A nonlinear map; non-\nlinear dynamics.", 0)]).blocks[0].text
    assert "non-linear" in build([text("A non-linear map; non-\nlinear dynamics.", 0)]).blocks[0].text


def test_dehyphenate_counts_only_joins():
    vocabulary = word_vocabulary(["x"])
    assert dehyphenate("exam-\nple and Smith-\nJones", vocabulary) == ("example and Smith-Jones", 1)


def test_code_tables_and_equations_keep_their_line_structure():
    document = build([
        {"type": "code", "code_body": "a-\nb  \n  c", "page_idx": 0},
        {"type": "table", "table_body": "| a-\n| b |", "page_idx": 0},
        {"type": "equation", "text": "x =\n y", "page_idx": 0},
    ])
    assert [b.text for b in document.blocks] == ["a-\nb\n  c", "| a-\n| b |", "x =\n y"]
    assert document.report.dehyphenated == 0


def running_pages(extra_per_page=None, pages=PAGES, header="Journal of Synthetic Studies (2019)"):
    items = []
    for n in range(pages):
        items.append(text(header.format(n=n + 1), n))
        items.append(text(f"Unique body paragraph number {n}" + PROSE, n))
        for extra in (extra_per_page or {}).get(n, []):
            items.append(extra)
        items.append(text(f"Page {n + 1}", n))
    return items


def test_running_headers_and_page_numbers_are_removed_by_repetition():
    document = build(running_pages())
    assert [b.text for b in document.blocks] == [
        f"Unique body paragraph number {n}" + PROSE for n in range(PAGES)]
    assert document.report.running_text_removed == 2 * PAGES


def test_running_text_detection_keeps_legitimate_repeats():
    extras = {2: [text("Results", 2, 2), text("Results", 2, 2), text("Same sentence twice.", 2),
                  text("Same sentence twice.", 2), text("Closing.", 2)]}
    document = build(running_pages(extras))
    texts = [b.text for b in document.blocks]
    assert texts.count("Results") == 2          # a section title repeated on one page
    assert texts.count("Same sentence twice.") == 2
    assert not any(t.startswith("Journal of") or t.startswith("Page ") for t in texts)


def test_repetition_needs_distinct_pages_and_edge_positions():
    # Present on only two pages: not running text.
    two = build(running_pages(pages=2))
    assert sum(b.text.startswith("Journal of") for b in two.blocks) == 2
    # Repeated on every page but in the middle of the page: ordinary text.
    items = []
    for n in range(PAGES):
        items += [text(f"Opening paragraph {n} of real text here, long enough to read.", n),
                  text(f"Second paragraph {n} of real text here, long enough to read.", n),
                  text("Important refrain.", n),
                  text(f"Fourth paragraph {n} of real text here, long enough to read.", n),
                  text(f"Fifth paragraph {n} of real text here, long enough to read.", n)]
    document = build(items)
    assert sum(b.text == "Important refrain." for b in document.blocks) == PAGES


def test_headings_are_never_running_text():
    items = []
    for n in range(PAGES):
        items += [text("Chapter heading", n, 2), text(f"Body number {n} with enough words to be prose here.", n)]
    document = build(items)
    assert sum(b.type == "heading" for b in document.blocks) == PAGES


def test_alternating_chapter_headers_in_a_long_document_are_removed():
    items = []
    for n in range(40):
        items += [text("Part Two: The Synthetic Chapter" if 10 <= n < 20 else "Part One: Beginnings", n),
                  text(f"Body paragraph {n}" + PROSE, n)]
    document = build(items)
    assert all(not b.text.startswith("Part ") for b in document.blocks)
    assert len(document.blocks) == 40


# --- hyphenation: suspended hyphens and addresses -----------------------------------------------

@pytest.mark.parametrize(("raw", "expected"), [
    ("short-\nand long-term effects", "short- and long-term effects"),      # suspended hyphen
    ("pre-\nand post-processing", "pre- and post-processing"),
    ("input-\nor output-bound", "input- or output-bound"),
    ("see https://example.org/some-\npath/file", "see https://example.org/some-path/file"),
    ("doi 10.1016/j.jbi-\nmed.2020.1", "doi 10.1016/j.jbi-med.2020.1"),   # a DOI keeps its hyphen
    ("write to me@exam-\nple.org", "write to me@exam-ple.org"),
    ("model-\nfree learning", "model-free learning"),
    ("a two-\nthirds majority", "a two-thirds majority"),
    ("an attach-\nment still joins", "an attachment still joins"),
    ("the left-\nright side", "the left-right side"),                         # whole-word opposition pair
    ("an up-\ndown scale and a north-\nsouth axis", "an up-down scale and a north-south axis"),
    ("input-\noutput pairs", "input-output pairs"),
])
def test_dehyphenation_keeps_suspended_hyphens_and_addresses(raw, expected):
    assert build([text(raw, 0)]).blocks[0].text == expected


# --- running text must not eat content ---------------------------------------------------------------

def body(n):
    return text(f"Distinct body paragraph number {n}" + PROSE, n)


def test_numbered_labels_and_footnotes_that_repeat_are_content_not_running_text():
    cases = {
        "Example N": lambda n: [text(f"Example {n + 1}.", n), body(n)],
        "Fig N": lambda n: [body(n), text(f"Fig. {n + 1}", n)],
        "footnote": lambda n: [body(n), {"type": "page_footnote", "text": f"{n + 1} Ibid., p. {n + 9}.", "page_idx": n}],
    }
    for name, page in cases.items():
        items = [item for n in range(PAGES) for item in page(n)]
        document = build(items)
        assert document.report.running_text_removed == 0, name
        assert len(document.blocks) == len(items), name


def test_a_line_under_a_table_is_a_table_note_not_a_footer():
    items = []
    for n in range(PAGES):
        items += [body(n), {"type": "table", "table_body": "| a |", "page_idx": n},
                  text("Source: author's own calculations.", n)]
    document = build(items)
    assert document.report.running_text_removed == 0
    assert sum(b.text.startswith("Source:") for b in document.blocks) == PAGES


def test_short_documents_are_left_alone():
    items = [item for n in range(5) for item in (text("Yes", n), body(n))]
    assert build(items).report.running_text_removed == 0
    assert build([item for n in range(PAGES) for item in (text("Yes", n), body(n))]).report.running_text_removed == PAGES


@pytest.mark.parametrize("footer", [
    lambda n: str(n + 1), lambda n: f"- {n + 1} -", lambda n: f"Page {n + 1}", lambda n: f"page {n + 1} of 6",
    lambda n: f"{n + 1} / 6", lambda n: f"p. {n + 1}", lambda n: f"{10 * n + 1}-{10 * n + 9}",
    lambda n: ["i", "ii", "iii", "iv", "v", "vi"][n], lambda n: f"Page {['i', 'ii', 'iii', 'iv', 'v', 'vi'][n]}",
])
def test_page_numbers_in_every_form_are_masked_and_removed(footer):
    items = [item for n in range(PAGES) for item in (body(n), text(footer(n), n))]
    document = build(items)
    assert document.report.running_text_removed == PAGES and len(document.blocks) == PAGES


def test_digits_are_masked_only_when_the_whole_paragraph_is_a_page_number():
    # Embedded numbers vary the text: nothing here repeats, so nothing is removed (a header that carries
    # its page number is left in the body rather than risk deleting content).
    items = []
    for n in range(PAGES):
        items += [text(f"Journal of Applied Synthetic Things {n + 1} (2019) {n}0-{n}9", n), body(n),
                  text(f"Table note: values in {1990 + n} prices, unless stated otherwise in the text.", n)]
    document = build(items)
    assert document.report.running_text_removed == 0 and len(document.blocks) == 3 * PAGES


def test_short_paragraphs_that_differ_only_in_a_number_are_kept():
    items = [item for n in range(PAGES)
             for item in (text(f"Figure {n + 1} shows the distribution of the synthetic sample", n), body(n),
                          text(f"Table {n + 1} lists the synthetic results by group and year", n))]
    document = build(items)
    assert document.report.running_text_removed == 0 and len(document.blocks) == len(items)


def test_three_pages_and_a_quarter_of_the_pages_remain_the_thresholds():
    def with_footer(pages, on):
        return [item for n in range(pages) for item in ([body(n), text("Shared footer line", n)] if n in on else [body(n)])]

    assert build(with_footer(12, {0, 1})).report.running_text_removed == 0          # two pages
    assert build(with_footer(12, {0, 1, 2})).report.running_text_removed == 3       # three pages, a quarter of 12
    assert build(with_footer(20, {0, 1, 2, 3})).report.running_text_removed == 0    # 4 < a quarter of 20
    assert build(with_footer(20, {0, 1, 2, 3, 4})).report.running_text_removed == 5


# --- more hyphenation cases: compounds, addresses, soft hyphens ---------------------------------------

@pytest.mark.parametrize(("raw", "expected"), [
    ("an x-\nray beam", "an x-ray beam"),                                         # one-letter left part
    ("a t-\ntest and a p-\nvalue", "a t-test and a p-value"),
    ("send an e-\nmail", "send an e-mail"),
    ("end-\nto-end encryption", "end-to-end encryption"),                         # a function word that starts a compound
    ("face-\nto-face talks", "face-to-face talks"),
    ("a built-\nin test and a plug-\nin", "a built-in test and a plug-in"),       # particles
    ("a DNA-\nbinding protein", "a DNA-binding protein"),                         # acronym compound
    ("visit www.my-\nsite.org today", "visit www.my-site.org today"),             # address, seen from the left
    ("see example-\ncorp.com", "see example-corp.com"),                           # address, seen from the right
    ("write john-\ndoe@example.org", "write john-doe@example.org"),
    ("exam­\nple items and the co­\noperation", "example items and the cooperation"),   # soft hyphen at a line end
    ("an exam­ple inline", "an example inline"),
])
def test_dehyphenation_review_cases(raw, expected):
    assert build([text(raw, 0)]).blocks[0].text == expected


def test_a_very_long_hard_wrapped_paragraph_is_dehyphenated_in_linear_time():
    import time

    unit = "word " * 20 + "hyphen-\nated "
    big = unit * 12000                       # about 1.8 MB with 12,000 candidate breaks
    start = time.perf_counter()
    joined, count = dehyphenate(big, word_vocabulary([]))
    assert count == 12000 and "hyphenated" in joined
    assert time.perf_counter() - start < 10  # the old rfind to offset 0 made this quadratic


# --- invisible and control characters ---------------------------------------------------------------

def test_joiners_stay_in_scripts_that_need_them_and_go_between_latin_and_cyrillic_letters():
    persian = "می‌خواهم"             # ZWNJ is spelling here
    emoji = "\U0001f468‍\U0001f469"
    mixed = "ab‍c and при‌вет"
    document = build([text(persian, 0), text(emoji, 0), text(mixed, 0)])
    assert [b.text for b in document.blocks] == [persian, emoji, "abc and привет"]


def test_zero_width_space_bom_and_word_joiner_are_removed():
    assert build([text("a​b﻿c⁠d", 0)]).blocks[0].text == "abcd"


def test_control_characters_are_removed_from_text_but_not_from_code():
    document = build([text("red\x1b[31m title\x07 here", 0),
                      {"type": "code", "code_body": "x = '‍'  # \x1b", "page_idx": 0}])
    assert document.blocks[0].text == "red[31m title here"
    assert document.blocks[1].text == "x = '‍'  # \x1b"


def test_a_soft_hyphen_at_a_line_end_is_not_a_word_break():
    assert build([text("A long sentence about exam­\nple items.", 0)]).blocks[0].text == \
        "A long sentence about example items."


# --- code is kept as written --------------------------------------------------------------------------

def test_code_blocks_keep_their_characters():
    code = "s = 'a‍b'  \nt = \"é\""
    document = build([{"type": "code", "code_body": code, "page_idx": 0}])
    assert document.blocks[0].text == "s = 'a‍b'\nt = \"é\""      # NFC and trailing spaces only
