"""
cantonese_gloss.py

Cantonese word-by-word gloss capability. Ported verbatim (FR-003) from the
commented-out block in create_language_video/language.py (lines 54-74) —
see specs/001-llm-line-processor/research.md § 1.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="cantonese-gloss",
    description="Cantonese dialogue -> word-by-word gloss with Jyutping",
    language_name="Cantonese",
    system_prompt=(
        "You are a Cantonese Chinese linguistics assistant that creates word-by-word glosses for language learners.\n\n"
        "For each line you receive, break down EVERY word/phrase. Return a JSON array of objects:\n"
        '[  {"cantonese": "我", "jyutping": "ngo5", "english": "I / me"},\n'
        '  {"cantonese": "想", "jyutping": "soeng2", "english": "want / think"},\n  ...\n]\n\n'
        "Rules:\n"
        "- Break down by meaningful units (words/phrases, not individual characters when they form a word)\n"
        "- Include Jyutping romanization with tone numbers for every entry\n"
        "- Note grammar particles and their function (e.g. 咗 zo2 = completed action, 嘅 ge3 = possessive)\n"
        "- Note Cantonese-specific vocabulary vs Mandarin equivalents where helpful\n"
        "- Explain verb complements and aspect markers in parentheses\n"
        "- For colloquial Cantonese expressions, keep them together and explain the meaning\n"
        "- Keep words in the same order as the line\n"
        "- Return ONLY the JSON array, no markdown, no explanation"
    ),
    input_format="two_line",
    target_field="cantonese",
    output_columns=["Cantonese", "Jyutping", "English meaning"],
)
