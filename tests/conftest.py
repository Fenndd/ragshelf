import os

import pytest


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Keep the developer's own overrides and credentials out of every test."""
    for name in list(os.environ):
        if name.startswith("RAGSHELF_") or name in ("DEEPSEEK_API_KEY", "OPENROUTER_API_KEY"):
            monkeypatch.delenv(name)
