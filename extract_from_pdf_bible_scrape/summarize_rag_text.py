#!/usr/bin/env python3
"""
Summarize/condense a text file in two passes:
  Pass 1: Regex — strips common web scraping artifacts (free, instant)
  Pass 2: Anthropic API — cleans remaining noise and condenses to target size

Usage:
    ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py galatians_combined.txt
    ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py galatians_combined.txt -o rag_summary_galatians.txt
    ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py my_notes.txt --target 80000

Requires:
    pip install anthropic
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

import anthropic


CHUNK_SIZE = 30000  # chars per chunk sent to API
MODEL = "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------------------
# Pass 1: Generic regex cleaning (works on any scraped web text)
# ---------------------------------------------------------------------------

# Exact single-line junk (case-insensitive match)
JUNK_LINES = {
    "contact", "who we are", "videos", "podcast", "support",
    "subscribe", "sharing is caring!", "share", "tweet", "pin",
    "leave a comment", "comment...", "post comment",
    "name (required)", "email (required)", "website",
    "one comment", "comments", "related posts", "recent posts",
    "newsletter", "follow us", "about us", "privacy policy",
    "terms of service", "cookie policy", "menu", "search",
    "sidebar", "footer", "header", "navigation",
}

# Line-level regex patterns (applied with re.MULTILINE, no DOTALL)
LINE_PATTERNS = [
    # Copyright footers
    r'©\s*Copyright.*',
    r'©\s*\d{4}.*',
    r'All Rights Reserved.*',
    # Cookie / privacy notices
    r'Do not sell my personal information',
    r'This (site|website) uses cookies.*',
    r'We use cookies.*',
    # Social share / ad lines
    r'Exclusive Member of Mediavine.*',
    r'Report An Ad\s*\|?',
    # Spaced-out promotional text (e.g. "S T U D Y  G A L A T I A N S")
    r'^[A-Z]\s[A-Z]\s[A-Z]\s[A-Z]\s[A-Z].*$',
    # "Save my name" checkbox text
    r'Save my name, email.*',
    # Dates standing alone (sidebar artifacts)
    r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}$',
    # Breadcrumb navigation
    r'Home\s*>>\s*.*',
    # Donation / support lines
    r'(Support|Donate)\s+(us|for)\s+as little as.*',
]

# Multi-line regex patterns (applied with re.DOTALL)
MULTILINE_PATTERNS = [
    # "We want to help you study..." promo blocks ending with SUPPORT/DONATE
    r'We want to help you study.*?SUPPORT',
    r'We want to help you.*?DONATE',
    # Comment form blocks
    r'Leave A Comment.*?POST\s*COMMENT',
]


def regex_clean(text: str) -> str:
    """Pass 1: Remove common web artifacts with generic regex patterns."""
    # Remove separator lines
    text = re.sub(r'^[=\-]{10,}$', '', text, flags=re.MULTILINE)

    # Apply line-level patterns
    for pattern in LINE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

    # Apply multi-line patterns
    for pattern in MULTILINE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

    # Line-by-line filtering
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()

        if not stripped:
            cleaned.append('')
            continue

        # Skip exact junk lines
        if stripped.lower() in JUNK_LINES:
            continue

        # Skip very short non-numeric lines (UI fragments)
        if len(stripped) <= 2 and not stripped[0].isdigit():
            continue

        cleaned.append(stripped)

    text = '\n'.join(cleaned)

    # Join lines broken mid-sentence by scraping (blank line between
    # continuation lines where next line starts lowercase)
    lines = text.split('\n')
    merged = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (line.strip()
                and i + 2 < len(lines)
                and lines[i + 1].strip() == ''
                and lines[i + 2].strip()
                and lines[i + 2].strip()[0].islower()):
            merged.append(line.strip() + ' ' + lines[i + 2].strip())
            i += 3
        else:
            merged.append(line)
            i += 1
    text = '\n'.join(merged)

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


# ---------------------------------------------------------------------------
# Pass 2: Anthropic API cleaning + condensing
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a text cleaner and condenser. You will receive a chunk of text \
that has already been partially cleaned by regex, but may still contain \
web scraping artifacts, navigation elements, ads, footers, cookie \
notices, comment sections, and other non-content noise.

Your job:
1. Remove ALL remaining web artifacts (nav bars, sidebars, ads, footers, \
comment sections, "Share/Tweet/Pin", cookie notices, subscription \
prompts, repeated page headers, user comments, etc.)
2. Remove excessive whitespace and blank lines.
3. Join lines that were broken mid-sentence by web scraping.
4. Preserve ALL actual content faithfully — do not rephrase, rewrite, \
or omit any substantive content.
5. Keep section headings, numbered points, outlines, teaching points, \
and applications.
6. Output clean, readable plain text.

IMPORTANT: Do NOT summarize or paraphrase the content. Keep all \
substantive text verbatim. Only remove noise and fix formatting."""


