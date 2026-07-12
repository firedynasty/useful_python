#!/usr/bin/env python3
"""
Flatten-Rename - YAML-aware flattening. Walk a nested directory tree,
rename generic files to include context from their path, and copy
everything into a single flat output directory.

Uses archive_config.yaml to decide how much of the path to bake into
the filename. For each file, walks up the directory tree until it finds
a folder name that matches a YAML route. That route becomes the implicit
sort target; any intermediate folders between the route and the file
get included as context in the filename.

Usage:
    python flatten_rename.py <source> <dest> <subject>
    python flatten_rename.py ~/notes/02-basketball ~/notes/02-basketball_b Basketball
    python flatten_rename.py ~/notes/02-basketball ~/notes/02-basketball_b Basketball --move

Dry-run by default. Add --move to actually copy files.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pip install pyyaml")
    sys.exit(1)


# Patterns considered "generic" — these get folder context prepended.
GENERIC_PATTERNS = [
    re.compile(r"^Screen Recording ", re.IGNORECASE),
    re.compile(r"^Screenshot ", re.IGNORECASE),
    re.compile(r"^clip_\d+", re.IGNORECASE),
    re.compile(r"^\d{8}_\d{6}", re.IGNORECASE),       # 20260608_191927
    re.compile(r"^Combined \d{4}-", re.IGNORECASE),    # Combined 2026-07-03...
    re.compile(r"^workout_\d+", re.IGNORECASE),
    re.compile(r"^shooting\d+", re.IGNORECASE),
    re.compile(r"^transition\d+", re.IGNORECASE),
    re.compile(r"^cutting\d+", re.IGNORECASE),
    re.compile(r"^image\d+", re.IGNORECASE),           # image1.png, image2.png
    re.compile(r"^[a-zA-Z]+_\d+\.", re.IGNORECASE),   # trae_1.mp4, pass_1.mp4
]

# Single-word filenames like "horns.mp4", "defense.mp4" — too vague alone.
SINGLE_WORD_RE = re.compile(r"^[a-zA-Z]+\.[a-zA-Z0-9]+$")

# Folder prefixes to skip when building context (wrapper folders).
SKIP_PREFIXES = ("vid_", "video")


def is_generic(filename: str) -> bool:
    """Check if a filename is too generic to stand alone."""
    for pat in GENERIC_PATTERNS:
        if pat.search(filename):
            return True
    if SINGLE_WORD_RE.match(filename):
        return True
    return False


def load_routes(config_path: Path, subject: str) -> tuple:
    """Load route names and their keywords from a YAML subject block.

    Returns: (route_names set, keyword_to_route dict)
      - route_names: {'skills_shooting', 'skills_dribbling', ...}
      - keyword_to_route: {'shooting': 'skills_shooting', 'dribbl': 'skills_dribbling', ...}
    """
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Check both root-level and nested subjects
    subject_info = None
    subjects = config.get("subjects", {})
    if subject in subjects:
        subject_info = subjects[subject]
    elif subject in config and isinstance(config[subject], dict):
        subject_info = config[subject]

    if not subject_info or "routes" not in subject_info:
        print(f"Subject '{subject}' not found in {config_path}")
        sys.exit(1)

    routes = subject_info["routes"]
    route_names = set(routes.keys())

    # Build reverse lookup: keyword → route name
    keyword_to_route = {}
    for route_name, keywords in routes.items():
        if keywords:
            for kw in keywords:
                keyword_to_route[kw.lower()] = route_name

    return route_names, keyword_to_route


def clean_part(part: str) -> str:
    """Clean a folder name for use in a filename — strip trailing underscores."""
    return part.rstrip("_")


def match_folder_to_route(folder_name: str, route_names: set,
                          keyword_to_route: dict) -> str | None:
    """Try to match a folder name to a YAML route.

    First checks exact match against route names, then checks if any
    YAML keyword appears in the folder name.

    Example: 'vid_workouts' contains 'workout' → matches 'workouts_drills'
    """
    # Exact match
    if folder_name in route_names:
        return folder_name

    # Keyword match against folder name
    folder_lower = folder_name.lower()
    for kw, route in keyword_to_route.items():
        if kw in folder_lower:
            return route

    return None


def build_context(filepath: Path, source_root: Path, route_names: set,
                  keyword_to_route: dict) -> tuple:
    """Walk up from the file's parent to find the YAML route, then collect
    intermediate folder names as context.

    Returns: (route_match, context_parts)
      - route_match: the YAML route name that matched, or None
      - context_parts: list of intermediate folder names between the route
        and the file (cleaned, skipping vid_* wrappers)

    Matches folder names against YAML routes by both exact name AND keyword
    matching. So 'vid_workouts' matches 'workouts_drills' because the keyword
    'workout' appears in the folder name.

    Example:
      game-film_breakdowns/game_highlights/harden_/clip_1.mp4
      route_names = {'game-film_breakdowns', 'skills_shooting', ...}

      → route_match = 'game-film_breakdowns'
      → context_parts = ['game_highlights', 'harden']
    """
    rel = filepath.relative_to(source_root)
    parts = list(rel.parent.parts)  # e.g. ['game-film_breakdowns', 'game_highlights', 'harden_']

    if not parts:
        return None, []

    # Walk from root toward leaf, looking for the YAML route match
    route_idx = None
    route_match = None
    for i, part in enumerate(parts):
        matched = match_folder_to_route(part, route_names, keyword_to_route)
        if matched:
            route_idx = i
            route_match = matched
            break

    if route_idx is not None:
        # Everything after the route match is context
        context = [
            clean_part(p) for p in parts[route_idx + 1:]
            if not any(p.startswith(pfx) for pfx in SKIP_PREFIXES)
        ]
        return route_match, context
    else:
        # No YAML route found — use all non-skip parts as context
        context = [
            clean_part(p) for p in parts
            if not any(p.startswith(pfx) for pfx in SKIP_PREFIXES)
        ]
        return None, context


def prompt_for_prefix(filepath: Path, source_root: Path, route_names: set,
                      cache: dict) -> str:
    """Ask the user to choose a prefix when no YAML route matches.

    Caches choices by parent folder so you only get asked once per folder,
    not once per file.
    """
    rel = filepath.relative_to(source_root)
    parent_key = str(rel.parent)

    if parent_key in cache:
        return cache[parent_key]

    sorted_routes = sorted(route_names)
    print(f"\n  No YAML route match for: {filepath}")
    print(f"  Available routes:")
    for i, route in enumerate(sorted_routes, 1):
        print(f"    {i}. {route}")
    print(f"    s. skip (keep filename as-is)")
    print(f"    o. open file")
    print(f"    Or type a custom prefix")

    while True:
        choice = input(f"  Choice for [{parent_key}]: ").strip()
        if choice.lower() == "o":
            subprocess.run(["open", str(filepath)])
            continue
        if choice.lower() == "s":
            cache[parent_key] = ""
            return ""
        if choice.isdigit() and 1 <= int(choice) <= len(sorted_routes):
            prefix = sorted_routes[int(choice) - 1]
            cache[parent_key] = prefix
            return prefix
        if choice:
            cache[parent_key] = choice
            return choice
        print("  Please enter a number, 's', 'o' to open, or a custom prefix.")


# Cache for user choices — shared across calls, keyed by parent folder.
_prompt_cache: dict = {}


def flatten_name(filepath: Path, source_root: Path, route_names: set,
                 keyword_to_route: dict, interactive: bool = False) -> str:
    """Produce a flat filename with folder context baked in.

    Any file that is nested (has parent folders) gets context prepended.
    Files at the source root only get context if they are generic.
    """
    name = filepath.name
    rel = filepath.relative_to(source_root)
    is_nested = len(rel.parts) > 1  # has parent folders

    if not is_nested and not is_generic(name):
        return name

    route_match, context_parts = build_context(filepath, source_root, route_names,
                                                keyword_to_route)

    if route_match is not None:
        # YAML route found — use intermediate folders as prefix
        if context_parts:
            prefix = "_".join(context_parts)
        else:
            prefix = route_match
    elif interactive:
        # No YAML route — ask the user
        prefix = prompt_for_prefix(filepath, source_root, route_names, _prompt_cache)
        if not prefix:
            return name  # user chose skip
        # Still include any intermediate context after the chosen prefix
        if context_parts:
            prefix = prefix + "_" + "_".join(context_parts)
    elif context_parts:
        # Non-interactive fallback — use folder names as context
        prefix = "_".join(context_parts)
    else:
        return name

    # Clean up Screen Recording names
    sr_match = re.match(
        r"^Screen Recording (\d{4}-\d{2}-\d{2}) at (\d+\.\d+\.\d+\s*[AP]M)(.*)",
        name, re.IGNORECASE,
    )
    if sr_match:
        date_part = sr_match.group(1)
        time_part = sr_match.group(2).replace(".", "").replace(" ", "")
        ext = filepath.suffix
        return f"{prefix}_{date_part}_{time_part}{ext}"

    # For other generic files: prefix_originalname
    return f"{prefix}_{name}"


def flatten(source: Path, dest: Path, route_names: set, keyword_to_route: dict,
            execute: bool = False, interactive: bool = False):
    """Walk source tree, plan renames, optionally copy to dest."""
    if not source.is_dir():
        print(f"Source not found: {source}")
        sys.exit(1)

    all_files = sorted(
        f for f in source.rglob("*")
        if f.is_file() and not f.name.startswith(".")
    )

    if not all_files:
        print(f"No files found in {source}")
        return

    # Build rename plan
    plan = []
    # Pre-populate with files already in dest so we don't overwrite them
    seen_names = {}
    if dest.is_dir():
        for existing in dest.iterdir():
            if existing.is_file():
                seen_names[existing.name] = existing

    for filepath in all_files:
        new_name = flatten_name(filepath, source, route_names, keyword_to_route,
                                interactive=interactive)

        # Handle collisions (against both existing dest files and current batch)
        if new_name in seen_names:
            stem = Path(new_name).stem
            ext = Path(new_name).suffix
            i = 2
            while f"{stem}_{i}{ext}" in seen_names:
                i += 1
            new_name = f"{stem}_{i}{ext}"

        seen_names[new_name] = filepath
        changed = (new_name != filepath.name)
        plan.append((filepath, new_name, changed))

    # Print plan
    renamed_count = sum(1 for _, _, changed in plan if changed)
    print(f"Source:  {source}")
    print(f"Dest:    {dest}")
    print(f"Routes:  {sorted(route_names)}")
    print(f"Files:   {len(plan)} total, {renamed_count} will be renamed")
    print()

    for src, new_name, changed in plan:
        rel = src.relative_to(source)
        if changed:
            print(f"  {rel}")
            print(f"    → {new_name}")
        else:
            print(f"  {rel}  (unchanged)")

    if not execute:
        print(f"\nDRY RUN — no files copied. Add --move to execute.")
        return

    dest.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src, new_name, _ in plan:
        dst = dest / new_name
        try:
            shutil.copy2(str(src), str(dst))
            copied += 1
        except Exception as e:
            print(f"  ERROR: {src} → {e}")

    print(f"\nCopied {copied} files to {dest}")


def main():
    parser = argparse.ArgumentParser(
        description="YAML-aware flatten: walk up from each file until a YAML "
                    "route matches, bake intermediate folders into the filename.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    script_dir = Path(__file__).parent
    default_config = script_dir / "archive_config.yaml"

    parser.add_argument("source", type=Path, help="Source directory to flatten")
    parser.add_argument("dest", type=Path, help="Destination flat directory")
    parser.add_argument("subject", help="Subject name from archive_config.yaml (e.g. Basketball)")
    parser.add_argument("-c", "--config", type=Path, default=default_config,
                        help="Path to archive_config.yaml")
    parser.add_argument("--move", action="store_true",
                        help="Actually copy files (default is dry-run)")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Prompt for prefix when no YAML route matches")

    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    dest = args.dest.expanduser().resolve()

    if source == dest:
        print("Source and dest cannot be the same directory.")
        sys.exit(1)

    route_names, keyword_to_route = load_routes(args.config, args.subject)
    flatten(source, dest, route_names, keyword_to_route,
            execute=args.move, interactive=args.interactive)


if __name__ == "__main__":
    main()
