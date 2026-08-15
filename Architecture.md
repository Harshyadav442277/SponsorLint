# Architecture — SponsorLint

Companion to `PRD.md`. This document defines **how** it is built: the pipeline, the stack, the folder layout, and the data contracts.

---

# 1. The central principle

## LLM = COMPILER. DETERMINISTIC CODE = VERIFIER.

The LLM may interpret the brief. It must **never** be the final judge of whether a recorded segment passed, wherever deterministic verification is possible.

**Wrong:**
```
brief + transcript → LLM → "looks compliant"
```

**Correct:**
```
              messy sponsor brief
                      │
                      ▼
          ┌───────────────────────┐
          │ Brief Extractor       │  pypdf → clean text
          └───────────┬───────────┘
                      ▼
          ┌───────────────────────┐
          │ Requirement Compiler  │  ← the ONLY LLM call
          │ constrained → JSON    │     never sees the transcript
          └───────────┬───────────┘
                      ▼
              sponsor-spec.json
                      │
                      ▼
          ┌───────────────────────┐
          │ USER REVIEWS / EDITS  │  ← the trust boundary
          └───────────┬───────────┘
                      ▼
           spec.approved.json
                      │
        ┌─────────────┴─────────────┐
        │                           │
        │              ┌────────────────────────┐
        │              │  sponsor-cut.mp4       │
        │              └────────────┬───────────┘
        │                           ▼
        │              ┌────────────────────────┐
        │              │ Transcriber            │  faster-whisper
        │              │ + ffprobe (duration)   │
        │              └────────────┬───────────┘
        │                           ▼
        │                    transcript.json      ← CACHED TO DISK
        │                           │
        └─────────────┬─────────────┘
                      ▼
          ┌───────────────────────┐
          │ Verifier              │  DETERMINISTIC. No LLM.
          │ 6 validators          │  Pure functions.
          └───────────┬───────────┘
                      ▼
              lint-results.json
                      │
                      ▼
          ┌───────────────────────┐
          │ Report                │  web view + terminal
          └───────────────────────┘
```

## The trust model, in one sentence

> **The model proposes the specification. The user owns the specification. Deterministic code enforces the approved specification.**

## Why this matters beyond aesthetics

| Property | Because the verifier is deterministic |
|---|---|
| **Reproducible** | Same inputs → same output, every time |
| **Auditable** | Every FAIL cites a transcript line and a source quote |
| **Testable** | The eval harness (§7) is only possible at all |
| **Debuggable** | Each stage is a separate CLI command (§6) |

This is the project's strongest technical talking point. It pre-empts *"isn't this just an LLM wrapper?"* — **the LLM never sees the transcript.**

---

# 2. Tech stack

## Backend

```
Python 3.11+
FastAPI          API + serves the web UI
Pydantic         schema validation at every boundary
pypdf            PDF text extraction
faster-whisper   transcription — base.en, CPU
ffmpeg/ffprobe   duration and media metadata
RapidFuzz        fuzzy matching for names/phrases only
```

**Use `faster-whisper` with the `base.en` model on CPU, from the start.** Do not take a GPU/CUDA detour — it is the most likely single hour-sink in this build and buys nothing on a 75-second clip.

The LLM API is **optional**. The default demo must not depend on it.

## Frontend

```
FastAPI + Jinja2 + vanilla JavaScript + plain CSS
```

**Do not start Next.js.** React only if it is already clearly faster for you. No SSR, no component library, no auth routing, no build step. See `Design.md` for the visual system.

## No infrastructure project

No PostgreSQL, Redis, ORM, migrations, accounts, campaign history, Kubernetes, queues, microservices, or object storage. Files and in-memory dicts. **Docker must not be required to run the judge demo.**

## Dependency split — this matters

Two requirements files, because the zero-key demo path depends on it:

```
requirements-demo.txt    fastapi uvicorn jinja2 pydantic rapidfuzz python-multipart
requirements.txt         the above + pypdf, faster-whisper, LLM client
```

A judge installs `requirements-demo.txt` and runs the real verifier. No model download, no API key.

---

# 3. Folder structure

