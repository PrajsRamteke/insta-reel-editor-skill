# Educational Reel Recipes

Ready-to-adapt beat structures with their graphics. Times are typical. Always anchor graphics to the
real words (`land_on`) from your transcript. Each recipe names a theme, but swap it for the brand's.

---

## 1. "N mistakes / N tips" listicle (30–45 s)

| Beat | Speech pattern | Graphic | Sound |
|------|----------------|---------|-------|
| Hook 0–2.5 s | "Most people do X wrong" / "3 mistakes that…" | `hook-title` start 0, kicker "Stop doing this" | `swoosh-up` at 0 (−12 dB) |
| Context 2.5–5 s | "Here are three…" | `chapter` "3 mistakes" (top-left) | — |
| Item 1 | "First, …" | `list-item` 1/3 lands on the key noun | `tick` on land |
| Item 2 | "Second, … 73%…" | `list-item` 2/3, then `stat` when the number is the point | `ding` at count end |
| Item 3 (best) | "And the biggest one…" | `callout` warning or `list-item` 3/3 | `thud` if negative |
| CTA | "Save this…" | `cta` save | soft `pop` |

Settings: `--pace tight`, karaoke captions, `clean-educator` or `bold-hype`, `auto_punch_on_cuts`.
Keep each item 5–9 s, and put the strongest item last or tease it in the hook.

## 2. Myth vs fact (20–35 s)

| Beat | Graphic |
|------|---------|
| "You've heard that X…" (the myth) | `hook-title` with the myth as a question: "Does *X* really…?" |
| Myth stated in full | `compare` start: left card "Myth" (cover) |
| "Actually…" / "The truth is…" | the same `compare`, with `reveal_word_src` = the word "actually" |
| Evidence ("a 2019 study found 40%…") | `stat` after the cover ends |
| What to do instead | `callout` variant `do` |
| CTA | `cta` send ("Send this to someone who believes this") |

Keep the cover at 4–5 s. Return to the speaker for the evidence: trust comes from the face.

## 3. Step-by-step tutorial (45–75 s)

| Beat | Graphic |
|------|---------|
| Result first (b-roll or image of the outcome) | `broll` cover 1.5–2.5 s + `hook-title` "How to *X* in 3 steps" |
| Step 1…N | `list-item` per step landing on the verb; `chapter` "Step 2/4" for long steps |
| Common mistake | `callout` warning |
| Recap | `checklist` with `item_times` on each spoken step name |
| CTA | `cta` save |

`--pace natural`, `clean-educator` or `tech-mono` (for software). Screen recordings: reframe with
`fit-blur --fit-anchor upper` (content above, captions below).

## 4. Stat explainer (15–30 s)

| Beat | Graphic |
|------|---------|
| The number first: "73% of adults…" | `hook-title` "*73%* of adults do this" OR a `stat` at start 0 |
| What it means | `keyword` on the consequence ("TIRED") |
| Why | `image` diagram or `callout` note |
| What to do | `callout` tip |
| CTA | `cta` |

Use one number per reel. Two numbers compete; a third is noise.

## 5. Exercise / yoga pose demo (20–45 s)

| Beat | Graphic |
|------|---------|
| Pose name + benefit | `chapter` "Bhujangasana · Cobra" + `hook-title` "Fix desk back in *60s*" |
| Setup cue ("place your palms…") | none; let the body be seen (captions only) |
| Breath / count cues | `keyword` "Inhale 4" / "Hold" / "Exhale 6" landing on the count words |
| Common error | `callout` warning "Don't lock your elbows", placed `top` (body stays visible) |
| Hold or repeat | optional `stat` counting seconds (`value: 30`, `suffix: "s"`, `count_dur` = hold length) |
| CTA | `cta` save "Save for your next break" |

`calm-wellness`, `--pace relaxed`, `phrase` captions. Reframe `fit-blur` for full-body landscape.
Never cover the body part being demonstrated. If unsure, region `top`.

## 6. Concept explainer with a diagram (40–60 s)

| Beat | Graphic |
|------|---------|
| Hook question | `hook-title` "Why do you *wake up tired*?" |
| Definition | `keyword` on the term ("CORTISOL") |
| Mechanism | `image` diagram (card) 3–4 s; maybe a 2nd image for step 2 |
| Analogy | captions only (let the voice work) |
| Evidence | `stat` |
| Takeaway | `quote` cover (the one-line rule) |
| CTA | `cta` |

## 7. Q&A / comment reply (20–40 s)

| Beat | Graphic |
|------|---------|
| The question | `hook-title` with kicker "You asked" and the question as the headline (≤ 7 words) |
| Short answer first | `keyword` "YES, BUT…" or `callout` fact |
| Nuance | `list-item`s or captions only |
| CTA | `cta` "Send me your question" (icon `send`) |

---

## Density sanity check (per 30 s)

| Personality | Hero graphics | Cover cards | Punch-ins | SFX |
|-------------|--------------|-------------|-----------|-----|
| Calm | 2–4 | ≤ 1 | 0–3 | ≤ 3 |
| Premium | 2–3 | ≤ 1 | 0–2 | ≤ 2 |
| Clean | 4–6 | ≤ 2 | 4–8 | 4–8 |
| Playful | 4–7 | ≤ 2 | 4–8 | 5–9 |
| Energetic | 5–9 (mostly keywords) | ≤ 2 | 6–12 | 6–10 |

Above this range it reads as a template. Below it, check the "visual change every 3–5 s" rule.
