#!/usr/bin/env python3
"""
Propose Config - Ask OpenAI to read a folder's filenames and draft a YAML
subject block for archive_config.yaml.

The model only sees filenames (not contents), so this is cheap. Review the
printed YAML and paste it into archive_config.yaml yourself; nothing is
written automatically unless you pass --append.

Usage:
    python propose_config.py ~/Downloads/iran Iran
    python propose_config.py ~/Downloads/iran Iran --model gpt-4o
    python propose_config.py ~/Downloads/iran Iran --append
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: pip install openai", file=sys.stderr)
    sys.exit(1)


DUP_RE = re.compile(r"^(.*?) \((\d+)\)(\.[^.]+)$")

SYSTEM_PROMPT = """You design folder routing rules for a keyword-based file sorter.

Given a list of filenames from one folder, propose a YAML block that groups
them into 4-8 topic subfolders plus one fallback. Output MUST be exactly
one YAML block matching this structure:

<SubjectName>:
  path: <path-as-given>
  # Order matters: first match wins.
  routes:
    <subfolder-1>:
      - keyword
      - keyword
    <subfolder-2>:
      - keyword
    <fallback-name>: []   # one empty-list fallback for unmatched files

Rules:
- Subfolder names: lowercase, hyphen-free single words when possible
- Keywords: lowercase substrings compared against lowercase filenames.
  Prefer distinctive tokens that appear in the actual filenames (use
  underscores/spaces as they appear). Avoid keywords that would match
  multiple subfolders.
- Put narrower/more specific subfolders first.
- Include exactly one fallback subfolder with an empty list (e.g.,
  `misc: []` or `context: []`).
- Output ONLY the YAML block. No prose, no fences, no commentary.
"""


def dedupe_listing(names: list[str]) -> list[str]:
    """Drop '(N)' copies from a name list for cleaner signal to the model."""
    base_names = set(names)
    kept = []
    for n in names:
        m = DUP_RE.match(n)
        if m and (m.group(1) + m.group(3)) in base_names:
            continue
        kept.append(n)
    return kept


def write_subject_block(config_path: Path, subject: str, yaml_block: str) -> str:
    """Insert `yaml_block` into `config_path`, replacing any existing block for
    `subject`. A subject block starts at a line `^<subject>:` (root-level, no
    indent) and runs until the next root-level key or end of file.

    Returns "replaced" or "appended" to describe the action taken.
    """
    text = config_path.read_text()
    lines = text.splitlines(keepends=True)

    # Find the start of the existing subject block, if any.
    start_re = re.compile(rf"^{re.escape(subject)}:\s*$")
    # A root-level key is any non-indented, non-comment, non-blank line ending
    # with ':'. Used to find where the existing block ends.
    root_key_re = re.compile(r"^[^\s#][^:]*:\s*(#.*)?$")

    start_idx = next((i for i, ln in enumerate(lines) if start_re.match(ln)), None)

    # Normalize the new block: ensure single trailing newline.
    new_block = yaml_block.rstrip("\n") + "\n"

    if start_idx is None:
        # Append — with one blank line of separation from prior content.
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        config_path.write_text(text + sep + new_block)
        return "appended"

    # Find end of the existing block: first subsequent root-level key.
    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        if root_key_re.match(lines[j]):
            end_idx = j
            break

    # Strip trailing blank lines inside the replaced block so spacing stays tidy.
    replacement_lines = new_block.splitlines(keepends=True)
    new_lines = lines[:start_idx] + replacement_lines
    # Ensure a blank line before whatever follows (if anything).
    if end_idx < len(lines):
        if not new_lines[-1].endswith("\n"):
            new_lines[-1] = new_lines[-1] + "\n"
        if not new_lines or not new_lines[-1].strip() == "":
            new_lines.append("\n")
        new_lines.extend(lines[end_idx:])

    config_path.write_text("".join(new_lines))
    return "replaced"


def propose(client: OpenAI, model: str, subject: str, path_str: str,
            filenames: list[str]) -> str:
    user_msg = (
        f"Subject name: {subject}\n"
        f"Folder path:  {path_str}\n\n"
        f"Filenames ({len(filenames)}):\n"
        + "\n".join(f"- {n}" for n in filenames)
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.2,
    )
    text = (resp.choices[0].message.content or "").strip()
    # Strip code fences if the model added them despite instructions.
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip() + "\n"


def main():
    ap = argparse.ArgumentParser(
        description="Ask OpenAI to draft a YAML subject block for archive_config.yaml.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("source", type=Path, help="Folder to analyze")
    ap.add_argument("subject", help="Subject name to use in the YAML block (e.g. Iran)")
    ap.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
    ap.add_argument("--config", type=Path,
                    default=Path(__file__).parent / "archive_config.yaml",
                    help="Target config file (only used with --append)")
    ap.add_argument("--append", action="store_true",
                    help="Write the proposal to archive_config.yaml, replacing any existing block for this subject")
    args = ap.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_dir():
        print(f"Not a directory: {source}", file=sys.stderr)
        sys.exit(1)

    names = sorted(
        f.name for f in source.iterdir()
        if f.is_file() and not f.name.startswith(".")
    )
    if not names:
        print(f"No files in {source}", file=sys.stderr)
        sys.exit(1)

    names = dedupe_listing(names)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Use the literal path the user passed (pre-resolve) so the YAML reads
    # naturally, e.g. "~/Downloads/iran" instead of "/Users/.../iran".
    path_str = str(args.source)
    yaml_block = propose(client, args.model, args.subject, path_str, names)

    print(yaml_block)

    if args.append:
        if not args.config.exists():
            print(f"Config not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        action = write_subject_block(args.config, args.subject, yaml_block)
        print(f"# {action} {args.subject} in {args.config}", file=sys.stderr)


if __name__ == "__main__":
    main()
