#!/usr/bin/env python3
"""
Smart Note - Split a multi-topic document and route each section into an
organized folder: append to existing files or create new ones.

Usage:
    python smart_note.py <folder> "Short single note"
    python smart_note.py <folder> -f multi_topic_summary.md
    python smart_note.py <folder> -f notes.md --dry-run

How it works:
    1. Splits input on markdown headings (## ) or --- separators into sections
    2. Skims the folder: subfolder names, filenames, first heading per file
    3. One API call routes ALL sections: append or create, which subfolder, which file
    4. Executes (or dry-runs) each placement
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Folder skimming
# ---------------------------------------------------------------------------

def skim_folder(folder: Path) -> dict:
    """Build a lightweight index: subfolder -> [{filename, title}].

    Reads only the first ~20 lines of each file looking for a heading.
    No full file reads.
    """
    index = {}

    for item in sorted(folder.iterdir()):
        if item.name.startswith('.') or item.name.startswith('_'):
            continue

        if item.is_dir():
            subfolder_name = item.name
            files_info = []
            for f in sorted(item.iterdir()):
                if f.is_file() and not f.name.startswith('.'):
                    title = _read_title(f)
                    files_info.append({'filename': f.name, 'title': title})
            index[subfolder_name] = files_info

        elif item.is_file():
            if '_root' not in index:
                index['_root'] = []
            title = _read_title(item)
            index['_root'].append({'filename': item.name, 'title': title})

    return index


def _read_title(filepath: Path, scan_lines: int = 20) -> str:
    """Extract the best title from a file by scanning the first N lines.

    Priority: first markdown heading found, else first non-empty line.
    """
    try:
        first_text = ""
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f):
                if i >= scan_lines:
                    break
                stripped = line.strip()
                if not stripped:
                    continue
                if not first_text:
                    first_text = stripped[:120]
                if stripped.startswith('#'):
                    return stripped.lstrip('#').strip()[:120]
        return first_text
    except Exception:
        return ""


def format_index_for_prompt(index: dict) -> str:
    """Format the skim index into a readable string for the AI prompt."""
    lines = []
    for subfolder, files in sorted(index.items()):
        if subfolder == '_root':
            lines.append("Root (unsorted files):")
        else:
            lines.append(f"{subfolder}/")

        for f in files:
            title_part = f" — {f['title']}" if f['title'] else ""
            lines.append(f"  {f['filename']}{title_part}")

        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section splitting
# ---------------------------------------------------------------------------

def split_sections(text: str) -> list[dict]:
    """Split a document into sections by ## headings.

    Returns list of {heading, body} dicts. A document with no ## headings
    is returned as a single section.
    """
    # Split on lines that start with ## (but not ### or deeper)
    parts = re.split(r'(?m)^(?=## (?!#))', text)

    sections = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        lines = part.split('\n', 1)
        first_line = lines[0].strip()

        # Check if this chunk starts with a ## heading
        if first_line.startswith('## '):
            heading = first_line.lstrip('#').strip()
            # Strip leading number prefix like "1. " or "7. "
            heading = re.sub(r'^\d+\.\s*', '', heading)
            body = lines[1].strip() if len(lines) > 1 else ""
        else:
            heading = ""
            body = part

        # Skip preamble-only sections (just a title + date, no substance)
        body_stripped = re.sub(r'---', '', body).strip()
        if not body_stripped and not heading:
            continue

        sections.append({'heading': heading, 'body': body})

    # If we only got one section (no ## splits), return the whole thing
    if len(sections) <= 1:
        return [{'heading': '', 'body': text.strip()}]

    # Filter out very short preamble sections (< 50 chars, no heading)
    filtered = []
    for s in sections:
        if not s['heading'] and len(s['body']) < 50:
            # Preamble like "# Title\n**Date:** ...\n## Context\n..."
            # Attach to next section if it exists
            continue
        filtered.append(s)

    return filtered if filtered else sections


def format_sections_for_prompt(sections: list[dict]) -> str:
    """Format sections into a numbered list for the AI prompt."""
    lines = []
    for i, s in enumerate(sections, 1):
        heading = s['heading'] or "(no heading)"
        # Truncate body for the prompt — AI only needs enough to understand the topic
        preview = s['body'][:300]
        if len(s['body']) > 300:
            preview += "..."
        lines.append(f"[{i}] {heading}\n{preview}\n")
    return "\n---\n".join(lines)


# ---------------------------------------------------------------------------
# AI routing
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You route note sections into an organized folder of markdown/text files.

You will receive:
1. A FOLDER INDEX showing subfolders, filenames, and titles of existing files
2. A numbered list of SECTIONS from a document the user wants to save

For EACH section, decide:
- APPEND to an existing file if the section clearly extends that file's topic
- CREATE a new file in the best-fitting subfolder if it's a distinct topic
- SKIP if the section is a pure summary/recap of other sections with no new information

Rules:
- **Spread across subfolders.** The folder structure exists for a reason. A section about strategy belongs in strategy/, not iran-war/. A section about Israel belongs in israel/, not iran-war/. Route by the section's PRIMARY topic, not the broader context of the document.
- Prefer APPEND when the section topic closely matches an existing file's specific subject
- Prefer CREATE when the section covers something new, even within the same subfolder
- For new filenames: use snake_case, descriptive, .md extension
- The "_root" entries are unsorted files at the top level — avoid placing notes there
- If two sections would go to the same new file, that's fine — they'll be written together
- SKIP summary/recap/key-themes sections that just restate points from other sections

Routing guidance — match the section's core topic:
- Military operations, war timeline, battlefield events → iran-war/
- Strategy, options, off-ramps, what-should-X-do → strategy/
- Nuclear weapons, enrichment, deterrence → nuclear/
- Israel-specific angles, US-Israel relationship → israel/
- Economics, oil, fiscal policy → misc/ (or a fitting subfolder)
- Geopolitics, third-party countries → geopolitics/
- Propaganda, media framing, narratives → propaganda/

Return ONLY a JSON object (no prose, no code fences):
{
  "decisions": [
    {
      "section": 1,
      "action": "append" or "create" or "skip",
      "subfolder": "subfolder_name",
      "filename": "target_file.md",
      "reason": "one sentence why"
    },
    ...
  ]
}"""


