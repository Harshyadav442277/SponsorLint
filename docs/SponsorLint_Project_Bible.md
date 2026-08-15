# SponsorLint — Project Bible

> **Pre-flight checks for sponsored YouTube integrations.**
>
> SponsorLint converts a sponsor brief into an executable set of requirements, checks the actual recorded sponsor segment, and produces timestamped PASS / WARN / FAIL results before the creator sends the video to the brand.

---

# 0. North Star

## One-line pitch

**ESLint catches mistakes before you ship code. SponsorLint catches mistakes before you send a sponsored YouTube integration to the brand.**

## The job-to-be-done

> “Before I send this sponsor cut for approval, tell me whether I actually followed the sponsor brief.”

## The user

**Primary user:** YouTube creator or editor handling paid sponsor integrations.

Do **not** broaden the persona to:

- all creators
- agencies
- TikTok creators
- social media managers
- influencer marketplaces
- advertisers
- brand campaign teams

Those may be future users. They are not the hackathon MVP.

## The moment of use

SponsorLint is used **after recording/editing the sponsor segment but before sending it to the sponsor for approval**.

That exact moment is the product.

---

# 1. Why This Exists

Sponsor briefs often contain many small requirements:

- exact product names
- exact discount percentages
- URLs
- mandatory CTAs
- disclosure language
- duration limits
- prohibited claims
- required talking points
- promo codes
- campaign dates
- phrases that must not be used

A creator can easily make a sponsor read that sounds perfectly fine but violates one tiny requirement.

The current process is manual:

```text
Open sponsor brief
        ↓
Open video
        ↓
Scrub through sponsor segment
        ↓
Compare spoken words against brief
        ↓
Notice mistake
        ↓
Re-edit / re-record
        ↓
Check again
```

SponsorLint compresses this into:

```text
Sponsor brief + sponsor video
            ↓
        SponsorLint
            ↓
Timestamped compliance report
```

---

# 2. Product Thesis

The hackathon should not be won by building the biggest product.

It should be won by building the **smallest product whose output is immediately useful and undeniable**.

SponsorLint is intentionally narrow.

It is **not an AI video editor**.

It is **not a sponsorship platform**.

It is **not a generic creator assistant**.

It is:

> **A linter for one high-friction step in the sponsored-video workflow.**

---

# 3. The Core Demo

The demo must make sense without explanation.

## Input

```text
sponsor-brief.pdf
sponsor-cut.mp4
```

Example brief:

```text
CAMPAIGN REQUIREMENTS

MUST:
- Mention "Threat Protection Pro"
- Mention 73% discount
- Say nordvpn.com/alex
- Include sponsored-content disclosure
- Include CTA

DO NOT:
- Say "completely anonymous"
- Say "unhackable"

INTEGRATION:
- 60–90 seconds
```

Example sponsor segment contains deliberate mistakes.

## Output

```text
SPONSORLINT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FAIL  2
WARN  1
PASS  4

❌ REQUIRED PHRASE
   Expected: "Threat Protection Pro"
   Result: Never mentioned

❌ WRONG VALUE
   Expected discount: 73%
   Detected: "up to 70%"
   Timestamp: 00:43

⚠ PROHIBITED CLAIM
   Detected:
   "makes you completely anonymous"
             ^^^^^^^^^^^^^^^^^^^^^
   Timestamp: 00:31

✓ Disclosure detected         00:02
✓ URL correct                 00:51
✓ Integration duration        74 sec
✓ CTA present                 00:48

Sponsor readiness: 57%

DO NOT SEND FOR APPROVAL
```

Then fix the video and rerun:

```text
✓ SPONSOR READY

7 / 7 requirements passed.
```

## Ideal demo narrative

```text
V1 → 5 problems
V2 → 2 problems
V3 → SPONSOR READY
```

This is stronger than a long feature tour.

---

# 4. The Product Contract

SponsorLint accepts exactly:

```text
1 sponsor brief
1 sponsor video
```

SponsorLint returns:

```text
1 structured specification
1 timestamped compliance report
1 overall readiness status
```

Everything else is optional.

---

# 5. MVP Scope

## Supported rule types

Only implement these six:

### 1. MUST_SAY

A required phrase, product name, talking point, or concept must appear.

Example:

```json
{
  "type": "MUST_SAY",
  "value": "Threat Protection Pro"
}
```

---

### 2. MUST_NOT_SAY

A prohibited claim or phrase must not appear.

Example:

