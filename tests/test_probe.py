"""Media probing must fail closed on corrupt or unbounded subprocess output."""

import subprocess
from types import SimpleNamespace

import pytest

from sponsorlint.transcript import probe
from sponsorlint.transcript.probe import ProbeError, probe_duration
from sponsorlint.models import Segment
from sponsorlint.transcript.transcribe import (
    TranscribeError,
    _bound_final_segment,
    _duration,
    _validated_transcript,
)


@pytest.mark.parametrize("output", ["nan", "inf", "0", "-2"])
def test_probe_rejects_nonfinite_or_nonpositive_duration(tmp_path, monkeypatch, output):
    media = tmp_path / "take.mp4"
    media.write_bytes(b"not real media")
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0, stdout=output, stderr=""
        ),
    )

    with pytest.raises(ProbeError, match="invalid duration"):
        probe_duration(media)


def test_probe_has_a_timeout_and_surfaces_it(tmp_path, monkeypatch):
    media = tmp_path / "take.mp4"
    media.write_bytes(b"not real media")

    def timeout(*_args, **kwargs):
        assert kwargs["timeout"] == 30
        raise subprocess.TimeoutExpired("ffprobe", kwargs["timeout"])

    monkeypatch.setattr(probe.subprocess, "run", timeout)
    with pytest.raises(ProbeError, match="timed out"):
        probe_duration(media)


@pytest.mark.parametrize("fallback", [float("nan"), float("inf"), 0, -1])
def test_decoder_fallback_duration_must_also_be_valid(tmp_path, monkeypatch, fallback):
    media = tmp_path / "take.mp4"
    media.write_bytes(b"not real media")
    monkeypatch.setattr(
        "sponsorlint.transcript.transcribe.probe_duration",
        lambda _path: (_ for _ in ()).throw(ProbeError("probe failed")),
    )

    with pytest.raises(TranscribeError, match="probe failed"):
        _duration(media, SimpleNamespace(duration=fallback))


def test_impossible_decoder_timeline_is_a_controlled_transcription_error():
    with pytest.raises(TranscribeError, match="invalid timestamps"):
        _validated_transcript(
            duration_seconds=1,
            segments=[Segment(start=0, end=2, text="speech")],
            source="take.mp4",
        )


def test_decoder_final_segment_is_bounded_to_media_duration():
    segments = [
        Segment(start=0, end=0.8, text="first"),
        Segment(start=0.8, end=7.4, text="last"),
    ]

    bounded = _bound_final_segment(segments, 1.0)

    assert bounded[0] == segments[0]
    assert bounded[1].start == 0.8
    assert bounded[1].end == 1.0
    assert segments[1].end == 7.4
