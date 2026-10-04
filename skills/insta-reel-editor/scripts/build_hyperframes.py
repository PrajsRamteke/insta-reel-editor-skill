#!/usr/bin/env python3
"""Compile reel-plan.json (+ captions.json) into a self-contained HyperFrames project.

Usage:
  python3 build_hyperframes.py reel-plan.json [--out composition] [--no-install] [--node-modules DIR]

The agent writes only reel-plan.json (creative decisions); this compiler writes the HTML, CSS and
GSAP timeline deterministically: theme tokens -> CSS variables, graphics -> components with
personality-matched entrances/exits, captions -> word-synced pages, camera -> punch-ins/drift,
face-aware placement (region "auto" keeps text off the face using reframe.json).
Then:  cd composition && npx hyperframes check && npx hyperframes snapshot --at 1,4 && \
       npx hyperframes render --quality delivery --output ../renders/graphics.mp4
Plan schema: reference/data-contracts.md. Component catalog: patterns/motion-graphics.md.
Fonts (Fontsource, OFL) and GSAP are vendored from an npm cache (~/.cache/insta-reel-editor/npm)
so renders are offline and deterministic. Indic/Arabic scripts get Noto fallbacks automatically;
emoji use the system emoji font.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from _common import CANVAS_H, CANVAS_W, SKILL_DIR, deep_merge, die, load_json, load_theme, load_words, log, media_duration, save_json

CACHE = Path(os.environ.get("REEL_CACHE", Path.home() / ".cache" / "insta-reel-editor")) / "npm"
DEFAULT_HOLD = {"hook-title": 2.8, "keyword": 1.6, "stat": 2.8, "list-item": 3.0, "callout": 3.2, "compare": 4.2,
                "checklist": 4.5, "lower-third": 3.0, "quote": 3.5, "image": 3.0, "broll": 3.0, "cta": 3.0,
                "chapter": 2.0, "sticker": 1.4}
REQUIRED = {"hook-title": ["text"], "keyword": ["text"], "stat": ["value"], "list-item": ["text"],
            "callout": ["text"], "compare": ["left", "right"], "checklist": ["items"], "lower-third": ["name"],
            "quote": ["text"], "image": ["src"], "broll": ["src"], "cta": ["text"], "chapter": ["text"],
            "sticker": ["text"]}
DEFAULT_REGION = {"hook-title": "auto", "keyword": "auto", "stat": "auto", "list-item": "auto", "callout": "auto",
                  "compare": "cover", "checklist": "auto", "lower-third": "lower-third", "quote": "cover",
                  "image": "auto", "broll": "cover", "cta": "lower", "chapter": "chip", "sticker": "auto"}
PERSONALITY_STYLE = {"clean": "slide", "calm": "fade", "premium": "reveal", "playful": "pop", "energetic": "pop"}
SCRIPT_FONTS = [  # (regex, family, fontsource package)
    (r"[\u0900-\u097F]", "Noto Sans Devanagari", "@fontsource/noto-sans-devanagari"),
    (r"[\u0980-\u09FF]", "Noto Sans Bengali", "@fontsource/noto-sans-bengali"),
    (r"[\u0A00-\u0A7F]", "Noto Sans Gurmukhi", "@fontsource/noto-sans-gurmukhi"),
    (r"[\u0A80-\u0AFF]", "Noto Sans Gujarati", "@fontsource/noto-sans-gujarati"),
    (r"[\u0B80-\u0BFF]", "Noto Sans Tamil", "@fontsource/noto-sans-tamil"),
    (r"[\u0C00-\u0C7F]", "Noto Sans Telugu", "@fontsource/noto-sans-telugu"),
    (r"[\u0C80-\u0CFF]", "Noto Sans Kannada", "@fontsource/noto-sans-kannada"),
    (r"[\u0D00-\u0D7F]", "Noto Sans Malayalam", "@fontsource/noto-sans-malayalam"),
    (r"[\u0600-\u06FF]", "Noto Sans Arabic", "@fontsource/noto-sans-arabic"),
    # Emoji are NOT vendored: Fontsource Noto Color Emoji subsets render blank in headless Chrome, so emoji
    # fall through to the system emoji font (Apple Color Emoji on macOS, Noto Color Emoji on Linux).
]
ICONS = {
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "alert": '<path d="M12 3.5L2.5 20h19L12 3.5z"/><path d="M12 10v4.5M12 17.2v.3"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.4v.3"/>',
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.8.6 1.1 1.4 1.1 2.2h5c0-.8.3-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
    "bookmark": '<path d="M6.5 3.5h11v17l-5.5-4-5.5 4z"/>',
    "send": '<path d="M21 3L10 14M21 3l-7 18-4-7-7-4z"/>',
    "heart": '<path d="M12 20s-7-4.4-9-8.8A5 5 0 0 1 12 6.5a5 5 0 0 1 9 4.7C19 15.6 12 20 12 20z"/>',
    "star": '<path d="M12 3l2.7 5.8 6.3.7-4.7 4.3 1.3 6.2L12 17l-5.6 3 1.3-6.2L3 9.5l6.3-.7z"/>',
    "arrow": '<path d="M4 12h15M13 6l6 6-6 6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2.5"/>',
    "flame": '<path d="M12 21a6 6 0 0 0 6-6c0-4-3-6.5-4-10-2 2-2.5 4-2.5 5.5C10 9.8 9 9 8.5 7.5 7 9.5 6 11.8 6 15a6 6 0 0 0 6 6z"/>',
    "sparkle": '<path d="M12 3l1.9 5.6L19.5 10.5 13.9 12.4 12 18l-1.9-5.6L4.5 10.5l5.6-1.9z"/>',
    "breath": '<path d="M3 9h11a3 3 0 1 0-3-3M3 15h15a3 3 0 1 1-3 3M3 12h7"/>',
    "play": '<path d="M7 4.5v15l12-7.5z"/>',
}
VARIANT_ICON = {"tip": "bulb", "warning": "alert", "myth": "x", "fact": "check", "note": "info", "do": "check",
                "dont": "x"}


# ------------------------------------------------------------------ helpers
def esc(s) -> str:
    return html.escape(str(s), quote=True)


def md(s: str) -> str:
    """Minimal markup: *word* -> accent emphasis. Everything else escaped."""
    parts = re.split(r"(\*[^*]+\*)", str(s))
    out = []
    for p in parts:
        if len(p) > 2 and p.startswith("*") and p.endswith("*"):
            out.append(f'<span class="em">{esc(p[1:-1])}</span>')
        else:
            out.append(esc(p))
    return "".join(out)


def words_html(s: str, cls: str) -> str:
    """Split into per-word spans (for staggered title reveals), keeping *emphasis*."""
    toks = re.findall(r"\*[^*]+\*|\S+", str(s))
    spans = []
    for t in toks:
        if t.startswith("*") and t.endswith("*") and len(t) > 2:
            spans.append(f'<span class="{cls} em">{esc(t[1:-1])}</span>')
        else:
            spans.append(f'<span class="{cls}">{esc(t)}</span>')
    return " ".join(spans)


def icon(name: str | None, cls: str = "ico") -> str:
    if not name or name not in ICONS:
        return ""
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def npm_ensure(pkgs: list[str], node_modules: str | None, allow_install: bool) -> Path:
    roots = [Path(node_modules)] if node_modules else []
    roots += [CACHE / "node_modules"]
    for r in roots:
        if all((r / p).exists() for p in pkgs):
            return r
    if not allow_install:
        die(f"missing npm packages {pkgs} (run without --no-install, or pass --node-modules)")
    if not shutil.which("npm"):
        die("npm not found. Install Node.js 22+ (needed for HyperFrames anyway).")
    CACHE.mkdir(parents=True, exist_ok=True)
    if not (CACHE / "package.json").exists():
        (CACHE / "package.json").write_text('{"name":"reel-cache","private":true}\n')
    log(f"[build] npm install {' '.join(pkgs)} -> {CACHE}")
    res = subprocess.run(["npm", "install", "--no-audit", "--no-fund", "--silent", "--prefix", str(CACHE), *pkgs],
                         capture_output=True, text=True)
    if res.returncode != 0:
        die("npm install failed:\n" + res.stderr[-1500:])
    return CACHE / "node_modules"


def vendor_font(nm: Path, pkg: str, weight: int, out_dir: Path) -> str:
    """Copy a Fontsource weight (all unicode-range subsets) and return inline @font-face CSS."""
    base = nm / pkg
    css_file = base / f"{weight}.css"
    if not css_file.exists():
        avail = sorted(p.stem for p in base.glob("[0-9]*.css") if p.stem.isdigit())
        if not avail:
            die(f"{pkg} has no weights?")
        best = min(avail, key=lambda w: abs(int(w) - weight))
        log(f"[build] {pkg} has no {weight}; using {best}")
        css_file = base / f"{best}.css"
    css = css_file.read_text()
    slug = pkg.split("/")[-1]
    dst = out_dir / "fonts" / slug
    dst.mkdir(parents=True, exist_ok=True)
    for fname in set(re.findall(r"url\(\./files/([^)]+?\.woff2)\)", css)):
        shutil.copy2(base / "files" / fname, dst / fname)
    css = re.sub(r"url\(\./files/([^)]+?\.woff2)\)", lambda m: f"url(fonts/{slug}/{m.group(1)})", css)
    css = re.sub(r",\s*url\(\./files/[^)]+?\.woff\) format\('woff'\)", "", css)
    css = re.sub(r"font-display:\s*swap;", "font-display: block;", css)
    return css


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.stat().st_size == src.stat().st_size and dst.stat().st_mtime >= src.stat().st_mtime:
            return
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


# ------------------------------------------------------------------ graphics markup
def card_cls(theme) -> str:
    return "card"


def gfx_markup(g: dict, theme: dict) -> str:
    t = g["type"]
    if t == "hook-title":
        kick = f'<div class="kicker">{md(g["kicker"])}</div>' if g.get("kicker") else ""
        box = " boxed" if theme.get("title", {}).get("box") else ""
        return f'{kick}<div class="headline{box}">{words_html(g["text"], "hw")}</div>'
    if t == "keyword":
        return f'<div class="kw">{icon(g.get("icon"))}<span class="kw-text">{md(g["text"])}</span></div>'
    if t == "stat":
        v = g["value"]
        dec = len(str(v).split(".")[1]) if "." in str(v) else 0
        label = f'<div class="stat-label">{md(g["label"])}</div>' if g.get("label") else ""
        return (f'<div class="card stat"><div class="stat-num"><span class="pre">{esc(g.get("prefix", ""))}</span>'
                f'<span class="num" data-to="{v}" data-dec="{dec}">{esc(g.get("from", 0))}</span>'
                f'<span class="suf">{esc(g.get("suffix", ""))}</span></div>{label}</div>')
    if t == "list-item":
        total = g.get("total")
        dots = ""
        if total:
            dots = '<div class="li-dots">' + "".join(
                f'<span class="dot{" on" if k + 1 <= int(g.get("index", 1)) else ""}"></span>' for k in range(int(total))) + "</div>"
        return (f'<div class="card li"><div class="li-row"><div class="li-badge">{esc(g.get("index", "•"))}</div>'
                f'<div class="li-text">{md(g["text"])}</div></div>{dots}</div>')
    if t == "callout":
        var = g.get("variant", "tip")
        ttl = g.get("title") or {"tip": "Pro tip", "warning": "Careful", "myth": "Myth", "fact": "Fact",
                                  "note": "Note", "do": "Do", "dont": "Don't"}.get(var, "")
        return (f'<div class="card callout v-{esc(var)}"><div class="co-head">{icon(g.get("icon") or VARIANT_ICON.get(var))}'
                f'<span class="co-title">{md(ttl)}</span></div><div class="co-text">{md(g["text"])}</div></div>')
    if t == "compare":
        L, R = g["left"], g["right"]
        return (f'<div class="cmp"><div class="card cmp-card bad"><div class="cmp-label">{icon(L.get("icon", "x"))}'
                f'<span>{md(L.get("label", "Myth"))}</span></div><div class="cmp-text">{md(L.get("text", ""))}</div></div>'
                f'<div class="card cmp-card good"><div class="cmp-label">{icon(R.get("icon", "check"))}'
                f'<span>{md(R.get("label", "Fact"))}</span></div><div class="cmp-text">{md(R.get("text", ""))}</div></div></div>')
    if t == "checklist":
        title = f'<div class="cl-title">{md(g["title"])}</div>' if g.get("title") else ""
        items = "".join(f'<div class="cl-item"><span class="cl-box">{icon("check", "cl-check")}</span>'
                        f'<span class="cl-text">{md(it)}</span></div>' for it in g["items"])
        return f'<div class="card checklist">{title}{items}</div>'
    if t == "lower-third":
        sub = f'<div class="lt-title">{md(g["title"])}</div>' if g.get("title") else ""
        return f'<div class="lt"><div class="lt-bar"></div><div class="lt-body"><div class="lt-name">{md(g["name"])}</div>{sub}</div></div>'
    if t == "quote":
        attr = f'<div class="q-attr">— {md(g["attribution"])}</div>' if g.get("attribution") else ""
        return f'<div class="quote"><div class="q-mark">“</div><div class="q-text">{md(g["text"])}</div>{attr}</div>'
    if t == "image":
        cap = f'<div class="img-cap">{md(g["caption"])}</div>' if g.get("caption") else ""
        return f'<div class="img-card"><img class="img" src="{esc(g["_asset"])}" alt=""/>{cap}</div>'
    if t == "cta":
        return f'<div class="cta">{icon(g.get("icon", "bookmark"))}<span>{md(g["text"])}</span></div>'
    if t == "chapter":
        return f'<div class="chip">{md(g["text"])}</div>'
    if t == "sticker":
        return f'<div class="sticker">{esc(g["text"])}</div>'
    raise ValueError(t)


# ------------------------------------------------------------------ main build
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--out", help="project dir (default <plan dir>/composition)")
    ap.add_argument("--no-install", action="store_true")
    ap.add_argument("--node-modules", help="existing node_modules containing gsap + @fontsource/*")
    a = ap.parse_args()

    plan_path = Path(a.plan).resolve()
    wd = plan_path.parent
    plan = load_json(plan_path)
    out = Path(a.out).resolve() if a.out else wd / "composition"
    (out / "assets").mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []

    def rel(p):
        p = Path(p)
        return p if p.is_absolute() else wd / p

    tspec = plan.get("theme")
    if isinstance(tspec, str) and tspec.endswith(".json"):
        # relative to the plan like every other path; else relative to the skill (preferences/<brand>.json)
        cand = rel(tspec)
        tspec = str(cand if cand.exists() or Path(tspec).is_absolute() else SKILL_DIR / tspec)
    theme = load_theme(tspec)
    if plan.get("theme_overrides"):
        theme = deep_merge(theme, plan["theme_overrides"])
    M = theme["motion"]
    personality = theme.get("personality", "clean")
    style = plan.get("motion_style") or PERSONALITY_STYLE.get(personality, "slide")

    # --- video + duration
    video = plan.get("video")
    if video:
        vsrc = rel(video)
        if not vsrc.exists():
            die(f"video not found: {vsrc}")
        link_or_copy(vsrc, out / "assets" / "aroll.mp4")
    duration = float(plan.get("duration") or (media_duration(rel(video)) if video else 0))
    if duration <= 0:
        die("plan needs 'duration' when there is no video")

    # --- words (for land_on / until_word)
    words = []
    if plan.get("words") and rel(plan["words"]).exists():
        words = load_words(rel(plan["words"]))["words"]

    def word_t(idx, key):
        if not words:
            die("graphic uses land_on/until_word but plan has no 'words' file")
        if not (0 <= int(idx) < len(words)):
            die(f"word index {idx} out of range (0..{len(words) - 1})")
        return float(words[int(idx)][key])

    # --- face box (for auto placement + camera focus)
    face = {"y0": 420, "y1": 860, "cx": 0.5, "cy": 0.33, "known": False, "present": bool(video)}
    rf = rel(plan.get("reframe", "reframe.json"))
    if rf.exists():
        fb = (load_json(rf).get("face_box_median") or {})
        if fb:
            face = {"y0": round(fb["y0_median"] * CANVAS_H), "y1": round(fb["y1_median"] * CANVAS_H),
                    "cx": round((fb["x0_median"] + fb["x1_median"]) / 2, 3),
                    "cy": round((fb["y0_median"] + fb["y1_median"]) / 2, 3), "known": True, "present": True}
    if plan.get("face_box"):  # manual override [y0,y1] px
        face.update({"y0": plan["face_box"][0], "y1": plan["face_box"][1], "known": True, "present": True})

    # --- captions
    cap_cfg = plan.get("captions") or {}
    caps = None
    if cap_cfg.get("enabled", True) and cap_cfg.get("file") and rel(cap_cfg["file"]).exists():
        caps = load_json(rel(cap_cfg["file"]))
    elif cap_cfg.get("enabled", True) and cap_cfg.get("file"):
        warnings.append(f"captions file {cap_cfg['file']} not found: building without captions")
    cap_style = (caps or {}).get("style") or theme["caption"]["style"]
    cap_theme = deep_merge(theme["caption"], cap_cfg.get("overrides", {}))
    if caps and cap_theme.get("style") and cap_theme["style"] != cap_style:
        warnings.append(f"captions.json was grouped as '{cap_style}' but the theme prefers "
                        f"'{cap_theme['style']}'. Re-run make_captions.py --style {cap_theme['style']} for best fit.")
    cap_bottom = int(cap_cfg.get("bottom", 1240))

    # --- graphics: validate + resolve timing
    gfx = []
    for n, g in enumerate(plan.get("graphics", [])):
        g = dict(g)
        t = g.get("type")
        if t not in REQUIRED:
            die(f"graphic #{n}: unknown type '{t}'. Types: {', '.join(REQUIRED)}")
        for req in REQUIRED[t]:
            if req not in g:
                die(f"graphic #{n} ({t}) needs '{req}'")
        def cut_idx(src_index):  # SOURCE word index -> cut-timeline index via src_i
            hit = [w["i"] for w in words if w.get("src_i") == int(src_index)]
            if not hit:
                die(f"graphic #{n}: source word {src_index} was cut out (not in the words file)")
            return hit[0]

        for key in ("land_on", "until_word", "reveal_word"):
            if f"{key}_src" in g and key not in g:
                g[key] = cut_idx(g[f"{key}_src"])
        if "item_words_src" in g and "item_words" not in g:
            g["item_words"] = [cut_idx(x) for x in g["item_words_src"]]
        if "reveal_word" in g and "reveal_at" not in g:
            g["reveal_at"] = round(word_t(g["reveal_word"], "start") - M["in"], 3)
        if "item_words" in g and "item_times" not in g:
            g["item_times"] = [round(word_t(x, "start") - 0.05, 3) for x in g["item_words"]]
        if t == "callout" and g.get("variant", "tip") not in VARIANT_ICON:
            die(f"graphic #{n}: callout variant '{g.get('variant')}' unknown. Use: {', '.join(VARIANT_ICON)}")
        g.setdefault("id", f"g{n + 1}")
        if not re.fullmatch(r"[A-Za-z][\w-]*", g["id"]):
            die(f"graphic id '{g['id']}' must start with a letter (letters, digits, - _)")
        if "start" in g:
            st = float(g["start"])
        elif "land_on" in g:
            st = word_t(g["land_on"], "start") - M["in"]
        else:
            die(f"graphic {g['id']} needs 'start' or 'land_on' (word index)")
        if "end" in g:
            en = float(g["end"])
        elif "until_word" in g:
            en = word_t(g["until_word"], "end") + 0.35
        else:
            en = st + float(g.get("hold", DEFAULT_HOLD[t]))
        st, en = max(0.0, st), min(duration, en)
        if en - st < M["in"] + M["out"] + 0.3:
            warnings.append(f"{g['id']} ({t}) is only {en - st:.2f}s on screen: too short to read")
        g["_start"], g["_end"] = round(st, 3), round(en, 3)
        g["region"] = g.get("region", DEFAULT_REGION[t])
        if t in ("image", "broll"):
            src = rel(g["src"])
            if not src.exists():
                die(f"{g['id']}: asset not found {src}")
            dst_name = f"{g['id']}{src.suffix.lower()}"
            link_or_copy(src, out / "assets" / dst_name)
            g["_asset"] = f"assets/{dst_name}"
        gfx.append(g)
    gfx.sort(key=lambda x: x["_start"])
    heroes = [g for g in gfx if g["type"] not in ("chapter", "lower-third", "sticker")]
    for p, q in zip(heroes, heroes[1:]):  # small overlaps (land_on/until_word padding) are trimmed: 0.15 s gap
        if -0.15 < p["_end"] - q["_start"] <= 0.8 and not (p.get("allow_overlap") or q.get("allow_overlap")) \
                and "end" not in p:
            p["_end"] = round(max(p["_start"] + M["in"] + M["out"] + 0.2, q["_start"] - 0.15), 3)
    for i, p in enumerate(heroes):
        for q in heroes[i + 1:]:
            if q["_start"] < p["_end"] - 0.05 and not (p.get("allow_overlap") or q.get("allow_overlap")):
                warnings.append(f"{p['id']} and {q['id']} overlap in time ({q['_start']:.2f} < {p['_end']:.2f}): "
                                "one hero graphic at a time (director/choreography.md)")
    for g in gfx:
        t, st, en = g["type"], g["_start"], g["_end"]
        # reading-time sanity (after trimming): ~0.5 s + 0.25 s per word of on-screen text
        txt = " ".join(str(g.get(k, "")) for k in ("text", "label", "kicker", "title", "name"))
        if t == "compare":
            txt += " " + str(g["left"].get("text", "")) + " " + str(g["right"].get("text", ""))
        if t == "checklist":
            txt += " " + " ".join(map(str, g["items"]))
        need_s = 0.5 + 0.25 * len(txt.split())
        if t not in ("broll", "image", "sticker") and (en - st) < need_s:
            warnings.append(f"{g['id']} ({t}) holds {en - st:.1f}s but its text needs ~{need_s:.1f}s to read")
        # secondary timings must fall inside the graphic's window
        if "reveal_at" in g and not (st + 0.2 <= float(g["reveal_at"]) <= en - 0.6):
            warnings.append(f"{g['id']}: reveal_at {g['reveal_at']} is outside {st:.2f}-{en:.2f}; clamped")
            g["reveal_at"] = round(min(max(float(g["reveal_at"]), st + 0.2), en - 0.6), 3)
        if "item_times" in g:
            if len(g["item_times"]) != len(g.get("items", [])):
                die(f"{g['id']}: item_times/item_words needs one entry per item")
            fixed = [round(min(max(float(x), st + 0.1), en - 0.4), 3) for x in g["item_times"]]
            if fixed != [round(float(x), 3) for x in g["item_times"]]:
                warnings.append(f"{g['id']}: some item_times were outside {st:.2f}-{en:.2f}; clamped")
            g["item_times"] = fixed

    # --- camera
    cam = plan.get("camera") or {}
    amb = deep_merge(theme.get("ambient", {}), plan.get("ambient", {}))
    drift = float(cam.get("drift_zoom", amb.get("drift_zoom", 0.0)))
    punch = float(cam.get("punch_scale", 1.1))
    focus = cam.get("focus") or [face["cx"], face["cy"]]
    changes = []  # (t, scale, dur)
    if cam.get("auto_punch_on_cuts"):
        cuts = cam.get("cuts")
        if isinstance(cuts, str) or cuts is None:
            er = rel(cuts or "edl.resolved.json")
            cuts = load_json(er).get("cuts", []) if er.exists() else []
            if not cuts:
                warnings.append("auto_punch_on_cuts: no cuts found (edl.resolved.json missing?)")
        level, last_t = 1.0, -9.0
        for t in cuts:
            if t - last_t < float(cam.get("min_gap", 1.2)) or t > duration - 0.3:
                continue
            level = punch if level == 1.0 else 1.0
            changes.append((round(float(t), 3), level, 0.0))
            last_t = t
    explicit = [(float(e["at"]), float(e.get("scale", punch)),
                 float(e.get("dur", 0.5)) if e.get("mode", "cut") == "smooth" else 0.0) for e in cam.get("events", [])]
    # explicit events win: drop auto punches within 0.1 s of an explicit change
    changes = [c for c in changes if all(abs(c[0] - e[0]) > 0.1 for e in explicit)] + explicit
    changes.sort(key=lambda c: c[0])
    segs, cur_t, cur_s = [], 0.0, 1.0
    for t, s, d in changes + [(duration, None, 0.0)]:
        if t > cur_t:
            seg_len = t - cur_t
            segs.append({"t": round(cur_t, 3), "d": round(seg_len, 3), "s0": cur_s,
                         "s1": round(cur_s * (1 + drift * min(1.0, seg_len / 5.0)), 4), "ease": "none"})
        if s is None:
            break
        if d > 0:
            segs.append({"t": round(t, 3), "d": round(d, 3), "s0": segs[-1]["s1"] if segs else cur_s, "s1": s,
                         "ease": "power2.inOut"})
            cur_t, cur_s = t + d, s
        else:
            cur_t, cur_s = t, s

    # --- fonts
    texts = []
    for g in gfx:
        texts.append(json.dumps({k: v for k, v in g.items() if not k.startswith("_")}, ensure_ascii=False))
    if caps:
        texts += [w["display"] for pg in caps["pages"] for w in pg["words"]]
    alltext = " ".join(texts)
    font_specs = [(theme["fonts"]["display"]["package"], int(theme["fonts"]["display"]["weight"])),
                  (theme["fonts"]["body"]["package"], int(theme["fonts"]["body"]["weight"]))]
    font_specs.append((theme["fonts"]["body"]["package"], 800))  # kickers, labels, list text
    if caps:
        font_specs.append((theme["fonts"]["body"]["package"], int(cap_theme.get("weight", 700))))
    fallback_families = []
    for rx, fam, pkg in SCRIPT_FONTS:
        if re.search(rx, alltext):
            fallback_families.append(fam)
            for w in {400, 700}:
                font_specs.append((pkg, w))
    font_specs = sorted(set(font_specs))
    pkgs = sorted({p for p, _ in font_specs} | {"gsap"})
    nm = npm_ensure(pkgs, a.node_modules, not a.no_install)
    font_css = "\n".join(vendor_font(nm, p, w, out) for p, w in font_specs)
    (out / "vendor").mkdir(exist_ok=True)
    shutil.copy2(nm / "gsap" / "dist" / "gsap.min.js", out / "vendor" / "gsap.min.js")

    def fam(f):
        return ", ".join([f"'{f['family']}'"] + [f"'{x}'" for x in fallback_families] + ["sans-serif"])

    C = theme["colors"]
    R = theme.get("shape", {}).get("radius", 24)
    PAD = theme.get("shape", {}).get("pad", 32)
    case = {"upper": "uppercase", "lower": "lowercase"}.get(cap_theme.get("case"), "none")
    tcase = {"upper": "uppercase", "lower": "lowercase"}.get(theme.get("title", {}).get("case"), "none")
    progress = plan.get("progress_bar", amb.get("progress_bar", False))

    # --- markup
    body = []
    bg = plan.get("background") or C.get("cover_bg", "#000")
    if video:
        body.append('<div id="cam"><video id="aroll" src="assets/aroll.mp4" playsinline data-has-audio="true" '
                    f'data-start="0" data-duration="{duration:.3f}" data-track-index="0"></video></div>')
    body.append('<div id="scrim-top" class="scrim"></div>')
    if caps and amb.get("scrim_bottom", True):
        body.append('<div id="scrim-bottom" class="scrim"></div>')
    track = 2
    runtime_gfx = []
    for g in gfx:
        dur = g["_end"] - g["_start"]
        common = f'data-start="{g["_start"]:.3f}" data-duration="{dur:.3f}" data-track-index="{track}"'
        if g["type"] == "broll":
            ms = float(g.get("media_start", 0))
            layout = g.get("layout", "cover")
            body.append(f'<div id="{g["id"]}-wrap" class="broll-wrap l-{layout}"><video id="{g["id"]}" class="broll" '
                        f'src="{esc(g["_asset"])}" muted playsinline {common} data-media-start="{ms:.3f}"></video></div>')
        else:
            cover = '<div class="cover-bg"></div>' if g["region"] == "cover" else ""
            body.append(f'<div id="{g["id"]}" class="clip gfx t-{g["type"]}" {common}>{cover}'
                        f'<div class="gfx-pos"><div class="gfx-anim">{gfx_markup(g, theme)}</div></div></div>')
        track += 1
        rg = {k: v for k, v in g.items() if k in ("id", "type", "region", "reveal_at", "item_times", "count_dur",
                                                    "layout", "ken_burns")}
        rg.update({"start": g["_start"], "end": g["_end"]})
        runtime_gfx.append(rg)
    cap_pages = []
    if caps:
        body.append('<div id="caps">')
        for pg in caps["pages"]:
            pid = re.sub(r"[^\w-]", "", str(pg["id"]))
            dur = max(0.05, pg["end"] - pg["start"])
            lines_html = []
            for ln in range(pg.get("lines", 1)):
                spans = []
                for j, w in enumerate(pg["words"]):
                    if w.get("line", 0) != ln:
                        continue
                    cls = "w em" if w.get("emph") else "w"
                    spans.append(f'<span class="{cls}" id="{pid}w{j}">{esc(w["display"])}</span>')
                lines_html.append(f'<div class="cap-line">{" ".join(spans)}</div>')
            body.append(f'<div id="{pid}" class="clip cap" data-start="{pg["start"]:.3f}" data-duration="{dur:.3f}" '
                        f'data-track-index="{track}"><div class="cap-inner">{"".join(lines_html)}</div></div>')
            cap_pages.append({"id": pid, "start": pg["start"], "end": pg["end"],
                              "words": [{"s": w["start"], "e": w["end"], "emph": bool(w.get("emph"))}
                                        for w in pg["words"]]})
        body.append("</div>")
    if progress:
        body.append('<div id="progress"></div>')
    body.append('<div id="measure" aria-hidden="true"></div>')

    runtime = {"duration": duration, "style": style, "motion": M, "personality": personality,
               "face": face, "capTop": cap_bottom - 250, "capStyle": cap_style,
               "highlight": cap_theme.get("highlight", "pill"), "colors": C,
               "capEmph": cap_theme.get("emph", C["accent"]), "gfx": runtime_gfx,
               "caps": cap_pages, "cam": segs, "progress": bool(progress), "scrimTop": amb.get("scrim_top", True),
               "titleMax": theme.get("title", {}).get("size", 104)}

    css = CSS.replace("/*FONTS*/", font_css)
    for k, v in {"--text": C["text"], "--shadow": C["shadow"], "--accent": C["accent"], "--on-accent": C["on_accent"],
                 "--card": C["card"], "--on-card": C["on_card"], "--muted": C["muted"], "--pos": C["positive"],
                 "--neg": C["negative"], "--warn": C["warning"], "--cover-bg": C["cover_bg"], "--radius": f"{R}px",
                 "--pad": f"{PAD}px", "--font-display": fam(theme["fonts"]["display"]),
                 "--font-body": fam(theme["fonts"]["body"]), "--cap-size": f"{cap_theme.get('size', 64)}px",
                 "--cap-weight": str(cap_theme.get("weight", 800)), "--cap-case": case, "--title-case": tcase,
                 "--display-weight": str(theme["fonts"]["display"]["weight"]),
                 "--body-weight": str(theme["fonts"]["body"]["weight"]),
                 "--cap-bottom": f"{CANVAS_H - cap_bottom}px", "--bg": bg,
                 "--focus": f"{focus[0] * 100:.1f}% {focus[1] * 100:.1f}%",
                 "--cap-emph": cap_theme.get("emph", C["accent"])}.items():
        css = css.replace(f"{k}:;", f"{k}: {v};")
    if cap_theme.get("box"):
        css += "\n.cap-inner{background:rgba(0,0,0,0.55);border-radius:14px;padding:10px 22px;}\n"
    page = (HTML.replace("/*CSS*/", css)
            .replace("<!--BODY-->", "\n    ".join(body))
            .replace("/*RUNTIME*/", json.dumps(runtime, ensure_ascii=False))
            .replace("/*JS*/", JS)
            .replace("__DUR__", f"{duration:.3f}"))
    (out / "index.html").write_text(page, encoding="utf-8")
    pkg_json = {"name": "reel", "private": True, "type": "module",
                "scripts": {"check": "npx --yes hyperframes check", "preview": "npx --yes hyperframes preview",
                            "snapshot": "npx --yes hyperframes snapshot --at 1,3,6",
                            "render": "npx --yes hyperframes render --quality delivery --output ../renders/graphics.mp4"}}
    save_json(pkg_json, out / "package.json")

    # --- report
    log(f"[build] {out / 'index.html'}  ({duration:.2f}s, theme={theme.get('name')}, style={style}, "
        f"{len(gfx)} graphics, {len(cap_pages)} caption pages, {len(changes)} camera changes)")
    for g in gfx:
        log(f"   {g['id']:<8} {g['type']:<12} {g['_start']:6.2f}-{g['_end']:6.2f}s  region={g['region']}")
    if not face["known"] and face["present"]:
        warnings.append("no face box (reframe.json): region 'auto' assumes the face sits at y 420-860px. "
                        "Check snapshots for text over the face.")
    for wmsg in warnings:
        log(f"  ! {wmsg}")
    save_json({"warnings": warnings, "graphics": [{"id": g["id"], "type": g["type"], "start": g["_start"],
                                                    "end": g["_end"], "region": g["region"]} for g in gfx],
               "camera": segs, "face": face}, out / "build-report.json")


# ------------------------------------------------------------------ templates
HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Reel</title>
    <script src="vendor/gsap.min.js"></script>
    <style>
/*CSS*/
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="reel" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920">
    <!--BODY-->
    </div>
    <script>
const R = /*RUNTIME*/;
/*JS*/
    </script>
  </body>
</html>
"""

