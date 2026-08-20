"""The numbers in the docs are the numbers the harness produces.

Architecture.md §7 says it outright: *do not fabricate perfection, publish
whatever the real number is.* Nothing enforced that. The eval block is quoted
in two documents, so a fixture added or a validator tuned left the published
figures silently stale — and for a project whose whole claim is that it does
not invent results, a stale accuracy figure is the worst drift available.
"""

import re
from pathlib import Path

import pytest

from sponsorlint.eval.runner import evaluate

ROOT = Path(__file__).resolve().parents[1]

#: Every document quoting the eval block.
PUBLISHING_DOCS = ("README.md", "Architecture.md")

_LABELS = {
    "Fixtures": "total",
    "Correct": "correct",
    "Incorrect": "incorrect",
    "False FAILs": "false_fails",
    "False PASSes": "false_passes",
    "Manual Review": "manual_review",
}


def published(document: str) -> dict[str, float]:
    """Parse whichever figures the document's eval block states."""
    text = (ROOT / document).read_text(encoding="utf-8")
    found: dict[str, float] = {}

    for label, attribute in _LABELS.items():
        # No end anchor: the False FAIL and False PASS lines carry a trailing
        # gloss after the count.
        match = re.search(rf"^{re.escape(label)}:\s+(\d+)\b", text, re.MULTILINE)
        if match:
            found[attribute] = int(match.group(1))

    accuracy = re.search(r"^Accuracy:\s+([\d.]+)%", text, re.MULTILINE)
    if accuracy:
        found["accuracy"] = float(accuracy.group(1))

    return found


@pytest.mark.parametrize("document", PUBLISHING_DOCS)
def test_the_document_actually_quotes_the_eval_block(document):
    # Guards the guard: a rename that stopped the block matching would
    # otherwise make this whole file pass vacuously.
    figures = published(document)
    assert figures.keys() >= {"total", "accuracy", "false_passes", "false_fails"}


@pytest.mark.parametrize("document", PUBLISHING_DOCS)
def test_published_figures_match_a_real_run(document):
    metrics = evaluate()
    for attribute, claimed in published(document).items():
        assert getattr(metrics, attribute) == claimed, (
            f"{document} publishes {attribute}={claimed}, but the harness "
            f"measures {getattr(metrics, attribute)}. Re-run "
            f"`python -m sponsorlint eval` and update the document."
        )


def test_the_two_documents_publish_the_same_figures():
    readme, architecture = (published(name) for name in PUBLISHING_DOCS)
    shared = readme.keys() & architecture.keys()
    assert shared, "the two eval blocks share no parsed figures"
    for attribute in shared:
        assert readme[attribute] == architecture[attribute]


def test_the_headline_fixture_count_matches_the_prose():
    # README states the fixture count in a sentence as well as in the block,
    # and the two drift independently.
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    prose = re.search(r"over (\d+) hand-labeled text fixtures", text)
    assert prose, "README no longer states the fixture count in prose"
    assert int(prose.group(1)) == evaluate().total
