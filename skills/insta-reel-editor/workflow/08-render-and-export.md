# 08 · Render & Export

## 1. Render the picture

```bash
cd $R/composition
npx hyperframes render --quality draft --output ../renders/draft.mp4       # fast look (optional)
npx hyperframes render --quality delivery --output ../renders/graphics.mp4 # final picture
```

- Render only after GATE 2 (preview approval).
- Read the render summary's second line: `beginframe` + GPU is fast; `screenshot` + `software gpu` is the
  slow path (common on Linux and in containers). On macOS, set `PRODUCER_BROWSER_GPU_MODE=hardware`.
- Typical speed: 1–6× realtime depending on GPU and composition. A 45 s reel takes 1–5 min.
- The composition carries the voice. `finalize.py` replaces it with the mixed audio, so the A-roll audio
  in `graphics.mp4` is only for preview.

## 2. Master and deliver

```bash
python3 $S/finalize.py --video $R/renders/graphics.mp4 --audio $R/media/mix.wav \
        --out $R/renders/final.mp4 --cover-at 0.6          # or --cover-image designed_cover.png
```

| Setting | Value | Why |
|---------|-------|-----|
| Video | H.264 High, level 4.2, yuv420p, CRF 18, maxrate 20M / bufsize 40M | Instagram re-encodes anyway: give it a clean, high-quality source under the 25 Mbps cap |
| GOP | 2 s, closed, no scene-cut keyframes | Graph API requires closed GOP |
| Frame rate | the render's (23–60), constant | API spec; keep the source rate |
| Colour | BT.709 primaries, transfer and matrix, TV range | Predictable colour; SDR |
| Audio | two-pass loudnorm (−14 LUFS, TP −1.5), AAC-LC 48 kHz stereo 128 kbps, padded to the video length | spec plus consistent loudness |
| Container | MP4, `+faststart` (moov first), no edit lists | Graph API requirements |
| Cover | `cover.jpg`, 1080×1920, high-quality JPEG from `--cover-at` (default 0 s) | upload as the custom cover |

`renders/final.json` stores the measured numbers.

## 3. Cover image

The cover shows in the Reels tab (9:16), the profile grid (**centre 3:4**, y 240–1680) and the feed (4:5).
- `--cover-at` defaults to 0 s (frame 0 already shows the hook). Passing 0.3–1.0 s grabs the frame after
  the hook title has settled, which is usually nicer.
- Keep the title and face inside **x 70–1010, y 420–1250**, which survives the 3:4, 4:5 and 1:1 crops and
  the UI overlay.
- For a designed cover, snapshot the hook (`npx hyperframes snapshot --at 0.8`), or build a variant plan
  with only the hook title and render one frame, then pass `--cover-image`.

## 4. Upload notes for the user

- Turn on **Settings → Media quality → Upload at highest quality** in the Instagram app.
- Expect softness for minutes to hours after posting while Instagram builds its higher-quality
  encodes (VP9/AV1 for popular reels).
- Hashtags: up to 5 (cap since Dec 2025). The caption text matters more for search than hashtags.
- Professional accounts can post a **Trial Reel** to test a hook variant with non-followers first.
- Auto captions in the Instagram app should be **off** when the reel has burned-in captions
  (otherwise they double up).

## Other engines

- FFmpeg + ASS: `build_ass.py --burn …` writes `renders/graphics.mp4`; then the same `finalize.py`.
- Remotion: `npx remotion render Reel ../renders/graphics.mp4 --codec=h264 --crf=18`; then `finalize.py`.
