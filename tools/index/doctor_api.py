"""Check the engine protocol versions supported by this installation."""

from tools.index.syntopica_config import SyntopicaConfig


def doctor_api(config: SyntopicaConfig) -> tuple[bool, str, str]:
    """Every declared engine currently implements protocol version one."""
    versions = (config.brain_api_version, config.clips_api_version)
    supported = all(version in (None, 1) for version in versions)
    if supported:
        return True, "api: supported", "ok"
    return False, "api: unsupported engine version", "api_unsupported"
