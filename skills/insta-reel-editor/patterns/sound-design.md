# Sound Design

Sound is where generated videos sound cheap. Rules that keep it designed:

## 1. Every effect is tied to something visible

| Visible event | Preset | Gain | Timing |
|---------------|--------|------|--------|
| Hook title appears (frame 0) | `swoosh-up` | −12 dB | `at: 0` |
| Keyword / sticker pops | `pop` | −9 dB | `on_word` of the keyword |
| List item / checklist tick | `tick` | −8 dB | `on_word` of the item |
| Stat finishes counting, correct answer | `ding` | −12 dB | `at: stat start + 1.0` |
| Myth / mistake / negative | `thud` | −8 dB | on the myth card |
| B-roll cut-in, cover card in | `whoosh` | −10 dB | `at: start − 0.05` |

Presets are synthesized by `make_sfx.py`: short, soft, license-free. Use your own via `"src"`.
Effects start `lead` 0.03 s before the visible contact, because the attack takes a moment to read as "on beat".

## 2. Fewer is better

- About 8 effects in 30 s reads as designed; about 20 reads as a template.
- Calm and premium: 0–3 effects total. Energetic: up to about 10.
- Never put SFX under every caption word or every cut.

## 3. Music bed

- Sits 18–22 dB under the voice and ducks a further 4–8 dB while speech is present (sidechain in `mix_audio.py`).
- Fade in 0.5–1 s and out 1.5–2 s. Ramp it out before the CTA instead of letting the track's own tail
  run under it.
- Match the personality: calm (pads, acoustic, 60–80 BPM), clean (light lo-fi or corporate pluck),
  energetic (driving 110–130 BPM), premium (sparse piano or strings), playful (ukulele, marimba).
- Generated music defaults to "hype". Offer the user two contrasting beds rather than picking for them.
- Licensing: see [workflow/07-audio.md](../workflow/07-audio.md) (business accounts, Sound Collection,
  in-app music).

## 4. Voice first

- Clean chain: HPF 80 Hz, small mud cut at 250 Hz, +2 dB presence at about 3 kHz, de-esser, 3:1 compression.
- Denoise only when hiss or hum is audible. Over-denoised voice sounds underwater.
- Room echo can't be fully fixed in post. Tell the user (lavalier mic, softer room) instead of over-processing.

## 5. Loudness

Two-pass loudnorm on the **final mix**: −14 LUFS integrated, true peak −1.5 dBTP, LRA 11. Then measure
(`verify_reel.py`). You can't listen, so report numbers: integrated, peak, and any music-only section
that is much louder than the speech.
