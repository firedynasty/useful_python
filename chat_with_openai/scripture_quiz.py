#!/usr/bin/env python3
"""
Scripture memorization quiz.

Usage:
  python scripture_quiz.py              # no AI, one verse at a time
  python scripture_quiz.py --bulk       # uses OpenAI to parse bulk recitation

Requires for --bulk mode: pip install openai
Set: export OPENAI_API_KEY=sk-...
"""

import re
import subprocess
import sys
import os
import json
import argparse


def get_clipboard():
    """Get clipboard contents (macOS)."""
    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
    return result.stdout.strip()


def parse_verses(text):
    """Parse numbered verses from text. Handles any numbering like 1,2,3 or 6,7,8,9."""
    # Try format A: number on its own line
    parts = re.split(r'(?m)^(\d+)\s*$', text.strip())
    verses = {}
    if len(parts) > 2:
        i = 1
        while i < len(parts) - 1:
            num = int(parts[i])
            verse_text = parts[i + 1].strip()
            if verse_text:
                verses[num] = verse_text
            i += 2
        if verses:
            return verses

    # Format B: number at start of line, e.g. "1 My son..." or "1. My son..." or "5Trust..."
    # Also handles biblegateway format where verse 1 has no number
    current_num = None
    current_lines = []
    first_line = True
    for line in text.strip().split('\n'):
        trimmed = line.strip()
        if not trimmed:
            continue
        match = re.match(r'^(\d+)[.\s]?\s*(.*)', trimmed)
        if match:
            if current_num is not None and current_lines:
                verses[current_num] = ' '.join(current_lines).strip()
            current_num = int(match.group(1))
            current_lines = [match.group(2)] if match.group(2) else []
            first_line = False
        elif first_line:
            current_num = 1
            current_lines = [trimmed]
            first_line = False
        elif current_num is not None:
            current_lines.append(trimmed)
    if current_num is not None and current_lines:
        verses[current_num] = ' '.join(current_lines).strip()
    return verses


def normalize(text):
    """Normalize text for comparison - lowercase, strip punctuation."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()


def grade(original, attempt):
    """Grade attempt against original using longest common subsequence."""
    orig_words = normalize(original)
    attempt_words = normalize(attempt)

    if not orig_words:
        return 100.0, []

    m, n = len(orig_words), len(attempt_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if orig_words[i - 1] == attempt_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    matched = dp[m][n]
    pct = (matched / m) * 100

    missed = []
    i, j = m, n
    matched_indices = set()
    while i > 0 and j > 0:
        if orig_words[i - 1] == attempt_words[j - 1]:
            matched_indices.add(i - 1)
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    for idx in range(m):
        if idx not in matched_indices:
            missed.append(orig_words[idx])

    return pct, missed


def speak_verse(text):
    """Read verse aloud using macOS say command."""
    subprocess.Popen(['say', text])


def split_bulk_with_openai(raw_text, verse_nums):
    """Use OpenAI to split a bulk recitation into individual verses."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("export OPENAI_API_KEY=sk-... (needed for --bulk mode)")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    prompt = f"""I recited multiple scripture verses in one go. The verse numbers I was reciting are: {verse_nums}

Here is my raw recitation:
\"\"\"{raw_text}\"\"\"

Split this into the individual verses based on the verse numbers I said. Return ONLY valid JSON like:
{{"1": "text of verse 1", "2": "text of verse 2"}}

