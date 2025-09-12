from redis import Redis
import json
from typing import Optional

class ResultsStore:
    def __init__(self, url: str, ttl_seconds: int = 86400) -> None:
        self.client = Redis.from_url(url, decode_responses=True)
        self.ttl = ttl_seconds

    def _key(self, task_id: str) -> str:
        return f"code_review:task:{task_id}"

    def save(self, task_id: str, payload: dict) -> None:
        self.client.set(self._key(task_id), json.dumps(payload), ex=self.ttl)

    def get(self, task_id: str) -> Optional[dict]:
        raw = self.client.get(self._key(task_id))
        return json.loads(raw) if raw else None

    def cache_by_fingerprint(self, fingerprint: str, payload: dict) -> None:
        self.client.set(f"code_review:fingerprint:{fingerprint}", json.dumps(payload), ex=self.ttl)

    def get_by_fingerprint(self, fingerprint: str) -> Optional[dict]:
        raw = self.client.get(f"code_review:fingerprint:{fingerprint}")
        return json.loads(raw) if raw else None
