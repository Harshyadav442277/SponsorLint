"""MUST_NOT_SAY — a prohibited phrase does not occur.

**Normalized exact containment only. No fuzzy matching.** A fuzzy prohibition
false-fires, and a false FAIL is the expensive error: it sends the creator back
to re-edit something that was fine. A near miss goes to MANUAL REVIEW, never to
FAIL.

The substring trap, in the direction the fixtures test it: a rule prohibiting
"completely anonymous" must not fire on a transcript that only says
"anonymously". Exact containment gives that for free.
"""

from __future__ import annotations

from ..models import Result, Rule, Transcript
from ..normalize import canonicalize
from .common import quoted, result
from .haystack import FUZZY_MIN_CHARS, FUZZY_THRESHOLD, Haystack


def check(rule: Rule, tx: Transcript) -> Result:
    hay = Haystack(tx)
    phrases = rule.phrases or []

    for phrase in phrases:
        needle = canonicalize(phrase)
        if not needle:
            continue
        hit = hay.contains(needle)
        if hit:
            return result(
                rule,
                "FAIL",
                "Prohibited claim",
                expected=f"never say {quoted(phrase)}",
                detected=quoted(phrase),
                timestamp=hit.start,
                evidence=hit.evidence,
            )

    for phrase in phrases:
        needle = canonicalize(phrase)
        if len(needle) < FUZZY_MIN_CHARS:
            continue
        score, hit = hay.best_fuzzy(needle, allow_truncation=True)
        if score >= FUZZY_THRESHOLD and hit is not None:
            return result(
                rule,
                "MANUAL_REVIEW",
                "Possible prohibited claim — check this one yourself",
                expected=f"never say {quoted(phrase)}",
                detected=f'close wording: "{hit.matched}"',
                timestamp=hit.start,
                evidence=hit.evidence,
                advisory=(
                    "The exact prohibited phrase does not occur, but the wording "
                    "is close. SponsorLint does not fail a prohibition on a "
                    "near match."
                ),
            )

    return result(
        rule,
        "PASS",
        "No prohibited claim found",
        expected=" and ".join(f"never say {quoted(p)}" for p in phrases),
        detected="not present",
    )
