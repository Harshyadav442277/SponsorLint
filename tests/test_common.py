"""The shared formatting helpers behind every report surface.

`fmt_timecode` is the single site the terminal report, the HTML report and the
disclosure advisory all format through, so its edge cases are worth pinning.
"""

import pytest

from sponsorlint.lint.common import fmt_seconds, fmt_timecode, quoted, uncapitalize


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (0, "00:00"),
        (7, "00:07"),
        (74.2, "01:14"),
        (599.9, "09:59"),
        (3599, "59:59"),
    ],
)
def test_timecode_under_an_hour_stays_minutes_and_seconds(seconds, expected):
    assert fmt_timecode(seconds) == expected


@pytest.mark.parametrize(
    "seconds,expected",
    [
        (3600, "1:00:00"),
        (3725, "1:02:05"),  # not "62:05"
        (7384, "2:03:04"),
    ],
)
def test_timecode_past_an_hour_shows_the_hour(seconds, expected):
    assert fmt_timecode(seconds) == expected


def test_timecode_fits_the_terminal_report_column():
    # report/terminal.py right-aligns the timecode in seven characters.
    assert len(fmt_timecode(7384)) <= 7


def test_a_missing_timestamp_renders_as_a_placeholder():
    assert fmt_timecode(None) == "--:--"


@pytest.mark.parametrize("seconds", [-1, -0.5, -3600])
def test_a_negative_timestamp_clamps_to_zero(seconds):
    assert fmt_timecode(seconds) == "00:00"


@pytest.mark.parametrize(
    "seconds,expected", [(30, "30s"), (90.0, "90s"), (7.5, "7.5s"), (0, "0s")]
)
def test_durations_render_without_trailing_zeros(seconds, expected):
    assert fmt_seconds(seconds) == expected


def test_quoted_wraps_in_double_quotes():
    assert quoted("Shield Mode") == '"Shield Mode"'


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Campaign discount", "campaign discount"),
        ("Campaign URL", "campaign URL"),  # only the first letter is touched
        ("", ""),
        ("A", "a"),
    ],
)
def test_uncapitalize_lowers_only_the_first_character(text, expected):
    assert uncapitalize(text) == expected
