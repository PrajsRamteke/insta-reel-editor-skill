"""Shared helpers for the insta-reel-editor scripts.

Standard library only. Every script imports this module from its own folder,
so run scripts as `python3 <skill>/scripts/<name>.py ...` from anywhere.
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
THEMES_DIR = SKILL_DIR / "assets" / "themes"

# Canvas + Instagram constants (see reference/instagram-specs.md, reference/safe-zones.md)
CANVAS_W, CANVAS_H = 1080, 1920
SAFE = {
    "top_organic": 220,      # Reels header / camera icon (organic)
    "top_conservative": 270, # Meta ads guidance: 14% of 1920
    "bottom_organic": 1500,  # username / caption / audio row starts (organic, collapsed caption)
    "bottom_conservative": 1250,  # Meta guidance: bottom 35% kept clear
    "side": 65,              # 6% side margins
    "rail_x": 940,           # right action rail starts (like/comment/share/save)
    "rail_y0": 1000,
    "rail_y1": 1750,
    "grid34_y0": 240,        # profile grid 3:4 crop
    "grid34_y1": 1680,
    "feed45_y0": 285,        # 4:5 feed preview crop
    "feed45_y1": 1635,
}

FILLERS_EN = {
    "um", "umm", "uh", "uhh", "uhm", "erm", "er", "ah", "ahh", "hmm", "hm", "mm", "mmm", "eh",
}


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def die(msg: str, code: int = 1) -> None:
    log(f"ERROR: {msg}")
    sys.exit(code)


def need(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        die(f"'{binary}' not found on PATH. Install it first (see workflow/01-probe-and-prep.md).")
    return path


def run(cmd: list[str], check: bool = True, capture: bool = True, quiet: bool = False,
        cwd: str | None = None) -> subprocess.CompletedProcess:
    if not quiet:
        log("$ " + " ".join(_q(c) for c in cmd))
    res = subprocess.run(cmd, capture_output=capture, text=True, cwd=cwd)
    if check and res.returncode != 0:
        tail = (res.stderr or "")[-2000:]
        die(f"command failed ({res.returncode}): {' '.join(cmd[:4])} ...\n{tail}")
    return res


def _q(s: str) -> str:
    return s if re.fullmatch(r"[\w./:=,+-]+", s) else "'" + s.replace("'", "'\\''") + "'"


def ffprobe_json(path: str | Path) -> dict:
    need("ffprobe")
    res = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)], quiet=True)
    return json.loads(res.stdout)


def parse_rate(rate: str | None) -> float:
    if not rate or rate in ("0/0", "N/A"):
        return 0.0
    if "/" in rate:
        n, d = rate.split("/")
        return float(n) / float(d) if float(d) else 0.0
    return float(rate)


def media_duration(path: str | Path) -> float:
    info = ffprobe_json(path)
    d = info.get("format", {}).get("duration")
    if d:
        return float(d)
    return max(float(s.get("duration", 0) or 0) for s in info.get("streams", []))


def video_stream(info: dict) -> dict | None:
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic", 0) == 0:
            return s
    return None


def audio_stream(info: dict) -> dict | None:
    for s in info.get("streams", []):
        if s.get("codec_type") == "audio":
            return s
    return None


def rotation_of(vs: dict) -> int:
    rot = 0
    tags = vs.get("tags", {}) or {}
    if "rotate" in tags:
        try:
            rot = int(float(tags["rotate"]))
        except ValueError:
            rot = 0
    for sd in vs.get("side_data_list", []) or []:
        if "rotation" in sd:
            try:
                rot = int(float(sd["rotation"]))
            except (TypeError, ValueError):
                pass
    return rot % 360


def display_size(vs: dict) -> tuple[int, int]:
    w, h = int(vs.get("width", 0)), int(vs.get("height", 0))
    if rotation_of(vs) in (90, 270):
        w, h = h, w
    return w, h


def load_json(path: str | Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fmt_ts(t: float) -> str:
    """Seconds -> MM:SS.mmm (for humans)."""
    t = max(0.0, t)
    m = int(t // 60)
    return f"{m:02d}:{t - m * 60:06.3f}"


def norm_token(text: str) -> str:
    """Lowercase and drop punctuation/symbols/spaces but KEEP combining marks (Devanagari matras etc.)."""
    import unicodedata
    return "".join(ch for ch in text.lower()
                    if ch == "'" or not unicodedata.category(ch).startswith(("P", "S", "Z", "C")))


def is_filler(text: str, extra: set[str] | None = None) -> bool:
    tok = norm_token(text)
    return bool(tok) and (tok in FILLERS_EN or (extra is not None and tok in extra))


SENTENCE_END = re.compile(r"[.!?।॥。？！]$")


def snap(t: float, fps: float) -> float:
    """Snap a time to the nearest frame boundary."""
    return round(round(t * fps) / fps, 6)


def load_theme(spec) -> dict:
    """Resolve a theme spec: preset name, path to JSON, or inline dict (optionally with 'extends')."""
    if spec is None:
        spec = "clean-educator"
    if isinstance(spec, str):
        p = Path(spec)
        if not p.suffix:
            p = THEMES_DIR / f"{spec}.json"
        if not p.exists():
            avail = ", ".join(sorted(x.stem for x in THEMES_DIR.glob("*.json")))
            die(f"theme '{spec}' not found. Available presets: {avail}")
        theme = load_json(p)
    else:
        theme = dict(spec)
    base_name = theme.pop("extends", None)
    if base_name:
        base = load_theme(base_name)
        theme = deep_merge(base, theme)
    return theme


def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def words_list(words_doc) -> list[dict]:
    """Accept either {'words': [...]} or a bare list."""
    if isinstance(words_doc, dict):
        return words_doc.get("words", [])
    return list(words_doc)


def load_words(path: str | Path) -> dict:
    """Load a words.json and make sure every word has 'i' and 'type' (hand-made files may lack them)."""
    doc = load_json(path)
    if isinstance(doc, list):
        doc = {"words": doc}
    for k, w in enumerate(doc.get("words", [])):
        w.setdefault("i", k)
        w.setdefault("type", "word")
    return doc


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def is_finite(x) -> bool:
    try:
        return math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def has_filter(name: str) -> bool:
    res = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
    return re.search(rf"\s{name}\s", res.stdout) is not None


def ensure_dir(p: str | Path) -> Path:
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in ("1", "true", "yes")
