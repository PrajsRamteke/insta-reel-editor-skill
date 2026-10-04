# 00 · Intake, Brief & Gates

## 1. Load preferences (always)

Read `preferences/user-preferences.md` and `preferences/brand-kit.md`. They answer most questions
before you ask them: theme, caption style, pace, target length, engine, ASR engine, approval mode,
music policy, CTA wording, language and key terms. Explicit requests in the current message win.

## 2. Set up the reel folder

One folder per reel, next to the source (never inside the skill folder; never modify the source):

```
<source dir>/<slug>-reel/
├── brief.md            ← from templates/brief.md
├── project.md          ← session log (templates/project-log.md); read it first on return visits
├── probe.json  prep.json
├── media/              mezz.mp4, voice16k.wav, cut.mov, vertical.mp4, mix.wav
├── transcript/         words.json, phrases.md, words.cut.json
├── beats.md  edl.json  edl.resolved.json  reframe.json  captions.json  reel-plan.json
├── assets/             b-roll, images, music, sfx/
├── composition/        generated HyperFrames project (don't hand-edit; rebuild from the plan)
├── renders/            graphics.mp4, final.mp4, cover.jpg, final.json
└── qa/                 contact sheets, frames, report.md
```

If `project.md` exists, summarise the last session in one sentence and ask whether to continue.

## 3. Look before you ask

Run `probe.py` and `prep.py` (step 01), then transcribe (step 02). Then look at
`qa/contact_source.jpg` and skim `phrases.md`. Questions shaped by the material beat a generic
questionnaire.

## 4. Decision gate: refuse or flag bad input

Stop and tell the user (with a suggestion) when:

| Problem | Detect | Suggest |
|---------|--------|---------|
| No speech, or garbage transcript | `qc.words == 0`, garbage ratio > 20%, mean conf < 0.6 | text-led reel with music; re-record; another ASR engine or language |
| Captions already burned in | visible text in `contact_source.jpg` | ask for the clean original; don't double-caption |
| Under 3 s, or nothing usable | probe duration | Instagram rejects < 3 s |
| Landscape source at ≤ 720p | probe warnings | upscaled crop will be soft; offer `fit-blur` |
| Very quiet or noisy audio | `probe.py --loudness` < −35 LUFS; audible hiss | warn; `mix_audio --denoise`; re-record if speech is unclear |
| Another app's watermark (TikTok, CapCut) | contact sheet | crop it out or use the original; watermarked reels are demoted |
| Multiple speakers talking over each other | transcript speakers | `fit-blur` or a manual crop; captions get busy |

## 5. Brief (fill `brief.md`; ask only for what's missing)

Must-know, inferred when possible:
- **Goal:** educate, grow (reach), sell, community, or brand.
- **Audience** and what they should do after watching (save, send, follow, click link in bio).
- **Archetype** and target **length** (from preferences or content).
- **Look:** theme or personality, brand colours, caption style.
- **Must keep / must cut** moments.
- **Music:** none, user-supplied file, or the Instagram app's library at upload time (often the best
  choice: licensed and trend-eligible; then export with **no music** and leave headroom).
- **Language** of the captions (same as speech, or translated).

Use AskUserQuestion with 1–4 targeted questions when the session is interactive. When unattended,
make the most reasonable choice and state it at the top of your report.

## 6. GATE 1: strategy approval (before cutting)

After transcription and the beat sheet, send a **4–8 sentence plan**:

> "This is a 52 s explainer. I'll open cold on 'Most people breathe the wrong way' (0:41) with a
> '3 breathing mistakes' title, cut the false start at 0:07 and the tangent at 0:30–0:38 (→ ~38 s),
> and use the clean-educator theme with karaoke captions. Graphics: list cards for the 3 mistakes, a
> 73% stat, and a 'Save this' CTA. Jump cuts get punch-ins; a soft music bed is optional. OK?"

Wait for approval, unless `approvals: auto` in preferences or the session is unattended. Record the
decision in `project.md`.

## 7. GATE 2: preview approval (before the final render)

After step 06, show 4–6 snapshot stills (hook, two graphics, a caption close-up, the ending) or the
Studio preview URL. Ask what to change, apply it, rebuild and re-check. The final render and
master happen only after approval.
