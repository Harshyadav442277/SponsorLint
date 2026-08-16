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
│   │   └── fixtures.json     46 labeled cases
│   │
│   └── web/
│       ├── app.py            FastAPI routes
│       ├── templates/
│       └── static/
│
├── samples/
│   ├── brief.md
│   ├── brief.pdf
│   ├── script.md                    recording and six-string gate
│   ├── spec.approved.json        COMMITTED — enables zero-key demo
│   ├── transcript.v1.json        COMMITTED
│   └── transcript.v3.json        COMMITTED
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

The real `sponsor-cut-v1.mp4` and `sponsor-cut-v3.mp4` are intentionally absent until the
pre-media recording gate is completed; the committed transcripts remain clearly labeled authored
fixtures in `samples/README.md`.

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

`severity` is `error` (blocking) or `warning` (non-blocking). **`severity` is consulted only when a rule FAILS.** A passing rule always reports `PASS` regardless of severity.

Rule types beyond the six in `PRD.md` §4.1 are rejected at validation.

### Per-type payload — a scalar `expected` is not enough

A single `expected` string cannot hold a duration window, a multi-phrase prohibition, or a placement constraint. **Pin the model exactly as below**; `models.py` is the first file written and every other module types against it.

```python
class Rule(BaseModel):
    id: str
    type: Literal["MUST_SAY","MUST_NOT_SAY","EXACT_VALUE",
                  "MUST_DISCLOSE","DURATION","URL_OR_CTA"]
    label: str
    source_quote: str                      # mandatory — reject without it
    severity: Literal["error","warning"] = "error"
    needs_review: bool = False

    expected: str | None = None            # EXACT_VALUE, URL_OR_CTA
    phrases: list[str] | None = None       # MUST_SAY, MUST_NOT_SAY
    min_seconds: float | None = None       # DURATION
    max_seconds: float | None = None       # DURATION
    within_first_seconds: float | None = None   # MUST_DISCLOSE placement
    within_last_seconds: float | None = None    # URL_OR_CTA placement
```

| Type | Populated fields | Semantics |
|---|---|---|
| `MUST_SAY` | `phrases: [str, ...]` | PASS if **any** phrase occurs |
| `MUST_NOT_SAY` | `phrases: [str, ...]` | PASS only if **none** occur. One brief sentence prohibiting N phrases compiles to **one rule with N phrases**, sharing one `source_quote` |
| `EXACT_VALUE` | `expected: str` | membership test, §5.1 |
| `URL_OR_CTA` | `expected: str`, optional `within_last_seconds` | canonicalized; a placement window makes a closing CTA distinct from a URL spoken anywhere, §5.1 |
| `MUST_DISCLOSE` | `within_first_seconds: float \| null` | accepted disclosure phrases are a module constant in `lint/disclosure.py`, **not** a rule field — the compiler never emits them |
| `DURATION` | `min_seconds`, `max_seconds` (either may be null) | `expected` omitted |

`MUST_SAY` and `MUST_NOT_SAY` always use `phrases`, never `expected`, so the editor and the validators have one shape to render and one to read.

## 4.2 Spec

