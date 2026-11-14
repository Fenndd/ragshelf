import os

from ragshelf.processing.chunk_clusterization import cluster_chunks
from ragshelf.loaders.universal_loader import extract_text_from_pdf, split_references, clean_spacing_and_hyphens, remove_irrelevant_sections
from ragshelf.processing.chunker import split_text

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

    print(type(raw_text))

for i in range(1, 5):
    process_pdf_in_folder(i)