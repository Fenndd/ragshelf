import numpy as np
from ragshelf.embeddings.bge_embedder import BGEEmbedder
from ragshelf.embeddings.scibert_embedder import SciBERTEmbedder

class CombinedEmbedder:
    def __init__(self, alpha: float = 0.75):
        """
        alpha: вес BGE. От 0.0 (только SciBERT) до 1.0 (только BGE)
        """
        self.alpha = alpha
        self.bge = BGEEmbedder()
        self.scibert = SciBERTEmbedder()

    def encode(self, texts: list[str], alpha: float = None) -> np.ndarray:
        """
        Возвращает объединённые эмбеддинги с весами.
        Если alpha не передан — используется self.alpha из конструктора.
        """
        if alpha is None:
            alpha = self.alpha

        # 1. Получаем эмбеддинги
        bge_embeddings = self.bge.encode(texts)
        scibert_embeddings = self.scibert.encode(texts)

        # 2. Нормализация по отдельности
        bge_norm = bge_embeddings / np.linalg.norm(bge_embeddings, axis=1, keepdims=True)
        scibert_norm = scibert_embeddings / np.linalg.norm(scibert_embeddings, axis=1, keepdims=True)

        # 3. Взвешенное объединение
        combined = np.concatenate([alpha * bge_norm, (1 - alpha) * scibert_norm], axis=1)

        # 4. Финальная нормализация
        combined /= np.linalg.norm(combined, axis=1, keepdims=True)

        return combined
