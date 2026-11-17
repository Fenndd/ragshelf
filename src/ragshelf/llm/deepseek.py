"""Cloud route, default provider: the DeepSeek platform API (ADR 0003)."""

import time
from collections.abc import Callable
from typing import Any

import requests

from ragshelf.config import DeepSeekLLMConfig
from ragshelf.llm.base import LLMError
from ragshelf.llm.openai_compatible import OpenAICompatibleClient


class DeepSeekClient(OpenAICompatibleClient):
    route = "cloud"

    def __init__(
        self,
        api_key: str,
        config: DeepSeekLLMConfig,
        *,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if api_key.startswith("sk-or-"):
            # The prototype kept an OpenRouter key under this variable name.
            # Refuse it rather than send another provider's credential here.
            raise LLMError(
                "DEEPSEEK_API_KEY holds an OpenRouter key (it starts with 'sk-or-'); "
                "put the DeepSeek platform key there and move the OpenRouter key "
                "to OPENROUTER_API_KEY"
            )
        super().__init__(
            base_url=config.base_url,
            model=config.model,
            timeout_seconds=config.timeout_seconds,
            max_retries=config.max_retries,
            api_key=api_key,
            api_key_name="DEEPSEEK_API_KEY",
            session=session,
            sleep=sleep,
        )
        self._config = config

    def _extra_payload(self) -> dict[str, Any]:
        # The platform thinks by default and bills it as output.
        return {"thinking": {"type": self._config.thinking}}
