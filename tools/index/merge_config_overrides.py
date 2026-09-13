"""Apply the seven non-credential environment overrides."""

from __future__ import annotations

from collections.abc import Mapping

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.merge_syntopica_documents import merge_syntopica_documents


def merge_config_overrides(
    document: Mapping[str, object], environ: Mapping[str, str]
) -> dict[str, object]:
    """Overlay only named settings, never reading CAPTURE_TOKEN."""
    result = dict(document)
    overrides = {
        "CAPTURE_MIRROR": ("capture", "mirror"),
        "CAPTURE_SERVICE_ORIGIN": ("capture", "origin"),
        "CLIPS_GRADE_RUNNER": ("runners", "grade"),
        "CLIPS_SYNTHESIS_RUNNER": ("runners", "synthesis"),
        "CLIPS_TRIAGE_RUNNER": ("runners", "triage"),
        "CLIPS_TRIAGE_REFINER": ("runners", "triageRefiner"),
        "CLIPS_HEADLESS_BROWSER": ("browser", "executable"),
    }
    for variable, (section, key) in overrides.items():
        value = environ.get(variable)
        if value is None:
            continue
        if variable == "CAPTURE_MIRROR" and value not in {"on", "off"}:
            raise InvalidSyntopicaConfigError("CAPTURE_MIRROR must be on or off")
        effective: str | bool = value == "on" if variable == "CAPTURE_MIRROR" else value
        result = merge_syntopica_documents(result, {section: {key: effective}})
    return result
