#!/usr/bin/env python3
"""Word-level, verbatim transcription -> normalized words.json (the reel's time spine).

Usage:
  python3 transcribe.py AUDIO_OR_VIDEO --out transcript/words.json [--engine auto] [--language en]
                        [--model NAME] [--keyterms terms.txt] [--no-verbatim-prompt]
  python3 transcribe.py --import FILE --format elevenlabs|openai|deepgram|whisperx|whisper|hyperframes|srt
                        --out transcript/words.json [--duration SECONDS]

Engines (pick with --engine; 'auto' tries them in this order and uses the first that works):
  elevenlabs      hosted, best at keeping fillers (ELEVENLABS_API_KEY).           scribe_v2
  deepgram        hosted, fast (DEEPGRAM_API_KEY), filler_words=true.           nova-3
  mlx             local on Apple Silicon (pip install mlx-whisper).              default mlx-community/whisper-large-v3-turbo
  faster-whisper  local, free (pip install faster-whisper). CPU/CUDA.            default model large-v3-turbo
  openai          hosted (OPENAI_API_KEY), verbose_json + word timestamps.      whisper-1
Output schema (reference/data-contracts.md):
  {"version":1,"engine","model","language","duration","words":[{"i","text","start","end","conf","type"}],"qc":{...}}
Why word-level verbatim: cuts, captions and motion-graphic timing all hang off word boundaries,
and fillers ("um") must be visible to be removable.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from _common import die, log, media_duration, save_json

VERBATIM_PROMPT = "Umm, let me think like, hmm... Okay, here's what I'm, like, thinking."


# ----------------------------------------------------------------- helpers
def to_wav16k(src: str) -> str:
    """Make a small 16 kHz mono wav (ASR engines want it; hosted APIs have size limits)."""
    if src.lower().endswith(".wav"):
        return src
    tmp = Path(tempfile.mkdtemp()) / "asr16k.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", str(tmp)], check=True)
    return str(tmp)


def to_m4a(src: str) -> str:
    tmp = Path(tempfile.mkdtemp()) / "asr.m4a"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                    "-c:a", "aac", "-b:a", "48k", str(tmp)], check=True)
    return str(tmp)


def multipart(fields: list[tuple[str, str]], files: list[tuple[str, str]]) -> tuple[bytes, str]:
    boundary = "----reel" + uuid.uuid4().hex
    out = bytearray()
    for k, v in fields:
        out += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files:
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{Path(path).name}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n").encode()
        out += Path(path).read_bytes() + b"\r\n"
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


def http(url: str, data: bytes, headers: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        die(f"{url} -> HTTP {e.code}: {e.read().decode(errors='replace')[:800]}")
    return {}


def read_terms(path: str | None) -> list[str]:
    if not path:
        return []
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]


# ----------------------------------------------------------------- engines
def eng_faster_whisper(audio: str, a) -> tuple[list[dict], str, str]:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        raise RuntimeError("faster-whisper not installed (pip install faster-whisper)")
    model_name = a.model or "large-v3-turbo"
    if model_name.endswith(".en") and a.language and a.language != "en":
        die(".en models translate other languages into English. Use a multilingual model for --language "
            f"{a.language}.")
    model = WhisperModel(model_name, device=a.device or "auto", compute_type=a.compute_type or "default")
    prompt = " ".join(filter(None, [None if a.no_verbatim_prompt else VERBATIM_PROMPT, ", ".join(a._terms)])) or None
    segs, info = model.transcribe(audio, language=a.language, word_timestamps=True, vad_filter=True, beam_size=5,
                                  initial_prompt=prompt, condition_on_previous_text=False)
    words = []
    for s in segs:
        for w in s.words or []:
            words.append({"text": w.word, "start": w.start, "end": w.end, "conf": round(float(w.probability), 3)})
    return words, f"faster-whisper:{model_name}", info.language


def eng_mlx(audio: str, a) -> tuple[list[dict], str, str]:
    try:
        import mlx_whisper  # type: ignore
    except ImportError:
        raise RuntimeError("mlx-whisper not installed (pip install mlx-whisper; Apple Silicon only)")
    repo = a.model or "mlx-community/whisper-large-v3-turbo"
    prompt = " ".join(filter(None, [None if a.no_verbatim_prompt else VERBATIM_PROMPT, ", ".join(a._terms)])) or None
    res = mlx_whisper.transcribe(audio, path_or_hf_repo=repo, word_timestamps=True, language=a.language,
                                 initial_prompt=prompt, condition_on_previous_text=False)
    return from_whisper_dict(res), f"mlx-whisper:{repo}", res.get("language") or (a.language or "")


def eng_elevenlabs(audio: str, a) -> tuple[list[dict], str, str]:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    model = a.model or "scribe_v2"
    fields = [("model_id", model), ("timestamps_granularity", "word"), ("tag_audio_events", "true"),
              ("no_verbatim", "false"), ("diarize", "true" if a.speakers and a.speakers > 1 else "false")]
    if a.language:
        fields.append(("language_code", a.language))
    if a.speakers:
        fields.append(("num_speakers", str(a.speakers)))
    for t in a._terms[:1000]:
        fields.append(("keyterms", t[:49]))
    body, ctype = multipart(fields, [("file", to_m4a(audio))])
    res = http("https://api.elevenlabs.io/v1/speech-to-text", body, {"xi-api-key": key, "Content-Type": ctype})
    return from_elevenlabs(res), f"elevenlabs:{model}", res.get("language_code") or (a.language or "")


def eng_deepgram(audio: str, a) -> tuple[list[dict], str, str]:
    key = os.environ.get("DEEPGRAM_API_KEY")
    if not key:
        raise RuntimeError("DEEPGRAM_API_KEY not set")
    model = a.model or "nova-3"
    q = [("model", model), ("smart_format", "true"), ("punctuate", "true"), ("filler_words", "true")]
    if a.language:
        q.append(("language", a.language))
    if a.speakers and a.speakers > 1:
        q.append(("diarize", "true"))
    for t in a._terms[:100]:
        q.append(("keyterm", t))
    url = "https://api.deepgram.com/v1/listen?" + urllib.parse.urlencode(q)
    res = http(url, Path(to_m4a(audio)).read_bytes(),
               {"Authorization": f"Token {key}", "Content-Type": "application/octet-stream"})
    return from_deepgram(res), f"deepgram:{model}", a.language or "en"


def eng_openai(audio: str, a) -> tuple[list[dict], str, str]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    model = a.model or "whisper-1"
    path = to_m4a(audio)
    if Path(path).stat().st_size > 25 * 1024 * 1024:
        die("Audio exceeds OpenAI's 25 MB limit even as 48 kbps AAC; split the source or use another engine.")
    fields = [("model", model), ("response_format", "verbose_json"), ("timestamp_granularities[]", "word"),
              ("timestamp_granularities[]", "segment")]
    if a.language:
        fields.append(("language", a.language))
    prompt = " ".join(filter(None, [None if a.no_verbatim_prompt else VERBATIM_PROMPT, ", ".join(a._terms)]))
    if prompt:
        fields.append(("prompt", prompt))
    body, ctype = multipart(fields, [("file", path)])
    res = http("https://api.openai.com/v1/audio/transcriptions", body,
               {"Authorization": f"Bearer {key}", "Content-Type": ctype})
    words = [{"text": w["word"], "start": w["start"], "end": w["end"]} for w in res.get("words", [])]
    return words, f"openai:{model}", res.get("language") or (a.language or "")


ENGINES = {"faster-whisper": eng_faster_whisper, "mlx": eng_mlx, "elevenlabs": eng_elevenlabs,
           "deepgram": eng_deepgram, "openai": eng_openai}
AUTO_ORDER = ["elevenlabs", "deepgram", "mlx", "faster-whisper", "openai"]


# ----------------------------------------------------------------- importers
def from_elevenlabs(res: dict) -> list[dict]:
    out = []
    for w in res.get("words", []):
        t = w.get("type", "word")
        if t == "spacing":
            continue
        item = {"text": w.get("text", ""), "start": w.get("start"), "end": w.get("end"),
                "type": "event" if t == "audio_event" else "word"}
        if w.get("speaker_id") is not None:
            item["speaker"] = w["speaker_id"]
        if w.get("logprob") is not None:
            import math
            item["conf"] = round(math.exp(float(w["logprob"])), 3)
        out.append(item)
    return out


def from_deepgram(res: dict) -> list[dict]:
    alt = res.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0]
    out = []
    for w in alt.get("words", []):
        item = {"text": w.get("punctuated_word") or w.get("word", ""), "start": w["start"], "end": w["end"],
                "conf": round(float(w.get("confidence", 0)), 3)}
        if "speaker" in w:
            item["speaker"] = f"S{w['speaker']}"
        out.append(item)
    return out


def from_whisper_dict(res: dict) -> list[dict]:
    out = []
    for s in res.get("segments", []):
        for w in s.get("words", []) or []:
            if w.get("start") is None:
                continue
            item = {"text": w.get("word", w.get("text", "")), "start": w["start"], "end": w["end"]}
            p = w.get("probability", w.get("score"))
            if p is not None:
                item["conf"] = round(float(p), 3)
            if w.get("speaker"):
                item["speaker"] = w["speaker"]
            out.append(item)
    return out


def from_whisperx(res: dict) -> list[dict]:
    """WhisperX leaves words containing digits without timings: interpolate them."""
    raw = []
    for s in res.get("segments", []):
        for w in s.get("words", []) or []:
            raw.append({"text": w.get("word", ""), "start": w.get("start"), "end": w.get("end"),
                        "conf": w.get("score"), "speaker": w.get("speaker")})
    for i, w in enumerate(raw):
        if w["start"] is None:
            prev_end = next((raw[j]["end"] for j in range(i - 1, -1, -1) if raw[j]["end"] is not None), 0.0)
            nxt = next((raw[j]["start"] for j in range(i + 1, len(raw)) if raw[j]["start"] is not None), prev_end + 0.4)
            w["start"], w["end"], w["interpolated"] = prev_end, max(prev_end + 0.05, nxt), True
    return [{k: v for k, v in w.items() if v is not None} for w in raw]


def from_hyperframes(res: dict) -> list[dict]:
    return [{"text": w["text"], "start": w["start"], "end": w["end"]} for w in res.get("words", [])
            if w.get("type", "word") == "word"]


def from_srt(text: str) -> list[dict]:
    """Phrase-level fallback: spread each cue's duration across its words by length (low precision)."""
    out = []
    blocks = re.split(r"\n\s*\n", text.strip())
    tre = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")

    def sec(h, m, s, ms):
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    for b in blocks:
        lines = b.splitlines()
        m = next((tre.search(ln) for ln in lines if tre.search(ln)), None)
        if not m:
            continue
        st, en = sec(*m.groups()[:4]), sec(*m.groups()[4:])
        txt = " ".join(ln for ln in lines if not tre.search(ln) and not ln.strip().isdigit())
        toks = re.sub(r"<[^>]+>", "", txt).split()
        if not toks:
            continue
        weights = [max(2, len(t)) for t in toks]
        tot, cur = sum(weights), st
        for t, wgt in zip(toks, weights):
            d = (en - st) * wgt / tot
            out.append({"text": t, "start": cur, "end": cur + d * 0.9, "approx": True})
            cur += d
    return out


