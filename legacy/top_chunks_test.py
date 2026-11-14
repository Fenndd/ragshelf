import json
import os

from ragshelf.store.dynamic_vector_store import DynamicVectorStore
from ragshelf.retrieval.reranker import Reranker
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def remove_duplicates(chunks: list[dict]) -> list[dict]:
    seen_ids = set()
    unique_chunks = []
    for chunk in chunks:
        if chunk["id"] not in seen_ids:
            seen_ids.add(chunk["id"])
            unique_chunks.append(chunk)
    return unique_chunks

query = "What is love addiction?"

if __name__ == "__main__":
    # --- 1. Загружаем статьи и делаем поиск ---
    store = DynamicVectorStore()
    articles = store.load_articles(["article_1", "article_2", "article_3", "article_4"])
    store.build_index(articles)

    # Векторный поиск (top-k = 20)
    top_chunks = store.search(query, k=20)

    # --- 2. Реранжирование: Cross-Encoder ---
    reranker_ce = Reranker(method="cross-encoder")
    reranked_ce = reranker_ce.rerank(query, top_chunks.copy())

    reranked_ce = sorted(reranked_ce, key=lambda x: x["rerank_score"], reverse=True)
    for r in reranked_ce:
        for r in reranked_ce:
            r.pop("embedding", None)

    reranked_ce = reranked_ce[:5]

    with open("reranked_cross_encoder.json", "w", encoding="utf-8") as f:
        json.dump(reranked_ce, f, indent=2, ensure_ascii=False)

    # --- 3. Реранжирование: GPT (DeepSeek) ---
    reranker_llm = Reranker(method="llm")
    reranked_llm = reranker_llm.rerank(query, top_chunks.copy())

    reranked_llm = sorted(reranked_llm, key=lambda x: x["rerank_score"], reverse=True)
    for r in reranked_llm:
        r.pop("embedding", None)

    reranked_llm = reranked_llm[:5]

    with open("reranked_llm.json", "w", encoding="utf-8") as f:
        json.dump(reranked_llm, f, indent=2, ensure_ascii=False)

    print("✅ Готово. Два rerank результата сохранены в JSON-файлы.")

