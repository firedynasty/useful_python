#!/usr/bin/env python3
"""
Smart Archive - Move files based on keywords defined in config.

Usage:
    python smart_archive.py <source> <subject>
    python smart_archive.py ~/Desktop JobSearch
    python smart_archive.py ~/Desktop JobSearch --move

Reads routes from archive_config.yaml
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

# Matches Chrome-style duplicate names like "foo (1).md", "bar (2).txt".
DUP_RE = re.compile(r"^(.*?) \((\d+)\)(\.[^.]+)$")

try:
    import yaml
except ImportError:
    print("Error: pip install pyyaml")
    sys.exit(1)


def load_config(config_path: Path) -> dict:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def expand_path(path_str: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(path_str)))


def match_subfolder(filename: str, routes: dict) -> tuple[str, str]:
    """
    Match filename to subfolder using routes from config.

    A route with an empty keyword list is treated as the fallback subfolder
    for unmatched files. If no explicit fallback is declared, defaults to
    "general".

    Returns: (subfolder, matched_keyword)
    """
    name_lower = filename.lower()
    ext = Path(filename).suffix.lower()

    fallback = "general"
    for subfolder, keywords in routes.items():
        if not keywords:
            fallback = subfolder
            continue
        for kw in keywords:
            kw_lower = kw.lower()
            # Check extension match
            if kw_lower.startswith('.') and ext == kw_lower:
                return subfolder, kw
            # Check keyword in filename
            if kw_lower in name_lower:
                return subfolder, kw

    return fallback, "no match"


def dedupe_chrome_copies(files: list[Path]) -> tuple[list[Path], list[Path]]:
    """Identify Chrome-style '(N)' copies whose content matches the base file.

    Returns: (kept, duplicates). `duplicates` is a list of '(N)' copy paths
    whose bytes exactly match a non-'(N)' sibling; callers may delete them.
    """
    hashes: dict[Path, str] = {}
    for f in files:
        try:
            hashes[f] = hashlib.sha256(f.read_bytes()).hexdigest()
        except OSError:
            hashes[f] = ""

    kept: list[Path] = []
    duplicates: list[Path] = []
    for f in files:
        m = DUP_RE.match(f.name)
        if m:
            base = f.parent / (m.group(1) + m.group(3))
            if base.exists() and hashes.get(base) and hashes.get(base) == hashes[f]:
                duplicates.append(f)
                continue
        kept.append(f)
    return kept, duplicates


CONTENT_CLASSIFY_SYSTEM = """You classify files into one of a fixed set of topics based on a content preview.

You will receive a TOPIC LIST and a numbered list of FILES (each with a short content preview).

For each file, return the single topic name from the list that best matches the file's content. If no topic clearly applies, return the fallback topic.