IMPORTERS = {"elevenlabs": from_elevenlabs, "deepgram": from_deepgram, "openai": None, "whisper": from_whisper_dict,
             "mlx": from_whisper_dict, "whisperx": from_whisperx, "hyperframes": from_hyperframes, "srt": None}


# ----------------------------------------------------------------- normalize + QC
def normalize(words: list[dict], duration: float | None) -> tuple[list[dict], dict]:
    clean = []
    for w in words:
        txt = (w.get("text") or "").strip()
        if not txt or w.get("start") is None or w.get("end") is None:
            continue
        w = dict(w)
        w["text"] = txt
        w["start"], w["end"] = round(float(w["start"]), 3), round(float(w["end"]), 3)
        w.setdefault("type", "event" if re.fullmatch(r"[\(\[].*[\)\]]", txt) else "word")
        clean.append(w)
    clean.sort(key=lambda x: x["start"])
    qc = {"zero_duration_fixed": 0, "inflated_fixed": [], "overlaps_fixed": 0, "garbage_tokens": 0,
          "approx_timing": any(w.get("approx") for w in clean)}
    for i, w in enumerate(clean):
        nxt = clean[i + 1]["start"] if i + 1 < len(clean) else (duration or w["end"] + 1)
        if w["end"] <= w["start"]:
            w["end"] = round(min(w["start"] + 0.08, max(nxt, w["start"] + 0.02)), 3)
            qc["zero_duration_fixed"] += 1
        # one word "spanning" a long silence is an ASR artifact; shrink it to a plausible length
        plaus = 0.15 + 0.075 * len(w["text"])
        if w["type"] == "word" and (w["end"] - w["start"]) > max(1.2, plaus * 2.5):
            qc["inflated_fixed"].append({"text": w["text"], "start": w["start"], "was_end": w["end"]})
            w["end"] = round(w["start"] + plaus, 3)
            w["inflated"] = True
        if i + 1 < len(clean) and w["end"] > clean[i + 1]["start"]:
            w["end"] = clean[i + 1]["start"]
            qc["overlaps_fixed"] += 1
        if w["type"] == "word" and not re.search(r"\w", w["text"], flags=re.UNICODE):
            qc["garbage_tokens"] += 1
    for i, w in enumerate(clean):
        w["i"] = i
    n = sum(1 for w in clean if w["type"] == "word")
    qc["words"] = n
    qc["garbage_ratio"] = round(qc["garbage_tokens"] / n, 3) if n else 0
    if clean:
        span = clean[-1]["end"] - clean[0]["start"]
        qc["words_per_sec"] = round(n / span, 2) if span > 0 else 0
    confs = [w["conf"] for w in clean if "conf" in w]
    qc["mean_conf"] = round(sum(confs) / len(confs), 3) if confs else None
    qc["low_conf_words"] = [{"i": w["i"], "text": w["text"], "conf": w["conf"]} for w in clean
                            if w.get("conf") is not None and w["conf"] < 0.4][:40]
    # repetition loop (a classic Whisper hallucination over music/silence)
    toks = [w["text"].lower() for w in clean if w["type"] == "word"]
    loops = 0
    for k in range(len(toks) - 8):
        if toks[k:k + 3] == toks[k + 3:k + 6] == toks[k + 6:k + 9]:
            loops += 1
    qc["repetition_loops"] = loops
    warn = []
    if n == 0:
        warn.append("No speech recognized. Music-only or silent clip? Captions are impossible; plan text-led graphics.")
    if qc["garbage_ratio"] > 0.2:
        warn.append("More than 20% garbage tokens: retry with a larger model or a hosted engine.")
    if loops:
        warn.append("Repeated 3-word loops found: likely hallucination over music/silence. Check those spans.")
    if qc["inflated_fixed"]:
        warn.append(f"{len(qc['inflated_fixed'])} words had implausible durations (ASR timing drift); shrunk.")
    if qc["approx_timing"]:
        warn.append("Timing is approximate (phrase-level import). Word-synced captions will be loose.")
    if qc.get("mean_conf") is not None and qc["mean_conf"] < 0.6:
        warn.append(f"Low mean confidence {qc['mean_conf']}: noisy audio or wrong --language.")
    qc["warnings"] = warn
    return clean, qc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?")
    ap.add_argument("--out", required=True)
    ap.add_argument("--engine", default="auto", choices=["auto", *ENGINES.keys()])
    ap.add_argument("--model")
    ap.add_argument("--language", help="ISO code, e.g. en, hi. Omit to auto-detect (local engines).")
    ap.add_argument("--keyterms", help="text file, one brand/term per line (improves spelling of names)")
    ap.add_argument("--speakers", type=int, help="expected number of speakers (enables diarization if >1)")
    ap.add_argument("--no-verbatim-prompt", action="store_true", help="don't nudge Whisper to keep fillers")
    ap.add_argument("--device")
    ap.add_argument("--compute-type")
    ap.add_argument("--import", dest="import_file")
    ap.add_argument("--format", choices=list(IMPORTERS.keys()))
    ap.add_argument("--duration", type=float, help="media duration (for imports)")
    ap.add_argument("--force", action="store_true", help="re-transcribe even if --out exists")
    a = ap.parse_args()
    a._terms = read_terms(a.keyterms)

    if Path(a.out).exists() and not a.force and not a.import_file:
        log(f"[transcribe] {a.out} exists (cached). Use --force to redo.")
        return

    duration = a.duration
    if a.import_file:
        if not a.format:
            die("--import needs --format")
        raw_text = Path(a.import_file).read_text(encoding="utf-8")
        if a.format == "srt":
            words = from_srt(raw_text)
        elif a.format == "openai":
            res = json.loads(raw_text)
            words = [{"text": w["word"], "start": w["start"], "end": w["end"]} for w in res.get("words", [])]
        else:
            words = IMPORTERS[a.format](json.loads(raw_text))
        engine, lang = f"import:{a.format}", a.language or ""
    else:
        if not a.audio:
            die("give an audio/video path or --import")
        duration = duration or media_duration(a.audio)
        audio = to_wav16k(a.audio)
        order = AUTO_ORDER if a.engine == "auto" else [a.engine]
        words, engine, lang, errors = None, "", "", []
        for name in order:
            try:
                log(f"[transcribe] trying {name} ...")
                words, engine, lang = ENGINES[name](audio, a)
                break
            except SystemExit:
                raise
            except Exception as e:  # missing package, no key, model download blocked, API error...
                errors.append(f"{name}: {type(e).__name__}: {e}")
        if words is None:
            die("no transcription engine available:\n  " + "\n  ".join(errors) +
                "\nInstall one (pip install faster-whisper) or set an API key. See workflow/02-transcribe.md.")

    words, qc = normalize(words, duration)
    doc = {"version": 1, "engine": engine, "language": lang, "duration": duration, "source": a.audio or a.import_file,
           "words": words, "qc": qc}
    save_json(doc, a.out)
    log(f"[transcribe] {engine}: {qc['words']} words, {qc.get('words_per_sec')} w/s, mean conf {qc.get('mean_conf')}"
        f" -> {a.out}")
    for wmsg in qc["warnings"]:
        log(f"  ! {wmsg}")


if __name__ == "__main__":
    main()
