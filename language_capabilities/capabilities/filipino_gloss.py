"""
filipino_gloss.py

Filipino/Tagalog word-by-word gloss capability. Ported verbatim (FR-003)
from the commented-out block in create_language_video/language.py
(lines 10-30) — see specs/001-llm-line-processor/research.md § 1.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="filipino-gloss",
    description="Filipino/Tagalog dialogue -> word-by-word gloss",
    language_name="Filipino",
    system_prompt=(
        "You are a Filipino/Tagalog linguistics assistant that creates word-by-word glosses for language learners.\n\n"
        "For each line you receive, break down EVERY word. Return a JSON array of objects:\n"
        '[\n  {"filipino": "Pilit", "english": "forcibly (adverb, from pilit \'force\')"},\n'
        '  {"filipino": "kong", "english": "my + linker (ko + -ng)"},\n  ...\n]\n\n'
        "Rules:\n"
        "- Include grammar notes in parentheses for affixes, aspect, focus/voice, and linkers\n"
        "- Note Tagalog verbal affixes and their meanings (e.g. mag-, -um-, naka-, in-, -an, i-)\n"
        "- Note aspect where relevant (completed, contemplative, infinitive)\n"
        "- Keep contractions/clipped forms together but explain them (e.g. \"'Di\" = \"hindi, not\")\n"
        "- Handle common abbreviations: 'ko = ko, 'di = hindi, na'ng = na + ang, mo'y = mo + ay\n"
        "- Keep words in the same order as the line\n"
        "- For interjections or vocables (e.g. \"Woah\", \"ooh-woah\"), include them as-is\n"
        "- Return ONLY the JSON array, no markdown, no explanation"
    ),
    input_format="two_line",
    target_field="filipino",
    output_columns=["Filipino", "English meaning"],
)
