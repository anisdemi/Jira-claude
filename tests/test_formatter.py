"""Tests for formatter module."""

import unittest

from jira_duplicate_detector.formatter import (
    format_issues,
    format_issues_summary_only,
    filter_issues_by_keys,
)


def _make_issue(key, summary, description=None, issue_type="Bug", status="To Do", priority="High"):
    """Helper to build a minimal Jira issue dict."""
    issue = {
        "key": key,
        "fields": {
            "summary": summary,
            "issuetype": {"name": issue_type},
            "status": {"name": status},
            "priority": {"name": priority} if priority else None,
            "description": description,
        }
    }
    return issue


class TestFormatIssues(unittest.TestCase):

    def test_single_issue(self):
        issues = [_make_issue("SCRUM-1", "Login fails", "Users cannot login")]
        result = format_issues(issues)
        self.assertIn("[SCRUM-1]", result)
        self.assertIn("Login fails", result)
        self.assertIn("Users cannot login", result)
        self.assertIn("Bug", result)
        self.assertIn("To Do", result)

    def test_multiple_issues_separated(self):
        issues = [
            _make_issue("SCRUM-1", "First issue"),
            _make_issue("SCRUM-2", "Second issue"),
        ]
        result = format_issues(issues)
        self.assertIn("[SCRUM-1]", result)
        self.assertIn("[SCRUM-2]", result)
        self.assertIn("\n\n", result)

    def test_no_description(self):
        issues = [_make_issue("SCRUM-1", "No desc", description=None)]
        result = format_issues(issues)
        self.assertIn("(no description)", result)

    def test_no_priority(self):
        issues = [_make_issue("SCRUM-1", "No priority", priority=None)]
        result = format_issues(issues)
        self.assertIn("Priority: N/A", result)

    def test_adf_description(self):
        adf = {
            "type": "doc",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": "ADF content here"}]}
            ]
        }
        issues = [_make_issue("SCRUM-1", "ADF test", description=adf)]
        result = format_issues(issues)
        self.assertIn("ADF content here", result)

    def test_empty_list(self):
        self.assertEqual(format_issues([]), "")

    def test_issue_type_and_status(self):
        issues = [_make_issue("SCRUM-5", "A story", issue_type="Story", status="In Progress")]
        result = format_issues(issues)
        self.assertIn("Story", result)
        self.assertIn("In Progress", result)


class TestFormatIssuesSummaryOnly(unittest.TestCase):

    def test_single_issue(self):
        issues = [_make_issue("SCRUM-1", "Login fails", "long description ignored")]
        result = format_issues_summary_only(issues)
        self.assertEqual(result, "[SCRUM-1] Login fails")
        self.assertNotIn("long description", result)

    def test_multiple_issues(self):
        issues = [
            _make_issue("SCRUM-1", "First"),
            _make_issue("SCRUM-2", "Second"),
        ]
        result = format_issues_summary_only(issues)
        lines = result.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], "[SCRUM-1] First")
        self.assertEqual(lines[1], "[SCRUM-2] Second")

    def test_empty_list(self):
        self.assertEqual(format_issues_summary_only([]), "")

    def test_no_description_in_output(self):
        adf = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "secret"}]}]}
        issues = [_make_issue("SCRUM-1", "Summary only", description=adf)]
        result = format_issues_summary_only(issues)
        self.assertNotIn("secret", result)
        self.assertIn("Summary only", result)


class TestFilterIssuesByKeys(unittest.TestCase):

    def test_filter_subset(self):
        issues = [
            _make_issue("SCRUM-1", "A"),
            _make_issue("SCRUM-2", "B"),
            _make_issue("SCRUM-3", "C"),
        ]
        result = filter_issues_by_keys(issues, {"SCRUM-1", "SCRUM-3"})
        keys = [i["key"] for i in result]
        self.assertEqual(keys, ["SCRUM-1", "SCRUM-3"])

    def test_filter_empty_keys(self):
        issues = [_make_issue("SCRUM-1", "A")]
        result = filter_issues_by_keys(issues, set())
        self.assertEqual(result, [])

    def test_filter_all_keys(self):
        issues = [_make_issue("SCRUM-1", "A"), _make_issue("SCRUM-2", "B")]
        result = filter_issues_by_keys(issues, {"SCRUM-1", "SCRUM-2"})
        self.assertEqual(len(result), 2)

    def test_filter_nonexistent_key(self):
        issues = [_make_issue("SCRUM-1", "A")]
        result = filter_issues_by_keys(issues, {"SCRUM-99"})
        self.assertEqual(result, [])

    def test_preserves_order(self):
        issues = [
            _make_issue("SCRUM-3", "C"),
            _make_issue("SCRUM-1", "A"),
            _make_issue("SCRUM-2", "B"),
        ]
        result = filter_issues_by_keys(issues, {"SCRUM-2", "SCRUM-3"})
        keys = [i["key"] for i in result]
        self.assertEqual(keys, ["SCRUM-3", "SCRUM-2"])


if __name__ == "__main__":
    unittest.main()
