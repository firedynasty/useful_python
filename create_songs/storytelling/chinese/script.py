import random
import requests
import time
import os
import sys

API_KEY = os.environ.get("MUAPI_KEY")
if not API_KEY:
    print("Error: MUAPI_KEY environment variable not set")
    sys.exit(1)

BASE_URL = "https://api.muapi.ai/api/v1"

lyrics_file = sys.argv[1] if len(sys.argv) > 1 else "lyrics.txt"
with open(lyrics_file, "r") as f:
    lyrics = f.read()

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

genres = ["conscious hip-hop", "political rap", "storytelling rap"]

beats = [
    "moody boom bap beat, 85-90 BPM, sparse piano loop, tension building",
    "cinematic trap-boom bap hybrid, 80-85 BPM, deep 808s, minor-key strings",
    "raw boom bap beat, 90-95 BPM, dusty drum break, haunting vocal sample",
]

vocals = [
    "narrative male vocalist, measured cadence, spoken-word interludes",
    "urgent male vocalist, rising intensity, layered gang-vocal ad-libs",
    "male vocalist, deliberate double-time verses, crowd-chant hook",
]

dynamics = [
    "tense verses, defiant hook, slow-burn build",
    "somber verses, rallying hook, dramatic bridge",
    "narrative verses building to protest-anthem hook, cathartic outro",
]



style = f"{random.choice(genres)}, {random.choice(beats)}, {random.choice(dynamics)}, {random.choice(vocals)}"
print(f"Style: {style}")

payload = {
    "prompt": lyrics,
    "style": style,
    "title": "The Planted Tree",
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

# Extract audio URL — outputs is a list of URLs or dicts
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
base_name = "planted_tree_v2"
out_path = f"{base_name}.mp3"
n = 2
while os.path.exists(out_path):
    out_path = f"{base_name}_{n}.mp3"
    n += 1

audio = requests.get(audio_url)
with open(out_path, "wb") as f:
    f.write(audio.content)

print(f"Saved to {out_path}")

