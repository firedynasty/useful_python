"""
language.py

Language configuration for the create_language_video pipeline.
Uncomment the language you want to use, comment out the others.

Used by: step1_tts.py, step3_gloss.py
"""

# ── Filipino / Tagalog ────────────────────────────────────────────────────────
# LANGUAGE_NAME = "Filipino"
# LANGUAGE_CODE = "tl"          # for Whisper transcription
# TTS_VOICE = "alloy"           # voice for target language lines
# GLOSS_PROMPT = (
#     "You are a Filipino/Tagalog linguistics assistant that creates word-by-word glosses for language learners.\n\n"
#     "For each line you receive, break down EVERY word. Return a JSON array of objects:\n"
#     '[\n  {"filipino": "Pilit", "english": "forcibly (adverb, from pilit \'force\')"},\n'
#     '  {"filipino": "kong", "english": "my + linker (ko + -ng)"},\n  ...\n]\n\n'
#     "Rules:\n"
#     "- Include grammar notes in parentheses for affixes, aspect, focus/voice, and linkers\n"
#     "- Note Tagalog verbal affixes and their meanings (e.g. mag-, -um-, naka-, in-, -an, i-)\n"
#     "- Note aspect where relevant (completed, contemplative, infinitive)\n"
#     "- Keep contractions/clipped forms together but explain them (e.g. \"'Di\" = \"hindi, not\")\n"
#     "- Handle common abbreviations: 'ko = ko, 'di = hindi, na'ng = na + ang, mo'y = mo + ay\n"
#     "- Keep words in the same order as the line\n"
#     "- For interjections or vocables (e.g. \"Woah\", \"ooh-woah\"), include them as-is\n"
#     "- Return ONLY the JSON array, no markdown, no explanation"
# )
# GLOSS_COLUMNS = ["Filipino", "English meaning"]
# TARGET_FIELD = "filipino"      # key name in gloss JSON + dialogue entries

# ── Mandarin Chinese ──────────────────────────────────────────────────────────
LANGUAGE_NAME = "Mandarin"
LANGUAGE_CODE = "zh"            # for Whisper transcription
TTS_VOICE = "alloy"             # voice for target language lines
GLOSS_PROMPT = (
    "You are a Mandarin Chinese linguistics assistant that creates word-by-word glosses for language learners.\n\n"
    "For each line you receive, break down EVERY word/phrase. Return a JSON array of objects:\n"
    '[  {"chinese": "我", "pinyin": "wǒ", "english": "I / me"},\n'
    '  {"chinese": "想", "pinyin": "xiǎng", "english": "want / think"},\n  ...\n]\n\n'
    "Rules:\n"
    "- Break down by meaningful units (words/phrases, not individual characters when they form a word)\n"
    "- Include pinyin with tone marks for every entry\n"
    "- Note grammar particles and their function (e.g. 了 le = completed action, 的 de = possessive/attributive)\n"
    "- Note measure words and their usage (e.g. 个 gè = general measure word)\n"
    "- Explain verb complements and directional verbs in parentheses\n"
    "- For chengyu (idioms) or set phrases, keep them together and explain the meaning\n"
    "- Keep words in the same order as the line\n"
    "- Return ONLY the JSON array, no markdown, no explanation"
)
GLOSS_COLUMNS = ["Chinese", "Pinyin", "English meaning"]
TARGET_FIELD = "chinese"        # key name in gloss JSON + dialogue entries

# ── Cantonese Chinese ─────────────────────────────────────────────────────────
# LANGUAGE_NAME = "Cantonese"
# LANGUAGE_CODE = "zh"            # Whisper uses "zh" for both; it auto-detects Cantonese
# TTS_VOICE = "alloy"             # voice for target language lines
# GLOSS_PROMPT = (
#     "You are a Cantonese Chinese linguistics assistant that creates word-by-word glosses for language learners.\n\n"
#     "For each line you receive, break down EVERY word/phrase. Return a JSON array of objects:\n"
#     '[  {"cantonese": "我", "jyutping": "ngo5", "english": "I / me"},\n'
#     '  {"cantonese": "想", "jyutping": "soeng2", "english": "want / think"},\n  ...\n]\n\n'
#     "Rules:\n"
#     "- Break down by meaningful units (words/phrases, not individual characters when they form a word)\n"
#     "- Include Jyutping romanization with tone numbers for every entry\n"
#     "- Note grammar particles and their function (e.g. 咗 zo2 = completed action, 嘅 ge3 = possessive)\n"
#     "- Note Cantonese-specific vocabulary vs Mandarin equivalents where helpful\n"
#     "- Explain verb complements and aspect markers in parentheses\n"
#     "- For colloquial Cantonese expressions, keep them together and explain the meaning\n"
#     "- Keep words in the same order as the line\n"
#     "- Return ONLY the JSON array, no markdown, no explanation"
# )
# GLOSS_COLUMNS = ["Cantonese", "Jyutping", "English meaning"]
# TARGET_FIELD = "cantonese"      # key name in gloss JSON + dialogue entries
