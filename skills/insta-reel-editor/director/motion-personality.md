# Motion Personality

Choose **one** personality per reel and apply it everywhere: graphics, captions, camera and sound.
A consistent personality is what makes edits feel *designed*. Mixed personalities feel templated.
The five personalities extend LottieFiles' four UI archetypes (Playful, Premium, Corporate,
Energetic) for video. "Corporate" becomes **Clean** (educator), and **Calm** is added for wellness
content, where slow, breathing motion is part of the message.

## The five personalities

### Calm (wellness, yoga, breathwork, health education)

| Parameter | Value |
|-----------|-------|
| Enter / exit | 0.60 s / 0.45 s (18 / 14 frames @30) |
| Ease | `sine.out` in, `sine.in` out. Breath-like, no snap |
| Overshoot | 0% |
| Entrance pattern | fade + 18 px rise |
| Captions | `phrase` (4–8 words), soft colour emphasis, no pop |
| Camera | slow drift +3% per 5 s; few punch-ins (only on hard jump cuts) |
| Cut pace | `relaxed`; keep breathing pauses |
| Sound | soft pad or acoustic bed −22 dB under the voice; at most 3 SFX (soft `ding`) |
| Theme | `calm-wellness` |

Avoid bounce, shake, glitch, fast whooshes and hype fonts. If the content says "slow down", the motion
must too.

### Premium (finance, founders, interviews, luxury, stories)

| Parameter | Value |
|-----------|-------|
| Enter / exit | 0.55 s / 0.35 s |
| Ease | `power2.out` with a mask **reveal** (clip-path wipe) |
| Overshoot | 0% |
| Entrance pattern | reveal top-to-bottom + 10 px settle |
| Captions | `phrase` or `minimal`, no word highlight |
| Camera | subtle drift +1.5%; rare smooth push-ins |
| Theme | `premium-editorial`, `minimal-subtitle` |

Generous holds, serif display type, fewer elements, never playful easing.

### Clean (default: explainers, tips, tutorials, education)

| Parameter | Value |
|-----------|-------|
| Enter / exit | 0.35 s / 0.25 s |
| Ease | `power3.out` in, `power2.in` out; keyword pops `back.out(1.4)` |
| Overshoot | 0–5% (keywords only) |
| Entrance pattern | slide up 36 px + fade |
| Captions | `karaoke` with an active-word pill |
| Camera | punch-ins on cuts (1.10), drift +2% |
| Theme | `clean-educator`, `tech-mono` |

### Playful (lifestyle, food, kids, light tips)

| Parameter | Value |
|-----------|-------|
| Enter / exit | 0.30 s / 0.20 s |
| Ease | `back.out(1.8)` in, `back.in(1.4)` out |
| Overshoot | 10–20%, slight rotation (−3°) on entrances |
| Entrance pattern | scale pop from 70% |
| Captions | `karaoke` pill, word pop 1.10 |
| Theme | `playful-pop` |

Overshoot above 25% looks broken. Not everything bounces: keep body text steady.

### Energetic (fitness, motivation, hot takes, trends)

| Parameter | Value |
|-----------|-------|
| Enter / exit | 0.20 s / 0.15 s |
| Ease | `expo.out` in, `power3.in` out; pops `back.out(2.2)` |
| Overshoot | 15–30% |
| Entrance pattern | snap pop, uppercase condensed type |
| Captions | `pop`, 1–3 words, uppercase, 80–90 px |
| Camera | punch-ins on every cut ≥ 1.2 s apart (1.12–1.15) |
| Cut pace | `tight` |
| Theme | `bold-hype` (progress bar on) |

Max energy everywhere means nothing stands out. Reserve the biggest pop for the payoff.

## Keyword matching

| The user or content says… | Personality |
|---------------------------|-------------|
| calm, mindful, gentle, soothing, wellness, yoga, breath, meditation | Calm |
| elegant, luxury, minimal, editorial, serious, founder, finance | Premium |
| clean, clear, educational, professional, tips, how-to (default) | Clean |
| fun, cute, friendly, colourful, food, family | Playful |
| bold, hype, energetic, gym, motivation, viral, trend | Energetic |

## Brand motion identity

Define three constants per brand (put them in `preferences/brand-kit.md`):

1. **Signature ease**, used for about 80% of moves (e.g. `power3.out`).
2. **Duration palette**: quick / standard / slow.

   | Tier | Calm | Premium | Clean | Playful | Energetic |
   |------|------|---------|-------|---------|-----------|
   | Quick | 0.35 s | 0.35 s | 0.20 s | 0.15 s | 0.10 s |
   | Standard | 0.60 s | 0.55 s | 0.35 s | 0.30 s | 0.20 s |
   | Slow | 0.90 s | 0.80 s | 0.50 s | 0.45 s | 0.30 s |

3. **Entrance pattern**: one way things arrive (rise, reveal, pop or slide).

In this skill these live in the theme's `motion` block (`in`, `out`, `ease_in`, `ease_out`, `pop`,
`stagger`, `word_pop`). Change them once in a custom theme, not per graphic.

## Mixing

- Keep 90% in the primary personality. One moment may borrow another. For example, a calm wellness
  reel may give its single stat a gentle `back.out(1.2)`. Never change mid-reel for no reason.
- Override with `"motion_style": "fade" | "reveal" | "slide" | "pop"` in `reel-plan.json` only when
  the theme is right but its motion isn't. Prefer choosing a different theme.

## Emotion → motion (per beat)

| Emotion of the line | Motion character | Ease | Duration |
|---------------------|------------------|------|----------|
| Curiosity (hook) | quick reveal, slight scale | `power3.out` | 0.3–0.4 s |
| Alarm / warning | sharp, direct, no overshoot; `thud` SFX | `power4.out` | 0.2–0.3 s |
| Relief / solution | rise + settle, a soft `ding` | `sine.out` / `power2.out` | 0.4–0.6 s |
| Delight / surprise | pop with overshoot | `back.out(1.8)` | 0.25–0.35 s |
| Authority / fact | steady slide, no bounce | `power2.out` | 0.35–0.5 s |
| Calm / instruction | slow fade | `sine.inOut` | 0.6–1.0 s |
