# Camera & Cuts

A talking head becomes "edited" through three moves: tight cuts, punch-ins that disguise them,
and a little ambient motion. Use transitions sparingly. On Reels the cut *is* the transition.

## Jump cuts + punch-ins

When pauses or fillers are cut from a static shot, the head jumps slightly. Change the framing on
the cut so it reads as a deliberate camera change:

- Alternate scale **1.00 ↔ 1.08–1.15** on cuts (`"camera": {"auto_punch_on_cuts": true, "punch_scale": 1.1}`).
- Skip cuts closer than **1.2 s** to the previous punch (`min_gap`), or the frame jitters.
- Zoom toward the face: `focus` defaults to the face centre from `reframe.json`.
- Below 1.08 looks like an error; above 1.2 loses resolution on 1080p sources.
- FFmpeg-only path: `auto_edl.py --alternate-zoom 1.1` writes `zoom` into every other EDL range and
  `render_cut.py` crops and scales those ranges.

## Smooth push-ins (emphasis)

`{"at": 21.4, "scale": 1.18, "mode": "smooth", "dur": 0.6}` eases in over 0.6 s (`power2.inOut`).
Use 1–2 per reel, on the payoff line, and reset at the next cut (`{"at": <cut>, "scale": 1.0}`).
Explicit events win over automatic punch-ins within 0.1 s of them.

## Drift (ambient)

A slow linear zoom (+2–3% per 5 s) restarts at each cut (`drift_zoom` in theme `ambient` or `camera`).
It keeps static frames alive without anyone noticing. Use 0 for premium and minimal looks if it feels
"floaty".

## Cadence rule

Something visual changes every **3–5 s**: a cut, punch-in, graphic, b-roll or push-in. Never let more than
8 s go static. `auto_edl.py` lists the long ranges; fill them with a punch-in event, a b-roll cutaway or
a graphic on that beat.

## B-roll

- **Why:** to show what words describe, to cover a jump or a weak take, and to reset attention.
- **How long:** 1.5–4 s. Cut in on a word, cut out on a word or a cut.
- **How:** `{"type": "broll", "src": "assets/x.mp4", "media_start": 2.0, "land_on": 33, "hold": 2.5}`.
  The voice continues; captions stay on top.
- `layout: card` keeps context (the speaker visible around it). `cover` is a full cutaway.
- Only use footage the user owns or licensed. Instagram demotes reposts and other apps' watermarks.

## Transitions

| Transition | Use | How |
|------------|-----|-----|
| **Hard cut** | 95% of the time | default |
| Punch-in cut | jump cuts on a talking head | camera auto punches |
| Smooth push | emphasis | camera smooth event |
| B-roll cutaway | change of subject, cover a cut | `broll` |
| Cover-card wipe | into or out of myth/fact or a quote | `compare` / `quote` cover (built-in fade) |
| Whip, glitch, spin | almost never; energetic trends only | custom component; never on calm or premium |

Avoid stacking a transition and a graphic entrance on the same frame.

## Speed

- Don't speed up speech to hit a length. Cut content instead. If you must, keep it ≤ 1.1× and use
  pitch-preserving `atempo` (0.5–2.0 per instance) in a custom ffmpeg step, and say so in the report.
- Slow motion b-roll is fine (`setpts`), muted.

## Framing checks

- Eyes around 30–40% of frame height. Headroom is not wasted: it is where hook titles live.
- Nothing important in the bottom 35% (UI) or under the right rail.
- After any punch-in, check the top of the head and the hands aren't awkwardly cropped (look at
  `qa/verify_sheet.jpg` "after cut" frames).
