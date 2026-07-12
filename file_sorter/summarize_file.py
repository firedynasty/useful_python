#!/usr/bin/env python3
"""
Batch summarize files and extract keywords using Anthropic API.

Usage:
    python summarize_file.py <folder>                    # API mode
    python summarize_file.py ~/Downloads --chars 1000    # Sample more chars
    python summarize_file.py ~/Desktop -o results.txt    # Save results
    python summarize_file.py . --native                  # Claude Code mode (no API)
    python summarize_file.py . --native -p "categorize"  # Custom prompt

Supported formats: .txt, .pdf, .docx, .rtf, .doc, .md, .html, etc.

Dependencies:
    pip install anthropic              # Required for API mode

    For documents (uses CLI tools, no pip needed):
    - PDF: pdftotext (brew install poppler)
    - DOCX: pandoc (brew install pandoc)
    - RTF/DOC: textutil (macOS built-in)
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], max_chars: int) -> str | None:
    """Run command and return stdout, or None on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout[:max_chars]
    except Exception:
        pass
    return None


def read_file_content(filepath: Path, max_chars: int = 500) -> str:
    """Read first N characters of file content using CLI tools."""
    suffix = filepath.suffix.lower()
    fpath = str(filepath)

    # PDF files - use pdftotext (poppler)
    if suffix == '.pdf':
        if shutil.which('pdftotext'):
            text = run_cmd(['pdftotext', fpath, '-'], max_chars)
            if text:
                return text
            return "[PDF - scanned/image-only, no text]"
        return "[PDF - install poppler: brew install poppler]"

    # DOCX files - use pandoc
    if suffix == '.docx':
        if shutil.which('pandoc'):
            text = run_cmd(['pandoc', '-t', 'plain', fpath], max_chars)
            if text:
                return text
            return "[DOCX - could not extract text]"
        return "[DOCX - install pandoc: brew install pandoc]"

    # RTF files - use textutil (macOS built-in)
    if suffix == '.rtf':
        if shutil.which('textutil'):
            text = run_cmd(['textutil', '-convert', 'txt', '-stdout', fpath], max_chars)
            if text:
                return text
            return "[RTF - could not extract text]"
        return "[RTF - textutil not found]"

    # DOC files (old Word) - use textutil (macOS built-in)
    if suffix == '.doc':
        if shutil.which('textutil'):
            text = run_cmd(['textutil', '-convert', 'txt', '-stdout', fpath], max_chars)
            if text:
                return text
            return "[DOC - could not extract text]"
        return "[DOC - textutil not found]"

    # Skip binary files
    binary_exts = {'.exe', '.dll', '.zip', '.tar', '.gz', '.jpg', '.jpeg',
                   '.png', '.gif', '.mp3', '.mp4', '.mov', '.dmg', '.iso'}
    if suffix in binary_exts:
        return f"[Binary file: {suffix}]"

    # Text-based files
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read(max_chars)
    except Exception as e:
        return f"[Error: {e}]"


