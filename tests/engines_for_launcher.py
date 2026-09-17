"""Which engines a launcher's own doctor should be tested against."""


def engines_for_launcher(launcher: str) -> tuple[str, ...]:
    """A brain launcher gets a brain-only instance; anything else keeps clips.

    Discovery is what these tests measure, and an instance declaring the clips
    engine requires node and pnpm - a toolchain a Python engine's test run has
    no reason to carry, and one the CI runner does not have.
    """
    return ("brain",) if "brain" in launcher else ("brain", "clips")
