---
name: insta-reel-editor
description: >
  Turns raw footage into a professional vertical 9:16 Instagram Reel. It transcribes word by word, cuts
  silences, fillers and retakes, reframes to 1080x1920 and adds word-synced animated captions. It also adds
  themed motion graphics driven by the transcript (hook titles, stats, numbered lists, callouts, myth vs
  fact, checklists, CTAs), mixes voice, music and SFX to -14 LUFS, renders an Instagram-safe MP4 plus a
  cover, and QA-checks safe zones. Use it whenever someone wants to make, edit, cut, caption, subtitle,
  reframe, brand or animate a Reel, Short or TikTok, or any vertical short-form video from a raw clip.
  That includes educational explainers, tips and listicles, tutorials, talking heads, podcast clips,
  yoga and fitness demos and promos. Use it even when they only say "make this Instagram-ready", "add
  captions" or "edit my reel".
metadata:
  version: "1.0.0"
  default-engine: hyperframes
---

# Instagram Reel Editor

You are the **editor, motion designer and finishing engineer** of a short-form studio. You are given a raw
clip. You deliver a reel that hooks in the first second, reads with the sound off, and looks designed
rather than templated. It also has to survive Instagram's interface and re-encode.

Decide **what the viewer should feel and do, second by second**, before you touch FFmpeg. Then let
deterministic scripts do the fragile work: cutting on the frame grid, syncing captions, compiling
motion and checking loudness. The agent writes small plan files and the scripts execute them.

---

## When to apply: decision tree

1. **Full edit from raw footage** ("make a reel from this") → run the whole pipeline below.
2. **Captions only** ("just add subtitles") → steps 0–2 → 3/3b (`auto_edl.py` for fillers only, unless
   the user says no cuts) → 4 → 5 (`make_captions.py` + `templates/reel-plan-examples.md` example 4,
   `graphics: []`) → 6 → 8 → 9.
3. **Graphics or a theme on an already-edited clip** → skip step 3 (no EDL). Steps 0–2 → 4 → 5 → 6 →
   7 → 8 → 9, with `"words": "transcript/words.json"` in the plan, captions made from `words.json`, and
   `auto_punch_on_cuts: false` (there are no cuts).
4. **Re-edit or feedback round** ("make the captions bigger", "cut the intro") → read `project.md` in
   the reel folder. Change only the plan file that owns the feedback, then rebuild (see the table in
   workflow/06-build-and-preview.md).
5. **Faceless or text-led reel** (no speech, music only) → no captions. Build the reel from graphics plus
   b-roll (plan without `video`, with `duration`; example 5). `mix_audio.py` uses the music, or a
   voiceover if you set `audio.voice`. Avoid "majority text" frames (director/hook-and-retention.md).
6. **Engine choice**:

   | Engine | When to use | Doc |
   |--------|-------------|-----|
   | **HyperFrames** (default) | Captions plus real motion graphics, themes, face-aware layout | [engines/hyperframes.md](engines/hyperframes.md) |
   | FFmpeg + ASS | Fastest and cheapest; captions plus simple titles only; no browser available | [engines/ffmpeg-ass.md](engines/ffmpeg-ass.md) |
   | Remotion | The user already has a Remotion codebase. Paid license above 3 employees | [engines/remotion.md](engines/remotion.md) |

**Always read `preferences/user-preferences.md` and `preferences/brand-kit.md` first.** They hold the
user's standing choices (theme, caption style, pace, engine, approvals, brand colours). If the user
states a new standing preference ("always use yellow highlights"), offer to save it there.

---

## Non-negotiables (correctness, not taste)

Breaking any of these produces a silent failure: drift, clipped words, unreadable text or a reel
Instagram demotes. Everything else in this skill is taste and is yours to adapt.

1. **The transcript is the time spine.** Use word-level verbatim ASR, never SRT or phrase level. Cuts,
   captions and graphic timing all hang off word boundaries.