```json
{
  "type": "MUST_NOT_SAY",
  "value": "completely anonymous"
}
```

---

### 3. EXACT_VALUE

A number or value must match the sponsor brief.

Examples:

- 73%
- $20
- 3 months free
- code HARSH20

```json
{
  "type": "EXACT_VALUE",
  "name": "discount",
  "expected": "73%"
}
```

---

### 4. MUST_DISCLOSE

The video must contain sponsorship disclosure.

Possible accepted forms:

```text
sponsored by
this video is sponsored by
paid partnership
thanks to X for sponsoring
```

---

### 5. DURATION

The sponsor segment must fall inside a required duration.

```json
{
  "type": "DURATION",
  "min_seconds": 60,
  "max_seconds": 90
}
```

---

### 6. URL_OR_CTA

Check that the expected link, promo code, or CTA is spoken.

Example:

```json
{
  "type": "URL_OR_CTA",
  "expected": "nordvpn.com/alex"
}
```

---

# 6. Explicit Non-Goals

Do not build:

- automatic sponsorship negotiation
- sponsorship discovery
- rate calculation
- creator marketplace
- brand CRM
- invoicing
- payment tracking
- campaign analytics
- social scheduling
- thumbnail generation
- auto-shorts
- generic video editing
- B-roll generation
- automatic voice replacement
- AI avatars
- sponsor script generation
- contract generation
- full legal compliance engine
- generic fact checking

If anyone says:

> “Wouldn’t it be cool if we also…”

The default answer is:

> **No.**

---

# 7. System Architecture

```text
              ┌───────────────────────┐
              │   Sponsor Brief PDF   │
              └──────────┬────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │   Brief Extractor     │
              │ PDF → clean text      │
              └──────────┬────────────┘
                         │
                         ▼
              ┌───────────────────────┐
              │ Requirement Compiler  │
              │ LLM → sponsor-spec    │
              └──────────┬────────────┘
                         │
                         ▼
                  sponsor-spec.json
                         │
                         │
                         ▼
┌────────────────┐   ┌───────────────────────┐
│ sponsor-cut.mp4│──►│ Transcript Extractor  │
└────────────────┘   │ Whisper + timestamps  │
                     └──────────┬────────────┘
                                │
                                ▼
                         transcript.json
                                │
              sponsor-spec.json │
                       ┌────────▼─────────┐
                       │ Verification     │
                       │ Engine           │
                       └────────┬─────────┘
                                │
                                ▼
                       lint-results.json
                                │
                    ┌───────────▼───────────┐
                    │ Report Generator      │
                    │ UI / HTML / terminal  │
                    └───────────────────────┘
```

---

# 8. Architecture Principle

## LLM responsibility

The LLM may:

- understand messy sponsor brief language
- normalize requirements
- classify requirement types
- extract expected values
- interpret semantic requirements

The LLM should **not** be the final judge of compliance whenever deterministic checking is possible.

Bad architecture:

```text
brief + transcript
      ↓
     LLM
      ↓
"Looks compliant"
```

Preferred architecture:

```text
brief
  ↓
LLM requirement compiler
  ↓
structured rules

video
  ↓
timestamped transcript

rules + transcript
      ↓
deterministic verifier
      ↓
PASS / WARN / FAIL
```

This is one of the project's strongest technical talking points.

---

# 9. Sponsor Specification

Example:

```json
{
  "campaign": "Example VPN Campaign",
  "rules": [
    {
      "id": "r1",
      "type": "MUST_SAY",
      "label": "Product name",
      "expected": "Threat Protection Pro",
      "severity": "error"
    },
    {
      "id": "r2",
      "type": "EXACT_VALUE",
      "label": "Discount",
      "expected": "73%",
      "severity": "error"
    },
    {
      "id": "r3",
      "type": "URL_OR_CTA",
      "label": "Campaign URL",
      "expected": "nordvpn.com/alex",
      "severity": "error"
    },
    {
      "id": "r4",
      "type": "MUST_DISCLOSE",
      "label": "Sponsorship disclosure",
      "severity": "error"
    },
    {
      "id": "r5",
      "type": "MUST_NOT_SAY",
      "label": "Forbidden claim",
      "expected": "completely anonymous",
      "severity": "error"
    },
    {
      "id": "r6",
      "type": "DURATION",
      "label": "Integration duration",
      "min_seconds": 60,
      "max_seconds": 90,
      "severity": "warning"
    }
  ]
}
```

---

# 10. Transcript Format

