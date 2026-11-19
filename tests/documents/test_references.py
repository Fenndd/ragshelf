"""Reference-list separation: multilingual headings, position, false positives."""

import pytest

from ragshelf.documents import build_document

ENTRY = "Smith, J. (2019). A synthetic study of nothing. Journal of Examples, 12, 1-10."
PROSE = ("Earlier work on this topic (Smith, 2019; Jones, 2020) argued at length that the synthetic effect "
         "depends on context, and that the evidence for it is mixed across the many settings that were "
         "examined by the authors in the years before the present study was designed and carried out. " * 2)


def build(items):
    return build_document(items, doc_id="d.pdf", content_hash="0" * 64)


def text(value, page=0, level=None):
    item = {"type": "text", "text": value, "page_idx": page}
    if level is not None:
        item["text_level"] = level
    return item


def reference_list(page=1):
    return [{"type": "list", "sub_type": "ref_text", "list_items": [ENTRY, ENTRY.replace("Smith", "Jones")],
             "page_idx": page}]


def split(heading, *, level=2, entries=None, tail=()):
    items = [text("Body title", 0, 1), text("Body paragraph before.", 0), text(heading, 1, level),
             *(entries if entries is not None else reference_list()), *tail]
    document = build(items)
    return [b.text for b in document.blocks], [b.text for b in document.references]


@pytest.mark.parametrize("heading", [
    "References", "REFERENCES", "7. References", "7 REFERENCES", "VII. References", "7.1 References",
    "References:", "Reference List", "Bibliography", "BIBLIOGRAPHY", "Works Cited",
    "Список литературы", "СПИСОК ЛИТЕРАТУРЫ", "Список использованной литературы", "Библиография",
    "Zoznam literatúry", "Zoznam použitej literatúry", "Referencie", "Zoznam literatury",
    "Literaturverzeichnis", "LITERATURVERZEICHNIS", "Quellenverzeichnis", "Referenzen",
    "Références", "RÉFÉRENCES", "Bibliographie", "Références bibliographiques",
    "Chapter 9: References", "Referencias", "Bibliografía",
    "Références",  # decomposed accents
])
def test_reference_headings_in_any_language_start_the_reference_list(heading):
    body, references = split(heading)
    assert body == ["Body title", "Body paragraph before."]
    assert references[0] == heading.replace("Références", "Références")
    assert len(references) == 2 and references[1].startswith("Smith, J.")


@pytest.mark.parametrize("heading", [
    "Literature Review",
    "A Review of the Literature on Attachment",
    "References to Violence in Media",
    "Reference Standards and Calibration",
    "Annotated Bibliography of Fieldwork Methods",
    "On Sources of Funding",
    "Cross-References Between Sections",
    "Referencing Style",
])
def test_headings_that_merely_contain_the_word_are_body_text(heading):
    body, references = split(heading, entries=[text("Ordinary paragraph of the section.", 1)])
    assert references == []
    assert heading in body


@pytest.mark.parametrize("heading", ["Literature", "Литература", "Literatúra", "Literatur"])
def test_ambiguous_bare_word_needs_reference_like_entries(heading):
    # A literature-review chapter: long prose with citations, not entries.
    body, references = split(heading, entries=[text(PROSE, 1)])
    assert references == [] and heading in body
    # The reference list: short entries with years.
    body, references = split(heading, entries=[text(ENTRY, 1), text(ENTRY.replace("Smith", "Jones"), 1)])
    assert references[0] == heading and body == ["Body title", "Body paragraph before."]
    # An explicitly labeled reference list is accepted too.
    body, references = split(heading)
    assert references[0] == heading


def test_reference_list_followed_by_appendices_is_not_swallowing_them():
    body, references = split("References", tail=[
        text("Appendix A: Survey items", 2, 2), text("Appendix paragraph.", 2),
        text("Acknowledgments", 2, 2), text("Thanks to nobody.", 2)])
    assert "Appendix A: Survey items" in body and "Appendix paragraph." in body
    assert "Acknowledgments" in body
    assert references[0] == "References" and len(references) == 2


def test_reference_list_in_the_middle_ends_at_the_next_section():
    body, references = split("References", tail=[text("8. Conclusion", 2, 2), text("Final remarks.", 2)])
    assert body[-2:] == ["8. Conclusion", "Final remarks."]
    assert len(references) == 2