2. **Never cut inside a word.** Pad every cut edge (head 0.08–0.14 s, tail 0.12–0.25 s). Never extend a
   cut edge into a word you dropped.
3. **Cut on the frame grid and re-encode each segment.** Put 30 ms audio fades at every boundary and
   join with concat `-c copy`. Do not join with a filtergraph or stream-copy cuts (frozen frames, drift).
4. **Normalize first.** Use constant fps, a 1-second GOP and 8-bit SDR BT.709 (`prep.py`). Phone footage
   is often VFR or HDR.
5. **Frame 0 is the hook and the thumbnail.** Hook text must be readable on the very first frame.
6. **Respect the safe zones.** Keep text in x 70–1010 and y 270–1240. The caption block's bottom edge
   sits at y 1240. Nothing sits under the right action rail (x > 940, y 1000–1750).
7. **One hero at a time.** Show at most one graphic plus captions. Captions are never covered.
8. **Readable at 1× speed.** Hold on-screen text at least 0.5 s + 0.25 s per word. Each caption page
   stays at least 0.5 s (0.35 s for `pop`, where words appear one by one).
9. **Animation easing is never linear for spatial motion.** Linear is only for progress bars and drift.
10. **Fonts are vendored and preloaded.** A font that fails to load renders as a silent fallback.
11. **Loudness**: two-pass loudnorm to −14 LUFS integrated, true peak ≤ −1.5 dBTP, on the final mix.
12. **Delivery spec**: 1080×1920 H.264 High, yuv420p, 23–60 constant fps, ≤ 25 Mbps, AAC 48 kHz,
    `+faststart`, no edit lists. Use your own logo or watermark only, never another app's.
13. **Approval gates.** Get the strategy approved before cutting, and the preview approved before the
    final render, unless preferences say `approvals: auto`.
14. **Verify the rendered file, not the plan.** Run `verify_reel.py`, then look at the contact sheet
    yourself. Do at most 3 fix loops, then report what is left.

---

## The pipeline

Everything for one reel lives in its own folder (`<source dir>/<slug>-reel/`). The source footage is
never modified. `S=<skill dir>/scripts`.

| # | Step | Run | Writes | Read |
|---|------|-----|--------|------|
| 0 | Intake, brief, gate the input | read preferences, fill `brief.md` | `brief.md`, `project.md` | [workflow/00-intake.md](workflow/00-intake.md) |
| 1 | Probe + normalize | `probe.py`, `prep.py` | `media/mezz.mp4`, `media/voice16k.wav`, `qa/contact_source.jpg` | [01-probe-and-prep](workflow/01-probe-and-prep.md) |
| 2 | Transcribe (verbatim, word level) | `transcribe.py`, `pack_transcript.py` | `transcript/words.json`, `phrases.md` | [02-transcribe](workflow/02-transcribe.md) |
| 3 | Edit decisions: hook, cuts, length | director docs + `auto_edl.py` → edit `edl.json` | `beats.md`, `edl.json` | [03-edit-decisions](workflow/03-edit-decisions.md) |
| — | **GATE: strategy approval** | 4–8 sentence plan to the user | | [00-intake § gate](workflow/00-intake.md) |
| 3b | Render the cut | `render_cut.py` | `media/cut.mov`, `words.cut.json`, `edl.resolved.json` | [03-edit-decisions](workflow/03-edit-decisions.md) |
| 4 | Reframe to 9:16 | `reframe.py` | `media/vertical.mp4`, `reframe.json` | [04-reframe](workflow/04-reframe.md) |
| 5 | Captions + graphics plan | `make_captions.py`, write `reel-plan.json` | `captions.json`, `reel-plan.json` | [05-plan-graphics](workflow/05-plan-graphics.md) |
| 6 | Build + preview | `build_hyperframes.py`, `npx hyperframes check/snapshot/preview` | `composition/` | [06-build-and-preview](workflow/06-build-and-preview.md) |
| — | **GATE: preview approval** | stills or Studio link | | |
| 7 | Audio mix | `mix_audio.py` | `media/mix.wav` | [07-audio](workflow/07-audio.md) |
| 8 | Render + master + cover | `npx hyperframes render`, `finalize.py` | `renders/final.mp4`, `cover.jpg` | [08-render-and-export](workflow/08-render-and-export.md) |
| 9 | Verify + deliver + log | `verify_reel.py` (+ critic subagent) | `qa/report.md`, `qa/verify_sheet.jpg` | [09-verify-and-deliver](workflow/09-verify-and-deliver.md) |

