"""Stage one of normalization: unicode, case, punctuation, whitespace.

Every later stage reads this one's output, so the set of characters it keeps is
load-bearing. `.` and `/` have to survive for URLs, `%` and `$` for values, `-`
for hyphenated numerals and spelled-out codes, and `'` so "today's sponsor is"
still matches the disclosure pattern.
"""

import pytest

from sponsorlint.normalize.text import collapse, normalize_text


@pytest.mark.parametrize("value", ["", "   ", "\t\n "])
def test_empty_and_blank_input_normalize_to_empty(value):
    assert normalize_text(value) == ""


def test_case_is_folded_and_whitespace_collapsed():
    assert normalize_text("  Aegis   VPN  ") == "aegis vpn"
    assert normalize_text("tabs\there\nand\nnewlines") == "tabs here and newlines"


def test_non_breaking_space_is_whitespace():
    # Briefs pasted out of a PDF are full of these.
    assert normalize_text("aegis\u00a0vpn") == "aegis vpn"


@pytest.mark.parametrize(
    "dash", ["\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2015", "\u2212"]
)
def test_every_dash_folds_to_a_plain_hyphen(dash):
    assert normalize_text(f"seventy{dash}three") == "seventy-three"


@pytest.mark.parametrize("quote", ["\u201c", "\u201d"])
def test_smart_double_quotes_are_dropped(quote):
    assert normalize_text(f"{quote}quoted{quote}") == "quoted"


@pytest.mark.parametrize("apostrophe", ["'", "\u2019", "\u2018", "\u201a", "\u2032"])
def test_apostrophes_survive_so_the_disclosure_pattern_still_matches(apostrophe):
    # disclosure.py matches r"\btoday's sponsor is\b" against normalized text.
    assert normalize_text(f"today{apostrophe}s sponsor is") == "today's sponsor is"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("save 73%!", "save 73%"),  # percent kept for values
        ("$20, please", "$20 please"),  # currency kept for values
        ("aegisvpn.com/alex", "aegisvpn.com/alex"),  # dot and slash kept for URLs
        ("seventy-three", "seventy-three"),  # hyphen kept for numerals and codes
    ],
)
def test_the_characters_later_stages_need_are_kept(text, expected):
    assert normalize_text(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Hello, World! (really?)", "hello world really"),
        ("50% off; use CODE", "50% off use code"),
        ("x=y", "x y"),
        ("a_b", "a b"),
    ],
)
def test_punctuation_no_stage_needs_becomes_a_separator(text, expected):
    # A separator, never a join: "x=y" must not collapse into the token "xy".
    assert normalize_text(text) == expected


def test_composed_and_decomposed_accents_compare_equal():
    assert normalize_text("caf\u00e9") == normalize_text("cafe\u0301")


def test_nfkc_folds_typographic_forms():
    assert normalize_text("\ufb01le") == "file"  # fi ligature


def test_normalization_is_idempotent():
    once = normalize_text("  “Aegis VPN” — save seventy-three percent!  ")
    assert normalize_text(once) == once


@pytest.mark.parametrize(
    "text,expected", [("  a   b  ", "a b"), ("", ""), ("a\t\nb", "a b")]
)
def test_collapse_only_touches_whitespace(text, expected):
    assert collapse(text) == expected


def test_collapse_preserves_case_and_punctuation():
    assert collapse("  Aegis, VPN!  ") == "Aegis, VPN!"
