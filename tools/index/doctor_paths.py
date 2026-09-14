"""Check the resolved instance paths, naming the ones that are absent."""

from tools.index.named_path import named_path
from tools.index.syntopica_config import SyntopicaConfig


def doctor_paths(config: SyntopicaConfig) -> tuple[bool, str]:
    """Require content paths and report absent state without creating it.

    A count alone sends the reader back to the source to find out what is
    wrong, so the names are part of the report. They are paths from the
    instance the caller already selected, not secrets.
    """
    missing = [path for path in config.configured_paths if not path.exists()]
    absent_state = [path for path in config.state_paths if not path.exists()]
    message = "paths: all present"
    if missing:
        names = ", ".join(named_path(path, config.data_root) for path in missing)
        message = f"paths: {len(missing)} missing ({names})"
    elif absent_state:
        message = "paths: required paths present"
    if absent_state:
        names = ", ".join(named_path(path, config.data_root) for path in absent_state)
        message += f"; state not created yet ({names})"
    return not missing, message
