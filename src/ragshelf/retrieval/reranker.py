import numpy as np
from sentence_transformers import CrossEncoder
from ragshelf.config import load_settings
from ragshelf.llm import create_chat_client

class Reranker:
    def __init__(self, method: str = "cross-encoder"):
        self.method = method

        if method == "cross-encoder":
            self.model = CrossEncoder("cross-encoder/nli-deberta-v3-base")

        elif method == "llm":
            # Raises LLMError if the configured route has no credentials.
            self.llm = create_chat_client(load_settings())

        else:
            raise ValueError("Unknown rerank method. Use 'cross-encoder' or 'llm'.")

    def rerank(self, query: str, results: list[dict]) -> list[dict]:
        if self.method == "cross-encoder":
            return self._rerank_with_cross_encoder(query, results)
        elif self.method == "llm":
            return self._rerank_with_llm(query, results)

    # РАБОТАЕТ ПЛОХО
    def _rerank_with_cross_encoder(self, query: str, results: list[dict]) -> list[dict]:
        pairs = [(query, r["text"]) for r in results]
        scores = self.model.predict(pairs)  # вернёт список из [c, n, e] — 3 класса

        # Берём только значение entailment (последний класс)
        if isinstance(scores[0], (list, tuple, np.ndarray)):
            scores = [float(s[-1]) for s in scores]  # entailment score
        else:
            scores = [float(s) for s in scores]  # fallback

        for r, s in zip(results, scores):
            r["rerank_score"] = s

        return sorted(results, key=lambda x: x["rerank_score"], reverse=True)

    def _rerank_with_llm(self, query: str, results: list[dict]) -> list[dict]:
        # Генерация пронумерированных чанков
        indexed_chunks = [f"[{i+1}] {r['text']}" for i, r in enumerate(results)]
        context = "\n\n".join(indexed_chunks)

        prompt = (
            f"Ты научный ассистент. Вот вопрос пользователя: \"{query}\"\n"
            f"Ниже представлены фрагменты из научных источников. \n"
            f"Отранжируй их от самого полезного до наименее полезного для ответа на вопрос.\n"
            f"Верни список уникальных номеров через запятую, без повторений и других комментариев.\n\n"
            f"{context}"
        )

        response = self.llm.complete(
            [{"role": "user", "content": prompt}], max_tokens=200, temperature=0.0
        ).text

        # Парсим список индексов, например: "3, 1, 4, 2, 5"
        import re
        index_matches = re.findall(r"\d+", response)
        indices = [int(i)-1 for i in index_matches if 0 <= int(i)-1 < len(results)]

        seen = set()
        unique_indices = []
        for i in indices:
            if i not in seen:
                seen.add(i)
                unique_indices.append(i)

        reranked = []
        for rank, i in enumerate(unique_indices):
            r = results[i]
            r["rerank_score"] = len(unique_indices) - rank
            reranked.append(r)

        return reranked
