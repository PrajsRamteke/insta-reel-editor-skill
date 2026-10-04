# 03 · Edit Decisions (EDL)

Most of the retention gain comes from **cutting fluff**: false starts, repeats, tangents and dead air.
Shaving every breath helps much less. Edit like a person, then let the script cut like a machine.

## 1. Draft the EDL automatically

```bash
python3 $S/auto_edl.py $R/transcript/words.json --out $R/edl.json --pace natural \
        --audio $R/media/mezz.mp4            # refine cut points into real silence
#  --drop 14-19,52     remove word ranges (retakes, tangents, slips) by SOURCE index
#  --keep-fillers      keep um/uh;  --fillers "basically,matlab"  extra filler words
#  --alternate-zoom 1.1  FFmpeg-engine punch-ins on every other range
```

| Pace | Max pause kept | Head pad | Tail pad | For |
|------|----------------|----------|----------|-----|
| `tight` | 0.25 s | 0.08 s | 0.12 s | listicles, hype, fast talkers |
| `natural` | 0.40 s | 0.10 s | 0.16 s | explainers (default) |
| `relaxed` | 0.65 s | 0.14 s | 0.25 s | calm, wellness, stories, guided practice |

The script snaps to word boundaries and never extends into a dropped word. It snaps to the frame grid,
keeps a 0.45 s end-hold after the last word, and merges cuts shorter than 0.12 s. It writes `stats`
(before and after duration, cut count) and `notes` (ranges over 8 s with no cut, outputs over 90 s).

## 2. Make the editorial calls (you, reading `phrases.md` + `beats.md`)

| Call | How |
|------|-----|
| **Retakes / false starts** | Same opening words repeated (listed in phrases.md): **cut the earlier take** (`--drop`). Spoken slates ("cut that", "let me redo") are always cut. |
| **Self-corrections** | "It's 70 — no, 73 percent" → keep only the corrected clause. |
| **Tangents** | Anything that doesn't serve the archetype's skeleton goes, even if it's good. |
| **Cold open (hook lift)** | Move the strongest line's range to the top of `ranges` (EDL order = output order), then continue from the natural start. ≤ 3 s. |
| **Length** | Hit the brief's target ± 15%. Over target: drop the weakest beat, don't speed up speech. |
| **Breaths and pauses** | Keep rhetorical pauses before a punchline (lengthen that range's tail to 0.3–0.6 s). In calm content, keep breathing gaps. |
| **Laughs / reactions** | `(laughs)` events are beats: extend the range past them. |
| **Ending** | End on the payoff or CTA word plus the end-hold. For a loop, cut right after the line that echoes the opening. |

Edit `edl.json` directly for these. Each range is `{"start","end","words":[first,last],"text","reason"}`
in **source** seconds. Ranges play in array order (cold opens are allowed). Keep `reason` short and
honest. It's your audit trail in `project.md`.

## 3. Cut-quality numbers (from practice)

| Parameter | Value | Note |
|-----------|-------|------|
| Head pad before the first kept word | 0.08–0.14 s | raise it if plosives ("p", "b") or the speaker's onset get clipped (some voices ramp up for about 0.18 s) |
| Tail pad after the last kept word | 0.12–0.25 s | ASR word ends drift 50–100 ms early or late |
| Shortest worthwhile cut | 0.12 s | below this, keep the audio continuous |
| Silence ≥ 0.4 s | clean cut point | 0.15–0.4 s works with a visual check; < 0.15 s is mid-phrase and unsafe |
| Boundary audio fade | 30 ms in and out | `render_cut.py` always applies it |
| Longest range without a visual change | 8 s | add a punch-in, b-roll or graphic |

## 4. GATE 1: approve the strategy

Before rendering, send the user the plan (hook, cuts, target length, look; see
[00-intake.md](00-intake.md)). Apply their changes to `edl.json`.

## 5. Render the cut

```bash
python3 $S/render_cut.py $R/edl.json            # --preview for a fast 540p look (crf 28)
```

- Every range is re-encoded on the frame grid (`-ss` before `-i`, re-encode = frame-accurate;
  stream-copy cuts snap to keyframes and freeze). Audio stays PCM. Ranges are joined with concat `-c copy`.
- It verifies that output video and audio durations equal the EDL sum within 1–2 frames.
- It writes `edl.resolved.json`: each range with `out_start`/`out_end`, plus `cuts` (output times of
  every boundary), which feeds the punch-ins and QA frames.
- It writes `transcript/words.cut.json`: words remapped to the cut timeline. Dropped words are removed,
  and each word keeps `src_i`. It warns when a cut edge clipped a word.

**Double check:** after the final render, `verify_reel.py --transcribe-check` re-transcribes the
output and diffs it against `words.cut.json`. Missing words mean a clipped cut; extra words mean a
ghost. This is the only reliable way to catch timing drift in the ASR.

## Hard rules recap

Never cut inside a word · pad every edge · re-encode on the frame grid · 30 ms fades · join with
concat copy · remap words to the output timeline (or re-transcribe the cut) · keep the original untouched.
