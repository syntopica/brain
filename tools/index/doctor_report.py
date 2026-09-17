"""Report configuration health with only credential-free status messages."""

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


def doctor_report(root: Path, environ: Mapping[str, str]) -> int:
    """Print one line per available check and return a shell-compatible status."""
    try:
        config = load_syntopica_config(root, environ)
    except InvalidSyntopicaConfigError as error:
        print(f"FAIL configuration: {error}")
        return 1
    except (OSError, ValueError):
        print("FAIL configuration: invalid paths, repository identities, remotes or settings")
        return 1
    checks: tuple[tuple[bool, str], ...] = (
        (True, "configuration: valid"),
        doctor_paths(config),
        doctor_repositories(root, config),
        doctor_retrieval(config),
        doctor_api(config),
        doctor_executables(config, environ),
        doctor_credentials(config, environ),
    )
    if config.archive is not None:
        checks += (doctor_archive(config.archive),)
    for passed, message in checks:
        print(f"{'PASS' if passed else 'FAIL'} {message}")
    return int(any(not passed for passed, _ in checks))
