# Architecture and Module Reference

## Overview

The tool follows a pipeline architecture with two analysis modes. Each step is handled by a dedicated module, making it easy to test, modify, or replace individual components.

### Single-Pass Mode (<= 30 issues)

```
  .env                 prompts/system_prompt.txt
   |                          |
   v                          v
[JiraClient]  -->  [formatter]  -->  [analyzer]  -->  [report]
 jira_client.py     formatter.py     analyzer.py      report.py
   |                    |                |                |
   |  Fetch issues      |  Format full   |  Claude AI     |  Save JSON
   |  from Jira API     |  details       |  (1 call)      |  Print console
   v                    v                v                v
 Raw JSON issues    Formatted text    JSON result     duplicate_report.json
```

### Two-Pass Mode (> 30 issues)

```
  .env             prompts/pass1_candidates.txt    prompts/pass2_analysis.txt
   |                          |                            |
   v                          v                            v
[JiraClient]  -->  [formatter]  -->  [analyzer PASS 1]  -->  [analyzer PASS 2]  -->  [report]
                       |                   |                       |
                       |  Summary-only     |  Candidate groups     |  Full analysis
                       |  (all issues)     |  (keys only)          |  (candidates only)
                       |                   |                       |
                       |  Full details     |                       |
                       |  (candidates      |                       |
                       |   only)           |                       |
```

The entry point `main.py` orchestrates the pipeline and chooses the mode.

---

## Module Reference

### `jira_client.py`

Handles all communication with the Jira Cloud REST API.

**Classes:**

- `JiraClient(base_url, email, api_token)`
  - `fetch_all_issues(project_key) -> list[dict]` — Fetches all issues from a project using `POST /rest/api/3/search/jql` with cursor-based pagination (`nextPageToken`/`isLast`). Returns raw Jira issue dicts.

**Functions:**

- `parse_description(desc) -> str` — Extracts plain text from Jira's ADF (Atlassian Document Format). Handles `None`, plain strings, and nested ADF JSON structures by recursively walking the node tree and collecting `text` nodes.

**API details:**
- Endpoint: `POST /rest/api/3/search/jql`
- Auth: HTTP Basic (email + API token)
- Pagination: cursor-based (`nextPageToken` in request body, `isLast` in response)
- Fields fetched: summary, description, issuetype, status, priority, created, updated
- Page size: 100 issues per request

---

### `formatter.py`

Transforms raw Jira issue dicts into text formats for Claude.

**Functions:**

- `format_issues(issues: list[dict]) -> str` — Full formatting with all fields. Each issue is rendered as:

```
[SCRUM-1] (Bug | To Do | Priority: High)
  Summary: Users unable to login after password reset
  Description: The extracted plain-text description...
```

Issues are separated by double newlines. Missing fields default to `N/A`. Empty descriptions show `(no description)`.

- `format_issues_summary_only(issues: list[dict]) -> str` — Lightweight formatting with key + summary only (no descriptions). Used in two-pass mode for pass 1. Each issue is one line:

```
[SCRUM-1] Users unable to login after password reset
```

- `filter_issues_by_keys(issues: list[dict], keys: set[str]) -> list[dict]` — Returns only issues whose key is in the given set. Used in two-pass mode to split issues into candidate and ungrouped sets. Preserves original order.

---

### `analyzer.py`

Handles prompt loading and Claude AI integration.

**Constants:**

- `PROMPTS_DIR` — Path to the `prompts/` directory, resolved relative to the module file.

**Functions:**

- `load_prompt(filename="system_prompt.txt") -> str` — Loads a prompt file from the `prompts/` directory. Raises `FileNotFoundError` if the file doesn't exist.

- `extract_json(text: str) -> dict` — Extracts a JSON object from Claude's response text. Finds the first `{` and last `}` in the text and attempts to parse the substring as JSON. Returns `{"raw_response": text}` if parsing fails.

- `analyze_issues(issues_text, project_key, issue_count) -> str` — Single-pass analysis. Sends all issues with full details in one prompt using `system_prompt.txt`. Returns Claude's raw response text.

- `analyze_pass1_candidates(summaries_text, project_key, issue_count) -> str` — Two-pass: pass 1. Sends only keys + summaries using `pass1_candidates.txt`. Returns raw response containing candidate groups JSON.

- `analyze_pass2_details(candidate_groups, grouped_text, ungrouped_text, project_key, total_issues) -> str` — Two-pass: pass 2. Sends full details of candidate issues plus ungrouped issues using `pass2_analysis.txt`. Returns raw response containing the full analysis JSON.

- `_query_claude(prompt, system_prompt) -> str` — Internal helper that sends a prompt to Claude via the Agent SDK `query()` function and returns the raw result text. The Claude Agent SDK import is deferred (inside this function) to allow testing the other functions without requiring the SDK.

