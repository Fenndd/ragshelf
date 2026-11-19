"""Plain Markdown/text inputs (the parse cache's passthrough bundles)."""

import pytest

from ragshelf.documents import build_document
from ragshelf.documents.markdown import markdown_items

SOURCE = """\
# Synthetic Note

Intro paragraph that wraps across two
lines and has an exam-
ple of a split word.

## Methods

- first point
- second point
  continued here
1. numbered one
2. numbered two

| a | b |
|---|---|
| 1 | 2 |

Table 1. Synthetic counts

$$
x = y + 1
$$

```python
def f():
    return 1
```

![figure](images/one.png)

Figure 2: A synthetic figure.

> quoted line

## References

[1] Smith, J. (2019). Foo. Journal, 1, 1-2.
"""


def build(markdown):
    return build_document(markdown_items(markdown), doc_id="n.md", content_hash="0" * 64)


def test_markdown_is_split_into_typed_blocks_on_one_logical_page():
    document = build(SOURCE)
    assert [(b.type, b.level, b.text) for b in document.blocks] == [
        ("heading", 1, "Synthetic Note"),
        ("paragraph", None, "Intro paragraph that wraps across two lines and has an example of a split word."),
        ("heading", 2, "Methods"),
        ("list", None, "first point\nsecond point continued here"),
        ("list", None, "1. numbered one\n2. numbered two"),
        ("table", None, "| a | b |\n|---|---|\n| 1 | 2 |"),
        ("caption", None, "Table 1. Synthetic counts"),
        ("equation", None, "x = y + 1"),
        ("code", None, "def f():\n    return 1"),
        ("caption", None, "Figure 2: A synthetic figure."),
        ("paragraph", None, "quoted line"),
    ]
    assert {b.page for b in document.blocks} == {1} and document.page_count == 1
    assert [b.text for b in document.references] == ["References", "[1] Smith, J. (2019). Foo. Journal, 1, 1-2."]
    assert document.metadata.title == "Synthetic Note" and document.metadata.source_of("title") == "mineru"


def test_plain_text_without_markup_is_paragraphs():
    document = build("First paragraph\nstill first.\n\nSecond paragraph.\n")
    assert [(b.type, b.text) for b in document.blocks] == [
        ("paragraph", "First paragraph still first."), ("paragraph", "Second paragraph.")]


def test_unclosed_fence_runs_to_the_end_and_empty_input_is_empty():
    document = build("Text\n\n```\ncode line\nmore")
    assert [(b.type, b.text) for b in document.blocks] == [("paragraph", "Text"), ("code", "code line\nmore")]
    assert markdown_items("") == [] and markdown_items("\n\n  \n") == []


def test_windows_line_endings_are_tolerated():
    document = build("# Title\r\n\r\nBody text.\r\n")
    assert [b.text for b in document.blocks] == ["Title", "Body text."]


def test_a_leading_bom_is_tolerated():
    document = build("﻿# Title\n\nBody text.\n")
    assert [(b.type, b.level, b.text) for b in document.blocks] == [("heading", 1, "Title"), ("paragraph", None, "Body text.")]


def test_setext_headings_are_headings():
    document = build("Setext Title\n============\n\nBody text.\n\nA Two-Line\nSection\n-------\n\nMore text.\n")
    assert [(b.type, b.level, b.text) for b in document.blocks] == [
        ("heading", 1, "Setext Title"), ("paragraph", None, "Body text."),
        ("heading", 2, "A Two-Line Section"), ("paragraph", None, "More text.")]
    assert document.metadata.title == "Setext Title"


def test_a_rule_after_a_blank_line_is_not_a_setext_underline():
    document = build("Text.\n\n---\n\nMore text.\n\n***\n")
    assert [(b.type, b.text) for b in document.blocks] == [("paragraph", "Text."), ("paragraph", "More text.")]


def test_yaml_front_matter_is_skipped():
    document = build("---\ntitle: X\nauthor: Y\n---\n# Real Title\n\nBody.\n")
    assert [(b.type, b.text) for b in document.blocks] == [("heading", "Real Title"), ("paragraph", "Body.")]
    # Two rules around prose are not front matter.
    kept = build("---\n\nJust prose between rules.\n\n---\n\nAfter.\n")
    assert [b.text for b in kept.blocks] == ["Just prose between rules.", "After."]