```json
{
  "duration_seconds": 74.2,
  "segments": [
    {
      "start": 0.0,
      "end": 3.8,
      "text": "This video is sponsored by Example VPN."
    },
    {
      "start": 28.3,
      "end": 33.4,
      "text": "It makes you completely anonymous online."
    },
    {
      "start": 41.1,
      "end": 45.2,
      "text": "You can get up to seventy percent off."
    }
  ]
}
```

Word-level timestamps are better if available, but segment timestamps are sufficient for the MVP.

---

# 11. Verification Strategy

## MUST_SAY

Use layers:

```text
1. normalized exact match
2. fuzzy string match
3. semantic fallback
```

Normalization:

- lowercase
- remove punctuation
- normalize whitespace
- optionally convert spoken numbers

Example:

```text
"Threat Protection Pro!"
→
"threat protection pro"
```

---

## MUST_NOT_SAY

Use:

```text
exact/fuzzy phrase match
+
semantic check only when needed
```

Return the timestamp and matching transcript.

---

## EXACT_VALUE

Normalize equivalent number formats.

Examples:

```text
73%
seventy-three percent
73 percent
```

all become:

```text
73%
```

Be careful with:

```text
70%
73%
```

This rule should be deterministic.

---

## MUST_DISCLOSE

Maintain a small disclosure phrase set:

```text
sponsored by
this video is sponsored by
paid partnership
thanks to X for sponsoring
sponsor of today's video
```

Could also use semantic matching as fallback.

---

## DURATION

Use `ffprobe`.

No LLM needed.

---

## URL_OR_CTA

Normalize spoken URLs:

```text
nord vpn dot com slash alex
nordvpn.com/alex
```

to a comparable canonical representation.

---

# 12. Result Schema

```json
{
  "status": "FAIL",
  "readiness_score": 57,
  "summary": {
    "pass": 4,
    "warn": 1,
    "fail": 2
  },
  "results": [
    {
      "rule_id": "r2",
      "status": "FAIL",
      "title": "Wrong discount",
      "expected": "73%",
      "detected": "70%",
      "timestamp": 43.1,
      "evidence": "You can get up to seventy percent off."
    }
  ]
}
```

---

# 13. Readiness Logic

Keep it simple.

Example:

```text
ERROR failed   → FAIL
WARNING failed → WARN
all errors pass → SPONSOR READY
```

Possible score:

```text
passed weighted rules / total weighted rules × 100
```

Do not overengineer scoring.

The binary state matters more:

```text
DO NOT SEND
```

or

```text
SPONSOR READY
```

---

# 14. UI

## Main screen

```text
SponsorLint

[ Upload sponsor brief ]
[ Upload sponsor segment ]

                 [ Run Check ]
```

After processing:

```text
Sponsor readiness
57%

2 FAILED
1 WARNING
4 PASSED
```

Then individual cards:

```text
❌ Wrong discount

Expected
73%

Detected
70%

00:43

"You can get up to seventy percent off."

[ Jump to timestamp ]
```

---

# 15. UI Priorities

Must have:

- upload brief
- upload video
- process button
- PASS / WARN / FAIL summary
- timestamped findings
- evidence text
- final readiness state

Nice to have:

- video player jumps to finding timestamp
- timeline markers
- downloadable report
- requirement preview before analysis

Do not spend hours polishing animations.

---

# 16. Recommended Stack

## Backend

```text
Python
FastAPI
ffmpeg / ffprobe
faster-whisper
PyMuPDF or pypdf
Pydantic
LLM API for structured extraction
```

## Frontend

Use whatever the team can ship fastest:

```text
Next.js / React
```

or even:

```text
FastAPI templates + basic HTML
```

A polished working pipeline beats sophisticated frontend architecture.

---

# 17. API Endpoints

Suggested minimal API:

```text
POST /api/brief/compile
POST /api/video/transcribe
POST /api/lint
POST /api/analyze
GET  /api/report/{id}
```

For hackathon speed, `/api/analyze` can perform everything.

Example:

```text
POST /api/analyze

multipart/form-data:
- brief
- video
```

Returns:

```json
{
  "spec": {},
  "transcript": {},
  "results": {}
}
```

---

# 18. Folder Structure

