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

## `T+0:00 – 0:25` · Setup, pre-flight, scope freeze

**Every external dependency gets proven now.** Discovering a broken install at T+1:00 costs an hour; discovering it at minute ten costs nothing.

- Create the repo. Copy the seven documents in.
- README with three things only: title, one-sentence pitch, input/output block.
- Create **both** requirements files first, so the split is never an afterthought:
  - `requirements-demo.txt` → `fastapi uvicorn jinja2 pydantic rapidfuzz python-multipart`
  - `requirements.txt` → the above **plus** `pypdf faster-whisper google-genai pytest`

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

**Then run all four pre-flight checks. Do not proceed past a failure.**

| # | Check | Command | If it fails |
|---|---|---|---|
| 1 | ffprobe answers | `ffprobe -version` | Install ffmpeg now. Only `transcribe` needs it — the demo path does not (`Architecture.md` §4.3) |
| 2 | **Whisper model cached** | `python -c "from faster_whisper import WhisperModel; WhisperModel('base.en')"` | ~140MB download. **Force it now, before recording** — it is not budgeted anywhere else |
| 3 | LLM reachable | one live smoke call returning a two-field object | Phase 5 is cut. The hand-written spec carries the demo; nothing else changes |
| 4 | Module invocation | `python -m sponsorlint` from repo root | Fix `__main__.py` before anything imports it |

> **GATE 0:25** — both requirements files install clean in a **fresh venv**, `base.en` is cached locally, ffprobe answers, and the LLM smoke call either succeeded or Phase 5 is formally cut and logged in `Memory.md`.

---

## `T+0:25 – 2:00` · PHASE 0 — Demo assets first

**Counterintuitive but correct.** The assets gate every downstream test, need no code, and need your voice at full energy — which you will not have at hour 30.

**Budgeted at 95 minutes, not 45.** This phase absorbs writing the brief, PDF export, scriptwriting, test-transcription, a full take, and phone-to-PC transfer. The old 45-minute figure was fiction, and the overrun would have pushed every downstream gate.

1. Write `samples/brief.md` **exactly as specified in `PRD.md` §5**. Do not "improve" it.
2. Export `samples/brief.pdf` with a header and reasonable typography.
3. Write the ~75-second script with the three planted errors.
4. **Test-transcribe the critical strings with `base.en`, right now** — see the gate below.
5. **If Whisper mangles any of them, change the wording now** — not at hour twenty-six.
6. Record V1. Phone mic is fine. Enunciate the numbers.
7. **In the same session, same mic, same room: record the three corrected sentences for V3.** Ten minutes now removes an hour at T+23:30 and eliminates the mic/level mismatch that splicing would otherwise expose.

### Parallel work (`Rules.md` §11 work split)

| Agent | During Phase 0 |
|---|---|
| **A** | `models.py` from `Architecture.md` §4.1 · six validator stubs, each with one failing test · `normalize/` skeleton |
| **B** | `brief/extract.py` (pypdf) · the compiler prompt file |
| **D** | brief, script, recording — **the critical path** |

Agent C (UI) has nothing to do until Phase 8. **Nothing an agent writes here may need the video.**

> **GATE 2:00** — brief and V1 exist, and `base.en` transcribes **all six** critical strings recognizably:
>
> | Must be *caught* | Must be *recognized* |
> |---|---|
> | "seventy percent" | "Shield Mode" |
> | "completely anonymous" | "aegisvpn.com/alex" |
> | the disclosure phrase | "seventy-three percent" |
>
> The old gate tested only the left column — the strings that must FAIL. But V3 reaching 7/7 depends entirely on the right column, and `aegisvpn.com/alex` is a fabricated brand name `base.en` may well mangle. **If any string in the right column is unrecognizable, change the script now.** Discovering it at Phase 7 or Phase 9 means the arc can never reach `SPONSOR READY`.

---

## `T+2:00 – 3:10` · PHASE 1 — Verifier vertical slice

**Do not build the compiler or the upload UI first.**

1. Hand-write `samples/spec.approved.json`
2. Transcribe V1 **once** → save `samples/transcript.v1.json`
3. **Never run Whisper again during development.** That file is your fixture for the next thirty hours
4. Basic text normalization
5. One validator: `MUST_SAY`
6. Print a real PASS/FAIL with a timestamp

> **GATE 3:10** — one command produces one real verdict from the cached real transcript.
>
> **If this fails, stop all UI and compiler work.** Nothing else matters until this works.

---

## `T+3:10 – 4:15` · PHASE 2 — The six validators

In order: `MUST_SAY` → `MUST_NOT_SAY` → `EXACT_VALUE` → `MUST_DISCLOSE` → `DURATION` → `URL_OR_CTA`

**Give `EXACT_VALUE` disproportionate attention.** It is the hard one and the one that matters.

Per validator: write the failing test → implement → pass → run on V1 → move on.

> **GATE 4:15** — all six families produce expected verdicts on V1.
>
> **The deterministic core now exists. Everything after this is upside.**

---

## `T+4:15 – 6:15` · PHASE 3 — Normalization depth + eval harness

- Spoken numbers, currency, percent (`normalize/numbers.py`)
- URLs (`normalize/urls.py`), promo codes (`normalize/codes.py`)
- 46 fixtures in `eval/fixtures.json`, heavy on hard negatives
- `python -m sponsorlint eval` printing real metrics
- Tune to avoid false FAILs; route ambiguity to `MANUAL REVIEW`

