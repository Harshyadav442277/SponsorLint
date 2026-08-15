# Design — SponsorLint

The interface should feel like a **developer linter**, not an AI dashboard.

Reference points: ESLint output · GitHub checks · IDE diagnostics · CI warnings · a code review.

**Not** reference points: chat bubbles · gradient heroes · glowing orbs · "AI-powered" badges · confetti.

---

# 1. Principles

**Verdict first, detail second.** The three-state banner is the largest element on the report screen. Everything else supports it.

**Semantic color is not decoration.** `FAIL` / `WARN` / `PASS` / `MANUAL REVIEW` carry meaning. The accent hue is deliberately outside the red-amber-green band so it never competes with a verdict.

**State reads without color.** Every status is also an icon and a word. A red badge that only says "2" fails for anyone with a color vision deficiency, and it fails in a grayscale screenshot in a README.

**Mono means machine.** Anything the system extracted, measured, or quoted is set in monospace: timecodes, rule types, expected/detected values, transcript evidence, source quotes. Prose written by us is sans. That split is the entire visual thesis — **the user can see at a glance what came from the machine and what came from us.**

**No fake progress.** Progress states name the real step being executed.

---

# 2. Color

Paste these tokens as-is.

```css
:root {
  /* ground */
  --bg:            #F6F7F9;
  --surface:       #FFFFFF;
  --surface-2:     #EDF0F3;
  --border:        #D9DEE5;
  --border-strong: #BCC5D0;

  /* text */
  --text:          #131820;
  --text-2:        #56616F;
  --text-3:        #8996A5;

  /* accent — ink blue, deliberately outside the semantic band */
  --accent:        #1F4E79;
  --accent-hover:  #163A5C;
  --accent-soft:   #DCE8F2;
  --on-accent:     #FFFFFF;

  /* semantic */
  --fail:          #B3271D;   --fail-soft:   #FBE4E1;
  --warn:          #96650A;   --warn-soft:   #FBEFD5;
  --pass:          #1B6E45;   --pass-soft:   #DCF0E5;
  --manual:        #5A5570;   --manual-soft: #E9E7EF;

  /* evidence highlight */
  --mark-bg:       #FBE4E1;
  --mark-underline:#B3271D;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:            #0E1116;
    --surface:       #161B22;
    --surface-2:     #1E252E;
    --border:        #2A323C;
    --border-strong: #3B4653;

    --text:          #E4E9EF;
    --text-2:        #9BA8B6;
    --text-3:        #6E7C8B;

    --accent:        #6FA8DC;
    --accent-hover:  #8CBCE8;
    --accent-soft:   #14283A;
    --on-accent:     #0E1116;

    --fail:          #F0837A;   --fail-soft:   #3A1B18;
    --warn:          #E3AE55;   --warn-soft:   #33280F;
    --pass:          #56C08A;   --pass-soft:   #12301F;
    --manual:        #A9A3C4;   --manual-soft: #22202E;

    --mark-bg:       #3A1B18;
    --mark-underline:#F0837A;
  }
}
```

## Rules for using them

- **Never** define a color only inside the dark block. Every token exists in `:root` first.
- `body` sets `background: var(--bg)` explicitly.
- `--warn` at `#96650A` is ~4.8:1 on white — fine for bold or ≥16px text, and always fine on `--warn-soft`. Do not use it for small light-weight body text.
- The accent is used for: primary buttons, links, focus rings, the active step in the flow. **Nothing else.** It never appears inside a result card.

---

# 3. Typography

No webfonts. System stacks only — zero download, zero build step, no silent fallback.

```css
--sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, sans-serif;
--mono: ui-monospace, "Cascadia Mono", "SF Mono", "Segoe UI Mono",
        Menlo, Consolas, "Liberation Mono", monospace;
```

## Scale

| Role | Size / weight / spacing | Family |
|---|---|---|
| Verdict banner | 28px · 650 · -0.02em | sans |
| Page title | 20px · 650 · -0.01em | sans |
| Card title | 15px · 600 | sans |
| Body | 14px · 400 · 1.55 | sans |
| Secondary | 13px · 400 · `--text-2` | sans |
| **Data** — expected, detected, values | 13px · 500 | **mono** |
| **Timecode** | 12px · 600 · tabular | **mono** |
| **Evidence / source quote** | 13px · 400 · 1.6 | **mono** |
| Label / chip | 11px · 600 · 0.08em · uppercase | mono |

Always `font-variant-numeric: tabular-nums` on timecodes, counts, and the eval table.

---

# 4. Spacing, radius, motion

