"""Every equivalence and non-equivalence in Architecture.md §5.1."""

import pytest

from sponsorlint.normalize import canonicalize
from sponsorlint.normalize.numbers import rewrite_number_words, value_pattern


def contains(value: str, text: str) -> bool:
    return bool(value_pattern(canonicalize(value)).search(canonicalize(text)))


@pytest.mark.parametrize(
    "text",
    [
        "save 73%",
        "save 73 percent",
        "save seventy-three percent",
        "save seventy three percent",
    ],
)
def test_all_spellings_of_73_percent_compare_equal(text):
    assert contains("73%", text)


@pytest.mark.parametrize("text", ["twenty dollars", "20 dollars", "$20"])
def test_all_spellings_of_20_dollars_compare_equal(text):
    assert contains("$20", text)


@pytest.mark.parametrize("text", ["three months free", "3 months free"])
def test_all_spellings_of_3_months_compare_equal(text):
    assert contains("3 months", text)


def test_70_does_not_equal_73():
    assert not contains("73%", "you can save up to seventy percent")


@pytest.mark.parametrize(
    "text",
    [
        "traffic grew one hundred and seventy three percent",  # 173%, leading digit
        "our support line is 730 4400",  # trailing digit
        "see chapter 173 for details",  # embedded
    ],
)
def test_boundary_guards_stop_partial_number_matches(text):
    assert not contains("73", text)
    assert not contains("73%", text)


@pytest.mark.parametrize(
    "text",
    ["73%", "73.0", "73.5", "$73", "73 dollars", "seventy third", "7 3"],
)
def test_unitless_value_does_not_match_a_different_numeric_shape(text):
    assert not contains("73", text)


def test_rewriter_is_idempotent_on_digits():
    assert rewrite_number_words("save 73 percent") == "save 73 percent"
    assert canonicalize("save 73%") == canonicalize("save seventy-three percent")


def test_compound_numbers_fold_correctly():
    assert rewrite_number_words("one hundred and twenty") == "120"
    assert rewrite_number_words("two thousand") == "2000"
    assert rewrite_number_words("nineteen") == "19"


def test_one_minute_and_thirty_seconds_is_not_the_normalizers_job():
    # The normalizer yields "1 minute and 30 seconds". Turning that into
    # min_seconds 60 / max_seconds 90 is semantic work the compiler does once.
    assert rewrite_number_words("one minute and thirty seconds") == "1 minute and 30 seconds"


def test_trailing_punctuation_survives_a_fold():
    assert rewrite_number_words("save seventy-three.") == "save 73."


@pytest.mark.parametrize(
    "text,expected",
    [
        ("nineteen ninety nine", "19 99"),  # a spoken price, not 118
        ("twenty twenty four", "20 24"),  # a spoken year, not 44
        ("nineteen eighty four", "19 84"),  # not 103
        ("three thirty", "3 30"),  # a time, not 33
        ("sixty sixty", "60 60"),  # not 120
        ("five five five", "5 5 5"),  # a spoken digit run, not 15
        ("ten ten", "10 10"),  # not 20
        ("two zero", "2 0"),  # the word2number defect, not folded to 2
    ],
)
def test_words_that_cannot_combine_do_not_sum_into_an_invented_number(text, expected):
    assert rewrite_number_words(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("seventy three", "73"),
        ("one hundred and twenty", "120"),
        ("one hundred twenty five", "125"),
        ("twenty five hundred", "2500"),
        ("nineteen hundred", "1900"),
        ("two thousand twenty four", "2024"),
        ("one million two hundred thousand", "1200000"),
        ("one hundred five", "105"),
    ],
)
def test_words_that_do_combine_still_fold_to_one_number(text, expected):
    assert rewrite_number_words(text) == expected


def test_a_spoken_year_no_longer_matches_a_value_nobody_said():
    # Before the run-splitting fix "nineteen ninety nine" canonicalized to 118,
    # so a brief requiring 118 passed against a transcript that never said it.
    assert not contains("118", "it launched in nineteen ninety nine")
    assert contains("99", "it launched in nineteen ninety nine")
