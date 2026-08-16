"""Validator evaluation. Architecture.md §7.

Runs every labeled fixture through the same code path the engine uses and
reports what actually happened. Pure text: no video, no Whisper, no API calls,
under a second.

Terminology, defined once and used everywhere:

    Positive     = SponsorLint reports a violation (returns FAIL).

    False FAIL   = reported FAIL when the requirement was actually satisfied.
                   Cost: the creator re-edits something that was fine.

    False PASS   = reported PASS when the requirement was actually violated.
                   Cost: a broken sponsor read ships to the brand.

The two errors are not symmetric. Avoid false FAILs, route ambiguity to MANUAL
REVIEW, then maximize violation catch rate.

**Do not fabricate perfection. Publish whatever the real number is.**
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..lint.engine import check_rule
from ..models import Rule, Transcript

FIXTURES = Path(__file__).with_name("fixtures.json")


@dataclass
class CaseOutcome:
    id: str
    expected: str
    actual: str
    note: str = ""

    @property
    def correct(self) -> bool:
        return self.expected == self.actual

    @property
    def is_false_fail(self) -> bool:
        return self.expected == "PASS" and self.actual == "FAIL"

    @property
    def is_false_pass(self) -> bool:
        return self.expected == "FAIL" and self.actual == "PASS"


@dataclass
class Metrics:
    outcomes: list[CaseOutcome] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.outcomes)

    @property
    def correct(self) -> int:
        return sum(1 for o in self.outcomes if o.correct)

    @property
    def incorrect(self) -> int:
        return self.total - self.correct

    @property
    def accuracy(self) -> float:
        return 0.0 if not self.total else round(self.correct / self.total * 100, 1)

    @property
    def false_fails(self) -> int:
        return sum(1 for o in self.outcomes if o.is_false_fail)

    @property
    def false_passes(self) -> int:
        return sum(1 for o in self.outcomes if o.is_false_pass)

    @property
    def manual_review(self) -> int:
        return sum(1 for o in self.outcomes if o.actual == "MANUAL_REVIEW")


def load_cases(path: Path = FIXTURES) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["cases"]


def evaluate(cases: list[dict] | None = None) -> Metrics:
    """Run every case. No case is skipped and no verdict is hardcoded."""
    metrics = Metrics()
    for case in cases if cases is not None else load_cases():
        rule = Rule.model_validate(case["rule"])
        transcript = Transcript.model_validate(case["transcript"])
        result = check_rule(rule, transcript)
        metrics.outcomes.append(
            CaseOutcome(
                id=case["id"],
                expected=case["expected"],
                actual=result.status,
                note=case.get("note", ""),
            )
        )
    return metrics


def run_eval(verbose: bool = False) -> Metrics:
    metrics = evaluate()

    if verbose:
        for outcome in metrics.outcomes:
            mark = "ok  " if outcome.correct else "MISS"
            print(f"  {mark}  {outcome.id:<42} expected {outcome.expected:<14} "
                  f"got {outcome.actual}")
        print()

    print("SponsorLint Validator Evaluation")
    print("--------------------------------")
    print(f"Fixtures:        {metrics.total:>5}")
    print(f"Correct:         {metrics.correct:>5}")
    print(f"Incorrect:       {metrics.incorrect:>5}")
    print(f"Accuracy:        {metrics.accuracy:>4}%")
    print()
    print(f"False FAILs:     {metrics.false_fails:>5}     "
          f"(reported FAIL, requirement was satisfied)")
    print(f"False PASSes:    {metrics.false_passes:>5}     "
          f"(reported PASS, requirement was violated)")
    print(f"Manual Review:   {metrics.manual_review:>5}")

    if metrics.incorrect:
        print()
        print("Misses:")
        for outcome in metrics.outcomes:
            if not outcome.correct:
                print(f"  {outcome.id}: expected {outcome.expected}, got {outcome.actual}")

    return metrics
