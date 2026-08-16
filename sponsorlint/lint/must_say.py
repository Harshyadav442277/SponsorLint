"""MUST_SAY — a required phrase, product name or talking point appears.

PASS if **any** phrase in the rule occurs. Normalized exact containment runs
first; `partial_ratio` >= 90 on the joined transcript is only the fallback.
"""

from __future__ import annotations

from ..models import Result, Rule, Transcript
from ..normalize import canonicalize
from .common import quoted, result
from .haystack import FUZZY_MIN_CHARS, FUZZY_THRESHOLD, Haystack

#: Only used to decide whether showing the nearest window helps the user
#: understand a failure. It is a display choice and never affects a verdict.
_SHOW_CLOSEST_ABOVE = 70.0


def check(rule: Rule, tx: Transcript) -> Result:
    hay = Haystack(tx)
    phrases = rule.phrases or []

    best_score = 0.0
    best_window = ""

    for phrase in phrases:
        needle = canonicalize(phrase)
        if not needle:
            continue

        hit = hay.contains(needle)
        if hit:
            return result(
                rule,
                "PASS",
                "Required mention present",
                expected=quoted(phrase),
                detected=hit.matched,
                timestamp=hit.start,
                evidence=hit.evidence,
            )

        # Short needles are matched exactly, never fuzzed: partial_ratio("vpn",
        # anything containing v...p...n) is 100.0.
        if len(needle) < FUZZY_MIN_CHARS:
            continue

        score, fuzzy_hit = hay.best_fuzzy(needle)
        if score >= FUZZY_THRESHOLD and fuzzy_hit is not None:
            return result(
                rule,
                "PASS",
                "Required mention present",
                expected=quoted(phrase),
                detected=fuzzy_hit.matched,
                timestamp=fuzzy_hit.start,
                evidence=fuzzy_hit.evidence,
            )
        if score > best_score and fuzzy_hit is not None:
            best_score = score
            best_window = fuzzy_hit.matched

    expected = " or ".join(quoted(p) for p in phrases)
    advisory = None
    if best_score >= _SHOW_CLOSEST_ABOVE and best_window:
        advisory = f'Closest match in the transcript: "{best_window}" ({best_score:.0f}%)'

    return result(
        rule,
        "FAIL",
        "Required mention missing",
        expected=expected,
        detected="not found",
        advisory=advisory,
    )