def summarize_batch(files_content: list[dict]) -> list[dict]:
    """
    Summarize multiple files in one API call.

    Args:
        files_content: list of {'filename': str, 'content': str}

    Returns:
        list of {'filename': str, 'keywords': list, 'explanation': str}
    """
    try:
        import anthropic
    except ImportError:
        print("Error: pip install anthropic")
        sys.exit(1)

    client = anthropic.Anthropic()

    # Build prompt for all files
    file_list = []
    for i, f in enumerate(files_content, 1):
        file_list.append(f"[{i}] {f['filename']}\n{f['content'][:500]}\n")

    prompt = f"""Analyze these files and extract 3 keywords + a brief explanation for each.

For each file:
1. Provide 3 keywords (lowercase) that help categorize it by topic/type/purpose
2. Write a 1-2 sentence explanation of what the file is/does

Files:
{'---'.join(file_list)}

Return in this exact format (one file per block):
1. keyword1, keyword2, keyword3
   Explanation goes here in 1-2 sentences.

2. keyword1, keyword2, keyword3
   Explanation goes here in 1-2 sentences.
...
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    response = message.content[0].text

    # Parse response - expect alternating keyword/explanation lines
    results = []
    lines = response.strip().split('\n')

    # Group by file number
    current_keywords = []
    current_explanation = ""
    file_idx = 0

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check if line starts with number (e.g., "1. " or "2. ")
        if line_stripped and line_stripped[0].isdigit() and '.' in line_stripped:
            # Save previous file if exists
            if file_idx > 0 and file_idx <= len(files_content):
                results.append({
                    'filename': files_content[file_idx - 1]['filename'],
                    'keywords': current_keywords,
                    'explanation': current_explanation.strip()
                })

            # Parse new keywords line
            keyword_part = line_stripped.split('.', 1)[-1].strip()
            current_keywords = [k.strip() for k in keyword_part.split(',')]
            current_explanation = ""
            file_idx += 1
        else:
            # This is an explanation line (may be indented)
            current_explanation += " " + line_stripped

    # Don't forget last file
    if file_idx > 0 and file_idx <= len(files_content):
        results.append({
            'filename': files_content[file_idx - 1]['filename'],
            'keywords': current_keywords,
            'explanation': current_explanation.strip()
        })

    # Fill in any missing files with empty results
    while len(results) < len(files_content):
        results.append({
            'filename': files_content[len(results)]['filename'],
            'keywords': [],
            'explanation': ""
        })

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Batch extract keywords from files using Anthropic API or Claude Code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (API mode):
    python summarize_file.py ~/Downloads
    python summarize_file.py ~/Desktop --chars 1000
    python summarize_file.py . -o keywords.txt

Examples (Native mode - for Claude Code):
    python summarize_file.py . --native
    python summarize_file.py ~/Downloads --native -p "categorize these files"
    python summarize_file.py . --native -o my_context.txt
        """
    )

    parser.add_argument('folder', type=Path, help='Folder to process')
    parser.add_argument('--chars', type=int, default=500,
                        help='Characters to sample per file (default: 500)')
    parser.add_argument('-o', '--output', type=Path,
                        help='Output file (default: print to stdout)')
    parser.add_argument('--batch-size', type=int, default=10,
                        help='Files per API call (default: 10)')
    parser.add_argument('--native', action='store_true',
                        help='Export files for Claude Code to process (no API call)')
    parser.add_argument('-p', '--prompt', type=str,
                        help='Custom prompt for Claude Code in native mode')

    args = parser.parse_args()

    if not args.folder.exists():
        print(f"Folder not found: {args.folder}")
        sys.exit(1)

    # Get all files
    files = [f for f in args.folder.iterdir()
             if f.is_file() and not f.name.startswith('.')]

    if not files:
        print(f"No files in {args.folder}")
        sys.exit(1)

    # Native mode: export for Claude Code without API call
    if args.native:
        print(f"Reading {len(files)} files from {args.folder}")
        print(f"Sampling {args.chars} chars per file\n")

        # Read all files
        files_content = []
        for i, f in enumerate(sorted(files), 1):
            print(f"[{i}/{len(files)}] Reading: {f.name}")
            content = read_file_content(f, args.chars)
            files_content.append({'filename': f.name, 'content': content})

        # Build output
        output_lines = []
        output_lines.append("=== ROLE: File Summarizer ===")
        output_lines.append("""You are a helpful assistant that analyzes files and provides summaries.

For each file below, provide:
1. Three keywords (lowercase) that categorize the file by topic/type/purpose
2. A 1-2 sentence explanation of what the file is/does

Format your response like:
filename.txt
  Keywords: keyword1, keyword2, keyword3
  Summary: Brief explanation here.
""")
        output_lines.append("=== END ROLE ===\n")

        output_lines.append(f"=== CONTEXT FROM {len(files_content)} FILE(S) ===\n")
        for fc in files_content:
            output_lines.append(f"--- FILE: {fc['filename']} ---")
            output_lines.append(fc['content'])
            output_lines.append("")
        output_lines.append("=== END OF CONTEXT ===")

        # Add custom prompt or default
        if args.prompt:
            output_lines.append(f"\n=== USER REQUEST ===")
            output_lines.append(args.prompt)
            output_lines.append("=== END REQUEST ===")
        else:
            output_lines.append("\n=== USER REQUEST ===")
            output_lines.append("Please analyze each file and provide keywords + a brief summary for each.")
            output_lines.append("=== END REQUEST ===")

        full_output = "\n".join(output_lines)

        # Write to file (default: claude_context.txt)
        output_file = args.output if args.output else Path("claude_context.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_output)

        # Print for Claude Code to see
        print("\n" + "=" * 60)
        print(full_output)
        print(f"\n[Context saved to: {output_file}]")
        print(f"[--native mode: Claude Code should now respond to the request above]")
        sys.exit(0)

    print(f"Processing {len(files)} files from {args.folder}")
    print(f"Sampling {args.chars} chars per file\n")

    # Read content
    files_content = []
    for i, f in enumerate(sorted(files), 1):
        print(f"[{i}/{len(files)}] Reading: {f.name}")
        content = read_file_content(f, args.chars)
        files_content.append({'filename': f.name, 'content': content})

    print()  # blank line before API calls

    # Process in batches
    all_results = []
    total_batches = (len(files_content) + args.batch_size - 1) // args.batch_size
    for i in range(0, len(files_content), args.batch_size):
        batch = files_content[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        print(f"API batch [{batch_num}/{total_batches}]: {len(batch)} files")
        for f in batch:
            print(f"  - {f['filename']}")
        results = summarize_batch(batch)
        all_results.extend(results)
        print()

    # Colors
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RESET = '\033[0m'

    # Output
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    output_lines = []
    for r in all_results:
        keywords = ', '.join(r['keywords'])
        explanation = r.get('explanation', '')

        # Plain text for file
        output_lines.append(f"{r['filename']}")
        output_lines.append(f"  Keywords: {keywords}")
        if explanation:
            output_lines.append(f"  Summary: {explanation}")
        output_lines.append("")  # blank line between files

        # Colored for terminal
        print(f"{CYAN}{r['filename']}{RESET}")
        print(f"  Keywords: {GREEN}{keywords}{RESET}")
        if explanation:
            print(f"  Summary: {YELLOW}{explanation}{RESET}")
        print()  # blank line

    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(output_lines))
        print(f"{YELLOW}Saved to {args.output}{RESET}")


if __name__ == "__main__":
    main()
