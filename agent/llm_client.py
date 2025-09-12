import requests
from typing import Optional

class LLMClient:
    def __init__(self, use_ollama: bool, ollama_url: str, ollama_model: str,
                 openai_api_key: Optional[str], openai_model: Optional[str]) -> None:
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url.rstrip("/")
        self.ollama_model = ollama_model
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model

    def review(self, file_name: str, patch: str) -> str:
        # Prepare a compact prompt to produce actionable review notes as JSON array.
        system = (
            "You are a senior code reviewer. Output only a compact JSON array of issues, each with keys: "
            "type (style|bug|perf|best_practice), line (number or null), description, suggestion, severity "
            "(info|warn|critical). Be precise and avoid generic advice."
        )
        user = f"FILE: {file_name}\nPATCH (unified diff):\n{patch[:20000]}"
        if self.use_ollama:
            payload = {
                "model": self.ollama_model,
                "prompt": system + "\n\n" + user,
                "stream": False
            }
            r = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            return data.get("response", "").strip()
        else:
            headers = {"Authorization": f"Bearer {self.openai_api_key}"}
            body = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            }
            r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=120)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
