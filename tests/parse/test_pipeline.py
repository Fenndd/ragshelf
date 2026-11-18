import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ragshelf.config import ModelsConfig, PathsConfig, Settings
from ragshelf.parse import content_hash, parse_library, scan_library
from ragshelf.parse.cache import batch_lock, parser_key


class FakeParser:
    def __init__(self, version="one", fail=False, mutate=False, invalid=False):
        self.version = version
        self.fail = fail
        self.mutate = mutate
        self.invalid = invalid
        self.calls = []
        self.closed = 0

    def descriptor(self, suffix):
        return {"name": "fake", "version": self.version, "settings": {"mode": "standard"}, "format": suffix.lower()}

    def parse(self, source, output, *, original):
        self.calls.append(source.read_bytes())
        assert source != original
        (output / "markdown.md").write_text("Synthetic ![figure](images/one.png)", encoding="utf-8")
        if self.fail:
            raise RuntimeError("PRIVATE document text should not escape")
        (output / "content_list.json").write_text(json.dumps(
            [{"type": "text", "text": "Synthetic", "page_idx": -1 if self.invalid else 0}]), encoding="utf-8")
        (output / "images").mkdir()
        (output / "images/one.png").write_bytes(b"synthetic image")
        if self.mutate:
            original.write_bytes(b"changed while parsing")

    def close(self):
        self.closed += 1


@pytest.fixture
def settings(tmp_path):
    library = tmp_path / "library"
    library.mkdir()
    return Settings(paths=PathsConfig(library=library, cache=tmp_path / "cache"),
                    models=ModelsConfig(mineru_home=tmp_path / "mineru", hf_home=tmp_path / "hf"))


def put(settings, name, payload=b"synthetic PDF"):
    path = settings.paths.library / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def test_scan_nested_case_sensitive_identity_sidecars_and_formats(settings):
    put(settings, "sub/My File.PDF")
    put(settings, "doc.docx")
    put(settings, "image.png")
    put(settings, "note.md")
    put(settings, "note.txt")
    put(settings, "doc.docx.metadata.json")
    put(settings, "~$lock.docx")
    put(settings, "unsupported.bin")
    sources = scan_library(settings.paths.library)
    assert {s.doc_id for s in sources} == {"sub/My File.PDF", "doc.docx", "image.png", "note.md", "note.txt"}
    assert all(s.content_hash == hashlib.sha256(b"synthetic PDF").hexdigest() for s in sources)


def test_missing_library_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        scan_library(tmp_path / "missing")


def test_sha256_uses_bytes(tmp_path):
    path = tmp_path / "bytes.pdf"
    path.write_bytes(b"\x00\xff\r\n")
    assert content_hash(path) == hashlib.sha256(b"\x00\xff\r\n").hexdigest()


def test_second_run_duplicates_and_rename_reuse_cache(settings):
    original = put(settings, "a.pdf")
    put(settings, "nested/duplicate.pdf")
    parser = FakeParser()
    first = parse_library(settings, backend=parser)
    assert (first.parsed, first.hits, first.failed) == (1, 1, 0)
    assert len(parser.calls) == parser.closed == 1
    original.rename(original.with_name("renamed.pdf"))
    again = FakeParser(fail=True)
    second = parse_library(settings, backend=again)
    assert (second.parsed, second.hits, second.failed) == (0, 2, 0)
    assert again.calls == [] and again.closed == 0
    assert "renamed.pdf" in {x.source.doc_id for x in second.outcomes}


def test_changed_bytes_miss_only_that_document(settings):
    first = put(settings, "a.pdf", b"first")
    put(settings, "b.pdf", b"second")
    parse_library(settings, backend=FakeParser())
    first.write_bytes(b"changed")
    parser = FakeParser()
    report = parse_library(settings, backend=parser)
    assert (report.parsed, report.hits) == (1, 1)
    assert parser.calls == [b"changed"]


