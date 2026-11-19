"""Metadata: parsed-content extraction, PDF metadata, DOI, language, sidecar precedence."""

import json

import pytest

from ragshelf.documents import MetadataError, build_document, normalize_doi
from ragshelf.documents.metadata import (
    PdfInfo,
    find_doi,
    read_pdf_metadata,
    read_sidecar,
    sidecar_path,
    split_authors,
)

PARAGRAPH = "A synthetic body paragraph with enough detail to describe the experiment and its preliminary results."


def text(value, page=0, level=None, **extra):
    item = {"type": "text", "text": value, "page_idx": page, **extra}
    if level is not None:
        item["text_level"] = level
    return item


def build(items, **kwargs):
    return build_document(items, doc_id="d.pdf", content_hash="0" * 64, **kwargs)


FRONT = [
    text("Attachment in Synthetic Adults", 0, 1),
    text("Jane Q. Smith1, John Doe2,* and Maria Novak1", 0),
    text("1 Department of Psychology, University of Nowhere", 0),
    text("Abstract", 0, 2),
    text(PARAGRAPH + " See doi:10.1234/Abc.DEF-9(1).", 0),
    {"type": "footer", "text": "© 2019 Synthetic Publishing", "page_idx": 0},
]


# --- DOI -----------------------------------------------------------------------

@pytest.mark.parametrize(("raw", "expected"), [
    ("doi:10.1234/Abc.DEF-9", "10.1234/abc.def-9"),
    ("https://doi.org/10.1234/ABC.5.", "10.1234/abc.5"),
    ("(see 10.1234/abc.5),", "10.1234/abc.5"),
    ("[10.1234/abc.5];", "10.1234/abc.5"),
    ("DOI 10.1002/(SICI)1097-4571(199806)49:8.", "10.1002/(sici)1097-4571(199806)49:8"),
    ("10.1016/S0140-6736(20)30183-5).", "10.1016/s0140-6736(20)30183-5"),
    ("10.12345678/x_y/z", "10.12345678/x_y/z"),
])
def test_doi_is_normalized_and_stripped_of_trailing_punctuation(raw, expected):
    assert normalize_doi(raw) == expected


@pytest.mark.parametrize("raw", ["", "no doi here", "10.12/short", "version 10.5 of 2019", "10.1234/"])
def test_non_dois_are_rejected(raw):
    assert normalize_doi(raw) is None


def test_first_doi_in_reading_order_wins_and_case_is_irrelevant_for_comparison():
    assert find_doi(["nothing", "see 10.1234/AAA.1 and 10.1234/bbb.2"]) == "10.1234/aaa.1"
    assert normalize_doi("10.1234/AAA.1") == normalize_doi("https://doi.org/10.1234/aaa.1")


# --- title, authors, year, DOI from parsed content ----------------------------

def test_parsed_metadata_has_provenance_and_language_stays_unknown():
    metadata = build(FRONT).metadata
    assert metadata.title == "Attachment in Synthetic Adults"
    assert metadata.authors == ("Jane Q. Smith", "John Doe", "Maria Novak")
    assert metadata.year == 2019
    assert metadata.doi == "10.1234/abc.def-9(1)"
    assert metadata.language is None
    assert dict(metadata.sources) == {"title": "mineru", "authors": "mineru", "year": "mineru",
                                      "doi": "doi-pattern"}
    assert metadata.source_of("title") == "mineru" and metadata.source_of("nonexistent") == "none"


def test_no_title_when_the_first_top_level_heading_is_a_section_name():
    metadata = build([text("1. Introduction", 0, 1), text(PARAGRAPH, 0), text("Real Title", 1, 1)]).metadata
    assert metadata.title is None and "title" not in dict(metadata.sources)


def test_affiliation_and_abstract_lines_are_not_authors():
    items = [text("A Title", 0, 1), text("1 Department of Things, University of Stuff", 0),
             text("Abstract: we study the thing.", 0), text(PARAGRAPH, 0)]
    assert build(items).metadata.authors == ()


