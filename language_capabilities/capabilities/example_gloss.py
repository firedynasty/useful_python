"""
example_gloss.py

TEMPLATE — copy this file to add a new capability. It is registered under
the name "example-gloss" purely as a working, runnable demonstration; it is
not a real launch capability (its prompt is intentionally trivial). See
../NEW_CAPABILITY_GUIDE.md.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="example-gloss",
    description="TEMPLATE — copy this file to add a new gloss capability",
    language_name="Example",
    system_prompt=(
        "You are a linguistics assistant that creates word-by-word glosses for language learners.\n\n"
        "For each line you receive, break down EVERY word/phrase. Return a JSON array of objects:\n"
        '[  {"example": "word", "english": "meaning"},\n  ...\n]\n\n'
        "Rules:\n"
        "- Keep words in the same order as the line\n"
        "- Return ONLY the JSON array, no markdown, no explanation"
    ),
    input_format="two_line",
    target_field="example",
    output_columns=["Example", "English meaning"],
)
