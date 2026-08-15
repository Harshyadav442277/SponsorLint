# SPONSORLINT — EXECUTION BIBLE
## Scope Contract, Architecture, Phases, Gates, and Acceptance Criteria

**Project:** SponsorLint
**One-line pitch:** **"Compile a sponsor brief into executable checks, run them against the recorded integration, and get timestamped PASS / WARN / FAIL before you send it to the brand."**

**Hackathon:** Social Media Automation Hackathon
**Deadline:** Aug 17, 2026 @ 4:30 AM IST
**Judging:** Functionality 30% · Real-world usefulness 30% · Creativity 20% · Technical execution 20%
**Core strategy:** Ship one complete, reliable, honest loop. Measure it. Make it runnable by a stranger in sixty seconds with no API key.

> This bible supersedes `SponsorLint_Project_Bible.md`. It incorporates the rulings in `BAKEOFF.md`, which selected SponsorLint over Cutcheck at ~80% confidence. Where the two documents disagree, **this one wins**. The prior bible is kept for reference only.

---

# 0. THIS DOCUMENT IS THE SOURCE OF TRUTH

Any coding agent, teammate, or assistant working on SponsorLint treats this as the **scope contract**.

If a capability is not required here, it is **not part of the hackathon build** unless explicitly marked a stretch goal.

When "this would be cool," "this would look impressive," "we could also add," or "a production system should" conflicts with this file — **this file wins**.

The primary failure mode is not missing features. It is **scope creep leaving the core loop incomplete or unreliable**, or **a judge who cannot run the thing**.

---

# 1. PRODUCT DEFINITION

SponsorLint is a pre-flight compliance checker for sponsored video integrations.

```
sponsor brief (PDF/text)  +  sponsor cut (MP4)
                    ↓
              SponsorLint
                    ↓
  timestamped PASS / WARN / FAIL + readiness state
```

## 1.1 Compile Mode

**Input:** a real sponsor brief, written as prose.
**Process:** an LLM extracts a constrained, machine-readable specification. Each extracted rule cites the source sentence that produced it.
**Output:** `sponsor-spec.json` — human-readable, editable, diffable.

## 1.2 Check Mode

**Input:** `sponsor-spec.json` + the recorded sponsor segment.
**Process:** transcribe with word/segment timestamps, then run **deterministic validators** against the transcript and media metadata.
**Output:** timestamped results with expected value, detected value, and the transcript line that proves it.

## 1.3 Eval Mode

**Input:** a fixture set of labeled `(rule, transcript snippet, expected verdict)` cases.
**Process:** run the verifier over all of them.
**Output:** precision, recall, false positives, false negatives.

**Mode 1.3 is not optional.** It is the single highest-leverage feature in this build and it is what separates this project from every other submission. See §11.

---

# 2. THE EXACT USER PROBLEM

Sponsor briefs are contracts with enumerated deliverables: exact product names, exact discount figures, tracked URLs, mandatory disclosure, duration windows, and prohibited claims.

The current process is manual:

```
open brief → open timeline → scrub the segment → compare spoken words
against the brief → notice a mistake → re-edit → check again
```

Missing one requirement costs a revision round with the brand, a delayed payment, or a strained relationship. The cost is **per revision cycle**, not once.

SponsorLint automates the comparison step. It does not edit, generate, or negotiate.

## What it is not

- Not an AI video editor
- Not a sponsorship marketplace or CRM
- Not a legal compliance engine
- Not a generic creator assistant

It is a **linter for one high-friction step**.

---

# 3. THE WINNING DEMO NARRATIVE

Understandable in under 15 seconds. Believable in under 60.

1. "Here is a real sponsor brief — written in prose, like brands actually write them."
2. "SponsorLint compiles it into seven machine-readable rules. Each one quotes the sentence it came from."
3. "Here is my recorded sponsor read."
4. "It found three problems, with timestamps and the transcript line that proves each one."
5. "I fix them and re-run the exact same spec." → `SPONSOR READY`

**The arc is the product:** `57% → 86% → SPONSOR READY`. A verdict *flipping* because the input changed beats any static output.

## The single strongest ten seconds

The brief says *"a discount of seventy-three percent off the two-year plan."* The creator said *"up to seventy percent."* SponsorLint catches it:

```
❌ WRONG VALUE   Expected: 73%   Detected: "up to 70%"   00:43
   "You can get up to seventy percent off the two-year plan."
```

