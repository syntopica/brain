"""Create isolated, generic data and engine repositories for public tests."""

import json
from collections.abc import Mapping
from pathlib import Path

from tests.brain_engine_path import brain_engine_path
from tests.rendered_fixture_index import rendered_fixture_index
from tests.syntopica_git import syntopica_git


def make_data_directory(
    root: Path,
    pages: Mapping[str, str] | None = None,
    engines: tuple[str, ...] = ("brain", "clips"),
) -> Path:
    """Build a synthetic instance under root without inheriting Git templates."""
    root = root.resolve()
    data = root / "data"
    content = (
        pages
        if pages is not None
        else {
            "notes/example.md": "---\ntitle: Example\nsummary: A generic note.\n---\n\nGeneric content.\n"
        }
    )
    # `engines.brain.path` always reads `../engine-brain`, so the document names
    # no absolute path and no home directory. Where a checkout providing the
    # configuration reader exists, that name is a symlink to it and the adapters
    # resolve for real; where none does, it is an empty repository carrying only
    # the schema, which is all a path-shape test needs.
    engine = brain_engine_path(Path(__file__).resolve().parents[2])
    repositories = [data] + [root / "engine-clips"] * ("clips" in engines)
    if engine is None:
        repositories.append(root / "engine-brain")
    for repository in repositories:
        repository.mkdir(parents=True, exist_ok=True)
        syntopica_git(repository, "init", "--quiet", "--template=", "--initial-branch=main")
    for directory in (
        "brain",
        "brain/captures",
        "brain/.ingest",
        "atrium",
        "conversations",
        "clips",
    ):
        (data / directory).mkdir(parents=True, exist_ok=True)
    if engine is None:
        (root / "engine-brain/schema").mkdir(parents=True, exist_ok=True)
        (root / "engine-brain/schema/syntopica-config.schema.json").write_bytes(
            (
                Path(__file__).resolve().parents[2] / "schema/syntopica-config.schema.json"
            ).read_bytes()
        )
    elif not (root / "engine-brain").exists():
        (root / "engine-brain").symlink_to(engine, target_is_directory=True)
    (data / ".config").mkdir(exist_ok=True)
    for filename in (
        "newsletter-accepted.json",
        "newsletter-rejected.json",
        "newsletter-rejected-booking.json",
        "project-aliases.json",
    ):
        (data / ".config" / filename).write_text(
            "{}\n" if filename == "project-aliases.json" else "[]\n", encoding="utf-8"
        )
    directories: set[str] = set()
    for name, text in content.items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or len(relative.parts) < 2
            or relative.suffix != ".md"
        ):
            raise ValueError(
                "Fixture pages must be relative Markdown paths inside a page directory"
            )
        destination = data / "brain" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        directories.add(relative.parent.as_posix())
    document = {
        "schemaVersion": 1,
        "instanceId": "fixture",
        "brain": {
            "pages": [f"brain/{directory}" for directory in sorted(directories)],
            "sources": "brain/captures",
            "index": "brain/index.md",
            "ledger": "brain/.ingest",
        },
        "clips": {"archive": "clips"},
        "atrium": {"path": "atrium"},
        "conversations": {"path": "conversations"},
        "engines": {name: {"path": f"../engine-{name}", "apiVersion": 1} for name in engines},
    }
    (data / "syntopica.config.json").write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )
    (data / "brain/index.md").write_text(
        rendered_fixture_index(data / "brain", sorted(directories)), encoding="utf-8"
    )
    return data
