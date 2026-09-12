#!/usr/bin/env python3
"""
script.py

Paraphrase a .txt file, one line at a time.

This is a thin wrapper around the `paraphrase-en` capability in
../language_capabilities/ — it does not reimplement the LLM call, JSON
parsing, or per-line error handling; see ../language_capabilities/engine.py
for that. This script just runs the capability's engine into a temporary
CSV, then extracts the "Paraphrase" column back out as a plain .txt.

By default it targets a local Ollama instance (no OPENAI_API_KEY needed),
using the paraphrase-en capability's default model (qwen3:8b). Pass
--backend openai to use the cloud API instead.

Usage:
  python script.py --input notes.txt
  python script.py --input notes.txt --output notes_paraphrased.txt
  python script.py --input notes.txt --backend openai --model gpt-4o-mini
"""

import argparse
import csv
import os
import sys
import tempfile

# Make the repo-root `language_capabilities` package importable regardless
# of the working directory this script is run from.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from language_capabilities import engine  # noqa: E402
from language_capabilities.capabilities import CATALOG  # noqa: E402

CAPABILITY_NAME = "paraphrase-en"
DEFAULT_LOCAL_BASE_URL = "http://localhost:11434/v1/"


def _build_client(backend: str, base_url: str):
    from openai import OpenAI

    if backend == "local":
        return OpenAI(api_key="ollama", base_url=base_url or DEFAULT_LOCAL_BASE_URL)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: OPENAI_API_KEY not set. Export it first, or pass --backend local "
            "to use a local server like Ollama instead.",
            file=sys.stderr,
        )
        sys.exit(1)
    return OpenAI(api_key=api_key)


def _default_output_path(input_path: str) -> str:
    base, ext = os.path.splitext(input_path)
    return f"{base}_paraphrased{ext or '.txt'}"


def _csv_to_paraphrased_txt(csv_path: str, output_path: str) -> None:
    """Extract just the paraphrased line for each row. A row with no
    paraphrase (blank second column) is a `[Section]` passthrough header
    from the input, not a real line — written back out as `[Section]`."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    lines = []
    for row in rows[1:]:  # skip header
        if not row:
            continue
        original, paraphrase = (row + [""])[:2]
        if paraphrase:
            lines.append(paraphrase)
        else:
            lines.append(f"[{original}]")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Paraphrase a .txt file, one line at a time.")
    parser.add_argument("--input", required=True, help="Path to the input .txt file (one English line per line)")
    parser.add_argument(
        "--output",
        default=None,
        help="Path for the paraphrased .txt (default: <input>_paraphrased.txt)",
    )
    parser.add_argument(
        "--backend",
        choices=["local", "openai"],
        default="local",
        help="LLM backend (default: local, e.g. Ollama)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help=f"Local backend base URL (default: {DEFAULT_LOCAL_BASE_URL})",
    )
    parser.add_argument(
        "--model", default=None, help="Override the capability's default model (default: qwen3:8b)"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    capability = CATALOG[CAPABILITY_NAME]
    client = _build_client(args.backend, args.base_url)
    output_path = args.output or _default_output_path(args.input)

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = os.path.join(tmp_dir, "paraphrased.csv")
        engine.run_capability(
            client=client,
            capability=capability,
            input_path=args.input,
            output_path=csv_path,
            model=args.model,
        )
        _csv_to_paraphrased_txt(csv_path, output_path)

    print(f"\nParaphrased text written to {output_path}")


if __name__ == "__main__":
    main()
