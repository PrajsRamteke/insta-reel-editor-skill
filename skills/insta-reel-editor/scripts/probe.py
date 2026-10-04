#!/usr/bin/env python3
"""Inspect a source video and say what the reel pipeline needs to do with it.

Usage:
  python3 probe.py INPUT [--out probe.json] [--loudness]

Prints a human summary to stderr and writes JSON (stdout or --out) with:
  orientation, display size, fps (+VFR suspicion), HDR flag, audio facts,
  warnings[], and recommended actions (reframe mode, fps, HDR tone-map...).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

from _common import (audio_stream, display_size, ffprobe_json, log, need, parse_rate, rotation_of,
                     save_json, video_stream)

STANDARD_FPS = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]


def classify(w: int, h: int) -> str:
    if not w or not h:
        return "unknown"
    r = w / h
    if abs(r - 9 / 16) < 0.02:
        return "vertical-9x16"
    if r < 1 and abs(r - 3 / 4) < 0.03:
        return "portrait-3x4"
    if r < 1 and abs(r - 4 / 5) < 0.03:
        return "portrait-4x5"
    if r < 0.9:
        return "portrait-other"
    if r <= 1.1:
        return "square"
    return "landscape"


def measure_loudness(path: str) -> dict:
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True)
    txt = res.stderr
    out = {}
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
    if m:
        out["integrated_lufs"] = float(m[-1])
    m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
    if m:
        out["true_peak_dbtp"] = float(m[-1])
    m = re.findall(r"LRA:\s+(-?[\d.]+) LU", txt)
    if m:
        out["lra"] = float(m[-1])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", help="write JSON here instead of stdout")
    ap.add_argument("--loudness", action="store_true", help="also measure EBU R128 loudness (slower)")
    a = ap.parse_args()
    need("ffprobe")

    info = ffprobe_json(a.input)
    fmt = info.get("format", {})
    vs, as_ = video_stream(info), audio_stream(info)
    warnings, actions = [], []
    rep: dict = {"input": a.input, "container": fmt.get("format_name"), "duration": float(fmt.get("duration", 0) or 0),
                 "size_mb": round(int(fmt.get("size", 0) or 0) / 1e6, 2),
                 "bitrate_mbps": round(int(fmt.get("bit_rate", 0) or 0) / 1e6, 2)}

    if not vs:
        warnings.append("No video stream: this is audio only. Use a still/cover image or b-roll as picture.")
    else:
        w, h = display_size(vs)
        r_fps, avg_fps = parse_rate(vs.get("r_frame_rate")), parse_rate(vs.get("avg_frame_rate"))
        fps = avg_fps or r_fps
        vfr = bool(r_fps and avg_fps and abs(r_fps - avg_fps) / max(r_fps, 1) > 0.01)
        transfer = (vs.get("color_transfer") or "").lower()
        primaries = (vs.get("color_primaries") or "").lower()
        hdr = transfer in ("smpte2084", "arib-std-b67") or primaries == "bt2020"
        pix = vs.get("pix_fmt", "")
        bit_depth = 10 if "10" in pix else (12 if "12" in pix else 8)
        orient = classify(w, h)
        rep["video"] = {"codec": vs.get("codec_name"), "width": w, "height": h, "coded": [vs.get("width"), vs.get("height")],
                        "rotation": rotation_of(vs), "fps": round(fps, 3), "r_frame_rate": vs.get("r_frame_rate"),
                        "vfr_suspected": vfr, "pix_fmt": pix, "bit_depth": bit_depth, "color_transfer": transfer or None,
                        "color_primaries": primaries or None, "hdr": hdr, "orientation": orient}

        # --- recommendations ---
        if orient == "vertical-9x16":
            actions.append("reframe: none needed (already 9:16) -> reframe.py --mode auto just scales to 1080x1920")
            if w < 1080:
                warnings.append(f"Vertical source is {w}x{h} (< 1080 wide). It will be upscaled and look soft.")
        elif orient in ("portrait-3x4", "portrait-4x5", "portrait-other", "square"):
            actions.append("reframe: crop-to-fill (track or center) or fit-blur; small crop needed")
        elif orient == "landscape":
            short = min(w, h)
            actions.append("reframe: landscape -> 9:16 needs face tracking (reframe.py --mode track) or fit-blur for "
                           "screen recordings / wide demos")
            crop_w = round(h * 9 / 16)
            if crop_w < 1080:
                warnings.append(f"A 9:16 crop of {w}x{h} is only {crop_w}x{h}; it will be upscaled "
                                f"{1080 / crop_w:.2f}x. Shoot 4K or vertical next time for sharper reels.")
            if short < 720:
                warnings.append("Very low resolution source.")
        if vfr:
            warnings.append("Variable frame rate suspected (common on phones). prep.py converts to constant fps.")
        if fps > 60.5:
            actions.append(f"fps: source is {fps:.0f} fps (slow-mo/high-speed). Conform to 30 (or 60) in prep.py.")
        elif fps and not any(abs(fps - s) < 0.05 for s in STANDARD_FPS):
            warnings.append(f"Unusual frame rate {fps:.3f}; prep.py will conform to 30.")
        if fps and fps < 23:
            warnings.append("Instagram's API requires 23-60 fps; conform to 30.")
        if hdr:
            warnings.append("HDR source (HLG/PQ/BT.2020). prep.py tone-maps to SDR BT.709 so graphics colors and "
                            "Instagram playback stay predictable.")
        if bit_depth > 8:
            actions.append("pix_fmt: convert to 8-bit yuv420p for delivery (prep.py does this).")

    if not as_:
        warnings.append("No audio stream. Captions need speech; plan a voiceover or music-only reel.")
    else:
        rep["audio"] = {"codec": as_.get("codec_name"), "channels": as_.get("channels"),
                        "sample_rate": int(as_.get("sample_rate", 0) or 0)}
        if a.loudness:
            rep["audio"].update(measure_loudness(a.input))
            il = rep["audio"].get("integrated_lufs")
            if il is not None and il < -35:
                warnings.append(f"Very quiet audio ({il} LUFS). Check the mic; normalization will raise noise too.")

    d = rep["duration"]
    if d and d < 3:
        warnings.append("Shorter than 3 s: Instagram rejects reels under 3 seconds.")
    if d > 15 * 60:
        warnings.append("Longer than 15 min (API max). Cut down or split.")
    elif d > 180:
        actions.append("length: raw is >3 min. Reels over 3 min are not recommended to non-followers; "
                       "target 15-90 s for reach (see director/hook-and-retention.md).")

    rep["warnings"], rep["actions"] = warnings, actions

    # human summary
    v = rep.get("video", {})
    log(f"[probe] {a.input}: {d:.2f}s, {v.get('width')}x{v.get('height')} {v.get('orientation')} "
        f"@ {v.get('fps')} fps, {v.get('codec')}, HDR={v.get('hdr')}, audio={'yes' if as_ else 'NO'}")
    for wmsg in warnings:
        log(f"  ! {wmsg}")
    for act in actions:
        log(f"  > {act}")

    if a.out:
        save_json(rep, a.out)
    else:
        json.dump(rep, sys.stdout, indent=2)
        print()


if __name__ == "__main__":
    main()
