# User Preferences

The skill reads this file **first, every time**, and treats it as the user's standing defaults. A
request in the current conversation always wins. When the user states a new standing preference
("always…", "never…", "from now on…"), offer to update this file. Change only the line it concerns,
and add a dated note in "Change log".

Edit the values in the right-hand column. Leave `default` to let the skill decide per reel.

## Look

| Setting | Value | Options |
|---------|-------|---------|
| Theme | `clean-educator` | `clean-educator` · `calm-wellness` · `bold-hype` · `premium-editorial` · `playful-pop` · `minimal-subtitle` · `tech-mono` · path to a custom theme JSON (see [style-presets.md](style-presets.md)) |
| Personality override | default | calm · premium · clean · playful · energetic |
| Caption style | default (from the theme) | karaoke · pop · phrase · minimal |
| Caption highlight | default (from the theme) | pill · color · underline · none |
| Caption bottom edge (px) | 1240 | 1100–1240 |
| Captions for fillers | hide | hide · show |
| Graphic density | default | low · medium · high |
| Progress bar | default | on · off |
| Use brand kit | yes | yes · no (see [brand-kit.md](brand-kit.md)) |

## Edit

| Setting | Value | Options |
|---------|-------|---------|
| Pace | default (by archetype) | tight · natural · relaxed |
| Target length | default (by content) | e.g. 30–45 s |
| Cut retakes and false starts | yes | yes · ask |
| Cold open (move the best line first) | ask | yes · ask · never |
| Punch-ins on jump cuts | yes | yes · no |
| B-roll | only what I provide | provide-only · suggest · none |

## Audio

| Setting | Value | Options |
|---------|-------|---------|
| Music | none (I add music in the Instagram app) | none · from `assets/` · ask |
| Music level under voice | −20 dB | −16 … −24 dB |
| SFX | minimal | none · minimal · normal |
| Voice clean-up chain | clean | clean · none |
| Loudness target | −14 LUFS / −1.5 dBTP | — |

## Pipeline

| Setting | Value | Options |
|---------|-------|---------|
| Rendering engine | hyperframes | hyperframes · ffmpeg-ass · remotion |
| Transcription engine | auto | auto · mlx · faster-whisper · elevenlabs · deepgram · openai |
| Transcription language | auto | en · hi · … |
| Approvals | ask | ask (strategy + preview gates) · auto (no stops; report decisions at the end) |
| Deliverables | final.mp4 + cover.jpg | + captions.srt · + draft.mp4 |
| Output location | next to the source, in `<slug>-reel/renders/` | any folder |
| Critic subagent before delivery | yes for publishable work | yes · no |

## Copy

| Setting | Value |
|---------|-------|
| Default CTA | Save this for later |
| CTA style | save · send · follow · comment-keyword |
| Suggest an Instagram caption + hashtags | yes |
| Max hashtags | 5 |

## Change log

- (YYYY-MM-DD) Created with defaults.
