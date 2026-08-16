"""faster-whisper wrapper. `base.en`, CPU, no GPU code path.

Imported only from the `transcribe` command branch and web upload route — never at
module scope on the demo path.

Transcribe once, cache forever: the resulting JSON is the fixture every
downstream test and the zero-key demo run against.
"""

from __future__ import annotations

import logging
import math
import sys
import threading
from pathlib import Path

from pydantic import ValidationError

from ..models import Segment, Transcript
from .probe import ProbeError, probe_duration


class TranscribeError(RuntimeError):
    pass


LOGGER = logging.getLogger("uvicorn.error")
_MODEL_CACHE: dict[str, object] = {}
_MODEL_CACHE_LOCK = threading.Lock()


def _whisper_model(model_size: str):
    """Lazily load and reuse one CPU model per size in this process."""
    cached = _MODEL_CACHE.get(model_size)
    if cached is not None:
        return cached

    with _MODEL_CACHE_LOCK:
        cached = _MODEL_CACHE.get(model_size)
        if cached is not None:
            return cached

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscribeError(
                "faster-whisper is not installed. It is in requirements.txt but not "
                "requirements-demo.txt:  pip install -r requirements.txt"
            ) from exc

        LOGGER.info("loading Whisper model")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        _MODEL_CACHE[model_size] = model
        LOGGER.info("Whisper model ready")
        return model


def transcribe(path: Path, model_size: str = "base.en") -> Transcript:
    """Transcribe a sponsor segment into timestamped segments."""
    if not path.exists():
        raise TranscribeError(f"Could not read {path} — the file does not exist.")

    try:
        # CPU only. No CUDA detection, no GPU wheels, no second code path —
        # it buys nothing on a 75-second clip.
        model = _whisper_model(model_size)
        LOGGER.info("transcription started")
        raw_segments, info = model.transcribe(str(path), vad_filter=True)
        segments = [
            Segment(start=round(s.start, 2), end=round(s.end, 2), text=s.text.strip())
            for s in raw_segments
            if s.text.strip()
        ]
        LOGGER.info("transcription completed")
    except TranscribeError:
        raise
    except Exception as exc:  # noqa: BLE001 - surfaced, never swallowed
        raise TranscribeError(
            f"Could not transcribe {path.name} — {type(exc).__name__}: {exc}"
        ) from exc

    if not segments:
        raise TranscribeError(
            f"Could not transcribe {path.name} — no speech was detected."
        )

    duration_seconds = _duration(path, info)
    return _validated_transcript(
        duration_seconds=duration_seconds,
        segments=_bound_final_segment(segments, duration_seconds),
        source=path.name,
    )


def _bound_final_segment(
    segments: list[Segment], duration_seconds: float
) -> list[Segment]:
    """Clamp faster-whisper's padded final timestamp to the media boundary.

    The decoder can assign the final spoken segment an end timestamp beyond the
    container duration while its start remains inside the media. Only that
    narrow final-segment shape is corrected; every other impossible timeline
    still reaches the strict Transcript validator and fails closed.
    """
    last = segments[-1]
    if last.start < duration_seconds < last.end:
        return [*segments[:-1], last.model_copy(update={"end": duration_seconds})]
    return segments


def _validated_transcript(
    *, duration_seconds: float, segments: list[Segment], source: str
) -> Transcript:
    """Turn impossible decoder timelines into a controlled media error."""
    try:
        return Transcript(
            duration_seconds=duration_seconds,
            segments=segments,
            source=source,
        )
    except ValidationError as exc:
        raise TranscribeError(
            f"Could not transcribe {source} — decoder returned invalid timestamps: {exc}"
        ) from exc


def _duration(path: Path, info) -> float:
    """ffprobe is the source of truth. When it is unavailable, fall back to the
    duration faster-whisper reports from its own decode — and say so, rather
    than continuing quietly."""
    try:
        return round(probe_duration(path), 2)
    except ProbeError as exc:
        fallback = round(float(getattr(info, "duration", 0.0)), 2)
        if not math.isfinite(fallback) or fallback <= 0:
            raise TranscribeError(str(exc)) from exc
        print(f"  note: {exc}", file=sys.stderr)
        print(f"  note: using the decoder's own duration instead ({fallback}s).",
              file=sys.stderr)
        return fallback