```text
sponsorlint/
│
├── app/
│   ├── main.py
│   ├── models.py
│   │
│   ├── brief/
│   │   ├── extract.py
│   │   └── compile.py
│   │
│   ├── video/
│   │   ├── transcribe.py
│   │   └── metadata.py
│   │
│   ├── lint/
│   │   ├── engine.py
│   │   ├── must_say.py
│   │   ├── must_not_say.py
│   │   ├── exact_value.py
│   │   ├── disclosure.py
│   │   ├── duration.py
│   │   └── cta.py
│   │
│   └── report/
│       └── generate.py
│
├── web/
│
├── samples/
│   ├── sponsor-brief.pdf
│   └── sponsor-cut.mp4
│
├── tests/
│
├── README.md
└── requirements.txt
```

---

# 19. Build Order

Never build horizontally.

Build one vertical slice first.

## Vertical slice #1

```text
PDF
 ↓
extract one required phrase
 ↓
transcribe MP4
 ↓
check phrase
 ↓
show PASS / FAIL
```

Once this works, the project already exists.

Then add rules one by one.

---

# 20. 24-Hour Plan

## Hour 0–2 — End-to-end skeleton

Goal:

> One real requirement from a PDF produces one real PASS / FAIL result against one real video.

Build:

- upload route
- PDF extraction
- transcription
- one `MUST_SAY` rule
- terminal/API result

**Gate:** working end-to-end pipeline.

---

## Hour 2–5 — Requirement compiler

Build LLM structured extraction.

Input:

```text
raw sponsor brief
```

Output:

```text
sponsor-spec.json
```

Validate with Pydantic.

**Gate:** messy brief reliably becomes valid structured rules.

---

## Hour 5–9 — Core lint rules

Implement:

- MUST_SAY
- MUST_NOT_SAY
- EXACT_VALUE
- DURATION
- MUST_DISCLOSE
- URL_OR_CTA

**Gate:** sample video produces known expected failures.

---

## Hour 9–13 — UI

Build:

- file upload
- loading state
- score/status
- results cards
- timestamps

**Gate:** judge can use it without terminal.

---

## Hour 13–16 — Evidence + timestamps

Every issue should include:

```text
expected
detected
timestamp
transcript evidence
```

**Gate:** no vague findings.

---

## Hour 16–18 — Demo dataset

Create:

```text
brief.pdf
video-v1.mp4
video-v2.mp4
video-v3.mp4
```

with controlled errors.

**Gate:** FAIL → FAIL → PASS demo works consistently.

---

## Hour 18–20 — Testing

Test:

- numbers
- punctuation
- casing
- similar phrases
- missing phrases
- disclosures
- URLs
- duration
- LLM malformed JSON
- transcription edge cases

**Gate:** demo cannot randomly fail.

---

## Hour 20–22 — README + pitch

Write:

- one sentence
- problem
- demo GIF/video
- architecture
- quickstart
- limitations
- future work

---

## Hour 22–24 — Polish only

Allowed:

- UI cleanup
- loading indicator
- video timestamp jumps
- nicer report

Forbidden:

- new product areas

---

# 21. Claude / Codex Work Split

If multiple agents are available:

## Agent 1 — Backend

Own:

- FastAPI
- file uploads
- transcription
- PDF extraction
- API

---

## Agent 2 — Lint Engine

Own:

- schemas
- rule validators
- normalization
- deterministic verification
- unit tests

---

## Agent 3 — Frontend

Own:

- upload interface
- results
- timestamp cards
- video player

---

## Agent 4 — Demo / QA / README

Own:

- test fixtures
- deliberate failure cases
- README
- demo script
- judge objections
- bug finding

---

# 22. Prompt for Requirement Compiler

System idea:

```text
You convert sponsorship briefs into a constrained machine-readable
verification specification.

Extract only requirements that can reasonably be verified from the
spoken content or duration of a recorded sponsor integration.

Allowed rule types:
- MUST_SAY
- MUST_NOT_SAY
- EXACT_VALUE
- MUST_DISCLOSE
- DURATION
- URL_OR_CTA

Do not invent requirements.
Do not infer requirements that are not present.
Preserve exact numbers, product names, URLs and prohibited claims.
Return valid JSON matching the supplied schema.
```

---

# 23. Failure Handling

## PDF cannot be parsed

Return:

```text
Could not extract readable text from sponsor brief.
```

Optional fallback:

```text
paste brief text manually
```

---

## Whisper fails

Return:

```text
Could not transcribe sponsor segment.
```

Do not silently continue.

---

## Requirement compiler uncertain

Represent uncertainty:

```json
{
  "confidence": 0.62,
  "needs_review": true
}
```

Do not pretend certainty.

