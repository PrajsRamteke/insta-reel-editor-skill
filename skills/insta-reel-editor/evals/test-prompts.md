# Evals: Test Prompts & Expected Behaviour

Run each scenario with and without the skill on the same footage, then compare against the rubric
(reference/quality-checklist.md). Good skills beat the no-skill baseline on every row.

## Triggering (the skill should activate)

| Prompt | Should trigger? |
|--------|-----------------|
| "Make this video Instagram-ready" (+ a .mov) | yes |
| "Add captions to my clip and cut the ums" | yes |
| "Turn my podcast into a 30 s reel" | yes |
| "Make a TikTok / YouTube Short from this" | yes (same 9:16 pipeline; mention platform differences) |
| "Write an Instagram caption for my photo" | no (no video editing) |
| "Make an animated logo intro" | no, unless it's for a reel (then it's a custom HyperFrames component) |

## Scenarios

### 1. Educational talking head (vertical, 70 s raw, 3 tips, fillers and one retake)
Expected: preferences read · brief · probe and prep · word-level ASR with QC · phrases.md read ·
beats.md with hook and triggers · retake dropped (earlier take) · fillers cut · strategy gate ·
35–45 s cut · karaoke captions · hook title on frame 0 · 3 list items + one stat landing on words ·
punch-ins on cuts · CTA save · −14 LUFS · verify PASS · contact sheet inspected · project.md written.

### 2. Landscape yoga demo, whole body, calm voice
Expected: `fit-blur` (not a crop that cuts limbs) · `calm-wellness` · `--pace relaxed` with breathing
pauses kept · phrase captions · pose-name chapter chip · breath-count keywords · warning callout placed
away from the body · no bounce or hype SFX.

### 3. Captions only, Hindi speech
Expected: `--language hi` with a multilingual model (never `.en`) · Devanagari captions render (Noto
fallback vendored) · no other graphics · emphasis on numbers · SRT exported on request.

### 4. Feedback round: "start with the 73% line and make the captions bigger"
Expected: read project.md · change only `edl.json` (cold-open range first) and the caption size override ·
rebuild the downstream steps · re-verify · log the session.

### 5. Bad input: music video with no speech
Expected: QC flags no speech · tell the user captions are impossible · offer a text-led or b-roll
reel plan instead · don't invent a transcript.

### 6. No browser available (CI box), captions + title needed fast
Expected: FFmpeg + ASS engine · karaoke captions + hook title burned in · unsupported graphics reported
as skipped · same finalize and verify.

## Output rubric (score 0–2 each)

Hook (frame 0 + spoken ≤ 0.5 s) · cut quality (no clipped words, no clicks) · caption readability and
sync · graphic relevance (triggered, land on words) · layout safety (UI zones, face) · motion consistency
(one personality) · audio (loudness, ducking) · spec compliance (verify PASS) · process (gates,
project.md) · honesty (remaining issues reported).