A fake demo would not bother normalizing spoken numerals. **This is the moment that proves the pipeline is real.** Over-invest in it (§10).

---

# 4. ABSOLUTE SCOPE

## 4.1 The six rule types

| Type | Checks |
|---|---|
| `MUST_SAY` | A required phrase, product name, or talking point appears |
| `MUST_NOT_SAY` | A prohibited claim does not appear |
| `EXACT_VALUE` | A number/figure matches the brief exactly |
| `MUST_DISCLOSE` | Sponsorship disclosure is present |
| `DURATION` | Segment length falls inside the required window |
| `URL_OR_CTA` | The tracked link or promo code is spoken |

## 4.2 The two additions this bible mandates

**`DISCLOSURE_PLACEMENT`** — disclosure must occur early enough to function as one.

```
⚠ DISCLOSURE PLACEMENT
  Detected at 03:47. Disclosure this late is unlikely to be
  considered clear and conspicuous.
```

Ten minutes of work on a timestamp you already compute. It is the line that signals you have spoken to someone who does this for a living. Threshold: flag if disclosure occurs after the first 25% of the segment, or after 30 seconds, whichever is earlier.

**`MANUAL_REVIEW`** — any extracted requirement that cannot be verified from audio or metadata is surfaced, not silently dropped and not faked.

```
□ MANUAL REVIEW
  "Product must be visible on screen for at least five seconds."
  SponsorLint does not verify visual requirements. Check this yourself.
```

This is a **trust feature**, not a limitation. A tool that refuses to fake a verdict is demonstrating judgment, and judgment is what Technical execution measures.

---

# 5. BANNED FROM THE MVP

Do not implement any of these until every acceptance test in §18 passes.

**Product scope:** sponsorship discovery · rate calculation · creator marketplace · brand CRM · invoicing · payment tracking · campaign analytics · contract generation · multi-campaign management · team accounts · auth · payments · billing.

**Video:** automatic editing · B-roll insertion · auto-cutting · voice replacement · AI avatars · thumbnail generation · auto-shorts · clip generation · EDL/FCPXML export · NLE plugins.

**Verification:** OCR · logo detection · object detection · face detection · any visual rule (flag as `MANUAL_REVIEW` instead) · general fact-checking · legal-compliance claims.

**Infrastructure:** database · Docker · Kubernetes · microservices · cloud deployment · vector DB · RAG · background job queue · websockets.

**Adjacent products:** any part of Cutcheck · retention analysis · multi-platform posting · SEO/title/description generation · comment moderation · scheduling.

**Specifically banned trap:** OCR via easyocr or tesseract. easyocr pulls ~2GB of torch on Windows. This is a stretch goal that eats hour 20 and returns nothing.

---

# 6. ARCHITECTURE

```
┌──────────────────┐
│ sponsor-brief    │  PDF or .md
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Brief Extractor  │  pypdf → clean text
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Requirement      │  LLM → constrained JSON
│ Compiler         │  every rule cites source_text
└────────┬─────────┘
         ▼
   sponsor-spec.json  ◄──── HUMAN EDITABLE. This is the product's soul.
         │
         │        ┌──────────────────┐
         │        │ sponsor-cut.mp4  │
         │        └────────┬─────────┘
         │                 ▼
         │        ┌──────────────────┐
         │        │ Transcriber      │  faster-whisper + ffprobe
         │        └────────┬─────────┘
         │                 ▼
         │          transcript.json  ◄──── CACHED TO DISK. Never re-run in dev.
         │                 │
         └────────┬────────┘
                  ▼
        ┌──────────────────┐
        │ Verifier         │  DETERMINISTIC. No LLM.
        │ 8 validators     │
        └────────┬─────────┘
                 ▼
          lint-results.json
                 │
                 ▼
        ┌──────────────────┐
        │ Report           │  web view + terminal
        └──────────────────┘
```

## 6.1 The LLM boundary — the central technical thesis

**The LLM compiles. It never judges.**

```
BAD:   brief + transcript → LLM → "looks compliant"
GOOD:  brief → LLM → structured rules
       video → timestamped transcript
       rules + transcript → deterministic verifier → PASS/WARN/FAIL
```

Consequences that make this a real argument and not a slogan:

- The verdict is **reproducible**. Same inputs, same output, every time.
- The verdict is **auditable**. Every FAIL cites a transcript line and a character span.
- The verdict is **testable**. §11's eval harness is only possible because the verifier is deterministic.
- The LLM's output is **inspectable and correctable** before it is used (§14, View 2).

