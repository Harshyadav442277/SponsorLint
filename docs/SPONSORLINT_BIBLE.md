# SPONSORLINT — THE BIBLE
## Scope Contract · Architecture · Build Phases · Validation · Demo Strategy · Agent Guardrails

**Status:** REFERENCE NARRATIVE — the whole plan in one file. **Not the authority.**
**Hackathon:** Social Media Automation Hackathon
**Deadline:** Aug 17, 2026 @ 4:30 AM IST
**Judging:** Functionality 30% · Real-world usefulness 30% · Creativity 20% · Technical execution 20%

> **Pre-flight QA for sponsored YouTube integrations.**
>
> ESLint catches mistakes before you ship code. SponsorLint catches mistakes before you send a sponsored integration to the brand.

---

# 0. WHAT THIS FILE IS — READ THIS FIRST

This is the **single-file reference narrative**: the entire plan, readable end to end, useful for onboarding a person, pasting into a tool that wants one document, or writing the submission blurb.

**It is not the build contract.** The seven documents at repo root are:

| File | Authority over |
|---|---|
| `PRD.md` | What we are building, for whom, acceptance criteria |
| `Architecture.md` | Pipeline, stack, schemas, verification strategy |
| `Rules.md` | What agents may and may not do |
| `Phases.md` | Build order, gates, the clock |
| `Design.md` | Colors, typography, components, CLI output |
| `Decisions.md` | Why the project is shaped this way |
| `Memory.md` | Live progress state |

## Precedence

> **If this file and a root document disagree, the root document wins — always, without discussion.**

Nothing is implemented from this file. Implement from `PRD.md` + `Architecture.md`, sequence from `Phases.md`, and stay inside `Rules.md`.

## Why this file can still be trusted

It was reconciled with the root documents on Aug 15, 2026 and carries the four freeze corrections in `Decisions.md` D19: the validator taxonomy (§10), no invented disclosure threshold (§12), `False FAIL` / `False PASS` terminology (§16), and no engineered scores (§9).

**Anyone editing a root document must either update this file to match or downgrade it to `STALE` in this header.** A reference narrative that has silently drifted is worse than no reference narrative — it is exactly the conflicting-authority failure every version of this plan has warned about.

> The main risk is not insufficient ambition. It is **building too much and weakening the one workflow judges need to believe.**

---

# 1. NORTH STAR

## The job to be done

> **"Before I send this sponsor cut for approval, did I actually follow the sponsor brief?"**

That is the entire product.

## The user

**A YouTube creator or video editor handling a paid sponsor integration.**

Do not broaden to agencies, advertiser dashboards, brand teams, TikTok/Instagram creators, influencer marketplaces, social media managers, generic creators, or compliance departments.

## The moment of use

```
record / edit sponsor segment
        ↓
BEFORE sending it to the sponsor
        ↓
   run SponsorLint
        ↓
 fix concrete violations
        ↓
   send for approval
```

**After creation, before approval.** That exact moment is the product.

## The thesis

Most social-media automation tools **generate** something. SponsorLint **checks** something.

> It is a linter for a high-friction creator workflow that has a concrete external specification. The sponsor brief is the spec. The recorded segment is the artifact.

---

# 2. POSITIONING

README opening line:

> **Every other tool generates content. This one checks it.**

Then:

> SponsorLint turns a sponsor brief into executable checks and runs them against the actual recorded sponsor integration.

Then:

> **Sponsor brief → executable requirements → sponsor video → timestamped PASS / WARN / FAIL.**

Do not lead with Whisper, LLMs, FastAPI, ffmpeg, "AI-powered," model names, or architecture diagrams. **Lead with the saved workflow.**

## The judge is probably not in the room

The event is **repo + README + optional video**. Assume no live demo, no laptop, no chance to explain. A judge clones the repo at 2 AM and gives you sixty seconds.

Two consequences that drive real decisions:

- **The README is the primary judging surface** (§22). Most of the field will pour hours into a video and ship three lines of markdown.
- **The zero-key clone-and-run path** (§17) is worth more than any UI polish.

---

# 3. PRODUCT CONTRACT

**Accepts exactly:**
```
1 sponsor brief
1 recorded sponsor segment
```

**Returns exactly:**
```
1 reviewed, approved structured specification
1 timestamped verification report
1 overall readiness state
```

**Action states:**
```
DO NOT SEND      a blocking requirement failed
REVIEW           no blocking failure, but warnings or manual-review items exist
SPONSOR READY    all blocking requirements passed
```

A percentage score is optional and secondary. The binary state is what matters.

---

# 4. CORE ARCHITECTURE PRINCIPLE

## LLM = COMPILER. DETERMINISTIC CODE = VERIFIER.

The LLM may interpret the brief. It must **never** be the final judge of whether a recorded segment passed, where deterministic verification is possible.

**Wrong:**
```
brief + transcript → LLM → "looks compliant"
```

