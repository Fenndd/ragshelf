import os
import json
import numpy as np
import faiss
from typing import List, Dict
from ragshelf.embeddings.combined_embedder import CombinedEmbedder
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class DynamicVectorStore:
    def __init__(self, source_dir: str = "data/library"):
        self.source_dir = source_dir
        self.index = None
        self.index_id_to_chunk: List[Dict] = []

    def load_articles(self, article_ids: List[str]) -> List[dict]:
        """
        Загружает чанки и эмбендинги только из указанных article_N.
        Возвращает список словарей с ключами: id, text, embedding, authors, year, source.
        """
        articles = []

        for article_id in article_ids:
            article_path = os.path.join(self.source_dir, article_id)
            chunks_path = os.path.join(article_path, "chunks.json")
            embeddings_path = os.path.join(article_path, "embeddings.npy")

            if not os.path.exists(chunks_path) or not os.path.exists(embeddings_path):
                print(f"⚠️ Пропуск {article_id} — отсутствуют данные")
                continue

            with open(chunks_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            embeddings = np.load(embeddings_path)

            if len(chunks) != len(embeddings):
                print(f"❌ Несоответствие размеров в {article_id}: {len(chunks)} vs {len(embeddings)}")
                continue

            for chunk, embedding in zip(chunks, embeddings):
                articles.append({
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "embedding": embedding / np.linalg.norm(embedding),  # нормализация
                    "authors": chunk.get("authors", ""),
                    "year": chunk.get("year", ""),
                    "source": chunk.get("source", "")
                })

        return articles

    def build_index(self, articles: List[dict]):
        """
        Строит FAISS IndexFlatIP индекс по переданным эмбеддингам.
        """
        if not articles:
            raise ValueError("Нет данных для индексации")

        dim = len(articles[0]["embedding"])
        self.index = faiss.IndexFlatIP(dim)

        embeddings_matrix = np.array([a["embedding"] for a in articles], dtype=np.float32)
        self.index.add(embeddings_matrix)

        self.index_id_to_chunk = articles  # сохраняем всё, не только текст

    def search(self, query: str, k: int = 5) -> List[dict]:
        """
        Возвращает top-k чанков с метаданными: text, id, authors, year, source, score.
        """
        if self.index is None:
            raise RuntimeError("Индекс ещё не построен")

        embedder = CombinedEmbedder()
        query_embedding = embedder.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        query_embedding = np.expand_dims(query_embedding.astype(np.float32), axis=0)
        scores, indices = self.index.search(query_embedding, k)

        results = []
        for i, score in zip(indices[0], scores[0]):
            if i < len(self.index_id_to_chunk):
                item = self.index_id_to_chunk[i].copy()
                item["score"] = float(score)
                results.append(item)

        return results
