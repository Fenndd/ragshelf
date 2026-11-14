import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer

class SciBERTEmbedder:
    def __init__(self, model_name: str = "allenai/scibert_scivocab_uncased"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def masked_mean_pooling(self, token_embeddings, attention_mask):
        mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        masked_embeddings = token_embeddings * mask
        summed = masked_embeddings.sum(1)
        counts = mask.sum(1)
        return summed / counts

    def encode(self, texts: list[str], batch_size: int = 8) -> np.ndarray:
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            inputs = self.tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                output = self.model(**inputs)
                pooled = self.masked_mean_pooling(output.last_hidden_state, inputs["attention_mask"])

            normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
            all_embeddings.append(normalized.cpu().numpy())

        return np.vstack(all_embeddings)
