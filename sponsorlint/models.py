"""Pydantic data contracts. Architecture.md §4.

Every boundary parses into one of these models: parse, don't validate later.

Import discipline: pydantic only. This module is on the zero-key demo path.
"""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    field_validator,
    model_validator,
)

# --------------------------------------------------------------------------
# Vocabularies
# --------------------------------------------------------------------------

RuleType = Literal[
    "MUST_SAY",
    "MUST_NOT_SAY",
    "EXACT_VALUE",
    "MUST_DISCLOSE",
    "DURATION",
    "URL_OR_CTA",
]

#: The six executable rule types. Anything else is rejected at validation
#: (PRD.md §4.1, Rules.md §1.2 — no seventh rule family).
RULE_TYPES: tuple[str, ...] = (
    "MUST_SAY",
    "MUST_NOT_SAY",
    "EXACT_VALUE",
    "MUST_DISCLOSE",
    "DURATION",
    "URL_OR_CTA",
)

Severity = Literal["error", "warning"]

#: A validator returns PASS, FAIL or MANUAL_REVIEW. WARN is produced by the
#: engine when a *warning*-severity rule fails — severity is consulted only on
#: failure (Architecture.md §4.1).
Status = Literal["PASS", "FAIL", "WARN", "MANUAL_REVIEW"]

Readiness = Literal["DO_NOT_SEND", "REVIEW", "SPONSOR_READY"]

READINESS_LABEL: dict[str, str] = {
    "DO_NOT_SEND": "DO NOT SEND",
    "REVIEW": "REVIEW",
    "SPONSOR_READY": "SPONSOR READY",
}


class SpecError(ValueError):
    """A specification cannot be verified as given."""


class EmptySpecError(SpecError):
    """No rules to check. Never resolves to SPONSOR READY (Rules.md §3)."""


# --------------------------------------------------------------------------
# Rule
# --------------------------------------------------------------------------


