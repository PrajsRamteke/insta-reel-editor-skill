# Choreography: Timing Graphics to Speech

In a reel, the **voice is the clock**. Motion feels intentional when it lands on words and cuts, and
random when it doesn't.

## Land on the word

The entrance should **finish** as the payoff word is spoken:

```
start = word.start − enter_duration        (compiler: "land_on": <cut word index>)
end   = last relevant word.end + 0.35 s     (compiler: "until_word": <index>)  or "hold": seconds
```

- The payoff word is the noun, number or verb that carries the meaning, not the first word of the
  sentence ("seventy-three *percent*" → land on "seventy").
- Early by up to 0.15 s feels anticipatory and good. Late by more than 0.1 s feels laggy and broken.
- Lists: land each item on its key noun or verb, not on "Second,".

## Holds (readable at 1×)

| Content | Minimum hold | Typical |
|---------|-------------|---------|
| Keyword (1–3 words) | 1.0 s | 1.2–1.8 s |
| Hook title (3–7 words) | 1.8 s | 2.2–3.0 s |
| Stat + label | 2.0 s | 2.5–3.0 s |
| List item / callout (5–10 words) | 2.0 s | until the next item, ≤ 5 s |
| Compare card (two short texts) | 3.5 s | 4–5 s |
| Checklist (3 items) | 3.5 s | 4–6 s |
| Rule of thumb | **0.5 s + 0.25 s per word** | the compiler warns below this |

Longer than about 6 s with nothing changing goes stale. Exit, or add a secondary beat (the second
compare card, the next checklist tick).

## One hero at a time

- Hero graphics never overlap. The compiler trims overlaps of 0.8 s or less automatically (the earlier
  graphic exits) and warns about bigger ones.
- Leave at least 0.15 s between one exit and the next entrance; 0.6 s is better between unrelated heroes.
- **Secondary** elements (`chapter` chip, `lower-third`, `sticker`) may coexist with a hero only if
  they sit in a different region and don't animate at the same moment.
- Captions run throughout and are never covered. `lower` graphics sit above the caption band.

## Enter / exit asymmetry

- Exits take 65–75% of the entrance duration (the viewer cares about arrival).
- Entrances decelerate (`*.out`); exits accelerate (`*.in`); on-screen moves use `*.inOut`.
- Same easing family across the reel. Vary start times, not curves.

## Stagger budgets (word-by-word titles, list ticks)

| Pattern | Delay per element | Total budget | Use |
|---------|-------------------|--------------|-----|
| Micro cascade | 0.02–0.04 s | < 0.25 s | title words (energetic) |
| Standard | 0.05–0.08 s | < 0.45 s | title words (clean, calm) |
| Spoken cadence | each item on its own word | whatever speech takes | checklists, list reveals |

Total decorative stagger stays under 0.5 s. Anything longer should follow speech instead.

## Cuts and camera

- **Punch-ins happen on cuts** (hard `set`, no tween): alternate 1.0 ↔ 1.08–1.15 so a jump cut reads
  as a deliberate camera change. Skip cuts closer than 1.2 s to the previous punch.
- **Smooth push-ins** (0.4–0.8 s, `power2.inOut`) emphasise a payoff line. At most 1–2 per reel.
- **Don't move the camera while a graphic enters.** If a cut and a graphic land within 0.3 s,
  either let the graphic land on the cut (aligned, which feels designed) or shift the graphic to its word.
- **Drift** (+2–3% scale over 5 s, linear) keeps static talking heads alive. Restart it at each
  cut so it doesn't accumulate.

## Graphic exits on cuts

When a graphic's end falls within 0.2 s of a cut, snap the end to the cut: the cut "takes" the
graphic away. Set `end` to the cut time from `edl.resolved.json` → `cuts`.

## The 1/3 rules (adapted)

- **Distance:** no element travels more than 1/3 of the frame width (360 px) in one move. Entrances
  use 18–54 px offsets. Big travels need an arc or a mask reveal instead.
- **Density:** with 3 or more elements on screen (e.g. checklist items), at most 1/3 animate at once.

## Sound sync

- Each SFX ties to a **visible** event (a pop as a keyword lands, a tick on a checklist item, a whoosh
  as b-roll cuts in), timed `lead` ≈ 0.03 s before the visual contact frame.
- 8 well-placed effects in 30 s feel designed; 20 feel cheap. See
  [patterns/sound-design.md](../patterns/sound-design.md).

## Choreography recipes

### Hook (0–3 s)
1. Frame 0: kicker chip plus headline already visible, settling from 106% → 100% (0.35 s).
2. 0.0–0.5 s: first caption page fades in (0.10 s), active word highlighted.
3. On the first cut (≈ 1.5–3 s): punch-in to 1.10; the hook title exits 0.25 s before or on the cut.

### List item (per beat)
1. Badge pops (scale 0.4 → 1, `back.out(2)`) 0.05 s after start.
2. Text slides in from −30 px, 0.12 s after start.
3. Progress dots show N/total. A `tick` SFX on land.
4. Exit on the next item's start (trimmed automatically) or on a cut.

### Stat
1. The card enters on the number word; count-up over 0.8–1.1 s (`power2.out`).
2. Label rises 0.2 s after.
3. A soft `ding` when the count completes (≈ `start + 1.0`).

### Myth vs fact (cover)
1. The cover backdrop fades to 94% (0.25 s) as the myth sentence starts.
2. The myth card enters; the fact card enters on "actually / the truth" (`reveal_at`); the myth dims to 55%.
3. The backdrop fades out; back to the speaker for "what to do".
