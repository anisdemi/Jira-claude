"""Issue formatting for Claude analysis."""

from .jira_client import parse_description


def format_issues(issues: list[dict]) -> str:
    """Format raw Jira issues into a readable text block for Claude (full details)."""
    formatted = []
    for issue in issues:
        fields = issue["fields"]
        key = issue["key"]
        summary = fields.get("summary", "N/A")
        issue_type = fields.get("issuetype", {}).get("name", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        priority = fields.get("priority", {}).get("name", "N/A") if fields.get("priority") else "N/A"
        description = parse_description(fields.get("description"))
        formatted.append(
            f"[{key}] ({issue_type} | {status} | Priority: {priority})\n"
            f"  Summary: {summary}\n"
            f"  Description: {description or '(no description)'}"
        )
    return "\n\n".join(formatted)


def format_issues_summary_only(issues: list[dict]) -> str:
    """Format issues with key + summary only (no descriptions). Used for pass 1."""
    lines = []
    for issue in issues:
        key = issue["key"]
        summary = issue["fields"].get("summary", "N/A")
        lines.append(f"[{key}] {summary}")
    return "\n".join(lines)


def filter_issues_by_keys(issues: list[dict], keys: set[str]) -> list[dict]:
    """Return only issues whose key is in the given set."""
    return [issue for issue in issues if issue["key"] in keys]
