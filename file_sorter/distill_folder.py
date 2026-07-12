#!/usr/bin/env python3
"""
Distill Folder - Turn .md/.txt files into "good-to-know" concise versions
using OpenAI, mirroring the source folder structure under <source>/concise/.

Pair with smart_archive.py:
    1. python smart_archive.py  ~/Downloads/iran Iran --move
    2. python distill_folder.py ~/Downloads/iran

After step 1 the raw files live in ~/Downloads/iran/<topic>/...
After step 2 distilled copies live in ~/Downloads/iran/concise/<topic>/...
so you can: `typoraed ~/Downloads/iran/concise/scorecards`.

Usage:
    python distill_folder.py ~/Downloads/iran
    python distill_folder.py ~/Downloads/iran --model gpt-4o-mini
    python distill_folder.py ~/Downloads/iran --dry-run
    python distill_folder.py ~/Downloads/iran --limit 3   # test first N files
    python distill_folder.py ~/Downloads/iran --overwrite
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: pip install openai", file=sys.stderr)
    sys.exit(1)


SYSTEM_PROMPT = """You distill a document into a "good-to-know" knowledge log.

KEEP:
- Core claims, arguments, and the evidence behind them
- Unique frameworks, doctrines, models, or definitions
- Specific facts, numbers, names, dates, actors
- Sharp quotes (with attribution if given)
- Actionable takeaways or decisions

DROP:
- Filler, transitions, chatty tone
- Redundant restatements
- Speculation without grounding
- Preamble, disclaimers, housekeeping

OUTPUT:
- Clean Markdown suitable for reading in Typora
- Start with a single `# Title` derived from the source
- 2-5 `## Section` headings grouping related points
- Bullet-heavy; short sentences; no fluff
- Target ~30-50% of source length when source is information-dense; shorter
  if the source is mostly fluff. Never pad to hit a length.
- If the source has essentially no useful content, output exactly:
  `# <Title>\\n\\n_No durable takeaways in source._`
