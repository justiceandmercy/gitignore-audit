"""Audit .gitignore rules against files in a Git repository."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

BROAD_PATTERNS = {"*", "**", "/*", "/**"}


@dataclass(frozen=True)
class Pattern:
    text: str
    line_number: int


def load_patterns(path: Path) -> List[Pattern]:
    """Load non-empty, non-comment lines from a .gitignore file."""
    patterns: List[Pattern] = []
    if not path.is_file():
        return patterns
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(Pattern(text=line, line_number=number))
    return patterns


def collect_candidates(root: Path) -> List[str]:
    """Collect repository file and directory paths, excluding .git."""
    result: List[str] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(directory for directory in dirs if directory != ".git")
        relative_current = Path(current).relative_to(root)
        for name in dirs + files:
            relative = (
                name
                if relative_current == Path(".")
                else (relative_current / name).as_posix()
            )
            result.append(relative)
    return sorted(result)


def _git(root: Path, args: List[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )


def tracked_files(root: Path) -> Set[str]:
    """Return paths tracked by Git."""
    process = _git(root, ["ls-files", "-z"])
    if process.returncode != 0:
        return set()
    return {path for path in process.stdout.split("\0") if path}


def match_patterns(root: Path, candidates: List[str]) -> Dict[str, Set[str]]:
    """Map .gitignore patterns to the repository paths they match."""
    matches: Dict[str, Set[str]] = {}
    if not candidates:
        return matches
    process = _git(
        root,
        ["check-ignore", "--no-index", "-v", "--stdin"],
        stdin="\n".join(candidates) + "\n",
    )
    if process.returncode not in (0, 1):
        raise RuntimeError(process.stderr.strip() or "git check-ignore failed")
    for line in process.stdout.splitlines():
        if "\t" not in line:
            continue
        metadata, path = line.split("\t", 1)
        parts = metadata.rsplit(":", 2)
        if len(parts) != 3:
            continue
        _source, _line_number, pattern = parts
        matches.setdefault(pattern, set()).add(path)
    return matches


def audit(root: Path | str, gitignore: Path | str | None = None) -> dict:
    """Audit a repository and return a JSON-serializable report."""
    root_path = Path(root).resolve()
    gitignore_path = (
        Path(gitignore).resolve() if gitignore is not None else root_path / ".gitignore"
    )
    patterns = load_patterns(gitignore_path)
    candidates = collect_candidates(root_path)
    raw_matches = match_patterns(root_path, candidates)
    tracked = tracked_files(root_path)

    match_map: Dict[str, Set[str]] = {pattern.text: set() for pattern in patterns}
    for pattern_text, paths in raw_matches.items():
        if pattern_text in match_map:
            match_map[pattern_text].update(paths)

    stale = [
        {"pattern": pattern.text, "line": pattern.line_number}
        for pattern in patterns
        if not match_map.get(pattern.text)
    ]

    seen: Set[str] = set()
    duplicates: List[dict] = []
    for pattern in patterns:
        if pattern.text in seen:
            continue
        occurrences = [item for item in patterns if item.text == pattern.text]
        if len(occurrences) > 1:
            duplicates.append({"pattern": pattern.text, "line": occurrences[0].line_number})
        seen.add(pattern.text)

    broad = [
        {"pattern": pattern.text, "line": pattern.line_number}
        for pattern in patterns
        if pattern.text in BROAD_PATTERNS
    ]

    ineffective = []
    for pattern in patterns:
        if pattern.text.startswith("!"):
            continue
        tracked_matches = sorted(match_map.get(pattern.text, set()) & tracked)
        if tracked_matches:
            ineffective.append(
                {
                    "pattern": pattern.text,
                    "line": pattern.line_number,
                    "tracked_matches": tracked_matches[:10],
                }
            )

    return {
        "root": str(root_path),
        "gitignore": str(gitignore_path),
        "pattern_count": len(patterns),
        "candidate_count": len(candidates),
        "tracked_count": len(tracked),
        "patterns": [
            {
                "text": pattern.text,
                "line": pattern.line_number,
                "matched_count": len(match_map.get(pattern.text, ())),
            }
            for pattern in patterns
        ],
        "stale": stale,
        "duplicate": duplicates,
        "broad": broad,
        "ineffective": ineffective,
    }


def has_issues(report: dict) -> bool:
    return bool(report["stale"] or report["duplicate"] or report["broad"] or report["ineffective"])
