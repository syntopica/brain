"""Check capture credential presence without retaining its value."""

from collections.abc import Mapping

from tools.index.syntopica_config import SyntopicaConfig


def doctor_credentials(
    config: SyntopicaConfig, environ: Mapping[str, str]
) -> tuple[bool, str, str]:
    """Disabled capture needs no credential; enabled capture requires a token."""
    if config.capture_origin is None and not config.capture_mirror:
        return True, "credentials: CAPTURE_TOKEN not required", "not_required"
    present = bool(environ.get("CAPTURE_TOKEN", "").strip())
    if present:
        return True, "credentials: CAPTURE_TOKEN present", "ok"
    return False, "credentials: CAPTURE_TOKEN absent", "token_absent"
