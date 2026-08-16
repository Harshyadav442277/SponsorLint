# samples/

The committed demo campaign. These files are what `python -m sponsorlint demo` runs against.

| File | What it is |
|---|---|
| `brief.md` | The Aegis VPN sponsor brief, as prose. The compiler's input. |
| `brief.pdf` | The same brief as a PDF, for the `compile` path and the web upload. |
| `script.md` | The recording script, with the three planted errors marked. |
| `spec.approved.json` | The seven-rule specification **after user review**. Hand-written, per `Phases.md` Phase 1. |
| `transcript.v1.json` | Transcript of the take with the planted errors. → `DO NOT SEND` |
| `transcript.v3.json` | Transcript of the corrected take. → `SPONSOR READY` |

## Status of the transcript fixtures

> **The two transcript files are authored fixtures, not yet Whisper output.**
> They match `script.md` line for line and carry realistic segment boundaries and
> timings, which is enough for every validator, the eval harness and the demo to
> run for real.
>
> Once `sponsor-cut-v1.mp4` and `sponsor-cut-v3.mp4` are recorded, regenerate both:
>
> ```bash
> python -m sponsorlint transcribe samples/sponsor-cut-v1.mp4 -o samples/transcript.v1.whisper.json
> python -m sponsorlint transcribe samples/sponsor-cut-v3.mp4 -o samples/transcript.v3.whisper.json
> python -m sponsorlint verify --spec samples/spec.approved.json --transcript samples/transcript.v1.whisper.json
> python -m sponsorlint verify --spec samples/spec.approved.json --transcript samples/transcript.v3.whisper.json
> ```
>
> The first verification is expected to exit 1 with `4/7 DO NOT SEND`; the second
> should exit 0 with `7/7 SPONSOR READY`. Inspect both candidate transcripts and
> confirm all six critical strings from `script.md` are recognizable before replacing
> the committed `transcript.v1.json` and `transcript.v3.json` fixtures.
>
> Nothing else changes — the verdict is computed from whatever the transcript says.
> That is the whole point of `Rules.md` §1.11.

`within_first_seconds: 15` in `spec.approved.json` is **user-authored**. The brief says
"near the beginning" and gives no number; SponsorLint never invents one
(`Architecture.md` §5.4).
