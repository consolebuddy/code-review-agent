from pydantic import BaseModel, Field
from typing import Optional, List

class AnalyzePRRequest(BaseModel):
    repo_url: str = Field(..., example="https://github.com/user/repo")
    pr_number: int = Field(..., example=123)
    github_token: Optional[str] = Field(None, description="Optional GitHub PAT; falls back to env var")

class Issue(BaseModel):
    type: str
    line: Optional[int] = None
    description: str
    suggestion: Optional[str] = None
    severity: str = "info"

class FileResult(BaseModel):
    name: str
    issues: List[Issue]

class Summary(BaseModel):
    total_files: int
    total_issues: int
    critical_issues: int

class AnalysisResults(BaseModel):
    files: List[FileResult]
    summary: Summary

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    error: Optional[str] = None

class TaskResultsResponse(BaseModel):
    task_id: str
    status: str
    results: Optional[AnalysisResults] = None
    error: Optional[str] = None
