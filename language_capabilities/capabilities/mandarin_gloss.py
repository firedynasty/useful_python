"""
mandarin_gloss.py

Mandarin word-by-word gloss capability. Ported verbatim (FR-003) from the
active block in create_language_video/language.py (lines 33-52), also
byte-identical in create_language_video_2/language.py — see
specs/001-llm-line-processor/research.md § 1.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="mandarin-gloss",
    description="Mandarin dialogue -> word-by-word gloss with pinyin",
    language_name="Mandarin",
    system_prompt=(
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
    ),
    input_format="two_line",
    target_field="chinese",
    output_columns=["Chinese", "Pinyin", "English meaning"],
)
