"""Claude-powered duplicate analysis and JSON extraction."""

import json
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(filename: str = "system_prompt.txt") -> str:
    """Load a prompt from the prompts directory."""
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def extract_json(text: str) -> dict:
    """Extract a JSON object from text that may contain preamble or markdown fences.

    Returns the parsed dict, or {"raw_response": text} if parsing fails.
    """
    cleaned = text.strip()
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1:
        cleaned = cleaned[first_brace:last_brace + 1]

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"raw_response": text}


async def _query_claude(prompt: str, system_prompt: str) -> str:
    """Send a prompt to Claude and return the raw response text."""
    from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

    result_text = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            system_prompt=system_prompt,
            max_turns=1,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text


async def analyze_issues(issues_text: str, project_key: str, issue_count: int) -> str:
    """Single-pass analysis: send all issues with full details to Claude.

    Used when the issue count is small enough to fit in one prompt.
    Returns raw result text.
    """
    system_prompt = load_prompt("system_prompt.txt")

    prompt = (
        f"Here are {issue_count} Jira issues from our banking platform project ({project_key}).\n"
        f"Analyze them for near-duplicates and return the JSON analysis.\n\n"
        f"{issues_text}"
    )

    return await _query_claude(prompt, system_prompt)


async def analyze_pass1_candidates(summaries_text: str, project_key: str, issue_count: int) -> str:
    """Pass 1: Send only summaries to identify candidate duplicate groups.

    Returns raw result text containing candidate groups JSON.
    """
    system_prompt = load_prompt("pass1_candidates.txt")

    prompt = (
        f"Here are {issue_count} Jira issues (key + summary only) "
        f"from project {project_key}.\n"
        f"Identify candidate groups of potential near-duplicates.\n\n"
        f"{summaries_text}"
    )

    return await _query_claude(prompt, system_prompt)


async def analyze_pass2_details(
    candidate_groups: list[dict],
    grouped_text: str,
    ungrouped_text: str,
    project_key: str,
    total_issues: int,
) -> str:
    """Pass 2: Send full details of candidate issues for confirmation and analysis.

    Returns raw result text containing the full analysis JSON.
    """
    system_prompt = load_prompt("pass2_analysis.txt")

    groups_summary = ""
    for group in candidate_groups:
        keys = ", ".join(group["issue_keys"])
        groups_summary += f"- Group '{group['theme']}': {keys}\n"

    prompt = (
        f"Project {project_key} — {total_issues} total issues.\n\n"
        f"== CANDIDATE DUPLICATE GROUPS (from pass 1) ==\n"
        f"{groups_summary}\n"
        f"== FULL DETAILS OF CANDIDATE ISSUES ==\n"
        f"{grouped_text}\n\n"
        f"== UNGROUPED ISSUES (provide solutions only) ==\n"
        f"{ungrouped_text}"
    )

    return await _query_claude(prompt, system_prompt)