Anticipate the objection *"isn't this just an LLM reading two files?"* — the answer is that the LLM never sees the transcript.

## 6.2 Layout

```
sponsorlint/
├── app/
│   ├── main.py              FastAPI
│   ├── schemas.py           Pydantic: Rule, Spec, Transcript, Result
│   ├── brief/
│   │   ├── extract.py       PDF/text → string
│   │   └── compile.py       string → Spec (the only LLM call)
│   ├── media/
│   │   ├── transcribe.py    faster-whisper
│   │   └── probe.py         ffprobe duration
│   ├── verify/
│   │   ├── engine.py        dispatch + readiness
│   │   ├── normalize.py     ◄── THE IMPORTANT FILE (§10)
│   │   ├── must_say.py
│   │   ├── must_not_say.py
│   │   ├── exact_value.py
│   │   ├── disclosure.py    includes placement check
│   │   ├── duration.py
│   │   └── cta.py
│   └── eval/
│       ├── fixtures.py      ~24 labeled cases
│       └── run.py           precision / recall
├── web/                     one page, served by FastAPI
├── samples/
│   ├── brief.pdf
│   ├── brief.md
│   ├── spec.json            COMMITTED — enables zero-key demo
│   ├── transcript.v1.json   COMMITTED
│   ├── transcript.v3.json   COMMITTED
│   ├── cut-v1.mp4
│   └── cut-v3.mp4
├── tests/
└── README.md
```

## 6.3 Stack

```
Python · FastAPI · Pydantic · faster-whisper (base.en, CPU) · pypdf
rapidfuzz · ffprobe · one LLM API for compilation only
```

Frontend: **one static page** served by FastAPI, talking to the API. No Next.js. No build step. If the page fights you for more than an hour, fall back to Jinja templates.

**Use `faster-whisper` `base.en` on CPU from the start.** Do not take a GPU/CUDA detour. It is the most likely single hour-sink in this build.

---

# 7. DATA CONTRACTS

```json
// Rule — note source_text, which is mandatory
{
  "id": "r2",
  "type": "EXACT_VALUE",
  "label": "Discount",
  "expected": "73%",
  "severity": "error",
  "source_text": "eligible for a discount of seventy-three percent off the two-year plan",
  "confidence": 0.94
}
```

```json
// Transcript
{
  "duration_seconds": 74.2,
  "segments": [
    { "start": 41.1, "end": 45.2, "text": "You can get up to seventy percent off." }
  ]
}
```

```json
// Result
{
  "rule_id": "r2",
  "status": "FAIL",
  "title": "Wrong discount",
  "expected": "73%",
  "detected": "70%",
  "timestamp": 43.1,
  "evidence": "You can get up to seventy percent off.",
  "evidence_span": [18, 35]
}
```

```json
// Report
{
  "status": "FAIL",
  "readiness_score": 57,
  "summary": { "pass": 4, "warn": 1, "fail": 2, "manual": 1 },
  "results": [ /* ... */ ]
}
```

`source_text` and `evidence` are **required fields**, not decorations. They are what make every claim auditable.

---

# 8. VERIFICATION STRATEGY

Layered, cheapest first, deterministic wherever possible.

| Rule | Strategy |
|---|---|
| `MUST_SAY` | normalize → exact substring → `rapidfuzz` ratio ≥ 90 → report best partial match on failure so the user sees *why* |
| `MUST_NOT_SAY` | same matching, inverted. Return timestamp + span. Beware substring traps: `anonymous` alone must not fire a rule for `"completely anonymous"` |
| `EXACT_VALUE` | full numeral normalization (§10). **Deterministic only. Never an LLM.** |
| `MUST_DISCLOSE` | phrase set + fuzzy: `sponsored by`, `this video is sponsored`, `paid partnership`, `thanks to X for sponsoring`, `sponsor of today's video` |
| `DISCLOSURE_PLACEMENT` | timestamp comparison on the disclosure result |
| `DURATION` | `ffprobe`. One call. No LLM |
| `URL_OR_CTA` | canonicalize spoken URLs and codes (§10) |

Normalization baseline for all text rules: lowercase, strip punctuation, collapse whitespace, expand common contractions.

---

# 9. READINESS LOGIC

```
any ERROR rule fails      → FAIL      → "DO NOT SEND FOR APPROVAL"
only WARNING rules fail   → WARN
all ERROR rules pass      → SPONSOR READY
```

