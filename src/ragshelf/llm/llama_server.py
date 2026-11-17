"""Local route: llama.cpp `llama-server` through its OpenAI-compatible endpoint.

The server is started outside this module (see ADR 0001 for the command).
"""

import time
from collections.abc import Callable
from typing import Any

import requests

from ragshelf.config import LocalLLMConfig
from ragshelf.llm.openai_compatible import OpenAICompatibleClient


class LlamaServerClient(OpenAICompatibleClient):
    route = "local"

    def __init__(
        self,
        config: LocalLLMConfig,
        *,
        model: str = "local",
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(
            base_url=config.base_url,
            model=model,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            session=session,
            sleep=sleep,
        )
        self._config = config

    def _extra_payload(self) -> dict[str, Any]:
        return {"chat_template_kwargs": {"enable_thinking": self._config.enable_thinking}}