**Correct:**
```
        messy sponsor brief
                ↓
        requirement compiler          ← the only LLM call
                ↓
        sponsor-spec.json
                ↓
    USER REVIEWS / EDITS SPEC         ← the trust boundary
                ↓
     approved specification
                ↓
        ┌───────┴───────┐
        │        recorded MP4
        │               ↓
        │      timestamped transcript
        └───────┬───────┘
                ↓
      deterministic validators
                ↓
        PASS / WARN / FAIL
                ↓
   timestamp + transcript evidence + source quote
```

## The trust model, in one sentence

> **The model proposes the specification. The user owns the specification. Deterministic code enforces the approved specification.**

This separation is the project's strongest technical talking point. It is also why §18's eval harness is possible at all — you cannot measure a nondeterministic verdict.

---

# 5. DEMO BRAND AND FIXTURES

Use a completely fictional sponsor. Never a real company's product name or campaign URL inside a fabricated brief with fabricated violations.

```
Brand:     Aegis VPN
URL:       aegisvpn.com/alex
Feature:   Shield Mode
Discount:  73%
Promo:     HARSH20
```

## The demo brief — build this exactly

The brief must be **prose, not a checklist**. If it is already a neat bulleted list, the compiler looks trivial and the whole architecture argument collapses into "I asked an LLM to read a formatted document."

```text
Aegis VPN — Creator Integration Brief
Campaign: Q3 Acquisition · Flight: Aug 1 – Sep 30, 2026

Please make clear near the beginning of the integration that this video
is sponsored by Aegis VPN. The integration should run no shorter than
one minute and no longer than one minute and thirty seconds.

When discussing the promotion, viewers should be told that they can save
seventy-three percent using the campaign offer, and should be directed to
aegisvpn.com/alex. Please mention Shield Mode by name at least once.

Avoid describing Aegis VPN as "completely anonymous" or "unhackable."

The closing should include a direct call to action telling viewers to
visit the campaign URL. The product interface should be visible on screen
for at least five seconds during the segment.
```

**Every sentence earns its place. Do not "improve" this brief:**

| Phrasing | Why it is written that way |
|---|---|
| *"no shorter than one minute and no longer than one minute and thirty seconds"* | → `DURATION 60–90`. **No regex extracts that.** This is the compiler's proof of work. |
| *"save seventy-three percent"* | Spelled out, buried mid-sentence. This is what makes numeral normalization (§13) visibly non-trivial. **Do not write `73%` as digits here.** |
| *"completely anonymous" or "unhackable"* — quoted literally | A deterministic `MUST_NOT_SAY` needs the literal phrase. Paraphrasing the prohibition ("do not describe it as untraceable") creates a semantic gap the verifier cannot bridge and silently breaks the demo. |
| *"near the beginning"* | The brief **does** specify placement, so `DISCLOSURE_PLACEMENT` becomes enforceable rather than advisory (§12). |
| *"visible on screen for at least five seconds"* | Unverifiable from audio → `MANUAL REVIEW`. Demonstrates the trust posture (§11). |

Yield: **7 checkable rules + 1 manual review**, exercising every rule type.

Export to `samples/brief.pdf` with a header and reasonable typography so it reads as real on screen.

---

# 6. CORE DEMO NARRATIVE

Record one ~75-second segment containing known mistakes:

| | |
|---|---|
| ❌ | says **"seventy percent"** instead of seventy-three |
| ❌ | never says **"Shield Mode"** |
| ❌ | says **"completely anonymous"** around 0:31 |
| ✓ | valid sponsorship disclosure, early |
| ✓ | correct campaign URL |
| ✓ | CTA present |
| ✓ | duration inside 60–90s |

Expected output:

```text
❌ WRONG VALUE          Expected: 73%   Detected: "seventy percent"   00:43
   "You can save up to seventy percent using my link."

❌ REQUIRED MENTION     Expected: "Shield Mode"   Not found

❌ PROHIBITED CLAIM     Detected: "completely anonymous"              00:31
   "It keeps you completely anonymous online."

□  MANUAL REVIEW        "Product interface visible for at least five seconds."
                        SponsorLint does not verify visual requirements.

DO NOT SEND
```

Fix only the offending lines, rerun the same approved spec:

```text
✓ SPONSOR READY — all blocking requirements passed.
```

## Do not record three full videos

Record one good base take. Re-record **only the incorrect sentences** and splice them in. Twenty minutes, not two hours. The `DO NOT SEND → SPONSOR READY` arc is preserved without burning build time.

---

# 7. RULE TYPES — HARD LIMIT

Six families. Do not add a seventh before §21 passes.

### `MUST_SAY`
A required phrase, product name, or talking point must appear.
```
normalized exact match → safe fuzzy match → FAIL or MANUAL REVIEW
```

### `MUST_NOT_SAY`
A prohibited phrase must not occur. Return matched wording, timestamp, transcript evidence.
**Substring trap:** bare `anonymous` must not fire a rule for `"completely anonymous"`.