def test_authors_in_russian_and_with_marks_are_split():
    items = [text("Название работы", 0, 1), text("Иван Петров$^{1}$, Анна Сидорова², Олег Иванов*", 0)]
    assert build(items).metadata.authors == ("Иван Петров", "Анна Сидорова", "Олег Иванов")


@pytest.mark.parametrize(("raw", "expected"), [
    ("Smith, John", ("Smith, John",)),
    ("Smith, J.; Doe, A.", ("Smith, J.", "Doe, A.")),
    ("Jane Smith, John Doe", ("Jane Smith", "John Doe")),
    ("Jane Smith and John Doe", ("Jane Smith", "John Doe")),
    ("Jane Smith & John Doe & Eve Roe", ("Jane Smith", "John Doe", "Eve Roe")),
    ("Jane Smith, John Doe, and Eve Roe", ("Jane Smith", "John Doe", "Eve Roe")),
    ("Jane Smith (jane@example.org)", ("Jane Smith",)),
    ("Jane Smith1,2, John Doe3", ("Jane Smith", "John Doe")),
    ("", ()),
])
def test_split_authors(raw, expected):
    assert split_authors(raw) == expected


@pytest.mark.parametrize(("notice", "year"), [
    ("© 2019 Synthetic Publishing", 2019),
    ("Copyright 2015 The Authors", 2015),
    ("Published online: 12 March 2021", 2021),
    ("Received 3 May 2018; Accepted 10 June 2018; Published 3 July 2019", 2019),
    ("Received 3 May 2018; Accepted 10 June 2018", 2018),
])
def test_year_from_publication_notices(notice, year):
    items = [text("Title", 0, 1), {"type": "footer", "text": notice, "page_idx": 0}]
    assert build(items).metadata.year == year


def test_body_prose_about_other_years_does_not_set_the_year():
    items = [text("Title", 0, 1), text("The result was first published in 1859 and is long disputed since then by many.", 0)]
    assert build(items).metadata.year is None


@pytest.mark.parametrize("sample", [
    "The committee reviewed the proposal carefully and decided that the experiment should continue "
    "for another year, because the preliminary results were encouraging and the costs were modest.",
    "Комитет внимательно рассмотрел предложение и решил, что эксперимент следует продолжить ещё "
    "один год, поскольку предварительные результаты были обнадёживающими, а затраты невелики.",
    "Výbor starostlivo posúdil návrh a rozhodol, že experiment by mal pokračovať ešte jeden rok, "
    "pretože predbežné výsledky boli povzbudivé a náklady boli primerané potrebám výskumu.",
    "Der Ausschuss prüfte den Vorschlag sorgfältig und beschloss, das Experiment um ein weiteres Jahr "
    "fortzusetzen, weil die vorläufigen Ergebnisse ermutigend und die Kosten bescheiden waren.",
    "Le comité a examiné attentivement la proposition et a décidé que l'expérience devait se poursuivre "
    "encore un an, parce que les résultats préliminaires étaient encourageants et les coûts modestes.",
], ids=["english", "russian", "slovak", "german", "french"])
def test_document_language_is_not_inferred_from_long_body_text(sample):
    metadata = build([text(sample * 100)]).metadata
    assert metadata.language is None
    assert metadata.source_of("language") == "none"


@pytest.mark.parametrize("language", [None, "", "  ", []])
def test_empty_sidecar_language_stays_unknown_with_long_text(tmp_path, language):
    path = tmp_path / "paper.pdf.metadata.json"
    path.write_text(json.dumps({"language": language}), encoding="utf-8")
    metadata = build(FRONT, sidecar=read_sidecar(path)).metadata
    assert metadata.language is None
    assert metadata.source_of("language") == "none"


# --- PDF metadata --------------------------------------------------------------------

def make_pdf(path, **metadata):
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/" + key[0].upper() + key[1:]: value for key, value in metadata.items()})
    with open(path, "wb") as stream:
        writer.write(stream)


