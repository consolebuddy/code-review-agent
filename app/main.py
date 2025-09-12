from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import get_settings
from .schemas import AnalyzePRRequest, TaskStatusResponse, TaskResultsResponse
from .celery_app import celery
from .tasks import analyze_pr_task, store

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Autonomous Code Review Agent", version="0.1.0")

origins = ["*"] if settings.ALLOWED_ORIGINS == "*" else [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: (HTTPException(status_code=429, detail="Rate limit exceeded")))
app.add_middleware(SlowAPIMiddleware)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/analyze-pr", response_model=TaskStatusResponse)
@limiter.limit(settings.RATE_LIMIT)
def analyze_pr(req: AnalyzePRRequest, request: Request):
    payload = {"repo_url": req.repo_url, "pr_number": req.pr_number, "token": req.github_token}
    async_result = analyze_pr_task.apply_async(args=[payload])
    logger.info("Enqueued analyze_pr task {}", async_result.id)
    return {"task_id": async_result.id, "status": "queued"}

@app.get("/status/{task_id}", response_model=TaskStatusResponse)
@limiter.limit(settings.RATE_LIMIT)
def status(task_id: str, request: Request):
    async_result = celery.AsyncResult(task_id)
    return {"task_id": task_id, "status": async_result.status.lower()}

@app.get("/results/{task_id}", response_model=TaskResultsResponse)
@limiter.limit(settings.RATE_LIMIT)
def results(task_id: str, request: Request):
    data = store.get(task_id)
    if not data:
        async_result = celery.AsyncResult(task_id)
        if not async_result or not async_result.result:
            raise HTTPException(status_code=404, detail="results not found (yet)")
        return async_result.result
    return data

@app.post("/webhook/github")
def gh_webhook(payload: dict):
    action = payload.get("action")
    pr = payload.get("pull_request", {})
    if not pr:
        return {"ignored": True}
    if action in {"opened", "synchronize", "reopened"}:
        repo_url = pr["base"]["repo"]["html_url"]
        pr_number = pr["number"]
        async_result = analyze_pr_task.apply_async(args=[{"repo_url": repo_url, "pr_number": pr_number, "token": None}])
        return {"enqueued": True, "task_id": async_result.id}
    return {"ignored": True}