"""

TRAILING_COPY_RE = re.compile(r"^(.*?) \(\d+\)$")


def safe_stem(name: str) -> str:
    stem = Path(name).stem
    m = TRAILING_COPY_RE.match(stem)
    return m.group(1) if m else stem


def distill(client: OpenAI, model: str, content: str, filename: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Source filename: {filename}\n\n---\n\n{content}"},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip() + "\n"


PREVENT_SUFFIX_RE = re.compile(r"\s*\(\d+\s*chars?\)\s*$", re.IGNORECASE)


def load_prevent_list(source: Path) -> set[Path]:
    """Read prevent_distill.txt from source folder. Returns a set of resolved Paths to skip.

    Lines can be copy-pasted directly from --list output, e.g.:
        /Users/stanleytan/Downloads/iran/misc/iran_score_card_prompt.md (487 chars)
    The trailing (N chars) is stripped automatically.
    Lines starting with # are comments. Blank lines are ignored.
    """
    prevent_file = source / "prevent_distill.txt"
    if not prevent_file.exists():
        return set()
    paths = set()
    for line in prevent_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = PREVENT_SUFFIX_RE.sub("", line).strip()
        if line:
            paths.add(Path(os.path.expanduser(line)).resolve())
    return paths


def print_file_listing(files: list[Path], header: str = ""):
    """Print full paths with character counts — copy paths into prevent_distill.txt to skip."""
    if header:
        print(header)
    for f in files:
        try:
            chars = len(f.read_text(errors="replace"))
        except OSError:
            chars = 0
        print(f"{f} ({chars} chars)")


def move_files(pairs: list[tuple[Path, Path]]):
    """Move each (src, dst) pair, creating parent dirs as needed."""
    for src, dst in pairs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def collect_files(source: Path, out_dir: Path) -> list[Path]:
    """Walk source for .md/.txt files, skipping the output directory."""
    results: list[Path] = []
    for f in source.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".md", ".txt"):
            continue
        if f.name.startswith("."):
            continue
        # Skip anything inside the output directory.
        try:
            f.relative_to(out_dir)
            continue
        except ValueError:
            pass
        results.append(f)
    return sorted(results)


def main():
    ap = argparse.ArgumentParser(
        description="Distill .md/.txt files into concise versions via OpenAI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("source", type=Path, help="Folder to walk (recursive)")
    ap.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
    ap.add_argument("--out", type=Path, default=None,
                    help="Output folder (default: <source>/concise)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show the file plan without calling the API")
    ap.add_argument("--limit", type=int, default=0,
                    help="Only process first N files (for cost testing)")
    ap.add_argument("--overwrite", action="store_true",
                    help="Overwrite existing distilled files")
    ap.add_argument("--list", action="store_true",
                    help="Print full paths + char counts of all files (no distilling). Copy paths into prevent_distill.txt to skip them.")
    args = ap.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_dir():
        print(f"Not a directory: {source}", file=sys.stderr)
        sys.exit(1)

    out_dir = (args.out or (source / "concise")).expanduser().resolve()

    # --list: just show full paths + char counts, nothing else.
    if args.list:
        all_files = collect_files(source, out_dir)
        print_file_listing(all_files, header=f"Files under {source}:\n")
        print(f"\n{len(all_files)} file(s). Copy paths into prevent_distill.txt to skip distillation.")
        return

    # Load prevent list and stash those files in a temp folder before distilling.
    prevent_paths = load_prevent_list(source)
    stash_dir = source / "_distill_skip"
    stashed: list[tuple[Path, Path]] = []  # (original_path, stash_path)

    if prevent_paths and not args.dry_run:
        for f in source.rglob("*"):
            if not f.is_file() or f.resolve() not in prevent_paths:
                continue
            try:
                f.relative_to(out_dir)
                continue  # skip files already in concise/
            except ValueError:
                pass
            stash_path = stash_dir / f.relative_to(source)
            stashed.append((f, stash_path))
        if stashed:
            print(f"Stashing {len(stashed)} protected file(s) from prevent_distill.txt...")
            for src, _ in stashed:
                print(f"  ~ {src}")
            move_files(stashed)
            print()

    files = collect_files(source, out_dir)
    if not files:
        print(f"No .md/.txt files to distill under {source}")
        # Restore stashed files before exiting.
        if stashed:
            move_files([(dst, src) for src, dst in stashed])
        return

    print(f"Source:  {source}")
    print(f"Out:     {out_dir}")
    print(f"Model:   {args.model}")
    print(f"Files:   {len(files)}")

    # Group by relative parent for the plan printout.
    by_parent: dict[str, list[Path]] = {}
    for f in files:
        rel_parent = str(f.parent.relative_to(source)) or "."
        by_parent.setdefault(rel_parent, []).append(f)

    for parent in sorted(by_parent):
        print(f"  {parent:20s} {len(by_parent[parent])}")

    if args.dry_run:
        print("\n--- DRY RUN ---")
        for parent in sorted(by_parent):
            print(f"\n{parent}/")
            for f in by_parent[parent]:
                print(f"  {f.name}")
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    out_dir.mkdir(parents=True, exist_ok=True)

    index: list[str] = ["# Concise Archive", "",
                        f"_Source: `{source}`_", ""]
    processed = 0
    errors: list[str] = []

    for parent in sorted(by_parent):
        index.append(f"## {parent}")
        index.append("")

        for f in by_parent[parent]:
            if args.limit and processed >= args.limit:
                break

            rel_parent = f.parent.relative_to(source)
            dest_dir = out_dir / rel_parent
            dest_dir.mkdir(parents=True, exist_ok=True)

            out_name = safe_stem(f.name) + ".md"
            out_path = dest_dir / out_name
            rel_out = out_path.relative_to(out_dir)

            if out_path.exists() and not args.overwrite:
                print(f"  skip (exists): {rel_out}")
                index.append(f"- [{safe_stem(f.name)}]({rel_out})")
                continue

            try:
                content = f.read_text(errors="replace")
            except OSError as e:
                errors.append(f"{f}: read failed: {e}")
                continue

            if not content.strip():
                print(f"  skip (empty):  {f.relative_to(source)}")
                continue

            print(f"  distilling:    {f.relative_to(source)}  ->  {rel_out}")
            try:
                out_path.write_text(distill(client, args.model, content, f.name))
                index.append(f"- [{safe_stem(f.name)}]({rel_out})")
                processed += 1
            except Exception as e:  # noqa: BLE001 - surface API errors, keep going
                errors.append(f"{f}: {e}")
                print(f"    error: {e}", file=sys.stderr)

        index.append("")
        if args.limit and processed >= args.limit:
            break

    (out_dir / "_index.md").write_text("\n".join(index))

    print(f"\nDone. Distilled {processed} file(s) into {out_dir}")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")

    # Print full listing of concise/ output files with char counts.
    concise_files = collect_files(out_dir, out_dir / "_none")
    if concise_files:
        print()
        print_file_listing(concise_files, header="Concise output:")

    # Restore stashed files back to their original locations.
    if stashed:
        print(f"\nRestoring {len(stashed)} protected file(s)...")
        move_files([(dst, src) for src, dst in stashed])
        try:
            stash_dir.rmdir()  # remove stash dir only if empty
        except OSError:
            pass
        print("  done — protected files back in place")


if __name__ == "__main__":
    main()
