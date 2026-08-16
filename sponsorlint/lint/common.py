"""Shared helpers for the validators. No logic that decides a verdict."""

from __future__ import annotations

from ..models import Result, Rule, Status


def fmt_timecode(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    seconds = max(0.0, float(seconds))
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


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
