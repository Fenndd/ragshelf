from ragshelf.store.dynamic_vector_store import DynamicVectorStore
from ragshelf.retrieval.reranker import Reranker
import json


query = "What is love addiction?"

# Загружаем базу и ищем
# --- 1. Загружаем статьи и делаем поиск ---
store = DynamicVectorStore()
articles = store.load_articles(["article_1", "article_2", "article_3", "article_4"])
store.build_index(articles)

# Векторный поиск (top-k = 20)
top_chunks = store.search(query, k=20)

# LLM rerank
reranker = Reranker(method="llm")
reranked = reranker.rerank(query, top_chunks)

print("\n🔍 LLM reranked results:")
for i, chunk in enumerate(reranked, 1):
    print(f"{i}. ID: {chunk['id']} | Rerank Score: {chunk.get('rerank_score', 'N/A')}")


for r in reranked:
    r.pop("embedding", None)

with open("reranked_llm.json", "w", encoding="utf-8") as f:
    json.dump(reranked, f, indent=2, ensure_ascii=False)

print("✅ Готово.")

