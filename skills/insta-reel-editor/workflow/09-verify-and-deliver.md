# 09 · Verify & Deliver

Verify the **rendered file**, not the plan. Plans are intentions; renders are facts.

## 1. Machine checks

```bash
python3 $S/verify_reel.py $R/renders/final.mp4 --transcribe-check     # exit 1 if any FAIL
```

| Check | Pass condition |
|-------|----------------|
| Container | moov before mdat (faststart) |
| Picture | 1080×1920, H.264/HEVC, yuv420p, constant 23–60 fps, ≤ 25 Mbps, BT.709 SDR |
| Audio | AAC ≤ 48 kHz, ≤ 2 ch; A/V durations within 0.1 s (AAC priming of 21–64 ms is normal) |
| Duration | 3 s–15 min; warns above 3 min (non-follower reach) |
| Loudness | −14 ± 1 LUFS (warn to ± 2.5), true peak ≤ −1 dBTP |
| Dead air | no silence ≥ 1.2 s (warn) |
| Picture faults | no black ≥ 0.2 s, no frozen picture ≥ 2 s (warn) |
| Words | re-transcription ≥ 95% similar to `words.cut.json` (missing = clipped, extra = ghost) |

It writes `qa/report.md`, `qa/report.json`, `qa/frames/*.png` and **`qa/verify_sheet.jpg`**: frames
at frame 0, the hook, every graphic's midpoint, just after cuts, sample caption pages and the last
frame, with the UI zones drawn (red = UI covers this, orange = conservative/ads margin, cyan
outline = 3:4 grid crop).

## 2. Look (required)

Read `qa/verify_sheet.jpg` and answer each question with yes or no:

- [ ] Frame 0: is the hook readable, and the face visible if there is one?
- [ ] Is no text inside red or orange zones, and nothing under the right rail?
- [ ] Is no graphic over the eyes or mouth?
- [ ] Are captions readable (contrast, size) and never covered?
- [ ] Is there one hero graphic per frame, in a consistent style?
- [ ] After cuts: no flash, no mismatched punch-in, no frozen frame?
- [ ] Does the last frame loop or show the CTA, and is it not black?

## 3. Critic pass (for anything the user will publish)

Spawn one fresh subagent with the final file path, `qa/verify_sheet.jpg`, `beats.md` and the brief.
Brief it to **roast, not praise**: a verdict, ranked problems with timecodes and evidence, and the
5 fixes to do first. Fresh eyes catch what the author stopped seeing (an unreadable 30 px label, a
payoff line cut off, a 0.4 s flash).

## 4. Fix loop

Fix → rebuild → re-render → re-verify. **At most 3 loops.** If issues remain after 3, deliver with
an honest list of what's left and why.

## 5. Deliver

- Final file: `renders/final.mp4`. Cover: `renders/cover.jpg`. Optional `renders/captions.srt`.
- If the user's folder is connected, write the deliverables there (next to the source) and name them
  in one sentence.
- Report in 3–5 lines: length, what was cut, look (theme and captions), QA status and anything flagged.
  Add a suggested Instagram caption (first line equals the hook) and up to 5 hashtags if the user wants them.

## 6. Persist

Append a session entry to `project.md` ([templates/project-log.md](../templates/project-log.md)):
strategy, decisions with reasons, QA numbers and anything outstanding. If the user expressed a
**standing** preference during the session ("always use this green", "never add music"), offer to
save it to `preferences/user-preferences.md` or `brand-kit.md`.
