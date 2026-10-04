# Typography & Colour for 9:16

Phones are held at about 30 cm, but text competes with a moving face, UI overlays and sunlight. Size up,
weight up, and limit choices.

## Type scale on 1080×1920

| Role | Size | Weight | Line height | Max |
|------|------|--------|-------------|-----|
| Hook headline | 88–132 px (auto-fit to ≤ 3 lines) | 700–900 (display) | 1.04–1.08 | 7 words |
| Keyword block | 54–92 px | display | 1.0 | 3 words |
| Stat number | 160–200 px | display | 1.0 | — |
| Card body (list, callout, compare) | 44–56 px | 700–800 | 1.15–1.25 | 14 words |
| Captions karaoke / pop | 60–66 / 80–90 px | 700–800 | 1.16 | 2 lines × 18 / 1 line × 14 chars |
| Captions phrase / minimal | 54–62 / 44–48 px | 600 | 1.16 | 2 lines × 26–28 chars |
| Kicker / chip / label | 30–40 px, letter-spacing 0.05–0.08 em, uppercase | 800 | 1.0 | 3 words |
| Never below | 30 px | — | — | — |

Rule of thumb (HyperFrames talking-head guidance): portrait sizes are about 1.3× landscape sizes. A 28 px
label that looked fine on a desktop preview is unreadable on a phone.

## Fonts

- Two families at most: a **display** (titles, numbers) and a **body** (captions, card text). Themes bundle
  both (Fontsource, SIL OFL: free for commercial video).
- Proven pairs: Inter/Inter (clean), Anton + Montserrat (hype), Fraunces + DM Sans (calm),
  Playfair Display + Inter (premium), Poppins/Poppins (playful), Space Grotesk + JetBrains Mono (tech).
- **Indic and Arabic scripts:** the compiler adds Noto Sans Devanagari, Bengali, Gurmukhi, Gujarati,
  Tamil, Telugu, Kannada, Malayalam or Arabic as fallbacks when the text contains them. Poppins and
  Mukta have their own Devanagari, so for Hindi-first brands set `fonts.body` to Mukta or Poppins.
- **Emoji** use the system colour-emoji font. Vendored emoji fonts render blank in headless Chrome.
- Fonts fail silently. The compiler preloads every face and logs `font failed to load` as a runtime
  error that `npx hyperframes check` reports.

## Legibility over video

| Background under text | Treatment |
|-----------------------|-----------|
| Dark, uniform | plain light text + soft shadow |
| Mid or busy | light text + shadow + scrim (themes add a bottom gradient behind captions, top gradient behind top graphics) |
| Bright (sky, white wall, light clothing) | text on a card (`card` colour), or captions `box: true` |

`npx hyperframes check` measures WCAG contrast on rendered frames. Aim for ≥ 4.5:1 for card text and
≥ 3:1 for large display text.

## Colour

- One **accent** (highlights, numbers, badges, CTA), plus a text colour, a card colour and semantic
  positive, negative and warning colours. That is the whole theme palette.
- The accent appears in ≤ 15% of frame area. If everything is yellow, nothing is.
- Semantic colours always come with an icon (✓ / ✕ / ⚠): colour-blind viewers and grayscale-ish
  sunlight viewing.
- Grade the footage *before* designing graphics (or not at all). Neon accents on a warm-graded face can
  clash, so pick the accent against the actual footage. Skin tones never get colour-shifted.
- Brand colours: put them in `preferences/brand-kit.md` → `theme_overrides`. Check the accent against
  white text for pill contrast (yellow and lime need `on_accent` near-black).

## Theme token reference (`assets/themes/*.json`)

```json
{
  "name": "clean-educator", "personality": "clean",
  "fonts":  {"display": {"family": "Inter", "package": "@fontsource/inter", "weight": 800},
             "body":    {"family": "Inter", "package": "@fontsource/inter", "weight": 600}},
  "colors": {"text": "#FFFFFF", "shadow": "rgba(0,0,0,0.55)", "accent": "#FFD60A", "on_accent": "#111111",
             "card": "rgba(16,16,20,0.86)", "on_card": "#FFFFFF", "muted": "#B9B9C3",
             "positive": "#30D158", "negative": "#FF453A", "warning": "#FF9F0A", "cover_bg": "#0E0E12"},
  "caption": {"style": "karaoke", "size": 66, "weight": 800, "case": "none", "highlight": "pill", "box": false},
  "title":   {"size": 104, "case": "none", "box": false},
  "shape":   {"radius": 28, "pad": 36},
  "motion":  {"in": 0.35, "out": 0.25, "ease_in": "power3.out", "ease_out": "power2.in",
              "pop": "back.out(1.4)", "stagger": 0.05, "word_pop": 1.08},
  "ambient": {"scrim_top": true, "scrim_bottom": true, "drift_zoom": 0.02, "progress_bar": false}
}
```

`caption.highlight`: `pill` · `color` · `underline` · `none`. `caption.emph`: colour of emphasized caption words
(default = accent; use a lighter tint when the accent is mid-luminance, e.g. pink or blue, so it stays legible over footage). `caption.case` / `title.case`: `none` · `upper` ·
`lower`. Any `@fontsource/<family>` package works for `package` (browse fontsource.org).
