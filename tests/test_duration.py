"""DURATION — the one validator that reads no text at all.

It reads `transcript.duration_seconds` and nothing else. ffprobe ran upstream
at transcribe time, which is what lets the zero-key demo run on a machine with
no ffmpeg on PATH, so the important negative property here is that checking a
duration never touches the media.
"""

import pytest

from sponsorlint.lint import duration
from sponsorlint.lint.engine import check_rule
from sponsorlint.models import Rule, Transcript


def transcript(seconds: float) -> Transcript:
    return Transcript(
        duration_seconds=seconds,
        segments=[{"start": 0.0, "end": min(3.0, seconds), "text": "sponsored by Aegis VPN"}],
    )


def rule(**kw) -> Rule:
    base = {
        "id": "duration",
        "type": "DURATION",
        "label": "Segment length",
        "source_quote": "The integration must run between 60 and 90 seconds.",
    }
    return Rule.model_validate({**base, **kw})


# -- verdicts ---------------------------------------------------------------


@pytest.mark.parametrize("seconds", [60.0, 74.2, 90.0])
def test_a_duration_inside_the_window_passes(seconds):
    result = duration.check(rule(min_seconds=60, max_seconds=90), transcript(seconds))
    assert result.status == "PASS"


@pytest.mark.parametrize("bounds", [{"min_seconds": 60}, {"min_seconds": 60, "max_seconds": 90}])
def test_the_lower_bound_is_inclusive(bounds):
    assert duration.check(rule(**bounds), transcript(60.0)).status == "PASS"
    assert duration.check(rule(**bounds), transcript(59.9)).status == "FAIL"


@pytest.mark.parametrize("bounds", [{"max_seconds": 90}, {"min_seconds": 60, "max_seconds": 90}])
def test_the_upper_bound_is_inclusive(bounds):
    assert duration.check(rule(**bounds), transcript(90.0)).status == "PASS"
    assert duration.check(rule(**bounds), transcript(90.1)).status == "FAIL"


def test_too_short_and_too_long_are_distinguishable_in_the_report():
    short = duration.check(rule(min_seconds=60, max_seconds=90), transcript(30.0))
    long = duration.check(rule(min_seconds=60, max_seconds=90), transcript(120.0))
    assert short.title == "Segment too short"
    assert long.title == "Segment too long"


# -- what the report says ---------------------------------------------------


@pytest.mark.parametrize(
    "bounds,expected",
    [
        ({"min_seconds": 60, "max_seconds": 90}, "60\u201390s"),
        ({"min_seconds": 60}, "at least 60s"),
        ({"max_seconds": 90}, "at most 90s"),
    ],
)
def test_the_window_is_described_from_whichever_bounds_exist(bounds, expected):
    assert duration.check(rule(**bounds), transcript(74.2)).expected == expected


def test_the_detected_duration_is_rounded_for_display():
    result = duration.check(rule(min_seconds=60), transcript(74.2481))
    assert result.detected == "74.2s"


def test_every_result_carries_the_source_quote():
    # The quote is what makes a finding auditable and is never omitted.
    for seconds in (30.0, 74.2, 120.0):
        result = duration.check(rule(min_seconds=60, max_seconds=90), transcript(seconds))
        assert result.source_quote == "The integration must run between 60 and 90 seconds."


# -- severity ---------------------------------------------------------------


def test_a_warning_severity_duration_failure_is_downgraded_to_warn():
    failing = rule(min_seconds=60, max_seconds=90, severity="warning")
    assert check_rule(failing, transcript(30.0)).status == "WARN"


def test_an_error_severity_duration_failure_stays_a_fail():
    failing = rule(min_seconds=60, max_seconds=90)
    assert check_rule(failing, transcript(30.0)).status == "FAIL"


# -- the ffmpeg-free guarantee ----------------------------------------------


def test_checking_a_duration_never_shells_out(monkeypatch):
    import subprocess

    def explode(*args, **kwargs):  # pragma: no cover - only runs on regression
        raise AssertionError("DURATION must not invoke ffprobe at verify time")

    monkeypatch.setattr(subprocess, "run", explode)
    monkeypatch.setattr(subprocess, "check_output", explode)
    assert duration.check(rule(min_seconds=60, max_seconds=90), transcript(74.2)).status == "PASS"
