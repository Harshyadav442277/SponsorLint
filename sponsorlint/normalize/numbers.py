"""Spoken numerals, currency, percent. Architecture.md §5.1.

Whisper emits digits sometimes and words other times, unpredictably, within the
same transcript. Both must compare equal, so we rewrite number-words to digits
*in place* and then test membership. The rewriter is idempotent on text that
already contains digits, which is exactly what makes both Whisper styles work.

`word2number` was tested and rejected: it raises on "save 73 percent", returns
31 for "one minute and thirty seconds", folds "two zero" to 2, and returns only
one number per string. This is a run-scanner instead, and adds no dependency.

A run is bounded twice over. `_may_follow` stops it at a word that cannot
continue the number, and a full stop stops it at the end of a sentence. Both
guards exist for the same reason: a run that keeps going past its number
reports a value nobody said.
"""

from __future__ import annotations

import re

UNITS: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}

TENS: dict[str, int] = {
    "twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

SCALES: dict[str, int] = {
    "hundred": 100,
    "thousand": 1_000,
    "million": 1_000_000,
    "billion": 1_000_000_000,
}

_NUMBER_WORDS = frozenset(UNITS) | frozenset(TENS) | frozenset(SCALES)

#: Trailing characters `normalize_text` preserves, re-attached after a fold so
#: "seventy-three percent." keeps its full stop.
_TRAIL = ".%$/'-"

_HYPHEN_BETWEEN_LETTERS = re.compile(r"(?<=[a-z])-(?=[a-z])")

#: What may legally precede each class of number-word inside one spoken number.
#:
#: Without this table a run of adjacent number-words is summed no matter whether
#: the words can actually combine, and the sum is a value nobody said:
#:
#:     "nineteen ninety nine"  ->  118      (19 + 90 + 9)
#:     "twenty twenty four"    ->  44       (20 + 20 + 4)
#:     "three thirty"          ->  33       (3 + 30)
#:
#: Inventing a number is the one thing this stage must never do (Rules.md §1.6).
#: A word that cannot continue the current number closes it and starts the next
#: one instead, so those three read 19 99, 20 24 and 3 30 — separate numbers,
#: none of them fabricated.
_MAY_FOLLOW: dict[str, frozenset] = {
    "unit": frozenset({None, "tens", "hundred", "scale"}),
    "teen": frozenset({None, "hundred", "scale"}),
    "zero": frozenset({None}),
    "tens": frozenset({None, "hundred", "scale"}),
    "hundred": frozenset({None, "unit", "teen", "tens"}),
    "scale": frozenset({None, "unit", "teen", "tens", "hundred"}),
}


def _kind(word: str) -> str:
    """Classify a number-word by how it combines, not by its value."""
    if word == "hundred":
        return "hundred"
    if word in SCALES:
        return "scale"
    if word in TENS:
        return "tens"
    value = UNITS[word]
    if value == 0:
        return "zero"
    return "teen" if value >= 10 else "unit"


def _may_follow(word: str, previous: str | None) -> bool:
    """True if `word` can continue a number whose last word was `previous`."""
    return previous in _MAY_FOLLOW[_kind(word)]


def _split_token(tok: str) -> tuple[str, str]:
    """Return (core, trailing punctuation)."""
    i = len(tok)
    while i > 0 and tok[i - 1] in _TRAIL:
        i -= 1
    return tok[:i], tok[i:]


def _fold(run: list[str]) -> int:
    """Fold one run of legally-combining number-words to a single integer.

    Units and tens accumulate; `hundred` multiplies the accumulator; larger
    scales flush it. The caller guarantees the run actually combines — see
    `_may_follow` — so this never has to decide whether a sum is meaningful.
    """
    total = 0
    current = 0
    for word in run:
        if word == "and":
            continue
        if word in UNITS:
            current += UNITS[word]
        elif word in TENS:
            current += TENS[word]
        elif word == "hundred":
            current = (current or 1) * 100
        else:
            current = (current or 1) * SCALES[word]
            total += current
            current = 0
    return total + current


def rewrite_number_words(text: str) -> str:
    """Rewrite maximal runs of number-words to digit strings, in place.

    Idempotent on digits: "73 percent" passes through untouched.
    """
    if not text:
        return ""
    text = _HYPHEN_BETWEEN_LETTERS.sub(" ", text)
    tokens = text.split(" ")
    out: list[str] = []
    i = 0
    n = len(tokens)

    while i < n:
        core, _ = _split_token(tokens[i])
        if core not in _NUMBER_WORDS:
            out.append(tokens[i])
            i += 1
            continue

        run: list[str] = []
        previous: str | None = None
        j = i
        trailing = ""
        while j < n:
            core, trail = _split_token(tokens[j])
            if core in _NUMBER_WORDS and _may_follow(core, previous):
                run.append(core)
                previous = _kind(core)
                trailing = trail
                j += 1
                if "." in trail:
                    # A full stop ends the sentence, and therefore the number.
                    # Without this the run walks straight across the boundary
                    # and "chapter two. three things" folds to "chapter 5".
                    break
            elif core == "and" and run and j + 1 < n:
                # Absorb an internal "and" only while a run is already open and
                # a number-word that can legally continue it actually follows:
                # "one hundred and twenty".
                nxt, _ = _split_token(tokens[j + 1])
                if nxt in _NUMBER_WORDS and _may_follow(nxt, previous):
                    run.append("and")
                    j += 1
                else:
                    break
            else:
                break

        if not run:  # unreachable: every kind of number-word may open a run
            out.append(tokens[i])
            i += 1
            continue

        out.append(f"{_fold(run)}{trailing}")
        i = j

    return " ".join(out)


_PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*(?:per\s+cent|percent|pct|%)")
_DOLLARS_AFTER = re.compile(r"(\d+(?:\.\d+)?)\s*(?:dollars|dollar|usd|bucks)\b")
_DOLLARS_BEFORE = re.compile(r"\$\s*(\d+(?:\.\d+)?)")


def fold_units(text: str) -> str:
    """Collapse spoken units onto their symbol so all spellings agree.

    73% == 73 percent == seventy-three percent
    $20 == 20 dollars == twenty dollars
    """
    text = _PERCENT.sub(r"\1%", text)
    text = _DOLLARS_AFTER.sub(r"$\1", text)
    text = _DOLLARS_BEFORE.sub(r"$\1", text)
    return text


def canonical_numeric(text: str) -> str:
    """Words to digits, then units to symbols."""
    return fold_units(rewrite_number_words(text))


def value_pattern(value: str) -> re.Pattern[str]:
    """A boundary-guarded membership pattern for an exact value.

    The guards are what stop `73` matching inside `730` or `chapter 173`.
    Numeric comparison is membership only — never fuzzy (Rules.md §1.6).
    """
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        # A unitless contractual number must not pass inside a decimal,
        # percentage, or currency amount: 73 != 73.0 != 73% != $73.
        return re.compile(rf"(?<![\d.$]){re.escape(value)}(?![\d.%])")
    return re.compile(rf"(?<![\d.]){re.escape(value)}(?![\d])")


_SHAPE_PERCENT = re.compile(r"\d+(?:\.\d+)?%")
_SHAPE_DOLLARS = re.compile(r"\$\d+(?:\.\d+)?")
_SHAPE_PLAIN = re.compile(r"(?<![\d.])\d+(?:\.\d+)?(?![\d])")


def same_shape_pattern(value: str) -> re.Pattern[str] | None:
    """Pattern matching values of the same shape as `value`.

    Used only to report what was detected instead — "expected 73%, detected
    70%". It never decides a verdict.
    """
    if value.endswith("%"):
        return _SHAPE_PERCENT
    if value.startswith("$"):
        return _SHAPE_DOLLARS
    if re.fullmatch(r"\d+(?:\.\d+)?", value):
        return _SHAPE_PLAIN
    return None
