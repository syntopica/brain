"""Operational Git deadlines without command or repository details."""

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError


class GitInspectionTimeoutError(InvalidSyntopicaConfigError):
    """Git inspection exceeded its deadline; configuration remains unverified."""
