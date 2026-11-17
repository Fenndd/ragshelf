"""A fake HTTP layer for the LLM client tests: no request leaves the process."""

import json as json_module

import pytest


class FakeResponse:
    def __init__(self, status_code=200, body=None, headers=None, text=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}
        self.text = text if text is not None else json_module.dumps(body)

    def json(self):
        if self._body is None:
            raise ValueError("no JSON body")
        return self._body


class FakeSession:
    """Replays outcomes in order; an exception instance is raised instead of returned."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.requests = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.requests.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def chat_body(text="An answer.", model="served-model", usage=(11, 7, 18), finish_reason="stop"):
    body = {
        "model": model,
        "choices": [
            {"message": {"role": "assistant", "content": text}, "finish_reason": finish_reason}
        ],
    }
    if usage is not None:
        prompt, completion, total = usage
        body["usage"] = {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": total,
        }
    return body


@pytest.fixture
def ok():
    """Build a 200 response carrying a chat completion."""
    return lambda **kwargs: FakeResponse(200, chat_body(**kwargs))


@pytest.fixture
def response():
    return FakeResponse


@pytest.fixture
def session():
    return FakeSession


class RecordedSleeps(list):
    """The delays a client asked to wait; `sleep` stands in for `time.sleep`."""

    def sleep(self, seconds):
        self.append(seconds)


@pytest.fixture
def sleeps():
    return RecordedSleeps()
