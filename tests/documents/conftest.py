"""Synthetic libraries and parse-cache bundles in the shape T005 writes.

Everything here is made up. The bundles are sealed with the real cache API, so
the loader validates them exactly as it validates real ones.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from ragshelf.config import load_settings
from ragshelf.parse import content_hash
from ragshelf.parse.cache import parser_key, publish, seal_bundle
from ragshelf.parse.pipeline import TEXT_DESCRIPTOR

FAKE_MINERU = {"name": "mineru", "version": "synthetic", "adapter_version": 1, "format": ".pdf"}


@dataclass
class Library:
    root: Path
    cache: Path

    def settings(self):
        return load_settings()

    def add(self, name, data=b"synthetic original", *, items=None, markdown="", sidecar=None,
            descriptor=FAKE_MINERU, bundle=True):
        """Write an original (and its sidecar), then seal a bundle for its bytes."""
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        if sidecar is not None:
            text = sidecar if isinstance(sidecar, str) else json.dumps(sidecar)
            (path.parent / (path.name + ".metadata.json")).write_text(text, encoding="utf-8")
        digest = content_hash(path)
        if bundle:
            self.bundle(digest, items if items is not None else [], markdown, descriptor)
        return path, digest

    def bundle(self, digest, items, markdown="", descriptor=FAKE_MINERU):
        entry = self.cache / "parse" / digest / parser_key(descriptor)
        entry.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=entry.parent, prefix=".work-") as work:
            stage = Path(work) / "bundle"
            stage.mkdir()
            (stage / "markdown.md").write_text(markdown, encoding="utf-8")
            (stage / "content_list.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            seal_bundle(stage, digest, descriptor)
            publish(stage, entry)
        return entry

    def add_text(self, name, text):
        """A passthrough original, bundled the way the parse stage bundles .md/.txt."""
        items = [{"type": "text", "text": text, "page_idx": 0}] if text else []
        return self.add(name, text, items=items, markdown=text, descriptor=TEXT_DESCRIPTOR)


@pytest.fixture
def library(tmp_path, monkeypatch):
    root, cache = tmp_path / "library", tmp_path / "cache"
    root.mkdir()
    monkeypatch.setenv("RAGSHELF_PATHS__LIBRARY", str(root))
    monkeypatch.setenv("RAGSHELF_PATHS__CACHE", str(cache))
    return Library(root, cache)
