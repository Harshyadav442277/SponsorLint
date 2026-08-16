"""ANSI terminal report. Design.md §7.

The CLI is a first-class surface: it is what `python -m sponsorlint demo`
shows, and what the README GIF captures.

Colour is dropped when stdout is not a TTY, so piped output and CI logs stay
readable and a README code block never contains escape sequences.
"""

from __future__ import annotations

import os
import sys
import textwrap

from ..lint.common import fmt_timecode
from ..models import Report, Result

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_STATUS_COLOR = {
    "FAIL": "\033[31m",
    "WARN": "\033[33m",
    "PASS": "\033[32m",
    "MANUAL_REVIEW": "\033[35m",
}

_STATUS_LABEL = {
    "FAIL": "FAIL",
    "WARN": "WARN",
    "PASS": "PASS",
    "MANUAL_REVIEW": "MANUAL",
}

_READINESS_COLOR = {
    "DO_NOT_SEND": "\033[31m",
    "REVIEW": "\033[33m",
    "SPONSOR_READY": "\033[32m",
}

_WIDTH = 62
_TITLE_WIDTH = 44


def _supports_color(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    if sys.platform == "win32":
        _enable_windows_ansi()
    return True


def _enable_windows_ansi() -> None:
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:  # noqa: BLE001 - colour is cosmetic, never fatal
        pass


class _Paint:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def __call__(self, text: str, *codes: str) -> str:
        if not self.enabled or not codes:
            return text
        return "".join(codes) + text + _RESET


def render(report: Report, stream=None) -> str:
    """Render the report as text. Returns it as well as writing it."""
    stream = stream or sys.stdout
    paint = _Paint(_supports_color(stream))
    lines: list[str] = []

    source = report.source or report.campaign or "sponsor segment"
    lines.append(f"SponsorLint — {source}")
    lines.append("")

    for result in report.results:
        lines.extend(_render_result(result, paint))

    for item in report.manual_review:
        label = "CONFIRMED" if item.confirmed else "MANUAL"
        color = _STATUS_COLOR["PASS"] if item.confirmed else _STATUS_COLOR["MANUAL_REVIEW"]
        lines.append(
            f"  {paint(label, color, _BOLD)}  {item.reason}"
        )
        lines.extend(_quote_block(item.source_quote, paint))
        if item.confirmed:
            lines.append("        Confirmed manually during spec review.")
        lines.append("")

    lines.append(paint("  " + "─" * _WIDTH, _DIM))
    lines.append(f"  {report.score.fraction} requirements passed")
    lines.append(f"  {_counts(report)}")
    lines.append("")

    verdict = paint(report.label, _READINESS_COLOR[report.status], _BOLD)
    lines.append(f"  {verdict}")
    lines.append("")

    text = "\n".join(lines)
    print(text, file=stream)
    return text


def _render_result(result: Result, paint: _Paint) -> list[str]:
    label = _STATUS_LABEL[result.status]
    color = _STATUS_COLOR[result.status]

    title = result.title
    if len(title) > _TITLE_WIDTH:
        title = title[: _TITLE_WIDTH - 1] + "…"

    head = f"  {paint(f'{label:<6}', color, _BOLD)}  {title:<{_TITLE_WIDTH}}"
    if result.timestamp is not None:
        head += paint(f"{fmt_timecode(result.timestamp):>7}", "\033[36m")
    else:
        head = head.rstrip()
    lines = [head]

    if result.expected:
        lines.append(f"        {paint('expected', _DIM)}  {result.expected}")
    if result.detected:
        lines.append(f"        {paint('detected', _DIM)}  {result.detected}")
    if result.evidence:
        lines.extend(_quote_block(result.evidence, paint, indent=8))
    if result.advisory:
        lines.append(f"        {paint(result.advisory, _DIM)}")
    if result.source_quote:
        quote = _shorten(result.source_quote, 58)
        source_line = f'from brief: "{quote}"'
        lines.append(f"        {paint(source_line, _DIM)}")

    lines.append("")
    return lines


def _quote_block(text: str, paint: _Paint, indent: int = 8) -> list[str]:
    pad = " " * indent
    wrapped = textwrap.wrap(f'"{text}"', width=_WIDTH - indent + 8) or [f'"{text}"']
    return [pad + line for line in wrapped]


def _shorten(text: str, width: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


def _counts(report: Report) -> str:
    s = report.summary
    parts = [f"{s.fail} failed"]
    if s.warn:
        parts.append(f"{s.warn} warning" + ("s" if s.warn != 1 else ""))
    parts.append(f"{s.passed} passed")
    if s.manual_review:
        parts.append(f"{s.manual_review} manual unresolved")
    if s.manual_confirmed:
        parts.append(f"{s.manual_confirmed} manual confirmed")
    return " · ".join(parts)