def test_appendix_heading_ends_the_list_even_at_a_deeper_level():
    body, references = split("References", level=2, tail=[text("Приложение Б", 2, 3), text("Текст приложения.", 2)])
    assert "Приложение Б" in body and len(references) == 2


def test_subheadings_inside_the_list_belong_to_it():
    body, references = split("References", tail=[text("Books", 1, 3), text(ENTRY, 1), text("Articles", 1, 3), text(ENTRY, 1)])
    assert body == ["Body title", "Body paragraph before."]
    assert "Books" in references and "Articles" in references


def test_parser_labeled_reference_lists_are_references_even_without_a_heading():
    items = [text("Title", 0, 1), text("Body text.", 0), *reference_list(page=1), text("Tail text.", 1)]
    document = build(items)
    assert [b.text for b in document.blocks] == ["Title", "Body text.", "Tail text."]
    assert len(document.references) == 1 and document.references[0].items[0].startswith("Smith")


def test_references_keep_block_types_and_pages():
    document = build([text("Intro", 0, 1), text("References", 3, 2), *reference_list(page=3)])
    heading, entries = document.references
    assert (heading.type, heading.level, heading.page) == ("heading", 2, 4)
    assert (entries.type, entries.page, len(entries.items)) == ("list", 4, 2)
    assert document.outline[0].text == "Intro" and len(document.outline) == 1


def test_a_bare_keyword_paragraph_acts_as_an_unlabeled_heading():
    items = [text("Title", 0, 1), text("Body text.", 0), text("REFERENCES", 1), text(ENTRY, 1), text(ENTRY, 1)]
    document = build(items)
    assert [b.text for b in document.blocks] == ["Title", "Body text."]
    assert len(document.references) == 3


def test_a_long_paragraph_is_never_taken_for_a_heading():
    document = build([text("Title", 0, 1), text("References", 0) | {"text": "References " + PROSE}])
    assert document.references == ()


def test_several_reference_sections_are_all_separated():
    items = [text("Ch 1", 0, 1), text("Body one.", 0), text("References", 1, 2), text(ENTRY, 1),
             text("Ch 2", 2, 1), text("Body two.", 2), text("References", 3, 2), text(ENTRY, 3)]
    document = build(items)
    assert [b.text for b in document.blocks] == ["Ch 1", "Body one.", "Ch 2", "Body two."]
    assert [b.text for b in document.references] == ["References", ENTRY, "References", ENTRY]


# --- more languages, and a language-independent fallback ------------------------------------------

@pytest.mark.parametrize("heading", [
    "参考文献", "参考资料", "5. 参考文献", "5.参考文献", "第5章 参考文献", "五、参考文献", "참고문헌",
    "Referenties", "Literatuurlijst", "Список літератури", "Список використаної літератури",
    "Irodalomjegyzék", "Použité zdroje", "Zoznam použitých zdrojov", "Cited References",
    "References and Further Reading", "Referências", "Referências Bibliográficas", "Použitá literatúra",
    "Literature Cited", "Kaynakça", "Referenser", "Referanser", "Βιβλιογραφία", "Obras citadas",
])
def test_more_reference_headings_are_recognized(heading):
    body, references = split(heading)
    assert body == ["Body title", "Body paragraph before."] and len(references) == 2


@pytest.mark.parametrize("heading", ["Reference", "Irodalom", "Literatuur", "Література", "Bronnen"])
def test_ambiguous_words_in_more_languages_need_citation_like_entries(heading):
    body, references = split(heading, entries=[text(PROSE, 1)])
    assert references == [] and heading in body
    body, references = split(heading, entries=[text(ENTRY, 1), text(ENTRY.replace("Smith", "Jones"), 1)])
    assert references[0] == heading and len(references) == 3


def test_an_unknown_heading_with_a_trailing_run_of_citations_is_still_the_reference_list():
    entries = [text(ENTRY.replace("Smith", name), 1) for name in ("Smith", "Jones", "Brown", "Green")]
    body, references = split("Zażółć gęślą jaźń", entries=entries)
    assert body == ["Body title", "Body paragraph before."]
    assert references[0] == "Zażółć gęślą jaźń" and len(references) == 5


