"""
language_capabilities

A reusable toolkit for the "send each line of a dialogue to an LLM, get a
structured gloss back" pattern duplicated across create_language_video/ and
create_language_video_2/. Each existing prompt/format/output-column bundle
is registered here as a "capability" (see capabilities/) instead of living
in its own duplicated script.

Runtime baseline (see specs/001-llm-line-processor/plan.md § Technical
Context): Python 3.11, and the already-installed `openai` (v1.x) package —
no new third-party dependency is introduced by this toolkit.

Commands:
    python -m language_capabilities.cli list
    python -m language_capabilities.cli run --capability <name> --input <path>

See specs/001-llm-line-processor/quickstart.md for full runnable scenarios,
and NEW_CAPABILITY_GUIDE.md for how to add a new capability.
"""
