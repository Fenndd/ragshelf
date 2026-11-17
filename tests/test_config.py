import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from ragshelf import config
from ragshelf.config import (
    REPO_ROOT,
    apply_environment,
    config_hash,
    hash_input,
    load_secrets,
    load_settings,
)

FAKE_KEY = "test-only-not-a-real-key"
KEY_VARIABLES = ["DEEPSEEK_API_KEY", "OPENROUTER_API_KEY"]


@pytest.fixture
def no_toml(tmp_path):
    return tmp_path / "absent.toml"


def write_toml(tmp_path, text):
    path = tmp_path / "ragshelf.toml"
    path.write_text(text, encoding="utf-8")
    return path


# Criterion 1: defaults.


def test_defaults_carry_the_adr_values(no_toml):
    settings = load_settings(no_toml)

    # ADR 0001.
    assert settings.models.parser_tier == "standard"
    assert settings.models.embedder_id == "microsoft/harrier-oss-v1-0.6b"
    assert settings.models.embedder_path == REPO_ROOT / "models" / "harrier-oss-v1-0.6b"
    assert settings.models.embedder_query_prompt == "web_search_query"
    assert settings.models.reranker_id == "Qwen/Qwen3-Reranker-0.6B"
    assert settings.models.reranker_path == REPO_ROOT / "models" / "Qwen3-Reranker-0.6B"
    assert settings.models.local_llm_path == (
        REPO_ROOT / "models" / "gguf" / "Qwen_Qwen3.5-9B-IQ4_XS.gguf"
    )
    assert settings.models.llama_server_path == (
        REPO_ROOT / ".tools" / "llama.cpp" / "llama-server.exe"
    )
    assert settings.llm.route == "cloud"
    assert settings.llm.openrouter.model == "deepseek/deepseek-v4.1-flash-1017"
    assert settings.llm.openrouter.reasoning_effort == "none"
    assert settings.llm.openrouter.provider.model_dump() == {
        "zdr": True,
        "data_collection": "deny",
        "sort": "price",
    }
    assert settings.llm.local.base_url == "http://127.0.0.1:8081/v1"
    assert settings.llm.local.enable_thinking is False

    # ADR 0003.
    assert settings.llm.cloud_provider == "deepseek"
    assert settings.llm.deepseek.base_url == "https://api.deepseek.com"
    assert settings.llm.deepseek.model == "deepseek-flash"
    assert settings.llm.deepseek.thinking == "disabled"

    # ADR 0002.
    assert settings.paths.library == REPO_ROOT / "data" / "library"
    assert settings.paths.cache == REPO_ROOT / "data" / "cache"
    assert settings.paths.index == REPO_ROOT / "data" / "index"
    assert settings.paths.traces == REPO_ROOT / "data" / "traces"
    assert settings.paths.eval == REPO_ROOT / "data" / "eval"
    assert settings.paths.models == REPO_ROOT / "models"
    assert settings.chunking.target_tokens == 512
    assert settings.chunking.max_tokens == 800
    assert 0.0 <= settings.chunking.overlap_ratio <= 0.15
    assert settings.retrieval.dense_top_k == 100
    assert settings.retrieval.lexical_top_k == 100
    assert settings.retrieval.rrf_k == 60
    assert settings.retrieval.rerank_depth == 50
    assert settings.retrieval.context_top_n == 8


def test_the_tracked_toml_file_changes_no_default(no_toml):
    assert config.TOML_FILE.is_file()
    assert load_settings() == load_settings(no_toml)


# Criterion 2: precedence.


def test_toml_overrides_a_default(tmp_path):
    toml = write_toml(tmp_path, "[retrieval]\nrrf_k = 45\n")

    settings = load_settings(toml)

    assert settings.retrieval.rrf_k == 45
    assert settings.retrieval.rerank_depth == 50  # untouched keys keep their defaults


def test_environment_overrides_toml(tmp_path, monkeypatch):
    toml = write_toml(tmp_path, "[retrieval]\nrrf_k = 45\n\n[llm]\nroute = 'local'\n")
    monkeypatch.setenv("RAGSHELF_RETRIEVAL__RRF_K", "30")

    settings = load_settings(toml)

    assert settings.retrieval.rrf_k == 30
    assert settings.llm.route == "local"  # TOML values without an override stay


def test_unknown_keys_are_rejected(tmp_path):
    with pytest.raises(ValidationError):
        load_settings(write_toml(tmp_path, "[retrieval]\nrrf = 45\n"))


def test_invalid_values_are_rejected(tmp_path):
    with pytest.raises(ValidationError):
        load_settings(write_toml(tmp_path, "[chunking]\ntarget_tokens = 900\n"))


# Criterion 3: hash and secrets.


def test_hash_is_stable_across_loads(no_toml):
    first, second = load_settings(no_toml), load_settings(no_toml)

    assert config_hash(first) == config_hash(second)
    assert len(config_hash(first)) == 64


