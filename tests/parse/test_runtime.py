"""Opt-in installed MinerU smoke using synthetic documents only."""

import json
import os
import subprocess
import sys

import pytest


@pytest.mark.slow
def test_installed_mineru_pdf_html_and_second_cli_run(tmp_path):
    import pymupdf

    library = tmp_path / "library"
    library.mkdir()
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Synthetic parse fixture. Water freezes at zero degrees Celsius.")
        document.save(library / "synthetic.pdf")
    (library / "synthetic.html").write_text(
        "<html><body><h1>Synthetic parse fixture</h1><p>Water freezes at zero degrees Celsius.</p></body></html>",
        encoding="utf-8")
    env = {**os.environ, "RAGSHELF_PATHS__LIBRARY": str(library), "RAGSHELF_PATHS__CACHE": str(tmp_path / "cache")}
    # A real, guarded module entry point is required for Windows spawn workers.
    for expected in ("0 cache hits, 2 parsed, 0 failed", "2 cache hits, 0 parsed, 0 failed"):
        result = subprocess.run([sys.executable, "-m", "ragshelf", "ingest", "--parse-only"],
                                env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        assert result.returncode == 0, result.stdout + result.stderr
        assert expected in result.stdout
    manifests = list((tmp_path / "cache/parse").rglob("manifest.json"))
    assert len(manifests) == 2
    for manifest in manifests:
        content = json.loads((manifest.parent / "content_list.json").read_text(encoding="utf-8"))
        assert content and {item["page_idx"] for item in content} == {0}
        assert "Water" in (manifest.parent / "markdown.md").read_text(encoding="utf-8")
