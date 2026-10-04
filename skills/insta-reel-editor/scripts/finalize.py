#!/usr/bin/env python3
"""Master the delivery file: two-pass loudness on the mix, Instagram-safe H.264 encode, cover image.

Usage:
  python3 finalize.py --video renders/graphics.mp4 [--audio media/mix.wav] --out renders/final.mp4
                      [--lufs -14] [--tp -1.5] [--cover-at 0.0 | --cover-image cover.png] [--crf 18]

Delivery spec (reference/instagram-specs.md): 1080x1920, H.264 High, yuv420p, closed GOP, constant fps
(source fps, 23-60), VBR capped at 20 Mbps (API max 25), BT.709 tags, AAC-LC 48 kHz stereo 128 kbps,
moov atom first (+faststart), no edit lists. Loudness: -14 LUFS integrated, true peak <= -1.5 dBTP
(practitioner convention; Meta publishes no target; -1.5 leaves headroom for AAC overshoot).
Also writes renders/cover.jpg (1080x1920 sRGB JPEG) and renders/final.json (measured numbers).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from _common import (audio_stream, die, ffprobe_json, log, need, parse_rate, run, save_json, video_stream)


def loudnorm_pass1(src: str, I: float, TP: float, LRA: float) -> dict:
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-vn", "-af",
                          f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
    if not m:
        die("loudnorm pass 1 failed:\n" + res.stderr[-800:])
    return json.loads(m.group(0))


def ebur128(path: str) -> dict:
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True)
    out = {}
    for key, rx in (("I", r"I:\s+(-?[\d.]+) LUFS"), ("LRA", r"LRA:\s+(-?[\d.]+) LU"), ("TP", r"Peak:\s+(-?[\d.]+) dBFS")):
        m = re.findall(rx, res.stderr)
        if m:
            out[key] = float(m[-1])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", required=True, help="rendered picture (HyperFrames/ASS/Remotion output)")
    ap.add_argument("--audio", help="mixed audio (mix_audio.py). Default: the video's own audio")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.5)
    ap.add_argument("--lra", type=float, default=11.0)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--maxrate", default="20M")
    ap.add_argument("--audio-bitrate", default="128k")
    ap.add_argument("--cover-at", type=float, default=0.0, help="seconds; the hook frame makes the best cover")
    ap.add_argument("--cover-image", help="use this image as the cover instead (scaled/cropped to 1080x1920)")
    ap.add_argument("--fps", help="force output fps (default: keep the render's fps)")
    a = ap.parse_args()
    need("ffmpeg")

    vinfo = ffprobe_json(a.video)
    vs = video_stream(vinfo)
    if not vs:
        die("no video stream in --video")
    fps_str = a.fps or vs.get("r_frame_rate", "30/1")
    fps = parse_rate(fps_str)
    if not 23 <= fps <= 60.01:
        log(f"[final] fps {fps:.3f} outside Instagram's 23-60: conforming to 30")
        fps_str, fps = "30", 30.0
    asrc = a.audio or a.video
    if not a.audio and not audio_stream(vinfo):
        die("no audio: pass --audio media/mix.wav (or the video has no sound track)")
    vdur = float(vs.get("duration") or vinfo["format"]["duration"])

    p1 = loudnorm_pass1(asrc, a.lufs, a.tp, a.lra)
    ln = (f"loudnorm=I={a.lufs}:TP={a.tp}:LRA={a.lra}:measured_I={p1['input_i']}:measured_TP={p1['input_tp']}:"
          f"measured_LRA={p1['input_lra']}:measured_thresh={p1['input_thresh']}:offset={p1['target_offset']}:"
          "linear=true:print_format=summary")
    log(f"[final] loudness in: {p1['input_i']} LUFS, TP {p1['input_tp']} dBTP -> target {a.lufs} LUFS / {a.tp} dBTP")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    w, h = int(vs["width"]), int(vs["height"])
    vf = []
    if (w, h) != (1080, 1920):
        vf.append("scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920")
        log(f"[final] input is {w}x{h}: scaling/cropping to 1080x1920")
    vf.append("format=yuv420p")
    gop = str(int(round(fps * 2)))
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.video]
    amap = "0:a:0"
    if a.audio:
        cmd += ["-i", a.audio]
        amap = "1:a:0"
    cmd += ["-map", "0:v:0", "-map", amap, "-vf", ",".join(vf), "-r", fps_str,
            "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-maxrate", a.maxrate,
            "-bufsize", str(int(a.maxrate.rstrip("Mm")) * 2) + "M", "-profile:v", "high", "-level:v", "4.2",
            "-g", gop, "-keyint_min", str(int(round(fps))), "-sc_threshold", "0", "-bf", "2",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
            "-af", ln + f",aresample=48000,apad=whole_dur={vdur:.3f}", "-c:a", "aac", "-b:a", a.audio_bitrate, "-ar", "48000", "-ac", "2",
            "-t", f"{vdur:.3f}", "-movflags", "+faststart", "-use_editlist", "0", str(out)]
    run(cmd)

    # cover
    cover = out.with_name("cover.jpg")
    if a.cover_image:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.cover_image, "-vf",
             "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920", "-frames:v", "1",
             "-q:v", "2", str(cover)])
    else:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{a.cover_at:.3f}", "-i", str(out),
             "-frames:v", "1", "-q:v", "2", str(cover)])

    oi = ffprobe_json(out)
    ovs, oas = video_stream(oi), audio_stream(oi)
    meas = ebur128(str(out))
    rep = {"file": str(out), "cover": str(cover), "duration": float(oi["format"]["duration"]),
           "size_mb": round(int(oi["format"]["size"]) / 1e6, 2),
           "video": {"codec": ovs["codec_name"], "profile": ovs.get("profile"), "w": ovs["width"], "h": ovs["height"],
                     "fps": ovs.get("r_frame_rate"), "pix_fmt": ovs.get("pix_fmt"),
                     "bitrate_mbps": round(int(ovs.get("bit_rate", 0) or 0) / 1e6, 2),
                     "duration": float(ovs.get("duration", 0))},
           "audio": {"codec": oas["codec_name"], "rate": oas.get("sample_rate"), "channels": oas.get("channels"),
                     "duration": float(oas.get("duration", 0)), **meas}}
    save_json(rep, out.with_name(out.stem + ".json"))
    log(f"[final] {out}: {rep['video']['w']}x{rep['video']['h']} {rep['video']['fps']} {rep['video']['codec']} "
        f"{rep['video']['bitrate_mbps']} Mbps, {rep['size_mb']} MB | audio {meas.get('I')} LUFS, TP {meas.get('TP')} dBTP"
        f" | cover -> {cover}")


if __name__ == "__main__":
    main()
