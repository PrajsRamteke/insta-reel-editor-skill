# Troubleshooting

## Edit & sync

| Symptom | Cause | Fix |
|---------|-------|-----|
| Captions drift progressively later | VFR source; or captions built from `words.json` (source timeline) | Run `prep.py`; always caption from `words.cut.json` |
| Captions early or late by a constant amount | ASR timing offset (some engines run 50–100 ms off) | `make_captions.py --offset -0.06` (or +); or re-transcribe the cut (`transcribe.py media/cut.mov`) |
| First syllable clipped after cuts | Head pad below the speaker's onset ramp | `auto_edl.py --head 0.14`, or extend that range's `start` by 0.05 |
| Last word clipped / breath cut | Tail pad too tight; ASR end early | `--tail 0.22`; check `render_cut` "words clipped" warning |
| Click or pop at a cut | Boundary without a fade (hand-made cut) | Always cut with `render_cut.py` (30 ms fades) |
| Frozen first frame on segments | Stream-copy cut / sparse keyframes | Re-encode per segment (render_cut does); prep for a 1 s GOP |
| A/V durations differ by > 2 frames | Non-frame-aligned ranges / VFR | `render_cut.py` snaps to frames; prep first |
| Same sentence twice | Retake not removed | Check "Possible retakes" in `phrases.md`; `--drop` the earlier one |

## Transcription

| Symptom | Cause | Fix |
|---------|-------|-----|
| "No transcription engine available" | Nothing installed or no key | `pip install faster-whisper` (or `mlx-whisper` on a Mac) or set an API key |
| English words on a Hindi video | `.en` model or wrong `--language` | multilingual model + `--language hi` |
| "Thank you." over silence, repeated loops | Whisper hallucination | QC flags `repetition_loops`; delete phantom words; use VAD (faster-whisper does) |
| Brand or pose names misspelled | No keyterms | `--keyterms keyterms.txt`; fix `display` in captions |
| No fillers in the transcript | Engine normalizes | ElevenLabs/Deepgram (fillers on) or the verbatim prompt (default) |

## Framing

| Symptom | Cause | Fix |
|---------|-------|-----|
| "no face detector → center crop" | opencv or mediapipe missing; model download blocked | `pip install opencv-python mediapipe`; or `--model` a local file |
| Haar unavailable on OpenCV 5 | OpenCV 5 removed cascades | use mediapipe or yunet (auto) |
| Camera hunts left and right | Two faces / gestures | raise `--deadzone 0.12`; or `fit-blur` |
| Limbs cut off in exercise clips | 9:16 crop of a wide shot | `--mode fit-blur` |
| Soft, blurry reel | 1080p landscape → 608 px crop upscaled | shoot vertical or 4K; tell the user |

## Graphics (HyperFrames)

| Symptom | Cause | Fix |
|---------|-------|-----|
| `check`: content_overlap with captions | graphic in the caption band | region `auto`/`lower` (lower sits above captions); shorter text |
| `[reel] gX cannot avoid the face` | big card + close-up face | `region: "cover"`, fewer words, or another moment |
| Text over the face | No face box (no reframe.json) | run `reframe.py`, or set `"face_box": [y0, y1]` |
| Hook invisible on frame 0 | `start` > 0.05 | `"start": 0` for the hook title |
| Fallback font / wrong glyphs | Fontsource package or weight missing; no network for the first install | rebuild online once (npm cache), or `--node-modules` |
| Emoji blank | vendored emoji fonts don't render headless | the compiler uses system emoji; install `fonts-noto-color-emoji` on Linux |
| Render very slow | software GPU (`screenshot` path) | macOS: `PRODUCER_BROWSER_GPU_MODE=hardware`; `--quality draft` while iterating |
| `Chrome Headless Shell is required` | browser not installed | `npx hyperframes browser ensure`, or set `PRODUCER_HEADLESS_SHELL_PATH` |
| Lint warnings `nested_structure_needs_subcomposition` | compiled single-file reel | expected; ignore (errors are not) |
| Graphic overlaps another | `land_on` + `until_word` overlap > 0.8 s | adjust times; small overlaps are auto-trimmed |

## Audio & delivery

| Symptom | Cause | Fix |
|---------|-------|-----|
| Loudness WARN/FAIL | mixed elsewhere or skipped finalize | always run `finalize.py` on the final mix |
| Music too loud under speech | `gain_db` too high / duck off | `gain_db: -22`, `duck: true`, `duck_ratio: 10` |
| Reel muted after upload | copyrighted music | remove it; use in-app library audio or royalty-free |
| Upload rejected | < 3 s, > 60 fps, odd codec | `verify_reel.py` lists the failing spec |
| Looks soft after posting | Instagram's basic encode first | wait; enable "Upload at highest quality" |

## Process

| Symptom | Fix |
|---------|-----|
| Endless fix loops | cap at 3 self-eval passes; report the remaining issues honestly |
| User feedback hits the wrong layer | use the feedback → file map in [workflow/06-build-and-preview.md](../workflow/06-build-and-preview.md) |
| Lost context on a return visit | read `project.md` first, then summarise the last session in one line |
