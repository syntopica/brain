"""Keep instance identifiers out of the reusable engine."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Every tracked file is scanned. An explicit path list was tried first and
# failed the way path lists do: it named the pre-split monorepo layout
# (`tools/clips/src`, `tools/capture`, `tools/sessions`, ...), seven of whose
# eleven entries stopped existing when the engine was split out. `git ls-files`
# reports nothing for a path that is gone, so the guard kept passing while
# covering four directories and none of `bin/`, `docs/`, `schema/`, the root
# documents, or `tools/office`, which arrived later. A list that silently stops
# matching is worse than no list, because it reads as a green check.
ALLOWED = frozenset(
    {
        # The copyright holder is the author, which is what a LICENSE is for.
        "LICENSE",
        # Both name the codeality-py dependency, which is published on PyPI
        # under its original scope. A package name is not instance data, and
        # renaming a published distribution is a separate decision. This file
        # deliberately does not spell that name: it is scanned like every
        # other, and exempting the guard from itself would be the one hole
        # nothing else can catch.
        "pyproject.toml",
        "uv.lock",
    }
)


def test_no_personal_identifier_in_engine() -> None:
    patterns = os.environ.get("SYNTOPICA_PERSONAL_DATA_PATTERNS")
    if not patterns:
        pytest.skip("SYNTOPICA_PERSONAL_DATA_PATTERNS is unset")
    # Tracked files only: what the split publishes is the Git tree, and an
    # ignored working copy - a rendered launchd job, a local override - is this
    # machine's, never the engine's.
    listed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    # A deletion staged later in the split leaves its name in the index while
    # the file is already gone, and ripgrep fails rather than skipping it.
    files = [
        name
        for name in listed.stdout.split("\0")
        if name and name not in ALLOWED and (ROOT / name).exists()
    ]
    assert files, "no tracked files to scan: the guard would pass vacuously"
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