```css
--s1: 4px;   --s2: 8px;   --s3: 12px;  --s4: 16px;
--s5: 24px;  --s6: 32px;  --s7: 48px;

--r-sm: 3px;   /* chips, inline code */
--r-md: 6px;   /* cards, inputs, buttons */
--r-lg: 10px;  /* the verdict banner */
```

Lay out sibling groups with flex/grid and `gap` — not per-element margins.

Motion: 120ms ease for hover, 200ms for state changes. Nothing else. Always honor `prefers-reduced-motion: reduce`.

---

# 5. Components

## 5.1 Verdict banner

The largest element on the report. Three states, each with icon + word + color.

```
┌─────────────────────────────────────────────────────────┐
│  ✕   DO NOT SEND                                        │   fail
│      2 failed · 1 warning · 4 passed · 1 manual review  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  !   REVIEW                                             │   warn
│      0 failed · 1 warning · 6 passed · 1 manual review  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ✓   SPONSOR READY                                      │   pass
│      All 7 blocking requirements passed.                │
└─────────────────────────────────────────────────────────┘
```

Background `--{state}-soft`, left border 4px `--{state}`, title in `--{state}`, subline in `--text-2`. Radius `--r-lg`, padding `--s5`.

## 5.2 Severity chip

```css
.chip {
  font: 600 11px/1 var(--mono);
  letter-spacing: .08em;
  text-transform: uppercase;
  padding: 4px 8px;
  border-radius: var(--r-sm);
}
.chip--fail   { background: var(--fail-soft);   color: var(--fail); }
.chip--warn   { background: var(--warn-soft);   color: var(--warn); }
.chip--pass   { background: var(--pass-soft);   color: var(--pass); }
.chip--manual { background: var(--manual-soft); color: var(--manual); }
```

Text is always the word: `FAIL` · `WARN` · `PASS` · `MANUAL`.

## 5.3 Result card

Failures first, then warnings, then manual review, then passes (collapsed by default).

```
┌──────────────────────────────────────────────────────────────┐
│ ▎ [FAIL]  Wrong campaign discount               ⟨ 00:43 ⟩    │
│ ▎                                                            │
│ ▎ Expected   73%                                             │
│ ▎ Detected   70%                                             │
│ ▎                                                            │
│ ▎ ┌────────────────────────────────────────────────────────┐ │
│ ▎ │ "You can save up to seventy percent using my link."    │ │
│ ▎ │                        ^^^^^^^^^^^^^^^^^               │ │
│ ▎ └────────────────────────────────────────────────────────┘ │
│ ▎                                                            │
│ ▎ From the brief                                             │
│ ▎ "viewers should be told that they can save seventy-three   │
│ ▎  percent using the campaign offer"                         │
└──────────────────────────────────────────────────────────────┘
```

- 3px left stripe in the semantic color — this is what makes a wall of cards scannable
- `Expected` / `Detected` on a two-column grid, labels in `--text-3` sans, values in mono
- Evidence block: `--surface-2` background, mono, matched span wrapped in `<mark>` (`--mark-bg` + 2px `--mark-underline` underline)
- `From the brief` section renders the `source_quote` — **this is the field that makes the finding auditable, never omit it**
- Timecode is a button. Clicking seeks the player

## 5.4 Split-screen spec review

The screen that kills three objections at once. Two columns, one row per rule, aligned.

```
┌─ SOURCE BRIEF ──────────────────┬─ COMPILED REQUIREMENTS ─────────┐
│                                 │                                 │
│ "...run no shorter than one     │ [DURATION]                      │
│  minute and no longer than one  │ min_seconds  60                 │
│  minute and thirty seconds."    │ max_seconds  90                 │
│                                 │ warning          [Edit] [Del]   │
│ ────────────────────────────────┼──────────────────────────────── │
│ "...they can save seventy-      │ [EXACT_VALUE]                   │
│  three percent..."              │ expected     73%                │
│                                 │ error            [Edit] [Del]   │
└─────────────────────────────────┴─────────────────────────────────┘

  7 requirements extracted · 1 flagged for manual review

  [ + Add Requirement ]              [ Approve & Check Video → ]
```

- Left column: the source sentence, mono, `--text-2`
- Right column: rule type as a chip in `--accent-soft`/`--accent`, fields as a label/value grid
- Hovering a row highlights **both** halves — that connection is the point of the screen
- A rule with `needs_review: true` gets a `MANUAL` chip and a `--warn` left stripe
- On mobile the columns stack, source above rule, with a thin connector line

## 5.5 Manual review item

Visually distinct from the three verdicts — this is not a pass or a failure.

```
┌──────────────────────────────────────────────────────────────┐
│ ▎ [MANUAL]  Visual requirement                               │
│ ▎ "The product interface should be visible on screen for at  │
│ ▎  least five seconds during the segment."                   │
│ ▎                                                            │
│ ▎ SponsorLint does not verify visual requirements. Check     │
│ ▎ this one yourself before sending.                          │
└──────────────────────────────────────────────────────────────┘
```

