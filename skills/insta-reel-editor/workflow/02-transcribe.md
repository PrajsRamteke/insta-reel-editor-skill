# 02 · Transcribe (word-level, verbatim)

Everything downstream hangs off word timestamps. A transcript that drops "um" hides cut points. One
that inflates a word across a pause makes captions linger. One with misspelled names puts typos on
screen.

## Run

```bash
python3 $S/transcribe.py $R/media/voice16k.wav --out $R/transcript/words.json \
        --language en --keyterms $R/keyterms.txt          # --engine auto|faster-whisper|mlx|elevenlabs|deepgram|openai
python3 $S/pack_transcript.py $R/transcript/words.json --out $R/transcript/phrases.md
```

Results are cached. It won't re-transcribe unless you pass `--force` (the source never changes).

## Engine ladder

| Engine | Cost | Fillers kept? | Notes |
|--------|------|---------------|-------|
| `elevenlabs` (scribe_v2) | paid API (`ELEVENLABS_API_KEY`) | yes, best (`no_verbatim=false`) | `keyterms`, audio events like "(laughs)", diarization |
| `deepgram` (nova-3) | paid API (`DEEPGRAM_API_KEY`) | yes with `filler_words=true` (set) | fast; `keyterm` prompting |
| `mlx` (whisper-large-v3-turbo) | free, Apple Silicon | partly (verbatim prompt) | `pip install mlx-whisper`; fastest local option on a Mac |
| `faster-whisper` (large-v3-turbo) | free, CPU/CUDA | partly (verbatim prompt) | `pip install faster-whisper`; `--model small` for speed |
| `openai` (whisper-1) | paid API (`OPENAI_API_KEY`) | partly | 25 MB limit (audio is sent as 48 kbps AAC); `verbose_json` + word timestamps |

`auto` tries them in that order and uses the first that works. Set your default in
`preferences/user-preferences.md`.

**Language rules:** pass `--language` when you know it. Never use an English-only `.en` model on
non-English audio: it *translates* into English. For Hinglish (Hindi in Latin script), use
`--language hi` with a multilingual model, then review spelling. For Devanagari captions, keep the
ASR output; the compiler adds Noto Sans Devanagari automatically.

**Keyterms:** one term per line (brand names, product names, Sanskrit pose names, jargon). They go to
ElevenLabs `keyterms`, Deepgram `keyterm`, or the Whisper prompt.

## Quality control (printed and stored in `words.json → qc`)

| Signal | Meaning | Action |
|--------|---------|--------|
| `words == 0` | no speech found | music-only or silent clip; see the intake gate |
| `garbage_ratio > 0.2` | ♪ / symbols | bigger model or hosted engine |
| `repetition_loops > 0` | Whisper hallucination over silence or music | inspect those spans and delete the phantom words |
| `inflated_fixed` | a word spanning a long pause, auto-shrunk | fine; check captions there |
| `mean_conf < 0.6` / `low_conf_words` | noisy audio or wrong language | fix the words by hand or switch engine |
| `approx_timing` | imported SRT (phrase level) | loose caption sync; prefer real word timestamps |

## Fix the transcript before captioning

Edit `transcript/words.json` directly for misspellings (keep `start`/`end`). Captions are made from
the cut-timeline copy (`words.cut.json`), so fix the source **before** `render_cut.py`, or fix both.

## Importing existing transcripts

```bash
python3 $S/transcribe.py --import scribe.json --format elevenlabs --out $R/transcript/words.json
#   formats: elevenlabs | deepgram | openai | whisper (openai-whisper/mlx JSON) | whisperx | hyperframes | srt
```

WhisperX leaves digit words like "2014" without timings. The importer interpolates them.

## Reading `phrases.md`

```
[009.78-012.46] #20-#28    First, you breathe through your nose, not your mouth.  ⟨1.0s⟩
[017.01-019.95] #38-#47    {uh} Third, you hold your breath when you are stressed.
```

`#20-#28` are word indices for EDL `--drop` and beat sheets. `{uh}` is a filler. `⟨1.0s⟩` is the
pause after the phrase. The appended sections list **retake candidates** (same opening words
repeated: cut the earlier one), **graphic cues** and **pace** (wpm, fillers, total pause time).
