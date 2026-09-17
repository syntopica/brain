"""A brain-only instance must not be blocked by the TypeScript engines' tools."""

from pathlib import Path

from tests.fixtures.make_data_directory import make_data_directory
from tools.index.doctor_executables import doctor_executables
from tools.index.load_syntopica_config import load_syntopica_config
from tools.index.required_executables import required_executables


def test_node_and_pnpm_are_required_only_with_a_typescript_engine(tmp_path: Path) -> None:
    config = load_syntopica_config(make_data_directory(tmp_path, engines=("brain",)), {})
    assert config.clips_path is None
    assert set(required_executables(config)).isdisjoint({"node", "pnpm"})


def test_clips_brings_node_and_pnpm_back(tmp_path: Path) -> None:
    config = load_syntopica_config(make_data_directory(tmp_path), {})
    assert {"node", "pnpm"} <= set(required_executables(config))


def test_a_missing_executable_is_named_not_counted(tmp_path: Path) -> None:
    config = load_syntopica_config(make_data_directory(tmp_path), {})
    passed, message = doctor_executables(config, {"PATH": str(tmp_path / "empty")})
    assert not passed
    assert "git" in message and "uv" in message
