from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from gitignore_audit import audit


def _git_available() -> bool:
    return shutil.which("git") is not None


pytestmark = pytest.mark.skipif(not _git_available(), reason="git is required")


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def test_stale_pattern(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / ".gitignore").write_text("*.tmp\n*.pyc\n", encoding="utf-8")
    (repo / "a.pyc").write_text("", encoding="utf-8")

    report = audit(repo)

    assert [item["pattern"] for item in report["stale"]] == ["*.tmp"]
    assert report["ineffective"] == []


def test_ineffective_tracked_pattern(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (repo / "tracked.log").write_text("", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(repo), "add", "tracked.log"], check=True
    )

    report = audit(repo)

    assert report["ineffective"][0]["pattern"] == "*.log"
    assert report["ineffective"][0]["tracked_matches"] == ["tracked.log"]


def test_duplicate_and_broad_patterns(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / ".gitignore").write_text("*\n*\n", encoding="utf-8")

    report = audit(repo)

    assert report["duplicate"][0]["pattern"] == "*"
    assert report["broad"][0]["pattern"] == "*"


def test_cli_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = _make_repo(tmp_path)
    (repo / ".gitignore").write_text("*.tmp\n", encoding="utf-8")

    from cli import main

    exit_code = main([str(repo), "--json"])
    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert exit_code == 1
    assert report["stale"][0]["pattern"] == "*.tmp"