### `EXACT_VALUE`
Exact numeric or code-like values: `73%`, `$20`, `3 months`, `HARSH20`.
**One of the two technical centerpieces.** Deterministic only. Never an LLM. Never fuzzy (§14).

### `MUST_DISCLOSE`
Detect sponsorship disclosure and its timestamp.
```
sponsored by · this video is sponsored by · paid partnership
thanks to X for sponsoring · today's sponsor is
```

### `DURATION`
`ffprobe` against the brief's min/max. One call. No LLM.

### `URL_OR_CTA`
Expected URL, promo code, or CTA — spoken or written forms (§15).

---

# 8. SPEC SCHEMA

```json
{
  "campaign": "Aegis VPN Creator Campaign",
  "rules": [
    {
      "id": "r1",
      "type": "MUST_SAY",
      "label": "Required feature name",
      "expected": "Shield Mode",
      "source_quote": "Please mention Shield Mode by name at least once.",
      "severity": "error",
      "needs_review": false
    },
    {
      "id": "r2",
      "type": "EXACT_VALUE",
      "label": "Campaign discount",
      "expected": "73%",
      "source_quote": "viewers should be told that they can save seventy-three percent",
      "severity": "error",
      "needs_review": false
    }
  ]
}
```

**`source_quote` is mandatory on every rule.** Reject any extraction without it. It is what makes each rule auditable and what powers the split-screen review (§10).

The compiler must never invent a rule, and must preserve exact numbers, product names, URLs, promo codes, and prohibited language verbatim.

## Transcript contract

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

Segment timestamps are sufficient. Word timestamps are nice, not required.

## Result schema

```json
{
  "status": "FAIL",
  "summary": { "pass": 4, "warn": 1, "fail": 2, "manual_review": 1 },
  "results": [
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
  ]
}
```

Every failure answers five questions: **what was required, what was detected, where, what evidence, and where did the requirement come from.**

---

# 9. THE REQUIREMENT COMPILER

Important, but **not the first thing to build** (§20, Phase 5).

```text
Convert the sponsor brief into a constrained machine-readable
verification specification.

Extract only requirements that can reasonably be checked from the
spoken content or the duration of the recorded sponsor integration.

For every extracted rule:
- preserve a verbatim source_quote
- preserve exact numbers, product names, URLs, promo codes
- preserve prohibited language verbatim
- use only the six allowed rule types
- never invent a requirement
- never infer an unsupported requirement
- set needs_review=true when uncertain

Requirements that cannot be verified from audio or duration must be
returned as MANUAL_REVIEW, not dropped and not guessed.

Return data matching the supplied schema.
```

Pydantic validation is mandatory. One retry on malformed JSON, then surface the error — do not loop.

---

# 10. BRIEF REVIEW IS CORE, NOT STRETCH

The user must see and approve the extracted spec **before** verification runs.

```text
┌─ SOURCE BRIEF ─────────────────┬─ COMPILED REQUIREMENTS ──────────┐
│                                │                                  │
│ "...run no shorter than one    │ DURATION                         │
│  minute and no longer than     │ min_seconds: 60                  │
│  one minute and thirty         │ max_seconds: 90                  │
│  seconds."                     │ severity: warning   [Edit][Del]  │
│                                │                                  │
│ "...they can save seventy-     │ EXACT_VALUE                      │
│  three percent..."             │ Discount = 73%                   │
│                                │ severity: error     [Edit][Del]  │
└────────────────────────────────┴──────────────────────────────────┘

7 requirements extracted · 1 flagged for manual review

[ + Add Requirement ]                    [ Approve & Check Video → ]
```

The user can **edit, delete, add, and approve**. The approved spec — not the raw extraction — is what enters the verifier.

## Why this single screen is worth more than any other UI work

| Objection | Killed by |
|---|---|
| "The LLM hallucinated the requirements" | Every rule cites its source sentence |
| "You planted the errors you found" | The judge adds their own rule and re-runs |
| "Can you trust an LLM to read a contract?" | You don't have to — the correction **is** the product |

Every other AI submission at this event is an oracle. Yours has a spec the user can argue with.

---

# 11. UNVERIFIABLE REQUIREMENTS

```
"Show the app clearly."          "Keep the tone enthusiastic."
"Make the product look premium." "Display the logo for five seconds."
```

Unless a reliable validator exists, output **`MANUAL REVIEW`**. Never let the LLM invent confidence.

`MANUAL REVIEW` items are excluded from the score, listed separately, and never block `SPONSOR READY` — but they are always visible.

This is a **trust feature**, not a limitation. A tool that refuses to fake a verdict is demonstrating judgment, and judgment is what Technical execution measures.

## Count the check surface this way

```
6 executable rule types
+ 1 disclosure-placement advisory   (a property of the MUST_DISCLOSE result — §12)
+ 1 MANUAL_REVIEW outcome           (what happens when no validator exists)
```

**There are six validators.** `MANUAL_REVIEW` is not a validator — it is the outcome when no supported validator applies. Disclosure placement is not a seventh rule type. Never write "seven rule types" or "eight validators."