Score: `passed weighted rules / total weighted rules × 100`. Display it, but **the binary state is what matters**. Do not overengineer scoring, do not invent tiers, do not add a twelve-level severity system.

`MANUAL_REVIEW` items are excluded from the score and listed separately. They never block `SPONSOR READY`, but they are always visible.

---

# 10. NUMERAL AND URL NORMALIZATION

**This is the file that makes the project look like engineering rather than string matching. Over-invest here.**

Whisper emits digits sometimes and words other times, unpredictably, within the same transcript. **Handle both. Test both.** This is not optional — it is the most common silent failure in this build.

Must handle:

```
"seventy-three percent"   → 73%
"seventy three percent"   → 73%
"73 percent"              → 73%
"73%"                     → 73%
"up to seventy percent"   → 70%     ← must NOT match 73%
"twenty dollars"          → $20
"$20"                     → $20
"three months free"       → 3 months
"two-year plan"           → 2 year
```

Promo codes spelled aloud:

```
"H-A-R-S-H two zero"      → HARSH20
"code alex twenty"        → ALEX20
```

Spoken URLs:

```
"aegis vpn dot com slash alex"    → aegisvpn.com/alex
"aegisvpn.com/alex"               → aegisvpn.com/alex
"aegis v p n dot com slash alex"  → aegisvpn.com/alex
```

One unit test per line above. Those tests **are** the eval fixtures in §11 — write them once, use them twice.

---

# 11. THE EVAL HARNESS

Stolen from Cutcheck's `backtest`, which its own execution bible deleted. This is 90 minutes of work and it is the highest-leverage thing in this document.

```
$ sponsorlint eval

24 labeled cases · 23 correct
false positives 0 · false negatives 1
precision 1.00 · recall 0.96

tuned for zero false positives — see README
```

## 11.1 How it works

Pure text fixtures: `(rule, transcript_snippet, expected_verdict)`. **No video. No Whisper. No LLM. Runs in under a second.**

## 11.2 Load it with hard negatives

The number is worthless without them:

| Rule | Snippet | Expected |
|---|---|---|
| `EXACT_VALUE 73%` | "up to seventy percent off" | FAIL |
| `EXACT_VALUE 73%` | "seventy-three percent off" | PASS |
| `MUST_SAY "Aegis Shield Suite"` | "try the Aegis shield today" | FAIL |
| `MUST_SAY "Aegis Shield Suite"` | "the Aegis Shield Suite is..." | PASS |
| `MUST_NOT_SAY "completely anonymous"` | "browse anonymously" | PASS *(no violation)* |
| `MUST_NOT_SAY "completely anonymous"` | "makes you completely anonymous" | FAIL |
| `MUST_DISCLOSE` | "I sponsored a little league team once" | FAIL *(no disclosure)* |
| `URL_OR_CTA aegisvpn.com/alex` | "aegis vpn dot com slash alex" | PASS |

## 11.3 The tuning stance — say this out loud

**Tune for zero false positives, and state why:**

> A false FAIL wastes the creator's afternoon. A false PASS ships a broken sponsor read to the brand. The two errors are not symmetric, so SponsorLint is tuned to never cry wolf, and reports its recall cost honestly.

That is a designed engineering tradeoff, backed by a measured number. It converts *"isn't this just string matching?"* into *"it's string matching that I measured, which is more than the rest of the field can say."*

## 11.4 Where the number goes

**In the README, above the feature list.** Most repos bury validation. Yours leads with it.

---

# 12. THE DEMO ASSETS

Build these **before writing code**. They gate every downstream test, need no code, and need your voice at full energy — which you will not have at hour 30.

## 12.1 The brief must be prose, not a bulleted list

This is the difference between "the LLM parsed a list" and "the LLM did real work." Use a fictional brand — **`Aegis VPN`, `aegisvpn.com/alex`**. Never a real company's product name in a fabricated brief with fabricated violations.

