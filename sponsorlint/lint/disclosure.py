"""MUST_DISCLOSE — sponsorship disclosure is present, with a timestamp.

Accepted disclosure phrasings are a **module constant**, not a rule field: the
compiler never emits them, so a brief cannot accidentally narrow or widen what
counts as a disclosure.

Placement (Architecture.md §5.4) is a derived property of this result, not a
seventh rule type:

    brief states placement in words but gives no number
        -> compiler emits within_first_seconds: null, needs_review: true
        -> the review screen requires a value before the spec is approvable
        -> the number came from the user, never from us

    brief states no placement at all
        -> within_first_seconds stays null
        -> report presence and timestamp, plus an advisory. Never a verdict.

No invented threshold. No regulatory language — we check the supplied brief,
not the law.
"""

from __future__ import annotations

import re

from ..models import Result, Rule, Transcript
from .common import fmt_timecode, result
from .haystack import Haystack

#: The five accepted phrasings. Exact containment only — "I sponsored a little
#: league team once" is not a disclosure, and fuzzy matching would say it was.
DISCLOSURE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bthis video is sponsored by\b"),
    re.compile(r"\bsponsored by\b"),
    re.compile(r"\bpaid partnership\b"),
    re.compile(r"\btoday's sponsor is\b"),
    re.compile(r"\bthanks to .{1,40}? for sponsoring\b"),
)


def _earliest(hay: Haystack):
    """The first disclosure phrase in the transcript, preferring the longest
    phrasing when two start at the same place."""
    best = None
    best_offset = None
    for pattern in DISCLOSURE_PATTERNS:
        for match in pattern.finditer(hay.numeric):
            offset = match.start()
            if _is_non_affirmative(hay.numeric, offset):
                continue
            if best_offset is None or offset < best_offset or (
                offset == best_offset and len(match.group(0)) > len(best[1])
            ):
                best_offset = offset
                best = (offset, match.group(0))

    if best is None:
        return None
    return hay.hit_at(best[0], best[1])


def _is_non_affirmative(text: str, match_start: int) -> bool:
    """Reject narrow, deterministic negations, questions, and past claims."""
    prefix = text[max(0, match_start - 80) : match_start]
    negation = re.search(
        r"\b(?:not|never|isn't|isnt)\b(?:\s+(?:a|an|the|this|video|is|was)){0,4}\s*$",
        prefix,
    )
    counterfactual = re.search(r"\bwish\b(?:\s+[a-z0-9']+){0,6}\s*$", prefix)
    past_relationship = re.search(
        r"\b(?:used\s+to\s+be|no\s+longer|formerly|previously)\s*$",
        prefix,
    )
    reported_question = re.search(
        r"\b(?:asked|wondered)\b(?:\s+[a-z0-9']+){0,8}\s*$",
        prefix,
    )
    inverted_question = re.search(
        r"\b(?:is|was|are|were)\s+(?:this|that|it|the\s+video)\s*$",
        prefix,
    )
    return any((
        negation,
        counterfactual,
        past_relationship,
        reported_question,
        inverted_question,
    ))


def check(rule: Rule, tx: Transcript) -> Result:
    hay = Haystack(tx)
    hit = _earliest(hay)

    if hit is None:
        return result(
            rule,
            "FAIL",
            "Sponsorship disclosure missing",
            expected="a spoken sponsorship disclosure",
            detected="not found",
        )

    timecode = fmt_timecode(hit.start)
    limit = rule.within_first_seconds

    if limit is None:
        # The brief did not state placement. Presence is the requirement; the
        # timestamp is reported and placement is an advisory, never a verdict.
        return result(
            rule,
            "PASS",
            "Sponsorship disclosure present",
            expected="a spoken sponsorship disclosure",
            detected=f"disclosed at {timecode}",
            timestamp=hit.start,
            evidence=hit.evidence,
            advisory=f"Disclosure occurs at {timecode}. Review placement before sending.",
        )

    expected = f"within first {limit:g}s (user-set)"
    if hit.start <= limit:
        return result(
            rule,
            "PASS",
            "Disclosure near beginning",
            expected=expected,
            detected=f"disclosed at {timecode}",
            timestamp=hit.start,
            evidence=hit.evidence,
        )

    return result(
        rule,
        "FAIL",
        "Disclosure too late",
        expected=expected,
        detected=f"disclosed at {timecode}",
        timestamp=hit.start,
        evidence=hit.evidence,
    )
