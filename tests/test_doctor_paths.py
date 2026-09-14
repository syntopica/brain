"""Missing machine state is normal; missing instance content is not."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tools.index.doctor_report import doctor_report


@pytest.mark.parametrize("memory_path", ["mem", "state/agent-memory"])
def test_missing_state_is_named_without_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], memory_path: str
) -> None:
    root = make_data_directory(tmp_path)
    (root / "mem").rmdir()
    (root / "syntopica.local.json").write_text(
        json.dumps({"mem": {"path": memory_path}}), encoding="utf-8"
    )
    with patch("tools.index.doctor_executables.shutil.which", return_value="/synthetic/bin/tool"):
        assert doctor_report(root, {}) == 0
    assert f"PASS paths: required paths present; state not created yet ({memory_path})" in (
        capsys.readouterr().out
    )
    assert not (root / memory_path).exists()


@pytest.mark.parametrize("missing_state", [False, True])
def test_missing_pages_still_fail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], missing_state: bool
) -> None:
    root = make_data_directory(tmp_path)
    (root / "syntopica.local.json").write_text(
        json.dumps({"brain": {"pages": ["brain/absent"]}}), encoding="utf-8"
    )
    if missing_state:
        (root / "mem").rmdir()
    with patch("tools.index.doctor_executables.shutil.which", return_value="/synthetic/bin/tool"):
        assert doctor_report(root, {}) == 1
    output = capsys.readouterr().out
    assert "FAIL paths: 1 missing (brain/absent)" in output
    if missing_state:
        assert "; state not created yet (mem)" in output


def test_state_path_does_not_exempt_a_required_path_at_the_same_location(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = make_data_directory(tmp_path)
    (root / "syntopica.local.json").write_text(
        json.dumps({"brain": {"pages": ["shared"]}, "mem": {"path": "shared"}}),
        encoding="utf-8",
    )
    with patch("tools.index.doctor_executables.shutil.which", return_value="/synthetic/bin/tool"):
        assert doctor_report(root, {}) == 1
    assert "FAIL paths: 1 missing (shared)" in capsys.readouterr().out
