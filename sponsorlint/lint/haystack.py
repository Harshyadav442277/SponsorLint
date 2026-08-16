"""The searchable transcript. Architecture.md §5.2.

**Always the joined transcript, never per segment.** A required phrase routinely
straddles a Whisper segment break: for segments "definitely try shield" /
"mode when you sign up.", the best per-segment score for "shield mode" is 70.6
(FAIL) while the joined text scores 100.0 (PASS). A per-segment loop is a false
FAIL that depends on where Whisper happened to cut.

Two views are kept over the same segments:

    numeric   number-words folded to digits — phrases and exact values
    plain     punctuation-normalized only   — spelled-aloud codes, where
              folding "two zero" to 2 would destroy the code

Each view carries its own offset map so a hit resolves back to a segment, and
therefore to a timestamp and a line of raw evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rapidfuzz import fuzz
from rapidfuzz.distance import DamerauLevenshtein

from ..models import Transcript
from ..normalize import canonicalize, normalize_text

#: rapidfuzz partial_ratio threshold. Measured in Architecture.md §5.2: the
#: worst true-negative margin is 83.3, leaving 6.7 points of headroom. Do not
#: move it in either direction (Rules.md §1.5).
FUZZY_THRESHOLD = 90.0

#: partial_ratio("vpn", <any transcript containing v...p...n>) is 100.0. Short
#: needles are matched exactly, never fuzzed.
FUZZY_MIN_CHARS = 8


@dataclass(frozen=True)
class Hit:
    """A match, resolved back to the segment it started in."""

    segment_index: int
    start: float
    end: float
    evidence: str
    matched: str


class Haystack:
    """Joined, normalized transcript with an offset -> segment map."""

    def __init__(self, transcript: Transcript) -> None:
        self._segments = transcript.segments
        self.numeric, self._numeric_spans = self._build(canonicalize)
        self.plain, self._plain_spans = self._build(normalize_text)

    def _build(self, fn) -> tuple[str, list[tuple[int, int, int]]]:
        parts: list[str] = []
        spans: list[tuple[int, int, int]] = []
        offset = 0
        for index, segment in enumerate(self._segments):
            text = fn(segment.text)
            if not text:
                continue
            parts.append(text)
            spans.append((offset, offset + len(text), index))
            offset += len(text) + 1  # the joining space
        return " ".join(parts), spans

    # -- resolution ---------------------------------------------------------

    def _hit(self, offset: int, matched: str, spans) -> Hit | None:
        for start, end, index in spans:
            if start <= offset < end:
                segment = self._segments[index]
                return Hit(
                    segment_index=index,
                    start=segment.start,
                    end=segment.end,
                    evidence=segment.text.strip(),
                    matched=matched,
                )
        # Offset landed on a joining space; attribute it to the next segment.
        for start, _end, index in spans:
            if start >= offset:
                segment = self._segments[index]
                return Hit(
                    segment_index=index,
                    start=segment.start,
                    end=segment.end,
                    evidence=segment.text.strip(),
                    matched=matched,
                )
        return None

    def _views(self):
        return (("numeric", self.numeric, self._numeric_spans),
                ("plain", self.plain, self._plain_spans))

    # -- search -------------------------------------------------------------

    def search(self, pattern: re.Pattern[str], view: str = "numeric") -> Hit | None:
        for name, text, spans in self._views():
            if name != view:
                continue
            match = pattern.search(text)
            if match:
                return self._hit(match.start(), match.group(0), spans)
        return None

    def search_all(self, pattern: re.Pattern[str], view: str = "numeric") -> list[Hit]:
        for name, text, spans in self._views():
            if name != view:
                continue
            hits = [self._hit(m.start(), m.group(0), spans) for m in pattern.finditer(text)]
            return [h for h in hits if h is not None]
        return []

    def search_any_view(self, pattern: re.Pattern[str]) -> Hit | None:
        """Try every view. Both are exact matches, so this cannot invent a hit."""
        for _name, text, spans in self._views():
            match = pattern.search(text)
            if match:
                return self._hit(match.start(), match.group(0), spans)
        return None

    def search_all_any_view(self, pattern: re.Pattern[str]) -> list[Hit]:
        """Return exact hits from both views, deduplicated by segment/time/text."""
        hits: list[Hit] = []
        seen: set[tuple[int, float, str]] = set()
        for _name, text, spans in self._views():
            for match in pattern.finditer(text):
                hit = self._hit(match.start(), match.group(0), spans)
                if hit is None:
                    continue
                key = (hit.segment_index, hit.start, hit.matched)
                if key not in seen:
                    seen.add(key)
                    hits.append(hit)
        return hits

    def hit_at(self, offset: int, matched: str, view: str = "numeric") -> Hit | None:
        """Resolve a known match offset back to its transcript segment."""
        spans = self._numeric_spans if view == "numeric" else self._plain_spans
        return self._hit(offset, matched, spans)

    def contains(self, needle: str, view: str = "numeric") -> Hit | None:
        """Normalized exact containment, guarded by word boundaries.

        This runs first on every phrase rule. Fuzzy is only ever the fallback.
        """
        if not needle:
            return None
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])")
        return self.search(pattern, view=view)

    def contains_all(self, needle: str, view: str = "numeric") -> list[Hit]:
        if not needle:
            return []
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])")
        return self.search_all(pattern, view=view)

    def best_fuzzy(
        self, needle: str, *, allow_truncation: bool = False
    ) -> tuple[float, Hit | None]:
        """`fuzz.partial_ratio` against the joined transcript.

        Never `fuzz.ratio` (whole-string; scores true matches 10-67, so nothing
        could pass at threshold 90) and never `partial_token_set_ratio`
        (returns 100.0 on both documented hard negatives).
        """
        if not needle or not self.numeric:
            return 0.0, None

        alignment = fuzz.partial_ratio_alignment(needle, self.numeric)
        if alignment is None:
            return 0.0, None

        # Score complete token windows instead of accepting partial_ratio's
        # single global alignment. This avoids a bad prefix hit masking a later
        # valid Whisper typo in the same transcript.
        token_count = len(re.findall(r"[a-z0-9]+", needle))
        tokens = list(re.finditer(r"[a-z0-9]+", self.numeric))
        best_score = 0.0
        best_hit = None
        for index in range(0, len(tokens) - token_count + 1):
            group = tokens[index : index + token_count]
            start, end = group[0].start(), group[-1].end()
            window = self.numeric[start:end]
            if not _tokens_are_transcription_neighbours(
                needle, window, allow_truncation=allow_truncation
            ):
                continue
            score = float(fuzz.partial_ratio(needle, window))
            if score > best_score:
                best_score = score
                best_hit = self._hit(start, window, self._numeric_spans)

        if best_hit is not None:
            return best_score, best_hit
        return float(alignment.score), None


def _tokens_are_transcription_neighbours(
    needle: str, window: str, *, allow_truncation: bool
) -> bool:
    expected = re.findall(r"[a-z0-9]+", needle)
    detected = re.findall(r"[a-z0-9]+", window)
    if len(expected) != len(detected):
        return False

    for left, right in zip(expected, detected):
        if left == right:
            continue
        if min(len(left), len(right)) < 4:
            return False
        if DamerauLevenshtein.distance(left, right) != 1:
            return False
        if len(left) == len(right):
            # Preserve an adjacent transposition such as shield -> sheild,
            # while rejecting same-length substitutions such as mode -> node.
            if sorted(left) != sorted(right):
                return False
            continue
        # A missing final character is useful only when routing a prohibited
        # near-match to MANUAL_REVIEW. Required mentions never get this looser
        # treatment, and added suffixes are always rejected.
        if not allow_truncation or len(right) != len(left) - 1:
            return False
    return True
