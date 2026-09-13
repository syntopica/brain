"""Inspect raw and effective remote URLs without displaying their contents."""

from __future__ import annotations

from pathlib import Path

from tools.index.invalid_syntopica_config_error import InvalidSyntopicaConfigError
from tools.index.run_syntopica_git import run_syntopica_git
from tools.index.validate_syntopica_urls import validate_syntopica_urls


def validate_syntopica_git_remotes(root: Path) -> None:
    """Check fetch and push URLs, including Git's insteadOf rewrites."""
    raw = run_syntopica_git(
        root,
        (
            "config",
            "--local",
            "--includes",
            "--null",
            "--get-regexp",
            r"^remote\..*\.(url|pushurl)$",
        ),
    )
    if raw.returncode not in {0, 1}:
        raise InvalidSyntopicaConfigError("Cannot inspect configured Git remotes")
    for entry in raw.stdout.split("\0"):
        _key, separator, value = entry.partition("\n")
        if separator:
            validate_syntopica_urls(value)
    remotes = run_syntopica_git(root, ("remote",))
    if remotes.returncode:
        raise InvalidSyntopicaConfigError("Cannot enumerate configured Git remotes")
    for remote in remotes.stdout.splitlines():
        for options in (("--all",), ("--push", "--all")):
            effective = run_syntopica_git(root, ("remote", "get-url", *options, "--", remote))
            if effective.returncode:
                raise InvalidSyntopicaConfigError("Cannot resolve configured Git remote")
            for url in effective.stdout.splitlines():
                validate_syntopica_urls(url)
