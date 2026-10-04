# Engine: FFmpeg + ASS (fast path)

No browser and no Node. Seconds to render. Use it when the user wants captions plus simple titles
quickly or cheaply, when HyperFrames can't run, or for batch caption jobs.

## What it supports

| Feature | Support |
|---------|---------|
| Captions: karaoke (colour highlight + 108% active word), pop (progressive reveal), phrase, minimal (box) | ✅ |
| `hook-title` (kicker + headline, auto-wrapped), `keyword` (accent box pop), `cta` (accent box), `chapter` chip | ✅ |
| Cards (stat count-up, list, callout, compare, checklist), b-roll, images, cover cards | ❌ (skipped with a warning) |
| Punch-ins | via EDL range `zoom` (`auto_edl.py --alternate-zoom 1.1`) |
| Drift, smooth pushes, face-aware placement | ❌ |
| Pill highlight behind the active word | ❌ (colour only) |

## Run

```bash
python3 $S/build_ass.py $R/reel-plan.json --burn $R/media/vertical.mp4 --video-out $R/renders/graphics.mp4
python3 $S/mix_audio.py $R/reel-plan.json
python3 $S/finalize.py --video $R/renders/graphics.mp4 --audio $R/media/mix.wav --out $R/renders/final.mp4
```

`build_ass.py` vendors the theme's Fontsource `.woff` files into `fonts_ass/` (libass/FreeType loads
WOFF1) and burns with `ass=captions.ass:fontsdir=fonts_ass`, run from the reel folder.

## ASS essentials (if you edit the .ass)

```
[Script Info]
PlayResX: 1080          ← without these, sizes are relative to 384×288
PlayResY: 1920
WrapStyle: 2            ← no auto-wrap; lines broken with \N
ScaledBorderAndShadow: yes
```
- Colours are `&HAABBGGRR` (alpha first, then BGR): white `&H00FFFFFF`, yellow #FFD60A → `&H000AD6FF`.
- Alignment numpad: 2 = bottom centre (captions, MarginV = 1920 − 1240 = 680), 8 = top centre (titles), 5 = centre.
- BorderStyle 3 = opaque box (OutlineColour is the box colour).
- Useful overrides: `{\fad(in,out)}`, `{\move(x1,y1,x2,y2,t1,t2)}`, `{\t(t1,t2,\fscx100\fscy100)}` (animate scale),
  `{\alpha&HFF&}` (hidden but keeps layout: used for pop reveals), `{\c&H…&}` (colour).
- libass font sizes read about 20% smaller than CSS px at the same number. The script scales by 1.2 to match themes.

## Karaoke technique used

For each page, one Dialogue event per active-word interval (`word.start` → `next.start`), each containing
the whole page with only the active word recoloured and scaled. Layout never shifts, sync is word-exact,
and fades apply to the first and last segments only.
