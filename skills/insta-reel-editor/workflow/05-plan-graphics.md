# 05 · Plan Captions & Graphics

The agent writes **two small files**; the compiler does the rest.

## 1. Captions

```bash
python3 $S/make_captions.py $R/transcript/words.cut.json --out $R/captions.json \
        --style karaoke --keywords "nose,73%,breath" --srt $R/renders/captions.srt
```

- The style follows the theme or personality: `karaoke` (default), `pop` (energetic), `phrase` (calm or
  premium), `minimal` (cinematic). See [patterns/captions.md](../patterns/captions.md).
- Then **open `captions.json` and read the pages**. Fix awkward breaks by moving words between pages,
  set `"emph": true` on the 1–2 key words per sentence, and fix spellings in `display`.
- Fillers are hidden by default (`--keep-fillers` to show them). Trailing commas and periods are stripped
  (`--punct keep` to keep them).

## 2. Reel plan

Write `reel-plan.json` next to the other files. Start from
[templates/reel-plan-examples.md](../templates/reel-plan-examples.md). Schema:
[reference/data-contracts.md](../reference/data-contracts.md). Component catalog:
[patterns/motion-graphics.md](../patterns/motion-graphics.md).

```json
{
  "version": 1,
  "video": "media/vertical.mp4",
  "words": "transcript/words.cut.json",
  "theme": "clean-educator",
  "theme_overrides": {"colors": {"accent": "#FFD60A"}},
  "captions": {"file": "captions.json"},
  "camera": {"auto_punch_on_cuts": true, "punch_scale": 1.1},
  "graphics": [
    {"type": "hook-title", "start": 0, "end": 2.2, "kicker": "Stop doing this", "text": "*3* breathing mistakes"},
    {"type": "list-item", "land_on_src": 25, "until_word_src": 28, "index": 1, "total": 3, "text": "Breathe through your *nose*"},
    {"type": "stat", "land_on_src": 30, "until_word_src": 37, "value": 73, "suffix": "%", "label": "of adults breathe too fast"},
    {"type": "cta", "land_on_src": 48, "end": 14.9, "text": "Save this for tonight", "icon": "bookmark"}
  ],
  "audio": {"music": {"src": "assets/bed.mp3", "gain_db": -20, "duck": true},
            "sfx": [{"preset": "pop", "on_word_src": 30}]}
}
```

### Planning procedure

1. From `beats.md`, take every beat that has a trigger → one graphic each (see
   [director/content-analysis.md](../director/content-analysis.md)).
2. **Anchor timing to words.** Prefer `land_on_src` / `until_word_src`: the source indices you
   already used in `phrases.md` and `beats.md`. They survive re-cuts. `land_on` / `until_word` take
   cut-timeline indices (`words.cut.json`). Secondary timings: `reveal_word_src` (compare) and
   `item_words_src` (checklist). Use absolute `start`/`end` only for the hook (start 0) and for ends
   snapped to cuts.
3. Pick the **region**: `auto` (face-aware) for most; `cover` for compare/quote/diagrams;
   `lower` for CTA; `top` for hook titles only when the face is low in the frame.
4. Check the budget: one hero at a time, a visual change every 3–5 s, and roughly 25% of runtime or
   less as full cover cards.
5. Add the camera: `auto_punch_on_cuts` for talking heads, plus at most 1–2 smooth push-ins on payoff lines.
6. Add sound only for visible events (see [patterns/sound-design.md](../patterns/sound-design.md)).

### Text rules

- Graphic text **paraphrases** the speech in fewer words; it doesn't duplicate the caption.
  Hook 3–7 words, keyword 1–3, list item ≤ 7, callout ≤ 14, compare sides ≤ 10 each.
- `*word*` = accent emphasis (one per text block).
- Sentence case reads faster than ALL CAPS, except where the theme's `title.case` is `upper` (bold-hype).
- Numbers as digits ("73%", "3"), never spelled out on screen.
- Hindi or other scripts are fine: Noto fallbacks are added automatically. Emoji use the system font;
  prefer the built-in icons for anything critical.

## 3. Optional assets

- **B-roll / images:** place files in `assets/` and reference them with `broll` (video, muted,
  `media_start` to pick the moment) or `image`. Keep b-roll at 1.5–4 s, with a cut-in on a word.
- **Music:** `assets/*.mp3` with a licence you own, or leave it out and add Instagram library audio at upload.
- **SFX:** presets `pop`, `tick`, `ding`, `whoosh`, `swoosh-up`, `thud` are synthesized on first use.

Next: build and preview ([06-build-and-preview.md](06-build-and-preview.md)).
