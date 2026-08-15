# Phases — SponsorLint

Build order and gates. `T+0` is when you start.

**Deadline: Aug 17, 2026 @ 4:30 AM IST.** This plan assumes ~30 working hours with a six-hour sleep block. Adjust the offsets to your actual start time; do not adjust the order.

---

# The governing rule

**Never build horizontally.** Do not start PDF parsing + Whisper + LLM + six validators + UI at once.

```
handwritten approved spec + cached real transcript
                ↓
        ONE deterministic validator
                ↓
            real verdict
```

Only then add the surrounding machinery.

**Do not start a phase before the previous gate passes.** A gate is a binary question with a demonstrable answer, not a feeling.

---

## `T+0:00 – 0:15` · Setup and scope freeze

- Create the repo. Copy the seven documents in.
- README with three things only: title, one-sentence pitch, input/output block.
- `pip install fastapi uvicorn jinja2 pydantic rapidfuzz python-multipart`
- Create both requirements files now (`requirements-demo.txt`, `requirements.txt`) so the split is never an afterthought.

> **GATE** — repo exists, demo deps install clean.

---

## `T+0:15 – 1:00` · PHASE 0 — Demo assets first

**Counterintuitive but correct.** The assets gate every downstream test, need no code, and need your voice at full energy — which you will not have at hour 30.

1. Write `samples/brief.md` **exactly as specified in `PRD.md` §5**. Do not "improve" it.
2. Export `samples/brief.pdf` with a header and reasonable typography.
3. Write the ~75-second script with the three planted errors.
4. **Test-transcribe just the three error sentences with `base.en`, right now.**
5. **If Whisper mangles the centerpiece, change the wording now** — not at hour twenty-six. Your entire demo rests on one transcription.
6. Record V1. Phone mic is fine. Enunciate the numbers.

*Agents scaffold in parallel:* repo skeleton, six validator stubs each with one failing test, `ffprobe` wrapper, Pydantic schemas. Nothing that needs the video.

> **GATE 1:00** — brief and V1 exist. The numeric error, the prohibited phrase, and the disclosure all transcribe reliably.

---

## `T+1:00 – 2:10` · PHASE 1 — Verifier vertical slice

**Do not build the compiler or the upload UI first.**

1. Hand-write `samples/spec.approved.json`
2. Transcribe V1 **once** → save `samples/transcript.v1.json`
3. **Never run Whisper again during development.** That file is your fixture for the next thirty hours
4. Basic text normalization
5. One validator: `MUST_SAY`
6. Print a real PASS/FAIL with a timestamp

> **GATE 2:10** — one command produces one real verdict from the cached real transcript.
>
> **If this fails, stop all UI and compiler work.** Nothing else matters until this works.

---

## `T+2:10 – 3:15` · PHASE 2 — The six validators

In order: `MUST_SAY` → `MUST_NOT_SAY` → `EXACT_VALUE` → `MUST_DISCLOSE` → `DURATION` → `URL_OR_CTA`

**Give `EXACT_VALUE` disproportionate attention.** It is the hard one and the one that matters.

Per validator: write the failing test → implement → pass → run on V1 → move on.

> **GATE 3:15** — all six families produce expected verdicts on V1.
>
> **The deterministic core now exists. Everything after this is upside.**

---

## `T+3:15 – 5:15` · PHASE 3 — Normalization depth + eval harness

- Spoken numbers, currency, percent (`normalize/numbers.py`)
- URLs (`normalize/urls.py`), promo codes (`normalize/codes.py`)
- 24–30 fixtures in `eval/fixtures.json`, heavy on hard negatives
- `python -m sponsorlint eval` printing real metrics
- Tune to avoid false FAILs; route ambiguity to `MANUAL REVIEW`

> **GATE 5:15** — real metrics printed. No hardcoded score. False FAILs and false PASSes both visible.

---

## `T+5:15 – 7:00` · PHASE 4 — Zero-key demo path

- Commit `spec.approved.json`, `transcript.v1.json`, `video-metadata.v1.json`
- Wire `python -m sponsorlint demo`
- Confirm `requirements-demo.txt` has no whisper, no LLM client, no torch

> **GATE 7:00** — fresh clone → one command → real output. No key, no download, under sixty seconds.
>
> ### You are now submittable.
>
> A CLI with real, measured analysis and a working quickstart already satisfies the event rules — *"a working script counts."* Everything past here raises the ceiling. **Nothing past here is load-bearing.**

---

## `T+7:00 – 9:30` · PHASE 5 — PDF extraction + compiler

