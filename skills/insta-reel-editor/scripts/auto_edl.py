#!/usr/bin/env python3
"""Draft an edit decision list (EDL) from word timestamps: tighten pauses, drop fillers/retakes.

Usage:
  python3 auto_edl.py transcript/words.json --out edl.json [--pace natural]
                      [--drop 14-19,33] [--keep-fillers] [--audio media/mezz.mp4]
                      [--source media/mezz.mp4] [--fps 30] [--alternate-zoom 1.1]

Pace presets (max pause kept inside a run / head pad / tail pad, seconds):
  tight    0.25 / 0.08 / 0.12   fast talking-head, hype, listicles
  natural  0.40 / 0.10 / 0.16   default: educational, explainers
  relaxed  0.65 / 0.14 / 0.25   calm, wellness, storytelling, guided practice
Rules baked in (workflow/03-edit-decisions.md): cut only at word boundaries, pad every edge,
never extend into a dropped word, snap to the frame grid, and keep a short end-hold.
The agent should READ the result (and phrases.md) and edit ranges by hand where taste matters:
retakes, false starts, tangents, a better hook (cold open), and the overall length target.
"""
from __future__ import annotations

import argparse
import math
import re
import subprocess

from _common import is_filler, load_json, log, media_duration, norm_token, save_json, load_words

PACE = {"tight": (0.25, 0.08, 0.12), "natural": (0.40, 0.10, 0.16), "relaxed": (0.65, 0.14, 0.25)}


def parse_drops(spec: str | None) -> set[int]:
    out: set[int] = set()
    if not spec:
        return out
    for part in spec.split(","):
        part = part.strip().lstrip("#")
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a.lstrip("#")), int(b.lstrip("#")) + 1))
        else:
            out.add(int(part))
    return out


