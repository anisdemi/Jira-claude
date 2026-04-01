"""Report output — console printing and JSON file saving."""

import json


def save_report(report: dict, filepath: str = "duplicate_report.json") -> str:
    """Save report dict to a JSON file. Returns the filepath."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return filepath


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