def test_the_trailing_fallback_needs_citation_shaped_entries_and_leaves_prose_alone():
    sentence = "In 1850 the author published a novel and the critics responded warmly."
    prose = [text(sentence, 1) for _ in range(5)]
    body, references = split("Zażółć gęślą jaźń", entries=prose)
    assert references == [] and body.count(sentence) == 5
    # Fewer than three entries, or a minority of citations, do not qualify either.
    assert split("Zażółć", entries=[text(ENTRY, 1), text(ENTRY, 1)])[1] == []
    assert split("Zażółć", entries=[text(ENTRY, 1)] + prose[:4])[1] == []


def test_a_document_that_is_only_citations_keeps_a_body():
    document = build([text(ENTRY, 0) for _ in range(5)])
    assert len(document.blocks) == 5 and document.references == ()


@pytest.mark.parametrize(("heading", "sentence"), [
    ("Literature", "In 1850 the author published a novel and critics responded warmly."),
    ("Литература", "В 1850 году вышел роман, и критики тепло отозвались о нём."),
])
def test_a_literary_history_chapter_with_dates_is_not_a_reference_list(heading, sentence):
    items = [text("Book", 0, 1), text("Intro text.", 0), text(heading, 1, 1), *[text(sentence, 1) for _ in range(5)],
             text("Next Chapter", 2, 1), text("More text.", 2)]
    document = build(items)
    assert document.references == () and len(document.blocks) == 10


# --- keyword lines that are not headings; where a list ends -------------------------------------------------

def test_contents_lines_that_read_like_reference_headings_do_not_swallow_the_front_matter():
    preface = ["The first preface paragraph, in plain words, thanks the readers of the draft.",
               "The second preface paragraph says what the book covers and what it leaves out."]
    items = [text("Title", 0, 1), text("Contents", 0, 1), text("Introduction", 0), text("Methods", 0),
             text("References", 0), text("Index", 0), *[text(p, 0) for p in preface],
             text("Chapter 1", 1, 1), text("Body of the chapter.", 1),
             text("References", 5, 1), text(ENTRY, 5), text(ENTRY, 5)]
    document = build(items)
    body = [b.text for b in document.blocks]
    assert all(p in body for p in preface) and body.count("References") == 1 and "Index" in body
    assert [b.text for b in document.references] == ["References", ENTRY, ENTRY]


def test_a_bare_keyword_paragraph_holds_only_its_citation_run():
    prose = "Back to ordinary prose that follows the list, without any heading at all."
    document = build([text("Title", 0, 1), text("Body text.", 0), text("REFERENCES", 1), text(ENTRY, 1), text(ENTRY, 1),
                      text(prose, 1), text("More prose that also belongs to the body of the document.", 1)])
    assert len(document.references) == 3 and prose in [b.text for b in document.blocks]


def test_a_bare_keyword_paragraph_without_citations_after_it_stays_in_the_body():
    for word in ("References", "Bibliography", "Список литературы", "Literatur"):
        document = build([text("Title", 0, 1), text(word, 0), text("An ordinary body paragraph follows it.", 0)])
        assert document.references == () and len(document.blocks) == 3, word


def test_one_odd_entry_does_not_cut_a_bare_run_but_two_do():
    odd = "Plato. The Republic."
    kept = build([text("T", 0, 1), text("Body.", 0), text("References", 1), text(ENTRY, 1), text(odd, 1), text(ENTRY, 1)])
    assert len(kept.references) == 4
    cut = build([text("T", 0, 1), text("Body.", 0), text("References", 1), text(ENTRY, 1), text(odd, 1), text(odd, 1),
                 text(ENTRY, 1)])
    assert len(cut.references) == 2


def test_a_figure_or_table_ends_the_reference_list():
    items = [text("Book", 0, 1), text("Text.", 0), text("References", 1, 2), text(ENTRY, 1),
             {"type": "image", "image_caption": ["Figure 9. A map"], "page_idx": 1},
             {"type": "table", "table_body": "| a |", "page_idx": 1}, text("Closing remark in the body.", 1)]
    document = build(items)
    assert [b.text for b in document.references] == ["References", ENTRY]
    assert [b.type for b in document.blocks][-3:] == ["caption", "table", "paragraph"]


@pytest.mark.parametrize(("heading", "level"), [("About the authors", 3), ("About the Author", 2), ("Biographies", 3),
                                                ("Index", 2), ("Об авторах", 3)])
def test_trailing_back_matter_is_not_part_of_the_reference_list(heading, level):
    body, references = split("References", tail=[text(heading, 1, level), text("Short biography text of the author.", 1)])
    assert heading in body and len(references) == 2