---

# 12. DISCLOSURE PLACEMENT

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

**No invented threshold.** Do not flag on "after 25% of the segment" or "after 30 seconds" or any other number we made up. A rule not derived from the sponsor brief is a requirement we are inventing on the creator's behalf — and it edges toward the legal-compliance claim §24 bans.

**Never emit regulatory language.** No *"clear and conspicuous,"* no *"FTC,"* no *"legally required."* We check the supplied brief, not the law.

---

# 13. NORMALIZATION ENGINE

A shared deterministic module. Ordered pipeline:

```
raw text → unicode → case → punctuation → whitespace
        → numbers → currency/percent → URLs → promo codes
        → comparison-ready representation
```

## Spoken numbers — core, not polish

**Whisper emits digits sometimes and words other times, unpredictably, within the same transcript. Support both. Test both.** This is the most common silent failure in this build.

Must compare equal:
```
73%   ·   73 percent   ·   seventy-three percent   ·   seventy three percent
$20   ·   twenty dollars   ·   20 dollars
3 months   ·   three months
```

Must **not** compare equal:
```
70%   vs   73%
```

## Promo codes
```
"H-A-R-S-H two zero"  ·  "HARSH two zero"  ·  "HARSH20"   →   HARSH20
```

## URLs
```
aegisvpn.com/alex
aegis vpn dot com slash alex
aegisvpn dot com slash alex
www.aegisvpn.com/alex
```
Normalize spaces, verbal punctuation, optional `www`, scheme, casing, trailing slash. **Always return the original transcript text as evidence.**

---

# 14. MATCHING POLICY

Three states:

| Outcome | State |
|---|---|
| Exact or canonical match | `PASS` |
| Deterministic mismatch | `FAIL` |
| Ambiguous | `MANUAL REVIEW` |

**Fuzzy matching is acceptable** for minor transcription noise in names and phrases — `"Shield Mode"` versus a small tokenization error.

**Fuzzy matching is never acceptable for numeric values.** `70` is not `73`.

> **Do not loosen a fuzzy threshold to make the demo pass.** If you find yourself tuning a threshold to turn a FAIL green, you have broken the product.

---

# 15. CLI SURFACE

Decomposed so the project is debuggable and falsifiable in pieces.

```bash
sponsorlint demo                                   # zero-key, cached fixtures, real verifier
sponsorlint verify --spec S.json --transcript T.json   # deterministic checks only
sponsorlint transcribe cut.mp4                     # Whisper → transcript JSON
sponsorlint compile brief.pdf                      # PDF + LLM → proposed spec
sponsorlint analyze brief.pdf cut.mp4              # the full flow
sponsorlint eval                                   # validator metrics
```

---

# 16. THE EVAL HARNESS — CORE, NOT STRETCH

**24–30 pure-text fixtures. No video. No Whisper. No API calls. Runs in under a second.**

This is the single highest-leverage feature in the build, and almost no submission in the field will have one.

## Fixtures — load with hard negatives

The number is worthless without them.

| Rule | Transcript | Expected |
|---|---|---|
| `MUST_SAY "Shield Mode"` | "Try Shield Mode today." | PASS |
| `MUST_SAY "Shield Mode"` | "Try the shield feature today." | FAIL |
| `EXACT_VALUE 73%` | "save seventy-three percent" | PASS |
| `EXACT_VALUE 73%` | "save seventy percent" | **FAIL** |
| `MUST_NOT_SAY "completely anonymous"` | "This makes you completely anonymous." | FAIL |
| `MUST_NOT_SAY "completely anonymous"` | "browse anonymously" | PASS (no violation) |
| `MUST_DISCLOSE` | "I sponsored a little league team once." | FAIL |
| `URL_OR_CTA aegisvpn.com/alex` | "aegis vpn dot com slash alex" | PASS |
| `EXACT_VALUE HARSH20` | "use code H-A-R-S-H two zero" | PASS |

## Output

```text
SponsorLint Validator Evaluation
--------------------------------
Fixtures:          28
Correct:           27
Incorrect:          1
Accuracy:        96.4%

False FAILs:        0
False PASSes:       1
Manual Review:      3
```

**Do not fabricate perfection.** Publish whatever the real number is.

## Tuning policy — state this out loud

> A false FAIL wastes the creator's afternoon. A false PASS ships a broken sponsor read to the brand. The two errors are not symmetric.
>
> **Avoid false FAILs. Route ambiguity to MANUAL REVIEW. Then maximize violation catch rate.**

That is a designed engineering tradeoff, backed by a measured number. It converts *"isn't this just string matching?"* into *"it's string matching that I measured, which is more than the rest of the field can say."*

**The number goes in the README above the feature list** (§22).

---

# 17. ZERO-KEY, FAST CLONE-TO-OUTPUT

Two walls kill you with an async judge, and both are on the default path unless you fix them:

