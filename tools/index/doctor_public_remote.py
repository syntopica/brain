"""Recognize the public engine repository identities across Git URL forms."""

import re
from urllib.parse import unquote, urlsplit


def doctor_public_remote(value: str) -> bool:
    """Match HTTPS, SSH, scp and git transport URLs without rendering them."""
    normalized = re.sub(r"^([^/@]+@)?github\.com:", "ssh://github.com/", value, flags=re.IGNORECASE)
    parsed = urlsplit(normalized)
    return (parsed.hostname or "").lower() == "github.com" and unquote(parsed.path).strip(
        "/"
    ).lower().removesuffix(".git") in {"syntopica/brain", "syntopica/clips"}
