"""Shared helpers for the validators. No logic that decides a verdict."""

from __future__ import annotations

from ..models import Result, Rule, Status


def fmt_timecode(seconds: float | None) -> str:
    """MM:SS, widening to H:MM:SS once the timestamp passes an hour.

    The transcript covers the whole video, not only the sponsor segment, so an
    integration placed late in a long upload lands past 60:00. Rendered as a
    bare minute count that reads "62:05" — a number no editor can scrub to.
    The player's own timecode is 1:02:05, so that is what the report shows.
    """
    if seconds is None:
        return "--:--"
    total = int(max(0.0, float(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def fmt_seconds(seconds: float) -> str:
    return f"{seconds:g}s"


def quoted(text: str) -> str:
    return f'"{text}"'


def uncapitalize(text: str) -> str:
    """"Campaign discount" -> "campaign discount", "Campaign URL" -> "campaign URL"."""
    return text[:1].lower() + text[1:] if text else text


def result(rule: Rule, status: Status, title: str, **fields) -> Result:
    """Build a Result carrying the rule's identity and source quote.

    The source quote travels with every finding — it is what makes the finding
    auditable, and it is never omitted.
    """
    return Result(
        rule_id=rule.id,
        rule_type=rule.type,
        status=status,
        title=title,
        source_quote=rule.source_quote,
        severity=rule.severity,
        **fields,
    )
