from ragshelf.config import load_settings
from ragshelf.llm import ChatClient, create_chat_client

SYSTEM_PROMPT = "Ты научный ассистент. Пиши строго, академически, с учётом источников."


def generate_paragraph(
    query: str, context_chunks: list, client: ChatClient | None = None
) -> str:
    """Draft a paragraph from the chunks. Raises `LLMError` if the request fails."""
    if client is None:
        client = create_chat_client(load_settings())

    context = "\n\n".join(context_chunks)
    prompt = (
        f"На основе следующих фрагментов научных источников напиши черновик абзаца по теме запроса: '{query}'.\n\n"
        f"{context}"
    )

    completion = client.complete(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.3,
    )
    return completion.text
