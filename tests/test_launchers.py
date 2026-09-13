"""Public launchers resolve code independently from the selected data directory."""

import os
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tests.tool_paths import ROOT

# Which launchers exist is per repository: the engines are separate
# repositories and each ships its own. Discovered rather than listed, so this
# file is the same in all of them and names only what is actually there.
LAUNCHERS = [
    name for name in ("bin/brain", "tools/clips/bin/clips", "bin/clips") if (ROOT / name).is_file()
]
BRAIN_ONLY = pytest.mark.skipif("bin/brain" not in LAUNCHERS, reason="no brain launcher here")
CLIPS_LAUNCHER = next((name for name in LAUNCHERS if name.endswith("bin/clips")), None)
CLIPS_PACKAGE = ROOT / "tools/clips" if (ROOT / "tools/clips/package.json").is_file() else ROOT
CLIPS_ONLY = pytest.mark.skipif(CLIPS_LAUNCHER is None, reason="no clips package here")


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_launcher_doctor_from_tmp_with_explicit_data(tmp_path: Path, launcher: str) -> None:
    data = make_data_directory(tmp_path)
    result = subprocess.run(
        [str(ROOT / launcher), "--data", str(data), "doctor"],
        cwd="/tmp",
        env={
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "SYNTOPICA_DATA",
                "CAPTURE_MIRROR",
                "CAPTURE_SERVICE_ORIGIN",
                "CLIPS_GRADE_RUNNER",
                "CLIPS_SYNTHESIS_RUNNER",
                "CLIPS_TRIAGE_RUNNER",
                "CLIPS_TRIAGE_REFINER",
                "CLIPS_HEADLESS_BROWSER",
            }
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_launcher_from_tmp_requires_data_configuration(launcher: str) -> None:
    result = subprocess.run(
        [str(ROOT / launcher), "doctor"],
        cwd="/tmp",
        env={key: value for key, value in os.environ.items() if key != "SYNTOPICA_DATA"},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode != 0
    assert "syntopica.config.json" in result.stdout + result.stderr


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_symlink_launcher_discovers_from_callers_directory(tmp_path: Path, launcher: str) -> None:
    data = make_data_directory(tmp_path)
    link = tmp_path / "launcher"
    link.symlink_to(ROOT / launcher)
    caller = data / "nested" / "deeper"
    caller.mkdir(parents=True)
    result = subprocess.run(
        [str(link), "doctor"],
        cwd=caller,
        env={
            key: value
            for key, value in os.environ.items()
            if key
            not in {
                "SYNTOPICA_DATA",
                "CAPTURE_MIRROR",
                "CAPTURE_SERVICE_ORIGIN",
                "CLIPS_GRADE_RUNNER",
                "CLIPS_SYNTHESIS_RUNNER",
                "CLIPS_TRIAGE_RUNNER",
                "CLIPS_TRIAGE_REFINER",
                "CLIPS_HEADLESS_BROWSER",
            }
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@BRAIN_ONLY
@pytest.mark.parametrize("command", ["index", "graph", "lint"])
def test_brain_subcommands_target_selected_fixture(tmp_path: Path, command: str) -> None:
    data = make_data_directory(tmp_path)
    result = subprocess.run(
        [str(ROOT / "bin/brain"), "--data", str(data), command],
        cwd="/tmp",
        env={
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("CAPTURE_", "CLIPS_"))
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    if command == "graph":
        assert (data / "brain/graph.html").is_file()
    else:
        assert not (data / "brain/graph.html").exists()


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_invalid_explicit_selection_never_falls_back(tmp_path: Path, launcher: str) -> None:
    data = make_data_directory(tmp_path)
    result = subprocess.run(
        [str(ROOT / launcher), "--data", str(tmp_path), "doctor"],
        cwd=data,
        env={**os.environ, "SYNTOPICA_DATA": str(data)},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode != 0
    assert "syntopica.config.json" in result.stdout + result.stderr


@CLIPS_ONLY
@pytest.mark.parametrize("invocation", ["launcher", "node", "pnpm"])
def test_clips_status_preserves_existing_invocation_styles(tmp_path: Path, invocation: str) -> None:
    data = make_data_directory(tmp_path)
    command = {
        "launcher": [str(CLIPS_PACKAGE / "bin/clips")],
        "node": ["node", str(CLIPS_PACKAGE / "src/main.ts")],
        "pnpm": ["pnpm", "--dir", str(CLIPS_PACKAGE), "clips"],
    }[invocation]
    result = subprocess.run(
        [*command, "--data", str(data), "status"],
        cwd="/tmp",
        env={
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("CAPTURE_", "CLIPS_"))
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 clips" in result.stdout
