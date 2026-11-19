"""Loading from the parse cache and `ragshelf inspect`."""

import os
import subprocess
import sys

import pytest

from ragshelf.cli import main
from ragshelf.documents import (
    ParseCacheMissingError,
    UnknownDocumentError,
    find_source,
    load_document,
    load_library,
    locate_bundle,
)
from ragshelf.parse import content_hash

PARAGRAPH = "A synthetic body paragraph with enough detail to describe the experiment and its preliminary results."


def text(value, page=0, level=None):
    item = {"type": "text", "text": value, "page_idx": page}
    if level is not None:
        item["text_level"] = level
    return item


def write_pdf(path, **metadata):
    """A one-page PDF with the given Info entries (`title=` becomes `/Title`)."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    if metadata:
        writer.add_metadata({"/" + key[0].upper() + key[1:]: value for key, value in metadata.items()})
    with open(path, "wb") as stream:
        writer.write(stream)


def paper_items(title="Synthetic Paper"):
    return [text(title, 0, 1), text("Jane Smith1, John Doe2", 0), text("Introduction", 0, 2), text(PARAGRAPH, 0),
            text("Methods", 1, 2), text("Participants", 1, 3), text(PARAGRAPH, 1),
            text("References", 2, 2),
            {"type": "list", "sub_type": "ref_text", "list_items": ["Smith (2019). Foo."], "page_idx": 2}]


def test_load_document_from_the_cache_applies_the_sidecar(library):
    library.add("papers/a.pdf", items=paper_items(), sidecar={"year": 1999})
    document = load_document(library.settings(), "papers/a.pdf")
    assert document.doc_id == "papers/a.pdf" and len(document.content_hash) == 64
    assert document.metadata.title == "Synthetic Paper" and document.metadata.source_of("title") == "mineru"
    assert document.metadata.year == 1999 and document.metadata.source_of("year") == "sidecar"
    assert len(document.references) == 2 and document.page_count == 3
    assert document.parser_key


def test_pdf_metadata_of_the_original_is_used(library):
    path, _ = library.add("a.pdf", items=[text(PARAGRAPH)])
    write_pdf(path, title="Metadata Title", author="Pat Quill")
    library.bundle(content_hash(path), [text(PARAGRAPH)])
    document = load_document(library.settings(), "a.pdf")
    assert (document.metadata.title, document.metadata.authors) == ("Metadata Title", ("Pat Quill",))
    assert document.metadata.source_of("title") == "pdf"


def test_identity_follows_the_parse_stage(library):
    library.add("deep/folder/Mixed Case.PDF", items=paper_items())
    assert find_source(library.settings(), "deep/folder/Mixed Case.PDF").doc_id == "deep/folder/Mixed Case.PDF"
    for wrong in ("deep/folder/mixed case.pdf", "Mixed Case.PDF", "deep\\folder\\Mixed Case.PDF", "", "../x.pdf"):
        with pytest.raises(UnknownDocumentError):
            find_source(library.settings(), wrong)


def test_missing_or_invalid_cache_is_reported(library):
    library.add("nocache.pdf", items=paper_items(), bundle=False)
    with pytest.raises(ParseCacheMissingError, match="ragshelf ingest --parse-only"):
        load_document(library.settings(), "nocache.pdf")
    path, digest = library.add("tampered.pdf", b"other bytes", items=paper_items())
    entry = next((library.cache / "parse" / digest).iterdir())
    (entry / "content_list.json").write_text("[]", encoding="utf-8")  # no longer matches the manifest
    with pytest.raises(ParseCacheMissingError):
        load_document(library.settings(), "tampered.pdf")


def test_newest_valid_bundle_wins_and_invalid_ones_are_ignored(library):
    path, digest = library.add("a.pdf", items=[text("Old Title", 0, 1)])
    old = next((library.cache / "parse" / digest).iterdir())
    newer = {"name": "mineru", "version": "newer", "adapter_version": 1, "format": ".pdf"}
    new = library.bundle(digest, [text("New Title", 0, 1)], descriptor=newer)
    os.utime(old / "manifest.json", (1, 1))
    assert load_document(library.settings(), "a.pdf").metadata.title == "New Title"
    (new / "markdown.md").write_text("tampered", encoding="utf-8")
    assert load_document(library.settings(), "a.pdf").metadata.title == "Old Title"
    assert locate_bundle(library.settings(), find_source(library.settings(), "a.pdf")) == old


def test_unchanged_bytes_share_the_cache_and_changed_bytes_need_a_new_one(library):
    library.add("a.pdf", b"v1", items=paper_items())
    library.add("copy.pdf", b"v1", items=paper_items("Other"), bundle=False)
    assert load_document(library.settings(), "copy.pdf").metadata.title == "Synthetic Paper"
    (library.root / "a.pdf").write_bytes(b"v2")
    with pytest.raises(ParseCacheMissingError):
        load_document(library.settings(), "a.pdf")


def test_text_passthrough_documents_are_parsed_from_markdown(library):
    library.add_text("notes/n.md", "# Note Title\n\n## Part\n\nBody of the note.\n")
    document = load_document(library.settings(), "notes/n.md")
    assert [(b.type, b.level) for b in document.blocks] == [("heading", 1), ("heading", 2), ("paragraph", None)]
    assert document.metadata.title == "Note Title"


def test_load_library_isolates_failures(library):
    library.add("good.pdf", items=paper_items())
    library.add("nocache.pdf", b"x", items=[], bundle=False)
    library.add("badsidecar.pdf", b"y", items=paper_items(), sidecar="{not json SECRETCONTENT")
    results = {r.source.doc_id: r for r in load_library(library.settings())}
    assert results["good.pdf"].document is not None and results["good.pdf"].error is None
    assert "ragshelf ingest --parse-only" in results["nocache.pdf"].error
    assert "badsidecar.pdf.metadata.json: invalid JSON" in results["badsidecar.pdf"].error
    assert "SECRETCONTENT" not in results["badsidecar.pdf"].error


# --- CLI -------------------------------------------------------------------------------

def test_inspect_prints_metadata_with_provenance_and_the_outline(library, capsys):
    library.add("papers/a.pdf", items=paper_items(), sidecar={"title": "Sidecar Title"})
    assert main(["inspect", "papers/a.pdf"]) == 0
    out = capsys.readouterr().out
    assert "doc_id: papers/a.pdf" in out
    assert "title: Sidecar Title  [sidecar]" in out
    assert "authors: Jane Smith; John Doe  [mineru]" in out
    assert "language: -  [none]" in out
    assert "year: -  [none]" in out
    # Outline: two spaces per level below 1, page numbers 1-based.
    assert ("\nOutline (4 headings):\nSynthetic Paper  (p. 1)\n  Introduction  (p. 1)\n"
            "  Methods  (p. 2)\n    Participants  (p. 2)\n") in out
    assert "References: 1 entries from p. 3" in out


def test_inspect_prints_normalized_sidecar_language(library, capsys):
    library.add("a.pdf", items=paper_items(), sidecar={"language": "SK_sk"})
    assert main(["inspect", "a.pdf"]) == 0
    assert "language: sk  [sidecar]" in capsys.readouterr().out


def test_inspect_unknown_id_is_a_clear_nonzero_error(library, capsys):
    library.add("a.pdf", items=paper_items())
    assert main(["inspect", "missing.pdf"]) == 1
    captured = capsys.readouterr()
    assert "unknown document id: 'missing.pdf'" in captured.err and captured.out == ""


def test_inspect_without_a_cache_entry_says_to_parse_first(library, capsys):
    library.add("a.pdf", items=paper_items(), bundle=False)
    assert main(["inspect", "a.pdf"]) == 1
    assert "run 'ragshelf ingest --parse-only'" in capsys.readouterr().err


def test_inspect_with_a_broken_sidecar_names_the_file_only(library, capsys):
    library.add("a.pdf", items=paper_items(), sidecar='{"title": "SECRETCONTENT",')
    assert main(["inspect", "a.pdf"]) == 1
    err = capsys.readouterr().err
    assert "a.pdf.metadata.json" in err and "SECRETCONTENT" not in err


def test_inspect_missing_library_is_an_error(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("RAGSHELF_PATHS__LIBRARY", str(tmp_path / "missing"))
    monkeypatch.setenv("RAGSHELF_PATHS__CACHE", str(tmp_path / "cache"))
    assert main(["inspect", "--all"]) == 1
    assert "FileNotFoundError" in capsys.readouterr().err


def parse_records(out):
    """`inspect --all` output as {doc_id: {field: value}}; a failed document has an `ERROR` key."""
    records = {}
    for block in out.strip().split("\n\n")[:-1]:
        header, *fields = block.splitlines()
        assert header.startswith("[") and "] " in header, header
        record = {}
        for line in fields:
            key, _, value = line.strip().partition(":")
            record[key] = value.strip()
        records[header.split("] ", 1)[1]] = record
    return records


def test_inspect_all_prints_a_record_for_every_document(library, capsys):
    library.add("one.pdf", b"1", items=paper_items("First Synthetic Paper"))
    library.add("sub/two.pdf", b"2", items=paper_items("Второй документ"), sidecar={"year": 2015, "doi": "10.1000/ABC.2"})
    library.add_text("three.md", "# Third\n\nText.\n")
    assert main(["inspect", "--all"]) == 0
    out = capsys.readouterr().out
    records = parse_records(out)
    assert set(records) == {"one.pdf", "sub/two.pdf", "three.md"}
    assert records["one.pdf"] == {"title": "First Synthetic Paper", "authors": "Jane Smith; John Doe", "year": "-", "doi": "-"}
    assert records["sub/two.pdf"] == {"title": "Второй документ", "authors": "Jane Smith; John Doe", "year": "2015",
                                      "doi": "10.1000/abc.2"}
    assert records["three.md"]["title"] == "Third" and records["three.md"]["authors"] == "-"
    assert out.rstrip().endswith("3 documents, 0 failed.")


def test_inspect_all_fails_if_any_document_fails_but_still_shows_the_rest(library, capsys):
    library.add("good.pdf", b"1", items=paper_items("Good One"))
    library.add("nocache.pdf", b"2", items=[], bundle=False)
    assert main(["inspect", "--all"]) == 1
    out = capsys.readouterr().out
    assert "Good One" in out and "ERROR: nocache.pdf: no valid parse cache entry" in out
    assert "2 documents, 1 failed." in out


def test_inspect_requires_exactly_one_of_doc_id_or_all(library, capsys):
    assert main(["inspect"]) == 2
    assert main(["inspect", "a.pdf", "--all"]) == 2
    assert capsys.readouterr().err.count("exactly one of <doc_id> or --all") == 2


def test_inspect_is_listed_in_help(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    assert "inspect" in capsys.readouterr().out


def test_inspect_never_loads_a_model_runtime_or_language_detector(library, tmp_path):
    path, digest = library.add("a.pdf", items=paper_items())
    write_pdf(path, title="Synthetic")
    library.bundle(content_hash(path), paper_items())
    library.add_text("n.md", "# Note\n\nText.\n")
    script = (
        "import sys\n"
        "from ragshelf.cli import main\n"
        "assert main(['inspect', '--all']) == 0\n"
        "assert main(['inspect', 'a.pdf']) == 0\n"
        "heavy = [m for m in ('torch', 'transformers', 'mineru.parser', 'mineru.model', 'onnxruntime', 'pymupdf', 'langdetect')\n"
        "         if m in sys.modules]\n"
        "print('HEAVY', heavy)\n"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, encoding="utf-8",
                            env=dict(os.environ), timeout=120)
    assert result.returncode == 0, result.stderr
    assert "HEAVY []" in result.stdout, result.stdout


def test_inspect_output_is_utf8_when_redirected(library, tmp_path):
    library.add("a.pdf", items=paper_items("Заголовок Ž"))
    target = tmp_path / "out.txt"
    script = "import sys\nfrom ragshelf.cli import main\nraise SystemExit(main(['inspect', '--all']))\n"
    with target.open("wb") as stream:
        result = subprocess.run([sys.executable, "-c", script], stdout=stream, stderr=subprocess.PIPE,
                                env={**os.environ, "PYTHONIOENCODING": ""}, timeout=120)
    assert result.returncode == 0, result.stderr
    assert "Заголовок Ž" in target.read_text(encoding="utf-8")


def test_inspect_all_prints_long_titles_and_author_lists_in_full(library, capsys):
    title = ("A Very Long Synthetic Title About Nothing In Particular That Goes On Well Past Fifty Characters " * 3).strip()
    names = [f"{a} {b}" for a, b in zip("Alice Bob Carol Dave Erin Frank Grace Heidi Ivan Judy Karl Liam".split(),
                                                "Smith Jones Brown Green White Black Young Hall Allen King Wright Scott".split())]
    assert len(title) > 200 and len("; ".join(names)) > 100
    library.add("long.pdf", items=[text(title, 0, 1), text(", ".join(names), 0), text(PARAGRAPH, 0)])
    assert main(["inspect", "--all"]) == 0
    out = capsys.readouterr().out
    assert title in out and "; ".join(names) in out and "…" not in out


def test_inspect_all_records_hold_the_whole_title_and_author_list(library, capsys):
    title = ("A Very Long Synthetic Title About Nothing In Particular That Goes On Well Past Fifty Characters " * 4).strip()
    first = "Alice Bob Carol Dave Erin Frank Grace Heidi Ivan Judy Karl Liam".split()
    last = "Smith Jones Brown Green White Black Young Hall Allen King Wright Scott".split()
    names = "; ".join(f"{a} {b}" for a, b in zip(first, last))
    library.add("long.pdf", items=[text(title, 0, 1), text(names.replace(";", ","), 0), text(PARAGRAPH, 0)])
    assert main(["inspect", "--all"]) == 0
    record = parse_records(capsys.readouterr().out)["long.pdf"]
    assert record["title"] == title and record["authors"] == names


def test_inspect_prints_no_control_characters_from_a_hostile_title(library, capsys):
    library.add("a.pdf", items=[text("Title\x1b[31m red\x07", 0, 1), text(PARAGRAPH, 0)],
                sidecar={"authors": "Eve\x1b]0;pwned\x07 Roe"})
    assert main(["inspect", "--all"]) == 0
    assert main(["inspect", "a.pdf"]) == 0
    out = capsys.readouterr().out
    assert "\x1b" not in out and "\x07" not in out and "Eve" in out


@pytest.mark.parametrize("controls", [
    "".join(chr(code) for code in range(0x20) if not chr(code).isspace()),
    "".join(chr(code) for code in range(0x7f, 0xa0) if not chr(code).isspace()),
    "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069",
], ids=["c0", "del-c1", "bidi"])
@pytest.mark.parametrize("selection", ["--all", "a.pdf"], ids=["all", "single"])
def test_inspect_sanitizes_sidecar_doi_controls(library, capsys, controls, selection):
    # Whitespace terminates DOI extraction; exercise all controls that can survive it.
    doi = f"10.1234/a{controls}z"
    library.add("a.pdf", items=paper_items(), sidecar={"doi": doi})
    document = load_document(library.settings(), "a.pdf")
    assert document.metadata.doi == doi
    assert document.metadata.source_of("doi") == "sidecar"

    assert main(["inspect", selection]) == 0
    out = capsys.readouterr().out
    assert all(control not in out for control in controls)
    assert f"10.1234/a{'?' * len(controls)}z" in out
    assert not any(ord(char) < 0x20 and char != "\n" or 0x7f <= ord(char) < 0xa0
                   for char in out)


def test_inspect_exits_zero_when_stdout_is_the_null_device(library):
    # On Windows the null device reports itself as a terminal with a code page that cannot hold this title.
    library.add("a.pdf", items=paper_items("Заголовок Ž 中文"))
    script = "from ragshelf.cli import main\nraise SystemExit(main(['inspect', '--all']))\n"
    result = subprocess.run([sys.executable, "-c", script], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                            env={**os.environ, "PYTHONIOENCODING": ""}, timeout=120)
    assert result.returncode == 0, result.stderr
    assert result.stderr == b""


def test_inspect_reports_an_output_failure_as_such(library, monkeypatch, capsys):
    library.add("a.pdf", items=paper_items())

    real_print = print

    def broken_print(*args, **kwargs):
        if kwargs.get("file") is None:
            raise BrokenPipeError("closed")
        real_print(*args, **kwargs)

    monkeypatch.setattr("builtins.print", broken_print)
    assert main(["inspect", "a.pdf"]) == 1
    err = capsys.readouterr().err
    assert "BrokenPipeError; could not write the output" in err and "could not load" not in err


def test_inspect_flags_reference_like_entries_left_in_the_body(library, capsys):
    cited = "12. Jones, K. (2001). A synthetic note. Journal of Examples, 4, 5-9."
    items = paper_items()[:-2] + [text(cited, 1), text(PARAGRAPH, 1)] + paper_items()[-2:]
    library.add("papers/b.pdf", items=items)
    assert main(["inspect", "papers/b.pdf"]) == 0
    out = capsys.readouterr().out
    assert "Check: 1 numbered, citation-shaped entries remain in the body" in out
    assert "Jones" not in out
    library.add("papers/c.pdf", items=paper_items())
    assert main(["inspect", "papers/c.pdf"]) == 0
    assert "Check:" not in capsys.readouterr().out