```json
{
  "campaign": "Aegis VPN Creator Campaign",
  "rules": [ /* Rule[] */ ],
  "manual_review": [
    {
      "source_quote": "The product interface should be visible on screen for at least five seconds.",
      "reason": "Visual requirement — not verifiable from audio or duration.",
      "confirmed": false
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

**`duration_seconds` is REQUIRED and is the only duration any validator ever reads.** `ffprobe` runs upstream in `transcript/probe.py` at transcribe time and writes the value into this file. Validators stay pure (`Rules.md` §5) and never shell out — **this is what keeps the zero-key demo free of an ffmpeg dependency on the judge's machine.** There is no separate `video-metadata.json`; a second duration source would silently disagree with this one.

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
  "status": "DO_NOT_SEND",
  "summary": { "pass": 4, "warn": 0, "fail": 3, "manual_review": 0, "manual_confirmed": 1 },
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

### The algorithm — a run-scanner, no new dependency

Do not reach for `word2number`. It was tested against the strings a validator actually receives and fails on all of them: it raises on `"save 73 percent"` (cannot read digits at all, defeating the whole digits-or-words requirement), returns `31` for `"one minute and thirty seconds"`, returns `2` for `"two zero"` (codes need concatenation, not summation), and returns only one number per string.

**Rewrite number-words to digits in place, then test membership.** In `normalize/numbers.py`:

1. Lowercase, then `re.sub(r'(?<=[a-z])-(?=[a-z])', ' ', text)` so `seventy-three` tokenizes.
2. Tokenize on whitespace.
3. Walk tokens. On each **maximal run** of number-words — `UNITS` 0–19, `TENS` 20–90, `SCALES` hundred/thousand/million, absorbing an internal `and` only while a run is already open — fold the run to an int: units and tens accumulate, `hundred` multiplies the accumulator, larger scales flush it. Emit the digit string in place. Leave every other token untouched.
4. Result: `"you can save up to 70 percent using my link."` The rewriter is **idempotent** on text that already contains digits — which is exactly what makes both Whisper output styles work.

**`EXACT_VALUE` then does not parse at all — it is a membership test.** Canonicalize the transcript with the rewriter, then search with a boundary-guarded pattern:

```python
re.search(rf'(?<![\d.]){re.escape(value)}(?![\d])', canonical)
```

Verified: `73` in `"seventy-three percent"` → True · in `"seventy percent"` → False · in `"73 percent"` → True · in `"730 dollars"` → False · in `"chapter 173"` → False.

**`normalize/codes.py` uses a separate per-digit map** (`two`→`2`, `zero`→`0`, concatenated, letters uppercased) — **never** the arithmetic folder, which would fold `two zero` to 2.

`"one minute and thirty seconds"` → 90 is the **compiler's** job (Phase 5, LLM), not the normalizer's. The normalizer correctly yields `"1 minute and 30 seconds"`; turning that into `min_seconds: 60, max_seconds: 90` is semantic work the LLM does once, at compile time.

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

### The haystack: always the JOINED transcript, never per segment

Build the haystack **once**, after normalization:

```python
haystack = " ".join(seg.text for seg in transcript.segments)   # then normalize
offsets  = [(char_offset, segment_index), ...]                 # to resolve a hit back
```

A required phrase routinely straddles a Whisper segment break. **Measured:** for segments `"definitely try shield"` / `"mode when you sign up."`, the best per-segment score for `"shield mode"` is **70.6** (FAIL) while the joined text scores **100.0** (PASS). A per-segment loop is the highest-probability silent demo break in the project — it depends on where Whisper happens to cut, so it can pass at GATE 2:10 and fail after the Phase 9 re-splice at T+23:30.

Keep the `(offset → segment)` map so a match resolves back to a segment for its timestamp.

### The scorer: `partial_ratio`, never `ratio`, never `partial_token_set_ratio`

```python
from rapidfuzz import fuzz
score = fuzz.partial_ratio(normalized_phrase, normalized_haystack)   # threshold >= 90
```

Measured on rapidfuzz against the §7 fixtures — this is not a preference, `ratio` is simply broken here:

| needle vs haystack | `ratio` | `partial_ratio` | `partial_token_set_ratio` | must be |
|---|---:|---:|---:|---|
| `shield mode` / "try shield mode today." | 66.7 | **100.0** | 100.0 | PASS |
| `completely anonymous` / full transcript | 21.3 | **100.0** | 100.0 | PASS |
| `sponsored by` / full transcript | 13.3 | **100.0** | 100.0 | PASS |
| `shield mode` / "try the shield feature today." | 45.0 | **72.7** | 100.0 ✗ | FAIL |
| `completely anonymous` / "browse anonymously" | 63.2 | **71.4** | 73.3 | no fire |
| `sponsored by` / "i sponsored a little league team once." | 40.0 | **83.3** | 100.0 ✗ | FAIL |

- **`fuzz.ratio` is whole-string similarity.** It scores every true match 10–67, so at a ≥90 threshold nothing could ever pass. Implementing §5.2 literally would return FAIL for every phrase rule in the demo.
- **`partial_token_set_ratio` returns 100.0 on both documented hard negatives.** It is a false-PASS generator. Never use it.
- `partial_ratio`'s worst true-negative margin is the little-league case at 83.3 — **6.7 points of headroom at threshold 90.** Do not raise the threshold above 90 and do not lower it.

**Short-needle guard.** `partial_ratio("vpn", <any transcript containing v…p…n>)` = **100.0**. Any phrase shorter than **8 characters after normalization must be matched exactly, never fuzzed.**

### Order of operations

Normalized exact containment runs first on every phrase rule. Fuzzy is only the fallback.

**Fuzzy matching is never acceptable for numeric values.** `70` is not `73`. `EXACT_VALUE` is membership only (§5.1).

> **Do not loosen a fuzzy threshold to make the demo pass.** If you are tuning a threshold to turn a FAIL green, you have broken the product.

## 5.3 Per-validator notes

Every validator has the signature `(rule: Rule, tx: Transcript) -> Result`. **Pure — no I/O, no network, no subprocess** (`Rules.md` §5). Everything a validator needs is already in those two objects.

| Validator | Notes |
|---|---|
| `MUST_SAY` | any of `rule.phrases`: normalized exact containment → `partial_ratio` ≥90 → FAIL. On failure report the best-scoring window as the closest match so the user sees *why* |
| `MUST_NOT_SAY` | **normalized exact containment only — no fuzzy.** A fuzzy prohibition false-fires, and a false FAIL is the expensive error (§7). Exact hit → FAIL with that segment's timestamp. Score ≥90 without containment → `MANUAL REVIEW`, never FAIL |
| `EXACT_VALUE` | membership test on the canonicalized transcript (§5.1). Deterministic only. Never an LLM. Never fuzzy |
| `MUST_DISCLOSE` | matches the module-level phrase constant in `lint/disclosure.py` — `sponsored by`, `this video is sponsored by`, `paid partnership`, `thanks to X for sponsoring`, `today's sponsor is`. The compiler never emits these. **Always return the timestamp.** Placement per §5.4 |
| `DURATION` | reads `tx.duration_seconds` against `rule.min_seconds` / `rule.max_seconds`. **Never shells out to ffprobe** — that ran upstream at transcribe time (§4.3) |
| `URL_OR_CTA` | canonicalize both sides per §5.1, then containment |

