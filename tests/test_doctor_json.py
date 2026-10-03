"""`brain doctor --json` reports each check by name, outcome and fixed code."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.fixtures.make_data_directory import make_data_directory
from tools.index.brain_cli import brain_cli
from tools.index.doctor_document import doctor_document

WHICH = "tools.index.doctor_executables.shutil.which"


def test_healthy_instance_document(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = make_data_directory(tmp_path)
    with patch(WHICH, return_value="/synthetic/bin/tool"):
        assert brain_cli(["--data", str(data), "doctor", "--json"]) == 0
    document = json.loads(capsys.readouterr().out)
    assert document["schemaVersion"] == 1
    assert document["ok"] is True
    assert [check["name"] for check in document["checks"]] == [
        "configuration",
        "paths",
        "repositories",
        "retrieval",
        "api",
        "executables",
        "credentials",
        "archive",
    ]
    assert all(set(check) == {"name", "ok", "code"} for check in document["checks"])
    assert str(tmp_path) not in json.dumps(document)


def test_failures_carry_codes_without_names(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    (data / "brain/captures").rmdir()
    with patch(WHICH, return_value=None):
        document = doctor_document(data, {"PATH": "/synthetic/empty"})
    codes = {check["name"]: check["code"] for check in document["checks"]}
    assert document["ok"] is False
    assert codes["paths"] == "paths_missing"
    assert codes["executables"] == "executables_missing"
    assert "captures" not in json.dumps(document)


def test_invalid_configuration_is_one_failing_check(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    (data / "syntopica.config.json").write_text('{"schemaVersion": 1}\n', encoding="utf-8")
    document = doctor_document(data, {})
    assert document["checks"] == [{"name": "configuration", "ok": False, "code": "config_invalid"}]


def test_capture_token_codes(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    origin = {"CAPTURE_SERVICE_ORIGIN": "https://capture.example.test"}
    codes = [
        {c["name"]: c["code"] for c in doctor_document(data, environ)["checks"]}["credentials"]
        for environ in (origin, {**origin, "CAPTURE_TOKEN": "synthetic-token-never-printed"})
    ]
    assert codes == ["token_absent", "ok"]


def test_doctor_rejects_any_other_argument(tmp_path: Path) -> None:
    data = make_data_directory(tmp_path)
    with pytest.raises(SystemExit):
        brain_cli(["--data", str(data), "doctor", "--verbose"])
