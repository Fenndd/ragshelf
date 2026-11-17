import pytest
from fakes import ScriptedChatClient

from ragshelf.generation.rag_chain import generate_paragraph
from ragshelf.llm import LLMError

MESSAGES = [{"role": "user", "content": "one two three"}]


def test_scripted_client_replays_answers_and_records_calls():
    client = ScriptedChatClient(["first", "second answer"], model="m", route="local")

    first = client.complete(MESSAGES, max_tokens=5, temperature=0.0)
    second = client.complete(MESSAGES, max_tokens=9, temperature=0.5)

    assert (first.text, first.model, first.route) == ("first", "m", "local")
    assert first.usage.total_tokens == first.usage.prompt_tokens + first.usage.completion_tokens
    assert second.text == "second answer"
    assert [(call.max_tokens, call.temperature) for call in client.calls] == [(5, 0.0), (9, 0.5)]
    assert client.calls[0].messages == MESSAGES


def test_scripted_client_raises_scripted_errors_and_when_exhausted():
    client = ScriptedChatClient([LLMError("scripted failure")])

    with pytest.raises(LLMError, match="scripted failure"):
        client.complete(MESSAGES, 5, 0.0)
    with pytest.raises(LLMError, match="no more answers"):
        client.complete(MESSAGES, 5, 0.0)


def test_generate_paragraph_sends_the_query_and_chunks_to_the_client():
    client = ScriptedChatClient(["Черновик абзаца."])

    text = generate_paragraph("влияние X на Y", ["chunk one", "chunk two"], client=client)

    assert text == "Черновик абзаца."
    (call,) = client.calls
    assert [message["role"] for message in call.messages] == ["system", "user"]
    assert "влияние X на Y" in call.messages[1]["content"]
    assert "chunk one\n\nchunk two" in call.messages[1]["content"]


def test_generate_paragraph_propagates_llm_errors():
    client = ScriptedChatClient([LLMError("HTTP 500")])

    with pytest.raises(LLMError):
        generate_paragraph("q", ["chunk"], client=client)
