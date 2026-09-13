"""Every tool under tools/ is valid Python for the interpreter that runs it.

This is the cheapest net there is, and it exists because of a real failure:
a mechanical `ruff --fix` pass in another repository removed an import that
was in use and nothing noticed until a run broke. Parsing catches the whole
class of damage a rewrite can do to a file's syntax, over every tool at once,
without importing anything and so without running anything.
"""

import ast

import pytest

from tests.tool_paths import tool_paths


@pytest.mark.parametrize("path", tool_paths(), ids=str)
def test_a_tool_parses(path) -> None:
    source = path.read_text(encoding="utf-8")
    ast.parse(source, filename=str(path))
