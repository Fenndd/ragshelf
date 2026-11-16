"""Typed configuration for the pipeline.

Settings come from, in order of precedence: `RAGSHELF_*` environment variables
(nested fields joined with `__`, for example `RAGSHELF_RETRIEVAL__RRF_K=30`),
`ragshelf.toml` at the repository root, and the defaults below, which carry
the values decided in docs/decisions/0001-model-stack.md and
0002-pipeline-architecture.md.

Secrets are not settings: they are loaded separately by `load_secrets()` from
the process environment or `.env`, never from `ragshelf.toml`, and never enter
`config_hash()`.

This module must stay importable without loading any model library, so that
`apply_environment()` can run before those libraries read their variables.
"""

import hashlib
import json
import os
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

# src/ragshelf/config.py -> repository root. The package is installed in
# editable mode, so this is the checkout that holds data/ and models/.
REPO_ROOT = Path(__file__).resolve().parents[2]
TOML_FILE = REPO_ROOT / "ragshelf.toml"
ENV_FILE = REPO_ROOT / ".env"

# The TOML file the next `Settings()` reads; `load_settings` sets it per call.
_toml_file: ContextVar[Path] = ContextVar("ragshelf_toml_file", default=TOML_FILE)


def _resolve(path: Path) -> Path:
    """Make a path absolute, taking relative paths from the repository root."""
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


