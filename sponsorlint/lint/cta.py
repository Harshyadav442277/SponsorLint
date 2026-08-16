"""URL_OR_CTA — the tracked URL, promo code or call to action is spoken.

Both sides are canonicalized, then matched. A URL is matched by a pattern built
from the expected URL, so "aegis vpn dot com slash alex" and
"www.aegisvpn.com/alex" both resolve to the same campaign link — and the
original transcript line always comes back as the evidence.
"""

from __future__ import annotations

from ..models import Result, Rule, Transcript
from ..normalize import canonicalize
from ..normalize.codes import looks_like_code
from ..normalize.codes import spoken_pattern as code_pattern
from ..normalize.urls import looks_like_url
from ..normalize.urls import spoken_pattern as url_pattern
from .common import result
from .haystack import FUZZY_MIN_CHARS, FUZZY_THRESHOLD, Haystack


def check(rule: Rule, tx: Transcript) -> Result:
    expected = (rule.expected or "").strip()
    hay = Haystack(tx)

    is_identifier = looks_like_url(expected) or looks_like_code(expected)

    hit = None
    if looks_like_url(expected):
        hit = hay.search_any_view(url_pattern(expected))
    elif looks_like_code(expected):
        hit = hay.search_any_view(code_pattern(expected))

    if hit is None:
        hit = hay.contains(canonicalize(expected))

    # A tracked URL or promo code is an identifier, not a phrase: it is either
    # the campaign's or it is somebody else's. Fuzzy matching one is the same
    # mistake as fuzzy-matching 70 against 73. The margin is thin — measured,
    # "aegisvpn.com/alex" scores 82.4 against a spoken "aegis.com/alex" and
    # 76.5 against "aegisvpn.com/jordan", both under threshold but only just.
    # Fuzzy is used for prose calls to action and nothing else.
    if hit is None and not is_identifier:
        needle = canonicalize(expected)
        if len(needle) >= FUZZY_MIN_CHARS:
            score, fuzzy_hit = hay.best_fuzzy(needle)
            if score >= FUZZY_THRESHOLD:
                hit = fuzzy_hit

    if hit is not None:
        return result(
            rule,
            "PASS",
            rule.label,
            expected=expected,
            detected=hit.matched,
            timestamp=hit.start,
            evidence=hit.evidence,
        )

    return result(
        rule,
        "FAIL",
        f"{rule.label} — not spoken",
        expected=expected,
        detected="not found",
    )
