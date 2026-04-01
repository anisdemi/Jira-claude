"""Jira REST API client and ADF description parser."""

import requests


class JiraClient:
    """Client for fetching issues from Jira Cloud REST API."""

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)

    def fetch_all_issues(self, project_key: str) -> list[dict]:
        """Fetch all issues from a project via POST /rest/api/3/search/jql with cursor pagination."""
        url = f"{self.base_url}/rest/api/3/search/jql"
        all_issues = []
        next_page_token = None

        while True:
            body = {
                "jql": f"project = {project_key} ORDER BY created ASC",
                "maxResults": 100,
                "fields": ["summary", "description", "issuetype", "status", "priority", "created", "updated"],
            }
            if next_page_token:
                body["nextPageToken"] = next_page_token

            response = requests.post(
                url, json=body, auth=self.auth, headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            )
            response.raise_for_status()
            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            if data.get("isLast", True) or not issues:
                break
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

        return all_issues


def parse_description(desc) -> str:
    """Extract plain text from Jira ADF (Atlassian Document Format) description."""
    if desc is None:
        return ""
    if isinstance(desc, str):
        return desc
    texts = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for child in node.get("content", []):
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(desc)
    return " ".join(texts).strip()
