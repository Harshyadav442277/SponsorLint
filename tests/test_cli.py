"""CLI behavior that is easy to regress on Windows."""

from pathlib import Path

from sponsorlint import cli


class LegacyWindowsStream:
    """Small stdout stand-in that begins on the Windows CP-1252 codec."""

    def __init__(self) -> None:
        self.encoding = "cp1252"
        self.reconfigured_to = None
        self.parts: list[str] = []

    def reconfigure(self, *, encoding: str) -> None:
        self.encoding = encoding
        self.reconfigured_to = encoding

    def write(self, value: str) -> int:
        self.parts.append(value)
        return len(value)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False


def test_main_switches_legacy_windows_stdio_to_utf8(monkeypatch):
    stdout = LegacyWindowsStream()
    stderr = LegacyWindowsStream()
    monkeypatch.setattr(cli.sys, "platform", "win32")
    monkeypatch.setattr(cli.sys, "stdout", stdout)
    monkeypatch.setattr(cli.sys, "stderr", stderr)

    assert cli.main(["demo", "--arc"]) == 0
    assert stdout.reconfigured_to == "utf-8"
    assert stderr.reconfigured_to == "utf-8"


def test_compile_setup_error_is_readable(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    brief = Path(__file__).resolve().parents[1] / "samples" / "brief.pdf"

    assert cli.main(["compile", str(brief)]) == 2
    error = capsys.readouterr().err
    assert "ANTHROPIC_API_KEY is not set" in error
    assert "Traceback" not in error


def test_transcribe_missing_file_error_is_readable(tmp_path, capsys):
    missing = tmp_path / "missing.mp4"

    assert cli.main(["transcribe", str(missing)]) == 2
    error = capsys.readouterr().err
    assert "file does not exist" in error
    assert "Traceback" not in error
