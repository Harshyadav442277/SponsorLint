"""CLI behavior that is easy to regress on Windows."""

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
