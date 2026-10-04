#!/usr/bin/env python3
"""Render an EDL into one continuous cut and remap the transcript onto the new timeline.

Usage:
  python3 render_cut.py edl.json [--words transcript/words.json] [--out media/cut.mov]
                        [--words-out transcript/words.cut.json] [--preview]

Paths inside edl.json are relative to the EDL's folder (the reel workdir).
Method (hard rules from workflow/03-edit-decisions.md):
  * every range is re-encoded on the frame grid (frame-accurate, no frozen first frames)
  * 30 ms audio fades at every boundary (no clicks), audio kept as PCM (no generation loss)
  * segments are joined with the concat demuxer (-c copy) -> one encode, no drift
  * optional per-range "zoom" (and "focus":[x,y] 0..1) = punch-in for jump cuts (FFmpeg path)
Writes: media/cut.mov, transcript/words.cut.json, edl.resolved.json (ranges with output times + cut list).
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from _common import (die, load_words, ffprobe_json, load_json, log, need, parse_rate, run, save_json, video_stream,
                     audio_stream)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edl")
    ap.add_argument("--words", help="words.json on the SOURCE timeline (default transcript/words.json)")
    ap.add_argument("--out", help="default media/cut.mov")
    ap.add_argument("--words-out", help="default transcript/words.cut.json")
    ap.add_argument("--preview", action="store_true", help="fast 540p draft (crf 28) for a quick look")
    ap.add_argument("--crf", type=int, default=16)
    a = ap.parse_args()
    need("ffmpeg")

    edl_path = Path(a.edl).resolve()
    wd = edl_path.parent
    edl = load_json(edl_path)
    src = Path(edl["source"])
    src = src if src.is_absolute() else wd / src
    if not src.exists():
        die(f"source not found: {src}")
    info = ffprobe_json(src)
    vs, has_audio = video_stream(info), audio_stream(info) is not None
    fps_str = vs.get("r_frame_rate", "30/1")
    fps = parse_rate(fps_str) or float(edl.get("fps", 30))
    gop = str(max(1, round(fps)))
    out = Path(a.out) if a.out else wd / "media" / ("cut_preview.mov" if a.preview else "cut.mov")
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix="reelcut_"))
    listing, resolved, offset_f = [], [], 0
    for k, r in enumerate(edl["ranges"]):
        sf, ef = round(r["start"] * fps), round(r["end"] * fps)
        if ef <= sf:
            log(f"  skip empty range {k}")
            continue
        n = ef - sf
        ss, dur = sf / fps, n / fps
        vf = []
        z = float(r.get("zoom", 1.0) or 1.0)
        if z > 1.0:
            fx, fy = (r.get("focus") or [0.5, 0.4])
            vf.append(f"crop=trunc(iw/{z}/2)*2:trunc(ih/{z}/2)*2:(iw-iw/{z})*{fx}:(ih-ih/{z})*{fy}")
            vf.append(f"scale={vs['width']}:{vs['height']}:flags=lanczos")
        if a.preview:
            vf.append("scale=-2:540")
        vf.append("format=yuv420p")
        seg = tmp / f"seg_{k:03d}.mov"
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{ss:.6f}", "-i", str(src),
               "-t", f"{dur:.6f}", "-map", "0:v:0"]
        if has_audio:
            cmd += ["-map", "0:a:0"]
        cmd += ["-vf", ",".join(vf), "-r", fps_str, "-c:v", "libx264", "-preset", "veryfast" if a.preview else "fast",
                "-crf", "28" if a.preview else str(a.crf), "-g", gop, "-keyint_min", gop, "-sc_threshold", "0",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
        if has_audio:
            fd = min(0.03, dur / 4)
            cmd += ["-af", f"afade=t=in:st=0:d={fd:.3f},afade=t=out:st={max(0.0, dur - fd):.4f}:d={fd:.3f}",
                    "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
        cmd += [str(seg)]
        run(cmd, quiet=True)
        listing.append(f"file '{seg}'")
        resolved.append({**r, "src_start": round(ss, 4), "src_end": round(ef / fps, 4),
                         "out_start": round(offset_f / fps, 4), "out_end": round((offset_f + n) / fps, 4)})
        offset_f += n
        log(f"  seg {k:02d}: {ss:7.3f}-{ef / fps:7.3f}s ({dur:5.2f}s){'  zoom ' + str(z) if z > 1 else ''}")

    (tmp / "list.txt").write_text("\n".join(listing) + "\n")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i",
         str(tmp / "list.txt"), "-c", "copy", str(out)])
    shutil.rmtree(tmp, ignore_errors=True)

    # verify
    oi = ffprobe_json(out)
    expect = offset_f / fps
    vdur = float(video_stream(oi).get("duration", 0) or oi["format"]["duration"])
    adur = float(audio_stream(oi).get("duration", 0)) if has_audio else vdur
    log(f"[cut] {len(resolved)} segments -> {out}  expected {expect:.3f}s, video {vdur:.3f}s, audio {adur:.3f}s")
    if abs(vdur - expect) > 1.5 / fps or abs(adur - vdur) > 2.0 / fps:
        log("  ! duration mismatch > 1-2 frames: check the source for VFR (run prep.py) before going on")

    cuts = [r["out_start"] for r in resolved[1:]]
    save_json({**edl, "fps": fps, "ranges": resolved, "cuts": cuts, "output": str(out.relative_to(wd))
               if out.is_relative_to(wd) else str(out), "output_duration": round(expect, 4)},
              wd / "edl.resolved.json")

    # remap words onto the output timeline
    wpath = Path(a.words) if a.words else wd / "transcript" / "words.json"
    if not wpath.exists():
        log(f"  (no {wpath}; skipped word remap — re-transcribe the cut instead)")
        return
    wdoc = load_words(wpath)
    dropped = {d["i"] for d in edl.get("dropped", [])}
    new_words, clipped = [], 0
    for r in resolved:
        for w in wdoc["words"]:
            if w["i"] in dropped:
                continue
            mid = (w["start"] + w["end"]) / 2
            if not (r["src_start"] <= mid < r["src_end"]):
                continue
            s = max(w["start"], r["src_start"]) - r["src_start"] + r["out_start"]
            e = min(w["end"], r["src_end"]) - r["src_start"] + r["out_start"]
            if w["start"] < r["src_start"] - 0.01 or w["end"] > r["src_end"] + 0.01:
                clipped += 1
            nw = {**w, "src_i": w["i"], "start": round(s, 3), "end": round(max(e, s + 0.02), 3)}
            new_words.append(nw)
    for i, w in enumerate(new_words):
        w["i"] = i
    wout = Path(a.words_out) if a.words_out else wd / "transcript" / "words.cut.json"
    save_json({**{k: v for k, v in wdoc.items() if k not in ("words", "qc")}, "timeline": "cut",
               "duration": round(expect, 4), "words": new_words}, wout)
    log(f"[cut] remapped {len(new_words)} words -> {wout}" + (f"  ({clipped} words clipped by a cut edge!)"
                                                              if clipped else ""))


if __name__ == "__main__":
    main()
