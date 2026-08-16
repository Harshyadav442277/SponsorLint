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
Phase:            10 complete in code. External gates need a recording and API key.
Last gate passed: Full dependency install + base.en CPU initialization
Clock:            built and hardened across four sessions, Aug 16 2026
Submittable:      YES — Phase 4 gate and canonical browser arc verified
```

**What works, verified by running it:**

- `python -m sponsorlint demo` → `3 FAIL · 0 WARN · 4 PASS · 1 MANUAL` → `4/7` → `DO NOT SEND`
- `python -m sponsorlint demo --arc` → `V1 4/7 DO NOT SEND` → `V3 7/7 SPONSOR READY`
- `python -m sponsorlint eval` → 30 fixtures, 29 correct, **96.7%**, 0 False PASSes, 1 False FAIL
- `python -m pytest tests -q` → **111 passed, 1 xfailed** in ~1.7s
- `python -m sponsorlint serve` → full four-screen flow drives end to end in a browser
- All six validators, the engine, normalization, the eval harness, the terminal report
- `compile` / `transcribe` / `analyze` are written but **not exercised live** (no key, no video)

**Verified in fresh `.venv-current` on Windows (full development dependencies):**

- `demo` and `eval` both run and exit 0
- `demo --arc` renders Unicode terminal output under Windows without a CP-1252 crash
- API regression test drives sample → approve → V1 → V3 → stored report
- In-app browser drives all four screens to both canonical verdicts with no console warnings/errors
- AST scan still finds zero module-scope `faster_whisper` / `pypdf` / `anthropic` / `torch` imports on the demo path
- `faster-whisper` and `anthropic` install cleanly; `base.en` is downloaded, cached, and initializes on CPU with `int8`
- Missing-key and missing-video failures are readable CLI errors with exit code 2, not tracebacks
- The earlier `.venv-judge` no-ffmpeg reproduction remains historical evidence; its Python 3.12 base was removed from this machine, so its launcher is now stale

**Next action:** record `samples/sponsor-cut-v1.mp4` and `samples/sponsor-cut-v3.mp4`
from `samples/script.md`, then follow the candidate-transcript commands in
`samples/README.md`. Do not overwrite the authored fixtures before the six-string gate passes.

---

## Gate tracker

| Phase | Gate | Status |
|---|---|---|
| — | Repo exists, demo deps install clean | ☑ |
| 0 | Brief + V1 exist; Whisper hears the planted errors | ☐ **brief/script/PDF exist; V1 not recorded** |
| 1 | One command → one real verdict from cached transcript | ☑ |
| 2 | All six validators produce verdicts on V1 | ☑ |
| 3 | `eval` prints real metrics, no hardcoded score | ☑ 96.7% |
| **4** | **Fresh clone → `demo` → real output, no key** ← **SUBMITTABLE** | ☑ verified in `.venv-judge` |
| 5 | Prose brief → correct spec, `min_seconds: 60` extracted | ☐ **code complete, no live API call made** |
| 6 | Editing `73%` → `70%` flips the real verdict | ☑ verified in the browser and in `tests/test_engine.py` |
| 7 | Fresh MP4 → real report, no manual file editing | ☐ **code complete, no video to try** |
| 8 | Judge understands the report without a terminal | ☑ |
| 9 | `DO NOT SEND → SPONSOR READY` arc runs clean twice | ☑ on fixtures; re-verify after recording |
| 10 | README complete with real eval numbers | ☑ |
| — | Clean clone, fresh venv, everything runs | ☑ |

---

## Acceptance tests

Mirrors `PRD.md` §6. Check off only when actually verified, not when believed.

```
☑  1  Approved spec + transcript → deterministic results
☑  2  MUST_SAY pass/fail
☑  3  MUST_NOT_SAY + timestamp, no partial-substring false fire
☑  4  "seventy-three percent" PASSES 73%
☑  5  "seventy percent" FAILS 73%
☑  6  Spoken URL normalizes                    (4 forms, tests/test_normalize_urls.py)
☑  7  Spoken promo code normalizes             (H-A-R-S-H two zero → HARSH20)
☑  8  Disclosure detected with timestamp
☑  9  DURATION reads transcript.duration_seconds (validator never shells out)
☐ 10  Prose brief compiles to valid schema     — needs one live API call
☑ 11  Every rule carries source_quote          (enforced in models.py, rejected without)
☑ 12  Unverifiable requirements → MANUAL REVIEW
☑ 13  User can edit / add / delete rules
☑ 14  Edited spec changes the real verdict     (browser + test_engine.py)
☐ 15  Fresh MP4 transcribed and verified       — needs the recording
☑ 16  eval reports actual metrics
☑ 17  demo works with no credentials, no download, no ffmpeg
☑ 18  Every failure shows expected/detected/timestamp/evidence/source
☑ 19  Readiness states resolve correctly       (all three, plus manual-review isolation)
☑ 20  No hardcoded verdicts anywhere
```

18 of 20 pass. The two open ones both need an artifact only the creator can produce (an API key, a recording) — no code is missing for either.

---

## Key facts an agent needs

Pinned so nobody has to re-derive them.

| | |
|---|---|
| Fictional brand | `Aegis VPN` · `aegisvpn.com/alex` · `Shield Mode` · `73%` · `HARSH20` |
| Planted errors in V1 | "seventy percent" (0:43) · no "Shield Mode" · "completely anonymous" (0:31) |
| Expected V1 verdict | 3 FAIL · 0 WARN · 4 PASS · 1 MANUAL → `4/7` → `DO NOT SEND` |
| Transcript fixture | `samples/transcript.v1.json` — **cached, never re-run Whisper in dev** |
| Whisper config | `faster-whisper`, `base.en`, **CPU only, no GPU path** |
| Fuzzy scorer | `rapidfuzz.fuzz.partial_ratio` >= 90 on the **joined** transcript. Never `ratio`, never `partial_token_set_ratio` |
| Canonical spec | 7 rules, all `severity: error` — see `PRD.md` §5 |
| Demo command | `python -m sponsorlint demo` — no key, no download, run from repo root |
| Real eval number | **96.7%** · 30 fixtures · 0 False PASSes · 1 False FAIL (documented limitation) |
| Never cut | eval number · zero-key demo · README |

### Measured values, so nobody re-litigates them

| Needle vs haystack | `partial_ratio` | Consequence |
|---|---:|---|
| `shield mode` / "try sheild mode today" (Whisper typo) | 90.9 | PASS — barely over threshold |
| `shield mode` / "try mode shield today" | 81.8 | FAIL |
| `shield mode` / "try the shield feature today" | 72.7 | FAIL |
| `completely anonymous` / "completely anonymou online" | 95.0 | MANUAL REVIEW, never FAIL |
| `aegisvpn.com/alex` / "aegis.com/alex" | 82.4 | FAIL — 7.6 points of headroom, hence no URL fuzzing |
| `aegisvpn.com/alex` / "aegisvpn.com/jordan" | 76.5 | FAIL |

---

## Session log

*Newest first. One block per working session.*

### Session 4 — real-input preflight · Aug 16, 2026

- Installed the full `requirements.txt` stack in `.venv-current`, including `faster-whisper` and `anthropic`
- Downloaded and initialized the pinned `base.en` Whisper model on CPU with `int8`; the model is cached locally and ready for the recording
- Confirmed `samples/brief.pdf` extracts successfully; the live compiler remains correctly blocked because `ANTHROPIC_API_KEY` is not set
- Confirmed against the current official Anthropic docs and installed SDK 0.122.0 that `claude-opus-5`, `messages.parse(...)`, Pydantic `output_format`, and `parsed_output` are all valid
- Fixed `compile`, `transcribe`, and `analyze` so expected setup failures return readable exit-code-2 messages instead of Python tracebacks; added two regression tests
- Corrected GATE 2:00 from seven spoken strings to six: `HARSH20` is a normalization fixture, not a requirement in the frozen brief/spec/script
- Added a safe `.whisper.json` candidate workflow so first-pass transcription cannot overwrite the authored demo fixtures
- Final gate: **111 passed, 1 intentional xfail**

### Session 3 — Windows hardening + browser QA · Aug 16, 2026

- Preserved the existing untracked build and created `.venv-current` from the bundled Python 3.12 runtime after discovering that `.venv` and `.venv-judge` point to a removed interpreter
- Added a repo-local `pytest.ini`; without it, pytest inherited `C:\Users\hyada\pyproject.toml`, chose the home directory as `rootdir`, and failed against the filesystem sandbox before collecting this project's tests
- Fixed the Windows CLI crash by switching process-owned stdout/stderr to UTF-8 before rendering the box-drawing report; added a regression test
- Added an end-to-end FastAPI regression test for sample load → approval → V1 `DO_NOT_SEND` → V3 `SPONSOR_READY` → persisted report, plus the current `httpx2` test dependency
- Drove the same arc through the rendered four-screen UI in the in-app browser and checked the finished report visually; no browser warnings or errors
- Final gate: **109 passed, 1 intentional xfail** · eval **96.7%** · **0 False PASSes**

### Session 2 — the build · Aug 16, 2026

Built the whole thing, in the phase order `Phases.md` specifies, verifying each gate by running it.

- **Phase 0:** `samples/brief.md` verbatim from `PRD.md` §5 (not "improved"), `brief.pdf` generated by a dependency-free `tools/make_brief_pdf.py`, `script.md` with the three planted errors marked and the three V3 replacement lines, and both transcript fixtures hand-authored to match the script (see Deviations D-1)
- **Phase 1–2:** `models.py` with the pinned per-type payload, the normalization pipeline, the joined-transcript `Haystack` with two views and offset maps, all six validators, engine with three-clause readiness resolution
- **Phase 3:** 30 labeled fixtures. First pass scored 30/30, which meant the fixtures were too easy — swapped six weak cases for six harder ones and the real number became 96.7%
- **Phase 4:** zero-key demo, `--arc`, AST import check, and the `.venv-judge` verification
- **Phase 5:** pypdf extraction, versioned prompt, `claude-opus-5` structured outputs against the `Spec` model, one retry then surface
- **Phase 6–8:** FastAPI + Jinja2 + vanilla JS, three screens plus the report, `Design.md` tokens applied literally
- **Phase 10:** README in the `Phases.md` order, eval number above the feature list

**Three real bugs found by running things, not by reading them:**

1. `normalize_text` strips `:`, so `https://x` arrived as `https //x` and the scheme regex never matched. Caught by `tests/test_normalize_urls.py`.
2. `templates.TemplateResponse("index.html", {"request": request})` — the installed Starlette requires the newer `(request, name)` signature and threw `TypeError: unhashable type: 'dict'` on every page load. Caught by opening the page.
3. I wrote "measured 90.3" into a code comment about URL fuzzing from memory. The actual measurement is **82.4**. Corrected in the comment and pinned in the table above. Do not state a measurement you have not run.