CSS = """/*FONTS*/
:root {
  --text:; --shadow:; --accent:; --on-accent:; --card:; --on-card:; --muted:; --pos:; --neg:; --warn:;
  --cover-bg:; --radius:; --pad:; --font-display:; --font-body:; --cap-size:; --cap-weight:; --cap-case:;
  --title-case:; --display-weight:; --body-weight:; --cap-bottom:; --bg:; --focus:; --cap-emph:;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: #000; }
#root { position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--bg);
  font-family: var(--font-body); font-weight: var(--body-weight); color: var(--text);
  -webkit-font-smoothing: antialiased; text-rendering: geometricPrecision; }
#cam { position: absolute; inset: 0; transform-origin: var(--focus); }
#aroll { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
.scrim { position: absolute; left: 0; right: 0; pointer-events: none; opacity: 0; }
#scrim-top { top: 0; height: 900px; background: linear-gradient(to bottom, rgba(0,0,0,0.55), rgba(0,0,0,0.25) 55%, rgba(0,0,0,0)); }
#scrim-bottom { top: 860px; height: 1060px; opacity: 1;
  background: linear-gradient(to bottom, rgba(0,0,0,0), rgba(0,0,0,0.38) 30%, rgba(0,0,0,0.5) 60%, rgba(0,0,0,0.55)); }
.gfx { position: absolute; inset: 0; pointer-events: none; }
.gfx-pos { position: absolute; left: 70px; right: 70px; top: 270px; display: flex; justify-content: center; }
.gfx-anim { display: flex; flex-direction: column; align-items: center; max-width: 940px; }
.cover-bg { position: absolute; inset: 0; background: var(--cover-bg); opacity: 0; }
.em { color: var(--accent); }
.card { background: var(--card); color: var(--on-card); border-radius: var(--radius); padding: var(--pad);
  box-shadow: 0 18px 50px rgba(0,0,0,0.35); }
.card .em { color: var(--accent); }
.ico { width: 1em; height: 1em; flex: none; }
/* hook title */
.kicker { display: inline-block; font-family: var(--font-body); font-weight: 800; font-size: 34px; letter-spacing: 0.06em;
  text-transform: uppercase; background: var(--accent); color: var(--on-accent); border-radius: 999px; padding: 10px 26px;
  margin-bottom: 22px; }
.headline { font-family: var(--font-display); font-weight: var(--display-weight); line-height: 1.06; text-align: center;
  text-transform: var(--title-case); letter-spacing: -0.01em; text-shadow: 0 6px 30px var(--shadow), 0 2px 6px var(--shadow);
  width: 940px; }
.headline.boxed { background: var(--card); color: var(--on-card); border-radius: var(--radius); padding: 22px 34px; text-shadow: none; }
.hw { display: inline-block; }
/* keyword */
.kw { display: flex; align-items: center; gap: 18px; background: var(--accent); color: var(--on-accent);
  font-family: var(--font-display); font-weight: var(--display-weight); font-size: 92px; line-height: 1.0;
  padding: 20px 40px; border-radius: var(--radius); text-transform: var(--title-case); text-align: center;
  box-shadow: 0 16px 50px rgba(0,0,0,0.35); max-width: 940px; }
.kw .em { color: var(--on-accent); text-decoration: underline; }
/* stat */
.stat { text-align: center; min-width: 560px; }
.stat-num { font-family: var(--font-display); font-weight: var(--display-weight); font-size: 180px; line-height: 1.0;
  color: var(--accent); font-variant-numeric: tabular-nums; }
.stat-num .pre, .stat-num .suf { font-size: 0.55em; }
.stat-label { font-size: 46px; line-height: 1.2; margin-top: 10px; color: var(--on-card); max-width: 820px; }
/* list item */
.li { min-width: 700px; max-width: 940px; }
.li-row { display: flex; align-items: center; gap: 28px; }
.li-badge { flex: none; width: 104px; height: 104px; border-radius: 50%; background: var(--accent); color: var(--on-accent);
  display: flex; align-items: center; justify-content: center; font-family: var(--font-display);
  font-weight: var(--display-weight); font-size: 60px; }
.li-text { font-family: var(--font-body); font-weight: 800; font-size: 56px; line-height: 1.15; }
.li-dots { display: flex; gap: 12px; justify-content: center; margin-top: 22px; }
.dot { width: 16px; height: 16px; border-radius: 50%; background: var(--muted); opacity: 0.5; }
.dot.on { background: var(--accent); opacity: 1; }
/* callout */
.callout { max-width: 900px; min-width: 640px; }
.co-head { display: flex; align-items: center; gap: 14px; font-size: 40px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--accent); margin-bottom: 14px; }
.callout.v-warning .co-head, .callout.v-dont .co-head { color: var(--warn); }
.callout.v-myth .co-head { color: var(--neg); }
.callout.v-fact .co-head, .callout.v-do .co-head { color: var(--pos); }
.co-text { font-size: 50px; line-height: 1.22; font-weight: 700; }
/* compare */
.cmp { display: flex; flex-direction: column; gap: 30px; width: 900px; }
.cmp-card { width: 100%; }
.cmp-label { display: flex; align-items: center; gap: 14px; font-size: 40px; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.05em; margin-bottom: 12px; }
.cmp-card.bad .cmp-label { color: var(--neg); }
.cmp-card.good .cmp-label { color: var(--pos); }
.cmp-text { font-size: 50px; line-height: 1.2; font-weight: 700; }
.cmp-card.bad .cmp-text { opacity: 0.85; }
/* checklist */
.checklist { min-width: 720px; max-width: 920px; }
.cl-title { font-family: var(--font-display); font-weight: var(--display-weight); font-size: 56px; margin-bottom: 18px; }
.cl-item { display: flex; align-items: center; gap: 22px; font-size: 48px; font-weight: 700; line-height: 1.2; padding: 10px 0; }
.cl-box { flex: none; width: 60px; height: 60px; border-radius: 14px; border: 4px solid var(--muted);
  display: flex; align-items: center; justify-content: center; }
.cl-check { width: 42px; height: 42px; color: var(--pos); opacity: 0; }
/* lower third */
.lt { display: flex; align-items: stretch; gap: 20px; }
.lt-bar { width: 12px; border-radius: 6px; background: var(--accent); }
.lt-name { font-family: var(--font-display); font-weight: var(--display-weight); font-size: 54px; line-height: 1.1;
  text-shadow: 0 4px 18px var(--shadow); }
.lt-title { font-size: 36px; color: var(--muted); margin-top: 6px; text-shadow: 0 3px 12px var(--shadow); }
/* quote */
.quote { text-align: center; max-width: 900px; }
.q-mark { font-family: var(--font-display); font-size: 220px; line-height: 0.7; color: var(--accent); }
.q-text { font-family: var(--font-display); font-weight: var(--display-weight); font-size: 70px; line-height: 1.18; }
.q-attr { font-size: 38px; color: var(--muted); margin-top: 26px; }
/* image */
.img-card { background: var(--card); border-radius: var(--radius); padding: 16px; box-shadow: 0 18px 50px rgba(0,0,0,0.4); }
.img { display: block; max-width: 860px; max-height: 760px; border-radius: calc(var(--radius) - 8px); object-fit: cover; }
.img-cap { font-size: 38px; text-align: center; padding: 14px 8px 4px; color: var(--on-card); }
/* b-roll */
.broll-wrap { position: absolute; opacity: 0; overflow: hidden; }
.broll-wrap.l-cover { inset: 0; }
.broll-wrap.l-card { left: 90px; right: 90px; top: 300px; height: 900px; border-radius: var(--radius);
  box-shadow: 0 24px 60px rgba(0,0,0,0.45); }
.broll { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }
/* cta */
.cta { display: flex; align-items: center; gap: 18px; background: var(--accent); color: var(--on-accent);
  font-family: var(--font-body); font-weight: 800; font-size: 48px; padding: 22px 40px; border-radius: 999px;
  box-shadow: 0 16px 44px rgba(0,0,0,0.35); }
/* chapter chip */
.chip { display: inline-block; background: var(--card); color: var(--on-card); font-weight: 800; font-size: 32px;
  letter-spacing: 0.08em; text-transform: uppercase; padding: 12px 24px; border-radius: 999px; }
/* sticker */
.sticker { font-size: 150px; line-height: 1; filter: drop-shadow(0 10px 24px rgba(0,0,0,0.35)); }
/* captions */
#caps { position: absolute; inset: 0; pointer-events: none; }
.cap { position: absolute; left: 140px; right: 140px; bottom: var(--cap-bottom); display: flex; justify-content: safe center; }
.cap-inner { text-align: center; font-family: var(--font-body); font-weight: var(--cap-weight); font-size: var(--cap-size);
  line-height: 1.16; text-transform: var(--cap-case); color: var(--text);
  text-shadow: 0 2px 4px rgba(0,0,0,0.9), 0 4px 18px rgba(0,0,0,0.6); }
.cap-line { white-space: nowrap; }
.w { display: inline-block; padding: 0 0.12em; border-radius: 0.22em; }
.w.em { color: var(--cap-emph); }
#progress { position: absolute; left: 0; top: 0; width: 1080px; height: 8px; background: var(--accent); transform-origin: 0 50%; }
#measure { position: absolute; left: -3000px; top: 0; width: 1080px; visibility: hidden; }"""

