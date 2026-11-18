from pathlib import Path

import pytest

from ragshelf.config import PathsConfig, Settings
from ragshelf.parse import parse_library
from ragshelf.parse.html import html_dependencies


HTML = b'<html><head><link rel="stylesheet" href="style.css"></head><body><p class="hidden">Synthetic hidden text</p><p>Visible text.</p><img src="missing.png"></body></html>'


class NativeHtmlBackend:
    """Use actual native conversion, without importing a GPU/model runtime."""

    def __init__(self, mutate=False):
        self.calls = 0
        self.mutate = mutate

    def descriptor(self, suffix):
        return {"name": "native-html-test", "version": 1}

    def parse(self, source, output, *, original):
        import json
        from io import BytesIO
        from docvortex.analyzers.native.html.converter import HtmlConverter
        from docvortex.document.contracts import HtmlSourceContext

        self.calls += 1
        converter = HtmlConverter()
        converter.convert(BytesIO(source.read_bytes()), source_context=HtmlSourceContext(
            source_uri=original.as_uri(), local_resource_root=original.parent))
        # Keep the full native result only in the synthetic test artifact.
        text = json.dumps(converter.pages, ensure_ascii=False)
        (output / "markdown.md").write_text(text, encoding="utf-8")
        (output / "content_list.json").write_text(json.dumps([{"type": "text", "text": text, "page_idx": 0}]), encoding="utf-8")
        if self.mutate:
            (original.parent / "style.css").write_text(".hidden {display:none}")

    def close(self):
        pass


def test_html_context_css_mutation_and_unrelated_files(tmp_path):
    library = tmp_path / "library"
    for name, css in (("a", ".hidden {display:none}"), ("b", ".hidden {display:block}")):
        folder = library / name
        folder.mkdir(parents=True)
        (folder / "document.html").write_bytes(HTML)
        (folder / "style.css").write_text(css)
    settings = Settings(paths=PathsConfig(library=library, cache=tmp_path / "cache"))
    backend = NativeHtmlBackend()
    first = parse_library(settings, backend=backend)
    assert (first.parsed, first.hits, first.failed) == (2, 0, 0)
    assert "Synthetic hidden text" not in (first.outcomes[0].cache_path / "markdown.md").read_text()
    assert "Synthetic hidden text" in (first.outcomes[1].cache_path / "markdown.md").read_text()
    assert parse_library(settings, backend=backend).hits == 2
    (library / "a/unrelated.bin").write_bytes(b"irrelevant")
    assert parse_library(settings, backend=backend).hits == 2
    (library / "b/style.css").write_text(".hidden {display:none}")
    changed = parse_library(settings, backend=backend)
    assert (changed.parsed, changed.hits) == (1, 1)
    assert "Synthetic hidden text" not in (changed.outcomes[1].cache_path / "markdown.md").read_text()


def test_missing_image_creation_and_base_href_dependency(tmp_path):
    source = tmp_path / "document.html"
    source.write_bytes(HTML.replace(b"<head>", b'<head><base href="assets/">'))
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/style.css").write_text("p {font-weight:bold}")
    first = html_dependencies(source, original=source)
    assert first["local_resources"]["assets/missing.png"] is None
    assert "assets/style.css" in first["local_resources"]
    (tmp_path / "assets/missing.png").write_bytes(b"now present, invalid synthetic image")
    assert html_dependencies(source, original=source) != first


def test_dependency_change_during_parse_never_publishes(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    (library / "document.html").write_bytes(HTML)
    (library / "style.css").write_text(".hidden {display:block}")
    settings = Settings(paths=PathsConfig(library=library, cache=tmp_path / "cache"))
    report = parse_library(settings, backend=NativeHtmlBackend(mutate=True))
    assert report.failed == 1
    assert not list((tmp_path / "cache").rglob("manifest.json"))


def test_remote_base_image_does_not_depend_on_neighbor_file(tmp_path):
    source = tmp_path / "document.html"
    source.write_bytes(b'<html><head><base href="https://example.invalid/"></head><body><p>Synthetic</p><img src="figure.png"></body></html>')
    first = html_dependencies(source, original=source)
    assert first["local_resources"] == {}
    (tmp_path / "figure.png").write_bytes(b"unrelated local image")
    assert html_dependencies(source, original=source) == first


def test_dependency_mutation_during_cache_validation_is_not_a_hit(tmp_path, monkeypatch):
    import ragshelf.parse.pipeline as pipeline

    library = tmp_path / "library"
    library.mkdir()
    (library / "document.html").write_bytes(HTML)
    css = library / "style.css"
    css.write_text(".hidden {display:block}")
    settings = Settings(paths=PathsConfig(library=library, cache=tmp_path / "cache"))
    assert parse_library(settings, backend=NativeHtmlBackend()).parsed == 1
    validate = pipeline.cache_valid

    def mutate(*args):
        valid = validate(*args)
        css.write_text(".hidden {display:none}")
        return valid

    monkeypatch.setattr(pipeline, "cache_valid", mutate)
    report = parse_library(settings, backend=NativeHtmlBackend())
    assert report.failed == 1 and report.hits == 0
