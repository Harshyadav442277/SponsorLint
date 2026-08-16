"""Dispatch and readiness resolution. Architecture.md §5.5.

The verifier is deterministic. No LLM runs here, ever — the model compiled the
brief long before this point and never sees the transcript.
"""

from __future__ import annotations

from ..models import (
    EmptySpecError,
    Report,
    Result,
    Score,
    Spec,
    Summary,
    Transcript,
)
from . import cta, disclosure, duration, exact_value, must_not_say, must_say
from .common import result

VALIDATORS = {
    "MUST_SAY": must_say.check,
    "MUST_NOT_SAY": must_not_say.check,
    "EXACT_VALUE": exact_value.check,
    "MUST_DISCLOSE": disclosure.check,
    "DURATION": duration.check,
    "URL_OR_CTA": cta.check,
}

#: Failures first, then warnings, then manual review, then passes.
_ORDER = {"FAIL": 0, "WARN": 1, "MANUAL_REVIEW": 2, "PASS": 3}


def run(spec: Spec, transcript: Transcript) -> Report:
    """Run the approved spec against the transcript and resolve readiness."""
    if not spec.rules:
        raise EmptySpecError("No requirements to check. Add at least one rule.")

    results = [check_rule(rule, transcript) for rule in spec.rules]
    results.sort(key=lambda r: _ORDER[r.status])

    scored = [r for r in results if r.status in ("PASS", "FAIL", "WARN")]
    summary = Summary(
        passed=sum(1 for r in results if r.status == "PASS"),
        warn=sum(1 for r in results if r.status == "WARN"),
        fail=sum(1 for r in results if r.status == "FAIL"),
        manual_review=sum(1 for r in results if r.status == "MANUAL_REVIEW")
        + sum(1 for item in spec.manual_review if not item.confirmed),
        manual_confirmed=sum(1 for item in spec.manual_review if item.confirmed),
    )

    return Report(
        status=_readiness(results, spec),
        summary=summary,
        score=Score(passed=summary.passed, total=len(scored)),
        results=results,
        manual_review=list(spec.manual_review),
        campaign=spec.campaign,
        source=transcript.source,
    )


def check_rule(rule, transcript: Transcript) -> Result:
    """Run one rule. Public so the eval harness and the unit tests exercise the
    exact code path the engine uses, including its failure handling."""
    validator = VALIDATORS.get(rule.type)
    if validator is None:  # unreachable while the schema holds; never a PASS
        return result(
            rule,
            "MANUAL_REVIEW",
            "No validator for this rule type",
            detected=f"unsupported rule type {rule.type}",
        )

    try:
        outcome = validator(rule, transcript)
    except Exception as exc:  # noqa: BLE001 - surfaced, never swallowed
        # An exception inside a validator produces MANUAL REVIEW with the
        # reason attached, never PASS (Rules.md §3).
        return result(
            rule,
            "MANUAL_REVIEW",
            "Check could not be completed",
            detected="check failed",
            advisory=f"{type(exc).__name__}: {exc}",
        )

    if outcome.status == "FAIL" and rule.severity == "warning":
        return outcome.model_copy(update={"status": "WARN"})
    return outcome


def _readiness(results: list[Result], spec: Spec) -> str:
    """Resolve failures first; uncertainty stays REVIEW until a human resolves it."""
    if any(r.status == "FAIL" for r in results):
        return "DO_NOT_SEND"
    if any(r.status in ("WARN", "MANUAL_REVIEW") for r in results):
        return "REVIEW"
    if any(not item.confirmed for item in spec.manual_review):
        return "REVIEW"
    return "SPONSOR_READY"
