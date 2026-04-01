"""Tests for analyzer module — prompt loading and JSON extraction."""

import unittest

from jira_duplicate_detector.analyzer import load_prompt, extract_json


class TestLoadPrompt(unittest.TestCase):

    def test_loads_default_prompt(self):
        prompt = load_prompt()
        self.assertIn("near-duplicate", prompt)
        self.assertIn("analysis_summary", prompt)

    def test_loads_pass1_prompt(self):
        prompt = load_prompt("pass1_candidates.txt")
        self.assertIn("candidate_groups", prompt)
        self.assertIn("ungrouped_keys", prompt)

    def test_loads_pass2_prompt(self):
        prompt = load_prompt("pass2_analysis.txt")
        self.assertIn("analysis_summary", prompt)
        self.assertIn("duplicate_groups", prompt)
        self.assertIn("unique_issues", prompt)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_prompt("nonexistent_prompt.txt")

    def test_loads_custom_file(self):
        from jira_duplicate_detector.analyzer import PROMPTS_DIR
        test_file = PROMPTS_DIR / "_test_prompt.txt"
        try:
            test_file.write_text("custom prompt content", encoding="utf-8")
            result = load_prompt("_test_prompt.txt")
            self.assertEqual(result, "custom prompt content")
        finally:
            test_file.unlink(missing_ok=True)


class TestExtractJson(unittest.TestCase):

    def test_pure_json(self):
        text = '{"key": "value"}'
        result = extract_json(text)
        self.assertEqual(result, {"key": "value"})

    def test_json_with_preamble(self):
        text = 'Here is the analysis.\n\n{"analysis_summary": {"total": 5}}'
        result = extract_json(text)
        self.assertEqual(result["analysis_summary"]["total"], 5)

    def test_json_with_markdown_fences(self):
        text = '```json\n{"key": "value"}\n```'
        result = extract_json(text)
        self.assertEqual(result, {"key": "value"})

    def test_json_with_text_before_and_after(self):
        text = 'Some text before {"data": 42} some text after'
        result = extract_json(text)
        self.assertEqual(result, {"data": 42})

    def test_invalid_json_returns_raw(self):
        text = "This is not JSON at all"
        result = extract_json(text)
        self.assertIn("raw_response", result)
        self.assertEqual(result["raw_response"], text)

    def test_no_braces_returns_raw(self):
        text = "No braces here"
        result = extract_json(text)
        self.assertIn("raw_response", result)

    def test_nested_json(self):
        text = '{"outer": {"inner": [1, 2, 3]}}'
        result = extract_json(text)
        self.assertEqual(result["outer"]["inner"], [1, 2, 3])

    def test_empty_string(self):
        result = extract_json("")
        self.assertIn("raw_response", result)

    def test_real_world_response(self):
        text = (
            "Let me analyze these issues.\n\n"
            '{"analysis_summary": {"total_issues_analyzed": 38, '
            '"duplicate_groups_found": 8, "total_duplicate_issues": 19, '
            '"unique_issues": 19}, "duplicate_groups": [], "unique_issues": []}'
        )
        result = extract_json(text)
        self.assertEqual(result["analysis_summary"]["total_issues_analyzed"], 38)
        self.assertEqual(result["analysis_summary"]["duplicate_groups_found"], 8)

    def test_pass1_response(self):
        text = (
            '{"candidate_groups": ['
            '{"group_id": 1, "theme": "Login", "issue_keys": ["SCRUM-1", "SCRUM-2"]}'
            '], "ungrouped_keys": ["SCRUM-3"]}'
        )
        result = extract_json(text)
        self.assertEqual(len(result["candidate_groups"]), 1)
        self.assertEqual(result["candidate_groups"][0]["issue_keys"], ["SCRUM-1", "SCRUM-2"])
        self.assertEqual(result["ungrouped_keys"], ["SCRUM-3"])


if __name__ == "__main__":
    unittest.main()
