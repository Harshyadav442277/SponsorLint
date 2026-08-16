# Rules — SponsorLint

Boundaries for any AI agent, teammate, or assistant working on this project.

**If this file conflicts with an agent suggestion, "this would look cooler," "a production system should," or an older document — this file wins.**

> The main risk is not insufficient ambition. It is **building too much and weakening the one workflow judges need to believe.**

---

# 0. The plan is frozen

`PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, and `Design.md` are **settled**. The product was chosen through an adversarial review and the corrections from that review are already applied (`Decisions.md`).

**Do not send these documents to another agent asking it to redesign the product.** Every extra review round produces plausible new features and costs hours you do not have.

The only review prompt permitted from here:

> *"Find contradictions, implementation blockers, or requirements that cannot be completed within the deadline. Do not propose new features."*

A finding that fits that prompt gets fixed in the source document and noted in `Memory.md` under Deviations. Anything else is out of scope.

---

# 1. The sixteen rules

1. **Do not add features because they are easy.**
2. **Do not add a seventh rule family** before every acceptance test in `PRD.md` §6 passes.
3. **Do not put an LLM in a final verdict** where deterministic code can verify. The LLM compiles; it never judges.
4. **Do not silently turn uncertainty into `PASS`.** Ambiguity goes to `MANUAL REVIEW`.
5. **Do not loosen a fuzzy threshold to make a demo pass.** If you are tuning a threshold to turn a FAIL green, you have broken the product.
6. **Do not fuzzy-match numeric values, ever.** `70` is not `73`.
7. **Do not polish UI before the verifier works.**
8. **Do not rewrite a working architecture for elegance.**
9. **Do not add a database, auth, billing, or Docker-first architecture.**
10. **Do not make the default demo require an API key or a model download.**
11. **Do not hardcode verdict output.** Every result is computed.
12. **Do not claim legal compliance.** You check the supplied brief, not the law.
13. **Do not add Cutcheck, retention analytics, or any second product.**
14. **Do not invent a rule the sponsor brief did not state.** No arbitrary disclosure thresholds, no house style guidance, no best-practice nagging. If it is not in the brief, it is not a requirement.
15. **Do not engineer scoring weights to produce a nicer number.** Report what the formula produces.
16. **When unsure whether something is in scope, it is out of scope.**

---

# 2. Libraries

## Use these

| Library | For |
|---|---|
| `fastapi` + `uvicorn` | API and serving the UI |
| `jinja2` | templates |
| `pydantic` | schema validation at every boundary |
| `rapidfuzz` | fuzzy matching — **names and phrases only**. `fuzz.partial_ratio` ≥ 90 on the **joined** transcript. **Never `fuzz.ratio`** (whole-string; measured 10–67 on true matches, so nothing can ever pass). **Never `partial_token_set_ratio`** (measured 100.0 on both documented hard negatives — a false-PASS machine) |
| `pypdf` | PDF text extraction |
| `faster-whisper` | transcription — **`base.en` model, CPU** |
| `ffmpeg` / `ffprobe` | duration, **at transcribe time only**. `ffprobe` writes `duration_seconds` into the transcript; validators read it from there and never shell out. **The demo path must run with no ffmpeg on PATH** |
| `pytest` | tests |

## Do not add without a reason tied to an acceptance test

Every new dependency is installation risk on a judge's machine.

## Explicitly banned

| Banned | Why |
|---|---|
| `easyocr`, `pytesseract` | **Named trap.** easyocr pulls ~2GB of torch on Windows; tesseract needs a system binary. A stretch goal that eats hour 20 and returns nothing. Visual requirements go to `MANUAL REVIEW`, which is the better answer anyway |
| `openai-whisper` (original) | Slower and heavier than `faster-whisper` for identical output |
| `torch` directly | Nothing here needs it |
| Next.js, React, any build step | See `Design.md`. Vanilla JS and plain CSS |
| Any ORM, `sqlalchemy`, `alembic` | No database. Files and in-memory dicts |
| `celery`, `redis`, any queue | Synchronous is fine for a 75-second clip |
| Any vector DB, `langchain`, `llamaindex` | One structured LLM call. No framework needed |

## GPU

**`faster-whisper` with `base.en` on CPU, from the start.** Do not detect CUDA, do not add a GPU code path, do not install GPU wheels. This is the most likely single hour-sink in the build and buys nothing on a 75-second clip.

---

# 3. Error handling

## The principle

**Never fail silently. Never fake a result. Never guess.**

Every error either surfaces a readable message or routes to `MANUAL REVIEW`.

## Per-failure behavior

| Failure | Required behavior |
|---|---|
| PDF unparseable | `"Could not extract readable text from the brief."` Offer a paste-text fallback |
| Compiler returns malformed JSON | Pydantic validation, **one** retry, then surface the error. Do not loop |
| Compiler is uncertain about a rule | Emit the rule with `needs_review: true`. Never fake certainty |
| Requirement not verifiable from audio/duration | Return it in `manual_review`. **Never drop it. Never guess it** |
| Whisper fails | `"Could not transcribe the sponsor segment."` **Do not silently continue** |
| Whisper output is questionable | Show the transcript evidence. Ambiguity → `MANUAL REVIEW` |
| `ffprobe` missing or fails | Clear message naming ffmpeg as the missing dependency |
| No rules in the approved spec | `"No requirements to check. Add at least one rule."` Do not return `SPONSOR READY` |
| Video file unreadable | Name the file and the reason |

## Message style

Errors say what went wrong and how to fix it. No apologies, no vagueness, no stack traces in the UI.

```
BAD:   "An error occurred."
BAD:   "Sorry! Something went wrong :("
GOOD:  "Could not extract text from brief.pdf — the file appears to be
        a scanned image. Paste the brief text instead."
