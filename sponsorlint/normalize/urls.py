"""Spoken URL canonicalization. Architecture.md §5.1.

All four of these must resolve to the same campaign URL:

    aegisvpn.com/alex
    aegis vpn dot com slash alex
    aegisvpn dot com slash alex
    www.aegisvpn.com/alex

Matching a URL inside a transcript is done with a pattern built *from the
expected URL*, rather than by canonicalizing the whole transcript — that keeps
the match tight and lets us hand back the original transcript text as evidence.
"""

from __future__ import annotations

import re

from .text import normalize_text

_VERBAL = (
    (re.compile(r"\bforward\s+slash\b"), "/"),
    (re.compile(r"\bslash\b"), "/"),
    (re.compile(r"\bdot\b"), "."),
    (re.compile(r"\b(?:dash|hyphen)\b"), "-"),
    (re.compile(r"\bunderscore\b"), "_"),
)

_AROUND_PUNCT = re.compile(r"\s*([./_-])\s*")

#: `normalize_text` drops the colon, so "https://x" arrives as "https//x".
#: Both forms have to be recognized.
_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:?//")
_SCHEME_PREFIX = r"(?:[a-z][a-z0-9+.-]*:?//)?"

_SEPARATORS = "./_-"


def canonical_url(url: str) -> str:
    """Normalize a single written or spoken URL to one comparable form."""
    u = normalize_text(url)
    for pattern, replacement in _VERBAL:
        u = pattern.sub(replacement, u)
    u = _AROUND_PUNCT.sub(r"\1", u)
    u = u.replace(" ", "")
    u = _SCHEME.sub("", u)
    if u.startswith("www."):
        u = u[4:]
    return u.rstrip("/.")


def looks_like_url(value: str) -> bool:
    canon = canonical_url(value)
    return bool(re.search(r"[a-z0-9]\.[a-z]{2,}", canon))


def _literal_chars(chunk: str) -> str:
    """Allow at most one space between characters, so "aegis vpn" matches
    "aegisvpn" without letting the pattern wander across a whole sentence."""
    return r"[\s-]?".join(re.escape(c) for c in chunk)


def spoken_pattern(url: str) -> re.Pattern[str]:
    """A pattern matching every spoken form of `url` in normalized text."""
    canon = canonical_url(url)
    parts = re.split(rf"([{re.escape(_SEPARATORS)}])", canon)

    pieces: list[str] = []
    for part in parts:
        if not part:
            continue
        if part == ".":
            pieces.append(r"\s*(?:\.|dot)\s*")
        elif part == "/":
            pieces.append(r"\s*(?:/|forward\s+slash|slash)\s*")
        elif part == "-":
            pieces.append(r"\s*(?:-|dash|hyphen)\s*")
        elif part == "_":
            pieces.append(r"\s*(?:_|underscore)\s*")
        else:
            pieces.append(_literal_chars(part))

    body = "".join(pieces)
    return re.compile(_SCHEME_PREFIX + r"(?:www\s*(?:\.|dot)\s*)?" + body + r"/?")
