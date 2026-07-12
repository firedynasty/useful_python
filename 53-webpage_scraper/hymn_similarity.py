"""
Hymn Similarity Finder
Finds hymns similar to a given hymn (by number or first-line text search).

If hymn_similarities.json exists (built by build_hymn_index.py), uses AI embeddings.
Otherwise falls back to topic-overlap scoring.

Usage:
  python hymn_similarity.py 370
  python hymn_similarity.py "I love the Lord"
  python hymn_similarity.py          # interactive mode
"""

import csv
import json
import os
import argparse
from collections import defaultdict

INDEX_FILE = "hymn_similarities.json"


# ── Data loading ─────────────────────────────────────────────────────────────

def load_hymns(csv_path):
    hymn_topics = defaultdict(set)
    hymn_title = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            num = row["Hymn #"].strip()
            topic = row["Topic"].strip()
            subtopic = row["Sub-Topic"].strip()
            title = row["First Line"].strip()
            hymn_topics[num].add((topic, subtopic))
            if num not in hymn_title:
                hymn_title[num] = title
    return hymn_topics, hymn_title


def load_index(index_path):
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            return json.load(f)
    return None


# ── Hymn resolution (number or text search) ───────────────────────────────────

def search_by_text(query, hymn_title):
    q = query.lower()
    return [(num, title) for num, title in hymn_title.items() if q in title.lower()]


def resolve_hymn(query, hymn_title):
    candidate = f"#{query}" if not query.startswith("#") else query
    if candidate in hymn_title:
        return candidate

    matches = search_by_text(query, hymn_title)
    if not matches:
        print(f'No hymns found matching "{query}".')
        return None
    if len(matches) == 1:
        num, title = matches[0]
        print(f'Found: {num} "{title}"')
        return num
    print(f'\nMultiple hymns match "{query}":')
    for i, (num, title) in enumerate(matches[:20], 1):
        print(f"  {i}. {num}  {title}")
    choice = input("Enter number to select (or press Enter to cancel): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(matches):
        return matches[int(choice) - 1][0]
    return None


# ── Display ───────────────────────────────────────────────────────────────────

def print_header(key, title, topics):
    print(f'\nHymn {key}: "{title}"')
    print(f"Topics ({len(topics)}):")
    for t in sorted(topics):
        print(f"  - {t}")


def print_results(results, top_n, score_label):
    print(f"\nTop {top_n} similar hymns ({score_label}):\n")
    print(f"{'Rank':<5} {'Hymn':<10} {'Score':>6}  {'Shared Topics':<35}  First Line")
    print("-" * 95)
    for rank, (hymn, title, score, shared) in enumerate(results[:top_n], 1):
        shared_str = ", ".join(shared) if shared else "—"
        print(f"{rank:<5} {hymn:<10} {score:>5.0%}  {shared_str:<35}  {title}")


# ── AI-index search ───────────────────────────────────────────────────────────

def find_similar_ai(key, index, top_n):
    entry = index.get(key)
    if not entry:
        print(f"Hymn {key} not found in index.")
        return

    print_header(key, entry["title"], entry["topics"])

    results = [
        (s["hymn"], s["title"], s["score"], s["shared_topics"])
        for s in entry["similar"]
    ]
    print_results(results, top_n, "AI semantic similarity")


# ── Fallback topic-overlap search ─────────────────────────────────────────────

def jaccard(set_a, set_b):
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def find_similar_topics(key, hymn_topics, hymn_title, top_n):
    target_topics = hymn_topics[key]
    target_title = hymn_title[key]

    print_header(key, target_title, [t + (f"/{s}" if s else "") for t, s in sorted(target_topics)])

    scores = []
    for num, topics in hymn_topics.items():
        if num == key:
            continue
        shared = target_topics & topics
        if not shared:
            continue
        score = jaccard(target_topics, topics)
        shared_labels = [t + (f"/{s}" if s else "") for t, s in sorted(shared)]
        scores.append((num, hymn_title[num], score, shared_labels))

    scores.sort(key=lambda x: -x[2])
    print_results(scores, top_n, "topic overlap — run build_hymn_index.py for AI scoring")


# ── Entry point ───────────────────────────────────────────────────────────────

def find_similar(query, hymn_topics, hymn_title, index, top_n):
    key = resolve_hymn(query, hymn_title)
    if key is None:
        return
    if key not in hymn_title:
        print(f"Hymn {key} not found.")
        return

    if index and key in index:
        find_similar_ai(key, index, top_n)
    else:
        find_similar_topics(key, hymn_topics, hymn_title, top_n)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("hymn", nargs="?", help="Hymn number or words from first line")
    parser.add_argument("--top", type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument("--csv", default="hymnary_h1955_merged.csv")
    parser.add_argument("--index", default=INDEX_FILE, help="Path to JSON index file")
    args = parser.parse_args()

    hymn_topics, hymn_title = load_hymns(args.csv)
    index = load_index(args.index)

    if index:
        print(f"Using AI index ({args.index}) — {len(index)} hymns.")
    else:
        print(f"No AI index found. Using topic-overlap scoring.")
        print(f"  Run: python build_hymn_index.py   to build the AI index.")

    if args.hymn:
        find_similar(args.hymn, hymn_topics, hymn_title, index, args.top)
    else:
        print("\nHymn Similarity Finder — enter a hymn number or words from the first line.")
        while True:
            query = input("\nSearch (or 'q' to quit): ").strip()
            if query.lower() == "q":
                break
            if not query:
                continue
            top_n = input("How many results? [10]: ").strip()
            top_n = int(top_n) if top_n.isdigit() else 10
            find_similar(query, hymn_topics, hymn_title, index, top_n)


if __name__ == "__main__":
    main()
