import requests
import os

class DeepSeekLLM:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model_url = "https://openrouter.ai/api/v1/chat/completions"
        # Selected in docs/decisions/0001-model-stack.md: cheapest model that
        # passes the grounding, Russian-quality and data-use criteria.
        self.model = "deepseek/deepseek-v4.1-flash-1017"

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost",  # обязательно! (любой валидный)
            "X-Title": "ragshelf",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Ты научный ассистент. Пиши строго, академически, с учётом источников."},
                {"role": "user", "content": prompt}
            ],
            # Thinking is on by default and billed as output; RAG answers do not need it.
            "reasoning": {"effort": "none"},
            # Route only to endpoints that neither retain nor train on prompts.
            "provider": {"zdr": True, "data_collection": "deny", "sort": "price"}
        }

        response = requests.post(self.model_url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print("❌ Ошибка запроса:", response.status_code, response.text)
            return "[Ошибка генерации текста]"
