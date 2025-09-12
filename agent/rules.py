from typing import List, Dict

def quick_static_checks(file_name: str, patch: str) -> List[Dict]:
    # Parse added lines from unified diff and flag common issues.
    issues: List[Dict] = []
    for line in patch.splitlines():
        if not line.startswith('+') or line.startswith('+++'):
            continue
        content = line[1:]  # strip '+'
        if len(content) > 120:
            issues.append({
                "type": "style", "line": None, "description": "Line too long (>120 chars)",
                "suggestion": "Wrap or refactor long line", "severity": "info"
            })
        if "TODO" in content:
            issues.append({
                "type": "best_practice", "line": None, "description": "TODO left in code",
                "suggestion": "Resolve TODO or link to a ticket", "severity": "warn"
            })
        if "print(" in content and file_name.endswith(".py"):
            issues.append({
                "type": "best_practice", "line": None, "description": "print() in production code",
                "suggestion": "Use logging instead", "severity": "info"
            })
        if "except:" in content and file_name.endswith(".py"):
            issues.append({
                "type": "bug", "line": None, "description": "Bare except",
                "suggestion": "Catch specific exception types", "severity": "warn"
            })
    return issues
