"""
korean_gloss.py

Korean word-by-word gloss capability. Ported verbatim (FR-003) from
create_language_video_2/koreanVocab/language.py — see
specs/001-llm-line-processor/research.md § 1. This is the one launch
capability that uses the "three_line" (A:/P:/B:) input format.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="korean-gloss",
    description="Korean dialogue -> word-by-word gloss with romanization",
    language_name="Korean",
    system_prompt=(
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
    ),
    input_format="three_line",
    target_field="korean",
    output_columns=["Korean", "Romanization", "English meaning"],
)
