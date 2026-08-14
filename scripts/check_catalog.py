#!/usr/bin/env python3
"""Validate data/tools.json and keep it aligned with docs/TOOL_CATALOG.md."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_JSON = ROOT / "data" / "tools.json"
CATALOG_MD = ROOT / "docs" / "TOOL_CATALOG.md"

REQUIRED_TOOL_FIELDS = ("name", "url", "summary", "offline_capable", "optional_cloud", "tags")
LINK_RE = re.compile(r"^- \[([^\]]+)\]\(([^)]+)\) - (.+)$")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def parse_markdown_tools(path: Path) -> list[tuple[str, str, str]]:
    tools: list[tuple[str, str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = LINK_RE.match(line.strip())
        if match:
            tools.append((match.group(1), match.group(2), match.group(3).rstrip(".")))
    return tools


def check_json_structure(catalog: dict, errors: list[str]) -> list[tuple[str, str]]:
    if "categories" not in catalog or not isinstance(catalog["categories"], list):
        fail("tools.json missing categories list", errors)
        return []

    seen_names: set[str] = set()
    seen_urls: set[str] = set()
    tools: list[tuple[str, str]] = []

    for category in catalog["categories"]:
        if "id" not in category or "name" not in category:
            fail(f"category missing id/name: {category!r}", errors)
            continue
        if "tools" not in category or not isinstance(category["tools"], list):
            fail(f"category {category.get('id')} missing tools list", errors)
            continue
        for tool in category["tools"]:
            for field in REQUIRED_TOOL_FIELDS:
                if field not in tool:
                    fail(f"{category.get('id')}/{tool.get('name', '?')} missing field: {field}", errors)
            name = tool.get("name")
            url = tool.get("url")
            if not isinstance(tool.get("tags"), list):
                fail(f"{name}: tags must be a list", errors)
            if not isinstance(tool.get("offline_capable"), bool):
                fail(f"{name}: offline_capable must be bool", errors)
            if not isinstance(tool.get("optional_cloud"), bool):
                fail(f"{name}: optional_cloud must be bool", errors)
            if name in seen_names:
                fail(f"duplicate tool name: {name}", errors)
            if url in seen_urls:
                fail(f"duplicate tool url: {url}", errors)
            if name:
                seen_names.add(name)
            if url:
                seen_urls.add(url)
            if name and url:
                tools.append((name, url))
    return tools


def check_markdown_alignment(
    json_tools: list[tuple[str, str]],
    md_tools: list[tuple[str, str, str]],
    errors: list[str],
) -> None:
    json_by_name = {name: url for name, url in json_tools}
    md_by_name = {name: url for name, url, _ in md_tools}

    missing_in_json = sorted(set(md_by_name) - set(json_by_name))
    missing_in_md = sorted(set(json_by_name) - set(md_by_name))

    for name in missing_in_json:
        fail(f"markdown tool missing from tools.json: {name}", errors)
    for name in missing_in_md:
        fail(f"tools.json tool missing from TOOL_CATALOG.md: {name}", errors)

    for name in sorted(set(json_by_name) & set(md_by_name)):
        if json_by_name[name] != md_by_name[name]:
            fail(
                f"URL mismatch for {name}: json={json_by_name[name]} md={md_by_name[name]}",
                errors,
            )


def main() -> int:
    errors: list[str] = []

    if not CATALOG_JSON.is_file():
        print(f"Missing {CATALOG_JSON}", file=sys.stderr)
        return 1
    if not CATALOG_MD.is_file():
        print(f"Missing {CATALOG_MD}", file=sys.stderr)
        return 1

    try:
        catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON in {CATALOG_JSON}: {exc}", file=sys.stderr)
        return 1

    json_tools = check_json_structure(catalog, errors)
    md_tools = parse_markdown_tools(CATALOG_MD)
    if not md_tools:
        fail("no tools parsed from TOOL_CATALOG.md", errors)
    check_markdown_alignment(json_tools, md_tools, errors)

    if errors:
        print("Catalog check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"OK: {len(json_tools)} tools across "
        f"{len(catalog.get('categories', []))} categories; "
        "JSON and TOOL_CATALOG.md aligned."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
