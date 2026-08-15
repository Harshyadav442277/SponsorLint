# Decisions — SponsorLint

Why the project is shaped the way it is. Read this before proposing a change to `PRD.md`, `Architecture.md`, or `Rules.md` — most "obvious improvements" were already considered and rejected for a reason recorded here.

Format: **the decision · the alternative · why · what would change our minds.**

---

## D1 · Build SponsorLint, not Cutcheck

**Decided:** Aug 15, 2026, after an adversarial bakeoff (two advocates + a judge). Full record in git history: `git show e759a5b:docs/BAKEOFF.md`.

**Alternative:** Cutcheck — mine a creator's own retention curves for editing patterns that coincide with viewer drop-off, then lint the next unpublished cut.

**Why SponsorLint won, 7.6 to 6.7 on the rubric:**

Cutcheck is the **better idea**, and it lost anyway. Under a 72-hour clock with retention exports already on disk, it would be the pick. That was not the situation.

| | Cutcheck | SponsorLint |
|---|---|---|
| Functionality 30% | 6 | **8** |
| Usefulness 30% | 7 | **8** |
| Creativity 20% | **8** | 7 |
| Technical execution 20% | 6 | **7** |

The three findings that decided it:

1. **Cutcheck's Phase 0 was a four-way conjunction on a stranger's weekend.** A creator must agree within hours, perform 5–10 per-video Studio exports, *also* hand over multi-gigabyte source files, and have a channel large enough that the curves are not noise. Probability of clean data by hour 8: under 20%.
2. **Total function vs. partial function.** A brief always compiles to rules; rules always evaluate to a status; the report is never empty. Cutcheck can legitimately produce *nothing* — if no rule clears minimum support, the product ceases to exist, and you discover that around hour 14–20 with one recovery available: fake the data.
3. **Cutcheck is cliff-edged, not layered.** Its Phases 1–3 produce no user-facing output. A Cutcheck that halts at Phase 2 is a script that detects silence in an MP4. SponsorLint at hour 8 is a working script, and the event says explicitly that a working script counts.

**What would change our minds:** nothing, within this hackathon. See D2.

---

## D2 · If retention data arrives mid-build, do not switch

**Why:** Cutcheck from a cold start in the remaining hours, with data landing mid-build and no validation harness, is a worse bet than a finished SponsorLint. Switching abandons certain progress for a project with four more gates ahead of it.

Bank the data. Cutcheck is a genuinely good post-hackathon project and will still be good in September, built properly, with a backtest and the promise–payoff analysis a 36-hour version would have to cut.

---

## D3 · The LLM compiles; deterministic code verifies

**Alternative:** feed the brief and the transcript to an LLM and ask "is this compliant?"

**Why:** four properties fall out of the split, and none survive the alternative.

| Property | Why it matters |
|---|---|
| Reproducible | Same inputs → same output. A judge who reruns gets the same answer |
| Auditable | Every FAIL cites a transcript line and a source quote |
| **Testable** | The eval harness (D5) is only possible because verdicts are deterministic |
| Debuggable | Each stage is a separate CLI command |

It is also the answer to the objection every AI submission faces: *"isn't this just a wrapper?"* — **the LLM never sees the transcript.**

**What would change our minds:** a rule type that genuinely cannot be verified deterministically. Those go to `MANUAL REVIEW` instead (D6).

---

## D4 · The user approves the spec before verification runs

**Alternative:** compile the brief and go straight to checking.

**Why:** one screen kills three objections at once.

| Objection | Killed by |
|---|---|
| "The LLM hallucinated the requirements" | Every rule cites its source sentence |
| "You planted the errors you found" | The judge adds their own rule and re-runs |
| "Can you trust an LLM to read a contract?" | You don't have to — the correction **is** the product |

Trust model: **the model proposes the specification, the user owns the specification, deterministic code enforces the approved specification.**

Every other AI submission at this event is an oracle. Ours has a spec the user can argue with.

