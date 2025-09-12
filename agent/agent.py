import json
from typing import Dict, Any, List
from .llm_client import LLMClient
from .rules import quick_static_checks

def analyze_diff(llm: LLMClient, files: List[dict]) -> Dict[str, Any]:
    results_files = []
    total_issues = 0
    critical = 0

    for f in files:
        name = f.get("filename")
        patch = f.get("patch") or ""
        file_issues = []

        file_issues.extend(quick_static_checks(name, patch))

        try:
            llm_resp = llm.review(name, patch)
            parsed = None
            try:
                parsed = json.loads(llm_resp)
            except Exception:
                start = llm_resp.find('[')
                end = llm_resp.rfind(']')
                if 0 <= start < end:
                    parsed = json.loads(llm_resp[start:end+1])
            if isinstance(parsed, list):
                for it in parsed:
                    file_issues.append({
                        "type": str(it.get("type", "best_practice")),
                        "line": it.get("line"),
                        "description": str(it.get("description", ""))[:500],
                        "suggestion": str(it.get("suggestion", ""))[:500],
                        "severity": str(it.get("severity", "info"))
                    })
        except Exception:
            pass

        total_issues += len(file_issues)
        critical += sum(1 for i in file_issues if i.get("severity") == "critical")
        results_files.append({"name": name, "issues": file_issues})

    return {
        "files": results_files,
        "summary": {
            "total_files": len(results_files),
            "total_issues": total_issues,
            "critical_issues": critical
        }
    }
