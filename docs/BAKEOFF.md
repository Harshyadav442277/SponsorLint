# The Bakeoff — Cutcheck vs. SponsorLint

**Question:** with ~36 hours on the clock, which project has the higher chance of winning?

**Format:** two advocates argued opposite sides. A judge who has sat through hundreds of hackathon demos ruled. The judge was then shown both advocate briefs and asked whether anything changed.

**Outcome:** **SponsorLint, ~80% confidence.** Cutcheck is the better idea and loses anyway.

---

## Ground rules

| | |
|---|---|
| **Event** | Social Media Automation Hackathon — working tool automating part of the creator pipeline. Repo + README required, demo video optional. *"Actually run and produce a real result — a UI is a bonus, but a working script counts."* |
| **Rubric** | Functionality **30%** · Real-world usefulness **30%** · Creativity **20%** · Technical execution **20%** |
| **Deadline** | Aug 17 2026, 4:30 AM IST |
| **Time at judging** | ~Aug 15, late afternoon IST — **roughly 36 hours**, including sleep |
| **Team** | Solo or small, with AI coding assistance |
| **Open risk** | No confirmed real YouTube retention exports in hand. Cutcheck's Phase 0 gate is **unmet**. |

### The contenders

**Cutcheck** — learns which editing patterns coincided with audience drop-off in a creator's past videos, then warns about those patterns in the next unpublished cut. Source: `CUTCHECK_EXECUTION_BIBLE.md`.

**SponsorLint** — compiles a sponsor brief into executable checks, runs them against the recorded sponsor segment, and returns timestamped PASS / WARN / FAIL before the creator sends it to the brand. Source: `SponsorLint_Project_Bible.md`.

Both pitch themselves as "ESLint for X." The metaphor is a wash.

---

# Round 1 — The case for Cutcheck

### Rubric, line by line

**Functionality (30%).** Four independently verifiable stages, all offline and deterministic: CSV→cliffs, MP4→silence/scene/low-motion, events×cliffs→`rules.json`, new MP4+rules→`lint_report.json`. No network, no API key, no model download, no rate limit, no nondeterminism in the critical path — §31 Rule 9 bans LLMs from the analysis path outright. Every failure mode is local and debuggable at 3 AM. Gates are front-loaded: Phase 1 has a hard stop, Phase 4 is named "the central product milestone," UI is deferred to Phase 5.

**Real-world usefulness (30%).** The strongest column. Retention is the metric YouTube's own algorithm optimizes against; every creator looks at the graph and fails to act on it, because turning a squiggly line into an editing decision is unstructured manual labor. Three properties that resist attack:

- **Per-creator, not generic.** No chatbot can produce *"on your channel, low-motion sections over 6.5s aligned with cliffs 5 of 8 times."*
- **Closes a loop that is currently open.** The market is full of asset generators. This consumes outcome data and feeds it back into production.
- **Larger denominator.** Every creator with a back catalogue, versus SponsorLint's own §0 scope lock to creators handling paid sponsor integrations.

§19's banned-claims list also makes the pitch honest, and volunteering a limitation before it is asked converts a deduction into a credibility gain.

**Creativity (20%).** *"Your retention graph is training data for a linter"* is a memorable reframe — not a new model, a new direction of data flow.

**Technical execution (20%).** §24 reads as a checklist of what judges scan for: typed schemas, module boundaries, cheap unit tests on pure functions, documented limitations, explicit error states. Support / hit rate / baseline / lift / average drop, with a `support >= 3` floor that refuses to emit a rule on thin evidence.

### The demo moment

Split screen. Left, the creator's real Studio retention curve with a visible cliff at 0:48. Right, a rules card:

```
LOW VISUAL ACTIVITY · 5/8 similar sections aligned with cliffs
avg decline 8.1% · lift 2.6x
```

Drag in an unpublished MP4. Real progress stages tick. The timeline paints three markers:

```
00:18 — HIGH — 7.2s of low visual activity. Across your previous 8
videos, similar sections aligned with an average 8.4% decline.
```

**Why it survives:** the judge watches a machine learn something specific about *one person* and then act on it. Every other submission shows a generic transformation where the same input yields the same output for everybody. `2.6x` was computed, not written.

### Attack on SponsorLint

