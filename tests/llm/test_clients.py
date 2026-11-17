import traceback

import pytest
import requests
from pydantic import SecretStr

from ragshelf.config import (
    DeepSeekLLMConfig,
    LocalLLMConfig,
    OpenRouterLLMConfig,
    Secrets,
    Settings,
)
from ragshelf.llm import (
    DeepSeekClient,
    LlamaServerClient,
    LLMError,
    OpenRouterClient,
    Usage,
    create_chat_client,
)

API_KEY = "test-only-not-a-real-key"
MESSAGES = [
    {"role": "system", "content": "Answer briefly."},
    {"role": "user", "content": "Что такое RAG?"},
]


def deepseek_client(fake_session, sleeps, **config):
    return DeepSeekClient(
        API_KEY, DeepSeekLLMConfig(**config), session=fake_session, sleep=sleeps.sleep
    )


def openrouter_client(fake_session, sleeps, **config):
    return OpenRouterClient(
        API_KEY, OpenRouterLLMConfig(**config), session=fake_session, sleep=sleeps.sleep
    )


def local_client(fake_session, sleeps, **config):
    return LlamaServerClient(
        LocalLLMConfig(**config), model="local.gguf", session=fake_session, sleep=sleeps.sleep
    )


# Success and request shape.


def test_success_returns_the_completion(session, ok, sleeps):
    http = session([ok(text="  RAG — это поиск плюс генерация.  ", model="deepseek-served")])

    completion = deepseek_client(http, sleeps).complete(MESSAGES, max_tokens=200, temperature=0.1)

    assert completion.text == "RAG — это поиск плюс генерация."
    assert completion.model == "deepseek-served"
    assert completion.route == "cloud"
    assert completion.usage == Usage(prompt_tokens=11, completion_tokens=7, total_tokens=18)
    assert completion.finish_reason == "stop"
    assert sleeps == []


def test_deepseek_request_follows_adr_0003(session, ok, sleeps):
    http = session([ok()])

    deepseek_client(http, sleeps).complete(MESSAGES, max_tokens=200, temperature=0.1)

    (request,) = http.requests
    assert request["url"] == "https://api.deepseek.com/chat/completions"
    assert request["headers"] == {"Authorization": f"Bearer {API_KEY}"}
    assert request["timeout"] == 60.0
    assert request["json"] == {
        "model": "deepseek-flash",
        "messages": MESSAGES,
        "max_tokens": 200,
        "temperature": 0.1,
        "thinking": {"type": "disabled"},
    }


