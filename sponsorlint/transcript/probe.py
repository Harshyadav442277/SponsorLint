"""ffprobe duration. Architecture.md §4.3.

This runs **upstream, at transcribe time**, and writes `duration_seconds` into
the transcript. Validators read it from there and never shell out — which is
what lets the zero-key demo run on a machine with no ffmpeg on PATH.
"""

from __future__ import annotations

import math
import subprocess
from pathlib import Path


class ProbeError(RuntimeError):
    pass


def probe_duration(path: Path) -> float:
    """Media duration in seconds, via ffprobe."""
    if not path.exists():
        raise ProbeError(f"Could not read {path} — the file does not exist.")

    try:
        completed = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise ProbeError(
            "ffprobe is not on PATH. Install ffmpeg to read media duration. "
            "Only `transcribe` needs it — `demo`, `verify` and `eval` do not."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(
            f"ffprobe timed out while reading {path.name}. The media may be corrupt."
        ) from exc

    if completed.returncode != 0:
        raise ProbeError(
            f"ffprobe could not read {path.name} — {completed.stderr.strip() or 'unknown error'}"
        )

    try:
        duration = float(completed.stdout.strip())
    except ValueError as exc:
        raise ProbeError(
            f"ffprobe returned no duration for {path.name}. The file may not contain audio."
        ) from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ProbeError(
            f"ffprobe returned an invalid duration for {path.name}. "
            "The file may be corrupt or may not contain audio."
        )
    return duration
