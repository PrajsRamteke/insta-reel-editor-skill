# 01 · Probe & Prep

## Install check (first run on a machine)

```bash
ffmpeg -version | head -1            # need ffmpeg + ffprobe (Homebrew: brew install ffmpeg)
python3 --version                    # 3.9+
node --version                       # 22+ for HyperFrames (engines/hyperframes.md)
npx hyperframes doctor               # Chrome headless shell, FFmpeg, memory
python3 -c "import cv2, mediapipe"   # optional: face-tracked reframing (pip install opencv-python mediapipe)
```

## Probe

```bash
python3 $S/probe.py raw.mp4 --loudness --out $R/probe.json
```

It reports orientation (vertical 9:16, 4:5, 3:4, square, landscape), display size after rotation,
fps and VFR suspicion, HDR (HLG/PQ/BT.2020), bit depth, audio presence and loudness, and duration
warnings. It also prints **actions**, for example "landscape → reframe track or fit-blur".

## Prep (normalize to a mezzanine)

```bash
python3 $S/prep.py raw.mp4 --workdir $R            # --fps auto|30|60, --no-tonemap
```

| Problem in phone footage | What prep does | Why it matters |
|--------------------------|----------------|----------------|
| Variable frame rate | `fps=` conform to the nearest standard (or 30) | VFR drifts captions and A/V after cuts |
| Sparse keyframes (GOP 2–10 s) | 1-second GOP, no scene-cut keyframes | Browser renderers freeze on seek; cuts land exactly |
| HDR (iPhone HLG / Dolby Vision) | zscale + hable tone-map → SDR BT.709 | Graphics colours shift; Instagram may show it washed out |
| 10-bit / 4:2:2 | 8-bit yuv420p | Delivery format; faster everywhere |
| Rotation metadata | applied (ffmpeg autorotate) | Sizes are always the displayed orientation |
| Vertical at odd sizes (e.g. 1242×2208) | scaled and cropped to exactly 1080×1920 | One canvas everywhere |
| 120/240 fps slow-mo | conformed to 30 | Instagram accepts 23–60 fps |

Outputs: `media/mezz.mp4` (CRF 16, AAC 320k), `media/voice16k.wav` (ASR input),
`qa/contact_source.jpg` (one tile per N seconds, at most 40). **Read the contact sheet image**:
it is the fastest way to know framing, burned-in text, lighting and how much b-roll you need.

## Multiple source clips (takes, b-roll-heavy shoots)

Treat the A-roll as **one source**: prep every clip with the same `--fps`, then concatenate the
mezzanines (identical codec settings, so stream copy is safe). Transcribe the joined file once.

```bash
for f in take1.mov take2.mov take3.mov; do python3 $S/prep.py "$f" --workdir "$R/clips/${f%.*}" --fps 30; done
printf "file '%s'\n" $R/clips/*/media/mezz.mp4 > $R/clips/list.txt
ffmpeg -f concat -safe 0 -i $R/clips/list.txt -c copy $R/media/mezz.mp4
ffmpeg -i $R/media/mezz.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le $R/media/voice16k.wav
```

All mezzanines must share size and fps (vertical clips always come out 1080×1920; for mixed
orientations, run `reframe.py` on each clip first and concatenate the vertical results).
The EDL then picks the best take of each beat on that single timeline (retake detection in
`phrases.md` works across clip boundaries). Pure b-roll clips don't go in the A-roll: put them in
`assets/` and place them as `broll` graphics.

## Gotchas

- An ffmpeg build without `libzimg` can't tone-map HDR: prep warns. On macOS, Homebrew's ffmpeg has it.
- Don't upscale vertical sources below 1080 px wide beyond 1080×1920; they will look soft. Say so.
- Keep the original. All edits are re-done from `mezz.mp4`, so you can always rebuild.