---

## Rule cannot be objectively verified

Mark:

```text
MANUAL REVIEW
```

Example:

```text
"Show the product clearly for at least 5 seconds."
```

Unless you actually implement visual verification, do not fake it.

---

# 24. The Trust Principle

SponsorLint should be conservative.

It is better to say:

```text
⚠ Manual review required
```

than confidently produce a false pass.

This can be used as a judging strength:

> SponsorLint separates deterministic checks from ambiguous checks instead of pretending an LLM can guarantee everything.

---

# 25. Testing Bible

## Unit tests

### MUST_SAY

```text
expected: "Threat Protection Pro"
transcript: "Try Threat Protection Pro today"
→ PASS
```

```text
expected: "Threat Protection Pro"
transcript: "Try our threat system today"
→ FAIL
```

---

### EXACT_VALUE

```text
expected: 73%
transcript: "seventy-three percent off"
→ PASS
```

```text
expected: 73%
transcript: "seventy percent off"
→ FAIL
```

---

### MUST_NOT_SAY

```text
forbidden: "unhackable"
transcript: "This makes you unhackable."
→ FAIL
```

---

### DURATION

```text
min: 60
max: 90
video: 74s
→ PASS
```

---

## Integration test

Given:

```text
samples/brief.pdf
samples/video-v1.mp4
```

Expected:

```text
2 FAIL
1 WARN
4 PASS
```

This exact test protects the demo.

---

# 26. Judge Objections

## “Isn't this just an LLM reading two files?”

Answer:

> The LLM only compiles messy brief language into a constrained specification. The actual checks are performed against timestamped video evidence using deterministic validators wherever possible.

---

## “Why not just ask ChatGPT?”

Answer:

> ChatGPT can summarize a brief, but SponsorLint produces repeatable pass/fail checks, timestamps, evidence, exact numeric validation and a reusable machine-readable specification.

---

## “Why would creators use this?”

Answer:

> It targets the exact moment before sponsor approval, when missing a small requirement can trigger another revision cycle.

---

## “Does it edit the video?”

Answer:

> No. Deliberately. SponsorLint is a pre-flight checker, not another AI editor.

---

## “What if the sponsor brief contains visual requirements?”

Answer:

> The MVP flags unsupported visual requirements for manual review rather than pretending to verify them.

This is a strong answer.

---

## “Could brands use this too?”

Answer:

> Yes, eventually. But the MVP is built specifically for creators and editors checking a sponsor segment before submission.

Keep the scope narrow.

---

# 27. Competitive Positioning

Do not pitch:

```text
AI tool for creators
```

Pitch:

```text
Pre-flight QA for sponsored YouTube integrations
```

Do not pitch:

```text
AI sponsorship automation platform
```

Pitch:

```text
Sponsor brief → executable checks → sponsor-ready video
```

Do not pitch:

```text
We use Whisper + an LLM + ffmpeg...
```

Pitch the saved workflow first.

---

# 28. Naming

Primary:

# SponsorLint

Strong because:

- immediate developer analogy
- communicates checking, not editing
- easy to remember
- explains the product category

## Tagline options

**Best:**

> Pre-flight checks for sponsored YouTube integrations.

Alternative:

> Catch sponsor mistakes before the brand does.

Developer version:

> ESLint for sponsored videos.

---

# 29. Landing Page Copy

## Hero

```text
Catch sponsor mistakes before the brand does.

Upload the sponsor brief and your recorded integration.
SponsorLint checks required claims, prohibited language,
discounts, URLs, disclosures and timing before you send it
for approval.

[ Check my sponsor cut ]
```

---

# 30. README Opening

```text
# SponsorLint

SponsorLint converts a sponsorship brief into executable checks and
runs them against the actual recorded YouTube sponsor integration.

Think ESLint, but for sponsor reads.

Upload:
- sponsor-brief.pdf
- sponsor-cut.mp4

Get:
- PASS / WARN / FAIL
- exact failed requirement
- timestamp
- transcript evidence
- sponsor-readiness status
```

---

# 31. Submission Description

## Problem

Creators frequently receive detailed sponsor briefs containing exact claims, prices, links, disclosures and prohibited phrases. Verifying a finished integration against the brief is repetitive manual work, and missed requirements often result in another approval round.

## Solution

SponsorLint converts the sponsor brief into a structured verification specification, transcribes the recorded sponsor segment and checks the video against each requirement.

## Result

