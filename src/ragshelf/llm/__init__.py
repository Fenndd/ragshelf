"""LLM clients behind one chat interface.

Cloud route: the DeepSeek platform by default, OpenRouter as an alternative.
Local route: llama-server.
"""

from typing import Literal

from ragshelf.config import Secrets, Settings, load_secrets
from ragshelf.llm.base import ChatClient, Completion, LLMError, Message, Route, Usage
from ragshelf.llm.deepseek import DeepSeekClient
from ragshelf.llm.llama_server import LlamaServerClient
from ragshelf.llm.openrouter import OpenRouterClient

__all__ = [
    "ChatClient",
    "Completion",
    "DeepSeekClient",
    "LLMError",
    "LlamaServerClient",
    "Message",
    "OpenRouterClient",
    "Usage",
    "create_chat_client",
]

CloudProvider = Literal["deepseek", "openrouter"]


def create_chat_client(
    settings: Settings,
    secrets: Secrets | None = None,
    route: Route | None = None,
    cloud_provider: CloudProvider | None = None,
) -> ChatClient:
    """Build the client for the configured route and cloud provider.

    `route` and `cloud_provider` override the configuration. Raises `LLMError`
    when the chosen cloud provider has no key.
    """
    route = settings.llm.route if route is None else route
    if route == "local":
        return LlamaServerClient(
            settings.llm.local, model=settings.models.local_llm_path.name
        )

    if secrets is None:
        secrets = load_secrets()
    if cloud_provider is None:
        cloud_provider = settings.llm.cloud_provider
    if cloud_provider == "openrouter":
        if secrets.openrouter_api_key is None:
            raise LLMError("OPENROUTER_API_KEY is not set; add it to .env")
        return OpenRouterClient(
            secrets.openrouter_api_key.get_secret_value(), settings.llm.openrouter
        )
    if secrets.deepseek_api_key is None:
        raise LLMError("DEEPSEEK_API_KEY is not set; add it to .env")
    return DeepSeekClient(
        secrets.deepseek_api_key.get_secret_value(), settings.llm.deepseek
    )
