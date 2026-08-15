# Memory — SponsorLint

**Live progress state. Update it every session.**

This file exists so a fresh agent — new chat, new tool, new context window — can pick up the build without re-reading the codebase or inventing what happened. It is the cheapest token you will ever spend.

---

## How to use this file

**Read it first.** Before touching any code, read this file, then `Phases.md` for the current phase, then only the source files that phase touches. Do not scan the repo.

**Write it last.** Before you end a session, or hand off, or run out of context:

1. Update **Current state** — phase, last gate passed, what works
2. Move finished items into **Session log** with a one-line summary
3. Record anything broken in **Known issues** with enough detail to act on
4. Record any deviation from the plan in **Deviations** — and why
5. Set **Next action** to a single concrete task, not a category

**Rules:**
- Newest session at the top of the log
- Never delete history — append and correct
- Concrete over vague: `"EXACT_VALUE fails on 'seventy-three'—word-form parser missing hyphen handling"` beats `"number stuff broken"`
- If you disagree with the plan, write it in **Deviations** and continue with the current scope. Do not silently redefine it (`Rules.md` §11)

---

## Current state

```
Phase:            NOT STARTED
Last gate passed: —
Clock:            T+0 not yet set
Submittable:      NO  (becomes YES at Phase 4 gate)
```

**What works:** nothing yet — no code written.

**What exists:** the seven planning documents at repo root — **the only authority**. Superseded plans deleted; git history retains them.

**Next action:** Start `Phases.md` `T+0:00 – 0:15` — create the repo skeleton and both requirements files.

---

## Gate tracker

Mark each as it passes. This is the fastest read of project status.

| Phase | Gate | Status |
|---|---|---|
| — | Repo exists, demo deps install clean | ☐ |
| 0 | Brief + V1 exist; Whisper hears the planted errors | ☐ |
| 1 | One command → one real verdict from cached transcript | ☐ |
| 2 | All six validators produce verdicts on V1 | ☐ |
| 3 | `eval` prints real metrics, no hardcoded score | ☐ |
| **4** | **Fresh clone → `demo` → real output, no key** ← **SUBMITTABLE** | ☐ |
| 5 | Prose brief → correct spec, `min_seconds: 60` extracted | ☐ |
| 6 | Editing `73%` → `70%` flips the real verdict | ☐ |
| 7 | Fresh MP4 → real report, no manual file editing | ☐ |
| 8 | Judge understands the report without a terminal | ☐ |
| 9 | `DO NOT SEND → SPONSOR READY` arc runs clean twice | ☐ |
| 10 | README complete with real eval numbers | ☐ |
| — | Clean clone, fresh venv, everything runs | ☐ |

---

## Acceptance tests

Mirrors `PRD.md` §6. Check off only when actually verified, not when believed.

```
☐  1  Approved spec + transcript → deterministic results
☐  2  MUST_SAY pass/fail
☐  3  MUST_NOT_SAY + timestamp, no partial-substring false fire
☐  4  "seventy-three percent" PASSES 73%
☐  5  "seventy percent" FAILS 73%
☐  6  Spoken URL normalizes
☐  7  Spoken promo code normalizes
☐  8  Disclosure detected with timestamp
☐  9  ffprobe duration validation
☐ 10  Prose brief compiles to valid schema
☐ 11  Every rule carries source_quote
☐ 12  Unverifiable requirements → MANUAL REVIEW
☐ 13  User can edit / add / delete rules
☐ 14  Edited spec changes the real verdict
☐ 15  Fresh MP4 transcribed and verified
☐ 16  eval reports actual metrics
☐ 17  demo works with no credentials, no download
☐ 18  Every failure shows expected/detected/timestamp/evidence/source
☐ 19  Readiness states resolve correctly
☐ 20  No hardcoded verdicts anywhere
```

---

## Key facts an agent needs

Pinned so nobody has to re-derive them.

| | |
|---|---|
| Fictional brand | `Aegis VPN` · `aegisvpn.com/alex` · `Shield Mode` · `73%` · `HARSH20` |
| Planted errors in V1 | "seventy percent" (~0:43) · no "Shield Mode" · "completely anonymous" (~0:31) |
| Expected V1 verdict | 2 FAIL · 1 WARN · 4 PASS · 1 MANUAL → `DO NOT SEND` |
| Transcript fixture | `samples/transcript.v1.json` — **cached, never re-run Whisper in dev** |
| Whisper config | `faster-whisper`, `base.en`, **CPU only, no GPU path** |
| Demo command | `python -m sponsorlint demo` — no key, no download |
| Never cut | eval number · zero-key demo · README |

---

## Session log

*Newest first. One block per working session.*

### Session 0 — planning · Aug 15, 2026

- Ran an adversarial bakeoff between Cutcheck and SponsorLint. SponsorLint won 7.6 to 6.7. Reasoning preserved in `Decisions.md` D1
- Merged three prior SponsorLint plans into a single bible, then split it into these seven documents
- Applied four freeze corrections from a final review — validator taxonomy, no invented disclosure threshold, `False FAIL`/`False PASS` terminology, no engineered scores (`Decisions.md` D19)
- Deleted the superseded plans; git history retains them. **These seven documents are the only authority**
- **Plan is frozen** (`Rules.md` §0). No more redesign rounds
- **No code written**

---

## Known issues

*Anything broken, flaky, or deferred. Include enough detail to act without asking.*

```
(none yet)
```

Format:
```
[ISSUE] <one-line symptom>
  where:  file:line or command
  repro:  exact steps
  impact: blocks Phase N / cosmetic / demo risk
  status: open / worked around / fixed in <commit>
```

---

## Deviations from the plan

*Anything done differently from `PRD.md` / `Architecture.md` / `Rules.md` / `Phases.md`, and why. If a deviation turns out to be right, promote it into the source document and note that here.*

```
(none yet)
```

---

## Cut log

*What was dropped, when, and why. Prevents re-litigating and gives the README's limitations section a factual basis.*

```
(nothing cut yet)
```

Cut order from `Rules.md` §9: demo video → jump-to-timestamp → UI polish → web UI entirely.

---

## Handoff note

*Overwrite this every session with what the next agent most needs to know. Two or three sentences, no more.*

> Nothing has been built. Start at `Phases.md` `T+0:00`. Read `PRD.md` §5 before writing the demo brief and do not "improve" it — every sentence in it is load-bearing, and `Decisions.md` D8 explains why.
