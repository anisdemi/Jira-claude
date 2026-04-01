"""
Jira Duplicate Issue Detector — Claude Agent SDK
Connects to Jira Cloud, fetches issues in Python, then uses Claude
only for the semantic duplicate analysis.
Authentication: Uses your logged-in Claude Code CLI session (no API key needed).
"""

import os
import json
import anyio
import requests
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")


# ---------------------------------------------------------------------------
# Jira REST API Client
# ---------------------------------------------------------------------------

class JiraClient:
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


# ---------------------------------------------------------------------------
# ADF (Atlassian Document Format) Parser
# ---------------------------------------------------------------------------

def parse_description(desc) -> str:
    """Extract plain text from Jira ADF description."""
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


# ---------------------------------------------------------------------------
# Format issues for Claude
# ---------------------------------------------------------------------------

def format_issues(issues: list[dict]) -> str:
    """Format raw Jira issues into a readable text block for Claude."""
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


# ---------------------------------------------------------------------------
# System Prompt & Analysis Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert software project manager and Jira analyst working for a major bank.

You will be given a list of Jira issues. Analyze them semantically to find near-duplicate groups.

For each group, explain WHY they are similar and suggest a solution.

Return ONLY valid JSON matching this exact schema (no markdown, no code fences):
{
  "analysis_summary": {
    "total_issues_analyzed": number,
    "duplicate_groups_found": number,
    "total_duplicate_issues": number,
    "unique_issues": number
  },
  "duplicate_groups": [
    {
      "group_id": number,
      "theme": "string - name for the duplicate group",
      "confidence": "HIGH|MEDIUM|LOW",
      "issues": [{"key": "SCRUM-X", "summary": "..."}],
      "similarity_explanation": "why these are the same issue",
      "recommended_primary": "SCRUM-X (the one to keep)",
      "recommended_action": "what to do with the duplicates",
      "solution": {
        "description": "concrete fix recommendation",
        "priority": "CRITICAL|HIGH|MEDIUM|LOW",
        "complexity": "Simple|Medium|Complex",
        "technical_details": "technical implementation suggestion"
      }
    }
  ],
  "unique_issues": [
    {
      "key": "SCRUM-X",
      "summary": "...",
      "solution": {
        "description": "...",
        "priority": "CRITICAL|HIGH|MEDIUM|LOW",
        "complexity": "Simple|Medium|Complex"
      }
    }
  ]
}

Be thorough. Issues are "near-duplicates" when they describe the same underlying problem
even if they use completely different words, detail levels, or technical terminology."""


# ---------------------------------------------------------------------------
# Console Report
# ---------------------------------------------------------------------------

def print_report(report: dict):
    """Print a formatted console report from the analysis JSON."""
    summary = report.get("analysis_summary", {})
    groups = report.get("duplicate_groups", [])
    unique = report.get("unique_issues", [])

    print(f"\nTotal issues analyzed: {summary.get('total_issues_analyzed', '?')}")
    print(f"Duplicate groups found: {summary.get('duplicate_groups_found', '?')}")
    print(f"Issues in duplicate groups: {summary.get('total_duplicate_issues', '?')}")
    print(f"Unique issues: {summary.get('unique_issues', '?')}")

    for group in groups:
        confidence = group.get("confidence", "?")
        print(f"\n{'=' * 55}")
        print(f"DUPLICATE GROUP {group.get('group_id', '?')}: {group.get('theme', 'Unknown')}")
        print(f"Confidence: {confidence}")
        print("Issues:")
        issues = group.get("issues", [])
        primary = group.get("recommended_primary", "")
        for iss in issues:
            marker = " *" if iss.get("key", "") in primary else "  "
            print(f"  {marker} {iss.get('key', '?')}: {iss.get('summary', '?')}")
        print(f"Why similar: {group.get('similarity_explanation', '?')}")
        sol = group.get("solution", {})
        print(f"Solution: {sol.get('description', '?')}")
        print(f"Priority: {sol.get('priority', '?')} | Complexity: {sol.get('complexity', '?')}")

    if unique:
        print(f"\n{'=' * 55}")
        print(f"UNIQUE ISSUES ({len(unique)}):")
        for iss in unique:
            print(f"  {iss.get('key', '?')}: {iss.get('summary', '?')}")

    print(f"\n{'=' * 55}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    # Validate env vars
    missing = [
        v for v in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY")
        if not os.getenv(v)
    ]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please configure your .env file. See .env.example for the template.")
        return

    # Step 1: Fetch issues from Jira (Python handles this directly)
    print(f"\nFetching issues from Jira project {JIRA_PROJECT_KEY}...")
    jira = JiraClient(JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)
    try:
        issues = jira.fetch_all_issues(JIRA_PROJECT_KEY)
    except requests.HTTPError as e:
        print(f"ERROR: Failed to fetch issues from Jira: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        return

    print(f"Fetched {len(issues)} issues.")

    if not issues:
        print("No issues found. Nothing to analyze.")
        return

    # Step 2: Format issues and send to Claude for analysis only
    issues_text = format_issues(issues)

    prompt = (
        f"Here are {len(issues)} Jira issues from our banking platform project ({JIRA_PROJECT_KEY}).\n"
        f"Analyze them for near-duplicates and return the JSON analysis.\n\n"
        f"{issues_text}"
    )

    print("Sending issues to Claude for duplicate analysis...")

    # Step 3: Claude does semantic analysis (no tools needed)
    result_text = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            max_turns=1,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    if not result_text:
        print("ERROR: No response from Claude.")
        return

    # Step 4: Parse JSON and save report (Python handles this directly)
    # Extract JSON object from response (Claude may add preamble text)
    cleaned = result_text.strip()
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1:
        cleaned = cleaned[first_brace:last_brace + 1]

    try:
        report = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"WARNING: Could not parse Claude's response as JSON: {e}")
        print("Raw response saved to duplicate_report.json")
        report = {"raw_response": result_text}

    filepath = "duplicate_report.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Report saved to {filepath}")

    # Step 5: Print formatted console report
    if "analysis_summary" in report:
        print_report(report)
    else:
        print("\nClaude's response:")
        print(result_text[:2000])

    print("\nAnalysis complete.")


if __name__ == "__main__":
    print("=" * 60)
    print("  Jira Duplicate Detector - Claude Agent SDK")
    print("=" * 60)

    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"\nError: {e}")
