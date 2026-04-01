# Jira Duplicate Issue Detector

A Python CLI tool that connects to a Jira Cloud instance, fetches all issues from a project, and uses Claude AI to semantically detect near-duplicate issues and suggest solutions.

Built for a banking sector POC — AI-powered Jira issue management.

## Table of Contents

- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the Solution](#running-the-solution)
- [Running the Tests](#running-the-tests)
- [Project Structure](#project-structure)
- [Customizing the Prompt](#customizing-the-prompt)
- [Output Format](#output-format)
- [Two-Pass Analysis](#two-pass-analysis)
- [Troubleshooting](#troubleshooting)

---

## How It Works

The tool operates in two modes depending on the number of issues:

### Single-Pass (small projects, <= 30 issues)

1. **Fetch** — Python connects to Jira Cloud REST API and downloads all issues (handles pagination automatically).
2. **Parse** — Jira descriptions in ADF (Atlassian Document Format) are converted to plain text.
3. **Format** — Issues are formatted with key, type, status, priority, summary, and description.
4. **Analyze** — All issues with full details are sent to Claude in one prompt.
5. **Report** — The JSON report is saved to `duplicate_report.json` and a formatted summary is printed to the console.

### Two-Pass (larger projects, > 30 issues)

1. **Fetch** — Same as above.
2. **Pass 1 (lightweight)** — Only issue keys + summaries (no descriptions) are sent to Claude to identify candidate duplicate groups. This is a small payload regardless of issue count.
3. **Pass 2 (targeted)** — Full details are sent only for the candidate issues identified in pass 1, plus summaries for ungrouped issues. Claude confirms or rejects the candidates and generates solutions.
4. **Report** — Same as single-pass.

The two-pass approach keeps token usage manageable even for projects with hundreds or thousands of issues, since descriptions (the bulk of the data) are only sent for suspected duplicates.

**Key design choice:** Python handles all I/O (Jira API, file saving). Claude only does the semantic analysis. This keeps the tool reliable and testable.

---

## Prerequisites

- **Python 3.10+**
- **Claude Code CLI** — installed and logged in (the Agent SDK authenticates through your CLI session, no API key needed)
- **Jira Cloud instance** with API access

### Installing Claude Code CLI

If you haven't already:

```
npm install -g @anthropic-ai/claude-code
claude login
```

Verify you're logged in:

```
claude --version
```

### Getting a Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "Duplicate Detector")
4. Copy the token — it won't be shown again

---

## Setup

### 1. Clone or navigate to the project

```
cd "C:\Users\anisd\Documents\Jira claude"
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- `claude-agent-sdk` — Claude Agent SDK for AI analysis
- `requests` — HTTP client for Jira API
- `python-dotenv` — Environment variable loading from `.env`
- `anyio` — Async runtime
- `pytest` — Test framework

### 4. Configure environment variables

Copy the example and fill in your credentials:

```powershell
copy .env.example .env
```

Edit `.env`:

```env
JIRA_BASE_URL=https://your-instance.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=SCRUM
```

| Variable | Description |
|----------|-------------|
| `JIRA_BASE_URL` | Your Jira Cloud instance URL |
| `JIRA_EMAIL` | Email associated with your Atlassian account |
| `JIRA_API_TOKEN` | API token generated from Atlassian |
| `JIRA_PROJECT_KEY` | The Jira project key to analyze (e.g., `SCRUM`) |

> **Note:** No `ANTHROPIC_API_KEY` is needed. The Claude Agent SDK authenticates through your logged-in Claude Code CLI session.

---

## Running the Solution

```powershell
python main.py
```

### Expected Output (single-pass, <= 30 issues)

```
============================================================
  Jira Duplicate Detector - Claude Agent SDK
============================================================

Fetching issues from Jira project SCRUM...
Fetched 25 issues.
Sending issues to Claude for duplicate analysis...
Using single-pass analysis...
Report saved to duplicate_report.json

[... duplicate groups and summary ...]

Analysis complete.
```

### Expected Output (two-pass, > 30 issues)

```
============================================================
  Jira Duplicate Detector - Claude Agent SDK
============================================================

Fetching issues from Jira project SCRUM...
Fetched 38 issues.
Sending issues to Claude for duplicate analysis...
Pass 1: Sending summaries to identify candidate groups...
  Found 8 candidate groups (19 issues)
  19 ungrouped issues
Pass 2: Sending full details for confirmation and solutions...
Report saved to duplicate_report.json

Total issues analyzed: 38
Duplicate groups found: 8
Issues in duplicate groups: 19
Unique issues: 19

=======================================================
DUPLICATE GROUP 1: Mobile Login Failure After Password Reset
Confidence: HIGH
Issues:
   * SCRUM-1: Users unable to login to mobile banking app after password reset
     SCRUM-2: Mobile app login fails after changing password
     SCRUM-3: Authentication error when accessing mobile banking post password update
Why similar: All three describe the same defect...
Solution: Fix the auth token cache invalidation...
Priority: CRITICAL | Complexity: Medium
=======================================================

[... more groups ...]

Analysis complete.
```

### Adjusting the Threshold

The threshold for switching between single-pass and two-pass is set in `main.py`:

```python
SINGLE_PASS_THRESHOLD = 30
```

- Set it higher if you want single-pass for larger projects (faster, but uses more tokens)
- Set it lower to force two-pass even for small projects (saves tokens, but slower due to two Claude calls)

### Output Files

| File | Description |
|------|-------------|
| `duplicate_report.json` | Full structured JSON report with all duplicate groups, explanations, and solutions |

---

## Running the Tests

### Install pytest (if not already installed)

```powershell
pip install pytest
```

### Run all tests

```powershell
pytest tests/ -v
```

### Run tests with unittest (no pytest needed)

```powershell
python -m unittest discover tests -v
```

### Run a specific test file

```powershell
pytest tests/test_jira_client.py -v
pytest tests/test_formatter.py -v
pytest tests/test_analyzer.py -v
pytest tests/test_report.py -v
```

### Run a specific test

```powershell
pytest tests/test_jira_client.py::TestParseDescription::test_simple_adf_paragraph -v
```

### Test Summary

| Test File | Tests | What It Covers |
|-----------|-------|----------------|
| `test_jira_client.py` | 11 | ADF parser (8 cases: None, string, simple ADF, multi-paragraph, nested, empty, non-text nodes, list input) + JiraClient (3 cases: trailing slash, single page, multi-page pagination, empty project) |
| `test_formatter.py` | 16 | Full formatting (7), summary-only formatting (4), issue filtering by keys (5) |
| `test_analyzer.py` | 15 | Prompt loading (5: default, pass1, pass2, missing, custom) + JSON extraction (10: pure JSON, preamble, markdown, wrapping, invalid, no braces, nested, empty, real-world, pass1 response) |
| `test_report.py` | 8 | Report saving (valid JSON, unicode) + console printing (summary, group details, unique issues, primary marker, empty report) |
| **Total** | **50** | |

All tests run offline — no Jira or Claude connections needed. The JiraClient tests use mocked HTTP responses.

---

## Project Structure

```
jira-duplicate-detector/
|
|-- main.py                             Entry point — orchestrates the pipeline
|
|-- jira_duplicate_detector/            Python package
|   |-- __init__.py                     Re-exports all public functions/classes
|   |-- jira_client.py                  JiraClient class + ADF parser
|   |-- formatter.py                    Formats Jira issues into text for Claude
|   |-- analyzer.py                     Loads prompts, calls Claude, extracts JSON
|   |-- report.py                       Saves JSON report + prints console summary
|
|-- prompts/
|   |-- system_prompt.txt               Single-pass system prompt
|   |-- pass1_candidates.txt            Two-pass: pass 1 prompt (summaries only)
|   |-- pass2_analysis.txt              Two-pass: pass 2 prompt (full details)
|
|-- tests/
|   |-- __init__.py
|   |-- test_jira_client.py             Tests for Jira API client + ADF parser
|   |-- test_formatter.py               Tests for issue formatting + filtering
|   |-- test_analyzer.py                Tests for prompt loading + JSON extraction
|   |-- test_report.py                  Tests for report output
|
|-- docs/
|   |-- README.md                       This file
|   |-- architecture.md                 Architecture and module reference
|
|-- .env                                Your credentials (gitignored)
|-- .env.example                        Template for credentials
|-- requirements.txt                    Python dependencies
|-- duplicate_report.json               Generated output (after running)
|-- IMPLEMENTATION_SPEC.md              Original specification document
```

---

## Customizing the Prompt

The prompts sent to Claude live in the `prompts/` directory. You can edit them freely without touching any code.

| File | Used By | Purpose |
|------|---------|---------|
| `system_prompt.txt` | Single-pass mode | Full analysis in one prompt |
| `pass1_candidates.txt` | Two-pass: pass 1 | Identify candidate groups from summaries only |
| `pass2_analysis.txt` | Two-pass: pass 2 | Confirm candidates and generate solutions |

### What you can customize

- **Role description** — Change "expert software project manager" to match your domain
- **JSON schema** — Add or remove fields from the output structure
- **Confidence criteria** — Define what HIGH/MEDIUM/LOW means for your team
- **Analysis instructions** — Add specific rules (e.g., "ignore issues older than 6 months")
- **Solution format** — Change how solutions are structured
- **Candidate sensitivity** — In `pass1_candidates.txt`, adjust how aggressively Claude groups candidates (currently set to be generous to avoid missing real duplicates)

### Example: Adding a severity field

Add this to the `duplicate_groups` schema in the prompt:

```
"severity_score": "1-10 numeric score of how critical this duplicate group is"
```

Claude will include it in the JSON output on the next run. If using two-pass, add it to `pass2_analysis.txt` (that's the prompt that produces the final output).

### Using multiple prompts

The `load_prompt()` function accepts a filename parameter. You can create additional prompt files in `prompts/` (e.g., `security_focused.txt`) and modify `analyzer.py` to load a different one.

---

## Output Format

The `duplicate_report.json` follows this structure (same for both single-pass and two-pass):

```json
{
  "analysis_summary": {
    "total_issues_analyzed": 38,
    "duplicate_groups_found": 8,
    "total_duplicate_issues": 19,
    "unique_issues": 19
  },
  "duplicate_groups": [
    {
      "group_id": 1,
      "theme": "Mobile Login Failure After Password Reset",
      "confidence": "HIGH",
      "issues": [
        {"key": "SCRUM-1", "summary": "..."},
        {"key": "SCRUM-2", "summary": "..."}
      ],
      "similarity_explanation": "Why these are duplicates",
      "recommended_primary": "SCRUM-1",
      "recommended_action": "What to do with the duplicates",
      "solution": {
        "description": "Concrete fix recommendation",
        "priority": "CRITICAL",
        "complexity": "Medium",
        "technical_details": "Implementation details"
      }
    }
  ],
  "unique_issues": [
    {
      "key": "SCRUM-14",
      "summary": "...",
      "solution": {
        "description": "...",
        "priority": "HIGH",
        "complexity": "Complex"
      }
    }
  ]
}
```

---

## Two-Pass Analysis

### Why two passes?

Claude Opus 4.6 has a 200K token context window (1M in beta). For a project with hundreds of issues, sending all issues with full descriptions in a single prompt can exceed this limit. The two-pass approach solves this:

| | Pass 1 | Pass 2 |
|---|---|---|
| **Data sent** | Keys + summaries only | Full details for candidates only |
| **Token cost** | Very low (< 5K tokens for 500 issues) | Moderate (only suspected duplicates) |
| **Prompt** | `pass1_candidates.txt` | `pass2_analysis.txt` |
| **Claude's job** | Group similar-sounding issues | Confirm duplicates, generate solutions |

### How it scales

| Issues | Single-pass tokens (est.) | Two-pass tokens (est.) |
|--------|---------------------------|------------------------|
| 38 | ~15K | ~8K (pass 1) + ~8K (pass 2) |
| 200 | ~80K | ~12K + ~15K |
| 1,000 | ~400K (exceeds limit) | ~50K + ~20K |
| 5,000 | Impossible | ~250K + ~25K |

### Pass 1 candidate sensitivity

The pass 1 prompt instructs Claude to be **generous** — it's better to include a false positive than miss a real duplicate. Pass 2 then confirms or rejects each candidate with the full descriptions. This ensures high recall without sacrificing precision.

---

## Troubleshooting

### "No module named 'claude_agent_sdk'"

Make sure your virtual environment is activated and dependencies are installed:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### "ERROR: Missing environment variables"

Your `.env` file is missing or incomplete. Copy from the example:

```powershell
copy .env.example .env
```

Then fill in all four variables.

### Jira API returns 410 Gone

The old `/rest/api/2/search` endpoint has been deprecated by Atlassian. This tool uses the current `POST /rest/api/3/search/jql` endpoint. If you still get 410 errors, check that your Jira instance is on Jira Cloud (not Jira Server/Data Center).

### Jira API returns 401 Unauthorized

- Verify your `JIRA_EMAIL` matches the email on your Atlassian account
- Generate a fresh API token at https://id.atlassian.com/manage-profile/security/api-tokens
- Make sure there are no trailing spaces in your `.env` values

### Claude returns no response or empty result

- Verify you are logged into Claude Code CLI: run `claude --version`
- If your session expired, run `claude login` again

### JSON parsing warning

If you see "Could not parse Claude's response as JSON", the raw response is saved to `duplicate_report.json` under the `raw_response` key. This usually means Claude added unexpected text. Try running again — results may vary between runs.

### Two-pass: Pass 1 finds no candidates

If pass 1 returns no candidate groups, the tool still proceeds to generate solutions for all issues as unique. This can happen if the summaries are too different for Claude to detect similarity. Consider lowering the `SINGLE_PASS_THRESHOLD` to force single-pass mode, which uses full descriptions.