"""Run every available configuration check once, for any presentation."""

from collections.abc import Mapping
from pathlib import Path

from tools.index.doctor_api import doctor_api
from tools.index.doctor_archive import doctor_archive
from tools.index.doctor_credentials import doctor_credentials
from tools.index.doctor_executables import doctor_executables
from tools.index.doctor_paths import doctor_paths
from tools.index.doctor_repositories import doctor_repositories
from tools.index.doctor_retrieval import doctor_retrieval
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.load_syntopica_config import load_syntopica_config


def doctor_checks(root: Path, environ: Mapping[str, str]) -> tuple[tuple[bool, str, str], ...]:
    """Each check as `(passed, credential-free message, fixed code)`.

    The check's name is the message up to its first colon. A configuration that
    cannot load ends the run with that one failing check, because every other
    check reads the configuration.
    """
    try:
        config = load_syntopica_config(root, environ)
    except InvalidSyntopicaConfigError as error:
        return ((False, f"configuration: {error}", "config_invalid"),)
    except (OSError, ValueError):
        return (
            (
                False,
                "configuration: invalid paths, repository identities, remotes or settings",
                "config_invalid",
            ),
        )
    checks: tuple[tuple[bool, str, str], ...] = (
        (True, "configuration: valid", "ok"),
        doctor_paths(config),
        doctor_repositories(root, config),
        doctor_retrieval(config),
        doctor_api(config),
        doctor_executables(config, environ),
        doctor_credentials(config, environ),
    )
    if config.archive is not None:
        checks += (doctor_archive(config.archive),)
    return checks