TARGET_PROMPT = """\

ADDITIONAL INSTRUCTION: The user wants the output condensed to fit a \
target size. After cleaning artifacts, also:
- Remove repetitive content that appears across multiple sections
- Condense discussion questions to just the key questions
- Remove promotional/meta content about the source material itself
- Keep all teaching points and applications in full
Aim to reduce the content by approximately {reduction_pct}%."""


def get_client() -> anthropic.Anthropic:
    """Create Anthropic client, checking for API key."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Usage: ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py <file>")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end >= len(text):
            chunks.append(text[start:])
            break

        # Find a paragraph break near the end
        search_start = max(end - 2000, start)
        break_pos = text.rfind('\n\n', search_start, end)

        if break_pos > start:
            end = break_pos
        else:
            break_pos = text.rfind('\n', search_start, end)
            if break_pos > start:
                end = break_pos

        chunks.append(text[start:end])
        start = end

    return chunks


def summarize_chunk(
    client: anthropic.Anthropic,
    model: str,
    chunk: str,
    chunk_num: int,
    total_chunks: int,
    extra_prompt: str = "",
) -> str:
    """Send a chunk to Claude for cleaning/condensing."""
    user_msg = (
        f"Clean and condense the following text "
        f"(chunk {chunk_num}/{total_chunks}):\n\n{chunk}"
    )

    response = client.messages.create(
        model=model,
        max_tokens=8192,
        system=SYSTEM_PROMPT + extra_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )

    return response.content[0].text


def main():
    parser = argparse.ArgumentParser(
        description="Two-pass text summarizer: regex clean then Anthropic API condense",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py galatians_combined.txt
  ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py galatians_combined.txt -o rag_summary_galatians.txt
  ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py my_notes.txt --target 80000
  ANTHROPIC_API_KEY=sk-... python summarize_rag_text.py book.txt --model claude-sonnet-4-5-20241022
        """
    )
    parser.add_argument("input_file", help="Input text file to summarize")
    parser.add_argument("-o", "--output", help="Output file (default: rag_summary_<input>)")
    parser.add_argument(
        "--target", type=int, default=150000,
        help="Target character count (default: 150000)"
    )
    parser.add_argument(
        "--model", default=MODEL,
        help=f"Anthropic model to use (default: {MODEL})"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=CHUNK_SIZE,
        help=f"Characters per API chunk (default: {CHUNK_SIZE})"
    )
    args = parser.parse_args()

    # Read input
    if not os.path.exists(args.input_file):
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)

    with open(args.input_file, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    original_len = len(text)
    print(f"Input: {args.input_file} ({original_len:,} chars)")
    print(f"Target: {args.target:,} chars")
    print(f"Model: {args.model}")
    print()

    # --- Pass 1: Regex ---
    print("Pass 1: Regex cleaning...")
    text = regex_clean(text)
    print(f"  After regex: {len(text):,} chars ({original_len - len(text):,} removed)")
    print()

    # --- Pass 2: Anthropic API ---
    print("Pass 2: Anthropic API cleaning + condensing...")

    # Calculate reduction target relative to regex-cleaned text
    extra_prompt = ""
    if len(text) > args.target:
        reduction_pct = int((1 - args.target / len(text)) * 100)
        extra_prompt = TARGET_PROMPT.format(reduction_pct=reduction_pct)
        print(f"  Reduction needed: ~{reduction_pct}%")

    chunks = split_into_chunks(text, args.chunk_size)
    print(f"  Split into {len(chunks)} chunks")
    print()

    client = get_client()
    results = []

    for i, chunk in enumerate(chunks, 1):
        print(
            f"  Chunk {i}/{len(chunks)} ({len(chunk):,} chars)...",
            end=" ", flush=True,
        )
        start_time = time.time()

        result = summarize_chunk(
            client=client,
            model=args.model,
            chunk=chunk,
            chunk_num=i,
            total_chunks=len(chunks),
            extra_prompt=extra_prompt,
        )

        elapsed = time.time() - start_time
        print(f"-> {len(result):,} chars ({elapsed:.1f}s)")
        results.append(result)

    # Combine results
    output_text = "\n\n".join(results)

    # Determine output filename
    output_path = args.output
    if not output_path:
        stem = Path(args.input_file).stem
        output_path = f"rag_summary_{stem}.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    reduction = (1 - len(output_text) / original_len) * 100
    print()
    print(f"Saved to: {output_path}")
    print(f"Result: {original_len:,} -> {len(output_text):,} chars ({reduction:.1f}% smaller)")


if __name__ == "__main__":
    main()
