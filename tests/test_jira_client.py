"""Tests for jira_client module — JiraClient and parse_description."""

import unittest
from unittest.mock import patch, MagicMock

from jira_duplicate_detector.jira_client import JiraClient, parse_description


class TestParseDescription(unittest.TestCase):
    """Tests for ADF description parser."""

    def test_none_returns_empty(self):
        self.assertEqual(parse_description(None), "")

    def test_plain_string_passthrough(self):
        self.assertEqual(parse_description("hello world"), "hello world")

    def test_simple_adf_paragraph(self):
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Login fails after reset"}
                    ]
                }
            ]
        }
        self.assertEqual(parse_description(adf), "Login fails after reset")

    def test_multi_paragraph_adf(self):
        adf = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "First paragraph."}]
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Second paragraph."}]
                }
            ]
        }
        self.assertEqual(parse_description(adf), "First paragraph. Second paragraph.")

    def test_nested_content(self):
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item 1"}]
                                }
                            ]
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item 2"}]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertEqual(parse_description(adf), "Item 1 Item 2")

    def test_empty_adf(self):
        adf = {"type": "doc", "content": []}
        self.assertEqual(parse_description(adf), "")

    def test_adf_with_non_text_nodes(self):
        adf = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Before "},
                        {"type": "mention", "attrs": {"id": "user1"}},
                        {"type": "text", "text": " after"}
                    ]
                }
            ]
        }
        result = parse_description(adf)
        self.assertIn("Before", result)
        self.assertIn("after", result)
        # Non-text nodes are skipped, text nodes joined with spaces
        self.assertNotIn("mention", result)

    def test_list_input(self):
        nodes = [
            {"type": "text", "text": "a"},
            {"type": "text", "text": "b"},
        ]
        self.assertEqual(parse_description(nodes), "a b")


class TestJiraClient(unittest.TestCase):
    """Tests for JiraClient."""

    def test_init_strips_trailing_slash(self):
        client = JiraClient("https://example.atlassian.net/", "a@b.com", "token")
        self.assertEqual(client.base_url, "https://example.atlassian.net")

    @patch("jira_duplicate_detector.jira_client.requests.post")
    def test_fetch_single_page(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "issues": [{"key": "TEST-1", "fields": {}}],
            "isLast": True,
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        client = JiraClient("https://example.atlassian.net", "a@b.com", "token")
        issues = client.fetch_all_issues("TEST")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["key"], "TEST-1")
        mock_post.assert_called_once()

    @patch("jira_duplicate_detector.jira_client.requests.post")
    def test_fetch_multiple_pages(self, mock_post):
        page1 = MagicMock()
        page1.json.return_value = {
            "issues": [{"key": "TEST-1", "fields": {}}],
            "isLast": False,
            "nextPageToken": "token123",
        }
        page1.raise_for_status = MagicMock()

        page2 = MagicMock()
        page2.json.return_value = {
            "issues": [{"key": "TEST-2", "fields": {}}],
            "isLast": True,
        }
        page2.raise_for_status = MagicMock()

        mock_post.side_effect = [page1, page2]

        client = JiraClient("https://example.atlassian.net", "a@b.com", "token")
        issues = client.fetch_all_issues("TEST")

        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["key"], "TEST-1")
        self.assertEqual(issues[1]["key"], "TEST-2")
        self.assertEqual(mock_post.call_count, 2)

        # Second call should include nextPageToken
        second_call_body = mock_post.call_args_list[1][1]["json"]
        self.assertEqual(second_call_body["nextPageToken"], "token123")

    @patch("jira_duplicate_detector.jira_client.requests.post")
    def test_fetch_empty_project(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"issues": [], "isLast": True}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        client = JiraClient("https://example.atlassian.net", "a@b.com", "token")
        issues = client.fetch_all_issues("EMPTY")

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
