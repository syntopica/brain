"""Read one frontmatter scalar, however Prettier decided to wrap it."""


def folded_value(block: str, key: str) -> str:
    """The value of ``key``, joined back up if it spans several lines.

    Prettier reflows frontmatter at 80 columns, so a value long enough to be
    worth writing is stored folded - either continuing after the key or, when
    the first word would already overflow, entirely on the lines below it. Read
    as one line, a summary came back cut mid-sentence with its opening quote
    still attached, and a title came back empty, which lint then reported as a
    missing title on three pages that have one.

    A line indented under a key can only be that key's continuation in YAML, so
    every indented line up to the next column-0 key belongs to the value.
    """
    lines = block.split("\n")
    for index, line in enumerate(lines):
        if not line.startswith(f"{key}:"):
            continue
        parts = [line[len(key) + 1 :].strip()]
        for following in lines[index + 1 :]:
            if not following[:1].isspace():
                break
            parts.append(following.strip())
        return " ".join(part for part in parts if part)
    return ""
