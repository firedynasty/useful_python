import os
import subprocess
import threading
import asyncio
import queue
import pyperclip
import sounddevice as sd
from kokoro_onnx import Kokoro

VOICE = "am_michael"   # try af_nicole, af_bella, bf_emma, bm_george, etc.
SPEED = 1.0
HANDOFF_WORDS = 20     # how many words macOS `say` speaks while Kokoro loads

_dir = os.path.dirname(os.path.abspath(__file__))

text = pyperclip.paste().strip()
if not text:
    print("Clipboard is empty.")
    raise SystemExit

words = text.split()
lead_text = " ".join(words[:HANDOFF_WORDS])
rest_text = " ".join(words[HANDOFF_WORDS:]) if len(words) > HANDOFF_WORDS else ""

print(f"Speaking {len(text)} chars with {VOICE}…")

# 1) Start macOS say immediately for the first few words
say_proc = subprocess.Popen(["say", "-r", "185", lead_text])

# 2) Load Kokoro AND pre-generate audio chunks in a background thread
audio_queue = queue.Queue()
SENTINEL = None

def load_and_generate():
    kokoro = Kokoro(os.path.join(_dir, "kokoro-v1.0.onnx"), os.path.join(_dir, "voices-v1.0.bin"))
    if rest_text:
        stream = kokoro.create_stream(rest_text, voice=VOICE, speed=SPEED, lang="en-us")
        loop = asyncio.new_event_loop()
        async def gen():
            async for samples, sr in stream:
                audio_queue.put((samples, sr))
        loop.run_until_complete(gen())
    audio_queue.put(SENTINEL)

generator = threading.Thread(target=load_and_generate)
generator.start()

# 3) Wait for say to finish
say_proc.wait()

# 4) Play pre-buffered Kokoro chunks (first one likely already ready)
while True:
    item = audio_queue.get()
    if item is SENTINEL:
        break
    samples, sr = item
    sd.play(samples, sr)
    sd.wait()

generator.join()