def test_openrouter_request_follows_adr_0001(session, ok, sleeps):
    http = session([ok()])

    openrouter_client(http, sleeps).complete(MESSAGES, max_tokens=200, temperature=0.1)

    (request,) = http.requests
    assert request["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert request["headers"] == {"Authorization": f"Bearer {API_KEY}"}
    assert request["json"] == {
        "model": "deepseek/deepseek-v4.1-flash-1017",
        "messages": MESSAGES,
        "max_tokens": 200,
        "temperature": 0.1,
        "reasoning": {"effort": "none"},
        "provider": {"zdr": True, "data_collection": "deny", "sort": "price"},
    }


def test_local_request_disables_thinking_and_sends_no_credentials(session, ok, sleeps):
    http = session([ok(model="local.gguf")])

    completion = local_client(http, sleeps).complete(MESSAGES, max_tokens=64, temperature=0.0)

    (request,) = http.requests
    assert request["url"] == "http://127.0.0.1:8081/v1/chat/completions"
    assert request["headers"] == {}
    assert request["timeout"] == 120.0
    assert request["json"]["chat_template_kwargs"] == {"enable_thinking": False}
    assert request["json"]["model"] == "local.gguf"
    assert "thinking" not in request["json"]
    assert "provider" not in request["json"]
    assert completion.route == "local"
    assert completion.text == "An answer."


def test_settings_come_from_configuration(session, ok, sleeps):
    http = session([ok()])
    client = deepseek_client(
        http, sleeps, base_url="https://example.test/v9/", model="other", thinking="enabled",
        timeout_seconds=5,
    )

    client.complete(MESSAGES, max_tokens=10, temperature=0.0)

    (request,) = http.requests
    assert request["url"] == "https://example.test/v9/chat/completions"
    assert request["json"]["model"] == "other"
    assert request["json"]["thinking"] == {"type": "enabled"}
    assert request["timeout"] == 5


@pytest.mark.parametrize(
    "overrides",
    [
        {"model": None, "usage": None},
        {"model": 5, "usage": ["not", "an", "object"]},
        {"model": "", "usage": "none"},
    ],
)
def test_missing_or_malformed_usage_and_model_fall_back(session, response, sleeps, overrides):
    body = {"choices": [{"message": {"content": "An answer."}}], **overrides}
    http = session([response(200, body)])

    completion = deepseek_client(http, sleeps).complete(MESSAGES, max_tokens=10, temperature=0.0)

    assert completion.text == "An answer."
    assert completion.model == "deepseek-flash"
    assert completion.usage == Usage()
    assert completion.finish_reason is None


def test_a_truncated_answer_is_returned_with_its_finish_reason(session, ok, sleeps):
    http = session([ok(text="An answer cut", finish_reason="length")])

    completion = deepseek_client(http, sleeps).complete(MESSAGES, max_tokens=3, temperature=0.0)

    assert completion.text == "An answer cut"
    assert completion.finish_reason == "length"


# Retries.


def test_a_429_is_retried(session, ok, response, sleeps):
    http = session([response(429, {"error": "rate limited"}), ok()])

    completion = deepseek_client(http, sleeps).complete(MESSAGES, max_tokens=10, temperature=0.0)

    assert completion.text == "An answer."
    assert len(http.requests) == 2
    assert sleeps == [1.0]


def test_backoff_grows_and_honours_retry_after(session, ok, response, sleeps):
    http = session(
        [
            response(503, {"error": "busy"}),
            response(429, {"error": "slow down"}, headers={"Retry-After": "7"}),
            response(500, {"error": "oops"}, headers={"Retry-After": "600"}),
            ok(),
        ]
    )

    deepseek_client(http, sleeps).complete(MESSAGES, max_tokens=10, temperature=0.0)

    # 1 s, then the server's 7 s (above the 2 s backoff), then the 30 s cap.
    assert sleeps == [1.0, 7.0, 30.0]


@pytest.mark.parametrize("retry_after", ["Wed, 21 Oct 2026 07:28:00 GMT", "-5", ""])
def test_an_unusable_retry_after_falls_back_to_backoff(session, ok, response, sleeps, retry_after):
    http = session([response(429, {"error": "x"}, headers={"Retry-After": retry_after}), ok()])

    deepseek_client(http, sleeps).complete(MESSAGES, max_tokens=10, temperature=0.0)

    assert sleeps == [1.0]


def test_retries_stop_at_the_limit(session, response, sleeps):
    http = session([response(500, {"error": "down"})] * 3)

    with pytest.raises(LLMError, match="HTTP 500 after 3 attempt"):
        deepseek_client(http, sleeps, max_retries=2).complete(MESSAGES, 10, 0.0)

    assert len(http.requests) == 3
    assert len(sleeps) == 2


def test_no_retries_when_max_retries_is_zero(session, response, sleeps):
    http = session([response(429, {"error": "rate limited"})])

    with pytest.raises(LLMError, match="HTTP 429 after 1 attempt"):
        deepseek_client(http, sleeps, max_retries=0).complete(MESSAGES, 10, 0.0)

    assert len(http.requests) == 1
    assert sleeps == []


def test_a_400_is_not_retried(session, response, sleeps):
    http = session([response(400, {"error": {"message": "bad request"}})])

    with pytest.raises(LLMError, match="HTTP 400") as excinfo:
        deepseek_client(http, sleeps).complete(MESSAGES, 10, 0.0)

    assert len(http.requests) == 1
    assert sleeps == []
    assert "bad request" in str(excinfo.value)


def test_a_long_error_body_is_truncated(session, response, sleeps):
    http = session([response(400, None, text="x" * 5000)])

    with pytest.raises(LLMError) as excinfo:
        deepseek_client(http, sleeps).complete(MESSAGES, 10, 0.0)

    assert str(excinfo.value).count("x") == 500


# Failures raise LLMError and never become answer text.


def test_a_timeout_raises_llm_error_without_retrying(session, sleeps):
    http = session([requests.Timeout("read timed out")])

    with pytest.raises(LLMError, match="timed out after 60 s"):
        deepseek_client(http, sleeps).complete(MESSAGES, 10, 0.0)

    assert len(http.requests) == 1
    assert sleeps == []


def test_a_connection_error_raises_llm_error(session, sleeps):
    http = session([requests.ConnectionError("connection refused")])

    with pytest.raises(LLMError, match="local LLM request failed: ConnectionError"):
        local_client(http, sleeps).complete(MESSAGES, 10, 0.0)

    assert len(http.requests) == 1


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ({"error": {"message": "provider unavailable", "code": 502}}, "returned an error"),
        ({"choices": []}, "no message content"),
        ({"choices": {"0": "not a list"}}, "no message content"),
        ({"choices": [{"message": {"content": None}}]}, "empty answer"),
        ({"choices": [{"message": {"content": "   "}}]}, "empty answer"),
        (["not", "an", "object"], "unexpected response"),
        (
            {"choices": [{"message": {"content": "partial"}, "finish_reason": "error"}]},
            "returned an error",
        ),
        (
            {"choices": [{"message": {"content": "partial"}, "error": {"message": "upstream"}}]},
            "upstream",
        ),
    ],
)
def test_a_200_without_a_usable_answer_raises_llm_error(session, response, sleeps, body, message):
    http = session([response(200, body)])

    with pytest.raises(LLMError, match=message):
        deepseek_client(http, sleeps).complete(MESSAGES, 10, 0.0)


