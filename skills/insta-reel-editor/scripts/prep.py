#!/usr/bin/env python3
"""Normalize a raw clip into an edit-friendly mezzanine + ASR audio + contact sheet.

Usage:
  python3 prep.py INPUT --workdir REEL_DIR [--fps auto|30|60|...] [--no-tonemap]

Creates (inside REEL_DIR):
  prep.json                  what was done (fps, size, HDR/VFR flags, paths)
  media/mezz.mp4             constant fps, 1-second GOP (seek-safe), SDR BT.709, 8-bit yuv420p,
                             AAC 48 kHz; vertical 9:16 sources are scaled to exactly 1080x1920
  media/voice16k.wav         16 kHz mono PCM for transcription
  qa/contact_source.jpg      1 thumbnail every N seconds (<= 40 tiles) for a quick visual read
Why: phones record variable frame rate + sparse keyframes + sometimes HDR; all three cause
A/V drift, frozen frames on seek, or washed-out colors later in the pipeline.
"""
from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

from _common import (audio_stream, display_size, ensure_dir, ffprobe_json, has_filter, log, need, parse_rate,
                     run, save_json, video_stream)

STANDARD = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]


def pick_fps(src_fps: float, vfr: bool, req: str) -> str:
    if req != "auto":
        return req
    if vfr or src_fps <= 0:
        return "30"
    if src_fps > 60.5:
        return "30"
    best = min(STANDARD, key=lambda s: abs(src_fps - s))
    if abs(src_fps - best) < 0.02:
        return {23.976: "24000/1001", 29.97: "30000/1001", 59.94: "60000/1001"}.get(best, str(int(best)))
    return "30"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--fps", default="auto", help="auto keeps standard constant rates, else conforms to 30")
    ap.add_argument("--no-tonemap", action="store_true", help="skip HDR->SDR tone mapping")
    ap.add_argument("--max-long-side", type=int, default=3840)
    ap.add_argument("--crf", type=int, default=16)
    a = ap.parse_args()
    need("ffmpeg")

    wd = ensure_dir(a.workdir)
    media, qa = ensure_dir(wd / "media"), ensure_dir(wd / "qa")
    info = ffprobe_json(a.input)
    vs, as_ = video_stream(info), audio_stream(info)
    if not vs:
        raise SystemExit("prep.py needs a video stream (for audio-only, build picture from stills/b-roll).")
    w, h = display_size(vs)
    r_fps, avg_fps = parse_rate(vs.get("r_frame_rate")), parse_rate(vs.get("avg_frame_rate"))
    vfr = bool(r_fps and avg_fps and abs(r_fps - avg_fps) / max(r_fps, 1) > 0.01)
    fps = pick_fps(avg_fps or r_fps, vfr, a.fps)
    transfer = (vs.get("color_transfer") or "").lower()
    hdr = transfer in ("smpte2084", "arib-std-b67") or (vs.get("color_primaries") or "").lower() == "bt2020"

    vf = []
    if hdr and not a.no_tonemap:
        if has_filter("zscale") and has_filter("tonemap"):
            vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
                      "zscale=t=bt709:m=bt709:r=tv")
            log("[prep] HDR source -> tone-mapping to SDR BT.709 (hable)")
        else:
            log("[prep] WARNING: HDR source but this ffmpeg lacks zscale/tonemap; colors may look washed out. "
                "Install an ffmpeg build with libzimg (e.g. Homebrew ffmpeg) or export SDR from the phone.")
    ratio = w / h if h else 1
    if abs(ratio - 9 / 16) < 0.02:
        vf.append("scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920")
    elif max(w, h) > a.max_long_side:
        if w >= h:
            vf.append(f"scale={a.max_long_side}:-2:flags=lanczos")
        else:
            vf.append(f"scale=-2:{a.max_long_side}:flags=lanczos")
    vf.append(f"fps={fps}")
    vf.append("format=yuv420p")
    fps_num = eval(fps) if "/" in fps else float(fps)  # noqa: S307 - constant from our own table
    gop = str(max(1, round(fps_num)))

    mezz = media / "mezz.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.input, "-map", "0:v:0"]
    if as_:
        cmd += ["-map", "0:a:0"]
    cmd += ["-vf", ",".join(vf), "-c:v", "libx264", "-preset", "fast", "-crf", str(a.crf),
            "-g", gop, "-keyint_min", gop, "-sc_threshold", "0", "-bf", "2",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-movflags", "+faststart"]
    if as_:
        cmd += ["-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2"]
    cmd += [str(mezz)]
    run(cmd)

    if as_:
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mezz), "-vn", "-ac", "1", "-ar", "16000",
             "-c:a", "pcm_s16le", str(media / "voice16k.wav")])
    else:
        log("[prep] no audio stream: skipped voice16k.wav")

    # contact sheet
    m_info = ffprobe_json(mezz)
    dur = float(m_info["format"]["duration"])
    step = max(1, math.ceil(dur / 40))
    n = max(1, math.ceil(dur / step))
    cols = 8
    rows = max(1, math.ceil(n / cols))
    mw, mh = display_size(video_stream(m_info))
    tw = 216 if mh >= mw else 320
    sheet = qa / "contact_source.jpg"
    base = f"fps=1/{step},scale={tw}:-2"
    label = ",drawtext=text='%{pts\\:hms}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6"
    for extra in (label, ""):
        res = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mezz),
                              "-vf", f"{base}{extra},tile={cols}x{rows}:padding=4:margin=4", "-frames:v", "1",
                              "-q:v", "3", str(sheet)], capture_output=True, text=True)
        if res.returncode == 0:
            break
    m_vs = video_stream(m_info)
    rep = {"input": a.input, "mezz": str(mezz), "duration": dur, "fps": fps, "width": mw, "height": mh,
           "src_width": w, "src_height": h, "hdr_source": hdr, "vfr_source": vfr,
           "has_audio": bool(as_), "contact_sheet": str(sheet), "contact_step_s": step,
           "codec": m_vs.get("codec_name")}
    save_json(rep, wd / "prep.json")
    log(f"[prep] mezz {mw}x{mh} @ {fps} fps, {dur:.2f}s -> {mezz}")
    log(f"[prep] contact sheet ({step}s/tile) -> {sheet}")


if __name__ == "__main__":
    main()