JS = r"""
const M = R.motion;
const $ = (id) => document.getElementById(id);
const TOP = 270;

function fitText(el, maxPx, minPx, maxLines, lh) {
  let s = maxPx;
  el.style.fontSize = s + 'px';
  while (s > minPx && (el.scrollHeight > Math.ceil(s * lh * maxLines) + 4 || el.scrollWidth > el.clientWidth + 2)) {
    s -= 2; el.style.fontSize = s + 'px';
  }
  return s;
}

// Clips outside their time window may be hidden, so all fitting/measuring happens on an
// off-canvas clone inside #measure; results are copied back onto the real nodes.
function fitAndMeasure(pos) {
  const m = $('measure');
  const c = pos.cloneNode(true);
  m.appendChild(c);
  const rules = [['.headline', R.titleMax, 60, 3, 1.06], ['.kw', 92, 54, 2, 1.0], ['.q-text', 70, 46, 6, 1.18],
                 ['.co-text', 50, 36, 5, 1.22], ['.li-text', 56, 40, 3, 1.15]];
  for (const [sel, mx, mn, lines, lh] of rules) {
    const src = pos.querySelector(sel), dst = c.querySelector(sel);
    if (src && dst) src.style.fontSize = fitText(dst, mx, mn, lines, lh) + 'px';
  }
  const h = c.getBoundingClientRect().height;
  m.removeChild(c);
  return h;
}

function placeGraphic(g, clip, reserved) {
  // reserved = bands {y0, y1} held by secondary elements (chapter chip, lower-third) during this graphic
  const pos = clip.querySelector('.gfx-pos');
  if (!pos) return;
  if (g.type === 'lower-third') { pos.style.left = '80px'; pos.style.right = 'auto'; pos.style.justifyContent = 'flex-start'; }
  if (g.type === 'chapter') { pos.style.left = '70px'; pos.style.right = 'auto'; }
  const h = fitAndMeasure(pos);
  const F = R.face, capTop = R.capTop;
  let topLimit = TOP, lowLimit = capTop - 10;               // usable vertical band for this graphic
  for (const r of reserved || []) {
    if (r.y0 < 700) topLimit = Math.max(topLimit, r.y1 + 16);
    else lowLimit = Math.min(lowLimit, r.y0 - 16);
  }
  const bLimit = Math.min(capTop - 24, lowLimit);
  let top = topLimit, scale = 1;
  const region = g.type === 'chapter' ? 'chip' : (g.region || 'auto');
  if (region === 'chip') top = TOP;
  else if (region === 'top') top = topLimit;
  else if (region === 'middle') top = Math.min(Math.max(820 - h / 2, topLimit), bLimit - h);
  else if (region === 'lower') top = lowLimit - h;           // sits just above the caption band
  else if (region === 'lower-third') top = capTop - 40 - h;
  else if (region === 'cover') top = topLimit + Math.max(0, (capTop - 30 - topLimit - h) / 2);
  else if (!F.present) top = topLimit + Math.max(0, (bLimit - topLimit - h) / 2);   // faceless: centre
  else {                                  // auto: biggest free band above / below the face
    const A = [topLimit, F.y0 - 30], B = [Math.max(F.y1 + 30, topLimit), bLimit];
    const ha = A[1] - A[0], hb = B[1] - B[0];
    if (h <= ha) top = A[0];
    else if (h <= hb) top = B[0] + (hb - h) / 2;
    else {
      const band = ha >= hb ? A : B, room = Math.max(ha, hb);
      scale = Math.max(0.72, room / h);
      top = band[0] + Math.max(0, (room - h * scale) / 2);
      if (h * scale > room + 1) console.warn('[reel] ' + g.id + ' cannot avoid the face; consider region "cover"');
    }
  }
  pos.style.top = Math.round(top) + 'px';
  if (scale < 1) { pos.style.transformOrigin = '50% 0'; pos.style.transform = 'scale(' + scale.toFixed(3) + ')'; }
  g._top = top; g._h = h * scale;
}

// Captions are nowrap lines: shrink any page whose widest line exceeds the 800 px band (min 0.72x).
function fitCaptions() {
  const m = $('measure');
  const maxW = 800;
  for (const p of R.caps) {
    const inner = $(p.id) && $(p.id).querySelector('.cap-inner');
    if (!inner) continue;
    const c = inner.cloneNode(true);
    c.removeAttribute('id');
    c.querySelectorAll('[id]').forEach((n) => n.removeAttribute('id'));
    c.style.display = 'inline-block';
    m.appendChild(c);
    let widest = 0;
    c.querySelectorAll('.cap-line').forEach((ln) => { widest = Math.max(widest, ln.scrollWidth); });
    m.removeChild(c);
    if (widest > maxW) {
      const base = parseFloat(getComputedStyle(inner).fontSize);
      inner.style.fontSize = Math.max(base * 0.72, Math.floor(base * maxW / widest)) + 'px';
    }
  }
}

function enter(tl, el, t, kind) {
  const d = M.in, s = R.style;
  if (kind === 'fade' || s === 'fade') return tl.fromTo(el, {opacity: 0, y: 18}, {opacity: 1, y: 0, duration: d, ease: M.ease_in}, t);
  if (s === 'reveal') return tl.fromTo(el, {opacity: 0, clipPath: 'inset(0% 0% 100% 0%)', y: 10},
    {opacity: 1, clipPath: 'inset(0% 0% 0% 0%)', y: 0, duration: d, ease: M.ease_in}, t);
  if (s === 'pop') return tl.fromTo(el, {opacity: 0, scale: 0.7, rotation: R.personality === 'playful' ? -3 : 0},
    {opacity: 1, scale: 1, rotation: 0, duration: d, ease: M.pop}, t);
  return tl.fromTo(el, {opacity: 0, y: 36}, {opacity: 1, y: 0, duration: d, ease: M.ease_in}, t);
}

function exit(tl, el, t) {
  const s = R.style;
  const to = s === 'pop' ? {opacity: 0, scale: 0.92} : (s === 'reveal' ? {opacity: 0} : {opacity: 0, y: -18});
  tl.to(el, Object.assign(to, {duration: M.out, ease: M.ease_out}), Math.max(t - M.out, 0));
}

function buildGraphic(tl, g) {
  if (g.type === 'broll') {
    const w = $(g.id + '-wrap');
    tl.fromTo(w, {opacity: 0}, {opacity: 1, duration: 0.18, ease: 'power1.out'}, g.start);
    if (g.ken_burns !== false) tl.fromTo(w, {scale: 1.0}, {scale: 1.06, duration: g.end - g.start, ease: 'none'}, g.start);
    tl.to(w, {opacity: 0, duration: 0.15, ease: 'power1.in'}, g.end - 0.15);
    return;
  }
  const clip = $(g.id);
  const anim = clip.querySelector('.gfx-anim');
  const cover = clip.querySelector('.cover-bg');
  if (cover) {
    tl.fromTo(cover, {opacity: 0}, {opacity: 0.94, duration: 0.25, ease: 'power1.out'}, g.start);
    tl.to(cover, {opacity: 0, duration: 0.22, ease: 'power1.in'}, g.end - 0.22);
  }
  const t0 = g.start;
  switch (g.type) {
    case 'hook-title': {
      const k = anim.querySelector('.kicker');
      const ws = anim.querySelectorAll('.hw');
      tl.set(anim, {opacity: 1}, t0);
      if (k && t0 >= 0.05) tl.fromTo(k, {opacity: 0, y: 20, scale: 0.9}, {opacity: 1, y: 0, scale: 1, duration: M.in, ease: M.pop}, t0);
      const st = Math.min(M.stagger, 0.45 / Math.max(1, ws.length));
      if (t0 < 0.05) {
        // frame 0 is the thumbnail and the hook: text must already be readable, so settle instead of fade
        tl.fromTo(anim, {scale: 1.06}, {scale: 1, duration: Math.max(0.35, M.in), ease: M.ease_in}, 0);
      } else {
        tl.fromTo(ws, {opacity: 0, y: R.style === 'fade' ? 20 : 54}, {opacity: 1, y: 0, duration: M.in, ease: M.ease_in, stagger: st}, t0 + (k ? 0.08 : 0));
      }
      break;
    }
    case 'stat': {
      enter(tl, anim, t0);
      const n = anim.querySelector('.num');
      const to = parseFloat(n.dataset.to), dec = parseInt(n.dataset.dec || '0', 10);
      const from = parseFloat(n.textContent) || 0;
      const o = {v: from};
      const fmt = (v) => dec ? v.toFixed(dec) : Math.round(v).toLocaleString('en-US');
      n.textContent = fmt(from);
      tl.to(o, {v: to, duration: g.count_dur || Math.min(1.1, (g.end - g.start) * 0.45), ease: 'power2.out',
        onUpdate: () => { n.textContent = fmt(o.v); }}, t0 + 0.05);
      const lab = anim.querySelector('.stat-label');
      if (lab) tl.fromTo(lab, {opacity: 0, y: 14}, {opacity: 1, y: 0, duration: M.in, ease: M.ease_in}, t0 + 0.2);
      break;
    }
    case 'list-item': {
      enter(tl, anim, t0);
      const b = anim.querySelector('.li-badge');
      tl.fromTo(b, {scale: 0.4}, {scale: 1, duration: Math.max(0.25, M.in), ease: 'back.out(2)'}, t0 + 0.05);
      const tx = anim.querySelector('.li-text');
      tl.fromTo(tx, {opacity: 0, x: -30}, {opacity: 1, x: 0, duration: M.in, ease: M.ease_in}, t0 + 0.12);
      break;
    }
    case 'compare': {
      const cards = anim.querySelectorAll('.cmp-card');
      tl.set(anim, {opacity: 1}, t0);
      enter(tl, cards[0], t0);
      const r = g.reveal_at || (t0 + (g.end - t0) * 0.4);
      enter(tl, cards[1], r);
      tl.to(cards[0], {opacity: 0.55, duration: 0.3, ease: 'power1.out'}, r);
      break;
    }
    case 'checklist': {
      enter(tl, anim, t0);
      const items = anim.querySelectorAll('.cl-item');
      const times = g.item_times || Array.from(items, (_, i) => t0 + 0.4 + i * Math.max(0.5, (g.end - t0 - 1.0) / items.length));
      items.forEach((it, i) => {
        tl.fromTo(it, {opacity: 0.35}, {opacity: 1, duration: 0.2, ease: 'power1.out'}, times[i]);
        tl.fromTo(it.querySelector('.cl-check'), {opacity: 0, scale: 0.3}, {opacity: 1, scale: 1, duration: 0.25, ease: 'back.out(2.5)'}, times[i]);
      });
      break;
    }
    case 'cta': {
      enter(tl, anim, t0);
      const reps = Math.max(0, Math.floor((g.end - t0 - M.in - M.out) / 1.2) - 1);
      if (reps > 0) tl.to(anim.querySelector('.cta'), {scale: 1.04, duration: 0.6, ease: 'sine.inOut', yoyo: true, repeat: reps * 2 - 1}, t0 + M.in + 0.2);
      break;
    }
    case 'keyword': {
      if (R.style === 'slide' || R.style === 'pop') tl.fromTo(anim, {opacity: 0, scale: 0.6}, {opacity: 1, scale: 1, duration: Math.max(0.22, M.in), ease: M.pop}, t0);
      else enter(tl, anim, t0);
      break;
    }
    case 'lower-third': {
      const bar = anim.querySelector('.lt-bar');
      tl.set(anim, {opacity: 1}, t0);
      tl.fromTo(bar, {scaleY: 0}, {scaleY: 1, duration: M.in, ease: M.ease_in}, t0);
      tl.fromTo(anim.querySelector('.lt-body'), {opacity: 0, x: -24}, {opacity: 1, x: 0, duration: M.in, ease: M.ease_in}, t0 + 0.1);
      break;
    }
    case 'image': {
      enter(tl, anim, t0);
      if (g.ken_burns !== false) tl.fromTo(anim.querySelector('.img'), {scale: 1.0}, {scale: 1.05, duration: g.end - t0, ease: 'none'}, t0);
      break;
    }
    case 'sticker': {
      tl.fromTo(anim, {opacity: 0, scale: 0.3, rotation: -12}, {opacity: 1, scale: 1, rotation: 0, duration: 0.35, ease: 'back.out(2.4)'}, t0);
      break;
    }
    default:
      enter(tl, anim, t0);
  }
  exit(tl, anim, g.end);
  if (R.scrimTop && g._top !== undefined && g._top < 700 && g.region !== 'cover') {
    const sc = $('scrim-top');
    tl.to(sc, {opacity: 1, duration: 0.3, ease: 'power1.out'}, t0);
    tl.to(sc, {opacity: 0, duration: 0.3, ease: 'power1.in'}, Math.max(t0 + 0.3, g.end - 0.3));
  }
}

function buildCaptions(tl) {
  const pill = R.highlight === 'pill', col = R.highlight === 'color', und = R.highlight === 'underline';
  for (const p of R.caps) {
    const inner = $(p.id).querySelector('.cap-inner');
    const pop = R.capStyle === 'pop';
    const fadeIn = R.capStyle === 'phrase' || R.capStyle === 'minimal' ? 0.18 : 0.1;
    tl.fromTo(inner, {opacity: 0, y: pop ? 0 : 10}, {opacity: 1, y: 0, duration: fadeIn, ease: 'power2.out'}, p.start);
    tl.to(inner, {opacity: 0, duration: 0.08, ease: 'power1.in'}, Math.max(p.start + fadeIn, p.end - 0.08));
    if (R.highlight === 'none' && !pop) continue;
    p.words.forEach((w, j) => {
      const sp = $(p.id + 'w' + j);
      if (!sp) return;
      if (pop) tl.fromTo(sp, {opacity: 0, scale: 0.6}, {opacity: 1, scale: 1, duration: 0.14, ease: M.pop}, Math.max(p.start, w.s - 0.04));
      const next = j + 1 < p.words.length ? p.words[j + 1].s : Math.min(p.end, w.e + 0.25);
      const base = {color: w.emph ? R.capEmph : R.colors.text, backgroundColor: 'rgba(0,0,0,0)', boxShadow: 'none'};
      let on = null;
      if (pill) on = {color: R.colors.on_accent, backgroundColor: R.colors.accent};
      else if (col) on = {color: R.colors.accent};
      else if (und) on = {boxShadow: 'inset 0 -0.14em 0 ' + R.colors.accent};
      if (on) { tl.set(sp, on, w.s); tl.set(sp, base, Math.max(w.s + 0.05, next)); }
      if (!pop && M.word_pop > 1.001) tl.fromTo(sp, {scale: 1}, {scale: M.word_pop, duration: 0.09, ease: 'power1.out', yoyo: true, repeat: 1}, w.s);
    });
  }
}

function build() {
  const tl = gsap.timeline({paused: true});
  // camera: punch-ins on cuts + slow drift (ambient life)
  const cam = $('cam');
  if (cam) for (const s of R.cam) tl.fromTo(cam, {scale: s.s0}, {scale: s.s1, duration: Math.max(0.001, s.d), ease: s.ease, immediateRender: false}, s.t);
  // text fitting + face-aware placement (fonts are loaded at this point).
  // Secondaries first: their bands are then reserved for any hero visible at the same time.
  const reserved = [];
  for (const g of R.gfx) {
    const clip = $(g.id);
    if (!clip || (g.type !== 'chapter' && g.type !== 'lower-third')) continue;
    placeGraphic(g, clip, []);
    reserved.push({t0: g.start, t1: g.end, y0: g._top, y1: g._top + g._h});
  }
  for (const g of R.gfx) {
    const clip = $(g.id);
    if (!clip || g.type === 'broll' || g.type === 'chapter' || g.type === 'lower-third') continue;
    placeGraphic(g, clip, reserved.filter((r) => r.t0 < g.end && g.start < r.t1));
  }
  fitCaptions();
  for (const g of R.gfx) buildGraphic(tl, g);
  if (R.caps.length) buildCaptions(tl);
  if (R.progress) tl.fromTo('#progress', {scaleX: 0}, {scaleX: 1, duration: R.duration, ease: 'none'}, 0);
  window.__timelines['reel'] = tl;
}

const fontsToCheck = [getComputedStyle(document.documentElement).getPropertyValue('--font-display'),
                      getComputedStyle(document.documentElement).getPropertyValue('--font-body')];
// Load every declared face up front (unicode-range subsets such as emoji or Devanagari otherwise load
// lazily when a clip first shows, and a seek-based renderer captures that frame before the font arrives).
Promise.all(Array.from(document.fonts, (f) => f.load().catch(() => null))).then(() => document.fonts.ready).then(() => {
  for (const f of fontsToCheck) {
    const first = f.split(',')[0].trim();
    if (first && !document.fonts.check('700 64px ' + first)) console.error('[reel] font failed to load: ' + first);
  }
  build();
});
"""

if __name__ == "__main__":
    main()
