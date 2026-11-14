from typing import List
import hdbscan
from sentence_transformers import SentenceTransformer
import tiktoken
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def refine_short_chunks(short_chunks: List[str], model, tokenizer, max_tokens: int = 512) -> List[str]:
    """
    Объединяет подряд идущие короткие чанки, если они схожи по смыслу (cosine similarity > 0.7)
    и не превышают лимит по токенам.
    """
    refined = []
    i = 0
    while i < len(short_chunks):
        curr = short_chunks[i]
        curr_len = len(tokenizer.encode(curr))

        if i + 1 < len(short_chunks):
            next_chunk = short_chunks[i + 1]
            combined = curr + "\n\n" + next_chunk
            combined_len = len(tokenizer.encode(combined))

            if combined_len <= max_tokens:
                vec1 = model.encode([curr])[0].reshape(1, -1)
                vec2 = model.encode([next_chunk])[0].reshape(1, -1)
                sim = cosine_similarity(vec1, vec2)[0][0]

                if sim > 0.7:
                    refined.append(combined.strip())
                    i += 2
                    continue

        refined.append(curr)
        i += 1

    return refined


def cluster_chunks(chunks: List[str], max_tokens_per_chunk: int = 512) -> List[str]:
    """
    Принимает список чанков и возвращает список объединённых по теме чанков
    с учётом ограничения в 512 токенов на итоговый чанк.
    Если после кластеризации остаётся много коротких чанков — проводится линейное осмысленное объединение.
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(chunks, show_progress_bar=True)

    clusterer = hdbscan.HDBSCAN(min_cluster_size=2)
    labels = clusterer.fit_predict(embeddings)

    clustered = {}
    for i, (chunk, label) in enumerate(zip(chunks, labels)):
        if label == -1:
            label = f"noise_{i}"
        clustered.setdefault(label, []).append((i, chunk))

    tokenizer = tiktoken.get_encoding("cl100k_base")
    final_chunks = []

    for label in sorted(clustered.keys(), key=lambda x: str(x)):
        sorted_group = sorted(clustered[label], key=lambda x: x[0])
        buffer = ""
        for _, chunk in sorted_group:
            new_buffer = buffer + "\n\n" + chunk if buffer else chunk
            if len(tokenizer.encode(new_buffer)) <= max_tokens_per_chunk:
                buffer = new_buffer
            else:
                if buffer:
                    final_chunks.append(buffer.strip())
                buffer = chunk
        if buffer:
            final_chunks.append(buffer.strip())

    # Выделяем короткие чанки и проверяем их долю
    short_chunks = [c for c in final_chunks if len(tokenizer.encode(c)) < 150]
    long_chunks = [c for c in final_chunks if len(tokenizer.encode(c)) >= 150]

    if len(short_chunks) / len(final_chunks) > 0.3:
        refined_short = refine_short_chunks(short_chunks, model, tokenizer, max_tokens=max_tokens_per_chunk)
        final_chunks = long_chunks + refined_short

    return final_chunks

