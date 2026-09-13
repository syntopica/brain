"""Refuse public engine remotes on the private capture archive."""

from pathlib import Path

from tools.index.doctor_public_remote import doctor_public_remote
from tools.index.run_syntopica_git import run_syntopica_git


def doctor_archive(archive: Path) -> tuple[bool, str]:
    """Inspect every raw and rewritten fetch/push URL without displaying it."""
    raw = run_syntopica_git(
        archive, ("config", "--includes", "--null", "--get-regexp", r"^remote\..*\.(url|pushurl)$")
    )
    remotes = run_syntopica_git(archive, ("remote",))
    if raw.returncode not in {0, 1} or remotes.returncode:
        return False, "archive: cannot inspect remotes"
    urls = [entry.partition("\n")[2] for entry in raw.stdout.split("\0") if "\n" in entry]
    for remote in remotes.stdout.splitlines():
        for options in (("--all",), ("--push", "--all")):
            result = run_syntopica_git(archive, ("remote", "get-url", *options, "--", remote))
            if result.returncode:
                return False, "archive: cannot resolve remotes"
            urls.extend(result.stdout.splitlines())
    if any(doctor_public_remote(url) for url in urls):
        return False, "archive: public engine remote refused"
    return True, "archive: no public engine remote"
