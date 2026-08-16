"""Render samples/brief.md to samples/brief.pdf.

A build script, not part of the package. It hand-writes a minimal PDF rather
than adding a PDF-authoring dependency: `Rules.md` §2 treats every new package
as installation risk on a judge's machine, and this runs once.

    python tools/make_brief_pdf.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "samples" / "brief.md"
TARGET = ROOT / "samples" / "brief.pdf"

PAGE_W, PAGE_H = 612, 792
MARGIN = 64
LEADING = 15
WRAP = 84


#: The Helvetica WinAnsi encoding has no em/en dash, and a latin-1 "replace"
#: turns them into "?" in the extracted text. Fold them to a hyphen instead so
#: a compiled `source_quote` matches the prose shown beside it.
_SUBSTITUTIONS = {"—": "-", "–": "-", "‘": "'", "’": "'",
                  "“": '"', "”": '"', "…": "..."}


def escape(text: str) -> str:
    for src, dst in _SUBSTITUTIONS.items():
        text = text.replace(src, dst)
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def content_stream(lines: list[tuple[str, str, int]]) -> str:
    """lines: (text, font, size)."""
    out = ["BT", f"1 0 0 1 {MARGIN} {PAGE_H - MARGIN} Tm", f"{LEADING} TL"]
    current = None
    for text, font, size in lines:
        if (font, size) != current:
            out.append(f"/{font} {size} Tf")
            out.append(f"{size + 5} TL")
            current = (font, size)
        out.append(f"({escape(text)}) Tj")
        out.append("T*")
    out.append("ET")
    return "\n".join(out)


def layout(markdown: str) -> list[tuple[str, str, int]]:
    lines: list[tuple[str, str, int]] = []
    for index, raw in enumerate(markdown.strip().split("\n")):
        raw = raw.rstrip()
        if not raw:
            lines.append(("", "F2", 11))
            continue
        font, size = ("F1", 15) if index == 0 else ("F2", 11)
        for chunk in textwrap.wrap(raw, WRAP) or [""]:
            lines.append((chunk, font, size))
    return lines


def build(markdown: str) -> bytes:
    stream = content_stream(layout(markdown)).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /Contents 4 0 R >>"
        ).encode("latin-1"),
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n"
    ).encode()
    return bytes(pdf)


def main() -> None:
    TARGET.write_bytes(build(SOURCE.read_text(encoding="utf-8")))
    print(f"Wrote {TARGET.relative_to(ROOT)} ({TARGET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
