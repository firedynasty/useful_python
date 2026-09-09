import random
import requests
import time
import os
import sys
import subprocess

API_KEY = os.environ.get("MUAPI_KEY")
if not API_KEY:
    print("Error: MUAPI_KEY environment variable not set")
    sys.exit(1)

BASE_URL = "https://api.muapi.ai/api/v1"

# Parse -c flag (clipboard notes)
notes = None
if "-c" in sys.argv:
    notes = subprocess.check_output("pbpaste", text=True).strip()
    sys.argv.remove("-c")
    print(f"Notes from clipboard: {notes}")

# Parse -s flag (custom style string)
custom_style = None
if "-s" in sys.argv:
    idx = sys.argv.index("-s")
    custom_style = sys.argv[idx + 1]
    sys.argv.pop(idx + 1)
    sys.argv.pop(idx)
    print(f"Custom style: {custom_style}")

lyrics_file = sys.argv[1] if len(sys.argv) > 1 else None
if lyrics_file:
    with open(lyrics_file, "r", encoding="utf-8") as f:
        lyrics = f.read()
else:
    lyrics = "[instrumental]"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

genres = [
    "Bach-inspired lo-fi, baroque counterpoint",
    "lo-fi baroque, J.S. Bach influenced",
    "chill lo-fi, baroque polyphony, Bach chorale style",
]

instruments = [
    "harpsichord resampled through lo-fi filter, pizzicato strings, soft boom bap drums, vinyl crackle",
    "muted harpsichord, cello pizzicato, lazy hip hop drums, tape hiss, warm vinyl texture",
    "lo-fi piano playing Bach-style figures, pizzicato strings, dusty drum break, ambient pad",
]

moods = [
    "no dynamic swells, no dramatic builds, calm and repetitive, ADHD study music",
    "steady and meditative, loop-friendly, no tension or release, focus music",
    "gentle and unhurried, consistent energy throughout, background study music",
]

bpm = random.choice(["75 BPM", "80 BPM", "85 BPM"])

if custom_style:
    style = custom_style
else:
    style = f"{random.choice(genres)}, {random.choice(instruments)}, {bpm}, {random.choice(moods)}"
if notes:
    style += f", melody: {notes}"
print(f"Style: {style}")

# Derive output base name
if lyrics_file:
    base_name = os.path.splitext(os.path.basename(lyrics_file))[0]
else:
    base_name = "bach_lofi"

payload = {
    "prompt": lyrics,
    "style": style,
    "title": "Bach Lo-Fi",
    "custom_mode": True,
    "instrumental": True,
    "model": "V5"
}

resp = requests.post(f"{BASE_URL}/suno-create-music", json=payload, headers=headers)
print(f"Status code: {resp.status_code}")
result = resp.json()
print(f"Response: {result}")

request_id = result.get("request_id")
if not request_id:
    print("No request_id in response.")
    sys.exit(1)

# Poll for completion (max 5 minutes)
print("Polling for completion...")
max_polls = 30
for attempt in range(max_polls):
    poll = requests.get(f"{BASE_URL}/predictions/{request_id}/result", headers=headers)
    status = poll.json()
    state = status.get("status")
    print(f"[{attempt+1}/{max_polls}] Status: {state}")
    if state not in ("processing", "queued"):
        break
    if state == "failed" or state == "error" or status.get("error"):
        raise Exception(status.get("error") or str(status))
    time.sleep(10)
else:
    print("Timed out after 5 minutes. The API may be overloaded — try again later.")
    sys.exit(1)

# Extract audio URL
outputs = status.get("outputs", [])
if outputs:
    first = outputs[0]
    audio_url = first if isinstance(first, str) else first.get("audio_url") or first.get("url")
else:
    audio_url = status.get("audio_url")
if not audio_url:
    print("Could not find audio_url in completed response. See poll response above.")
    sys.exit(1)

# Download — avoid overwriting existing files by appending _2, _3, etc.
out_path = f"{base_name}.mp3"
n = 2
while os.path.exists(out_path):
    out_path = f"{base_name}_{n}.mp3"
    n += 1

audio = requests.get(audio_url)
with open(out_path, "wb") as f:
    f.write(audio.content)

print(f"Saved to {out_path}")
