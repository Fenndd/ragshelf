"""The chat interface every LLM client implements."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, Protocol, TypedDict

Route = Literal["cloud", "local"]


class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True)
class Usage:
    """Token counts as reported by the endpoint; `None` when it reports none."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class Completion:
    text: str
    # The model that answered, as named by the endpoint.
    model: str
    route: Route
    usage: Usage
    # Why generation stopped, as reported by the endpoint. "length" means the
    # answer was cut off at `max_tokens`; the caller decides what to do then.
    finish_reason: str | None = None


class LLMError(RuntimeError):
    """A request did not produce an answer. Never returned as answer text."""


class ChatClient(Protocol):
    def complete(
        self, messages: Sequence[Message], max_tokens: int, temperature: float
    ) -> Completion:
        """Return the model's answer or raise `LLMError`."""
        ...
