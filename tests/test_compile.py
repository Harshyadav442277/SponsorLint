"""The model may propose a spec; only brief-grounded evidence may leave compilation."""

from types import SimpleNamespace

import pytest

from sponsorlint.brief.compile import CompileError, compile_brief
from sponsorlint.models import Spec


class FakeMessages:
    def __init__(self, spec: Spec):
        self.spec = spec
        self.calls = 0

    def parse(self, **_kwargs):
        self.calls += 1
        return SimpleNamespace(stop_reason="end_turn", parsed_output=self.spec.model_copy(deep=True))


def client_for(spec: Spec):
    messages = FakeMessages(spec)
    return SimpleNamespace(messages=messages), messages


def test_compiler_rejects_invented_rule_source_quote_after_one_retry():
    spec = Spec.model_validate({
        "rules": [{
            "id": "r1",
            "type": "MUST_SAY",
            "label": "Impossible claim",
            "source_quote": "Brand guarantees immortality.",
            "phrases": ["immortality"],
        }],
    })
    client, messages = client_for(spec)

    with pytest.raises(CompileError, match="does not occur"):
        compile_brief("Mention the product name.", client=client)
    assert messages.calls == 2


def test_compiler_rejects_invented_manual_review_source_quote():
    spec = Spec.model_validate({
        "rules": [{
            "id": "r1",
            "type": "MUST_SAY",
            "label": "Product mention",
            "source_quote": "Mention the product name.",
            "phrases": ["Aegis VPN"],
        }],
        "manual_review": [{
            "source_quote": "Show a flying unicorn.",
            "reason": "Visual requirement.",
        }],
    })
    client, _messages = client_for(spec)

    with pytest.raises(CompileError, match="Manual-review item"):
        compile_brief("Mention the product name.", client=client)


def test_compiler_grounding_normalizes_whitespace_only():
    spec = Spec.model_validate({
        "rules": [{
            "id": "r1",
            "type": "MUST_SAY",
            "label": "Product mention",
            "source_quote": "Mention the product name.",
            "phrases": ["Aegis VPN"],
        }],
    })
    client, messages = client_for(spec)

    result = compile_brief("Campaign\n\nMention   the product name.", client=client)
    assert result.rules[0].source_quote == "Mention the product name."
    assert messages.calls == 1