**This is why `Phases.md` GATE 12:00 is "changing 73% to 70% flips the verdict"** — if the edit does not change the outcome, the screen is a mockup and the whole argument collapses.

---

## D5 · The eval harness is required, not a stretch goal

**Borrowed from the losing side.** Cutcheck's earlier plan had a `backtest` verb producing a real precision number; its own execution bible then deleted it — removing the single best answer to its worst objection. We took the idea.

**Why:** almost no hackathon submission measures its own claims. A disclaimer is a pre-emptive concession; a measured number is a defense. It also directly answers *"isn't this just string matching?"* — it's string matching **that we measured**, which is more than the rest of the field can say.

**Tuning policy — the reasoning behind it:**

> A false FAIL wastes the creator's afternoon. A false PASS ships a broken sponsor read to the brand. The two errors are not symmetric, so we avoid false FAILs, route ambiguity to `MANUAL REVIEW`, and then maximize violation catch rate.

That is a designed engineering tradeoff, stated in one sentence, backed by a number.

**Publish the real number even if it is bad.** A mediocre measured number outscores an unmeasured claim with anyone who has a research background.

---

## D6 · Unverifiable requirements become MANUAL REVIEW

**Alternatives rejected:** silently drop them · let the LLM guess · build OCR.

**Why:** a tool that refuses to fake a verdict is demonstrating judgment, and judgment is what Technical execution measures. It also converts our largest capability gap into a trust feature.

**On OCR specifically:** `easyocr` pulls ~2GB of torch on Windows and tesseract needs a system binary. It is a stretch goal that eats hour 20 and returns nothing. `MANUAL REVIEW` is not the consolation prize here — it is the better answer.

---

## D7 · Disclosure placement is an advisory, not a verdict

**Earlier draft got this wrong** and emitted *"unlikely to be considered clear and conspicuous"* — FTC statutory language, which contradicted our own rule against legal claims.

**Current behavior:** if the brief specifies placement (the demo brief says *"near the beginning"*), enforce it as a normal rule. If it does not and disclosure is late, emit an advisory only. **Never quote regulatory language. Never call it non-compliance.**

We check the supplied brief, not the law.

---

## D8 · The demo brief is prose, and every sentence is deliberate

**Alternative:** a clean bulleted requirements list.

**Why:** if the brief is already structured, the compiler looks like it parsed a list, and the whole D3 architecture argument collapses into *"I asked an LLM to read a formatted document."* No regex extracts `min_seconds: 60` from *"no shorter than one minute."*

**Two specific choices that look like mistakes and are not:**

- **`seventy-three percent` spelled out, buried mid-sentence.** Writing `73%` as digits hands the compiler an easy extraction and removes the numeral-normalization moment, which is the ten seconds that prove the pipeline is real.
- **Prohibited claims quoted literally** (`"completely anonymous"`, `"unhackable"`) rather than paraphrased. An earlier draft wrote *"characterize the service as making the user untraceable"* — more realistic, but it creates a semantic gap a deterministic `MUST_NOT_SAY` cannot bridge, silently breaking the demo. Realism loses to a working chain.

Do not "improve" the brief in `PRD.md` §5.

---

## D9 · Fictional brand throughout

Earlier drafts used `Threat Protection Pro` and `nordvpn.com/alex` — a real company's actual product name and URL format, inside a fabricated brief with fabricated compliance violations, in a public repo.

Needless risk and it reads as careless. `Aegis VPN` / `aegisvpn.com/alex` / `Shield Mode` cost ten minutes and remove an unforced error.

---

## D10 · Zero-key demo path is a core deliverable

**Assume the judge is never in the room.** The event is repo + README + optional video. Someone clones at 2 AM and gives us sixty seconds.

Two walls kill that, and both sit on the default path unless explicitly removed:

- an `OPENAI_API_KEY` prompt → gone in thirty seconds
- a Whisper model download → gone in sixty

