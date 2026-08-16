# PRD — SponsorLint

**Pre-flight QA for sponsored YouTube integrations.**

> ESLint catches mistakes before you ship code. SponsorLint catches mistakes before you send a sponsored integration to the brand.

| | |
|---|---|
| **Event** | Social Media Automation Hackathon |
| **Deadline** | Aug 17, 2026 @ 4:30 AM IST |
| **Judging** | Functionality 30% · Real-world usefulness 30% · Creativity 20% · Technical execution 20% |
| **Submission** | Repo + README required. Demo video optional. |

## Document set

These seven documents are the **sole authority**. Read them in this order:

| File | Answers |
|---|---|
| **PRD.md** ← you are here | What are we building, for whom, and what counts as done |
| `Architecture.md` | How it is built — flow, stack, folder structure, schemas |
| `Rules.md` | What the AI may and may not do |
| `Phases.md` | Build order, gates, and the clock |
| `Design.md` | Colors, typography, components, CLI output |
| `Decisions.md` | Why the project is shaped this way |
| `Memory.md` | Live progress state — **update as you go** |

## The one other file

`docs/SPONSORLINT_BIBLE.md` is the **reference narrative** — the whole plan in one readable file, for onboarding a person or pasting into a tool that wants a single document. It is kept deliberately and is reconciled with these seven documents.

> **It is not an authority. If it and a root document disagree, the root document wins.**
>
> Anyone editing a root document must update the bible to match or mark it `STALE` in its own header.

Everything else is gone. Four earlier plans (`SPONSORLINT_FINAL_EXECUTION_BIBLE.md`, `SPONSORLINT_EXECUTION_BIBLE.superseded.md`, `SponsorLint_Project_Bible.md`, `STRATEGY.md`) and the decision record `BAKEOFF.md` were deleted from the working tree — git history retains them (`git show e759a5b:docs/BAKEOFF.md`).

If you find one of those on disk, in Downloads, or pasted into a chat: **it is history, not instructions.** Two contradict decisions recorded here — see `Decisions.md` D7 and D9.

---

# 1. The problem

Sponsor briefs are contracts with enumerated deliverables: exact product names, exact discount figures, tracked URLs, mandatory disclosure, duration windows, prohibited claims.

Today, verifying a finished integration against the brief is manual:

```
open brief → open timeline → scrub the segment → compare spoken words
against the brief → notice a mistake → re-edit → check again
```

Missing one requirement costs a revision round with the brand, a delayed payment, or a strained relationship. **The cost is per revision cycle, not once.**

## The job to be done

> **"Before I send this sponsor cut for approval, did I actually follow the sponsor brief?"**

That is the entire product.

## The thesis

Most social-media automation tools **generate** something. SponsorLint **checks** something.

It is a linter for a high-friction creator workflow that has a concrete external specification. **The sponsor brief is the spec. The recorded segment is the artifact.**

---

# 2. The user

**A YouTube creator or video editor handling a paid sponsor integration.**

Do **not** broaden the MVP persona to: agencies · advertiser dashboards · brand campaign teams · TikTok or Instagram creators · influencer marketplaces · social media managers · generic creators · legal or compliance departments.

Those may be future users. They are not this build.

## Moment of use

```
record / edit sponsor segment
        ↓
BEFORE sending it to the sponsor      ← the product lives here
        ↓
   run SponsorLint
        ↓
 fix concrete violations
        ↓
   send for approval
```

---

# 3. Product contract

**Accepts exactly:**
```
1 sponsor brief (PDF or text)
1 recorded sponsor segment (MP4)
```

**Returns exactly:**
```
1 reviewed, approved structured specification
1 timestamped verification report
1 overall readiness state
```

**Action states:**

| State | Meaning |
|---|---|
| `DO NOT SEND` | A blocking requirement failed |
| `REVIEW` | No blocking failure, but a warning failed or a manual item remains unresolved |
| `SPONSOR READY` | All automated requirements passed and every manual item was explicitly confirmed |

A percentage score is optional and secondary. **The binary state is what matters.**

---

# 4. Features

## 4.1 Required — the MVP

### F1 · Brief compilation
Extract text from a PDF or markdown brief and compile it into a constrained machine-readable specification. Every extracted rule carries a verbatim `source_quote` from the brief.

### F2 · Spec review and approval
The user sees the compiled spec **before** verification runs, in a split-screen view with the source prose beside each extracted rule. The user can **edit, delete, add, and approve**. The approved spec — not the raw extraction — enters the verifier.

### F3 · Transcription
The recorded segment is transcribed with timestamps. Segment-level timestamps are sufficient.

### F4 · Deterministic verification — six rule types

