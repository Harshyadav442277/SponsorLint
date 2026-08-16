"""Every labeled fixture, run as a unit test.

`sponsorlint/eval/fixtures.json` and this file assert the same things: written
once, used twice (Rules.md §4). One case is a documented known limitation and
is expected to miss — asserting it here would freeze the bug in place, so the
suite checks the *aggregate* instead: no False PASSes, and no regression in the
number of misses.
"""

import pytest

from sponsorlint.eval.runner import evaluate, load_cases
from sponsorlint.lint.engine import check_rule
from sponsorlint.models import Rule, Transcript

CASES = load_cases()

#: Cases SponsorLint is known to get wrong, with the reason. Anything else
#: missing is a regression.
KNOWN_MISSES = {"disclosure/known-limitation-unlisted-phrasing"}


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_fixture(case):
    result = check_rule(
        Rule.model_validate(case["rule"]),
        Transcript.model_validate(case["transcript"]),
    )
    if case["id"] in KNOWN_MISSES:
        pytest.xfail(case["note"])
    assert result.status == case["expected"], case["note"]


def test_no_false_passes():
    """A False PASS ships a broken sponsor read to the brand. Zero tolerance."""
    metrics = evaluate()
    offenders = [o.id for o in metrics.outcomes if o.is_false_pass]
    assert offenders == []


def test_false_fails_are_only_the_known_limitations():
    metrics = evaluate()
    offenders = {o.id for o in metrics.outcomes if o.is_false_fail}
    assert offenders <= KNOWN_MISSES


def test_fixture_count_is_in_range():
    assert 24 <= len(CASES) <= 30


def test_every_fixture_rule_carries_a_source_quote():
    for case in CASES:
        assert case["rule"].get("source_quote", "").strip()
