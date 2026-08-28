#!/usr/bin/env python3
"""
rag_to_topics.py — Extract a RAG knowledge base into organized topic .md files.

Usage:
    python rag_to_topics.py --rag rag_lindsay --output ./lindsay_topics/
    python rag_to_topics.py --rag /full/path/to/rag_folder --output ./topics/
    python rag_to_topics.py --rag rag_lindsay --output ./topics/ --topics "mental state" "forensics" "legal defense"

Steps:
    1. Ask the model to identify main topics from the knowledge base
    2. For each topic, query the RAG to retrieve relevant chunks
    3. Write each topic to a numbered .md file
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


APPS_DIR = os.path.dirname(os.path.abspath(__file__))

# ── RAG loader ────────────────────────────────────────────────────────────────

def load_rag(rag_folder: str):
    rag_path = rag_folder if os.path.isabs(rag_folder) else os.path.join(APPS_DIR, rag_folder)
    if not os.path.exists(rag_path):
        # Try streamlit_apps directory
        alt = os.path.join(os.path.dirname(APPS_DIR), "github", "streamlit_apps", rag_folder)
        if os.path.exists(alt):
            rag_path = alt
        else:
            print(f"Error: RAG folder not found: {rag_folder}")
            sys.exit(1)

    if not os.path.exists(os.path.join(rag_path, "rag_config.toml")):
        print(f"Error: {rag_path} is not a valid RAG folder (missing rag_config.toml)")
        sys.exit(1)

    if rag_path not in sys.path:
        sys.path.insert(0, rag_path)

    for mod in ["src.retrieval", "src.constants", "src"]:
        sys.modules.pop(mod, None)

    from src.retrieval import get_knowledge_base, get_context
    from src.constants import get_rag_config
    return get_knowledge_base, get_context, get_rag_config, rag_path


def retrieve(gc, gkb, grc, query: str) -> str:
    config = grc()
    k_base = gkb()
    return gc(
        k_base=k_base,
        query_text=query,
        n_retrieve=config["retriever"]["n_retrieve"],
        n_titles=config["retriever"]["n_titles"],
        enrich_first=config["retriever"]["enrich_first"],
    )


# ── OpenAI helpers ────────────────────────────────────────────────────────────

def ask(client, model: str, system: str, user: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


def discover_topics(client, model: str, gc, gkb, grc, rag_name: str) -> list[str]:
    """Ask the model to identify the main topics in the knowledge base."""
    print("Discovering topics…")

    # Sample the RAG with a broad query to get an overview
    overview_context = retrieve(gc, gkb, grc, "main topics overview summary key themes")

    system = (
        "You are analyzing a knowledge base to identify its main topics. "
        "Return ONLY a JSON array of topic strings, nothing else. "
        "Each topic should be a short descriptive phrase (3-6 words). "
        "Aim for 6-12 distinct, non-overlapping topics. "
        'Example: ["Mental state and psychiatry", "Forensic evidence", "Legal defense strategy"]'
    )
    user = (
        f"Knowledge base: {rag_name}\n\n"
        f"Sample content:\n{overview_context}\n\n"
        "List the main topics covered in this knowledge base as a JSON array."
    )

    raw = ask(client, model, system, user)

    # Extract JSON array from response
    match = re.search(r'\[.*?\]', raw, re.DOTALL)
    if not match:
        print(f"Warning: could not parse topics from response:\n{raw}")
        sys.exit(1)

    topics = json.loads(match.group())
    print(f"  Found {len(topics)} topics:")
    for i, t in enumerate(topics, 1):
        print(f"    {i}. {t}")
    return topics


def write_topic_file(
    client, model: str,
    gc, gkb, grc,
    topic: str,
    index: int,
    output_dir: str,
    rag_name: str,
) -> str:
    """Retrieve content for a topic and write it to a .md file."""
    print(f"  [{index}] {topic}…", end="", flush=True)

    context = retrieve(gc, gkb, grc, topic)

    system = (
        "You are organizing research notes into a structured markdown document. "
        "Using the provided context, write a clear, well-organized summary of the topic. "
        "Use markdown headers (##, ###) to structure the content. "
        "Preserve specific facts, quotes, dates, and details from the context. "
        "Do not add information not present in the context."
    )
    user = (
        f"Topic: {topic}\n"
        f"Knowledge base: {rag_name}\n\n"
        f"[Retrieved Context]\n{context}\n[End Context]\n\n"
        f"Write a structured markdown summary of '{topic}' based on the context above."
    )

    content = ask(client, model, system, user)

    # Build filename: "03-mental-state-and-psychiatry.md"
    slug = re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')
    filename = f"{index:02d}-{slug}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {topic}\n\n")
        f.write(f"*Source: {rag_name}*\n\n")
        f.write("---\n\n")
        f.write(content)
        f.write("\n")

    print(f" → {filename} ({len(content):,} chars)")
    return filepath


def write_index(topics: list[str], files: list[str], output_dir: str, rag_name: str):
    """Write an index.md listing all topics."""
    filepath = os.path.join(output_dir, "index.md")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {rag_name} — Topic Index\n\n")
        for i, (topic, fpath) in enumerate(zip(topics, files), 1):
            fname = os.path.basename(fpath)
            f.write(f"{i}. [{topic}]({fname})\n")
    print(f"  → index.md")
    return filepath


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract a RAG knowledge base into organized topic .md files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rag_to_topics.py --rag rag_lindsay --output ./lindsay_topics/
  python rag_to_topics.py --rag /full/path/to/rag_folder --output ./topics/
  python rag_to_topics.py --rag rag_lindsay --output ./topics/ --topics "mental state" "forensics"
        """
    )
    parser.add_argument("--rag", required=True, help="RAG folder name or full path")
    parser.add_argument("--output", help="Output directory for .md files (default: <rag_name>_topics)")
    parser.add_argument(
        "--topics", nargs="+",
        help="Explicit list of topics (skips auto-discovery)"
    )
    parser.add_argument(
        "--model", default="gpt-4o-mini",
        choices=["gpt-4o-mini", "gpt-4.1-mini", "gpt-4.1"],
        help="OpenAI model to use (default: gpt-4o-mini — recommended for cost)"
    )
    args = parser.parse_args()

    # API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = input("OpenAI API key: ").strip()
        if not api_key:
            print("Error: API key required")
            sys.exit(1)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except ImportError:
        print("Error: openai package not installed. Run: pip install openai")
        sys.exit(1)

    # Load RAG
    print(f"\nLoading RAG: {args.rag}")
    gkb, gc, grc, rag_path = load_rag(args.rag)
    rag_name = Path(rag_path).name

    # Output directory
    output = args.output or f"{rag_name}_topics"
    os.makedirs(output, exist_ok=True)
    args.output = output
    print(f"Output: {output}")

    print("=" * 60)

    # Discover or use provided topics
    if args.topics:
        topics = args.topics
        print(f"Using {len(topics)} provided topics:")
        for i, t in enumerate(topics, 1):
            print(f"  {i}. {t}")
    else:
        print("\nEnter topics one per line (leave blank and press Enter to auto-discover):")
        manual_topics = []
        while True:
            try:
                line = input(f"  Topic {len(manual_topics) + 1}: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                break
            manual_topics.append(line)

        if manual_topics:
            topics = manual_topics
            print(f"\nUsing {len(topics)} entered topics.")
        else:
            print("\nNo topics entered — auto-discovering…")
            topics = discover_topics(client, args.model, gc, gkb, grc, rag_name)

    print(f"\nExtracting {len(topics)} topic files…")
    written_files = []
    for i, topic in enumerate(topics, 1):
        fpath = write_topic_file(client, args.model, gc, gkb, grc, topic, i, args.output, rag_name)
        written_files.append(fpath)

    print("\nWriting index…")
    write_index(topics, written_files, args.output, rag_name)

    print()
    print("=" * 60)
    print(f"  Done! {len(written_files)} topic files + index.md")
    print(f"  Output: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