class Rule(BaseModel):
    """One executable requirement extracted from the sponsor brief.

    `source_quote` is mandatory: it is what makes a finding auditable and what
    powers the split-screen review. An extraction without it is rejected.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    type: RuleType
    label: str
    source_quote: str
    severity: Severity = "error"
    needs_review: bool = False

    expected: str | None = None  # EXACT_VALUE, URL_OR_CTA
    phrases: list[str] | None = None  # MUST_SAY, MUST_NOT_SAY
    min_seconds: FiniteFloat | None = None  # DURATION
    max_seconds: FiniteFloat | None = None  # DURATION
    within_first_seconds: FiniteFloat | None = None  # MUST_DISCLOSE placement
    within_last_seconds: FiniteFloat | None = None  # URL_OR_CTA closing placement

    @field_validator("id", "label")
    @classmethod
    def _identity_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("rule id and label cannot be empty")
        return v.strip()

    @field_validator("source_quote")
    @classmethod
    def _quote_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(
                "source_quote is mandatory — every rule must cite the sentence "
                "of the brief it came from"
            )
        return v.strip()

    @field_validator("phrases")
    @classmethod
    def _clean_phrases(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = [p.strip() for p in v if p and p.strip()]
        return cleaned or None

    @model_validator(mode="after")
    def _check_payload(self) -> "Rule":
        t = self.type

        allowed_payloads = {
            "MUST_SAY": {"phrases"},
            "MUST_NOT_SAY": {"phrases"},
            "EXACT_VALUE": {"expected"},
            "MUST_DISCLOSE": {"within_first_seconds"},
            "DURATION": {"min_seconds", "max_seconds"},
            "URL_OR_CTA": {"expected", "within_last_seconds"},
        }
        payload = {
            "expected": self.expected,
            "phrases": self.phrases,
            "min_seconds": self.min_seconds,
            "max_seconds": self.max_seconds,
            "within_first_seconds": self.within_first_seconds,
            "within_last_seconds": self.within_last_seconds,
        }
        wrong = sorted(
            name for name, value in payload.items()
            if value is not None and name not in allowed_payloads[t]
        )
        if wrong:
            raise ValueError(f"{t} does not accept: {', '.join(wrong)}")

        if t in ("MUST_SAY", "MUST_NOT_SAY"):
            if not self.phrases:
                raise ValueError(f"{t} requires at least one entry in `phrases`")

        elif t in ("EXACT_VALUE", "URL_OR_CTA"):
            if not self.expected or not self.expected.strip():
                raise ValueError(f"{t} requires `expected`")
            object.__setattr__(self, "expected", self.expected.strip())
            if t == "URL_OR_CTA" and self.within_last_seconds is not None:
                if self.within_last_seconds <= 0:
                    raise ValueError("`within_last_seconds` must be positive")

        elif t == "DURATION":
            if self.min_seconds is None and self.max_seconds is None:
                raise ValueError("DURATION requires `min_seconds` or `max_seconds`")
            if self.min_seconds is not None and self.min_seconds < 0:
                raise ValueError("DURATION `min_seconds` cannot be negative")
            if self.max_seconds is not None and self.max_seconds <= 0:
                raise ValueError("DURATION `max_seconds` must be positive")
            if (
                self.min_seconds is not None
                and self.max_seconds is not None
                and self.min_seconds > self.max_seconds
            ):
                raise ValueError("DURATION `min_seconds` exceeds `max_seconds`")

        elif t == "MUST_DISCLOSE":
            # within_first_seconds may legitimately be null: the brief may not
            # state placement at all (Architecture.md §5.4).
            if self.within_first_seconds is not None and self.within_first_seconds <= 0:
                raise ValueError("`within_first_seconds` must be positive")

        return self


class ManualReviewItem(BaseModel):
    """A brief requirement no validator can check. Surfaced, never dropped."""

    model_config = ConfigDict(extra="forbid")

    source_quote: str
    reason: str = "Not verifiable from audio or duration."
    confirmed: bool = False

    @field_validator("source_quote")
    @classmethod
    def _manual_quote_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_quote is mandatory for manual-review items")
        return v.strip()

    @field_validator("reason")
    @classmethod
    def _manual_reason_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("manual-review reason cannot be empty")
        return v.strip()


# --------------------------------------------------------------------------
# Spec
# --------------------------------------------------------------------------


class Spec(BaseModel):
    """The compiled requirements. After the review screen, this is *approved*."""

    model_config = ConfigDict(extra="forbid")

    campaign: str = "Untitled campaign"
    rules: list[Rule] = Field(default_factory=list)
    manual_review: list[ManualReviewItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_ids(self) -> "Spec":
        seen: set[str] = set()
        for r in self.rules:
            if r.id in seen:
                raise ValueError(f"duplicate rule id: {r.id}")
            seen.add(r.id)
        return self

    def approval_blockers(self) -> list[str]:
        """Reasons this spec is not yet approvable.

        The trust boundary (Architecture.md §5.4): a rule the compiler was
        unsure about must be resolved by the user before verification runs. A
        MUST_DISCLOSE whose placement threshold is still null is the specific
        case the demo brief produces — the number must come from the user,
        never from us.
        """
        blockers: list[str] = []
        for r in self.rules:
            if r.type == "MUST_DISCLOSE" and r.needs_review and r.within_first_seconds is None:
                blockers.append(
                    f"{r.id}: the brief specifies disclosure placement but gives no "
                    f"number. Set `within_first_seconds` before approving."
                )
            elif r.needs_review:
                blockers.append(
                    f"{r.id}: flagged for review by the compiler. Confirm or edit it."
                )
        return blockers

    def next_rule_id(self) -> str:
        n = 1
        used = {r.id for r in self.rules}
        while f"r{n}" in used:
            n += 1
        return f"r{n}"


# --------------------------------------------------------------------------
# Transcript
# --------------------------------------------------------------------------


class Segment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: FiniteFloat = Field(ge=0)
    end: FiniteFloat = Field(ge=0)
    text: str

    @field_validator("text")
    @classmethod
    def _text_required(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("segment text cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def _ordered_times(self) -> "Segment":
        if self.end < self.start:
            raise ValueError("segment end cannot precede its start")
        return self


class Transcript(BaseModel):
    """Transcribed sponsor segment.

    `duration_seconds` is REQUIRED and is the only duration any validator ever
    reads. ffprobe runs upstream at transcribe time and writes it here, which is
    what keeps the demo path free of an ffmpeg dependency (Architecture.md §4.3).
    """

    model_config = ConfigDict(extra="forbid")

    duration_seconds: FiniteFloat = Field(gt=0)
    segments: list[Segment] = Field(default_factory=list)
    source: str | None = None

    @model_validator(mode="after")
    def _valid_timeline(self) -> "Transcript":
        previous_start = -1.0
        for segment in self.segments:
            if segment.start < previous_start:
                raise ValueError("segments must be ordered by start time")
            if segment.end > self.duration_seconds:
                raise ValueError("segment extends past transcript duration")
            previous_start = segment.start
        return self

    def full_text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------


class Result(BaseModel):
    """One finding. Answers five questions: what was required, what was
    detected, where, what evidence, where the requirement came from."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_type: RuleType
    status: Status
    title: str
    source_quote: str
    severity: Severity = "error"

    expected: str | None = None
    detected: str | None = None
    timestamp: float | None = None
    evidence: str | None = None
    #: Non-blocking note. Used for disclosure placement when the brief did not
    #: state one (Architecture.md §5.4). Never a verdict.
    advisory: str | None = None


class Summary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    passed: int = Field(0, alias="pass")
    warn: int = 0
    fail: int = 0
    manual_review: int = 0  # unresolved manual items
    manual_confirmed: int = 0


class Score(BaseModel):
    """Raw fraction. Manual-review items are excluded from both halves."""

    passed: int = 0
    total: int = 0

    @property
    def fraction(self) -> str:
        return f"{self.passed}/{self.total}"

    @property
    def percent(self) -> float:
        return 0.0 if self.total == 0 else round(self.passed / self.total * 100, 1)


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Readiness
    summary: Summary
    score: Score
    results: list[Result] = Field(default_factory=list)
    manual_review: list[ManualReviewItem] = Field(default_factory=list)
    campaign: str | None = None
    source: str | None = None

    @property
    def label(self) -> str:
        return READINESS_LABEL[self.status]
