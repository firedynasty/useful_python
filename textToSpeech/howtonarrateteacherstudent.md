# How To: Narrator Teacher–Student Dialogue
*Print and keep for reference*

---

## Overview

Turn a markdown dialogue file into a multi-voice MP3 with a timestamp map,
then ask questions about any moment in the audio using Claude chat.

---

## Step 1 — Write or get a dialogue file

Save your content as a `.md` file (e.g. `speakthis.md`).

**Supported markdown format:**

```
# Section Heading          → narrator voice, spoken aloud
## Sub-heading             → narrator voice

**STUDENT:** Your question here.
**TEACHER:** The answer here.

> Scripture quote here     → scripture voice (reverent)
```

*Tip: Ask Claude chat — "give me a teacher-student dialogue on [topic]" and save the output as speakthis.md*

---

## Step 2 — Generate the audio

### Option A: ElevenLabs (higher quality, requires API key + credits)

```bash
export ELEVENLABS_API_KEY="your-key"
python narrator_teacher_student.py speakthis.md -o my_lesson.mp3
```

### Option B: Kokoro (free, offline, no API key)

```bash
python narrator_teacher_student_kokoro.py speakthis.md -o my_lesson.mp3
```

**Flags:**
- `-o my_lesson.mp3` — output filename (default: dialogue_output.mp3)
- `-c` — read from clipboard instead of a file
- `--dry-run` — preview parsed segments without generating audio
- `--speed 1.2` — faster playback (Kokoro only)

**Output:** Two files are created side by side:
- `my_lesson.mp3` — the audio
- `my_lesson.json` — timestamp map of every segment (needed for ask_at.py)

---

## Voice reference

| Role | ElevenLabs | Kokoro |
|------|-----------|--------|
| Narrator | Adam (warm male) | am_michael |
| Student | Bella (American female) | af_bella |
| Teacher | Arnold (British male) | bm_george |
| Scripture | Antoni (deep male) | bf_emma |

*To swap voices: edit the `VOICES` dict at the top of the script.*

---

## Step 3 — Ask a question at any timestamp

### From the terminal

Pause the audio, note the time, then run:

```bash
python ask_at.py 3:00 my_lesson.json -q "Why does Jesus stay silent?"
```

- Copies a context block + your question to clipboard
- Paste directly into Claude chat
- A macOS notification confirms it was copied

**Flags:**
- `3:00` — timestamp (M:SS format, or H:MM:SS, or raw seconds)
- `my_lesson.json` — the sidecar file (omit to auto-use most recent)
- `-q "question"` — your question (omit to leave a blank placeholder)
- `--context 5` — show 5 segments before/after instead of 3

### From Finder (Automator Quick Action)

Set up once, then right-click any `.json` transcript file:

**Setup:**
1. Open Automator → New Document → **Quick Action**
2. "Workflow receives current **files or folders**" in **Finder**
3. Add action: **Run AppleScript**
4. Paste contents of `automator_script_ask_at_timestamp.txt`
5. Save as **"Ask At Timestamp"**

**Usage:**
1. Right-click the `.json` file → Quick Actions → Ask At Timestamp
2. Enter timestamp when prompted (e.g. `3:00`)
3. Enter your question when prompted
4. Switch to Claude chat and paste

---

## Full example workflow

```bash
# 1. Generate audio + JSON from a dialogue file
python narrator_teacher_student_kokoro.py speakthis.md -o canannite_womans_faith.mp3

# 2. Listen to canannite_womans_faith.mp3 — pause at 3:00

# 3. Ask a question about that moment
python ask_at.py 3:00 canannite_womans_faith.json -q "What does Son of David mean?"

# 4. Paste clipboard into Claude chat
```

---

## File locations

| File | Path |
|------|------|
| ElevenLabs script | `narrator_teacher_student.py` |
| Kokoro script | `narrator_teacher_student_kokoro.py` |
| Timestamp lookup | `ask_at.py` |
| Automator script | `automator_script_ask_at_timestamp.txt` |
| Kokoro model | `kokoro-v1.0.onnx` |
| Kokoro voices | `voices-v1.0.bin` |

All scripts live in: `/Users/stanleytan/Documents/technical/python/textToSpeech/`

---

## Dependencies

```bash
pip install elevenlabs pydub kokoro-onnx numpy sounddevice
brew install ffmpeg
```
