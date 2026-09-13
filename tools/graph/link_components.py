"""The connected clusters of the link graph, read undirected."""


def link_components(neighbours: dict[str, set[str]]) -> list[list[str]]:
    """Every component, largest first, members sorted.

    Undirected on purpose: a page reachable only by following a link backwards
    is still reachable by a reader, who sees inbound and outbound alike in the
    viewer. One component means the wiki is one body of knowledge; a second one
    is a set of pages that cannot be reached from the rest by any path, which
    the orphan count cannot show - a cluster of pages linking to each other and
    to nothing else has no orphans in it.
    """
    seen: set[str] = set()
    components: list[list[str]] = []
    for start in sorted(neighbours):
        if start in seen:
            continue
        component: list[str] = []
        stack = [start]
        seen.add(start)
        while stack:
            page = stack.pop()
            component.append(page)
            for other in sorted(neighbours[page]):
                if other not in seen:
                    seen.add(other)
                    stack.append(other)
        components.append(sorted(component))
    components.sort(key=lambda members: (-len(members), members[0]))
    return components