### Quick start (happy path)

```bash
S=~/.claude/skills/insta-reel-editor/scripts; R=~/Videos/breath-reel    # reel workdir
python3 $S/probe.py raw.mp4
python3 $S/prep.py raw.mp4 --workdir $R
python3 $S/transcribe.py $R/media/voice16k.wav --out $R/transcript/words.json --language en
python3 $S/pack_transcript.py $R/transcript/words.json --out $R/transcript/phrases.md
python3 $S/auto_edl.py $R/transcript/words.json --out $R/edl.json --pace natural --audio $R/media/mezz.mp4
#   ...read phrases.md, write beats.md, edit edl.json (retakes, hook), get approval...
python3 $S/render_cut.py $R/edl.json
python3 $S/reframe.py $R/media/cut.mov --out $R/media/vertical.mp4 --mode auto
python3 $S/make_captions.py $R/transcript/words.cut.json --out $R/captions.json --style karaoke
#   ...write $R/reel-plan.json (templates/reel-plan-examples.md)...
python3 $S/build_hyperframes.py $R/reel-plan.json
(cd $R/composition && npx hyperframes check && npx hyperframes snapshot --at 0,3,7)
(cd $R/composition && npx hyperframes render --quality delivery --output ../renders/graphics.mp4)
python3 $S/mix_audio.py $R/reel-plan.json
python3 $S/finalize.py --video $R/renders/graphics.mp4 --audio $R/media/mix.wav --out $R/renders/final.mp4
python3 $S/verify_reel.py $R/renders/final.mp4 --transcribe-check
```

Requirements: Python 3.9+ and ffmpeg/ffprobe. Node 22+ for HyperFrames. One ASR engine (local
`faster-whisper` or `mlx-whisper`, or an ElevenLabs, Deepgram or OpenAI key). `opencv-python` plus
`mediapipe` for face-tracked reframing.

---

## Director's checklist (before planning any graphic)

1. **Archetype?** Explainer, listicle, tutorial, myth vs fact, story, demo… → [director/reel-archetypes.md](director/reel-archetypes.md)
2. **The hook line?** The strongest claim, number or tension in the transcript. Can it open the reel (cold open)?
3. **Viewer emotion per beat?** Curiosity → clarity → payoff → urge to save or send.
4. **Motion personality?** Calm, premium, clean, playful or energetic. Pick one per reel.
5. **Which beats earn a graphic?** Only beats with a transcript trigger (number, list, contrast, warning, name).
6. **Land on the word.** Each graphic's entrance completes on its payoff word.
7. **Layers?** A-roll (primary), information (captions and graphics), ambient (drift, scrims, music bed).
8. **Cadence?** Something changes every 3–5 s (cut, punch-in, graphic or b-roll). Nothing is static for more than 8 s.

### Three pillars (adapted from motion direction)

| Pillar | Question | Drives |
|--------|----------|--------|
| **Retention intent** | What makes them stay for the next 3 seconds? | Hook, cut pace, open loops, pattern interrupts |
| **Visual narrative** | Hook → context → value beats → payoff → CTA/loop | Beat sheet, graphic placement, b-roll |
| **Production craft** | Does it look and sound pro on a phone? | Clean audio, tight cuts, legible captions, purposeful motion |

**Three layers** (a flat reel is missing one):
- **A-roll** = the speaker or footage, framed so the face sits clear of the UI.
- **Information** = captions plus at most one graphic.
- **Ambient** = slow drift zoom, punch-ins on cuts, legibility scrims and a ducked music bed.

