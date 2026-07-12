#!/usr/bin/env python3
"""
collapse_transcript.py

Fixes YouTube auto-caption "rolling cue" duplication, where flattened
transcripts repeat overlapping chunks of text (e.g. "We are about to
face a health We are about to face a health apocalypse..."), and
decodes HTML entities (e.g. &gt; -> >) left over from VTT source data.

Usage:
    python3 collapse_transcript.py input.txt output.txt
    python3 collapse_transcript.py input.txt          # prints to stdout
    cat input.txt | python3 collapse_transcript.py -  # read from stdin
"""

import sys
import re
import html
import textwrap

MAX_OVERLAP_WORDS = 60  # generous ceiling; rolling cues rarely repeat this much


def collapse_repeats(words):
    """
    Greedily walk the word stream. At each position, check whether the
    upcoming words are just a repeat of the tail end of what's already
    been emitted. If so, skip them instead of appending duplicates.
    """
    output = []
    i = 0
    n = len(words)

    while i < n:
        max_check = min(len(output), MAX_OVERLAP_WORDS, n - i)
        overlap = 0

        for L in range(max_check, 0, -1):
            if output[-L:] == words[i:i + L]:
                overlap = L
                break

        if overlap > 0:
            i += overlap  # skip the repeated chunk entirely
        else:
            output.append(words[i])
            i += 1

    return output


def process_text(raw_text):
    header_pattern = re.compile(r"^\[\d{1,2}:\d{2}(:\d{2})?\]$")
    lines = raw_text.splitlines()

    result_lines = []
    buffer_words = []

    def flush_buffer():
        if buffer_words:
            cleaned = collapse_repeats(buffer_words)
            wrapped = textwrap.fill(" ".join(cleaned), width=45)
            result_lines.append(wrapped)
            buffer_words.clear()

    for line in lines:
        stripped = line.strip()
        if stripped == "" or header_pattern.match(stripped) or stripped.startswith("http"):
            flush_buffer()
            result_lines.append(line)
        else:
            # Decode HTML entities (&gt; -> >, &amp; -> &, etc.) before
            # splitting into words, so entities aren't accidentally
            # treated as separate tokens or left encoded in the output.
            decoded = html.unescape(stripped)
            buffer_words.extend(decoded.split())

    flush_buffer()
    return "\n".join(result_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: collapse_transcript.py <input file or -> [output file]", file=sys.stderr)
        sys.exit(1)

    input_arg = sys.argv[1]
    if input_arg == "-":
        raw_text = sys.stdin.read()
    else:
        with open(input_arg, encoding="utf-8") as f:
            raw_text = f.read()

    result = process_text(raw_text)

    if len(sys.argv) >= 3:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Collapsed transcript saved to: {sys.argv[2]}")
    else:
        print(result)


if __name__ == "__main__":
    main()
