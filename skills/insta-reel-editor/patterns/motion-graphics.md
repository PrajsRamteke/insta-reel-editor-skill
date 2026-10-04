# Motion-Graphics Components

The compiler (`build_hyperframes.py`) turns each entry in `reel-plan.json → graphics` into a themed,
personality-matched, face-aware animated component. Every component accepts these **common fields**:

| Field | Meaning |
|-------|---------|
| `type` | one of the components below (required) |
| `id` | optional; letters first (`g1`, `stat-73`) |
| `start` / `end` | seconds on the cut timeline |
| `land_on` / `until_word` | cut-timeline word index; start = word.start − enter duration, end = word.end + 0.35 |
| `land_on_src` / `until_word_src` | the same with **source** indices (looked up via `src_i`). **Preferred**: they survive re-cuts |
| `hold` | seconds, when there is no `end` / `until_word` (defaults per type below) |
| `region` | `auto` (face-aware) · `top` · `middle` · `lower` (above captions) · `cover` (full-frame card) |
| `allow_overlap` | `true` to deliberately layer with another hero (rare) |

Text fields accept `*accent*` markup. Icons: `check x alert info bulb bookmark send heart star arrow
clock flame sparkle breath play`.

## Catalog

### `hook-title`: the opener
```json
{"type": "hook-title", "start": 0, "end": 2.4, "kicker": "Stop doing this", "text": "*3* breathing mistakes"}
```
Kicker = small accent pill (category or warning, ≤ 3 words); headline = 3–7 words, auto-fit to ≤ 3 lines.
At `start: 0` the title is fully visible on frame 0 and settles 106% → 100%. Later starts stagger
word by word. Default region `auto`; themes with `title.box` put it on a card.

### `keyword`: a stressed word or verdict
```json
{"type": "keyword", "land_on": 42, "text": "SLOW DOWN", "icon": "breath", "region": "middle"}
```
Accent block, 1–3 words, pops (clean/playful/energetic) or reveals (premium/calm). 1.2–1.8 s.

### `stat`: a number that matters
```json
{"type": "stat", "land_on": 23, "until_word": 30, "value": 73, "suffix": "%", "label": "of adults breathe too fast"}
```
Counts up from `from` (default 0) over about 1 s. `prefix` (e.g. "₹", "$"), `suffix`, decimals inferred from
`value` (`2.5`). Label ≤ 8 words. Pair with a `ding` SFX at the end of the count.

### `list-item`: numbered point
```json
{"type": "list-item", "land_on": 25, "until_word": 37, "index": 1, "total": 3, "text": "Breathe through your *nose*"}
```
Badge with the number, text ≤ 7 words, progress dots when `total` is set. One per list beat; the next
item's start trims the previous one.

### `chapter`: small section chip (secondary)
```json
{"type": "chapter", "start": 3.0, "end": 9.5, "text": "Mistake 1/3"}
```
Top-left chip at y 270. It can coexist with a hero graphic: heroes visible at the same time are
pushed below the chip automatically. Good for long listicles and pose names.

### `callout`: tip, warning, myth, fact, note, do, don't
```json
{"type": "callout", "variant": "warning", "land_on": 41, "text": "Don't hold your breath when stressed", "title": "Careful"}
```
Variant (`tip` · `warning` · `myth` · `fact` · `note` · `do` · `dont`; anything else is rejected) sets the
icon and title colour (tip = accent + bulb, warning = amber + alert, myth = red + x, fact = green +
check, note = info). Text ≤ 14 words.

### `compare`: myth vs fact, before vs after, don't vs do
```json
{"type": "compare", "start": 12.1, "end": 17.0, "reveal_at": 14.2,
 "left": {"label": "Myth", "text": "Breathe fast for more air"},
 "right": {"label": "Fact", "text": "Slow breaths deliver *more* oxygen"}}
```
Default region `cover` (full-frame backdrop at 94%). The left card enters at start; the right card at
`reveal_word_src` / `reveal_word` (a word index) or `reveal_at` (seconds; default 40% in), when the left
dims to 55%. Times outside the window are clamped with a warning. For before/after, set labels and icons:
`"left": {"label": "Before", "icon": "clock", ...}, "right": {"label": "After", "icon": "star", ...}`.

### `checklist`: steps or recap
```json
{"type": "checklist", "start": 18.0, "end": 24.0, "title": "Try tonight",
 "items": ["4 s inhale", "7 s hold", "8 s exhale"], "item_times": [18.6, 20.1, 21.9]}
```
Items tick in on `item_words_src` / `item_words` (one word index per item: their spoken words) or
`item_times` (seconds), else evenly. 3–5 items, each ≤ 5 words.