1. **LLM on the critical path, and the bible knows it.** §7 makes the requirement compiler an LLM call. §35.2 lists hallucinated requirements as a project-killer with mitigations that are *review*, not *removal*. §20 budgets test time for "LLM malformed JSON." That is an API key, a network call, latency and nondeterminism sitting between the judge and the result. §23's "paste brief text manually" fallback is an admission the front of the pipeline is fragile.
2. **The demo dataset is builder-authored, which hollows out usefulness.** §20 says create the brief and three videos "with controlled errors"; §25 locks the expected output to `2 FAIL / 1 WARN / 4 PASS`. The builder writes the brief, records a video deliberately saying "seventy" instead of "seventy-three," then demonstrates the tool notices. *Of course it found the error you planted.* Cutcheck's demo has an outside party in it — a real audience whose behavior neither builder nor tool controls.
3. **Stripped of framing, the core is string matching over a transcript.** Four of six rule types reduce to substring/fuzzy match, one to number normalization, one to `ffprobe`. Whisper + difflib + a regex table. It caps the ceiling: the tool can never tell the creator anything the brief did not already state. It verifies a checklist someone else wrote; Cutcheck *authors* the checklist from evidence.

### Conceded weakness

**The data.** The entire differentiating claim is real retention exports, and the builder does not have them. Not public, not scrapeable, not purchasable — behind the channel owner's Studio login. Cold outreach with a stranger's willingness on the critical path.

It compounds. Even with CSVs in hand, correlations may come back weak — every rule under `support >= 3`, or lift near 1.0. §21 handles that honorably, but it is a catastrophic demo: the moment described above requires a card that says `2.6x`. If the honest number is `1.1x`, there is no demo, only a correctly-behaving tool with nothing to show.

> *"'Someone must say yes in the next several hours' is an honest single point of failure, and I will not dress it as anything else."*

### Feasibility

**70%** for a complete, demoable, non-faked loop. But *"loop runs end to end on verified real creator exports with at least one rule above `support >= 3` and lift ≥ 2.0"* — the version that actually produces the demo moment — is priced at **45%**.

---

# Round 2 — The case for SponsorLint

### Rubric, line by line

**Functionality (30%).** Every component either works off the shelf or is a string comparison. Critically, **the inputs are manufacturable**: the builder writes the brief and records the read. This is the only project where creating the demo dataset is a *writing* task rather than an *acquisition* task. The §19 vertical slice is achievable in the first 2 hours, so the project has something submittable by hour 2 and every hour after is additive rather than load-bearing — the single most valuable property a 36-hour project can have.

**Real-world usefulness (30%).** A sponsor brief is a contract with enumerated deliverables; failing one triggers a re-cut, delayed payment, or a lost renewal. *"You said 70%, the brief says 73%, at 00:43"* is actionable in one step.

The sharpest distinction between the two projects: SponsorLint's finding is a **defect against a specification the user already agreed to** — ground truth exists, sits in the PDF, and the tool is either right or wrong about it. Cutcheck's is a **statistical association from n=3–10** which its own documentation concedes yields hypotheses, not proof. *"Would a creator act on this?"* gets an unambiguous yes from one and a "maybe, if they believe the correlation" from the other.

**Creativity (20%).** Sponsor compliance is not usually thought of as a lintable problem. `sponsor-spec.json` is the memorable artifact — the brief becomes reusable, re-runnable against v2, v3, v4. In a field whose modal submission is a generator, Cutcheck is an *analyzer* (rarer) and SponsorLint is a *verifier against an external contract* (rarer still) — and the only one of the three that says **no** to the creator.

**Technical execution (20%).** §8 is the strongest asset: the LLM compiles, deterministic validators judge. That pre-empts the standard "this is a wrapper" objection. The `MANUAL REVIEW` escape hatch for visual requirements reads as maturity — a tool that refuses to fake a verdict is demonstrating judgment, which is what the 20% measures.

### The demo moment

Brief PDF visible, showing `73%` and `DO NOT SAY: "completely anonymous"`. The report renders:

```
❌ WRONG VALUE   Expected: 73%   Detected: "up to 70%"   00:43
   "You can get up to seventy percent off."
```

Rerun on v3: `✓ SPONSOR READY — 7/7`.

**Why it lands:** a falsifiable claim the judge verifies with their own eyes and ears. No trust required, no statistics to accept, no *"take my word that this retention curve is real."* The spoken-numeral catch is the detail that proves the pipeline is genuinely running — a fake demo would not bother normalizing spoken numerals. And red-to-green is a narrative arc; most projects show one static output, this shows a verdict *flipping* because the input actually changed.

### Attack on Cutcheck