---

### `report.py`

Handles all output — both file and console.

**Functions:**

- `save_report(report: dict, filepath="duplicate_report.json") -> str` — Writes the report dict to a JSON file with 2-space indentation and UTF-8 encoding. Returns the filepath.

- `print_report(report: dict)` — Prints a formatted console summary including:
  - Analysis summary (totals)
  - Each duplicate group with theme, confidence, issues (primary marked with `*`), similarity explanation, solution, priority, and complexity
  - List of unique issues

---

### `main.py`

Entry point that orchestrates the pipeline:

1. Loads environment variables from `.env`
2. Validates that all required variables are set
3. Creates a `JiraClient` and fetches all issues
4. Chooses analysis mode based on `SINGLE_PASS_THRESHOLD` (default: 30)
   - **Single-pass** (`run_single_pass`): formats all issues, sends one prompt
   - **Two-pass** (`run_two_pass`): sends summaries first, then full details for candidates
5. Extracts JSON via `extract_json()`
6. Saves report via `save_report()`
7. Prints console report via `print_report()`

Run with: `python main.py`

---

## Prompt Files

| File | Mode | Input | Output |
|------|------|-------|--------|
| `system_prompt.txt` | Single-pass | All issues, full details | Final analysis JSON |
| `pass1_candidates.txt` | Two-pass, pass 1 | All issues, keys + summaries only | Candidate groups JSON |
| `pass2_analysis.txt` | Two-pass, pass 2 | Candidate issues with full details + ungrouped issues | Final analysis JSON |

### Pass 1 output schema

```json
{
  "candidate_groups": [
    {
      "group_id": 1,
      "theme": "Login Issues",
      "issue_keys": ["SCRUM-1", "SCRUM-2", "SCRUM-3"]
    }
  ],
  "ungrouped_keys": ["SCRUM-14", "SCRUM-15"]
}
```

### Pass 2 / Single-pass output schema

See [Output Format in README.md](README.md#output-format).

---

## Data Flow

### Single-Pass

```
Jira Cloud API
     |
     | POST /rest/api/3/search/jql (paginated)
     v
JiraClient.fetch_all_issues()
     |
     | list[dict] — raw Jira issue objects
     v
format_issues()                        system_prompt.txt
     |                                        |
     | str — full formatted text               |
     v                                        v
analyze_issues()  <----  Claude Agent SDK  <----
     |
     | str — raw Claude response
     v
extract_json()
     |
     | dict — parsed JSON report
     v
save_report()  +  print_report()
     |                |
     v                v
duplicate_report.json   Console output
```

### Two-Pass

```
Jira Cloud API
     |
     v
JiraClient.fetch_all_issues()
     |
     | list[dict] — all issues
     |
     +----> format_issues_summary_only()       pass1_candidates.txt
     |           |                                     |
     |           | str — keys + summaries only          |
     |           v                                     v
     |      analyze_pass1_candidates()  <----  Claude  <----
     |           |
     |           | candidate_groups + ungrouped_keys
     |           v
     +----> filter_issues_by_keys(grouped)
     |           |
     |           v
     |      format_issues(candidates)           pass2_analysis.txt
     |           |                                     |
     +----> filter_issues_by_keys(ungrouped)           |
     |           |                                     |
     |           v                                     v
     |      analyze_pass2_details()  <----  Claude  <----
     |           |
     |           | str — raw Claude response
     v           v
          extract_json()
               |
               v
     save_report()  +  print_report()
```

---

## Testing Strategy

Tests are organized to mirror the module structure. Each test file covers one module.

**Principles:**
- All tests run offline (no network, no Claude, no Jira)
- External dependencies (HTTP requests) are mocked
- The `analyze_*` and `_query_claude` functions are NOT tested in unit tests because they require a live Claude session. The functions they depend on (`load_prompt`, `extract_json`) are fully tested.
- Tests use `unittest` (stdlib) so they work without pytest, but pytest is included for convenience

**Test counts:**

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_jira_client.py` | 11 | `JiraClient` (single page, multi-page, empty) + `parse_description` (8 ADF cases) |
| `test_formatter.py` | 16 | `format_issues` (7) + `format_issues_summary_only` (4) + `filter_issues_by_keys` (5) |
| `test_analyzer.py` | 15 | `load_prompt` (5: default, pass1, pass2, missing, custom) + `extract_json` (10 cases) |
| `test_report.py` | 8 | `save_report` (2) + `print_report` (6) |
| **Total** | **50** | |

**Adding tests for new features:**
1. Add your feature to the appropriate module
2. Add corresponding tests in the matching test file
3. Run `python -m unittest discover tests -v` or `pytest tests/ -v` to verify