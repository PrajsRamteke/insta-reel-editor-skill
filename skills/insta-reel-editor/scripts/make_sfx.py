#!/usr/bin/env python3
"""Synthesize a tiny, license-free SFX kit (no downloads): pop, tick, ding, whoosh, swoosh-up, thud.

Usage:
  python3 make_sfx.py --out assets/sfx          # writes <name>.wav (48 kHz stereo)

Why synthesize: stock SFX packs carry licenses and are easy to overuse. These are short, quiet
by design, and tie to visible events only (patterns/sound-design.md): pop = keyword/sticker,
tick = list item/checkbox, ding = stat lands / correct, whoosh = transition/b-roll in,
swoosh-up = hook title, thud = myth/negative.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import log, need, run

KIT = {
    "pop": ("aevalsrc=exprs='0.75*sin(2*PI*(520+2200*exp(-38*t))*t)*exp(-26*t)':s=48000:d=0.16", ""),
    "tick": ("aevalsrc=exprs='0.55*sin(2*PI*2300*t)*exp(-110*t)+0.25*sin(2*PI*4100*t)*exp(-160*t)':s=48000:d=0.06", ""),
    "ding": ("aevalsrc=exprs='0.42*sin(2*PI*1318.5*t)*exp(-5.5*t)+0.22*sin(2*PI*2637*t)*exp(-8*t)"
             "+0.12*sin(2*PI*3955*t)*exp(-11*t)':s=48000:d=1.1", ""),
    "whoosh": ("anoisesrc=color=pink:sample_rate=48000:amplitude=0.6:duration=0.5",
               ",highpass=f=350,lowpass=f=6000,afade=t=in:d=0.28:curve=exp,afade=t=out:st=0.28:d=0.22"),
    "swoosh-up": ("anoisesrc=color=white:sample_rate=48000:amplitude=0.35:duration=0.45",
                  ",highpass=f=900,lowpass=f=9000,afade=t=in:d=0.35:curve=qsin,afade=t=out:st=0.35:d=0.1"),
    "thud": ("aevalsrc=exprs='0.9*sin(2*PI*(55+90*exp(-25*t))*t)*exp(-14*t)':s=48000:d=0.35", ",lowpass=f=400"),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="assets/sfx")
    a = ap.parse_args()
    need("ffmpeg")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, (src, post) in KIT.items():
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", src,
             "-af", f"aformat=channel_layouts=stereo{post},alimiter=limit=0.89", "-ar", "48000",
             "-c:a", "pcm_s16le", str(out / f"{name}.wav")], quiet=True)
    log(f"[sfx] wrote {', '.join(KIT)} -> {out}")


if __name__ == "__main__":
    main()