Instead of manually comparing a PDF and a timeline, the creator receives timestamped PASS / WARN / FAIL diagnostics before sending the integration to the sponsor.

---

# 32. 30-Second Pitch

> Sponsored YouTube videos often go through brand approval because the creator has to follow a detailed sponsor brief: exact discounts, product names, disclosures, links and claims they aren't allowed to make. Today, editors manually compare that PDF against the finished video. SponsorLint converts the brief into executable checks, analyzes the actual sponsor segment and tells you exactly what failed and where. Think ESLint for sponsored videos — catch the mistake before the sponsor does.

---

# 33. 60-Second Demo Script

> Here is a sponsor brief requiring a 73% discount, this exact product name, a disclosure and this URL, while prohibiting two claims.
>
> Here is our finished sponsor segment.
>
> SponsorLint compiles the brief into six machine-readable rules, transcribes the actual video, and checks each rule.
>
> It found that I said 70% instead of 73%, never mentioned the required product feature, and used a prohibited claim at 31 seconds.
>
> After fixing those issues, I rerun the exact same check.
>
> Now every requirement passes and the integration is marked Sponsor Ready.
>
> SponsorLint is pre-flight QA for sponsored YouTube integrations.

---

# 34. Stretch Goals

Only after the core demo is perfect.

## Stretch 1 — Jump to timestamp

Click finding:

```text
00:43
```

video jumps to that moment.

High demo value, low complexity.

---

## Stretch 2 — Brief review screen

Before video analysis, display:

```text
We extracted 7 requirements.

✓ 3 required mentions
✓ 1 prohibited claim
✓ 1 discount
✓ disclosure
✓ duration
```

User can correct extraction.

Very useful.

---

## Stretch 3 — Downloadable report

Generate:

```text
sponsorlint-report.html
```

Useful for editor/team handoff.

---

## Stretch 4 — Visual rules

Only if everything else is complete.

Examples:

- logo visible
- product shown
- QR code shown

This is significantly more complex.

---

# 35. Things That Can Kill the Project

## 1. Scope creep

Biggest threat.

Do not build a sponsorship platform.

---

## 2. LLM hallucinated requirements

Mitigation:

- structured schema
- quote source text
- show extracted rules before running
- never invent unsupported requirements

---

## 3. Whisper inaccuracies

Mitigation:

- controlled demo audio
- fuzzy matching
- transcript visible to user
- allow manual transcript correction if necessary

---

## 4. Overclaiming compliance

Never say:

```text
legally compliant
```

Say:

```text
matches the supplied sponsor brief
```

SponsorLint checks the provided requirements, not the law.

---

## 5. Building visual analysis too early

Ignore visual requirements in MVP.

Flag them:

```text
MANUAL REVIEW REQUIRED
```

---

# 36. Definition of Done

SponsorLint is done when this works reliably:

```text
1. Upload real PDF brief.
2. Upload real MP4 sponsor segment.
3. Extract structured requirements.
4. Transcribe the video.
5. Evaluate six supported rule types.
6. Display timestamped evidence.
7. Produce clear PASS / WARN / FAIL.
8. Rerun after corrections.
9. Show SPONSOR READY.
```

Everything after that is optional.

---

# 37. The One Metric

For the hackathon, the metric is not:

```text
number of features
```

It is:

```text
How quickly does a judge understand the problem,
believe the solution works,
and see a real result?
```

Target:

> **Under 15 seconds to understand. Under 60 seconds to believe.**

---

# 38. Final Product Doctrine

When making any build decision, ask:

### Does this help answer:

> “Did I follow this sponsor brief in this sponsor segment?”

If yes, consider it.

If no, reject it.

---

# 39. Final Scope Lock

## We are building:

> **SponsorLint: a pre-flight QA checker for recorded YouTube sponsor integrations.**

## Inputs:

```text
Sponsor brief
Sponsor segment
```

## Outputs:

```text
Structured requirements
Timestamped violations
PASS / WARN / FAIL
Sponsor readiness
```

## Supported checks:

```text
MUST_SAY
MUST_NOT_SAY
EXACT_VALUE
MUST_DISCLOSE
DURATION
URL_OR_CTA
```

## We are NOT building:

```text
a general creator platform
a video editor
a sponsorship marketplace
a campaign manager
```

---

# 40. Final Mantra

> **Narrow enough to finish.**
>
> **Specific enough to remember.**
>
> **Deterministic enough to trust.**
>
> **Visual enough to demo.**
>
> **Useful enough to matter.**
