"""The searchable transcript: two views, one offset map, and the fuzzy gate.

Haystack decides what "found" means for every validator, and until now it was
only tested through them. These cover it directly.
"""

import re

import pytest

from sponsorlint.lint.haystack import FUZZY_THRESHOLD, Haystack
from sponsorlint.models import Transcript
from sponsorlint.normalize import canonicalize


def haystack(*pairs, duration: float = 120.0) -> Haystack:
    segments = [{"start": start, "end": start + 3.0, "text": text} for start, text in pairs]
    return Haystack(Transcript(duration_seconds=duration, segments=segments))


# -- the joined transcript --------------------------------------------------


def test_a_phrase_straddling_a_segment_break_is_found():
    # The module's headline claim: per segment, the best score for "shield
    # mode" across this break is 70.6 and the rule fails on where Whisper
    # happened to cut. Joined, it is an exact match.
    hay = haystack((0.0, "definitely try shield"), (4.0, "mode when you sign up."))
    hit = hay.contains(canonicalize("shield mode"))
    assert hit is not None
    assert hit.matched == "shield mode"


def test_a_straddling_hit_resolves_to_the_segment_it_starts_in():
    hay = haystack((0.0, "definitely try shield"), (4.0, "mode when you sign up."))
    hit = hay.contains(canonicalize("shield mode"))
    assert hit.segment_index == 0
    assert hit.start == 0.0
    assert hit.evidence == "definitely try shield"


def test_a_hit_carries_the_raw_segment_text_as_evidence():
    hay = haystack((0.0, "Save 73% with Aegis VPN."))
    hit = hay.contains("73%")
    # Evidence is the untouched line, not the normalized haystack.
    assert hit.evidence == "Save 73% with Aegis VPN."


def test_an_empty_transcript_yields_no_hits():
    hay = Haystack(Transcript(duration_seconds=10.0, segments=[]))
    assert hay.numeric == ""
    assert hay.contains("anything") is None
    assert hay.best_fuzzy("anything at all") == (0.0, None)


# -- the two views ----------------------------------------------------------


def test_the_numeric_view_folds_number_words_and_the_plain_view_does_not():
    hay = haystack((0.0, "use code HARSH two zero today"))
    assert "2 0" in hay.numeric
    assert "two zero" in hay.plain


def test_a_spelled_code_is_reachable_through_the_plain_view_only():
    hay = haystack((0.0, "use code HARSH two zero today"))
    pattern = re.compile(r"harsh two zero")
    assert hay.search(pattern, view="numeric") is None
    assert hay.search(pattern, view="plain") is not None
    assert hay.search_any_view(pattern) is not None


def test_search_all_any_view_deduplicates_a_hit_both_views_share():
    # "shield mode" contains no numerals, so both views hold it identically.
    hay = haystack((0.0, "shield mode is on"))
    hits = hay.search_all_any_view(re.compile(r"shield mode"))
    assert len(hits) == 1


def test_search_all_returns_every_occurrence_in_order():
    hay = haystack((0.0, "save 73% today"), (10.0, "again 73% tomorrow"))
    hits = hay.search_all(re.compile(r"73%"))
    assert [h.segment_index for h in hits] == [0, 1]
    assert [h.start for h in hits] == [0.0, 10.0]


# -- containment guards -----------------------------------------------------


def test_containment_is_guarded_by_word_boundaries():
    # The substring trap must_not_say.py depends on: a rule prohibiting
    # "anonymous" must not fire on "anonymously".
    hay = haystack((0.0, "we keep you anonymously safe"))
    assert hay.contains("anonymous") is None
    assert hay.contains("anonymously") is not None


@pytest.mark.parametrize("needle", ["", None])
def test_an_empty_needle_never_matches(needle):
    hay = haystack((0.0, "anything at all"))
    assert hay.contains(needle or "") is None
    assert hay.contains_all(needle or "") == []


# -- the fuzzy gate ---------------------------------------------------------


def test_a_transcription_transposition_is_accepted():
    hay = haystack((0.0, "definitely try sheild mode now"))
    score, hit = hay.best_fuzzy("shield mode")
    assert score >= FUZZY_THRESHOLD
    assert hit is not None
    assert hit.matched == "sheild mode"


def test_a_same_length_substitution_is_rejected_despite_a_passing_score():
    # "mode" -> "node" is a different word, not a transcription slip. The
    # alignment score still clears the threshold, so the hit being None is the
    # only thing stopping a false PASS — every caller checks it.
    hay = haystack((0.0, "definitely try shield node now"))
    score, hit = hay.best_fuzzy("shield mode")
    assert score >= FUZZY_THRESHOLD
    assert hit is None


def test_a_dropped_final_character_needs_truncation_to_be_allowed():
    hay = haystack((0.0, "it is completely anonymou here"))
    assert hay.best_fuzzy("completely anonymous")[1] is None
    score, hit = hay.best_fuzzy("completely anonymous", allow_truncation=True)
    assert score >= FUZZY_THRESHOLD
    assert hit is not None


def test_a_differing_token_count_never_matches():
    hay = haystack((0.0, "shield is the mode we use"))
    assert hay.best_fuzzy("shield mode")[1] is None