- an `OPENAI_API_KEY` prompt → gone in thirty seconds
- a Whisper model download → gone in sixty

## The deliverable

```bash
git clone <repo> && cd sponsorlint
pip install -r requirements-demo.txt
python -m sponsorlint demo
```

Runs the **real deterministic verifier** against committed fixtures:

```
samples/spec.approved.json
samples/transcript.v1.json
samples/video-metadata.v1.json
```

No API key. No network. No model download. **No hardcoded verdicts.**

Heavy dependencies (`faster-whisper`, LLM client) go in a separate `requirements.txt`, documented but not required for the demo.

State it in the README in one line:

> The demo runs verification live against a cached transcript. Pass `--transcribe` to run Whisper yourself, or `--compile` to re-extract the spec from the PDF.

> **Caching is not cheating; fake output is.** The check must execute for real. Only the expensive, deterministic upstream steps are cached.

## Reproducibility rule

Before submission, run from a clean clone in a fresh virtualenv. The default demo must not secretly depend on:

- local absolute paths
- files outside the repo
- hidden environment variables
- a running database
- a developer-only model path
- a forgotten API service

---

# 18. STACK

## Backend
```
Python · FastAPI · Pydantic · pypdf · faster-whisper · ffmpeg/ffprobe · RapidFuzz
```

**Use `faster-whisper` with the `base.en` model on CPU, from the start.** Do not take a GPU/CUDA detour — it is the most likely single hour-sink in this build and it buys you nothing on a 75-second clip.

The LLM API is optional. **The default demo must not depend on it.**

## Frontend
```
FastAPI · Jinja2 · vanilla JavaScript · plain CSS
```

**Do not start Next.js.** React only if it is already clearly faster for you. No SSR, no component library, no auth routing, no framework architecture.

## No infrastructure project
No PostgreSQL, Redis, ORM, migrations, accounts, campaign history, Kubernetes, queues, microservices, object storage, or deployment architecture. Files and in-memory structures. **Docker must not be required to run the judge demo.**

---

# 19. FOLDER STRUCTURE

```text
sponsorlint/
├── sponsorlint/
│   ├── __main__.py
│   ├── cli.py
│   ├── models.py
│   ├── brief/          extract.py · compile.py · schema.py
│   ├── transcript/     transcribe.py · schema.py
│   ├── normalize/      text.py · numbers.py · urls.py · codes.py
│   ├── lint/           engine.py · must_say.py · must_not_say.py
│   │                   exact_value.py · disclosure.py · duration.py · cta.py
│   ├── report/         render.py
│   └── eval/           runner.py · fixtures.json
├── web/                templates/ · static/
├── samples/
│   ├── brief.md · brief.pdf
│   ├── spec.approved.json
│   ├── transcript.v1.json · transcript.v3.json
│   ├── video-metadata.v1.json
│   └── sponsor-cut-v1.mp4
├── tests/
├── README.md
├── requirements-demo.txt      # zero-key path only
├── requirements.txt           # full: whisper, LLM client
└── SPONSORLINT_BIBLE.md
```

Do not reorganize a working repo for aesthetics.

---

# 20. BUILD PHASES

**Never build horizontally.** Do not start PDF parsing + Whisper + LLM + six validators + UI at once.

```
handwritten approved spec + cached real transcript
                ↓
        ONE deterministic validator
                ↓
            real verdict
```

Only then add the surrounding machinery.

`T+0` is when you start. **The sleep block is mandatory.** You are one person and the last four hours are worth nothing if you cannot think.

---

### `T+0:00 – 0:15` · Setup and scope freeze
Repo. Copy this bible in. README with title, pitch, input/output block only. Install: `fastapi uvicorn jinja2 pydantic pypdf rapidfuzz python-multipart`.

> **GATE** — repo exists, deps install clean.

---

### `T+0:15 – 1:00` · PHASE 0 — Demo assets first
1. Write `samples/brief.md` **exactly as specified in §5**. Export `brief.pdf`.
2. Write the ~75-second script with the three planted errors.
3. **Test-transcribe just the three error sentences with `base.en`, right now.**
4. **If Whisper mangles the centerpiece, change the wording now** — not at hour twenty-six.
5. Record V1.

*Agents scaffold in parallel:* repo skeleton, six validator stubs each with one failing test, `ffprobe` wrapper, Pydantic schemas. Nothing that needs the video.

> **GATE** — brief and V1 exist; the numeric error, the prohibited phrase, and the disclosure all transcribe reliably.

---

### `T+1:00 – 2:10` · PHASE 1 — Verifier vertical slice
Do **not** build the compiler or the upload UI first.

1. Hand-write `samples/spec.approved.json`
2. Transcribe V1 **once** → save `samples/transcript.v1.json`. **Never run Whisper again in development.**
3. Basic normalization
4. One validator: `MUST_SAY`
5. Print a real PASS/FAIL

> **GATE 2:10** — one command produces one real verdict from the cached real transcript. **If this fails, stop all UI and compiler work.**

---

