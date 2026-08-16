"""faster-whisper wrapper. `base.en`, CPU, no GPU code path.

Imported only from the `transcribe` command branch and web upload route — never at
module scope on the demo path.

Transcribe once, cache forever: the resulting JSON is the fixture every
downstream test and the zero-key demo run against.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ..models import Segment, Transcript
from .probe import ProbeError, probe_duration


class TranscribeError(RuntimeError):
    pass


def transcribe(path: Path, model_size: str = "base.en") -> Transcript:
    """Transcribe a sponsor segment into timestamped segments."""
    if not path.exists():
        raise TranscribeError(f"Could not read {path} — the file does not exist.")

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise TranscribeError(
            "faster-whisper is not installed. It is in requirements.txt but not "
            "requirements-demo.txt:  pip install -r requirements.txt"
        ) from exc

    try:
        # CPU only. No CUDA detection, no GPU wheels, no second code path —
        # it buys nothing on a 75-second clip.
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        raw_segments, info = model.transcribe(str(path), vad_filter=True)
        segments = [
            Segment(start=round(s.start, 2), end=round(s.end, 2), text=s.text.strip())
            for s in raw_segments
            if s.text.strip()
        ]
    except Exception as exc:  # noqa: BLE001 - surfaced, never swallowed
        raise TranscribeError(
            f"Could not transcribe {path.name} — {type(exc).__name__}: {exc}"
        ) from exc

    if not segments:
        raise TranscribeError(
            f"Could not transcribe {path.name} — no speech was detected."
        )

    return Transcript(
        duration_seconds=_duration(path, info),
        segments=segments,
        source=path.name,
    )


def _duration(path: Path, info) -> float:
    """ffprobe is the source of truth. When it is unavailable, fall back to the
    duration faster-whisper reports from its own decode — and say so, rather
    than continuing quietly."""
    try:
        return round(probe_duration(path), 2)
    except ProbeError as exc:
        fallback = round(float(getattr(info, "duration", 0.0)), 2)
        if not fallback:
            raise TranscribeError(str(exc)) from exc
        print(f"  note: {exc}", file=sys.stderr)
        print(f"  note: using the decoder's own duration instead ({fallback}s).",
              file=sys.stderr)
        return fallback
