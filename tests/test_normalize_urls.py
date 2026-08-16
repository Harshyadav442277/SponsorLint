"""All four spoken URL forms in Architecture.md §5.1."""

import pytest

from sponsorlint.normalize import canonicalize
from sponsorlint.normalize.urls import canonical_url, looks_like_url, spoken_pattern

URL = "aegisvpn.com/alex"


@pytest.mark.parametrize(
    "spoken",
    [
        "go to aegisvpn.com/alex today",
        "go to aegis vpn dot com slash alex today",
        "go to aegisvpn dot com slash alex today",
        "go to www.aegisvpn.com/alex today",
        "go to WWW.AegisVPN.com/Alex today",
        "go to https://aegisvpn.com/alex/ today",
    ],
)
def test_every_spoken_form_matches(spoken):
    assert spoken_pattern(URL).search(canonicalize(spoken))


@pytest.mark.parametrize(
    "spoken",
    [
        "go to aegisvpn.com/jordan today",
        "go to aegis.com/alex today",
        "just check the link in the description",
    ],
)
def test_wrong_url_does_not_match(spoken):
    assert not spoken_pattern(URL).search(canonicalize(spoken))


@pytest.mark.parametrize(
    "spoken",
    [
        "go to notaegisvpn.com/alex today",
        "go to aegisvpn.com/alexander today",
        "go to aegisvpn.com/alex2 today",
        "go to aegisvpn.com/alex.evil.com today",
        "go to aegisvpn.com/alex slash billing today",
    ],
)
def test_url_does_not_match_inside_a_longer_or_different_url(spoken):
    assert not spoken_pattern(URL).search(canonicalize(spoken))


def test_canonical_url_strips_scheme_www_and_trailing_slash():
    assert canonical_url("https://www.AegisVPN.com/alex/") == URL
    assert canonical_url("aegis vpn dot com slash alex") == URL


def test_looks_like_url():
    assert looks_like_url(URL)
    assert not looks_like_url("HARSH20")
    assert not looks_like_url("visit the link below")
