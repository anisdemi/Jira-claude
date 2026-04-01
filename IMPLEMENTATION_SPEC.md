# JIRA Duplicate Issue Detector — Implementation Spec

> **Target**: Claude Code implementation using the **Claude Agent SDK for Python**
> **Client**: Banking sector — POC for AI-powered Jira issue management
> **Goal**: Detect semantically similar (near-duplicate) Jira issues and suggest solutions

---

## 1. Project Overview

Build a Python CLI tool that:

1. Connects to a Jira Cloud instance via REST API
2. Fetches all issues from a given project
3. Uses **Claude AI** (via the Claude Agent SDK) to semantically analyze issues
4. Detects near-duplicate groups (issues describing the same problem in different words)
5. Suggests technical solutions for each group
6. Outputs a formatted console report + JSON file

### Why Claude Agent SDK?

We use `claude-agent-sdk` (not the raw `anthropic` SDK) because it provides:

- Agentic tool-calling via custom MCP tools defined in Python
- Claude Code's built-in tool loop (Claude decides when to call tools)
- Session management for multi-turn interactions
- The `@tool` decorator for defining tools as simple Python functions

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Python CLI App                        │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  Jira REST    │    │  Claude Agent SDK             │   │
│  │  API Client   │◄──►│  (ClaudeSDKClient)            │   │
│  │  (requests)   │    │                                │   │
│  └──────────────┘    │  Custom MCP Tools:              │   │
│                      │   • fetch_jira_issues           │   │
│                      │   • save_report                 │   │
│                      │                                 │   │
│                      │  Claude analyzes issues,        │   │
│                      │  calls tools as needed,         │   │
│                      │  returns structured analysis    │   │
│                      └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Environment & Prerequisites

### 3.1 Python Version

- Python 3.10+ (required by claude-agent-sdk)

### 3.2 Dependencies

```
requirements.txt:

claude-agent-sdk
requests
python-dotenv
```

### 3.3 Environment Variables (`.env` file)

```env
# Anthropic API Key — required for Claude Agent SDK
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Jira Cloud Configuration (pre-filled for the demo Jira instance)
JIRA_BASE_URL=https://uni5-technologies.atlassian.net
JIRA_EMAIL=anis.sibachir@uni5-technologies.com
JIRA_API_TOKEN=ATATT3xFfGF0uvgRLUFtxhKO49zq3obfWUHD8kNJQh6INTqIZet7Zn-8FGNrpRBtwfeMhP6wK5vkHXOLiiVMRhTR7DRkpJdm7c-Z2-ZxGDppRugpHYb3GR-ffJJgIKqN4bYzv77G85j7zaFBtTS0DjQpgZYmWfZ0SSdMZmD6W3--cD-2u94Z68o=0BD95283
JIRA_PROJECT_KEY=SCRUM
```

> **Note**: The Jira credentials above are pre-filled for the demo instance. You only need to add your own `ANTHROPIC_API_KEY`.

### 3.4 How to Get Credentials

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "Claude Duplicate Detector")
4. Copy the generated token — it won't be shown again

**Anthropic API Key:**
1. Go to https://console.anthropic.com/settings/keys
2. Click "Create Key"
3. Copy the key (starts with `sk-ant-`)

---

## 4. Implementation Details

### 4.1 Project Structure

```
jira-duplicate-detector/
├── .env                          # Credentials (gitignored)
├── .env.example                  # Template for credentials
├── requirements.txt              # Python dependencies
├── jira_duplicate_detector.py    # Main entry point
└── duplicate_report.json         # Generated output (gitignored)
```

Everything goes in a **single file** (`jira_duplicate_detector.py`) for simplicity. This is a POC.

### 4.2 Jira REST API Client

Create a simple class to interact with Jira Cloud:

```python
import requests

class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)
        self.headers = {"Accept": "application/json"}

    def fetch_all_issues(self, project_key: str) -> list[dict]:
        """Fetch all issues from a project via JQL search with pagination."""
        url = f"{self.base_url}/rest/api/3/search"
        all_issues = []
        start_at = 0

        while True:
            params = {
                "jql": f"project = {project_key} ORDER BY created ASC",
                "startAt": start_at,
                "maxResults": 100,
                "fields": "summary,description,issuetype,status,priority,created,updated",
            }
            response = requests.get(url, params=params, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)
            start_at += len(issues)
            if start_at >= data.get("total", 0) or not issues:
                break

        return all_issues
```