def test_a_non_json_200_raises_llm_error(session, response, sleeps):
    http = session([response(200, None, text="<html>gateway</html>")])

    with pytest.raises(LLMError, match="non-JSON"):
        deepseek_client(http, sleeps).complete(MESSAGES, 10, 0.0)


# The API key stays out of every message.


@pytest.mark.parametrize("client_class", [DeepSeekClient, OpenRouterClient])
@pytest.mark.parametrize("bad_key", ["", "key\n", "key\r", "two words", "ключ", "tab\tkey"])
def test_a_malformed_key_is_rejected_without_echoing_it(client_class, bad_key):
    config = DeepSeekLLMConfig() if client_class is DeepSeekClient else OpenRouterLLMConfig()

    with pytest.raises(LLMError, match="_API_KEY is empty or malformed") as excinfo:
        client_class(bad_key, config)

    if bad_key:
        assert bad_key not in str(excinfo.value)


def test_a_key_with_a_newline_never_reaches_requests():
    # With a real session, `requests` would raise InvalidHeader quoting the
    # whole header value. The client must refuse the key before that.
    with pytest.raises(LLMError) as excinfo:
        DeepSeekClient(API_KEY + "\n", DeepSeekLLMConfig(), session=requests.Session())

    assert API_KEY not in str(excinfo.value)
    assert excinfo.value.__cause__ is None


def test_an_openrouter_key_is_not_sent_to_the_deepseek_platform(session, sleeps):
    http = session([])
    openrouter_key = "sk-or-v1-test-only-not-a-real-key"

    with pytest.raises(LLMError, match="holds an OpenRouter key") as excinfo:
        DeepSeekClient(openrouter_key, DeepSeekLLMConfig(), session=http, sleep=sleeps.sleep)

    assert openrouter_key not in str(excinfo.value)
    assert http.requests == []


def test_the_key_is_redacted_from_errors_that_quote_it(session, response, sleeps):
    quoting_failures = [
        requests.exceptions.InvalidHeader(f"Invalid header value: 'Bearer {API_KEY}'"),
        response(401, {"error": {"message": f"invalid key {API_KEY}"}}),
        response(200, {"error": {"message": f"rejected {API_KEY}"}}),
    ]
    for failure in quoting_failures:
        with pytest.raises(LLMError) as excinfo:
            deepseek_client(session([failure]), sleeps).complete(MESSAGES, 10, 0.0)

        assert API_KEY not in str(excinfo.value)
        assert "<redacted>" in str(excinfo.value)
        # A cause that quotes the key must not be chained into the traceback.
        assert excinfo.value.__cause__ is None


def test_ordinary_errors_keep_sanitized_details_without_chaining(session, sleeps):
    with pytest.raises(LLMError) as excinfo:
        deepseek_client(session([requests.ConnectionError("reset")]), sleeps).complete(
            MESSAGES, 10, 0.0
        )

    assert "ConnectionError: reset" in str(excinfo.value)
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True
    assert API_KEY not in str(excinfo.value)


