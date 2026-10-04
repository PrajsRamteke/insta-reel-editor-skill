#!/usr/bin/env python3
"""QA gate for a finished reel: spec compliance, loudness, A/V sync, dead air, black/frozen frames,
and a contact sheet of the moments that matter with Instagram's UI zones drawn on top.

Usage:
  python3 verify_reel.py renders/final.mp4 [--workdir .] [--plan reel-plan.json] [--edl edl.resolved.json]
                         [--captions captions.json] [--expected-words transcript/words.cut.json]
                         [--transcribe-check [--engine auto]] [--max-frames 24]

Writes qa/report.json, qa/report.md, qa/frames/*.png and qa/verify_sheet.jpg. Exit code 1 if any FAIL.
Then LOOK at qa/verify_sheet.jpg (Read it): red = UI covers this, orange = conservative/ads zone,
cyan box = 3:4 profile-grid crop. Text, faces and key visuals must avoid red/orange.
The --transcribe-check re-transcribes the final file and diffs it against the intended words:
missing words = a cut clipped speech; extra words = a ghost/duplicate slipped in.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

from _common import (SAFE, audio_stream, ffprobe_json, has_filter, is_filler, load_json, load_words, log, need,
                     norm_token, parse_rate, save_json, video_stream)

GUIDES = ",".join([
    f"drawbox=x=0:y=0:w=1080:h={SAFE['top_organic']}:color=red@0.20:t=fill",
    f"drawbox=x=0:y={SAFE['top_organic']}:w=1080:h={SAFE['top_conservative'] - SAFE['top_organic']}:color=orange@0.14:t=fill",
    f"drawbox=x=0:y={SAFE['bottom_conservative']}:w=1080:h={SAFE['bottom_organic'] - SAFE['bottom_conservative']}:color=orange@0.14:t=fill",
    f"drawbox=x=0:y={SAFE['bottom_organic']}:w=1080:h={1920 - SAFE['bottom_organic']}:color=red@0.20:t=fill",
    f"drawbox=x={SAFE['rail_x']}:y={SAFE['rail_y0']}:w={1080 - SAFE['rail_x']}:h={SAFE['rail_y1'] - SAFE['rail_y0']}:color=red@0.18:t=fill",
    f"drawbox=x=0:y={SAFE['grid34_y0']}:w=1080:h={SAFE['grid34_y1'] - SAFE['grid34_y0']}:color=cyan@0.9:t=4",
])


def atoms_order(path: str) -> list[str]:
    order = []
    with open(path, "rb") as f:
        while True:
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            size, typ = struct.unpack(">I4s", hdr)
            name = typ.decode("latin-1")
            order.append(name)
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]
                f.seek(size - 16, 1)
            elif size == 0:
                break
            else:
                f.seek(size - 8, 1)
    return order


def ff_stderr(args: list[str]) -> str:
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True).stderr


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--workdir", default=None, help="reel folder (default: parent of renders/)")
    ap.add_argument("--plan")
    ap.add_argument("--edl")
    ap.add_argument("--captions")
    ap.add_argument("--expected-words")
    ap.add_argument("--transcribe-check", action="store_true")
    ap.add_argument("--engine", default="auto")
    ap.add_argument("--language")
    ap.add_argument("--max-frames", type=int, default=24)
    ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    need("ffmpeg")

    video = Path(a.video).resolve()
    wd = Path(a.workdir).resolve() if a.workdir else (video.parent.parent if video.parent.name == "renders" else video.parent)
    qa = wd / "qa"
    (qa / "frames").mkdir(parents=True, exist_ok=True)

    def opt(p, default):
        if p:
            return Path(p)
        d = wd / default
        return d if d.exists() else None

    plan_p, edl_p, cap_p = opt(a.plan, "reel-plan.json"), opt(a.edl, "edl.resolved.json"), opt(a.captions, "captions.json")
    exp_p = opt(a.expected_words, "transcript/words.cut.json")
    checks = []

    def add(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    info = ffprobe_json(video)
    vs, as_ = video_stream(info), audio_stream(info)
    fmt = info["format"]
    dur = float(fmt["duration"])
    # ---- container / codec spec
    order = atoms_order(str(video))
    moov_first = "moov" in order and "mdat" in order and order.index("moov") < order.index("mdat")
    add("moov atom before mdat (faststart)", "PASS" if moov_first else "FAIL", " ".join(order[:6]))
    with open(video, "rb") as fh:
        head = fh.read(4 * 1024 * 1024) if moov_first else fh.read()
    has_elst = b"elst" in head[:head.find(b"mdat")] if b"mdat" in head else b"elst" in head
    add("no edit lists (Graph API)", "PASS" if not has_elst else "WARN",
        "none" if not has_elst else "elst box present: re-mux with finalize.py (-use_editlist 0)")
    if vs:
        w, h = int(vs["width"]), int(vs["height"])
        add("resolution 1080x1920", "PASS" if (w, h) == (1080, 1920) else ("WARN" if abs(w / h - 9 / 16) < 0.01 else "FAIL"),
            f"{w}x{h}")
        add("video codec H.264/HEVC", "PASS" if vs["codec_name"] in ("h264", "hevc") else "FAIL",
            f"{vs['codec_name']} {vs.get('profile', '')}")
        if vs["codec_name"] == "h264":
            add("H.264 profile High/Main, progressive", "PASS" if vs.get("profile") in ("High", "Main") and
                vs.get("field_order", "progressive") in ("progressive", "unknown") else "WARN",
                f"{vs.get('profile')} / {vs.get('field_order', 'progressive')}")
        add("pixel format yuv420p (8-bit 4:2:0)", "PASS" if vs.get("pix_fmt") == "yuv420p" else "WARN", vs.get("pix_fmt"))
        fps = parse_rate(vs.get("avg_frame_rate")) or parse_rate(vs.get("r_frame_rate"))
        rfps = parse_rate(vs.get("r_frame_rate"))
        add("frame rate 23-60, constant", "PASS" if 23 <= fps <= 60.01 and abs(fps - rfps) < 0.05 else "FAIL",
            f"avg {fps:.3f} / r {rfps:.3f}")
        br = int(vs.get("bit_rate", 0) or 0) / 1e6
        add("video bitrate <= 25 Mbps", "PASS" if br <= 25 else "FAIL", f"{br:.2f} Mbps")
        prim = vs.get("color_primaries")
        add("color tagged BT.709 (SDR)", "PASS" if prim in ("bt709", None) and vs.get("color_transfer") not in
            ("smpte2084", "arib-std-b67") else "WARN", f"primaries={prim} transfer={vs.get('color_transfer')}")
    else:
        add("video stream", "FAIL", "missing")
    if as_:
        add("audio AAC 48 kHz, mono/stereo", "PASS" if as_["codec_name"] == "aac" and int(as_.get("sample_rate", 0)) <= 48000
            and int(as_.get("channels", 0)) <= 2 else "FAIL",
            f"{as_['codec_name']} {as_.get('sample_rate')} Hz {as_.get('channels')} ch")
        vdur, adur = float(vs.get("duration", dur)), float(as_.get("duration", dur))
        diff = abs(vdur - adur)
        add("audio/video durations match", "PASS" if diff <= 0.1 else ("WARN" if diff <= 0.25 else "FAIL"),
            f"video {vdur:.3f}s, audio {adur:.3f}s (diff {diff * 1000:.0f} ms; AAC priming ~21-64 ms is normal)")
    else:
        add("audio stream", "WARN", "silent reel: muted reels are not recommended by Instagram")
    add("duration 3 s - 15 min", "PASS" if 3 <= dur <= 900 else "FAIL", f"{dur:.2f}s")
    if dur > 180:
        add("duration <= 3 min (recommendable to non-followers)", "WARN", f"{dur:.0f}s")
    size_mb = int(fmt.get("size", 0)) / 1e6
    add("file size <= 300 MB (API)", "PASS" if size_mb <= 300 else "WARN", f"{size_mb:.1f} MB")

    # ---- loudness
    if as_:
        txt = ff_stderr(["-i", str(video), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", txt)
        TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", txt)
        I = float(I[-1]) if I else None
        TP = float(TP[-1]) if TP else None
        if I is not None:
            add(f"integrated loudness ~{a.lufs} LUFS", "PASS" if abs(I - a.lufs) <= 1.0 else ("WARN" if abs(I - a.lufs) <= 2.5 else "FAIL"),
                f"{I} LUFS")
        if TP is not None:
            add("true peak <= -1 dBTP", "PASS" if TP <= -1.5 else ("WARN" if TP <= -1.0 else "FAIL"),
                f"{TP} dBTP (target -1.5)")
        sil = ff_stderr(["-i", str(video), "-vn", "-af", "silencedetect=noise=-45dB:d=1.2", "-f", "null", "-"])
        spans = list(zip(map(float, re.findall(r"silence_start: (-?[\d.]+)", sil)),
                         map(float, re.findall(r"silence_end: (-?[\d.]+)", sil))))
        add("no dead air >= 1.2 s", "PASS" if not spans else "WARN",
            ", ".join(f"{s:.1f}-{e:.1f}s" for s, e in spans) or "none")

    # ---- black / frozen picture
    if vs:
        txt = ff_stderr(["-i", str(video), "-an", "-vf", "blackdetect=d=0.2:pix_th=0.08,freezedetect=n=-60dB:d=2",
                         "-f", "null", "-"])
        blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", txt)
        add("no black frames >= 0.2 s", "PASS" if not blacks else "WARN",
            ", ".join(f"{float(s):.2f}-{float(e):.2f}s" for s, e in blacks) or "none")
        fstarts = re.findall(r"freeze_start: ([\d.]+)", txt)
        fends = re.findall(r"freeze_end: ([\d.]+)", txt)
        add("no frozen picture >= 2 s", "PASS" if not fstarts else "WARN",
            ", ".join(f"{float(s):.1f}-{float(e):.1f}s" for s, e in zip(fstarts, fends + ['end'] * 5)) or "none")
        if dur > 8:
            # visual-change cadence: very long stretches with no cut/graphic feel static on Reels
            pass

    # ---- frames at moments that matter
    times = [0.0, min(0.5, dur / 4)]
    labels = {0.0: "frame0/cover", round(min(0.5, dur / 4), 2): "hook"}
    rep_p = (wd / "composition" / "build-report.json")
    gfx = []
    if rep_p.exists():
        gfx = load_json(rep_p).get("graphics", [])
    elif plan_p and plan_p.exists():
        gfx = [{"id": g.get("id", f"g{i}"), "start": g["start"], "end": g["end"], "type": g.get("type")}
               for i, g in enumerate(load_json(plan_p).get("graphics", [])) if "start" in g and "end" in g]
    for g in gfx:
        t = round(min(g["end"] - 0.05, g["start"] + max(0.6, (g["end"] - g["start"]) * 0.5)), 2)
        times.append(t)
        labels[t] = f"{g['id']} {g.get('type', '')}"
    if edl_p and edl_p.exists():
        for c in load_json(edl_p).get("cuts", [])[:12]:
            t = round(c + 0.07, 2)
            times.append(t)
            labels.setdefault(t, "after cut")
    if cap_p and cap_p.exists():
        pages = load_json(cap_p).get("pages", [])
        for pg in pages[:: max(1, len(pages) // 5)][:5]:
            w0 = pg["words"][min(1, len(pg["words"]) - 1)]
            t = round(w0["start"] + 0.05, 2)
            times.append(t)
            labels.setdefault(t, f"caption {pg['id']}")
    times.append(max(0.0, round(dur - 0.15, 2)))
    labels.setdefault(max(0.0, round(dur - 0.15, 2)), "last frame / loop")
    uniq = []
    for t in sorted(set(times)):
        if 0 <= t < dur and (not uniq or t - uniq[-1] >= 0.25):
            uniq.append(t)
    if len(uniq) > a.max_frames:
        step = len(uniq) / a.max_frames
        uniq = [uniq[int(i * step)] for i in range(a.max_frames)]
    can_text = has_filter("drawtext")
    frame_files = []
    for k, t in enumerate(uniq):
        lab = labels.get(t, "")
        vf = GUIDES + ",scale=360:640"
        if can_text:
            safe_lab = re.sub(r"[^\w .:/-]", "", f"{t:.2f}s {lab}")[:40]
            vf += f",drawtext=text='{safe_lab}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.7"
        fp = qa / "frames" / f"f{k:02d}_{t:06.2f}.png"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(video),
                        "-frames:v", "1", "-vf", vf, str(fp)], check=False)
        if fp.exists():
            frame_files.append(fp)
    sheet = qa / "verify_sheet.jpg"
    if frame_files:
        cols = 6
        rows = (len(frame_files) + cols - 1) // cols
        lst = qa / "frames" / "list.txt"
        lst.write_text("".join(f"file '{p}'\nduration 1\n" for p in frame_files))
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-vf", f"tile={cols}x{rows}:padding=6:margin=6:color=0x202020", "-frames:v", "1", "-q:v", "3",
                        str(sheet)], check=False)

    # ---- re-transcribe and diff (catches clipped words / ghosts)
    if a.transcribe_check and exp_p and exp_p.exists():
        out_words = qa / "words.final.json"
        cmd = [sys.executable, str(Path(__file__).with_name("transcribe.py")), str(video), "--out", str(out_words),
               "--engine", a.engine, "--force"]
        if a.language:
            cmd += ["--language", a.language]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and out_words.exists():
            exp = [norm_token(w["text"]) for w in load_words(exp_p)["words"] if not is_filler(w["text"])]
            got = [norm_token(w["text"]) for w in load_words(out_words)["words"] if not is_filler(w["text"])]
            exp, got = [x for x in exp if x], [x for x in got if x]
            sm = difflib.SequenceMatcher(a=exp, b=got, autojunk=False)
            missing, extra = [], []
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op in ("delete", "replace"):
                    missing.append(" ".join(exp[i1:i2]))
                if op in ("insert", "replace"):
                    extra.append(" ".join(got[j1:j2]))
            ratio = sm.ratio()
            st = "PASS" if ratio >= 0.95 else ("WARN" if ratio >= 0.85 else "FAIL")
            add("re-transcription matches intended words", st,
                f"similarity {ratio:.2%}; missing: {missing[:8]}; extra: {extra[:8]}")
        else:
            add("re-transcription matches intended words", "WARN", "could not transcribe: " + res.stderr[-300:])

    fails = [c for c in checks if c["status"] == "FAIL"]
    warns = [c for c in checks if c["status"] == "WARN"]
    report = {"video": str(video), "duration": dur, "checks": checks, "frames": [str(p) for p in frame_files],
              "sheet": str(sheet) if frame_files else None, "summary": {"fail": len(fails), "warn": len(warns),
                                                                         "pass": len(checks) - len(fails) - len(warns)}}
    save_json(report, qa / "report.json")
    md = [f"# Reel QA — {video.name}", "", f"**{len(fails)} FAIL · {len(warns)} WARN · "
          f"{report['summary']['pass']} PASS**", "", "| Status | Check | Detail |", "|---|---|---|"]
    md += [f"| {c['status']} | {c['check']} | {c['detail']} |" for c in checks]
    md += ["", f"Contact sheet: `{sheet.name}` (red = UI overlay, orange = conservative/ads zone, cyan = 3:4 grid crop)",
           "", "Visual checklist (look at the sheet): hook readable on frame 0 · no text in red zones · no text over "
           "eyes/mouth · captions never hidden by graphics · one hero element at a time · last frame loops cleanly."]
    (qa / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for c in checks:
        log(f"  [{c['status']}] {c['check']}: {c['detail']}")
    log(f"[verify] {len(fails)} FAIL, {len(warns)} WARN -> {qa / 'report.md'}; sheet {sheet}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
