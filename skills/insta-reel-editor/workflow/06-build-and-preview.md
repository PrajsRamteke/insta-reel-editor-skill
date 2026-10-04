# 06 · Build & Preview

## Build (HyperFrames, the default engine)

```bash
python3 $S/build_hyperframes.py $R/reel-plan.json          # → $R/composition/
cd $R/composition
npx hyperframes check                                        # lint + runtime + layout + contrast gate
npx hyperframes snapshot --at 0,2.5,6,10,14                  # PNG stills in composition/snapshots/
npx hyperframes preview                                      # Studio in the browser (optional)
```

The compiler:
- validates the plan (types, required fields, ids, word indices) and resolves `land_on`/`until_word`
- trims small hero overlaps and warns about reading-time and overlap problems
- vendors GSAP and the theme fonts (Fontsource, OFL) plus Noto fallbacks for Indic or Arabic text, from
  an npm cache (`~/.cache/insta-reel-editor/npm`; first run needs network)
- hard-links the A-roll and assets into `composition/assets/`
- writes `index.html` (one paused GSAP timeline), `package.json` scripts and `build-report.json`
  (resolved times, regions, camera segments, face box, warnings)

**Read the build log warnings.** They are the compiler telling you about choreography problems.

## Check

`npx hyperframes check` must say **Check passed**. Expected and harmless for compiled reels:
lint *warnings* `nested_structure_needs_subcomposition` and `timeline_track_too_dense` (a Studio
readability hint, not a render problem). Must fix:

| Finding | Meaning | Fix |
|---------|---------|-----|
| Layout `content_overlap` | Two text blocks collide (often a graphic over captions) | change region (`auto`/`lower`), shorten text, or move the graphic in time |
| Contrast `x:1 (need 3:1)` | Text unreadable on its background | use a card background, a different region, or theme `card` alpha ↑ |
| Runtime `[reel] gX cannot avoid the face` | Not enough room above or below the face | `region: "cover"`, shorter text, or move it to a moment with a wider shot |
| Runtime `[reel] font failed to load` | Missing font file | rebuild (it re-vendors); check the theme's `package`/`weight` |
| Any lint *error* | Broken composition | rebuild; if hand-edited, revert to the compiler output |

## Look at it

Read the snapshot PNGs (or contact sheet `snapshots/contact-sheet.jpg`). Check against
[reference/quality-checklist.md](../reference/quality-checklist.md): hook on frame 0, no text over
eyes or mouth, captions clear of graphics, one hero at a time, text inside the safe zones, consistent
personality. Fix in `reel-plan.json` and rebuild. **Never hand-edit `composition/index.html`**: the
next build overwrites it. If you need something the compiler can't do, see "Custom graphics" in
[engines/hyperframes.md](../engines/hyperframes.md).

## GATE 2: preview approval

Show the user 4–6 stills (hook, two key graphics, a caption close-up, the ending) or the Studio URL.
Ask what to change. Map their feedback to the right file:

| Feedback | Change | Rebuild from |
|----------|--------|--------------|
| "Cut X", "too long", "start with Y" | `edl.json` | `render_cut.py` → reframe → captions → build → (after approval) render → `mix_audio.py` → `finalize.py`. Anchors written as `land_on_src`/`on_word_src` survive; re-check any cut-index `land_on`/`on_word` |
| "Wrong word in captions", "bigger captions", "different highlight" | `captions.json` / `theme_overrides.caption` | build |
| "Different colours/font/feel" | `theme` / `theme_overrides` | build |
| "Graphic too early/late, wrong text, remove it" | `reel-plan.json` graphics | build |
| "Covers my face" | region, or `face_box` override | build |
| "Music too loud", "no whoosh" | `reel-plan.json → audio` | `mix_audio.py` + `finalize.py` only |

Rebuild costs about 2 s; check and snapshots about 30–60 s. Iterate freely before the final render.

## FFmpeg + ASS alternative (no browser)

```bash
python3 $S/build_ass.py $R/reel-plan.json --burn $R/media/vertical.mp4 --video-out $R/renders/graphics.mp4
```

This covers captions plus hook-title, keyword, cta and chapter. Other graphic types are skipped with a
warning. Use EDL range `zoom` (`auto_edl.py --alternate-zoom 1.1`) for punch-ins. See
[engines/ffmpeg-ass.md](../engines/ffmpeg-ass.md).
