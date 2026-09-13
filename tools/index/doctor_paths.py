"""Check the resolved instance paths, naming the ones that are absent."""

from tools.index.named_path import named_path
from tools.index.syntopica_config import SyntopicaConfig


def doctor_paths(config: SyntopicaConfig) -> tuple[bool, str]:
    """Require every schema-configured path to exist, and say which do not.

    A count alone sends the reader back to the source to find out what is
    wrong, so the names are part of the report. They are paths from the
    instance the caller already selected, not secrets.
    """
    missing = [path for path in config.configured_paths if not path.exists()]
    if not missing:
        return True, "paths: all present"
    names = ", ".join(named_path(path, config.data_root) for path in missing)
    return False, f"paths: {len(missing)} missing ({names})"
