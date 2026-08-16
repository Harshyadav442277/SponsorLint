"""Command dispatch. Architecture.md §6.

Invocation is always `python -m sponsorlint <command>`, run from the repo root.
There is no pyproject.toml, no setup.py and no console script — the bare
`sponsorlint` form does not exist.

IMPORT DISCIPLINE — this is what makes the zero-key path work.

Module scope here may import only from `models`, `lint/`, `report/`,
`normalize/` and `eval/` — modules whose entire dependency set is in
`requirements-demo.txt`. `faster_whisper`, `pypdf` and the LLM client are
imported *inside the command branch that needs them*. A module-scope import of
any of them kills `demo` on a judge's machine before dispatch runs, and is
invisible on a dev machine that has them installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import EmptySpecError, Spec, Transcript

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = REPO_ROOT / "samples"

USAGE = """SponsorLint — pre-flight QA for sponsored YouTube integrations.

  python -m sponsorlint demo                    zero-key demo on the committed campaign
  python -m sponsorlint demo --arc              the DO NOT SEND -> SPONSOR READY arc
  python -m sponsorlint verify --spec S --transcript T
  python -m sponsorlint eval                    validator accuracy over labeled fixtures
  python -m sponsorlint compile BRIEF           brief -> proposed spec (needs an API key)
  python -m sponsorlint transcribe VIDEO        video -> transcript (needs ffmpeg)
  python -m sponsorlint analyze BRIEF VIDEO     the full flow
  python -m sponsorlint serve                   the web UI

