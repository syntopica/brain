"""Whether the configured index no longer matches the pages it lists."""

from pathlib import Path

from tools.index.normalized import normalized
from tools.index.rendered import rendered
from tools.index.syntopica_config import SyntopicaConfig


def index_stale(config: SyntopicaConfig, directories: tuple[Path, ...]) -> bool:
    """True when the index is absent or differs from a fresh render."""
    return not config.index.is_file() or normalized(
        config.index.read_text(encoding="utf-8")
    ) != normalized(rendered(config.index.parent, directories, config.inbox))
