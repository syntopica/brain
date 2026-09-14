"""Load the chosen instance configuration and enforce its safety boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import cast

from tools.index.classify_syntopica_paths import classify_syntopica_paths
from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.merge_config_overrides import merge_config_overrides
from tools.index.merge_syntopica_documents import merge_syntopica_documents
from tools.index.read_syntopica_document import read_syntopica_document
from tools.index.resolve_syntopica_browser import resolve_syntopica_browser
from tools.index.resolve_syntopica_paths import resolve_syntopica_paths
from tools.index.syntopica_config import SyntopicaConfig
from tools.index.syntopica_config_schema import SYNTOPICA_CONFIG_SCHEMA
from tools.index.syntopica_schema_defaults import syntopica_schema_defaults
from tools.index.syntopica_value_origins import syntopica_value_origins
from tools.index.validate_syntopica_git_roots import validate_syntopica_git_roots
from tools.index.validate_syntopica_schema import validate_syntopica_schema
from tools.index.validate_syntopica_urls import validate_syntopica_urls


def load_syntopica_config(root: Path, environ: Mapping[str, str]) -> SyntopicaConfig:
    """Merge defaults, tracked, local and environment settings for this root."""
    try:
        root = root.resolve()
        tracked = (root / "syntopica.config.json").resolve()
        local = root / "syntopica.local.json"
        document = syntopica_schema_defaults(SYNTOPICA_CONFIG_SCHEMA)
        origins = syntopica_value_origins(document, tracked.parent)
        for path in (tracked, local):
            if path == local and not path.exists() and not path.is_symlink():
                continue
            overlay = read_syntopica_document(path)
            document = merge_syntopica_documents(document, overlay)
            origins.update(syntopica_value_origins(overlay, path.resolve().parent))
    except (OSError, RuntimeError, ValueError):
        raise InvalidSyntopicaConfigError("Cannot resolve configuration files") from None
    validate_syntopica_schema(document)
    document = merge_config_overrides(document, environ)
    validate_syntopica_schema(document)
    validate_syntopica_urls(document)
    paths = resolve_syntopica_paths(document, origins, root)
    path_kinds = classify_syntopica_paths(paths)
    archive = paths[("clips", "archive")][0]
    brain_path = paths[("engines", "brain", "path")][0]
    clips_path = paths[("engines", "clips", "path")][0]
    validate_syntopica_git_roots((root, archive, brain_path, clips_path))
    capture = cast(Mapping[str, object], document["capture"])
    browser = cast(Mapping[str, object], document["browser"])
    browser_origin = (
        root if "CLIPS_HEADLESS_BROWSER" in environ else origins[("browser", "executable")]
    )
    engines = cast(Mapping[str, Mapping[str, object]], document["engines"])
    return SyntopicaConfig(
        data_root=root,
        brain_api_version=cast(int, engines["brain"]["apiVersion"]),
        clips_api_version=cast(int, engines["clips"]["apiVersion"]),
        configured_paths=path_kinds["required"],
        state_paths=path_kinds["state"],
        schema_version=int(cast(int, document["schemaVersion"])),
        instance_id=cast(str, document["instanceId"]),
        pages=paths[("brain", "pages")],
        sources=paths[("brain", "sources")][0],
        index=paths[("brain", "index")][0],
        ledger=paths[("brain", "ledger")][0],
        archive=archive,
        legacy_archive=next(iter(paths[("clips", "legacyArchive")]), None),
        repository_url=cast(
            str | None, cast(Mapping[str, object], document["clips"])["repositoryUrl"]
        ),
        screening_scope=cast(str, capture["screeningScope"]),
        desktop_roots=paths[("sessions", "desktopRoots")],
        brain_path=brain_path,
        clips_path=clips_path,
        capture_origin=cast(str | None, capture["origin"]),
        capture_mirror=cast(bool, capture["mirror"]),
        runners=MappingProxyType(dict(cast(Mapping[str, str | None], document["runners"]))),
        browser=resolve_syntopica_browser(cast(str | None, browser["executable"]), browser_origin),
    )
