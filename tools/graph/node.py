"""The shape of a graph node as the viewer receives it.

A page reduced to what the viewer draws: identity, the labels it filters on,
and the two degrees it sizes by. `in` and `out` count distinct linked pages,
never link occurrences, so a page named three times in one body is one edge.
`in` is a Python keyword, which is why this is the functional TypedDict syntax
and not a class.
"""

from typing import TypedDict

Node = TypedDict(
    "Node",
    {
        "id": str,
        "title": str,
        "type": str,
        "dir": str,
        "updated": str,
        "in": int,
        "out": int,
    },
)
