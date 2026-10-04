# Engine: Remotion (alternative)

[Remotion](https://www.remotion.dev) renders React components to video. Choose it when the user already
has a Remotion codebase or brand system, or explicitly asks for React.

**License:** Remotion is free for individuals, for-profit companies with **up to 3 employees** and
non-profits. Larger companies need a paid Company License, and reselling a derivative product isn't
allowed (remotion.dev license). Check this before choosing it for a team or company.

For depth, install the official skills: `npx skills add remotion-dev/skills` (`remotion-best-practices`,
`remotion-captions`, `remotion-render`, …).

## Mapping this skill's plan to Remotion

| reel-plan concept | Remotion |
|-------------------|----------|
| canvas | `<Composition id="Reel" width={1080} height={1920} fps={30} durationInFrames={Math.round(duration*30)} />`; use `calculateMetadata` to read the video's duration |
| A-roll | `<Video src={staticFile('aroll.mp4')} />` from `@remotion/media` inside an `<AbsoluteFill>` wrapper that gets the camera scale |
| graphic window | `<Sequence from={Math.round(start*fps)} durationInFrames={…} premountFor={fps}>` |
| enter / exit | `interpolate(frame, [0, inF], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.25, 1, 0.5, 1)})`; exit mirrored at the end |
| pop | `spring({frame, fps, config: {damping: 12, stiffness: 200}})` |
| captions | `captions.json` → map pages to `<Sequence>`s; highlight when `frame/fps` is in [word.start, next.start); or `createTikTokStyleCaptions()` from `@remotion/captions` (words need a **leading space** in `text`, render with `white-space: pre`) |
| fonts | `loadFont()` from `@remotion/google-fonts/Inter` (restrict `weights` and `subsets`) |
| text fit | `fitText({text, withinWidth: 940, fontFamily, fontWeight})` from `@remotion/layout-utils` |
| punch-in | `scale` at cut frames from `edl.resolved.json → cuts` |

## Rules that bite (from Remotion's own skills)

- Drive **every** animation from `useCurrentFrame()`. CSS transitions and animations and Tailwind `animate-*` don't render.
- `interpolate` doesn't clamp by default: always pass `extrapolateLeft/Right: 'clamp'`.
- Use separate `scale`/`translate` CSS properties rather than one `transform` string when animating several.
- Assets in `public/`, loaded via `staticFile()`.
- Transitions (`<TransitionSeries>`) **shorten** the total duration by the transition length; overlays don't.
- Spot-check frames before a full render: `npx remotion render Reel out/frames --frames=0,45,300 --image-format=png`.

## Render, then finish with this skill's scripts

```bash
npx remotion render Reel ../renders/graphics.mp4 --codec=h264 --crf=18 --pixel-format=yuv420p
python3 $S/mix_audio.py $R/reel-plan.json
python3 $S/finalize.py --video $R/renders/graphics.mp4 --audio $R/media/mix.wav --out $R/renders/final.mp4
python3 $S/verify_reel.py $R/renders/final.mp4 --transcribe-check
```

Keep the director rules, safe zones, caption spec and QA identical. Only the rendering layer changes.