Dashed left stripe in `--manual`. Never counted in the score. Never blocks `SPONSOR READY`.

## 5.6 Progress

Name the real step. Never a fake percentage.

```
✓ Extracted brief text
✓ Compiled 7 requirements
◐ Transcribing sponsor segment…
· Running checks
```

Done `--pass` · active `--accent` with a spinner · pending `--text-3`.

## 5.7 Buttons

```css
.btn-primary { background: var(--accent); color: var(--on-accent); }
.btn-primary:hover { background: var(--accent-hover); }
.btn-ghost   { background: transparent; color: var(--text);
               border: 1px solid var(--border-strong); }
```

14px/600, padding `10px 16px`, radius `--r-md`. A button says exactly what happens: `Approve & Check Video`, not `Continue`.

---

# 6. Layout

```
Container      max-width 1100px, centered, 24px gutters
Report column  max-width 780px — cards are scanned, not read wide
Review split   two equal columns at ≥900px, stacked below
```

Wide content (the eval table, long transcript lines) gets `overflow-x: auto` on its own container. **The page body never scrolls sideways.**

## Screens

| # | Screen | Contains |
|---|---|---|
| 1 | Upload | Two file inputs, `Compile Brief`, `Load sample campaign` |
| 2 | Review spec | Split screen, edit/delete/add, `Approve & Check Video` |
| 3 | Processing | Real progress steps |
| 4 | Report | Verdict banner, summary counts, result cards, manual review |

`Load sample campaign` is always visible on screen 1 and always works. A judge who does not want to upload anything must still reach screen 4.

---

# 7. Terminal output

The CLI is a first-class surface — it is what `sponsorlint demo` shows, and likely what the README GIF captures.

```
SponsorLint — samples/sponsor-cut-v1.mp4

  FAIL  Wrong campaign discount                            00:43
        expected  73%
        detected  70%
        "You can save up to seventy percent using my link."
        from brief: "...they can save seventy-three percent..."

  FAIL  Required mention missing
        expected  "Shield Mode"
        detected  not found
        from brief: "Please mention Shield Mode by name at least once."

  FAIL  Prohibited claim                                   00:31
        detected  "completely anonymous"
        "It keeps you completely anonymous online."

  WARN  Disclosure placement                               00:04
        brief requires disclosure near the beginning — OK

  MANUAL  Visual requirement — not verifiable from audio
        "The product interface should be visible for five seconds."

  ────────────────────────────────────────────────────────────
  2 failed · 1 warning · 4 passed · 1 manual review

  DO NOT SEND
```

## ANSI

| Element | Code |
|---|---|
| `FAIL` | `\033[31m` bold |
| `WARN` | `\033[33m` bold |
| `PASS` | `\033[32m` bold |
| `MANUAL` | `\033[35m` bold |
| Timecode | `\033[36m` |
| Labels, dim text | `\033[2m` |
| Verdict line | bold + semantic color |

**Detect a non-TTY and drop all codes.** Piped output and CI logs must stay readable — and a README code block with escape sequences in it looks broken.

---

# 8. Accessibility

- Contrast ≥ 4.5:1 for body text, ≥ 3:1 for large text and UI borders. The tokens are chosen to satisfy this in both themes
- **Never color alone.** Every status carries icon + word
- Visible focus ring on every interactive element: `outline: 2px solid var(--accent); outline-offset: 2px`
- Timecode buttons are real `<button>` elements, keyboard reachable
- `<mark>` for the matched span — it carries semantics, not just a background
- Honor `prefers-reduced-motion: reduce` — kill the spinner animation, keep the state text

---

# 9. Copy

Speak like a linter.

**Use:** rule · warning · evidence · timestamp · severity · spec · check · requirement · source · pass · fail · manual review

**Never:** AI magic · smart insights · AI-powered score · revolutionary · seamless · effortless · unlock · supercharge

Findings state the fact, not a judgment of the user:

```
BAD:   "Oops! You forgot to mention the product name."
GOOD:  "Required mention missing — 'Shield Mode' not found."
```

Empty states say what to do next:

```
No requirements to check.
Add at least one rule, or re-compile the brief.
```

---

# 10. The README GIF

The single most-viewed visual artifact in the project.

- Terminal, dark theme, ~6 seconds, no narration, no cursor wiggling
- Shows: `sponsorlint demo` → findings scroll → `DO NOT SEND` → the corrected run → `SPONSOR READY`
- Font ≥ 16px in the recording — it will be viewed at half size on GitHub
- Trim every idle frame. The whole point is the verdict flipping
