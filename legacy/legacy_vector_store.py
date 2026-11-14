from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle
from typing import List

class VectorStore:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.text_chunks = []

    def build_index(self, chunks: List[str]):
        print("🔄 Векторизация чанков...")
        self.text_chunks = chunks
        embeddings = self.model.encode(chunks, show_progress_bar=True)
        dimension = embeddings[0].shape[0]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings))
        print(f"✅ Индекс создан. Всего чанков: {len(chunks)}")

    def save_index(self, index_path="faiss.index", chunks_path="chunks.pkl"):
        faiss.write_index(self.index, index_path)
        with open(chunks_path, "wb") as f:
            pickle.dump(self.text_chunks, f)
        print(f"💾 Индекс сохранён: {index_path}")
        print(f"💾 Чанки сохранены: {chunks_path}")

    def load_index(self, index_path="faiss.index", chunks_path="chunks.pkl"):
        self.index = faiss.read_index(index_path)
        with open(chunks_path, "rb") as f:
            self.text_chunks = pickle.load(f)
        print("📂 Индекс и чанки загружены.")

    def search(self, query: str, top_k: int = 3):
        print(f"🔍 Поиск по запросу: {query}")
        query_vector = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_vector), top_k)
        results = [self.text_chunks[i] for i in indices[0]]
        return results
