import os

from ragshelf.processing.chunk_clusterization import cluster_chunks
from ragshelf.loaders.universal_loader import extract_text_from_pdf, split_references, clean_spacing_and_hyphens, remove_irrelevant_sections
from ragshelf.processing.chunker import split_text
from ragshelf.processing.token_counter import count_tokens_in_text

def process_pdf_in_folder(i: int, base_dir: str = "data/experiments/chunking"):
    folder_path = os.path.join(base_dir, str(i))
    if not os.path.isdir(folder_path):
        print(f"❌ Папка не найдена: {folder_path}")
        return

    # Найдём PDF
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"❌ PDF не найден в {folder_path}")
        return

    pdf_path = os.path.join(folder_path, pdf_files[0])
    print(f"📄 Обработка: {pdf_path}")

    # --- 1. Извлечение текста ---
    raw_text = extract_text_from_pdf(pdf_path, method="columns")

    #TEST
    # output_path = os.path.join(folder_path, "raw_text.txt")
    # with open(output_path, "w", encoding="utf-8") as f:
    #     f.write(raw_text)

    # --- 2. Деление на основной текст и литературу ---
    main_text, references = split_references(raw_text, i)

    # --- 3. Чистим литературу и сохраняем ---
    cleaned_refs = clean_spacing_and_hyphens(references)
    with open(os.path.join(folder_path, "references.txt"), "w", encoding="utf-8") as f:
        f.write(cleaned_refs)

    # --- 4. Чистим основной текст ---
    main_text = clean_spacing_and_hyphens(main_text)

    # --- Удаление нерелевантных секций с логом ---
    main_text, removed_sections_log = remove_irrelevant_sections(main_text)
    with open(os.path.join(folder_path, "removed_sections_log.txt"), "w", encoding="utf-8") as f:
        for section in removed_sections_log:
            f.write(section + "\n\n" + "-" * 60 + "\n\n")

    # --- 5. Делим на чанки ---
    chunks, removed_log = split_text(main_text)

    output_path = os.path.join(folder_path, "chunked_output.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for j, chunk in enumerate(chunks):
            f.write(f"--- ЧАНК {j + 1} ---\n")
            f.write(chunk + "\n")
            f.write("=" * 60 + "\n\n")

        # --- 7. Лог удалённых чанков ---
    removed_path = os.path.join(folder_path, "removed_chunks_log.txt")
    with open(removed_path, "w", encoding="utf-8") as f:
        for reasoned in removed_log:
            f.write(reasoned + "\n\n" + "-" * 60 + "\n\n")

    print(f"✅ Готово. Свежих чанков: {len(chunks)}, удалено: {len(removed_log)}")
    chunks_clust, cluster_log = cluster_chunks(chunks)

    max = 0
    for chunk in chunks_clust:
        if count_tokens_in_text(chunk) > max:
            max = count_tokens_in_text(chunk)

    print(f"Максимальная длина чанка: {max}")

    output2_path = os.path.join(folder_path, "chunked_clustered_output.txt")

    with open(output2_path, "w", encoding="utf-8") as f:
        for j, chunk in enumerate(chunks_clust):
            f.write(f"--- ЧАНК {j+1} ---\n")
            f.write(chunk + "\n")
            f.write("=" * 60 + "\n\n")

    cluster_path = os.path.join(folder_path, "cluster_log.txt")
    with open(cluster_path, "w", encoding="utf-8") as f:
        for section in cluster_log:
            f.write(section + "\n\n" + "-" * 60 + "\n\n")

    print(f"✅ Готово. Кластеризированных Чанков: {len(chunks_clust)}")


for i in range(20, 22):
    process_pdf_in_folder(i)
