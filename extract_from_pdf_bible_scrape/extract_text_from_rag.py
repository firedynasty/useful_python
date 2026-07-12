#!/usr/bin/env python3
"""
Extract text from a RAG folder back into a .txt file.

Usage:
    python extract_text_from_rag.py rag_galatians
    python extract_text_from_rag.py rag_galatians -o galatians_restored.txt
    python extract_text_from_rag.py rag_don_quixote --list-sections

This script:
1. Reads the rag_config.toml to find the LanceDB table and overlap setting
2. Loads all chunks from LanceDB ordered by section_num and rank_abs
3. Reassembles chunks by removing overlapping text
4. Outputs the reconstructed text to a .txt file
"""

import argparse
import os
import sys
import tomllib

import lancedb
import pandas as pd


def load_config(rag_dir: str) -> dict:
    """Load rag_config.toml from the RAG folder."""
    config_path = os.path.join(rag_dir, "rag_config.toml")
    if not os.path.exists(config_path):
        print(f"Error: Config not found: {config_path}")
        sys.exit(1)

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def load_chunks(rag_dir: str, config: dict) -> pd.DataFrame:
    """Load all chunks from LanceDB, ordered by section_num and rank_abs."""
    db_uri = os.path.join(rag_dir, config["knowledge_base"]["uri"])
    table_name = config["knowledge_base"]["table_name"]

    if not os.path.exists(db_uri):
        print(f"Error: Database not found: {db_uri}")
        sys.exit(1)

    db = lancedb.connect(db_uri)

    try:
        table = db.open_table(table_name)
    except Exception as e:
        print(f"Error: Could not open table '{table_name}': {e}")
        available = db.table_names()
        if available:
            print(f"Available tables: {', '.join(available)}")
        sys.exit(1)

    df = table.to_pandas()
    cols = ["text", "section", "section_num", "rank_abs", "n_docs"]
    df = df[cols].sort_values(["section_num", "rank_abs"]).reset_index(drop=True)

    return df


def reassemble_text(df: pd.DataFrame, overlap: int) -> str:
    """Reassemble the original text from ordered chunks."""
    output_lines = []
    current_section = None

    for _, row in df.iterrows():
        section = row["section"]
        rank = row["rank_abs"]
        text = row["text"]

        if section != current_section:
            # New section — add section header and full text
            if current_section is not None:
                output_lines.append("")  # blank line between sections
            output_lines.append(section)
            output_lines.append("")
            output_lines.append(text)
            current_section = section
        else:
            # Continuation chunk — strip the overlap
            if rank > 0 and overlap > 0 and len(text) > overlap:
                output_lines.append(text[overlap:])
            else:
                output_lines.append(text)

    return "\n".join(output_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from a RAG folder back into a .txt file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_text_from_rag.py rag_galatians
  python extract_text_from_rag.py rag_galatians -o galatians_restored.txt
  python extract_text_from_rag.py rag_don_quixote --list-sections
        """
    )
    parser.add_argument(
        "rag_dir",
        help="Path to the RAG folder (e.g., rag_galatians)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output .txt file path (default: <table_name>_restored.txt)"
    )
    parser.add_argument(
        "--list-sections",
        action="store_true",
        help="Only list sections and chunk counts, don't extract"
    )
    args = parser.parse_args()

    # Validate RAG directory
    if not os.path.isdir(args.rag_dir):
        print(f"Error: Not a directory: {args.rag_dir}")
        sys.exit(1)

    # Load config
    config = load_config(args.rag_dir)
    table_name = config["knowledge_base"]["table_name"]
    overlap = config["embeddings"].get("overlap", 150)

    print(f"RAG folder: {args.rag_dir}")
    print(f"Table: {table_name}")
    print(f"Overlap: {overlap} chars")
    print()

    # Load chunks
    print("Loading chunks from LanceDB...")
    df = load_chunks(args.rag_dir, config)
    print(f"  Loaded {len(df)} chunks")

    # Show section info
    section_info = (
        df.groupby(["section_num", "section"])
        .agg(chunks=("text", "count"), chars=("text", lambda x: sum(len(t) for t in x)))
        .reset_index()
        .sort_values("section_num")
    )

    print(f"\n  {len(section_info)} sections:")
    for _, row in section_info.iterrows():
        print(f"    {row['section'][:60]} — {row['chunks']} chunks, {row['chars']:,} chars")

    if args.list_sections:
        return

    # Reassemble text
    print("\nReassembling text...")
    text = reassemble_text(df, overlap)
    print(f"  Reconstructed {len(text):,} characters")

    # Write output
    output_path = args.output or f"{table_name}_restored.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()
