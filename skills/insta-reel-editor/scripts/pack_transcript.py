#!/usr/bin/env python3
"""Turn words.json into a compact, time-annotated reading view for the editor (LLM).

Usage:
  python3 pack_transcript.py transcript/words.json --out transcript/phrases.md [--pause 0.5]

phrases.md lists one phrase per line with its time range and word-index range, marks fillers,
pauses, audio events and low-confidence words, then appends three helper sections:
  * possible retakes (same opening words repeated within 15 s -> usually keep the later take)
  * graphic cues (numbers, lists/ordinals, contrasts, questions, warnings)
  * pace stats
Reading this is ~10x cheaper than raw JSON and keeps word-boundary precision via #indices.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import SENTENCE_END, is_filler, load_json, log, norm_token, load_words

NUM_WORDS = {"zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
             "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
             "forty", "fifty", "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million", "billion",
             "percent", "half", "double", "triple"}
ORDINALS = {"first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "step",
            "number", "tip", "mistake", "mistakes", "reason", "reasons", "rule", "rules", "lastly", "finally", "next"}
CONTRAST = {"but", "actually", "instead", "myth", "truth", "wrong", "right", "mistake", "never", "always", "stop",
            "don't", "dont", "avoid", "secret", "nobody", "everyone", "most", "before", "after", "versus", "vs"}
WARN = {"warning", "careful", "dangerous", "never", "avoid", "stop", "injury", "pain", "risk"}


def phrases(words: list[dict], pause: float) -> list[list[dict]]:
    out, cur = [], []
    for i, w in enumerate(words):
        if cur:
            gap = w["start"] - cur[-1]["end"]
            prev_txt = cur[-1]["text"]
            spk_change = w.get("speaker") != cur[-1].get("speaker")
            if gap >= pause or spk_change or (SENTENCE_END.search(prev_txt) and gap >= 0.15):
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def render_word(w: dict) -> str:
    t = w["text"]
    if w.get("type") == "event":
        return t if t.startswith("(") else f"({t})"
    if is_filler(t):
        return "{" + t + "}"
    if w.get("conf") is not None and w["conf"] < 0.4:
        return t + "?"
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words")
    ap.add_argument("--out", required=True)
    ap.add_argument("--pause", type=float, default=0.5, help="silence (s) that starts a new phrase")
    a = ap.parse_args()

    doc = load_words(a.words)
    words = doc["words"] if isinstance(doc, dict) else doc
    if not words:
        Path(a.out).write_text("# Transcript\n\n(no speech)\n", encoding="utf-8")
        return
    ph = phrases(words, a.pause)
    dur = doc.get("duration") or words[-1]["end"]
    n_words = sum(1 for w in words if w.get("type", "word") == "word")
    speech = sum(w["end"] - w["start"] for w in words)
    fillers = [w for w in words if is_filler(w["text"])]
    lines = [f"# Transcript — {dur:.1f} s, {n_words} words ({doc.get('engine', '?')}, lang={doc.get('language', '?')})",
             "",
             "Legend: `[start-end] #first-#last text` · `{um}` filler · `⟨0.9s⟩` pause after phrase · "
             "`(laughs)` audio event · `word?` low confidence · `S1:` speaker change",
             "", "```"]
    last_spk = None
    for p in ph:
        nxt_start = None
        last_idx = p[-1]["i"]
        if last_idx + 1 < len(words):
            nxt_start = words[last_idx + 1]["start"]
        gap = (nxt_start - p[-1]["end"]) if nxt_start is not None else 0
        spk = p[0].get("speaker")
        spk_txt = f"{spk}: " if spk is not None and spk != last_spk and len({w.get('speaker') for w in words}) > 1 else ""
        last_spk = spk
        rng = f"#{p[0]['i']}" + (f"-#{p[-1]['i']}" if len(p) > 1 else "")
        txt = " ".join(render_word(w) for w in p)
        pause_txt = f"  ⟨{gap:.1f}s⟩" if gap >= 0.3 else ""
        lines.append(f"[{p[0]['start']:06.2f}-{p[-1]['end']:06.2f}] {rng:<10} {spk_txt}{txt}{pause_txt}")
    lines.append("```")

    # ---- possible retakes
    def opening(p, k=3):
        toks = [norm_token(w["text"]) for w in p if not is_filler(w["text"]) and w.get("type", "word") == "word"]
        return tuple(t for t in toks[:k] if t)

    retakes = []
    for i, p in enumerate(ph):
        o = opening(p)
        if len(o) < 2:
            continue
        for q in ph[i + 1:]:
            if q[0]["start"] - p[-1]["end"] > 15:
                break
            if opening(q, len(o)) == o:
                retakes.append((p, q))
                break
    lines += ["", "## Possible retakes (same opening words) — usually cut the EARLIER one", ""]
    if retakes:
        for p, q in retakes:
            lines.append(f"- #{p[0]['i']}-#{p[-1]['i']} \"{' '.join(w['text'] for w in p)}\"  ↔  "
                         f"#{q[0]['i']}-#{q[-1]['i']} \"{' '.join(w['text'] for w in q)}\"")
    else:
        lines.append("- none detected (still read for false starts and self-corrections)")

    # ---- graphic cues
    cues = []
    for w in words:
        tok = norm_token(w["text"])
        tags = []
        if re.search(r"\d", w["text"]) or tok in NUM_WORDS:
            tags.append("number")
        if tok in ORDINALS:
            tags.append("list/step")
        if tok in CONTRAST:
            tags.append("contrast")
        if tok in WARN:
            tags.append("warning")
        if w["text"].endswith("?"):
            tags.append("question")
        if tags:
            cues.append(f"- #{w['i']} @{w['start']:.2f}s \"{w['text']}\" — {', '.join(tags)}")
    lines += ["", "## Graphic cues (candidates only — the beat sheet decides)", ""]
    lines += cues or ["- none"]

    # ---- stats
    long_pauses = []
    for i in range(1, len(words)):
        g = words[i]["start"] - words[i - 1]["end"]
        if g >= 0.7:
            long_pauses.append(g)
    wps = n_words / max(0.1, (words[-1]["end"] - words[0]["start"]))
    lines += ["", "## Pace", "",
              f"- speaking rate: {wps:.2f} words/s ({wps * 60:.0f} wpm); speech covers {speech / max(dur, 0.1):.0%} "
              f"of the clip",
              f"- fillers: {len(fillers)}; pauses ≥0.7 s: {len(long_pauses)} totalling {sum(long_pauses):.1f} s",
              f"- lead-in before first word: {words[0]['start']:.2f} s; tail after last word: "
              f"{max(0.0, dur - words[-1]['end']):.2f} s", ""]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines), encoding="utf-8")
    log(f"[pack] {len(ph)} phrases, {len(retakes)} retake candidates, {len(cues)} cues -> {a.out}")


if __name__ == "__main__":
    main()