```
AEGIS VPN — CREATOR INTEGRATION BRIEF
Campaign: Q3 Summer Acquisition
Flight dates: August 1 – September 30, 2026

SCOPE OF INTEGRATION

The Creator agrees to produce one (1) integrated segment within a single
long-form video. The integration should run no shorter than a minute and
no longer than a minute and a half.

REQUIRED MESSAGING

The segment must reference the Aegis Shield Suite by name at least once.
Subscribers arriving through the Creator's tracked link are eligible for a
discount of seventy-three percent off the two-year plan, and this figure
should be stated clearly. The Creator's tracked link is aegisvpn.com/alex
and should be spoken aloud in addition to appearing on screen.

DISCLOSURE

In accordance with applicable advertising guidelines, the Creator must
disclose the commercial nature of the partnership at or near the start of
the integration.

PROHIBITED CLAIMS

Under no circumstances should the integration characterize the service as
making the user untraceable, nor should it describe the product as
impossible to compromise. Claims of absolute security are not permitted.

PRODUCTION NOTES

The product interface should be visible on screen for at least five
seconds during the segment.
```

Why every paragraph earns its place:

- `min_seconds: 60` comes from *"no shorter than a minute"* — **no regex extracts that**
- `73%` is spelled out and buried mid-sentence
- Prohibitions are phrased as negations, not as a `DO NOT SAY:` list
- The production note is unverifiable from audio → becomes `MANUAL_REVIEW`, which demonstrates the trust posture

Export to PDF with a header and reasonable typography so it looks real on screen.

## 12.2 The recorded segments

Write a ~75-second script with errors baked in at known timestamps:

| Time | Planted error |
|---|---|
| ~0:31 | "makes you completely anonymous" — prohibited claim |
| ~0:43 | "up to seventy percent" — should be 73% |
| — | Never says "Aegis Shield Suite" |

**Then do the check nobody thinks of.** Before committing to the script, transcribe *just those three sentences* with `base.en`. If Whisper garbles "seventy percent" or mangles the URL, **change the script to a mistake it can hear**. Your entire centerpiece rests on one transcription. Verify it in hour one, not hour twenty-six.

## 12.3 Build V3 cheaply

Do not record three full videos. Record V1 with all errors, then **re-record only the offending sentences and splice**. Twenty minutes, not two hours.

Render the arc as a **side-by-side report diff**. The climbing readiness score is your README GIF.

---

# 13. THE ZERO-KEY DEMO PATH

**Assume the judge never sees you.** The event is repo + README + optional video. There may be no room, no laptop, no live demo. The judge clones the repo at 2 AM and gives you sixty seconds.

Two walls kill you there, and both are on the default path right now:

- An `OPENAI_API_KEY` prompt → gone in thirty seconds
- A 140MB Whisper model download → gone in sixty

## The fix

```bash
git clone <repo> && cd sponsorlint
pip install -e .
sponsorlint demo          # no keys. no downloads. no network.
```

`sponsorlint demo` runs the **verifier live** against the committed `spec.json` and `transcript.v1.json`, then again against `transcript.v3.json` to show the arc.

```
--compile      re-run LLM extraction from the PDF   (needs a key)
--transcribe   re-run Whisper on the MP4            (downloads a model)
```

State it explicitly in the README, in one line:

> The demo runs verification live against a cached transcript. Pass `--transcribe` to run Whisper yourself, or `--compile` to re-extract the spec from the PDF.

**Caching is not cheating; fake output is.** The check must execute for real. Only the expensive, deterministic upstream steps are cached.

This costs about 30 minutes and it neutralizes Cutcheck's one genuine structural advantage — being zero-key by construction.

---

# 14. USER INTERFACE

Three views. The UI is not the product; the pipeline is. But a judge must understand it without the README.

## VIEW 1 — Upload

```
[ Sponsor brief   ]  brief.pdf
[ Sponsor segment ]  cut-v1.mp4
                              [ Run check ]
[ Load sample campaign ]   ← always present, always works
```

## VIEW 2 — Compiled spec (PROMOTED TO CORE — not a stretch goal)

**Split screen. Source prose left, extracted rule right.** Each rule shows the sentence it came from.

```
┌─ FROM THE BRIEF ──────────────┬─ EXTRACTED ─────────────────┐
│ "The integration should run   │ DURATION                    │
│  no shorter than a minute and │ min_seconds: 60             │
│  no longer than a minute and  │ max_seconds: 90             │
│  a half."                     │ severity: warning     [edit]│
└───────────────────────────────┴─────────────────────────────┘

7 requirements extracted · 1 flagged for manual review
[ + Add rule ]                              [ Run check → ]
```

**Rules must be editable, and the judge must be able to add one and re-run.**

This single screen kills three objections at once:

