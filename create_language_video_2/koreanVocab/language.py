"""
language.py

Korean language configuration for the create_language_video pipeline.
Used by: step1_tts.py, step3_gloss.py
"""

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
    "- For idiomatic expressions, keep them together and explain the meaning\n"
    "- Return ONLY the JSON array, no markdown, no explanation"
)
GLOSS_COLUMNS = ["Korean", "Romanization", "English meaning"]
TARGET_FIELD = "korean"
