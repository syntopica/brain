"""Importing a tool must not run it.

A script that acts at module scope cannot be imported, tested, or read by a
linter's fixer without side effects: it reads argv that a test does not have,
writes files, or exits. Every tool here is therefore expected to keep its work
behind `main()` and a `__main__` guard.

Tools are imported with their own directory on `sys.path`, because that is
what running `python3 tools/graph/build.py` gives them, and several import a
sibling by bare name on purpose.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from tests.tool_paths import tool_paths

# Needs the mempalace package, which is a separate project this repository
# only drives; there is nothing to install here.
NEEDS_MEMPALACE = "tools/mempalace/"
# Puts ~/p/pyfirma on sys.path and imports its signer: a separate checkout,
# not a package, so a machine without it cannot import this tool at all.
NEEDS_PYFIRMA_CHECKOUT = "tools/pyfirma/"
# A missing third-party module means an extra is not installed on this machine,
# which is a skip; a missing module of our own is a broken sibling import.
TOOL_MODULE_NAMES = frozenset(path.stem for path in tool_paths())


def _import(path: Path) -> None:
    name = "brain_tool_" + path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    original_path, original_argv = sys.path[:], sys.argv[:]
    sys.path.insert(0, str(path.parent))
    sys.argv = [str(path)]
    # Registered under its name while it executes, as a real import would be:
    # on 3.12 and 3.13 a dataclass with postponed annotations resolves them
    # through sys.modules[cls.__module__] and dies on the missing entry.
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
        sys.path[:] = original_path
        sys.argv[:] = original_argv


@pytest.mark.parametrize("path", tool_paths(), ids=str)
def test_importing_a_tool_runs_nothing(path: Path) -> None:
    if NEEDS_MEMPALACE in path.as_posix():
        pytest.importorskip("mempalace")
    if NEEDS_PYFIRMA_CHECKOUT in path.as_posix():
        pytest.importorskip("signer")
    try:
        _import(path)
    except ModuleNotFoundError as error:
        if error.name in TOOL_MODULE_NAMES:
            pytest.fail(f"{path} imports {error.name!r}, a tool module it cannot find")
        pytest.skip(f"{path} requires unavailable module {error.name!r}")
    except SystemExit as error:
        pytest.fail(f"{path} exited on import with {error.code!r}")