@pytest.mark.parametrize("exception_class", [requests.Timeout, requests.ConnectionError])
@pytest.mark.parametrize("location", ["message", "cause", "context"])
def test_transport_tracebacks_never_expose_the_key(session, sleeps, exception_class, location):
    failure = exception_class(f"rejected {API_KEY}" if location == "message" else "failed")
    if location == "cause":
        failure.__cause__ = ValueError(f"rejected {API_KEY}")
    elif location == "context":
        failure.__context__ = ValueError(f"rejected {API_KEY}")

    with pytest.raises(LLMError) as excinfo:
        deepseek_client(session([failure]), sleeps).complete(MESSAGES, 10, 0.0)

    rendered = "".join(traceback.format_exception(excinfo.value))
    assert API_KEY not in rendered
    assert excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ is True


@pytest.mark.parametrize("error_location", ["http", "top_level", "choice"])
def test_keys_are_redacted_before_error_text_is_truncated(session, response, sleeps, error_location):
    detail = "x" * 490 + API_KEY
    if error_location == "http":
        failure = response(401, None, text=detail)
    elif error_location == "top_level":
        failure = response(200, {"error": detail})
    else:
        failure = response(200, {"choices": [{"message": {"content": "partial"}, "error": detail}]})

    with pytest.raises(LLMError) as excinfo:
        deepseek_client(session([failure]), sleeps).complete(MESSAGES, 10, 0.0)

    assert API_KEY not in str(excinfo.value)
    assert API_KEY[:10] not in str(excinfo.value)
    assert "<redacted>" in str(excinfo.value)


def test_json_decode_tracebacks_never_expose_the_key(session, response, sleeps, monkeypatch):
    failure = response(200)

    def invalid_json():
        raise requests.exceptions.JSONDecodeError(f"invalid {API_KEY}", "body", 0)

    monkeypatch.setattr(failure, "json", invalid_json)

    with pytest.raises(LLMError, match="non-JSON") as excinfo:
        deepseek_client(session([failure]), sleeps).complete(MESSAGES, 10, 0.0)

    assert API_KEY not in "".join(traceback.format_exception(excinfo.value))


# Factory.


def secrets(deepseek=None, openrouter=None):
    return Secrets(
        deepseek_api_key=SecretStr(deepseek) if deepseek else None,
        openrouter_api_key=SecretStr(openrouter) if openrouter else None,
    )


def test_factory_defaults_to_the_deepseek_platform():
    client = create_chat_client(Settings(), secrets(deepseek=API_KEY), route="cloud")

    assert isinstance(client, DeepSeekClient)


def test_factory_builds_the_requested_route_and_provider():
    settings, keys = Settings(), secrets(deepseek=API_KEY, openrouter=API_KEY)

    assert isinstance(
        create_chat_client(settings, keys, route="cloud", cloud_provider="openrouter"),
        OpenRouterClient,
    )
    assert isinstance(
        create_chat_client(settings, keys, route="cloud", cloud_provider="deepseek"),
        DeepSeekClient,
    )
    assert isinstance(create_chat_client(settings, keys, route="local"), LlamaServerClient)


def test_factory_follows_the_configuration(monkeypatch):
    keys = secrets(deepseek=API_KEY, openrouter=API_KEY)

    monkeypatch.setenv("RAGSHELF_LLM__ROUTE", "local")
    assert isinstance(create_chat_client(Settings(), keys), LlamaServerClient)
    monkeypatch.setenv("RAGSHELF_LLM__ROUTE", "cloud")
    monkeypatch.setenv("RAGSHELF_LLM__CLOUD_PROVIDER", "openrouter")
    assert isinstance(create_chat_client(Settings(), keys), OpenRouterClient)
    monkeypatch.setenv("RAGSHELF_LLM__CLOUD_PROVIDER", "deepseek")
    assert isinstance(create_chat_client(Settings(), keys), DeepSeekClient)


@pytest.mark.parametrize(
    ("provider", "variable"),
    [("deepseek", "DEEPSEEK_API_KEY"), ("openrouter", "OPENROUTER_API_KEY")],
)
def test_factory_fails_loudly_without_the_providers_key(provider, variable):
    # The other provider's key does not help.
    other = {"openrouter": API_KEY} if provider == "deepseek" else {"deepseek": API_KEY}

    with pytest.raises(LLMError, match=f"{variable} is not set"):
        create_chat_client(Settings(), secrets(**other), route="cloud", cloud_provider=provider)


def test_the_local_route_needs_no_key():
    client = create_chat_client(Settings(), secrets(), route="local")

    assert isinstance(client, LlamaServerClient)
