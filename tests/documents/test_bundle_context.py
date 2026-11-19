"""HTML bundles must match their current source and consumed resources."""

import json
import os
import subprocess
import sys
from io import BytesIO

import pytest

from ragshelf.documents import ParseCacheMissingError, load_document, load_library
from ragshelf.parse import parse_library


HTML = ('<html><head><link rel="stylesheet" href="style.css"></head><body>'
        '<p class="hidden">Synthetic hidden text</p><p>Visible text.</p>'
        '<img src="missing.png"></body></html>')


class NativeHtmlBackend:
    def descriptor(self, suffix):
        return {"name": "native-html-context-test", "version": 1}

    def parse(self, source, output, *, original):
        from docvortex.analyzers.native.html.converter import HtmlConverter
        from docvortex.document.contracts import HtmlSourceContext

        converter = HtmlConverter()
        converter.convert(BytesIO(source.read_bytes()), source_context=HtmlSourceContext(
            source_uri=original.as_uri(), local_resource_root=original.parent))
        text = json.dumps(converter.pages, ensure_ascii=False)
        (output / "markdown.md").write_text(text, encoding="utf-8")
        (output / "content_list.json").write_text(json.dumps([
            {"type": "text", "text": text, "page_idx": 0}]), encoding="utf-8")

    def close(self):
        pass


def parsed(library):
    report = parse_library(library.settings(), backend=NativeHtmlBackend())
    assert report.failed == 0
    return report


def body(document):
    return "\n".join(block.text for block in document.blocks)


@pytest.mark.parametrize("suffix", [".html", ".HTM", ".shtml"])
def test_identical_html_bytes_load_their_own_context(library, suffix):
    for folder, display in (("a", "none"), ("b", "block")):
        source, _ = library.add(f"{folder}/document{suffix}", HTML, bundle=False)
        (source.parent / "style.css").write_text(f".hidden {{display:{display}}}")
    report = parsed(library)
    assert report.parsed == 2
    for index, outcome in enumerate(report.outcomes, 1):
        os.utime(outcome.cache_path / "manifest.json", (index * 1000, index * 1000))
    results = load_library(library.settings())
    assert all(result.error is None for result in results)
    first, second = (result.document for result in results)
    assert "Synthetic hidden text" not in body(first)
    assert "Synthetic hidden text" in body(second)
    assert first.content_hash == second.content_hash
    assert first.parser_key == report.outcomes[0].cache_path.name
    assert second.parser_key == report.outcomes[1].cache_path.name
    assert first.parser_key != second.parser_key


@pytest.mark.parametrize("change", ["stylesheet", "missing-image"])
def test_changed_html_dependency_requires_an_applicable_bundle(library, change):
    source, _ = library.add("document.html", HTML, bundle=False)
    css = source.parent / "style.css"
    css.write_text(".hidden {display:block}")
    old = parsed(library).outcomes[0].cache_path
    if change == "stylesheet":
        css.write_text(".hidden {display:none}")
    else:
        (source.parent / "missing.png").write_bytes(b"synthetic image")
    with pytest.raises(ParseCacheMissingError, match="ingest --parse-only"):
        load_document(library.settings(), "document.html")
    result = next(result for result in load_library(library.settings())
                  if result.source.doc_id == "document.html")
    assert result.document is None and "ingest --parse-only" in result.error
    new = parsed(library).outcomes[0].cache_path
    assert new != old
    # Recency must not make the stale bundle applicable again.
    os.utime(old / "manifest.json", (9000000000, 9000000000))
    document = load_document(library.settings(), "document.html")
    assert document.parser_key == new.name
    assert ("Synthetic hidden text" in body(document)) == (change != "stylesheet")


def test_html_bundle_without_source_context_is_not_applicable(library):
    library.add("document.html", HTML, items=[
        {"type": "text", "text": "Context-free stale output", "page_idx": 0}])
    with pytest.raises(ParseCacheMissingError):
        load_document(library.settings(), "document.html")


def test_unconsumed_neighbor_does_not_invalidate_html_bundle(library):
    source, _ = library.add("document.html", HTML, bundle=False)
    entry = parsed(library).outcomes[0].cache_path
    (source.parent / "unrelated.bin").write_bytes(b"irrelevant")
    assert load_document(library.settings(), "document.html").parser_key == entry.name


def test_dependency_change_during_bundle_validation_is_rejected(library, monkeypatch):
    import ragshelf.documents.loader as loader

    source, _ = library.add("document.html", HTML, bundle=False)
    css = source.parent / "style.css"
    css.write_text(".hidden {display:block}")
    parsed(library)
    validate = loader.cache_valid

    def mutate(*args):
        valid = validate(*args)
        css.write_text(".hidden {display:none}")
        return valid

    monkeypatch.setattr(loader, "cache_valid", mutate)
    with pytest.raises(ParseCacheMissingError):
        load_document(library.settings(), "document.html")


@pytest.mark.parametrize("suffix", [".html", ".txt"])
@pytest.mark.parametrize("bulk", [False, True])
def test_source_bytes_change_during_bundle_validation_is_rejected(library, monkeypatch, suffix, bulk):
    import ragshelf.documents.loader as loader
    from ragshelf.parse import content_hash

    name = "document" + suffix
    if suffix == ".html":
        source, _ = library.add(name, HTML, bundle=False)
        parsed(library)
        replacement = HTML.replace("Visible text.", "Changed source text.")
    else:
        source, _ = library.add_text(name, "Original synthetic text.")
        replacement = "Changed synthetic text."
    original_hash = content_hash(source)
    validate = loader.cache_valid

    def mutate(*args):
        valid = validate(*args)
        assert valid
        source.write_text(replacement, encoding="utf-8")
        return valid

    monkeypatch.setattr(loader, "cache_valid", mutate)
    if bulk:
        result, = load_library(library.settings())
        assert result.document is None
        assert "ingest --parse-only" in result.error
    else:
        with pytest.raises(ParseCacheMissingError, match="ingest --parse-only"):
            load_document(library.settings(), name)
    assert content_hash(source) != original_hash


def test_html_inspection_keeps_model_runtimes_unloaded(library):
    library.add("document.html", HTML, bundle=False)
    parsed(library)
    code = '''
import sys
from ragshelf.cli import main
assert main(["inspect", "--all"]) == 0
assert main(["inspect", "document.html"]) == 0
for name in ("torch", "transformers", "onnxruntime", "mineru.parser", "mineru.model", "pymupdf"):
    assert not any(key == name or key.startswith(name + ".") for key in sys.modules), name
'''
    result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
