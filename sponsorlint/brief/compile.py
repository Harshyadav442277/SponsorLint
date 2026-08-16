"""Brief text -> Spec. The only LLM call in the project. Architecture.md §9.

The model **proposes** the specification. The user owns it. Deterministic code
enforces the approved version. Nothing here ever sees a transcript.

Imported only from the `compile` command branch and web compile route — never at
module scope on the demo path.
"""

from __future__ import annotations

import os
import sys

from ..models import Spec
from .prompt import PROMPT_VERSION, build_prompt

MODEL = "gemini-3-flash-preview"
MAX_TOKENS = 16000
REQUEST_TIMEOUT_SECONDS = 60


class CompileError(RuntimeError):
    pass


def compile_brief(brief_text: str, *, model: str = MODEL, client=None) -> Spec:
    """Compile a sponsor brief into a proposed specification.

    Structured output is constrained by JSON Schema generated from `Spec`, then
    validated through the authoritative Pydantic model. One retry on a malformed
    or schema-violating response, then the error is surfaced — never a loop, and
    never a faked spec.
    """
    if not brief_text.strip():
        raise CompileError("The brief is empty — nothing to compile.")

    client = client or _client()
    prompt = build_prompt(brief_text)
    last_error: Exception | None = None

    for attempt in (1, 2):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=_generation_config(),
            )
            spec = _parsed_spec(response)
        except Exception as exc:  # noqa: BLE001 - surfaced below, never swallowed
            last_error = exc
            if attempt == 2 or _is_non_retryable_client_error(exc):
                retry_note = " after one retry" if attempt == 2 else ""
                raise CompileError(
                    "The compiler request or structured response failed"
                    f"{retry_note} — {_safe_error(exc)}"
                ) from exc
            _announce_retry()
            continue

        try:
            return _finalize(spec, brief_text)
        except CompileError as exc:
            last_error = exc
            if attempt == 2:
                raise
            _announce_retry()
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


def _generation_config():
    try:
        from google.genai import types
    except ImportError as exc:
        raise CompileError(
            "The google-genai package is not installed. It is in requirements.txt "
            "but not requirements-demo.txt:  pip install -r requirements.txt"
        ) from exc

    return types.GenerateContentConfig(
        response_mime_type="application/json",
        # `response_schema=Spec` maps Pydantic's `extra="forbid"` to an
        # OpenAPI field Gemini rejects. The SDK's JSON Schema path preserves
        # that constraint, and `_parsed_spec` still performs authoritative
        # Pydantic validation on the returned structure.
        response_json_schema=Spec.model_json_schema(),
        max_output_tokens=MAX_TOKENS,
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_SECONDS * 1000,
            # SponsorLint owns the explicit two-attempt policy. Disable the
            # SDK's default retries so one retry remains literally true.
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def _parsed_spec(response) -> Spec:
    parsed = getattr(response, "parsed", None)
    if parsed is None:
        raise CompileError("The model returned no valid structured output.")
    if isinstance(parsed, Spec):
        return parsed
    return Spec.model_validate(parsed)


def _announce_retry() -> None:
    print("Compiler response was invalid; retrying once.", file=sys.stderr)


def _safe_error(exc: Exception) -> str:
    message = str(exc)
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        message = message.replace(key, "[redacted]")
    return f"{type(exc).__name__}: {message}"


def _is_non_retryable_client_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    return isinstance(code, int) and 400 <= code < 500 and code not in (408, 429)


def _client():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise CompileError(
            "GEMINI_API_KEY is not set. The compiler needs it; `demo`, "
            "`verify` and `eval` do not."
        )

    try:
        from google import genai
    except ImportError as exc:
        raise CompileError(
            "The google-genai package is not installed. It is in requirements.txt "
            "but not requirements-demo.txt:  pip install -r requirements.txt"
        ) from exc

    return genai.Client(api_key=key)


__all__ = [
    "compile_brief",
    "CompileError",
    "MODEL",
    "PROMPT_VERSION",
    "REQUEST_TIMEOUT_SECONDS",
]
