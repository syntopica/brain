"""Check the engine protocol versions supported by this installation."""

from tools.index.syntopica_config import SyntopicaConfig


def doctor_api(config: SyntopicaConfig) -> tuple[bool, str]:
    """Both engines currently implement protocol version one."""
    supported = config.brain_api_version == config.clips_api_version == 1
    return supported, "api: supported" if supported else "api: unsupported engine version"
