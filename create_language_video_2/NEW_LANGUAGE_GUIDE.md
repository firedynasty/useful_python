# How to Add a New Language

Step-by-step guide to create a lesson video pipeline for any language.
Uses the `frenchVocab/` folder as the template.

## Prerequisites

- `OPENAI_API_KEY` set in your environment
- Python 3 with `openai` and `pydub` packages
- `ffmpeg` installed

## Steps

### 1. Copy the template

```bash
cp -r frenchVocab/ spanishVocab/    # or koreanVocab/, etc.
cd spanishVocab/
```

### 2. Download the frequency list

Frequency lists come from [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords) (OpenSubtitles data, 50k most common words).

```bash
# Pattern: https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/<CODE>/<CODE>_50k.txt
curl -sL "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/es/es_50k.txt" -o es_50k.txt
```

**Available language codes (60+ languages):**

| Code | Language | Code | Language | Code | Language |
|------|----------|------|----------|------|----------|
| ar | Arabic | fr | French | pl | Polish |
| bg | Bulgarian | de | German | pt | Portuguese |
| ca | Catalan | el | Greek | pt_br | Brazilian Portuguese |
| zh_cn | Chinese (Simplified) | he | Hebrew | ro | Romanian |
| zh_tw | Chinese (Traditional) | hi | Hindi | ru | Russian |
| hr | Croatian | hu | Hungarian | sr | Serbian |
| cs | Czech | id | Indonesian | sk | Slovak |
| da | Danish | it | Italian | sl | Slovenian |
| nl | Dutch | ja | Japanese | es | Spanish |
| en | English | ko | Korean | sv | Swedish |
| et | Estonian | lt | Lithuanian | th | Thai |
| fi | Finnish | ms | Malay | tl | Tagalog |
| fa | Persian | no | Norwegian | tr | Turkish |
| bn | Bengali | ta | Tamil | uk | Ukrainian |
| vi | Vietnamese | ur | Urdu | ml | Malayalam |

Full list: https://github.com/hermitdave/FrequencyWords/tree/master/content/2018

### 3. Update `generate_vocab.py`

Change the `--freq_file` default and the filter regex if needed:

```python
parser.add_argument("--freq_file", default="es_50k.txt", ...)  # was fr_50k.txt
```

For languages with different junk patterns, update `SKIP_RE`:
- **CJK languages (Chinese, Japanese, Korean):** single-character filter may be too aggressive — CJK single characters are real words. Change to only skip digits/punctuation.
- **Languages with apostrophes (French, Italian):** keep the contraction filter.
- **Most other languages:** the default filter works fine.

You can also adjust `LEVEL_SIZES` if you want more/fewer words per tier.

### 4. Update `language.py`

This is the main config file. Change all fields:

```python
# ── Spanish example ──────────────────────────────────────────────
LANGUAGE_NAME = "Spanish"
LANGUAGE_CODE = "es"            # for Whisper transcription
TTS_VOICE = "alloy"             # OpenAI TTS voice
GLOSS_PROMPT = (
    "You are a Spanish linguistics assistant that creates word-by-word glosses for language learners.\n\n"
    "For each line you receive, break down EVERY word. Return a JSON array of objects:\n"
    '[  {"spanish": "Yo", "english": "I (subject pronoun, 1st person singular)"},\n'
    '  {"spanish": "quiero", "english": "want (present tense of querer)"},\n  ...\n]\n\n'
    "Rules:\n"
    "- Include grammar notes in parentheses for conjugation, gender, number, tense, and mood\n"
    "- Note verb tense/mood (e.g. pretérito, subjuntivo, condicional)\n"
    "- Note gender and number for nouns and adjectives (e.g. f., m., pl.)\n"
    "- Keep words in the same order as the line\n"
    "- For idiomatic expressions, keep them together and explain the meaning\n"
    "- Return ONLY the JSON array, no markdown, no explanation"
)
GLOSS_COLUMNS = ["Spanish", "English meaning"]
TARGET_FIELD = "spanish"
```

