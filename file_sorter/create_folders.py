#!/usr/bin/env python3
"""
Create Folders - Read route names from archive_config.yaml and create
the corresponding directories in a target location.

Usage:
    python create_folders.py <dest> <subject>
    python create_folders.py ~/notes/02-basketball_b Basketball
    python create_folders.py ~/Downloads/dropbox_sorted Basketball
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pip install pyyaml")
    sys.exit(1)


def create_folders(dest: Path, config_path: Path, subject: str):
    with open(config_path) as f:
        config = yaml.safe_load(f)

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

    for route_name in routes:
        folder = dest / route_name
        folder.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {folder}")

    print(f"\nCreated {len(routes)} folders in {dest}")


def main():
    parser = argparse.ArgumentParser(
        description="Create category folders from YAML routes.",
    )

    script_dir = Path(__file__).parent
    default_config = script_dir / "archive_config.yaml"

    parser.add_argument("dest", type=Path, help="Directory to create folders in")
    parser.add_argument("subject", help="Subject name from archive_config.yaml")
    parser.add_argument("-c", "--config", type=Path, default=default_config)

    args = parser.parse_args()
    dest = args.dest.expanduser().resolve()
    create_folders(dest, args.config, args.subject)


if __name__ == "__main__":
    main()
