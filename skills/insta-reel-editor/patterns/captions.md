# Captions

Captions are the reel's second voice. Meta reported in Nov 2024 that most Reels views are sound-on
(over 75%). Captions still matter: people watch muted in public, and captioned videos are more likely
to be finished. Instagram's own guide says to caption the speech *and* add text overlays for key moments.

## Styles

| Style | Words / page | Lines | Size (theme) | Motion | Highlight | When |
|-------|-------------|-------|--------------|--------|-----------|------|
| `karaoke` | 2–4 (≤ 18 chars/line) | ≤ 2 | 60–66 px, weight 700–800 | page fades in 0.10 s, active word pops 1.06–1.10× | pill (accent bg) or colour | default; tips, explainers |
| `pop` | 1–3 (≤ 14 chars) | 1 | 80–90 px, uppercase, condensed | each word pops on its start (0.14 s, back.out) | colour | energetic, hype, fitness |
| `phrase` | 4–8 (≤ 26 chars/line) | ≤ 2 | 54–62 px, weight 600 | page fades 0.18 s; no per-word motion | none or soft colour | calm, premium, stories |
| `minimal` | 3–6 (≤ 28 chars/line) | ≤ 2 | ~46 px on a translucent box | fade | none | cinematic, footage-first, vlogs |

## Placement

- Bottom edge at **y = 1240** (`captions.bottom`), centred, max width 800 px (x 140–940). That clears
  the right action rail and Meta's bottom-35% zone.
- Screen recordings: reframe with `fit-blur --fit-anchor upper` so the content sits at y 290–900 and the
  default caption band sits below it. Only raise captions (`"captions": {"bottom": 1150}`) when the lower
  frame is busy *and* nothing important is there.
- Captions are a persistent layer: graphics use `auto`, `top`, `middle` or `lower` (which sits above the band).
  The compiler's layout check flags overlaps.
- A bottom legibility scrim (a gradient behind the band) is part of most themes. Turn it off with
  `"ambient": {"scrim_bottom": false}` on clean, dark footage.

## Grouping rules (`make_captions.py`)

Break a page when any of these is true:
1. pause ≥ style threshold (0.30–0.50 s)
2. previous word ends a sentence (`. ! ?`)
3. comma, colon or semicolon plus a pause ≥ 0.2 s (or the page already has 2+ words)
4. word cap, character cap (lines × chars/line) or time cap (1.6–3.5 s) reached

Then improve readability:
- **No dangling function words**: "breathe the / wrong way" becomes "breathe / the wrong way".
- **Orphans**: a lone word after a page joins the previous page when contiguous.
- **Flash guard**: pages under 0.5 s merge into a neighbour when it fits; otherwise they are extended.
- **Timing**: page appears 60 ms before its first word and lingers ≤ 0.5 s, never overlapping the next page.
- **Line split**: balanced two lines, preferring a break after punctuation.

## Emphasis

- Auto: digits, %, currency and number words. Add your own with `--keywords "nose,cortisol"`.
- Edit `captions.json`: `"emph": true` on 1–2 words per sentence (≤ 20% of words overall).
- Emphasized words render in the accent colour. In karaoke, the *active* word gets the pill or colour
  regardless.

## Text hygiene

- Fillers hidden (um, uh, erm, hmm…). Keep "like" or "you know" unless they bloat a page; delete them in
  `captions.json` if so (meaning first, verbatim second).
- Strip trailing `. ,` (default `--punct strip`); keep `?` and `!`.
- Numbers as digits. Fix ASR spellings of names and terms in `display`.
- Uppercase only for `pop` (or themes with `caption.case: upper`). Mixed case reads faster.
- Profanity, if the brand requires it: mask in `display` ("f***").

## Accessibility and contrast

- Text has a soft shadow (and the bottom scrim) by default. On bright, busy footage use the
  `minimal` style box, or set `"captions": {"overrides": {"box": true}}`.
- `npx hyperframes check` runs WCAG contrast on rendered frames and flags failures.
- Avoid red/green-only meaning: icons accompany colour in callouts and compare cards.

## SRT for other platforms

`make_captions.py --srt renders/captions.srt` writes the same pages as SRT (for YouTube Shorts uploads,
accessibility, or translation). Instagram itself has no SRT upload for Reels. If the reel has burned-in
captions, turn the app's auto-captions off so they don't double up.

## Translated or bilingual captions

1. Translate page by page (keep page timing). Edit `display` in a copy, `captions.hi.json`.
2. Check line length: Devanagari renders wider. Drop to 3 words per page or use `phrase` with 2 lines.
3. Fonts: the compiler adds Noto Sans Devanagari, Bengali, Tamil and others automatically when it sees those scripts.
