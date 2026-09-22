import random
import re
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

# Parse --ask flag (interactively pick beat/vocal/dynamic instead of random)
ask = "--ask" in sys.argv
if ask:
    sys.argv.remove("--ask")

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

# Parse -t flag (custom title; otherwise derived from the lyrics filename)
custom_title = None
if "-t" in sys.argv:
    idx = sys.argv.index("-t")
    custom_title = sys.argv[idx + 1]
    sys.argv.pop(idx + 1)
    sys.argv.pop(idx)

lyrics_file = sys.argv[1] if len(sys.argv) > 1 else None

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Style modeled on "Juicy"-era 90s East Coast storytelling rap: a grateful,
# vindicated narrator looking back from the top. Each lyrics file is a
# different angle on Cus D'Amato and Tyson (training methods, fear,
# discipline, the Catskill house, the loss), so the sound stays warm and
# nostalgic while the verses carry the specifics.
beats = [
    "90s East Coast boom bap, 92 BPM, mellow R&B soul sample loop, warm Rhodes, dusty drums",
    "boom bap beat, 88-92 BPM, vinyl-crackle funk bassline, soft string swells, crisp snare",
    "laid-back boom bap, 90 BPM, chopped 70s soul sample, muted horns, head-nod groove",
    "gritty boom bap, 94-96 BPM, dusty piano loop, heavy kick, jazzy upright bass",
    "smooth 90s hip-hop beat, 86-90 BPM, glossy R&B keys, finger-snap percussion, deep bass",
    "cinematic boom bap, 85 BPM, gym-bell and speed-bag percussion textures, somber strings, hard snare",
]

vocals = [
    "laid-back conversational male rap flow, relaxed baritone, nostalgic and grateful, smooth sung female R&B hook",
    "confident storytelling male rapper, clear diction, measured cadence, soulful female vocal on the chorus",
    "gravelly male rapper, heavy-hearted delivery, spoken-word asides, warm male-female harmony hook",
    "smooth baritone rapper, effortless off-beat flow, ad-libs between lines, sung R&B hook",
]

dynamics = [
    "spoken-word intro dedication, reflective verses, triumphant feel-good hook",
    "nostalgic verses building to a victorious chorus, somber stripped-down outro",
    "grateful storytelling verses, anthemic hook, final verse turns bittersweet",
    "quiet spoken intro, steady head-nod verses, celebratory hook, spoken farewell outro",
]

def choose(label, options):
    print(f"\nChoose a {label}:")
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        choice = input(f"\nEnter number (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print(f"Invalid choice, please enter a number between 1 and {len(options)}.")

if custom_style:
    style = custom_style
else:
    chosen_beat = choose("beat", beats) if ask else random.choice(beats)
    chosen_vocal = choose("vocal", vocals) if ask else random.choice(vocals)
    chosen_dynamic = choose("dynamic arc", dynamics) if ask else random.choice(dynamics)
    style = (
        f"storytelling rap, rags-to-riches memoir, grateful and vindicated tone, "
        f"{chosen_beat}, {chosen_vocal}, {chosen_dynamic}"
    )

if notes:
    style += f", melody: {notes}"
print(f"\nStyle: {style}")

# Derive output base name
if lyrics_file:
    base_name = os.path.splitext(os.path.basename(lyrics_file))[0]
else:
    base_name = "cus_damato"

# Title from filename: "092226_the_catskill_house" -> "The Catskill House"
title = custom_title or re.sub(r"^\d+_", "", base_name).replace("_", " ").title()
print(f"Title: {title}")

is_instrumental = lyrics_file is None
prompt_text = "[instrumental]" if is_instrumental else open(lyrics_file).read()

payload = {
    "prompt": prompt_text,
    "style": style,
    "title": title,
    "custom_mode": True,
    "instrumental": is_instrumental,
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
    if state in ("failed", "error") or status.get("error"):
        raise Exception(status.get("error") or str(status))
    if state not in ("processing", "queued"):
        break
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
    print(f"Full completed response: {status}")
    print("Could not find audio_url in completed response.")
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
