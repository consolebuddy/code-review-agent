from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("ok") is True

def test_analyze_pr_schema():
    r = client.post("/analyze-pr", json={"repo_url":"https://github.com/user/repo", "pr_number": 1})
    assert r.status_code == 200
    data = r.json()
    assert "task_id" in data and data["status"] in {"queued", "pending"}
