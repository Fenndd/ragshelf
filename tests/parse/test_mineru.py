import json
import sys
from contextvars import ContextVar
from types import SimpleNamespace

import pytest

from ragshelf.parse.mineru import MinerUBackend


def test_adapter_uses_local_api_materializes_assets_and_releases_owner(tmp_path, monkeypatch):
    calls = []
    owner_context = ContextVar("test_owner", default=None)
    owner = object()
    middle = object()
    exported = object()
    released = []

    def parse(path, **kwargs):
        assert owner_context.get() is owner
        calls.append(kwargs)
        return SimpleNamespace(middle_json=middle)

    def materialize(value):
        assert value is middle
        return exported, {"images/figure.png": b"synthetic image"}

    monkeypatch.setitem(sys.modules, "docvortex.export", SimpleNamespace(
        materialize_middle=materialize, validate_materialized_assets=lambda *args: None))
    monkeypatch.setitem(sys.modules, "mineru.config", SimpleNamespace(VlmConfig=lambda **kwargs: kwargs))
    monkeypatch.setitem(sys.modules, "mineru.model.runtime.ownership", SimpleNamespace(
        RuntimeOwner=lambda: owner, runtime_owner=owner_context,
        release_runtime_owner=lambda value: released.append(value)))
    monkeypatch.setitem(sys.modules, "mineru.parser", SimpleNamespace(
        parse=parse, ParseResult=lambda **kwargs: SimpleNamespace(markdown=lambda: "![figure](images/figure.png)")))
    monkeypatch.setitem(sys.modules, "mineru.render", SimpleNamespace(
        render_content_list=lambda value: [{"type": "image", "img_path": "images/figure.png", "page_idx": 3}]))
    backend = MinerUBackend()
    monkeypatch.setattr(backend, "descriptor", lambda suffix: {"tier": "standard"})
    output = tmp_path / "output"
    output.mkdir()
    backend.parse(tmp_path / "snapshot.pdf", output, original=tmp_path / "original.pdf")
    assert calls[0]["tier"] == "standard"
    assert calls[0]["vlm_config"] == {"engine": "llama-cpp", "server_url": "", "api_key": "", "model": ""}
    assert (output / "images/figure.png").read_bytes() == b"synthetic image"
    assert json.loads((output / "content_list.json").read_text())[0]["page_idx"] == 3
    backend.close()
    assert released == [owner]
    assert owner_context.get() is None
    backend.close()
    assert released == [owner]


def test_descriptor_matches_native_dispatch_and_refuses_remote_postprocessing(monkeypatch):
    config = SimpleNamespace(
        llm_aided=SimpleNamespace(features=SimpleNamespace(title_leveling=False, cross_page_table_cell_merge=False)),
        model=SimpleNamespace(small_backend="torch", onnx_device="auto", source="local", base_dir="models"),
        render=SimpleNamespace(model_dump=lambda **kwargs: {"latex_delimiters": {}}))
    monkeypatch.setitem(sys.modules, "mineru.config", SimpleNamespace(get_config=lambda: config))
    backend = MinerUBackend()
    assert backend.descriptor(".pdf")["tier"] == "standard"
    assert backend.descriptor(".png")["tier"] == "standard"
    for suffix in (".html", ".docx", ".epub", ".csv"):
        assert backend.descriptor(suffix)["tier"] == "flash"
    config.llm_aided.features.title_leveling = True
    with pytest.raises(ValueError, match="Remote"):
        backend.descriptor(".pdf")


def test_unsupported_tier_is_explicit():
    with pytest.raises(ValueError, match="standard"):
        MinerUBackend("advanced")