1. **Phase 0 is an acquisition gate the builder does not control, and it is unmet.** Every other risk is an engineering risk the builder can grind through. This one is social. The fallback forbids presenting synthetic data as real, so the failure branch is: build the whole machine, then tell a judge the numbers are synthetic. That guts both 30% categories at once.
2. **The central claim is a statistical result from a sample too small to persuade.** A quantitative judge asks what lift 2.6 means on n=8 with no confidence interval, and the bible has already conceded the answer. Worse, §21's failure mode is real: if no rule clears minimum support, the correct behavior is "not enough evidence" — a demo with no output. SponsorLint has no equivalent empty state.
3. **Compute cost per iteration is high and the loop is slow.** Three CV/audio detectors, each needing independent tuning, across 3–10 full-length videos. §21 anticipates having to *delete one* — feature attrition is planned for, which tells you the schedule is tight.

### Conceded weakness

**The judge concludes it is Whisper plus string matching, and the LLM step is decorative.** Four of six rule types reduce to normalized substring search. Good for Functionality — it is why it ships — but directly adverse under Technical execution.

The §26 rebuttal is only as good as the messiness of the brief it runs against, and the brief is one the builder wrote. **If the demo brief is a tidy bulleted list, the compiler looks like it parsed a list**, and the architectural argument collapses into "I asked an LLM to read a formatted document."

Mitigation, and the highest-leverage two hours available: write the brief as *realistic prose* — legalese with the discount buried mid-sentence, prohibitions phrased as negations, duration as *"no shorter than a minute and no longer than a minute and a half."*

### Feasibility

**~85%.** No third party, no API approval, no acquisition. Degrades gracefully: 36 hours a polished web app, 20 hours a CLI with six rules, 8 hours a working script with three rules — and a working script counts. No cliff-edge failure state.

---

# Round 3 — The rulings

### (a) "Of course it found the error you planted" — **OVERRULED, and it boomerangs**

The charge is real but misidentifies where the planting matters.

> In SponsorLint, the builder authors the **test input**. In Cutcheck-as-it-will-actually-ship, the builder authors the **ground truth**.

Phase 0 is unmet, so the retention curves will be synthetic. The learning engine then mines cliffs the builder placed, in videos the builder chose, and emits rules whose entire claim to authority is *"this came from your real audience."* Strip the real audience and the product is a tautology generator.

The decisive asymmetry is **live falsifiability**. A judge can break SponsorLint on the spot — *"add a rule that I have to say the word banana."* Thirty seconds, real result, objection dead. There is no equivalent move against Cutcheck: a judge cannot produce their own channel's retention CSVs and matching video files on demand.

### (b) Phase 0 is an unmet blocking gate — **SUSTAINED, and worse than argued**

Not merely "a stranger's inbox." A four-way conjunction:

1. A creator must agree, within hours, on a weekend, for nothing.
2. They must perform 5–10 separate manual Studio exports — retention export is per-video and fiddly.
3. **They must also supply the video files.** Every discussion of this risk talks about CSVs. CSVs are the easy half; eight source videos is a multi-gigabyte ask.
4. Their channel must be large enough that the curves are not noise — so the *cooperative-creator* set and the *statistically-usable-creator* set are different, and you need the intersection.

Probability of clean real data in hand by hour 8: **under 20%**. The acquisition is serial; nothing downstream validates until it lands.

### (c) Small-n statistics — **LIABILITY as planned; ASSET only in the version that was deleted**

The judge found `STRATEGY.md` in the repo — an earlier, different Cutcheck plan carrying a third verb, `cutcheck backtest`, producing a real leave-one-out precision number.

> The word "backtest" appears six times in `STRATEGY.md`. It appears **zero** times in the Execution Bible's 1,873 lines.

The de-scoping pass deleted the single best answer to Cutcheck's single worst objection, leaving only the disclaimer. **A disclaimer is not a defense; it is a pre-emptive concession.**

Three surviving soft spots:

- **Threshold fitting.** §4.3 tunes the cliff threshold on the dataset that §8 then reports lift from. Fitting and reporting on identical data. The correction is a held-out video — which is `backtest`, which is gone.
- **`n` is ambiguous.** The Bible's `"support": 8` means eight *feature events*; `STRATEGY.md` prints `(n=9)` right after "your last 9 videos," implying nine *videos*. A judge asking "n=8 what?" has found the seam.
- **Baseline construction is unspecified.** `baseline_rate: 0.24` appears with no defined reference population — and it is the number the entire lift claim divides by.

