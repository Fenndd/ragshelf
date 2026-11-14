import numpy as np
from tqdm import tqdm
from sentence_transformers import util
from ragshelf.embeddings.combined_embedder import CombinedEmbedder
from ragshelf.loaders.universal_loader import extract_text_from_pdf
from ragshelf.processing.chunker import split_text
from ragshelf.processing.cluster_hdbscan import cluster_chunks
import torch

# 🔧 Настройка
WEIGHT_COMBINATIONS = [(0.7, 0.3), (0.5, 0.5), (0.3, 0.7)]
TEST_QUERIES = [
    "What is emotional dependency in relationships?",
    "Attachment disorders in romantic partnerships",
    "How is addiction classified in psychology?"
]
TOP_K = 3

# 📦 Загрузка чанков
# 1. Загружаем текст
text = extract_text_from_pdf("healthpsychologyresearch_2023_11_70218.pdf", "columns")
chunks = split_text(text)
chunks = cluster_chunks(chunks)
texts = chunks

# 🔍 Векторизация всех чанков для всех весов
embedder = CombinedEmbedder()
chunk_vectors_by_weight = {}

print("\n📐 Векторизация всех чанков...")
for w_bge, w_sci in WEIGHT_COMBINATIONS:
    print(f"→ Вес BGE: {w_bge}, SciBERT: {w_sci}")
    vectors = embedder.encode(texts, weight_bge=w_bge, weight_scibert=w_sci)
    chunk_vectors_by_weight[(w_bge, w_sci)] = torch.tensor(vectors)

# 🧪 Векторизация запросов и сравнение результатов
print("\n🔍 Сравнение запросов:")
for query in TEST_QUERIES:
    print(f"\n🧠 Запрос: {query}")
    query_vecs = {}
    for w_bge, w_sci in WEIGHT_COMBINATIONS:
        query_vec = embedder.encode([query], weight_bge=w_bge, weight_scibert=w_sci)[0]
        query_vecs[(w_bge, w_sci)] = torch.tensor(query_vec)

    for (w_bge, w_sci), chunk_matrix in chunk_vectors_by_weight.items():
        query_vec = query_vecs[(w_bge, w_sci)]
        cos_scores = util.cos_sim(query_vec, chunk_matrix)[0]
        top_indices = torch.topk(cos_scores, k=TOP_K).indices.tolist()
        print(f"\n🔹 Вес BGE: {w_bge}, SciBERT: {w_sci}")
        for idx in top_indices:
            print(f" - [{cos_scores[idx]:.4f}] {texts[idx][:150]}...\n")