### `T+2:10 – 3:15` · PHASE 2 — The six validators
In order: `MUST_SAY` → `MUST_NOT_SAY` → `EXACT_VALUE` → `MUST_DISCLOSE` → `DURATION` → `URL_OR_CTA`.

**Give `EXACT_VALUE` disproportionate attention.** For each: write the failing test, implement, pass, run on V1, move on.

> **GATE 3:15** — all six families produce expected verdicts on V1. **The deterministic core now exists. Everything after this is upside.**

---

### `T+3:15 – 5:15` · PHASE 3 — Normalization depth + eval harness
Numbers, currency, URLs, promo codes. Then 24–30 fixtures and `sponsorlint eval`.

> **GATE 5:15** — real metrics printed. No hardcoded score. False FAILs and false PASSes both visible.

---

### `T+5:15 – 7:00` · PHASE 4 — Zero-key demo path
Commit `spec.approved.json`, `transcript.v1.json`, `video-metadata.v1.json`. Wire `python -m sponsorlint demo`. Split `requirements-demo.txt` from `requirements.txt`.

> **GATE 7:00** — fresh clone → one command → real output. No key, no download, under sixty seconds.
>
> **You are now submittable.** A CLI with real, measured analysis and a working quickstart already satisfies the event's rules. Everything past here raises the ceiling; nothing past here is load-bearing.

---

### `T+7:00 – 9:30` · PHASE 5 — PDF extraction + compiler
Text extraction, constrained prompt, structured parse, Pydantic validation, `source_quote` preserved, uncertainty preserved, unsupported types rejected.

> **GATE 9:30** — the realistic prose brief produces the intended spec with no invented requirements, and `min_seconds: 60` came out of *"no shorter than one minute."*

---

### `T+9:30 – 12:00` · PHASE 6 — Editable spec review
Split-screen source/rules. Edit, delete, add, approve. The approved spec enters the verifier.

> **GATE 12:00** — **changing `73%` to `70%` in the approved spec changes the actual verdict.** This is the test that proves the spec drives the verifier and is not decorative.

---

### `T+12:00 – 13:30` · PHASE 7 — Full MP4 flow
Fresh MP4 → faster-whisper → timestamps → duration → transcript JSON → verifier. Cache successful transcripts during development.

> **GATE 13:30** — fresh MP4 in, real report out.

---

### `T+13:30 – 19:30` · **SLEEP. SIX HOURS. NOT OPTIONAL.**

---

### `T+19:30 – 23:30` · PHASE 8 — Web UI
Upload → Compile → Review/edit → Upload video → Run check → report. Real progress states only; **do not fake progress**. Sample-campaign button that always works.

> **GATE 23:30** — a nontechnical judge understands what failed and why, without a terminal.

---

### `T+23:30 – 25:00` · PHASE 9 — The demo arc
Splice corrected lines into the base take. Transcribe, commit `transcript.v3.json`. Capture `DO NOT SEND → SPONSOR READY` as a side-by-side report diff or GIF.

---

### `T+25:00 – 27:30` · PHASE 10 — README + visuals
See §22. This is the primary judging surface. Budget accordingly.

---

### `T+27:30 – 29:30` · Clean-environment reproduction
Fresh clone, fresh virtualenv, run everything. Fix what breaks. **Add no features.**

---

### `T+29:30 – deadline` · Buffer
Optional 90-second video only if the README is already excellent. Submit with margin. **Then stop touching the code.**

---

# 21. MVP ACCEPTANCE TESTS

Complete only when all pass.

1. Approved spec + transcript produces deterministic results
2. `MUST_SAY` pass/fail works
3. `MUST_NOT_SAY` returns violation + timestamp, and does not false-fire on a partial substring
4. "seventy-three percent" **passes** 73%
5. "seventy percent" **fails** 73%
6. Spoken URL normalizes correctly
7. At least one spoken promo-code form normalizes correctly
8. Sponsorship disclosure detected with timestamp
9. `ffprobe` duration validation works
10. Realistic prose brief compiles to valid schema
11. Every compiled rule carries a `source_quote`
12. Unverifiable requirements surface as `MANUAL REVIEW`, not dropped
13. User can edit / add / delete rules
14. **Edited spec changes the real verdict**
15. Fresh MP4 can be transcribed and verified
16. `sponsorlint eval` reports actual metrics
17. `sponsorlint demo` works without LLM credentials or a model download
18. Every failure shows expected / detected / timestamp / evidence / source quote
19. Blocking failure produces `DO NOT SEND`; all blocking passing produces `SPONSOR READY`
20. **No hardcoded verdicts anywhere.** Every result is computed

**If these pass, stop adding features.**

---

# 22. README — THE PRIMARY JUDGING SURFACE

The video is optional. This is the deliverable. Write it in judging order, not build order.

