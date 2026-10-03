"""Read `--json [--skip NAME]...` for `brain doctor`."""

from tools.index.doctor_check_names import DOCTOR_CHECK_NAMES


def doctor_skip_arguments(arguments: list[str]) -> frozenset[str]:
    """The checks to skip; only valid after `--json`, each a known check name.

    A caller whose environment is deliberately narrower than an operator's, such
    as a health poller that receives no credentials, skips the checks that read
    that environment instead of reporting them failed forever.
    """
    if arguments[:1] != ["--json"]:
        raise ValueError("doctor accepts --skip only after --json")
    rest = arguments[1:]
    if len(rest) % 2 or any(flag != "--skip" for flag in rest[::2]):
        raise ValueError("doctor accepts only --json [--skip NAME]...")
    names = frozenset(rest[1::2])
    if not names <= DOCTOR_CHECK_NAMES:
        raise ValueError("doctor --skip names an unknown check")
    return names
