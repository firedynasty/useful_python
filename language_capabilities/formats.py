"""
formats.py

The 3 input-format parsers declared by FR-005. Each capability declares
exactly one of these (no auto-detection — see research.md § 4's sibling
decision on explicit declaration). All three return a common shape so
engine.py can process every format the same way afterward: a list of
entries, each either

    {"type": "section", "name": <str>}

(a passthrough heading, e.g. "[Greeting]") or

    {"type": "line", "target": <str>, "english": <str>, "romanization": <str | None>}

"target" is the source-language text (what a capability's `target_field`
names in the original scripts); "romanization" is only ever populated by
the three_line format.
"""

import csv
import re
from typing import Dict, List, Optional

SECTION_PATTERN = re.compile(r"^\[(.+)\]$")
A_PATTERN = re.compile(r"^A:\s*(.+)$")
P_PATTERN = re.compile(r"^P:\s*(.+)$")
B_PATTERN = re.compile(r"^B:\s*(.+)$")


def parse_two_line(text: str) -> List[Dict]:
    """`A:`/`B:` dialogue pairs, with optional `[Section]` passthrough
    headings. Ported from create_language_video/step3_gloss.py."""
    raw = text.strip().split("\n")
    entries: List[Dict] = []
    i = 0
    while i < len(raw):
        line = raw[i].strip()
        if not line:
            i += 1
            continue

        section_match = SECTION_PATTERN.match(line)
        if section_match:
            entries.append({"type": "section", "name": section_match.group(1)})
            i += 1
            continue

        a_match = A_PATTERN.match(line)
        if a_match and i + 1 < len(raw):
            b_match = B_PATTERN.match(raw[i + 1].strip())
            if b_match:
                entries.append(
                    {
                        "type": "line",
                        "target": a_match.group(1),
                        "english": b_match.group(1),
                        "romanization": None,
                    }
                )
                i += 2
                continue
        i += 1
    return entries


def parse_three_line(text: str) -> List[Dict]:
    """`A:`/`P:`/`B:` triplets, falling back to `A:`/`B:` pairs when no `P:`
    line follows. Ported from
    create_language_video_2/koreanVocab/step3_gloss.py."""
    raw = text.strip().split("\n")
    entries: List[Dict] = []
    i = 0
    while i < len(raw):
        line = raw[i].strip()
        if not line:
            i += 1
            continue

        section_match = SECTION_PATTERN.match(line)
        if section_match:
            entries.append({"type": "section", "name": section_match.group(1)})
            i += 1
            continue

        a_match = A_PATTERN.match(line)
        if a_match:
            next_idx = i + 1
            romanization: Optional[str] = None
            if next_idx < len(raw):
                p_match = P_PATTERN.match(raw[next_idx].strip())
                if p_match:
                    romanization = p_match.group(1)
                    next_idx += 1
            if next_idx < len(raw):
                b_match = B_PATTERN.match(raw[next_idx].strip())
                if b_match:
                    entries.append(
                        {
                            "type": "line",
                            "target": a_match.group(1),
                            "english": b_match.group(1),
                            "romanization": romanization,
                        }
                    )
                    i = next_idx + 1
                    continue
        i += 1
    return entries


def parse_plain_lines(text: str) -> List[Dict]:
    """One line of plain text per entry — no `A:`/`B:` translation pairing,
    just lines (optionally grouped by `[Section]` passthrough headings).
    For monolingual capabilities, e.g. paraphrasing English lines, where
    there's no separate target-language/English pair, only the line itself.
    `english` and `romanization` are always None for this format."""
    raw = text.strip().split("\n")
    entries: List[Dict] = []
    for raw_line in raw:
        line = raw_line.strip()
        if not line:
            continue
        section_match = SECTION_PATTERN.match(line)
        if section_match:
            entries.append({"type": "section", "name": section_match.group(1)})
            continue
        entries.append({"type": "line", "target": line, "english": None, "romanization": None})
    return entries


def parse_csv_rows(path: str, target_field: str = "") -> List[Dict]:
    """Delimited-row (CSV) input. Ported from merging/generate_gloss.py's
    lyrics-table reading: the target-language column is looked up by header
    name (case-insensitive, matching `target_field`), falling back to
    column 1; the English column is looked up as "translation" or "english",
    falling back to the last column."""
    with open(path, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []

    header = [h.strip().lower() for h in rows[0]]
    target_lower = target_field.strip().lower()
    target_col = header.index(target_lower) if target_lower and target_lower in header else 1
    if "translation" in header:
        english_col = header.index("translation")
    elif "english" in header:
        english_col = header.index("english")
    else:
        english_col = len(rows[0]) - 1

    entries: List[Dict] = []
    for row in rows[1:]:
        if len(row) <= max(target_col, english_col):
            continue
        target = row[target_col].strip()
        english = row[english_col].strip()
        if target or english:
            entries.append(
                {
                    "type": "line",
                    "target": target,
                    "english": english,
                    "romanization": None,
                }
            )
    return entries
