"""DURATION — segment length falls inside the required window.

Reads `transcript.duration_seconds` and nothing else. **Never shells out to
ffprobe**: that ran upstream at transcribe time and wrote the value into the
transcript (Architecture.md §4.3). Keeping it out of here is what lets the
zero-key demo run on a machine with no ffmpeg on PATH.
"""

from __future__ import annotations

from ..models import Result, Rule, Transcript
from .common import fmt_seconds, result


def _window(rule: Rule) -> str:
    lo, hi = rule.min_seconds, rule.max_seconds
    if lo is not None and hi is not None:
        return f"{lo:g}–{fmt_seconds(hi)}"
    if lo is not None:
        return f"at least {fmt_seconds(lo)}"
    return f"at most {fmt_seconds(hi)}"


def check(rule: Rule, tx: Transcript) -> Result:
    actual = float(tx.duration_seconds)
    expected = _window(rule)
    detected = fmt_seconds(round(actual, 1))

    if rule.min_seconds is not None and actual < rule.min_seconds:
        return result(
            rule,
            "FAIL",
            "Segment too short",
            expected=expected,
            detected=detected,
        )

    if rule.max_seconds is not None and actual > rule.max_seconds:
        return result(
            rule,
            "FAIL",
            "Segment too long",
            expected=expected,
            detected=detected,
        )

    return result(
        rule,
        "PASS",
        "Duration inside the required window",
        expected=expected,
        detected=detected,
    )