### `lower-third`: name or credential (secondary)
```json
{"type": "lower-third", "start": 1.2, "end": 4.0, "name": "Dr. Asha Rao", "title": "Breathwork coach"}
```
Left-aligned above the caption band. Heroes visible at the same time keep clear of it. Use once,
early, and not on the hook frame.

### `quote`: a memorable line
```json
{"type": "quote", "land_on": 88, "until_word": 97, "text": "Slow is *smooth*, smooth is fast", "attribution": "Navy SEAL saying"}
```
Default region `cover`. ≤ 12 words. Once per reel.

### `image`: diagram, screenshot, product shot
```json
{"type": "image", "src": "assets/diaphragm.png", "land_on": 52, "hold": 3, "caption": "Belly, not chest", "region": "auto"}
```
Card with optional caption, slow Ken Burns (1.00 → 1.05; `"ken_burns": false` to disable).

### `broll`: cutaway footage
```json
{"type": "broll", "src": "assets/walk.mp4", "media_start": 3.0, "land_on": 61, "hold": 2.5, "layout": "cover"}
```
Muted video. `layout: cover` (full frame) or `card` (rounded inset). Pick `media_start` to show the
right moment. 1.5–4 s. The voice continues underneath and captions stay on top.

### `cta`: ending ask
```json
{"type": "cta", "land_on": 40, "end": 14.9, "text": "Save this for tonight", "icon": "bookmark"}
```
Accent pill above the caption band with a gentle pulse. Ask for a **save** or **send**; `icon: send` for
"send this to…".

### `sticker`: emoji pop (secondary, playful/energetic only)
```json
{"type": "sticker", "land_on": 77, "hold": 1.2, "text": "🔥", "region": "top"}
```
Uses the system emoji font (Apple Color Emoji on macOS). Sparingly: at most 1–2 per reel.

## Defaults per type

| Type | Default region | Default hold | Hero? |
|------|---------------|--------------|-------|
| hook-title | auto | 2.8 s | yes |
| keyword | auto | 1.6 s | yes |
| stat | auto | 2.8 s | yes |
| list-item | auto | 3.0 s | yes |
| chapter | chip (top-left) | 2.0 s | secondary |
| callout | auto | 3.2 s | yes |
| compare | cover | 4.2 s | yes |
| checklist | auto | 4.5 s | yes |
| lower-third | above captions, left | 3.0 s | secondary |
| quote | cover | 3.5 s | yes |
| image | auto | 3.0 s | yes |
| broll | cover | 3.0 s | yes |
| cta | lower | 3.0 s | yes |
| sticker | auto | 1.4 s | secondary |

## Regions and face-aware placement

- `auto`: measures the graphic, then places it in the larger free band **above** (y 270 → face top − 30)
  or **below** (face bottom + 30 → caption band − 24) the face from `reframe.json`. If neither fits, it
  scales down (≥ 0.72×) in the larger band and logs a runtime warning that `check` surfaces.
- Secondary bands are reserved first: a visible `chapter` chip pushes `top`/`auto` heroes below it, and a
  visible `lower-third` caps the lower band.
- `top`: top edge at y 270 (or below an active chip). `middle`: centred at y 820. `lower`: bottom edge just above the caption band.
  `cover`: full-frame backdrop; content centred in y 270–960.
- Override the face box when detection is missing: `"face_box": [520, 900]` (y0, y1 in px).

## Camera (in the same plan)

```json
"camera": {"auto_punch_on_cuts": true, "punch_scale": 1.1, "min_gap": 1.2, "drift_zoom": 0.02,
           "focus": [0.5, 0.33],
           "events": [{"at": 21.4, "scale": 1.18, "mode": "smooth", "dur": 0.6}, {"at": 24.0, "scale": 1.0}]}
```
See [camera-and-cuts.md](camera-and-cuts.md).

## Other plan switches

| Key | Effect |
|-----|--------|
| `theme` / `theme_overrides` | preset name and deep-merged overrides (colours, fonts, caption, motion, ambient) |
| `motion_style` | force `fade` · `reveal` · `slide` · `pop` (otherwise from the personality) |
| `progress_bar` | `true` adds a thin accent bar at the top filling over the reel |
| `ambient` | `{"scrim_top": true, "scrim_bottom": true, "drift_zoom": 0.02}` |
| `background` | colour behind everything (faceless reels without video) |
| `captions.bottom` | caption bottom edge in px (default 1240) |

## Custom components

When the catalog doesn't fit (charts, animated diagrams, maps, a branded intro), build that one piece
as its own HyperFrames composition or Lottie file, render it to a transparent or opaque clip, and place
it as `broll` (`layout: card` or `cover`). See [engines/hyperframes.md](../engines/hyperframes.md) →
"Custom graphics". Keep the reel's theme and personality.
