"""Boundary validation for externally supplied specifications and transcripts."""

import math

import pytest
from pydantic import ValidationError

from sponsorlint.models import Rule, Transcript


@pytest.mark.parametrize("duration", [math.nan, math.inf, -math.inf, 0, -1])
def test_transcript_duration_must_be_finite_and_positive(duration):
    with pytest.raises(ValidationError):
        Transcript.model_validate({
            "duration_seconds": duration,
            "segments": [],
        })


@pytest.mark.parametrize(
    "segment",
    [
        {"start": math.nan, "end": 2, "text": "speech"},
        {"start": -1, "end": 2, "text": "speech"},
        {"start": 3, "end": 2, "text": "speech"},
        {"start": 1, "end": 2, "text": "   "},
    ],
)
def test_segment_timestamps_and_text_are_validated(segment):
    with pytest.raises(ValidationError):
        Transcript.model_validate({
            "duration_seconds": 10,
            "segments": [segment],
        })


def test_segment_cannot_extend_past_media_duration():
    with pytest.raises(ValidationError, match="past transcript duration"):
        Transcript.model_validate({
            "duration_seconds": 10,
            "segments": [{"start": 9, "end": 11, "text": "speech"}],
        })


def test_segment_starts_must_be_monotonic():
    with pytest.raises(ValidationError, match="ordered by start time"):
        Transcript.model_validate({
            "duration_seconds": 10,
            "segments": [
                {"start": 4, "end": 5, "text": "later"},
                {"start": 1, "end": 2, "text": "earlier"},
            ],
        })


@pytest.mark.parametrize("value", [math.nan, math.inf, -1])
def test_duration_rule_bounds_must_be_finite_and_nonnegative(value):
    with pytest.raises(ValidationError):
        Rule.model_validate({
            "id": "duration",
            "type": "DURATION",
            "label": "Read length",
            "source_quote": "Keep the read under 75 seconds.",
            "max_seconds": value,
        })


@pytest.mark.parametrize(
    ("rule_type", "valid_payload", "wrong_payload"),
    [
        ("MUST_SAY", {"phrases": ["Shield Mode"]}, {"expected": "Shield Mode"}),
        ("MUST_NOT_SAY", {"phrases": ["unhackable"]}, {"max_seconds": 30}),
        ("EXACT_VALUE", {"expected": "73%"}, {"phrases": ["73%"]}),
        ("MUST_DISCLOSE", {}, {"within_last_seconds": 15}),
        ("DURATION", {"max_seconds": 90}, {"expected": "90"}),
        ("URL_OR_CTA", {"expected": "aegisvpn.com/alex"}, {"min_seconds": 1}),
    ],
)
def test_rule_types_reject_fields_owned_by_other_rule_types(
    rule_type, valid_payload, wrong_payload
):
    with pytest.raises(ValidationError, match="does not accept"):
        Rule.model_validate({
            "id": "r1",
            "type": rule_type,
            "label": "Requirement",
            "source_quote": "Contract language.",
            **valid_payload,
            **wrong_payload,
        })


@pytest.mark.parametrize("field", ["id", "label"])
def test_rule_identity_fields_cannot_be_empty(field):
    payload = {
        "id": "r1",
        "type": "MUST_SAY",
        "label": "Requirement",
        "source_quote": "Mention Shield Mode.",
        "phrases": ["Shield Mode"],
    }
    payload[field] = "   "
    with pytest.raises(ValidationError, match="cannot be empty"):
        Rule.model_validate(payload)


def test_duplicate_rule_ids_are_rejected():
    from sponsorlint.models import Spec

    payload = {
        "id": "r1",
        "type": "MUST_SAY",
        "label": "Requirement",
        "source_quote": "Mention Shield Mode.",
        "phrases": ["Shield Mode"],
    }
    with pytest.raises(ValidationError, match="duplicate rule id"):
        Spec.model_validate({"rules": [payload, payload]})


def test_manual_review_reason_cannot_be_empty():
    from sponsorlint.models import Spec

    with pytest.raises(ValidationError, match="reason cannot be empty"):
        Spec.model_validate({
            "manual_review": [{"source_quote": "Show the UI.", "reason": ""}],
        })
