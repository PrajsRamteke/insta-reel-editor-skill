# Style Presets (themes)

Seven presets in `assets/themes/*.json`. Each sets fonts, colours, caption style, title treatment,
shape, motion personality and ambient layers. Use one as is, extend it with `theme_overrides`, or
create your own.

| Preset | Personality | Fonts (display / body) | Accent | Captions | Feel | Best for |
|--------|-------------|------------------------|--------|----------|------|----------|
| `clean-educator` (default) | clean | Inter 800 / Inter 600 | yellow `#FFD60A` | karaoke, pill | crisp, confident, readable | explainers, tips, tutorials |
| `calm-wellness` | calm | Fraunces 600 / DM Sans 600 | sage `#B9D7A8` | phrase, soft colour | warm, slow, breathing | yoga, breathwork, meditation, health |
| `bold-hype` | energetic | Anton / Montserrat 800 | lime `#C6FF00` | pop, uppercase | loud, fast, high contrast | fitness, motivation, hot takes |
| `premium-editorial` | premium | Playfair Display 600 / Inter 600 | champagne `#E6D3A8` | phrase, no highlight | elegant, restrained | founders, finance, interviews, luxury |
| `playful-pop` | playful | Poppins 800 / Poppins 600 | pink `#FF4F9A` (dark text) on white cards | karaoke, pill | bouncy, friendly | lifestyle, food, family, light tips |
| `minimal-subtitle` | premium | Inter 700 / Inter 600 | white | minimal, box | invisible design | vlogs, cinematic b-roll, stories |
| `tech-mono` | clean (snappier: 0.28/0.20 s, `power4.out`) | Space Grotesk 700 / JetBrains Mono 700 | mint `#00E599` | karaoke, pill | technical, sharp | coding, AI, product demos |

## Choosing

1. Brand kit says a base theme → use it.
2. Otherwise the archetype default ([director/reel-archetypes.md](../director/reel-archetypes.md)).
3. Otherwise match the emotion keywords ([director/motion-personality.md](../director/motion-personality.md)).

Don't switch themes mid-series: a creator's reels should be recognizable in the grid.

## Customizing

**Small changes (per reel):**
```json
"theme": "clean-educator",
"theme_overrides": {"colors": {"accent": "#00C2A8", "on_accent": "#002420"}, "caption": {"size": 70}}
```

**A brand theme (reusable):** save as `preferences/<brand>.json` and reference it by path, relative to
the reel plan (or absolute):
```json
{
  "extends": "calm-wellness",
  "name": "habuild-calm",
  "colors": {"accent": "#F6B93B", "on_accent": "#2A1B00"},
  "fonts": {"body": {"family": "Mukta", "package": "@fontsource/mukta", "weight": 600}},
  "caption": {"style": "karaoke", "highlight": "color", "size": 62}
}
```
`"theme": "preferences/habuild-calm.json"` in `reel-plan.json` (looked up next to the plan first, then in
the skill folder).

**Token meanings** are documented in [reference/typography-and-color.md](../reference/typography-and-color.md).

## Preset previews (what to expect)

- **clean-educator**: white bold captions with a yellow pill on the spoken word; dark rounded cards;
  headlines slide up word by word; punch-ins on cuts; subtle drift.
- **calm-wellness**: serif headline fades in slowly; captions show whole phrases; sage accents;
  no bounce; longer holds; drift +3%.
- **bold-hype**: huge condensed uppercase words pop one at a time in lime; boxed titles; progress bar;
  fast cuts.
- **premium-editorial**: serif titles reveal top-to-bottom with no bounce; no highlight; generous space.
- **playful-pop**: white cards with pink accents, slight rotation on entrance, bouncy pops.
- **minimal-subtitle**: small boxed subtitles; graphics rare and quiet; footage first.
- **tech-mono**: mono captions with a mint pill; grotesk headlines; dark cards; progress bar.
