"""
engine.py

Shared processing engine (FR-006, FR-007, FR-008, FR-011): parses an input
file per a Capability's declared input_format, calls the LLM exactly once
per line, maps the JSON response onto the capability's output_columns, and
writes the result as a CSV — reproducing create_language_video/step3_gloss.py's
behavior. See specs/001-llm-line-processor/research.md §§ 2, 5 and
data-model.md § Processing Run / § Gloss Record.
"""

import csv
import json
import os
import time
from typing import Optional

from . import formats
from .capabilities import Capability


class ProcessingRun:
    """Tracks one run (data-model.md § Processing Run)."""

    def __init__(self, capability: Capability, input_path: str, output_path: str):
        self.capability = capability
        self.input_path = input_path
        self.output_path = output_path
        self.total_lines = 0
        self.current_line = 0
        self.error_count = 0


def _parse_input(capability: Capability, input_path: str):
    if capability.input_format == "csv_rows":
        return formats.parse_csv_rows(input_path, capability.target_field)

    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    if capability.input_format == "two_line":
        return formats.parse_two_line(text)
    if capability.input_format == "three_line":
        return formats.parse_three_line(text)
    if capability.input_format == "plain_lines":
        return formats.parse_plain_lines(text)
    raise ValueError(f"Unknown input_format {capability.input_format!r}")


def _build_user_prompt(capability: Capability, entry: dict) -> str:
    if entry.get("english") is None:
        # Monolingual capability (e.g. paraphrasing): no translation pair,
        # just send the line itself.
        return entry["target"]
    parts = [f"{capability.language_name}:", entry["target"]]
    if entry.get("romanization"):
        parts += ["", f"Romanization: {entry['romanization']}"]
    parts += ["", "English:", entry["english"]]
    return "\n".join(parts)


def _strip_code_fence(raw_resp: str) -> str:
    raw_resp = raw_resp.strip()
    if raw_resp.startswith("```"):
        raw_resp = raw_resp.split("\n", 1)[-1]
        raw_resp = raw_resp.rsplit("```", 1)[0]
    return raw_resp


def _map_row(capability: Capability, gloss_obj: dict, source_text: str) -> list:
    """Best-effort JSON-key-to-output-column mapping (data-model.md § Gloss
    Record): case-insensitive, prefix-tolerant match, blank cell fallback —
    ported verbatim from create_language_video/step3_gloss.py's row-building
    loop. A column literally named "Original" is special-cased to hold the
    source input line itself rather than a matched LLM JSON key, for
    capabilities (like paraphrasing) that want the original line alongside
    the LLM's output in the same row."""
    row = []
    for col in capability.output_columns:
        col_lower = col.lower().replace(" ", "_")
        if col_lower == "original":
            row.append(source_text)
            continue
        matched = False
        for key in gloss_obj:
            if key.lower() == col_lower or col_lower.startswith(key.lower()):
                row.append(gloss_obj[key])
                matched = True
                break
        if not matched:
            if col_lower == "english_meaning":
                row.append(gloss_obj.get("english", ""))
            else:
                row.append(gloss_obj.get(col_lower, ""))
    return row


def run_capability(
    client,
    capability: Capability,
    input_path: str,
    output_path: str,
    model: Optional[str] = None,
) -> ProcessingRun:
    """Executes one Processing Run.

    `client` is an already-constructed `openai.OpenAI` instance — dependency
    injected (rather than built here) so this function stays easy to test
    with a fake client.
    """
    model = model or capability.model
    run = ProcessingRun(capability, input_path, output_path)

    entries = _parse_input(capability, input_path)
    run.total_lines = sum(1 for e in entries if e["type"] == "line")
    print(f"Parsed {run.total_lines} dialogue lines ({capability.language_name})")

    blank_columns = len(capability.output_columns) - 1
    output_rows = []

    for entry in entries:
        if entry["type"] == "section":
            output_rows.append([entry["name"]] + [""] * blank_columns)
            continue

        run.current_line += 1
        preview = entry["target"][:40]
        print(f"  [{run.current_line}/{run.total_lines}] {preview}...")

        # Passthrough header rows above each gloss block (FR-011). Skipped
        # for capabilities that want one row per line instead (e.g.
        # paraphrasing, where the original line is its own output column).
        if capability.include_passthrough_headers:
            output_rows.append([entry["english"]] + [""] * blank_columns)
            output_rows.append([entry["target"]] + [""] * blank_columns)

        user_prompt = _build_user_prompt(capability, entry)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": capability.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        raw_resp = _strip_code_fence(response.choices[0].message.content)

        try:
            glosses = json.loads(raw_resp)
        except json.JSONDecodeError:
            run.error_count += 1
            print(f"    WARNING: line {run.current_line} ({preview}...) — invalid JSON, skipping")
            print(f"    {raw_resp[:200]}")
            time.sleep(0.5)
            continue

        print(f"    Got {len(glosses)} words")
        for gloss_obj in glosses:
            output_rows.append(_map_row(capability, gloss_obj, entry["target"]))

        time.sleep(0.5)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    if os.path.exists(output_path):
        print(f"  Note: overwriting existing output file {output_path}")

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(capability.output_columns)
        writer.writerows(output_rows)

    print(f"\nDone! Wrote {len(output_rows)} rows to {output_path}")
    if run.error_count:
        print(f"({run.error_count} line(s) skipped due to invalid LLM responses)")

    return run
