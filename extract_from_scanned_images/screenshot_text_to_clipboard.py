#!/usr/bin/env python3
"""
Extract text from the latest screenshot on the Desktop and copy it to the clipboard.

Usage:
    python screenshot_text_to_clipboard.py              # latest screenshot
    python screenshot_text_to_clipboard.py ./photo.png  # specific image

Requires:
    export OPENAI_API_KEY="sk-..."   (already in ~/.zshrc)
    pip install openai
"""

import base64
import glob
import os
import subprocess
import sys

import openai


def latest_screenshot() -> str | None:
    files = glob.glob(os.path.expanduser("~/Desktop/Screenshot*.png"))
    return max(files, key=os.path.getmtime) if files else None


def extract_text(client, image_path: str) -> str:
    with open(image_path, "rb") as f:
        b64_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_data}"},
                },
                {
                    "type": "text",
                    "text": "Extract all the text from this image exactly as written. "
                            "Preserve paragraphs and formatting. "
                            "Output only the extracted text, nothing else.",
                },
            ],
        }],
    )
    raw = response.choices[0].message.content
    # Collapse newlines and surrounding whitespace into a single space
    return " ".join(raw.split())


TEMP_CAPTURE = "/tmp/ocr_capture.png"


def capture_region() -> str:
    result = subprocess.run(["screencapture", "-i", TEMP_CAPTURE])
    if result.returncode != 0 or not os.path.isfile(TEMP_CAPTURE):
        print("Screenshot cancelled or failed.")
        sys.exit(0)
    return TEMP_CAPTURE


def main():
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = capture_region()

    if not os.path.isfile(image_path):
        print(f"File not found: {image_path}")
        sys.exit(1)

    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)

    print(f"Extracting: {image_path}")
    text = extract_text(openai.OpenAI(), image_path)

    subprocess.run("pbcopy", input=text.encode("utf-8"), check=True)
    print("-" * 50)
    print(text)
    print("-" * 50)
    print("Copied to clipboard.")

    # Also append to front TextEdit document if one is open
    applescript = """
tell application "TextEdit"
    if (count of documents) > 0 then
        set text of document 1 to (text of document 1) & " " & (the clipboard)
    end if
end tell
"""
    subprocess.run(["osascript", "-e", applescript], check=False)


if __name__ == "__main__":
    main()
