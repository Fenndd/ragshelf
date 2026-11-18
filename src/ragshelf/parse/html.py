"""Fingerprint precisely the local resources consumed by DocVortex HTML.

The installed native converter is used for discovery, including its content
selection and URL/base rules. Remote images remain references and remote CSS is
ignored by DocVortex; this operation makes no network requests or model loads.
"""

from pathlib import Path
from typing import Any

from .scan import content_hash

HTML_EXTENSIONS = frozenset({".html", ".htm", ".shtml"})


def html_dependencies(source: Path, *, original: Path) -> dict[str, Any]:
    from docvortex.analyzers.native.html.converter import HtmlConverter
    from docvortex.analyzers.native.html.document import parse_html_document
    from docvortex.analyzers.native.html.resources import HtmlResourceContext
    from docvortex.document.contracts import HtmlSourceContext

    root = original.parent.resolve()
    dependencies: dict[str, str | None] = {}

    class TrackedResources(HtmlResourceContext):
        def _signature(self, reference: str) -> tuple[Path | None, str | None]:
            path = self._resolve_local_path(reference)
            return path, content_hash(path) if path is not None and path.is_file() else None

        def _record(self, reference, operation):
            path, before = self._signature(reference)
            result = operation()
            if self._signature(reference) != (path, before):
                raise ValueError("HTML dependency changed during discovery")
            if path is not None:
                dependencies[path.relative_to(root).as_posix()] = before
            return result

        def load_stylesheet(self, href):
            return self._record(href, lambda: super(TrackedResources, self).load_stylesheet(href))

        def resolve_image(self, source, *, alt=""):
            normalized = (source or "").strip()
            if normalized.casefold().startswith("data:") or self._resolve_remote_image_url(normalized):
                return super().resolve_image(source, alt=alt)
            return self._record(normalized, lambda: super(TrackedResources, self).resolve_image(source, alt=alt))

    context = HtmlSourceContext(source_uri=original.as_uri(), local_resource_root=root)
    document = parse_html_document(source.read_bytes(), context)
    resources = TrackedResources(context, base_href=document.base_href)
    # This private seam is the installed 4.2.2/DocVortex native conversion path.
    # The dependency version is included in the owning parser descriptor.
    HtmlConverter()._convert_document(document, resources)
    for name, digest in dependencies.items():
        path = root / name
        if (content_hash(path) if path.is_file() else None) != digest:
            raise ValueError("HTML dependency changed during discovery")
    return {"source_uri": original.as_uri(), "local_resources": dependencies}
