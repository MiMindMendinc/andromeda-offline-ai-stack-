#!/usr/bin/env python3
"""Search the Andromeda tool catalog (data/tools.json)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "data" / "tools.json"


def load_catalog(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def iter_tools(catalog: dict):
    for category in catalog.get("categories", []):
        for tool in category.get("tools", []):
            yield category, tool


def matches(tool: dict, category: dict, query: str, tag: str | None, recommended: bool) -> bool:
    if recommended and not tool.get("recommended"):
        return False
    if tag and tag.lower() not in [t.lower() for t in tool.get("tags", [])]:
        return False
    if not query:
        return True
    haystack = " ".join(
        [
            tool.get("name", ""),
            tool.get("summary", ""),
            category.get("name", ""),
            category.get("id", ""),
            " ".join(tool.get("tags", [])),
            tool.get("url", ""),
        ]
    ).lower()
    return query.lower() in haystack


def format_tool(category: dict, tool: dict) -> str:
    flags = []
    if tool.get("recommended"):
        flags.append("recommended")
    if tool.get("optional_cloud"):
        flags.append("optional-cloud")
    if tool.get("offline_capable"):
        flags.append("offline")
    flag_text = f" [{', '.join(flags)}]" if flags else ""
    tags = ", ".join(tool.get("tags", []))
    return (
        f"{tool.get('name')}{flag_text}\n"
        f"  category: {category.get('name')}\n"
        f"  summary:  {tool.get('summary')}\n"
        f"  url:      {tool.get('url')}\n"
        f"  tags:     {tags}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search Andromeda tools.json")
    parser.add_argument("query", nargs="?", default="", help="Substring to match")
    parser.add_argument("--tag", help="Filter by tag")
    parser.add_argument("--recommended", action="store_true", help="Only recommended tools")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help="Path to tools.json",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON results")
    args = parser.parse_args(argv)

    if not args.catalog.is_file():
        print(f"Catalog not found: {args.catalog}", file=sys.stderr)
        return 1

    catalog = load_catalog(args.catalog)
    results = [
        {"category": category.get("id"), "category_name": category.get("name"), **tool}
        for category, tool in iter_tools(catalog)
        if matches(tool, category, args.query, args.tag, args.recommended)
    ]

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        print()
    else:
        if not results:
            print("No tools matched.")
            return 1
        for category, tool in (
            (c, t)
            for c, t in iter_tools(catalog)
            if matches(t, c, args.query, args.tag, args.recommended)
        ):
            print(format_tool(category, tool))
            print()
        print(f"{len(results)} tool(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
