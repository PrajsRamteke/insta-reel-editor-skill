# Reel Archetypes

Pick one archetype per reel. It sets the skeleton (beat order), the cut pace, caption style,
graphic density and default theme. Mixing archetypes is fine if one leads, for example a listicle
whose second item is a myth vs fact.

## Quick table

| Archetype | Skeleton | Length | Pace (`auto_edl --pace`) | Captions | Graphic density | Signature graphics | Default theme |
|-----------|----------|--------|--------------------------|----------|-----------------|--------------------|---------------|
| **Explainer** (one concept) | Hook → why it matters → how it works → example → takeaway | 30–60 s | natural | karaoke | 1 per 6–8 s | keyword, stat, image/diagram, callout | clean-educator |
| **Listicle** ("3 tips / 5 mistakes") | Hook with count → item 1…N → best item last → CTA | 20–60 s (3–7 items) | tight | karaoke or pop | 1 per item + chapter | hook-title, chapter, list-item, cta | clean-educator / bold-hype |
| **Step-by-step tutorial** | Result first → steps → common mistake → recap | 30–90 s | natural | karaoke | 1 per step | list-item, checklist, callout tip/warning, broll | clean-educator / tech-mono |
| **Myth vs fact** | Myth stated → "actually" → evidence → what to do | 20–45 s | natural | karaoke | 1–2 cover cards | compare, callout myth/fact, stat | clean-educator |
| **Stat / insight** | Shocking number → what it means → why → action | 15–40 s | tight | karaoke | 1–2 | stat, keyword, cta | clean-educator / premium-editorial |
| **Before / after transformation** | After (result) first → before → what changed → how | 15–45 s | natural | phrase or karaoke | 1–3 | compare (before/after), image, stat | playful-pop / clean-educator |
| **Story / personal experience** | Tension line → setup → turning point → lesson | 30–90 s | relaxed | phrase | low (1 per 10–15 s) | quote, keyword, lower-third | premium-editorial / minimal-subtitle |
| **Opinion / hot take** | Claim → reason 1–2 → concession → restated claim | 15–45 s | tight | pop | medium | keyword, hook-title, compare | bold-hype |
| **Q&A / comment reply** | The question on screen → short answer → nuance → CTA | 15–45 s | natural | karaoke | low | hook-title (the question), callout | clean-educator |
| **Demo / exercise / yoga pose** | Name + benefit → setup cue → movement → common error → breath/count cue | 15–60 s | relaxed | phrase (big, few words) | 1 per cue | chapter (pose name), callout warning, checklist, count stat | calm-wellness |
| **Guided practice** (breath, meditation) | Invitation → instruction → silent practice → close | 30–90 s | relaxed (keep silences!) | phrase | very low | checklist, keyword ("Inhale 4"), progress | calm-wellness / minimal-subtitle |
| **Podcast / interview clip** | Best 20–60 s moment → context lower-third → punchline | 20–60 s | natural | karaoke | low | lower-third, quote, keyword | premium-editorial |
| **Announcement / promo** | Hook → what's new → 1–3 benefits → CTA (link in bio) | 10–30 s | tight | pop or karaoke | high | hook-title, keyword, stat, cta | brand theme |

## Archetype notes

### Explainer
The voice carries the logic. Graphics **anchor** the key noun or number (keyword or stat) and show what
words can't (diagram image, b-roll of the thing). Avoid a wall of cards: the face is the trust signal.

### Listicle
- Say the count in the hook and show it ("*3* mistakes"). Show progress with a `chapter` chip
  ("2/3") or `list-item` dots. Progress cues reduce drop-off because viewers know how much is left.
- Put the strongest item **last**, or tease it ("the third one surprised me") for an open loop.
- Each item is one beat. Cut any intro between items: go "Second: …" straight to the point.

### Step-by-step tutorial
Show the end result in the first 2 s (b-roll or image), then the steps. Each step gets a `list-item`
landing on its verb. Add one `callout` warning for the most common mistake. End with a `checklist`
recap that viewers screenshot or save.

### Myth vs fact
Use a `compare` cover card. The myth card appears on the myth sentence, and the fact card on
"actually / the truth is". The myth card dims when the fact lands. Keep the cover under 5 s, then
return to the speaker for the "what to do".

### Before / after
Lead with the after: it is the hook. The compare card's labels become "Before" and "After" (set
`left.label`/`right.label` and icons `x`/`check`, or `clock`/`star`).

### Story
Fewer, slower, bigger. Phrase captions, premium or calm motion, a lower-third once, and maybe one
`quote` card on the lesson line. Keep the emotional pauses (`--pace relaxed`).

### Demo / exercise / yoga pose
- Framing matters more than graphics. Whole-body moves in landscape need `reframe.py --mode fit-blur`
  (a 9:16 crop would amputate limbs), or a careful `track` crop when only the upper body matters.
- Name the pose or exercise with a `chapter` chip at the start of each pose.
- Cue graphics are short and big: "Inhale 4", "Hold 7", "Exhale 8" as `keyword`s on the counting words.
- Safety `callout` warning ("Keep knees soft") lands on the cue word. Don't cover the body part
  being demonstrated: place callouts top or lower.

### Guided practice
Silence is content here. Don't cut the breathing gaps (`auto_edl --pace relaxed --max-gap 3.0`, or
protect ranges by hand). Captions only when speaking. A slow progress bar or a counting `stat` works.

### Podcast / interview
Find the 20–60 s with a complete thought and a punchline (use the hook types in
[content-analysis.md](content-analysis.md)). Use one `lower-third` for the guest's name early, and
`quote` only for the single best line. Two speakers in landscape: `reframe.py --mode track` follows
the dominant face, so review the crop. For fast back-and-forth, `fit-blur` is safer.

## Footage-type adjustments

| Footage | Reframe | Caption placement | Graphics |
|---------|---------|-------------------|----------|
| Vertical talking head | `auto` (scale) | default (bottom edge 1240) | `auto` region; face box from `reframe.py` |
| Landscape talking head | `track` | default | `auto` |
| Screen recording (code, app) | `fit-blur --fit-anchor upper`, or crop to the region of interest | default band (below the content) | keyword/callout in the blurred margins |
| Voiceover + b-roll | per clip; `broll` cover | default | heavier graphic density is fine |
| Whole-body exercise | `fit-blur` or `track` with a wide crop | default | top region; never over the body |
| Interview, 2 people | `track` (dominant face) or `fit-blur` | default | lower-third once |
