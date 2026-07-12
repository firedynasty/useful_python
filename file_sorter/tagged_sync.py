#!/usr/bin/env python3
"""Sync only directories containing a tag file to a destination via scp.

Walk a source directory tree, find every folder that contains a marker
file (default: tagged.txt), and scp each one to a destination while
preserving the relative path structure.

Usage (run from inside the notes folder):

    cd ~/Documents/notes

    # Dry run — see what would sync:
    python ~/Documents/technical/python/file_sorter/tagged_sync.py . akaysjou@162.241.225.12:~/public_html/notes/ --dry-run

    # Sync for real:
    python ~/Documents/technical/python/file_sorter/tagged_sync.py . akaysjou@162.241.225.12:~/public_html/notes/

    # Just list which folders are tagged:
    python ~/Documents/technical/python/file_sorter/tagged_sync.py . --list

    # Custom tag file name:
    python ~/Documents/technical/python/file_sorter/tagged_sync.py . dest/ --tag sync_me.txt

How it works:
    1. Drop a "tagged.txt" file into any folder you want synced
    2. Run this script with "." as source and your remote as dest
    3. Only folders containing tagged.txt get copied (with their contents)
    4. The tagged.txt file itself is NOT copied to the destination
    5. index.php is automatically copied to the destination root
       so the PHP content viewer is available to browse everything

    To skip copying index.php, use --no-index.
    To use a different index.php, use --index /path/to/index.php.

Example — given this tree:
    notes/
    ├── admin_assistant/
    │   └── udemy/           <-- tagged.txt here
    ├── analysis/
    │   └── other_/
    │       ├── resumes/     <-- tagged.txt here
    │       ├── summaries/   <-- tagged.txt here
    │       └── with_references/

    Only udemy/, resumes/, and summaries/ will be synced.
    other_/ itself and with_references/ are skipped.
    index.php is placed at the destination root to view them.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# Default path to the PHP content viewer
DEFAULT_INDEX_PHP = os.path.join(
    os.path.expanduser("~"),
    "Documents/technical/github/vercel_textviewer/phpAppForBluehost/index.php",
)


def find_tagged_dirs(source, tag_file):
    """Find all directories containing the tag file."""
    tagged = []
    for dirpath, _dirnames, filenames in os.walk(source):
        if tag_file in filenames:
            tagged.append(dirpath)
    tagged.sort()
    return tagged


def is_rclone(dest):
    """Check if destination is an rclone remote (e.g. dropbox:/path)."""
    if ":" not in dest:
        return False
    host = dest.split(":", 1)[0]
    # rclone remotes are simple names (no @ or /), scp has user@host
    return "@" not in host and "/" not in host


def is_remote(dest):
    """Check if destination is a remote scp path (user@host:path)."""
    return ":" in dest and not is_rclone(dest)


def parse_remote(dest):
    """Split 'user@host:path' into (user@host, path)."""
    host, path = dest.split(":", 1)
    return host, path


def ensure_remote_dir(host, remote_dir):
    """Create directory on remote host if it doesn't exist."""
    cmd = ["ssh", host, f"mkdir -p {remote_dir}"]
    subprocess.run(cmd, capture_output=True)


def sync_tagged_dirs_rclone(source, dest, tagged_dirs, tag_file, dry_run=False):
    """Copy tagged directories to an rclone remote destination."""
    source = os.path.abspath(source)
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for tagged_dir in tagged_dirs:
            tagged_dir = os.path.abspath(tagged_dir)
            rel_path = os.path.relpath(tagged_dir, source)
            staging_dest = os.path.join(tmpdir, rel_path)

            print(f"\n  Staging: {rel_path}/")

            shutil.copytree(
                tagged_dir,
                staging_dest,
                ignore=shutil.ignore_patterns(tag_file),
            )

        if not os.listdir(tmpdir):
            print("  (nothing to sync)")
            return [("(empty)", 0)]

        print(f"\n{'[DRY RUN] ' if dry_run else ''}Uploading to {dest}")

        if dry_run:
            for tagged_dir in tagged_dirs:
                rel_path = os.path.relpath(os.path.abspath(tagged_dir), source)
                print(f"  {rel_path}/")
                for f in sorted(os.listdir(tagged_dir)):
                    if f == tag_file:
                        continue
                    print(f"    {f}")
                results.append((rel_path, 0))
            return results

        cmd = ["rclone", "copy", tmpdir + "/", dest.rstrip("/") + "/", "--progress"]
        result = subprocess.run(cmd)

        for tagged_dir in tagged_dirs:
            rel_path = os.path.relpath(os.path.abspath(tagged_dir), source)
            results.append((rel_path, result.returncode))

    return results


