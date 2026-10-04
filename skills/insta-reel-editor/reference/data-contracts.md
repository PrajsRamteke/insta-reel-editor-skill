# Data Contracts

The files that flow between steps. Paths inside a file are **relative to that file's folder** (the reel
workdir) unless absolute. All times are in seconds.

## Contents
1. `words.json` / `words.cut.json`: transcript
2. `edl.json` / `edl.resolved.json`: cut decisions
3. `reframe.json`: framing and face track
4. `captions.json`: caption pages
5. `reel-plan.json`: the creative plan (the main file the agent writes)
6. Theme JSON

---

## 1. words.json (source timeline) · words.cut.json (cut timeline)

```json
{
  "version": 1, "engine": "elevenlabs:scribe_v2", "language": "en", "duration": 63.2, "source": "media/voice16k.wav",
  "words": [
    {"i": 0, "text": "Most", "start": 0.40, "end": 0.63, "conf": 0.95, "type": "word", "speaker": "speaker_0"},
    {"i": 6, "text": "(laughs)", "start": 2.0, "end": 2.3, "type": "event"}
  ],
  "qc": {"words": 54, "garbage_ratio": 0, "repetition_loops": 0, "inflated_fixed": [], "warnings": []}
}
```
- `text` keeps punctuation ("way."), which is needed for sentence breaks. No leading spaces.
- `type`: `word` | `event` (audio events are never captioned).
- Optional: `conf` (0–1), `speaker`, `inflated` (duration was shrunk), `interpolated` (WhisperX digits),
  `approx` (SRT import).
- `words.cut.json` adds `"timeline": "cut"` and per word `src_i` (source index). `i` is re-numbered from 0.

## 2. edl.json → edl.resolved.json

```json
{
  "version": 1, "source": "media/mezz.mp4", "fps": 30, "pace": "natural",
  "params": {"max_gap": 0.4, "head": 0.1, "tail": 0.16, "end_hold": 0.45},
  "ranges": [
    {"start": 41.2, "end": 43.6, "words": [212, 218], "text": "Most people breathe…", "reason": "cold open"},
    {"start": 0.37, "end": 2.2, "words": [0, 5], "text": "…", "reason": "speech", "zoom": 1.0, "focus": [0.5, 0.4]}
  ],
  "dropped": [{"i": 6, "text": "um", "start": 3.07, "end": 3.37, "reason": "filler"}],
  "stats": {"source_duration": 63.2, "output_duration": 38.4, "removed_s": 24.8, "cuts": 11},
  "notes": ["2 ranges run longer than 8 s with no cut: …"]
}
```
- `ranges` play **in array order** (cold opens allowed). Times are on the source; `render_cut.py` snaps them
  to frames. `words` = [first, last] source indices (informational).
- Optional per range: `zoom` (≥ 1, FFmpeg-path punch-in) and `focus` [x, y] 0–1.
- `edl.resolved.json` (written by `render_cut.py`) adds per range `src_start`, `src_end`, `out_start`, `out_end`,
  plus top-level `cuts` (output times of every boundary), `output`, `output_duration`.

## 3. reframe.json

```json
{
  "mode": "track", "source_size": [1920, 1080], "detector": "mediapipe-blazeface", "face_coverage": 0.97,
  "crop_width": 608, "keyframes": [[0.0, 0.31], [5.6, 0.31], [6.2, 0.40]],
  "face_box_median": {"x0_median": 0.35, "y0_median": 0.21, "x1_median": 0.63, "y1_median": 0.35},
  "face_track": [{"t": 0.0, "box": [0.35, 0.19, 0.63, 0.35]}, {"t": 0.6, "box": null}]
}
```
- `keyframes`: [time, face-centre x as a fraction of the source width] for the lazy camera.
- Face boxes are normalized to the **9:16 output canvas** (x0, y0, x1, y1). The compiler converts them to px.

## 4. captions.json

```json
{
  "version": 1, "style": "karaoke", "source": "transcript/words.cut.json",
  "params": {"max_words": 4, "max_chars": 18, "lines": 2, "pause": 0.45, "max_dur": 2.6},
  "pages": [
    {"id": "c0", "start": 0.0, "end": 1.13, "lines": 2,
     "words": [{"i": 0, "text": "Most", "display": "Most", "start": 0.03, "end": 0.27, "line": 0, "emph": false}]}
  ]
}
```
- `display` is what is shown (punctuation stripped, spelling fixed). `text` is the ASR original.
- Pages never overlap; `line` is 0 or 1. Edit freely, keeping times monotonic.

## 5. reel-plan.json

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `version` | int | 1 | |
| `video` | path | — | 9:16 A-roll (`media/vertical.mp4`). Omit for faceless reels (then `duration` is required) |
| `duration` | s | video length | |
| `words` | path | — | cut-timeline words, needed for `land_on`/`until_word`/`on_word` |
| `theme` | name/path/object | `clean-educator` | `assets/themes/<name>.json`, a JSON path, or an inline object (may `"extends": "<name>"`) |
| `theme_overrides` | object | — | deep-merged into the theme (e.g. `{"colors": {"accent": "#00C2A8"}}`) |
| `motion_style` | `fade`·`reveal`·`slide`·`pop` | from personality | force the entrance style |
| `reframe` | path | `reframe.json` | face box source |
| `face_box` | [y0, y1] px | from reframe | manual override for `auto` placement |
| `captions` | object | — | `{"file": "captions.json", "enabled": true, "bottom": 1240, "overrides": {"size": 70, "highlight": "color", "box": false}}` |
| `camera` | object | — | `auto_punch_on_cuts` (bool), `punch_scale` (1.1), `cuts` (path or list; default `edl.resolved.json`), `min_gap` (1.2), `drift_zoom`, `focus` [x, y], `events` [{`at`, `scale`, `mode`: `cut`/`smooth`, `dur`}] |
| `graphics` | array | [] | components, see [patterns/motion-graphics.md](../patterns/motion-graphics.md) |
| `progress_bar` | bool | theme | thin top bar |
| `ambient` | object | theme | `scrim_top`, `scrim_bottom`, `drift_zoom`, `progress_bar` |
| `background` | colour | theme `cover_bg` | canvas background |
| `audio` | object | — | for `mix_audio.py`: `voice` (default `media/cut.mov`, else `video`, else none = music-only), `voice_chain`, `denoise`, `music` {`src`, `gain_db`, `duck`, `duck_ratio`, `fade_in`, `fade_out`, `offset`}, `sfx` [{`src`/`preset`, `at`/`on_word`, `gain_db`, `lead`}] |

Graphic object (common fields): `type`, `id`, `start`/`end` or `land_on`/`until_word`
(`land_on_src`/`until_word_src` for source indices; preferred) or `hold`, `region`, `allow_overlap`.
Word-anchored secondaries: `reveal_word(_src)` (compare), `item_words(_src)` (checklist). SFX:
`on_word_src` or `on_word`. Type-specific
fields: [patterns/motion-graphics.md](../patterns/motion-graphics.md).

Compiler outputs: `composition/index.html`, `composition/build-report.json` (`warnings`, resolved `graphics`
with `start`/`end`/`region`, `camera` segments, `face`).

## 6. Theme JSON

See [typography-and-color.md](typography-and-color.md#theme-token-reference-assetsthemesjson). Custom
themes: save a JSON in the reel folder or the skill's `preferences/` folder and reference it by path
(`"theme": "preferences/my-brand.json"`: tried relative to the plan first, then to the skill folder),
or inline with `{"extends": "clean-educator", ...}`.
