"""Terminal rendering must stay valid and readable on every supported Python."""

from io import StringIO

from sponsorlint.models import Report, Result, Score, Summary
from sponsorlint.report.terminal import render


def test_source_quote_renders_with_literal_quotes():
    report = Report(
        status="DO_NOT_SEND",
        summary=Summary(fail=1),
        score=Score(passed=0, total=1),
        results=[
            Result(
                rule_id="r1",
                rule_type="MUST_SAY",
                status="FAIL",
                title="Required mention missing",
                source_quote="Mention Shield Mode.",
                expected="Shield Mode",
                detected="not found",
            )
        ],
    )
    stream = StringIO()

    output = render(report, stream=stream)

    assert 'from brief: "Mention Shield Mode."' in output
    assert stream.getvalue() == output + "\n"
