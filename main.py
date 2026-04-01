"""
Jira Duplicate Issue Detector — Entry Point

Two-pass analysis:
  Pass 1 — Send only issue keys + summaries (lightweight) to identify candidate groups
  Pass 2 — Send full details of candidates only for confirmation and solutions

Falls back to single-pass for small projects (under the threshold).
"""

import os
import anyio
import requests
from dotenv import load_dotenv

from jira_duplicate_detector import (
    JiraClient,
    format_issues,
    format_issues_summary_only,
    filter_issues_by_keys,
    analyze_issues,
    analyze_pass1_candidates,
    analyze_pass2_details,
    extract_json,
    print_report,
    save_report,
)

load_dotenv()

# Below this threshold, use single-pass (all issues + full details in one prompt).
# Above it, use two-pass to stay within context limits.
SINGLE_PASS_THRESHOLD = 30


async def run_single_pass(issues, project_key):
    """Single-pass: send all issues with full details in one prompt."""
    print("Using single-pass analysis...")
    issues_text = format_issues(issues)
    result_text = await analyze_issues(issues_text, project_key, len(issues))
    return result_text


async def run_two_pass(issues, project_key):
    """Two-pass: summaries first, then full details for candidates only."""

    # Pass 1: summaries only
    print("Pass 1: Sending summaries to identify candidate groups...")
    summaries_text = format_issues_summary_only(issues)
    pass1_result = await analyze_pass1_candidates(summaries_text, project_key, len(issues))

    if not pass1_result:
        print("ERROR: No response from Claude in pass 1.")
        return ""

    pass1_data = extract_json(pass1_result)
    candidate_groups = pass1_data.get("candidate_groups", [])

    if not candidate_groups:
        print("No candidate duplicate groups found in pass 1.")
        # Still run pass 2 to get solutions for all issues
        candidate_groups = []

    # Collect keys from candidate groups
    grouped_keys = set()
    for group in candidate_groups:
        for key in group.get("issue_keys", []):
            grouped_keys.add(key)

    ungrouped_keys = {issue["key"] for issue in issues} - grouped_keys

    print(f"  Found {len(candidate_groups)} candidate groups ({len(grouped_keys)} issues)")
    print(f"  {len(ungrouped_keys)} ungrouped issues")

    # Pass 2: full details for candidates + summaries for ungrouped
    print("Pass 2: Sending full details for confirmation and solutions...")
    grouped_issues = filter_issues_by_keys(issues, grouped_keys)
    ungrouped_issues = filter_issues_by_keys(issues, ungrouped_keys)

    grouped_text = format_issues(grouped_issues) if grouped_issues else "(none)"
    ungrouped_text = format_issues(ungrouped_issues) if ungrouped_issues else "(none)"

    pass2_result = await analyze_pass2_details(
        candidate_groups, grouped_text, ungrouped_text, project_key, len(issues)
    )

    return pass2_result


async def main():
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")

    missing = [
        name for name, val in [
            ("JIRA_BASE_URL", base_url),
            ("JIRA_EMAIL", email),
            ("JIRA_API_TOKEN", api_token),
            ("JIRA_PROJECT_KEY", project_key),
        ]
        if not val
    ]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        print("Please configure your .env file. See .env.example for the template.")
        return

    # Step 1: Fetch issues from Jira
    print(f"\nFetching issues from Jira project {project_key}...")
    jira = JiraClient(base_url, email, api_token)
    try:
        issues = jira.fetch_all_issues(project_key)
    except requests.HTTPError as e:
        print(f"ERROR: Failed to fetch issues from Jira: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        return

    print(f"Fetched {len(issues)} issues.")

    if not issues:
        print("No issues found. Nothing to analyze.")
        return

    # Step 2: Analyze — choose strategy based on issue count
    print(f"Sending issues to Claude for duplicate analysis...")

    if len(issues) <= SINGLE_PASS_THRESHOLD:
        result_text = await run_single_pass(issues, project_key)
    else:
        result_text = await run_two_pass(issues, project_key)

    if not result_text:
        print("ERROR: No response from Claude.")
        return

    # Step 3: Parse and save report
    report = extract_json(result_text)

    filepath = save_report(report)
    print(f"Report saved to {filepath}")

    # Step 4: Print console report
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
