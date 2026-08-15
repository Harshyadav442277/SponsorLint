# Cutcheck

**A linter for video edits, compiled from your own audience-retention data.** Point it at an unpublished cut and it tells you which seconds will lose viewers — and why — before you upload.

```
$ cutcheck lint raw/ep-42.mp4    →  3 problems (1 error, 2 warnings)
```

> Hackathon strategy brief. Derived from the posted challenge text and the Devpost lineage of
> *YouTube Automation Hackathon: Code the Channel of Tomorrow*, whose listing now returns 410.
> Sponsor list, judge panel and weighted rubric were not retrievable — re-tune against those
> if you can find the live page.

---

## Contents

- [The thesis](#the-thesis)
- [What the brief is actually telling you](#what-the-brief-is-actually-telling-you)
- [The field you're up against](#the-field-youre-up-against)
- [The build: Cutcheck](#the-build-cutcheck)
- [How it works](#how-it-works)
- [Why this wins](#why-this-wins)
- [The 24 hours](#the-24-hours)
- [The README, in judging order](#the-readme-in-judging-order)
- [Questions a judge will ask](#questions-a-judge-will-ask)
- [Honest risks](#honest-risks)
- [Before the clock starts](#before-the-clock-starts)

---

## The thesis

**Every other project at this hackathon will automate _making_ content. This one automates _learning from_ it.**

In a field of fifty generators, the one diagnostic tool isn't incrementally better — it's in a different category, which is the only reliable way to be memorable to a judge on submission number thirty-one.

YouTube hands every creator this curve and no explanation. Cutcheck supplies the explanation, then compiles it into rules that run against your next video.

```
 100% ┤●
      │ ╲
      │  ╲──╮
  75% ┤     ╰────╮
      │          ╰───╮
      │              ▼ ◀── CLIFF   0:47   −18%   sponsor read begins pre-payoff
  50% ┤              ╰──────╮
      │                     ╰────────╮
      │                              ▼ ◀── CLIFF   6:12   −11%   4.1s dead air, no cut
  25% ┤                              ╰──────────────────
      │
   0% ┼──────┬──────┬──────┬──────┬──────┬──────┬──────┬───
     0:00   1:30   3:00   4:30   6:00   7:30   9:00  10:30
```

<sub>Illustrative — shape and annotations are representative, not to scale.</sub>

---

## What the brief is actually telling you

The listing is near-verbatim from Devpost's *YouTube Automation Hackathon* (that page now 410s, so this is a re-run or a broadened variant). Origin matters: the event is **YouTube-shaped underneath the "social media" label**. Six things in the copy are load-bearing.

| The line | What it actually means |
|---|---|
| *"Demo video (**Optional**)"* | The single most exploitable line in the brief. When the video is optional, the **README becomes the primary judging surface** — and most teams will still dump their effort into the video and ship a three-line README. Near-free differentiation. |
| *"thumbnail generation, metadata and SEO, upload scheduling, analytics reporting, comment moderation, clip generation"* | Not a menu of good ideas — a **map of the saturated zone**. Organizers write these to lower the barrier to entry, and the effect is that most of the field clusters inside them. Being inside the list is necessary for compliance; being *the obvious build* inside it is fatal. |
| *"pick a problem you've actually run into as a creator **or editor**"* | "Or editor" is doing quiet work. Nearly everyone builds for the creator-as-poster. Almost nobody builds for the person in the timeline at 2am. Anything that speaks the editor's language — timecode, cut lists, EDL/XML exports — reads as insider knowledge instantly. |
| *"Actually run and produce a real result — a UI is a bonus, but a working script counts"* | Said twice, in two sections. The rubric is anti-vaporware to an unusual degree. Optimize for **a judge cloning your repo and getting output in under a minute**, not for a pretty React shell over a stubbed backend. |
| *"less time on repetitive creator busywork and more time actually making content"* | The stated north star is **time reclaimed**, not AI capability demonstrated. Any claim you make should be denominated in hours or in a measurable outcome, never in model names. |
| *"Brainstorm your idea early… Don't hesitate to ask for help."* | Pre-event engagement is invited, and organizers remember the teams that showed up in the channel. It also gives you cover to do the one thing that builds a real moat here: **acquire retention data from actual creators before the clock starts.** |

---

## The field you're up against

Forecast of the submission distribution, based on how this brief steers people:

| Likely submission | Share | Why judges discount it |
|---|---:|---|
| **AI thumbnail generator**<br><sub>prompt → image model → 1280×720</sub> | ~30% | Output is generically "AI-looking." Judges know thumbnails are won by face, contrast and A/B testing — not by generation. Indistinguishable from ten neighbours. |
| **Long video → auto-shorts**<br><sub>Whisper + LLM timestamps + ffmpeg</sub> | ~25% | Opus Clip and Vizard already do this commercially. The hackathon version is a visibly worse copy of a product the judges have used. |
| **Multi-platform scheduler** | ~15% | Dies on API access. Almost always demoed against mocks, which collides head-on with *"actually run and produce a real result."* |
| **Comment moderation / auto-reply bot** | ~12% | Easy to demo, shallow underneath, and raises an authenticity objection the team usually hasn't thought through. |
| **Analytics dashboard + LLM summary** | ~10% | Charts you already have in Studio, restated. Describes the past; changes nothing about the next video. |
| **Genuinely novel** | ~8% | This is the bracket worth competing in. It is small. |

> ### Runner-up, and why it lost
>
> The strongest alternative was **messy client feedback → applied rough cut**: paste a Google Doc or Discord thread of timestamped notes, get back an FCPXML you open in Resolve with the cuts already made. Real editor pain, genuinely unsolved for small teams, great "insider" signal.
>
> It lost on **demo surface** — the payoff only lands inside an NLE the judge doesn't have open, and the novelty is plumbing rather than insight. Keep it as the fallback if data acquisition fails.

---

## The build: Cutcheck

A CLI with three verbs. The whole product is the loop between them.

### `cutcheck learn ./catalog`

Ingests your published videos plus their retention curves. Extracts a per-second feature timeline for each, finds the cliffs, and mines *channel-specific* rules with support and lift. Writes `rules.yaml`.

### `cutcheck lint cut.mp4`

Runs those rules against an unpublished edit. Emits lint-style diagnostics at timecodes, a predicted retention curve, an HTML report, and an EDL of suggested cuts.

### `cutcheck backtest`

Leave-one-out across your catalog: hold back a video, mine rules from the rest, check whether flagged timestamps land on real cliffs. Reports precision and recall.

**The third verb is the differentiator.** Almost no hackathon project validates its own claims. Shipping a number — even a mediocre one, honestly reported — moves you from "plausible demo" to "engineering."

### What a judge sees in the terminal

```console
$ cutcheck lint raw/ep-42.mp4

raw/ep-42.mp4:0:11  error    intro-before-first-cut
    19s elapsed before the first scene change. Your last 9 videos lost
    a mean 11.4% by 0:15 when this exceeded 6s.  (n=9, lift 2.7x)

raw/ep-42.mp4:2:38  warning  sponsor-before-payoff
    Sponsor read starts 38s before the hook's promise is fulfilled.
    Post-payoff sponsors cost you 3.1%; pre-payoff cost 9.8%.  (n=6)

raw/ep-42.mp4:5:02  warning  dead-air
    4.1s of silence with no scene change. Correlated with a cliff in
    7 of 11 past occurrences.  (n=11, lift 2.1x)

3 problems (1 error, 2 warnings)
predicted 30s retention  61%  · channel median 68%

→ .cutcheck/ep-42.html   annotated report
→ ep-42.edl              suggested cuts, opens in Resolve / Premiere
```

Every diagnostic carries its own evidence — `n` and lift, from the creator's own catalog. **That single formatting decision is what separates this from a chatbot giving advice.**

---

## How it works

### Feature timeline (per second, per video)

| Feature | How | Novelty |
|---|---|---|
| Word-level transcript | `yt-dlp` auto-captions, or `faster-whisper` locally | table stakes |
| Speaking rate (rolling WPM) | Derived from word timings | table stakes |
| Silence gaps | ffmpeg `silencedetect` | table stakes |
| Shot changes | PySceneDetect content detector | table stakes |
| Audio energy variance | RMS over 1s windows | table stakes |
| **Beat labels** — hook / branding / sponsor / tangent / payoff / recap / CTA | LLM segments the transcript into a labelled structure | **strong** |
| **Promise–payoff distance** — seconds between the hook stating a promise and the video first delivering on it | LLM extracts the promise, then locates its first fulfilment | **this is the idea** |
| **Unmarked topic shift** — semantic change with no visual cut to signal it | Embedding distance across transcript windows, cross-referenced against scene changes | **this is the idea** |

### Cliff detection and attribution

- Normalise retention `r(t)`, take the drop rate `d(t) = −Δr/Δt`, z-score it *within* each video so length and channel size cancel out.
- Cliffs are local maxima of `d(t)` above threshold. For each cliff, take the feature window `[t−8s, t+2s]`.
- Attribution is deliberately **interpretable, not accurate**: conditional lift tables across the catalog, reported with `n`. At ten videos, a gradient-boosted model with SHAP is statistical theatre — a lift table is honest and a judge can audit it in their head.
- The LLM writes the human sentence, but is constrained to cite only the computed evidence. **It explains; it does not decide.**

### The compiled artifact

```yaml
# rules.yaml — mined from 11 videos on @yourchannel
- id: intro-before-first-cut
  when: seconds_until_first_scene_change > 6
  penalty: -11.4%   # mean retention at 0:15 vs. baseline
  support: {n: 9, lift: 2.7}
  severity: error

- id: sponsor-before-payoff
  when: beat == "sponsor" and t < promise_payoff_t
  penalty: -9.8%
  support: {n: 6, lift: 3.1}
  severity: warning
```

Human-readable, hand-editable, diffable. A creator can open it, disagree with a rule, and delete it. **That property alone makes the tool feel like a tool rather than an oracle.**

---

## Why this wins

**1. Category separation.** It is squarely inside "analytics reporting," so no judge can rule it out of scope — but it occupies a slot nobody else is standing in. Compliant and uncontested at the same time is the ideal position.

**2. It survives "isn't this just a prompt?"** — the silent question behind every AI hackathon submission. Cutcheck's answer is structural: its rules come from statistical aggregation over *your private retention data*. No general model can know your audience tolerates a 40-second sponsor read but bails on 8 seconds of silence.

**3. It validates itself.** `backtest` produces a falsifiable number. Reporting *"precision 0.63 on held-out cliffs, n=11 — small sample, treat rules as hypotheses"* beats any confident claim. Judges have seen a hundred overclaims and zero honest error bars.

**4. The metaphor lands in three seconds.** "CI for your video edit." Your judges are developers. Lint output at timecodes, a `rules.yaml`, a failing check — they understand the entire product before you finish the sentence.

**5. The data is the moat.** Competitors can copy the idea in an hour. They cannot copy eleven real retention exports from creators who agreed to share them. This is the one advantage that is genuinely hard to replicate mid-event.

**6. It reclaims real time.** Straight at the stated north star. The alternative to Cutcheck is a creator manually scrubbing a retention graph against their own timeline for an hour per video, and mostly guessing.

---

## The 24 hours

Each block ends in a runnable state. If you fall behind, cut from the bottom of the block, **never from the gate**.

### `00:00` — Skeleton, end to end, ugly

CLI scaffold. Read one video + one retention CSV. ffmpeg scene detection and silence only. Hardcode a single rule. Print one diagnostic.

> **Gate:** one real warning printed from real data

### `03:00` — Features and cliffs

Captions via `yt-dlp` (skip Whisper unless you must — it costs you an hour of GPU time you don't have). WPM, silence, scene density. Cliff detection on `d(t)`. HTML report with the curve and markers.

> **Gate:** the hero chart renders from your own data

### `09:00` — Beat labelling and attribution

LLM pass for beat labels and promise–payoff distance. Per-cliff attribution with evidence strings. This is where the project stops looking like a chart and starts looking like a diagnosis.

> **Gate:** a cliff explained in a sentence a creator would believe

### `14:00` — Rule mining and lint mode

Lift tables across the catalog → `rules.yaml`. `lint` evaluates rules against a held-out video. Lint-formatted terminal output.

> **Gate:** `cutcheck lint` works on a video the miner never saw

### `18:00` — Backtest and the honest number

Leave-one-out loop. Precision/recall against real cliffs. Write the number into the README *whatever it is*.

> **Gate:** a validation number exists and is not hidden

### `20:00` — The judge's first 60 seconds

Sample pack committed. `cutcheck demo` runs with zero API keys. README written. Terminal GIF recorded. **This block is worth more than any feature you could build instead — protect it.**

> **Gate:** clone → one command → output, under a minute, no keys

### `22:00` — Stretch, in strict order

1. EDL / FCPXML export of suggested cuts (OpenTimelineIO) — the editor signal
2. GitHub Action that fails a PR on a lint error — the "they took it all the way" flourish
3. Demo video, if the README is already excellent

> **Never cut:** offline demo · README · backtest number

---

## The README, in judging order

The video is optional, so this is the deliverable. Structure it the way a judge reads it, not the way you built it.

1. **One sentence and one GIF**, above everything. The GIF is the terminal output scrolling — six seconds, no narration.
2. **The 60-second quickstart** — `git clone`, `pip install -e .`, `cutcheck demo`. Zero keys. State the zero-keys fact explicitly; it's a promise most repos break.
3. **The pain, in one paragraph**, told from a real creator's mouth. Name them if they gave you the data.
4. **How it works** — the pipeline diagram and the `rules.yaml` sample. Show the artifact, not the architecture-astronaut version.
5. **Does it actually work?** — the backtest number, the sample size, and the honest caveat. Put this *before* the feature list; it is your strongest paragraph and most repos bury it.
6. **Limitations**, written by you, in plain terms. Correlation is not causation. Small `n`. Say it before a judge gets to say it.
7. **Real setup for real data** — the OAuth path and the Studio CSV path — last, because it's the part that can fail on someone else's machine.

---

## Questions a judge will ask

<details>
<summary><b>Couldn't I just ask ChatGPT what makes videos lose viewers?</b></summary>

You'd get generic best practices. Cutcheck tells you that *your* audience abandons at eight seconds of silence but sits through a forty-second sponsor read, because it measured that across your last eleven videos. Every rule ships with its sample size and lift. Delete the ones you disagree with — it's a YAML file.
</details>

<details>
<summary><b>Correlation isn't causation. How do you know the sponsor read caused the drop?</b></summary>

It doesn't, and the tool never says it does. It generates ranked, evidence-carrying hypotheses and suggests the A/B that would settle each one. That framing is deliberate — a tool that told you it had found causation from eleven observations would be lying to you.
</details>

<details>
<summary><b>Eleven videos is not a dataset.</b></summary>

Correct, and it's why every diagnostic prints `n` and every rule has a confidence tier. The backtest is exactly the measurement of how much you should trust rules mined from small `n`. It gets sharply better at forty videos, and the architecture doesn't change.
</details>

<details>
<summary><b>Doesn't YouTube Studio already show me this?</b></summary>

Studio shows the curve. It does not tell you what was on screen at the cliff, does not aggregate patterns across your catalog, and cannot check an unpublished cut. **Studio is the thermometer. This is the diagnosis and the prescription.**
</details>

<details>
<summary><b>Where did the retention data come from?</b></summary>

Real exports from *[creator]*, shared with permission, plus a synthetic set for reproducible tests — clearly labelled as synthetic in the repo. Never blur that line; a judge who catches it discounts everything else you said.
</details>

<details>
<summary><b>Does this work for TikTok and Reels?</b></summary>

The ingest takes any normalised retention series, so yes in principle — both platforms expose retention graphs. YouTube is the deep integration because it has an API. One line in the README covers the breadth without costing you a minute of build time.
</details>

---

## Honest risks

| Risk | Severity | Mitigation |
|---|---|---|
| **No real retention data** — the whole project rests on it | `critical` | Solve this *before* the event. Three paths in parallel: your own channel, two small creators asked in the pre-event channel, and YouTube Studio CSV export as the no-OAuth fallback. |
| **OAuth eats four hours** | `critical` | Do not put OAuth on the critical path. CSV ingest first; the API path is a stretch goal that never blocks the demo. |
| **Small-`n` statistics look flimsy** | `moderate` | Turn it into a strength by naming it first, everywhere: in output, in the README, in the pitch. Confidence tiers on rules. |
| **Whisper transcription burns hours** | `moderate` | Default to YouTube's own caption track via `yt-dlp`. Whisper only for unpublished cuts, on the smallest model that works. |
| **Scope creep into a web UI** | `moderate` | The brief explicitly says a script counts. A single self-contained HTML report file is the entire UI budget. |
| **Backtest number comes out bad** | `low` | Publish it anyway with the caveat. A mediocre measured number outscores an unmeasured claim with judges who have any research background. |

---

## Before the clock starts

Ordered by how badly the project suffers without them.

1. **Get retention exports from two or three real creators.** Post in the pre-event channel — the brief invites exactly this. Ask for the Studio audience-retention export plus the video URL, for their last ten videos. This is the moat and it takes days, not hours.
2. **Verify the export path yourself** on any channel you control, including a test one. Confirm the file format and column names before the event, not at hour three.
3. **Pre-build the boring plumbing** — ffmpeg wrappers, PySceneDetect, caption fetch — as a separate throwaway repo you're allowed to reference. Check the event's rules on pre-existing code first and follow them exactly.
4. **Write the README's first paragraph now**, before any code. If you can't make the pain vivid in four sentences, the framing is still wrong and it's cheap to fix today.
5. **Find the actual event page** and check for sponsor APIs and a weighted rubric. If a sponsor's API can carry any part of this pipeline, use it — "use of platform" is a scored line item on most rubrics of this shape.
