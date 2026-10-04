# Timing & Easing Tables

Video is watched passively at phone distance, so it needs slightly longer durations than UI
micro-interactions (LottieFiles' UI tables are about 1.2–1.5× faster). Think in **frames**.

## Seconds ↔ frames

| Seconds | @24 fps | @30 fps | @60 fps |
|---------|---------|---------|---------|
| 0.033 | 1 | 1 | 2 |
| 0.10 | 2–3 | 3 | 6 |
| 0.15 | 4 | 4–5 | 9 |
| 0.20 | 5 | 6 | 12 |
| 0.25 | 6 | 7–8 | 15 |
| 0.35 | 8 | 10–11 | 21 |
| 0.50 | 12 | 15 | 30 |
| 0.60 | 14–15 | 18 | 36 |
| 1.00 | 24 | 30 | 60 |

## Durations by element (reels)

| Element | Enter | Exit | Hold (min) |
|---------|-------|------|-----------|
| Caption page | 0.10–0.18 s fade (+10 px rise) | 0.08 s | 0.5 s |
| Active-word pop | 0.08–0.09 s up, yoyo back | — | — |
| Pop-style word | 0.14 s scale 0.6 → 1 | — | — |
| Keyword / sticker | 0.20–0.35 s | 0.15–0.25 s | 1.0 s |
| Hook title | 0.3–0.6 s (word stagger 0.03–0.08 s) | 0.15–0.45 s | 1.8 s |
| Card (stat, list, callout) | 0.30–0.60 s | 0.20–0.45 s | 2.0 s |
| Cover backdrop | 0.25 s to 94% | 0.22 s | — |
| Stat count-up | 0.8–1.1 s, `power2.out` | — | — |
| Checklist tick | 0.20–0.25 s, `back.out(2.5)` | — | — |
| Punch-in | 0 (hard set on the cut) | — | ≥ 1.2 s between punches |
| Smooth push | 0.4–0.8 s, `power2.inOut` | — | — |
| B-roll in / out | 0.15–0.18 s fade | 0.15 s | 1.5 s |

Exit = 65–75% of enter. Distance scales duration: < 50 px moves at 0.8×, 100 px 1.0×, 200 px 1.3×.

## Easing families (GSAP ↔ CSS ↔ Remotion)

| Use | GSAP | CSS cubic-bezier (≈ easings.net) | Remotion |
|-----|------|----------------------------------|----------|
| Entrance (default) | `power3.out` | `(0.25, 1, 0.5, 1)` easeOutQuart | `Easing.bezier(0.25, 1, 0.5, 1)` |
| Entrance, softer | `power2.out` | `(0.33, 1, 0.68, 1)` easeOutCubic | `Easing.out(Easing.cubic)` |
| Entrance, punchy | `expo.out` | `(0.16, 1, 0.3, 1)` easeOutExpo | `Easing.bezier(0.16, 1, 0.3, 1)` |
| Breath-like (calm) | `sine.out` / `sine.inOut` | `(0.61, 1, 0.88, 1)` / `(0.37, 0, 0.63, 1)` | `Easing.inOut(Easing.sin)` |
| Pop with overshoot | `back.out(1.4–2.2)` | `(0.34, 1.56, 0.64, 1)` easeOutBack | `spring({damping: 12, stiffness: 200})` |
| Exit | `power2.in` | `(0.32, 0, 0.67, 0)` easeInCubic | `Easing.in(Easing.cubic)` |
| On-screen move / camera push | `power2.inOut` | `(0.65, 0, 0.35, 1)` easeInOutCubic | `Easing.inOut(Easing.cubic)` |
| Progress bar, drift, rotation | `none` (linear) | `linear` | `Easing.linear` |
| Material standard (UI feel) | `CustomEase` | `(0.2, 0, 0, 1)` MD3 | `Easing.bezier(0.2, 0, 0, 1)` |
| Premium / elegant | `power2.out` | `(0.4, 0, 0.2, 1)` | `Easing.bezier(0.4, 0, 0.2, 1)` |

GSAP naming: `power1` = quad, `power2` = cubic, `power3` = quart, `power4` = quint. **Never linear for
spatial motion.** Linear is only for progress, drift and continuous rotation.

## Springs (Remotion / Framer-style)

| Feel | damping | stiffness | Use |
|------|---------|-----------|-----|
| No bounce (premium, calm) | 200 | 100 | `spring({damping: 200})` |
| Standard settle | 18–24 | 250–350 | cards |
| Bouncy (playful) | 10–15 | 150–250 | keyword pops |
| Very bouncy (energetic payoff only) | 5–10 | 100–200 | once per reel |

## Stagger

| Pattern | Per element | Total budget |
|---------|-------------|--------------|
| Title words, energetic | 0.03 s | < 0.25 s |
| Title words, clean | 0.05 s | < 0.45 s |
| Title words, calm or premium | 0.07–0.08 s | < 0.5 s |
| Lists / checklists | on each spoken word | follows speech |

## Overshoot budget

| Context | Overshoot |
|---------|-----------|
| Calm, premium | 0% |
| Clean keyword | 3–5% |
| Playful | 10–20% |
| Energetic payoff | 15–30% |
| Warnings / myths | 0% (firm) |

## Personality palettes (theme `motion` block)

| Personality | `in` | `out` | `ease_in` | `ease_out` | `pop` | `stagger` | `word_pop` |
|-------------|------|-------|-----------|------------|-------|-----------|-----------|
| calm | 0.60 | 0.45 | sine.out | sine.in | power2.out | 0.08 | 1.00 |
| premium | 0.55 | 0.35 | power2.out | power2.in | power2.out | 0.07 | 1.00 |
| clean | 0.35 | 0.25 | power3.out | power2.in | back.out(1.4) | 0.05 | 1.08 |
| playful | 0.30 | 0.20 | back.out(1.8) | back.in(1.4) | back.out(2) | 0.06 | 1.10 |
| energetic | 0.20 | 0.15 | expo.out | power3.in | back.out(2.2) | 0.03 | 1.12 |
