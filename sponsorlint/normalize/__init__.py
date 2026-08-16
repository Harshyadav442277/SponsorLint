"""Deterministic text normalization. Architecture.md §5.1.

    raw text -> unicode -> case -> punctuation -> whitespace
             -> numbers -> currency/percent
             -> comparison-ready representation

URLs and promo codes are handled by their own modules, which build a pattern
*from the expected value* rather than rewriting the transcript — see `urls.py`
and `codes.py` for why.

Everything here is a pure function.
"""

from __future__ import annotations

from .numbers import canonical_numeric
from .text import collapse, normalize_text

__all__ = ["canonicalize", "normalize_text", "canonical_numeric", "collapse"]


def canonicalize(text: str) -> str:
    """The comparison-ready form used for phrases and exact values."""
    return canonical_numeric(normalize_text(text))
