import re
import requests
from typing import Any, Dict, List, Tuple

def parse_github_repo(repo_url: str) -> Tuple[str, str]:
    # e.g., https://github.com/user/repo(.git)?
    m = re.match(r'https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$', repo_url)
    if not m:
        raise ValueError("Invalid GitHub repository URL")
    return m.group('owner'), m.group('repo')

def list_pr_files(repo_url: str, pr_number: int, token: str | None, max_files: int = 200) -> List[Dict[str, Any]]:
    owner, repo = parse_github_repo(repo_url)
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    files: List[Dict[str, Any]] = []
    page = 1
    while True:
        resp = requests.get(url, headers=headers, params={"page": page, "per_page": 100}, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        files.extend(batch)
        if len(batch) < 100 or len(files) >= max_files:
            break
        page += 1
    return files[:max_files]

def get_pr_head_sha(repo_url: str, pr_number: int, token: str | None) -> str:
    owner, repo = parse_github_repo(repo_url)
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["head"]["sha"]
