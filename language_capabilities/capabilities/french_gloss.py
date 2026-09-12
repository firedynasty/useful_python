"""
french_gloss.py

French word-by-word gloss capability. Ported verbatim (FR-003) from
create_language_video_2/frenchVocab/language.py — see
specs/001-llm-line-processor/research.md § 1.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="french-gloss",
    description="French dialogue -> word-by-word gloss",
    language_name="French",
    system_prompt=(
        "You are a French linguistics assistant that creates word-by-word glosses for language learners.\n\n"
        "For each line you receive, break down EVERY word. Return a JSON array of objects:\n"
        '[  {"french": "Je", "english": "I (subject pronoun, 1st person singular)"},\n'
        '  {"french": "voudrais", "english": "would like (conditional of vouloir)"},\n  ...\n]\n\n'
        "Rules:\n"
        "- Include grammar notes in parentheses for conjugation, gender, number, tense, and mood\n"
        "- Note verb tense/mood (e.g. passé composé, subjonctif, conditionnel)\n"
        "- Note gender and number for nouns and adjectives (e.g. f., m., pl.)\n"
        "- Explain contractions (e.g. l' = le/la before vowel, j' = je before vowel, du = de + le)\n"
        "- Note liaison and elision where relevant\n"
        "- Keep words in the same order as the line\n"
        "- For idiomatic expressions, keep them together and explain the meaning\n"
        "- Return ONLY the JSON array, no markdown, no explanation"
    ),
    input_format="two_line",
    target_field="french",
    output_columns=["French", "English meaning"],
)
