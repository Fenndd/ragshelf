"""Parse a library without coupling cache identity to later pipeline stages."""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Protocol

from ragshelf.config import Settings, apply_environment

from .cache import batch_lock, cache_valid, parser_key, publish, seal_bundle
from .html import HTML_EXTENSIONS, html_dependencies
from .scan import PASSTHROUGH_EXTENSIONS, DocumentSource, content_hash, scan_library

TEXT_DESCRIPTOR = {"name": "text-passthrough", "version": 1, "encoding": "utf-8-sig", "page_index": "logical-zero"}


class ParseBackend(Protocol):
    def descriptor(self, suffix: str) -> dict[str, Any]: ...
    def parse(self, source: Path, output: Path, *, original: Path) -> None: ...
    def close(self) -> None: ...


@dataclass(frozen=True)
class ParseOutcome:
    source: DocumentSource
    status: str
    cache_path: Path | None = None
    error: str | None = None


@dataclass(frozen=True)
class ParseReport:
    outcomes: list[ParseOutcome]

    @property
    def hits(self) -> int:
        return sum(item.status == "hit" for item in self.outcomes)

    @property
    def parsed(self) -> int:
        return sum(item.status == "parsed" for item in self.outcomes)

    @property
    def failed(self) -> int:
        return sum(item.status == "failed" for item in self.outcomes)


def parse_library(settings: Settings, *, backend: ParseBackend | None = None) -> ParseReport:
    """Cache originals sequentially, reuse duplicates, and release the batch.

    A backend error never publishes a cache entry. Errors expose only their
    exception class: third-party exception messages may contain document text.
    Cache hits inspect lightweight settings but never import a model runtime.
    """
    apply_environment(settings)
    root = settings.paths.cache / "parse"
    outcomes = []
    used_backend = False
    with batch_lock(root):
        sources = scan_library(settings.paths.library)
        try:
            for source in sources:
                try:
                    text_input = source.path.suffix.lower() in PASSTHROUGH_EXTENSIONS
                    if not text_input and backend is None:
                        from .mineru import MinerUBackend

                        backend = MinerUBackend(settings.models.parser_tier)
                    descriptor = TEXT_DESCRIPTOR if text_input else backend.descriptor(source.path.suffix)
                    if source.path.suffix.lower() in HTML_EXTENSIONS:
                        descriptor = {**descriptor, "html_context": html_dependencies(source.path, original=source.path)}
                    entry = root / source.content_hash / parser_key(descriptor)
                    if cache_valid(entry, source.content_hash, descriptor):
                        # The scanner's identity must still describe the original.
                        if content_hash(source.path) != source.content_hash:
                            raise ValueError("Source changed while scanning")
                        if "html_context" in descriptor and html_dependencies(source.path, original=source.path) != descriptor["html_context"]:
                            raise ValueError("HTML dependencies changed during cache validation")
                        outcomes.append(ParseOutcome(source, "hit", entry))
                        continue
                    entry.parent.mkdir(parents=True, exist_ok=True)
                    with TemporaryDirectory(prefix=".work-", dir=entry.parent) as work:
                        workspace = Path(work)
                        snapshot = workspace / ("source" + source.path.suffix.lower())
                        shutil.copyfile(source.path, snapshot)
                        if content_hash(snapshot) != source.content_hash:
                            raise ValueError("Source changed while creating snapshot")
                        stage = workspace / "bundle"
                        stage.mkdir()
                        if text_input:
                            text = snapshot.read_text(encoding="utf-8-sig")
                            (stage / "markdown.md").write_text(text, encoding="utf-8")
                            (stage / "content_list.json").write_text(json.dumps(
                                [{"type": "text", "text": text, "page_idx": 0}] if text else [],
                                ensure_ascii=False), encoding="utf-8")
                        else:
                            used_backend = True
                            backend.parse(snapshot, stage, original=source.path)
                        if content_hash(source.path) != source.content_hash:
                            raise ValueError("Source changed during parsing")
                        if "html_context" in descriptor and html_dependencies(snapshot, original=source.path) != descriptor["html_context"]:
                            raise ValueError("HTML dependencies changed during parsing")
                        seal_bundle(stage, source.content_hash, descriptor)
                        publish(stage, entry)
                    outcomes.append(ParseOutcome(source, "parsed", entry))
                except Exception as exc:
                    outcomes.append(ParseOutcome(source, "failed", error=type(exc).__name__))
        finally:
            if used_backend:
                backend.close()
    return ParseReport(outcomes)
