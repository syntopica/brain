"""Check required runtimes and explicitly enabled integrations."""

import os
import shutil
from collections.abc import Mapping

from tools.index.required_executables import required_executables
from tools.index.syntopica_config import SyntopicaConfig


def doctor_executables(config: SyntopicaConfig, environ: Mapping[str, str]) -> tuple[bool, str]:
    """Resolve commands on the supplied PATH without executing integrations.

    A count alone sends the reader looking through the source for the names;
    the names are what makes the failure repairable.
    """
    missing = [
        command
        for command in required_executables(config)
        if shutil.which(command, path=environ.get("PATH", os.defpath)) is None
    ]
    if missing:
        return False, f"executables: {len(missing)} missing ({', '.join(missing)})"
    return True, "executables: all present"
