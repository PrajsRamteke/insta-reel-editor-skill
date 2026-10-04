#!/usr/bin/env python3
"""FFmpeg-only engine: captions (+ simple titles) as an ASS subtitle file, optionally burned in.

Usage:
  python3 build_ass.py reel-plan.json [--out captions.ass] [--burn media/vertical.mp4 --video-out renders/graphics.mp4]
  python3 build_ass.py --captions captions.json --theme clean-educator --out captions.ass

Fast, cheap, no browser. Supports: word-synced captions (karaoke color highlight, pop reveal, phrase,
minimal), and the text graphics hook-title, keyword, cta, chapter. Everything else (cards, stats,
compare, b-roll, camera moves) needs the HyperFrames engine (engines/hyperframes.md); camera punch-ins
on this path come from EDL range "zoom" (auto_edl.py --alternate-zoom).
ASS gotchas handled here: PlayResX/Y = 1080x1920 (else sizes are relative to 384x288), colors are
&HAABBGGRR, WrapStyle 2 (we break lines ourselves), fonts loaded from fontsdir (Fontsource .woff).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

from _common import SKILL_DIR, die, load_json, load_theme, load_words, log, media_duration, run, deep_merge

CACHE_NM = Path(os.environ.get("REEL_CACHE", Path.home() / ".cache" / "insta-reel-editor")) / "npm" / "node_modules"


def ass_color(css: str, alpha: float | None = None) -> str:
    css = css.strip()
    a = 0.0
    m = re.match(r"rgba?\(([^)]+)\)", css)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        r, g, b = (int(float(x)) for x in parts[:3])
        if len(parts) > 3:
            a = 1 - float(parts[3])
    else:
        h = css.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    if alpha is not None:
        a = 1 - alpha
    return f"&H{int(round(a * 255)):02X}{b:02X}{g:02X}{r:02X}"


def ts(t: float) -> str:
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    cs = int(round((s - int(s)) * 100))
    if cs == 100:
        cs, s = 0, int(s) + 1
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


ASS_SCALE = 1.2  # libass font size reads ~20% smaller than CSS px at the same number


def wrap(text: str, max_chars: int) -> str:
    lines, cur = [], ""
    for wd in text.split():
        if cur and len(cur) + 1 + len(wd.replace("*", "")) > max_chars:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    if cur:
        lines.append(cur)
    return r"\N".join(lines)


def clean(t: str) -> str:
    return t.replace("\\", "/").replace("{", "(").replace("}", ")")


def vendor_ass_fonts(theme: dict, fontsdir: Path) -> None:
    fontsdir.mkdir(parents=True, exist_ok=True)
    for role in ("display", "body"):
        f = theme["fonts"][role]
        slug = f["package"].split("/")[-1]
        files = CACHE_NM / f["package"] / "files"
        if not files.exists():
            subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--silent", "--prefix",
                            str(CACHE_NM.parent), f["package"]], capture_output=True)
        for w in sorted({int(f["weight"]), 800, 700}):
            for cand in (files / f"{slug}-latin-{w}-normal.woff", files / f"{slug}-latin-ext-{w}-normal.woff"):
                if cand.exists():
                    shutil.copy2(cand, fontsdir / cand.name)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", nargs="?")
    ap.add_argument("--captions")
    ap.add_argument("--theme")
    ap.add_argument("--out")
    ap.add_argument("--burn", help="video to burn the subtitles into")
    ap.add_argument("--video-out")
    ap.add_argument("--fontsdir")
    a = ap.parse_args()

    wd = Path(a.plan).resolve().parent if a.plan else Path.cwd()
    plan = load_json(a.plan) if a.plan else {}

    def rel(p):
        p = Path(p)
        return p if p.is_absolute() else wd / p

    tspec = a.theme or plan.get("theme")
    if isinstance(tspec, str) and tspec.endswith(".json") and not Path(tspec).is_absolute():
        cand = rel(tspec) if not a.theme else Path(tspec)
        tspec = str(cand if cand.exists() else SKILL_DIR / tspec)
    theme = load_theme(tspec)
    if plan.get("theme_overrides"):
        theme = deep_merge(theme, plan["theme_overrides"])
    C, cap = theme["colors"], deep_merge(theme["caption"], (plan.get("captions") or {}).get("overrides", {}))
    cap_file = a.captions or (plan.get("captions") or {}).get("file")
    caps = load_json(rel(cap_file)) if cap_file and rel(cap_file).exists() else None
    style = (caps or {}).get("style", cap.get("style", "karaoke"))
    upper = cap.get("case") == "upper"
    body_font, disp_font = theme["fonts"]["body"]["family"], theme["fonts"]["display"]["family"]
    margin_v = 1920 - int((plan.get("captions") or {}).get("bottom", 1240))
    size = int(int(cap.get("size", 64)) * ASS_SCALE)
    text_c, acc_c, on_acc = ass_color(C["text"]), ass_color(C["accent"]), ass_color(C["on_accent"])
    card_c = ass_color(C["card"])

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{body_font},{size},{text_c},{acc_c},&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,{3 if not cap.get('box') else 0},{2 if not cap.get('box') else 0},2,140,140,{margin_v},1
Style: CapBox,{body_font},{size},{text_c},{acc_c},&H70000000,&H70000000,-1,0,0,0,100,100,0,0,3,10,0,2,140,140,{margin_v},1
Style: Title,{disp_font},{int(theme.get('title', {}).get('size', 104) * 0.9 * ASS_SCALE)},{text_c},{acc_c},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,3,8,80,80,300,1
Style: Box,{disp_font},84,{on_acc},{on_acc},{acc_c},{acc_c},-1,0,0,0,100,100,0,0,3,18,0,5,80,80,0,1
Style: Chip,{body_font},34,{ass_color(C['on_card'])},{acc_c},{card_c},{card_c},-1,0,0,0,100,100,1,0,3,12,0,7,70,70,270,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    cap_style = "CapBox" if cap.get("box") else "Cap"
    if caps:
        for pg in caps["pages"]:
            words = pg["words"]
            nlines = pg.get("lines", 1)

            def render(active: int | None, revealed: int) -> str:
                lines = []
                for ln in range(nlines):
                    parts = []
                    for j, w in enumerate(words):
                        if w.get("line", 0) != ln:
                            continue
                        t = clean(w["display"].upper() if upper else w["display"])
                        if style == "pop" and j > revealed:
                            parts.append(r"{\alpha&HFF&}" + t + r"{\alpha&H00&}")
                        elif active == j and cap.get("highlight", "pill") != "none":
                            parts.append(r"{\c" + acc_c + r"&\fscx108\fscy108}" + t + r"{\c" + (acc_c if w.get('emph') else text_c) + r"&\fscx100\fscy100}")
                        elif w.get("emph"):
                            parts.append(r"{\c" + acc_c + "&}" + t + r"{\c" + text_c + "&}")
                        else:
                            parts.append(t)
                    lines.append(" ".join(parts))
                return r"\N".join(lines)

            segs = []
            cursor = pg["start"]
            hl = cap.get("highlight", "pill") != "none" or style == "pop"
            if style in ("karaoke", "pop") and hl:
                if words[0]["start"] > cursor + 0.02:
                    segs.append((cursor, words[0]["start"], render(None, -1)))
                for j, w in enumerate(words):
                    st = max(cursor, w["start"])
                    en = words[j + 1]["start"] if j + 1 < len(words) else min(pg["end"], w["end"] + 0.25)
                    if en > st:
                        segs.append((st, en, render(j, j)))
                        cursor = en
                if pg["end"] > cursor + 0.02:
                    segs.append((cursor, pg["end"], render(None, len(words))))
            else:
                segs.append((pg["start"], pg["end"], render(None, len(words))))
            for k, (st, en, txt) in enumerate(segs):
                fad = ""
                if k == 0 and len(segs) == 1:
                    fad = r"{\fad(90,70)}"
                elif k == 0:
                    fad = r"{\fad(90,0)}"
                elif k == len(segs) - 1:
                    fad = r"{\fad(0,70)}"
                ev.append(f"Dialogue: 1,{ts(st)},{ts(en)},{cap_style},,0,0,0,,{fad}{txt}")

    # simple text graphics
    words_doc = load_words(rel(plan["words"]))["words"] if plan.get("words") and rel(plan["words"]).exists() else []
    skipped = []
    for g in plan.get("graphics", []):
        t = g.get("type")
        if "start" in g:
            st = float(g["start"])
        elif "land_on" in g and words_doc:
            st = float(words_doc[int(g["land_on"])]["start"]) - 0.2
        else:
            continue
        en = float(g["end"]) if "end" in g else (float(words_doc[int(g["until_word"])]["end"]) + 0.35
                                                 if "until_word" in g and words_doc else st + float(g.get("hold", 2.5)))
        st = max(0.0, st)
        raw = clean(str(g.get("text", "")))
        if t == "hook-title":  # WrapStyle 2 never wraps: break the title ourselves (~0.55 em per char)
            tsize = int(theme.get("title", {}).get("size", 104) * 0.9 * ASS_SCALE)
            raw = wrap(raw, max(8, int(900 / (tsize * 0.55))))
        txt = re.sub(r"\*([^*]+)\*", lambda m: r"{\c" + acc_c + "&}" + m.group(1) + r"{\c" + text_c + "&}", raw)
        if t == "hook-title":
            kick = clean(g.get("kicker", ""))
            body = (r"{\fs48\c" + acc_c + "&}" + kick.upper() + r"\N{\fs" + str(tsize) + r"\c" + text_c + "&}") if kick else ""
            fad = r"{\fad(0,220)}" if st < 0.05 else r"{\fad(160,220)\move(540,330,540,300,0,220)}"
            ev.append(f"Dialogue: 2,{ts(st)},{ts(en)},Title,,0,0,0,,{fad}{body}{txt}")
        elif t == "keyword":
            plain = clean(re.sub(r"\*", "", str(g.get("text", ""))))
            ev.append(f"Dialogue: 2,{ts(st)},{ts(en)},Box,,0,0,0,,{{\\pos(540,560)\\fad(120,160)\\fscx60\\fscy60\\t(0,180,\\fscx100\\fscy100)}}{plain}")
        elif t == "cta":
            plain = clean(re.sub(r"\*", "", str(g.get("text", ""))))
            ev.append(f"Dialogue: 2,{ts(st)},{ts(en)},Box,,0,0,0,,{{\\fs52\\pos(540,960)\\fad(160,160)}}{plain}")
        elif t == "chapter":
            ev.append(f"Dialogue: 2,{ts(st)},{ts(en)},Chip,,0,0,0,,{{\\fad(120,120)}}{txt.upper()}")
        else:
            skipped.append(f"{g.get('id', t)}:{t}")
    out = Path(a.out) if a.out else wd / "captions.ass"
    out.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    log(f"[ass] {len(ev)} events ({style} captions) -> {out}")
    if skipped:
        log(f"  ! not supported on the FFmpeg engine (use HyperFrames): {', '.join(skipped)}")

    if a.burn:
        fontsdir = Path(a.fontsdir) if a.fontsdir else wd / "fonts_ass"
        vendor_ass_fonts(theme, fontsdir)
        vout = Path(a.video_out) if a.video_out else wd / "renders" / "graphics.mp4"
        vout.parent.mkdir(parents=True, exist_ok=True)
        src = rel(a.burn).resolve()
        fdur = media_duration(src)
        # the ass filter parses ':' and '\\' in paths: run from the ASS file's folder with relative names
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vf",
             f"ass={out.name}:fontsdir={fontsdir.relative_to(out.parent) if fontsdir.is_relative_to(out.parent) else fontsdir}",
             "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "copy",
             "-t", f"{fdur:.3f}", str(vout.resolve())], cwd=str(out.parent))
        log(f"[ass] burned -> {vout}")


if __name__ == "__main__":
    main()