Use the verse numbers as keys. If a verse is missing or I skipped it, omit it from the JSON."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    reply = resp.choices[0].message.content.strip()
    # Extract JSON from response
    json_match = re.search(r'\{[^{}]*\}', reply, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return json.loads(reply)


def multi_line_input(prompt_msg):
    """Read multiple lines until empty line is entered."""
    print(prompt_msg)
    print("(press Enter twice when done)")
    lines = []
    empty_count = 0
    while True:
        line = input()
        if line == '':
            empty_count += 1
            if empty_count >= 1 and lines:
                break
            lines.append('')
        else:
            empty_count = 0
            lines.append(line)
    return '\n'.join(lines).strip()


def print_grade(pct, missed, verse_text=None):
    """Print grade feedback."""
    if pct == 100:
        print(f"  {pct:.0f}% - Perfect!")
    elif pct >= 80:
        print(f"  {pct:.0f}% - Great!")
    elif pct >= 60:
        print(f"  {pct:.0f}% - Good effort")
    else:
        print(f"  {pct:.0f}% - Keep practicing")
    if missed and verse_text:
        print(f"  Actual: {verse_text}")


def print_results(results, verses):
    """Print final summary."""
    print("\n" + "=" * 40)
    print("RESULTS")
    print("=" * 40)
    total_pct = 0
    for num, pct, missed in results:
        status = "PERFECT" if pct == 100 else f"{pct:.0f}%"
        print(f"  Verse {num}: {status}")
        total_pct += pct

    avg = total_pct / len(results) if results else 0
    print(f"\n  Overall: {avg:.0f}%")

    show_answers = [r for r in results if r[1] < 100]
    if show_answers:
        print(f"\n{'=' * 40}")
        print("REVIEW (verses below 100%)")
        print("=" * 40)
        for num, pct, _ in show_answers:
            print(f"\n  Verse {num} ({pct:.0f}%):")
            print(f"  {verses[num]}")


def main():
    parser = argparse.ArgumentParser(description="Scripture memorization quiz")
    parser.add_argument("--bulk", action="store_true",
                        help="Recite all verses at once (uses OpenAI to split)")
    args = parser.parse_args()

    print("=== Scripture Memorization Quiz ===\n")

    # Step 1: Get scripture
    use_clip = input("Use clipboard for scripture? (y/n): ").strip().lower()
    if use_clip == 'y':
        text = get_clipboard()
        if not text:
            print("Clipboard is empty.")
            sys.exit(1)
        print(f"\nLoaded from clipboard ({len(text)} chars)")
    else:
        text = multi_line_input("\nPaste your scripture below:")

    # Step 2: Parse verses
    verses = parse_verses(text)
    if not verses:
        print("No numbered verses found. Make sure each verse number is on its own line.")
        sys.exit(1)

    verse_nums = sorted(verses.keys())
    print(f"\nFound {len(verses)} verses: {', '.join(str(n) for n in verse_nums)}")
    print("-" * 40)

    if args.bulk:
        # ── BULK MODE: recite all at once, OpenAI splits ──
        print("\nRecite all verses in one go.")
        print("Say the verse number before each verse (e.g. '1 blessed is the man 2 but his delight...')")
        print("Paste your recitation below:\n")
        raw = input(">> ").strip()

        if not raw:
            print("Nothing entered.")
            return

        print("\n  Sending to OpenAI to split by verse...")
        try:
            split = split_bulk_with_openai(raw, verse_nums)
        except Exception as e:
            print(f"  Error: {e}")
            return

        results = []
        for num in verse_nums:
            key = str(num)
            if key in split:
                pct, missed = grade(verses[num], split[key])
                print(f"\n--- Verse {num} ---")
                print(f"  You said: {split[key]}")
                print_grade(pct, missed, verses[num])
                results.append((num, pct, missed))
            else:
                print(f"\n--- Verse {num} ---")
                print("  Skipped")
                results.append((num, 0.0, []))

        print_results(results, verses)

    else:
        # ── VERSE-BY-VERSE MODE: no AI needed ──
        # Quiz - free recitation, matches against all verses
        results = []
        remaining = set(verse_nums)
        print(f"\nRecite any verse — I'll figure out which one.")
        print(f"Type 'done' when finished.\n")

        while remaining:
            attempt = input("Recite: ").strip()
            if not attempt:
                continue
            if attempt.lower() == "done":
                break

            # Check if they started with a verse number
            num_match = re.match(r'^(\d+)[.\s]\s*(.*)', attempt)
            if num_match:
                stated_num = int(num_match.group(1))
                attempt_text = num_match.group(2)
                if stated_num in verses:
                    best_num = stated_num
                    best_pct, best_missed = grade(verses[stated_num], attempt_text)
                else:
                    print(f"  Verse {stated_num} not in loaded verses.")
                    continue
            else:
                # Score against all remaining verses, pick best match
                best_num = None
                best_pct = 0
                best_missed = []
                attempt_text = attempt
                for num in remaining:
                    pct, missed = grade(verses[num], attempt)
                    if pct > best_pct:
                        best_num = num
                        best_pct = pct
                        best_missed = missed

                if best_num is None or best_pct < 20:
                    print("  Couldn't match that to any verse. Try again.")
                    continue

            print(f"  → Verse {best_num}")
            print_grade(best_pct, best_missed, verses[best_num])
            results.append((best_num, best_pct, best_missed))
            remaining.discard(best_num)
            if remaining:
                print(f"  Remaining: {', '.join(str(n) for n in sorted(remaining))}")

        # Mark skipped verses
        for num in sorted(remaining):
            results.append((num, 0.0, []))

        results.sort(key=lambda r: r[0])
        print_results(results, verses)


if __name__ == '__main__':
    main()