| Type | Checks |
|---|---|
| `MUST_SAY` | A required phrase, product name, or talking point appears |
| `MUST_NOT_SAY` | A prohibited phrase does not occur |
| `EXACT_VALUE` | A numeric or code-like value matches exactly |
| `MUST_DISCLOSE` | Sponsorship disclosure is present, with timestamp |
| `DURATION` | Segment length falls inside the required window |
| `URL_OR_CTA` | The tracked URL, promo code, or CTA is spoken |

### F5 · Manual review
Requirements that cannot be verified from audio or duration are surfaced as `MANUAL REVIEW` — never dropped, never guessed. Excluded from the automated score and always visible. They keep readiness at `REVIEW` until the creator explicitly confirms them.

### The check surface — count it this way

```
6 executable rule types
+ 1 disclosure-placement advisory   (derived, not a rule type)
+ 1 MANUAL_REVIEW outcome           (what happens when no validator exists)
```

**There are six validators.** `MANUAL_REVIEW` is not a validator — it is the outcome when no supported validator applies. Disclosure placement is not a seventh rule type — it is a property of the `MUST_DISCLOSE` result. Never write "seven rule types" or "eight validators."

### F6 · Timestamped evidence
Every finding answers five questions: **what was required · what was detected · where · what evidence · where did the requirement come from.**

### F7 · Eval harness
`python -m sponsorlint eval` runs the validators over 46 labeled text fixtures and reports real accuracy, false FAILs, and false PASSes. **This is a required feature, not a stretch goal.**

### F8 · Zero-key demo
`python -m sponsorlint demo` runs the real verifier against committed fixtures with no API key, no network, and no model download.

## 4.2 Stretch — only after §6 passes

- Click a finding to seek the video player to that timestamp
- Downloadable HTML report
- Disclosure-placement advisory when the brief does not specify placement
- 90-second demo video

## 4.3 Explicitly out of scope

See `Rules.md` §6 for the full kill list. Headline exclusions: no visual/OCR verification, no video editing, no sponsorship marketplace, no database, no auth, no retention analytics.

---

# 5. Demo scenario

**Fictional brand throughout.** Never a real company's product name or campaign URL inside a fabricated brief with fabricated violations.

```
Brand: Aegis VPN   URL: aegisvpn.com/alex   Feature: Shield Mode
Discount: 73%      Promo: HARSH20
```

## The demo brief — build this exactly

The brief must be **prose, not a checklist**. A neat bulleted list makes the compiler look trivial and collapses the whole architecture argument into *"I asked an LLM to read a formatted document."*

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

### Do not "improve" this brief

| Phrasing | Why |
|---|---|
| *"no shorter than one minute and no longer than one minute and thirty seconds"* | → `DURATION 60–90`. **No regex extracts that.** This is the compiler's proof of work. |
| *"save seventy-three percent"* | Spelled out, buried mid-sentence. Makes numeral normalization visibly non-trivial. **Never write `73%` as digits here.** |
| *"completely anonymous" / "unhackable"* — quoted literally | A deterministic `MUST_NOT_SAY` needs the literal phrase. Paraphrasing the prohibition creates a semantic gap the verifier cannot bridge and silently breaks the demo. |
| *"near the beginning"* | The brief specifies placement, so disclosure placement is enforceable rather than advisory. |
| *"visible on screen for at least five seconds"* | Unverifiable from audio → `MANUAL REVIEW`. Demonstrates the trust posture. |

**Yield: 7 checkable rules + 1 manual review**, exercising every rule type.

### The canonical spec — pin this, do not re-derive it

The brief does not decompose unambiguously. Two readings give 7 and two give 8, and Phase 1 hand-writes `samples/spec.approved.json` as the very first artifact while Phase 5's gate is "the compiler produces the intended spec" — unfalsifiable without a written target. **This is the target.**

| id | type | payload | sev | from the brief |
|---|---|---|---|---|
| `r1` | `MUST_DISCLOSE` | `within_first_seconds: 15` | error | "make clear near the beginning … sponsored by Aegis VPN" |
| `r2` | `DURATION` | `min_seconds: 60, max_seconds: 90` | error | "no shorter than one minute and no longer than one minute and thirty seconds" |
| `r3` | `EXACT_VALUE` | `expected: "73%"` | error | "they can save seventy-three percent" |
| `r4` | `URL_OR_CTA` | `expected: "aegisvpn.com/alex"` | error | "should be directed to aegisvpn.com/alex" |
| `r5` | `MUST_SAY` | `phrases: ["Shield Mode"]` | error | "mention Shield Mode by name at least once" |
| `r6` | `MUST_NOT_SAY` | `phrases: ["completely anonymous", "unhackable"]` | error | "Avoid describing Aegis VPN as …" |
| `r7` | `URL_OR_CTA` | `expected: "aegisvpn.com/alex", within_last_seconds: 15` | error | "The closing should include a direct call to action" |
| — | manual review | — | — | "product interface should be visible on screen for at least five seconds" |