Run from the repo root. `demo` and `eval` need no API key, no model download
and no ffmpeg."""


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------


class SponsorLintError(Exception):
    """A readable failure. Says what went wrong and how to fix it."""


def main(argv: list[str] | None = None) -> int:
    _configure_windows_stdio()
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0

    command, rest = argv[0], argv[1:]
    handlers = {
        "demo": _demo,
        "verify": _verify,
        "eval": _eval,
        "compile": _compile,
        "transcribe": _transcribe,
        "analyze": _analyze,
        "serve": _serve,
    }

    handler = handlers.get(command)
    if handler is None:
        print(f"Unknown command: {command}\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    try:
        return handler(rest)
    except EmptySpecError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except SponsorLintError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _configure_windows_stdio() -> None:
    """Keep the Unicode report readable on Windows' legacy code pages.

    Python still inherits CP-1252 in some Windows terminals and subprocess
    captures.  The report deliberately uses a box-drawing divider, which that
    codec cannot represent.  Reconfigure only the process-owned standard
    streams; test doubles such as ``StringIO`` do not expose ``reconfigure``
    and are left alone.
    """
    if sys.platform != "win32":
        return

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            # Encoding is presentation-only; it must never prevent a check.
            pass


# --------------------------------------------------------------------------
# demo — the zero-key path
# --------------------------------------------------------------------------


def _demo(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m sponsorlint demo")
    parser.add_argument("--v3", action="store_true", help="run the corrected take")
    parser.add_argument("--arc", action="store_true", help="run V1 then V3")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args(argv)

    from .lint.engine import run
    from .report.terminal import render

    spec = _load_spec(SAMPLES / "spec.approved.json")

    takes = ["v1", "v3"] if args.arc else (["v3"] if args.v3 else ["v1"])
    reports = []
    for take in takes:
        transcript = _load_transcript(SAMPLES / f"transcript.{take}.json")
        report = run(spec, transcript)
        reports.append((take, report))
        if args.json:
            print(json.dumps(report.model_dump(by_alias=True), indent=2))
        else:
            render(report)

    if args.arc and not args.json:
        print("  " + "─" * 62)
        for take, report in reports:
            print(f"  {take.upper():<4} {report.score.fraction} requirements passed"
                  f"      {report.label}")
        print()

    return 0


# --------------------------------------------------------------------------
# verify — deterministic checks only
# --------------------------------------------------------------------------


def _verify(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m sponsorlint verify")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    from .lint.engine import run
    from .report.terminal import render

    report = run(_load_spec(Path(args.spec)), _load_transcript(Path(args.transcript)))

    if args.json:
        print(json.dumps(report.model_dump(by_alias=True), indent=2))
    else:
        render(report)

    # Linter semantics: a blocking failure is a non-zero exit.
    return 1 if report.status == "DO_NOT_SEND" else 0


# --------------------------------------------------------------------------
# eval — validator metrics
# --------------------------------------------------------------------------


def _eval(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m sponsorlint eval")
    parser.add_argument("--verbose", action="store_true", help="list every case")
    args = parser.parse_args(argv)

    from .eval.runner import run_eval

    run_eval(verbose=args.verbose)
    return 0  # metrics are reported, never enforced as a gate


# --------------------------------------------------------------------------
# compile — the only LLM call
# --------------------------------------------------------------------------


def _compile(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m sponsorlint compile")
    parser.add_argument("brief")
    parser.add_argument("-o", "--out", help="write the proposed spec here")
    args = parser.parse_args(argv)

    from .brief.compile import CompileError, compile_brief  # LLM client imported here
    from .brief.extract import ExtractError, extract_text  # pypdf imported here

    try:
        text = extract_text(Path(args.brief))
        spec = compile_brief(text)
    except (CompileError, ExtractError) as exc:
        raise SponsorLintError(str(exc)) from exc
    payload = json.dumps(spec.model_dump(exclude_none=True), indent=2)

    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"Wrote {args.out} — {len(spec.rules)} rules, "
              f"{len(spec.manual_review)} for manual review.")
        print("Review it before verifying: the spec is yours, not the model's.")
    else:
        print(payload)
    return 0


# --------------------------------------------------------------------------
# transcribe — faster-whisper + ffprobe
# --------------------------------------------------------------------------


def _transcribe(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m sponsorlint transcribe")
    parser.add_argument("video")
    parser.add_argument("-o", "--out", help="write the transcript here")
    parser.add_argument("--model", default="base.en")
    args = parser.parse_args(argv)

    from .transcript.transcribe import TranscribeError, transcribe  # faster-whisper imported here

    try:
        transcript = transcribe(Path(args.video), model_size=args.model)
    except TranscribeError as exc:
        raise SponsorLintError(str(exc)) from exc
    payload = json.dumps(transcript.model_dump(), indent=2)

    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"Wrote {args.out} — {len(transcript.segments)} segments, "
              f"{transcript.duration_seconds:.1f}s.")
    else:
        print(payload)
    return 0


# --------------------------------------------------------------------------
# analyze — the full flow
# --------------------------------------------------------------------------


def _analyze(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m sponsorlint analyze")
    parser.add_argument("brief")
    parser.add_argument("video")
    parser.add_argument("--model", default="base.en")
    parser.add_argument("--yes", action="store_true",
                        help="skip the spec review step (not recommended)")
    args = parser.parse_args(argv)

    from .brief.compile import CompileError, compile_brief
    from .brief.extract import ExtractError, extract_text
    from .lint.engine import run
    from .report.terminal import render
    from .transcript.transcribe import TranscribeError, transcribe

    print("· Extracting brief text")
    try:
        text = extract_text(Path(args.brief))
    except ExtractError as exc:
        raise SponsorLintError(str(exc)) from exc

    print("· Compiling requirements")
    try:
        spec = compile_brief(text)
    except CompileError as exc:
        raise SponsorLintError(str(exc)) from exc

    blockers = spec.approval_blockers()
    if blockers and not args.yes:
        print("\nThis spec is not approvable yet — the compiler needs your input:\n")
        for blocker in blockers:
            print(f"  · {blocker}")
        print("\nOpen the review screen to resolve it:  python -m sponsorlint serve")
        print("Or re-run with --yes to check only the rules that are complete.")
        return 2

    print("· Transcribing sponsor segment")
    try:
        transcript = transcribe(Path(args.video), model_size=args.model)
    except TranscribeError as exc:
        raise SponsorLintError(str(exc)) from exc

    print("· Running checks\n")
    report = run(spec, transcript)
    render(report)
    return 1 if report.status == "DO_NOT_SEND" else 0


# --------------------------------------------------------------------------
# serve — the web UI
# --------------------------------------------------------------------------


def _serve(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m sponsorlint serve")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    import uvicorn

    print(f"SponsorLint UI on http://{args.host}:{args.port}")
    uvicorn.run("sponsorlint.web.app:app", host=args.host, port=args.port, log_level="warning")
    return 0


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------


def _read_json(path: Path, what: str) -> dict:
    if not path.exists():
        raise SponsorLintError(
            f"Could not read the {what}: {path} does not exist. "
            f"Run documented commands from the repo root."
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SponsorLintError(f"{path} is not valid JSON — {exc}") from exc


def _load_spec(path: Path) -> Spec:
    from pydantic import ValidationError

    try:
        return Spec.model_validate(_read_json(path, "spec"))
    except ValidationError as exc:
        raise SponsorLintError(f"{path} is not a valid specification:\n{exc}") from exc


def _load_transcript(path: Path) -> Transcript:
    from pydantic import ValidationError

    try:
        return Transcript.model_validate(_read_json(path, "transcript"))
    except ValidationError as exc:
        raise SponsorLintError(f"{path} is not a valid transcript:\n{exc}") from exc