def test_a_wrapped_line_that_starts_with_a_number_stays_in_its_paragraph():
    document = build("The study was conducted in a hospital with\n12. patients were enrolled. The second\n"
                     "3) arm was larger than planned.\n")
    assert [(b.type, b.text) for b in document.blocks] == [(
        "paragraph", "The study was conducted in a hospital with 12. patients were enrolled. The second "
                     "3) arm was larger than planned.")]


def test_one_dot_and_bullets_still_interrupt_a_paragraph():
    document = build("Steps follow:\n1. open it\n2. close it\n\nNotes:\n- one\n- two\n")
    assert [(b.type, b.text) for b in document.blocks] == [
        ("paragraph", "Steps follow:"), ("list", "1. open it\n2. close it"), ("paragraph", "Notes:"), ("list", "one\ntwo")]


@pytest.mark.parametrize("marker", [".", ")"])
@pytest.mark.parametrize("initials", ["", ", J."])
def test_numbered_bibliography_under_ambiguous_heading_keeps_its_evidence(marker, initials):
    entries = tuple(f"{n}{marker} {author}{initials} ({year}). {title} work." for n, author, year, title in [
        (1, "Smith", 2020, "First"), (2, "Jones", 2021, "Second"), (3, "Brown", 2022, "Third")])
    document = build("# Note\n\nBody.\n\n## Literature\n\n" + "\n".join(entries))
    assert [b.text for b in document.blocks] == ["Note", "Body."]
    assert [b.text for b in document.references] == ["Literature", "\n".join(entries)]
    assert document.references[1].items == entries
    assert document.report.reference_like_in_body == 0


def test_ordinary_numbered_steps_under_ambiguous_heading_remain_in_body():
    document = build("# Note\n\n## Literature\n\n1. Open the book.\n2. Read the chapter.\n3. Close it.")
    assert document.references == ()
    assert document.blocks[-1].items == ("1. Open the book.", "2. Read the chapter.", "3. Close it.")
    assert document.report.reference_like_in_body == 0


def test_retained_numbered_citations_are_counted_in_body_leakage():
    document = build("# Note\n\n## Discussion\n\n1. Smith, J. (2020). First work.\n"
                     "2. Jones, J. (2021). Second work.\n\nThese are discussed in the body.")
    assert document.references == ()
    assert document.blocks[2].items == ("1. Smith, J. (2020). First work.",
                                        "2. Jones, J. (2021). Second work.")
    assert document.report.reference_like_in_body == 2


def test_ordered_list_continuations_keep_numbering_and_join_wrapped_text():
    document = build("# Note\n\n4) Open the book\n   and turn the page.\n5) Read the chapter.")
    assert document.blocks[-1].items == ("4) Open the book and turn the page.", "5) Read the chapter.")


@pytest.mark.parametrize("table", [
    "Name | Value\n--- | ---\na | b",
    "| Name | Value |\n| --- | --- |\n| a | b |",
    "Name | Value\n:--- | ---:\na | b",
])
def test_pipe_tables_preserve_rows_with_or_without_outer_pipes(table):
    document = build("# Note\n\n" + table)
    assert [(b.type, b.text) for b in document.blocks] == [("heading", "Note"), ("table", table)]


@pytest.mark.parametrize("prose", [
    "Name | Value\ncontinues as ordinary prose.",
    "Use a | b for alternatives.\n\nAnother paragraph.",
    "Name | Value\n--- | invalid\na | b",
])
def test_prose_with_pipes_is_not_a_table(prose):
    document = build("# Note\n\n" + prose)
    assert all(b.type == "paragraph" for b in document.blocks[1:])


def test_setext_heading_with_a_pipe_is_not_a_table():
    document = build("# Note\n\nName | Value\n---")
    assert [(b.type, b.level, b.text) for b in document.blocks] == [
        ("heading", 1, "Note"), ("heading", 2, "Name | Value")]