def silences(path: str, noise_db: float | None, min_d: float = 0.12) -> list[tuple[float, float]]:
    if noise_db is None:
        res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af",
                              "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True)
        m = re.search(r'"input_thresh"\s*:\s*"(-?[\d.]+)"', res.stderr)
        noise_db = float(m.group(1)) if m else -40.0
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af",
                          f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"],
                         capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", res.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", res.stderr)]
    return list(zip(starts, ends))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pace", choices=PACE.keys(), default="natural")
    ap.add_argument("--max-gap", type=float)
    ap.add_argument("--head", type=float)
    ap.add_argument("--tail", type=float)
    ap.add_argument("--end-hold", type=float, default=0.45, help="seconds kept after the final word")
    ap.add_argument("--min-cut", type=float, default=0.12, help="don't make cuts shorter than this")
    ap.add_argument("--drop", help="word indices/ranges to remove, e.g. '14-19,33' (retakes, tangents)")
    ap.add_argument("--keep-fillers", action="store_true")
    ap.add_argument("--fillers", help="extra filler tokens, comma separated (e.g. 'basically,matlab')")
    ap.add_argument("--audio", help="media to refine cut points into real silence (optional)")
    ap.add_argument("--noise-db", type=float, help="silence threshold; default adaptive (loudnorm input_thresh)")
    ap.add_argument("--source", default="media/mezz.mp4", help="path written into the EDL (relative to EDL dir)")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--duration", type=float, help="source duration (default: from words.json or --audio)")
    ap.add_argument("--alternate-zoom", type=float, default=0.0,
                    help="FFmpeg path only: give every other range this zoom (e.g. 1.1) to hide jump cuts")
    a = ap.parse_args()

    max_gap, head, tail = PACE[a.pace]
    max_gap = a.max_gap if a.max_gap is not None else max_gap
    head = a.head if a.head is not None else head
    tail = a.tail if a.tail is not None else tail
    doc = load_words(a.words)
    words = [w for w in doc["words"]]
    duration = a.duration or doc.get("duration") or (media_duration(a.audio) if a.audio else words[-1]["end"] + 1)
    extra = {norm_token(x) for x in (a.fillers or "").split(",") if x.strip()}
    explicit = parse_drops(a.drop)

    dropped_idx = set(explicit)
    reasons = {i: "manual" for i in explicit}
    if not a.keep_fillers:
        for w in words:
            if w.get("type", "word") == "word" and is_filler(w["text"], extra):
                dropped_idx.add(w["i"])
                reasons.setdefault(w["i"], "filler")
    speech = [w for w in words if w.get("type", "word") == "word"]
    kept = [w for w in speech if w["i"] not in dropped_idx]
    if not kept:
        raise SystemExit("Nothing left to keep. Check --drop.")
    by_i = {w["i"]: w for w in words}

    # group kept words into runs
    runs: list[list[dict]] = [[kept[0]]]
    for prev, cur in zip(kept, kept[1:]):
        between = [i for i in range(prev["i"] + 1, cur["i"]) if i in dropped_idx]
        if between or cur["start"] - prev["end"] > max_gap:
            runs.append([cur])
        else:
            runs[-1].append(cur)

    sil = silences(a.audio, a.noise_db) if a.audio else []

    def dropped_between(i0: int, i1: int) -> list[dict]:
        return [by_i[i] for i in range(i0 + 1, i1) if i in dropped_idx]

    ranges = []
    for k, run in enumerate(runs):
        first, last = run[0], run[-1]
        lo_bound = 0.0
        hi_bound = duration
        if k > 0:
            d = dropped_between(runs[k - 1][-1]["i"], first["i"])
            lo_bound = (d[-1]["end"] + 0.01) if d else runs[k - 1][-1]["end"]
        if k + 1 < len(runs):
            d = dropped_between(last["i"], runs[k + 1][0]["i"])
            hi_bound = (d[0]["start"] - 0.01) if d else runs[k + 1][0]["start"]
        st = max(lo_bound, first["start"] - head)
        en_tail = a.end_hold if k == len(runs) - 1 else tail
        en = min(hi_bound, last["end"] + en_tail)
        # refine into real silence: end where silence begins, start where it ends (if close)
        for s0, s1 in sil:
            if last["end"] - 0.05 <= s0 <= last["end"] + 0.35 and k != len(runs) - 1:
                en = min(hi_bound, max(last["end"] + 0.04, min(en, s0 + 0.06)))
            if first["start"] - 0.35 <= s1 <= first["start"] + 0.05:
                st = max(lo_bound, min(first["start"] - 0.03, max(st, s1 - 0.05)))
        ranges.append({"start": st, "end": en, "lo": lo_bound, "hi": hi_bound, "words": [first["i"], last["i"]],
                       "text": " ".join(w["text"] for w in run)})

    # merge ranges separated by a hair (no dropped words between)
    merged = [ranges[0]]
    for r in ranges[1:]:
        p = merged[-1]
        if r["start"] - p["end"] < a.min_cut and not dropped_between(p["words"][1], r["words"][0]):
            p["end"], p["hi"] = r["end"], r["hi"]
            p["words"][1] = r["words"][1]
            p["text"] += " " + r["text"]
        else:
            merged.append(r)

    # snap to frame grid without overlaps
    fps = a.fps
    out_ranges, prev_end_f = [], -1
    for r in merged:
        # round to the nearest frame, but never cross into a dropped word (lo/hi bounds)
        sf = max(round(r["start"] * fps), math.ceil(r["lo"] * fps - 1e-6), prev_end_f if prev_end_f >= 0 else 0)
        ef = min(round(r["end"] * fps), math.floor(r["hi"] * fps + 1e-6), math.floor(duration * fps + 1e-6))
        ef = max(ef, sf + 1)
        prev_end_f = ef
        rr = {"start": round(sf / fps, 4), "end": round(ef / fps, 4), "words": r["words"], "text": r["text"],
              "reason": "speech"}
        out_ranges.append(rr)
    if a.alternate_zoom and a.alternate_zoom > 1:
        for j, r in enumerate(out_ranges):
            r["zoom"] = a.alternate_zoom if j % 2 == 1 else 1.0

    # bookkeeping
    dropped = []
    for i in sorted(dropped_idx):
        w = by_i.get(i)
        if w:
            dropped.append({"i": i, "text": w["text"], "start": w["start"], "end": w["end"], "reason": reasons.get(i)})
    out_dur = sum(r["end"] - r["start"] for r in out_ranges)
    notes = []
    long_ranges = [r for r in out_ranges if r["end"] - r["start"] > 8]
    if long_ranges:
        notes.append(f"{len(long_ranges)} ranges run longer than 8 s with no cut: plan a punch-in, b-roll or graphic "
                     "inside them (director/hook-and-retention.md).")
    if out_dur > 90:
        notes.append(f"Output is {out_dur:.0f} s. For reach, most reels land at 15-90 s: consider cutting tangents.")
    edl = {"version": 1, "source": a.source, "fps": fps, "pace": a.pace,
           "params": {"max_gap": max_gap, "head": head, "tail": tail, "end_hold": a.end_hold},
           "ranges": out_ranges, "dropped": dropped,
           "stats": {"source_duration": round(duration, 3), "output_duration": round(out_dur, 3),
                     "removed_s": round(duration - out_dur, 3), "cuts": max(0, len(out_ranges) - 1)},
           "notes": notes}
    save_json(edl, a.out)
    log(f"[edl] {len(out_ranges)} ranges, {edl['stats']['cuts']} cuts, {duration:.2f}s -> {out_dur:.2f}s "
        f"(removed {duration - out_dur:.2f}s, {len(dropped)} words dropped) -> {a.out}")
    for n in notes:
        log(f"  ! {n}")


if __name__ == "__main__":
    main()
