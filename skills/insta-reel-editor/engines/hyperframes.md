# Engine: HyperFrames (default)

[HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen, Apache-2.0) renders HTML + CSS + GSAP
to MP4 deterministically in headless Chrome. It is built for agents: lint, layout and contrast audits,
snapshots, a Studio preview, and a component registry. It fits this skill because graphics are just HTML,
the license is permissive, and the same composition previews in a browser.

## Setup

```bash
node --version                 # 22+
npx hyperframes doctor         # FFmpeg + Chrome headless shell; "whisper-cpp/Kokoro/MusicGen" are optional
npx hyperframes browser ensure # downloads Chrome headless shell if missing
```
Optional, deeper HyperFrames knowledge for custom work: `npx skills add heygen-com/hyperframes`
(skills `hyperframes-core`, `-animation`, `-keyframes`, `-cli`, `-registry`, `embedded-captions`, `talking-head-recut`).

Environment knobs: `PRODUCER_HEADLESS_SHELL_PATH=/path/to/headless_shell` (use an existing browser),
`PRODUCER_BROWSER_GPU_MODE=hardware` (macOS speed-up).

## The compiled project

`build_hyperframes.py reel-plan.json` writes `composition/`:

```
composition/
├── index.html          one standalone composition: root data-composition-id="reel", 1080×1920
├── vendor/gsap.min.js  vendored (no CDN at render time)
├── fonts/<family>/     Fontsource woff2 subsets, inlined @font-face (font-display: block)
├── assets/             aroll.mp4 (hard link), b-roll, images
├── package.json        npm run check | preview | snapshot | render
└── build-report.json   resolved timings, regions, camera segments, face box, warnings
```

Structure inside `#root`:
- `#cam` (untimed wrapper, `transform-origin` = face) > `<video id="aroll" data-start=0 data-has-audio>`.
  Punch-ins and drift tween `#cam`'s scale, never the video element itself.
- `#scrim-top`, `#scrim-bottom`: legibility gradients (top fades in only with top-band graphics).
- One `.clip.gfx` per graphic (`data-start`, `data-duration`, own track) > `.gfx-pos` (placement and fit
  scale) > `.gfx-anim` (GSAP target) > component markup.
- B-roll: an untimed `.broll-wrap` (opacity and Ken Burns) > a timed muted `<video data-media-start>`.
- `#caps` > one `.clip.cap` per caption page > `.cap-inner` > `.cap-line` > `span.w` per word.
- `#progress` (optional), `#measure` (off-canvas measuring box).
- One `gsap.timeline({paused: true})` registered as `window.__timelines["reel"]` **after** every font face
  has loaded (`document.fonts` loaded explicitly, because unicode-range subsets otherwise load lazily and miss frames).

### Rules the compiler already follows (keep them if you hand-author)
- No CSS `transform` on any element GSAP tweens (`gsap_css_transform_conflict`); set initial states in `fromTo`.
- Never tween `visibility` or `autoAlpha` on a `.clip`. Animate a child (`.gfx-anim`, `.cap-inner`).
- No `<video data-start>` inside another timed element; media timing lives on the video, motion on an untimed wrapper.
- Every `<audio>` needs an `id` (the compiler adds none: audio is mixed in ffmpeg).
- No `Math.random`, `Date.now` or network at render. Finite repeats only.
- Measure and fit text on an off-canvas clone (hidden clips report zero size).

## Commands

```bash
cd composition
npx hyperframes lint                       # fast structural check
npx hyperframes check                      # lint + runtime + layout overlap + motion + WCAG contrast (gate)
npx hyperframes snapshot --at 0,2.5,6      # PNGs in snapshots/ + contact-sheet.jpg
npx hyperframes preview                    # Studio (scrub, inspect, the user can tweak)
npx hyperframes render --quality draft   --output ../renders/draft.mp4
npx hyperframes render --quality delivery --output ../renders/graphics.mp4
```

Expected lint **warnings** for compiled reels: `nested_structure_needs_subcomposition`,
`timeline_track_too_dense`. Errors are never expected.

## Custom graphics (beyond the catalog)

1. **Search the registry first:** `npx hyperframes catalog --query "animated bar chart reveal"`, then
   `npx hyperframes add <name>` into a *separate* project (`npx hyperframes init gfx-chart`).
2. Author the piece as its own 1080×1920 composition (transparent background), using the reel's theme
   colours and fonts and the personality's eases from [reference/timing-easing.md](../reference/timing-easing.md).
3. Render it: an opaque MP4 always works (`npx hyperframes render --output ../assets/chart.mp4`, designed on the
   theme's `cover_bg`). For a transparent overlay, render `--format webm` and check a snapshot of the reel:
   alpha passthrough depends on your HyperFrames version.
4. Place it in the reel plan as `{"type": "broll", "src": "assets/chart.mp4", "layout": "cover", "land_on": …}`
   (`layout: "card"` for an inset).

Lottie animations (LottieFiles) can be embedded the same way: a small HyperFrames project with the Lottie
adapter (`hyperframes-animation` → `adapters/lottie.md`), rendered to WebM, placed as b-roll.

## Editing after build

Don't hand-edit `index.html`: rebuild from `reel-plan.json`. For quick user tweaks in Studio (moving a
card a few px), mirror the change back into the plan (`face_box`, `region`, `captions.bottom`, theme overrides)
so the next build keeps it.

## Performance

- Software GPU (Linux containers): about 4–7× slower than realtime for a full reel at 1080×1920. Use
  `--quality draft` and snapshots while iterating, and render the delivery version once.
- Fewer simultaneous elements renders faster. Captions are cheap; full-frame blurs and shadows are expensive.
- Long reels (> 90 s): consider `npx hyperframes render --docker` or the cloud and lambda options in `hyperframes-cli`.