**Still not done:** the recording. Everything downstream of it is built and tested against fixtures.

### Session 1 — hardening · Aug 16, 2026

- Six-lens survey of the frozen docs, scoped to `Rules.md` §0. Nine distinct blockers found and closed (`Decisions.md` D21)
- **Measured, not argued:** `rapidfuzz.ratio` scores every true match 10–67 — the specified matcher could never have passed anything. Now `partial_ratio` on the joined transcript
- **Verified by building it:** a module-scope faster-whisper import kills `demo` in a demo-only venv before dispatch. Import discipline + AST check added
- Fixed: V1 verdict is `3 FAIL · 0 WARN · 4 PASS · 1 MANUAL` (was wrong in 4 files) · V3 could never reach SPONSOR READY · Rule schema couldn't hold DURATION/multi-phrase/placement · DURATION had 3 duration sources · two invocation forms
- Canonical 7-rule spec pinned in `PRD.md` §5. Phase clock reflowed; Phase 0 rebudgeted 45→95 min; per-gate failure recovery added
- **Still no code written**

### Session 0 — planning · Aug 15, 2026

- Ran an adversarial bakeoff between Cutcheck and SponsorLint. SponsorLint won 7.6 to 6.7. Reasoning preserved in `Decisions.md` D1
- Merged three prior SponsorLint plans into a single bible, then split it into these seven documents
- Applied four freeze corrections from a final review — validator taxonomy, no invented disclosure threshold, `False FAIL`/`False PASS` terminology, no engineered scores (`Decisions.md` D19)
- Deleted the superseded plans; git history retains them. **These seven documents are the only authority**
- **Plan is frozen** (`Rules.md` §0). No more redesign rounds
- **No code written**

