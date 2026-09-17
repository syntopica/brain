"""Decide which commands an instance's configured components actually need."""

from tools.index.syntopica_config import SyntopicaConfig

# "fallback" chains two transports and ends on agy, so agy is what it always
# needs; "manual" and "off" need no command at all and are absent on purpose.
ADAPTERS = {
    "codex": "codex",
    "agy-fine": "agy",
    "agy-bulk": "agy",
    "cursor": "cursor-agent",
    "fallback": "agy",
}


def required_executables(config: SyntopicaConfig) -> tuple[str, ...]:
    """Name every command this instance needs, in a stable reporting order.

    Node and pnpm belong to the TypeScript engines, not to the wiki: index,
    graph and lint run without them, so a brain-only instance that does not
    have them is healthy rather than broken.
    """
    commands = {"git", "uv"}
    if config.clips_path is not None or config.atrium_path is not None:
        commands.update(("node", "pnpm"))
    commands.update(ADAPTERS[runner] for runner in config.runners.values() if runner in ADAPTERS)
    if config.browser is not None:
        commands.add(config.browser)
    return tuple(sorted(commands))
