# Text-to-Speech Tools

Collection of TTS scripts using ElevenLabs and local models (Kokoro) for various use cases.

## Key Scripts

### vocab_teacher.py — Vocabulary Recitation Audio
Generates teacher-style audio from vocabulary lists. The workflow is:
1. Ask Claude (chat) for vocab words in markdown format, e.g. "what are some vocab words I should know based on this so I can form a mental model to be able to explain to someone else what [topic] is"
2. Claude outputs grouped vocab in markdown: `- **Term** — definition` with `**bold headers**` for sections
3. Either copy from Claude chat and run with `-c`, or save as `.md` file

**Supported input formats (auto-detected):**
- **Markdown** — `- **Term** — definition` with bold/heading section breaks (from Claude chat)
- **CSV** — `term,"definition with commas"` (e.g. Google IT cert vocab exports)
- **Dash-delimited** — `Term -- definition`

**Usage:**
```bash
export ELEVENLABS_API_KEY="your-key"

# Clipboard (copy vocab from Claude chat, then run)
python vocab_teacher.py -c
python vocab_teacher.py -c -o engineering_vocab.mp3

# File inputs
python vocab_teacher.py vocab_notes.md
python vocab_teacher.py /Users/stanleytan/Downloads/vocab_google_it_course_1_module_2.csv

# Adjust pacing
python vocab_teacher.py -c --pause 2000 --section-pause 3000
```

**How it sounds:** Section headers are announced as spoken breaks ("The big picture words..."), then each term follows with a natural teacher cadence: "Engineering... solving real problems by designing and building things on purpose." with configurable silence gaps between entries.

**Voice/cadence settings** (in script): stability=0.4 (expressive), style=0.5 (teacher feel), default pause=1200ms between terms, 2000ms after section headers.

### Other Scripts
- `multi_speaker.py` — Multi-speaker dialogue TTS using ElevenLabs
- `narrator.py` — Narration TTS
- `speak_clipboard.py` / `speak_clipboard_es.py` / `speak_clipboard_zh.py` — Read clipboard aloud (English/Spanish/Chinese)
- `transcribe_groq.py` — Audio transcription via Groq

## Dependencies
```bash
pip install elevenlabs pydub
brew install ffmpeg
```

## Common CSV Source
Google IT Support cert vocab exports live in `~/Downloads/` as `vocab_google_it_course_*.csv`
