# Recording script — Aegis VPN sponsor segment

Target length **~75 seconds**, inside the brief's 60–90 second window.
Phone mic is fine. Enunciate the numbers.

## V1 — the take with three planted errors

Three lines are deliberately wrong. They are marked ❌.

| ~time | line |
|---|---|
| 0:00 | This video is sponsored by Aegis VPN. |
| 0:04 | I've been using them for about three months now, and honestly it's the one subscription I haven't thought about cancelling. |
| 0:11 | If you've ever connected to hotel Wi-Fi and immediately regretted it, you already know the problem. |
| 0:19 | Aegis runs its own network, so your traffic isn't sitting on some shared box in a data center you've never heard of. |
| 0:26 | The apps are on everything, phone, laptop, even my TV. |
| 0:31 | ❌ It keeps you **completely anonymous** online. |
| 0:35 | Setup took me maybe two minutes, and I haven't touched a setting since. |
| 0:43 | ❌ You can save up to **seventy percent** using my link. |
| 0:48 | That's AegisVPN.com/Alex, and the offer runs through the end of September. |
| 0:56 | I'd honestly recommend it even without the discount, but the discount does make it very easy. |
| 1:03 | So go to aegisvpn.com/alex and get yourself covered before your next trip. |
| 1:11 | Alright, back to the video. |

**The third planted error is an omission:** the phrase "Shield Mode" never occurs anywhere in V1.

Expected verdict: **3 FAIL · 0 WARN · 4 PASS · 1 MANUAL CONFIRMED → 4/7 → DO NOT SEND**

## V3 — the corrected take

**Do not record a second full video.** Re-record only these three lines, in the same
session, same mic, same room, and splice them over the V1 base take.

| replaces | corrected line |
|---|---|
| 0:26 | **Shield Mode** blocks trackers and sketchy sites automatically, and the apps are on everything, phone, laptop, even my TV. |
| 0:31 | It keeps your connection private on any network. |
| 0:43 | You can save up to **seventy-three percent** using my link. |

The 0:26 replacement carries the "Shield Mode" mention, so one splice fixes two rules.

Expected verdict: **0 FAIL · 7 PASS · 1 MANUAL CONFIRMED → 7/7 → SPONSOR READY**

Before approving either take, verify that the fictional Aegis interface remains visible for at
least five seconds, then check **Confirmed manually** in the review screen. The committed approved
sample records this confirmation; an unchecked manual item correctly resolves to `REVIEW`.

## Before you commit to this script — GATE 2:00

Transcribe the six critical strings with `base.en` and confirm each is
recognizable. If any is mangled, change the wording **now**.

| must be *caught* | must be *recognized* |
|---|---|
| "seventy percent" | "Shield Mode" |
| "completely anonymous" | "aegisvpn.com/alex" |
| "This video is sponsored by" | "seventy-three percent" |

```bash
python -m sponsorlint transcribe samples/sponsor-cut-v1.mp4 -o samples/transcript.v1.whisper.json
```

Inspect this candidate and confirm all six strings above before intentionally using it.
Do not overwrite the authored `transcript.v1.json` fixture during the recording gate.
