"""Raw summary: extracted from build.py."""


def raw_summary(block: str) -> str:
    """The `summary:` value, joined back up if it spans several lines.

    Prettier reflows frontmatter at 80 columns, so a summary long enough to be
    worth writing is stored folded - either continuing after the key or, when
    the first word would already overflow, entirely on the lines below it. Read
    as one line, the value came back cut mid-sentence with its opening quote
    still attached, which is what `index.md` listed for `capture-service`,
    `env-inventory` and eight others.

    A line indented under a key can only be that key's continuation in YAML, so
    every indented line up to the next column-0 key belongs to the summary.
    """
    lines = block.split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("summary:"):
            continue
        parts = [line[len("summary:") :].strip()]
        for following in lines[i + 1 :]:
            if not following[:1].isspace():
                break
            parts.append(following.strip())
        return " ".join(part for part in parts if part)
    return ""
