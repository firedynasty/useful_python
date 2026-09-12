"""
paraphrase_en.py

Paraphrases a plain English line into one rewritten line. Monolingual — no
translation pairing, so it uses input_format="plain_lines" and disables the
gloss-style passthrough header rows (include_passthrough_headers=False):
each input line becomes exactly one output row, [Original, Paraphrase].

Designed for a local LLM backend (`run --backend local`, e.g. Ollama — see
README.md), but works against any OpenAI-compatible client, including the
cloud default. `model` defaults to "qwen3:8b" — validated live against this
capability with no JSON-parsing issues (Qwen3's optional "thinking mode"
did not leak <think> reasoning into the response for this prompt shape).
Override with --model for a different local model or a cloud one.
"""

from ._types import Capability

CAPABILITY = Capability(
    name="paraphrase-en",
    description="Paraphrase a plain English line into one rewritten line",
    language_name="English",
    system_prompt=(
        "You are an English writing assistant that paraphrases a single line at a time.\n\n"
        "For the line you receive, return a JSON array with EXACTLY ONE object:\n"
        '[  {"paraphrase": "..."}  ]\n\n'
        "Rules:\n"
        "- Preserve the original meaning; do not add or remove information\n"
        "- Vary word choice and sentence structure from the original\n"
        "- Keep roughly the same length and register (casual stays casual, formal stays formal)\n"
        "- Return ONLY the JSON array, no markdown, no explanation"
    ),
    input_format="plain_lines",
    output_columns=["Original", "Paraphrase"],
    include_passthrough_headers=False,
    model="qwen3:8b",
)