1. **Category line + GIF.** *"Every other tool generates content. This one checks it."* The GIF is `DO NOT SEND → SPONSOR READY`, six seconds, no narration.
2. **The problem**, one paragraph, from a creator's mouth. Concrete cost: another approval round, delayed payment.
3. **Input / output block.**
4. **60-second quickstart** — clone, install, `demo`. **State the zero-keys fact explicitly**; it's a promise most repos break.
5. **Does it actually work?** — the real `sponsorlint eval` numbers, the fixture count, the avoid-false-FAILs policy and why. **Put this before the feature list.** It is your strongest paragraph and most repos bury it.
6. **How it works** — compiler → editable spec → deterministic validators. Show `sponsor-spec.json`.
7. **Rule types.**
8. **Limitations**, written by you. No visual verification. Whisper accuracy bounds. Checks the supplied brief, not the law.
9. **Full run instructions** — API key, model download — last, because that's the part that can fail on someone else's machine.

## Four things the README must prove

| | |
|---|---|
| Specific workflow | brief → checks → recorded segment → violations |
| Real execution | actual output, not a mockup |
| Not an LLM wrapper | compiler → editable spec → deterministic validators |
| Tested | actual `sponsorlint eval` numbers |

---

# 23. DEMO VIDEO

Only if time remains. Two minutes, three maximum.

```
problem → messy brief → compiled editable rules → run V1
→ 70 vs 73 + prohibited phrase + missing feature
→ run corrected version → SPONSOR READY → eval proof, briefly
```

Close on:

> **Catch the sponsor mistake before the sponsor does.**

---

# 24. CLAIMS

## Allowed
- Checks a recorded sponsor segment against the supplied brief
- Produces timestamped evidence for supported requirements
- Catches exact-value mistakes such as 70% vs 73%
- Converts messy sponsor instructions into a reviewed machine-readable specification
- Reruns the same checks after edits
- Reduces repetitive pre-approval QA
- Is tuned to avoid false FAILs, measured over N labeled cases

## Forbidden
- Guarantees sponsor approval
- Guarantees legal compliance / "makes a video legally compliant"
- Verifies every kind of requirement
- Replaces brand review
- Catches every possible mistake
- Any claim the eval harness does not support

---

# 25. JUDGE OBJECTIONS

**"Isn't this just ChatGPT reading two files?"**
> The model only compiles messy brief language into a constrained, editable specification — it never sees the transcript. Final verification is rerunnable code over timestamped evidence. The repo includes an eval suite and a zero-key verifier demo.

**"Why not just paste the brief and transcript into ChatGPT?"**
> SponsorLint produces a reusable specification, exact validators, timestamps, source evidence, repeatable pass/fail results, and the same checks rerun against every revision.

**"Isn't this just string matching?"**
> The verification half is deterministic string and numeral work, deliberately — that is what makes results auditable and testable. The interesting parts are compiling prose into a spec, and normalization: catching "seventy percent" against a required 73% is not a substring match.

**"You planted the errors."**
> The demo input is controlled, but the verifier is not hardcoded to it. Add a requirement in the review screen and rerun. There is also an independent fixture suite.

**"What if the LLM misunderstands the brief?"**
> Its output is never silently trusted. Every rule cites source text and is editable before approval.

**"What if Whisper is wrong?"**
> Transcript evidence is shown, and ambiguous cases route to manual review.

**"Does it check visuals?"**
> Not in the MVP. Unsupported visual requirements are explicitly marked for manual review rather than guessed.

**"Only n=28 in your eval."**
> Correct, and it is stated. It is 28 more labeled cases than most submissions have, the fixtures are in the repo, and the hard negatives are the ones that matter.

---

# 26. FAILURE HANDLING

| Failure | Response |
|---|---|
| PDF unparseable | Clear error + manual paste-text fallback |
| Compiler fails | Manual spec editing still works; verifier unaffected |
| Compiler returns malformed JSON | Pydantic validation + one retry, then surface the error. Worst case ship the committed spec |
| Whisper fails | Show the error. **Do not silently continue** |
| Whisper garbles a planted error | Caught at the `T+1:00` gate. Re-record the sentence |
| Transcript questionable | Show evidence; ambiguity → `MANUAL REVIEW` |
| Unsupported visual requirement | `MANUAL REVIEW` |
| UI fights you >1 hour | Jinja templates. The pipeline matters more |
| Behind schedule | Cut in order: demo video → jump-to-timestamp → UI polish → web UI entirely (ship the CLI) |

**Never cut:** the eval number · the zero-key demo path · the README.

---

# 27. PRIORITY ORDER

1. Deterministic verifier
2. Spoken-number / value normalization
3. Real fixture + reliable transcript
4. Validator unit tests
5. Eval harness
6. Zero-key clone-and-run
7. Brief compiler
8. Editable source-grounded review
9. Full MP4 flow
10. Report UI
11. README
12. Demo arc
13. Demo video
14. Everything else

**Cut from the bottom.** A beautiful UI with fake analysis loses. A CLI with real, measured analysis wins.

---

# 28. AGENT WORK SPLIT

