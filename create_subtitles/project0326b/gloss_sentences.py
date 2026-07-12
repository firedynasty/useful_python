#!/usr/bin/env python3
"""
Gloss Chinese sentences from english_chinese.txt using OpenAI 4o-mini.
Produces word-level breakdowns with pinyin and English glosses.

Usage:
  python gloss_sentences.py -i english_chinese.txt -o glossed.tsv
  python gloss_sentences.py -i english_chinese.txt -o glossed.tsv --mode words
  python gloss_sentences.py -i english_chinese.txt -o glossed.tsv --mode both


so, adjust:
python gloss_sentences.py -i english_chinese.txt -o glossed.tsv --mode words --batch-size 20  
"""

import argparse
import json
import os
import re
import time
from openai import OpenAI


def parse_input(filepath):
    """Parse english_chinese.txt → list of (chinese, english) tuples."""
    pairs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Format: "0:00 中文内容 English content"
            # Remove leading timestamp
            match = re.match(r"^\d+:\d{2}\s+(.+)", line)
            if not match:
                continue
            rest = match.group(1)
            # Split at boundary between Chinese and Latin characters
            # Find where Chinese text ends and English begins
            split = find_split(rest)
            if split:
                chinese, english = split
                pairs.append((chinese.strip(), english.strip()))
            else:
                pairs.append((rest.strip(), ""))
    return pairs


def find_split(text):
    """Split text into Chinese portion and English portion.

    Looks for the transition point where we go from CJK characters
    to a run of Latin/ASCII that looks like English text.
    """
    # Strategy: find the last CJK character (or CJK punctuation),
    # everything before and including it is Chinese,
    # everything after is English.
    last_cjk = -1
    for i, ch in enumerate(text):
        if is_cjk(ch):
            last_cjk = i
    if last_cjk == -1:
        return None
    chinese = text[:last_cjk + 1].strip()
    english = text[last_cjk + 1:].strip()
    return (chinese, english)


def is_cjk(ch):
    """Check if character is CJK or CJK punctuation."""
    cp = ord(ch)
    return (
        (0x4E00 <= cp <= 0x9FFF) or      # CJK Unified
        (0x3400 <= cp <= 0x4DBF) or      # CJK Extension A
        (0x3000 <= cp <= 0x303F) or      # CJK Symbols and Punctuation
        (0xFF00 <= cp <= 0xFFEF) or      # Fullwidth forms
        (0xFE30 <= cp <= 0xFE4F) or      # CJK Compatibility Forms
        ch in '，。！？、；：""''（）【】《》'  # Common Chinese punctuation
    )


def deduplicate(pairs):
    """Keep only first occurrence of each unique Chinese sentence."""
    seen = set()
    unique = []
    for chinese, english in pairs:
        if chinese not in seen:
            seen.add(chinese)
            unique.append((chinese, english))
    return unique


def gloss_batch(client, sentences, batch_size=10):
    """Call 4o-mini to get word-level glosses for a batch of sentences.

    Returns list of lists, each inner list contains dicts with:
      {chinese, pinyin, english_gloss}
    """
    all_glosses = []

    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i + batch_size]
        numbered = "\n".join(f"{j+1}. {s}" for j, s in enumerate(batch))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Mandarin linguist. For each numbered Chinese sentence, "
                        "return a JSON object with the sentence number as key and an array of word objects as value. "
                        "Each word object has: \"chinese\" (the word/token), \"pinyin\" (with tone marks), "
                        "\"english_gloss\" (brief English meaning). "
                        "Break sentences into natural vocabulary units (words, not individual characters). "
                        "Return ONLY valid JSON, no markdown fences."
                    )
                },
                {"role": "user", "content": numbered}
            ],
            temperature=0.1
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  Warning: Failed to parse JSON for batch {i//batch_size + 1}, retrying...")
            # Retry once
            time.sleep(1)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Mandarin linguist. For each numbered Chinese sentence, "
                            "return a JSON object with the sentence number as key and an array of word objects as value. "
                            "Each word object has: \"chinese\", \"pinyin\" (with tone marks), \"english_gloss\". "
                            "Return ONLY valid JSON, no markdown."
                        )
                    },
                    {"role": "user", "content": numbered}
                ],
                temperature=0
            )
            raw = response.choices[0].message.content.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)

        for j in range(len(batch)):
            key = str(j + 1)
            if key in parsed:
                all_glosses.append(parsed[key])
            else:
                all_glosses.append([])

        done = min(i + batch_size, len(sentences))
        print(f"  Glossed {done}/{len(sentences)} sentences")
        if done < len(sentences):
            time.sleep(0.3)

    return all_glosses


def format_sentences(pairs, glosses):
    """Mode A: one row per sentence with full pinyin."""
    rows = []
    for idx, ((chinese, english), words) in enumerate(zip(pairs, glosses), 1):
        pinyin = " ".join(w.get("pinyin", "") for w in words)
        rows.append(f"{idx}\t{chinese}\t{pinyin}\t{english}")
    return rows


def format_words(glosses):
    """Mode B: deduplicated word cards across all sentences."""
    seen = set()
    rows = []
    idx = 1
    for words in glosses:
        for w in words:
            ch = w.get("chinese", "")
            if ch and ch not in seen:
                seen.add(ch)
                rows.append(f"{idx}\t{ch}\t{w.get('pinyin', '')}\t{w.get('english_gloss', '')}")
                idx += 1
    return rows


def main():
    parser = argparse.ArgumentParser(description="Gloss Chinese sentences with pinyin and English")
    parser.add_argument("-i", "--input", required=True, help="Input english_chinese.txt file")
    parser.add_argument("-o", "--output", default=None, help="Output file (default: stdout)")
    parser.add_argument("--mode", choices=["sentences", "words", "both"], default="both",
                        help="Output mode (default: both)")
    parser.add_argument("--batch-size", type=int, default=10, help="Sentences per API call (default: 10)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set")
        return

    # Step 1: Parse
    pairs = parse_input(args.input)
    print(f"Parsed {len(pairs)} lines from {args.input}")

    # Step 2: Deduplicate
    pairs = deduplicate(pairs)
    print(f"After dedup: {len(pairs)} unique sentences")

    # Step 3: Gloss via API
    client = OpenAI(api_key=api_key)
    sentences = [ch for ch, _ in pairs]
    print("Calling 4o-mini for word-level glosses...")
    glosses = gloss_batch(client, sentences, batch_size=args.batch_size)

    # Step 4 & 5: Format output
    header = "#\tChinese\tPinyin\tEnglish"
    output_lines = []

    if args.mode in ("sentences", "both"):
        output_lines.append("=== Sentence Cards ===")
        output_lines.append(header)
        output_lines.extend(format_sentences(pairs, glosses))

    if args.mode == "both":
        output_lines.append("")

    if args.mode in ("words", "both"):
        output_lines.append("=== Word Cards ===")
        output_lines.append(header)
        output_lines.extend(format_words(glosses))

    result = "\n".join(output_lines)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"Written to {args.output}")
    else:
        print()
        print(result)


if __name__ == "__main__":
    main()
