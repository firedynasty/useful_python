import os
import pyperclip
import sounddevice as sd
from kokoro_onnx import Kokoro
from misaki.espeak import EspeakG2P

VOICE = "ef_dora"  # Spanish voices: ef_dora (female), em_alex (male), em_santa (male)
SPEED = 1.0

_dir = os.path.dirname(os.path.abspath(__file__))
kokoro = Kokoro(os.path.join(_dir, "kokoro-v1.0.onnx"), os.path.join(_dir, "voices-v1.0.bin"))
g2p = EspeakG2P(language="es")

text = pyperclip.paste().strip()
if not text:
    print("Clipboard is empty.")
    raise SystemExit

print(f"Speaking {len(text)} chars with {VOICE}…")

# Convert Spanish text to phonemes using misaki/espeak
phonemes, _ = g2p(text)

# Pass phonemes directly to kokoro
stream = kokoro.create_stream(phonemes, voice=VOICE, speed=SPEED, is_phonemes=True)

import asyncio
async def play():
    async for samples, sr in stream:
        sd.play(samples, sr)
        sd.wait()

asyncio.run(play())
