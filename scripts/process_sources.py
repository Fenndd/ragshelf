import os
import json
import shutil
from pathlib import Path
from ragshelf.loaders.universal_loader import extract_text_from_pdf, split_references, clean_spacing_and_hyphens, remove_irrelevant_sections
from ragshelf.processing.chunker import split_text
from ragshelf.processing.cluster_hdbscan import cluster_chunks
from ragshelf.embeddings.combined_embedder import CombinedEmbedder
import numpy as np


def get_next_article_index(source_dir: str) -> int:
    existing = [f for f in os.listdir(source_dir) if f.startswith("article_") and os.path.isdir(os.path.join(source_dir, f))]
    indices = [int(f.split("_")[1]) for f in existing if f.split("_")[1].isdigit()]
    return max(indices, default=0) + 1


def load_metadata(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def process_single_source(folder_path: str, target_dir: str, article_index: int):
    # --- Определения путей ---
    article_id = f"article_{article_index}"
    article_path = os.path.join(target_dir, article_id)
    os.makedirs(article_path, exist_ok=True)

    # --- Найти PDF и metadata.json ---
    files = os.listdir(folder_path)
    pdf_file = next((f for f in files if f.lower().endswith(".pdf")), None)
    metadata_file = next((f for f in files if f == "metadata.json"), None)

    if not pdf_file or not metadata_file:
        print(f"❌ Пропуск: {folder_path} — отсутствует PDF или metadata.json")
        return None

    # --- Копирование ---
    shutil.copy(os.path.join(folder_path, pdf_file), os.path.join(article_path, pdf_file))
    shutil.copy(os.path.join(folder_path, metadata_file), os.path.join(article_path, "metadata.json"))

    metadata = load_metadata(os.path.join(folder_path, metadata_file))
    authors = metadata.get("authors", "")
    year = metadata.get("year", "")

    # --- Чтение текста и выделение источников ---
    raw_text = extract_text_from_pdf(os.path.join(article_path, pdf_file), method="columns")
    main_text, references = split_references(raw_text)
    main_text = clean_spacing_and_hyphens(main_text)

    # --- Удаление нерелевантных секций с логом ---
    main_text, removed_sections_log = remove_irrelevant_sections(main_text)
    with open(os.path.join(article_path, "removed_sections_log.txt"), "w", encoding="utf-8") as f:
        for section in removed_sections_log:
            f.write(section + "\n\n" + "-" * 60 + "\n\n")

    # --- Сохранение источников ---
    references_text = clean_spacing_and_hyphens(references)
    with open(os.path.join(article_path, "references.txt"), "w", encoding="utf-8") as f:
        f.write(references_text)


    # --- Обработка текста ---
    chunks, removed_chunks_log = split_text(main_text)
    with open(os.path.join(article_path, "removed_chunks_log.txt"), "w", encoding="utf-8") as f:
        for reasoned in removed_chunks_log:
            f.write(reasoned + "\n\n" + "-" * 60 + "\n\n")
    chunks = cluster_chunks(chunks)

    # --- Сборка чанков ---
    final_chunks = []
    for j, chunk in enumerate(chunks):
        final_chunks.append({
            "id": f"{article_index}_{j}",
            "text": chunk.strip(),
            "source": f"data/library/{article_id}/references.txt",
            "authors": authors,
            "year": year
        })

    with open(os.path.join(article_path, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(final_chunks, f, indent=2, ensure_ascii=False)

    # --- Эмбеддинги ---
    embedder = CombinedEmbedder()
    embeddings = embedder.encode([ch["text"] for ch in final_chunks])
    np.save(os.path.join(article_path, "embeddings.npy"), embeddings)

    return article_id, metadata


# def update_manifest(manifest_path: str, article_id: str, metadata: dict):
#     if os.path.exists(manifest_path):
#         with open(manifest_path, "r", encoding="utf-8") as f:
#             manifest = json.load(f)
#     else:
#         manifest = {}
#
#     manifest[article_id] = {
#         "authors": metadata.get("authors", ""),
#         "year": metadata.get("year", ""),
#         "path": f"data/library/{article_id}/"
#     }
#
#     with open(manifest_path, "w", encoding="utf-8") as f:
#         json.dump(manifest, f, indent=2, ensure_ascii=False)


# --- Основная точка входа ---
def process_all_sources(source_input_dir: str, source_target_dir: str = "data/library"):
    os.makedirs(source_target_dir, exist_ok=True)
    # manifest_path = os.path.join(source_target_dir, "manifest.json")
    next_index = get_next_article_index(source_target_dir)

    folders = [os.path.join(source_input_dir, f) for f in os.listdir(source_input_dir) if os.path.isdir(os.path.join(source_input_dir, f))]
    for folder in folders:
        result = process_single_source(folder, source_target_dir, next_index)
        if result:
            article_id, metadata = result
            # update_manifest(manifest_path, article_id, metadata)
            next_index += 1

process_all_sources("data/inbox")