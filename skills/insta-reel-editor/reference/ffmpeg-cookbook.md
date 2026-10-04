# FFmpeg Cookbook (reel-specific)

Tested recipes behind the scripts, for one-off fixes. `$IN`/`$OUT` are placeholders.

## Inspect

```bash
ffprobe -v error -show_streams -show_format -of json $IN                     # everything
ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate,avg_frame_rate -of csv=p=0 $IN  # VFR if they differ
ffmpeg -i $IN -vf "fps=1,scale=216:-2,tile=8x5" -frames:v 1 sheet.jpg          # contact sheet
ffmpeg -i $IN -af ebur128=peak=true -f null - 2>&1 | tail -12                   # loudness + true peak
ffmpeg -i $IN -af silencedetect=noise=-40dB:d=0.4 -f null - 2>&1 | grep silence # pauses
```

## Normalize (what prep.py does)

```bash
ffmpeg -i $IN -vf "fps=30,format=yuv420p" -c:v libx264 -preset fast -crf 16 -g 30 -keyint_min 30 \
  -sc_threshold 0 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 320k -ar 48000 -ac 2 -movflags +faststart mezz.mp4
# HDR (HLG/PQ) -> SDR, needs libzimg:
-vf "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
```

## Frame-accurate cut of one range (what render_cut.py does per range)

```bash
ffmpeg -ss 12.400000 -i mezz.mp4 -t 3.266667 -vf format=yuv420p -r 30 -c:v libx264 -crf 16 -g 30 \
  -af "afade=t=in:st=0:d=0.03,afade=t=out:st=3.2367:d=0.03" -c:a pcm_s16le -ar 48000 -ac 2 seg_000.mov
printf "file 'seg_000.mov'\nfile 'seg_001.mov'\n" > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy cut.mov
```
`-ss` before `-i` plus a re-encode is frame-accurate. `-c copy` cuts snap to keyframes (frozen or extra
frames). Use durations that are whole frames (`n/fps`) so audio and video stay the same length.

## Reframe

```bash
# static centre crop 16:9 -> 9:16
ffmpeg -i $IN -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920:flags=lanczos" $OUT
# fit with blurred fill (no borders)
ffmpeg -i $IN -filter_complex "[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=-0.12[bg];[b]scale=1080:1920:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" $OUT
# time-varying crop x (reframe.py builds this expression from face keyframes)
-vf "crop=608:1080:'if(lt(t,5.6),296,if(lt(t,6.2),296+176*(3*((t-5.6)/0.6)^2-2*((t-5.6)/0.6)^3),472))':0"
```

## Punch-in for a range (FFmpeg path)

```bash
-vf "crop=trunc(iw/1.1/2)*2:trunc(ih/1.1/2)*2:(iw-iw/1.1)*0.5:(ih-ih/1.1)*0.4,scale=1080:1920:flags=lanczos"
```

## Captions with ASS

```bash
ffmpeg -i vertical.mp4 -vf "ass=captions.ass:fontsdir=fonts_ass" -c:v libx264 -crf 16 -c:a copy out.mp4
```
Run from the folder containing the `.ass` (the filter parses `:` and `\` in paths). Set `PlayResX: 1080`
and `PlayResY: 1920` in the script header, or sizes are relative to 384×288. Colours are `&HAABBGGRR`.

## Overlays

```bash
# place an animation clip (its frame 0) at t=4.2 s
ffmpeg -i base.mp4 -i anim.mov -filter_complex "[1:v]setpts=PTS-STARTPTS+4.2/TB[o];[0:v][o]overlay=0:0:eof_action=pass" -c:a copy $OUT
# logo/handle watermark (your own brand only), 70% opacity, inside the safe zone
ffmpeg -i $IN -i logo.png -filter_complex "[1]format=rgba,colorchannelmixer=aa=0.7,scale=160:-1[l];[0][l]overlay=W-w-90:290" $OUT
```

## Audio

```bash
# two-pass loudness (finalize.py)
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null -     # read measured_* values
ffmpeg -i mix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=-19.2:measured_TP=-3.1:measured_LRA=6.0:measured_thresh=-29.5:offset=0.4:linear=true,aresample=48000" -c:a aac -b:a 128k out.m4a
# duck music under voice
-filter_complex "[1:a]volume=-20dB[m];[m][0:a]sidechaincompress=threshold=0.02:ratio=8:attack=25:release=420[md];[0:a][md]amix=inputs=2:normalize=0"
# voice clean-up
-af "highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3200:t=q:w=1:g=2,deesser=i=0.35,acompressor=threshold=-21dB:ratio=3:attack=8:release=160:makeup=2"
# light denoise (only if hiss is audible)
-af afftdn=nf=-25
# speed 1.1x keeping pitch (avoid; cut content instead)
-filter_complex "[0:v]setpts=PTS/1.1[v];[0:a]atempo=1.1[a]"
```
loudnorm upsamples to 192 kHz internally, so always set `aresample=48000` / `-ar 48000` after it.

## Delivery encode (finalize.py)

```bash
ffmpeg -i graphics.mp4 -i mix.wav -map 0:v -map 1:a -vf format=yuv420p -r 30 \
  -c:v libx264 -preset slow -crf 18 -maxrate 20M -bufsize 40M -profile:v high -level:v 4.2 \
  -g 60 -keyint_min 30 -sc_threshold 0 -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -af "loudnorm=…(pass 2)…,aresample=48000" -c:a aac -b:a 128k -ar 48000 -ac 2 \
  -movflags +faststart -use_editlist 0 final.mp4
ffmpeg -ss 0.6 -i final.mp4 -frames:v 1 -q:v 2 cover.jpg
```

## QA

```bash
ffmpeg -i final.mp4 -vf "blackdetect=d=0.2:pix_th=0.08,freezedetect=n=-60dB:d=2" -an -f null -   # picture faults
ffmpeg -ss 3.2 -i final.mp4 -frames:v 1 -vf "drawbox=y=1500:w=1080:h=420:color=red@0.3:t=fill" f.png
```
