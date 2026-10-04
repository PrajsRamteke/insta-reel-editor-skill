# Safe Zones (1080 × 1920)

Instagram overlays UI on reels: the header and camera icon at the top; the username, caption, audio
ticker and navigation at the bottom; like, comment, share, save and audio on the right. Different
phones and states (caption expanded, ads "Sponsored" label) move these. So this skill uses two levels.

## Zone map

| Zone | y range (px) | x range (px) | Rule | Source |
|------|-------------|--------------|------|--------|
| Top UI (organic) | 0–220 | all | no text, no faces | observed 108–220 px [44]; Buffer 250 px [19] |
| Top margin (conservative / ads) | 220–270 | all | no text | Meta: top 14% ≈ 270 px (via [17][18]) |
| **Title-safe core** | **270–1240** | **70–1010** | all text and graphics | this skill |
| Caption band | ≈ 990–1240 | 140–940 | captions only (+ `lower` graphics above it) | this skill; HyperFrames rail guidance 600–700 px from the bottom |
| Right action rail | 1000–1750 | 940–1080 | no text, no key visuals | ~100–120 px wide [18]; Hopper: bottom-right up to 40% [13] |
| Bottom margin (conservative / ads) | 1250–1500 | all | no text | Meta: bottom 35% ≈ 670 px (via [17]) |
| Bottom UI (organic) | 1500–1920 | all | no text | observed 310–450 px [44] |
| Sides | — | 0–65 and 1015–1080 | no text | Meta: 6% ≈ 65 px [17] |

`verify_reel.py` draws these on its contact sheet: **red** = organic UI and rail, **orange** = conservative
margins, **cyan outline** = the 3:4 grid crop.

```
   0 ┌────────────────────────────────────┐
     │▓▓▓▓▓▓▓▓▓ header / camera ▓▓▓▓▓▓▓▓▓▓│ 0–220   red
 220 │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ 220–270 orange
 270 ├─65─┬──────────────────────────┬─65─┤ ← title-safe top (hook titles start here)
     │    │                          │    │
     │    │  graphics: above or      │    │
     │    │  below the face (auto)   │    │
     │    │                          │    │
 990 │    ├──── caption band ────────┤    │
1000 │    │ x 140 ──────────── 940 │▓rail▓│ rail x 940–1080, y 1000–1750
1240 ├────┴──────────────────────────┴────┤ ← caption bottom edge
     │░░░░░░░░░░ conservative ░░░░░░░░░░░░│ 1250–1500 orange
1500 │▓▓▓ username · caption · audio ▓▓▓▓▓│ 1500–1920 red
1920 └────────────────────────────────────┘
```

## Grid and feed crops (cover and first frame)

| Crop | Visible y | Keep cover title and face inside |
|------|-----------|----------------------------------|
| Profile grid 3:4 | 240–1680 | — |
| Feed 4:5 | 285–1635 | — |
| Legacy 1:1 | 420–1500 | — |
| **Survives all + UI** | — | **x 70–1010, y 420–1250** |

## Conflicts between sources

- Some caption guides suggest placing captions at 65–70% of frame height (y 1250–1345). That collides
  with Meta's bottom-35% guidance, so this skill keeps the caption **bottom** edge at 1240.
- Buffer's 250 px bottom margin is too tight for organic reels with a 2-line caption expanded.
- Ads placements are stricter than organic ones. Using the conservative zones means one master works
  for both.

## Practical tips

- Faces: eyes around y 580–760 (30–40%). That leaves y 270–520 for hook titles above the head.
- When a face fills the frame (close-ups), use `cover` cards or graphics below the chin. `auto` handles it.
- Screen recordings: move important UI into the core with `fit-blur` plus a manual zoom, not under the rail.
- The camera icon (top-right) and the "Reels" label (top-left) are small but always on top. Never put
  chips at y < 270.

Sources: [13] hopperhq.com/blog/instagram-reel-size · [17] 1clickreport.com (cites facebook.com/business/help/980593475366490)
· [18] zeely.ai/blog/master-instagram-safe-zones · [19] buffer.com/resources/instagram-image-size
· [44] blitzcutai.com/blog/best-caption-size-instagram-reels-2026
