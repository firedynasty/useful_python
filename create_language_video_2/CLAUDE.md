# CLAUDE.md

## Project Overview

Language learning video generator. Takes a dialogue transcript, generates TTS audio, burns subtitles onto a black-background video, and produces a word-by-word gloss CSV. Currently configured for Mandarin Chinese but supports Filipino and Cantonese via `language.py`.

## Pipeline

1. **Write dialogue** in `dialogue.txt` using the format from `prompt.txt` (use an LLM to generate)
2. **`python step1_tts.py`** — Reads `dialogue.txt`, generates per-line TTS audio via OpenAI, stitches into `output/dialogue.mp3`, and creates SRT subtitle files (`mandarin.srt`, `pinyin.srt`, `english.srt`)
3. **`bash step2_video.sh`** — Burns subtitles onto black background video using ffmpeg. Produces two videos:
   - `output/lesson.mp4` — full version (Chinese top, pinyin middle, English bottom)
   - `output/lesson_test.mp4` — Chinese-only subtitles (for reading practice)
4. **`python step3_gloss.py`** — Sends each dialogue line to OpenAI for word-by-word breakdown, outputs `output/gloss_output.csv`

## Dialogue Format (A/P/B triplets)

```
[Scene 1]
A: 姐姐，今天有什么菜？
P: Jiějie, jīntiān yǒu shénme cài?
B: Ate, what are the dishes today?
```

- `A:` = target language (Chinese characters)
- `P:` = pinyin with tone marks (optional — omitted for non-Chinese languages)
- `B:` = English translation
- Grouped by `[Scene N]` headers
- The parser is backwards-compatible: A/B pairs without P: lines still work

## Language Configuration

`language.py` controls the active language. Uncomment one block:
- **Mandarin** (active) — uses `zh` for Whisper, gloss includes pinyin column
- **Filipino** — uses `tl`, no pinyin line needed
- **Cantonese** — uses `zh`, gloss includes Jyutping column

Key exports: `LANGUAGE_NAME`, `LANGUAGE_CODE`, `TTS_VOICE`, `GLOSS_PROMPT`, `GLOSS_COLUMNS`, `TARGET_FIELD`

## Other Tools

- **`transcribe_mp3.py`** — Standalone Whisper transcription tool. Auto-chunks files over 24MB. Outputs SRT + plain text.

## Requirements

- `OPENAI_API_KEY` environment variable
- Python packages: `openai`, `pydub`
- System: `ffmpeg`, `ffprobe`

## Common Commands

```bash
# Full pipeline
python step1_tts.py --input dialogue.txt --output_dir output/
bash step2_video.sh output/
python step3_gloss.py --input dialogue.txt --output output/gloss_output.csv

# Transcribe existing audio
python transcribe_mp3.py -i audio.mp3 --language zh
```
