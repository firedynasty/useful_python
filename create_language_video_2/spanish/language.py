"""
language.py

Spanish language configuration for the create_language_video pipeline.
Used by: step1_tts.py, step3_gloss.py
"""

LANGUAGE_NAME = "Spanish"
LANGUAGE_CODE = "es"
TTS_VOICE = "alloy"
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