```text
sponsorlint/
├── sponsorlint/
│   ├── __main__.py           python -m sponsorlint
│   ├── cli.py                command dispatch
│   ├── models.py             Pydantic: Rule, Spec, Transcript, Result, Report
│   │
│   ├── brief/
│   │   ├── extract.py        PDF/md → text
│   │   ├── compile.py        text → Spec  (the only LLM call)
│   │   └── prompt.py         the compiler prompt, versioned
│   │
│   ├── transcript/
│   │   ├── transcribe.py     faster-whisper wrapper
│   │   └── probe.py          ffprobe duration
│   │
│   ├── normalize/            ← pure functions, heavily unit-tested
│   │   ├── text.py           unicode, case, punctuation, whitespace
│   │   ├── numbers.py        spoken numerals, currency, percent
│   │   ├── urls.py           spoken URL canonicalization
│   │   └── codes.py          promo codes spelled aloud
│   │
│   ├── lint/
│   │   ├── engine.py         dispatch + readiness resolution
│   │   ├── must_say.py
│   │   ├── must_not_say.py
│   │   ├── exact_value.py
│   │   ├── disclosure.py     presence + placement
│   │   ├── duration.py
│   │   └── cta.py
│   │
│   ├── report/
│   │   ├── terminal.py       ANSI output — see Design.md §7
│   │   └── render.py         JSON → template context
│   │
│   ├── eval/
│   │   ├── runner.py
│   │   └── fixtures.json     24–30 labeled cases
│   │
│   └── web/
│       ├── app.py            FastAPI routes
│       ├── templates/
│       └── static/
│
├── samples/
│   ├── brief.md
│   ├── brief.pdf
│   ├── spec.approved.json        COMMITTED — enables zero-key demo
│   ├── transcript.v1.json        COMMITTED
│   ├── transcript.v3.json        COMMITTED
│   ├── video-metadata.v1.json    COMMITTED
│   ├── sponsor-cut-v1.mp4
│   └── sponsor-cut-v3.mp4
│
├── tests/
│   ├── test_normalize_numbers.py
│   ├── test_normalize_urls.py
│   ├── test_validators.py
│   └── test_engine.py
│
├── PRD.md · Architecture.md · Rules.md · Phases.md
├── Design.md · Decisions.md · Memory.md
├── README.md
├── requirements-demo.txt
└── requirements.txt
```

**Do not reorganize a working repo for aesthetics.**

---

# 4. Data contracts

Every boundary is a Pydantic model. Validate on the way in and on the way out.

## 4.1 Rule

```json
{
  "id": "r2",
  "type": "EXACT_VALUE",
  "label": "Campaign discount",
  "expected": "73%",
  "source_quote": "viewers should be told that they can save seventy-three percent",
  "severity": "error",
  "needs_review": false
}
```

`source_quote` is **mandatory**. Reject any extraction without it — it is what makes each rule auditable and what powers the split-screen review.

`severity` is `error` (blocking) or `warning` (non-blocking).

Rule types beyond the six in `PRD.md` §4.1 are rejected at validation.

## 4.2 Spec

```json
{
  "campaign": "Aegis VPN Creator Campaign",
  "rules": [ /* Rule[] */ ],
  "manual_review": [
    {
      "source_quote": "The product interface should be visible on screen for at least five seconds.",
      "reason": "Visual requirement — not verifiable from audio or duration."
    }
  ]
}
```

## 4.3 Transcript

```json
{
  "duration_seconds": 74.2,
  "segments": [
    { "start": 0.0,  "end": 3.8,  "text": "This video is sponsored by Aegis VPN." },
    { "start": 28.3, "end": 33.4, "text": "It keeps you completely anonymous online." },
    { "start": 41.1, "end": 45.2, "text": "You can save up to seventy percent." }
  ]
}
```

Segment timestamps are sufficient. Word timestamps are useful, not required.

## 4.4 Result

```json
{
  "rule_id": "r2",
  "rule_type": "EXACT_VALUE",
  "status": "FAIL",
  "title": "Wrong campaign discount",
  "expected": "73%",
  "detected": "70%",
  "timestamp": 43.1,
  "evidence": "You can save up to seventy percent.",
  "source_quote": "viewers should be told that they can save seventy-three percent"
}
```

Every failure answers five questions: **what was required · what was detected · where · what evidence · where did the requirement come from.**

## 4.5 Report

```json
{
  "status": "FAIL",
  "summary": { "pass": 4, "warn": 1, "fail": 2, "manual_review": 1 },
  "results": [ /* Result[] */ ],
  "manual_review": [ /* ManualReviewItem[] */ ]
}
```

---

# 5. Verification strategy

## 5.1 Normalization pipeline

A shared deterministic module. Ordered:

