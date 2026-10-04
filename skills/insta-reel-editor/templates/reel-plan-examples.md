# reel-plan.json Examples

Copy the closest example into `<reel folder>/reel-plan.json`, then replace the word indices with real
ones. The examples use **source** indices from `phrases.md` (`*_src` keys), which survive re-cuts.
Cut-timeline keys (`land_on`, `until_word`, `on_word`, `reveal_word`, `item_words`) also work. Full schema:
[reference/data-contracts.md](../reference/data-contracts.md). Components:
[patterns/motion-graphics.md](../patterns/motion-graphics.md).

## 1. Listicle explainer (clean-educator, karaoke)

```json
{
  "version": 1,
  "video": "media/vertical.mp4",
  "words": "transcript/words.cut.json",
  "theme": "clean-educator",
  "captions": {"file": "captions.json"},
  "camera": {"auto_punch_on_cuts": true, "punch_scale": 1.1},
  "graphics": [
    {"type": "hook-title", "start": 0, "end": 2.3, "kicker": "Stop doing this", "text": "*3* breathing mistakes"},
    {"type": "chapter", "land_on_src": 10, "until_word_src": 47, "text": "3 mistakes"},
    {"type": "list-item", "land_on_src": 25, "until_word_src": 28, "index": 1, "total": 3, "text": "Breathe through your *nose*"},
    {"type": "stat", "land_on_src": 30, "until_word_src": 37, "value": 73, "suffix": "%", "label": "of adults breathe too fast"},
    {"type": "list-item", "land_on_src": 41, "until_word_src": 47, "index": 3, "total": 3, "text": "Don't hold your breath when *stressed*"},
    {"type": "cta", "land_on_src": 48, "end": 14.9, "text": "Save this for tonight", "icon": "bookmark"}
  ],
  "audio": {
    "sfx": [
      {"preset": "swoosh-up", "at": 0.0, "gain_db": -12},
      {"preset": "tick", "on_word_src": 25},
      {"preset": "ding", "on_word_src": 32, "gain_db": -12},
      {"preset": "tick", "on_word_src": 41}
    ]
  }
}
```

## 2. Myth vs fact (clean-educator, brand accent)

```json
{
  "version": 1,
  "video": "media/vertical.mp4",
  "words": "transcript/words.cut.json",
  "theme": "clean-educator",
  "theme_overrides": {"colors": {"accent": "#00C2A8", "on_accent": "#00211C"}},
  "captions": {"file": "captions.json"},
  "camera": {"auto_punch_on_cuts": true, "events": [{"at": 19.2, "scale": 1.16, "mode": "smooth", "dur": 0.6}]},
  "graphics": [
    {"type": "hook-title", "start": 0, "end": 2.5, "kicker": "Myth", "text": "Does stretching *prevent* injury?"},
    {"type": "compare", "land_on_src": 14, "until_word_src": 41, "reveal_word_src": 31,
     "left":  {"label": "Myth", "text": "Static stretching before a run prevents injury"},
     "right": {"label": "Fact", "text": "A *dynamic* warm-up does more"}},
    {"type": "stat", "land_on_src": 47, "hold": 2.8, "value": 2.5, "suffix": "x", "label": "more effective warm-up (study)"},
    {"type": "callout", "variant": "do", "land_on_src": 58, "until_word_src": 70, "text": "5 minutes of leg swings + lunges"},
    {"type": "cta", "land_on_src": 74, "hold": 2.6, "text": "Send this to your running buddy", "icon": "send"}
  ],
  "audio": {"music": {"src": "assets/bed.mp3", "gain_db": -21, "duck": true},
            "sfx": [{"preset": "thud", "on_word_src": 14, "gain_db": -9}, {"preset": "ding", "at": 9.8, "gain_db": -12}]}
}
```

## 3. Calm yoga demo (calm-wellness, phrase captions, landscape source → fit-blur)

```json
{
  "version": 1,
  "video": "media/vertical.mp4",
  "words": "transcript/words.cut.json",
  "theme": "calm-wellness",
  "captions": {"file": "captions.json"},
  "camera": {"auto_punch_on_cuts": false, "drift_zoom": 0.03},
  "graphics": [
    {"type": "hook-title", "start": 0, "end": 3.0, "kicker": "60-second reset", "text": "Ease *desk back* tension", "region": "top"},
    {"type": "chapter", "land_on_src": 6, "until_word_src": 40, "text": "Bhujangasana · Cobra"},
    {"type": "keyword", "land_on_src": 18, "hold": 1.6, "text": "Inhale 4", "icon": "breath", "region": "top"},
    {"type": "keyword", "land_on_src": 25, "hold": 1.6, "text": "Exhale 6", "icon": "breath", "region": "top"},
    {"type": "callout", "variant": "warning", "land_on_src": 31, "until_word_src": 38, "text": "Keep your elbows *soft*", "region": "top"},
    {"type": "checklist", "land_on_src": 44, "end": 27.5, "title": "Your 60 seconds",
     "items": ["3 slow breaths", "Lift on the inhale", "Rest in child's pose"], "item_words_src": [46, 49, 53]},
    {"type": "cta", "land_on_src": 52, "end": 31.0, "text": "Save for your next break"}
  ],
  "audio": {"music": {"src": "assets/soft-pad.mp3", "gain_db": -22, "duck": true, "fade_out": 2.0}}
}
```
Captions for this one: `make_captions.py … --style phrase`. Reframe: `reframe.py … --mode fit-blur`
(whole body visible). Pace: `auto_edl.py … --pace relaxed`.

## 4. Captions-only (minimal)

```json
{
  "version": 1,
  "video": "media/vertical.mp4",
  "theme": "minimal-subtitle",
  "captions": {"file": "captions.json"},
  "graphics": []
}
```

## 5. Faceless / text-led reel (no video; b-roll and cards only)

```json
{
  "version": 1,
  "duration": 18.0,
  "theme": "bold-hype",
  "background": "#0B0B0B",
  "graphics": [
    {"type": "hook-title", "start": 0, "end": 3.0, "text": "The *2-minute* rule"},
    {"type": "broll", "src": "assets/desk.mp4", "start": 3.0, "end": 7.5, "layout": "cover"},
    {"type": "keyword", "start": 7.6, "end": 9.4, "text": "START TINY"},
    {"type": "broll", "src": "assets/shoes.mp4", "start": 9.5, "end": 14.0, "layout": "cover"},
    {"type": "cta", "start": 14.2, "end": 18.0, "text": "Send this to a procrastinator", "icon": "send"}
  ],
  "audio": {"voice": "assets/voiceover.wav"}
}
```
Keep frames from becoming "majority text": b-roll carries most of the runtime.
