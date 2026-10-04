# 07 · Audio

Audio is where generated videos sound cheap. The voice is the product: clear, present, consistent.
Music and SFX are seasoning.

## Mix

```bash
python3 $S/mix_audio.py $R/reel-plan.json            # → $R/media/mix.wav (48 kHz PCM, pre-loudness)
```

Configured in `reel-plan.json → audio` (all optional):

```json
"audio": {
  "voice": "media/cut.mov",
  "voice_chain": "clean",
  "denoise": false,
  "music": {"src": "assets/bed.mp3", "gain_db": -20, "duck": true, "duck_ratio": 8, "fade_in": 0.6, "fade_out": 1.5},
  "sfx": [
    {"preset": "swoosh-up", "at": 0.0, "gain_db": -12},
    {"preset": "pop", "on_word_src": 30, "gain_db": -9},
    {"preset": "tick", "on_word_src": 25, "gain_db": -8},
    {"src": "assets/custom-hit.wav", "at": 9.4, "gain_db": -6}
  ]
}
```

- **Voice source:** defaults to `media/cut.mov` (lossless PCM) when it exists, else the plan's `video`.
  Set `audio.voice` for a separate voiceover. With no voice at all (music-only reel) the length comes
  from the plan's `duration` and the music becomes the soundtrack.
- **SFX anchors:** `on_word_src` (source index, survives re-cuts) or `on_word` (cut index).
- **Voice chain `clean`:** high-pass 80 Hz, −1.5 dB at 250 Hz (mud), +2 dB at 3.2 kHz (presence), de-ess,
  3:1 compression. `none` leaves it untouched. Any string is treated as a raw ffmpeg `-af` chain.
- **Denoise** (`afftdn`) only for audible hiss or hum. It dulls clean recordings.
- **Music** loops to length. Its loudness is measured and set `gain_db` below the voice
  (−18 to −22 dB is a bed). It ducks further under speech via sidechain compression, with fades in and out.
- **SFX** at `at` seconds or `on_word` (cut-timeline index; starts `lead` 0.03 s early). Presets are
  synthesized and license-free (`make_sfx.py`).

## Levels (targets)

| Element | Target | Notes |
|---------|--------|-------|
| Final mix | **−14 LUFS integrated**, true peak ≤ −1.5 dBTP, LRA ≤ 11 | applied in `finalize.py` (two-pass loudnorm) |
| Music bed under speech | 18–22 dB below the voice; ducks a further 4–8 dB while talking | sources disagree (4–5 dB vs 15–20 dB under); a bed should never compete with consonants |
| Music alone (intro or outro, no speech) | up to 6–10 dB below the voice level | fade it under the CTA |
| SFX | −6 to −12 dB | felt, not noticed; never louder than speech |

Meta publishes no LUFS target for Reels. −14 LUFS / −1 dBTP is the cross-platform convention.
Mastering louder gains nothing (platforms normalize) and costs dynamics.

## Music policy

- **Business accounts** may only use Meta's Sound Collection in-app, and copyrighted music can get a
  reel muted. Muted reels are not recommended.
- Options, in order of safety: (1) no music, adding Instagram library audio when posting (the user
  picks a track and volume in the app; trend-eligible); (2) a royalty-free or owned track mixed here;
  (3) silence plus a good voice. Never rip commercial songs.
- If the user will add in-app music, export **without** music and keep the voice at −14 LUFS. In the
  app, set the added track's volume low (about 10–20%).

## Checks

`finalize.py` prints measured loudness and `verify_reel.py` gates it. You can't listen, so report
numbers instead: integrated LUFS, true peak, and any section where music-only parts jump more than
6 LU above speech (`ffmpeg -i final.mp4 -af ebur128 -f null -` shows momentary values).
