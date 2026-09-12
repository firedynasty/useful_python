"""
spanish_gloss.py

Spanish word-by-word gloss capability. Ported verbatim (FR-003) from
create_language_video_2/spanish/language.py — see
specs/001-llm-line-processor/research.md § 1.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="spanish-gloss",
    description="Spanish dialogue -> word-by-word gloss",
    language_name="Spanish",
    system_prompt=(
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
    ),
    input_format="two_line",
    target_field="spanish",
    output_columns=["Spanish", "English meaning"],
)
