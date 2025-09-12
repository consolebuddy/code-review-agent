# Autonomous Code Review Agent (FastAPI + Celery + Redis + Ollama)

An autonomous, goal‑oriented code review system for GitHub Pull Requests. It exposes an API to enqueue PR analyses, processes them asynchronously with Celery, runs static+LLM‑based review, and returns structured results.

## ✨ Features

- **FastAPI** REST endpoints: `POST /analyze-pr`, `GET /status/{task_id}`, `GET /results/{task_id}`
- **Celery** async task queue with **Redis** broker/backend
- **Caching** by PR head commit fingerprint (Redis, TTL configurable)
- **AI Agent**: quick static heuristics + LLM (Ollama local or OpenAI-compatible)
- **Structured output** per file with `type`, `line`, `description`, `suggestion`, `severity`
- **Rate limiting** with `slowapi` (Redis)
- **GitHub webhook** endpoint to auto‑enqueue on PR updates
- **Docker Compose** for API, Worker, Redis, and optional Ollama
- **pytest** basic tests
- **Structured logging** via loguru

---

## 🧱 Architecture

```
Client -> FastAPI (/analyze-pr) -> Celery task ->
  GitHub Files & Patch -> Static Rules + LLM Agent -> Results to Redis (cache + task) ->
  Client polls /status and /results
```

- **Caching key**: SHA256(repo_url:pr_number:head_sha)
- **Resilience**: LLM failures are swallowed; static checks still return useful issues.
- **Extensibility**: Add more language‑specific rules under `agent/rules.py`.

---

## 🚀 Quickstart (Docker)

1) Copy env and edit if needed:
```bash
cp .env.example .env
```

2) (Optional) Pull an Ollama model, e.g. `mistral`:
```bash
docker compose up -d ollama
# In another shell: load model (first run downloads it)
# curl http://localhost:11434/api/pull -d '{"name":"mistral"}'
```

3) Start API, Worker, Redis:
```bash
docker compose up --build
```

4) Health check:
```bash
curl http://localhost:8000/healthz
```

5) Enqueue analysis:
```bash
curl -X POST http://localhost:8000/analyze-pr   -H "Content-Type: application/json"   -d '{"repo_url":"https://github.com/user/repo","pr_number":123,"github_token":"YOUR_PAT_OR_EMPTY"}'
```

6) Check status:
```bash
curl http://localhost:8000/status/TASK_ID_FROM_PREV_STEP
```

7) Get results:
```bash
curl http://localhost:8000/results/TASK_ID_FROM_PREV_STEP
```

> For private repos or higher rate limit, provide `github_token` in body or `GITHUB_TOKEN` in `.env`.

---

## 🧪 Tests

Run unit tests locally:
```bash
pip install -r requirements.txt
pytest -q
```

---

## 🔧 Local Dev (without Docker)

1) Python 3.11+ recommended.
2) Create venv & install deps:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
3) Start Redis locally (Docker or native).
4) Start API:
```bash
uvicorn app.main:app --reload
```
5) Start worker:
```bash
celery -A app.celery_app worker --loglevel=INFO
```

---

## 📦 API

### POST `/analyze-pr`

**Body**
```json
{
  "repo_url": "https://github.com/user/repo",
  "pr_number": 123,
  "github_token": "optional_token"
}
```

**Response**
```json
{"task_id":"<id>", "status":"queued"}
```

### GET `/status/{task_id}`
**Response**
```json
{"task_id":"<id>", "status":"pending|started|completed|failed"}
```

### GET `/results/{task_id}`
**Response** (example)
```json
{
  "task_id": "abc123",
  "status": "completed",
  "results": {
    "files": [
      {
        "name": "main.py",
        "issues": [
          {
            "type": "style",
            "line": 15,
            "description": "Line too long",
            "suggestion": "Break line into multiple lines",
            "severity": "info"
          }
        ]
      }
    ],
    "summary": { "total_files": 1, "total_issues": 1, "critical_issues": 0 }
  }
}
```

### POST `/webhook/github`
Receives PR events (`opened`, `synchronize`, `reopened`) and enqueues a review automatically.

---

## 🧠 Agent Details

- **Static rules** (`agent/rules.py`): long lines, `TODO`, `print()` (Python), `bare except` (Python). Extend easily.
- **LLM review** (`agent/llm_client.py` + `agent/agent.py`):
  - If `USE_OLLAMA=true`, calls `POST /api/generate` with `OLLAMA_MODEL`.
  - Else uses OpenAI Chat Completions (set `OPENAI_API_KEY` and `OPENAI_MODEL`).
  - Expects a JSON array of issue objects; non‑JSON output is best‑effort parsed.

---

## 🗃 Storage

- **Redis DB 0**: Celery broker/backend
- **Redis DB 1**: Results & cache (`RESULT_REDIS_URL`)
- TTL for cache & task snapshots: `RESULT_CACHE_TTL_SECONDS` (default: 24h)

---

## 🧰 Design Decisions

- **Celery over BackgroundTasks**: enables worker scaling & retries.
- **Redis**: simple single dependency for queue + cache; replaceable with Postgres later.
- **Heuristics + LLM**: ensures useful output even if the model is unavailable.
- **Fingerprint cache**: avoids re‑running analysis if `head_sha` unchanged.

---

## 🔒 Rate Limiting

Configured via `RATE_LIMIT` (e.g., `20/minute`). Uses client IP as key.

---

## 🌐 Multi-language Support

Add language‑specific rules in `agent/rules.py` and adjust LLM system prompt to emphasize language. The agent already operates on unified diffs regardless of language.

---

## 📈 Logging

Using `loguru`. Celery also emits task logs. In production, configure JSON sink or ship to ELK/Datadog.

---

## 🧭 Roadmap / Future Improvements

- Postgres result store with schemas + search
- Deeper static analysis per language (flake8/pylint/golangci-lint, etc.)
- Inline GitHub Review Comments API
- Model function calling & toolformer prompts
- Fine-grained rate limiting and auth (API keys, GitHub App auth)
- Retries & backoff on GitHub API errors
- Better JSON schema validation of LLM output

---

## 📜 License

MIT
