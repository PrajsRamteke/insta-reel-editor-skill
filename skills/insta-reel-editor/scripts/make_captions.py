#!/usr/bin/env python3
"""Group cut-timeline words into readable, word-synced caption pages.

Usage:
  python3 make_captions.py transcript/words.cut.json --out captions.json [--style karaoke]
                           [--max-words N] [--max-chars N] [--lines 1|2] [--keywords "breath,73%"]
                           [--keep-fillers] [--punct strip|keep] [--srt captions.srt]

Styles (defaults; see patterns/captions.md):
  karaoke  2-4 words, <=18 chars/line, 2 lines, active word highlighted   (default, most reels)
  pop      1-3 words, <=14 chars, 1 line, each word pops on its start      (hype, energetic)
  phrase   4-8 words, <=26 chars/line, 2 lines, whole phrase fades          (calm, premium, storytelling)
  minimal  3-6 words, <=28 chars/line, 2 lines, small, no highlight         (cinematic, subtle)
Break rules: pause >= threshold, sentence end, comma + pause, word/char/time caps.
Hard constraints: no overlapping pages, each page >= 0.5 s on screen (merged or extended),
page appears ~60 ms before its first word, lingers <= 0.5 s after its last word.
Auto emphasis: numbers/percentages + --keywords. Edit "emph" flags in the JSON to taste.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import SENTENCE_END, is_filler, load_json, log, norm_token, save_json, load_words

STYLES = {
    "karaoke": dict(max_words=4, max_chars=18, lines=2, pause=0.45, max_dur=2.6),
    "pop": dict(max_words=3, max_chars=14, lines=1, pause=0.30, max_dur=1.6),
    "phrase": dict(max_words=8, max_chars=26, lines=2, pause=0.50, max_dur=3.5),
    "minimal": dict(max_words=6, max_chars=28, lines=2, pause=0.50, max_dur=3.2),
}
FUNCTION = {"the", "a", "an", "of", "to", "and", "or", "but", "in", "on", "at", "for", "with", "your", "my", "our",
            "their", "his", "her", "its", "this", "that", "is", "are", "was", "be", "so", "if", "as", "from", "by",
            "i", "you", "we", "they", "it", "not", "no", "very", "too", "just"}
NUMBERISH = re.compile(r"\d|%|\$|₹|€|£")
NUM_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "twenty", "thirty",
             "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion",
             "percent", "half", "double", "triple", "zero"}


def display_text(t: str, punct: str) -> str:
    if punct == "strip":
        t = re.sub(r"[.,;:]+$", "", t)
        t = re.sub(r"^[\"'“”‘’(]+|[\"'“”‘’)]+$", "", t)
    return t


def split_lines(words: list[dict], max_chars: int, lines: int) -> None:
    texts = [w["display"] for w in words]
    total = len(" ".join(texts))
    for w in words:
        w["line"] = 0
    if lines < 2 or total <= max_chars or len(words) < 2:
        return
    best, best_k = None, 1
    for k in range(1, len(words)):
        l1, l2 = len(" ".join(texts[:k])), len(" ".join(texts[k:]))
        score = max(l1, l2) - (3 if re.search(r"[,;:]$", words[k - 1]["text"]) else 0)
        if best is None or score < best:
            best, best_k = score, k
    for w in words[best_k:]:
        w["line"] = 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words")
    ap.add_argument("--out", required=True)
    ap.add_argument("--style", choices=STYLES.keys(), default="karaoke")
    ap.add_argument("--max-words", type=int)
    ap.add_argument("--max-chars", type=int, help="max characters per line")
    ap.add_argument("--lines", type=int, choices=[1, 2])
    ap.add_argument("--pause", type=float, help="silence that forces a new page")
    ap.add_argument("--keywords", default="", help="comma list of words to emphasize (case-insensitive)")
    ap.add_argument("--keep-fillers", action="store_true", help="caption um/uh too (default: hidden)")
    ap.add_argument("--punct", choices=["strip", "keep"], default="strip")
    ap.add_argument("--lead", type=float, default=0.06)
    ap.add_argument("--linger", type=float, default=0.5)
    ap.add_argument("--min-dur", type=float, default=None, help="min page time (default 0.5 s; 0.35 s for pop)")
    ap.add_argument("--offset", type=float, default=0.0,
                    help="shift all word times (s); fixes an engine's constant early/late bias, e.g. -0.06")
    ap.add_argument("--srt", help="also write an SRT (accessibility / other platforms)")
    a = ap.parse_args()

    p = dict(STYLES[a.style])
    for k in ("max_words", "max_chars", "lines", "pause"):
        if getattr(a, k) is not None:
            p[k] = getattr(a, k)
    doc = load_words(a.words)
    kw = {norm_token(k) for k in a.keywords.split(",") if k.strip()}
    words = []
    for w in doc["words"]:
        if w.get("type", "word") != "word":
            continue
        if not a.keep_fillers and is_filler(w["text"]):
            continue
        tok = norm_token(w["text"])
        emph = bool(NUMBERISH.search(w["text"]) or tok in NUM_WORDS or (tok and tok in kw))
        words.append({"i": w["i"], "text": w["text"], "display": display_text(w["text"], a.punct),
                      "start": max(0.0, w["start"] + a.offset), "end": max(0.0, w["end"] + a.offset), "emph": emph})
    words = [w for w in words if w["display"]]
    cap = p["max_chars"] * p["lines"]
    slack = 0 if a.style == "pop" else 4  # pop is one big line: never exceed its width budget
    if a.min_dur is None:
        a.min_dur = 0.35 if a.style == "pop" else 0.5  # pop words appear one by one, so shorter pages read fine

    pages: list[list[dict]] = []
    cur: list[dict] = []
    for w in words:
        if cur:
            prev = cur[-1]
            gap = w["start"] - prev["end"]
            chars = len(" ".join(x["display"] for x in cur + [w]))
            brk = (gap >= p["pause"] or SENTENCE_END.search(prev["text"]) or
                   (re.search(r"[,;:]$", prev["text"]) and (gap >= 0.2 or len(cur) >= 2)) or
                   len(cur) >= p["max_words"] or chars > cap or (w["end"] - cur[0]["start"]) > p["max_dur"])
            if brk:
                pages.append(cur)
                cur = []
        cur.append(w)
    if cur:
        pages.append(cur)

    # readability: don't end a page on a dangling function word ("breathe the / wrong way")
    for k in range(len(pages) - 1):
        pg, nx = pages[k], pages[k + 1]
        while len(pg) > 1 and norm_token(pg[-1]["text"]) in FUNCTION and not re.search(r"[.,!?;:।]$", pg[-1]["text"]) \
                and nx[0]["start"] - pg[-1]["end"] < p["pause"] \
                and len(" ".join(x["display"] for x in [pg[-1]] + nx)) <= cap + slack:
            nx.insert(0, pg.pop())

    # orphans: a lone word left at a sentence end joins the previous page when it is contiguous
    if a.style != "pop":
        k = 1
        while k < len(pages):
            pg, pv = pages[k], pages[k - 1]
            if len(pg) == 1 and pg[0]["start"] - pv[-1]["end"] < 0.35 and \
                    len(" ".join(x["display"] for x in pv + pg)) <= cap + slack and \
                    not SENTENCE_END.search(pv[-1]["text"]):
                pv.extend(pages.pop(k))
                continue
            k += 1

    # merge pages that would flash (< min_dur) into a neighbour when it still fits
    i = 0
    while i < len(pages):
        pg = pages[i]
        dur = pg[-1]["end"] - pg[0]["start"] + a.linger
        if dur < a.min_dur and len(pages) > 1:
            nxt = pages[i + 1] if i + 1 < len(pages) else None
            prv = pages[i - 1] if i > 0 else None
            for tgt, before in ((nxt, True), (prv, False)):
                if tgt is None:
                    continue
                merged = pg + tgt if before else tgt + pg
                gap = (tgt[0]["start"] - pg[-1]["end"]) if before else (pg[0]["start"] - tgt[-1]["end"])
                if len(merged) <= p["max_words"] + (0 if a.style == "pop" else 1) \
                        and len(" ".join(x["display"] for x in merged)) <= cap + slack and gap < 0.8:
                    if before:
                        pages[i + 1] = merged
                        pages.pop(i)
                    else:
                        pages[i - 1] = merged
                        pages.pop(i)
                    i = max(0, i - 1)
                    break
            else:
                i += 1
                continue
            continue
        i += 1

    out_pages = []
    for k, pg in enumerate(pages):
        split_lines(pg, p["max_chars"], p["lines"])
        st = max(0.0, pg[0]["start"] - a.lead)
        if out_pages:
            st = max(st, out_pages[-1]["end"])
        en = pg[-1]["end"] + a.linger
        if k + 1 < len(pages):
            en = min(en, max(pages[k + 1][0]["start"] - a.lead, pg[-1]["end"] + 0.05))
        if en - st < a.min_dur:
            limit = (pages[k + 1][0]["start"] - a.lead) if k + 1 < len(pages) else en + a.min_dur
            en = min(st + a.min_dur, max(en, limit))
        out_pages.append({"id": f"c{k}", "start": round(st, 3), "end": round(en, 3),
                          "lines": 1 + max(w["line"] for w in pg),
                          "words": [{k2: w[k2] for k2 in ("i", "text", "display", "start", "end", "line", "emph")}
                                    for w in pg]})
    res = {"version": 1, "style": a.style, "source": a.words, "params": p, "pages": out_pages}
    save_json(res, a.out)
    flashes = sum(1 for pg in out_pages if pg["end"] - pg["start"] < a.min_dur - 1e-3)
    log(f"[captions] {a.style}: {len(words)} words -> {len(out_pages)} pages"
        + (f" ({flashes} still shorter than {a.min_dur}s: fast speech, fine if rare)" if flashes else "")
        + f" -> {a.out}")

    if a.srt:
        def ts(t):
            h, r = divmod(t, 3600)
            m, s = divmod(r, 60)
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"
        blocks = []
        for n, pg in enumerate(out_pages, 1):
            lines = [" ".join(w["display"] for w in pg["words"] if w["line"] == ln) for ln in range(pg["lines"])]
            blocks.append(f"{n}\n{ts(pg['start'])} --> {ts(pg['end'])}\n" + "\n".join(lines) + "\n")
        Path(a.srt).parent.mkdir(parents=True, exist_ok=True)
        with open(a.srt, "w", encoding="utf-8") as f:
            f.write("\n".join(blocks))


if __name__ == "__main__":
    main()
