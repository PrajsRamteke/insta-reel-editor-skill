#!/usr/bin/env python3
"""Mix the reel's audio: cleaned voice + ducked music bed + SFX hits -> one PCM wav (pre-loudness).

Usage:
  python3 mix_audio.py reel-plan.json [--out media/mix.wav]
  python3 mix_audio.py --voice media/cut.mov --music assets/bed.mp3 --out media/mix.wav [--sfx sfx.json]

Reads plan["audio"] (all optional; see workflow/07-audio.md):
  {"voice": "media/cut.mov", "voice_chain": "clean"|"none"|"<raw ffmpeg -af>", "denoise": false,
   "music": {"src": "assets/bed.mp3", "gain_db": -20, "duck": true, "duck_ratio": 8,
             "fade_in": 0.6, "fade_out": 1.5, "offset": 0},
   "sfx": [{"src": "assets/sfx/pop.wav", "at": 3.2, "gain_db": -6}, ...]}
SFX "at" may also be a word: {"preset": "pop", "on_word": 23} (cut index) or "on_word_src" (source index).
No voice (music-only / faceless reel): length comes from plan["duration"] and a silent bed is used.
Voice "clean" chain = high-pass 80 Hz + gentle presence (+2 dB @ 3 kHz) + de-ess + 3:1 compressor.
Music is looped to length, sits gain_db under 0 dBFS-ish, and ducks under speech via sidechain.
Loudness normalization happens later in finalize.py (two-pass loudnorm on the full mix).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from _common import SKILL_DIR, die, load_json, load_words, log, media_duration, need, run

VOICE_CHAINS = {
    "clean": "highpass=f=80,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3200:t=q:w=1.0:g=2,"
             "deesser=i=0.35,acompressor=threshold=-21dB:ratio=3:attack=8:release=160:makeup=2",
    "none": "anull",
}


def measure_i(path: str) -> float | None:
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", res.stderr)
    return float(m[-1]) if m else None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan", nargs="?")
    ap.add_argument("--voice")
    ap.add_argument("--music")
    ap.add_argument("--music-gain-db", type=float, default=-20.0)
    ap.add_argument("--no-duck", action="store_true")
    ap.add_argument("--sfx", help="JSON list of {src|preset, at|on_word, gain_db}")
    ap.add_argument("--voice-chain", default=None)
    ap.add_argument("--denoise", action="store_true", help="add afftdn (only for audible hiss/hum)")
    ap.add_argument("--out")
    a = ap.parse_args()
    need("ffmpeg")

    wd = Path(a.plan).resolve().parent if a.plan else Path.cwd()
    plan = load_json(a.plan) if a.plan else {}
    cfg = dict(plan.get("audio", {}))

    def rel(p):
        p = Path(p)
        return p if p.is_absolute() else wd / p

    # voice: explicit > lossless cut (PCM) > the plan's video > none (music-only reel)
    if a.voice or cfg.get("voice"):
        voice = rel(a.voice or cfg.get("voice"))
        if not voice.exists():
            die(f"voice source not found: {voice}")
    elif (wd / "media" / "cut.mov").exists():
        voice = wd / "media" / "cut.mov"
    elif plan.get("video") and rel(plan["video"]).exists():
        voice = rel(plan["video"])
    else:
        voice = None
    if voice is None and not plan.get("duration"):
        die("no voice source and no plan 'duration': nothing defines the reel length")
    music_cfg = cfg.get("music") or ({"src": a.music} if a.music else None)
    if a.music and music_cfg:
        music_cfg["src"] = a.music
    sfx = cfg.get("sfx", [])
    if a.sfx:
        sfx = load_json(a.sfx)
    words = []
    if any("on_word" in s or "on_word_src" in s for s in sfx):
        if not plan.get("words"):
            die("sfx uses on_word but the plan has no 'words' file")
        words = load_words(rel(plan["words"]))["words"]
    chain = a.voice_chain or cfg.get("voice_chain", "clean")
    chain = VOICE_CHAINS.get(chain, chain)
    if a.denoise or cfg.get("denoise"):
        chain = "afftdn=nf=-25," + chain
    dur = float(plan.get("duration") or 0) or media_duration(voice)
    out = Path(a.out) if a.out else wd / "media" / "mix.wav"
    out.parent.mkdir(parents=True, exist_ok=True)

    if voice is not None:
        inputs = ["-i", str(voice)]
        fc = [f"[0:a]aresample=48000,aformat=channel_layouts=stereo,{chain},apad,atrim=0:{dur:.3f},asplit=2[vmix][vsc]"]
    else:  # music-only reel: a silent "voice" keeps the graph (and the sidechain) identical
        inputs = ["-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        fc = ["[0:a]asplit=2[vmix][vsc]"]
    mix_labels = ["[vmix]"]
    n = 1
    if music_cfg and music_cfg.get("src"):
        msrc = rel(music_cfg["src"])
        if voice is None:
            music_cfg = {**music_cfg, "duck": False}
        if not msrc.exists():
            die(f"music not found: {msrc}")
        mi = measure_i(str(msrc)) or -16.0
        vi = (measure_i(str(voice)) if voice is not None else None) or -14.0
        # place the bed gain_db below the voice's loudness (default 20 dB under -> clearly a bed)
        gain = (vi + float(music_cfg.get("gain_db", a.music_gain_db))) - mi
        if voice is None:  # music IS the soundtrack: bring it near the final target; finalize does the rest
            gain = -16.0 - mi
        fi, fo = float(music_cfg.get("fade_in", 0.6)), float(music_cfg.get("fade_out", 1.5))
        off = float(music_cfg.get("offset", 0))
        inputs += ["-stream_loop", "-1", "-ss", f"{off}", "-i", str(msrc)]
        m = (f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
             f"volume={gain:.2f}dB,afade=t=in:d={fi},afade=t=out:st={max(0.0, dur - fo):.3f}:d={fo}")
        if music_cfg.get("duck", True) and not a.no_duck:
            ratio = float(music_cfg.get("duck_ratio", 8))
            fc.append(m + "[mus]")
            fc.append(f"[mus][vsc]sidechaincompress=threshold=0.02:ratio={ratio}:attack=25:release=420:makeup=1[mduck]")
            mix_labels.append("[mduck]")
        else:
            fc.append(m + "[mduck]")
            fc.append("[vsc]anullsink")
            mix_labels.append("[mduck]")
        log(f"[mix] music {msrc.name}: {mi:.1f} LUFS -> gain {gain:+.1f} dB (voice {vi:.1f} LUFS, bed "
            f"{music_cfg.get('gain_db', a.music_gain_db)} dB under){' + ducking' if music_cfg.get('duck', True) and not a.no_duck else ''}")
        n += 1
    else:
        fc.append("[vsc]anullsink")
    for s in sfx:
        src = s.get("src") or (SKILL_DIR / "assets" / "sfx" / f"{s.get('preset')}.wav")
        src = rel(src) if not Path(str(src)).is_absolute() else Path(src)
        if not src.exists():
            alt = wd / "assets" / "sfx" / f"{s.get('preset')}.wav"
            if s.get("preset") and not alt.exists():  # synthesize the kit on first use
                run([sys.executable, str(Path(__file__).with_name("make_sfx.py")), "--out", str(wd / "assets" / "sfx")])
            if s.get("preset") and alt.exists():
                src = alt
            else:
                die(f"sfx not found: {src} (presets: pop, tick, ding, whoosh, swoosh-up, thud)")
        if "at" in s:
            at = float(s["at"])
        else:
            if "on_word_src" in s:
                hit = [w for w in words if w.get("src_i") == int(s["on_word_src"])]
                if not hit:
                    die(f"sfx on_word_src {s['on_word_src']} was cut out")
                wobj = hit[0]
            else:
                wobj = words[int(s["on_word"])]
            at = float(wobj["start"]) - float(s.get("lead", 0.03))
        at = max(0.0, at)
        ms = int(round(at * 1000))
        inputs += ["-i", str(src)]
        fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,volume={float(s.get('gain_db', -8))}dB,"
                  f"adelay={ms}|{ms}[s{n}]")
        mix_labels.append(f"[s{n}]")
        n += 1
    if len(mix_labels) == 1:
        fc.append(f"{mix_labels[0]}anull[out]")
    else:
        fc.append(f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:normalize=0:dropout_transition=0,"
                  "alimiter=limit=0.95:level=disabled[out]")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[out]", "-t", f"{dur:.3f}", "-c:a", "pcm_s16le", "-ar", "48000", str(out)])
    log(f"[mix] {len(sfx)} sfx, music={'yes' if music_cfg and music_cfg.get('src') else 'no'} -> {out} "
        f"({dur:.2f}s, {measure_i(str(out))} LUFS before normalization)")


if __name__ == "__main__":
    main()