| Objection | Killed by |
|---|---|
| "The LLM hallucinated the requirements" | Every rule cites its source sentence |
| "You planted the errors you found" | The judge plants their own, live |
| "Can you trust an LLM to read a contract?" | You don't have to — the correction *is* the product |

Every other AI submission at this event is an oracle. Yours has a config file the user can argue with.

## VIEW 3 — Report

```
SPONSOR READINESS   57%        ❌ DO NOT SEND FOR APPROVAL
2 FAILED · 1 WARNING · 4 PASSED · 1 MANUAL REVIEW
```

Then cards, worst first, each with expected / detected / timestamp / transcript evidence / `[ Jump to 00:43 ]`.

Clicking a finding seeks the video player. High demo value, low complexity — build it if View 3 is otherwise done.

## Visual language

Speak like a linter, not an AI dashboard. Use: *rule, warning, evidence, timestamp, severity, spec, check, PASS/FAIL*. Never: *AI magic, smart insights, AI-powered score, revolutionary*.

---

# 15. PHASE PLAN

`T+0` is when you start. Deadline is Aug 17 4:30 AM IST. **The sleep block is mandatory and is in the plan for a reason** — the last four hours of a hackathon are worth nothing if you cannot think.

One correction to the prior bible: it front-loaded the upload route and PDF extraction. Both are worthless until the verifier works, and PDF parsing is twenty minutes of zero-risk work at any point. **Hand-write the spec JSON and go straight at transcript → check.**

### `T+0:00 – 0:15` — Clear the decks
- Repo, branch, `pip install faster-whisper pypdf rapidfuzz pydantic fastapi uvicorn python-multipart`
- README with three things only: title, one-sentence pitch, input/output block
- **Gate:** repo exists, deps install clean

### `T+0:15 – 1:00` — Demo assets, out loud, before any code
- Write `samples/brief.md` as **prose**, fictional brand (§12.1). Export to PDF
- Write the 75-second script with planted errors
- **Transcribe the three error sentences with `base.en` and confirm Whisper hears them.** Change the script if not
- Record V1

*Agents work in parallel:* repo skeleton, eight validator stubs each with one failing test, `ffprobe` wrapper, Pydantic schemas. Nothing that needs the video.

> **GATE 1:00** — `brief.pdf` and `cut-v1.mp4` exist, and Whisper demonstrably hears the planted errors.

### `T+1:00 – 2:10` — Vertical slice, ugly, end to end
- Transcribe V1 → **write `samples/transcript.v1.json` to disk immediately.** Never run Whisper again in development
- Hand-write `samples/spec.json`. Do not build the compiler yet
- Implement exactly one check: `MUST_SAY` with normalization

> **GATE 2:10** — one command prints one real verdict from one real video. If not, strip the compiler plan to a single prompt with no retry logic and move on.

### `T+2:10 – 3:00` — The other seven validators
- `MUST_NOT_SAY`, `EXACT_VALUE`, `MUST_DISCLOSE`, `DISCLOSURE_PLACEMENT`, `DURATION`, `URL_OR_CTA`, `MANUAL_REVIEW`
- **Give `EXACT_VALUE` half the block.** It is the hard one and the one that matters
- Write each unit test as you write each rule — this **is** the eval harness

> **GATE 3:00** — all rule types produce `2 FAIL / 1 WARN / 4 PASS / 1 MANUAL` on V1. **The project now exists. Everything after is upside.**

### `T+3:00 – 5:30` — Requirement compiler
- pypdf extraction, one LLM call, Pydantic validation, one retry on malformed JSON
- **`source_text` is mandatory on every rule.** Reject extractions without it
- Unverifiable requirements → `MANUAL_REVIEW`, never dropped

> **GATE 5:30** — the prose brief compiles to a valid spec that matches the hand-written one.

### `T+5:30 – 7:00` — Eval harness (§11)
- ~24 fixtures, heavy on hard negatives
- `sponsorlint eval` prints precision/recall
- Tune to zero false positives

> **GATE 7:00** — a real measured number exists.

### `T+7:00 – 11:00` — UI
- Views 1 and 3 first, then View 2
- Sample-campaign button that always works
- Real progress states. Do not fake progress

> **GATE 11:00** — a judge can drive it without a terminal.

### `T+11:00 – 13:30` — View 2 editable + V3 assets
- Split-screen spec review, edit a rule, add a rule, re-run
- Splice V3, transcribe, commit `transcript.v3.json`
- Verify the `57% → SPONSOR READY` arc runs clean

