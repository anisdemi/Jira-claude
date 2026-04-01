"""Tests for report module — save and print."""

import json
import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

from jira_duplicate_detector.report import save_report, print_report


SAMPLE_REPORT = {
    "analysis_summary": {
        "total_issues_analyzed": 10,
        "duplicate_groups_found": 2,
        "total_duplicate_issues": 5,
        "unique_issues": 5,
    },
    "duplicate_groups": [
        {
            "group_id": 1,
            "theme": "Login Issues",
            "confidence": "HIGH",
            "issues": [
                {"key": "SCRUM-1", "summary": "Login fails"},
                {"key": "SCRUM-2", "summary": "Cannot sign in"},
            ],
            "similarity_explanation": "Both about login failure",
            "recommended_primary": "SCRUM-1",
            "recommended_action": "Merge SCRUM-2 into SCRUM-1",
            "solution": {
                "description": "Fix auth cache",
                "priority": "CRITICAL",
                "complexity": "Medium",
                "technical_details": "Invalidate cache on password change",
            },
        },
    ],
    "unique_issues": [
        {
            "key": "SCRUM-5",
            "summary": "Add dark mode",
            "solution": {
                "description": "Implement dark theme",
                "priority": "LOW",
                "complexity": "Simple",
            },
        },
    ],
}


class TestSaveReport(unittest.TestCase):

    def test_saves_valid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result_path = save_report(SAMPLE_REPORT, filepath)
            self.assertEqual(result_path, filepath)

            with open(filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            self.assertEqual(loaded["analysis_summary"]["total_issues_analyzed"], 10)
            self.assertEqual(len(loaded["duplicate_groups"]), 1)
            self.assertEqual(len(loaded["unique_issues"]), 1)
        finally:
            os.unlink(filepath)

    def test_handles_unicode(self):
        report = {"note": "Transfert bancaire en euros"}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            filepath = f.name

        try:
            save_report(report, filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertIn("euros", loaded["note"])
        finally:
            os.unlink(filepath)


class TestPrintReport(unittest.TestCase):

    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_summary(self, mock_stdout):
        print_report(SAMPLE_REPORT)
        output = mock_stdout.getvalue()
        self.assertIn("Total issues analyzed: 10", output)
        self.assertIn("Duplicate groups found: 2", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_group_details(self, mock_stdout):
        print_report(SAMPLE_REPORT)
        output = mock_stdout.getvalue()
        self.assertIn("Login Issues", output)
        self.assertIn("SCRUM-1", output)
        self.assertIn("SCRUM-2", output)
        self.assertIn("HIGH", output)
        self.assertIn("Fix auth cache", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_prints_unique_issues(self, mock_stdout):
        print_report(SAMPLE_REPORT)
        output = mock_stdout.getvalue()
        self.assertIn("UNIQUE ISSUES", output)
        self.assertIn("SCRUM-5", output)
        self.assertIn("Add dark mode", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_primary_issue_marker(self, mock_stdout):
        print_report(SAMPLE_REPORT)
        output = mock_stdout.getvalue()
        # Primary issue SCRUM-1 should have a * marker
        self.assertIn(" * SCRUM-1", output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_empty_report(self, mock_stdout):
        empty = {"analysis_summary": {}, "duplicate_groups": [], "unique_issues": []}
        print_report(empty)
        output = mock_stdout.getvalue()
        self.assertIn("Total issues analyzed: ?", output)


if __name__ == "__main__":
    unittest.main()