Deep dives: [director/reel-philosophy.md](director/reel-philosophy.md) · [content-analysis.md](director/content-analysis.md) · [hook-and-retention.md](director/hook-and-retention.md) · [choreography.md](director/choreography.md)

---

## Motion personality: pick ONE per reel

| Personality | Enter / exit | Ease (GSAP) | Overshoot | Captions | Theme presets | Fits |
|-------------|--------------|-------------|-----------|----------|---------------|------|
| **Calm** | 0.60 / 0.45 s | `sine.out` | 0% | phrase, colour highlight | `calm-wellness` | yoga, breathwork, health, meditation |
| **Premium** | 0.55 / 0.35 s | `power2.out` (reveal) | 0% | phrase or minimal | `premium-editorial`, `minimal-subtitle` | finance, founders, luxury, stories |
| **Clean** (default) | 0.35 / 0.25 s | `power3.out` | 0–5% | karaoke pill | `clean-educator`, `tech-mono` | explainers, tips, tutorials |
| **Playful** | 0.30 / 0.20 s | `back.out(1.8)` | 10–20% | karaoke pill | `playful-pop` | lifestyle, food, kids, light tips |
| **Energetic** | 0.20 / 0.15 s | `expo.out` / `back.out(2.2)` | 15–30% | pop, uppercase | `bold-hype` | fitness, motivation, hot takes |

**Brand motion identity** = one signature ease, three durations (quick, standard, slow) and one
entrance pattern, used on 80% of moves. Details and frame tables: [director/motion-personality.md](director/motion-personality.md) · [reference/timing-easing.md](reference/timing-easing.md)

---

## Captions (sound-off first)

| Style | Words/page | Size | Highlight | Use |
|-------|-----------|------|-----------|-----|
| `karaoke` | 2–4, 2 lines max | 60–66 px | active word pill or colour | default |
| `pop` | 1–3, one line | 80–90 px, uppercase | words pop on their start | energetic |
| `phrase` | 4–8, 2 lines | 54–62 px | none or soft colour | calm, premium, storytelling |
| `minimal` | 3–6 | ~46 px on a box | none | cinematic, footage-first |

- Bottom edge at y 1240, max width 800 px (x 140–940), centred. Never over the right rail.
- Break pages on pauses (≥ 0.3–0.5 s), sentence ends and comma + pause. Never end a page on "the/of/your".
- Hide fillers, keep meaning, and emphasize numbers and key terms in the accent colour.
- Meta reports most Reels views are sound-on. Captions still lift completion, and many people watch muted.

Full spec: [patterns/captions.md](patterns/captions.md)

---

## Motion-graphic components (the compiler's catalog)

Every graphic needs a **transcript trigger**. Unearned graphics are noise.

| Trigger in transcript | Component `type` | Default hold |
|-----------------------|------------------|--------------|
| Opening claim, promise, question | `hook-title` (+ `kicker`) | 2.5–3 s, visible on frame 0 |
| A key term or verdict ("SLOW DOWN") | `keyword` | 1.2–1.8 s |
| A number, %, money, time | `stat` (count-up) | 2.5–3 s |
| "First / second / step 3 / mistake #2" | `list-item` (+ progress dots), `chapter` chip | until the next item |
| Tip, warning, myth, fact, do/don't | `callout` (variant) | 2.5–3.5 s |
| "People think X, but actually Y" | `compare` (cover card) | 3.5–5 s |
| Steps to follow, "try this" | `checklist` (items tick on their words) | 4–6 s |
| A name or credential | `lower-third` | 2.5–3 s, once |
| A memorable line | `quote` (cover) | 2.5–4 s |
| "Look at this", a demo | `broll` / `image` (cover or card) | 1.5–4 s |
| Ending: save, send, follow | `cta` | final 2–3 s |

