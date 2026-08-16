"""Unicode, case, punctuation, whitespace. Architecture.md §5.1, stage one.

Pure functions. No I/O.
"""

from __future__ import annotations

import re
import unicodedata

_QUOTES = {
    "‘": "'",
    "’": "'",
    "‚": "'",
    "“": '"',
    "”": '"',
    "′": "'",
}

_DASHES = {
    "‐": "-",
    "‑": "-",
    "‒": "-",
    "–": "-",
    "—": "-",
    "―": "-",
    "−": "-",
}

#: Punctuation that survives normalization because a later stage needs it:
#: `.` and `/` for URLs, `%` and `$` for values, `-` for hyphenated numerals and
#: spelled-out codes, `'` so "today's sponsor is" still matches.
_KEEP = frozenset(".%$/'-")

_WS = re.compile(r"\s+")


def normalize_text(s: str) -> str:
    """Lowercase, fold unicode, drop punctuation, collapse whitespace."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    for src, dst in _QUOTES.items():
        s = s.replace(src, dst)
    for src, dst in _DASHES.items():
        s = s.replace(src, dst)
    s = s.lower()
    s = "".join(c if (c.isalnum() or c.isspace() or c in _KEEP) else " " for c in s)
    return _WS.sub(" ", s).strip()


def collapse(s: str) -> str:
    return _WS.sub(" ", s).strip()
