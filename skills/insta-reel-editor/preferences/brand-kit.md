# Brand Kit

Fill this in once per brand. The skill applies it to every reel through `theme_overrides`, uses the
key terms for transcription, and follows the do/don't list. Keep several brands as several files
(`brand-kit.<name>.md`) and say which one to use.

## Identity

| Field | Value |
|-------|-------|
| Brand / creator name | _e.g. Habuild_ |
| Instagram handle | _@handle_ |
| Audience | _e.g. busy adults 25–45 starting a daily yoga habit_ |
| Voice | _e.g. warm, encouraging, science-backed, never preachy_ |
| Languages | _e.g. English, Hindi (Devanagari), Hinglish_ |
| Base theme | _e.g. calm-wellness_ |

## Theme overrides (pasted into `reel-plan.json → theme_overrides`)

```json
{
  "colors": {
    "accent": "#FFD60A",
    "on_accent": "#111111",
    "card": "rgba(16,16,20,0.86)",
    "text": "#FFFFFF"
  },
  "fonts": {
    "display": {"family": "Inter", "package": "@fontsource/inter", "weight": 800},
    "body": {"family": "Inter", "package": "@fontsource/inter", "weight": 600}
  },
  "caption": {"highlight": "pill"},
  "motion": {"ease_in": "power3.out"}
}
```

Any Fontsource family works (`@fontsource/<name>`, see fontsource.org). Check the accent against
`on_accent` for contrast (yellow and lime need near-black text). For Hindi-first brands, pick a body
font with Devanagari (Mukta, Poppins), or rely on the automatic Noto fallback.

## Brand motion identity

| Constant | Value |
|----------|-------|
| Signature ease (80% of moves) | _e.g. power3.out_ |
| Duration palette (quick / standard / slow) | _e.g. 0.2 / 0.35 / 0.5 s_ |
| Entrance pattern | _e.g. rise 36 px + fade_ |

## Logo & handle

| Field | Value |
|-------|-------|
| Logo file | _path to PNG/SVG, transparent_ |
| Use | _e.g. end card only, or none (preferred: Instagram already shows the handle)_ |
| Placement if used | inside the safe zone, top-right at y ≥ 290, ≤ 160 px wide, 70% opacity |

Your own logo is fine on Reels. Never other apps' watermarks.

## Key terms (ASR spelling): one per line, also save as `keyterms.txt`

```
Habuild
Surya Namaskar
Bhujangasana
pranayama
```

## Recurring copy

| Field | Value |
|-------|-------|
| Default CTA | _e.g. "Save this for your next session"_ |
| Comment-keyword CTA | _e.g. "Comment YOGA for the free plan"_ |
| Disclaimer (health, finance) | _e.g. "Not medical advice. Consult your doctor." Shown as a small end chip if needed_ |

## Do / Don't

- Do: _e.g. show real members, natural light, calm pacing_
- Don't: _e.g. fear-based hooks, before/after body shots, hype music, profanity_