> **GATE 6:15** — real metrics printed. No hardcoded score. False FAILs and false PASSes both visible.

---

## `T+6:15 – 8:00` · PHASE 4 — Zero-key demo path

- Commit `spec.approved.json` and `transcript.v1.json` — **two fixtures, not three**. Duration lives on the transcript (`Architecture.md` §4.3)
- Wire `python -m sponsorlint demo`
- Confirm `requirements-demo.txt` has no whisper, no LLM client, no pypdf, no torch
- **Run the import-discipline check** (`Architecture.md` §6). A module-scope `faster_whisper` import in `cli.py` kills the demo for a judge and is invisible on your machine

**Verify in a venv built from `requirements-demo.txt` ALONE — not your dev environment:**

```bash
python -m venv .venv-judge
.venv-judge\Scripts\pip install -r requirements-demo.txt
.venv-judge\Scripts\python -m sponsorlint demo
```

Your dev env has faster-whisper installed, so `demo` will appear to work there right up until the clean-environment run at T+27:30 — two hours before the deadline, after the README and GIF are already recorded.

> **GATE 8:00** — fresh clone → one command → real output. No key, no download, **no ffmpeg**, under sixty seconds, from a venv that has only the six demo packages.
>
> ### You are now submittable.
>
> A CLI with real, measured analysis and a working quickstart already satisfies the event rules — *"a working script counts."* Everything past here raises the ceiling. **Nothing past here is load-bearing.**

---

## `T+8:00 – 10:00` · PHASE 5 — PDF extraction + compiler

- `pypdf` text extraction
- The constrained prompt (`Architecture.md` §9)
- Structured parse → Pydantic validation → one retry on malformed JSON
- `source_quote` preserved on every rule; reject extractions without it
- Unverifiable requirements → `manual_review`, not dropped
- Unsupported rule types rejected at validation

> **GATE 10:00** — the realistic prose brief produces the intended spec with no invented requirements, and `min_seconds: 60` came out of *"no shorter than one minute."*

---

## `T+10:00 – 12:00` · PHASE 6 — Editable spec review

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
- Capture the arc as a side-by-side report diff or GIF

Show it as a **raw fraction**, not a percentage — it cannot be accused of tuned weights:

```
V1   4/7 requirements passed      DO NOT SEND
V2   6/7 requirements passed      DO NOT SEND
V3   7/7 requirements passed      SPONSOR READY
```

Whatever the real counts are, use those. Do not adjust rule weights to make the arc look better (`Rules.md` §1.15).

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
| — | 0:00–0:25 | Repo, deps, **pre-flight** | Fresh venv installs, base.en cached, ffprobe + LLM checked |
| 0 | 0:25–2:00 | Brief, script, V1 **+ V3 lines** | Whisper hears all 6 critical strings |
| 1 | 2:00–3:10 | Vertical slice | One real verdict |
| 2 | 3:10–4:15 | Six validators | All produce verdicts on V1 |
| 3 | 4:15–6:15 | Normalization + eval | Real metrics printed |
| 4 | 6:15–8:00 | Zero-key demo | **Submittable** — verified in a demo-only venv |
| 5 | 8:00–10:00 | PDF + compiler | Prose → correct spec |
| 6 | 10:00–12:00 | Editable review | Edited spec flips the verdict |
| 7 | 12:00–13:30 | Full MP4 flow | Fresh video → real report |
| — | 13:30–19:30 | **Sleep** | — |
| 8 | 19:30–23:30 | Web UI | Judge needs no terminal |
| 9 | 23:30–25:00 | Demo arc | Runs clean twice |
| 10 | 25:00–27:30 | README + GIF | — |
| — | 27:30–29:30 | Clean-env repro | Works from scratch |
| — | 29:30+ | Buffer, submit | — |

---

# When a gate fails

Only Phase 1 had a stop instruction. Every gate needs one, because "the gate failed" at hour 12 with no written recovery is how a plan turns into improvisation.

| Gate | If it fails |
|---|---|
| `0:25` pre-flight | ffprobe → install, demo path unaffected. Whisper → **hard stop**, nothing works without it. LLM → cut Phase 5, log it, continue |
| `2:00` assets | Reword the script and re-record **now**. Never proceed with a string Whisper cannot hear |
| `2:10` vertical slice | **Hard stop.** Strip the compiler plan to a single prompt with no retry logic. Nothing else matters until one real verdict prints |
| `3:15` six validators | Ship the ones that work; a broken validator becomes `MANUAL REVIEW`, never a fake PASS. Log it in `Memory.md` |
| `5:15` eval | Reduce the fixture count, never fake the number. A real 18-case number beats an invented 28-case one |
| `7:00` zero-key | **Hard stop — this is the submission.** Nothing after this matters until a clean venv runs `demo` |
| `9:30` compiler | Cut Phase 5. The committed hand-written spec carries the demo. Say so in the README's limitations |
| `12:00` editable spec | Ship read-only spec review. Note in the README that editing is not wired |
| `13:30` full MP4 | Ship the cached-transcript path only. `transcribe` becomes a documented manual step |
| `23:30` UI | Ship the CLI (`Rules.md` §9). The event says a working script counts |
| `25:00` demo arc | Ship V1 only. A single honest `DO NOT SEND` beats a broken arc |

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

Phase 4 is the line. If you reach `T+8:00` with the zero-key demo working, you have a complete submission no matter what happens next.
