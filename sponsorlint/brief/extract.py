"""Brief -> clean text. PDF via pypdf, markdown and plain text directly.

Imported only from the `compile` command branch and web compile route.
"""

from __future__ import annotations

import re
from pathlib import Path


class ExtractError(RuntimeError):
    pass


def extract_text(path: Path) -> str:
    if not path.exists():
        raise ExtractError(f"Could not read {path} — the file does not exist.")

    if path.suffix.lower() == ".pdf":
        return _clean(_from_pdf(path))
    if path.suffix.lower() in (".md", ".txt", ".markdown", ""):
        return _clean(path.read_text(encoding="utf-8", errors="replace"))

    raise ExtractError(
        f"Cannot read {path.suffix or 'that file type'} briefs. "
        f"Supply a .pdf, .md or .txt file, or paste the brief text instead."
    )


def _from_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ExtractError(
            "pypdf is not installed. It is in requirements.txt but not "
            "requirements-demo.txt:  pip install -r requirements.txt"
        ) from exc

    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # noqa: BLE001
        raise ExtractError(
            f"Could not extract readable text from {path.name} — "
            f"{type(exc).__name__}: {exc}. Paste the brief text instead."
        ) from exc

    text = "\n".join(pages)
    if not text.strip():
        raise ExtractError(
            f"Could not extract readable text from {path.name} — the file "
            f"appears to be a scanned image. Paste the brief text instead."
        )
    return text


def _clean(text: str) -> str:
    """Join hard-wrapped lines into sentences so `source_quote` can span them.

    A brief exported to PDF wraps mid-sentence, and a quote that carries a line
    break will not match the prose shown beside it in the review screen.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    paragraphs = re.split(r"\n\s*\n", text)
    joined = [" ".join(line.strip() for line in p.split("\n") if line.strip())
              for p in paragraphs]
    return "\n\n".join(p for p in joined if p).strip()