def leaf_overrides(prefix, value):
    """One (dotted key, changed value) pair for every leaf setting."""
    for key, item in value.items():
        dotted = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            yield from leaf_overrides(dotted, item)
        elif isinstance(item, bool):
            yield dotted, not item
        elif isinstance(item, int):
            yield dotted, item + 1
        elif isinstance(item, float):
            # Stay inside the 0-0.15 range allowed for chunking.overlap_ratio.
            yield dotted, item / 2
        elif isinstance(item, Path):
            yield dotted, str(item) + "-changed"
        elif dotted == "llm.route":
            yield dotted, "local"
        elif dotted == "llm.cloud_provider":
            yield dotted, "openrouter"
        elif dotted == "llm.deepseek.thinking":
            yield dotted, "enabled"
        elif dotted == "llm.openrouter.provider.data_collection":
            yield dotted, "allow"
        elif dotted == "llm.openrouter.provider.sort":
            yield dotted, "latency"
        else:
            yield dotted, item + "-changed"


def test_hash_changes_when_any_setting_changes(no_toml, monkeypatch):
    defaults = load_settings(no_toml)
    baseline = config_hash(defaults)
    overrides = dict(leaf_overrides("", defaults.model_dump()))
    assert len(overrides) > 30  # every section is covered

    seen = {baseline}
    for dotted, changed in overrides.items():
        variable = "RAGSHELF_" + dotted.upper().replace(".", "__")
        with monkeypatch.context() as patch:
            patch.setenv(variable, str(changed))
            digest = config_hash(load_settings(no_toml))
        assert digest not in seen, f"{dotted} does not affect the hash"
        seen.add(digest)


@pytest.mark.parametrize("variable", KEY_VARIABLES)
def test_secrets_stay_out_of_the_hash_and_repr(tmp_path, no_toml, monkeypatch, variable):
    env_file = tmp_path / ".env"
    env_file.write_text(f"{variable}={FAKE_KEY}\n", encoding="utf-8")
    without_key = config_hash(load_settings(no_toml))

    secrets = load_secrets(env_file)
    monkeypatch.setenv(variable, FAKE_KEY)
    settings = load_settings(no_toml)

    assert getattr(secrets, variable.lower()).get_secret_value() == FAKE_KEY
    assert FAKE_KEY not in repr(secrets)
    assert FAKE_KEY not in str(secrets)
    assert FAKE_KEY not in repr(settings)
    assert FAKE_KEY not in hash_input(settings)
    assert config_hash(settings) == without_key


def test_each_key_is_read_from_its_own_variable(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=deepseek-fake\n", encoding="utf-8")

    secrets = load_secrets(env_file)

    assert secrets.deepseek_api_key.get_secret_value() == "deepseek-fake"
    assert secrets.openrouter_api_key is None


@pytest.mark.parametrize("variable", KEY_VARIABLES)
def test_secrets_cannot_be_set_in_toml(tmp_path, variable):
    with pytest.raises(ValidationError):
        load_settings(write_toml(tmp_path, f'{variable.lower()} = "{FAKE_KEY}"\n'))


@pytest.mark.parametrize("variable", KEY_VARIABLES)
def test_a_missing_or_empty_key_is_none(tmp_path, variable):
    empty = tmp_path / ".env"
    empty.write_text(f"{variable}=\n", encoding="utf-8")

    assert getattr(load_secrets(tmp_path / "absent.env"), variable.lower()) is None
    assert getattr(load_secrets(empty), variable.lower()) is None


# Criterion 4: paths do not depend on the working directory.


def test_paths_and_hash_ignore_the_working_directory(tmp_path, no_toml, monkeypatch):
    here = load_settings(no_toml)

    monkeypatch.chdir(tmp_path)
    elsewhere = load_settings(no_toml)

    assert elsewhere == here
    assert config_hash(elsewhere) == config_hash(here)
    for path in elsewhere.paths.model_dump().values():
        assert path.is_absolute()
        assert path.is_relative_to(REPO_ROOT)


def test_relative_overrides_resolve_from_the_repository_root(tmp_path, monkeypatch):
    toml = write_toml(tmp_path, "[paths]\nlibrary = 'data/other'\n")
    monkeypatch.chdir(tmp_path)

    assert load_settings(toml).paths.library == REPO_ROOT / "data" / "other"


def test_absolute_overrides_are_kept(tmp_path):
    target = tmp_path / "library"
    toml = write_toml(tmp_path, f"[paths]\nlibrary = '{target.as_posix()}'\n")

    assert load_settings(toml).paths.library == target


# Environment for model libraries.


def test_apply_environment_sets_project_local_folders(no_toml, monkeypatch):
    for name in ("HF_HOME", "MINERU_HOME", "HF_HUB_DISABLE_TELEMETRY", "MINERU_TELEMETRY_DISABLED"):
        monkeypatch.setenv(name, "replaced-by-apply-environment")

    apply_environment(load_settings(no_toml))

    assert Path(os.environ["HF_HOME"]) == REPO_ROOT / "models" / "hf"
    assert Path(os.environ["MINERU_HOME"]) == REPO_ROOT / "models" / "mineru"
    assert os.environ["HF_HUB_DISABLE_TELEMETRY"] == "1"
    assert os.environ["MINERU_TELEMETRY_DISABLED"] == "1"


def test_config_imports_no_model_library():
    import subprocess
    import sys

    code = (
        "import sys, ragshelf.config; "
        "heavy = {'torch', 'transformers', 'sentence_transformers', 'huggingface_hub', 'mineru'}; "
        "print(sorted(heavy & set(sys.modules)))"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]"
