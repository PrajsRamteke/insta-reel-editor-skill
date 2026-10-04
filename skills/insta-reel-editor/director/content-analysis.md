# Content Analysis: Transcript → Beat Sheet

The transcript decides what the reel is about, where it cuts and what the graphics say. Read
`transcript/phrases.md` (from `pack_transcript.py`), not raw JSON. It gives phrase-level lines with
`[start-end] #first-#last` word indices, fillers in `{braces}`, pauses `⟨0.9s⟩`, retake candidates
and graphic cues.

## Step 1: Classify

Answer in one line each (they go to the top of `beats.md`):

| Question | Options | Consequence |
|----------|---------|-------------|
| Footage type | talking head · voiceover + b-roll · screen recording · demo/exercise · interview/podcast · vlog | Reframe mode, b-roll needs, caption position |
| Archetype | see [reel-archetypes.md](reel-archetypes.md) | Structure, pace, graphic density, default theme |
| Audience promise | "learn X", "avoid Y", "feel Z" | Hook wording and CTA |
| Emotion arc | e.g. concern → relief → motivation | Personality, music, easing |
| Language / script | en, hi, Hinglish, … | ASR `--language`, fonts (auto Noto fallbacks) |

## Step 2: Find the hook

Rank the candidate opening lines. The best hook is usually **not** the first sentence the speaker
said ("Hi guys, so today…" is never the hook).

| Hook type | Transcript signal | Example |
|-----------|-------------------|---------|
| Bold claim / contrarian | "most people", "wrong", "stop", "nobody tells you" | "Most people breathe the wrong way." |
| Number promise | a count + a noun | "3 mistakes that ruin your sleep" |
| Pain / mistake | "if you…", "mistake", "why your…" | "If your back hurts after yoga, read this." |
| Result first | an outcome, a time, a before/after | "I fixed my posture in 21 days." |
| Question | ends with "?" | "Why do you wake up tired?" |
| Curiosity gap | "the third one…", "here's what actually…" | "The last one surprised my doctor." |

**Cold open:** if the strongest line is at 0:40, you may move it to 0:00 (a range from later in the
EDL placed first), then cut back into the natural start. Keep it under 3 s, and make sure the reel
later pays it off. Never promise in the hook what the reel doesn't deliver: viewers punish bait by
skipping, which hurts distribution.

## Step 3: Cut into beats

A beat is one idea, usually 3–10 s, separated by a pause, a discourse marker ("first", "but",
"so", "the second thing") or a topic change. For each beat record:

- time range and word indices (from phrases.md)
- **one-line purpose** (hook / context / value / payoff / CTA)
- **trigger** for a graphic, if any (see the table below)
- **payoff word**: the exact word the graphic should land on
- keep / trim / cut decision (tangents, repeats, weaker takes)

## Step 4: Detect graphic triggers

`phrases.md` lists candidates (numbers, ordinals, contrast words, warnings, questions). Confirm
them semantically. Only beats with a real trigger get a graphic.

| Trigger | Typical words | Component | Payoff word |
|---------|---------------|-----------|-------------|
| Count / list structure | "three tips", "first", "step 2", "mistake number" | `list-item` + `chapter` | the item's key noun |
| Number / statistic | digits, "percent", "times", "hours", currency | `stat` | the number itself |
| Contrast / myth | "but actually", "myth", "the truth is", "instead" | `compare` or `callout` myth/fact | the corrected claim |
| Warning | "never", "avoid", "careful", "don't" | `callout` warning / dont | the action word |
| Tip / how-to | "try", "here's how", "do this" | `callout` tip or `checklist` | the verb |
| Key term / verdict | a word the speaker stresses, a defined term | `keyword` | that word |
| Identity | name, title, credential | `lower-third` | the name (once, early) |
| Quote-worthy line | an aphorism, a punchline | `quote` (cover) | the last word |
| Visual reference | "look at this", "like this", "this pose" | `broll` / `image` | demonstrative word |
| Ending | "save this", "follow", "send this to…" | `cta` | the verb |

**Density:** clean/educational reels average one graphic every 4–8 s. Calm or premium reels, one
every 8–15 s. Energetic reels can go every 2–4 s if they are small keywords. Captions run throughout
in every case.

## Step 5: Write `beats.md`

Use [templates/beat-sheet.md](../templates/beat-sheet.md). Example (from a 40 s breathwork explainer):

| # | Time | Words | Purpose | Says | Trigger → graphic | Lands on |
|---|------|-------|---------|------|-------------------|----------|
| 1 | 0.4–2.2 | #0–5 | Hook | "Most people breathe the wrong way." | claim → `hook-title` "*3* breathing mistakes" (frame 0) | — |
| 2 | 4.0–6.2 | #7–13 | Context | "Here are three mistakes you are making." | count → `chapter` "3 mistakes" | "three" #9 |
| — | 7.6–9.3 | #14–19 | (retake) | "First, you breathe through your mouth." | cut: an earlier take of beat 3 | — |
| 3 | 9.8–12.5 | #20–28 | Value 1 | "First, you breathe through your nose…" | list → `list-item` 1/3 | "nose," #25 |
| 4 | 13.5–16.6 | #29–37 | Value 2 + payoff | "Seventy three percent of adults breathe too fast." | number → `stat` 73% | "seventy" #30 |
| 5 | 17.0–20.0 | #38–47 | Value 3 | "{uh} Third, you hold your breath when…" | warning → `list-item` 3/3 | "hold" #41 |
| 6 | 21.0–22.5 | #48–53 | CTA | "Save this and try it tonight." | ending → `cta` "Save for tonight" | "Save" #48 |

**Index spaces:** `beats.md` and `edl.json` use **source** word indices (`words.json`). After
`render_cut.py`, graphics use **cut-timeline** indices from `words.cut.json`. Each cut word keeps its
source index in `src_i`, so translate with a lookup. `reel-plan.json` also accepts `land_on_src` / `until_word_src` and does the lookup for you.

## Step 6: Choose emphasis words for captions

Mark 1–2 words per sentence: numbers, the key noun, the verb of the instruction. Pass them as
`--keywords` to `make_captions.py`, or flip `"emph": true` in `captions.json`. Emphasizing more
than 20% of words means nothing stands out.

## Pitfalls

- **Reading the raw transcript literally.** ASR mishears names and terms. Pass a `--keyterms` file
  (brand terms) and fix spellings in `words.json` before captioning; don't caption errors.
- **Graphics for every sentence.** If you can't name the trigger, there is no graphic.
- **Cold-open bait.** The hook must be paid off inside the reel.
- **Losing the joke or the breath.** Keep laughs, reactions and rhetorical pauses. They are beats too.