### 4.3 Description Parser

Jira descriptions come in ADF (Atlassian Document Format) — a nested JSON structure. We need to extract plain text:

```python
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
```

### 4.4 Claude Agent SDK Integration

This is the core. We use `ClaudeSDKClient` with **custom MCP tools**.

#### 4.4.1 Custom Tool: `fetch_jira_issues`

Define a tool that Claude can call to fetch issues from Jira:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk import AssistantMessage, TextBlock, ToolUseBlock, ToolResultBlock, ResultMessage

@tool(
    name="fetch_jira_issues",
    description="Fetch all issues from the configured Jira project. Returns a formatted list of all issues with their key, type, status, summary, and description.",
    input_schema={}
)
async def fetch_jira_issues_tool(args):
    """Fetch all Jira issues and return them formatted."""
    jira = JiraClient(JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)
    issues = jira.fetch_all_issues(JIRA_PROJECT_KEY)

    formatted = []
    for issue in issues:
        fields = issue["fields"]
        key = issue["key"]
        summary = fields.get("summary", "N/A")
        issue_type = fields.get("issuetype", {}).get("name", "N/A")
        status = fields.get("status", {}).get("name", "N/A")
        description = parse_description(fields.get("description"))
        formatted.append(
            f"[{key}] ({issue_type} | {status})\n"
            f"  Summary: {summary}\n"
            f"  Description: {description}"
        )

    result_text = f"Found {len(issues)} issues:\n\n" + "\n\n".join(formatted)
    return {"content": [{"type": "text", "text": result_text}]}
```

#### 4.4.2 Custom Tool: `save_report`

Define a tool that Claude can call to save the analysis report:

```python
import json

@tool(
    name="save_report",
    description="Save the duplicate detection analysis report as a JSON file. Pass the complete JSON analysis object as a string.",
    input_schema={"report_json": str}
)
async def save_report_tool(args):
    """Save the analysis report to a JSON file."""
    report_text = args.get("report_json", "{}")
    try:
        report = json.loads(report_text)
    except json.JSONDecodeError:
        report = {"raw": report_text}

    filepath = "duplicate_report.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return {"content": [{"type": "text", "text": f"Report saved to {filepath}"}]}
```

#### 4.4.3 MCP Server and Client Setup

```python
import anyio

# Create the MCP server with our tools
server = create_sdk_mcp_server(
    name="jira-tools",
    version="1.0.0",
    tools=[fetch_jira_issues_tool, save_report_tool]
)

