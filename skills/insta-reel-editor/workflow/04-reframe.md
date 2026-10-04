# 04 · Reframe to 9:16

```bash
python3 $S/reframe.py $R/media/cut.mov --out $R/media/vertical.mp4 --mode auto
#   modes: auto | track | center [--x 0.4] | fit-blur | fit-color [--bg "#101010"]
#   --fit-anchor upper   fit modes: frame at y=290 so captions sit below it (screen recordings)
#   --deadzone 0.08  --detector auto|mediapipe|yunet|haar  --model <file>
```

Always run it, even on vertical footage. It writes `reframe.json` with the **face box** (median and per
second, normalized to the 9:16 canvas). `build_hyperframes.py` uses that box to keep graphics off the
face (`region: "auto"`) and to aim punch-ins at the face.

## Choosing a mode

| Source | Mode | Why |
|--------|------|-----|
| Vertical 9:16 | `auto` → scale | Already framed |
| Landscape talking head (one person) | `track` | Follows the face with a lazy camera |
| Landscape, whole-body exercise, yoga, dance | `fit-blur` (or `track` with care) | A 608-px-wide crop amputates limbs |
| Screen recording, slides, code | `fit-blur --fit-anchor upper` | Content sits at y 290–900, so captions below it never cover it |
| Two people in conversation | `track` (dominant face) or `fit-blur` | Fast back-and-forth makes tracking jumpy |
| 4:5 / 1:1 phone footage | `track` or `center` | Small crop; fit-blur if heads are near the edges |

Instagram demotes bordered reels. `fit-blur` fills the frame with a blurred copy, which is far better
than black bars. Use it deliberately, not by default.

## How tracking works (and why it looks human)

1. Detect faces at 5 fps (MediaPipe BlazeFace → OpenCV YuNet → Haar, whichever is installed; models
   download once to `~/.cache/insta-reel-editor`).
2. Fill gaps, then apply a ~1 s median filter (kills jitter and false positives); prefer the face
   nearest the previous one.
3. **Lazy camera:** hold still while the face stays inside a dead-zone (8% of source width). When it
   leaves for more than 0.5 s, ease (smoothstep, 0.6 s) to the new position. Never start a move in the
   last 0.8 s.
4. Render with one ffmpeg `crop` whose x is a piecewise-smoothstep expression of `t`, then lanczos
   scale to 1080×1920.

Face coverage below 50% prints a warning (profile shots, sunglasses, low light). Check the result or
fall back to `center --x` or `fit-blur`.

## Quality notes

- A 9:16 crop from 1080p landscape is only 608×1080, which upscales 1.78× and looks soft on phones.
  From 4K it's 1215×2160, which downscales and stays sharp. Tell the user when the source limits quality.
- Keep the eyes around y 0.30–0.40 of the frame (the camera focus defaults to the face centre). Faces
  too low collide with captions; faces too high collide with hook titles.
- For emphasis zooms at a specific moment, use `camera.events` in the plan (scale around the face
  `focus`). For a different crop *position*, re-run `reframe.py` (`center --x`) rather than hacking the plan.
- With no detector installed, `auto` falls back to a centre crop and says so. Install with
  `pip install opencv-python mediapipe`.
