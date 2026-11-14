from typing import List, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from ragshelf.embeddings.combined_embedder import CombinedEmbedder
import numpy as np
import tiktoken


def count_tokens(text: str, tokenizer) -> int:
    return len(tokenizer.encode(text))


def merge_semantic_chunks(
    chunks: List[str],
    embedder: CombinedEmbedder,
    tokenizer,
    max_tokens: int = 512,
    similarity_thresholds: List[float] = [0.55, 0.5, 0.47],
) -> Tuple[List[str], List[str]]:
    """
    Многопроходное объединение чанков по смыслу с финальной обработкой одиночных и локально-связанных коротких чанков.
    """
    logs = []
    for pass_num, threshold in enumerate(similarity_thresholds, start=1):
        i = 0
        merged_chunks = []
        used = set()

        while i < len(chunks):
            if i in used:
                i += 1
                continue

            curr = chunks[i]
            curr_len = count_tokens(curr, tokenizer)
            vec1 = embedder.encode([curr])[0].reshape(1, -1)
            merged = curr
            merged_indices = [i]

            j = i + 1
            while j < len(chunks):
                if j in used:
                    j += 1
                    continue

                candidate = chunks[j]
                candidate_len = count_tokens(candidate, tokenizer)
                if curr_len + candidate_len > max_tokens:
                    break

                vec2 = embedder.encode([candidate])[0].reshape(1, -1)
                sim = cosine_similarity(vec1, vec2)[0][0]
                if sim >= threshold:
                    merged += "\n\n" + candidate
                    curr_len += candidate_len
                    used.add(j)
                    merged_indices.append(j)
                j += 1

            merged_chunks.append(merged.strip())
            logs.append(f"[PASS {pass_num}] merged chunks {merged_indices}")
            i += 1

        chunks = merged_chunks

    # ===== 🟡 Финальный merge для одиночных коротких чанков =====
    final_chunks = []
    used = set()
    embeddings = embedder.encode(chunks)
    for i in range(len(chunks)):
        if i in used:
            continue
        curr = chunks[i]
        curr_len = count_tokens(curr, tokenizer)
        if curr_len >= 150:
            final_chunks.append(curr)
            continue

        vec1 = embeddings[i].reshape(1, -1)
        best_sim = 0
        best_idx = -1
        for j in range(len(chunks)):
            if j == i or j in used:
                continue
            vec2 = embeddings[j].reshape(1, -1)
            sim = cosine_similarity(vec1, vec2)[0][0]
            if sim > best_sim and sim >= 0.48 and curr_len + count_tokens(chunks[j], tokenizer) <= max_tokens:
                best_sim = sim
                best_idx = j

        if best_idx != -1:
            merged = "\n\n".join([curr, chunks[best_idx]])
            final_chunks.append(merged.strip())
            used.add(i)
            used.add(best_idx)
            logs.append(f"[FINAL MERGE] chunks {i} + {best_idx} (sim={best_sim:.2f})")
        else:
            final_chunks.append(curr)

    return final_chunks, logs


def deduplicate_chunks(chunks: List[str], embedder: CombinedEmbedder, threshold: float = 0.92) -> List[str]:
    """
    Удаляет дублирующие чанки (по смыслу). Оставляет только уникальные.
    """
    unique = []
    embeddings = embedder.encode(chunks)
    norm_embeds = [v / np.linalg.norm(v) for v in embeddings]
    used = set()

    for i in range(len(chunks)):
        if i in used:
            continue
        unique.append(chunks[i])
        for j in range(i + 1, len(chunks)):
            if j in used:
                continue
            sim = cosine_similarity([norm_embeds[i]], [norm_embeds[j]])[0][0]
            if sim >= threshold:
                used.add(j)

    return unique

def symmetric_merge_chunks(
    chunks: List[str],
    embedder: CombinedEmbedder,
    tokenizer,
    max_tokens: int = 512,
    similarity_threshold: float = 0.5
) -> Tuple[List[str], List[str]]:
    """
    Симметричная кластеризация чанков на основе полной similarity-матрицы.
    Все чанки группируются по смыслу и объединяются в пределах max_tokens.
    """
    logs = []
    embeddings = embedder.encode(chunks)
    norm_embeds = [v / np.linalg.norm(v) for v in embeddings]
    sim_matrix = cosine_similarity(norm_embeds)

    used = set()
    merged_chunks = []

    for i in range(len(chunks)):
        if i in used:
            continue

        group = [i]
        current_len = count_tokens(chunks[i], tokenizer)

        for j in range(len(chunks)):
            if j == i or j in used:
                continue
            if sim_matrix[i][j] >= similarity_threshold:
                candidate_len = count_tokens(chunks[j], tokenizer)
                if current_len + candidate_len <= max_tokens:
                    group.append(j)
                    current_len += candidate_len

        merged_text = "\n\n".join([chunks[k] for k in sorted(group)])
        for idx in group:
            used.add(idx)

        merged_chunks.append(merged_text.strip())
        logs.append(f"[SYMMETRIC] merged chunks {sorted(group)}")

    return merged_chunks, logs



def cluster_chunks(
    chunks: List[str],
    max_tokens_per_chunk: int = 512,
    mode: str = "greedy"
) -> Tuple[List[str], List[str]]:
    """
    Универсальная кластеризация:
    - greedy: многопроходная линейная агрегация по смыслу;
    - symmetric: глобальная кластеризация на основе similarity-матрицы.
    """
    if not chunks:
        return [], []

    embedder = CombinedEmbedder()
    tokenizer = tiktoken.get_encoding("cl100k_base")

    if mode == "symmetric":
        merged_chunks, merge_log = symmetric_merge_chunks(
            chunks,
            embedder,
            tokenizer,
            max_tokens=max_tokens_per_chunk,
            similarity_threshold=0.5
        )
    else:
        merged_chunks, merge_log = merge_semantic_chunks(
            chunks,
            embedder,
            tokenizer,
            max_tokens=max_tokens_per_chunk,
            similarity_thresholds=[0.55, 0.5, 0.47]
        )

    unique_chunks = deduplicate_chunks(merged_chunks, embedder, threshold=0.92)
    unique_chunks.sort(key=lambda x: (-count_tokens(x, tokenizer), x))

    return unique_chunks, merge_log

