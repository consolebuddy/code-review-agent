import hashlib
from typing import Any, Dict
from loguru import logger
from .celery_app import celery
from .config import get_settings
from storage.results_store import ResultsStore
from services.github_service import list_pr_files, get_pr_head_sha
from agent.llm_client import LLMClient
from agent.agent import analyze_diff

settings = get_settings()
store = ResultsStore(url=settings.RESULT_REDIS_URL, ttl_seconds=settings.RESULT_CACHE_TTL_SECONDS)

def _fingerprint(repo_url: str, pr_number: int, head_sha: str) -> str:
    return hashlib.sha256(f"{repo_url}:{pr_number}:{head_sha}".encode()).hexdigest()

@celery.task(bind=True, name="analyze_pr_task")
def analyze_pr_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    repo_url = payload["repo_url"]
    pr_number = int(payload["pr_number"])
    token = payload.get("token") or settings.GITHUB_TOKEN

    try:
        head_sha = get_pr_head_sha(repo_url, pr_number, token)
        fp = _fingerprint(repo_url, pr_number, head_sha)
        cached = store.get_by_fingerprint(fp)
        if cached:
            logger.info("Cache hit for fingerprint {}", fp)
            result = {"task_id": self.request.id, "status": "completed", "results": cached}
            store.save(self.request.id, result)
            return result

        files = list_pr_files(repo_url, pr_number, token, settings.MAX_FILES_PER_PR)

        llm = LLMClient(
            use_ollama=settings.USE_OLLAMA,
            ollama_url=settings.OLLAMA_BASE_URL,
            ollama_model=settings.OLLAMA_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_model=settings.OPENAI_MODEL,
        )
        analysis = analyze_diff(llm, files)

        result = {"task_id": self.request.id, "status": "completed", "results": analysis}
        store.save(self.request.id, result)
        store.cache_by_fingerprint(fp, analysis)
        return result
    except Exception as e:
        logger.exception("analyze_pr_task failed")
        err = {"task_id": self.request.id, "status": "failed", "error": str(e)}
        store.save(self.request.id, err)
        return err
