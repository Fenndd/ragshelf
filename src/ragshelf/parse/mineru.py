"""Local API used by mineru-kit 4.2.2; imports remain lazy until needed."""

import gc
import json
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any

from .cache import safe_child


class MinerUBackend:
    """One runtime owner for a batch, with explicit release even on failure."""

    def __init__(self, tier: str = "standard"):
        if tier != "standard":
            raise ValueError("The supported MinerU parser tier is standard (ADR 0001)")
        self._owner = None
        self._token = None

    def descriptor(self, suffix: str) -> dict[str, Any]:
        from mineru.config import get_config
        from mineru.filetypes import is_flash_only_parse_extension

        config = get_config()
        if config.llm_aided.features.title_leveling or config.llm_aided.features.cross_page_table_cell_merge:
            raise ValueError("Remote MinerU LLM-aided processing must be disabled")
        # Credentials and remote addresses are deliberately neither copied nor
        # hashed. The actual parse call explicitly selects the local engine.
        return {"name": "mineru", "version": version("mineru"), "docvortex_version": version("docvortex"),
                "adapter_version": 1, "format": suffix.lower(),
                "tier": "flash" if is_flash_only_parse_extension(suffix) else "standard",
                "ocr_mode": "auto", "image_analysis": True, "page_range": "",
                "vlm_engine": "llama-cpp", "small_backend": config.model.small_backend,
                "onnx_device": config.model.onnx_device, "model_source": config.model.source,
                "model_base_dir": config.model.base_dir,
                "render": config.render.model_dump(mode="json")}

    def parse(self, source: Path, output: Path, *, original: Path) -> None:
        from docvortex.export import materialize_middle, validate_materialized_assets
        from mineru.config import VlmConfig
        from mineru.model.runtime.ownership import RuntimeOwner, runtime_owner
        from mineru.parser import ParseResult, parse
        from mineru.render import render_content_list

        if self._owner is None:
            self._owner = RuntimeOwner()
            self._token = runtime_owner.set(self._owner)
        descriptor = self.descriptor(source.suffix)
        kwargs = {}
        if source.suffix.lower() in {".html", ".htm", ".shtml"}:
            from docvortex.document.contracts import HtmlSourceContext

            kwargs["source_context"] = HtmlSourceContext(
                source_uri=original.as_uri(), local_resource_root=original.parent)
        result = parse(source, tier=descriptor["tier"], ocr_mode="auto", image_analysis=True,
                       vlm_config=VlmConfig(engine="llama-cpp", server_url="", api_key="", model=""), **kwargs)
        middle, assets = materialize_middle(result.middle_json)
        validate_materialized_assets(middle, assets)
        rendered = ParseResult(middle_json=middle)
        (output / "markdown.md").write_text(rendered.markdown(), encoding="utf-8")
        (output / "content_list.json").write_text(
            json.dumps(render_content_list(middle), ensure_ascii=False, allow_nan=False), encoding="utf-8")
        for name, payload in assets.items():
            destination = safe_child(output, name)
            if name in {"manifest.json", "markdown.md", "content_list.json"}:
                raise ValueError("Parser asset collides with a cache artifact")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)

    def close(self) -> None:
        if self._owner is None:
            return
        from mineru.model.runtime.ownership import release_runtime_owner, runtime_owner

        try:
            release_runtime_owner(self._owner)
        finally:
            runtime_owner.reset(self._token)
            self._owner = self._token = None
            gc.collect()
            torch = sys.modules.get("torch")
            if torch is not None and torch.cuda.is_initialized():
                torch.cuda.empty_cache()