```python
# ── Korean example ───────────────────────────────────────────────
LANGUAGE_NAME = "Korean"
LANGUAGE_CODE = "ko"
TTS_VOICE = "alloy"
GLOSS_PROMPT = (
    "You are a Korean linguistics assistant that creates word-by-word glosses for language learners.\n\n"
    "For each line you receive, break down EVERY word/particle. Return a JSON array of objects:\n"
    '[  {"korean": "저", "romanization": "jeo", "english": "I (humble/formal)"},\n'
    '  {"korean": "는", "romanization": "neun", "english": "topic marker particle"},\n  ...\n]\n\n'
    "Rules:\n"
    "- Include romanization for every entry\n"
    "- Note grammar particles and their function (은/는 topic, 이/가 subject, 을/를 object, etc.)\n"
    "- Note verb conjugation level (formal, polite, casual) and tense\n"
    "- Note honorific forms where relevant\n"
    "- Keep words in the same order as the line\n"
    "- Return ONLY the JSON array, no markdown, no explanation"
)
GLOSS_COLUMNS = ["Korean", "Romanization", "English meaning"]
TARGET_FIELD = "korean"
```

### 5. Update `generate_dialogue.py`

Change the dialogue format in the prompt. For most languages it's A:/B: pairs (target/English). For languages with romanization (Korean, Japanese, Arabic), add P: lines:

**Without romanization (Spanish, German, Italian, etc.):**
```
A: Hola, ¿cómo estás?
B: Hello, how are you?
```
No changes needed — the French template already uses A:/B: pairs.

**With romanization (Korean, Japanese, Arabic, etc.):**
```
A: 안녕하세요, 어떻게 지내세요?
P: Annyeonghaseyo, eotteoke jinaeseyo?
B: Hello, how are you?
```
Update the prompt example format and add P: parsing back into `step1_tts.py` (copy from the Mandarin version which handles A/P/B triplets).

### 6. Update `step2_video.sh`

For **romanization languages**, copy the 3-subtitle version from the Mandarin `step2_video.sh` (target top, romanization middle, English bottom).

For **non-romanization languages**, the French version works as-is (target top, English bottom).

The font may need changing for CJK scripts:
- **Korean/Japanese/Chinese:** Use `FontName=AppleGothic` or `FontName=STHeiti` on macOS
- **Arabic/Hebrew:** Use `FontName=Arial Unicode MS`
- **Latin scripts:** `FontName=Arial Unicode MS` works for all

### 7. Delete old vocab and frequency file

```bash
rm -rf vocab/ fr_50k.txt
```

### 8. Generate everything

```bash
export OPENAI_API_KEY=sk-...

# One-time: download freq list + generate vocab
curl -sL "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/es/es_50k.txt" -o es_50k.txt
python generate_vocab.py

# See word groups
python extract_word_groups.py

# Generate lessons
./run_cefr.sh A1          # all 10 lessons for A1
./run_cefr.sh B1 3        # just B1 lesson 3
```

## Quick-start commands for common languages

### Spanish
```bash
cp -r frenchVocab/ spanishVocab/ && cd spanishVocab/
curl -sL "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/es/es_50k.txt" -o es_50k.txt
# Edit language.py, generate_vocab.py (freq_file default), then:
python generate_vocab.py && python extract_word_groups.py
```

### Korean
```bash
cp -r frenchVocab/ koreanVocab/ && cd koreanVocab/
curl -sL "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ko/ko_50k.txt" -o ko_50k.txt
# Edit language.py, generate_vocab.py, generate_dialogue.py (add P: lines), step1_tts.py (add P: parsing), step2_video.sh (3 subtitle tracks)
python generate_vocab.py && python extract_word_groups.py
```

### Japanese
```bash
cp -r frenchVocab/ japaneseVocab/ && cd japaneseVocab/
curl -sL "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ja/ja_50k.txt" -o ja_50k.txt
# Same edits as Korean — add romaji P: line support
python generate_vocab.py && python extract_word_groups.py
```

### German
```bash
cp -r frenchVocab/ germanVocab/ && cd germanVocab/
curl -sL "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_50k.txt" -o de_50k.txt
# Edit language.py, generate_vocab.py (freq_file default)
# German has gendered nouns (m/f/n) — update gloss prompt for 3 genders
python generate_vocab.py && python extract_word_groups.py
```
