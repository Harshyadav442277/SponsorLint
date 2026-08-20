"""Promo codes spelled aloud. Architecture.md §5.1."""

import pytest

from sponsorlint.normalize import canonicalize
from sponsorlint.normalize.numbers import rewrite_number_words
from sponsorlint.normalize.text import normalize_text
from sponsorlint.normalize.codes import canonical_codes, looks_like_code, spoken_pattern


@pytest.mark.parametrize(
    "spoken",
    [
        "use code HARSH20 at checkout",
        "use code HARSH two zero at checkout",
        "use code H-A-R-S-H two zero at checkout",
        "use code h a r s h two oh at checkout",
    ],
)
def test_every_spoken_form_of_the_code_matches(spoken):
    pattern = spoken_pattern("HARSH20")
    # The code path searches the punctuation-normalized view, because folding
    # number words would turn "two zero" into 2.
    assert pattern.search(normalize_text(spoken)) or pattern.search(canonicalize(spoken))


def test_the_arithmetic_folder_still_does_not_produce_the_code():
    # This is why codes.py keeps its own per-digit map. The arithmetic folder
    # no longer sums "two zero" to 2, but it yields two separate numbers, which
    # is still not the code digits "20".
    assert rewrite_number_words("two zero") == "2 0"
    assert rewrite_number_words("harsh two zero") == "harsh 2 0"


@pytest.mark.parametrize(
    "spoken",
    [
        "use code HARSH21",
        "use code HARSH2",
        "use code HARSH200",
        "use code harsh twenty",
    ],
)
def test_wrong_code_does_not_match(spoken):
    assert not spoken_pattern("HARSH20").search(normalize_text(spoken))


def test_canonical_codes_folds_a_spelled_run():
    assert "HARSH20" in canonical_codes("use code H-A-R-S-H two zero at checkout")


def test_looks_like_code():
    assert looks_like_code("HARSH20")
    assert not looks_like_code("aegisvpn.com/alex")
    assert not looks_like_code("visit the link below")


@pytest.mark.parametrize("code", ["SAVE-20", "SAVE_20", "HARSH-20", "AEGIS-VPN1"])
def test_a_code_written_with_a_separator_is_still_a_code(code):
    # A code the gate turns away is handed to the prose path and fuzzy-matched,
    # which is exactly what lint/cta.py forbids for an identifier.
    assert looks_like_code(code)


@pytest.mark.parametrize(
    "phrase",
    ["well-known", "state-of-the-art", "sign-up", "two words", "vpn", "", "   "],
)
def test_prose_is_still_not_a_code(phrase):
    assert not looks_like_code(phrase)


@pytest.mark.parametrize(
    "spoken",
    ["use code save20", "use code save two zero", "use code s-a-v-e two zero"],
)
def test_a_separator_bearing_code_matches_every_spoken_form(spoken):
    pattern = spoken_pattern("SAVE-20")
    assert pattern.search(normalize_text(spoken)) or pattern.search(canonicalize(spoken))