def test_an_ambiguous_heading_with_nothing_after_it_stays_in_the_body():
    document = build([text("Book", 0, 1), text("Text.", 0), text("Literature", 1, 2)])
    assert document.references == () and len(document.blocks) == 3


def test_thousands_of_bare_keyword_paragraphs_are_scanned_in_linear_time():
    import time

    items = [text("Title", 0, 1)] + [text("Literature", 0) for _ in range(20000)]
    start = time.perf_counter()
    document = build(items)
    assert document.references == () and len(document.blocks) == 20001
    assert time.perf_counter() - start < 10     # 20,000 candidates took minutes when each rescanned the rest


# --- review round 2: flat heading levels, mixed labeled/plain entries, prose chapters with initials ---------

def numbered(n):
    return f"{n}. Jones, K. Notes on example number {n}, in Collected Essays, Example Press, 2001, p. {n}."


def test_same_level_subheadings_stay_inside_the_reference_list():
    # One heading level throughout (as in MinerU output): "Books" and "Web sources" are not new chapters.
    items = [text("Book", 0, 1), text("Body text.", 0), text("References", 1, 1), text("Journal articles", 1, 1),
             text(ENTRY, 1), text(ENTRY, 1), text("Books", 1, 1), text(ENTRY, 1), text(ENTRY, 1),
             text("Web sources", 1, 1), text(ENTRY, 1), text(ENTRY, 1), text(ENTRY, 1)]
    document = build(items)
    assert [b.text for b in document.blocks] == ["Book", "Body text."]
    assert [b.text for b in document.references].count(ENTRY) == 7 and len(document.references) == 11


def test_a_same_level_heading_followed_by_prose_still_ends_the_list():
    items = [text("Book", 0, 1), text("References", 1, 1), text(ENTRY, 1), text(ENTRY, 1),
             text("Chapter 9", 2, 1), text(PROSE, 2), text(PROSE, 2)]
    document = build(items)
    assert [b.text for b in document.blocks] == ["Book", "Chapter 9", PROSE.strip(), PROSE.strip()] and len(document.references) == 3


def test_a_same_level_heading_with_a_single_citation_does_not_swallow_a_chapter():
    items = [text("Book", 0, 1), text("References", 1, 1), text(ENTRY, 1), text(ENTRY, 1),
             text("Chapter 9", 2, 1), text(ENTRY, 2), text(PROSE, 2), text(PROSE, 2)]
    document = build(items)
    assert "Chapter 9" in [b.text for b in document.blocks] and len(document.references) == 3


def ref_text(*entries, page=1):
    return {"type": "list", "sub_type": "ref_text", "list_items": list(entries), "page_idx": page}


def test_plain_numbered_entries_beside_and_between_labeled_lists_are_references():
    items = [text("Book", 0, 1), text("Last chapter text.", 0),
             text("Notes", 5, 2), text(numbered(1), 5), text(numbered(2), 5), ref_text(ENTRY, ENTRY, page=5),
             text(numbered(3), 5), text("Chapter two notes", 6, 2), text(numbered(4), 6), ref_text(ENTRY, page=6),
             text(numbered(5), 6), text("Tail paragraph of the body.", 7)]
    document = build(items)
    body = [b.text for b in document.blocks]
    assert body == ["Book", "Last chapter text.", "Notes", "Tail paragraph of the body."]
    assert [b.text for b in document.references][:2] == [numbered(1), numbered(2)]
    assert "Chapter two notes" in [b.text for b in document.references]
    assert sum(b.type in {"paragraph", "list"} for b in document.references) == 7


def test_entries_next_to_a_labeled_list_are_pulled_in_only_when_they_look_like_entries():
    plain = "A short plain remark in the body."
    items = [text("Book", 0, 1), text(plain, 0), text("2. Wash the sample", 0),
             ref_text(ENTRY, page=1), text(plain, 1), text(numbered(9), 1)]
    document = build(items)
    body = [b.text for b in document.blocks]
    assert plain in body and numbered(9) in body                     # the plain paragraph stops the run
    assert "2. Wash the sample" in body         # shorter than an entry: stays


def test_a_heading_after_a_labeled_list_stays_when_prose_follows_it():
    items = [text("Book", 0, 1), text("Chapter 1", 0, 2), ref_text(ENTRY, page=0), text("Chapter 2", 1, 2),
             text(PROSE, 1), text(PROSE, 1), text("Exercises", 2, 2), text(numbered(1), 2), text(numbered(2), 2)]
    document = build(items)
    body = [b.text for b in document.blocks]
    assert "Chapter 2" in body and PROSE.strip() in body and "Exercises" in body
    assert [b.text for b in document.references] == [ENTRY]


