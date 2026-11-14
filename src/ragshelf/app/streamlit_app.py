import streamlit as st
from ragshelf.generation.rag_chain import generate_paragraph
from ragshelf.store.dynamic_vector_store import DynamicVectorStore
from ragshelf.embeddings.combined_embedder import CombinedEmbedder
from ragshelf.loaders.universal_loader import extract_text_from_pdf
from ragshelf.processing.chunker import split_text
import os
import time

st.set_page_config(page_title="RAG: Генерация черновиков", layout="wide")
st.title("📚 Генератор черновиков по документам")

# --- Состояние ---
if "store" not in st.session_state:
    st.session_state.store = None
    st.session_state.loaded = False

# --- Загрузка PDF ---
st.sidebar.header("📄 Источник PDF")
uploaded_file = st.sidebar.file_uploader("Загрузите PDF", type="pdf")

if uploaded_file and st.sidebar.button("🔄 Обработать PDF"):
    with st.spinner("Извлечение и векторизация..."):
        # Сохраняем файл
        pdf_path = os.path.join("temp.pdf")
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.read())

        text = extract_text_from_pdf(pdf_path)
        chunks, _removed = split_text(text)

        embeddings = CombinedEmbedder().encode(chunks)
        store = DynamicVectorStore()
        store.build_index([
            {"id": str(i), "text": chunk, "embedding": embedding}
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ])

        st.session_state.store = store
        st.session_state.loaded = True
        st.success("Индекс успешно создан!")

# --- Поле ввода запроса ---
st.subheader("✍️ Введите вопрос или тему для генерации")
query = st.text_area("Пример: Как любовная зависимость связана с привязанностью?", height=100)

use_sources = st.checkbox("Использовать PDF-источник (RAG)", value=True)

if st.button("🚀 Сгенерировать черновик"):
    if not query.strip():
        st.warning("Пожалуйста, введите запрос.")
    elif use_sources and not st.session_state.loaded:
        st.error("Сначала загрузите и обработайте PDF!")
    else:
        with st.spinner("Генерация черновика..."):
            start = time.time()
            results = []
            if use_sources:
                results = [r["text"] for r in st.session_state.store.search(query, k=3)]
            answer = generate_paragraph(query, results)
            end = time.time()

        st.success(f"✅ Черновик сгенерирован за {end - start:.2f} сек")
        st.markdown("### 📄 Результат")
        st.markdown(answer)

        with st.expander("🔍 Использованные фрагменты", expanded=False):
            for i, r in enumerate(results):
                st.markdown(f"**Фрагмент {i+1}:**\n> {r}")
