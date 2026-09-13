"""Keep instance identifiers out of the reusable engine."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = (
    "tools/clips/src",
    "tools/graph",
    "tools/index",
    "tools/eval",
    "tools/capture",
    "tools/review",
    "tools/sessions",
    "tools/chatgpt",
    "tools/review-pass",
    "tools/projects",
    "tests",
)


def test_no_personal_identifier_in_engine() -> None:
    patterns = os.environ.get("SYNTOPICA_PERSONAL_DATA_PATTERNS")
    if not patterns:
        pytest.skip("SYNTOPICA_PERSONAL_DATA_PATTERNS is unset")
    # Tracked files only: what the split publishes is the Git tree, and an
    # ignored working copy - a rendered launchd job, a local override - is this
    # machine's, never the engine's.
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", *ENGINE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    # A deletion staged later in the split leaves its name in the index while
    # the file is already gone, and ripgrep fails rather than skipping it.
    files = [name for name in listed.stdout.split("\0") if name and (ROOT / name).exists()]
    result = subprocess.run(
        ["rg", "-a", "-l", "-i", "-f", patterns, *files],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1), result.stderr
    matches = sorted(result.stdout.splitlines())
    assert not matches, f"Personal identifiers in {len(matches)} files:\n" + "\n".join(matches)