**The substring trap, stated in the direction the fixture tests it:** a rule prohibiting `"completely anonymous"` must **not** fire on a transcript that only says `"anonymously"`. Exact containment gives this for free; fuzzy does not (measured 71.4, safely under threshold, but only because the threshold holds).

## 5.4 Disclosure placement

Not a rule type. A derived property of the `MUST_DISCLOSE` result.

**The paradox, and its resolution.** The demo brief says *"near the beginning"* — placement is specified, so it should be enforced. But *"near the beginning"* is not a number, and enforcing it requires comparing the timestamp to a threshold, and every available threshold is one **we** invented, which `Rules.md` §1.14 forbids. The check is simultaneously mandated and prohibited.

**Route the number through the trust boundary instead.** This is D4 doing exactly what it exists for — and it invents nothing on the creator's behalf:

```
brief states placement in words but gives no number
        ↓
compiler emits MUST_DISCLOSE with
    within_first_seconds: null
    needs_review: true
        ↓
the review screen renders the empty field and requires a value
    → the spec is NOT approvable while it is null
        ↓
the number came from the USER, never from us
        ↓
validator: disclosure timestamp <= within_first_seconds ? PASS : FAIL

brief states no placement at all
        ↓
within_first_seconds stays null
        ↓
report presence + timestamp only. Optional advisory, never a verdict:
    ⚠ ADVISORY — Disclosure occurs at 00:47.
                 Review placement before sending.
```

`samples/spec.approved.json` ships a **user-authored `within_first_seconds: 15`**. V1 discloses at 0.0–3.8s, so it passes with margin. Note in the README that the user chose that number.

**No invented threshold.** Do not flag on "after 25% of the segment" or "after 30 seconds" or any other number we made up. Any rule not derived from the sponsor brief is a rule we are inventing on the creator's behalf, and it edges toward the legal-compliance claim `Rules.md` §8 bans.

**Never emit regulatory language.** No *"clear and conspicuous,"* no *"FTC,"* no *"legally required."* We check the supplied brief, not the law.

## 5.5 Readiness resolution

Three mutually exclusive clauses. Manual uncertainty must be resolved explicitly.

```
any error-severity rule FAILS                       → DO NOT SEND

no error-severity failure, but at least one
  warning-severity rule FAILS, validator returns
  MANUAL_REVIEW, or manual item is unconfirmed      → REVIEW

all error-severity rules pass and no
  warning failed; every manual item confirmed       → SPONSOR READY
```

`MANUAL REVIEW` items are excluded from the automated score and always listed. The creator can
explicitly confirm an external check; until then, SponsorLint says `REVIEW` rather than claiming
automation verified something it cannot observe.

All seven demo rules are `severity: error`. The committed approved sample leaves the visual item
unconfirmed because the real V3 media does not show the required product interface, so V1 is
`DO NOT SEND` and V3 is `REVIEW` despite passing all seven automated checks.

### On the score

If a percentage is shown, it is `passed scored automated rules / total scored automated rules × 100`
and nothing else. No rule weighting is implemented.

**Do not engineer weights to produce a nicer-looking number**, and do not carry a target percentage from any earlier draft. Report what the formula produces. Better still, prefer the raw fraction in demo material — it is more trustworthy and cannot be accused of being tuned:

