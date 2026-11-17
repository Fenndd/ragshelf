"""Shared request logic for OpenAI-compatible chat-completion endpoints."""

import time
from collections.abc import Callable, Sequence
from typing import Any

import requests

from ragshelf.llm.base import Completion, LLMError, Message, Route, Usage

# How much of an error response body goes into the exception message.
_ERROR_BODY_CHARS = 500
# Upper bound for one wait between attempts, including a server's Retry-After.
_MAX_BACKOFF_SECONDS = 30.0
_REDACTED = "<redacted>"


def _is_retryable(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


def _check_api_key(api_key: str, name: str) -> None:
    """Reject a key that cannot be a header value, without echoing it.

    `requests` refuses such a header with an exception that quotes the whole
    value, so a stray newline would otherwise put the key into a traceback.
    """
    if not api_key or not api_key.isascii() or not api_key.isprintable() or " " in api_key:
        raise LLMError(
            f"{name} is empty or malformed: it must be printable ASCII without whitespace"
        )


class OpenAICompatibleClient:
    """POSTs to `<base_url>/chat/completions` with a timeout and bounded retries.

    Retries only HTTP 429 and 5xx, with exponential backoff. Every other
    failure, including a timeout, raises `LLMError` at once. Error messages
    carry the status and the start of the response body, never request headers,
    and the API key is redacted from any text that could contain it.
    """

    route: Route

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        api_key: str | None = None,
        api_key_name: str = "The API key",
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        backoff_seconds: float = 1.0,
    ) -> None:
        if api_key is not None:
            _check_api_key(api_key, api_key_name)
        self._api_key = api_key
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._session = session if session is not None else requests.Session()
        self._sleep = sleep
        self._backoff_seconds = backoff_seconds

    def _headers(self) -> dict[str, str]:
        if self._api_key is None:
            return {}
        return {"Authorization": f"Bearer {self._api_key}"}

    def _extra_payload(self) -> dict[str, Any]:
        return {}

    def _redact(self, text: str) -> str:
        if self._api_key is None:
            return text
        return text.replace(self._api_key, _REDACTED)

    def complete(
        self, messages: Sequence[Message], max_tokens: int, temperature: float
    ) -> Completion:
        payload = {
            "model": self._model,
            "messages": list(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            **self._extra_payload(),
        }
        return self._parse(self._post(payload))

    def _post(self, payload: dict[str, Any]) -> requests.Response:
        attempts = self._max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                response = self._session.post(
                    self._url,
                    headers=self._headers(),
                    json=payload,
                    timeout=self._timeout_seconds,
                )
            except requests.Timeout:
                raise LLMError(
                    f"{self.route} LLM request timed out after {self._timeout_seconds:g} s"
                ) from None
            except requests.RequestException as exc:
                detail = str(exc)
                error = LLMError(
                    f"{self.route} LLM request failed: "
                    f"{type(exc).__name__}: {self._redact(detail)}"
                )
                # Even a safe-looking exception can have a credential-bearing
                # nested cause or context. Keep only the sanitized diagnostic.
                raise error from None

            if response.status_code == 200:
                return response
            if _is_retryable(response.status_code) and attempt < attempts:
                self._sleep(self._retry_delay(response, attempt))
                continue
            raise LLMError(
                f"{self.route} LLM request failed with HTTP {response.status_code} "
                f"after {attempt} attempt(s): "
                f"{self._redact(response.text)[:_ERROR_BODY_CHARS]}"
            )
        raise AssertionError("unreachable")  # the loop returns or raises

    def _retry_delay(self, response: requests.Response, attempt: int) -> float:
        delay = self._backoff_seconds * 2 ** (attempt - 1)
        try:
            delay = max(delay, float(response.headers.get("Retry-After", "")))
        except ValueError:
            pass  # absent, or an HTTP date: keep the exponential delay
        return min(delay, _MAX_BACKOFF_SECONDS)

    def _parse(self, response: requests.Response) -> Completion:
        try:
            data = response.json()
        except ValueError:
            raise LLMError(f"{self.route} LLM returned a non-JSON response") from None
        if not isinstance(data, dict):
            raise LLMError(f"{self.route} LLM returned an unexpected response")
        if data.get("error"):
            # A provider can report an upstream failure inside a 200 response.
            raise LLMError(self._error_message(data["error"]))
        try:
            choice = data["choices"][0]
            text = choice["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"{self.route} LLM response has no message content") from None

        finish_reason = choice.get("finish_reason")
        if choice.get("error") or finish_reason == "error":
            # The failure can also sit on the choice, next to a partial answer.
            raise LLMError(self._error_message(choice.get("error") or "finish_reason is 'error'"))
        if not isinstance(text, str) or not text.strip():
            raise LLMError(f"{self.route} LLM returned an empty answer")

        usage = data.get("usage")
        if not isinstance(usage, dict):
            usage = {}
        model = data.get("model")
        return Completion(
            text=text.strip(),
            model=model if isinstance(model, str) and model else self._model,
            route=self.route,
            usage=Usage(
                prompt_tokens=_token_count(usage.get("prompt_tokens")),
                completion_tokens=_token_count(usage.get("completion_tokens")),
                total_tokens=_token_count(usage.get("total_tokens")),
            ),
            finish_reason=finish_reason if isinstance(finish_reason, str) else None,
        )

    def _error_message(self, error: Any) -> str:
        return (
            f"{self.route} LLM returned an error: "
            f"{self._redact(str(error))[:_ERROR_BODY_CHARS]}"
        )


def _token_count(value: Any) -> int | None:
    # bool is an int subclass; a count is never a bool.
    return value if isinstance(value, int) and not isinstance(value, bool) else None