def route_sections(sections: list[dict], index: dict, model: str) -> list[dict]:
    """Ask OpenAI where to place each section. Returns list of decisions."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: pip install openai", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    index_text = format_index_for_prompt(index)
    sections_text = format_sections_for_prompt(sections)

    user_msg = f"FOLDER INDEX:\n{index_text}\n\nSECTIONS:\n{sections_text}"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    data = json.loads(resp.choices[0].message.content or "{}")
    return data.get('decisions', [])


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def execute_decisions(folder: Path, sections: list[dict], decisions: list[dict],
                      dry_run: bool):
    """Apply each routing decision: append or create."""

    # Separate skips from actionable decisions
    skipped = [d for d in decisions if d.get('action') == 'skip']
    actionable = [d for d in decisions if d.get('action') != 'skip']

    # Group sections that target the same file (e.g., two sections both CREATE
    # the same new file) so they get written together.
    # Key: (action, subfolder, filename) -> list of section indices
    grouped = {}
    for d in actionable:
        sec_idx = d.get('section', 0) - 1
        if sec_idx < 0 or sec_idx >= len(sections):
            continue
        key = (d['action'], d['subfolder'], d['filename'])
        if key not in grouped:
            grouped[key] = {'decision': d, 'section_indices': []}
        grouped[key]['section_indices'].append(sec_idx)

    print("=" * 60)
    print(f"ROUTING PLAN  ({len(actionable)} to write, {len(skipped)} skipped)")
    print("=" * 60)

    if skipped:
        for d in skipped:
            sec_idx = d.get('section', 0) - 1
            heading = sections[sec_idx]['heading'] if 0 <= sec_idx < len(sections) else "?"
            print(f"\n  SKIP    [{d['section']}] {heading}")
            print(f"         Reason: {d.get('reason', '')}")

    for key, group in grouped.items():
        action, subfolder, filename = key
        reason = group['decision'].get('reason', '')
        sec_nums = [i + 1 for i in group['section_indices']]
        sec_label = ", ".join(str(n) for n in sec_nums)

        if subfolder == '_root':
            target_display = filename
        else:
            target_display = f"{subfolder}/{filename}"

        headings = []
        for i in group['section_indices']:
            h = sections[i]['heading'] or "(no heading)"
            headings.append(h)

        print(f"\n  {action.upper():6s}  {target_display}")
        print(f"         Section(s) {sec_label}: {'; '.join(headings)}")
        print(f"         Reason: {reason}")

    print()

    if dry_run:
        print("DRY RUN — no files written. Remove --dry-run to execute.")
        return

    # Execute
    print("Writing...")
    print()

    written = 0
    for key, group in grouped.items():
        action, subfolder, filename = key
        sec_indices = group['section_indices']

        # Build the combined text for all sections targeting this file
        combined_parts = []
        for i in sec_indices:
            s = sections[i]
            if s['heading']:
                combined_parts.append(f"## {s['heading']}\n\n{s['body']}")
            else:
                combined_parts.append(s['body'])
        combined_text = "\n\n---\n\n".join(combined_parts)

        # Resolve target path
        if subfolder == '_root':
            target = folder / filename
        else:
            target = folder / subfolder / filename

        target.parent.mkdir(parents=True, exist_ok=True)

        if action == 'append':
            if not target.exists():
                print(f"  {target.relative_to(folder)} — doesn't exist, creating instead")
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(combined_text + "\n")
            else:
                with open(target, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n---\n\n{combined_text}\n")
                print(f"  APPEND  {target.relative_to(folder)}")
        else:
            if target.exists():
                stem, suffix = target.stem, target.suffix
                n = 2
                while target.exists():
                    target = target.parent / f"{stem}_{n}{suffix}"
                    n += 1
                print(f"  CREATE  {target.relative_to(folder)}  (name adjusted, original taken)")
            else:
                print(f"  CREATE  {target.relative_to(folder)}")
            with open(target, 'w', encoding='utf-8') as f:
                f.write(combined_text + "\n")

        written += 1

    print(f"\nDone: {written} file(s) written.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Smart note taker — split and route notes into organized folders',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single short note
    python smart_note.py ~/notes/iran "Day 12: Iran fired 30 missiles at Haifa"

    # Multi-section document
    python smart_note.py ~/notes/iran -f new_iran_notes.md

    # Preview routing without writing
    python smart_note.py ~/notes/iran -f notes.md --dry-run

    # See what the AI sees (no API call)
    python smart_note.py ~/notes/iran --skim

    # See how the input splits into sections (no API call)
    python smart_note.py ~/notes/iran -f notes.md --split
        """
    )

    parser.add_argument('folder', type=Path, help='Organized folder to add notes to')
    parser.add_argument('note', nargs='?', help='Note text (or use -f for file)')
    parser.add_argument('-f', '--file', type=Path, help='Read note from file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show routing plan without writing')
    parser.add_argument('--model', default='gpt-4o',
                        help='OpenAI model (default: gpt-4o)')
    parser.add_argument('--skim', action='store_true',
                        help='Print the folder index and exit (no API call)')
    parser.add_argument('--split', action='store_true',
                        help='Show how the input splits into sections (no API call)')

    args = parser.parse_args()
    folder = Path(os.path.expanduser(str(args.folder)))

    if not folder.exists():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    # Build the lightweight index
    index = skim_folder(folder)

    if args.skim:
        print(format_index_for_prompt(index))
        return

    # Get the note text
    if args.file:
        fpath = Path(os.path.expanduser(str(args.file)))
        if not fpath.exists():
            print(f"File not found: {fpath}")
            sys.exit(1)
        text = fpath.read_text(encoding='utf-8').strip()
    elif args.note:
        text = args.note.strip()
    else:
        parser.error("Provide a note as an argument or with -f <file>")
        return

    if not text:
        print("Empty input, nothing to do.")
        return

    # Split into sections
    sections = split_sections(text)

    if args.split:
        print(f"Split into {len(sections)} section(s):\n")
        for i, s in enumerate(sections, 1):
            heading = s['heading'] or "(no heading)"
            body_preview = s['body'][:100].replace('\n', ' ')
            if len(s['body']) > 100:
                body_preview += "..."
            print(f"  [{i}] {heading}")
            print(f"      {body_preview}")
            print()
        return

    print(f"Folder:   {folder}")
    print(f"Sections: {len(sections)}")
    for i, s in enumerate(sections, 1):
        heading = s['heading'] or "(no heading)"
        print(f"  [{i}] {heading}")
    print()

    # Route all sections in one API call
    decisions = route_sections(sections, index, args.model)

    if not decisions:
        print("AI returned no routing decisions.")
        sys.exit(1)

    # Execute
    execute_decisions(folder, sections, decisions, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
