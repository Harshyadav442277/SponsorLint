"""Promo codes spelled aloud. Architecture.md §5.1.

    "H-A-R-S-H two zero"  ·  "HARSH two zero"  ·  "HARSH20"   ->   HARSH20

This module uses a **per-digit** map. It must never share the arithmetic folder
in `numbers.py`, which correctly folds "two zero" to 2 — right for prose,
catastrophic for a code.
"""

from __future__ import annotations

import re

from .text import normalize_text

#: Per-digit only. "twenty" is deliberately absent: a code is read out digit by
#: digit, and folding "two zero" to 2 is exactly the bug this map exists to avoid.
DIGIT_WORDS: dict[str, str] = {
    "zero": "0", "oh": "0", "o": "0", "nought": "0",
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "niner": "9",
}

_CHUNK = re.compile(r"[a-z]+|\d+")
_SPELLED_RUN = re.compile(r"\b(?:[a-z][\s-]+){1,}[a-z]\b")
_SEP = r"[\s-]?"


def looks_like_code(value: str) -> bool:
    """A promo code: one token, alphanumeric, and not plain prose."""
    v = value.strip()
    if " " in v or not v.isalnum():
        return False
    has_alpha = any(c.isalpha() for c in v)
    has_digit = any(c.isdigit() for c in v)
    return (has_alpha and has_digit) or (has_alpha and v.isupper() and len(v) >= 4)


def _digit_alternatives(digit: str) -> str:
    # Longest first so "oh" is preferred over "o" before backtracking.
    words = sorted((w for w, d in DIGIT_WORDS.items() if d == digit),
                   key=lambda w: (-len(w), w))
    return "(?:" + "|".join(words + [digit]) + ")"


def spoken_pattern(code: str) -> re.Pattern[str]:
    """A pattern matching every spoken form of `code` in normalized text.

    Built from the expected code rather than by canonicalizing the transcript,
    so there is no chance of inventing a code that was never said.
    """
    canon = normalize_text(code).replace(" ", "").replace("-", "")
    pieces: list[str] = []
    for chunk in _CHUNK.findall(canon):
        if chunk.isdigit():
            pieces.append(_SEP.join(_digit_alternatives(d) for d in chunk))
        else:
            pieces.append(_SEP.join(re.escape(c) for c in chunk))
    return re.compile(r"\b" + _SEP.join(pieces) + r"\b")


def canonical_codes(text: str) -> str:
    """Fold spelled-aloud runs in `text` into single uppercase tokens.

    "use code h-a-r-s-h two zero" -> "use code HARSH20"

    Reported as evidence only; matching goes through `spoken_pattern`.
    """
    s = normalize_text(text)

    def _join_letters(m: re.Match[str]) -> str:
        letters = re.findall(r"[a-z]", m.group(0))
        return "".join(letters).upper() if len(letters) >= 2 else m.group(0)

    s = _SPELLED_RUN.sub(_join_letters, s)

    tokens = s.split(" ")
    out: list[str] = []
    for tok in tokens:
        core = tok.strip(".,'")
        if out and out[-1].isupper() and out[-1].isalnum() and core in DIGIT_WORDS:
            out[-1] += DIGIT_WORDS[core]
        elif out and out[-1].isupper() and out[-1].isalnum() and core.isdigit():
            out[-1] += core
        else:
            out.append(tok)
    return " ".join(out)