def sync_tagged_dirs(source, dest, tagged_dirs, tag_file, dry_run=False):
    """Copy each tagged directory to the destination using scp."""
    source = os.path.abspath(source)
    results = []
    remote = is_remote(dest)

    if remote and not dry_run:
        # Build the full nested structure in a single temp dir, then scp
        # the whole tree in one shot — one password prompt for all folders
        host, base_path = parse_remote(dest)

        with tempfile.TemporaryDirectory() as tmpdir:
            for tagged_dir in tagged_dirs:
                tagged_dir = os.path.abspath(tagged_dir)
                rel_path = os.path.relpath(tagged_dir, source)
                staging_dest = os.path.join(tmpdir, rel_path)

                print(f"\n  Staging: {rel_path}/")

                shutil.copytree(
                    tagged_dir,
                    staging_dest,
                    ignore=shutil.ignore_patterns(tag_file),
                )

            # scp the whole tree to the remote destination in one go
            # This creates all intermediate directories automatically
            items = os.listdir(tmpdir)
            if not items:
                print("  (nothing to sync)")
                return [(r, 0) for r in ["(empty)"]]

            src_paths = [os.path.join(tmpdir, item) for item in items]
            remote_dest = f"{host}:{base_path.rstrip('/')}/"
            print(f"\n  Uploading to {remote_dest}")
            cmd = ["scp", "-r"] + src_paths + [remote_dest]
            result = subprocess.run(cmd)

            for tagged_dir in tagged_dirs:
                rel_path = os.path.relpath(os.path.abspath(tagged_dir), source)
                results.append((rel_path, result.returncode))

        return results

    # Dry run or local copy
    for tagged_dir in tagged_dirs:
        tagged_dir = os.path.abspath(tagged_dir)
        rel_path = os.path.relpath(tagged_dir, source)

        if remote:
            host, base_path = parse_remote(dest)
            dst = f"{host}:{base_path.rstrip('/')}/{rel_path}"
        else:
            dst = os.path.join(dest, rel_path)

        print(f"\n{'[DRY RUN] ' if dry_run else ''}Syncing: {rel_path}/")
        print(f"  {tagged_dir}/ -> {dst}/")

        if dry_run:
            for f in sorted(os.listdir(tagged_dir)):
                if f == tag_file:
                    continue
                print(f"    {f}")
            results.append((rel_path, 0))
            continue

        # Local copy
        os.makedirs(dst, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            staging = os.path.join(tmpdir, "staging")
            shutil.copytree(
                tagged_dir,
                staging,
                ignore=shutil.ignore_patterns(tag_file),
            )
            for item in os.listdir(staging):
                s = os.path.join(staging, item)
                d = os.path.join(dst, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
        results.append((rel_path, 0))

    return results


def sync_index_php(index_path, dest, dry_run=False):
    """Copy index.php to the destination root."""
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Copying index.php to destination root")
    print(f"  {index_path} -> {dest.rstrip('/')}/index.php")

    if dry_run:
        return 0

    if is_remote(dest):
        host, base_path = parse_remote(dest)
        ensure_remote_dir(host, base_path.rstrip("/"))
        dst = f"{host}:{base_path.rstrip('/')}/index.php"
        cmd = ["scp", index_path, dst]
        result = subprocess.run(cmd)
        return result.returncode
    else:
        os.makedirs(dest, exist_ok=True)
        shutil.copy2(index_path, os.path.join(dest, "index.php"))
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Sync only directories containing a tag file to a destination.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python tagged_sync.py . user@host:~/public_html/notes/",
    )
    parser.add_argument(
        "source", help="Source directory to scan (use . for current directory)"
    )
    parser.add_argument(
        "dest",
        nargs="?",
        default=None,
        help="Destination path (local or user@host:/path)",
    )
    parser.add_argument(
        "--tag",
        default="tagged.txt",
        help="Name of the marker file to look for (default: tagged.txt)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without transferring files",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Just list tagged directories, don't sync anything",
    )
    parser.add_argument(
        "--index",
        default=DEFAULT_INDEX_PHP,
        help=f"Path to index.php to copy to destination root (default: {DEFAULT_INDEX_PHP})",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Skip copying index.php to the destination",
    )
    args = parser.parse_args()

    source = os.path.expanduser(args.source)
    if not os.path.isdir(source):
        print(f"Error: source directory not found: {source}", file=sys.stderr)
        sys.exit(1)

    tagged_dirs = find_tagged_dirs(source, args.tag)

    if not tagged_dirs:
        print(f"No directories containing '{args.tag}' found in {os.path.abspath(source)}")
        sys.exit(0)

    print(f"Found {len(tagged_dirs)} tagged folder(s):\n")
    for d in tagged_dirs:
        rel = os.path.relpath(d, source)
        print(f"  {rel}/")

    if args.list:
        sys.exit(0)

    if not args.dest:
        print(
            "\nNo destination specified. Provide a dest to sync, or use --list to just list."
        )
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"Source:      {os.path.abspath(source)}")
    print(f"Destination: {args.dest}")
    if args.dry_run:
        print("Mode:        DRY RUN (nothing will be transferred)")
    print(f"{'=' * 60}")

    use_rclone = is_rclone(args.dest)

    if use_rclone:
        results = sync_tagged_dirs_rclone(
            source, args.dest, tagged_dirs, args.tag, dry_run=args.dry_run,
        )
    else:
        results = sync_tagged_dirs(
            source, args.dest, tagged_dirs, args.tag, dry_run=args.dry_run,
        )

    # Copy index.php to destination root (skip for rclone destinations)
    index_ok = True
    if not args.no_index and not use_rclone:
        index_path = os.path.expanduser(args.index)
        if os.path.isfile(index_path):
            rc = sync_index_php(index_path, args.dest, dry_run=args.dry_run)
            if rc != 0:
                index_ok = False
                print(f"  WARNING: Failed to copy index.php (exit code {rc})")
        else:
            print(f"\n  WARNING: index.php not found at {index_path}, skipping")
            index_ok = False

    # Summary
    print(f"\n{'=' * 60}")
    ok = sum(1 for _, rc in results if rc == 0)
    fail = sum(1 for _, rc in results if rc != 0)
    print(f"Done. Synced: {ok}  Failed: {fail}", end="")
    if not args.no_index and not use_rclone:
        print(f"  index.php: {'OK' if index_ok else 'FAILED'}", end="")
    print()
    if fail:
        for path, rc in results:
            if rc != 0:
                print(f"  FAILED: {path} (exit code {rc})")
        sys.exit(1)


if __name__ == "__main__":
    main()