`python -m sponsorlint demo` runs the **real verifier** against committed fixtures. Split requirements files enforce it.

> **Caching is not cheating; fake output is.** The check executes for real; only the expensive, deterministic upstream steps are cached.

This also neutralizes the one genuine structural advantage Cutcheck had — being zero-key by construction — for about 30 minutes of work.

---

## D11 · The README is the primary judging surface

The demo video is **optional**. That means most of the field will pour their last hours into a video and ship three lines of markdown. The README is therefore the cheapest differentiation available at this event.

Consequence in `Phases.md`: the README gets a dedicated 2.5-hour block, and the eval number goes **above** the feature list because most repos bury validation.

---

## D12 · Zero-key demo lands at Phase 4, not Phase 8

**Alternative:** build it near the end, alongside polish.

**Why:** it is the safety net, so it should arrive early. At `T+7:00` the project is submittable — real analysis, measured, runnable by a stranger. Everything after raises the ceiling; nothing after is load-bearing. A safety net delivered last is not a safety net.

---

## D13 · Six rule types, hard limit

**Why:** each additional type is a new normalization surface, new fixtures, new failure modes, and a new way for the demo to break. The six cover the demo brief completely and every common sponsor requirement that is verifiable from audio or duration.

**What would change our minds:** all twenty acceptance tests passing with time left.

---

## D14 · Vanilla stack, no build step

FastAPI + Jinja2 + vanilla JS + plain CSS. No Next.js, no React unless it is already faster for the team, no bundler.

**Why:** a build step is a category of failure that produces nothing a judge can see. The UI is three screens and a list of cards. `Design.md` specifies it fully in CSS custom properties.

**Fallback if the UI fights us for more than an hour:** ship the CLI. The event says a working script counts, and `Rules.md` §9 puts the web UI last in the cut order.

---

## D15 · `faster-whisper` `base.en` on CPU, no GPU path

**Why:** the single most likely hour-sink in the build, and it buys nothing on a 75-second clip. No CUDA detection, no GPU wheels, no second code path.

---

## D16 · Transcribe once, cache forever

Whisper runs **once** during development, at Phase 1. `samples/transcript.v1.json` is then the fixture for the remaining thirty hours.

**Why:** it makes every downstream iteration instant, it makes the validators testable without media, and it is what the zero-key demo ships against.

**Corollary — the Phase 0 reality check:** transcribe the three planted error sentences *before* committing to the script. If Whisper garbles "seventy percent," change the script to a mistake it can hear. The entire demo centerpiece rests on one transcription, and finding out at hour 26 is fatal.

---

## D17 · Six hours of sleep are in the plan

**Why:** the builder is one person on a ~30-hour clock. Every gate after `T+13:30` is judgment work rather than typing. A plan with no sleep block is a plan that gets abandoned around hour 20, and the last four hours are worth nothing if you cannot think.

---

## D18 · The goal is un-dismissable, not unbeatable

A project that "cannot lose against anyone" is not achievable. Judging is stochastic, 20% of the rubric is explicitly taste, and we control neither the field nor demo order nor judge fatigue.

The achievable target: **no judge can complete the sentence *"this doesn't work"* or *"I've seen this one."*** Un-dismissable projects do not always win, but they never place badly — and in a field where most submissions are dismissible in ten seconds, that is most of the distance.

Every one of D5, D10, D11, and D12 exists to serve that target.

---

## D19 · Four freeze corrections, and the plan is now closed

Applied Aug 15, 2026, from a final review pass. Three of the four were already absent from the seven documents and are now stated **explicitly** rather than merely not violated — absence is not a guardrail, since a future agent reintroduces what nobody forbade.

**19a · Validator taxonomy.** Earlier drafts drifted between "six rule types" and "eight validators." Fixed form (`PRD.md` §4.1):

```
6 executable rule types
+ 1 disclosure-placement advisory   (a property of the MUST_DISCLOSE result)
+ 1 MANUAL_REVIEW outcome           (what happens when no validator exists)
```