> **GATE 13:30** — the judge can add a rule and see it evaluated.

### `T+13:30 – 19:30` — **SLEEP. SIX HOURS. NOT OPTIONAL.**

### `T+19:30 – 22:00` — Zero-key demo path (§13)
- Commit `spec.json`, both transcripts
- `sponsorlint demo` with no keys, no downloads, no network
- `--compile` / `--transcribe` flags
- Error handling: unparseable PDF, failed transcription, empty spec — all readable, none silent

> **GATE 22:00** — fresh clone → one command → real output, under sixty seconds, no key.

### `T+22:00 – 25:00` — README (§17) + GIF
The video is optional, so **this is the primary judging surface.** Most of the field will pour hours into video and ship three lines of markdown.

### `T+25:00 – 27:00` — Testing and hardening
Run the full path from a clean clone in a fresh virtualenv. Fix what breaks. Do not add features.

### `T+27:00 – 29:00` — Optional 90-second video, only if the README is already excellent

### `T+29:00 – deadline` — Buffer. Submit with margin. **Do not touch the code.**

---

# 16. ACCEPTANCE TESTS

The MVP is complete when all of these pass.

| # | Test |
|---|---|
| 1 | A prose PDF brief compiles to a valid spec with ≥6 rules |
| 2 | Every extracted rule carries a `source_text` quoting the brief |
| 3 | An unverifiable requirement is surfaced as `MANUAL_REVIEW`, not dropped |
| 4 | The video transcribes with usable timestamps |
| 5 | All eight validators run and produce statuses |
| 6 | `EXACT_VALUE` catches "seventy percent" against a required 73% |
| 7 | `MUST_NOT_SAY` does not false-fire on a partial substring |
| 8 | Every FAIL carries a timestamp and a transcript evidence line |
| 9 | Readiness resolves to FAIL / WARN / SPONSOR READY correctly |
| 10 | V3 re-runs the same spec and reaches SPONSOR READY |
| 11 | A judge can edit a rule in the UI and re-run |
| 12 | `sponsorlint eval` prints a real precision/recall number |
| 13 | Fresh clone → `sponsorlint demo` → real output, no API key, no download |
| 14 | No hardcoded verdicts anywhere. Every result is computed |

---

# 17. README STRUCTURE

Written in judging order, not build order.

1. **One sentence + the GIF.** The readiness score climbing from 57% to SPONSOR READY. Six seconds, no narration.
2. **The 60-second quickstart.** `clone`, `pip install -e .`, `sponsorlint demo`. **State the zero-keys fact explicitly** — it is a promise most repos break.
3. **The problem, one paragraph**, from a creator's point of view. Concrete cost: another approval round, delayed payment.
4. **Does it actually work?** The eval number, the fixture count, the zero-false-positive tuning stance and why. **Put this before the feature list.** It is your strongest paragraph and most repos bury it.
5. **How it works.** The pipeline diagram and the LLM-compiles/deterministic-verifies boundary. Show `sponsor-spec.json`.
6. **Limitations, written by you.** No visual verification. Whisper accuracy bounds. Checks the supplied brief, not the law. Say it before a judge does.
7. **Full setup** — API key for `--compile`, model download for `--transcribe` — last, because it is the part that can fail on someone else's machine.

Opening line:

> **Every other tool here generates content. This one checks it.**

---

# 18. CLAIMS

## Allowed

- SponsorLint converts a sponsor brief into executable checks
- It verifies the recorded integration against the supplied requirements
- It reports timestamped evidence for every finding
- It is tuned for zero false positives, measured over N labeled cases
- It flags requirements it cannot verify instead of guessing

## Forbidden

- "Legally compliant" — you check the brief, not the law
- "Guarantees sponsor approval"
- "Verifies visual requirements" — you do not
- "100% accurate" — you have a measured number; use it
- Any claim the eval harness does not support

---

# 19. JUDGE OBJECTIONS

**"Isn't this just an LLM reading two files?"**
The LLM never sees the video or the transcript. It only compiles brief prose into a constrained spec, and every rule cites the sentence it came from. The verdicts come from deterministic validators, which is why they are reproducible and why they can be measured — see `sponsorlint eval`.

**"Why not just ask ChatGPT?"**
ChatGPT can summarize a brief. It cannot give you a repeatable pass/fail with a timestamp and a transcript span, a reusable machine-readable spec you can re-run against v2 and v3, or a measured false-positive rate.

