"""Brief -> clean text, and the four ways it can fail.

Every failure here has to arrive as an ExtractError carrying a next step the
user can act on, because this is the first thing that runs on an uploaded file
and a raw traceback at that point tells them nothing.
"""

from pathlib import Path

import pytest

from sponsorlint.brief.extract import ExtractError, _clean, extract_text

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


# -- accepted inputs --------------------------------------------------------


@pytest.mark.parametrize("suffix", [".md", ".txt", ".markdown", ""])
def test_text_briefs_are_read_directly(tmp_path, suffix):
    path = tmp_path / f"brief{suffix}"
    path.write_text("Mention Shield Mode by name.", encoding="utf-8")
    assert extract_text(path) == "Mention Shield Mode by name."


def test_the_sample_markdown_brief_extracts():
    assert "Aegis VPN" in extract_text(SAMPLES / "brief.md")


def test_undecodable_bytes_do_not_raise(tmp_path):
    # errors="replace" — a mis-encoded brief still reaches the compiler rather
    # than dying on a UnicodeDecodeError the user cannot act on.
    path = tmp_path / "latin1.md"
    path.write_bytes("Mention Café Mode.".encode("latin-1"))
    assert "Mention Caf" in extract_text(path)


# -- rejected inputs --------------------------------------------------------


def test_a_missing_file_names_the_path(tmp_path):
    with pytest.raises(ExtractError, match="does not exist"):
        extract_text(tmp_path / "nope.md")


@pytest.mark.parametrize("suffix", [".docx", ".rtf", ".pages", ".mp4"])
def test_an_unsupported_type_says_what_to_supply_instead(tmp_path, suffix):
    path = tmp_path / f"brief{suffix}"
    path.write_bytes(b"whatever")
    with pytest.raises(ExtractError, match="(?i)paste the brief text instead"):
        extract_text(path)


# -- the line-joining that source_quote depends on --------------------------


def test_hard_wrapped_lines_are_joined_into_sentences():
    # A brief exported to PDF wraps mid-sentence. A source_quote carrying a
    # line break will not match the prose shown beside it in the review screen.
    assert _clean("Mention the\nproduct name.") == "Mention the product name."


def test_paragraph_breaks_survive_the_join():
    assert _clean("First para\nwrapped.\n\nSecond para\nwrapped.") == (
        "First para wrapped.\n\nSecond para wrapped."
    )


@pytest.mark.parametrize("newline", ["\r\n", "\r"])
def test_windows_and_classic_mac_newlines_normalize(newline):
    assert _clean(f"one{newline}two") == "one two"


def test_runs_of_spaces_and_tabs_collapse():
    assert _clean("spaced   \t  out") == "spaced out"


def test_blank_input_cleans_to_empty():
    assert _clean("") == ""
    assert _clean("\n\n   \n\n") == ""


# -- pdf --------------------------------------------------------------------


def test_the_sample_pdf_brief_extracts():
    pytest.importorskip("pypdf")
    assert "Aegis VPN" in extract_text(SAMPLES / "brief.pdf")


def test_a_pdf_with_no_text_layer_is_reported_as_scanned(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    path = tmp_path / "scanned.pdf"
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)

    with pytest.raises(ExtractError, match="scanned image"):
        extract_text(path)


def test_an_unreadable_pdf_is_reported_rather_than_raised_raw(tmp_path):
    pytest.importorskip("pypdf")
    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"%PDF-1.4 this is not actually a pdf")

    with pytest.raises(ExtractError, match="(?i)corrupt\.pdf.*paste the brief text"):
        extract_text(path)