```
V1   4/7 requirements passed      DO NOT SEND
V2   6/7 requirements passed      DO NOT SEND
V3   7/7 requirements passed      REVIEW
```

The binary state is what matters. The score is decoration.

---

# 6. CLI surface

## Invocation form — `python -m sponsorlint`, always

**There is no `pyproject.toml`, no `setup.py`, no `pip install -e .`, and no `sponsorlint` console script.** The bare `sponsorlint demo` form does not exist and must not appear in the README, the GIF, or any acceptance criterion — a judge who copy-pastes it gets `'sponsorlint' is not recognized`, on the 60-second first impression.

`python -m sponsorlint` works with zero packaging because Python puts the current directory on `sys.path` for `-m`. **All documented commands must be run from the repo root**; say so in the README quickstart.

## Import discipline — this is what makes the zero-key path work

`cli.py`, `__main__.py` and `models.py` may import at module scope **only** from `models`, `lint/`, `report/`, `normalize/` and `eval/` — modules whose entire dependency set is in `requirements-demo.txt`.

`faster_whisper`, `pypdf` and the LLM client are imported **inside the command branch that needs them**:

```python
def main(argv):
    cmd = argv[0]
    if cmd in ("demo", "verify", "eval"):
        from .lint.engine import run                    # demo deps only
    elif cmd == "transcribe":
        from .transcript.transcribe import transcribe    # faster-whisper HERE
    elif cmd == "compile":
        from .brief.extract import extract               # pypdf HERE
```

The same applies to `web/app.py`: the `/`, `/api/sample` and `/api/verify` routes must not pull a full-path import at module scope.

> **Verified, not theorized.** Building this exact layout with a module-scope `from .transcript.transcribe import ...` and running `python -m sponsorlint demo` in a venv containing only the six demo packages dies with `ModuleNotFoundError: No module named 'faster_whisper'`, exit 1, **before dispatch runs**. Moving the import into its branch makes the identical command exit 0.
>
> **You will never see this locally** — your dev machine has faster-whisper installed. It surfaces at the clean-environment run at T+27:30, two hours before the deadline, after the README and GIF are already recorded.

Guard it with a check that runs in Phase 4:

```bash
python -c "import ast,sys; m=ast.parse(open('sponsorlint/cli.py').read()); \
bad=[n for n in ast.walk(m) if isinstance(n,(ast.Import,ast.ImportFrom)) and n.col_offset==0 \
and any(x in ast.dump(n) for x in ('faster_whisper','pypdf','openai','google'))]; \
sys.exit(len(bad))"
```

*(Confirmed separately: bare `import faster_whisper` performs no network I/O and the Silero VAD onnx ships inside the wheel, so the "no download" claim is achievable. The transitive import is the only thing that breaks it.)*

## Commands

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

**46 pure-text fixtures. No video. No Whisper. No API calls. Runs in under a second.**

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
Fixtures:          46
Correct:           45
Incorrect:          1
Accuracy:        97.8%

False FAILs:        1     (reported FAIL, requirement was satisfied)
False PASSes:       0     (reported PASS, requirement was violated)
Manual Review:      1
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
git clone https://github.com/Harshyadav442277/SponsorLint.git
cd SponsorLint
pip install -r requirements-demo.txt
python -m sponsorlint demo
```

Runs the **real deterministic verifier** against `samples/spec.approved.json` and `samples/transcript.v1.json` — the same two inputs `verify` takes, so the demo and the eval exercise identical code paths. Duration comes from `transcript.duration_seconds` (§4.3), which is why no ffmpeg is needed on the judge's machine.

**No hardcoded verdicts.** The approved specification and transcript fixture are committed as
reproducible inputs; the verifier computes the verdict at runtime.

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

## Provider — decided, not deferred

```
package:  google-genai
model:    gemini-3-flash-preview
mechanism: structured output — send Spec.model_json_schema(), then validate
           the returned structure with the authoritative Spec Pydantic model
```

Do not use an assistant prefill to force JSON; structured outputs is the mechanism.

The installed SDK's direct `response_schema=Spec` translation was rejected live because it mapped
Pydantic's `extra="forbid"` constraint to an unsupported OpenAPI field. The supported
`response_json_schema` path preserves the JSON Schema constraint, and SponsorLint still validates
the returned structure through `Spec.model_validate` before source grounding. SDK retries are
disabled; SponsorLint permits at most one explicit retry.

This path was validated live against `samples/brief.pdf` on Aug 17, 2026. The seven-rule proposal
and one manual item passed schema validation and literal source grounding, then received explicit
human approval with 15-second opening and closing placement thresholds. The zero-key path remains
independent of the compiler.

## The prompt

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
