#!/usr/bin/env python3
"""Command-line interface for gitignore-audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gitignore_audit import audit, has_issues


def _print_human(report: dict) -> None:
    print(f"gitignore audit: {report['root']}")
    print(
        "patterns: "
        f"{report['pattern_count']}; "
        f"candidates: {report['candidate_count']}; "
        f"tracked: {report['tracked_count']}"
    )

    sections = [
        ("Stale patterns", "stale"),
        ("Duplicate patterns", "duplicate"),
        ("Broad patterns", "broad"),
        ("Ineffective patterns", "ineffective"),
    ]
    found = False
    for title, key in sections:
        items = report[key]
        if not items:
            continue
        found = True
        print(f"\n{title} ({len(items)}):")
        for item in items:
            if key == "ineffective":
                matches = ", ".join(item["tracked_matches"])
                print(f"  {item['pattern']} (line {item['line']}): {matches}")
            else:
                print(f"  {item['pattern']} (line {item['line']})")
    if not found:
        print("\nNo issues found.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit .gitignore rules against repository files."
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument("--gitignore", help="path to an alternate ignore file")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)

    try:
        report = audit(args.root, args.gitignore)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)
    return 1 if has_issues(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
