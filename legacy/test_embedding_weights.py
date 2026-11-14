# test_embedding_weights.py

from ragshelf.loaders.universal_loader import extract_text_from_pdf
from ragshelf.processing.chunker import split_text
from ragshelf.processing.cluster_hdbscan import cluster_chunks
from ragshelf.embeddings.combined_embedder import CombinedEmbedder
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# === 1. Загрузка и обработка PDF ===
pdf_path = "healthpsychologyresearch_2023_11_70218.pdf"
text = extract_text_from_pdf(pdf_path, method="columns")
chunks = split_text(text)
chunks = cluster_chunks(chunks)

# === 2. Подготовка эмбеддеров ===
embedder = CombinedEmbedder()
bge_embeddings = embedder.bge.encode(chunks)
scibert_embeddings = embedder.scibert.encode(chunks)

# === 3. Ввод пользовательского запроса ===
query = "Как любовная зависимость связана с привязанностью?"
query_embed_bge = embedder.bge.encode([query])
query_embed_scibert = embedder.scibert.encode([query])

# === 4. Тестируем разные веса ===
alphas = [0.0, 0.25, 0.5, 0.75, 1.0]

for alpha in alphas:
    # Взвешенное объединение + нормализация
    chunk_vectors = np.concatenate([alpha * bge_embeddings, (1 - alpha) * scibert_embeddings], axis=1)
    chunk_vectors /= np.linalg.norm(chunk_vectors, axis=1, keepdims=True)

    query_vector = np.concatenate([alpha * query_embed_bge, (1 - alpha) * query_embed_scibert], axis=1)
    query_vector /= np.linalg.norm(query_vector)

    # Косинусная близость
    scores = cosine_similarity(query_vector.reshape(1, -1), chunk_vectors)[0]
    top_indices = scores.argsort()[-3:][::-1]

    print(f"\n🔎 Top-3 результаты для alpha = {alpha}:\n")
    for i in top_indices:
        print(f"[score = {scores[i]:.4f}] {chunks[i][:300]}...\n")

