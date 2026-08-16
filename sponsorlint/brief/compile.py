"""Brief text -> Spec. The only LLM call in the project. Architecture.md §9.

The model **proposes** the specification. The user owns it. Deterministic code
enforces the approved version. Nothing here ever sees a transcript.

Imported only from the `compile` and `analyze` command branches — never at
module scope on the demo path.
"""

from __future__ import annotations

import os

from ..models import Spec
from .prompt import PROMPT_VERSION, build_prompt

MODEL = "claude-opus-5"
MAX_TOKENS = 16000


class CompileError(RuntimeError):
    pass


def compile_brief(brief_text: str, *, model: str = MODEL, client=None) -> Spec:
    """Compile a sponsor brief into a proposed specification.

    Structured outputs pass the `Spec` model to the API directly, so the API
    constraint and the Pydantic validation are the same schema. One retry on a
    malformed or schema-violating response, then the error is surfaced — never
    a loop, and never a faked spec.
    """
    if not brief_text.strip():
        raise CompileError("The brief is empty — nothing to compile.")

    client = client or _client()
    prompt = build_prompt(brief_text)
    last_error: Exception | None = None

    for attempt in (1, 2):
        try:
            response = client.messages.parse(
                model=model,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
                output_format=Spec,
            )
        except Exception as exc:  # noqa: BLE001 - surfaced below, never swallowed
            last_error = exc
            if attempt == 2:
                raise CompileError(
                    f"The compiler request failed — {type(exc).__name__}: {exc}"
                ) from exc
            continue

        if response.stop_reason == "refusal":
            raise CompileError(
                "The model declined to compile this brief. Review the brief text, "
                "or write the specification by hand and verify with "
                "`python -m sponsorlint verify`."
            )

        spec = response.parsed_output
        if spec is None:
            last_error = CompileError("The model returned no structured output.")
            if attempt == 2:
                raise last_error
            continue

        return _finalize(spec)

    raise CompileError(f"Could not compile the brief — {last_error}")


def _finalize(spec: Spec) -> Spec:
    """Normalize ids and reject anything the schema could not catch."""
    for index, rule in enumerate(spec.rules, start=1):
        if not rule.id:
            rule.id = f"r{index}"
        if not rule.label:
            rule.label = rule.type.replace("_", " ").title()
        # Belt and braces: source_quote is mandatory in the model, so an
        # extraction without one has already been rejected by validation.
        if not rule.source_quote.strip():
            raise CompileError(
                f"Rule {rule.id} has no source quote. Every rule must cite the "
                f"sentence of the brief it came from."
            )
    return spec


def _client():
    try:
        import anthropic
    except ImportError as exc:
        raise CompileError(
            "The anthropic package is not installed. It is in requirements.txt "
            "but not requirements-demo.txt:  pip install -r requirements.txt"
        ) from exc

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise CompileError(
            "ANTHROPIC_API_KEY is not set. The compiler needs it; `demo`, "
            "`verify` and `eval` do not."
        )
    return anthropic.Anthropic()


__all__ = ["compile_brief", "CompileError", "MODEL", "PROMPT_VERSION"]
