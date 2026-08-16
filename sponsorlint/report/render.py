"""Report JSON -> template context. Design.md §5.3.

The only presentation logic here is timecode formatting and highlighting the
matched span inside the evidence line. Nothing is recomputed; the verdict
arrives already decided.
"""

from __future__ import annotations

import html
import re

from ..lint.common import fmt_timecode
from ..models import Report

STATUS_CHIP = {
    "FAIL": "fail",
    "WARN": "warn",
    "PASS": "pass",
    "MANUAL_REVIEW": "manual",
}

STATUS_WORD = {
    "FAIL": "FAIL",
    "WARN": "WARN",
    "PASS": "PASS",
    "MANUAL_REVIEW": "MANUAL",
}

READINESS_CLASS = {
    "DO_NOT_SEND": "fail",
    "REVIEW": "warn",
    "SPONSOR_READY": "pass",
}

READINESS_ICON = {
    "DO_NOT_SEND": "✕",
    "REVIEW": "!",
    "SPONSOR_READY": "✓",
}


def highlight(evidence: str | None, matched: str | None) -> str:
    """Wrap the matched span in `<mark>`.

    `matched` comes from the normalized haystack, so it will not always be
    findable in the raw line — a value detected as "70%" was spoken as "seventy
    percent". When it cannot be located the evidence is returned unmarked
    rather than guessed at.
    """
    if not evidence:
        return ""
    safe = html.escape(evidence)
    if not matched:
        return safe

    words = [re.escape(html.escape(w)) for w in matched.split() if w]
    if not words:
        return safe

    pattern = re.compile(r"\W*".join(words), re.IGNORECASE)
    match = pattern.search(safe)
    if not match:
        return safe
    return (
        safe[: match.start()]
        + "<mark>"
        + safe[match.start() : match.end()]
        + "</mark>"
        + safe[match.end() :]
    )


def report_context(report: Report) -> dict:
    """Everything the report template needs, already formatted."""
    return {
        "status": report.status,
        "label": report.label,
        "state_class": READINESS_CLASS[report.status],
        "icon": READINESS_ICON[report.status],
        "campaign": report.campaign,
        "source": report.source,
        "score": report.score.fraction,
        "summary": report.summary.model_dump(by_alias=True),
        "subline": _subline(report),
        "results": [
            {
                "rule_id": r.rule_id,
                "rule_type": r.rule_type,
                "status": r.status,
                "chip": STATUS_CHIP[r.status],
                "word": STATUS_WORD[r.status],
                "title": r.title,
                "expected": r.expected,
                "detected": r.detected,
                "timestamp": r.timestamp,
                "timecode": fmt_timecode(r.timestamp) if r.timestamp is not None else None,
                "evidence_html": highlight(r.evidence, r.detected),
                "evidence": r.evidence,
                "advisory": r.advisory,
                "source_quote": r.source_quote,
            }
            for r in report.results
        ],
        "manual_review": [
            {"source_quote": m.source_quote, "reason": m.reason, "confirmed": m.confirmed}
            for m in report.manual_review
        ],
    }


def _subline(report: Report) -> str:
    s = report.summary
    if report.status == "SPONSOR_READY":
        blocking = s.passed
        line = f"All {blocking} blocking requirement{'s' if blocking != 1 else ''} passed."
        if s.manual_confirmed:
            line += (
                f" {s.manual_confirmed} manual item"
                f"{'s' if s.manual_confirmed != 1 else ''} confirmed."
            )
        return line

    parts = [f"{s.fail} failed"]
    if s.warn:
        parts.append(f"{s.warn} warning" + ("s" if s.warn != 1 else ""))
    parts.append(f"{s.passed} passed")
    if s.manual_review:
        parts.append(f"{s.manual_review} manual unresolved")
    if s.manual_confirmed:
        parts.append(f"{s.manual_confirmed} manual confirmed")
    return " · ".join(parts)