| Agent | Owns |
|---|---|
| **A — Deterministic engine** | schemas, normalization, six validators, eval harness, unit tests |
| **B — Brief compiler** | PDF extraction, LLM prompt, `source_quote`, schema validation, uncertainty |
| **C — Web UI** | upload, split-screen review, edit/delete/add, video input, result cards |
| **D — Demo / QA** | Aegis brief, V1 and spliced V3, eval cases, README, clean-env reproduction |

**Agents may not redefine scope.**

---

# 29. AGENT OPERATING RULES

1. Do not add features because they are easy.
2. Do not add a seventh rule family before §21 passes.
3. Do not put an LLM in a final verdict where code can verify.
4. Do not silently turn uncertainty into `PASS`.
5. Do not loosen a fuzzy threshold to make a demo pass.
6. Do not fuzzy-match numeric values, ever.
7. Do not polish UI before the verifier works.
8. Do not rewrite a working architecture for elegance.
9. Do not add a database, auth, billing, or Docker-first architecture.
10. Do not make the default demo require an API key or a model download.
11. Do not hardcode verdict output.
12. Do not claim legal compliance.
13. Do not add Cutcheck, retention analytics, or any second product.
14. When unsure whether something is in scope, it is **out of scope**.

---

# 30. KILL LIST

**Do not build:** general creator platform · Cutcheck integration · retention analytics · automatic video editing · re-recording · voice cloning · sponsor script generation · sponsor negotiation or discovery · brand/influencer marketplace · rate estimation · contract generation · invoicing · campaign CRM · analytics dashboard · social scheduling · YouTube/TikTok/Instagram posting · thumbnail generation · auto-shorts · B-roll generation · AI avatars · logo detection · generic fact checker · legal compliance engine · browser extension · mobile app · multi-user system · authentication · billing · database-backed history · Kubernetes · queues · microservices · vector DB · RAG · autonomous agents · fancy deployment · animation systems.

**Named trap — do not build OCR.** `easyocr` pulls ~2GB of torch on Windows; tesseract is a system-binary install. It is a stretch goal that eats hour 20 and returns nothing. Visual requirements go to `MANUAL REVIEW`, which is the better answer anyway.

If someone says *"wouldn't it be cool if…"* the default answer is **No.**

---

# 31. IF RETENTION DATA ARRIVES MID-BUILD

You will be tempted to switch to Cutcheck. **Do not.**

Cutcheck from a cold start in the remaining hours, with data landing mid-build and no validation harness, is a worse bet than a finished SponsorLint — and you would be abandoning certain progress for a project with four more gates ahead of it.

Bank the data. Cutcheck is a genuinely good post-hackathon project and it will still be good in September, when you can build it properly with a backtest.

---

# 32. FEATURE REQUEST FILTER

1. Does it directly answer *"did I follow this sponsor brief?"*
2. Does it improve a judging criterion?
3. Will a judge see or verify it?
4. Can it be built and tested quickly?
5. Does it strengthen the existing workflow rather than create a second product?

Fewer than **4/5** YES → **do not build it.**

---

# 33. DEFINITION OF DONE

```
REALISTIC PROSE SPONSOR BRIEF
        ↓
BRIEF TEXT EXTRACTION
        ↓
REQUIREMENT COMPILATION
        ↓
EDITABLE, SOURCE-GROUNDED SPEC REVIEW
        ↓
APPROVED sponsor-spec.json
        ↓
   +  TIMESTAMPED TRANSCRIPT  ←  RECORDED SPONSOR VIDEO
        ↓
DETERMINISTIC VERIFICATION
        ↓
PASS / WARN / FAIL
  + timestamp + transcript evidence + source quote
        ↓
DO NOT SEND  /  REVIEW  /  SPONSOR READY
        ↓
FIX → RERUN → SPONSOR READY
```

And independently:

```bash
python -m sponsorlint demo   # works with no API credentials, no model download
python -m sponsorlint eval   # reports actual validator metrics
```

Then: **stop adding features. Test. Polish. Record. Submit.**

---

# 34. FINAL MANTRA

> **Narrow enough to finish.**
> **Specific enough to remember.**
> **Deterministic enough to trust.**
> **Fast enough to verify.**
> **Useful enough to matter.**

## The one metric

> **Under 15 seconds to understand. Under 60 seconds to believe. Under 60 seconds to run.**

The goal is not to be unbeatable — nothing is, and 20% of the rubric is taste. The goal is to be **un-dismissable**: no judge can finish the sentence *"this doesn't work"* or *"I've seen this one."*

---

# 35. FINAL INSTRUCTION TO ALL AGENTS

Do not optimize SponsorLint for what it could become in six months.

Optimize it for the judge with dozens of submissions who needs to understand in seconds:

```text
the brief required seventy-three percent
the creator said seventy
SponsorLint caught it at 00:43
the source sentence is right there
the spec is editable and the verifier is rerunnable
the fixed video passes
and there is a measured number proving the validators work
```

That is the product.

**Ship that.**