def test_pdf_metadata_is_read(tmp_path):
    path = tmp_path / "a.pdf"
    make_pdf(path, title="Synthetic PDF Title", author="Jane Smith; John Doe", creationDate="D:20170304120000Z",
             subject="doi:10.5555/pdf.meta")
    info = read_pdf_metadata(path)
    assert info == PdfInfo("Synthetic PDF Title", ("Jane Smith", "John Doe"), 2017, "10.5555/pdf.meta")


def test_pdf_metadata_garbage_is_ignored(tmp_path):
    path = tmp_path / "junk.pdf"
    make_pdf(path, title="Microsoft Word - draft.docx", author="admin", creationDate="D:99")
    assert read_pdf_metadata(path) == PdfInfo()


@pytest.mark.parametrize("title", [
    "PowerPoint Presentation", "Slide 1", "Layout 1", "Adobe Acrobat Document", "stdin", "Untitled-1",
    "arXiv:2101.00001v1 [cs.CL] 1 Jan 2021", "report.pdf", "Microsoft Word - x",
])
def test_pdf_placeholder_titles_are_ignored(tmp_path, title):
    path = tmp_path / "a.pdf"
    make_pdf(path, title=title)
    assert read_pdf_metadata(path).title is None


@pytest.mark.parametrize("author", ["Microsoft Office User", "Acrobat Distiller", "PDFCreator", "PC", "Windows User"])
def test_pdf_placeholder_authors_are_ignored(tmp_path, author):
    path = tmp_path / "a.pdf"
    make_pdf(path, author=author)
    assert read_pdf_metadata(path).authors == ()


@pytest.mark.parametrize(("created", "year"), [
    ("D:19700101000000Z", None),                 # the epoch default of a tool that never set a date
    ("D:19921231000000Z", None),                 # before PDF existed
    ("D:20170304120000+01'00'", 2017),
    ("D:20990101000000Z", None),                 # in the future
])
def test_pdf_creation_year_rejects_placeholders(tmp_path, created, year):
    path = tmp_path / "a.pdf"
    make_pdf(path, title="Synthetic PDF Title", creationDate=created)
    assert read_pdf_metadata(path).created_year == year


def test_pdf_metadata_is_cleaned_like_the_body(tmp_path):
    path = tmp_path / "a.pdf"
    make_pdf(path, title="Clean" + chr(0xad) + "ed" + chr(0x1b) + "[31m Title", author="Jane" + chr(0x200b) + " Smith")
    info = read_pdf_metadata(path)
    assert chr(0xad) not in info.title and chr(0x1b) not in info.title and info.title.startswith("Cleaned")
    assert info.authors == ("Jane Smith",)


