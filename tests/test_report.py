"""Report HTML may mark evidence but may never trust transcript markup."""

from sponsorlint.report.render import highlight


def test_evidence_highlighting_escapes_active_html():
    rendered = highlight('<img src=x onerror="alert(1)"> Shield Mode', "Shield Mode")

    assert "<img" not in rendered
    assert "onerror=\"" not in rendered
    assert "&lt;img" in rendered
    assert "<mark>Shield Mode</mark>" in rendered
