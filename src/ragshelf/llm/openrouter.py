"""Cloud route, alternative provider: OpenRouter with the ADR 0001 settings."""

import time
from collections.abc import Callable
from typing import Any

import requests

from ragshelf.config import OpenRouterLLMConfig
from ragshelf.llm.openai_compatible import OpenAICompatibleClient


class OpenRouterClient(OpenAICompatibleClient):
    route = "cloud"

    def __init__(
        self,
        api_key: str,
        config: OpenRouterLLMConfig,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        super().__init__(
            base_url=config.base_url,
            model=config.model,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            api_key=api_key,
            api_key_name="OPENROUTER_API_KEY",
            session=session,
            sleep=sleep,
        )
        self._config = config

    def _extra_payload(self) -> dict[str, Any]:
        return {
            # Thinking is billed as output, and RAG answers do not need it.
            "reasoning": {"effort": self._config.reasoning_effort},
            # Route only to endpoints that neither retain nor train on prompts.
            "provider": self._config.provider.model_dump(),
        }