def test_encrypted_and_damaged_pdfs_give_no_information_and_no_noise(tmp_path, capfd):
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": "Secret Synthetic Title"})
    writer.encrypt("user-password")
    with open(tmp_path / "enc.pdf", "wb") as stream:
        writer.write(stream)
    make_pdf(tmp_path / "ok.pdf", title="Synthetic PDF Title")
    damaged = (tmp_path / "ok.pdf").read_bytes()
    (tmp_path / "cut.pdf").write_bytes(damaged[: len(damaged) // 2])
    (tmp_path / "garbage.pdf").write_bytes(b"%PDF-1.4\n" + b"\x00\xff" * 200 + b"\n%%EOF")
    for name in ("enc.pdf", "cut.pdf", "garbage.pdf"):
        info = read_pdf_metadata(tmp_path / name)
        assert info.title is None or name == "cut.pdf", name
    assert read_pdf_metadata(tmp_path / "enc.pdf") == PdfInfo()
    captured = capfd.readouterr()
    assert captured.err == "" and captured.out == ""


def test_pymupdf_is_not_used_by_the_documents_package():
    import pathlib
    import subprocess
    import sys

    import ragshelf.documents as package

    root = pathlib.Path(package.__file__).parent
    assert not [p.name for p in root.glob("*.py") if "pymupdf" in p.read_text(encoding="utf-8")]
    script = ("import sys, ragshelf.documents.render, ragshelf.documents.loader\n"
              "print('pymupdf' in sys.modules, 'fitz' in sys.modules)")
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["False", "False"]


def test_unreadable_or_missing_pdfs_yield_no_information(tmp_path):
    (tmp_path / "bad.pdf").write_bytes(b"this is not a pdf")
    (tmp_path / "empty.pdf").write_bytes(b"")
    assert read_pdf_metadata(tmp_path / "bad.pdf") == PdfInfo()
    assert read_pdf_metadata(tmp_path / "empty.pdf") == PdfInfo()
    assert read_pdf_metadata(tmp_path / "missing.pdf") == PdfInfo()


def test_reading_pdf_metadata_does_not_modify_the_file(tmp_path):
    path = tmp_path / "a.pdf"
    make_pdf(path, title="Synthetic PDF Title")
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    read_pdf_metadata(path)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_pdf_fills_only_what_parsed_content_lacks():
    pdf = PdfInfo("PDF Title", ("Pdf Author",), 2001, "10.5555/pdf")
    metadata = build([text(PARAGRAPH, 0)], pdf=pdf).metadata
    assert (metadata.title, metadata.authors, metadata.year, metadata.doi) == (
        "PDF Title", ("Pdf Author",), 2001, "10.5555/pdf")
    # The PDF's creation year is when the file was made: it fills the year but is labeled apart.
    assert [metadata.source_of(f) for f in ("title", "authors", "year", "doi")] == ["pdf", "pdf", "pdf-created", "pdf"]
    parsed = build(FRONT, pdf=pdf).metadata
    assert parsed.title == "Attachment in Synthetic Adults" and parsed.source_of("title") == "mineru"
    assert parsed.year == 2019 and parsed.source_of("year") == "mineru"
    # An explicit DOI in the PDF's own metadata outranks a DOI pattern in the text.
    assert parsed.doi == "10.5555/pdf" and parsed.source_of("doi") == "pdf"


# --- sidecar ---------------------------------------------------------------------------

def test_sidecar_replaces_only_the_fields_it_supplies():
    sidecar = {"title": "Corrected Title", "year": 2020}
    metadata = build(FRONT, sidecar=read_sidecar_from(sidecar)).metadata
    assert (metadata.title, metadata.year) == ("Corrected Title", 2020)
    assert metadata.source_of("title") == "sidecar" and metadata.source_of("year") == "sidecar"
    # Everything else is still extracted.
    assert metadata.authors == ("Jane Q. Smith", "John Doe", "Maria Novak") and metadata.source_of("authors") == "mineru"
    assert metadata.doi == "10.1234/abc.def-9(1)" and metadata.source_of("doi") == "doi-pattern"
    assert metadata.language is None and metadata.source_of("language") == "none"


def test_every_field_can_be_overridden_by_the_sidecar():
    sidecar = read_sidecar_from({"title": "T", "authors": ["A One", "B Two"], "year": "2001", "doi": "https://doi.org/10.1000/X.1",
                                 "language": "SK"})
    metadata = build(FRONT, sidecar=sidecar).metadata
    assert (metadata.title, metadata.authors, metadata.year, metadata.doi, metadata.language) == (
        "T", ("A One", "B Two"), 2001, "10.1000/x.1", "sk")
    assert {source for _, source in metadata.sources} == {"sidecar"}


def test_empty_sidecar_values_do_not_override():
    sidecar = read_sidecar_from({"title": "", "authors": [], "year": None, "doi": "  ", "language": ""})
    assert sidecar == {}
    assert build(FRONT, sidecar=sidecar).metadata.title == "Attachment in Synthetic Adults"


def read_sidecar_from(data):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "x.pdf.metadata.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return read_sidecar(path)


def test_sidecar_accepts_the_prototype_shape_and_aliases(tmp_path):
    path = tmp_path / "a.pdf.metadata.json"
    path.write_text(json.dumps({"authors": "Smith, J.; Doe, A.", "year": "2014", "extra": {"ignored": True},
                                "Author": "Ignored Alias"}), encoding="utf-8")
    assert read_sidecar(path) == {"authors": ("Smith, J.", "Doe, A."), "year": 2014}
    path.write_text(json.dumps({"author": ["Only Alias"], "lang": "RU"}), encoding="utf-8")
    assert read_sidecar(path) == {"authors": ("Only Alias",), "language": "ru"}


@pytest.mark.parametrize("key", ["date", "published", "publication_year", "created", "note"])
def test_unknown_sidecar_keys_are_ignored_even_when_they_look_like_a_year(tmp_path, key):
    # Only `year` is the year: another key (a journal named in "published") must not fail the document.
    path = tmp_path / "a.pdf.metadata.json"
    path.write_text(json.dumps({"title": "T", key: "Nature"}), encoding="utf-8")
    assert read_sidecar(path) == {"title": "T"}


@pytest.mark.parametrize(("given", "language"), [
    ("en", "en"), ("EN", "en"), ("en_US", "en"), ("en-GB", "en"), ("English", "en"), ("ru", "ru"),
    ("Slovak", "sk"), ("zh-CN", "zh"), ("tlh", "tlh"), ("Klingon", "klingon"),
])
def test_sidecar_language_is_normalized_and_used_with_sidecar_provenance(tmp_path, given, language):
    path = tmp_path / "a.pdf.metadata.json"
    path.write_text(json.dumps({"language": given}), encoding="utf-8")
    sidecar = read_sidecar(path)
    assert sidecar == {"language": language}
    metadata = build(FRONT, sidecar=sidecar).metadata
    assert metadata.language == language
    assert metadata.source_of("language") == "sidecar"


def test_sidecar_with_a_byte_order_mark_is_read(tmp_path):
    path = tmp_path / "a.pdf.metadata.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps({"title": "T"}).encode("utf-8"))
    assert read_sidecar(path) == {"title": "T"}


def test_missing_sidecar_is_not_an_error(tmp_path):
    assert read_sidecar(tmp_path / "nope.metadata.json") == {}
    assert sidecar_path(tmp_path / "dir" / "My Paper.pdf").name == "My Paper.pdf.metadata.json"


@pytest.mark.parametrize(("content", "message"), [
    ('{"title": "SECRETTITLE", ', "invalid JSON at line 1"),
    ('["SECRETTITLE"]', "top level must be a JSON object"),
    ('{"year": "SECRETYEAR"}', "field 'year' is not a valid year"),
    ('{"year": 12}', "field 'year' is not a valid year"),
    ('{"year": true}', "field 'year' is not a valid year"),
    ('{"doi": "SECRETDOI"}', "field 'doi' is not a valid DOI"),
    ('{"title": 5}', "field 'title' must be a string"),
    ('{"language": 5}', "field 'language' must be a string"),
    ('{"authors": [1, "SECRET"]}', "field 'authors' must be a string or a list of strings"),
])
def test_malformed_sidecars_name_the_file_and_never_quote_the_content(tmp_path, content, message):
    path = tmp_path / "paper.pdf.metadata.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(MetadataError) as raised:
        read_sidecar(path)
    assert "paper.pdf.metadata.json" in str(raised.value) and message in str(raised.value)
    assert "SECRET" not in str(raised.value) and str(tmp_path) not in str(raised.value)


def test_sidecar_that_is_not_utf8_is_a_clear_error(tmp_path):
    path = tmp_path / "paper.pdf.metadata.json"
    path.write_bytes(b'{"title": "\xff\xfe"}')
    with pytest.raises(MetadataError, match="paper.pdf.metadata.json: cannot be read as UTF-8"):
        read_sidecar(path)


# --- sidecar authors are the user's words ---------------------------------------------------

@pytest.mark.parametrize(("raw", "expected"), [
    # An organisational author and a long compound name are kept whole, never dropped.
    ("American Psychological Association Task Force on Evidence-Based Practice",
     ("American Psychological Association Task Force on Evidence-Based Practice",)),
    ("Juan Carlos de la Cruz y Gomez Perez", ("Juan Carlos de la Cruz y Gomez Perez",)),
    # "Last, First, Last, First" and initials: pairs stay together.
    ("Smith, J., Jones, K.", ("Smith, J.", "Jones, K.")),
    ("Smith, J. K., Jones, K.", ("Smith, J. K.", "Jones, K.")),
    ("Smith, John", ("Smith, John",)),
    # A suffix stays with its author, parentheses are kept.
    ("Martin Luther King, Jr.", ("Martin Luther King, Jr.",)),
    ("Dr. John Smith, PhD", ("Dr. John Smith, PhD",)),
    ("J. Smith (Harvard), K. Jones (MIT)", ("J. Smith (Harvard)", "K. Jones (MIT)")),
    ("A. Author (Harvard, MA), B. Writer", ("A. Author (Harvard, MA)", "B. Writer")),
    # Clear separators.
    ("Jane Smith, John Doe", ("Jane Smith", "John Doe")),
    ("Jane Smith and John Doe", ("Jane Smith", "John Doe")),
    ("Jane Smith & John Doe", ("Jane Smith", "John Doe")),
    ("Jane Smith, John Doe, and Eve Roe", ("Jane Smith", "John Doe", "Eve Roe")),
    ("Smith, J.; Doe, A.", ("Smith, J.", "Doe, A.")),
    ("Иван Петров и Анна Сидорова", ("Иван Петров", "Анна Сидорова")),
    # A comma list that cannot be told from "Last, First" parts stays one author.
    ("Plato, Aristotle", ("Plato, Aristotle",)),
])
def test_sidecar_authors_string_is_taken_verbatim(raw, expected):
    from ragshelf.documents.metadata import split_sidecar_authors

    assert split_sidecar_authors(raw) == expected


def test_a_sidecar_author_string_always_overrides_and_reports_the_sidecar():
    name = "American Psychological Association Task Force on Evidence-Based Practice"
    metadata = build(FRONT, sidecar=read_sidecar_from({"authors": name})).metadata
    assert metadata.authors == (name,) and metadata.source_of("authors") == "sidecar"


def test_sidecar_author_string_and_list_forms_agree():
    for names in (["Smith, J.", "Jones, K."], ["Jane Smith", "John Doe"]):
        as_list = read_sidecar_from({"authors": names})
        as_text = read_sidecar_from({"authors": "; ".join(names)})
        assert as_list == as_text == {"authors": tuple(names)}


def test_a_sidecar_author_value_that_cannot_be_used_is_an_error_not_a_fallback(tmp_path):
    path = tmp_path / "a.pdf.metadata.json"
    path.write_text(json.dumps({"authors": ";;"}), encoding="utf-8")
    with pytest.raises(MetadataError, match="field 'authors' has no author name"):
        read_sidecar(path)


@pytest.mark.parametrize(("raw", "expected"), [
    ("Smith, J., Jones, K.", ("Smith, J.", "Jones, K.")),
    ("Smith J., Jones K.", ("Smith J.", "Jones K.")),
    ("Dr. John Smith, PhD", ("Dr. John Smith, PhD",)),
    ("Martin Luther King, Jr.", ("Martin Luther King, Jr.",)),
    ("Jane Smith, John Doe, Eve Roe", ("Jane Smith", "John Doe", "Eve Roe")),
])
def test_last_first_initials_format_is_not_split_into_fragments(raw, expected):
    assert split_authors(raw) == expected


# --- titles that start with a section word ---------------------------------------------------

@pytest.mark.parametrize("title", [
    "Introduction to Algorithms", "Abstract Algebra", "Resume Screening with Transformers",
    "Keywords Extraction from Texts", "References to Violence in Media", "Contents of the Universe",
    "1. Introduction to Machine Learning",
])
def test_a_title_that_starts_with_a_section_word_is_still_a_title_with_its_authors(title):
    metadata = build([text(title, 0, 1), text("Jane Smith, John Doe", 0)]).metadata
    assert metadata.title == title and metadata.authors == ("Jane Smith", "John Doe")


@pytest.mark.parametrize("heading", [
    "Abstract", "ABSTRACT", "Abstract:", "Abstract: we study the thing", "1 Introduction", "I. INTRODUCTION",
    "Keywords: a, b", "Contents", "Содержание", "Résumé",
])
def test_a_bare_section_name_is_still_not_a_title(heading):
    assert build([text(heading, 0, 1), text("Jane Smith, John Doe", 0)]).metadata.title is None


# --- DOI choice -----------------------------------------------------------------------------

def footnote(value, page=0):
    return {"type": "page_footnote", "text": value, "page_idx": page}


def test_a_doi_cited_in_a_footnote_does_not_beat_the_documents_own_labeled_doi():
    items = [text("Title", 0, 1), footnote("See Brown et al. doi:10.9999/cited.2015.1"),
             text("Own paper doi: 10.1000/own.2020.5 " + PARAGRAPH, 0)]
    assert build(items).metadata.doi == "10.1000/own.2020.5"


def test_a_footnote_doi_alone_is_not_the_documents_doi():
    assert build([text("Title", 0, 1), footnote("See doi:10.9999/cited.2015.1"), text(PARAGRAPH, 0)]).metadata.doi is None


def test_a_doi_in_header_or_footer_furniture_is_the_documents_own():
    items = [text("Title", 0, 1), text("Prior work: doi:10.9999/cited.1 " + PARAGRAPH, 0),
             {"type": "footer", "text": "https://doi.org/10.1000/own.1", "page_idx": 0}]
    assert build(items).metadata.doi == "10.1000/own.1"


def test_a_text_that_starts_with_a_doi_label_wins_over_prose_mentions():
    items = [text("Title", 0, 1), text("Compare doi:10.9999/cited.1 " + PARAGRAPH, 0), text("DOI: 10.1000/own.1", 0)]
    assert build(items).metadata.doi == "10.1000/own.1"


def test_prose_on_the_second_page_does_not_supply_a_doi():
    items = [text("Title", 0, 1), text(PARAGRAPH, 0), text("As shown earlier (https://doi.org/10.5555/prior.1).", 1)]
    assert build(items).metadata.doi is None
    items[-1] = text("https://doi.org/10.5555/own.1", 1)
    assert build(items).metadata.doi == "10.5555/own.1"


def test_several_unlabeled_dois_on_the_first_page_give_no_doi_but_one_gives_it():
    assert build([text("Title", 0, 1), text("see 10.1111/a.1 and 10.2222/b.2 " + PARAGRAPH, 0)]).metadata.doi is None
    assert build([text("Title", 0, 1), text("see 10.1111/a.1 " + PARAGRAPH, 0)]).metadata.doi == "10.1111/a.1"


def test_a_missing_pdf_dependency_fails_loudly(tmp_path, monkeypatch):
    import sys

    monkeypatch.setitem(sys.modules, "pypdf", None)
    with pytest.raises(ImportError):
        read_pdf_metadata(tmp_path / "a.pdf")


# --- more title and author edge cases ----------------------------------------------------------

@pytest.mark.parametrize("heading", [
    "Background", "Methods", "2. Methods", "Summary", "Results", "Preface", "Einleitung", "Wstęp",
    "Введение", "1", "2019", "- 3 -",
])
def test_generic_section_names_and_headings_without_letters_are_not_titles(heading):
    assert build([text(heading, 0, 1), text("Jane Smith, John Doe", 0)]).metadata.title is None


@pytest.mark.parametrize("title", [
    "Methods: A Practical Guide", "Summary of Findings", "Background Radiation", "Results Matter",
])
def test_titles_that_start_with_a_generic_section_word_are_still_titles(title):
    assert build([text(title, 0, 1), text("Jane Smith, John Doe", 0)]).metadata.title == title


@pytest.mark.parametrize("line", [
    "Lecture Notes For Students", "Chapter One", "Technical Report Draft Version", "Report On The Synthetic Thing",
    "Working Paper Series Number Two",
])
def test_a_label_line_after_the_title_is_not_an_author_line(line):
    assert build([text("A Real Title", 0, 1), text(line, 0)]).metadata.authors == ()


@pytest.mark.parametrize("line", ["张伟 李明", "محمد علي", "田中 太郎"])
def test_authors_in_scripts_without_letter_case_are_found(line):
    assert build([text("A Title", 0, 1), text(line, 0)]).metadata.authors == (line,)


@pytest.mark.parametrize(("raw", "expected"), [
    ("Smith J.A., Jones K.B.", ("Smith J.A.", "Jones K.B.")),
    ("J. K. Rowling and A. A. Milne", ("J. K. Rowling", "A. A. Milne")),
    ("Smith.", ("Smith",)),
])
def test_initials_keep_their_final_period(raw, expected):
    assert split_authors(raw) == expected


def test_title_and_authors_are_cleaned_like_the_body_text():
    items = [text("Ti­tle with​ soft\u0007 breaks", 0, 1), text("Jane​ Smith\x07, John Doe", 0)]
    metadata = build(items).metadata
    assert metadata.title == "Title with soft breaks"
    assert metadata.authors == ("Jane Smith", "John Doe")


# --- DOI edge cases ---------------------------------------------------------------------------------

@pytest.mark.parametrize(("raw", "expected"), [
    ("https://doi.org/10.1234/abc?utm_source=x", "10.1234/abc"),
    ("10.1234/abc,10.5678/def", "10.1234/abc"),
    ("10.1000/abc;10.2000/def", "10.1000/abc"),
    ("10.1002/x.CO;2-O", "10.1002/x.co;2-o"),                    # a semicolon inside a DOI stays
    ("doi:10.1234/abc–", "10.1234/abc"),
])
def test_doi_cuts_at_a_second_doi_a_query_string_and_trailing_dashes(raw, expected):
    assert normalize_doi(raw) == expected


# --- language values --------------------------------------------------------------------------------

@pytest.mark.parametrize(("raw", "expected"), [
    ("zh-cn", "zh"), ("en_US", "en"), ("English", "en"), (" RU ", "ru"), ("pt", "pt"), ("not a language", "not a language"),
])
def test_normalize_language(raw, expected):
    from ragshelf.documents.metadata import normalize_language

    assert normalize_language(raw) == expected


def test_the_pdf_creation_year_is_a_weaker_source_than_parsed_content():
    pdf = PdfInfo(None, (), 2010, None)
    assert build([text(PARAGRAPH, 0)], pdf=pdf).metadata.source_of("year") == "pdf-created"
    parsed = build(FRONT, pdf=pdf).metadata
    assert parsed.year == 2019 and parsed.source_of("year") == "mineru"
    assert build([text(PARAGRAPH, 0)], pdf=pdf, sidecar={"year": 1999}).metadata.source_of("year") == "sidecar"


# --- review round 2: the affiliation filter must not reject names -------------------------------------------

@pytest.mark.parametrize(("line", "authors"), [
    ("Gustav Svensson, Anna Berg", ("Gustav Svensson", "Anna Berg")),
    ("Gustavo Pérez, María López", ("Gustavo Pérez", "María López")),
    ("Anna Gustavsson and Karl Berg", ("Anna Gustavsson", "Karl Berg")),
    ("Ustav Patel, Rao Kumar", ("Ustav Patel", "Rao Kumar")),
    ("Jane Smith (jane@x.org), John Doe (john@x.org)", ("Jane Smith", "John Doe")),
    ("Jane Smith jane@x.org", ("Jane Smith",)),
    ("Jane Smith <jane@x.org>, John Doe <john@x.org>", ("Jane Smith", "John Doe")),
])
def test_names_that_contain_an_affiliation_fragment_or_an_email_are_still_authors(line, authors):
    assert build([text("A Title", 0, 1), text(line, 0)]).metadata.authors == authors


@pytest.mark.parametrize("line", [
    "Ústav informatiky SAV, Bratislava",
    "Ustav experimentalnej fyziky SAV",
    "Z ústavu pre výskum",
    "Jane Smith (University of Oxford), John Doe",
    "Department of Things",
    "jane@x.org, john@x.org",
    "https://example.org/people Jane Smith",
])
def test_affiliation_and_contact_lines_are_still_not_authors(line):
    assert build([text("A Title", 0, 1), text(line, 0)]).metadata.authors == ()