SYSTEM_PROMPT = """You are an expert software project manager and Jira analyst working for a major bank.

When asked to analyze Jira issues for duplicates:

1. Call the fetch_jira_issues tool to get all issues
2. Analyze them semantically to find near-duplicate groups
3. For each group, explain WHY they are similar and suggest a solution
4. Call save_report to save the structured JSON analysis
5. Print a formatted summary to the user

Your analysis JSON must follow this schema:
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

async def main():
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        mcp_servers={"jira": server},
        allowed_tools=["mcp__jira__fetch_jira_issues", "mcp__jira__save_report"],
        max_turns=10,  # allow enough turns for tool calls + analysis
    )

    async with ClaudeSDKClient(options=options) as client:
        # Send the initial prompt — Claude will autonomously:
        # 1. Call fetch_jira_issues
        # 2. Analyze the results
        # 3. Call save_report
        # 4. Return a summary
        await client.query(
            "Analyze all Jira issues in our banking platform project for near-duplicates. "
            "Fetch the issues, detect duplicate groups, suggest solutions, and save the report."
        )

        # Collect and print Claude's response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
            elif isinstance(message, ResultMessage):
                # ResultMessage indicates the agent loop completed
                print("\n✅ Analysis complete.")

if __name__ == "__main__":
    print("=" * 60)
    print("  🏦 Jira Duplicate Detector — Claude Agent SDK")
    print("=" * 60)
    anyio.run(main)
```

### 4.5 Important Notes for Implementation

1. **`input_schema` on `@tool`**: The `@tool` decorator takes `input_schema` as a dict mapping param names to types. For `fetch_jira_issues` which takes no args, pass `{}`. For `save_report`, pass `{"report_json": str}`.

2. **`allowed_tools` naming convention**: When using custom MCP tools, the tool name follows the pattern `mcp__<server_name>__<tool_name>`. Since we named our server `"jira"`, the tools are `mcp__jira__fetch_jira_issues` and `mcp__jira__save_report`.

3. **`max_turns`**: Set this to at least 10 to give Claude enough room to call tools and process results. Each tool call + response is a turn.

4. **Error handling**: Wrap the `anyio.run(main)` in a try/except to handle common errors (missing env vars, Jira auth failures, network issues).

5. **ADF parsing**: Jira Cloud API v3 returns descriptions in Atlassian Document Format (JSON), NOT plain text. The `parse_description()` function handles this.

6. **Pagination**: The Jira search API returns max 100 results per page. The `fetch_all_issues` method handles pagination automatically.

---

## 5. Expected Output

### Console Output (example)

```
==============================================================
  🏦 Jira Duplicate Detector — Claude Agent SDK
==============================================================

🔍 Analyzing 38 Jira issues for near-duplicates...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DUPLICATE GROUP 1: Mobile Login After Password Change
Confidence: 🔴 HIGH
Issues:
  ⭐ SCRUM-1: Users unable to login to mobile banking app after password reset
     SCRUM-2: Mobile app login fails after changing password
     SCRUM-3: Authentication error when accessing mobile banking post password update
Why similar: All three describe the same authentication failure after password update
Solution: Fix session token cache invalidation on password reset
Priority: CRITICAL | Complexity: Medium
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[... more groups ...]

✅ Report saved to duplicate_report.json
✅ Analysis complete.
```

### JSON Output (`duplicate_report.json`)

The JSON report follows the schema defined in the system prompt (section 4.4.3).

---

## 6. Testing

To verify the implementation:

1. Ensure the `.env` file has valid credentials
2. Run `python jira_duplicate_detector.py`
3. Check that:
   - All 38 issues are fetched from Jira
   - At least 7-8 duplicate groups are detected (see expected groups below)
   - Each group has a solution suggestion
   - `duplicate_report.json` is saved with valid JSON

### Expected Duplicate Groups (ground truth)

| # | Theme | Issue Keys |
|---|---|---|
| 1 | Mobile login after password change | SCRUM-1, 2, 3 |
| 2 | Wire/SWIFT transfer timeouts | SCRUM-4, 5, 6 |
| 3 | AML/compliance report slow performance | SCRUM-7, 8, 9 |
| 4 | Payment gateway 503 errors | SCRUM-10, 11 |
| 5 | Stale dashboard balance | SCRUM-12, 13 |
| 6 | Contactless fraud detection | SCRUM-19, 20 |
| 7 | Loan/mortgage pipeline stuck | SCRUM-21, 22 |
| 8 | Random session expiry | SCRUM-23, 24 |

---

## 7. Jira Instance Details

- **URL**: https://uni5-technologies.atlassian.net
- **Project Key**: SCRUM
- **Project Name**: My Scrum Space
- **Cloud ID**: d588f1ca-7b6d-4eba-8046-aeb7d034b13d
- **Total issues**: 38 (SCRUM-1 through SCRUM-38)
- **Issue types used**: Bug, Story, Task

---

## 8. Reference Links

- Claude Agent SDK docs: https://platform.claude.com/docs/en/agent-sdk/python
- Claude Agent SDK PyPI: https://pypi.org/project/claude-agent-sdk/
- Claude Agent SDK GitHub: https://github.com/anthropics/claude-agent-sdk-python
- Jira REST API v3: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- Jira API tokens: https://id.atlassian.com/manage-profile/security/api-tokens
- Anthropic API keys: https://console.anthropic.com/settings/keys