Output: ONLY a JSON object mapping the numeric id (as string) to a topic name. No prose, no code fences."""


def classify_by_content(
    entries: list[dict],
    topics: list[str],
    fallback_topic: str,
    model: str,
    max_chars: int = 500,
    batch_size: int = 10,
) -> dict[Path, str]:
    """Ask OpenAI to assign a topic to each file using a content preview.

    `entries` items are {'path': Path, 'name': str}. Returns {Path: topic}.
    Topic is guaranteed to be in `topics` or equal to `fallback_topic`.
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: pip install openai (required for --content-aware)", file=sys.stderr)
        sys.exit(1)

    # Reuse summarize_file's multi-format preview reader (.pdf, .docx, .rtf, etc.)
    try:
        from summarize_file import read_file_content
    except ImportError:
        print("Error: summarize_file.py must live alongside smart_archive.py", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    valid_topics = set(topics) | {fallback_topic}
    topic_lines = "\n".join(f"- {t}" for t in topics) + f"\n- {fallback_topic}   (fallback)"

    result: dict[Path, str] = {}

    for start in range(0, len(entries), batch_size):
        batch = entries[start:start + batch_size]
        preview_blocks = []
        for idx, item in enumerate(batch, 1):
            preview = read_file_content(item['path'], max_chars) or "[empty]"
            preview_blocks.append(
                f"[{idx}] {item['name']}\nContent preview:\n{preview}\n"
            )

        user_msg = (
            f"Topics:\n{topic_lines}\n\n"
            f"Files:\n" + "---\n".join(preview_blocks) + "\n"
            f"Return JSON like {{\"1\": \"topic\", \"2\": \"topic\"}}."
        )

        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": CONTENT_CLASSIFY_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
        except Exception as e:  # noqa: BLE001
            print(f"  content-aware batch failed: {e}", file=sys.stderr)
            data = {}

        for idx_str, topic in data.items():
            try:
                idx = int(idx_str)
            except (TypeError, ValueError):
                continue
            if not (1 <= idx <= len(batch)):
                continue
            item = batch[idx - 1]
            result[item['path']] = topic if topic in valid_topics else fallback_topic

    # Any file not answered for falls back.
    for item in entries:
        result.setdefault(item['path'], fallback_topic)

    return result


def get_all_subjects(config: dict) -> dict:
    """Get subjects from both 'subjects:' section and root level (no indent needed)."""
    subjects = dict(config.get('subjects', {}))
    # Also check root level - any key with 'routes' is a subject
    for key, val in config.items():
        if key not in ('subjects', 'archive_root') and isinstance(val, dict) and 'routes' in val:
            subjects[key] = val
    return subjects


def sort_files(source: Path, subject: str, config: dict, execute: bool = False,
               dedupe: bool = True, content_aware: bool = False,
               content_model: str = "gpt-4o", content_chars: int = 500):
    """Sort files from source into subject's subfolders.

    When `content_aware` is True, any file that the filename-keyword matcher
    sent to the fallback subfolder gets a second chance: a content preview is
    sent to `content_model` to pick the best-fitting YAML topic.
    """

    subjects = get_all_subjects(config)

    if subject not in subjects:
        print(f"Subject '{subject}' not found in config.")
        print(f"Available: {', '.join(subjects.keys())}")
        sys.exit(1)

    subject_info = subjects[subject]
    dest_base = expand_path(subject_info.get('path', f'~/Archive/{subject}'))
    routes = subject_info.get('routes', {})

    if not source.exists():
        print(f"Source not found: {source}")
        sys.exit(1)

    files = [f for f in source.iterdir()
             if f.is_file() and not f.name.startswith('.')]

    if not files:
        print(f"No files in {source}")
        return

    duplicates: list[Path] = []
    if dedupe:
        files, duplicates = dedupe_chrome_copies(files)

    print(f"Source:  {source}")
    print(f"Subject: {subject}")
    print(f"Dest:    {dest_base}")
    print(f"Files:   {len(files)}"
          + (f"  (plus {len(duplicates)} '(N)' duplicates)" if duplicates else ""))
    print()

    if duplicates:
        print("Chrome-style duplicates (byte-identical to base):")
        for d in duplicates[:10]:
            print(f"  ~ {d.name}")
        if len(duplicates) > 10:
            print(f"  ... +{len(duplicates) - 10} more")
        print("  (will be deleted on --move)" if execute else "  (would be deleted on --move)")
        print()

    # Group by subfolder
    results = {}

    for filepath in sorted(files):
        subfolder, keyword = match_subfolder(filepath.name, routes)

        if subfolder not in results:
            results[subfolder] = []

        results[subfolder].append({
            'path': filepath,
            'name': filepath.name,
            'keyword': keyword
        })

    # Second pass: for files that fell through to the fallback bucket,
    # ask the model to pick a YAML topic from the file's content preview.
    if content_aware:
        fallback_topic = next((s for s, kw in routes.items() if not kw), "general")
        topics = [s for s, kw in routes.items() if kw]
        unmatched = [f for f in results.get(fallback_topic, [])
                     if f['keyword'] == 'no match']
        if unmatched and topics:
            print(f"--content-aware: classifying {len(unmatched)} unmatched "
                  f"file(s) via {content_model} ...")
            decisions = classify_by_content(
                unmatched, topics, fallback_topic,
                model=content_model, max_chars=content_chars,
            )
            remaining = []
            for f in results.get(fallback_topic, []):
                new_topic = decisions.get(f['path']) if f['keyword'] == 'no match' else None
                if new_topic and new_topic != fallback_topic:
                    results.setdefault(new_topic, []).append(
                        {**f, 'keyword': f'[content→{new_topic}]'}
                    )
                else:
                    remaining.append(f)
            if remaining:
                results[fallback_topic] = remaining
            else:
                results.pop(fallback_topic, None)
            print()

    # Print plan
    print("=" * 50)
    print("SORT PLAN")
    print("=" * 50)

    for subfolder, files_list in sorted(results.items()):
        print(f"\n→ {subject}/{subfolder}/  ({len(files_list)} files)")

        for f in files_list[:10]:
            print(f"    {f['name']}")
            print(f"      matched: {f['keyword']}")

        if len(files_list) > 10:
            print(f"    ... +{len(files_list) - 10} more")

    if not execute:
        print("\n" + "=" * 50)
        print("DRY RUN - no files moved")
        print("Add --move to execute")
        print("=" * 50)
        return

    # Execute
    print("\n" + "=" * 50)
    print("MOVING FILES...")
    print("=" * 50)

    for d in duplicates:
        try:
            d.unlink()
            print(f"  ~ deleted duplicate: {d.name}")
        except OSError as e:
            print(f"  ! could not delete {d.name}: {e}")

    moved = 0
    for subfolder, files_list in results.items():
        dest_path = dest_base / subfolder
        dest_path.mkdir(parents=True, exist_ok=True)

        for f in files_list:
            src = f['path']
            dst = dest_path / f['name']

            # Handle duplicates
            if dst.exists():
                stem, suffix = dst.stem, dst.suffix
                i = 1
                while dst.exists():
                    dst = dest_path / f"{stem}_{i}{suffix}"
                    i += 1

            try:
                shutil.move(str(src), str(dst))
                moved += 1
                print(f"  ✓ {f['name']} → {subfolder}/")
            except Exception as e:
                print(f"  ✗ {f['name']}: {e}")

    print(f"\nMoved {moved} files to {dest_base}")


def list_subjects(config: dict):
    """Show all subjects and their routes."""
    subjects = get_all_subjects(config)

    print("\nAvailable Subjects:")
    print("=" * 50)

    for name, info in subjects.items():
        path = info.get('path', '')
        routes = info.get('routes', {})

        print(f"\n{name}")
        print(f"  path: {path}")
        print(f"  subfolders:")

        for subfolder, keywords in routes.items():
            kw_str = ", ".join(keywords[:3]) if keywords else "(fallback)"
            if keywords and len(keywords) > 3:
                kw_str += f" +{len(keywords)-3}"
            print(f"    {subfolder}: {kw_str}")


def main():
    parser = argparse.ArgumentParser(
        description='Sort files by keywords from config',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python smart_archive.py ~/Desktop JobSearch
    python smart_archive.py ~/Desktop Bible --move
    python smart_archive.py --list
        """
    )

    script_dir = Path(__file__).parent
    default_config = script_dir / 'archive_config.yaml'

    parser.add_argument('source', type=Path, nargs='?', help='Source folder')
    parser.add_argument('subject', nargs='?', help='Subject from config (JobSearch, Bible, etc.)')
    parser.add_argument('-c', '--config', type=Path, default=default_config)
    parser.add_argument('--move', action='store_true', help='Actually move files')
    parser.add_argument('--list', action='store_true', help='List all subjects')
    parser.add_argument('--no-dedupe', action='store_true',
                        help="Don't drop Chrome-style '(N)' content-identical duplicates")
    parser.add_argument('--content-aware', action='store_true',
                        help='For unmatched files, send a content preview to OpenAI and route into an existing YAML topic')
    parser.add_argument('--content-model', default='gpt-4o',
                        help='Model for --content-aware (default: gpt-4o)')
    parser.add_argument('--content-chars', type=int, default=500,
                        help='Chars of content preview per file (default: 500)')

    args = parser.parse_args()

    if not args.config.exists():
        print(f"Config not found: {args.config}")
        sys.exit(1)

    config = load_config(args.config)

    if args.list:
        list_subjects(config)
        return

    if not args.source or not args.subject:
        parser.print_help()
        print("\n")
        list_subjects(config)
        return

    sort_files(args.source, args.subject, config, execute=args.move,
               dedupe=not args.no_dedupe,
               content_aware=args.content_aware,
               content_model=args.content_model,
               content_chars=args.content_chars)


if __name__ == "__main__":
    main()