class _Section(BaseModel):
    """Base for configuration sections: immutable, unknown keys are errors.

    Every field annotated as `Path` is resolved against the repository root, so
    the same settings name the same files whatever the working directory is.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def _resolve_paths(self):
        for name, field in type(self).model_fields.items():
            if field.annotation is Path:
                # The model is frozen; this runs once, during validation.
                object.__setattr__(self, name, _resolve(getattr(self, name)))
        return self


class PathsConfig(_Section):
    library: Path = Path("data/library")
    cache: Path = Path("data/cache")
    index: Path = Path("data/index")
    traces: Path = Path("data/traces")
    eval: Path = Path("data/eval")
    models: Path = Path("models")


class ModelsConfig(_Section):
    # Parsing: MinerU run in-process with `mineru-kit parse` (ADR 0001).
    parser_tier: str = "standard"
    mineru_home: Path = Path("models/mineru")
    hf_home: Path = Path("models/hf")
    # Embeddings.
    embedder_id: str = "microsoft/harrier-oss-v1-0.6b"
    embedder_path: Path = Path("models/harrier-oss-v1-0.6b")
    embedder_query_prompt: str = "web_search_query"
    # Reranker.
    reranker_id: str = "Qwen/Qwen3-Reranker-0.6B"
    reranker_path: Path = Path("models/Qwen3-Reranker-0.6B")
    # Local generation and query translation.
    local_llm_id: str = "bartowski/Qwen_Qwen3.5-9B-GGUF"
    local_llm_path: Path = Path("models/gguf/Qwen_Qwen3.5-9B-IQ4_XS.gguf")
    llama_server_path: Path = Path(".tools/llama.cpp/llama-server.exe")


class ChunkingConfig(_Section):
    target_tokens: int = Field(default=512, gt=0)
    max_tokens: int = Field(default=800, gt=0)
    # ADR 0002 allows 0-15%, tuned with the evaluation.
    overlap_ratio: float = Field(default=0.10, ge=0.0, le=0.15)
    # Sections shorter than this merge into a neighbour.
    min_section_tokens: int = Field(default=100, ge=0)

    @model_validator(mode="after")
    def _target_within_max(self):
        if self.target_tokens > self.max_tokens:
            raise ValueError("chunking.target_tokens must not exceed chunking.max_tokens")
        return self


class RetrievalConfig(_Section):
    dense_top_k: int = Field(default=100, gt=0)
    lexical_top_k: int = Field(default=100, gt=0)
    rrf_k: int = Field(default=60, gt=0)
    rerank_depth: int = Field(default=50, gt=0)
    context_top_n: int = Field(default=8, gt=0)


class ProviderPreferences(_Section):
    """OpenRouter provider routing preferences (ADR 0001)."""

    zdr: bool = True
    data_collection: Literal["allow", "deny"] = "deny"
    sort: Literal["price", "throughput", "latency"] = "price"


class CloudLLMConfig(_Section):
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "deepseek/deepseek-v4.1-flash-1017"
    reasoning_effort: str = "none"
    provider: ProviderPreferences = ProviderPreferences()
    timeout_seconds: float = Field(default=60.0, gt=0)
    max_retries: int = Field(default=3, ge=0)


class LocalLLMConfig(_Section):
    # llama-server's OpenAI-compatible endpoint, as started by the ADR 0001 command.
    base_url: str = "http://127.0.0.1:8081/v1"
    enable_thinking: bool = False
    timeout_seconds: float = Field(default=120.0, gt=0)
    max_retries: int = Field(default=1, ge=0)


class LLMConfig(_Section):
    route: Literal["cloud", "local"] = "cloud"
    cloud: CloudLLMConfig = CloudLLMConfig()
    local: LocalLLMConfig = LocalLLMConfig()


class Settings(BaseSettings):
    """All non-secret settings of one pipeline setup."""

    model_config = SettingsConfigDict(
        env_prefix="RAGSHELF_",
        env_nested_delimiter="__",
        extra="forbid",
        frozen=True,
    )

    paths: PathsConfig = PathsConfig()
    models: ModelsConfig = ModelsConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    llm: LLMConfig = LLMConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Earlier sources win. `.env` is deliberately not a settings source:
        # it holds secrets, which `Secrets` reads.
        toml_settings = TomlConfigSettingsSource(settings_cls, toml_file=_toml_file.get())
        return (init_settings, env_settings, toml_settings)


class Secrets(BaseSettings):
    """Credentials. Values are masked in `repr` and are never hashed."""

    # `.env.example` ships the key with an empty value; treat that as "not set".
    model_config = SettingsConfigDict(extra="ignore", frozen=True, env_ignore_empty=True)

    openrouter_api_key: SecretStr | None = None


def load_settings(toml_file: Path | None = None) -> Settings:
    """Load settings from `ragshelf.toml` (or `toml_file`) and the environment.

    A missing TOML file is not an error: the defaults apply.
    """
    token = _toml_file.set(TOML_FILE if toml_file is None else toml_file)
    try:
        return Settings()
    finally:
        _toml_file.reset(token)


def load_secrets(env_file: Path | None = None) -> Secrets:
    """Load credentials from the process environment, then `.env` (or `env_file`)."""
    return Secrets(_env_file=ENV_FILE if env_file is None else env_file)


def _portable(value: Any) -> Any:
    """Rewrite absolute paths under the repository root as relative POSIX paths.

    The hash then identifies the setup, not the folder the checkout lives in.
    """
    if isinstance(value, dict):
        return {key: _portable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_portable(item) for item in value]
    if isinstance(value, Path):
        try:
            return value.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            return value.as_posix()
    return value


def hash_input(settings: Settings) -> str:
    """The canonical JSON text that `config_hash` hashes."""
    return json.dumps(
        _portable(settings.model_dump(mode="python")),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def config_hash(settings: Settings) -> str:
    """Stable SHA-256 hex digest of the non-secret settings."""
    return hashlib.sha256(hash_input(settings).encode("utf-8")).hexdigest()


def apply_environment(settings: Settings) -> None:
    """Point model libraries at project-local folders and disable telemetry.

    Call this before importing `transformers`, `sentence_transformers`,
    `huggingface_hub`, or MinerU: they read these variables at import time.
    """
    os.environ["HF_HOME"] = str(settings.models.hf_home)
    os.environ["MINERU_HOME"] = str(settings.models.mineru_home)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["MINERU_TELEMETRY_DISABLED"] = "1"