def test_a_labeled_list_before_a_chapter_heading_leaves_the_heading_in_the_body():
    # A per-chapter bibliography without its own heading: the chapter heading before it is not part of the list.
    items = [text("Book", 0, 1), text("Chapter 1", 0, 2), text("Prose of the chapter.", 0), ref_text(ENTRY, page=0),
             text("Chapter 2", 1, 2), text("Prose of chapter two.", 1)]
    document = build(items)
    assert [b.text for b in document.blocks] == ["Book", "Chapter 1", "Prose of the chapter.", "Chapter 2",
                                                 "Prose of chapter two."]


def test_labeled_neighbours_are_scanned_in_linear_time():
    import time

    items = [text("Book", 0, 1)]
    for k in range(4000):
        items += [ref_text(ENTRY, page=1), text(numbered(k), 1), text(f"Heading {k}", 1, 2)]
    start = time.perf_counter()
    document = build(items)
    assert len(document.blocks) >= 1 and time.perf_counter() - start < 10


@pytest.mark.parametrize(("heading", "sentence"), [
    ("Литература", "В 1837 г. А. С. Пушкин написал поэму, и критики тепло отозвались о ней."),
    ("Literature", "In 1850 N. Hawthorne published a novel, and the critics responded warmly."),
    ("Literatur", "Im Jahr 1850 veröffentlichte N. Hawthorne einen Roman, den Kritiker lobten."),
    ("Literatúra", "V roku 1850 vydal N. Hawthorne román, ktorý kritici prijali veľmi vrelo."),
])
def test_initials_and_a_year_inside_a_sentence_do_not_make_a_literature_chapter_a_reference_list(heading, sentence):
    items = [text("Book", 0, 1), text("Intro text.", 0), text(heading, 1, 2), *[text(sentence, 1) for _ in range(4)],
             text("Next chapter", 2, 2), text("More text.", 2)]
    document = build(items)
    assert document.references == () and len(document.blocks) == 9


@pytest.mark.parametrize(("heading", "entry"), [
    ("Литература", "Пушкин А. С. Евгений Онегин. М.: Наука, 1833. С. 12-15."),
    ("Литература", "Пушкин, А. С. Евгений Онегин. 1833."),
    ("Literature", "Smith J. A. 2019. A synthetic study of nothing. Journal of Examples 12(3): 1-10."),
    ("Literatur", "Müller, H.: Ein synthetisches Beispiel. In: Beispiele 12 (2019), S. 3-9."),
    ("Literature", "1. A. Hawthorne, The Scarlet Letter, Boston, 1850."),
    ("Literature", "[3] Brown et al. Another synthetic example, 2018."),
    ("Literature", "Doe J., Roe R. Example theory. https://example.org/paper, 2017."),
])
def test_a_bare_literature_heading_accepts_real_bibliographic_entries(heading, entry):
    items = [text("Book", 0, 1), text("Intro text.", 0), text(heading, 1, 2), *[text(entry, 1) for _ in range(3)],
             text("Next chapter", 2, 2), text("More text.", 2)]
    document = build(items)
    assert [b.text for b in document.references] == [heading, entry, entry, entry]


def test_a_bare_literature_paragraph_also_needs_bibliographic_entries():
    prose = "In 1850 N. Hawthorne published a novel, and the critics responded warmly."
    document = build([text("Book", 0, 1), text("Intro.", 0), text("Literature", 1), text(prose, 1), text(prose, 1)])
    assert document.references == ()


def test_the_report_counts_reference_like_entries_left_in_the_body_without_quoting_them():
    cited = "12. Jones, K. (2001). A synthetic note. Journal of Examples, 4, 5-9."
    # A plain paragraph between the labeled lists ends the run, so the numbered citation stays in the body.
    items = [text("Book", 0, 1), text("Body.", 0), ref_text(ENTRY, page=1), text(PROSE, 1), text(cited, 1),
             text(PROSE, 1), ref_text(ENTRY, page=2)]
    document = build(items)
    assert cited in [b.text for b in document.blocks]
    assert document.report.reference_like_in_body == 1
    assert build([text("Book", 0, 1), text("Body.", 0), ref_text(ENTRY, page=1)]).report.reference_like_in_body == 0