**"Isn't this just string matching?"**
The verification half is deterministic string and numeral work, deliberately. That is the architecture, not an accident — it is what makes the results auditable and testable. The interesting parts are the compilation of prose into a spec, and normalization: catching "up to seventy percent" against a required 73% is not a substring match.

**"You wrote the brief and planted the errors."**
Add a rule in View 2 and re-run. The spec is editable and the verifier does not know which rules came from me.

**"What about visual requirements?"**
Flagged as `MANUAL_REVIEW`. The MVP does not verify them and does not pretend to.

**"Only n=24 in your eval."**
Correct, and it is stated. It is 24 more labeled cases than most submissions have, the fixtures are in the repo, and the hard negatives are the ones that matter.

---

# 20. FAILURE MODES

| Failure | Response |
|---|---|
| PDF unparseable | "Could not extract readable text." Offer paste-text fallback |
| Whisper fails | "Could not transcribe." Do not silently continue |
| Whisper garbles a planted error | Caught at `GATE 1:00`. Re-record the sentence |
| Compiler returns malformed JSON | Pydantic validation + one retry. Worst case, ship the committed `spec.json` and repair after |
| Compiler is uncertain | Emit `confidence` and `needs_review: true`. Never fake certainty |
| Requirement not objectively verifiable | `MANUAL_REVIEW`. Never fake a verdict |
| UI fights you >1 hour | Fall back to Jinja templates. The pipeline matters more |
| Behind schedule | Cut in this order: demo video → jump-to-timestamp → View 2 editing → View 2 entirely → web UI (ship the CLI) |

**Never cut:** the eval number · the zero-key demo path · the README.

---

# 21. PRIORITY ORDER

1. End-to-end verifier loop
2. Correct findings with timestamps and evidence
3. The eval number
4. Zero-key clone-and-run
5. README
6. Compiled-spec review screen
7. Web UI
8. The V1→V3 arc
9. Demo video
10. Everything else

**A beautiful UI with fake analysis loses. A CLI with real, measured analysis wins.**

---

# 22. AGENT OPERATING RULES

1. Do not add a feature because it is easy.
2. Do not add a dependency that does not serve an acceptance test.
3. Do not put an LLM anywhere in the verification path.
4. Do not fabricate a verdict, a timestamp, or a score.
5. Do not drop a requirement you cannot verify — flag it `MANUAL_REVIEW`.
6. Do not redesign working architecture for elegance.
7. Do not build stretch goals before §16 passes.
8. Do not fold in any part of Cutcheck. A solo 36-hour build cannot carry two products.
9. Do not build OCR, visual verification, a database, or auth.
10. When unsure whether something is in scope, it is **out of scope**.

---

# 23. IF RETENTION DATA ARRIVES MID-BUILD

You will be tempted. **Do not switch.**

Cutcheck from a cold start in the remaining hours, with data landing mid-build and no validation harness, is a worse bet than a finished SponsorLint — and you would be abandoning certain progress for a project with four more gates ahead of it.

Bank the data. Cutcheck is a genuinely good post-hackathon project and it will still be good in September, when you can build it properly, with `backtest`, and with the promise–payoff analysis this hackathon version would have had to cut.

---

# 24. DEFINITION OF DONE

```
PROSE SPONSOR BRIEF
        ↓
  LLM COMPILER  ──→  sponsor-spec.json  (editable, source-cited)
        ↓
RECORDED SPONSOR SEGMENT
        ↓
   TRANSCRIPT (timestamped, cached)
        ↓
DETERMINISTIC VERIFIER
        ↓
TIMESTAMPED PASS / WARN / FAIL
   + transcript evidence
   + manual-review flags
   + readiness state
        ↓
   FIX → RE-RUN → SPONSOR READY
```

Plus: a measured eval number, and a stranger can run all of it in sixty seconds with no API key.

When this works reliably: **stop building. Test. Write the README. Submit with margin.**

---

# 25. NORTH STAR

> **SponsorLint turns a sponsor brief into executable checks and tells you exactly which requirement you missed, where, and what you actually said — before the brand finds out.**

If a change does not make that sentence more true, do not build it.

## The one metric

> **Under 15 seconds to understand. Under 60 seconds to believe. Under 60 seconds to run.**

The goal is not to be unbeatable — nothing is, and 20% of the rubric is taste. The goal is to be **un-dismissable**: no judge can finish the sentence *"this doesn't work"* or *"I've seen this one."*
