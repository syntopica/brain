"""Say which retrieval this instance actually has, so silence is not mistaken for coverage."""

from pathlib import Path

from tools.index.syntopica_config import SyntopicaConfig


def doctor_retrieval(config: SyntopicaConfig) -> tuple[bool, str]:
    """Report keyword-only or keyword-and-semantic, and never fail on either.

    A wiki with no semantic lane is a supported instance, not a broken one: this
    engine holds no embeddings by design, and `brain find` answers over the
    pages' own words. What is not supported is a session assuming a paraphrase
    would have been found. Semantic retrieval over these pages comes from the
    atrium engine, which indexes them beside the conversation archive, so the
    honest line is which of the two is installed.
    """
    path = config.atrium_path
    if path is None:
        return True, (
            "retrieval: keyword only (`brain find`); add the atrium engine for semantic search"
        )
    if not Path(path).is_dir():
        return True, (
            f"retrieval: keyword only (`brain find`); atrium is configured at {path} "
            "but the checkout is absent"
        )
    return True, "retrieval: keyword (`brain find`) and semantic (atrium)"