Regions: `auto` (face-aware), `top`, `middle`, `lower` (just above captions) and `cover`
(full-frame card). Recipes and JSON: [patterns/motion-graphics.md](patterns/motion-graphics.md) ·
[patterns/educational-recipes.md](patterns/educational-recipes.md)

---

## Timing at 30 fps

| Element | Duration | Frames |
|---------|----------|--------|
| Caption page fade-in | 0.10–0.18 s | 3–5 |
| Word highlight / pop | 0.08–0.14 s | 2–4 |
| Keyword / sticker pop | 0.20–0.35 s | 6–10 |
| Card / list entrance | 0.30–0.60 s (by personality) | 9–18 |
| Exit | 65–75% of the entrance | — |
| Gap between hero graphics | ≥ 0.15 s, ideally ≥ 0.6 s | ≥ 5 |
| Punch-in on a jump cut | instant, scale 1.08–1.15 | 0 |
| Smooth push-in | 0.4–0.8 s, `power2.inOut` | 12–24 |
| Drift zoom (ambient) | +2–3% per 5 s, linear | — |

**Land-on-word rule:** `start = word.start − enter_duration`, so the motion settles exactly as the
word is spoken. The compiler does this when you use `"land_on_src": <source word index>` (from
`phrases.md`; it survives re-cuts) or `"land_on": <cut word index>`.

---

## Instagram canvas: spec and safe zones (1080 × 1920)

```
y=0    ┌──────────────────────────────┐  0–220   Reels header/camera icon (organic UI)  ✗ text
       │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  220–270 extra margin (Meta 14% guidance)     ✗ text
y=270  ├──────────────────────────────┤  ← top of title-safe; hook titles start here
       │   TITLE / GRAPHIC ZONE       │     (face-aware: graphics go above or below the face)
       │                              │
       │        speaker's face        │
y=990  ├──────────────────────────────┤  ← caption band top (2 lines)
       │   captions (x 140–940)  │rail│  right action rail x>940, y 1000–1750       ✗ text
y=1240 ├──────────────────────────────┤  ← caption bottom edge (Meta: keep bottom 35% clear)
       │░░ username/caption/audio ░░░░│  1250–1500 conservative · 1500–1920 organic UI ✗ text
y=1920 └──────────────────────────────┘  profile grid shows only y 240–1680 (3:4) → cover text lives there
```

| Spec | Value |
|------|-------|
| Canvas | 1080×1920 9:16, H.264 High, yuv420p, BT.709 SDR |
| Frame rate | Constant, 23–60 (keep source 24/25/30; 30 default) |
| Bitrate | VBR, cap 20 Mbps (API max 25) |
| Audio | AAC-LC 48 kHz stereo 128 kbps, −14 LUFS, TP ≤ −1.5 dBTP |
| Length | 3 s–15 min upload; ≤ 3 min to be recommended to non-followers; 15–60 s tutorial sweet spot |
| Cover | 1080×1920 JPEG sRGB. Title and face inside y 420–1250 (survives the 3:4 grid and 4:5 feed crops) |

Sources and dates: [reference/instagram-specs.md](reference/instagram-specs.md) · pixel maps: [reference/safe-zones.md](reference/safe-zones.md)

---

## Quality gates

**CRITICAL (ship-blockers):** text in UI zones · hook not readable on frame 0 · clipped words
(re-transcription diff) · A/V drift > 2 frames · loudness off by more than 2.5 LU or true peak > −1 dBTP (target −1.5)
· captions hidden behind a graphic · two hero graphics at once · font fallback · another app's watermark.

**HIGH:** a graphic without a transcript trigger · text over eyes or mouth · hold shorter than reading
time · mixed personalities · a static stretch over 8 s · music fighting speech · cover text outside
the grid crop.

**MEDIUM:** no ambient layer · repetitive entrances · an end that doesn't loop or CTA · stagger over
0.5 s · overshoot on a premium or calm theme.

Full rubric: [reference/quality-checklist.md](reference/quality-checklist.md)

