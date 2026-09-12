"""
_types.py

The Capability data model (spec data-model.md § Capability): the reusable
"feature" unit this toolkit is built around — replaces what used to require
a whole duplicated script + a `language.py`-style config file.

Validation here enforces data-model.md's rules directly, so an invalid
capability fails loudly at import time (during registry discovery) rather
than silently producing broken output later.
"""

from dataclasses import dataclass, field
from typing import List, Literal

# "Declares which of the supported parsers (FR-005) this capability uses;
#  no auto-detection" (data-model.md § Capability). "plain_lines" was added
# for monolingual (no-translation-pairing) capabilities like paraphrasing —
# one text line per entry, no A:/B: pair required.
InputFormat = Literal["two_line", "three_line", "csv_rows", "plain_lines"]

_VALID_INPUT_FORMATS = ("two_line", "three_line", "csv_rows", "plain_lines")


class CapabilityDefinitionError(ValueError):
    """Raised when a Capability is defined with invalid or incomplete fields."""


@dataclass(frozen=True)
class Capability:
    """One registered capability.

    Fields mirror data-model.md § Capability:
      name            - unique slug, e.g. "mandarin-gloss" (required)
      description     - one-line description (required, non-empty)
      language_name   - human-readable label, e.g. "Mandarin" (required)
      system_prompt   - the LLM system prompt, ported verbatim from the
                         source language.py (required, non-empty)
      input_format    - "two_line" | "three_line" | "csv_rows" (required)
      output_columns  - ordered CSV header columns (required, non-empty;
                         order is significant)
      target_field    - required when input_format is "two_line" or
                         "three_line"; not used for "csv_rows"/"plain_lines"
      model           - LLM model name (default: "gpt-4o", matching the
                         existing scripts' default)
      include_passthrough_headers - whether to emit the English/target-line
                         header rows above each line's output (FR-011).
                         Default True (existing gloss capabilities' shape).
                         A monolingual, one-row-per-line capability like
                         paraphrasing sets this False.
    """

    name: str
    description: str
    language_name: str
    system_prompt: str
    input_format: InputFormat
    output_columns: List[str] = field(default_factory=list)
    target_field: str = ""
    model: str = "gpt-4o"
    include_passthrough_headers: bool = True

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise CapabilityDefinitionError("Capability.name must be non-empty")
        if not self.description or not self.description.strip():
            raise CapabilityDefinitionError(f"{self.name}: description must be non-empty")
        if not self.language_name or not self.language_name.strip():
            raise CapabilityDefinitionError(f"{self.name}: language_name must be non-empty")
        if not self.system_prompt or not self.system_prompt.strip():
            raise CapabilityDefinitionError(f"{self.name}: system_prompt must be non-empty")
        if self.input_format not in _VALID_INPUT_FORMATS:
            raise CapabilityDefinitionError(
                f"{self.name}: input_format must be one of {_VALID_INPUT_FORMATS} "
                f"(got {self.input_format!r})"
            )
        if not self.output_columns:
            raise CapabilityDefinitionError(f"{self.name}: output_columns must be non-empty")
        if self.input_format in ("two_line", "three_line") and not self.target_field:
            raise CapabilityDefinitionError(
                f"{self.name}: target_field is required when input_format is "
                f"{self.input_format!r}"
            )