---

## Known issues

```
[ISSUE] Disclosure matching misses "this is sponsored content"
  where:  sponsorlint/lint/disclosure.py DISCLOSURE_PATTERNS
  repro:  python -m sponsorlint eval  ->  disclosure/known-limitation-unlisted-phrasing
  impact: one measured False FAIL. Documented in the README limitations and kept in
          the fixture set deliberately, so the published number stays honest.
  status: open by choice. Architecture.md §5.3 pins the five accepted phrasings;
          adding a sixth is a scope decision, not a bug fix. Do not quietly widen it.

[ISSUE] Recording does not exist yet
  where:  samples/sponsor-cut-v1.mp4, samples/sponsor-cut-v3.mp4
  repro:  ls samples/*.mp4
  impact: GATE 2:00 (Whisper hears all six critical strings) is UNTESTED.
          `aegisvpn.com/alex` is a fabricated brand name base.en may mangle -- if it
          does, reword the script BEFORE recording, per Phases.md.
  status: open. Blocks acceptance tests 15 and the real GATE 9.

[ISSUE] Compiler never called live
  where:  sponsorlint/brief/compile.py
  repro:  ANTHROPIC_API_KEY=... python -m sponsorlint compile samples/brief.pdf
  impact: acceptance test 10 unverified. If it fails, Phase 5 is cut per Phases.md
          and the committed hand-written spec carries the demo -- the zero-key path
          does not need the compiler at all.
  status: open. Blocks nothing that is already working.
```

---

## Deviations from the plan

*Anything done differently from `PRD.md` / `Architecture.md` / `Rules.md` / `Phases.md`, and why.*

