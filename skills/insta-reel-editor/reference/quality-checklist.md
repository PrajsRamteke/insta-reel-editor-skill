# Quality Checklist

Use it twice: on preview snapshots (before the final render) and on `qa/verify_sheet.jpg` (after).
Score each line ✓ / ✗. A CRITICAL ✗ blocks delivery.

## Story & retention
- [ ] Hook line chosen deliberately (not just the first sentence); spoken within 0.5 s
- [ ] Hook text readable on **frame 0**, 3–7 words, one accent word
- [ ] Every beat has one purpose; tangents, retakes and false starts removed
- [ ] Visual change every 3–5 s; no stretch > 8 s static
- [ ] Payoff graphic in the last third; ending loops or asks to save/send; no black end frame
- [ ] Length fits the archetype (most land at 15–60 s)

## Cuts & timing
- [ ] No clipped first or last syllables (re-transcription diff ≥ 95%)
- [ ] No audible clicks at cuts; rhetorical pauses and laughs kept
- [ ] Jump cuts disguised (punch-ins or b-roll); punches ≥ 1.2 s apart
- [ ] A/V in sync (durations within 0.1 s; captions on their words)

## Captions
- [ ] On every spoken word that matters; fillers hidden; spellings correct (names, terms)
- [ ] ≤ 2 lines; no page under 0.5 s; no dangling "the / of"
- [ ] Bottom edge at y ≤ 1240; inside x 140–940; never covered by a graphic
- [ ] Emphasis on ≤ 20% of words; contrast passes

## Motion graphics
- [ ] Every graphic has a transcript trigger and lands on its payoff word (±0.15 s)
- [ ] One hero at a time; secondary elements don't animate at the same moment
- [ ] Holds ≥ 0.5 s + 0.25 s per word
- [ ] Nothing over the eyes or mouth; nothing in UI zones (red/orange on the sheet)
- [ ] One personality, consistently applied (eases, durations, entrance pattern)
- [ ] Cover cards ≤ about 25% of runtime; the speaker stays the star
- [ ] No linear easing on spatial motion; exits shorter than entrances

## Audio
- [ ] −14 ± 1 LUFS integrated; true peak ≤ −1 dBTP
- [ ] Voice clear and present; music bed never competes with consonants
- [ ] SFX only on visible events, ≤ about 8 per 30 s (fewer for calm or premium)
- [ ] Music licensed (or left for in-app selection); no muted sections

## Technical / platform
- [ ] 1080×1920, H.264, yuv420p, constant 23–60 fps, ≤ 25 Mbps, BT.709 SDR
- [ ] AAC 48 kHz stereo; `+faststart`; no edit lists
- [ ] Cover: title and face inside x 70–1010, y 420–1250
- [ ] No other apps' watermarks; no borders or letterboxing (use fit-blur)
- [ ] Fonts rendered (no fallback faces); emoji visible

## Severity tiers

**CRITICAL:** text in UI zones · hook unreadable on frame 0 · clipped words · A/V drift > 2 frames ·
loudness off by > 2.5 LU or true peak > −1 dBTP · captions hidden by a graphic · two heroes at once ·
font fallback · another app's watermark · wrong resolution or spec FAIL in `verify_reel.py`.

**HIGH:** graphic without a trigger · text over eyes or mouth · hold shorter than reading time · mixed
personalities · > 8 s static · music fighting speech · cover text outside the grid crop · spelling errors.

**MEDIUM:** no ambient layer · repetitive entrances · ending neither loops nor asks · stagger > 0.5 s ·
overshoot on calm or premium · SFX overuse · emphasis overuse.

## The stranger test

Watch it once muted, as someone who doesn't know the creator. Do you understand the point by the end?
Would you send it to someone? If not, the problem is in the beats (story), not in the graphics.