### (d) "Whisper + string matching" — **SUSTAINED on facts, DISMISSED on consequence**

Yes: pypdf → one LLM call → faster-whisper → normalization → `ffprobe`. Nothing there is hard.

But Technical execution is 20%, the joint-lowest weight, and on hackathon rubrics that line means *"is this built well,"* not *"was this hard."* Clean architectural separation, Pydantic at the boundary, per-rule unit tests, explicit `MANUAL REVIEW`, non-silent failures — that is what scores. **A well-executed simple system beats a half-finished hard one every time.** Cost: about one point.

### (e) "It might produce no output" — **not fatal as a demo risk; fatal as a schedule risk**

Two null states, treated as equivalent in the plan. They are not.

The harmless one is a new video producing no warnings — mitigable by choosing the demo video.

The dangerous one is upstream: **no rule clears `support >= 3`**. Then View 2 is empty, View 3 has nothing to apply, and the product ceases to exist. You discover this at Phase 3, hours 14–20, with one recovery available: synthesize data that produces rules. Which is the honesty collapse from ruling (a), arrived at by a different road, at the worst possible hour.

> SponsorLint's pipeline is a **total function** — a brief always compiles to rules, rules always evaluate to a status, the report is never empty. Cutcheck's is **partial**: a legitimate input can yield the empty set. For a 36-hour build this is worth more than any feature either project could add.

### (f) Raised by the judge, unprompted

`STRATEGY.md`'s own field forecast lists *"Analytics dashboard + LLM summary — ~10%"* among the discounted clusters. Cutcheck sits adjacent to that cluster, and a tired judge on submission thirty-one pattern-matches in five seconds, before the differentiation gets a hearing. SponsorLint is adjacent to nothing on that list.

**The category-separation argument invented for Cutcheck turns out to favor SponsorLint.**

---

# Scorecard

| Criterion | Weight | Cutcheck | SponsorLint |
|---|---:|---:|---:|
| Functionality | 30% | 6 | **8** |
| Real-world usefulness | 30% | 7 | **8** |
| Creativity | 20% | **8** | 7 |
| Technical execution | 20% | 6 | **7** |
| **Weighted total** | | **6.7** | **7.6** |

**Functionality — 6 vs 8, the widest gap and the one that decides it.** Cutcheck's 6 is an expectation across three scenarios: ~20% complete-with-real-data (~8.5), ~55% complete-but-synthetic (~6.5, the loop runs while the claim hollows out), ~25% incomplete because the front of the pipeline was blocked for the first third of the clock (~3). Note what the 6 conceals: **Cutcheck's realistic best case beats SponsorLint's, and its realistic worst case is a non-submission.**

**Usefulness — 7 vs 8, the line where Cutcheck could have won.** Not scored down for ambition — scored down for *efficacy doubt*. The action it produces ("add a cut at 00:18") is advice the creator already had, now with a statistic attached, and the mechanism by which a rule mined from video A transfers to video B is shaky. A judge who is themselves a creator will think: *my cliffs are about topic and pacing and whether I delivered what the title promised, not about frame-difference scores.* That objection has no good answer.

**Creativity — 8 vs 7, Cutcheck wins plainly.** But the delivered version is not the imagined one. The Execution Bible bans promise–payoff analysis, beat labelling, semantic topic-shift detection, embeddings, and EDL export — every element `STRATEGY.md` marked *"this is the idea."* What survives is silence + low-motion + cut-frequency correlated against drop-offs. **8 for the concept; the artifact is closer to 7.**

---

# Verdict

> **Build SponsorLint. Confidence: high — around 80%.**
>
> This is not close, and it is not close for a reason that has nothing to do with which idea is better. **Cutcheck is the better idea.** Under a 72-hour clock with retention exports already on disk, I would pick Cutcheck and expect it to win. That is not the situation.

Where the remaining 20% sits: if a judge happens to be a data person who lights up at the retention loop, the concept could carry a rougher build past a cleaner one. Creativity is 20% and creativity is taste. **You cannot plan around a judge's taste. You can plan around a working pipeline.**

---

# Round 4 — Revision after reading both briefs

No ruling reversed, no score moved. The verdict *firmed up*: the Cutcheck advocate's own concession ("an honest single point of failure") and its 45% figure for the strong version landed in the same territory as the judge's estimate.

### One real upgrade