```

## Never do this

```python
except Exception:
    pass                    # forbidden
except Exception:
    return PASS             # forbidden — this is faking a verdict
```

An exception inside a validator produces `MANUAL REVIEW` with the reason attached, never `PASS`.

---

# 4. Testing

## Write the failing test first, for every validator

The workflow per validator: write the failing test → implement → pass → run on V1 → move on.

## The fixtures are the tests

`sponsorlint/eval/fixtures.json` and `tests/` assert the same things. **Write each case once, use it twice.** The eval harness reads the fixtures; the unit tests read the fixtures.

## Minimum coverage

| Module | Must be tested |
|---|---|
| `normalize/numbers.py` | every equivalence and non-equivalence in `Architecture.md` §5.1 |
| `normalize/urls.py` | all four spoken URL forms |
| `normalize/codes.py` | at least one spelled-aloud promo code |
| each validator | one PASS, one FAIL, one edge case |
| `lint/engine.py` | readiness resolution for all three states |

Do not build an enormous suite. These are high-value and cheap.

---

# 5. Code standards

- **Validators are pure functions.** `(rule, transcript) → Result`. No I/O, no globals, no network. This is what makes them testable and what makes the eval harness possible.
- **Pydantic at every boundary.** Parse, don't validate-later.
- **No hidden state.** In-memory session dict keyed by uuid is the entire persistence layer.
- **Type hints on public functions.** Not exhaustive, just the module surfaces.
- **Match the surrounding code.** Do not introduce a second style.
- Commit messages describe the change. **No `Co-Authored-By` trailers, no AI attribution.**

---

# 6. Kill list

**Do not build any of these.**

**Product scope:** general creator platform · Cutcheck integration · retention analytics · sponsorship discovery · sponsor negotiation · rate estimation · brand or influencer marketplace · brand CRM · contract generation · invoicing · payment tracking · campaign analytics · multi-campaign management · social scheduling · YouTube/TikTok/Instagram posting.

**Video:** automatic editing · automatic re-recording · voice cloning · AI avatars · B-roll generation · sponsor script generation · thumbnail generation · auto-shorts · clip generation · EDL/FCPXML export · NLE plugins.

**Verification:** OCR · logo detection · object detection · face detection · any visual rule · generic fact checking · legal compliance engine.

**Infrastructure:** database · Docker-required demo · Kubernetes · queues · microservices · object storage · vector DB · RAG · autonomous agents · multi-agent runtime · deployment architecture.

**Product surface:** browser extension · mobile app · multi-user system · authentication · billing · database-backed history · onboarding wizard · settings dashboard · theme selector · animation systems.

If someone says *"wouldn't it be cool if…"* the default answer is **No.**

---

# 7. Feature request filter

Before adding anything, answer:

1. Does it directly answer *"did I follow this sponsor brief?"*
2. Does it improve a judging criterion?
3. Will a judge see or verify it?
4. Can it be built and tested quickly?
5. Does it strengthen the existing workflow rather than create a second product?

**Fewer than 4/5 YES → do not build it.**

---

# 8. Claims

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
- Guarantees legal compliance · "makes a video legally compliant"
- Verifies every kind of requirement
- Replaces brand review
- Catches every possible mistake
- **Any claim the eval harness does not support**

## Specifically: no regulatory language

Do not emit or write phrases like *"clear and conspicuous,"* *"FTC compliant,"* or *"legally required."* The disclosure-placement check emits an **advisory**, not a legal verdict, and only when the brief did not specify placement itself (`Architecture.md` §5.4).

## Specifically: never write "false positive"

The term reverses meaning depending on whether the reader thinks the positive event is a violation or a passing check. Always use the explicit form:

```
False FAIL   reported FAIL, requirement was actually satisfied
False PASS   reported PASS, requirement was actually violated
```

Definitions live in `Architecture.md` §7. Use them in output, in the README, and in conversation.

---

# 9. Cut order

If the clock goes bad, cut in exactly this order:

```
1. demo video
2. jump-to-timestamp on findings
3. UI polish
4. the web UI entirely — ship the CLI
```

**Never cut:** the eval number · the zero-key demo path · the README.

---

# 10. If retention data arrives mid-build

You will be tempted to switch to Cutcheck. **Do not.**

Cutcheck from a cold start in the remaining hours, with data landing mid-build and no validation harness, is a worse bet than a finished SponsorLint — and you would be abandoning certain progress for a project with four more gates ahead of it.

Bank the data. See `Decisions.md` §2.

---

# 11. Agent work split

| Agent | Owns |
|---|---|
| **A — Deterministic engine** | schemas · normalization · six validators · eval harness · unit tests |
| **B — Brief compiler** | PDF extraction · LLM prompt · `source_quote` preservation · schema validation · uncertainty handling |
| **C — Web UI** | upload · split-screen review · edit/delete/add · video input · result cards |
| **D — Demo / QA** | Aegis brief · V1 and spliced V3 · eval cases · README · clean-environment reproduction |

**Agents may not redefine scope.** An agent that believes the scope is wrong writes the objection into `Memory.md` and continues with the current scope.

---

# 12. Before you finish a work session

**Update `Memory.md`.** Every session. What you completed, what gate you passed, what is broken, what is next. An agent that finishes work without updating `Memory.md` has left the next agent to re-derive everything from the codebase.