- `pypdf` text extraction
- The constrained prompt (`Architecture.md` §9)
- Structured parse → Pydantic validation → one retry on malformed JSON
- `source_quote` preserved on every rule; reject extractions without it
- Unverifiable requirements → `manual_review`, not dropped
- Unsupported rule types rejected at validation

> **GATE 9:30** — the realistic prose brief produces the intended spec with no invented requirements, and `min_seconds: 60` came out of *"no shorter than one minute."*

---

## `T+9:30 – 12:00` · PHASE 6 — Editable spec review

Split-screen: source prose left, extracted rule right, `source_quote` visible. Edit, delete, add, approve. The **approved** spec enters the verifier.

> **GATE 12:00** — **changing `73%` to `70%` in the approved spec changes the actual verdict.**
>
> This is the test that proves the spec drives the verifier and is not decorative. If the verdict does not flip, the review screen is a mockup.

---

## `T+12:00 – 13:30` · PHASE 7 — Full MP4 flow

Fresh MP4 → `faster-whisper` → timestamps → `ffprobe` duration → transcript JSON → verifier. Cache successful transcripts during development.

> **GATE 13:30** — fresh MP4 in, real report out, no manual file editing.

---

## `T+13:30 – 19:30` · SLEEP

**Six hours. Not optional.**

You are one person. The last four hours of a hackathon are worth nothing if you cannot think, and every gate from here is judgment work rather than typing. A plan with no sleep block is a plan that gets abandoned around hour 20.

---

## `T+19:30 – 23:30` · PHASE 8 — Web UI

```
Upload → Compile → Review/edit spec → Upload video → Run check → Report
```

- Real progress states only. **Do not fake progress**
- A `[ Load sample campaign ]` button that always works
- See `Design.md` for the visual system

> **GATE 23:30** — a nontechnical judge understands what failed and why, without a terminal.

---

## `T+23:30 – 25:00` · PHASE 9 — The demo arc

- Re-record only the offending sentences and splice into the base take
- Transcribe, commit `transcript.v3.json`
- Capture `DO NOT SEND → SPONSOR READY` as a side-by-side report diff or GIF

> **GATE 25:00** — the arc runs clean twice in a row.

---

## `T+25:00 – 27:30` · PHASE 10 — README and visuals

The video is optional, so **this is the primary judging surface.** Structure per `PRD.md` §7 and the order below:

1. Category line + GIF
2. The problem, one paragraph
3. Input / output block
4. 60-second quickstart — **state the zero-keys fact explicitly**
5. **Does it actually work?** — the real eval numbers. **Before the feature list**
6. How it works — compiler → editable spec → deterministic validators
7. Rule types
8. Limitations, written by you
9. Full run instructions — API key, model download — last

---

## `T+27:30 – 29:30` · Clean-environment reproduction

Fresh clone, fresh virtualenv, run everything. Fix what breaks. **Add no features.**

Check the reproducibility list in `Architecture.md` §8.

---

## `T+29:30 – deadline` · Buffer

Optional 90-second demo video **only if the README is already excellent**. Submit with margin. **Then stop touching the code.**

---

# Phase summary

| Phase | Window | Delivers | Gate |
|---|---|---|---|
| — | 0:00–0:15 | Repo, deps | Installs clean |
| 0 | 0:15–1:00 | Brief, script, V1 | Whisper hears the planted errors |
| 1 | 1:00–2:10 | Vertical slice | One real verdict |
| 2 | 2:10–3:15 | Six validators | All produce verdicts on V1 |
| 3 | 3:15–5:15 | Normalization + eval | Real metrics printed |
| 4 | 5:15–7:00 | Zero-key demo | **Submittable** |
| 5 | 7:00–9:30 | PDF + compiler | Prose → correct spec |
| 6 | 9:30–12:00 | Editable review | Edited spec flips the verdict |
| 7 | 12:00–13:30 | Full MP4 flow | Fresh video → real report |
| — | 13:30–19:30 | **Sleep** | — |
| 8 | 19:30–23:30 | Web UI | Judge needs no terminal |
| 9 | 23:30–25:00 | Demo arc | Runs clean twice |
| 10 | 25:00–27:30 | README + GIF | — |
| — | 27:30–29:30 | Clean-env repro | Works from scratch |
| — | 29:30+ | Buffer, submit | — |

---

# If you fall behind

Cut in exactly this order (from `Rules.md` §9):

```
1. demo video
2. jump-to-timestamp on findings
3. UI polish
4. the web UI entirely — ship the CLI
```

**Never cut:** the eval number · the zero-key demo path · the README.

Phase 4 is the line. If you reach `T+7:00` with the zero-key demo working, you have a complete submission no matter what happens next.
