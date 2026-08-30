#!/usr/bin/env python3
"""
mindmap.py — Open the folder mind map for any directory.

Usage (from any terminal directory):
    python /path/to/mindmap.py              # uses $PWD, depth 2
    python /path/to/mindmap.py ~/Documents  # specific path, depth 2
    python /path/to/mindmap.py . 3          # current dir, depth 3

Add to ~/.zshrc for anywhere access:
    alias mindmap='python3 /Users/stanleytan/Documents/technical/python/xmind/mindmap_folders/mindmap.py'

Then just run:
    mindmap          # opens mindmap for current dir
    mindmap . 3      # depth 3
    mindmap ~/notes  # specific folder
"""

import sys
import os
import re
import json
import socket
import subprocess
import tempfile
import threading
import webbrowser
import http.server
import socketserver
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / "tree-mindmap.html"


def run_tree(path: str, depth: int) -> str:
    """Run `tree -d -L depth path` and return its output."""
    try:
        result = subprocess.run(
            ["tree", "-d", "-L", str(depth), path],
            capture_output=True, text=True
        )
        if result.returncode != 0 and not result.stdout:
            print(f"Warning: tree exited with code {result.returncode}")
            print(result.stderr)
        return result.stdout
    except FileNotFoundError:
        print("Error: 'tree' command not found.")
        print("Install it with:  brew install tree")
        sys.exit(1)


def build_html(base_path: str, tree_output: str) -> str:
    """Inject base_path and tree_output into the HTML template."""
    html = TEMPLATE_PATH.read_text(encoding="utf-8")

    folder_name = Path(base_path).name or base_path

    # 1. Replace base path input value — regex-based so it works regardless of
    #    what default value is hardcoded in the template.
    html = re.sub(
        r'(<input\s+id="basePath"[^>]*\s+value=")[^"]*(")',
        rf'\g<1>{base_path}\g<2>',
        html
    )

    # 2. Update <title> and <h1> to show the current folder name
    html = re.sub(r'<title>[^<]*</title>', f'<title>{folder_name} — folder mind map</title>', html)
    html = re.sub(r'(<h1>[^<]*</h1>)', f'<h1>{folder_name} — folder mind map</h1>', html)

    # 3. Replace the EXAMPLE_TREE constant with the live tree output (JSON string
    #    so all escaping is correct, including Unicode box-drawing chars).
    tree_js = json.dumps(tree_output)
    old_start = "const EXAMPLE_TREE = `"
    old_end = "`;"
    start_idx = html.find(old_start)
    end_idx   = html.find(old_end, start_idx) + len(old_end)
    if start_idx != -1 and end_idx > start_idx:
        html = html[:start_idx] + f"const EXAMPLE_TREE = {tree_js};" + html[end_idx:]

    return html


def main():
    # Parse arguments
    args = sys.argv[1:]
    target = args[0] if len(args) >= 1 else os.getcwd()
    depth  = int(args[1]) if len(args) >= 2 else 2

    target = str(Path(target).expanduser().resolve())

    if not os.path.isdir(target):
        print(f"Error: '{target}' is not a directory.")
        sys.exit(1)

    print(f"  Path : {target}")
    print(f"  Depth: {depth}")
    print("  Running tree…")

    tree_output = run_tree(target, depth)

    html = build_html(target, tree_output)

    # Write to a temp file in a dedicated temp directory so the HTTP server
    # only exposes that one folder (not all of /tmp).
    tmp_dir = tempfile.mkdtemp(prefix="mindmap_")
    tmp_path = os.path.join(tmp_dir, "index.html")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Serve via localhost so the browser grants clipboard access.
    # file:// URLs are treated as opaque origins and block navigator.clipboard.
    with socket.socket() as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=tmp_dir, **kwargs)
        def log_message(self, *args):
            pass  # suppress per-request log noise

    with socketserver.TCPServer(("127.0.0.1", port), QuietHandler) as httpd:
        url = f"http://localhost:{port}/index.html"
        print(f"  Serving: {url}")
        webbrowser.open(url)
        print("  Press Ctrl+C to stop the server when done.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")


if __name__ == "__main__":
    main()