def test_parser_version_invalidates_but_unrelated_config_does_not(settings):
    put(settings, "a.pdf")
    parse_library(settings, backend=FakeParser())
    changed = settings.model_copy(update={"retrieval": settings.retrieval.model_copy(update={"rrf_k": 31})})
    assert parse_library(changed, backend=FakeParser()).hits == 1
    assert parse_library(settings, backend=FakeParser(version="two")).parsed == 1
    assert parser_key({"version": 1, "settings": {"mode": "x"}}) != parser_key({"version": 1, "settings": {"mode": "y"}})
    assert parser_key({"b": 2, "a": 1}) == parser_key({"a": 1, "b": 2})


@pytest.mark.parametrize("broken", ["markdown.md", "content_list.json", "images/one.png", "manifest.json"])
def test_corrupt_artifact_is_not_a_hit_and_old_bundle_is_preserved(settings, broken):
    put(settings, "a.pdf")
    entry = parse_library(settings, backend=FakeParser()).outcomes[0].cache_path
    (entry / broken).write_bytes(b"corrupt")
    parser = FakeParser()
    report = parse_library(settings, backend=parser)
    assert (report.parsed, report.hits, report.failed) == (1, 0, 0)
    assert len(list(entry.parent.glob(".invalid-*"))) == 1


def test_partial_bundle_is_not_a_hit(settings):
    put(settings, "a.pdf")
    entry = parse_library(settings, backend=FakeParser()).outcomes[0].cache_path
    (entry / "manifest.json").unlink()
    assert parse_library(settings, backend=FakeParser()).parsed == 1


@pytest.mark.parametrize("option", ["fail", "invalid", "mutate"])
def test_failed_or_mutating_parse_never_publishes_and_releases(settings, option):
    put(settings, "a.pdf")
    parser = FakeParser(**{option: True})
    report = parse_library(settings, backend=parser)
    assert report.failed == 1 and report.parsed == 0
    assert parser.closed == 1
    assert "PRIVATE" not in repr(report)
    assert not list((settings.paths.cache / "parse").rglob("manifest.json"))
    assert not list((settings.paths.cache / "parse").rglob(".work-*"))


def test_mutation_between_scan_and_snapshot_fails(settings, monkeypatch):
    import ragshelf.parse.pipeline as pipeline

    path = put(settings, "a.pdf")
    scan = pipeline.scan_library

    def mutate(root):
        sources = scan(root)
        path.write_bytes(b"mutated")
        return sources

    monkeypatch.setattr(pipeline, "scan_library", mutate)
    parser = FakeParser()
    assert parse_library(settings, backend=parser).failed == 1
    assert not parser.calls


def test_text_passthrough_utf8_bom_empty_and_failure(settings):
    put(settings, "note.md", b"\xef\xbb\xbf# Synthetic\nSlovak: \xc4\x8d")
    put(settings, "empty.txt", b"")
    put(settings, "invalid.txt", b"\xff")
    parser = FakeParser(fail=True)
    report = parse_library(settings, backend=parser)
    assert (report.parsed, report.failed) == (2, 1)
    assert parser.calls == []
    note = next(x for x in report.outcomes if x.source.doc_id == "note.md")
    assert (note.cache_path / "markdown.md").read_text(encoding="utf-8") == "# Synthetic\nSlovak: č"
    assert json.loads((note.cache_path / "content_list.json").read_text(encoding="utf-8"))[0]["page_idx"] == 0


def test_lock_excludes_concurrent_batch_and_is_reusable(settings):
    root = settings.paths.cache / "parse"
    with batch_lock(root):
        result = subprocess.run([sys.executable, "-c",
            "from pathlib import Path; from ragshelf.parse.cache import batch_lock; "
            "lock = batch_lock(Path(__import__('sys').argv[1])); lock.__enter__()", str(root)],
            capture_output=True, text=True)
        assert result.returncode != 0
    with batch_lock(root):
        pass


def test_import_has_no_model_side_effects():
    result = subprocess.run([sys.executable, "-c",
        "import sys; import ragshelf.parse; assert 'torch' not in sys.modules; "
        "assert 'mineru.parser' not in sys.modules"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