```
raw text → unicode → case → punctuation → whitespace
        → numbers → currency/percent → URLs → promo codes
        → comparison-ready representation
```

### Spoken numbers — core, not polish

**Whisper emits digits sometimes and words other times, unpredictably, within the same transcript. Support both. Test both.** This is the most common silent failure in this build.

Must compare equal:
```
73%  ·  73 percent  ·  seventy-three percent  ·  seventy three percent
$20  ·  twenty dollars  ·  20 dollars
3 months  ·  three months
```

Must **not** compare equal:
```
70%   vs   73%
```

### Promo codes
```
"H-A-R-S-H two zero"  ·  "HARSH two zero"  ·  "HARSH20"   →   HARSH20
```

### URLs
```
aegisvpn.com/alex  ·  aegis vpn dot com slash alex
aegisvpn dot com slash alex  ·  www.aegisvpn.com/alex
```
Normalize spaces, verbal punctuation, optional `www`, scheme, casing, trailing slash. **Always return the original transcript text as evidence.**

## 5.2 Matching policy

| Outcome | State |
|---|---|
| Exact or canonical match | `PASS` |
| Deterministic mismatch | `FAIL` |
| Ambiguous | `MANUAL REVIEW` |

**Fuzzy matching is acceptable** for minor transcription noise in names and phrases — `"Shield Mode"` versus a small tokenization error. Threshold ≥ 90 on `rapidfuzz.ratio`.

**Fuzzy matching is never acceptable for numeric values.** `70` is not `73`.

> **Do not loosen a fuzzy threshold to make the demo pass.** If you are tuning a threshold to turn a FAIL green, you have broken the product.

## 5.3 Per-validator notes

| Validator | Notes |
|---|---|
| `MUST_SAY` | normalized exact → fuzzy ≥90 → FAIL. On failure, report the closest partial match so the user sees *why* |
| `MUST_NOT_SAY` | same, inverted. **Substring trap:** bare `anonymous` must not fire a rule for `"completely anonymous"` |
| `EXACT_VALUE` | full numeral normalization. Deterministic only. Never an LLM. Never fuzzy |
| `MUST_DISCLOSE` | phrase set + fuzzy: `sponsored by`, `this video is sponsored by`, `paid partnership`, `thanks to X for sponsoring`, `today's sponsor is`. **Always return the timestamp** |
| `DURATION` | `ffprobe`. One call. No LLM |
| `URL_OR_CTA` | canonicalize per §5.1 |

## 5.4 Disclosure placement

Not a rule type. A derived property of the `MUST_DISCLOSE` result.

```
if the brief specifies placement:
    enforce it as a normal rule          # demo brief: "near the beginning"

else:
    show the disclosure timestamp only

    optional advisory, never a verdict:
    ⚠ ADVISORY — Disclosure occurs at 00:47.
                 Review placement before sending.
```

**No invented threshold.** Do not flag on "after 25% of the segment" or "after 30 seconds" or any other number we made up. Any rule not derived from the sponsor brief is a rule we are inventing on the creator's behalf, and it edges toward the legal-compliance claim `Rules.md` §8 bans.

**Never emit regulatory language.** No *"clear and conspicuous,"* no *"FTC,"* no *"legally required."* We check the supplied brief, not the law.

## 5.5 Readiness resolution

```
any blocking (error) rule fails         → DO NOT SEND
no blocking failure, warnings or
  manual-review items exist             → REVIEW
all blocking rules pass                 → SPONSOR READY
```

`MANUAL REVIEW` items are excluded from the score, listed separately, and **never block** `SPONSOR READY`.

### On the score

If a percentage is shown, it is `passed weighted rules / total weighted rules × 100` and nothing else.

**Do not engineer weights to produce a nicer-looking number.** If the demo arc naturally lands on 57% → 86%, fine; if it lands somewhere else, report what it lands on. Better still, prefer the raw fraction in demo material — it is more trustworthy and cannot be accused of being tuned:

```
V1   4/7 requirements passed      DO NOT SEND
V2   6/7 requirements passed      DO NOT SEND
V3   7/7 requirements passed      SPONSOR READY
```

The binary state is what matters. The score is decoration.

---

# 6. CLI surface

Decomposed so the project is debuggable and falsifiable in pieces.

