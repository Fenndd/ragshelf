import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer

class BGEEmbedder:
    def __init__(self, model_path: str = "models/bge-large-en-v1.5"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()

    def encode(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                model_output = self.model(**inputs)
                embeddings = model_output.last_hidden_state[:, 0]  # CLS token

            normalized = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            all_embeddings.append(normalized.cpu().numpy())

        return np.vstack(all_embeddings)