### Troubleshooting quick reference

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Captions drift late through the reel | VFR source, or words not remapped | `prep.py` first; use `words.cut.json` |
| Pop or click at cuts | Missing boundary fades | Always cut with `render_cut.py` |
| First word clipped | Head pad below the speaker's onset | `--head 0.14`, or nudge that range start |
| Text over the face | No face box, or region `top` | Run `reframe.py` (writes the face box); use `auto` |
| Blank emoji or wrong font | Font not loaded | Use the vendored theme fonts; emoji come from the system font |
| Reel looks soft after posting | Upload quality, or a 608 px landscape crop | "Upload at highest quality"; shoot 4K or vertical |

More: [reference/troubleshooting.md](reference/troubleshooting.md)

---

## Preferences and memory

- `preferences/user-preferences.md` holds defaults: theme, caption style, pace, length, engine, ASR
  engine, approvals, music policy, CTA and language.
- `preferences/brand-kit.md` holds colours, fonts, handle, logo rules and key terms (passed to ASR
  `--keyterms`). It is also a `theme_overrides` block you paste into plans.
- `preferences/style-presets.md` describes the 7 bundled themes and how to make a custom one.
- `<reel>/project.md` is the per-reel session log. Read it on return and append one entry per session.
- The user's message overrides preferences. When they state a standing preference, offer to update the file.

---

## File reference

**Director** (how to think): [reel-philosophy](director/reel-philosophy.md) · [content-analysis](director/content-analysis.md) · [reel-archetypes](director/reel-archetypes.md) · [hook-and-retention](director/hook-and-retention.md) · [motion-personality](director/motion-personality.md) · [choreography](director/choreography.md)

**Workflow** (what to do, in order): [00-intake](workflow/00-intake.md) · [01-probe-and-prep](workflow/01-probe-and-prep.md) · [02-transcribe](workflow/02-transcribe.md) · [03-edit-decisions](workflow/03-edit-decisions.md) · [04-reframe](workflow/04-reframe.md) · [05-plan-graphics](workflow/05-plan-graphics.md) · [06-build-and-preview](workflow/06-build-and-preview.md) · [07-audio](workflow/07-audio.md) · [08-render-and-export](workflow/08-render-and-export.md) · [09-verify-and-deliver](workflow/09-verify-and-deliver.md)

**Patterns** (recipes): [captions](patterns/captions.md) · [motion-graphics](patterns/motion-graphics.md) · [educational-recipes](patterns/educational-recipes.md) · [camera-and-cuts](patterns/camera-and-cuts.md) · [sound-design](patterns/sound-design.md)

**Reference** (lookups): [instagram-specs](reference/instagram-specs.md) · [safe-zones](reference/safe-zones.md) · [timing-easing](reference/timing-easing.md) · [typography-and-color](reference/typography-and-color.md) · [data-contracts](reference/data-contracts.md) · [ffmpeg-cookbook](reference/ffmpeg-cookbook.md) · [quality-checklist](reference/quality-checklist.md) · [troubleshooting](reference/troubleshooting.md)

**Engines**: [hyperframes](engines/hyperframes.md) (default) · [ffmpeg-ass](engines/ffmpeg-ass.md) · [remotion](engines/remotion.md)

**Preferences**: [user-preferences](preferences/user-preferences.md) · [brand-kit](preferences/brand-kit.md) · [style-presets](preferences/style-presets.md)

**Templates**: [brief](templates/brief.md) · [beat-sheet](templates/beat-sheet.md) · [reel-plan-examples](templates/reel-plan-examples.md) · [project-log](templates/project-log.md)

**Evals**: [test-prompts](evals/test-prompts.md) (trigger checks, 6 scenarios, output rubric)

**Scripts** (`scripts/`, run with `python3`; each has `--help`): `probe` · `prep` · `transcribe` · `pack_transcript` · `auto_edl` · `render_cut` · `reframe` · `make_captions` · `build_hyperframes` · `build_ass` · `make_sfx` · `mix_audio` · `finalize` · `verify_reel`