`MANUAL_REVIEW` is not a validator — it is the absence of one. Counting it as a rule type inflates the surface and muddies the architecture.

**19b · No invented disclosure threshold.** An earlier draft flagged disclosure occurring after 25% of the segment or 30 seconds, with the string *"unlikely to be considered clear and conspicuous."* Both are removed. That threshold was **a rule not derived from the sponsor brief** — we would have been inventing a requirement on the creator's behalf — and the wording was FTC statutory language, contradicting D7 and `Rules.md` §8. Current behavior in `Architecture.md` §5.4: brief specifies placement → enforce; otherwise → show the timestamp, optional advisory, never a verdict.

**19c · "False positive" is banned as a term.** It reverses meaning depending on whether the reader treats a violation or a passing check as the positive event — so a judge can read our strongest engineering stance backwards. Replaced everywhere with `False FAIL` and `False PASS`, defined once in `Architecture.md` §7 with the asymmetric cost attached to each.

**19d · Do not engineer weights to hit a score.** The `57% → 86%` figures in earlier drafts were illustrative and risked becoming a target. Demo material now uses the raw fraction (`4/7 → 6/7 → 7/7`), which is more trustworthy and cannot be accused of tuning. `Rules.md` §1.15 makes it a rule.

**And the plan is frozen.** `Rules.md` §0 now closes it. The product was chosen through adversarial review, the corrections are applied, and further review rounds produce plausible new features at the cost of hours we do not have. The only permitted review prompt from here:

> *"Find contradictions, implementation blockers, or requirements that cannot be completed within the deadline. Do not propose new features."*

---

## Open questions

| Question | Owner | Resolve by |
|---|---|---|
| Which LLM provider for the compiler | — | Phase 5 |
| Whether the eval fixture count lands at 24 or 30 | — | Phase 3 |
| Whether jump-to-timestamp survives the cut | — | Phase 8 |

---

## Superseded documents

Deleted from the working tree; **retained in git history** (`git show e759a5b:docs/<file>`). They are history, not instructions.

| File | What it was | Contradicts |
|---|---|---|
| `STRATEGY.md` | Original Cutcheck pitch and rubric decode | D1 — wrong product |
| `BAKEOFF.md` | The full adversarial comparison and rulings — source for D1 | — |
| `SponsorLint_Project_Bible.md` | First SponsorLint plan | **D9** — uses a real brand's product name and URL |
| `SPONSORLINT_EXECUTION_BIBLE.superseded.md` | Second plan, folding in the bakeoff | **D7, D19b** — emits FTC statutory language |
| `SPONSORLINT_FINAL_EXECUTION_BIBLE.md` | Third plan | D19a — validator-count drift |

**Why they were removed rather than archived in-repo:** each is a superseded authority, and two contain instructions these documents explicitly reverse. An agent that greps the repo, or a session pointed at a folder, reintroduces a documented bug. Git already preserves everything, so an archive folder alongside version control is redundant *and* a loaded gun.

## D20 · Keep the bible, as a reference narrative

**Kept:** `docs/SPONSORLINT_BIBLE.md` — the merged bible, direct source of the seven documents.

**Why keep it** when D19's whole argument was that superseded authorities are dangerous: a single readable file has real uses the seven do not cover — onboarding a person, pasting into a tool that wants one document, drafting the submission blurb. The seven are optimized for an agent working one phase at a time; the bible is optimized for a human reading end to end.

**Why it is safe, unlike the four that were deleted:**

1. Its header was inverted — it now declares itself a reference narrative and states that root documents win any disagreement.
2. It carries all four D19 corrections. It does not contradict anything.
3. It is one file with an unambiguous status line, not a folder of four rival plans.

**The standing obligation:** anyone editing a root document either updates the bible to match or flips its header to `STALE`. **A reference narrative that has silently drifted is worse than none** — it is precisely the failure mode D19 was about, wearing a friendlier label.
