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

lyrics_file = sys.argv[1] if len(sys.argv) > 1 else "lyrics.txt"
with open(lyrics_file, "r", encoding="utf-8") as f:
    lyrics = f.read()

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

genres = ["traditional hymn", "classical hymn", "gospel hymn"]

instruments = [
    "pipe organ, four-part choral harmonies",
    "piano, gentle strings, traditional choir",
    "acoustic piano, soft brass, congregational choir",
]

vocals = [
    "male vocalist, reverent and stately tone, four-part harmony",
    "male vocalist, dignified and warm, choral backing",
    "male vocalist, solemn and tender, hymn-style phrasing",
]

dynamics = [
    "steady strophic form, each verse building in fullness, majestic outro",
    "gentle verses, swelling chorus, peaceful resolution",
    "measured tempo, reverent throughout, triumphant final verse",
]

style = f"{random.choice(genres)}, {random.choice(instruments)}, {random.choice(vocals)}, {random.choice(dynamics)}"
if notes:
    style += f", melody: {notes}"
print(f"Style: {style}")

# Derive output base name from lyrics filename (without extension)
lyrics_base = os.path.splitext(os.path.basename(lyrics_file))[0]

payload = {
    "prompt": lyrics,
    "style": style,
    "title": lyrics_base.replace("_", " ").title(),
    "custom_mode": True,
    "instrumental": False,
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

# Poll for completion
print("Polling for completion...")
while True:
    poll = requests.get(f"{BASE_URL}/predictions/{request_id}/result", headers=headers)
    status = poll.json()
    print(f"Poll response: {status}")
    state = status.get("status")
    if state not in ("processing", "queued"):
        break
    elif state == "failed" or state == "error" or status.get("error"):
        raise Exception(status.get("error") or str(status))
    time.sleep(10)

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
out_path = f"{lyrics_base}.mp3"
n = 2
while os.path.exists(out_path):
    out_path = f"{lyrics_base}_{n}.mp3"
    n += 1

audio = requests.get(audio_url)
with open(out_path, "wb") as f:
    f.write(audio.content)

print(f"Saved to {out_path}")
