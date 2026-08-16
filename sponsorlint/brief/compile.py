"""Brief text -> Spec. The only LLM call in the project. Architecture.md §9.

The model **proposes** the specification. The user owns it. Deterministic code
enforces the approved version. Nothing here ever sees a transcript.

Imported only from the `compile` command branch and web compile route — never at
module scope on the demo path.
"""

from __future__ import annotations

import os

from ..models import Spec
from .prompt import PROMPT_VERSION, build_prompt

MODEL = "claude-opus-5"
MAX_TOKENS = 16000
REQUEST_TIMEOUT_SECONDS = 60


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
                timeout=REQUEST_TIMEOUT_SECONDS,
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

        try:
            return _finalize(spec, brief_text)
        except CompileError as exc:
            last_error = exc
            if attempt == 2:
                raise
            continue

    raise CompileError(f"Could not compile the brief — {last_error}")


def _finalize(spec: Spec, brief_text: str) -> Spec:
    """Ground every compiler-provided quote in the brief."""
    normalized_brief = _normalized_whitespace(brief_text)
    for rule in spec.rules:
        # Belt and braces: source_quote is mandatory in the model, so an
        # extraction without one has already been rejected by validation.
        if not rule.source_quote.strip():
            raise CompileError(
                f"Rule {rule.id} has no source quote. Every rule must cite the "
                f"sentence of the brief it came from."
            )
        if _normalized_whitespace(rule.source_quote) not in normalized_brief:
            raise CompileError(
                f"Rule {rule.id} cites text that does not occur in the supplied brief: "
                f"{rule.source_quote!r}"
            )
    for index, item in enumerate(spec.manual_review, start=1):
        if _normalized_whitespace(item.source_quote) not in normalized_brief:
            raise CompileError(
                f"Manual-review item {index} cites text that does not occur in the "
                f"supplied brief: {item.source_quote!r}"
            )
    return spec


def _normalized_whitespace(text: str) -> str:
    return " ".join(text.split())


def _client():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise CompileError(
            "ANTHROPIC_API_KEY is not set. The compiler needs it; `demo`, "
            "`verify` and `eval` do not."
        )

    try:
        import anthropic
    except ImportError as exc:
        raise CompileError(
            "The anthropic package is not installed. It is in requirements.txt "
            "but not requirements-demo.txt:  pip install -r requirements.txt"
        ) from exc

    # The explicit two-attempt loop above is the retry policy. Disable the
    # SDK's hidden automatic retries so "retry once" remains literally true.
    return anthropic.Anthropic(max_retries=0)


__all__ = [
    "compile_brief",
    "CompileError",
    "MODEL",
    "PROMPT_VERSION",
    "REQUEST_TIMEOUT_SECONDS",
]
