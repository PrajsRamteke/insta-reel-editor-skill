# Hook & Retention

Instagram's Reels insights measure **skip rate** (the share of viewers who leave in the first 3 seconds)
and show a retention curve ("the flatter the line, the more engaged"). The edit wins or loses on
the opening and on cadence.

## The first 3 seconds

| Rule | Why | How (in this skill) |
|------|-----|---------------------|
| Hook readable on **frame 0** | Frame 0 is the default thumbnail and the first impression while the video buffers | `hook-title` with `start: 0`. The compiler settles it in place instead of fading it from invisible |
| Spoken hook starts within 0.5 s | Lead-in silence is dead air | `auto_edl.py` trims the lead-in to the head pad |
| Say it and show it | Sound-off and sound-on viewers both get it | Hook title paraphrases the spoken line; captions run too |
| No intro, logo sting or "hey guys" | Pure skip fuel | Cut it in the EDL; put branding in a lower-third or not at all |
| Motion or change within 1 s | A static first second reads like a photo | Hook words stagger in, a punch-in on the first cut, or the first word pops |
| Face close and clear | Faces stop thumbs | `reframe` focus on the face; avoid covering it with the hook |

### Hook formulas (fill from the transcript, don't invent claims)

- **Number + outcome/pain:** "*3* breathing mistakes" / "5 stretches for desk back pain"
- **Contrarian:** "Stop doing crunches." / "You're stretching *wrong*."
- **Result first:** "I fixed my sleep in 14 days."
- **Question that names the viewer:** "Wake up tired every day?"
- **Curiosity gap:** "The last one surprised my doctor."
- **Kicker + headline:** kicker = category or warning ("STOP DOING THIS"), headline = promise.

Keep hook titles to **3–7 words**, at most 3 lines, with one accent word (`*word*`).

## Retention devices (the body)

| Device | Implementation | Cadence |
|--------|----------------|---------|
| Visual change | Cut, punch-in, graphic, b-roll or camera push | every 3–5 s; never > 8 s static |
| Jump cuts with punch-ins | `camera.auto_punch_on_cuts` alternates 1.0 ↔ 1.08–1.15 | on cuts ≥ 1.2 s apart |
| Progress cues | `chapter` "2/3", `list-item` dots, `progress_bar` | per list item |
| Open loop | "…and the third one is the one nobody does" | once, early |
| Pattern interrupt | Sticker or keyword pop, b-roll cutaway, SFX on a reveal | every 8–15 s, not more |
| Tight pauses | `--pace tight/natural` | always, but keep rhetorical pauses and laughs |
| Payoff placement | Best graphic on the best line, in the last third | once |

`auto_edl.py` flags ranges longer than 8 s with no cut. Add a punch-in, b-roll or a graphic there.

## Endings: loop or CTA

- **Loop:** the last line flows into the first ("…and that's why most people breathe the wrong way" →
  opening "Most people breathe the wrong way"). Cut tight, with no end card. Replays count as watch time.
- **CTA:** prefer **save** ("Save this for tonight") or **send** ("Send this to someone who…").
  Sends drive non-follower reach. "Follow for more" is the weakest ask. Keep the CTA card 2–3 s, above
  the caption band (`region: lower`), and don't stack a CTA on top of a loop.
- Don't fade to black: a black last frame kills the loop and looks like an error.

## Length

| Goal | Length | Source |
|------|--------|--------|
| Trends, one-liners | 3–15 s | Instagram reels guide (Sep 2026) |
| Tutorials, tips (the sweet spot) | 15–60 s | Instagram reels guide; Socialinsider 2026 (45–60 s had the best engagement rate) |
| Detailed how-tos | 60 s–3 min | Instagram reels guide |
| Reach to non-followers | ≤ 3 min | Instagram Creators FAQ: longer reels are recommended only to followers |

Cut to the length the **content** deserves. Mosseri stated the top signals are watch time, likes per
reach and sends per reach, and a tight 35 s beats a padded 60 s.

## What Instagram says it demotes

From the official ranking post (2023) and the originality updates (2024–2026):

- low-resolution or **watermarked** reels (other apps' logos; your own logo is fine)
- reels with **borders**, muted reels, and **majority-text** reels
- reposted or unoriginal content (aggregators lose recommendation eligibility; minor crops or
  watermarks don't make content original. Voice-over, commentary and edits do)

So keep the person or footage dominant, don't letterbox lazily (prefer `fit-blur` over black bars,
or crop), keep audio on, and publish originals.

## Trial Reels and testing

Professional accounts can post **Trial Reels** (shown to non-followers first). A cheap way to A/B
two hooks: render two variants that differ only in the first 3 s (hook title and cold-open range)
and post one as a trial. `build_hyperframes.py` makes variants easy: copy `reel-plan.json`, change
the hook, rebuild.

## Retention checklist

- [ ] Frame 0 shows the hook text (and the face, if any)
- [ ] First spoken word at ≤ 0.5 s
- [ ] No segment > 8 s without a visual change
- [ ] Count, list or progress visible when the reel is a list
- [ ] Payoff graphic in the last third
- [ ] Ending loops or carries a save/send CTA; no black end frame
- [ ] Length justified by content; ≤ 90 s unless it's a deep how-to