The realistic-prose brief beats what the judge originally wrote. Build it **into the review screen**: source paragraph on the left, extracted `sponsor-spec.json` on the right. No regex pulls `min_seconds: 60` out of *"no shorter than a minute and no longer than a minute and a half"* — so the compiler is visibly doing work, and the §8 architecture argument stops being a talking point and becomes a demonstration. It costs nothing extra: **you were writing the brief anyway, you just write it worse on purpose.**

### Overstatements caught, by severity

| # | Claim | Ruling |
|---|---|---|
| 1 | Cutcheck "degrades gracefully — reaching Phase 4 and stopping is still submittable" | **The largest misrepresentation in either brief.** Phases 1–3 produce no user-facing output. A Cutcheck that halts at Phase 2 is a script that detects silence in an MP4. First product value appears at Phase 4, hours 14–20. **Cutcheck is cliff-edged, not layered.** SponsorLint's version of the claim is the true one. |
| 2 | "A careful editor with Ctrl-F does most of this in ten minutes" | Understates the manual baseline. Ctrl-F needs a transcript you don't have, cannot match "seventy percent" against 73%, cannot find a phrase you forgot to look for, and the cost is *per revision cycle*. |
| 3 | SponsorLint: "no step can fail in a way the builder cannot diagnose in 20 minutes" | False, and its own §5 concedes the counterexample — Whisper garbling the planted numeral silently eats the demo centerpiece. |
| 4 | "Every threshold tune requires re-deriving features across the corpus" | Overstated. Features extract once and cache; only changing a *detector's* parameters forces re-extraction. Right about the first pass, wrong about the loop. |
| 5 | "Sponsor readiness: 57% is a weighted count of the builder's own rules" | Attacks a strawman the bible pre-emptively disowned — §13 already says the binary state matters more. |
| 6 | "hypotheses, not causal proof" cited to §20 | Substance accurate, citation wrong. Trivial. |

### One thing both advocates got wrong together

Both argued as though there is a live demo table. **The event is repo + README + optional video.** There may be no room, no laptop, no judge to interrupt.

This *strengthens* the falsifiability ruling rather than weakening it — an async judge who clones the repo can edit a rule and re-run at their own pace, which is better proof than a scripted stage moment. But it means the **zero-key clone-and-run path and the README are worth more than either brief credited**, and any effort budgeted for live-demo theater should move there.

---

# What would actually win

**On "a project that cannot lose against anyone": not achievable, and chasing it will cost you the win.** Judging is stochastic. 20% of the rubric is explicitly taste. You cannot control the field, demo order, judge fatigue, or whether anyone opens your README.

The correct target is **un-dismissable** — make it so no judge can complete the sentence *"this doesn't work"* or *"I've seen this one."* Un-dismissable projects do not always win, but they never place badly, and in a field where most submissions are dismissible in ten seconds, that is most of the distance.

Ordered by leverage:

1. **Steal `backtest`.** 90 minutes. `sponsorlint eval` over ~24 pure-text fixtures — no video, no Whisper, runs in a second. Load it with hard negatives: `70%` vs `73%`, `"threat protection"` vs the required full name, bare `anonymous` vs `"completely anonymous"`, a URL spoken as *"dot com slash."* Tune for **zero false positives and say so**: a false FAIL wastes an afternoon, a false PASS ships a broken read to the brand. A designed tradeoff, backed by a number, in the README **above** the feature list.
2. **Promote the brief-review screen to core, and make it editable.** Show the compiled spec with each rule quoting its source line; let the judge add a rule and re-run. Kills three objections at once — hallucination, planted errors, and *"can you trust an LLM to read a contract"* (you don't have to; the correction **is** the product). Build the prose-vs-spec split screen here.
3. **Zero-key, sub-60s clone-to-output.** Commit the compiled spec and cached transcript; `sponsorlint demo` runs the **verifier live** against them. `--compile` / `--transcribe` re-run the expensive steps. An API-key wall loses the judge in thirty seconds; a 140MB model download loses them in sixty. Both are on the default path right now. *Caching is not cheating; fake output is.*
4. **Over-invest in spoken-numeral normalization.** It is the entire "this is engineering" moment. Word forms, hyphenated compounds, `$20` vs "twenty dollars", promo codes spelled aloud (`"H-A-R-S-H two zero"` → `HARSH20`), and **both output modes Whisper produces** — it emits digits sometimes and words other times. One unit test per case, feeding the eval harness.
5. **Add the free domain-knowledge check: disclosure *placement*.** `⚠ Detected at 03:47 — disclosure this late is unlikely to be clear and conspicuous.` Ten minutes on a timestamp you already compute, and it is the line that reads as insider knowledge.
6. **Protect the V1→V2→V3 arc, cheaply.** Don't record three videos — record one 75-second take with all errors, then re-record only the offending sentences and splice. Render the arc as a side-by-side report diff. The climbing readiness score is your README GIF.
7. **Rename the brand, in the first ten minutes.** The bible uses `"Threat Protection Pro"` and `nordvpn.com/alex` — NordVPN's actual product name and URL format, inside a fabricated brief with fabricated violations. Use `Aegis VPN` / `aegisvpn.com/alex`.
8. **Take Cutcheck's positioning wholesale.** First line of the README: *"Every other tool here generates content. This one checks it."* And since the video is optional, the README is the primary judging surface while most of the field still pours hours into video and ships three lines of markdown.
9. **Kill list.** No Next.js. No database. No auth, no Docker, no deployment. No visual/OCR rules — easyocr pulls ~2GB of torch on Windows at hour 20. Do not build all six rule types before one runs end to end. **Do not fold any part of Cutcheck in as a second tab.**
10. **If retention data arrives at hour 6, do not switch.** Bank it. Cutcheck from a cold start in 30 hours, with data landing mid-build and no validation harness, is a worse bet than a finished SponsorLint. It is a genuinely good September project — done properly, with `backtest`, and with the promise–payoff idea the Execution Bible had to cut.

---

# The first three hours

One correction to the SponsorLint bible's own Hour 0–2: it front-loads the upload route and PDF extraction. Both are worthless until the verifier works, and PDF parsing is twenty minutes of zero-risk work at any point. **Hand-write the spec JSON and go straight at transcript → check.**

### 0:00–0:15 — Commit and clear the decks
- Rename the brand. Archive `STRATEGY.md` out of repo root — it must not be the first thing a judge sees.
- Commit a README with three things only: title, one-sentence pitch, input/output block.
- Send two creator DMs asking for retention exports. Sixty seconds, free lottery ticket for September. Then close the tab.

### 0:15–1:00 — Make the demo assets, out loud, before any code
Counterintuitive but correct: the assets gate every downstream test, need no code, and need your voice at full energy — which you will not have at hour 30. Coding agents scaffold in parallel.

- Write `samples/brief.md` — seven requirements, **fictional brand**, **realistic prose not a bulleted list**. Export to PDF so it looks real on camera.
- Write the 75-second script with errors baked in at known timestamps: *"up to seventy percent"*, the omitted product name, the prohibited claim near 0:31.
- **Then the check nobody thinks of:** transcribe just those three error sentences with `base.en` *before* committing to the script. If Whisper garbles "seventy percent," change the script to a mistake it *can* hear. **Your entire centerpiece rests on one transcription — verify it in hour one, not hour twenty-six.**
- Record V1. Phone mic is fine. Enunciate the numbers.

*In parallel, hand the agents:* repo skeleton, six rule-checker stubs each with one failing unit test, the `ffprobe` wrapper, Pydantic schemas.

### 1:00–2:10 — The vertical slice, ugly, end to end
```bash
pip install faster-whisper pypdf rapidfuzz pydantic fastapi uvicorn python-multipart
```
- Transcribe V1 → **write `samples/transcript.v1.json` to disk immediately.** That file is your fixture for the next thirty hours. Never run Whisper again during development.
- Hand-write `samples/spec.json`. Do not build the LLM compiler yet.
- Implement exactly one check — MUST_SAY with normalization — printing status, timestamp, evidence line.

> **Gate 2:10** — one command prints one real verdict from one real video. If this hasn't happened, strip the LLM compiler to a single prompt with no retry logic and move on.

### 2:10–3:00 — The other five, against the cached transcript
- MUST_NOT_SAY, EXACT_VALUE, MUST_DISCLOSE, DURATION, URL_OR_CTA. Give **EXACT_VALUE half the block** — it is the hard one and the one that matters.
- Write each rule's unit test as you write the rule. Five extra minutes each, and it **is** the eval harness from #1 — the measured number comes nearly free later.

> **Gate 3:00** — all six rule types produce the expected `2 FAIL / 1 WARN / 4 PASS` on V1.

At 3:00 the project exists. Everything after is upside: the LLM compiler, the editable review screen, the UI, the eval number, the README. If the clock goes badly wrong from here, you already have a working script — **and the event says explicitly that a working script counts.**
