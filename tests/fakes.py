"""Test doubles for the pipeline's interfaces. No network, no models."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from ragshelf.llm.base import Completion, LLMError, Message, Route, Usage


@dataclass
class ChatCall:
    messages: list[Message]
    max_tokens: int
    temperature: float


@dataclass
class ScriptedChatClient:
    """A `ChatClient` that replays a script and records what it was asked.

    Each script item is either the answer text or an exception to raise.
    Asking for more answers than the script holds raises `LLMError`.
    """

    script: Sequence[str | Exception] = ()
    model: str = "fake-model"
    route: Route = "cloud"
    calls: list[ChatCall] = field(default_factory=list)

    def complete(
        self, messages: Sequence[Message], max_tokens: int, temperature: float
    ) -> Completion:
        self.calls.append(ChatCall(list(messages), max_tokens, temperature))
        if len(self.calls) > len(self.script):
            raise LLMError("ScriptedChatClient: the script has no more answers")
        item = self.script[len(self.calls) - 1]
        if isinstance(item, Exception):
            raise item
        prompt_tokens = sum(len(message["content"].split()) for message in messages)
        completion_tokens = len(item.split())
        return Completion(
            text=item,
            model=self.model,
            route=self.route,
            usage=Usage(prompt_tokens, completion_tokens, prompt_tokens + completion_tokens),
        )
