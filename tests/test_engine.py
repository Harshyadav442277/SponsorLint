"""Readiness resolution for all three states, plus the rules around them."""

import json
from pathlib import Path

import pytest

from sponsorlint.lint.engine import run
from sponsorlint.models import EmptySpecError, Rule, Spec, SpecError, Transcript

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def transcript(text: str = "This video is sponsored by Aegis VPN.", duration: float = 74.2):
    return Transcript(
        duration_seconds=duration,
        segments=[{"start": 0.0, "end": 3.8, "text": text}],
    )


def rule(**kw) -> Rule:
    base = {
        "id": "r1",
        "type": "MUST_SAY",
        "label": "Feature mention",
        "source_quote": "Please mention Shield Mode by name at least once.",
        "phrases": ["Shield Mode"],
    }
    return Rule.model_validate({**base, **kw})


# -- the three readiness states -------------------------------------------


def test_blocking_failure_is_do_not_send():
    report = run(Spec(rules=[rule()]), transcript())
    assert report.status == "DO_NOT_SEND"
    assert report.label == "DO NOT SEND"


def test_failing_warning_rule_is_review():
    report = run(Spec(rules=[rule(severity="warning")]), transcript())
    assert report.results[0].status == "WARN"
    assert report.status == "REVIEW"


def test_all_passing_is_sponsor_ready():
    report = run(Spec(rules=[rule()]), transcript("Try Shield Mode today."))
    assert report.status == "SPONSOR_READY"


def test_a_passing_rule_reports_pass_regardless_of_severity():
    """Severity is consulted only when a rule FAILS."""
    report = run(Spec(rules=[rule(severity="warning")]), transcript("Try Shield Mode today."))
    assert report.results[0].status == "PASS"
    assert report.status == "SPONSOR_READY"


# -- manual review is explicit and blocks until resolved -------------------


def test_unresolved_manual_review_item_is_review():
    spec = Spec(
        rules=[rule()],
        manual_review=[{"source_quote": "Interface visible for five seconds.",
                        "reason": "Visual requirement."}],
    )
    report = run(spec, transcript("Try Shield Mode today."))
    assert report.status == "REVIEW"
    assert report.summary.manual_review == 1
    assert report.summary.manual_confirmed == 0


def test_confirmed_manual_review_item_allows_sponsor_ready():
    spec = Spec(
        rules=[rule()],
        manual_review=[{"source_quote": "Interface visible for five seconds.",
                        "reason": "Visual requirement.", "confirmed": True}],
    )
    report = run(spec, transcript("Try Shield Mode today."))
    assert report.status == "SPONSOR_READY"
    assert report.summary.manual_review == 0
    assert report.summary.manual_confirmed == 1


def test_manual_review_items_are_excluded_from_the_score():
    spec = Spec(
        rules=[rule()],
        manual_review=[{"source_quote": "Interface visible.", "reason": "Visual."}],
    )
    report = run(spec, transcript("Try Shield Mode today."))
    assert report.score.fraction == "1/1"


def test_any_failure_wins_over_warnings_and_unresolved_manual_items():
    spec = Spec(
        rules=[rule(id="fail"), rule(id="warn", severity="warning")],
        manual_review=[{"source_quote": "Check the visual.", "reason": "Visual."}],
    )
    report = run(spec, transcript())
    assert report.status == "DO_NOT_SEND"
    assert (report.summary.fail, report.summary.warn, report.summary.manual_review) == (1, 1, 1)


def test_every_manual_item_must_be_confirmed_before_sponsor_ready():
    spec = Spec(
        rules=[rule()],
        manual_review=[
            {"source_quote": "Check visual one.", "reason": "Visual.", "confirmed": True},
            {"source_quote": "Check visual two.", "reason": "Visual.", "confirmed": False},
        ],
    )
    assert run(spec, transcript("Try Shield Mode today.")).status == "REVIEW"

    spec.manual_review[1].confirmed = True
    assert run(spec, transcript("Try Shield Mode today.")).status == "SPONSOR_READY"


# -- error handling --------------------------------------------------------


def test_empty_spec_never_resolves_to_sponsor_ready():
    with pytest.raises(EmptySpecError):
        run(Spec(rules=[]), transcript())


def test_review_required_rule_cannot_enter_the_verifier():
    unresolved = rule(needs_review=True)
    with pytest.raises(SpecError, match="flagged for review"):
        run(Spec(rules=[unresolved]), transcript("Try Shield Mode today."))


def test_a_validator_exception_becomes_manual_review_not_pass(monkeypatch):
    from sponsorlint.lint import engine

    def boom(_rule, _tx):
        raise RuntimeError("kaboom")

    monkeypatch.setitem(engine.VALIDATORS, "MUST_SAY", boom)
    report = run(Spec(rules=[rule()]), transcript())
    assert report.results[0].status == "MANUAL_REVIEW"
    assert report.status == "REVIEW"
    assert "kaboom" in report.results[0].advisory


# -- the committed demo campaign ------------------------------------------


def load(name: str):
    return json.loads((SAMPLES / name).read_text(encoding="utf-8"))


def test_v1_produces_the_canonical_verdict():
    spec = Spec.model_validate(load("spec.approved.json"))
    report = run(spec, Transcript.model_validate(load("transcript.v1.json")))

    assert (report.summary.fail, report.summary.warn,
            report.summary.passed, report.summary.manual_review) == (3, 0, 4, 1)
    assert report.summary.manual_confirmed == 0
    assert report.score.fraction == "4/7"
    assert report.status == "DO_NOT_SEND"


def test_v3_stays_in_review_while_visual_item_is_unresolved():
    spec = Spec.model_validate(load("spec.approved.json"))
    report = run(spec, Transcript.model_validate(load("transcript.v3.json")))

    assert report.score.fraction == "7/7"
    assert report.summary.fail == 0
    assert report.summary.manual_review == 1
    assert report.status == "REVIEW"


def test_editing_the_spec_changes_the_real_verdict():
    """The test that proves the spec drives the verifier and is not decorative.
    V3 says seventy-three percent; asking for 70% must flip r3 to FAIL."""
    raw = load("spec.approved.json")
    spec = Spec.model_validate(raw)
    tx = Transcript.model_validate(load("transcript.v3.json"))
    assert run(spec, tx).status == "REVIEW"

    for r in raw["rules"]:
        if r["id"] == "r3":
            r["expected"] = "70%"
    edited = run(Spec.model_validate(raw), tx)

    assert edited.status == "DO_NOT_SEND"
    assert edited.score.fraction == "6/7"


def test_every_finding_answers_all_five_questions():
    """what was required · what was detected · where · evidence · source."""
    spec = Spec.model_validate(load("spec.approved.json"))
    report = run(spec, Transcript.model_validate(load("transcript.v1.json")))

    for result in report.results:
        assert result.source_quote
        assert result.expected
        assert result.detected
        if result.status == "FAIL" and result.detected != "not found":
            assert result.timestamp is not None
            assert result.evidence