**The two decompositions that matter, and why:**

- **r6 is ONE rule with two phrases, not two rules.** Two rules makes the yield 8 and breaks the `4/7` arc everywhere. The `phrases: list[str]` field in `Architecture.md` §4.1 exists for exactly this.
- **`within_first_seconds: 15` is user-authored**, supplied through the review screen — never invented by the tool (`Architecture.md` §5.4).

**All seven are `severity: error`.** Nothing in this brief produces a `WARN`.

### V1 verdict — canonical, use these numbers everywhere

V1 fails `r3` (says "seventy percent"), `r5` (never says "Shield Mode"), `r6` (says "completely anonymous"). Everything else passes.

```
3 FAIL · 0 WARN · 4 PASS · 1 MANUAL CONFIRMED   →   4/7   →   DO NOT SEND
V3: 7/7 → SPONSOR READY
```

## The recorded segment

One ~75-second take with planted errors:

| | |
|---|---|
| ❌ | says **"seventy percent"** instead of seventy-three (~0:43) |
| ❌ | never says **"Shield Mode"** |
| ❌ | says **"completely anonymous"** (~0:31) |
| ✓ | valid disclosure, early |
| ✓ | correct campaign URL |
| ✓ | CTA present |
| ✓ | duration inside 60–90s |

**Do not record three full videos.** Record one good base take, re-record only the offending sentences, splice them in. Twenty minutes, not two hours.

## Expected output

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

Fix the offending lines, rerun the same approved spec → `SPONSOR READY`.

---

# 6. Acceptance criteria

The MVP is complete only when **all** pass.

| # | Test |
|---|---|
| 1 | Approved spec + transcript produces deterministic results |
| 2 | `MUST_SAY` pass/fail works |
| 3 | `MUST_NOT_SAY` returns violation + timestamp, and does not false-fire on a partial substring |
| 4 | "seventy-three percent" **passes** 73% |
| 5 | "seventy percent" **fails** 73% |
| 6 | Spoken URL normalizes correctly |
| 7 | At least one spoken promo-code form normalizes correctly |
| 8 | Sponsorship disclosure detected with timestamp |
| 9 | `ffprobe` duration validation works |
| 10 | Realistic prose brief compiles to valid schema |
| 11 | Every compiled rule carries a `source_quote` that is verified against the submitted brief |
| 12 | Unverifiable requirements surface as `MANUAL REVIEW`, not dropped |
| 13 | User can edit / add / delete rules |
| 14 | **Edited spec changes the real verdict** (change 73% → 70%, verdict flips) |
| 15 | Fresh MP4 can be transcribed and verified |
| 16 | `python -m sponsorlint eval` reports actual metrics |
| 17 | `python -m sponsorlint demo` works from a clean clone with no LLM credentials, no model download, and **no ffmpeg on PATH** |
| 18 | Every failure shows expected / detected / timestamp / evidence / source quote |
| 19 | Blocking failure → `DO NOT SEND`; unresolved manual → `REVIEW`; all requirements resolved → `SPONSOR READY` |
| 20 | **No hardcoded verdicts anywhere.** Every result is computed |

**When these pass, stop adding features.** Test, polish, write the README, submit.

---

# 7. Success metric

> **Under 15 seconds to understand. Under 60 seconds to believe. Under 60 seconds to run.**

The goal is not to be unbeatable — 20% of the rubric is taste. The goal is to be **un-dismissable**: no judge can finish the sentence *"this doesn't work"* or *"I've seen this one."*

## The judge is probably not in the room

The event is repo + README + optional video. Assume no live demo. A judge clones the repo at 2 AM and gives you sixty seconds. Two consequences:

- **The README is the primary judging surface.** Most of the field will pour hours into a video and ship three lines of markdown.
- **The zero-key clone-and-run path is worth more than any UI polish.**

## Positioning

README opening line:

> **A sponsor brief is a contract. SponsorLint makes it executable.**

Then:

> SponsorLint turns a sponsor brief into executable checks and runs them against the actual recorded sponsor integration.
>
> **Sponsor brief → executable requirements → sponsor video → timestamped PASS / WARN / FAIL.**

Never lead with Whisper, LLMs, FastAPI, ffmpeg, "AI-powered," or model names. **Lead with the saved workflow.**
