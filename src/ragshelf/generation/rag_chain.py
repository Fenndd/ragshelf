import os
from dotenv import load_dotenv
from ragshelf.llm.deepseek_llm import DeepSeekLLM

load_dotenv()

def generate_paragraph(query: str, context_chunks: list) -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    llm = DeepSeekLLM(api_key=api_key)

    context = "\n\n".join(context_chunks)
    prompt = (
        f"На основе следующих фрагментов научных источников напиши черновик абзаца по теме запроса: '{query}'.\n\n"
        f"{context}"
    )

    return llm.generate(prompt)
