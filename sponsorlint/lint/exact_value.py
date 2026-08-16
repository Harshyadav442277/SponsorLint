"""EXACT_VALUE — a numeric or code-like value matches exactly.

This is the validator that matters and the one that is easiest to get wrong.

It does not *parse* anything. The transcript is canonicalized (number-words
folded to digits, percent and currency folded onto their symbol) and the
expected value is then a boundary-guarded membership test:

    73 in "seventy-three percent"  -> True
    73 in "seventy percent"        -> False
    73 in "730 dollars"            -> False
    73 in "chapter 173"            -> False

Deterministic only. Never an LLM, never fuzzy — 70 is not 73 (Rules.md §1.6).
"""

from __future__ import annotations

from rapidfuzz.distance import Levenshtein

from ..models import Result, Rule, Transcript
from ..normalize import canonicalize
from ..normalize.codes import canonical_codes, looks_like_code
from ..normalize.codes import spoken_pattern as code_pattern
from ..normalize.numbers import same_shape_pattern, value_pattern
from .common import result, uncapitalize
from .haystack import Haystack


def check(rule: Rule, tx: Transcript) -> Result:
    expected = (rule.expected or "").strip()
    hay = Haystack(tx)
    value = canonicalize(expected)
    what = uncapitalize(rule.label)

    hit = hay.search(value_pattern(value))
    if hit:
        return result(
            rule,
            "PASS",
            f"Correct {what}",
            expected=expected,
            detected=hit.matched,
            timestamp=hit.start,
            evidence=hit.evidence,
        )

    # A promo code read out loud is still an exact match, just spelled
    # differently: "H-A-R-S-H two zero" is HARSH20.
    if looks_like_code(expected):
        hit = hay.search_any_view(code_pattern(expected))
        if hit:
            return result(
                rule,
                "PASS",
                f"Correct {what}",
                expected=expected,
                detected=canonical_codes(hit.matched).strip() or hit.matched,
                timestamp=hit.start,
                evidence=hit.evidence,
            )

    detected, hit = _closest_of_same_shape(hay, value)
    return result(
        rule,
        "FAIL",
        f"Wrong {what}" if hit else f"{rule.label} not found",
        expected=expected,
        detected=detected,
        timestamp=hit.start if hit else None,
        evidence=hit.evidence if hit else None,
    )


def _closest_of_same_shape(hay: Haystack, value: str):
    """What was said instead — reported, never used to decide the verdict."""
    shape = same_shape_pattern(value)
    if shape is None:
        return "not found", None

    hits = hay.search_all(shape)
    if not hits:
        return "not found", None

    best = min(hits, key=lambda h: (Levenshtein.distance(h.matched, value), h.start))
    return best.matched, best
