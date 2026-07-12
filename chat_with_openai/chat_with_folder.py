#!/usr/bin/env python3
"""
Chat with your folder - search-then-read approach.
The AI only knows what's in your files. It searches for relevant files,
reads them, then responds from the content. No outside knowledge.

Usage:
  python chat_with_folder.py /path/to/folder          # search & read files on demand
  python chat_with_folder.py -c                        # chat about clipboard contents
  python chat_with_folder.py /path/to/folder -m gpt-4o

Requires: pip install openai sounddevice numpy soundfile
Set: export OPENAI_API_KEY=sk-...
"""

import os
import sys
import glob
import json
import argparse
import tempfile
import numpy as np
from datetime import datetime

try:
    import sounddevice as sd
except ImportError:
    print("Missing: pip install sounddevice")
    sys.exit(1)

try:
    import soundfile as sf
except ImportError:
    print("Missing: pip install soundfile")
    sys.exit(1)

try:
    from openai import OpenAI
except ImportError:
    print("Missing: pip install openai")
    sys.exit(1)


SAMPLE_RATE = 44100
CHANNELS = 1
TEXT_EXTENSIONS = (".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".csv", ".sh")


# ── File index ──

def build_index(root_path):
    """Walk folder, build lightweight index: path, name, category, preview."""
    index = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        for fname in sorted(filenames):
            if not any(fname.lower().endswith(ext) for ext in TEXT_EXTENSIONS):
                continue
            fpath = os.path.join(dirpath, fname)
            rel = os.path.relpath(fpath, root_path)
            # Category from subfolder name
            parts = rel.split(os.sep)
            category = parts[0] if len(parts) > 1 else "root"
            # Preview: first 200 chars
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    preview = f.read(200).replace("\n", " ").strip()
            except Exception:
                preview = ""
            index.append({
                "path": fpath,
                "relative": rel,
                "name": os.path.splitext(fname)[0],
                "category": category,
                "preview": preview,
            })
    return index


def search_files(index, query):
    """Simple keyword search over filenames, categories, and previews."""
    query_words = query.lower().split()
    results = []
    for entry in index:
        searchable = f"{entry['name']} {entry['category']} {entry['preview']}".lower()
        score = sum(1 for w in query_words if w in searchable)
        if score > 0:
            results.append((score, entry))
    results.sort(key=lambda x: -x[0])
    return [r[1] for r in results[:8]]


def read_file(file_path, max_chars=15000):
    """Read a file's full content, capped."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        return content
    except Exception as e:
        return f"Error reading file: {e}"


# ── OpenAI tool definitions ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search the user's files by keywords. Returns matching file names, categories, and previews. Use this to find relevant files before reading them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords to search for (e.g. 'prayer', 'faith', 'genesis', 'psalms')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full content of a specific file. Use the relative path from search results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "The relative path of the file to read (from search results)"
                    }
                },
                "required": ["relative_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "List all available categories/folders and how many files are in each.",
            "parameters": {
                "type": "object",
                "properties": {},
            }
        }
    },
]


def handle_tool_call(tool_call, index, root_path):
    """Execute a tool call, return the result string."""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    if name == "search_files":
        results = search_files(index, args["query"])
        if not results:
            return "No files found matching that query."
        lines = []
        for r in results:
            lines.append(f"- {r['relative']}  (category: {r['category']})\n  Preview: {r['preview'][:120]}")
        return "\n".join(lines)

    elif name == "read_file":
        rel = args["relative_path"]
        fpath = os.path.join(root_path, rel)
        if not os.path.isfile(fpath):
            return f"File not found: {rel}"
        content = read_file(fpath)
        return f"=== {rel} ===\n{content}"

    elif name == "list_categories":
        cats = {}
        for entry in index:
            cats[entry["category"]] = cats.get(entry["category"], 0) + 1
        lines = [f"- {cat} ({count} files)" for cat, count in sorted(cats.items())]
        return "\n".join(lines)

    return "Unknown tool."


# ── Audio ──

def select_input_device():
    devices = sd.query_devices()
    input_devs = [(i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0]
    if not input_devs:
        print("No input devices found.")
        sys.exit(1)
    print("\nInput devices:")
    for idx, (dev_id, dev) in enumerate(input_devs):
        marker = " *" if dev_id == sd.default.device[0] else ""
        print(f"  {idx}  {dev['name']}{marker}")
    choice = input("\nDevice # (Enter=default): ").strip()
    try:
        selected_id = input_devs[int(choice)][0] if choice else sd.default.device[0]
    except (ValueError, IndexError):
        selected_id = sd.default.device[0]
    print(f"> {sd.query_devices(selected_id)['name']}\n")
    return selected_id


def record(device_id):
    chunks = []
    def callback(indata, frames, time_info, status):
        chunks.append(indata.copy())
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS,
        dtype="int16", device=device_id, callback=callback,
    )
    print("  Recording... [Enter to stop]", flush=True)
    stream.start()
    try:
        input()
    except EOFError:
        pass
    stream.stop()
    stream.close()
    if not chunks:
        return None
    audio = np.concatenate(chunks, axis=0)
    print(f"  {len(audio) / SAMPLE_RATE:.1f}s captured")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, SAMPLE_RATE)
    tmp.close()
    return tmp.name


def transcribe(client, wav_path):
    print("  Transcribing...", end=" ", flush=True)
    with open(wav_path, "rb") as f:
        result = client.audio.transcriptions.create(model="whisper-1", file=f, language="en")
    print("ok")
    return result.text.strip()


# ── Main ──

def main():
    parser = argparse.ArgumentParser(description="Chat with your folder")
    parser.add_argument("folder", nargs="?", help="Folder to chat about")
    parser.add_argument("-m", "--model", default="gpt-4o-mini")
    parser.add_argument("-c", "--clipboard", action="store_true",
                        help="Chat about clipboard contents instead of a folder")
    args = parser.parse_args()

    if not args.clipboard and not args.folder:
        parser.error("provide a folder path or use -c for clipboard")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # ── Clipboard mode: simple chat, no tools ──
    use_clipboard = args.clipboard
    clipboard_text = None
    index = None
    root_path = None
    use_tools = False

    if use_clipboard:
        import subprocess
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        clipboard_text = result.stdout.strip()
        if not clipboard_text:
            print("Clipboard is empty.")
            sys.exit(1)
        print(f"Loaded clipboard ({len(clipboard_text):,} chars)")
        print(f"Preview: {clipboard_text[:150]}...")

        system_prompt = (
            "You are a helpful assistant. Answer questions ONLY using the text below. "
            "Do NOT use any outside knowledge. If the answer is not in the text, say so.\n\n"
            "--- CLIPBOARD CONTENT ---\n" + clipboard_text
        )
    else:
        # ── Folder mode: search-then-read with tools ──
        if not os.path.isdir(args.folder):
            print(f"Not a folder: {args.folder}")
            sys.exit(1)

        use_tools = True
        root_path = os.path.abspath(args.folder)
        print(f"Indexing {root_path}...")
        index = build_index(root_path)
        print(f"Found {len(index)} text files in {len(set(e['category'] for e in index))} categories")

        cats = {}
        for entry in index:
            cats[entry["category"]] = cats.get(entry["category"], 0) + 1
        cat_summary = ", ".join(f"{cat} ({n})" for cat, n in sorted(cats.items()))

        system_prompt = (
            "You are a helpful assistant that ONLY answers from the user's personal files. "
            "You have access to tools to search and read files from the user's folder.\n\n"
            "RULES:\n"
            "- ALWAYS search for relevant files before answering a question.\n"
            "- ONLY use information found in the files. Do NOT use outside knowledge.\n"
            "- If you can't find relevant information, say so honestly.\n"
            "- Cite which file your answer comes from.\n"
            "- Be conversational and natural.\n\n"
            f"Available categories: {cat_summary}\n"
            f"Total files: {len(index)}"
        )

    device_id = select_input_device()

    messages = [{"role": "system", "content": system_prompt}]

    mode_label = "CLIPBOARD" if use_clipboard else f"{len(index)} files indexed"
    print()
    print("=" * 50)
    print(f"  FOLDER CHAT  |  {args.model}")
    print(f"  {mode_label}")
    print("=" * 50)
    print()
    print("  [Enter]  record       [q]  quit")
    print("  [t]      type instead [s]  save chat")
    print("  [h]      history")
    print()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        cmd = line.lower()

        if cmd == "q":
            print("bye")
            break

        if cmd == "s":
            save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conversations")
            os.makedirs(save_dir, exist_ok=True)
            fname = f"folder_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            fpath = os.path.join(save_dir, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                for m in messages:
                    if m["role"] == "system":
                        continue
                    if m["role"] == "tool":
                        continue
                    prefix = "You" if m["role"] == "user" else "AI"
                    content = m.get("content", "")
                    if content:
                        f.write(f"{prefix}: {content}\n\n")
            print(f"  saved {fpath}")
            continue

        if cmd == "h":
            for m in messages:
                if m["role"] in ("system", "tool"):
                    continue
                prefix = "You" if m["role"] == "user" else "AI"
                content = m.get("content", "")
                if content:
                    print(f"\n{prefix}: {content}")
            print()
            continue

        # Type mode
        if cmd == "t":
            user_text = input("  Type: ").strip()
            if not user_text:
                continue
        elif cmd == "":
            # Record
            wav = record(device_id)
            if not wav:
                print("  (nothing captured)")
                continue
            try:
                user_text = transcribe(client, wav)
            finally:
                try:
                    os.unlink(wav)
                except OSError:
                    pass
            if not user_text:
                print("  (no speech detected)")
                continue
        else:
            # Treat typed text directly as input
            user_text = line

        print(f"\n  You: {user_text}")
        messages.append({"role": "user", "content": user_text})

        # Chat loop with tool calls
        try:
            max_rounds = 10
            for _ in range(max_rounds):
                print("  ...", end="", flush=True)
                call_args = {"model": args.model, "messages": messages}
                if use_tools:
                    call_args["tools"] = TOOLS
                resp = client.chat.completions.create(**call_args)
                msg = resp.choices[0].message

                if msg.tool_calls:
                    messages.append(msg)
                    for tc in msg.tool_calls:
                        print(f"\r  [{tc.function.name}: {tc.function.arguments}]")
                        result = handle_tool_call(tc, index, root_path)
                        if tc.function.name == "read_file":
                            print(f"\n{result}\n")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })
                else:
                    reply = msg.content
                    messages.append({"role": "assistant", "content": reply})
                    print(f"\r  AI: {reply}\n")
                    break

        except Exception as e:
            print(f"\n  Error: {e}")
            # Remove the user message if we failed
            messages.pop()


if __name__ == "__main__":
    main()