**D-1 · Transcript fixtures are hand-authored, not Whisper output.** `Phases.md` Phase 1 says
"transcribe V1 once". There is no V1 to transcribe yet. `samples/transcript.v1.json` and
`.v3.json` match `samples/script.md` line for line with realistic segment boundaries and timings.
Every validator, the eval and the demo run for real against them; only the *provenance* of the
text is different. Flagged in `samples/README.md` and in the README limitations. **Regenerate both
with `transcribe` once the takes exist** — nothing else changes.

**D-2 · Eval fixture set rebalanced, count held at 30.** The first 30 scored 30/30, which measures
the fixtures rather than the tool. Dropped six weak cases (`must_say/exact`,
`must_say/case-and-punctuation`, `must_not_say/negated-still-spoken`,
`exact_value/spelled-out-unhyphenated`, `url_or_cta/mixed-case`, `duration/inside-window`) and
added six harder ones, including one **deliberate known-limitation case labeled by ground truth**
that produces a real False FAIL. Count stays inside the documented 24–30 band.

**D-3 · `URL_OR_CTA` does not fuzzy-match URLs or promo codes.** `Architecture.md` §5.3 says
"canonicalize both sides, then containment"; it does not forbid a fuzzy fallback, and my first
draft had one. A tracked URL is an identifier, not a phrase — the same class of thing as a numeric
value, which `Rules.md` §1.6 forbids fuzzing. Measured margin is only 7.6 points
(`aegisvpn.com/alex` vs `aegis.com/alex` = 82.4). Fuzzy is now used only for prose CTAs.

**D-4 · `transcribe` falls back to the decoder's own duration when ffprobe is missing.**
`Rules.md` §3 says "clear message naming ffmpeg as the missing dependency". It does that, on
stderr, and then uses the duration faster-whisper reports from its own decode rather than failing
the whole transcription. Not silent, and strictly better than losing the transcript.

**D-5 · The compiler prompt carries a `SCHEMA_NOTES` addendum.** `Architecture.md` §9's prompt
alone cannot produce the disclosure-placement shape §5.4 mandates
(`within_first_seconds: null, needs_review: true` when the brief states placement in words but
gives no number). The addendum states the per-type payload rules and that one behavior. §9's text
is unchanged and comes first.

**D-6 · `Report.status` uses the readiness values, not `"FAIL"`.** `Architecture.md` §4.5's
example JSON shows `"status": "FAIL"`, which contradicts §5.5 and `PRD.md` §3. Went with the
normative three states (`DO_NOT_SEND` / `REVIEW` / `SPONSOR_READY`) and added a `label` property
for display.

**D-7 · `Result` gained an `advisory` field.** Required by §5.4's disclosure advisory, and reused
for the MANUAL_REVIEW reason and the MUST_SAY closest-match hint. Never a verdict.

**D-8 · The review screen has no [Edit] mode.** `Design.md` §5.4 shows `[Edit] [Del]`. Fields are
always live inputs instead, with Delete kept. Fewer clicks, and it makes GATE 12:00 demonstrable
in about four seconds.

**D-9 · No server-side `fallbacks` on the compiler call.** The Anthropic guidance is to opt into
refusal fallbacks by default on `claude-opus-5`. `client.messages.parse()` — the clean structured-
output path that lets the API constraint and the Pydantic validation be the same schema — is not
on the beta namespace, and combining the two is an unverified shape. A refusal instead surfaces as
a readable error, which is what `Rules.md` §3 asks for anyway.

**D-10 · Timecode buttons copy, they do not seek.** There is no video player in the UI, and
jump-to-timestamp is cut #2 in `Rules.md` §9. The button is still a real keyboard-reachable
`<button>`; clicking copies `00:43` so it can be pasted into an editor timeline.

**D-11 · GATE 2:00 checks six spoken strings, not seven.** `Phases.md` had added `HARSH20`
to the recording gate even though the frozen demo brief, canonical spec, and script never mention
that code. Promo-code normalization remains covered by acceptance test 7 and its labeled fixtures;
requiring it in the recording would invent a sponsor requirement and contradict `Rules.md` §1.1.

---

## Cut log

```
Nothing cut. Every feature in PRD.md §4.1 is implemented, including the eval harness
and the zero-key demo. Stretch items from §4.2 not built: jump-to-timestamp seeking
(no player), downloadable HTML report, demo video.
```

Cut order from `Rules.md` §9: demo video → jump-to-timestamp → UI polish → web UI entirely.

---

## Handoff note

> Everything is built and the zero-key path is verified in a clean demo-only venv — the project is
> submittable as it stands. The one missing artifact is the recording: write it from
> `samples/script.md`, check GATE 2:00 (all six critical strings, both columns) *before*
> committing to the take, then regenerate both transcripts with `transcribe`. Read
> **Deviations D-1** first — the committed transcripts are authored fixtures, and the README says so.