```bash
python -m sponsorlint demo
# zero-key. Cached fixtures, real verifier. No network, no model download.

python -m sponsorlint verify --spec S.json --transcript T.json
# deterministic checks only

python -m sponsorlint transcribe cut.mp4
# faster-whisper → transcript JSON

python -m sponsorlint compile brief.pdf
# PDF + LLM → proposed spec

python -m sponsorlint analyze brief.pdf cut.mp4
# the full flow

python -m sponsorlint eval
# validator metrics
```

## Web routes

```
GET  /                        upload view
POST /api/compile             brief → proposed spec
POST /api/spec/approve        edited spec → session store (in-memory dict)
POST /api/verify              approved spec + video → report
GET  /api/report/{id}         fetch a report
GET  /api/sample              load the committed demo campaign
```

---

# 7. Eval harness

**24–30 pure-text fixtures. No video. No Whisper. No API calls. Runs in under a second.**

Fixtures are `(rule, transcript_snippet, expected_verdict)` tuples in `sponsorlint/eval/fixtures.json`. They are the same assertions as the unit tests — **write each one once, use it twice.**

## Load with hard negatives

The number is worthless without them.

| Rule | Transcript | Expected |
|---|---|---|
| `MUST_SAY "Shield Mode"` | "Try Shield Mode today." | PASS |
| `MUST_SAY "Shield Mode"` | "Try the shield feature today." | FAIL |
| `EXACT_VALUE 73%` | "save seventy-three percent" | PASS |
| `EXACT_VALUE 73%` | "save seventy percent" | **FAIL** |
| `MUST_NOT_SAY "completely anonymous"` | "This makes you completely anonymous." | FAIL |
| `MUST_NOT_SAY "completely anonymous"` | "browse anonymously" | PASS *(no violation)* |
| `MUST_DISCLOSE` | "I sponsored a little league team once." | FAIL |
| `URL_OR_CTA aegisvpn.com/alex` | "aegis vpn dot com slash alex" | PASS |
| `EXACT_VALUE HARSH20` | "use code H-A-R-S-H two zero" | PASS |

## Terminology — define this once, use it everywhere

Judges and readers interpret "false positive" in opposite directions depending on whether they think the positive event is *a violation* or *a passing check*. Remove the ambiguity by never using the bare term.

```
Positive       = SponsorLint reports a violation (returns FAIL).

False FAIL     = SponsorLint reports FAIL when the requirement
                 was actually satisfied.
                 Cost: the creator re-edits something that was fine.

False PASS     = SponsorLint reports PASS when the requirement
                 was actually violated.
                 Cost: a broken sponsor read ships to the brand.
```

Use `False FAIL` and `False PASS` in output, in the README, and in conversation. **Do not write "false positive" anywhere.**

## Output

```text
SponsorLint Validator Evaluation
--------------------------------
Fixtures:          28
Correct:           27
Incorrect:          1
Accuracy:        96.4%

False FAILs:        0     (reported FAIL, requirement was satisfied)
False PASSes:       1     (reported PASS, requirement was violated)
Manual Review:      3
```

**Do not fabricate perfection.** Publish whatever the real number is.

## Tuning policy — state this out loud

> A false FAIL wastes the creator's afternoon. A false PASS ships a broken sponsor read to the brand. The two errors are not symmetric.
>
> **Avoid false FAILs. Route ambiguity to MANUAL REVIEW. Then maximize violation catch rate.**

---

# 8. The zero-key path

Two walls kill you with an async judge, and both are on the default path unless explicitly fixed:

- an `OPENAI_API_KEY` prompt → gone in thirty seconds
- a Whisper model download → gone in sixty

## Deliverable

```bash
git clone <repo> && cd sponsorlint
pip install -r requirements-demo.txt
python -m sponsorlint demo
```

Runs the **real deterministic verifier** against `samples/spec.approved.json`, `samples/transcript.v1.json`, and `samples/video-metadata.v1.json`.

**No hardcoded verdicts.** The check executes for real; only the expensive, deterministic upstream steps are cached.

> **Caching is not cheating; fake output is.**

## Reproducibility rule

Before submission, run from a clean clone in a fresh virtualenv. The default demo must not secretly depend on:

- local absolute paths
- files outside the repo
- hidden environment variables
- a running database
- a developer-only model path
- a forgotten API service

---

# 9. The compiler prompt

Lives in `sponsorlint/brief/prompt.py`, versioned with the code.

```text
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
```

Pydantic validation is mandatory. **One retry** on malformed JSON, then surface the error — do not loop.
