"""The compiler prompt, versioned with the code. Architecture.md §9.

This is the **only** place an LLM appears in SponsorLint, and it never sees the
transcript — it converts the brief into a specification the user then reviews.
"""

PROMPT_VERSION = "1.0"

COMPILER_PROMPT = """\
Convert the sponsor brief into a constrained machine-readable
verification specification.

Extract only requirements that can reasonably be checked from the
spoken content or the duration of the recorded sponsor integration.

For every extracted rule:
- preserve a verbatim source_quote from the brief
- preserve exact numbers, product names, URLs, promo codes
- preserve prohibited language verbatim
- use only the six allowed rule types
- never invent a requirement
- never infer an unsupported requirement
- set needs_review=true when uncertain

Requirements that cannot be verified from audio or duration must be
returned in manual_review, not dropped and not guessed.

Return data matching the supplied schema.
"""

#: Field-level rules the schema alone cannot express. Architecture.md §4.1 and
#: §5.4 both require specific compiler behavior that the base prompt does not
#: state — without this the compiler cannot produce the disclosure-placement
#: shape the review screen depends on.
SCHEMA_NOTES = """\

Per rule type:

- MUST_SAY / MUST_NOT_SAY use `phrases`, never `expected`. One brief sentence
  prohibiting several phrases is ONE rule with several phrases, sharing one
  source_quote.
- EXACT_VALUE / URL_OR_CTA use `expected`. Write numbers the way the brief's
  own figures resolve: "seventy-three percent" becomes "73%".
- DURATION uses `min_seconds` / `max_seconds` and omits `expected`.
  "no shorter than one minute and no longer than one minute and thirty
  seconds" becomes min_seconds 60, max_seconds 90.
- MUST_DISCLOSE never carries disclosure phrasings — the verifier holds those.
  For placement:
    * brief gives a number ("within the first 30 seconds")
        -> within_first_seconds: 30, needs_review: false
    * brief states placement in words but no number ("near the beginning")
        -> within_first_seconds: null, needs_review: true
          The user supplies the number on the review screen. Never invent one.
    * brief says nothing about placement
        -> within_first_seconds: null, needs_review: false

severity is "error" unless the brief itself marks a requirement as optional or
preferred, in which case use "warning".

Give each rule a short human label and a sequential id: r1, r2, r3, ...
"""


def build_prompt(brief_text: str) -> str:
    return (
        f"{COMPILER_PROMPT}{SCHEMA_NOTES}\n"
        f"--- SPONSOR BRIEF ---\n{brief_text.strip()}\n--- END BRIEF ---"
    )
